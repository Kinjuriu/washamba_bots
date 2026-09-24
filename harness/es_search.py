"""Black-box policy search (evolution-strategy style) over W3's market-race constants.

This is the practical form of "try RL" for our situation: instead of training a network, it treats
the agent's tunable constants as the policy parameters and improves them from game outcomes
(win / loss / tie), the same signal RL would use. Only the market-race family is searched, because
every board-changing overlay so far lost the mirror; this family is the one that has won (race44).

Stages:
  screen   : random candidates around W3's defaults, each played on a small fixed seed block,
             both seats, against the opponent pool. Scored by points (win 1, tie 0.5).
  confirm  : the best K screened candidates on FRESH seeds (selection on the screen inflates it).
Outputs go to --out (jsonl per game) and --out.summary.json.

Usage (Mac, Python with kaggle-environments==1.32.7):
  python es_search.py --base ../submissions/w3_herdsafe2700.py \
      --opp w3=../submissions/w3_herdsafe2700.py --opp w1=../submissions/w1_v15stack_race44.py \
      --opp hsv3=../agents/herdsafev3/main.py --opp v57=../agents/v57/main.py \
      --screen-seeds 5001-5006 --confirm-seeds 6001-6030 --n 60 --top 5 --workers 7 \
      --workdir es_w3 --out es_w3/results.jsonl
"""
import argparse, json, os, random, re, subprocess, sys, collections
from concurrent.futures import ThreadPoolExecutor

# name: (choices). The LAST assignment of each name in the file is the one patched.
SPACE = {
    "V9_RACE_DEFAULT": [40, 42, 44, 46, 48],
    "V9_RACE_MAX": [44, 48, 52, 56],
    "V9_RACE_MARGIN": [8, 10, 12, 14, 16],
    "V9_RACE_GAP": [2, 3, 4],
    "V9_RACE_WINDOW": [24, 30, 36],
    "V9_RACEPX_MARGIN": [-10, -5, 0, 5, 10],
    "V9_RACEGATE_MARGIN": [-10, -5, 0, 5, 10],
    "_V92_P_H": [36, 48, 60],
    "_V92_P_K": [3, 4, 5],
    "_HP_WINDOW": [2, 3, 4, 5, 6],
    "V9_COURIER_FROM_HOUR": [10, 12, 14],
}
GAME = r"""
import sys, json, os
sys.path[:0] = [os.path.dirname(p) for p in (sys.argv[1], sys.argv[2])]
from kaggle_environments import make
env = make('kaggriculture', configuration={'seed': int(sys.argv[3])}, debug=False)
env.run([sys.argv[1], sys.argv[2]])
last = env.steps[-1]
print(json.dumps([last[0].reward, last[1].reward, last[0].status, last[1].status]))
"""


def seeds(t):
    out = []
    for part in t.split(","):
        a, _, b = part.partition("-")
        out += list(range(int(a), int(b or a) + 1))
    return out


def defaults(src):
    d = {}
    for k in SPACE:
        m = re.findall(r"^%s\s*=\s*([-0-9.]+)" % re.escape(k), src, re.M)
        if m:
            d[k] = float(m[-1]) if "." in m[-1] else int(m[-1])
    return d


def patch(src, params):
    lines = src.split("\n")
    for k, v in params.items():
        idx = [i for i, l in enumerate(lines) if re.match(r"^%s\s*=\s*[-0-9.]+" % re.escape(k), l)]
        if not idx:
            raise SystemExit("constant not found: " + k)
        i = idx[-1]
        lines[i] = re.sub(r"^(%s\s*=\s*)[-0-9.]+" % re.escape(k), r"\g<1>%s" % v, lines[i])
    return "\n".join(lines)


def play(job):
    cand, pc, opp, po, seed, seat = job
    a, b = (pc, po) if seat == 0 else (po, pc)
    r = subprocess.run([sys.executable, "-c", GAME, os.path.abspath(a), os.path.abspath(b), str(seed)],
                       capture_output=True, text=True, timeout=900)
    try:
        ra, rb, sa, sb = json.loads(r.stdout.strip().splitlines()[-1])
    except Exception:
        return dict(cand=cand, opp=opp, seed=seed, seat=seat, error=r.stderr[-300:])
    mine, theirs = (ra, rb) if seat == 0 else (rb, ra)
    return dict(cand=cand, opp=opp, seed=seed, seat=seat, mine=mine, theirs=theirs, ok=(sa == sb == "DONE"))


def run(cands, opps, seedlist, workers, out):
    jobs = [(c, p, o, po, s, seat) for c, p in cands.items() for o, po in opps.items() for s in seedlist for seat in (0, 1)]
    score = collections.defaultdict(lambda: [0.0, 0, 0.0])  # points, games, margin
    per_opp = collections.defaultdict(lambda: [0.0, 0])
    with open(out, "a") as f, ThreadPoolExecutor(workers) as pool:
        for r in pool.map(play, jobs):
            f.write(json.dumps(r) + "\n")
            if "error" in r:
                continue
            d = r["mine"] - r["theirs"]
            pts = 1.0 if d > 0 else 0.5 if d == 0 else 0.0
            s = score[r["cand"]]; s[0] += pts; s[1] += 1; s[2] += d
            po = per_opp[(r["cand"], r["opp"])]; po[0] += pts; po[1] += 1
    return ({c: dict(points=s[0] / s[1], games=s[1], mean_margin=s[2] / s[1]) for c, s in score.items()},
            {"%s|%s" % k: v[0] / v[1] for k, v in per_opp.items()})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True)
    ap.add_argument("--opp", action="append", required=True, help="name=path")
    ap.add_argument("--screen-seeds", default="5001-5006")
    ap.add_argument("--confirm-seeds", default="6001-6030")
    ap.add_argument("--n", type=int, default=60)
    ap.add_argument("--top", type=int, default=5)
    ap.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) - 1))
    ap.add_argument("--workdir", default="es_work")
    ap.add_argument("--out", default="es_work/results.jsonl")
    ap.add_argument("--rng", type=int, default=7)
    a = ap.parse_args()
    from importlib.metadata import version
    if version("kaggle-environments") != "1.32.7":
        sys.exit("need kaggle-environments 1.32.7")
    os.makedirs(a.workdir, exist_ok=True)
    src = open(a.base).read()
    base = defaults(src)
    missing = [k for k in SPACE if k not in base]
    if missing:
        print("not found in base (skipped):", missing)
    space = {k: v for k, v in SPACE.items() if k in base}
    rng = random.Random(a.rng)
    opps = dict(x.split("=", 1) for x in a.opp)
    cands, params = {}, {}
    cands["base"] = a.base; params["base"] = {}
    seen = set()
    while len(cands) < a.n + 1:
        k_changes = rng.choice([1, 1, 2, 2, 3])
        p = {k: rng.choice(space[k]) for k in rng.sample(sorted(space), k_changes)}
        p = {k: v for k, v in p.items() if v != base[k]}
        key = json.dumps(p, sort_keys=True)
        if not p or key in seen:
            continue
        seen.add(key)
        name = "c%03d" % len(cands)
        path = os.path.join(a.workdir, name + ".py")
        open(path, "w").write(patch(src, p))
        cands[name] = path; params[name] = p
    print("screening", len(cands), "candidates x", len(opps), "opponents x", len(seeds(a.screen_seeds)), "seeds x 2 seats", flush=True)
    screen, screen_opp = run(cands, opps, seeds(a.screen_seeds), a.workers, a.out)
    ranked = sorted((c for c in screen if c != "base"), key=lambda c: (-screen[c]["points"], -screen[c]["mean_margin"]))
    top = ranked[: a.top]
    print("screen base", screen.get("base"), "top", [(c, round(screen[c]["points"], 3), params[c]) for c in top], flush=True)
    conf, conf_opp = run({c: cands[c] for c in ["base"] + top}, opps, seeds(a.confirm_seeds), a.workers, a.out)
    summary = dict(base_defaults=base, space=space, params=params, screen=screen, screen_per_opp=screen_opp,
                   confirm=conf, confirm_per_opp=conf_opp, top=top)
    json.dump(summary, open(a.out + ".summary.json", "w"), indent=1)
    print("\nCONFIRM (fresh seeds): candidate points / mean margin / params")
    for c in ["base"] + top:
        print(c, round(conf[c]["points"], 3), round(conf[c]["mean_margin"]), params.get(c))
        print("   per opponent:", {k.split("|")[1]: round(v, 3) for k, v in conf_opp.items() if k.startswith(c + "|")})


if __name__ == "__main__":
    main()
