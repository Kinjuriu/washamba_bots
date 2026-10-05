"""WANTAM gate report: Sonnet's top-12 throughput measures on our own games.
Targets (SCHEDULER_INFERENCE.md, top-12): actions/visit ~2, moves per useful action
0.60-0.71 (d15-22), idle share 1-3% after d8, wheat plantings >=4.6/day d23-29,
crew ~11 d8-14 / ~12 d15-22, unintended escapes 0."""
import sys, os
from collections import Counter
MOVES = {"NORTH", "SOUTH", "EAST", "WEST"}

def metrics(steps, seat, start, starve_log=None):
    n_units = moves = useful = idle = 0
    visits = 0; vis_actions = 0
    last = {}          # unit idx -> (tile, had_useful)
    wheat_plant = Counter(); crew = Counter(); days = Counter()
    mv_d = Counter(); us_d = Counter()
    for t in range(start + 1, len(steps)):
        act = steps[t][seat].action or {}
        o = steps[t - 1][0].observation
        f = o.farms[seat]
        day = (t - 1) // 24; hour = (t - 1) % 24
        pos = [tuple(f["farmer"])] + [tuple(h) for h in f["hands"]]
        units = [act.get("farmer", ["PASS"])] + list(act.get("hands", []))
        if hour == 12:
            crew[day] = len(pos) - 1
        for i, u in enumerate(units[:len(pos)]):
            op = (u or ["PASS"])[0]
            n_units += 1
            if hour == 0 and i:   # new hands appear; reset per day
                pass
            key = (day, i)
            if op in MOVES:
                moves += 1; mv_d[day] += 1
                if key in last and last[key][1]:
                    visits += 1
                last[key] = (None, False)
            elif op == "PASS":
                idle += 1
            else:
                useful += 1; us_d[day] += 1; vis_actions += 1
                if op == "PLANT" and len(u) > 1 and u[1] == "WHEAT":
                    wheat_plant[day] += 1
                prev = last.get(key)
                if prev is None or prev[0] != pos[i]:
                    if prev is not None and prev[1]:
                        visits += 1
                last[key] = (pos[i], True)
    visits += sum(1 for v in last.values() if v[1])
    # escapes: animal present at dawn d, structure without animal at dawn d+1
    esc = Counter(); intended = 0
    for d in range(start // 24, 29):
        a = steps[d * 24][0].observation.farms[seat]["tiles"]
        b = steps[(d + 1) * 24][0].observation.farms[seat]["tiles"]
        for y in range(10):
            for x in range(10):
                ta, tb = a[y][x], b[y][x]
                if isinstance(ta, dict) and "animal" in ta and isinstance(tb, dict) and "animal" not in tb \
                        and tb.get("kind") in ("COOP", "PASTURE") and ta.get("consecutive_unfed", 0) >= 1:
                    esc[d] += 1
                    if starve_log and (x, y) in starve_log.get(d, set()):
                        intended += 1
    lost = Counter()
    for d in range(start // 24, 29):
        a = steps[d * 24][0].observation.farms[seat]["tiles"]
        b = steps[(d + 1) * 24][0].observation.farms[seat]["tiles"]
        for y in range(10):
            for x in range(10):
                ta, tb = a[y][x], b[y][x]
                if isinstance(ta, dict) and ta.get("kind") == "PLANT" and isinstance(tb, dict) and tb.get("kind") == "WEED":
                    lost[ta["crop"]] += 1
    mid = [d for d in range(15, 23)]
    mpu_mid = sum(mv_d[d] for d in mid) / max(1, sum(us_d[d] for d in mid))
    return {"actions_per_visit": round(vis_actions / max(1, visits), 2),
            "moves_per_useful": round(moves / max(1, useful), 2),
            "moves_per_useful_d15_22": round(mpu_mid, 2),
            "idle_share": round(idle / max(1, n_units), 3),
            "wheat_plant_per_day_d23_29": round(sum(wheat_plant[d] for d in range(23, 30)) / 7, 1),
            "crew_d15_22": round(sum(crew[d] for d in mid) / len(mid), 1),
            "escapes": sum(esc.values()), "escapes_unintended": sum(esc.values()) - intended,
            "useful": useful, "moves": moves, "crops_lost": dict(lost)}

if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import h14
    from kaggle_environments import make
    kind = sys.argv[1]
    for seed in [int(s) for s in sys.argv[2].split(",")]:
        seat = seed % 2
        for k in (None, kind):
            a = [h14.load_last_callable(h14.BASE), h14.load_last_callable(h14.BASE)]
            if k: a[seat] = h14.hybrid(k)
            env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed}); env.run(a)
            sl = getattr(a[seat].state["ctrl"], "starve_log", None) if k else None
            m = metrics(env.steps, seat, h14.HANDOVER, sl)
            print(seed, (k or "W3").ljust(7), int(env.steps[-1][seat].reward), m)
