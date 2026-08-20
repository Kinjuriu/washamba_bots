"""Turn-by-turn actions for the opening days of a replay.

`animal_timeline.py` shows WHAT a top agent ends each day with. This shows the
exact order it does things in, which is the part we cannot guess: the
interleaving of BUILD / BUY_ANIMAL / PICKUP / PLACE decides whether a herd comes
up in parallel or serialises behind one round trip, and that is the difference
between four pens on day 0 and one pen on day 7.

Usage:
    python experiments/opening_trace.py <replay.json> [--player 1] [--days 3]
"""

import json
import sys


def trace(path, player, days):
    d = json.load(open(path))
    info = d.get("info") or {}
    print(f"episode {info.get('EpisodeId')}  teams {info.get('TeamNames')}  "
          f"rewards {d.get('rewards')}  player {player}")
    print(f"{'d':>2} {'h':>2} {'money':>6} {'farmer':<26} {'hands':<52} market")
    for step in d["steps"]:
        cell = step[player]
        obs = cell.get("observation") or {}
        day = obs.get("day")
        if day is None or day >= days:
            continue
        act = cell.get("action")
        if not isinstance(act, dict):
            continue
        farms = obs.get("farms") or []
        money = farms[player].get("money", 0) if player < len(farms) else 0
        farmer = " ".join(str(x) for x in (act.get("farmer") or [])) or "-"
        hands = " | ".join(
            " ".join(str(x) for x in h) for h in (act.get("hands") or []) if h
        ) or "-"
        market = " ".join(
            "".join(str(x) for x in o) for o in (act.get("market") or []) if o
        ) or "-"
        print(f"{day:>2} {obs.get('hour', 0):>2} {money:>6.0f} {farmer:<26} {hands:<52} {market}")


if __name__ == "__main__":
    a = sys.argv
    p = int(a[a.index("--player") + 1]) if "--player" in a else 0
    n = int(a[a.index("--days") + 1]) if "--days" in a else 3
    trace(a[1], p, n)
