"""Selling-cadence experiment: the sell-now-vs-hold framework, as its own
testable module. experiments/pricing_cadence_experiment_report.md).

This is the single authored copy of the three new deterministic functions
(estimate_sell_or_hold_value, inventory_pressure, cadence_urgency). The
standalone agent variants under experiments/pricing_cadence_variants/
carry an inlined copy of the same logic (main.py's own precedent for why:
"inline forward pricing into main.py so a bare upload stands alone" -
kaggle_environments loads an agent file as a single script, so a variant
agent can't rely on importing a sibling experiments/ module at runtime).
This module exists so the logic has exactly one place to be read, tested,
and used from the notebook, instead of only living duplicated three times
inside agent_b.py/agent_c.py/agent_d.py.

NOT wired into main.py. Root main.py is untouched by this experiment.
"""

from pricing import PRICE_FLOOR, estimate_future_price, price_path_for_sale

TURNS_PER_DAY = 24
SEASON_DAYS = 30

# Same table as main.py's MAX_SELL_PER_TURN (duplicated here rather than
# imported from main.py on purpose - main.py is not touched by this
# experiment, and importing from it would create exactly the coupling
# the "do not modify main.py" instruction is trying to avoid).
MAX_SELL_PER_TURN = {
    "STRAWBERRY": 10,
    "MELON": 15,
    "WOOL": 5,
}

# How many days ahead "sell now vs hold" looks when judging today's
# price. Short on purpose: a multi-week lookahead would just re-derive
# choose_crop()'s own harvest-horizon forecast; this asks a narrower
# question - is today unusually bad or unusually good compared to the
# next few days, not "what will this be worth in three weeks."
SELL_HORIZON_DAYS = 3

# How strongly a large pile (shed + growing pipeline) lowers the price
# we're willing to accept, relative to what we could plausibly still
# sell by season end at this product's own per-turn cap. Not swept - a
# first-pass constant; the experiment measures the direction, not a
# tuned optimum.
INVENTORY_PRESSURE_WEIGHT = 1.0

# How strongly running out of season lowers the accepted price
# (continuous, replacing LIQUIDATION_START_DAY's hard cutoff) and
# raises the per-turn cap. Also unswept.
CADENCE_URGENCY_PRICE_WEIGHT = 0.6
CADENCE_URGENCY_CAP_WEIGHT = 1.0


def estimate_sell_or_hold_value(
    item,
    quantity,
    inventory,
    day,
    pipeline_supply=0,
    opponent_pipeline_supply=0,
    unlocked_shops=(),
    start_step=None,
    horizon_days=SELL_HORIZON_DAYS,
):
    """
    Compare selling `quantity` units of `item` right now against holding
    them for `horizon_days` more days, using the same deterministic price
    model choose_crop() already relies on - no financial futures-curve
    assumption, just the engine's own mechanics run forward from the
    current state.

        value_now  = revenue from price_path_for_sale() at the current
                     inventory - this turn's real per-unit price decay,
                     not just the spot price.
        value_hold = quantity * estimate_future_price()'s forecast at
                     the horizon, given our own pipeline and the
                     opponent's visible pipeline landing in between, and
                     town demand draining the market in between.

    Pure and deterministic - same inputs, same answer, no I/O. Returns a
    dict distinguishing value_now / value_hold (total and per-unit) and
    `hold_is_better`.
    """
    if start_step is None:
        start_step = day * TURNS_PER_DAY

    if quantity <= 0:
        return {
            "value_now": 0.0,
            "value_hold": 0.0,
            "value_now_per_unit": 0.0,
            "value_hold_per_unit": 0.0,
            "hold_is_better": False,
        }

    now = price_path_for_sale(item, inventory, quantity)
    value_now = float(sum(now["prices"]))

    forecast = estimate_future_price(
        item,
        inventory,
        turns_ahead=horizon_days * TURNS_PER_DAY,
        our_pipeline_supply=pipeline_supply,
        opponent_pipeline_supply=opponent_pipeline_supply,
        unlocked_shops=unlocked_shops,
        start_step=start_step,
    )
    value_hold_per_unit = float(forecast["future_price"])
    value_hold = value_hold_per_unit * quantity

    return {
        "value_now": value_now,
        "value_hold": value_hold,
        "value_now_per_unit": value_now / quantity,
        "value_hold_per_unit": value_hold_per_unit,
        "hold_is_better": value_hold > value_now,
    }


def inventory_pressure(item, shed_quantity, pipeline_supply, remaining_days):
    """
    How much of `item` we're carrying relative to what we could plausibly
    still move before season end, at this product's own per-turn cap and
    roughly one selling opportunity a day. >=1 means we are structurally
    overcommitted - even selling flat-out every remaining day at the cap
    would not clear it in time. Products with no listed per-turn cap
    (MAX_SELL_PER_TURN only lists the ones that need one) get a generous
    synthetic ceiling instead of an unbounded one, so pressure is ~0
    unless the pile is genuinely enormous.
    """
    cap = MAX_SELL_PER_TURN.get(item, 10_000)
    capacity = max(1, cap * max(1, remaining_days))
    carried = shed_quantity + pipeline_supply
    return carried / capacity


def cadence_urgency(day):
    """
    0 at day 0, rising smoothly toward 1 as the season ends - the
    continuous replacement for LIQUIDATION_START_DAY's hard switch.
    Matches the replay evidence of no day-22 selling cliff
    (docs/REPLAY_ANALYSIS.md): urgency should ramp, not flip.
    """
    return min(1.0, max(0.0, day) / (SEASON_DAYS - 1))
