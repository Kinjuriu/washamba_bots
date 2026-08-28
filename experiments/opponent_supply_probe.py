"""Data-collection probe for the opponent-supply-forecast audit.

RESEARCH ONLY. Does not touch main.py or pricing.py. Not wired into any
decision. Run directly:

    .venv/Scripts/python.exe experiments/opponent_supply_probe.py [n_seeds]

For each self-play episode (main.py vs main.py), walks every turn's
observation and records, per crop:

  - opp_yield[t]   = sum of tile["yield_units"] over the opponent's own
                     PLANT tiles of that crop, read directly from
                     obs["farms"][1-player] (public, shared object -
                     verified against kaggriculture.py's _new_plant /
                     _daily_refresh_plants / HARVEST handler: this is the
                     EXACT unit count HARVEST would move into their
                     inventory right now, not an estimate).
  - mkt_inv[t]     = obs["market"]["inventory"][crop]
  - mkt_price[t]   = obs["market"]["prices"][crop]

Then, for a set of forward horizons (in turns), computes:

  - Pearson correlation of opp_yield[t] against price_change[t, t+N]
    and inventory_delta[t, t+N].
  - A grouped comparison: turns where opp_yield[t] > 0 for a crop vs.
    turns where it is exactly 0, mean price_change and inventory_delta
    in each group.

This treats self-play as two identical, independent agents - "opponent"
here is just player index 1-player. Self-play is used deliberately (per
CLAUDE.md: "the honest number", the only local harness with a real
contested order book) rather than a built-in, which never sells and
would leave the market pristine, making a supply signal untestable.
"""
import sys
import statistics

from kaggle_environments import make

try:
    from kaggle_environments.envs.kaggriculture.kaggriculture import CROPS, ANIMALS
except ImportError:
    CROPS = {}
    ANIMALS = {}

ALL_PRODUCTS = list(CROPS.keys()) + [a["product"] for a in ANIMALS.values()]
HORIZONS = [24, 48, 96]  # 1, 2, 4 days


def opponent_standing_yield(obs):
    farms = obs.get("farms") or []
    player = obs.get("player", 0)
    if len(farms) < 2:
        return {}
    opp = farms[1 - player] or {}
    totals = {}
    for row in opp.get("tiles") or []:
        for tile in row or []:
            if not isinstance(tile, dict):
                continue
            if tile.get("kind") == "PLANT":
                totals[tile["crop"]] = totals.get(tile["crop"], 0) + tile.get("yield_units", 0)
            elif "animal" in tile:
                product = ANIMALS.get(tile["animal"], {}).get("product")
                if product:
                    totals[product] = totals.get(product, 0) + tile.get("yield_units", 0)
    return totals


def collect_episode(seed):
    env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed}, debug=False)
    env.run(["main.py", "main.py"])
    series = []
    for step in env.steps:
        obs = step[0].observation
        opp_yield = opponent_standing_yield(obs)
        market = obs.get("market") or {}
        inv = market.get("inventory") or {}
        prices = market.get("prices") or {}
        series.append({
            "t": obs.get("step", len(series)),
            "day": obs.get("day", 0),
            "opp_yield": opp_yield,
            "inv": dict(inv),
            "price": dict(prices),
        })
    return series


def pearson(xs, ys):
    n = len(xs)
    if n < 2:
        return None
    mx, my = statistics.mean(xs), statistics.mean(ys)
    sx = sum((x - mx) ** 2 for x in xs) ** 0.5
    sy = sum((y - my) ** 2 for y in ys) ** 0.5
    if sx == 0 or sy == 0:
        return None
    cov = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    return cov / (sx * sy)


def analyze(all_series, products):
    print(f"episodes: {len(all_series)}, turns/episode: {len(all_series[0]) if all_series else 0}")
    print()
    for product in products:
        nonzero_count = 0
        total_count = 0
        for series in all_series:
            for row in series:
                total_count += 1
                if row["opp_yield"].get(product, 0) > 0:
                    nonzero_count += 1
        pct = 100 * nonzero_count / total_count if total_count else 0
        print(f"=== {product}: opp_yield > 0 on {nonzero_count}/{total_count} turns ({pct:.1f}%) ===")
        if nonzero_count == 0:
            print("  (signal never positive - skipping correlation)")
            print()
            continue

        for N in HORIZONS:
            xs_price, ys_price = [], []
            xs_inv, ys_inv = [], []
            group0_price, group_pos_price = [], []
            group0_inv, group_pos_inv = [], []
            for series in all_series:
                n = len(series)
                for i in range(n - N):
                    y = series[i]["opp_yield"].get(product, 0)
                    p0 = series[i]["price"].get(product)
                    p1 = series[i + N]["price"].get(product)
                    inv0 = series[i]["inv"].get(product)
                    inv1 = series[i + N]["inv"].get(product)
                    if p0 is None or p1 is None or inv0 is None or inv1 is None:
                        continue
                    dprice = p1 - p0
                    dinv = inv1 - inv0
                    xs_price.append(y)
                    ys_price.append(dprice)
                    xs_inv.append(y)
                    ys_inv.append(dinv)
                    if y > 0:
                        group_pos_price.append(dprice)
                        group_pos_inv.append(dinv)
                    else:
                        group0_price.append(dprice)
                        group0_inv.append(dinv)

            r_price = pearson(xs_price, ys_price)
            r_inv = pearson(xs_inv, ys_inv)
            m0p = statistics.mean(group0_price) if group0_price else float("nan")
            mpp = statistics.mean(group_pos_price) if group_pos_price else float("nan")
            m0i = statistics.mean(group0_inv) if group0_inv else float("nan")
            mpi = statistics.mean(group_pos_inv) if group_pos_inv else float("nan")
            print(f"  horizon N={N:>3} turns:")
            print(f"    corr(opp_yield, price_change)     = {r_price}")
            print(f"    corr(opp_yield, inventory_change)  = {r_inv}")
            print(f"    mean price_change     | opp_yield=0: {m0p:8.2f}  | opp_yield>0: {mpp:8.2f}  (n0={len(group0_price)}, n+={len(group_pos_price)})")
            print(f"    mean inventory_change  | opp_yield=0: {m0i:8.2f}  | opp_yield>0: {mpi:8.2f}")
        print()


def main():
    n_seeds = int(sys.argv[1]) if len(sys.argv) > 1 else 6
    all_series = []
    for seed in range(n_seeds):
        print(f"collecting seed {seed}...", file=sys.stderr)
        all_series.append(collect_episode(seed))

    focus_products = ["MELON", "WHEAT", "TOMATO", "STRAWBERRY", "CARROT", "WOOL", "EGG", "MILK"]
    focus_products = [p for p in focus_products if p in ALL_PRODUCTS] or ALL_PRODUCTS
    analyze(all_series, focus_products)


if __name__ == "__main__":
    main()
