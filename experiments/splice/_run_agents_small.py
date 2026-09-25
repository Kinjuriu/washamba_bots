"""experiments/tapes/run_agents.py with Pool(2) and realized-price instrumentation.

Builder A copy (the original is untouched): same arguments, same bank summary lines, run
on 2 workers so another builder's episodes keep the CPU. Each worker also wraps the
engine's _commit_unit, so every executed SELL is logged with its seat, interpreter step
and realized price; per game and seat it records units and revenue per product, split
at step 192 (the splice handover).

Usage (relative paths only in the candidate list):
  timeout 2400 .venv/Scripts/python.exe experiments/splice/_run_agents_small.py \
      agents/.wb_w3_sells.py 900 908 agents/w3_herdsafe2700.py fam/wb_w3_sells.jsonl
"""
import json
import os
import statistics as st
import sys
from multiprocessing import Pool

sys.path.insert(0, "C:/Users/HP/Spidey-Hub/washamba_bots/experiments")
ROUTER = "C:/Users/HP/Spidey-Hub/washamba_bots/agents/router_yhay.py"
SPLIT = 192
PREMIUM = ("WOOL", "MILK", "STRAWBERRY")

_CUR = {}
_LOG = []


def _instrument():
    import kaggle_environments.envs.kaggriculture.kaggriculture as K
    if getattr(K, "_wb_instrumented", False):
        return
    orig_pm, orig_cu = K._process_market, K._commit_unit

    def _pm(state, env):
        _CUR["farms"] = state[0].observation.farms
        _CUR["step"] = state[0].observation.get("step", 0)
        return orig_pm(state, env)

    def _cu(op, item, price, farm, private, market, shed_capacity=100):
        ok = orig_cu(op, item, price, farm, private, market, shed_capacity)
        if ok and op == "SELL":
            _LOG.append((0 if farm is _CUR["farms"][0] else 1, _CUR["step"], item, price))
        return ok

    K._process_market, K._commit_unit = _pm, _cu
    K._wb_instrumented = True


def _sells(seat):
    out = {}
    for s, step, item, price in _LOG:
        if s != seat:
            continue
        row = out.setdefault(item, [0, 0, 0, 0])     # units<192, rev<192, units>=192, rev>=192
        k = 0 if step < SPLIT else 2
        row[k] += 1
        row[k + 1] += price
        day = out.setdefault("_days", {}).setdefault(item, {}).setdefault(str(step // 24), [0, 0])
        day[0] += 1
        day[1] += price
    return out


def _herd(env, seat, day=12):
    """Animals on the farm at dawn of `day` (the desync signature)."""
    obs = env.steps[min(day * 24, len(env.steps) - 1)][0]["observation"]
    return sum(1 for row in obs["farms"][seat]["tiles"] for t in row if isinstance(t, dict) and "animal" in t)


def job(args):
    from kaggle_environments import make
    _instrument()
    cand, opp, seed = args

    def play(a, b):
        _LOG.clear()
        env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed}); env.run([a, b])
        l, r = env.steps[-1]
        if l.status != "DONE" or r.status != "DONE" or l.reward == 3000 or r.reward == 3000:
            print("NON-DONE/INERT:", a, b, seed, l.status, r.status, l.reward, r.reward, flush=True)
        s0, s1 = _sells(0), _sells(1)
        s0["_herd12"], s1["_herd12"] = _herd(env, 0), _herd(env, 1)
        return l.reward, r.reward, s0, s1

    a0, b1, sa0, sb1 = play(cand, opp)
    b0, a1, sb0, sa1 = play(opp, cand)
    return cand, seed, a0, b1, a1, b0, {"cand": [sa0, sa1], "opp": [sb1, sb0]}


def _price_table(res):
    """Realized average price per premium product, candidate vs opponent, from step 192."""
    lines = []
    for item in PREMIUM:
        cols = []
        for who in ("cand", "opp"):
            u = r = u0 = r0 = 0
            for row in res:
                for d in row[6][who]:
                    x = d.get(item)
                    if x:
                        u0 += x[0]; r0 += x[1]; u += x[2]; r += x[3]
            cols.append((u, r, u0, r0))
        (cu, cr, cu0, cr0), (ou, orr, ou0, or0) = cols
        fmt = lambda u, r: f"{r / u:7.1f} x {u:5d}" if u else "      - x     0"
        # Same-day matched: on days both sides sold the item (from step 192), compare their
        # average prices weighted by the smaller volume. Removes the composition effect of
        # one side selling more units in a dearer part of the season.
        diff = weight = 0
        for row in res:
            for g in (0, 1):
                dc = row[6]["cand"][g].get("_days", {}).get(item, {})
                do = row[6]["opp"][g].get("_days", {}).get(item, {})
                for day, (u1, r1) in dc.items():
                    if int(day) < SPLIT // 24 or day not in do:
                        continue
                    u2, r2 = do[day]
                    w = min(u1, u2)
                    diff += w * (r1 / u1 - r2 / u2)
                    weight += w
        matched = f"{diff / weight:+6.1f}/unit over {weight} matched units" if weight else "n/a"
        lines.append(f"   {item:10} from step {SPLIT}: cand {fmt(cu, cr)}   opp {fmt(ou, orr)}"
                     f"   | same-day cand-opp {matched}   | before: cand {fmt(cu0, cr0)}   opp {fmt(ou0, or0)}")
    herd = [(g["_herd12"], o["_herd12"]) for row in res for g, o in zip(row[6]["cand"], row[6]["opp"])]
    lines.append(f"   animals at day 12, cand vs opp: {sum(h[0] for h in herd)} vs {sum(h[1] for h in herd)}"
                 f" over {len(herd)} games")
    return lines


if __name__ == "__main__":
    cands = [os.path.abspath(p) for p in sys.argv[1].split(",")]
    seeds = [int(x) for x in sys.argv[2].split(",")] if "," in sys.argv[2] else list(range(int(sys.argv[2]), int(sys.argv[3])))
    opp = os.path.abspath(sys.argv[4]) if len(sys.argv) > 4 else ROUTER
    out = sys.argv[5] if len(sys.argv) > 5 else "fam/agents_results.jsonl"
    jobs = [(c, opp, s) for c in cands for s in seeds]
    with Pool(2) as pool: res = pool.map(job, jobs)
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    with open(out, "a") as f:
        for c, s, a0, b1, a1, b0, sells in res:
            f.write(json.dumps({"cand": os.path.basename(c), "opp": os.path.basename(opp), "seed": s,
                                "seat0": [a0, b1], "seat1": [a1, b0], "sells": sells}) + "\n")
    for c in cands:
        rs = [r for r in res if r[0] == c]
        diffs = [r[2] - r[3] for r in rs] + [r[4] - r[5] for r in rs]
        w = sum(d > 0 for d in diffs); l = sum(d < 0 for d in diffs)
        print(f"{os.path.basename(c):28} vs {os.path.basename(opp):16} {w}-{l} of {len(diffs)}  mean {st.mean(diffs):+8,.0f}  median {st.median(diffs):+8,.0f}  min bank {min(min(r[2], r[4]) for r in rs):,.0f}  worst {min(diffs):+,.0f}")
        print("   per-seed:", " ".join(f"{r[1]}:{(r[2]-r[3]+r[4]-r[5])/2:+.0f}" for r in rs))
        print("   realized average SELL price (avg x units, both seats pooled):")
        for line in _price_table(rs):
            print(line)
