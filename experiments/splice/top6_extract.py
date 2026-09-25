"""Top-six per-day targets from real ladder replays (Builder A, splice build).

Picks recent episodes from experiments/endgame/kaggle_ds (ashok205 top-10 replay archive)
in which a top-six-family team plays. The top-six seat is identified from the replay itself
by its turn-1 opening, BUY_ANIMAL COW 1 + BUY_PRODUCT WHEAT 5 (canonical form from
experiments/endgame/field_families.py), and the opponent's family by the same classifier.
Each replay is re-simulated through the local engine from its recorded actions and seed with
experiments/splice/daymetrics.py instrumentation. Money for both seats is checked against the
recording at every step, and a game that diverges is dropped. That gives exact trades
(realized prices) and effective unit actions, which the recording alone does not.

Single process. Writes experiments/splice/top6_targets.json (percentiles by day) and
experiments/splice/top6_games.jsonl (one line per top-six seat: per-day values for it and
its opponent, for re-splitting without re-parsing).

Usage: .venv/Scripts/python.exe experiments/splice/top6_extract.py [--games 60] [--tape 30]
       [--since 2026-09-20] [--aggregate-only]
       ... --scan [--since 2026-09-13]   classify both seats' openings of every episode with a
                                          top-six-family team (decodes only the first 3 steps),
                                          cached in experiments/splice/top6_scan.json
       ... --add-tape 20                  extract top-six-vs-tape games found by the scan, append
                                          them to top6_games.jsonl, re-aggregate
"""
import argparse
import collections
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
ENDGAME = os.path.join(ROOT, "experiments", "endgame")
KDS = os.path.join(ENDGAME, "kaggle_ds")
FFOUT = os.path.join(ENDGAME, "field_families_out")
sys.path.insert(0, HERE)
sys.path.insert(0, ENDGAME)

import pandas as pd  # noqa: E402
import pyarrow.parquet as pq  # noqa: E402

import daymetrics as DM  # noqa: E402
import field_families as FF  # noqa: E402  (canon / classify only)
from kaggle_environments import make  # noqa: E402

OUT_TARGETS = os.path.join(HERE, "top6_targets.json")
OUT_GAMES = os.path.join(HERE, "top6_games.jsonl")
OUT_SCAN = os.path.join(HERE, "top6_scan.json")
TOP6_T1 = FF.canon([("BUY_ANIMAL", "COW", 1), ("BUY_PRODUCT", "WHEAT", 5)])
TAPE_FAMILIES = {"v15stack", "2945_farm", "herd_safe"}


def bucket(family):
    if family in TAPE_FAMILIES:
        return "tape"
    if family == "top_six":
        return "top6"
    return "other"


def name_to_family():
    """Team name -> family from the field-families session (pre-selection only)."""
    out = {}
    def load(name):
        with open(os.path.join(FFOUT, name), encoding="utf-8") as f:
            return json.load(f)
    for g in load("fetched_games.json"):
        out.setdefault(g["team_a_name"], g["fam_a"])
        out.setdefault(g["team_b_name"], g["fam_b"])
    for r in load("fetched_results.json").values():
        out.setdefault(r["team_name"], r["family"])
    for r in load("top100_table.json"):
        fam = r.get("family", "")
        out.setdefault(r["team"], "top_six" if fam == "top_six" else fam)
    return out


def candidates(since, n_games, n_tape):
    ep = pd.read_parquet(os.path.join(KDS, "episodes.parquet"),
                         columns=["date", "episode_id", "participants_json", "replay_shard"])
    n2f = name_to_family()
    top6_names = {n for n, f in n2f.items() if f == "top_six"}
    rows = {}
    for r in ep[ep.date >= since].itertuples():
        parts = json.loads(r.participants_json)
        mine = [p for p in parts if p in top6_names]
        if not mine or r.episode_id in rows:
            continue
        opp = [p for p in parts if p not in top6_names]
        fam = n2f.get(opp[0], "unmapped") if opp else "top_six"
        rows[r.episode_id] = (r.date, mine[0], bucket(fam) if fam != "unmapped" else "unmapped")
    # Round-robin over top-six teams (each team's games most recent first), then a quota
    # of tape-family opponents and the rest filled from everything else.
    by_team = collections.defaultdict(list)
    for eid, (date, team, b) in sorted(rows.items(), key=lambda kv: (kv[1][0], kv[0]), reverse=True):
        by_team[team].append((eid, date, team, b))
    ordered = []
    while any(by_team.values()):
        for team in sorted(by_team):
            if by_team[team]:
                ordered.append(by_team[team].pop(0))
    tape = [x for x in ordered if x[3] == "tape"][:n_tape]
    rest = [x for x in ordered if x[3] != "tape"][:max(0, n_games - len(tape))]
    return tape + rest


_SHARDS = None


def load_replay(eid):
    global _SHARDS
    if _SHARDS is None:
        with open(os.path.join(FFOUT, "shard_index.json"), encoding="utf-8") as f:
            _SHARDS = json.load(f)
    shard, rg = _SHARDS[str(eid)]
    shard = os.path.join(KDS, os.path.basename(shard))
    blob = pq.ParquetFile(shard).read_row_group(rg, columns=["replay_json"]).column("replay_json")[0].as_py()
    rep = json.loads(blob)
    if "replay" in rep:
        r = rep["replay"]
        rep = json.loads(r) if isinstance(r, str) else r
    return rep


def first_steps(eid, n=3):
    """Decode only steps[0..n-1] of a replay (the raw JSON is ~33 MB; this reads ~150 KB)."""
    global _SHARDS
    if _SHARDS is None:
        with open(os.path.join(FFOUT, "shard_index.json"), encoding="utf-8") as f:
            _SHARDS = json.load(f)
    shard, rg = _SHARDS[str(eid)]
    shard = os.path.join(KDS, os.path.basename(shard))
    blob = pq.ParquetFile(shard).read_row_group(rg, columns=["replay_json"]).column("replay_json")[0].as_py()
    dec = json.JSONDecoder()
    k = blob.index('"steps": [') + len('"steps": [')
    out = []
    for _ in range(n):
        obj, k = dec.raw_decode(blob, k)
        out.append(obj)
        while blob[k] in ", \n":
            k += 1
    return out


def scan(since):
    """Classify both seats' openings for every episode (since `since`) with a
    top-six-family team; cached so extraction can pick by the true opponent family."""
    ep = pd.read_parquet(os.path.join(KDS, "episodes.parquet"),
                         columns=["date", "episode_id", "participants_json"])
    top6_names = {n for n, f in name_to_family().items() if f == "top_six"}
    todo = {}
    for r in ep[ep.date >= since].itertuples():
        if any(p in top6_names for p in json.loads(r.participants_json)):
            todo.setdefault(int(r.episode_id), r.date)
    cache = {}
    if os.path.exists(OUT_SCAN):
        with open(OUT_SCAN, encoding="utf-8") as f:
            cache = json.load(f)
    t0 = time.time()
    for n, (eid, date) in enumerate(sorted(todo.items(), key=lambda kv: kv[1], reverse=True)):
        if str(eid) in cache:
            continue
        try:
            st = first_steps(eid)
            fams, top6 = [], []
            for s in (0, 1):
                a1 = FF.market(st[1][s].get("action") or {})
                a2 = FF.market(st[2][s].get("action") or {})
                fam, c1, _ = FF.classify(a1, a2)
                fams.append(fam if not fam.startswith("unknown") else "unknown")
                top6.append(c1 == TOP6_T1)
            cache[str(eid)] = {"date": date, "fam": fams, "top6_seat": top6}
        except Exception as e:
            cache[str(eid)] = {"date": date, "error": type(e).__name__}
        if n % 200 == 0:
            print(f"scan {n}/{len(todo)} {time.time() - t0:.0f}s", flush=True)
    with open(OUT_SCAN, "w", encoding="utf-8") as f:
        json.dump(cache, f)
    pairs = collections.Counter()
    for v in cache.values():
        if "fam" in v:
            for s in (0, 1):
                if v["top6_seat"][s]:
                    o = 1 - s
                    pairs["top_six" if v["top6_seat"][o] else bucket(v["fam"][o])] += 1
    print(f"scanned {len(cache)} episodes; top-six seats by opponent bucket: {dict(pairs)}")
    return cache


def final_shops(eid):
    """The season's final unlocked-shop list, read from the raw replay text."""
    global _SHARDS
    if _SHARDS is None:
        with open(os.path.join(FFOUT, "shard_index.json"), encoding="utf-8") as f:
            _SHARDS = json.load(f)
    shard, rg = _SHARDS[str(eid)]
    shard = os.path.join(KDS, os.path.basename(shard))
    blob = pq.ParquetFile(shard).read_row_group(rg, columns=["replay_json"]).column("replay_json")[0].as_py()
    k = blob.rfind('"unlocked_shops": [')
    shops, _ = json.JSONDecoder().raw_decode(blob, k + len('"unlocked_shops": '))
    return shops


def add_shops(games):
    """Backfill per-day drain (market context) into games extracted before it existed."""
    cache = {}
    for g in games:
        if "shops_final" not in g:
            eid = g["episode_id"]
            if eid not in cache:
                cache[eid] = final_shops(eid)
            g["shops_final"] = cache[eid]
        for side in ("days", "opp_days"):
            per = [DM.drain_by_product(DM.shops_on_day(g["shops_final"], d)) for d in range(len(g[side]["money_dawn"]))]
            for key in per[0]:
                g[side][key] = [row[key] for row in per]
    with open(OUT_GAMES, "w", encoding="utf-8") as f:
        for g in games:
            f.write(json.dumps(g) + "\n")
    return games


def resimulate(rep):
    """Re-run the recorded actions; None if any step's money differs from the recording."""
    cfg = dict(rep["configuration"])
    cfg["seed"] = rep["info"]["seed"]
    env = make("kaggriculture", configuration=cfg)
    env.reset(2)
    DM.REC.reset()
    steps = rep["steps"]
    for i in range(1, len(steps)):
        env.step([steps[i][s].get("action") or {} for s in (0, 1)])
        got = env.state[0].observation["farms"]
        want = steps[i][0]["observation"]["farms"]
        if any(abs(got[s]["money"] - want[s]["money"]) > 1e-6 for s in (0, 1)):
            return None
        if env.done:
            break
    return env


def extract(games_target, tape_target, since):
    picked = candidates(since, games_target, tape_target)
    print(f"{len(picked)} candidate episodes (pre-bucket: "
          f"{collections.Counter(b for *_, b in picked)})", flush=True)
    return extract_games(picked)


def load_games():
    with open(OUT_GAMES, encoding="utf-8") as f:
        return [json.loads(line) for line in f]


def extract_games(picked, append=False):
    DM.install()
    out = []
    skipped = collections.Counter()
    t0 = time.time()
    for k, (eid, date, team, _b) in enumerate(picked):
        try:
            rep = load_replay(eid)
        except Exception as e:  # missing shard row etc.
            skipped["load:" + type(e).__name__] += 1
            continue
        steps = rep["steps"]
        fams, t1s = [], []
        for s in (0, 1):
            a1 = FF.market(steps[1][s].get("action") or {})
            a2 = FF.market(steps[2][s].get("action") or {})
            fam, c1, _c2 = FF.classify(a1, a2)
            fams.append(fam)
            t1s.append(c1)
        seats = [s for s in (0, 1) if t1s[s] == TOP6_T1]
        if not seats:
            skipped["no_top6_opening"] += 1
            continue
        env = resimulate(rep)
        if env is None:
            skipped["resim_mismatch"] += 1
            continue
        names = rep["info"].get("TeamNames") or ["?", "?"]
        rewards = rep.get("rewards") or [None, None]
        shops_final = list(steps[-1][0]["observation"]["town"]["unlocked_shops"])
        for s in seats:
            o = 1 - s
            opp_fam = fams[o] if t1s[o] != TOP6_T1 else "top_six"
            out.append({
                "episode_id": int(eid), "date": date, "team": names[s], "seat": s, "shops_final": shops_final,
                "family": fams[s], "opponent": names[o],
                "opp_family": opp_fam if not opp_fam.startswith("unknown") else "unknown",
                "opp_bucket": bucket(opp_fam), "bank": rewards[s], "opp_bank": rewards[o],
                "days": DM.per_day(env.steps, s), "opp_days": DM.per_day(env.steps, o),
            })
        print(f"[{k + 1}/{len(picked)}] {eid} {date} {names[seats[0]]} vs {names[1 - seats[0]]} "
              f"({out[-1]['opp_family']}) banks {rewards} {time.time() - t0:.0f}s", flush=True)
        del rep, env
    print("skipped:", dict(skipped))
    with open(OUT_GAMES, "a" if append else "w", encoding="utf-8") as f:
        for g in out:
            f.write(json.dumps(g) + "\n")
    return out


def pct(vals, q):
    """Linear-interpolated percentile (numpy's default), q in [0, 100]."""
    v = sorted(vals)
    if not v:
        return None
    pos = (len(v) - 1) * q / 100.0
    lo = int(pos)
    hi = min(lo + 1, len(v) - 1)
    return v[lo] + (v[hi] - v[lo]) * (pos - lo)


def aggregate(games):
    for g in games:
        DM.add_cumulative(g["days"])
        DM.add_cumulative(g["opp_days"])
    splits = {"all": games,
              "vs_tape": [g for g in games if g["opp_bucket"] == "tape"],
              "vs_other": [g for g in games if g["opp_bucket"] == "other"],
              "vs_top6": [g for g in games if g["opp_bucket"] == "top6"]}
    metrics = list(games[0]["days"].keys())
    out = {"meta": {
        "built": time.strftime("%Y-%m-%d %H:%M"),
        "source": "ashok205 top-10 replay archive (experiments/endgame/kaggle_ds), re-simulated exactly",
        "top6_seat_rule": "turn-1 market == BUY_ANIMAL COW 1 + BUY_PRODUCT WHEAT 5",
        "tape_families": sorted(TAPE_FAMILIES),
        "n_games": {k: len(v) for k, v in splits.items()},
        "dates": sorted({g["date"] for g in games}),
        "teams": dict(collections.Counter(g["team"] for g in games)),
        "opponent_families": dict(collections.Counter(g["opp_family"] for g in games)),
        "day_index": "day d = obs steps 24d..24d+23; *_dawn/tiles/animals/planted/structures are "
                     "the state at obs step 24d; flows (sold, revenue, hires, feed, ...) are over the day",
    }, "splits": {}}
    for name, gs in splits.items():
        if not gs:
            continue
        per = {}
        for m in metrics:
            p25, p50, p75, n = [], [], [], []
            for d in range(DM.DAYS):
                vals = [g["days"][m][d] for g in gs if d < len(g["days"][m]) and g["days"][m][d] is not None]
                p25.append(pct(vals, 25))
                p50.append(pct(vals, 50))
                p75.append(pct(vals, 75))
                n.append(len(vals))
            per[m] = {"p25": p25, "p50": p50, "p75": p75, "n": n}
        season = {}
        for key, fn in (("bank", lambda g: g["bank"]), ("opp_bank", lambda g: g["opp_bank"]),
                        ("margin", lambda g: (g["bank"] or 0) - (g["opp_bank"] or 0))):
            vals = [fn(g) for g in gs if g["bank"] is not None]
            season[key] = {"p25": pct(vals, 25), "p50": pct(vals, 50), "p75": pct(vals, 75), "n": len(vals)}
        for p in DM.PRODUCTS:
            for side, key in (("days", "revenue_"), ("opp_days", "opp_revenue_")):
                vals = [sum(g[side]["revenue_" + p]) for g in gs]
                season[key + p] = {"p25": pct(vals, 25), "p50": pct(vals, 50), "p75": pct(vals, 75)}
            units = [sum(g["days"]["sold_" + p]) for g in gs]
            revs = [sum(g["days"]["revenue_" + p]) for g in gs]
            season["units_" + p] = {"p25": pct(units, 25), "p50": pct(units, 50), "p75": pct(units, 75)}
            season["avg_price_" + p] = (sum(revs) / sum(units)) if sum(units) else None
        out["splits"][name] = {"per_day": per, "season": season}
    with open(OUT_TARGETS, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=0)
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--games", type=int, default=60)
    ap.add_argument("--tape", type=int, default=30)
    ap.add_argument("--since", default="2026-09-20")
    ap.add_argument("--aggregate-only", action="store_true")
    ap.add_argument("--scan", action="store_true")
    ap.add_argument("--add-tape", type=int, default=0)
    ap.add_argument("--add-shops", action="store_true")
    a = ap.parse_args()
    if a.scan:
        scan(a.since)
        sys.exit(0)
    if a.add_shops:
        games = add_shops(load_games())
        res = aggregate(games)
        print("wrote", OUT_TARGETS, res["meta"]["n_games"])
        sys.exit(0)
    if a.add_tape:
        with open(OUT_SCAN, encoding="utf-8") as f:
            cache = json.load(f)
        have = {g["episode_id"] for g in load_games()}
        picks = []
        for eid, v in sorted(cache.items(), key=lambda kv: (kv[1]["date"], kv[0]), reverse=True):
            if "fam" not in v or int(eid) in have:
                continue
            if any(v["top6_seat"][s] and not v["top6_seat"][1 - s] and bucket(v["fam"][1 - s]) == "tape"
                   for s in (0, 1)):
                picks.append((int(eid), v["date"], "?", "tape"))
        print(f"{len(picks)} top-six-vs-tape episodes available; extracting {min(len(picks), a.add_tape)}")
        extract_games(picks[:a.add_tape], append=True)
        games = load_games()
    elif a.aggregate_only:
        games = load_games()
    else:
        games = extract(a.games, a.tape, a.since)
    res = aggregate(games)
    print("wrote", OUT_TARGETS, res["meta"]["n_games"])
