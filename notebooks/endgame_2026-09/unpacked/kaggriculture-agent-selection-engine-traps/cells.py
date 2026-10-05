# ---- cell 3
"""Agent selection harness for Kaggriculture.

Kaggle loads a submission by file path and selects the last callable
bound in the module namespace. Always health-check by path before
submitting. An agent that returns exactly the starting money is
passing every turn, not playing badly.
"""
import glob
import statistics
from kaggle_environments import make

# Competition config. Package defaults differ and will silently
# produce wrong results. Verify with starter_vs_pass() below.
CFG = {
    "episodeSteps": 720,
    "farmHandCostMult": 1,
    "startingMoney": 3000,
    "townCenterSellInterval": 12,
    "townShopSellInterval": 4,
    "townShopUnlockInterval": 3,
}


def starter_vs_pass():
    """Config check. Must return [3509, 3000] on engine 1.32.7."""
    e = make("kaggriculture", configuration=dict(CFG, seed=0))
    e.run(["starter", "pass"])
    return [round(s.reward) for s in e.steps[-1]]


def health_check(path):
    """Return final bank against a passive opponent.

    A value at or near 3000 means the agent never acted, usually a
    last-callable entrypoint problem rather than a weak strategy.
    """
    e = make("kaggriculture", configuration=dict(CFG, seed=0))
    e.run([path, "pass"])
    return e.steps[-1][0].reward


def head_to_head(candidate, baseline, seeds=(0, 1, 2)):
    """Play candidate against baseline in both seats across seeds.

    Returns (wins, games, mean money margin). Margin below about
    5,000 has not moved ladder rating in practice.
    """
    wins = 0
    games = 0
    margins = []
    for seed in seeds:
        for seat in (0, 1):
            e = make("kaggriculture", configuration=dict(CFG, seed=seed))
            pair = [candidate, baseline] if seat == 0 else [baseline, candidate]
            e.run(pair)
            final = e.steps[-1]
            mine = final[seat].reward
            theirs = final[1 - seat].reward
            margins.append(mine - theirs)
            wins += mine > theirs
            games += 1
    return wins, games, statistics.mean(margins)


def rank_candidates(baseline, folder="/kaggle/input/notebooks"):
    """Test every agent in folder against baseline, best first."""
    results = []
    for path in sorted(set(glob.glob(folder + "/**/*.py", recursive=True))):
        if path == baseline:
            continue
        if health_check(path) <= 3100:
            continue
        wins, games, margin = head_to_head(path, baseline)
        if wins > games / 2:
            results.append((wins, margin, path))
            print(wins, "/", games, round(margin), path, flush=True)
    return sorted(results, reverse=True)

# ---- cell 4
print("config check:", starter_vs_pass(), "(must be [3509, 3000])")

# ---- cell 6
"""Replay analysis for Kaggriculture.

Score is set mostly by the town shop draw rather than by farming
quality. These functions measure that from downloaded replays.
"""
import collections
import json

SHOP_PRODUCTS = {
    "BAKERY": ("EGG", "WHEAT"),
    "PIZZA_SHOP": ("MILK", "TOMATO", "WHEAT"),
    "BRUNCH_SPOT": ("EGG", "WHEAT", "STRAWBERRY"),
    "YARN_STORE": ("WOOL",),
    "ICE_CREAM_SHOP": ("STRAWBERRY", "MILK", "WHEAT"),
    "PET_CAFE": ("CARROT",),
    "SMOOTHIE_SHOP": ("STRAWBERRY", "MILK"),
    "FARMERS_MARKET": ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY"),
}


def load(path):
    raw = json.load(open(path))
    return raw["steps"] if isinstance(raw, dict) and "steps" in raw else raw


def shop_demand(steps):
    """Total shop demand per product. Single-product shops count 2x."""
    last = steps[-1][0].get("observation") or {}
    shops = list((last.get("town") or {}).get("unlocked_shops") or [])
    demand = collections.Counter()
    for shop in shops:
        products = SHOP_PRODUCTS.get(shop, ())
        for product in products:
            demand[product] += 2 if len(products) == 1 else 1
    return demand


def final_prices(steps):
    last = steps[-1][0].get("observation") or {}
    return (last.get("market") or {}).get("prices") or {}


def sold_by_player(steps, player):
    """Units sold per product, read from the action stream."""
    sold = collections.Counter()
    for step in steps:
        action = (step[player] or {}).get("action") if player < len(step) else None
        if not isinstance(action, dict):
            continue
        for order in action.get("market") or []:
            if order and order[0] == "SELL" and len(order) > 2:
                sold[order[1]] += order[2]
    return sold