"""Why harvest-before-collect nicked the bank: herd mix + yarn vs live.

Usage:
    .venv/Scripts/python.exe experiments/_why_harvest.py
"""
from pathlib import Path

from kaggle_environments import make

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "experiments" / "_facts_v20.py"
V20 = str(ROOT / "agents" / "route_v20.py")
SEEDS = (0, 8)

OLD = """        if held >= max_held:
            return act_here(["HARVEST"])
        if tile.get("fertilizer_available"):
            return act_here(["COLLECT_FERTILIZER"])
        if held > 0 and (held >= max_held - 2 or day >= SEASON_DAYS - 2):
            return act_here(["HARVEST"])
"""
NEW = """        if held > 0:
            return act_here(["HARVEST"])
        if tile.get("fertilizer_available"):
            return act_here(["COLLECT_FERTILIZER"])
"""


def _obs(raw):
    return dict(raw) if not isinstance(raw, dict) else raw


def mix(farm, private):
    c = s = 0
    for row in farm.get("tiles") or []:
        for t in row:
            if isinstance(t, dict):
                if t.get("animal") == "COW":
                    c += 1
                elif t.get("animal") == "SHEEP":
                    s += 1
    shed = private.get("shed") or {}
    c += int(shed.get("COW") or 0)
    s += int(shed.get("SHEEP") or 0)
    for inv in private.get("inventories") or []:
        if isinstance(inv, dict):
            c += int(inv.get("COW") or 0)
            s += int(inv.get("SHEEP") or 0)
    return c, s


def run(agent, seed):
    env = make(
        "kaggriculture",
        configuration={"episodeSteps": 720, "seed": seed},
        debug=False,
    )
    env.run([str(agent), V20])
    prev = None
    yarn = None
    buys = []
    eod = {}
    land = []
    for step in env.steps:
        raw = step[0]
        obs = _obs(raw.observation)
        act = raw.get("action") if hasattr(raw, "get") else None
        act = act or getattr(raw, "action", None) or {}
        if prev is None:
            prev = obs
            continue
        day = prev.get("day", 0)
        hour = prev.get("hour", 0)
        farm = (prev.get("farms") or [{}])[0]
        priv = prev.get("private") or {}
        shops = list((prev.get("town") or {}).get("unlocked_shops") or [])
        if yarn is None and "YARN_STORE" in shops:
            yarn = (day, hour, shops[:3])
        for o in act.get("market") or []:
            if o and o[0] == "BUY_LAND":
                land.append((day, hour))
            if o and o[0] == "BUY_ANIMAL" and day >= 6:
                qty = o[2] if len(o) > 2 else 1
                buys.append((day, hour, o[1], qty, int(farm.get("money") or 0), shops[:3]))
        if hour == 23:
            c, s = mix(farm, priv)
            eod[day] = (c, s, c + s, int(farm.get("money") or 0))
        prev = obs
    last = _obs(env.steps[-1][0].observation)
    farm = (last.get("farms") or [{}])[0]
    priv = last.get("private") or {}
    c, s = mix(farm, priv)
    return {
        "bank": int(farm.get("money") or 0),
        "end": (c, s, c + s),
        "yarn": yarn,
        "land": land,
        "buys": buys,
        "eod": eod,
    }


def show(label, seed, r):
    print(f"\n== {label} seed={seed} bank={r['bank']} land={r['land']} yarn={r['yarn']} end={r['end']}")
    print("  eod d7-d20  C/S/tot  $")
    for d in range(7, 21):
        if d in r["eod"]:
            c, s, t, m = r["eod"][d]
            print(f"    d{d:<2} {c}/{s}/{t}  ${m}")
    print("  BUY_ANIMAL from d6:")
    for row in r["buys"]:
        print(f"    d{row[0]}h{row[1]:02d} {row[2]} x{row[3]}  pre${row[4]}  shops={row[5]}")


def main():
    text = SRC.read_text(encoding="utf-8")
    if OLD not in text:
        raise SystemExit("harvest block not found")
    dest = ROOT / "experiments" / "_facts_harvest_arm.py"
    dest.write_text(text.replace(OLD, NEW, 1), encoding="utf-8")
    arms = (("live", SRC), ("harvest", dest))
    for seed in SEEDS:
        for name, path in arms:
            show(name, seed, run(path, seed))


if __name__ == "__main__":
    main()
