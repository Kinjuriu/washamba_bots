import sys, json, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import h14
from kaggle_environments import make
from collections import Counter, defaultdict

def run(seed, seat, kind):
    a = [h14.load_last_callable(h14.BASE), h14.load_last_callable(h14.BASE)]
    if kind: a[seat] = h14.hybrid(kind)
    env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})
    env.run(a)
    return env

def summarize(env, seat, start=336):
    steps = env.steps
    acts = Counter(); per_day = defaultdict(Counter); sells = Counter(); buys = Counter()
    useful = moves = passes = 0
    for t in range(start + 1, len(steps)):
        act = steps[t][seat].action or {}
        obs_prev = steps[t - 1][0].observation
        day = (t - 1) // 24
        units = [act.get("farmer", ["PASS"])] + list(act.get("hands", []))
        for u in units:
            op = u[0] if u else "PASS"
            if op in ("NORTH", "SOUTH", "EAST", "WEST"): moves += 1; per_day[day]["MOVE"] += 1
            elif op == "PASS": passes += 1; per_day[day]["PASS"] += 1
            else: useful += 1; acts[op] += 1; per_day[day][op] += 1
        for o in act.get("market", []) or []:
            if o and o[0] == "SELL": sells[o[1]] += int(o[2]) if len(o) > 2 else 1
            if o and o[0] in ("BUY_SEED", "BUY_ANIMAL", "BUY_PRODUCT", "HIRE", "BUY_LAND"):
                buys[(o[0], o[1] if len(o) > 1 else "")] += int(o[2]) if len(o) > 2 and str(o[2]).isdigit() else 1
    # board census at each dawn
    census = {}
    for d in (14, 17, 20, 23, 26, 29):
        f = steps[d * 24][0].observation.farms[seat]
        c = Counter()
        for row in f["tiles"]:
            for tt in row:
                if isinstance(tt, dict):
                    c[tt.get("crop") or tt.get("animal") or tt.get("kind")] += 1
        c["money"] = int(f["money"]); census[d] = dict(c)
    return {"useful": useful, "moves": moves, "pass": passes, "acts": dict(acts),
            "sells_req": dict(sells), "buys": {f"{k[0]}:{k[1]}": v for k, v in buys.items()}, "census": census,
            "final": steps[-1][seat].reward}

if __name__ == "__main__":
    seed = int(sys.argv[1]); seat = seed % 2; kind = sys.argv[2] if len(sys.argv) > 2 else "peter"
    for k in (None, kind):
        env = run(seed, seat, k)
        s = summarize(env, seat)
        print("=====", k or "W3")
        for key in ("final", "useful", "moves", "pass", "acts", "sells_req", "buys"): print(key, s[key])
        for d, c in s["census"].items(): print(" d", d, c)
