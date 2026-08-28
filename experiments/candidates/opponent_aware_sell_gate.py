"""
Issue #21 pricing track, Experiment 3: does opponent-supply information
improve the SELL/no-sell gate?

CONTEXT: docs/pricing_engine_notes.md audited pricing.py's wiring into
main.py and found opponent_pipeline (main.py's count_opponent_pipeline,
called once per turn and already threaded through decide_market_actions)
reaches choose_crop (what to plant) but never should_sell (whether to
sell) - despite decide_market_actions already having the variable in
scope. This experiment tests, in isolation, whether wiring it into the
sell decision helps.

HYPOTHESIS (bidirectional, must be able to fail): when the opponent has
substantial visible standing crop of a product we're holding, waiting is
more likely to land us into a market they've already depressed by the time
we'd otherwise sell - so selling now may beat waiting even when today's
spot price doesn't clear should_sell's existing threshold. When opponent
supply is negligible, this signal should do nothing. The experiment must
be able to show no effect, or a negative one (e.g. selling too early on a
signal that never actually materializes into a real opponent sale, since
their shed - what they actually intend to sell - is never visible; only
their standing crop is).

MECHANISM CHOSEN (one, not combined with anything else): the sell/no-sell
gate, via a short-horizon sell-now-vs-wait comparison, reusing
pricing_v1.py's already-tested compare_immediate_vs_delayed_selling. Not
sell cadence (no season_urgency/inventory_pressure - see recommend_sell_
cadence in pricing_v1.py, deliberately not used here), not a new
SELL_PRICE_THRESHOLDS value (the constant is untouched), not a
MAX_SELL_PER_TURN change (recommend_sell_quantity's call is untouched),
not a quantity change of any kind - only whether should_sell says yes.

ISOLATION, by construction, not by convention: should_sell_opponent_aware
below is should_sell(...) OR <opponent-driven override>, and the override
short-circuits to False whenever opponent_units <= 0. This guarantees
byte-identical behaviour to unmodified main.py on any turn where the
opponent has no visible standing crop of the product in question - so any
measured difference in the evaluation below is attributable only to turns
where opponent supply is actually nonzero, not to some other change
riding along.

Everything else in decide_market_actions is copied verbatim from main.py:
the FERTILIZER/WHEAT-reserve exclusions, the SHED_FORCE_SELL_THRESHOLD
overflow loop (deliberately NOT touched - forced sales already ignore
price entirely, so an opponent-aware override has nothing to add there),
recommend_sell_quantity's call (unchanged - sizing is out of scope), and
the BUY_SEED/FERTILIZER logic below it.

See experiments/opponent_aware_sell_gate_report.md for the full writeup:
hypothesis, evaluation results, diagnostics, and recommendation.

Usage:
    .venv/Scripts/python.exe experiments/candidates/opponent_aware_sell_gate.py   # self-test
    .venv/Scripts/python.exe experiments/selfplay_agent.py experiments/candidates/opponent_aware_sell_gate.py 6
    .venv/Scripts/python.exe experiments/head_to_head.py experiments/candidates/opponent_aware_sell_gate.py main.py 6
    .venv/Scripts/python.exe experiments/paired_compare.py main.py experiments/candidates/opponent_aware_sell_gate.py
"""
import os
import sys


def _find_repo_root():
    """kaggle_environments' agent loader intermittently exec's an agent
    file with no `__file__` present at all - a fixed dirname()-hop-count
    fallback was silently wrong some fraction of the time in an earlier
    experiment this session and produced ModuleNotFoundError mid-episode.
    Walk up from cwd and verify against main.py instead of guessing. (This
    candidate is not intended for Kaggle submission - see the module
    docstring - but the same loader quirk affects local runs too.)"""
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

# A single fixed near-term window, not a swept/tuned parameter - "does the
# opponent's visible supply make selling now beat waiting a short while,"
# not "what is the optimal horizon." One day: long enough for
# apply_town_demand's per-turn drain to matter at all, short enough that
# this cannot be mistaken for a season-length cadence/urgency mechanism.
OPPONENT_AWARE_HORIZON_TURNS = base.DEFAULT_TURNS_PER_DAY


def should_sell_opponent_aware(
    product, quantity, market_state, opponent_units, day,
    unlocked_shops=(), start_step=None,
):
    """should_sell(...), plus exactly one additional way to say yes: selling
    `quantity` right now beats waiting OPPONENT_AWARE_HORIZON_TURNS turns,
    once the opponent's visible standing supply of `product` is accounted
    for. our_pipeline_supply is deliberately pinned at 0 in the comparison
    below - this experiment isolates opponent supply's marginal
    contribution, not our own harvest timing (a different, already-built
    pricing_v1.py capability, out of scope here per the task's "choose
    only one mechanism").

    Never suppresses a sell the baseline would have made (short-circuits
    on the unmodified should_sell check first), and is a no-op whenever
    opponent_units <= 0 - see the module docstring for why that guard is
    what makes this an isolated ablation rather than a general reseller.
    """
    if base.should_sell(product, quantity, market_state):
        return True
    if quantity <= 0 or opponent_units <= 0:
        return False

    inventory = market_state.get("inventory", {}).get(product, 10000)
    if start_step is None:
        start_step = day * base.DEFAULT_TURNS_PER_DAY

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
    return not comparison["delay_is_better"]


def _decide_market_actions_opponent_aware(
    farm, private, market_state, day, reserved_wheat=0, unlocked_shops=(), start_step=None,
    opponent_pipeline=None,
):
    """Verbatim copy of main.decide_market_actions with exactly one line
    changed: the main sell loop's should_sell(...) call becomes
    should_sell_opponent_aware(...), passing the product's opponent-visible
    unit count plus day/unlocked_shops/start_step (all already parameters
    of this function, already threaded to choose_crop below - nothing new
    had to be plumbed in from further up the call stack). The
    SHED_FORCE_SELL_THRESHOLD overflow loop, BUY_SEED, and FERTILIZER logic
    are untouched."""
    actions = []
    already_selling = set()

    shed = private.get("shed", {})
    inventory = market_state.get("inventory", {})
    liquidating = day >= base.LIQUIDATION_START_DAY
    opponent_pipeline = opponent_pipeline or {}

    for product, quantity in shed.items():
        if product not in base.MARKET_PARAMS:
            continue

        if product == "FERTILIZER" and not liquidating:
            continue

        sell_quantity = quantity
        if product == "WHEAT":
            sell_quantity = max(0, quantity - reserved_wheat)

        # THE ONE CHANGE (part 1): should_sell -> should_sell_opponent_aware,
        # tracked separately from the plain threshold so min_price below can
        # stay consistent with WHY this sale was authorized. See this
        # module's docstring for the full isolation argument.
        if sell_quantity <= 0:
            continue

        baseline_says_sell = base.should_sell(product, sell_quantity, market_state)
        opponent_override_fired = False
        if not liquidating and not baseline_says_sell:
            opponent_override_fired = should_sell_opponent_aware(
                product, sell_quantity, market_state,
                opponent_pipeline.get(product, 0), day,
                unlocked_shops=unlocked_shops, start_step=start_step,
            )

        if liquidating or baseline_says_sell or opponent_override_fired:
            cap = base.MAX_SELL_PER_TURN.get(product, quantity)
            spot_price = market_state.get("prices", {}).get(product, 0)
            if liquidating:
                min_price = base.PRICE_FLOOR
            elif baseline_says_sell:
                # Unchanged from main.py: the fixed threshold is itself
                # already a valid floor here, since spot price already
                # clears it.
                min_price = base.SELL_PRICE_THRESHOLDS.get(product, base.DEFAULT_SELL_THRESHOLD)
            else:
                # THE ONE CHANGE (part 2): the opponent-aware override
                # authorized this sale at (approximately) today's spot
                # price, which is BELOW the fixed threshold by
                # construction (baseline_says_sell was False) - passing
                # the unchanged threshold as min_price here would silently
                # reject every unit and size the order to 0, contradicting
                # the gate's own yes. Use spot_price itself as the floor:
                # "sell down to today's price, no further" is the natural,
                # minimal floor for a decision that was only ever about
                # whether today beats waiting, not about accepting an
                # arbitrary new discount - recommend_sell_quantity's own
                # per-unit walk (unchanged) still governs exactly how many
                # units clear that floor.
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


base.decide_market_actions = _decide_market_actions_opponent_aware


def opponent_aware_sell_gate(obs):
    return base.nikaangukia_meroni(obs)


def _self_test(seeds=(0, 1, 2)):
    from kaggle_environments import make

    for seed in seeds:
        env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})
        env.run([opponent_aware_sell_gate, opponent_aware_sell_gate])
        a, b = env.steps[-1]
        print(f"seed {seed}: seat0 {a.reward:>8.0f} [{a.status}]   seat1 {b.reward:>8.0f} [{b.status}]")


agent = opponent_aware_sell_gate

if __name__ == "__main__":
    _self_test()
