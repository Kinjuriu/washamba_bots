"""Forward pricing research module for Kaggriculture. RESEARCH ONLY.

Not imported by main.py and does not change agent behaviour. This module
estimates how market price moves under our own sales, an assumed opponent's
sales, and town demand over time - so a future strategy change can be
designed against real engine mechanics instead of guessed thresholds.

Engine mechanics (read directly from the installed engine - see the
docstring of each function below for the exact source lines; "engine is the
source of truth" per CLAUDE.md):

    .venv/lib/python3.13/site-packages/kaggle_environments/envs/kaggriculture/kaggriculture.py

Summary (see docs/pricing_engine_notes.md for the full write-up):

  price(inv) = base + sign * amp * f(|inv - I0|), floored at $1, rounded
      sign = +1 below I0 (scarcity), -1 at/above I0 (glut)
      amp  = target * base / f(T)      (f evaluated at x=T)
      f in {linear, sq, sqrt, log, log10, hinge}, chosen per-product and
      per-direction (MARKET_PARAMS: below_func/below_target for inv<I0,
      above_func/above_target for inv>=I0)

  A trade commits one unit at a time; SELL adds 1 to market inventory
  (skipped entirely if the quoted price is already at the $1 floor - a
  crashed market can't be pushed any lower by continued selling); the next
  unit in the same order is re-quoted from that updated inventory. There is
  no single price for an N-unit order, only a price path.

  Town demand drains inventory (pushes price up) on two independent
  schedules: every `townShopSellInterval` turns (config default 4) each
  unlocked shop instance pulls 1 of each listed product (2 if the shop
  lists exactly one product); every `townCenterSellInterval` turns (config
  default 24 = once/day at turnsPerDay=24) the Town Center pulls 1 of every
  product except FERTILIZER. This is a demand pull, not a "restore to I0"
  mechanic - it drains a glut back toward I0 (price recovers) but makes
  existing scarcity worse (price keeps climbing) exactly the same way.

We prefer the engine's own `market_price` function when it can be imported
(so pricing behaviour can never drift from the engine we're actually scored
against), and fall back to a local reproduction of the same equation,
built from the engine's own published constants, if the import shape ever
changes - mirroring the try/except pattern main.py already uses for
MARKET_PARAMS.
"""

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
