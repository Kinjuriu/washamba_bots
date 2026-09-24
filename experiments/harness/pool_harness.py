"""Paired pool harness for Kaggriculture candidates.

Plays every candidate against every opponent on the same seeds, in both seats,
each game in its own subprocess so no agent module state leaks between games.
Scores the way Kaggle does: win / loss / tie only; mean margin is diagnostic.

Usage:
  python experiments/pool_harness.py \
      --agent w0=agents/w0_v15stack_control.py --agent w1=agents/w1_v15stack_race44.py \
      --agent v57=agents/public/v57.py \
      --candidates w1 --opponents w0 v57 --seeds 301-312 --workers 6 --out results/w1_gate.jsonl

Requires kaggle-environments==1.32.7 (Python 3.11+). The script refuses to run on any other version.
"""
import argparse, json, os, subprocess, sys, collections
from concurrent.futures import ThreadPoolExecutor

ENGINE = "1.32.7"
GAME = r"""
import sys, json, os
sys.path[:0] = [os.path.dirname(p) for p in (sys.argv[1], sys.argv[2])]
from kaggle_environments import make
env = make('kaggriculture', configuration={'seed': int(sys.argv[3])}, debug=False)
env.run([sys.argv[1], sys.argv[2]])
last = env.steps[-1]
print(json.dumps([last[0].reward, last[1].reward, last[0].status, last[1].status]))
"""


def seeds_from(text):
    out = []
    for part in text.split(","):
        if "-" in part:
            a, b = part.split("-"); out += list(range(int(a), int(b) + 1))
        else:
            out.append(int(part))
    return out


def play(job):
    a, b, pa, pb, seed, cand = job
    r = subprocess.run([sys.executable, "-c", GAME, os.path.abspath(pa), os.path.abspath(pb), str(seed)],
                       capture_output=True, text=True, timeout=900)
    try:
        ra, rb, sa, sb = json.loads(r.stdout.strip().splitlines()[-1])
    except Exception:
        return dict(a=a, b=b, seed=seed, cand=cand, error=r.stderr[-400:])
    return dict(a=a, b=b, seed=seed, cand=cand, ra=ra, rb=rb, sa=sa, sb=sb)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--agent", action="append", required=True, help="name=path")
    ap.add_argument("--candidates", nargs="+", required=True)
    ap.add_argument("--opponents", nargs="+", required=True)
    ap.add_argument("--seeds", default="301-312")
    ap.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) - 1))
    ap.add_argument("--out", default="results/pool_harness.jsonl")
    args = ap.parse_args()

    from importlib.metadata import version
    if version("kaggle-environments") != ENGINE:
        sys.exit(f"kaggle-environments {version('kaggle-environments')} installed; need {ENGINE}")
    paths = dict(x.split("=", 1) for x in args.agent)
    jobs = []
    for c in args.candidates:
        for o in args.opponents:
            for s in seeds_from(args.seeds):
                jobs.append((c, o, paths[c], paths[o], s, 0))   # candidate in seat 0
                jobs.append((o, c, paths[o], paths[c], s, 1))   # candidate in seat 1
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    agg = collections.defaultdict(lambda: [0, 0, 0, 0.0])
    with open(args.out, "a") as f, ThreadPoolExecutor(args.workers) as pool:
        for i, r in enumerate(pool.map(play, jobs), 1):
            f.write(json.dumps(r) + "\n"); f.flush()
            if "error" in r:
                print("ERROR", r); continue
            if r["sa"] != "DONE" or r["sb"] != "DONE":
                print("STATUS", r)
            if r["cand"] == 0:
                cand, opp, mine, theirs = r["a"], r["b"], r["ra"], r["rb"]
            else:
                cand, opp, mine, theirs = r["b"], r["a"], r["rb"], r["ra"]
            x = agg[(cand, opp)]; x[3] += mine - theirs
            x[0 if mine > theirs else 1 if mine < theirs else 2] += 1
            if i % 10 == 0:
                print(f"{i}/{len(jobs)} games", flush=True)
    print("\ncandidate vs opponent: W-L-T (mean margin)")
    for (c, o), x in sorted(agg.items()):
        n = sum(x[:3]) or 1
        print(f"{c:>12} vs {o:<12} {x[0]}-{x[1]}-{x[2]}  points {(x[0] + 0.5 * x[2]) / n:.3f}  mean {x[3] / n:+.0f}")


if __name__ == "__main__":
    main()
