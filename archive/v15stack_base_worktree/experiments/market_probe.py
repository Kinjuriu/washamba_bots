"""
Market investigation tool — economic intelligence layer.

Does NOT touch main.py / the submitted agent. Read-only: runs a normal episode
(main.py vs the built-in "starter" agent) purely to observe how the market
reacts, and separately reconstructs the documented price formula so we have
an analytical inventory -> price mapping per product, cross-checked against
what the live engine actually produced.

Two outputs:
  1. OBSERVED table: real (turn, inventory, price) samples pulled from a live
     720-turn episode, for WHEAT / CARROT / TOMATO / STRAWBERRY / MELON.
  2. ANALYTICAL curve: price(inventory) swept across a wide range per crop,
     from the documented price function:

         price(inv) = base + sign * amp * f(|inv - I0|)
         sign = +1 if inv < I0 (scarcity)   -1 if inv > I0 (glut)
         amp  = target * base / f(T)          (f evaluated at x=T)
         floored at $1, rounded to nearest dollar

  Params (base, I0, T, below_func, below_target, above_func, above_target)
  are taken verbatim from the competition Overview page's Market Mechanics
  table (captured 2026-08-15), which the Discussion tab confirms is the
  patched, engine-accurate version as of this season.

Usage:
    .venv/Scripts/python.exe experiments/market_probe.py
"""

import math
from kaggle_environments import make

# --- Analytical price model (from the documented Market Mechanics table) ---

I0 = 10_000

PRICE_PARAMS = {
    # product:      (base, T,   below_func, below_target, above_func, above_target)
    "WHEAT":      (25,  400, "sqrt",  0.80, "log",   0.20),
    "CARROT":     (35,  450, "hinge", 1.00, "sqrt",  0.70),
    "TOMATO":     (60,  200, "hinge", 0.40, "sqrt",  0.60),
    "STRAWBERRY": (120, 100, "sqrt",  0.70, "linear", 1.60),
    "MELON":      (250, 300, "log",   0.20, "sq",    3.60),
    "EGG":        (50,  332, "hinge", 0.40, "log",   0.20),
    "MILK":       (160, 122, "sqrt",  0.60, "linear", 1.60),
    "WOOL":       (200, 105, "log",   0.20, "sq",    3.20),
    "FERTILIZER": (100, 200, "linear", 0.40, "linear", 0.40),
}

FOCUS_PRODUCTS = ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON"]


def _f_shape(shape: str, x: float, T: int) -> float:
    if shape == "linear":
        return x
    if shape == "sq":
        return x ** 2
    if shape == "sqrt":
        return math.sqrt(x)
    if shape == "log":
        return math.log(1 + x)
    if shape == "log10":
        return math.log10(1 + x)
    if shape == "hinge":
        u = x / T
        return u + 8 * max(0.0, u - 1) ** 2
    raise ValueError(f"unknown shape {shape}")


def price_at(product: str, inventory: float) -> int:
    base, T, below_func, below_target, above_func, above_target = PRICE_PARAMS[product]
    x = abs(inventory - I0)
    if inventory == I0:
        return base
    if inventory < I0:
        shape, target, sign = below_func, below_target, 1
    else:
        shape, target, sign = above_func, above_target, -1
    amp = target * base / _f_shape(shape, T, T)
    p = base + sign * amp * _f_shape(shape, x, T)
    return max(1, round(p))


def print_analytical_curve(product: str) -> None:
    base, T, *_ = PRICE_PARAMS[product]
    print(f"\n--- {product}  (base=${base}, I0={I0}, T={T}) : inventory -> price ---")
    print(f"{'INVENTORY':>10} | {'PRICE':>6}   (delta from I0, in units of T)")
    offsets_in_T = [-3, -2, -1.5, -1, -0.75, -0.5, -0.25, -0.1, 0, 0.1, 0.25, 0.5, 0.75, 1, 1.5, 2, 3, 5]
    for k in offsets_in_T:
        inv = I0 + k * T
        if inv < 0:
            continue
        p = price_at(product, inv)
        tag = f"(I0{'+' if k >= 0 else ''}{k:g}T)"
        print(f"{inv:10.0f} | {p:6d}   {tag}")


# --- Live-episode observation (main.py untouched, we only read obs.market) ---

def run_and_sample_market(episode_steps: int = 720, sample_every: int = 24):
    """Runs main.py vs the built-in starter agent and records obs['market']
    at every `sample_every`-th turn (default: once per in-game day)."""
    env = make("kaggriculture", configuration={"episodeSteps": episode_steps}, debug=True)
    env.run(["main.py", "starter"])

    samples = []  # list of dicts: turn, product, inventory, price
    for turn_idx, step in enumerate(env.steps):
        if turn_idx % sample_every != 0:
            continue
        obs = step[0].observation
        market = obs.get("market", {})
        inv = market.get("inventory", {})
        prices = market.get("prices", {})
        for product in FOCUS_PRODUCTS:
            if product in inv and product in prices:
                samples.append(
                    {
                        "turn": turn_idx,
                        "product": product,
                        "inventory": inv[product],
                        "price": prices[product],
                    }
                )
    final = env.steps[-1]
    result = {
        "samples": samples,
        "final_reward_p0": final[0].reward,
        "final_reward_p1": final[1].reward,
        "final_status": (final[0].status, final[1].status),
    }
    return result


def print_observed_table(samples):
    print("\n=== OBSERVED market state, sampled once per in-game day (main.py vs starter) ===")
    header = f"{'TURN':>5} {'PRODUCT':<10} {'BASE PRICE':>10} {'INVENTORY':>10} {'PRICE':>6}"
    print(header)
    print("-" * len(header))
    for row in samples:
        base = PRICE_PARAMS[row["product"]][0]
        print(
            f"{row['turn']:5d} {row['product']:<10} {base:10d} "
            f"{row['inventory']:10.0f} {row['price']:6d}"
        )


def print_snapshot_table(samples):
    """One row per crop at the LAST sampled turn, matching the shape the user asked for."""
    print("\n=== Snapshot: last sampled turn per crop ===")
    header = f"{'PRODUCT':<12} {'BASE PRICE':>10} {'INVENTORY':>10} {'PRICE':>6}"
    print(header)
    print("-" * len(header))
    last_by_product = {}
    for row in samples:
        last_by_product[row["product"]] = row
    for product in FOCUS_PRODUCTS:
        row = last_by_product.get(product)
        base = PRICE_PARAMS[product][0]
        if row:
            print(f"{product:<12} {base:10d} {row['inventory']:10.0f} {row['price']:6d}")
        else:
            print(f"{product:<12} {base:10d} {'(no data)':>10} {'':>6}")


def cross_validate(samples):
    print("\n=== Cross-validation: does the live engine match the documented formula? ===")
    header = f"{'TURN':>5} {'PRODUCT':<10} {'OBS INV':>9} {'OBS PRICE':>9} {'PREDICTED':>9} {'MATCH':>6}"
    print(header)
    print("-" * len(header))
    mismatches = 0
    checked = 0
    for row in samples:
        predicted = price_at(row["product"], row["inventory"])
        match = predicted == row["price"]
        checked += 1
        if not match:
            mismatches += 1
        print(
            f"{row['turn']:5d} {row['product']:<10} {row['inventory']:9.0f} "
            f"{row['price']:9d} {predicted:9d} {'OK' if match else 'DIFF':>6}"
        )
    print(f"\n{checked - mismatches}/{checked} observed points match the documented formula exactly.")


if __name__ == "__main__":
    print("Running main.py vs starter, sampling market once per day (30 samples/product)...")
    result = run_and_sample_market()
    print(
        f"Episode finished: main.py reward={result['final_reward_p0']}, "
        f"starter reward={result['final_reward_p1']}, status={result['final_status']}"
    )

    print_observed_table(result["samples"])
    print_snapshot_table(result["samples"])
    cross_validate(result["samples"])

    print("\n\n=== ANALYTICAL price(inventory) curves (documented formula, wide sweep) ===")
    for product in FOCUS_PRODUCTS:
        print_analytical_curve(product)
