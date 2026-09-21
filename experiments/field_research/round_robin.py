"""Round-robin of decoded public notebooks vs our routers. Win count first.

Usage: .venv/bin/python experiments/field_research/round_robin.py [n_seeds] [workers]
Each pairing plays every seed in both seats. Results append to
experiments/field_research/rr_results.jsonl so a rerun resumes.
"""
import itertools, json, os, sys, time
from concurrent.futures import ProcessPoolExecutor, as_completed

HERE = os.path.dirname(os.path.abspath(__file__))
PUB = os.path.join(HERE, "public_agents")
AGENTS = {
    "v56": f"{PUB}/v56.py", "v55": f"{PUB}/v55.py",
    "master_v3": f"{PUB}/master_v3.py", "idle_seller": f"{PUB}/idle_seller.py",
    "fam_lead": "agents/router_fam_lead.py", "fam_yarn": "agents/router_fam_yarn.py",
}
AGENTS = {k: v for k, v in AGENTS.items() if os.path.exists(v)}  # only what has been fetched
OUT = os.path.join(HERE, "rr_results.jsonl")


def play(job):
    a, b, seed = job
    import io, contextlib
    from kaggle_environments import make
    t = time.time()
    with contextlib.redirect_stderr(io.StringIO()):
        env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})
        env.run([AGENTS[a], AGENTS[b]])
    last = env.steps[-1]
    return {"a": a, "b": b, "seed": seed, "ra": last[0].reward, "rb": last[1].reward,
            "st": [s.status for s in last], "sec": round(time.time() - t, 1)}


def table(rows):
    names = list(AGENTS)
    w = {n: [0, 0, 0] for n in names}
    h2h = {}
    for r in rows:
        if r["ra"] is None or r["rb"] is None:
            continue
        for me, op, m, o in ((r["a"], r["b"], r["ra"], r["rb"]), (r["b"], r["a"], r["rb"], r["ra"])):
            k = 0 if m > o else 1 if m < o else 2
            w[me][k] += 1
            h2h.setdefault((me, op), [0, 0, 0])[k] += 1
    print("\nagent          W-L-T     win%")
    for n in sorted(names, key=lambda n: -w[n][0] / max(1, sum(w[n]))):
        print(f"{n:12s} {w[n][0]:3d}-{w[n][1]:3d}-{w[n][2]:2d}  {100*w[n][0]/max(1,sum(w[n])):5.1f}")
    print("\nhead to head (row W-L-T vs column)")
    print(" " * 12 + "".join(f"{n[:9]:>10s}" for n in names))
    for a in names:
        print(f"{a:12s}" + "".join(f"{'-'.join(map(str, h2h.get((a, b), ['', '', '']))) if a != b else '.':>10s}" for b in names))
    bad = [r for r in rows if r["st"] != ["DONE", "DONE"]]
    if bad:
        print("\nNON-DONE episodes:", [(r["a"], r["b"], r["seed"], r["st"]) for r in bad][:10])


if __name__ == "__main__":
    n_seeds = int(sys.argv[1]) if len(sys.argv) > 1 else 4
    workers = int(sys.argv[2]) if len(sys.argv) > 2 else max(1, (os.cpu_count() or 4) - 2)
    done = [json.loads(l) for l in open(OUT)] if os.path.exists(OUT) else []
    seen = {(r["a"], r["b"], r["seed"]) for r in done}
    jobs = [(a, b, s) for a, b in itertools.permutations(AGENTS, 2) for s in range(500, 500 + n_seeds)
            if (a, b, s) not in seen]
    print(f"{len(jobs)} games to play, {len(done)} cached, {workers} workers", flush=True)
    with ProcessPoolExecutor(workers) as ex, open(OUT, "a") as f:
        for i, fut in enumerate(as_completed([ex.submit(play, j) for j in jobs]), 1):
            r = fut.result(); done.append(r); f.write(json.dumps(r) + "\n"); f.flush()
            print(f"[{i}/{len(jobs)}] {r['a']} {r['ra']} vs {r['b']} {r['rb']} seed {r['seed']} ({r['sec']}s)", flush=True)
    table(done)
