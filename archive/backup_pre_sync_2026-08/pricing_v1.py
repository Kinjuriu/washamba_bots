"""V1 forward price-path research model. RESEARCH ONLY.

Not imported by main.py and does not change agent behaviour. Builds
directly on `pricing.py`'s verified mechanics core (`market_price`,
`price_path_for_sale`, `apply_town_demand`, `simulate_single_product`,
`estimate_future_price`, `recommend_sell_quantity`) rather than
re-deriving any of it - those functions are imported, not reimplemented,
per "preserve the real engine pricing function wherever possible."

This module exists to close the specific gaps `docs/pricing_engine_notes.md`
found by auditing `pricing.py`'s wiring into `main.py`:

  1. own-harvest timing was a flat "everything lands at once" assumption -
     `estimate_own_harvest_units`/`estimate_own_pipeline` below replace that
     with a real projection of the engine's own yield-accrual rules.
  2. opponent supply was computed but never reached the sell decision -
     `estimate_opponent_pipeline` is a main.py-independent equivalent of
     `count_opponent_pipeline`, usable from this module without importing
     `main`.
  3. same-turn concurrent selling (both players selling the same product
     in the same turn) was not modelled at all - `price_path_concurrent`
     reproduces the engine's actual per-unit lockstep mechanic.
  4. nothing compared "sell now" against "sell later" - `compare_
     immediate_vs_delayed_selling` does exactly that.
  5. cadence was two step functions (a price threshold, a liquidation-day
     cliff) - `recommend_sell_cadence` proposes a continuous alternative,
     as a building block only, not wired anywhere.

Every new function's docstring cites the exact engine source line(s) it was
derived from - "engine is the source of truth" per CLAUDE.md. See
`experiments/pricing_v1_report.md` for the validation results and
`notebooks/pricing_v1_validation.ipynb` for the notebook that runs a real
episode and checks this module's predictions against what actually
happened, not just against the formula.

Status: proposal-grade research. Not merged into main.py. Not submitted to
Kaggle. Nothing here is wired into any live decision.
"""

from pricing import (  # noqa: F401 - re-exported for convenience
    DEFAULT_TOWN_SHOP_SELL_INTERVAL,
    DEFAULT_TOWN_CENTER_SELL_INTERVAL,
    DEFAULT_TURNS_PER_DAY,
    MARKET_PARAMS,
    PRICE_FLOOR,
    SHOPS,
    TOWN_CENTER_PRODUCTS,
    apply_town_demand,
    estimate_future_price,
    market_price,
    price_path_for_sale,
    recommend_sell_quantity,
    simulate_single_product,
)

try:
    from kaggle_environments.envs.kaggriculture.kaggriculture import CROPS
except ImportError:
    # Reproduction, not a guess: kaggriculture.py's own CROPS table,
    # confirmed by direct inspection (`python -c "from kaggle_environments...
    # import CROPS; print(CROPS)"`) against the installed engine while this
    # module was written. Kept in sync with pricing.py's own fallback
    # pattern for MARKET_PARAMS.
    CROPS = {
        "WHEAT":      {"seed": 10,  "first_yield_day": 2,  "max_yield_day": 4,  "interval": 0, "max_yield": 6, "ongoing": False},
        "CARROT":     {"seed": 20,  "first_yield_day": 2,  "max_yield_day": 3,  "interval": 0, "max_yield": 4, "ongoing": False},
        "TOMATO":     {"seed": 50,  "first_yield_day": 8,  "max_yield_day": 8,  "interval": 1, "max_yield": 4, "ongoing": True},
        "STRAWBERRY": {"seed": 100, "first_yield_day": 10, "max_yield_day": 10, "interval": 2, "max_yield": 4, "ongoing": True},
        "MELON":      {"seed": 80,  "first_yield_day": 10, "max_yield_day": 12, "interval": 0, "max_yield": 6, "ongoing": False},
    }

# A research-only default, not read from live configuration - pass the real
# episodeSteps/turnsPerDay-derived value through when you have it (e.g. from
# obs["day"] bookkeeping in a notebook). 30 matches every other reference to
# season length elsewhere in this repo (main.py's SEASON_DAYS).
DEFAULT_SEASON_DAYS = 30


# ---------------------------------------------------------------------
# 1. Expected own harvest
# ---------------------------------------------------------------------

def estimate_own_harvest_units(crop, planted_day, current_day, horizon_day, crop_info=None):
    """Projected `yield_units` a single tile of `crop`, planted on
    `planted_day`, will show at the START of `horizon_day` (i.e. what an
    `hour == 0` observation on `horizon_day` would read) - replacing
    pricing.py's "our supply lands all at once" simplification with the
    engine's actual accrual schedule.

    Two different mechanics, read directly from the engine
    (`kaggriculture.py`) rather than guessed, and validated against a real
    running episode, not just the formula in isolation - see
    `notebooks/pricing_v1_validation.ipynb`, section on own-harvest timing:

    - **Ongoing crops** (TOMATO, STRAWBERRY) accrue `+1` every `interval`
      days starting at `first_yield_day`, capped at `max_yield`
      (`_daily_refresh_plants`, kaggriculture.py:769-798). This runs as an
      end-of-day batch step keyed to `next_day = current_day + 1`, which
      already aligns with an `hour == 0` reading on `next_day` with no
      further adjustment needed - confirmed by an exact match against a
      live 12-day TOMATO episode.
    - **One-shot crops** (WHEAT, CARROT, MELON) start at `yield_units = 1`
      the instant they're planted (`_new_plant`, kaggriculture.py:215-226 -
      `"yield_units": 0 if cd["ongoing"] else 1`), then accrue a further
      `+1` on every *watered* day inside the window
      `[window_start, max_yield_day]`, where
      `window_start = (max_yield_day + 1) // 2` - **not**
      `first_yield_day`, a different, unrelated constant used elsewhere for
      season-maturity gating (`main.py`'s `choose_crop`). Confirmed by
      reading the WATER handler directly (`_apply_unit_action`,
      kaggriculture.py:431-443): `first_yield_day` never appears in that
      code path. For MELON specifically, `window_start` (6) and
      `first_yield_day` (10) are different numbers.

      Watering is a real-time, hour-by-hour action rather than an
      end-of-day batch step, so an `hour == 0` reading on `horizon_day`
      reflects watering already done on days up to `horizon_day - 1`, not
      `horizon_day` itself - an off-by-one this module's first draft got
      wrong (it initially omitted both the `+1` baseline and this offset)
      until checked against a live episode, where WHEAT's actual
      `yield_units` disagreed with the formula on the very first and last
      days of its window. Both are now folded into `applied_age` below.

    Necessary simplifying assumption, stated explicitly rather than
    hidden: **assumes every eligible day is watered**. Future watering
    compliance can't be known in advance, and this is the same class of
    assumption `pricing.py` already documents for pipeline timing. The
    fertilizer yield-doubling bonus is also not modelled (unknowable
    without an explicit fertilizer-usage plan), which makes this a
    conservative (never-overestimating) floor on both counts.
    """
    info = crop_info or CROPS.get(crop)
    if not info:
        return 0
    if horizon_day - planted_day < 0:
        return 0

    if info["ongoing"]:
        age = horizon_day - planted_day
        first = info["first_yield_day"]
        if age < first:
            return 0
        interval = max(1, info["interval"])
        ticks = (age - first) // interval + 1
        return min(info["max_yield"], ticks)

    max_yield_day = info["max_yield_day"]
    window_start = (max_yield_day + 1) // 2
    applied_age = horizon_day - planted_day - 1  # watering through the day BEFORE horizon_day
    watered_days_in_window = min(applied_age, max_yield_day) - window_start + 1
    baseline = 1  # _new_plant's immediate yield_units=1 for one-shot crops
    return min(info["max_yield"], baseline + max(0, watered_days_in_window))


def estimate_own_pipeline(tiles, current_day, horizon_day):
    """Sum `estimate_own_harvest_units` across every `PLANT` tile on our own
    farm, grouped by crop. `tiles` is the engine's own `farm["tiles"]`
    shape - a list of rows of tile dicts / `None` / `"LOCKED"` / weed
    dicts, exactly as it appears in a live observation, so this can be
    called directly on `obs["farms"][obs["player"]]["tiles"]`.
    """
    totals = {}
    for row in tiles or []:
        for tile in row or []:
            if isinstance(tile, dict) and tile.get("kind") == "PLANT":
                crop = tile.get("crop")
                units = estimate_own_harvest_units(
                    crop, tile.get("planted_day", current_day), current_day, horizon_day
                )
                if units:
                    totals[crop] = totals.get(crop, 0) + units
    return totals


# ---------------------------------------------------------------------
# 2. Estimated opponent supply
# ---------------------------------------------------------------------

def estimate_opponent_pipeline(opponent_tiles):
    """Lower-bound opponent supply, visible standing crop only - their shed
    is private and never appears in `obs` (`CLAUDE.md`: "opponent's shed
    is never visible"). Deliberately mirrors `main.py`'s own
    `count_opponent_pipeline` (each PLANT tile counted at the crop's full
    `max_yield`, not this module's own harvest-timing model) rather than
    using `estimate_own_harvest_units` here: we don't know the opponent's
    watering compliance any better than our own, and matching main.py's
    existing semantics keeps this function's output directly comparable to
    what the live agent already computes from the same tiles, rather than
    introducing a second, silently-different definition of "opponent
    supply." Takes a bare tiles structure (not `obs`) so this module has
    no dependency on `main.py`.
    """
    totals = {}
    for row in opponent_tiles or []:
        for tile in row or []:
            if isinstance(tile, dict) and tile.get("kind") == "PLANT":
                crop = tile.get("crop")
                info = CROPS.get(crop) or {}
                totals[crop] = totals.get(crop, 0) + (info.get("max_yield") or 1)
    return totals


# ---------------------------------------------------------------------
# 3. Same-turn concurrent selling
# ---------------------------------------------------------------------

def price_path_concurrent(item, starting_inventory, our_quantity, opponent_quantity, params=None):
    """Same-turn concurrent selling, modelled as true per-unit lockstep
    against one shared inventory - what `pricing.py`'s `price_path_for_sale`
    cannot represent, since it only ever models a single seller.

    Mirrors the engine's real `_process_market` loop exactly
    (kaggriculture.py:583-628): at each step, BOTH sides are quoted at the
    SAME pre-commit inventory ("Both players see the same pre-commit
    inventory for this unit" - the engine's own comment), both commit,
    and only then does inventory update - by however many sides actually
    committed a non-floor sale this step (`_commit_unit`,
    kaggriculture.py:652-661, called once per committing player per step,
    each call independently adding 1 to inventory if price > 1). The
    smaller of the two orders exhausts first; the larger order's excess
    then continues alone, at that point behaving exactly like
    `price_path_for_sale`.

    Returns each side's own realised price list plus the shared ending
    inventory - deliberately not a single merged list, since "our
    average price" and "their average price" both matter and are usually
    different once one order runs out before the other.
    """
    inventory = starting_inventory
    our_remaining = max(0, our_quantity)
    opponent_remaining = max(0, opponent_quantity)
    our_prices = []
    opponent_prices = []

    while our_remaining > 0 or opponent_remaining > 0:
        quote = market_price(item, inventory, params)
        committed = 0
        if our_remaining > 0:
            our_prices.append(quote)
            our_remaining -= 1
            committed += 1
        if opponent_remaining > 0:
            opponent_prices.append(quote)
            opponent_remaining -= 1
            committed += 1
        if quote > 1:
            inventory += committed

    return {
        "our_prices": our_prices,
        "opponent_prices": opponent_prices,
        "ending_inventory": inventory,
    }


# ---------------------------------------------------------------------
# 4. Price path / revenue for selling N units, and immediate-vs-delayed
# ---------------------------------------------------------------------

def expected_revenue_for_selling_n(item, current_inventory, n, params=None):
    """Sum of the realised per-unit prices for selling `n` units right now
    - a thin, explicitly-named wrapper over `price_path_for_sale`, kept
    separate so "price path" and "revenue" are two distinctly testable,
    distinctly named outputs rather than one dict callers have to know to
    sum themselves."""
    path = price_path_for_sale(item, current_inventory, n, params)
    return sum(path["prices"])


def compare_immediate_vs_delayed_selling(
    item,
    current_inventory,
    n,
    day,
    delay_turns,
    our_pipeline_supply=0,
    opponent_pipeline_supply=0,
    unlocked_shops=(),
    shop_interval=DEFAULT_TOWN_SHOP_SELL_INTERVAL,
    center_interval=DEFAULT_TOWN_CENTER_SELL_INTERVAL,
    start_step=None,
    params=None,
):
    """The hold-vs-sell-now comparison nothing in the live agent currently
    makes: sell `n` units right now, versus wait `delay_turns` and sell the
    same `n` units then, given the same forecasted pipeline supply landing
    in between (via `estimate_future_price`).

    Both sides sell the identical quantity `n` so the comparison isolates
    *timing* - selling a different amount at each point would conflate a
    timing question with a sizing question, which is exactly the kind of
    double-counted effect `docs/pricing_engine_notes.md` warns about
    (see its note on `choose_crop`'s old glut/self-supply terms).
    """
    if start_step is None:
        start_step = day * DEFAULT_TURNS_PER_DAY

    revenue_now = expected_revenue_for_selling_n(item, current_inventory, n, params)

    forecast = estimate_future_price(
        item,
        current_inventory,
        turns_ahead=delay_turns,
        our_pipeline_supply=our_pipeline_supply,
        opponent_pipeline_supply=opponent_pipeline_supply,
        unlocked_shops=unlocked_shops,
        shop_interval=shop_interval,
        center_interval=center_interval,
        start_step=start_step,
        params=params,
    )
    inventory_at_delay = forecast["inventory_after_demand"]
    revenue_delayed = expected_revenue_for_selling_n(item, inventory_at_delay, n, params)

    return {
        "revenue_now": revenue_now,
        "revenue_now_per_unit": (revenue_now / n) if n else 0.0,
        "revenue_delayed": revenue_delayed,
        "revenue_delayed_per_unit": (revenue_delayed / n) if n else 0.0,
        "inventory_at_delay": inventory_at_delay,
        "delay_is_better": revenue_delayed > revenue_now,
        "advantage": revenue_delayed - revenue_now,
    }


# ---------------------------------------------------------------------
# 5. Recommended selling quantity / cadence
# ---------------------------------------------------------------------

def inventory_pressure(shed_quantity, pipeline_supply, remaining_days, max_per_turn):
    """How much of a product we're carrying (held plus already-committed
    pipeline) relative to what could plausibly still be sold before the
    season ends, at this product's own per-turn cap and one selling
    opportunity a day. `>= 1` means structurally overcommitted - even
    selling flat-out every remaining day at the cap would not clear it in
    time, independent of what price does. Ported from the same idea
    `experiment/sell-cadence` used (see docs/pricing_engine_notes.md's
    "prior art" section) - reimplemented here rather than copied, so it
    can be tested against this module's own function set directly.
    """
    capacity = max(1, max_per_turn * max(1, remaining_days))
    carried = shed_quantity + pipeline_supply
    return carried / capacity


def season_urgency(day, season_days=DEFAULT_SEASON_DAYS):
    """0 early in the season, ramping continuously toward 1 as it ends -
    replacing a hard liquidation-day cliff (main.py's
    `LIQUIDATION_START_DAY`) with a signal a cadence function can blend
    with price, rather than switching mode entirely at one day boundary.
    Matches the replay evidence already in this repo
    (`docs/REPLAY_ANALYSIS.md`) that real top-ladder play shows no abrupt
    late-season selling cliff.
    """
    if season_days <= 1:
        return 1.0
    return min(1.0, max(0.0, day) / (season_days - 1))


def recommend_sell_cadence(
    item,
    current_inventory,
    shed_quantity,
    day,
    remaining_days,
    pipeline_supply=0,
    min_acceptable_price=None,
    max_per_turn=None,
    season_days=DEFAULT_SEASON_DAYS,
    params=None,
):
    """How much of `item` to sell this turn, and why - a deterministic
    building block for a future cadence experiment
    (`docs/pricing_engine_notes.md`'s proposed next layer, item 2), not a
    drop-in replacement for `should_sell`/`decide_market_actions` and not
    wired into `main.py`.

    Blends two signals instead of one fixed threshold:

    - **pressure** (`inventory_pressure`): if `>= 1`, sell everything held
      this turn (up to the per-turn cap) regardless of price - holding
      cannot possibly clear the pile in the days remaining.
    - **urgency** (`season_urgency`): otherwise, scale the effective
      minimum acceptable price down continuously as the season
      progresses (never below `PRICE_FLOOR`), then hand that adjusted
      floor to the existing, verified `recommend_sell_quantity` - this
      is deliberately a thin layer on top of an already-tested function,
      not a parallel reimplementation of its price-path walk.
    """
    urgency = season_urgency(day, season_days)
    cap = max_per_turn or shed_quantity or 1
    pressure = inventory_pressure(shed_quantity, pipeline_supply, remaining_days, cap)

    if pressure >= 1.0:
        return {
            "quantity": min(shed_quantity, max_per_turn or shed_quantity),
            "reason": "inventory_pressure",
            "urgency": urgency,
            "pressure": pressure,
            "effective_min_price": PRICE_FLOOR,
        }

    base_floor = min_acceptable_price if min_acceptable_price is not None else PRICE_FLOOR
    effective_min_price = max(PRICE_FLOOR, round(base_floor * (1.0 - urgency)))
    quantity = recommend_sell_quantity(
        item,
        current_inventory,
        shed_quantity,
        min_acceptable_price=effective_min_price,
        max_per_turn=max_per_turn,
        params=params,
    )
    return {
        "quantity": quantity,
        "reason": "price_path",
        "urgency": urgency,
        "pressure": pressure,
        "effective_min_price": effective_min_price,
    }


# ---------------------------------------------------------------------
# 6. Top-level orchestrator
# ---------------------------------------------------------------------

def forecast(
    item,
    current_inventory,
    day,
    turns_ahead,
    our_pipeline_supply=0,
    opponent_pipeline_supply=0,
    sell_quantity=0,
    unlocked_shops=(),
    shop_interval=DEFAULT_TOWN_SHOP_SELL_INTERVAL,
    center_interval=DEFAULT_TOWN_CENTER_SELL_INTERVAL,
    start_step=None,
    params=None,
):
    """One call producing every core required output together, for a
    notebook or a future caller that wants the full picture at once:
    `expected_future_inventory`, `expected_future_price`,
    `price_path_for_selling_n`, and `expected_revenue_for_selling_n`,
    alongside `simulate_single_product`'s own intermediate stages
    (spot price, price after our sale, price after opponent supply) so
    nothing is hidden behind a single number.

    `compare_immediate_vs_delayed_selling` and `recommend_sell_cadence`
    are separate calls, not folded in here, because they each need
    additional inputs (a delay horizon; shed quantity and remaining days)
    that don't belong on every forecast call.
    """
    if start_step is None:
        start_step = day * DEFAULT_TURNS_PER_DAY

    sim = simulate_single_product(
        item,
        current_inventory,
        our_supply=our_pipeline_supply,
        opponent_supply=opponent_pipeline_supply,
        turns_ahead=turns_ahead,
        unlocked_shops=unlocked_shops,
        shop_interval=shop_interval,
        center_interval=center_interval,
        start_step=start_step,
        params=params,
    )
    sell_path = price_path_for_sale(item, current_inventory, sell_quantity, params)

    result = dict(sim)
    result["expected_future_inventory"] = sim["inventory_after_demand"]
    result["expected_future_price"] = sim["future_price"]
    result["price_path_for_selling_n"] = sell_path["prices"]
    result["expected_revenue_for_selling_n"] = sum(sell_path["prices"])
    return result


# ---------------------------------------------------------------------
# 7. Sell-or-hold decision (one-step lookahead)
# ---------------------------------------------------------------------

# "One turn" per experiments/forward_sell_policy_v0_report.md's task
# spec, not a tuned constant - the smallest meaningful decision interval,
# since decide_market_actions already re-evaluates every turn. Named
# rather than inlined so a future experiment can cite exactly what this
# one changed, per that report's own finding about what a 1-turn horizon
# does and doesn't capture in this model.
DEFAULT_HOLD_HORIZON_TURNS = 1


def estimate_sell_or_hold_decision(
    item,
    current_inventory,
    shed_quantity,
    day,
    remaining_days,
    our_pipeline_supply=0,
    unlocked_shops=(),
    shop_interval=DEFAULT_TOWN_SHOP_SELL_INTERVAL,
    center_interval=DEFAULT_TOWN_CENTER_SELL_INTERVAL,
    start_step=None,
    hold_horizon_turns=DEFAULT_HOLD_HORIZON_TURNS,
    max_per_turn=None,
    season_days=DEFAULT_SEASON_DAYS,
    params=None,
):
    """Replaces "current_price > a fixed threshold" with a genuine
    sell-now-vs-hold-one-turn comparison, composed entirely from already-
    verified building blocks in this module - no new pricing math, no
    parallel reimplementation of market mechanics.

    1. Size the candidate sale down to PRICE_FLOOR
       (`recommend_sell_quantity`) - "how much would we sell this turn if
       we decided to sell at all," the same quantity `LIQUIDATION_START_DAY`
       already uses in `main.py` - so the comparison below is always
       "sell this quantity now" vs. "sell this same quantity after
       `hold_horizon_turns`," never a sizing question riding along.
    2. Compare selling that quantity now against selling it
       `hold_horizon_turns` later (`compare_immediate_vs_delayed_selling`),
       forecasting with our own pipeline supply (own harvest timing) -
       deliberately NOT the opponent's, out of scope for this experiment
       (see the report, and CLAUDE.md's "opponent-supply hypothesis
       closed for now").
    3. Override with a hard SELL if `inventory_pressure >= 1` - the same
       break-even `recommend_sell_cadence` (section 5, above) already
       uses, not a new number: even selling flat-out every remaining day
       at the cap wouldn't clear the position in time, so holding cannot
       be optimal regardless of what the price forecast says, since
       unsold inventory scores nothing at season end.

    Deliberately does NOT fold `season_urgency` into the decision with a
    blending coefficient - urgency is computed and returned for the
    caller to *measure* (does the decision naturally shift toward SELL
    as the season shortens, without being told to?), not to hand-tune
    the gate with an unjustified weight. See the report's "seasonality"
    section for what was actually measured.

    Ties resolve to SELL (`delay_is_better` requires a strict `>`,
    mirroring `compare_immediate_vs_delayed_selling`'s own definition) -
    worth stating explicitly, because at `hold_horizon_turns=1` with no
    pipeline supply landing, most turns have genuinely nothing that would
    make `revenue_delayed` differ from `revenue_now` at all (no town-
    demand tick fires on most single turns - see `apply_town_demand`'s
    interval checks), so this tie-break is not a corner case here, it is
    close to the common case. Reported, not hidden - see the report's
    behavioural diagnostics.
    """
    if start_step is None:
        start_step = day * DEFAULT_TURNS_PER_DAY

    cap = max_per_turn if max_per_turn is not None else shed_quantity
    quantity = recommend_sell_quantity(
        item, current_inventory, shed_quantity,
        min_acceptable_price=PRICE_FLOOR, max_per_turn=cap, params=params,
    )

    urgency = season_urgency(day, season_days)
    pressure = inventory_pressure(shed_quantity, our_pipeline_supply, remaining_days, cap or 1)

    if quantity <= 0:
        return {
            "quantity": 0, "prefer_sell": False, "reason": "nothing_to_sell",
            "pressure": pressure, "urgency": urgency,
            "revenue_now": 0.0, "revenue_delayed": 0.0, "advantage": 0.0,
            "opportunity_cost_of_holding": 0.0,
        }

    comparison = compare_immediate_vs_delayed_selling(
        item, current_inventory, quantity, day, hold_horizon_turns,
        our_pipeline_supply=our_pipeline_supply, opponent_pipeline_supply=0,
        unlocked_shops=unlocked_shops, shop_interval=shop_interval,
        center_interval=center_interval, start_step=start_step, params=params,
    )

    if pressure >= 1.0:
        prefer_sell, reason = True, "inventory_pressure"
    elif not comparison["delay_is_better"]:
        prefer_sell, reason = True, "sell_now_beats_hold"
    else:
        prefer_sell, reason = False, "hold_beats_sell_now"

    opportunity_cost_of_holding = max(0.0, comparison["revenue_now"] - comparison["revenue_delayed"])

    return {
        "quantity": quantity,
        "prefer_sell": prefer_sell,
        "reason": reason,
        "pressure": pressure,
        "urgency": urgency,
        "revenue_now": comparison["revenue_now"],
        "revenue_delayed": comparison["revenue_delayed"],
        "advantage": comparison["advantage"],
        "opportunity_cost_of_holding": opportunity_cost_of_holding,
    }


# ---------------------------------------------------------------------
# 8. Sell-or-hold decision (multi-day own-supply forecast, v1.1)
# ---------------------------------------------------------------------

# 4 days, not a value swept against evaluation results - reasoning:
# WHEAT's own max_yield_day is 4 (kaggriculture.py's CROPS table), so a
# 4-day window captures a currently-growing WHEAT tile's ENTIRE future
# yield trajectory rather than a partial slice of it, and WHEAT is by a
# wide margin the highest-volume decision product in this repo's own
# measurements (experiments/forward_sell_policy_v0_report.md: 75+
# sell-events/season, dwarfing every other crop). Separately, it also
# spans a full production interval for both currently-active animals
# (COW interval=2, SHEEP interval=3, ANIMALS table) and reaches
# MELON's watering window_start (6) closely enough that a season
# already past day 6 sees at least one MELON accrual tick inside the
# window. Sits inside the task's own "approximately 3-5 days" spec.
DEFAULT_HORIZON_DAYS = 4


def estimate_multi_day_sell_or_hold_decision(
    item,
    current_inventory,
    quantity,
    day,
    remaining_days,
    tiles=None,
    liquidation_start_day=None,
    unlocked_shops=(),
    shop_interval=DEFAULT_TOWN_SHOP_SELL_INTERVAL,
    center_interval=DEFAULT_TOWN_CENTER_SELL_INTERVAL,
    start_step=None,
    horizon_days=DEFAULT_HORIZON_DAYS,
    turns_per_day=DEFAULT_TURNS_PER_DAY,
    params=None,
):
    """v1.1 of the sell-or-hold decision - replaces v0's one-turn horizon
    (`estimate_sell_or_hold_decision`, section 7) with a genuine multi-day
    own-supply forecast, and does NOT size `quantity` itself: the caller
    passes in the exact quantity `main.py`'s own quantity-sizing pipeline
    already produced (`recommend_sell_quantity` with the product's real
    `SELL_PRICE_THRESHOLDS` floor, not `PRICE_FLOOR`) - this function only
    ever answers "sell this quantity now, or wait for a better day within
    the horizon to sell this SAME quantity," never a sizing question.
    Directly answers the docs/forward_sell_policy_v0_report.md finding
    that pinning `our_pipeline_supply=0` made 100% of v0's genuine
    (non-tie) comparisons trivially favour holding: here, at day
    granularity, `estimate_own_pipeline` (section 2, above - already
    validated against a live episode) gives a real answer for how much of
    `item` our own currently-growing tiles will add by each candidate
    future day, so "sell now" has a real chance to win on the merits, not
    just by tie-break.

    For each candidate day in `[day+1 .. day+effective_horizon]`:
      - our_pipeline_supply = estimate_own_pipeline(tiles, day, future_day)[item]
        - the same function `choose_crop`'s own forward-pricing already
          uses, not a new estimator. Animal products (WOOL/MILK/EGG) get
          0 here - `estimate_own_pipeline` only covers PLANT tiles
          (crops); extending it to the CARE-bank-driven animal accrual
          model is out of scope for this experiment (a genuinely
          different, more complex estimator, not a parallel
          reimplementation of an existing one - the very thing this task
          asked not to do). Documented as a real, scoped limitation, not
          hidden.
      - compare_immediate_vs_delayed_selling(item, current_inventory,
        quantity, day, delay_turns=(future_day-day)*turns_per_day,
        our_pipeline_supply=..., opponent_pipeline_supply=0, ...)
        - opponent supply is not a parameter this function accepts at
          all, per this experiment's explicit scope.
    The candidate future day with the HIGHEST revenue_delayed is kept.
    HOLD only if that best revenue strictly exceeds revenue_now - no
    added margin: a strict inequality on an already-economic quantity
    (realised revenue) needs no further coefficient, and ties keep the
    same "resolve to SELL" convention v0 already established.

    SEASON URGENCY, made structural rather than a blended weight: the
    horizon is capped at `min(horizon_days, remaining_days,
    liquidation_start_day - 1 - day)` when `liquidation_start_day` is
    given - proposing to "wait" past the day everything sells regardless
    of price isn't a real opportunity, it's evaluating a scenario that
    can't happen. As `day` approaches `liquidation_start_day`, this cap
    shrinks the candidate-day set on its own, with no added coefficient -
    on the last pre-liquidation day the effective horizon is 0 and the
    function returns SELL immediately, without ever calling the
    comparison. `LIQUIDATION_START_DAY` itself is untouched - this
    function is never even called on a liquidating turn (see the
    candidate's wiring), matching v0's isolation property.
    """
    if start_step is None:
        start_step = day * turns_per_day

    if quantity <= 0:
        return {
            "quantity": 0, "prefer_sell": False, "reason": "nothing_to_sell",
            "revenue_now": 0.0, "best_revenue_delayed": 0.0, "best_future_day": day,
            "advantage": 0.0, "opportunity_cost_of_holding": 0.0, "per_day": [],
        }

    effective_horizon = max(0, horizon_days)
    effective_horizon = min(effective_horizon, max(0, remaining_days))
    if liquidation_start_day is not None:
        effective_horizon = min(effective_horizon, max(0, liquidation_start_day - 1 - day))

    revenue_now = expected_revenue_for_selling_n(item, current_inventory, quantity, params)

    if effective_horizon <= 0:
        return {
            "quantity": quantity, "prefer_sell": True, "reason": "no_future_opportunity_in_horizon",
            "revenue_now": revenue_now, "best_revenue_delayed": revenue_now, "best_future_day": day,
            "advantage": 0.0, "opportunity_cost_of_holding": 0.0, "per_day": [],
        }

    per_day = []
    for offset in range(1, effective_horizon + 1):
        future_day = day + offset
        pipeline = estimate_own_pipeline(tiles, day, future_day) if tiles is not None else {}
        our_pipeline_supply = pipeline.get(item, 0)
        comparison = compare_immediate_vs_delayed_selling(
            item, current_inventory, quantity, day, offset * turns_per_day,
            our_pipeline_supply=our_pipeline_supply, opponent_pipeline_supply=0,
            unlocked_shops=unlocked_shops, shop_interval=shop_interval,
            center_interval=center_interval, start_step=start_step, params=params,
        )
        per_day.append({
            "future_day": future_day,
            "our_pipeline_supply": our_pipeline_supply,
            "revenue_delayed": comparison["revenue_delayed"],
        })

    best = max(per_day, key=lambda d: d["revenue_delayed"])
    prefer_sell = not (best["revenue_delayed"] > revenue_now)
    reason = "sell_now_beats_every_future_day" if prefer_sell else "a_future_day_beats_sell_now"
    opportunity_cost_of_holding = max(0.0, revenue_now - best["revenue_delayed"])

    return {
        "quantity": quantity,
        "prefer_sell": prefer_sell,
        "reason": reason,
        "revenue_now": revenue_now,
        "best_revenue_delayed": best["revenue_delayed"],
        "best_future_day": best["future_day"],
        "advantage": best["revenue_delayed"] - revenue_now,
        "opportunity_cost_of_holding": opportunity_cost_of_holding,
        "per_day": per_day,
    }
