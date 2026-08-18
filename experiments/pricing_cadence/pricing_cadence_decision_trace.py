"""Instrumented selling-decision tracer for the V1.2 mechanism audit
(experiments/pricing_cadence_v1_2_mechanism_audit_report.md).

Replays a real contested episode and, at every turn, for every product
held in the shed, records the full decision context - current inventory,
desired sell quantity before any cap, the cap actually in force (cadence-
adjusted where applicable), the minimum acceptable price, the actual
sell quantity, price before/after the proposed sale, and a purely
diagnostic forecast (estimate_future_price(), computed the same way for
every variant regardless of whether that variant's own decision logic
uses it) - then classifies what actually bound the decision:

    cap-bound       would have sold more if the per-turn cap were higher
    price-bound     stopped early because the price path crossed the
                    minimum acceptable price before the cap or the held
                    quantity did
    inventory-bound sold everything available; neither cap nor price
                    stopped it early
    no-sell         nothing sold this turn (blocked at the first unit, or
                    nothing held)
    liquidation     day >= LIQUIDATION_START_DAY - price is not the gate

Works for any variant file (A-style threshold logic or D-style forward-
price logic) by reading each variant's own functions/constants directly
from its loaded module - never hardcodes which family a file belongs to.
"""
import importlib.util

import pandas as pd
from kaggle_environments import make


def load_agent_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def classify_decision(desired_sell_quantity, cap, actual_sell_quantity, liquidating):
    """Pure, deterministic. See module docstring for the five labels."""
    if desired_sell_quantity <= 0:
        return "no-sell"
    if liquidating:
        return "liquidation"
    if actual_sell_quantity == 0:
        return "no-sell"
    bound = min(desired_sell_quantity, cap)
    if actual_sell_quantity < bound:
        return "price-bound"
    if cap < desired_sell_quantity and actual_sell_quantity == cap:
        return "cap-bound"
    if actual_sell_quantity == desired_sell_quantity:
        return "inventory-bound"
    return "unclassified"  # should not happen - safety net, not a silent guess


def _decision_context(mod, obs, day, liquidating, pipeline, opponent_pipeline, state):
    """Reproduces exactly what `mod`'s own decide_market_actions() would
    compute for min_price/cap per product, using that module's own
    constants - so a change to a variant's constants is picked up
    automatically rather than re-hardcoded here."""
    private = state["private"]
    market_state = state["market_state"]
    shed = private.get("shed", {})
    inventory = market_state.get("inventory", {})
    has_forward = hasattr(mod, "estimate_sell_or_hold_value")
    liquidation_day = getattr(mod, "LIQUIDATION_START_DAY", 19)

    rows = []
    for product, quantity in shed.items():
        if product not in mod.MARKET_PARAMS:
            continue
        if product == "FERTILIZER" and not liquidating:
            continue
        desired = quantity  # reserved_wheat approximated as 0 - diagnostic only
        if desired <= 0:
            continue

        stock = inventory.get(product, 10000)
        spot = mod.market_price(product, stock)
        base_cap = mod.MAX_SELL_PER_TURN.get(product, quantity)

        # Always-computed diagnostic forecast, independent of whether this
        # variant's own decision logic uses it - lets A be compared on the
        # same terms as D/D' even though A never calls this itself.
        forecast_fn = getattr(mod, "estimate_sell_or_hold_value", None)
        if forecast_fn is not None:
            sh = forecast_fn(
                product, desired, stock, day,
                pipeline_supply=pipeline.get(product, 0),
                opponent_pipeline_supply=opponent_pipeline.get(product, 0),
                unlocked_shops=state.get("unlocked_shops", ()),
                start_step=state.get("step"),
            )
            future_price = sh["value_hold_per_unit"]
        else:
            future_price = None

        if has_forward:
            min_price = future_price
            if hasattr(mod, "inventory_pressure"):
                pressure = mod.inventory_pressure(
                    product, quantity, pipeline.get(product, 0),
                    mod.remaining_season_days(day),
                )
                min_price = min_price / (1 + mod.INVENTORY_PRESSURE_WEIGHT * pressure)
            cap = base_cap
            if hasattr(mod, "cadence_urgency"):
                urgency = mod.cadence_urgency(day)
                min_price = min_price * (1 - mod.CADENCE_URGENCY_PRICE_WEIGHT * urgency)
                cap = max(1, round(cap * (1 + mod.CADENCE_URGENCY_CAP_WEIGHT * urgency)))
            min_price = mod.PRICE_FLOOR if liquidating else max(mod.PRICE_FLOOR, min_price)
        else:
            cap = base_cap
            min_price = (
                mod.PRICE_FLOOR
                if liquidating
                else mod.SELL_PRICE_THRESHOLDS.get(product, mod.DEFAULT_SELL_THRESHOLD)
            )

        recommended = mod.recommend_sell_quantity(
            product, stock, desired, min_acceptable_price=min_price, max_per_turn=cap,
        )
        price_after = mod.market_price(
            product,
            mod.price_path_for_sale(product, stock, recommended)["ending_inventory"],
        )

        rows.append({
            "day": day, "product": product,
            "market_inventory": stock, "shed_quantity": quantity,
            "desired_sell_quantity": desired, "base_cap": base_cap,
            "cadence_adjusted_cap": cap, "min_acceptable_price": min_price,
            "current_price": spot, "price_after_proposed_sale": price_after,
            "expected_future_price": future_price,
            "recommended_quantity": recommended, "liquidating": liquidating,
        })
    return rows


def trace_episode(agent_a_path, agent_a_name, agent_b_path, agent_b_name, seed):
    """One contested episode, both sides instrumented within the same
    market conditions. Returns (dataframe, balance_a, balance_b)."""
    mod_a = load_agent_module(agent_a_path, agent_a_name)
    mod_b = load_agent_module(agent_b_path, agent_b_name)
    env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed}, debug=False)
    env.run([agent_a_path, agent_b_path])

    turns_per_day = 24
    rows = []
    # env.steps[i].action is the action CHOSEN FROM env.steps[i-1].observation
    # - it is recorded at the index of the state it produced, not the state
    # it was computed from. Confirmed by tracing a real SELL order against
    # shed quantity directly: steps[i].observation's shed only reflects
    # steps[i].action once steps[i+1].observation is reached. Pairing
    # steps[i].observation with steps[i+1].action (not steps[i].action) is
    # therefore required to reproduce what the agent actually saw when it
    # made that decision.
    for index in range(len(env.steps) - 1):
        step = env.steps[index]
        next_step = env.steps[index + 1]
        day = index // turns_per_day
        for seat, mod, name in [(0, mod_a, agent_a_name), (1, mod_b, agent_b_name)]:
            action = next_step[seat].get("action") or {}
            sells = {}
            for order in action.get("market") or []:
                if order and order[0] == "SELL" and len(order) >= 3:
                    sells[order[1]] = sells.get(order[1], 0) + order[2]

            obs = step[seat].observation
            state = mod.extract_state(obs)
            farm = state["farm"]
            if not farm:
                continue
            liquidating = day >= getattr(mod, "LIQUIDATION_START_DAY", 19)
            pipeline = mod.count_pipeline_supply(farm, state["private"])
            opponent_pipeline = state.get("opponent_pipeline") or {}

            for row in _decision_context(mod, obs, day, liquidating, pipeline, opponent_pipeline, state):
                sold = sells.get(row["product"], 0)
                row["actual_sold"] = sold
                row["decision"] = classify_decision(
                    row["desired_sell_quantity"], row["cadence_adjusted_cap"], sold, liquidating,
                )
                row["revenue"] = sold * row["current_price"]
                row["agent"] = name
                rows.append(row)

    final = env.steps[-1]
    return pd.DataFrame(rows), final[0].reward, final[1].reward
