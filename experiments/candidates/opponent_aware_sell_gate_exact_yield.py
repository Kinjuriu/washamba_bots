"""
Follow-up to experiments/candidates/opponent_aware_sell_gate.py (see
experiments/opponent_aware_sell_gate_report.md), driven by
experiments/opponent_supply_forecast_audit.md's finding that
`count_opponent_pipeline` (opponent standing crop counted at a flat
`crop_info["max_yield"]` the instant any tile of that crop exists) is a
much cruder signal than what's actually observable: the opponent's real,
exact `tile["yield_units"]` - directly readable from `obs["farms"]`,
which is the literal same shared object for both players
(kaggriculture.py:271/952), and exactly the quantity `HARVEST` would move
into their inventory this instant (kaggriculture.py:446-462).

ONE conceptual change from the previous candidate, and only one: the
opponent-supply number fed into the SELL gate's override is now
`exact_opponent_standing_yield(obs)` instead of `count_opponent_pipeline(obs)`.
Nothing else moves:

  - should_sell_opponent_aware's mechanism (should_sell(...) OR a
    short-horizon sell-now-vs-wait comparison via
    pricing_v1.compare_immediate_vs_delayed_selling, OPPONENT_AWARE_HORIZON_TURNS
    unchanged at one day) is copied verbatim from the previous candidate.
  - SELL_PRICE_THRESHOLDS, MAX_SELL_PER_TURN, LIQUIDATION_START_DAY,
    SHED_FORCE_SELL_THRESHOLD: untouched, read from `base` exactly as
    before.
  - PLANTING IS UNTOUCHED. choose_crop is called from two places in the
    unpatched code (choose_unit_action's own PLANT branch, and
    decide_market_actions's BUY_SEED restock call) and both read
    `state["opponent_pipeline"]` / the `opponent_pipeline` parameter,
    which this module never modifies - both call sites keep seeing
    exactly what `count_opponent_pipeline` (the OLD, unmodified function)
    produces. See "how the exact-yield value reaches the sell gate
    without touching planting" below for the mechanism that keeps this
    true.
  - Concurrent-selling mechanics, quantity sizing (recommend_sell_quantity),
    land/animals/labor: all untouched, same as the previous candidate.

HOW THE EXACT-YIELD VALUE REACHES THE SELL GATE WITHOUT TOUCHING PLANTING:

`decide_market_actions` never receives `obs` - only the pre-extracted
`opponent_pipeline` dict, computed once per turn inside `extract_state`
via `count_opponent_pipeline(obs)` (main.py:1014) and threaded to BOTH
choose_crop call sites. Widening `opponent_pipeline` itself would
therefore also change planting - exactly what this experiment is
required not to do. So instead of touching `opponent_pipeline`, this
module wraps `base.count_opponent_pipeline` (the function `extract_state`
already calls, unmodified, once per turn) with a thin wrapper that:

  1. computes `exact_opponent_standing_yield(obs)` from the same `obs`
     count_opponent_pipeline was just given, and stashes it in a
     module-level cache (`_last_exact_opponent_yield`);
  2. calls through to the ORIGINAL, unpatched `count_opponent_pipeline`
     and returns its result completely unchanged.

Because `extract_state` runs exactly once per turn, as the first line of
`nikaangukia_meroni`, strictly before `decide_market_actions` is called
in that same turn (verified by reading main.py:2420 vs main.py:2469), the
cache always holds the correct turn's value by the time the sell gate
below reads it - and `state["opponent_pipeline"]` (what both choose_crop
call sites see) is provably byte-identical to the unpatched baseline,
since the wrapped function's return value is untouched.

ACTIVATION INSTRUMENTATION: every time the override is actually evaluated
(baseline said no, not liquidating), a record is appended to
ACTIVATION_LOG - see experiments/opponent_aware_sell_gate_exact_yield_report.md
section 6 for what's done with it. This candidate is not meant to be fast;
it's meant to be inspectable.

Usage:
    .venv/Scripts/python.exe experiments/candidates/opponent_aware_sell_gate_exact_yield.py   # self-test
    .venv/Scripts/python.exe experiments/selfplay_agent.py experiments/candidates/opponent_aware_sell_gate_exact_yield.py 6
    .venv/Scripts/python.exe experiments/head_to_head.py experiments/candidates/opponent_aware_sell_gate_exact_yield.py main.py 6
    .venv/Scripts/python.exe experiments/paired_compare.py main.py experiments/candidates/opponent_aware_sell_gate_exact_yield.py
"""
import os
import sys


def _find_repo_root():
    """Same defensive walk-up as the previous candidate - see its
    docstring for why a fixed dirname()-hop-count fallback is unsafe
    here."""
    candidates = []
    if "__file__" in dir():
        this_dir = os.path.dirname(os.path.abspath(__file__))
        candidates.append(os.path.abspath(os.path.join(this_dir, "..", "..")))
    here = os.getcwd()
    for _ in range(4):
        candidates.append(here)
        here = os.path.dirname(here)
    for c in candidates:
        if os.path.isfile(os.path.join(c, "main.py")):
            return c
    return os.getcwd()


_ROOT = _find_repo_root()
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import main as base  # noqa: E402
import pricing_v1  # noqa: E402

OPPONENT_AWARE_HORIZON_TURNS = base.DEFAULT_TURNS_PER_DAY  # unchanged from the previous candidate

# --- side channel: exact-yield opponent supply, cached once per turn ------

_last_exact_opponent_yield = {}
_original_count_opponent_pipeline = base.count_opponent_pipeline


def exact_opponent_standing_yield(obs):
    """The one conceptual change. Mirrors count_opponent_pipeline's shape
    exactly (same loop, same `farms[1-player]["tiles"]` source, verified
    directly observable in experiments/opponent_supply_forecast_audit.md
    section 1) but sums the tile's real `yield_units` instead of a flat
    `crop_info["max_yield"]` per tile - the exact quantity HARVEST would
    move to the opponent's inventory right now, not a ceiling assumed the
    instant any tile of that crop exists."""
    farms = obs.get("farms") or []
    player = obs.get("player", 0)
    if len(farms) < 2:
        return {}
    opponent = farms[1 - player] or {}
    supply = {}
    for row in (opponent.get("tiles") or []):
        for tile in row:
            if isinstance(tile, dict) and tile.get("kind") == "PLANT":
                supply[tile.get("crop")] = supply.get(tile.get("crop"), 0) + tile.get("yield_units", 0)
    return supply


def _count_opponent_pipeline_and_cache_exact_yield(obs):
    """Wraps the ORIGINAL count_opponent_pipeline: computes and caches the
    exact-yield reading as a side effect, then returns the original
    function's result completely unchanged, so state["opponent_pipeline"]
    - and therefore both choose_crop call sites, i.e. planting - stays
    byte-identical to the unpatched baseline."""
    global _last_exact_opponent_yield
    _last_exact_opponent_yield = exact_opponent_standing_yield(obs)
    return _original_count_opponent_pipeline(obs)


base.count_opponent_pipeline = _count_opponent_pipeline_and_cache_exact_yield


# --- activation instrumentation -------------------------------------------

ACTIVATION_LOG = []


def _log_activation(**record):
    ACTIVATION_LOG.append(record)


# --- the sell gate, and the one line inside it that changed ---------------

def should_sell_opponent_aware_exact_yield(
    product, quantity, market_state, opponent_units, day,
    unlocked_shops=(), start_step=None, log=False,
):
    """Byte-identical mechanism to the previous candidate's
    should_sell_opponent_aware - only the caller now passes an
    exact-yield-derived opponent_units instead of a max_yield-derived
    one. See that module for the isolation argument (short-circuits on
    the unmodified should_sell first; no-op whenever opponent_units<=0).

    Single source of truth for the gate decision - decide_market_actions
    below calls this directly rather than re-deriving the comparison
    inline, so the activation log (when log=True) can never silently
    diverge from what actually decided the sale. Logs only when this
    function is reached with the baseline already having said no (the
    only case decide_market_actions ever calls it for), which is exactly
    "the override was evaluated" per the task's activation-diagnostics
    requirement.
    """
    baseline_says_sell = base.should_sell(product, quantity, market_state)
    if baseline_says_sell:
        return True
    if quantity <= 0:
        return False

    inventory = market_state.get("inventory", {}).get(product, 10000)
    if start_step is None:
        start_step = day * base.DEFAULT_TURNS_PER_DAY
    spot_price = market_state.get("prices", {}).get(product, 0)
    sell_threshold = base.SELL_PRICE_THRESHOLDS.get(product, base.DEFAULT_SELL_THRESHOLD)

    if opponent_units <= 0:
        if log:
            _log_activation(
                day=day, product=product, opponent_units=opponent_units,
                our_shed_quantity=quantity, spot_price=spot_price,
                sell_threshold=sell_threshold, forecast_price_per_unit=None,
                revenue_now=None, revenue_delayed=None, fired=False,
                signal_available=False,
            )
        return False

    comparison = pricing_v1.compare_immediate_vs_delayed_selling(
        product,
        inventory,
        quantity,
        day,
        OPPONENT_AWARE_HORIZON_TURNS,
        our_pipeline_supply=0,
        opponent_pipeline_supply=opponent_units,
        unlocked_shops=unlocked_shops,
        start_step=start_step,
    )
    fired = not comparison["delay_is_better"]
    if log:
        _log_activation(
            day=day, product=product, opponent_units=opponent_units,
            our_shed_quantity=quantity, spot_price=spot_price,
            sell_threshold=sell_threshold,
            forecast_price_per_unit=comparison["revenue_delayed_per_unit"],
            revenue_now=comparison["revenue_now"],
            revenue_delayed=comparison["revenue_delayed"],
            fired=fired, signal_available=True,
        )
    return fired


def _decide_market_actions_opponent_aware_exact_yield(
    farm, private, market_state, day, reserved_wheat=0, unlocked_shops=(), start_step=None,
    opponent_pipeline=None,
):
    """Verbatim copy of the previous candidate's
    _decide_market_actions_opponent_aware, with exactly one substitution:
    the override's opponent-units source is
    `_last_exact_opponent_yield.get(product, 0)` (the side-channel cache,
    refreshed this turn by the count_opponent_pipeline wrapper above)
    instead of `opponent_pipeline.get(product, 0)`. The `opponent_pipeline`
    parameter itself is still accepted and still forwarded to
    base.choose_crop below completely unchanged - that call site is the
    BUY_SEED restock decision, part of planting, out of scope for this
    experiment. Everything else - FERTILIZER/WHEAT-reserve exclusions,
    SHED_FORCE_SELL_THRESHOLD overflow loop, min_price bookkeeping,
    recommend_sell_quantity's call - is character-for-character the same
    as the previous candidate."""
    actions = []
    already_selling = set()

    shed = private.get("shed", {})
    inventory = market_state.get("inventory", {})
    liquidating = day >= base.LIQUIDATION_START_DAY
    opponent_pipeline = opponent_pipeline or {}
    exact_yield = _last_exact_opponent_yield or {}

    for product, quantity in shed.items():
        if product not in base.MARKET_PARAMS:
            continue

        if product == "FERTILIZER" and not liquidating:
            continue

        sell_quantity = quantity
        if product == "WHEAT":
            sell_quantity = max(0, quantity - reserved_wheat)

        if sell_quantity <= 0:
            continue

        baseline_says_sell = base.should_sell(product, sell_quantity, market_state)
        opponent_override_fired = False
        if not liquidating and not baseline_says_sell:
            opponent_override_fired = should_sell_opponent_aware_exact_yield(
                product, sell_quantity, market_state,
                exact_yield.get(product, 0), day,
                unlocked_shops=unlocked_shops, start_step=start_step, log=True,
            )

        if liquidating or baseline_says_sell or opponent_override_fired:
            cap = base.MAX_SELL_PER_TURN.get(product, quantity)
            spot_price = market_state.get("prices", {}).get(product, 0)
            if liquidating:
                min_price = base.PRICE_FLOOR
            elif baseline_says_sell:
                min_price = base.SELL_PRICE_THRESHOLDS.get(product, base.DEFAULT_SELL_THRESHOLD)
            else:
                min_price = max(base.PRICE_FLOOR, spot_price)
            amount = base.recommend_sell_quantity(
                product,
                inventory.get(product, 10000),
                sell_quantity,
                min_acceptable_price=min_price,
                max_per_turn=cap,
            )
            if amount > 0:
                actions.append(["SELL", product, amount])
                already_selling.add(product)

    shed_total = sum(shed.values())
    if shed_total >= base.SHED_FORCE_SELL_THRESHOLD:
        for product, quantity in shed.items():
            if product not in base.MARKET_PARAMS:
                continue
            if product == "FERTILIZER" and not liquidating:
                continue
            if product in already_selling or quantity <= 0:
                continue
            sell_quantity = quantity
            if product == "WHEAT":
                sell_quantity = max(0, quantity - reserved_wheat)
            if sell_quantity <= 0:
                continue
            cap = base.MAX_SELL_PER_TURN.get(product, quantity)
            amount = base.recommend_sell_quantity(
                product,
                inventory.get(product, 10000),
                sell_quantity,
                min_acceptable_price=base.PRICE_FLOOR,
                max_per_turn=cap,
            )
            if amount > 0:
                actions.append(["SELL", product, amount])

    preferred_crop = base.choose_crop(
        farm, market_state, private, day, unlocked_shops=unlocked_shops,
        start_step=start_step, opponent_pipeline=opponent_pipeline,
    )
    if preferred_crop:
        seed_quantity = base.seed_restock_quantity(preferred_crop, farm, private)
        if seed_quantity > 0:
            actions.append(["BUY_SEED", preferred_crop, seed_quantity])

    if day <= base.FERTILIZER_LAST_USEFUL_DAY:
        held = shed.get("FERTILIZER", 0) + sum(
            (carried or {}).get("FERTILIZER", 0)
            for carried in (private.get("inventories") or [])
            if isinstance(carried, dict)
        )
        if held < base.MAX_FERTILIZER_STOCK:
            fertilizer_price = market_state.get("prices", {}).get("FERTILIZER", 0)
            wanted = sum(
                1
                for row in (farm.get("tiles") or [])
                for tile in row
                if base.wants_fertilizer(tile, day)
            )
            if wanted > held and fertilizer_price and farm.get("money", 0) >= fertilizer_price * 2:
                actions.append(["BUY_PRODUCT", "FERTILIZER", 1])

    return actions


base.decide_market_actions = _decide_market_actions_opponent_aware_exact_yield


def opponent_aware_sell_gate_exact_yield(obs):
    return base.nikaangukia_meroni(obs)


def _self_test(seeds=(0, 1, 2)):
    from kaggle_environments import make

    for seed in seeds:
        env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})
        env.run([opponent_aware_sell_gate_exact_yield, opponent_aware_sell_gate_exact_yield])
        a, b = env.steps[-1]
        print(f"seed {seed}: seat0 {a.reward:>8.0f} [{a.status}]   seat1 {b.reward:>8.0f} [{b.status}]")
    print(f"activation log entries: {len(ACTIVATION_LOG)}")


agent = opponent_aware_sell_gate_exact_yield

if __name__ == "__main__":
    _self_test()
