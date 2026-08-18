"""Extract the strategic shape of a real ladder episode.

The host publishes daily dumps of top-rated episodes as standard
kaggle_environments replays (kaggle/kaggriculture-episodes-<date>). This
pulls out the handful of signals that distinguish the dominant ladder
strategy from ours: when land is bought, how big the crew gets, which
animals, and the per-crop planting windows.
"""
import json
import sys
from collections import Counter, defaultdict

path = sys.argv[1]
d = json.load(open(path))
info = d.get("info") or {}
print(f"episode {info.get('EpisodeId')}  teams {info.get('TeamNames')}")
print(f"  rewards {d.get('rewards')}")

for p in (0, 1):
    land, animals, m = [], Counter(), Counter()
    units, tiles, sells = defaultdict(int), {}, defaultdict(int)
    plant = defaultdict(Counter)
    for st in d["steps"]:
        obs = st[p].get("observation") or {}
        day = obs.get("day")
        a = st[p].get("action") or {}
        if day is None or not isinstance(a, dict):
            continue
        units[day] = max(units[day], 1 + len(list(a.get("hands") or [])))
        for x in [a.get("farmer") or []] + list(a.get("hands") or []):
            if x and x[0] == "PLANT" and len(x) > 1:
                plant[day][x[1]] += 1
        for o in (a.get("market") or []):
            if not o:
                continue
            m[o[0]] += 1
            if o[0] == "BUY_LAND":
                land.append(day)
            if o[0] == "BUY_ANIMAL":
                animals[o[1]] += 1
            if o[0] == "SELL":
                sells[day] += 1
        f = (obs.get("farms") or [{}])[p]
        if f.get("tiles"):
            tiles[day] = sum(1 for r in f["tiles"] for t in r if t != "LOCKED")
    windows = {}
    for day, c in plant.items():
        for crop, n in c.items():
            lo, hi, tot = windows.get(crop, (99, -1, 0))
            windows[crop] = (min(lo, day), max(hi, day), tot + n)
    print(f"  --- seat {p} ---")
    print(f"    BUY_LAND days {land}  tiles {min(tiles.values(), default=0)} -> {max(tiles.values(), default=0)}")
    print(f"    animals {dict(animals)}  HIRE {m['HIRE']}  SELL {m['SELL']}  BUY_PRODUCT {m['BUY_PRODUCT']}")
    print(f"    units by day 0/6/9/12/20/29: {[units.get(x, 0) for x in (0, 6, 9, 12, 20, 29)]}")
    print(f"    first sell-heavy day: {min((day for day, n in sorted(sells.items()) if n >= 10), default=None)}")
    for crop, (lo, hi, tot) in sorted(windows.items(), key=lambda kv: -kv[1][2]):
        print(f"      {crop:11s} days {lo:2d}-{hi:2d}  total {tot}")
