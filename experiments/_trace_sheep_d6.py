"""Sheep CARE/FEED/HARVEST and yield_units d0-d7 vs v20, seed 0."""
from collections import Counter
from kaggle_environments import make

AGENT = "experiments/_facts_v20.py"
V20 = "agents/route_v20.py"


def _obs(raw):
    return dict(raw) if not isinstance(raw, dict) else raw


def sheep_tiles(farm):
    out = []
    for y, row in enumerate(farm.get("tiles") or []):
        for x, t in enumerate(row):
            if isinstance(t, dict) and t.get("animal") == "SHEEP":
                out.append((x, y, t))
    return out


def units(act):
    return [act.get("farmer") or []] + list(act.get("hands") or [])


def main():
    env = make(
        "kaggriculture",
        configuration={"episodeSteps": 720, "seed": 0},
        debug=False,
    )
    env.run([AGENT, V20])
    prev = [None, None]
    day_act = [Counter(), Counter()]
    for step in env.steps:
        for seat in (0, 1):
            raw = step[seat]
            obs = _obs(raw.observation)
            act = raw.get("action") if hasattr(raw, "get") else None
            act = act or getattr(raw, "action", None) or {}
            if prev[seat] is None:
                prev[seat] = obs
                continue
            p = prev[seat]
            day = p.get("day", 0)
            hour = p.get("hour", 0)
            farm = (p.get("farms") or [{}, {}])[seat]
            if day > 7:
                prev[seat] = obs
                continue
            for u in units(act):
                if u:
                    day_act[seat][(day, u[0])] += 1
            if hour == 0 or hour == 23:
                tiles = sheep_tiles(farm)
                bits = []
                for x, y, t in tiles:
                    bits.append(
                        f"({x},{y}) yld={t.get('yield_units', 0)} "
                        f"fed={int(bool(t.get('fed_today')))} "
                        f"care={int(bool(t.get('cared_today')))} "
                        f"bonus={t.get('pending_care_bonus', 0)} "
                        f"unfed={t.get('consecutive_unfed', 0)} "
                        f"placed={t.get('placed_day')}"
                    )
                tag = "EOD" if hour == 23 else "h00"
                print(f"  seat{seat} d{day}{tag} n={len(tiles)} " + " | ".join(bits))
            if hour == 23:
                print(
                    f"    seat{seat} d{day} acts "
                    f"FEED={day_act[seat][(day,'FEED')]} "
                    f"CARE={day_act[seat][(day,'CARE')]} "
                    f"HARVEST={day_act[seat][(day,'HARVEST')]} "
                    f"COLLECT={day_act[seat][(day,'COLLECT_FERTILIZER')]}"
                )
                day_act[seat] = Counter()
            prev[seat] = obs


if __name__ == "__main__":
    main()
