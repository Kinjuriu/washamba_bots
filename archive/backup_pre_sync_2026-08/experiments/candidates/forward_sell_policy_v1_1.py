"""
Forward-looking SELL policy, v1.1 - fixes the two problems
experiments/forward_sell_policy_v0_report.md identified in v0:

  1. v0's one-turn horizon mostly captured town-demand recovery and
     never modelled our own future harvest (pinned at 0, a day-vs-turn
     unit mismatch). v1.1 uses a genuine multi-day own-supply forecast
     (pricing_v1.estimate_multi_day_sell_or_hold_decision, section 8 of
     pricing_v1.py) built on the already-validated
     pricing_v1.estimate_own_pipeline.
  2. v0 sized every SELL order down to PRICE_FLOOR regardless of the
     sell/hold decision, coupling the timing question with a sizing
     change. v1.1 sizes quantity EXACTLY the way main.py already does -
     recommend_sell_quantity with the product's real SELL_PRICE_THRESHOLDS
     floor - before the forward decision ever runs, and the forward
     decision receives that quantity as a fixed input it cannot change.

HYPOTHESIS (bidirectional, must be able to fail): given the exact
quantity main.py would already sell this turn, does knowing our own
upcoming harvest/production over the next few days change whether
selling now beats waiting for a specific better day within that window?
Might not - if our own pipeline rarely lands meaningful volume within
`pricing_v1.DEFAULT_HORIZON_DAYS` for the products that matter, or if
town-demand recovery alone (still present in the model) already explains
most of what a longer horizon finds, the result could look a lot like v0
again. Both are real answers - see the report's diagnostics section for
which one this is.

MECHANISM: main.decide_market_actions's sell loop is copied verbatim,
with ONE substitution. Baseline's original two-step "should_sell(...) ->
recommend_sell_quantity(..., min_acceptable_price=SELL_PRICE_THRESHOLDS[...])"
becomes:

  1. amount = recommend_sell_quantity(product, inventory, sell_quantity,
     min_acceptable_price=SELL_PRICE_THRESHOLDS.get(product, DEFAULT_SELL_THRESHOLD),
     max_per_turn=cap)
     - CHARACTER FOR CHARACTER main.py's own quantity formula, same
       floor, same cap. Not PRICE_FLOOR (that was v0's coupling bug).
       This line alone is mathematically equivalent to baseline's
       should_sell() check too: recommend_sell_quantity's own walk stops
       at the first unit quoting under min_acceptable_price, which is
       exactly should_sell's `price >= threshold` test - so `amount > 0`
       here iff should_sell would have said yes. No separate should_sell
       call is needed or made.
  2. If amount > 0: pricing_v1.estimate_multi_day_sell_or_hold_decision(
     product, inventory, quantity=amount, day, remaining_days,
     tiles=farm["tiles"], liquidation_start_day=LIQUIDATION_START_DAY, ...)
     decides SELL (append ["SELL", product, amount] - the EXACT amount
     from step 1, untouched) or HOLD (append nothing this turn for this
     product).

Liquidation (day >= LIQUIDATION_START_DAY) is untouched: same bypass as
main.py, "sell regardless of price," and the forward decision function
is never even called on a liquidating turn (test-verified). Everything
else - FERTILIZER/WHEAT-reserve exclusions, SHED_FORCE_SELL_THRESHOLD,
choose_crop/BUY_SEED, the fertilizer buy logic, MAX_HANDS_PER_DAY, land,
animals, labor, opponent modelling - is character-for-character
main.py.

Opponent supply is not a parameter anywhere in this call chain - not
even pinned at 0 - per the task's explicit scope for this experiment.

DIAGNOSTICS: every product with amount > 0 this turn gets one record in
DECISION_LOG (day, product, quantity, prefer_sell, reason, revenue_now,
best_revenue_delayed, best_future_day, advantage,
opportunity_cost_of_holding, per_day) - the full multi-day breakdown, not
just the winning day, so the report can measure how often each offset in
the horizon actually wins.

Usage:
    .venv/Scripts/python.exe experiments/candidates/forward_sell_policy_v1_1.py   # self-test
    .venv/Scripts/python.exe experiments/selfplay_agent.py experiments/candidates/forward_sell_policy_v1_1.py 12
    .venv/Scripts/python.exe experiments/head_to_head.py experiments/candidates/forward_sell_policy_v1_1.py main.py 12
    .venv/Scripts/python.exe experiments/paired_compare.py main.py experiments/candidates/forward_sell_policy_v1_1.py
"""
import os
import sys


def _find_repo_root():
    """Same defensive walk-up as the other candidates in this directory."""
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


def _decide_market_actions_forward_sell_v1_1(
    farm, private, market_state, day, reserved_wheat=0, unlocked_shops=(), start_step=None,
    opponent_pipeline=None,
):
    """Verbatim copy of main.decide_market_actions with exactly one
    substitution in the main sell loop, described in this module's
    docstring: baseline quantity sizing is preserved exactly, and only
    the yes/no decision on top of that unchanged quantity is replaced by
    a multi-day own-supply forecast."""
    actions = []
    already_selling = set()

    shed = private.get("shed", {})
    inventory = market_state.get("inventory", {})
    liquidating = day >= base.LIQUIDATION_START_DAY
    remaining_days = base.remaining_season_days(day)
    tiles = farm.get("tiles")

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

        cap = base.MAX_SELL_PER_TURN.get(product, quantity)

        if liquidating:
            amount = base.recommend_sell_quantity(
                product, inventory.get(product, 10000), sell_quantity,
                min_acceptable_price=base.PRICE_FLOOR, max_per_turn=cap,
            )
            if amount > 0:
                actions.append(["SELL", product, amount])
                already_selling.add(product)
            continue

        # Step 1: EXACT baseline quantity - same floor, same cap,
        # mathematically equivalent to should_sell()'s own yes/no test
        # (see module docstring). Not touched by the decision below.
        min_price = base.SELL_PRICE_THRESHOLDS.get(product, base.DEFAULT_SELL_THRESHOLD)
        amount = base.recommend_sell_quantity(
            product, inventory.get(product, 10000), sell_quantity,
            min_acceptable_price=min_price, max_per_turn=cap,
        )
        if amount <= 0:
            continue

        # Step 2: the ONE change - sell this exact `amount` now, or wait
        # for a better day within the horizon to sell this SAME amount.
        decision = pricing_v1.estimate_multi_day_sell_or_hold_decision(
            product,
            inventory.get(product, 10000),
            amount,
            day,
            remaining_days,
            tiles=tiles,
            liquidation_start_day=base.LIQUIDATION_START_DAY,
            unlocked_shops=unlocked_shops,
            start_step=start_step,
        )
        _log_decision(day=day, product=product, **decision)

        if decision["prefer_sell"]:
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


base.decide_market_actions = _decide_market_actions_forward_sell_v1_1


def forward_sell_policy_v1_1(obs):
    return base.nikaangukia_meroni(obs)


def _self_test(seeds=(0, 1, 2)):
    from kaggle_environments import make

    for seed in seeds:
        env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})
        env.run([forward_sell_policy_v1_1, forward_sell_policy_v1_1])
        a, b = env.steps[-1]
        print(f"seed {seed}: seat0 {a.reward:>8.0f} [{a.status}]   seat1 {b.reward:>8.0f} [{b.status}]")
    print(f"decision log entries: {len(DECISION_LOG)}")


agent = forward_sell_policy_v1_1

if __name__ == "__main__":
    _self_test()
