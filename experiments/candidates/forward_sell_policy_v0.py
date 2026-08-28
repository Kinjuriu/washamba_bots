"""
Forward-looking SELL policy, v0 - the pricing track's next deterministic-
policy experiment, after `experiments/sell_threshold_audit_report.md`
found that no flat `SELL_PRICE_THRESHOLDS` constant (permissive or
strict) can distinguish "price is high and about to fall" from "price is
low and about to recover," because a constant carries no forecast at
all.

HYPOTHESIS (bidirectional, must be able to fail): replacing
`current_price > SELL_PRICE_THRESHOLD` with a genuine one-step
sell-now-vs-hold-one-turn value comparison
(`pricing_v1.estimate_sell_or_hold_decision`, built for this experiment
by composing already-verified `pricing_v1.py` functions - see that
module's section 7) produces better selling decisions than the flat
threshold. It might not: `pricing.py`'s mechanics have no way to know
the future, only to project the *known* effects already in scope (our
own pipeline supply, town demand) forward - if those effects rarely
differ across "now" vs. "one turn from now," the comparison degenerates
toward the same decision the threshold already made, or toward "always
sell" if it degenerates to a near-tie. Both are informative results,
not the same as "the code doesn't work" - see the report's diagnostics.

MECHANISM: `decide_market_actions`'s main sell loop is copied verbatim
from `main.py`, with exactly one change: `should_sell(product,
sell_quantity, market_state)` is replaced with a call to
`pricing_v1.estimate_sell_or_hold_decision(...)`, and quantity for a
SELL order now comes directly from that function's own `quantity` field
(the same PRICE_FLOOR-walked amount `recommend_sell_quantity` would give
liquidation) rather than being re-derived from a threshold-based
`min_acceptable_price`. Everything else - the FERTILIZER/WHEAT-reserve
exclusions, the `liquidating` bypass (unchanged: day >=
LIQUIDATION_START_DAY still means "sell regardless of price," this
experiment does not touch or replace that rule), the
SHED_FORCE_SELL_THRESHOLD overflow loop, `choose_crop`/BUY_SEED, and the
FERTILIZER buy logic - is untouched `main.py`, character for character.

`our_pipeline_supply` is pinned at 0 in the forward comparison, not
threaded from `count_pipeline_supply` - see the report's "assumptions"
section for why: `pricing_v1.estimate_own_pipeline` operates at day
granularity (yield accrual is computed relative to a horizon *day*), and
this experiment's hold horizon is a single *turn*
(`pricing_v1.DEFAULT_HOLD_HORIZON_TURNS = 1`) - at that granularity a
day-level accrual estimate would be a unit mismatch, not a genuine
signal. Opponent pipeline supply is out of scope entirely per the prior
experiment's closing instruction ("do not run another opponent-supply
experiment") and is not threaded in at all, not even pinned - there is
no parameter for it in this candidate's call.

ACTIVATION INSTRUMENTATION: every product with `sell_quantity > 0` this
turn gets one record in DECISION_LOG (day, product, quantity, prefer_sell,
reason, revenue_now, revenue_delayed, opportunity_cost_of_holding,
pressure, urgency) - not just the turns where the decision differs from
baseline, so the report's diagnostics can measure the full decision
population, not just the disagreements.

Usage:
    .venv/Scripts/python.exe experiments/candidates/forward_sell_policy_v0.py   # self-test
    .venv/Scripts/python.exe experiments/selfplay_agent.py experiments/candidates/forward_sell_policy_v0.py 12
    .venv/Scripts/python.exe experiments/head_to_head.py experiments/candidates/forward_sell_policy_v0.py main.py 12
    .venv/Scripts/python.exe experiments/paired_compare.py main.py experiments/candidates/forward_sell_policy_v0.py
"""
import os
import sys


def _find_repo_root():
    """Same defensive walk-up as the other candidates in this directory -
    see opponent_aware_sell_gate.py's docstring for why a fixed
    dirname()-hop-count fallback is unsafe here."""
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

DECISION_LOG = []


def _log_decision(**record):
    DECISION_LOG.append(record)


def _decide_market_actions_forward_sell(
    farm, private, market_state, day, reserved_wheat=0, unlocked_shops=(), start_step=None,
    opponent_pipeline=None,
):
    """Verbatim copy of main.decide_market_actions with exactly one
    substitution in the main sell loop: should_sell(...) -> a call to
    pricing_v1.estimate_sell_or_hold_decision(...), and the SELL order's
    quantity now comes from that function's own PRICE_FLOOR-walked
    `quantity` rather than being re-derived via recommend_sell_quantity
    with a threshold-based min_acceptable_price. The liquidation branch,
    the SHED_FORCE_SELL_THRESHOLD overflow loop, choose_crop/BUY_SEED,
    and the FERTILIZER buy logic are character-for-character the same as
    main.py."""
    actions = []
    already_selling = set()

    shed = private.get("shed", {})
    inventory = market_state.get("inventory", {})
    liquidating = day >= base.LIQUIDATION_START_DAY
    remaining_days = base.remaining_season_days(day)

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

        if liquidating:
            cap = base.MAX_SELL_PER_TURN.get(product, quantity)
            amount = base.recommend_sell_quantity(
                product, inventory.get(product, 10000), sell_quantity,
                min_acceptable_price=base.PRICE_FLOOR, max_per_turn=cap,
            )
            if amount > 0:
                actions.append(["SELL", product, amount])
                already_selling.add(product)
            continue

        # THE ONE CHANGE: should_sell(...) -> a genuine sell-now-vs-hold
        # value comparison. cap is passed through as max_per_turn so the
        # decision's own quantity sizing already respects
        # MAX_SELL_PER_TURN - no second sizing pass needed afterward,
        # unlike the threshold-based baseline (which sizes with
        # recommend_sell_quantity a second time using the threshold as
        # the floor).
        cap = base.MAX_SELL_PER_TURN.get(product, quantity)
        decision = pricing_v1.estimate_sell_or_hold_decision(
            product,
            inventory.get(product, 10000),
            sell_quantity,
            day,
            remaining_days,
            our_pipeline_supply=0,
            unlocked_shops=unlocked_shops,
            start_step=start_step,
            max_per_turn=cap,
        )
        _log_decision(day=day, product=product, **decision)

        if decision["prefer_sell"] and decision["quantity"] > 0:
            actions.append(["SELL", product, decision["quantity"]])
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


base.decide_market_actions = _decide_market_actions_forward_sell


def forward_sell_policy_v0(obs):
    return base.nikaangukia_meroni(obs)


def _self_test(seeds=(0, 1, 2)):
    from kaggle_environments import make

    for seed in seeds:
        env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})
        env.run([forward_sell_policy_v0, forward_sell_policy_v0])
        a, b = env.steps[-1]
        print(f"seed {seed}: seat0 {a.reward:>8.0f} [{a.status}]   seat1 {b.reward:>8.0f} [{b.status}]")
    print(f"decision log entries: {len(DECISION_LOG)}")


agent = forward_sell_policy_v0

if __name__ == "__main__":
    _self_test()
