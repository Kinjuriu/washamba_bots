"""
nikaangukia_meroni_v1
======================

Washamba Bots' deterministic agent for the Kaggriculture competition.

This is deliberately NOT a sophisticated AI. Every unit - the main farmer
and any hired hands - shares one reactive, rule-based priority list, and
they coordinate through a per-turn claim set so two units never spend
their turns on the same tile:

  1. Feeds an animal under its feet - ahead of even a ready harvest. A
     missed feeding is a permanent loss (the animal escapes for good),
     and it silently costs the CARE bank too, which only pays out on a
     day the animal was also fed.
  2. Harvests a ripe crop, or an animal whose held yield is near its cap
     (collecting its fertilizer first, since that is a separate output).
  3. Waters a crop, or cares for an already-fed animal, under its feet.
  4. Places a carried animal on the empty coop/pasture under its feet.
  5. Runs shed errands: collects a bought animal waiting for its home, or
     several days of wheat to go feed an animal elsewhere.
  6. Moves toward urgent work elsewhere (an animal to feed, a ripe crop,
     a crop about to weed out) before anything below.
  7. Carries a picked-up animal toward its coop/pasture if not there yet.
  8. Digs a weed under its feet for free, reclaiming dead land.
  9. Builds a coop (if still growing the animal side of the farm) or
     plants a sensible crop when standing on empty ground.
  10. Runs the fertilizer errand - collects a batch from the shed and
     carries it to an ongoing crop that is inside its payout window.
  11. Reclaims the nearest weed elsewhere - dead land is a permanent loss.
  12. Otherwise walks toward the closest useful tile.
  13. PASSes if there is genuinely nothing useful to do.

It also does simple, threshold-based market decisions: sell shed goods
when the price is good (capped per turn for premium goods so a big
harvest doesn't crash its own price), restock seed in one batched order
once a crop's stock is fully exhausted and we can afford it (see
SEED_REBUY_TRIGGER/seed_restock_quantity - buying one at a time on every
turn stock dipped below the cap used to trigger a full-price purchase
every single turn once planting demand was fixed, crashing the bank),
hire farm hands early each day against how much work is actually
pending, and buy one GOOSE at a time (see
ACTIVE_ANIMALS) plus a small wheat safety net for feeding it. Everything
still in the shed from LIQUIDATION_START_DAY on is sold regardless of
price - inventory scores nothing once the season ends.

The one piece of real economics is choose_crop(). FORWARD-PRICING EXPERIMENT
branch (see docs/EXPERIMENT_WORKFLOW.md): it scores a crop by *forecast*
revenue per growing day - pricing.py's estimate_future_price() at the
crop's first_yield_day horizon, given current market inventory and
everything we're already committed to selling - rather than today's spot
price. A melon planted today sells twelve days from now, into whatever
price our own harvest (and the market's own drift) has created by then.
See the docstring there before touching the formula - an earlier version
scored on spot price alone and once ranked crops by cheapness, planting
wheat all season and never once planting a melon.

NOT implemented in this version (on purpose, to keep V1 simple):
  - COW / SHEEP (the animal logic is data-driven off ACTIVE_ANIMALS, so
    enabling them is a config change, not new logic - though their
    products, MILK and WOOL, still need SELL_PRICE_THRESHOLDS/
    MAX_SELL_PER_TURN entries of their own before that's a good idea).
  - Buying land / unlocking new quadrants.
  - Any multi-turn planning, lookahead, or opponent modelling.

Every piece of environment metadata used here (CROPS, action names, the
observation shape) comes from the official Kaggriculture "Getting
Started" / Hosts notebook. Nothing is invented.
"""

# ---------------------------------------------------------------------
# Environment metadata (read from the engine, never hardcoded)
# ---------------------------------------------------------------------

# CROPS is the same environment-provided metadata table used in the
# official starter notebook's "Melon Maxxer" example. It tells us, per
# crop, the seed cost, how many days until it can be harvested, and how
# many units it yields - so we don't have to hard-code any of that
# ourselves.
try:
    from kaggle_environments.envs.kaggriculture.kaggriculture import ANIMALS, CROPS, SHOPS
except ImportError:
    # Defensive fallback: if this ever runs somewhere the environment
    # package isn't importable (e.g. a stripped-down test sandbox), we
    # still don't want the whole agent to blow up at import time. With
    # an empty CROPS table the agent simply won't plant anything - it
    # will still harvest/water/sell/PASS safely.
    CROPS = {}
    ANIMALS = {}
    SHOPS = {}

# Forward-pricing research module (pricing.py, this repo's root - see
# docs/EXPERIMENT_WORKFLOW.md). choose_crop() and decide_market_actions()
# reuse its estimate_future_price()/recommend_sell_quantity() instead of
# re-deriving the engine's price formula a second time here.
#
# Experiment-branch caveat, not yet resolved: the competition accepts a
# single main.py (or a .tar.gz with main.py at the root). A bare main.py
# upload would NOT bundle pricing.py, so this import only resolves inside
# this repo's checkout for now - see the experiment report before this
# branch is promoted anywhere near a real submission.
# ---------------------------------------------------------------------
# Forward pricing (inlined from pricing.py - DO NOT EDIT HERE)
# ---------------------------------------------------------------------
#
# The competition entrypoint is a single main.py, so `from pricing import ...`
# cannot work on Kaggle: a bare upload does not carry the module and the import
# fails before the agent is ever called. It passes every local check, because
# running from the repo root puts pricing.py on sys.path - which is exactly
# what makes it dangerous.
#
# pricing.py remains the source of truth and the place to edit. This copy is
# kept honest by test_inlined_pricing_matches_module, which compares the two
# implementations numerically rather than textually, so a drift shows up as a
# failing test instead of a silently different agent.

import math

try:
    from kaggle_environments.envs.kaggriculture.kaggriculture import (
        MARKET_PARAMS,
        PRICE_FLOOR,
        SHOPS,
        TOWN_CENTER_PRODUCTS,
    )
    from kaggle_environments.envs.kaggriculture.kaggriculture import (
        market_price as _engine_market_price,
    )
except ImportError:
    # Reproduction, not a guess: these are the same values kaggriculture.py
    # defines, copied so this module still works if the import path moves.
    PRICE_FLOOR = 1
    _MARKET_I0 = 10000
    MARKET_PARAMS = {
        "WHEAT":      {"base":  25, "I0": _MARKET_I0, "T": 400, "below_func": "sqrt",   "below_target": 0.80, "above_func": "log",    "above_target": 0.20},
        "CARROT":     {"base":  35, "I0": _MARKET_I0, "T": 450, "below_func": "hinge",  "below_target": 1.00, "above_func": "sqrt",   "above_target": 0.70},
        "TOMATO":     {"base":  60, "I0": _MARKET_I0, "T": 200, "below_func": "hinge",  "below_target": 0.40, "above_func": "sqrt",   "above_target": 0.60},
        "STRAWBERRY": {"base": 120, "I0": _MARKET_I0, "T": 100, "below_func": "sqrt",   "below_target": 0.70, "above_func": "linear", "above_target": 1.60},
        "MELON":      {"base": 250, "I0": _MARKET_I0, "T": 300, "below_func": "log",    "below_target": 0.20, "above_func": "sq",     "above_target": 3.60},
        "EGG":        {"base":  50, "I0": _MARKET_I0, "T": 332, "below_func": "hinge",  "below_target": 0.40, "above_func": "log",    "above_target": 0.20},
        "MILK":       {"base": 160, "I0": _MARKET_I0, "T": 122, "below_func": "sqrt",   "below_target": 0.60, "above_func": "linear", "above_target": 1.60},
        "WOOL":       {"base": 200, "I0": _MARKET_I0, "T": 105, "below_func": "log",    "below_target": 0.20, "above_func": "sq",     "above_target": 3.20},
        "FERTILIZER": {"base": 100, "I0": _MARKET_I0, "T": 200, "below_func": "linear", "below_target": 0.40, "above_func": "linear", "above_target": 0.40},
    }
    SHOPS = {
        "BAKERY":         ["EGG", "WHEAT"],
        "PIZZA_SHOP":     ["MILK", "TOMATO", "WHEAT"],
        "BRUNCH_SPOT":    ["EGG", "WHEAT", "STRAWBERRY"],
        "YARN_STORE":     ["WOOL"],
        "ICE_CREAM_SHOP": ["STRAWBERRY", "MILK", "WHEAT"],
        "PET_CAFE":       ["CARROT"],
        "SMOOTHIE_SHOP":  ["STRAWBERRY", "MILK"],
        "FARMERS_MARKET": ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY"],
    }
    TOWN_CENTER_PRODUCTS = [p for p in MARKET_PARAMS if p != "FERTILIZER"]
    _engine_market_price = None

# Same constant as the engine's HINGE_GAIN - only used by the local
# reproduction of _shape() below, not by the imported engine function.
HINGE_GAIN = 8.0

# Config defaults from kaggriculture.json - a research assumption when a
# live obs["configuration"] isn't available; pass the real values through
# where you have them (e.g. from env.configuration in a notebook).
DEFAULT_TOWN_SHOP_SELL_INTERVAL = 4
DEFAULT_TOWN_CENTER_SELL_INTERVAL = 24
DEFAULT_TURNS_PER_DAY = 24


def _shape(func, x, T=None):
    """Local reproduction of kaggriculture.py's `_shape` (engine has no
    public export for this - it's a private helper of `market_price`, which
    we call directly when available; this exists for the ImportError path
    and for exposing the per-unit shape to the notebook)."""
    x = max(0.0, x)
    if func == "linear":
        return x
    if func == "sq":
        return x * x
    if func == "sqrt":
        return math.sqrt(x)
    if func == "log":
        return math.log(1.0 + x)
    if func == "log10":
        return math.log10(1.0 + x)
    if func == "hinge":
        if not T or T <= 0:
            return x
        u = x / T
        return u + HINGE_GAIN * max(0.0, u - 1.0) ** 2
    return x


def market_price(item, inventory, params=None):
    """Price for `item` at a given market `inventory`, per the engine's
    `market_price` (kaggriculture.py:192-206). Uses the real engine
    function when it was importable; otherwise reproduces it exactly from
    MARKET_PARAMS above. Deterministic, no side effects.
    """
    p = (params or MARKET_PARAMS)[item]
    if _engine_market_price is not None and params is None:
        return _engine_market_price(item, inventory)

    base, I0, T = p["base"], p["I0"], p["T"]
    if inventory < I0:
        f = p["below_func"]
        amp = p["below_target"] * base / _shape(f, T, T)
        price = base + amp * _shape(f, I0 - inventory, T)
    else:
        f = p["above_func"]
        amp = p["above_target"] * base / _shape(f, T, T)
        price = base - amp * _shape(f, inventory - I0, T)
    return max(PRICE_FLOOR, int(round(price)))


def price_path_for_sale(item, starting_inventory, quantity, params=None):
    """The engine sells one unit at a time, re-quoting from the running
    inventory after each (kaggriculture.py:596-597, 652-661) - a crashed
    sale at the $1 floor does not add inventory, so once a run hits the
    floor every remaining unit also prices at $1 with no further inventory
    change. Returns a list of `quantity` per-unit prices actually realised,
    in order, plus the resulting inventory.

    This is the building block "add our supply -> calculate price" uses
    for more than one unit; for a single unit it's just `market_price`.
    """
    if quantity <= 0:
        return {"prices": [], "ending_inventory": starting_inventory}

    inventory = starting_inventory
    prices = []
    for _ in range(quantity):
        price = market_price(item, inventory, params)
        prices.append(price)
        if price > 1:
            inventory += 1
    return {"prices": prices, "ending_inventory": inventory}


def apply_town_demand(
    inventory,
    item,
    turns,
    unlocked_shops=(),
    shop_interval=DEFAULT_TOWN_SHOP_SELL_INTERVAL,
    center_interval=DEFAULT_TOWN_CENTER_SELL_INTERVAL,
    start_step=0,
):
    """Simulate town demand alone (no player orders) draining `item`'s
    market inventory over `turns` engine steps, per
    kaggriculture.py:728-749 (`_town_consume`). `unlocked_shops` is a
    snapshot list of currently-unlocked shop instances (by name, duplicates
    allowed) - future shop unlocks are stochastic and not modelled here;
    treat this as "if no new shop unlocks in this window."

    `start_step` matters because the interval check is `step % interval ==
    0` against the engine's absolute step counter, not a window-relative
    counter - pass the real `obs["step"]` when you have it so the phase
    lines up with what the engine will actually do.
    """
    for step in range(start_step, start_step + turns):
        if step % shop_interval == 0:
            for shop_name in unlocked_shops:
                products = SHOPS.get(shop_name, [])
                multiplier = 2 if len(products) == 1 else 1
                if item in products:
                    inventory -= multiplier
        if step % center_interval == 0 and item in TOWN_CENTER_PRODUCTS:
            inventory -= 1
    return inventory


def simulate_single_product(
    item,
    current_inventory,
    our_supply=0,
    opponent_supply=0,
    turns_ahead=0,
    unlocked_shops=(),
    shop_interval=DEFAULT_TOWN_SHOP_SELL_INTERVAL,
    center_interval=DEFAULT_TOWN_CENTER_SELL_INTERVAL,
    start_step=0,
    params=None,
):
    """The deterministic single-product simulator:

        current inventory
          -> add our supply     (price_path_for_sale)
          -> calculate price    (spot price right after our sale lands)
          -> add opponent supply (optional, same mechanic)
          -> remove town demand / recovery over `turns_ahead` turns
          -> calculate future price

    Returns a dict distinguishing every stage explicitly - these are four
    different numbers and conflating them is the mistake this module exists
    to avoid:

        spot_price                 price before anything in this call happens
        price_after_our_sale       price once our_supply units have sold
        our_sale_average_price     mean per-unit price realised by our_supply
        price_after_opponent_supply price after opponent_supply is added on
                                    top (equals price_after_our_sale if
                                    opponent_supply == 0)
        future_price                price after turns_ahead of town demand
        inventory_* (mirrors each price_* stage, for debugging/plotting)
    """
    spot_price = market_price(item, current_inventory, params)

    our_sale = price_path_for_sale(item, current_inventory, our_supply, params)
    inventory_after_our_sale = our_sale["ending_inventory"]
    price_after_our_sale = market_price(item, inventory_after_our_sale, params)
    our_sale_average_price = (
        sum(our_sale["prices"]) / len(our_sale["prices"])
        if our_sale["prices"]
        else spot_price
    )

    opponent_sale = price_path_for_sale(
        item, inventory_after_our_sale, opponent_supply, params
    )
    inventory_after_opponent_supply = opponent_sale["ending_inventory"]
    price_after_opponent_supply = market_price(
        item, inventory_after_opponent_supply, params
    )

    inventory_after_demand = apply_town_demand(
        inventory_after_opponent_supply,
        item,
        turns_ahead,
        unlocked_shops=unlocked_shops,
        shop_interval=shop_interval,
        center_interval=center_interval,
        start_step=start_step,
    )
    future_price = market_price(item, inventory_after_demand, params)

    return {
        "spot_price": spot_price,
        "spot_inventory": current_inventory,
        "price_after_our_sale": price_after_our_sale,
        "our_sale_average_price": our_sale_average_price,
        "inventory_after_our_sale": inventory_after_our_sale,
        "price_after_opponent_supply": price_after_opponent_supply,
        "inventory_after_opponent_supply": inventory_after_opponent_supply,
        "future_price": future_price,
        "inventory_after_demand": inventory_after_demand,
    }


def estimate_future_price(
    item,
    current_inventory,
    turns_ahead,
    our_pipeline_supply=0,
    opponent_pipeline_supply=0,
    unlocked_shops=(),
    shop_interval=DEFAULT_TOWN_SHOP_SELL_INTERVAL,
    center_interval=DEFAULT_TOWN_CENTER_SELL_INTERVAL,
    start_step=0,
    params=None,
):
    """Thin wrapper over `simulate_single_product`: estimate what `item`
    will be worth `turns_ahead` engine steps from now (e.g. at an expected
    harvest/sale date), given how much of it we and an assumed opponent
    expect to add to the market before then, and town demand draining
    inventory in between.

    This treats `our_pipeline_supply` / `opponent_pipeline_supply` as
    landing all at once, up front, rather than spread across the window -
    a deliberately simple (and slightly pessimistic on price) approximation
    for a first version; see docs/pricing_engine_notes.md for the
    discussion of that assumption.

    Returns the same structured dict as `simulate_single_product`; callers
    that only want the single number should read `["future_price"]`.
    """
    return simulate_single_product(
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


def recommend_sell_quantity(
    item,
    current_inventory,
    available_quantity,
    min_acceptable_price,
    max_per_turn=None,
    params=None,
):
    """How many units of `item` we could sell *this turn* before the price
    path drops below `min_acceptable_price`, capped by how many we actually
    hold (`available_quantity`) and an optional per-turn cap.

    Pure research helper - does not call should_sell() and is not wired
    into decide_market_actions(). Walks the same per-unit price path
    price_path_for_sale() computes and stops at the first unit that would
    quote below the floor, so the recommendation reflects the real
    within-order price decay rather than the spot price alone.
    """
    if available_quantity <= 0 or min_acceptable_price <= 0:
        return 0

    cap = available_quantity
    if max_per_turn is not None:
        cap = min(cap, max_per_turn)

    inventory = current_inventory
    count = 0
    for _ in range(cap):
        price = market_price(item, inventory, params)
        if price < min_acceptable_price:
            break
        count += 1
        if price > 1:
            inventory += 1
    return count


# ---------------------------------------------------------------------
# Season
# ---------------------------------------------------------------------

# The season is a fixed 30 days (0-indexed: day 0 through day 29), per the
# competition's hard constraints - not something that varies per episode.
SEASON_DAYS = 30

# Turns per in-game day - engine config default (kaggriculture.json
# turnsPerDay), and the value implied by the competition's fixed
# episodeSteps=720 (30 days x 24). Used to convert CROPS' day-based
# first_yield_day into a turn count for estimate_future_price().
TURNS_PER_DAY = 24

# ---------------------------------------------------------------------
# Crop selection
# ---------------------------------------------------------------------

# The only crops the environment actually defines seed metadata for.
# (EGG / MILK / WOOL / FERTILIZER are products, not plantable crops -
# they come from animals rather than seeds.)
PLANTABLE_CROPS = ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON"]

# ---------------------------------------------------------------------
# Selling and the shed
# ---------------------------------------------------------------------

# Minimum market price we're willing to sell a product at. These are
# simple, per-product thresholds so the team can tune them independently
# as we learn more about how each product's price tends to move.
# Any product not listed here falls back to DEFAULT_SELL_THRESHOLD.
SELL_PRICE_THRESHOLDS = {
    "WHEAT": 20,
    "CARROT": 25,
    "TOMATO": 40,
    "STRAWBERRY": 90,
    "MELON": 180,
    "EGG": 35,
    "WOOL": 140,
    "MILK": 115,
}
DEFAULT_SELL_THRESHOLD = 50

# MILK previously fell back to DEFAULT_SELL_THRESHOLD/an uncapped sell -
# safe at today's shipped 2-sheep-1-cow mix (measured: a threshold of 115
# and a cap of 7 are both exact no-ops there, +0 on 0 of 12 seeds - milk
# sells 36 units a season, largest single order 6, lowest sale price 202,
# because the town eats it faster than one cow produces it) but an
# unprotected gap the moment either changes: more cows, a different
# opponent that also sells milk, or any other logic that changes how much
# gets sold per turn. Giving it the same explicit threshold/cap pattern
# every other premium good already has closes that gap defensively, at
# measured zero cost in the one mix we can test today.

# Premium goods (base price > $100) crash hard toward the $1 floor when a
# large quantity is sold in one order, and there's no buy-back to undo it
# (BUY_PRODUCT only works for WHEAT/FERTILIZER) - the market only recovers
# gradually, via town shop/town-centre consumption between turns. Cap how
# much of these we sell in a single turn so a big harvest doesn't crater the
# price it would otherwise have fetched; the remainder stays in the shed and
# sells on a later turn once the price has had a chance to recover.
MAX_SELL_PER_TURN = {
    "STRAWBERRY": 10,
    "MELON": 15,
    "WOOL": 5,
    "MILK": 7,
}

# The shed holds at most 100 non-seed items - anything harvested past that
# cap is silently discarded at end of day, with no error and no way to
# recover it (see docs/kaggriculture_context.md). should_sell() alone can
# hold a slow-moving product indefinitely while price stays below
# threshold, right up until it overflows and evaporates for free. Once the
# shed gets this full, force a sale regardless of price - a mediocre sale
# beats a guaranteed $0.
SHED_FORCE_SELL_THRESHOLD = 70

# Anything still sitting in the shed when the season ends is worth exactly
# nothing - there is no scoring credit for inventory, only for bank balance.
# Measured on a real season: the shed sat at its 100-item cap on day 28
# holding 95 melons, because the price had drifted below the sell threshold
# and the agent kept waiting for a recovery that the season had no time
# left to deliver. From this day on, sell everything regardless of price.
# Still spread across turns via MAX_SELL_PER_TURN so the last few days
# don't dump the whole stock into one price-crashing order.
#
# Day 19, not 25, and the two evaluations disagree about that - which is the
# whole reason it is 19. Against `starter`, which never sells, holding out
# for a better price wins: day 19 is -440 there, worse on 10 of 12 seeds.
# Head to head against a copy of ourselves, where the order book is actually
# contested, day 19 is +617 and wins 21 of 24 matches. Selling into a market
# a competitor is also selling into is a race for the town's daily demand,
# and the loser gets the crashed price. The ladder is contested, so the
# head-to-head number is the one that predicts it (experiments/head_to_head.py).
#
# Swept 13/16/19/21/23/25/27: 19 is an interior peak, not an edge effect.
LIQUIDATION_START_DAY = 19

# ---------------------------------------------------------------------
# Seed buying
# ---------------------------------------------------------------------

# Don't stockpile more seeds of one crop than this - keeps cash free for
# other things instead of hoarding.
MAX_SEED_STOCKPILE = 3

# Never spend more than this fraction of our current cash on a single
# seed purchase, so a bad crop pick can't wipe out our bank balance.
SEED_SPEND_CAP_FRACTION = 0.5

# Only trigger a seed restock once a crop's held stock drops to (or below)
# this many - i.e. fully exhausted, not merely "below MAX_SEED_STOCKPILE".
#
# This one is load-bearing, not cosmetic. Once the shared per-turn PLANT
# budget below closes the seed-overcommit bug (units no longer collide on
# one held seed and get their PLANT silently dropped by the engine), a
# seed actually gets consumed almost every turn a unit stands on empty
# ground with one held. The old trigger - restock the instant held stock
# dipped under MAX_SEED_STOCKPILE - then re-fires *every single turn*:
# buy 1, a unit consumes it, buy 1 again next turn, forever, for as long
# as there's empty land and a seed-worthy crop. For MELON (~$80/seed) that
# is an ~$80/turn drain, and a controlled trace confirmed it crashed the
# bank from ~$2,160 to ~$25 by day 3-4, which starved the wheat safety net
# (BUY_PRODUCT silently no-ops below its price - kaggriculture.py:663) and
# killed the sheep by day 7 on every seed tested. Waiting until the crop is
# fully dry before restocking, then topping back up to MAX_SEED_STOCKPILE
# in one batched order (see seed_restock_quantity), buys the same total
# seed volume at roughly a third of the purchase frequency.
SEED_REBUY_TRIGGER = 0

# Never let a seed purchase - or the tail end of a restock batch - push the
# bank below this floor. This is the second half of the seed fix: even a
# batched, infrequent restock could still be timed badly enough to leave
# nothing for the next wheat purchase, so the wheat safety net in
# decide_animal_market_actions finds the cash drawer empty because seed
# buying got there first.
#
# Do not lower this. Below ~50 the guard stops binding at all and the
# ~$80/turn repurchase spiral comes straight back: 25 and 0 are byte
# identical at **-15,845, losing 0 of 12 seeds**, sheep dead on every one.
#
# 450, not 100, and the reason is that this is really a *timing* control
# rather than a safety floor. At 100 the agent spends its starting stake on
# seed during the days 3-7 cash trough; at 450 it cannot, so it waits and
# buys seed out of first-harvest income instead. Seed 0 against `starter`,
# 100 against 450: BUY_SEED 93 -> 33 (days 0-7: 33 -> 10), and the trough
# itself nearly disappears - bank at day 5 goes **$17 -> $392**. Fewer PLANT
# actions (137 -> 90) produce *more* harvests (115 -> 129), because the seed
# that does get bought actually lands instead of being spent into a turn
# where units collide on it.
#
# That is also why this and MIN_MONEY_TO_HIRE stopped fighting. Measured
# against the previous agent, the seed fix at 100 was -1,471 (3/12) - it and
# the hire gate were competing for the same trough dollars. Removing the
# trough removes the conflict.
#
# Swept on the built-in harness against the live agent: 0/25 -15,845 (0/12),
# 50 -1,121, 100 -1,471, 200 +2,533, 300 +3,410, **450 +5,389 (10/12,
# t=3.84)**, 700 +3,190. A real interior optimum - too high and it starts
# blocking seed the agent can afford. Confirmed head to head at **+4,166,
# winning 24 of 24.**
MIN_CASH_RESERVE_FOR_SEED_BUYING = 450

# ---------------------------------------------------------------------
# Fertilizer
# ---------------------------------------------------------------------

# FERTILIZE marks a plant for `day`, `day+1` and `day+2`, and the bonus is
# paid only on days the plant is *also* watered - `_daily_refresh_plants`
# gates it on `was_watered`. It is a multiplier on watering, never a
# substitute for it.
#
# Only ongoing crops can use it at all. `_daily_refresh_plants` skips
# one-time crops outright (`if not cd["ongoing"]: continue`), so a unit of
# fertilizer spent on wheat, carrot or melon is simply thrown away. That
# leaves the two ongoing crops, where each covered production tick banks
# +2 instead of +1:
#
#   TOMATO      interval 1 -> the 3-day cover catches 3 ticks
#   STRAWBERRY  interval 2 -> catches 2 ticks
FERTILIZABLE_CROPS = ("TOMATO", "STRAWBERRY")

# Bought fertilizer lands in the shed, but FERTILIZE spends from the acting
# unit's own inventory - so a unit has to stand shed-adjacent and PICKUP
# before it can fertilise anything. Carry a few at a time so one trip serves
# several plants instead of one.
FERTILIZER_CARRY_BATCH = 3

# Don't buy fertilizer we have no plant to use it on, and keep a lid on the
# stock so it doesn't crowd the shed or the cash. The Goose also produces
# fertilizer for free via COLLECT_FERTILIZER, so this cap is mostly a brake
# on buying what the animal already supplies.
MAX_FERTILIZER_STOCK = 6

# Fertilizer bought this late can't catch enough production ticks to repay
# itself before the season ends.
FERTILIZER_LAST_USEFUL_DAY = 24

# ---------------------------------------------------------------------
# Labour
# ---------------------------------------------------------------------

# Farm hands. The n-th hire of a day costs farmHandCostMult * fib(n) with
# fib indexed 1, 1, 2, 3, 5, 8, ... (kaggriculture.py:_fib / _hire_cost), and
# the counter resets every morning - so the first hand of the day costs $1
# and four hands cost $7 total. That is trivial against a ~$5,000 bank, and
# a single farmer's upkeep capacity (watering and digging) is what actually
# caps this agent's income: plant more tiles than one unit can water and the
# surplus weeds out. Hands are the cheapest way to raise that ceiling.
# Cumulative day cost by crew size: 4 hands $7, 6 hands $20, 8 hands $54.
# Even eight is under $1,700 for a full season, which is small against the
# extra tiles they keep alive.
MAX_HANDS_PER_DAY = 8

# Hands are cleared at the end of every day and must be re-hired each
# morning, so hire in the first few turns - a hand bought at hour 20 costs
# the same as one bought at hour 0 but does a fraction of the work.
HIRE_BEFORE_HOUR = 4

# HIRE competes with SELL/BUY_SEED for the 10 market orders we get each
# turn, and surplus orders are dropped silently. Spread the morning's hiring
# across the first few turns instead of emitting the whole crew at once and
# pushing the day's sales off the end of the list.
MAX_HIRES_PER_TURN = 3

# Roughly how many tiles needing attention justify one more hand. This is
# the ratio that actually sets crew size; MAX_HANDS_PER_DAY is only a
# ceiling for when we own more land. A ratio of 4 (about 6 hands) was once
# recorded here as 1,300-2,600 worse than 6, but that was judged against the
# across-seed stdev - the wrong test, since both arms play the same seeds and
# that variance cancels. Re-run head to head, 4 is +1,910 winning 16 of 16:
# the farm waters 19.2 tiles a day against 24 planted, so upkeep, not
# acreage, is what binds.
WORK_TILES_PER_HAND = 4

# Don't spend our last coins on labour - but the first hand of the day costs
# $1, so a $150 floor was reserving seed money against a purchase two orders
# of magnitude smaller. There is a cash trough on roughly days 3-7, after the
# seed/pasture/animal spend and before the first real harvest lands, and a
# 150 gate locks the crew out for whole days inside it. Measured head to head:
# 60 is +402 (10/16), 20 is +1,025 (19/24, worst match -102), 0 is +1,144 -
# monotone in how much of the trough the gate still blocks.
MIN_MONEY_TO_HIRE = 20

# ---------------------------------------------------------------------
# Market order budget
# ---------------------------------------------------------------------

# The engine processes at most this many market orders per player per turn
# and silently drops the rest (kaggriculture.json: maxMarketOrdersPerTurn),
# so going over the cap loses orders with no error to catch.
MAX_MARKET_ORDERS_PER_TURN = 10


# ---------------------------------------------------------------------
# Animal husbandry
# ---------------------------------------------------------------------

# Animal husbandry (V1 scope: just GOOSE). It's the cheapest animal ($300),
# has the fastest payback (first_yield_day=4), and produces every day
# (interval=1) - the fastest way to prove the whole build -> buy -> pickup
# -> place -> feed -> care -> harvest -> sell pipeline actually works before
# committing to COW/SHEEP. The logic below is written generically against
# this list, so extending it later is a config change, not new logic - see
# choose_animal_to_build for the priority order multiple species use.
ACTIVE_ANIMALS = ["SHEEP", "COW"]
ANIMAL_STRUCTURE_KINDS = {ANIMALS[a]["structure"] for a in ACTIVE_ANIMALS if a in ANIMALS}

# Cap on total animals we'll commit to (built structures, filled or not).
#
# Stays at 1. Three Geese were measured at +14% self-play on the pre-fertilizer,
# pre-day-19 agent (PR #10) and that measurement was correct for the agent it
# was taken on - but the agent moved underneath it. Re-measured on current
# main, with the fertilizer errand competing for the same unit-turns, three
# animals lose **-9,787 head to head, winning 0 of 16 matches**, and self-play
# is flat (27,983 against 28,206).
#
# Note the two harnesses disagreeing again, in the direction that matters:
# self-play changes BOTH sides, so a revenue stream that doesn't compete for
# a scarce market lifts both banks and looks free. Head to head is what shows
# the cost, and the cost is real - every coop takes a tile out of crop
# production and a share of the crew's upkeep capacity, which is the same
# ceiling BUY_LAND and a denser crew both ran into.
#
# Stays at 1, but NOT for the reason the old note gave, and the difference
# matters if you are thinking of raising it.
#
# A second sheep looks like one of the largest gains available when measured
# head to head against this agent: +5,119 (14/16) on 8 seeds, +3,623 (18/24)
# on 12. Paired against the `starter` built-in it is **-19,514, losing 0 of
# 12 seeds**. Both numbers are real; the second one is the one that matters,
# because it is a genuine failure and not a harness artifact.
#
# What happens: buying the second animal lands in the same days 3-7 cash
# trough that MIN_MONEY_TO_HIRE is tuned around, and drains it to nothing.
# The two constants are NOT coupled, though - checked, because the obvious
# worry is that cheap hiring drains the cash the animal needs. It is the other
# way round: at the old gate of 150 the second sheep is -31,059 (0/12), worse
# than the -19,514 it costs at 20. Cheaper hands cushion the collapse.
# Measured on seed 0 against `starter`, money at day 5 is $5 and at day 10 is
# $9 (against $17 and $482 with one sheep). With no cash the agent cannot buy
# feed, so FEED falls 29 -> 10 and **both sheep starve and escape** - the two
# pastures end the season empty, wool sold is 0, and the crew is under-hired
# for a third of the season (HIRE 165 -> 112, WATER 611 -> 466).
#
# It survives head to head only because that opponent crowds the market the
# same way we do, which changes our cash timing enough to clear the trough.
# Against a differently-shaped opponent it does not clear, and the ladder is
# full of differently-shaped opponents.
#
# So this is gated on cash, not on the count. Raising MAX_ANIMALS is safe only
# once buying animal n is conditional on surviving the trough - a bank floor
# or a day gate on the second purchase - at which point re-measure on BOTH
# harnesses. For the record, past 2 the count itself is the problem: 3 is
# -2,618 (6/16) and 4 is -16,121 (0/16) even head to head.
#
# Not market depth, though - that theory is wrong and worth not re-testing.
# WOOL floors 58 units above I0 on the static curve, but measured at one, two
# and three sheep the market ends BELOW the 10,000 baseline (9,822 / 9,855 /
# 9,743) at a price ABOVE the $200 base (244 / 243 / 248), with nothing left
# unsold. The town eats wool faster than three sheep can make it.
MAX_ANIMALS = 3

# Never buy an animal that eats more than this fraction of current cash in
# one shot - same reasoning as SEED_SPEND_CAP_FRACTION.
ANIMAL_SPEND_CAP_FRACTION = 0.5

# Keep at least this much WHEAT on hand (shed + carried) whenever we own a
# placed animal, buying more via BUY_PRODUCT if it ever hits zero. A missed
# feeding is not a recoverable loss like a weed (DIG reclaims those) - the
# animal escapes for good - so feed supply can't be left to chance on
# however wheat farming happens to be going that day.
MIN_WHEAT_RESERVE_FOR_FEEDING = 2

# Feeding spends wheat from the acting unit's own inventory, not the shed,
# so every meal otherwise costs a fresh shed round-trip. Carry a few days'
# worth per trip instead.
WHEAT_CARRY_BATCH = 3


# ---------------------------------------------------------------------
# Observation readers
#
# These small helpers pull pieces out of the observation defensively
# (using .get() and length checks) so a missing key, a None tile, or an
# unexpected shape never crashes the agent - it just falls back to "no
# information available" and lets the higher-level logic PASS safely.
# ---------------------------------------------------------------------

def get_player_farm(obs):
    """Return our own player's farm dict, or None if it can't be found."""
    farms = obs.get("farms")
    player = obs.get("player")
    if not isinstance(farms, list) or not isinstance(player, int):
        return None
    if player < 0 or player >= len(farms):
        return None
    return farms[player]


def get_tile_at(farm, x, y):
    """
    Return the tile dict/None/"LOCKED" at (x, y), or None if that's off the
    board. Note tiles are row-major - tiles[y][x] - while unit positions are
    [x, y]; mixing the two up is the classic silent bug in this game.
    """
    tiles = farm.get("tiles") if farm else None
    if not tiles or y < 0 or y >= len(tiles):
        return None
    row = tiles[y]
    if x < 0 or x >= len(row):
        return None
    return row[x]


def get_current_tile(farm):
    """Return the tile dict/None/"LOCKED" the farmer is currently standing on."""
    farmer_pos = farm.get("farmer") if farm else None
    if not farmer_pos or len(farmer_pos) != 2:
        return None
    return get_tile_at(farm, farmer_pos[0], farmer_pos[1])


def shed_access_tiles(board_size):
    """
    The four inner-corner tiles adjacent to the shed, matching the engine's
    own placement rule (kaggriculture.py: _shed_access_tiles /
    _is_shed_adjacent) - not exposed directly on `obs`, so we replicate the
    formula rather than guess at it.
    """
    half = board_size // 2
    return [(half - 1, half - 1), (half, half - 1), (half - 1, half), (half, half)]


def is_shed_adjacent(x, y, board_size):
    return (x, y) in shed_access_tiles(board_size)


def wants_fertilizer(tile, day):
    """
    True if fertilising this plant right now would actually pay.

    Only ongoing crops qualify (see FERTILIZABLE_CROPS), and only inside the
    stretch where the three-day cover still catches production ticks.
    Fertilizer applied outside that window is thrown away.

    The window edges come straight out of `_daily_refresh_plants`, which
    computes `days_since_first = (day + 1) - planted_day - first_yield_day`
    and produces while that is a non-negative multiple of `interval` with
    `days_since_first // interval + 1 <= max_yield`. Rewriting in terms of
    the age this function has (`age = day - planted_day`) puts the final
    tick at `first_yield_day - 1 + interval * (max_yield - 1)`.

    That `- 1` matters: without it the agent buys and applies a unit a day
    after the last tick it could possibly pay for.
    """
    if not (isinstance(tile, dict) and tile.get("kind") == "PLANT"):
        return False

    crop = tile.get("crop")
    if crop not in FERTILIZABLE_CROPS:
        return False

    if tile.get("fertilized_until_day", -1) >= day:
        return False  # already covered today

    crop_info = CROPS.get(crop) or {}
    first_yield_day = crop_info.get("first_yield_day")
    if first_yield_day is None:
        return False

    interval = crop_info.get("interval") or 1
    max_yield = crop_info.get("max_yield") or 1
    last_tick_age = first_yield_day - 1 + interval * (max_yield - 1)

    age = day - tile.get("planted_day", day)
    # Cover starts today and runs two more days, so applying just ahead of
    # the first tick still catches it.
    return (first_yield_day - 3) <= age <= last_tick_age


def find_fertilizer_target(farm, board_size, ux, uy, day, exclude=None):
    """Nearest plant worth fertilising, or None."""
    exclude = exclude or set()
    tiles = farm.get("tiles") or []

    best_target = None
    best_distance = None
    for y in range(board_size):
        row = tiles[y] if y < len(tiles) else []
        for x in range(len(row)):
            if (x, y) in exclude or not wants_fertilizer(row[x], day):
                continue
            distance = abs(x - ux) + abs(y - uy)
            if best_distance is None or distance < best_distance:
                best_distance = distance
                best_target = (x, y)
    return best_target


def nearest_shed_tile(fx, fy, board_size):
    """Closest of the four shed-access tiles to (fx, fy)."""
    tiles = shed_access_tiles(board_size)
    return min(tiles, key=lambda t: abs(t[0] - fx) + abs(t[1] - fy))


def get_market_state(obs):
    """Return {"prices": {...}, "inventory": {...}}, defaulting to empty dicts."""
    market = obs.get("market") or {}
    return {
        "prices": market.get("prices") or {},
        "inventory": market.get("inventory") or {},
    }


def extract_state(obs):
    """
    Pull everything the rest of the agent needs out of the raw
    observation, once, defensively. Downstream functions work off this
    tidy "state" dict instead of poking at obs directly everywhere.
    """
    obs = obs or {}
    farm = get_player_farm(obs)
    private = obs.get("private") or {}
    tiles = farm.get("tiles") if farm else None

    day = obs.get("day", 0)
    hour = obs.get("hour", 0)
    town = obs.get("town") or {}

    return {
        "farm": farm,
        "private": private,
        "market_state": get_market_state(obs),
        "board_size": len(tiles) if tiles else 0,
        "day": day,
        "hour": hour,
        # obs["step"] is framework-supplied (see CLAUDE.md's I/O contract);
        # the day*TURNS_PER_DAY+hour fallback only matters for a malformed
        # observation. Both feed estimate_future_price()'s town-demand
        # phase alignment via choose_crop() - see pricing.py.
        "step": obs.get("step", day * TURNS_PER_DAY + hour),
        "opponent_pipeline": count_opponent_pipeline(obs),
        "unlocked_shops": town.get("unlocked_shops") or [],
    }


# ---------------------------------------------------------------------
# Movement
# ---------------------------------------------------------------------

def step_toward(fx, fy, tx, ty):
    """
    Return a single direction ("NORTH"/"SOUTH"/"EAST"/"WEST") that moves
    one step closer to (tx, ty), or None if we're already there.

    This is simple Manhattan-distance movement, not real pathfinding -
    good enough for V1 since the board has no obstacles the farmer can't
    just walk around a tile at a time.
    """
    if fx > tx:
        return "WEST"
    if fx < tx:
        return "EAST"
    if fy > ty:
        return "NORTH"
    if fy < ty:
        return "SOUTH"
    return None


def is_harvestable(tile, day):
    """
    True if a PLANT tile is actually ready to pick right now.

    yield_units > 0 alone is NOT enough: a freshly planted non-ongoing crop
    (WHEAT/CARROT/MELON) starts with yield_units=1 the instant it's
    planted - a placeholder for its eventual payout, not a "ready now"
    signal. The environment separately gates HARVEST on
    `day - planted_day >= first_yield_day` and silently no-ops otherwise.
    Without checking that gate too, we'd repeatedly attempt (and fail) to
    harvest a still-growing crop every turn - and because that check runs
    before watering in the priority order, the crop never gets watered and
    dies before it ever matures.
    """
    if tile.get("yield_units", 0) <= 0:
        return False
    crop_info = CROPS.get(tile.get("crop"))
    if not crop_info:
        return False
    first_yield_day = crop_info.get("first_yield_day", 0)
    return day - tile.get("planted_day", day) >= first_yield_day


def remaining_season_days(day):
    """Days left, inclusive of today, before the season's last day (29)."""
    return (SEASON_DAYS - 1) - day


def has_plantable_seed(seeds, day):
    """
    True if at least one held seed belongs to a crop that could still
    reach first_yield_day before the season ends.

    Without this check, "any" targeting below would send the farmer
    walking toward an empty tile on the strength of a seed it can never
    usefully plant (choose_crop() would just refuse it again on arrival,
    per the same season-maturity gate) - not a money loss, but a wasted
    turn wandering toward a tile with nothing useful to do there.
    """
    remaining_days = remaining_season_days(day)
    for crop, count in seeds.items():
        if count <= 0:
            continue
        crop_info = CROPS.get(crop)
        if not crop_info:
            continue
        first_yield_day = crop_info.get("first_yield_day")
        if first_yield_day is None or first_yield_day <= remaining_days:
            return True
    return False


def find_nearest_target(farm, board_size, fx, fy, task, day, seeds=None, exclude=None):
    """
    Scan the whole farm grid and return the (x, y) of the closest tile
    matching `task`, or None if there isn't one.

    `exclude` is a set of (x, y) tiles another unit has already claimed
    this turn. Without it, every hand would pick the same nearest target
    and they'd all walk to one tile while the rest of the farm rotted.

    task options:
      "harvest"        - a plant or animal tile that's ready to pick right
                          now.
      "water_urgent"   - a plant tile that already missed a watering and
                          will turn into a weed if it's missed again today.
      "feed"    - an animal tile that already missed a feeding and
                          will escape for good if it's missed again today.
      "weed"           - a dead tile that can be dug back into plantable
                          ground.
      "empty_structure" - a built COOP/PASTURE with no animal in it yet.
      "any"            - anything at all worth walking to: a ripe plant,
                          an unwatered plant, or (if we're holding at
                          least one seed that can still mature) an empty
                          tile we could plant.
    """
    seeds = seeds or {}
    exclude = exclude or set()
    tiles = farm.get("tiles") or []
    have_any_seed = has_plantable_seed(seeds, day)

    best_target = None
    best_distance = None

    for y in range(board_size):
        row = tiles[y] if y < len(tiles) else []
        for x in range(len(row)):
            if (x, y) in exclude:
                continue
            tile = row[x]
            is_match = False

            if isinstance(tile, dict) and tile.get("kind") == "PLANT":
                is_ripe = is_harvestable(tile, day)
                needs_water = not tile.get("watered_today", True)
                missed_before = tile.get("consecutive_unwatered", 0) >= 1

                if task == "harvest" and is_ripe:
                    is_match = True
                elif task == "water_urgent" and needs_water and missed_before:
                    is_match = True
                elif task == "any" and (is_ripe or needs_water):
                    is_match = True

            elif isinstance(tile, dict) and "animal" in tile:
                is_ripe = tile.get("yield_units", 0) > 0
                needs_feed = not tile.get("fed_today", True)

                if task == "harvest" and is_ripe:
                    is_match = True
                elif task == "feed" and needs_feed:
                    is_match = True

            elif isinstance(tile, dict) and tile.get("kind") == "WEED" and task == "weed":
                is_match = True

            elif (
                isinstance(tile, dict)
                and tile.get("kind") in ANIMAL_STRUCTURE_KINDS
                and "animal" not in tile
                and task == "empty_structure"
            ):
                is_match = True

            elif tile is None and task == "any" and have_any_seed:
                is_match = True

            if is_match:
                distance = abs(x - fx) + abs(y - fy)
                if best_distance is None or distance < best_distance:
                    best_distance = distance
                    best_target = (x, y)

    return best_target


def _closer_target(fx, fy, target_a, target_b):
    """Pick whichever of two (possibly-None) targets is nearer to (fx, fy)."""
    if target_a is None:
        return target_b
    if target_b is None:
        return target_a

    dist_a = abs(target_a[0] - fx) + abs(target_a[1] - fy)
    dist_b = abs(target_b[0] - fx) + abs(target_b[1] - fy)
    return target_a if dist_a <= dist_b else target_b


# ---------------------------------------------------------------------
# Animals
# ---------------------------------------------------------------------

def unit_inventory(private, unit_idx):
    """
    The specific unit's own carried inventory (private["inventories"][idx],
    idx 0 = main farmer, idx i = the (i-1)th hand - matching the engine's
    own indexing). What a unit is carrying, not what's in the shed, is what
    FEED/PLACE actually consume.
    """
    inventories = private.get("inventories") or []
    if 0 <= unit_idx < len(inventories) and isinstance(inventories[unit_idx], dict):
        return inventories[unit_idx]
    return {}


def carried_animal(inv):
    """Which ACTIVE_ANIMALS item (if any) this unit is currently carrying."""
    for animal in ACTIVE_ANIMALS:
        if inv.get(animal, 0) > 0:
            return animal
    return None


def scan_animal_structures(farm, board_size):
    """
    One pass over the board counting ACTIVE_ANIMALS structures, split into
    filled (has an animal) and unfilled (built, waiting for one). A single
    scan avoids walking the whole grid separately for every related
    decision (build gating, buy gating).
    """
    tiles = farm.get("tiles") or []
    filled = 0
    unfilled = 0
    for y in range(board_size):
        row = tiles[y] if y < len(tiles) else []
        for tile in row:
            if isinstance(tile, dict) and tile.get("kind") in ANIMAL_STRUCTURE_KINDS:
                if "animal" in tile:
                    filled += 1
                else:
                    unfilled += 1
    return filled, unfilled


def count_owned_animals(farm, private, board_size):
    """
    Total ACTIVE_ANIMALS we've committed to: bought-but-uncollected (shed),
    carried by any unit, and already placed on the board. Used to gate
    buying - without counting the in-transit ones we'd keep overbuying past
    the cap while one is still being carried to its coop.
    """
    shed = private.get("shed", {})
    total = sum(shed.get(a, 0) for a in ACTIVE_ANIMALS)
    for inv in private.get("inventories") or []:
        if isinstance(inv, dict):
            total += sum(inv.get(a, 0) for a in ACTIVE_ANIMALS)
    filled, unfilled = scan_animal_structures(farm, board_size)
    return total + filled + unfilled


def count_animals_by_species(farm, private, board_size):
    """
    How many of each ACTIVE_ANIMALS species we hold, counting the shed,
    every unit's inventory, and animals already placed on the board.

    Unlike count_owned_animals this cannot count *unfilled* structures -
    an empty pasture has no species yet. That is the point: COW and SHEEP
    share the PASTURE structure (see the ANIMALS table), so which species
    we end up with is decided at BUY_ANIMAL, never at build time.
    """
    counts = {a: 0 for a in ACTIVE_ANIMALS}
    shed = private.get("shed", {})
    for a in ACTIVE_ANIMALS:
        counts[a] += shed.get(a, 0)
    for inv in private.get("inventories") or []:
        if isinstance(inv, dict):
            for a in ACTIVE_ANIMALS:
                counts[a] += inv.get(a, 0)
    tiles = farm.get("tiles") or []
    for y in range(board_size):
        row = tiles[y] if y < len(tiles) else []
        for tile in row:
            if isinstance(tile, dict) and tile.get("kind") in ANIMAL_STRUCTURE_KINDS:
                species = tile.get("animal")
                if species in counts:
                    counts[species] += 1
    return counts


def choose_animal_to_build(farm, board_size, day, pending_builds=0):
    """
    Pick which ACTIVE_ANIMALS species to build a structure for next, or
    None if we shouldn't build one right now.

    Same season-maturity gate choose_crop() uses for seeds: a species
    whose first_yield_day can't land before day 29 is refused, the same
    way a too-slow crop is - building for it would tie up a tile and
    ANIMAL_SPEND_CAP_FRACTION of our cash for a guaranteed dead loss with
    no offsetting revenue. This gate matters as MAX_ANIMALS or
    ACTIVE_ANIMALS grows enough that a build could land late in the season.

    Also picks *which* species: the first one (in ACTIVE_ANIMALS order)
    that's both affordable and has time left to pay off, rather than
    always building whatever ACTIVE_ANIMALS[0] happens to be regardless of
    season or affordability - matters once more than one species is
    active, since the structure kind for the wrong species is a wasted
    build.

    Under the cap, and only when every structure we've already built
    already has an animal in it (stops us tying up more than one tile at a
    time waiting on the buy/pickup/place chain to catch up) - same
    affordability bar as actually buying the animal (see
    decide_animal_market_actions), so we never build ahead of our ability
    to fill it.

    `pending_builds` is how many other units have already decided to build
    one THIS SAME TURN (see choose_unit_action) - every unit sees the same
    pre-turn board, so without this a farmer plus several hands can each
    independently see "no coop built yet" and all build one in the same
    turn, blowing straight through the cap in one shot.
    """
    filled, unfilled = scan_animal_structures(farm, board_size)
    if unfilled > 0 or pending_builds > 0 or filled >= MAX_ANIMALS:
        return None

    money = farm.get("money", 0)
    remaining_days = remaining_season_days(day)
    for animal in ACTIVE_ANIMALS:
        info = ANIMALS.get(animal)
        if not info:
            continue
        cost = info.get("cost")
        first_yield_day = info.get("first_yield_day")
        if cost is None or first_yield_day is None:
            continue
        if first_yield_day > remaining_days:
            continue  # can't reach even a first harvest before season end
        if money >= cost and cost <= money * ANIMAL_SPEND_CAP_FRACTION:
            return animal
    return None


def decide_animal_market_actions(farm, private, board_size, day):
    """
    Build the list of BUY_ANIMAL / feed-safety-net BUY_PRODUCT orders for
    this turn.
    """
    actions = []
    money = farm.get("money", 0)
    remaining_days = remaining_season_days(day)

    if count_owned_animals(farm, private, board_size) < MAX_ANIMALS:
        held = count_animals_by_species(farm, private, board_size)
        affordable = []
        for animal in ACTIVE_ANIMALS:
            info = ANIMALS.get(animal)
            cost = info.get("cost") if info else None
            first_yield_day = info.get("first_yield_day") if info else None
            if cost is None or first_yield_day is None:
                continue
            if first_yield_day > remaining_days:
                continue  # can't reach even a first harvest before season end
            if cost > money or cost > money * ANIMAL_SPEND_CAP_FRACTION:
                continue
            affordable.append(animal)

        if affordable:
            # Prefer a species we hold fewest of, ties broken by
            # ACTIVE_ANIMALS order. This used to take the first affordable
            # species outright, which silently made a multi-species roster
            # impossible: ACTIVE_ANIMALS = ["SHEEP", "COW"] bought SHEEP for
            # every slot and never once a cow, byte-identical to running two
            # sheep. The recorded sheep-plus-cow dead end therefore never
            # tested a cow at all.
            #
            # It matters because the species sell into *different* markets.
            # A second sheep competes with the first for WOOL; a cow adds
            # MILK, which we currently produce zero of. Real top-ladder
            # agents run COW x5-6 plus SHEEP x3 together
            # (docs/REPLAY_ANALYSIS.md).
            #
            # No-op at MAX_ANIMALS = 1: the only purchase happens with every
            # count at zero, so the tie-break picks ACTIVE_ANIMALS[0] exactly
            # as before.
            animal = min(affordable, key=lambda a: (held.get(a, 0), ACTIVE_ANIMALS.index(a)))
            actions.append(["BUY_ANIMAL", animal, 1])
            # one purchase at a time, same cadence as seed buying

    filled, _ = scan_animal_structures(farm, board_size)
    if filled > 0 and money > 0:
        shed_wheat = private.get("shed", {}).get("WHEAT", 0)
        carried_wheat = sum(
            inv.get("WHEAT", 0) for inv in (private.get("inventories") or []) if isinstance(inv, dict)
        )
        if shed_wheat + carried_wheat < MIN_WHEAT_RESERVE_FOR_FEEDING:
            actions.append(["BUY_PRODUCT", "WHEAT", 1])

    return actions


# ---------------------------------------------------------------------
# Labour
# ---------------------------------------------------------------------

def count_pending_work(farm, board_size, day, seeds=None):
    """
    How many tiles currently need a unit standing on them: a ripe crop to
    pick, a thirsty crop to water, a weed to dig, or plantable ground we
    hold a usable seed for.

    This is the demand side of the hiring decision - hire against real
    work, not against a fixed schedule.
    """
    seeds = seeds or {}
    tiles = farm.get("tiles") or []
    have_any_seed = has_plantable_seed(seeds, day)

    work = 0
    for y in range(board_size):
        row = tiles[y] if y < len(tiles) else []
        for x in range(len(row)):
            tile = row[x]
            if isinstance(tile, dict):
                kind = tile.get("kind")
                if kind == "PLANT":
                    if is_harvestable(tile, day) or not tile.get("watered_today", True):
                        work += 1
                elif kind == "WEED":
                    work += 1
            elif tile is None and have_any_seed:
                work += 1
    return work


def decide_hire_orders(farm, board_size, day, hour, seeds=None):
    """
    Decide how many farm hands to hire this turn, as ["HIRE"] market orders.

    Hands vanish at the end of every day, so this only fires in the first
    few turns of a day: same price, far more work out of them. The count is
    driven by how much work is actually waiting, capped by MAX_HANDS_PER_DAY
    because the cost sequence is Fibonacci within a day.
    """
    if hour >= HIRE_BEFORE_HOUR:
        return []
    if remaining_season_days(day) < 0:
        return []
    if farm.get("money", 0) < MIN_MONEY_TO_HIRE:
        return []

    work = count_pending_work(farm, board_size, day, seeds)
    wanted = min(MAX_HANDS_PER_DAY, work // WORK_TILES_PER_HAND)
    already_working = len(farm.get("hands") or [])
    shortfall = max(0, wanted - already_working)

    return [["HIRE"]] * min(shortfall, MAX_HIRES_PER_TURN)


# ---------------------------------------------------------------------
# Crop selection
# ---------------------------------------------------------------------

def count_opponent_pipeline(obs):
    """
    Units of each crop the OPPONENT is about to put on the market.

    The observation carries both farms. We can see every tile they hold and
    exactly which crop is growing on it - `obs["farms"][1 - player]` - and up
    to now the agent has never once looked. Everything it knew about the
    market was its own supply plus town demand, as if it were playing
    solitaire.

    That matters because both players sell into one shared order book. A melon
    the opponent harvests on day 14 depresses the price of ours on day 14
    exactly as much as one of our own, and estimate_future_price() already
    accepts an `opponent_pipeline_supply` argument for precisely this - it has
    simply been receiving 0.

    Their shed is private, so this is what is growing only: a lower bound on
    what they will sell, and the part we can actually see.
    """
    farms = obs.get("farms") or []
    player = obs.get("player", 0)
    if len(farms) < 2:
        return {}

    opponent = farms[1 - player] or {}
    supply = {}
    for row in (opponent.get("tiles") or []):
        for tile in row:
            if isinstance(tile, dict) and tile.get("kind") == "PLANT":
                crop = tile.get("crop")
                crop_info = CROPS.get(crop) or {}
                supply[crop] = supply.get(crop, 0) + (crop_info.get("max_yield") or 1)
    return supply


def count_pipeline_supply(farm, private):
    """
    Units of each crop we are already committed to selling: everything
    growing on our own tiles, plus whatever is already in the shed.

    This is the supply that will hit the market *because of us*, and it is
    the number the planting decision has to respect. Spot price says what a
    unit fetches today; it says nothing about what it will fetch after our
    own harvest lands.
    """
    supply = {}

    for product, quantity in (private.get("shed") or {}).items():
        if quantity:
            supply[product] = supply.get(product, 0) + quantity

    for row in (farm.get("tiles") or []):
        for tile in row:
            if isinstance(tile, dict) and tile.get("kind") == "PLANT":
                crop = tile.get("crop")
                crop_info = CROPS.get(crop) or {}
                supply[crop] = supply.get(crop, 0) + (crop_info.get("max_yield") or 1)

    return supply


def choose_crop(
    farm, market_state, private, day, unlocked_shops=(), start_step=None,
    opponent_pipeline=None,
):
    """
    Pick the crop we'd most like to plant next, or None if nothing makes
    sense right now (nothing affordable/held, or nothing left has time to
    mature).

    FORWARD-PRICING EXPERIMENT (see docs/EXPERIMENT_WORKFLOW.md and the
    experiment report under experiments/). Previously scored by *today's*
    price discounted by two hand-tuned terms (a glut discount relative to
    baseline stock, and a self-supply discount shaped like 1/(1+pressure)^k).
    Both terms were approximations of the same thing pricing.py's
    estimate_future_price() now computes exactly, from the engine's own
    market_price() formula: how the price at `crop`'s current inventory
    will actually move by the time a plant started today could be sold.

        score = future_price * expected_yield / growth_days

      - future_price: estimate_future_price()'s forecast for `crop` at its
        first_yield_day horizon, given current market inventory and
        everything we're already committed to selling (count_pipeline_supply
        - unchanged from before, just fed to the real formula instead of a
        hand-rolled discount). This is why the old glut/self-supply terms
        are gone rather than kept alongside: they approximated exactly what
        this one number now computes from the real engine mechanics, and
        keeping both would double-count the same effect.
      - growth_days: how long we have to wait for the payoff, so we
        don't favor a slow crop just because its total payout is bigger.

    A crop is only considered if we already hold a seed for it, or we
    can afford to buy one - AND it can reach first_yield_day before the
    season's last day (29). Diagnosed from a real lost game: without this
    check, the agent kept planting TOMATO (first_yield_day=8) as late as
    day 29, spending seed money on plants that mathematically could never
    produce a single unit - a guaranteed loss with no offsetting revenue.

    `unlocked_shops` / `start_step` are passed straight through to
    estimate_future_price() to phase-align its town-demand simulation with
    the real game (see pricing.py) - both default to "nothing unlocked,
    turn 0" so existing callers/tests keep working unchanged.
    """
    money = farm.get("money", 0)
    inventory = market_state.get("inventory", {})
    seeds = private.get("seeds", {})
    remaining_days = remaining_season_days(day)
    pipeline = count_pipeline_supply(farm, private)
    if start_step is None:
        start_step = day * TURNS_PER_DAY

    best_crop = None
    best_score = None

    for crop in PLANTABLE_CROPS:
        crop_info = CROPS.get(crop)
        if not crop_info:
            continue  # unknown crop metadata - skip rather than guess

        seed_cost = crop_info.get("seed")
        expected_yield = crop_info.get("max_yield")
        growth_days = crop_info.get("max_yield_day")
        first_yield_day = crop_info.get("first_yield_day")
        if seed_cost is None or expected_yield is None or not growth_days:
            continue
        if first_yield_day is not None and first_yield_day > remaining_days:
            continue  # can't reach even a first harvest before season end

        have_seed = seeds.get(crop, 0) > 0
        can_afford = money >= seed_cost
        if not have_seed and not can_afford:
            continue  # can't get hold of this crop right now

        # Default to I0 (10,000), not 0: every product is always present in
        # a real market observation (_new_market initialises all of them),
        # so an *actual* zero-inventory reading never happens - "missing"
        # only occurs in a malformed/partial obs, where assuming normal
        # supply is far safer than assuming total scarcity. The latter used
        # to feed near-zero inventory into a hinge-shaped below_func
        # (CARROT/TOMATO), which explodes hard near I0 - see
        # notebooks/pricing_analysis_v0.ipynb section 2b.
        stock = inventory.get(crop, 10000)
        turns_ahead = (first_yield_day or 0) * TURNS_PER_DAY
        forecast = estimate_future_price(
            crop,
            stock,
            turns_ahead=turns_ahead,
            our_pipeline_supply=pipeline.get(crop, 0),
            # What they are growing counts against the same order book as
            # what we are growing. Their shed is private, so this is a lower
            # bound - but a measured one, not an assumption.
            opponent_pipeline_supply=(opponent_pipeline or {}).get(crop, 0),
            unlocked_shops=unlocked_shops,
            start_step=start_step,
        )
        future_price = forecast["future_price"]

        score = future_price * expected_yield / growth_days

        if best_score is None or score > best_score:
            best_score = score
            best_crop = crop

    return best_crop


# ---------------------------------------------------------------------
# Market decisions
# ---------------------------------------------------------------------

def should_sell(product, quantity, market_state):
    """
    True if we should sell `quantity` units of `product` right now.

    Kept deliberately simple and easy to tune: sell only when the
    current price clears a fixed per-product threshold. We do NOT sell
    everything blindly just because we have it - a poor price means we
    hold and wait.
    """
    if quantity <= 0:
        return False

    price = market_state.get("prices", {}).get(product, 0)
    threshold = SELL_PRICE_THRESHOLDS.get(product, DEFAULT_SELL_THRESHOLD)
    return price >= threshold


def seed_restock_quantity(crop, farm, private):
    """
    How many units of `crop` seed to buy right now as a single BUY_SEED
    order, or 0 to buy none.

    Two gates, both explained in full at SEED_REBUY_TRIGGER /
    MIN_CASH_RESERVE_FOR_SEED_BUYING above:

      1. Only fires once we're fully out of the crop's seed (not merely
         under MAX_SEED_STOCKPILE) - this is the cadence fix. A single
         BUY_SEED order can carry a quantity (kaggriculture.py:602-603,
         673-678 process it one unit at a time within the turn, same
         mechanic the wheat BUY_PRODUCT batch already uses), so this tops
         the stockpile all the way back up to MAX_SEED_STOCKPILE in one
         order instead of dribbling out a fresh full-price purchase every
         single turn stock is consumed.
      2. Each unit in the batch is checked against SEED_SPEND_CAP_FRACTION
         and MIN_CASH_RESERVE_FOR_SEED_BUYING against the running balance
         *as if* the earlier units in this same batch had already been
         bought - so a batch can never spend more than we can actually
         afford, and never leaves the wheat safety net's cash drawer
         empty.
    """
    seeds = private.get("seeds", {})
    held = seeds.get(crop, 0)
    if held > SEED_REBUY_TRIGGER:
        return 0

    crop_info = CROPS.get(crop)
    if not crop_info:
        return 0
    seed_cost = crop_info.get("seed")
    if not seed_cost:
        return 0

    money = farm.get("money", 0)
    wanted = MAX_SEED_STOCKPILE - held

    quantity = 0
    while quantity < wanted:
        if seed_cost > money:
            break
        if seed_cost > money * SEED_SPEND_CAP_FRACTION:
            break  # would eat too much of our (running) cash reserve
        remaining_after = money - seed_cost
        if remaining_after < MIN_CASH_RESERVE_FOR_SEED_BUYING:
            break  # would starve the wheat safety net
        money = remaining_after
        quantity += 1

    return quantity


def decide_market_actions(
    farm, private, market_state, day, reserved_wheat=0, unlocked_shops=(), start_step=None,
    opponent_pipeline=None,
):
    """Build the list of ["SELL", ...] / ["BUY_SEED", ...] actions for this turn."""
    actions = []
    already_selling = set()

    # Sell anything sitting in the shed that's fetching a good price. Capped
    # per product (see MAX_SELL_PER_TURN) so a big harvest of a premium good
    # doesn't dump the whole stack into one price-crashing order.
    shed = private.get("shed", {})
    inventory = market_state.get("inventory", {})
    liquidating = day >= LIQUIDATION_START_DAY

    for product, quantity in shed.items():
        # Fertilizer is an input, not produce - and with a Goose on the farm
        # it arrives free via COLLECT_FERTILIZER. Its price clears the default
        # sell threshold comfortably, so without this guard the agent dumps
        # every unit the animal makes (and buys more, then sells those too:
        # 715 units round-tripped in one measured season with zero reaching a
        # plant). Hold it for the crops and only liquidate at season end,
        # when leftover stock scores nothing anyway.
        if product == "FERTILIZER" and not liquidating:
            continue

        # Hold back the wheat earmarked for feeding. Wheat is animal feed,
        # and an animal that misses two consecutive days escapes for good -
        # so selling the feed can permanently destroy a 300-cost asset for
        # a few dollars of wheat. The reserve is kept even while
        # liquidating: the animal still produces right up to the last day.
        sell_quantity = quantity
        if product == "WHEAT":
            sell_quantity = max(0, quantity - reserved_wheat)

        # Near the end of the season, price thresholds stop mattering:
        # unsold stock scores nothing, so any sale beats holding out.
        if sell_quantity > 0 and (
            liquidating or should_sell(product, sell_quantity, market_state)
        ):
            # FORWARD-PRICING EXPERIMENT: the *quantity* sold this turn now
            # comes from recommend_sell_quantity() (pricing.py) instead of a
            # blind min(sell_quantity, cap). It walks the same per-unit price
            # path the engine actually uses and stops before the price would
            # drop under our threshold - MAX_SELL_PER_TURN is still respected
            # as a hard ceiling either way. should_sell()'s yes/no gate is
            # unchanged; this only changes how much we sell once it says yes.
            #
            # Liquidating still means "sell regardless of price" - unsold
            # stock scores nothing at season end - so the floor price is the
            # only bar there, which makes this numerically identical to the
            # old min(sell_quantity, cap) in that mode (see
            # experiments/forward_pricing_experiment.py's report).
            cap = MAX_SELL_PER_TURN.get(product, quantity)
            min_price = (
                PRICE_FLOOR
                if liquidating
                else SELL_PRICE_THRESHOLDS.get(product, DEFAULT_SELL_THRESHOLD)
            )
            amount = recommend_sell_quantity(
                product,
                inventory.get(product, 10000),
                sell_quantity,
                min_acceptable_price=min_price,
                max_per_turn=cap,
            )
            if amount > 0:
                actions.append(["SELL", product, amount])
                already_selling.add(product)

    # Shed is nearly full: anything not already being sold above would just
    # be discarded once the cap hits. Force a sale (still capped, so we
    # don't crash a premium good's price on the way out) rather than let it
    # evaporate for free.
    shed_total = sum(shed.values())
    if shed_total >= SHED_FORCE_SELL_THRESHOLD:
        for product, quantity in shed.items():
            # Same exclusion as the main sell loop - the overflow valve
            # must not become the back door that dumps the fertilizer.
            # Fertilizer is an input, not produce - and with a Goose on the farm
            # it arrives free via COLLECT_FERTILIZER. Its price clears the default
            # sell threshold comfortably, so without this guard the agent dumps
            # every unit the animal makes (and buys more, then sells those too:
            # 715 units round-tripped in one measured season with zero reaching a
            # plant). Hold it for the crops and only liquidate at season end,
            # when leftover stock scores nothing anyway.
            if product == "FERTILIZER" and not liquidating:
                continue

            if product in already_selling or quantity <= 0:
                continue
            sell_quantity = quantity
            if product == "WHEAT":
                sell_quantity = max(0, quantity - reserved_wheat)
            if sell_quantity <= 0:
                continue
            cap = MAX_SELL_PER_TURN.get(product, quantity)
            amount = recommend_sell_quantity(
                product,
                inventory.get(product, 10000),
                sell_quantity,
                min_acceptable_price=PRICE_FLOOR,
                max_per_turn=cap,
            )
            if amount > 0:
                actions.append(["SELL", product, amount])

    # Buy exactly one seed of our preferred next crop, if it makes sense.
    preferred_crop = choose_crop(
        farm, market_state, private, day, unlocked_shops=unlocked_shops,
        start_step=start_step, opponent_pipeline=opponent_pipeline,
    )
    if preferred_crop:
        seed_quantity = seed_restock_quantity(preferred_crop, farm, private)
        if seed_quantity > 0:
            actions.append(["BUY_SEED", preferred_crop, seed_quantity])

    # Fertilizer, but only against ongoing crops we actually have in the
    # ground - it's the one product a unit has to fetch from the shed by
    # hand, so buying speculatively wastes both money and turns. A Goose
    # supplies it free, so in practice this only tops up when the crops
    # want more than the animal produced.
    #
    # Leave this rule alone in BOTH directions - it has been pushed each way
    # and both lost.
    #
    # It looks like churn: from LIQUIDATION_START_DAY the sell loop stops
    # exempting FERTILIZER, so we buy and sell the same product on the same
    # day (111 bought, 137 sold in one measured season). Blocking the buy
    # during liquidation lost -529 head to head, winning 1 of 16 matches.
    #
    # It also looks like arbitrage, and it is not. Buy and sell both average
    # $97.0; the round trip on those 111 units nets -$4. The apparent profit
    # is the 26 units the Goose produced free. Fertilizer is linear both ways
    # with target 0.40, so price = 100 - 0.2 x excess and every unit we trade
    # moves the price $0.20 against us, while sell price is quoted pre-sell
    # and buy price post-buy - a same-day round trip pays and receives the
    # same number by construction. Trading it deliberately (buy <=97 in
    # batches, release >=99) bought 573 units at 97.8 and sold 591 at 97.0,
    # losing -1,486 head to head, winning 0 of 16.
    #
    # See CLAUDE.md, "There is no fertilizer arbitrage".
    if day <= FERTILIZER_LAST_USEFUL_DAY:
        held = shed.get("FERTILIZER", 0) + sum(
            (carried or {}).get("FERTILIZER", 0)
            for carried in (private.get("inventories") or [])
            if isinstance(carried, dict)
        )
        if held < MAX_FERTILIZER_STOCK:
            fertilizer_price = market_state.get("prices", {}).get("FERTILIZER", 0)
            wanted = sum(
                1
                for row in (farm.get("tiles") or [])
                for tile in row
                if wants_fertilizer(tile, day)
            )
            if wanted > held and fertilizer_price and farm.get("money", 0) >= fertilizer_price * 2:
                actions.append(["BUY_PRODUCT", "FERTILIZER", 1])

    return actions


# ---------------------------------------------------------------------
# Farmer decision
# ---------------------------------------------------------------------

def choose_unit_action(
    state, ux, uy, unit_idx, claimed=None, pending_builds=None, feed_claimed=None,
    plant_budget=None,
):
    """
    Decide the single action for one unit - the main farmer or a hired
    hand - standing at (ux, uy), following the fixed priority order
    described at the top of this file.

    `unit_idx` is this unit's index into private["inventories"] (0 = main
    farmer, i = the (i-1)th hand), needed to know what it's personally
    carrying - FEED and PLACE consume from that, not the shed.

    `claimed` is the set of (x, y) tiles other units have already taken
    this turn, and whatever this unit settles on is added to it. Without
    that bookkeeping every hand would independently pick the same nearest
    target and the whole crew would walk to one tile while the rest of
    the farm went to weeds - which defeats the point of hiring them.

    `pending_builds` is a shared one-item counter ([n]) of how many
    structures other units have already decided to build this same turn.
    Every unit sees the same pre-turn board, so without this a farmer plus
    several hands could each independently see "no coop built yet" and all
    build one in the same turn, blowing straight through MAX_ANIMALS.

    `plant_budget` is a shared {crop: remaining_seed} dict, decremented as
    each unit commits to a PLANT this turn - the seed-overcommit fix. Every
    unit sees the same pre-turn `seeds` count, so without a shared budget,
    several units standing on empty tiles in the same turn could each
    independently decide to plant the same understocked crop; the engine
    then drops ALL of that turn's PLANT requests for the crop, not just the
    excess, once demand exceeds held seed (kaggriculture.py:920-931) - so
    every involved unit's turn is wasted, not just the surplus ones.
    Defaults to a fresh copy of `seeds` when not supplied, so a single
    standalone call (e.g. in a test) behaves exactly as before.
    """
    claimed = claimed if claimed is not None else set()
    pending_builds = pending_builds if pending_builds is not None else [0]
    feed_claimed = feed_claimed if feed_claimed is not None else set()

    farm = state["farm"]
    if not farm:
        return ["PASS"]

    board_size = state["board_size"]
    day = state["day"]
    private = state["private"]
    seeds = private.get("seeds", {})
    plant_budget = plant_budget if plant_budget is not None else dict(seeds)
    inv = unit_inventory(private, unit_idx)
    tile = get_tile_at(farm, ux, uy)

    # Another unit already acted on this tile this turn. Every tile action is
    # either once-per-day (WATER, CARE, FEED) or consumes its target outright
    # (HARVEST, DIG, PLANT, COLLECT_FERTILIZER), so a second unit acting here
    # spends its whole turn on an engine no-op. Units decide from a shared
    # observation snapshot, so without this they all see `cared_today: False`
    # and all pick CARE - measured at 76 CARE actions across only 30 distinct
    # days, i.e. 46 turns burned, with multiple units caring for the same
    # goose on 30 separate turns.
    #
    # Standing in for the tile with a sentinel makes the whole local-action
    # ladder below fall through (it is all `isinstance(tile, dict)` and
    # `tile is None` checks), so the unit goes and finds real work instead.
    if (ux, uy) in claimed:
        tile = "TAKEN"

    is_animal_tile = isinstance(tile, dict) and "animal" in tile

    def act_here(action):
        """Take an action on our own tile, and reserve it against other units."""
        claimed.add((ux, uy))
        return action

    def walk_to(target):
        """Step toward a target and reserve it, so no one else heads there."""
        direction = step_toward(ux, uy, target[0], target[1])
        if not direction:
            return None
        claimed.add((target[0], target[1]))
        return [direction]

    # 1. Feed an animal before any harvest/care task. A Goose with
    # consecutive_unfed == 1 can escape at the next day boundary, so this
    # safety action must outrank even a ready harvest.
    if is_animal_tile and not tile.get("fed_today"):
        if inv.get("WHEAT", 0) > 0:
            feed_claimed.add((ux, uy))
            return act_here(["FEED"])

    # 2. Harvest a ripe crop or an animal whose held yield is close to its
    # capacity. Animal goods do not decay, so do not spend one action
    # harvesting a single Egg every day.
    if isinstance(tile, dict) and tile.get("kind") == "PLANT" and is_harvestable(tile, day):
        return act_here(["HARVEST"])
    if is_animal_tile:
        animal = ANIMALS.get(tile.get("animal"), {})
        max_held = animal.get("max_held", 1)
        held = tile.get("yield_units", 0)
        if held >= max_held:
            return act_here(["HARVEST"])

        # Fertilizer is a separate non-stacking daily output. Collect it
        # before care/harvest whenever the animal has room for another yield.
        if tile.get("fertilizer_available"):
            return act_here(["COLLECT_FERTILIZER"])

        # Leave enough room for the next Goose production, but cash out near
        # season end so output cannot be stranded on the tile.
        if held > 0 and (held >= max_held - 2 or day >= SEASON_DAYS - 2):
            return act_here(["HARVEST"])

    # 3. Water a crop under our feet, or care for an already-fed animal under
    #    feet. Feed always wins over care when only one action is possible:
    #    a missed feeding is a permanent loss (the animal escapes for good
    #    - see _daily_refresh_animals), care is just a bonus multiplier.
    if isinstance(tile, dict) and tile.get("kind") == "PLANT" and not tile.get("watered_today", True):
        return act_here(["WATER"])
    if is_animal_tile:
        if not tile.get("cared_today"):
            return act_here(["CARE"])

    # 3b. Fertilise the ongoing crop under our feet, if we're carrying any.
    #     Free in movement terms - we are already standing here - and worth
    #     several hundred on a tomato or strawberry. Ranked below watering
    #     because the bonus only pays on days the plant is watered anyway,
    #     so watering first is strictly better when we can only do one.
    if inv.get("FERTILIZER", 0) > 0 and wants_fertilizer(tile, day):
        return act_here(["FERTILIZE"])

    # 4. Place a carried animal on the empty structure under our feet.
    animal_in_hand = carried_animal(inv)
    if animal_in_hand and isinstance(tile, dict) and "animal" not in tile:
        structure = ANIMALS.get(animal_in_hand, {}).get("structure")
        if structure and tile.get("kind") == structure:
            return act_here(["PLACE", animal_in_hand])

    # 5. Shed errands: collect a bought animal waiting for its home, or
    #    wheat we need to go feed a starving animal elsewhere.
    if is_shed_adjacent(ux, uy, board_size):
        shed = private.get("shed", {})
        if animal_in_hand is None:
            _, unfilled = scan_animal_structures(farm, board_size)
            if unfilled > 0:
                for animal in ACTIVE_ANIMALS:
                    if shed.get(animal, 0) > 0:
                        return act_here(["PICKUP", animal, 1])
        if inv.get("WHEAT", 0) <= 0 and shed.get("WHEAT", 0) > 0:
            if find_nearest_target(farm, board_size, ux, uy, "feed", day, exclude=claimed):
                # Collect several days of feed in one trip. Feeding needs
                # wheat in the acting unit's own inventory, so picking up a
                # single grain means a fresh shed round-trip for every meal.
                return act_here(
                    ["PICKUP", "WHEAT", min(shed.get("WHEAT", 0), WHEAT_CARRY_BATCH)]
                )

    # 6. Something urgent elsewhere - a ripe crop/animal, a crop about to
    #    weed out, or an animal about to escape - beats anything below.
    #    Preventing a loss is worth more than reclaiming one already lost.
    #    If the winning target needs feeding and we're not carrying wheat,
    #    detour to the shed instead of arriving empty-handed (only if the
    #    shed actually has wheat - otherwise there's nothing to do about it
    #    this turn).
    # Feed is a daily errand, not a rescue. An earlier version only walked to
    # an animal that had ALREADY missed a day, which self-oscillates: feeding
    # resets consecutive_unfed, so the next day never looks urgent and the
    # animal is fed every OTHER day - 15 meals in a 30-day season, measured.
    # That left the Goose permanently one blocked turn from escaping for good,
    # and threw away most of the CARE bank, which only accrues on days the
    # animal was also fed and is discarded unpaid if its production day is not
    # (see _daily_refresh_animals in the engine).
    #
    # Feed is also a separate reservation class. A crop worker without Wheat
    # must not claim the Goose tile for HARVEST/WATER movement before a
    # different unit carrying Wheat has a chance to reach it.
    feed_target = find_nearest_target(farm, board_size, ux, uy, "feed", day, exclude=set())
    if feed_target in feed_claimed:
        feed_target = None
    if feed_target:
        if inv.get("WHEAT", 0) <= 0:
            if private.get("shed", {}).get("WHEAT", 0) > 0:
                moved = walk_to(nearest_shed_tile(ux, uy, board_size))
                if moved:
                    return moved
        else:
            feed_claimed.add(feed_target)
            moved = walk_to(feed_target)
            if moved:
                return moved

    non_feed_exclude = set(claimed)
    if feed_target is not None:
        non_feed_exclude.add(feed_target)
    harvest_target = find_nearest_target(farm, board_size, ux, uy, "harvest", day, exclude=non_feed_exclude)
    water_target = find_nearest_target(farm, board_size, ux, uy, "water_urgent", day, exclude=non_feed_exclude)
    urgent_target = _closer_target(ux, uy, harvest_target, water_target)
    if urgent_target:
        moved = walk_to(urgent_target)
        if moved:
            return moved

    # 7. Carrying an animal we haven't placed yet - go find it a home.
    if animal_in_hand:
        structure_target = find_nearest_target(
            farm, board_size, ux, uy, "empty_structure", day, exclude=claimed
        )
        if structure_target:
            moved = walk_to(structure_target)
            if moved:
                return moved

    # 8. Reclaim a weed under our feet - free, and turns dead land back into
    #    something we can plant again instead of losing it for the rest of
    #    the season.
    if isinstance(tile, dict) and tile.get("kind") == "WEED":
        return act_here(["DIG"])

    # 9. Empty ground under our feet: build a coop/pasture if we're still
    #    growing the animal side of the farm and don't already have one
    #    waiting for a tenant, otherwise plant a crop.
    if tile is None:
        animal_to_build = choose_animal_to_build(farm, board_size, day, pending_builds[0])
        if animal_to_build:
            pending_builds[0] += 1
            structure = ANIMALS[animal_to_build]["structure"]
            return act_here([f"BUILD_{structure}"])
        crop = choose_crop(
            farm,
            state["market_state"],
            private,
            day,
            unlocked_shops=state.get("unlocked_shops", ()),
            start_step=state.get("step"),
            opponent_pipeline=state.get("opponent_pipeline"),
        )
        if crop and plant_budget.get(crop, 0) > 0:
            plant_budget[crop] -= 1
            return act_here(["PLANT", crop])

    # 10. Fertilizer logistics. Fertilizer reaches the shed either by
    #     purchase or free from the Goose, but FERTILIZE spends from the
    #     unit's own inventory - so this is a collect-then-deliver errand.
    #     Deliberately ranked below every crop-upkeep step above: a plant
    #     that dies unwatered costs far more than a fertilizer bonus is
    #     worth, and the bonus only pays on watered days regardless.
    shed_fertilizer = (private.get("shed") or {}).get("FERTILIZER", 0)

    if inv.get("FERTILIZER", 0) > 0:
        fertilize_target = find_fertilizer_target(
            farm, board_size, ux, uy, day, exclude=claimed
        )
        if fertilize_target:
            moved = walk_to(fertilize_target)
            if moved:
                return moved

    elif shed_fertilizer > 0 and find_fertilizer_target(
        farm, board_size, ux, uy, day, exclude=claimed
    ):
        # Collect a batch so one trip serves several plants.
        if is_shed_adjacent(ux, uy, board_size):
            return act_here(
                ["PICKUP", "FERTILIZER", min(shed_fertilizer, FERTILIZER_CARRY_BATCH)]
            )
        moved = walk_to(nearest_shed_tile(ux, uy, board_size))
        if moved:
            return moved

    # 11. Reclaim the nearest weed elsewhere - dead land is a permanent loss
    #    until it's dug back to plantable ground, so don't just leave it.
    weed_target = find_nearest_target(
        farm, board_size, ux, uy, "weed", day, exclude=claimed
    )
    if weed_target:
        moved = walk_to(weed_target)
        if moved:
            return moved

    # 12. Nothing to do right here - walk toward the closest useful tile.
    fallback_target = find_nearest_target(
        farm, board_size, ux, uy, "any", day, seeds, exclude=claimed
    )
    if fallback_target and fallback_target != (ux, uy):
        moved = walk_to(fallback_target)
        if moved:
            return moved

    # 13. Genuinely nothing useful to do.
    return ["PASS"]


def choose_farmer_action(
    state, claimed=None, pending_builds=None, feed_claimed=None, plant_budget=None
):
    """Our main farmer's action - the shared unit logic, anchored at the farmer."""
    farm = state.get("farm")
    if not farm:
        return ["PASS"]

    farmer_pos = farm.get("farmer")
    if not farmer_pos or len(farmer_pos) != 2:
        return ["PASS"]

    return choose_unit_action(
        state, farmer_pos[0], farmer_pos[1], 0, claimed, pending_builds, feed_claimed,
        plant_budget,
    )


# ---------------------------------------------------------------------
# Agent entry point
# ---------------------------------------------------------------------

def nikaangukia_meroni(obs):
    """
    Washamba Bots' V1 agent.

    Always returns a well-formed action dict, even for a missing or
    malformed observation - if anything goes wrong we fall back to a
    safe PASS instead of crashing.
    """
    try:
        state = extract_state(obs)
        farm = state["farm"]
        if not farm:
            return {"farmer": ["PASS"], "hands": [], "market": []}

        board_size = state["board_size"]
        day = state["day"]
        hour = state["hour"]
        private = state["private"]
        seeds = private.get("seeds", {})

        # One shared claim set across every unit this turn, so the farmer and
        # each hand pick different tiles instead of piling onto the same one.
        # pending_builds is the same idea for coop/pasture construction, and
        # plant_budget is the same idea for PLANT: a shared {crop: seeds
        # left} counter, decremented as each unit commits to a planting, so
        # at most as many units plant a crop this turn as we hold seed for -
        # see choose_unit_action's docstring for why an uncoordinated PLANT
        # decision wastes every involved unit's turn, not just the surplus.
        claimed = set()
        pending_builds = [0]
        feed_claimed = set()
        plant_budget = dict(seeds)
        farmer_action = choose_farmer_action(
            state, claimed, pending_builds, feed_claimed, plant_budget
        )
        hands_actions = [
            choose_unit_action(
                state, hand[0], hand[1], idx + 1, claimed, pending_builds, feed_claimed,
                plant_budget,
            )
            for idx, hand in enumerate(farm.get("hands") or [])
            if isinstance(hand, (list, tuple)) and len(hand) == 2
        ]

        # Hires go first: they're a few dollars each and multiply how much
        # work the crew gets through, so they're the last orders we'd want
        # silently dropped if we ever brush the per-turn cap. Animal orders
        # go last - buying one or topping up feed reserve is less
        # time-critical turn-to-turn than hiring or selling at a good price.
        market = decide_hire_orders(farm, board_size, day, hour, seeds)
        filled_animals, _ = scan_animal_structures(farm, board_size)
        reserved_wheat = filled_animals * MIN_WHEAT_RESERVE_FOR_FEEDING
        market += decide_market_actions(
            farm,
            private,
            state["market_state"],
            day,
            reserved_wheat=reserved_wheat,
            unlocked_shops=state["unlocked_shops"],
            start_step=state["step"],
            opponent_pipeline=state.get("opponent_pipeline"),
        )
        market += decide_animal_market_actions(farm, private, board_size, day)

        return {
            "farmer": farmer_action,
            "hands": hands_actions,
            "market": market[:MAX_MARKET_ORDERS_PER_TURN],
        }
    except Exception:
        # Last line of defense: an agent that crashes forfeits the match,
        # so an unexpected observation shape should always fall back to
        # a harmless PASS rather than raising.
        return {"farmer": ["PASS"], "hands": [], "market": []}


# The framework picks the LAST callable in this module's namespace - not a
# function named `agent` (kaggle_environments/agent.py:64). Anything callable
# defined below this line silently becomes the submission instead, the episode
# still reports DONE, every action is discarded as invalid, and the agent
# finishes on exactly its starting money. Keep this binding last.
agent = nikaangukia_meroni
