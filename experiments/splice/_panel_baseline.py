"""experiments/splice/_panel_baseline.py <candidate.py> [threads]

Reproduces Stephane's top-six panel baseline (harness/top6panel.py) for a
candidate, without editing any of Stephane's files -- per the task: "adapt
paths via a small wrapper rather than editing Stephane's files." Not a frozen
deliverable; supporting script for the "Panel baseline" section of
experiments/splice/base_choice.md, kept so those numbers are reproducible.

Why a wrapper instead of running harness/top6panel.py directly: that script
hardcodes its replay directory to
`~/KagricultureLocalData/episodes/20260923T153431Z_top6/replays/`, which does
not exist on this machine (or in the repo -- replays are ~31 MB each and
gitignored). harness/tapeopp.py, which does the actual per-episode work
(replay the recorded top team's exact tape at their original seat, play the
candidate at the other seat, same seed), takes a replay PATH as a plain
argument and hardcodes nothing -- so it is reused UNCHANGED, called the same
way top6panel.py itself calls it (subprocess, one call per episode). Only the
path and the download are new.

Episodes: harness/top6_panel.json lists 80 (episode_id, seat, team) rows;
harness/faithful_eps.json is a fixed 38-id subset of those (already
computed, not recomputed here) for which the frozen-replay comparison stays
representative post-divergence. This script downloads and runs only those
38, matching the "W0 wins 6 of 38 faithful episodes" target exactly, since
the other 42 are never used in that number and downloading them (~31 MB
each) would not change it.

Downloads whatever's missing from https://www.kaggleusercontent.com/episodes/
{id}.json (no auth) into experiments/endgame/rep/{id}.json.gz -- gzip-wrapped
on arrival so harness/tapeopp.py's own `json.load(gzip.open(path))` needs no
changes. Verified against a live download: the JSON shape matches exactly
what tapeopp.py expects (`info.seed`, `info.TeamNames`, `rewards`, `steps`).
experiments/endgame/rep/ is already gitignored (existing convention, other
downloaded replays already live there).

Usage:
    .venv/Scripts/python.exe experiments/splice/_panel_baseline.py agents/w0_v15stack_control.py
    .venv/Scripts/python.exe experiments/splice/_panel_baseline.py agents/w3_herdsafe2700.py 6
"""
import json
import os
import statistics
import subprocess
import sys
import urllib.request
import gzip
from concurrent.futures import ThreadPoolExecutor

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(os.path.dirname(THIS_DIR))
HARNESS_DIR = os.path.join(REPO_ROOT, "harness")
REP_DIR = os.path.join(REPO_ROOT, "experiments", "endgame", "rep")
RESULTS_DIR = os.path.join(THIS_DIR, "results")
TAPEOPP = os.path.join(HARNESS_DIR, "tapeopp.py")

EPISODE_URL = "https://www.kaggleusercontent.com/episodes/{id}.json"


def _ensure_downloaded(ep, threads):
    path = os.path.join(REP_DIR, f"{ep}.json.gz")
    if os.path.exists(path) and os.path.getsize(path) > 0:
        return path
    os.makedirs(REP_DIR, exist_ok=True)
    with urllib.request.urlopen(EPISODE_URL.format(id=ep), timeout=120) as resp:
        raw = resp.read()
    with gzip.open(path, "wb") as f:
        f.write(raw)
    return path


def _one(item, candidate):
    ep, seat, team = item
    replay_path = os.path.join(REP_DIR, f"{ep}.json.gz")
    if not os.path.exists(replay_path):
        return {"ep": ep, "team": team, "error": "replay not downloaded"}
    r = subprocess.run(
        [sys.executable, TAPEOPP, replay_path, str(seat), candidate],
        capture_output=True, text=True, timeout=180,
    )
    try:
        res = json.loads(r.stdout.strip().splitlines()[-1])
    except Exception:
        return {"ep": ep, "team": team, "error": (r.stderr or r.stdout or "")[-500:]}
    res.update(ep=ep, team=team, seat=seat, cand=os.path.basename(candidate))
    return res


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    candidate = os.path.abspath(sys.argv[1])
    if not os.path.exists(candidate):
        sys.exit(f"_panel_baseline.py: candidate not found: {candidate}")
    threads = int(sys.argv[2]) if len(sys.argv) > 2 else 3
    if threads > 6:
        print(f"_panel_baseline.py: threads={threads} > 6 -- the task caps downloads at 6; "
              f"proceeding since it was explicit.")

    panel = json.load(open(os.path.join(HARNESS_DIR, "top6_panel.json")))
    faithful = set(json.load(open(os.path.join(HARNESS_DIR, "faithful_eps.json"))))
    faithful_items = [item for item in panel if item[0] in faithful]
    assert len(faithful_items) == len(faithful) == 38, (
        f"expected 38 faithful items matched against top6_panel.json, got {len(faithful_items)}"
    )

    print(f"downloading/verifying {len(faithful_items)} faithful episodes into "
          f"{os.path.relpath(REP_DIR, REPO_ROOT)} (<= {min(threads, 6)} at a time)...")
    with ThreadPoolExecutor(min(threads, 6)) as pool:
        list(pool.map(lambda item: _ensure_downloaded(item[0], threads), faithful_items))

    print(f"running {os.path.relpath(candidate, REPO_ROOT)} against the panel "
          f"({threads} threads, each spawning a full 720-step episode via harness/tapeopp.py)...")
    with ThreadPoolExecutor(threads) as pool:
        results = list(pool.map(lambda item: _one(item, candidate), faithful_items))

    os.makedirs(RESULTS_DIR, exist_ok=True)
    out_path = os.path.join(RESULTS_DIR, f"panel_{os.path.splitext(os.path.basename(candidate))[0]}.jsonl")
    with open(out_path, "w") as f:
        for res in results:
            f.write(json.dumps(res) + "\n")

    margins, wins = [], 0
    errors = [res for res in results if "error" in res]
    for res in results:
        if "error" in res:
            print(f"  ERROR ep={res['ep']} team={res.get('team')}: {res['error']}")
            continue
        margin = res["ours_bank"] - res["tape_bank"]
        margins.append(margin)
        if margin > 0:
            wins += 1

    print(f"\n{os.path.basename(candidate)}: {wins} wins of {len(margins)} faithful episodes "
          f"({len(errors)} errors)")
    if margins:
        print(f"  median margin {statistics.median(margins):+,.0f}   mean {statistics.mean(margins):+,.0f}   "
              f"worst {min(margins):+,.0f}   best {max(margins):+,.0f}")
    print(f"  raw: {os.path.relpath(out_path, REPO_ROOT)}")


if __name__ == "__main__":
    main()
