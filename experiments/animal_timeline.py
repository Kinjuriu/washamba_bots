"""Day-by-day animal economics from a replay - ours or a top-ladder agent's.

The open question this exists to answer: we cannot sustain more than 4 animals
(5 collapses to $356 because the days 3-7 cash trough empties and the herd
starves), while top-ladder agents run 8-9. `replay_shape.py` shows us WHAT they
end up with; this shows the cash and feed path they take to get there.

Usage:
    python experiments/animal_timeline.py <replay.json>
    python experiments/animal_timeline.py <replay.json> --player 1
"""

import json
import sys
from collections import Counter, defaultdict

ANIMAL_KINDS = {"COOP", "PASTURE", "BARN", "STABLE"}


def timeline(path, player):
    d = json.load(open(path))
    info = d.get("info") or {}
    print(f"episode {info.get('EpisodeId')}  teams {info.get('TeamNames')}")
    print(f"rewards {d.get('rewards')}   reading player {player}")

    per_day = defaultdict(lambda: {
        "money": [], "animals": 0, "structures": 0, "wheat": 0, "tiles": 0,
        "crew": 0, "acts": Counter(),
    })

    for step in d["steps"]:
        cell = step[player]
        obs = cell.get("observation") or {}
        day = obs.get("day")
        if day is None:
            continue
        row = per_day[day]
        farms = obs.get("farms") or []
        if player < len(farms):
            farm = farms[player] or {}
            row["money"].append(farm.get("money", 0))
            tiles = farm.get("tiles") or []
            structures = animals = owned = 0
            for line in tiles:
                for t in line:
                    if t != "LOCKED":
                        owned += 1
                    if isinstance(t, dict) and t.get("kind") in ANIMAL_KINDS:
                        structures += 1
                        if t.get("animal"):
                            animals += 1
            row["structures"] = max(row["structures"], structures)
            row["animals"] = max(row["animals"], animals)
            row["tiles"] = max(row["tiles"], owned)
            row["crew"] = max(row["crew"], len(farm.get("hands") or []))
        priv = obs.get("private") or {}
        shed = priv.get("shed") or {}
        carried = sum(
            inv.get("WHEAT", 0)
            for inv in (priv.get("inventories") or [])
            if isinstance(inv, dict)
        )
        row["wheat"] = max(row["wheat"], shed.get("WHEAT", 0) + carried)

        act = cell.get("action")
        if not isinstance(act, dict):
            continue
        for unit in [act.get("farmer") or []] + list(act.get("hands") or []):
            if unit:
                row["acts"][unit[0]] += 1
        for order in act.get("market") or []:
            if not order:
                continue
            key = order[0]
            if key in ("BUY_ANIMAL", "BUY_PRODUCT", "BUY_SEED") and len(order) > 1:
                key = f"{key}:{order[1]}"
            row["acts"][key] += 1

    print()
    print(f"{'day':>3} {'money lo':>9} {'money hi':>9} {'tiles':>5} {'crew':>4} "
          f"{'pen':>3} {'herd':>4} {'wheat':>5} {'FEED':>4} {'buys':>22}")
    for day in sorted(per_day):
        r = per_day[day]
        money = r["money"] or [0]
        buys = " ".join(
            f"{k.split(':')[-1][:4]}x{v}"
            for k, v in r["acts"].items()
            if k.startswith(("BUY_ANIMAL", "BUY_PRODUCT", "BUY_LAND"))
        )
        print(f"{day:>3} {min(money):>9.0f} {max(money):>9.0f} {r['tiles']:>5} "
              f"{r['crew']:>4} {r['structures']:>3} {r['animals']:>4} "
              f"{r['wheat']:>5} {r['acts']['FEED']:>4} {buys:>22}")

    total = Counter()
    for r in per_day.values():
        total.update(r["acts"])
    print("\nseason totals:", {k: v for k, v in total.most_common(14)})


if __name__ == "__main__":
    p = 1 if "--player" in sys.argv and sys.argv[sys.argv.index("--player") + 1] == "1" else 0
    timeline(sys.argv[1], p)
