#!/usr/bin/env python3
"""Kaggriculture episode scraper.

Crawls the public episode graph: seed submission ids -> ListEpisodes ->
new episode ids + opponents' submission ids -> replay JSONs from the CDN.

State lives next to this script:
  state.json          known submission ids + fetched episode ids
  raw/{id}.json.gz    full replays, working copy (packed into replays.parquet for upload)
  episodes.csv        one row per episode (times, type, banks, ratings)
  agents.csv          one row per (episode, agent)
  teams.csv           team id -> team name + current ladder score
  episode_features.csv  per-seat behavior features parsed out of every replay

Run: python scrape.py [--max-new N]   (polite: ~1 req/sec)
"""
import argparse
import csv
import gzip
import json
import subprocess
import sys
import time
from pathlib import Path

import requests

HERE = Path(__file__).parent
RAW = HERE / "raw"
STATE = HERE / "state.json"
LIST_URL = "https://www.kaggle.com/api/i/competitions.EpisodeService/ListEpisodes"
REPLAY_URL = "https://www.kaggleusercontent.com/episodes/{id}.json"

# Public leaderboard snapshot 2026-07-31 (all 36 teams' latest submissions);
# the crawl discovers new ones from episode pairings automatically.
SEED_SUBMISSIONS = [
    55118227, 55116580, 55116691, 55117099, 55118449, 55117347, 55115388,
    55118741, 55118157, 55118855, 55115608, 55116223, 55115974, 55118395,
    55115818, 55118396, 55117565, 55118615, 55118013, 55115318, 55117304,
    55119028, 55117284, 55117940, 55117886, 55116523, 55116608, 55117088,
    55118784, 55115877, 55118706, 55117932, 55115641, 55116892, 55117274,
    55118574,
]


def load_state():
    if STATE.exists():
        return json.loads(STATE.read_text())
    return {"submissions": SEED_SUBMISSIONS, "episodes": {}}


def save_state(state):
    STATE.write_text(json.dumps(state, indent=0))


def list_episodes(session, submission_id):
    # Throttling is ambient, not transient: two touches, then skip.
    for attempt in range(2):
        r = session.post(LIST_URL, json={"submissionId": submission_id}, timeout=30)
        if r.status_code == 429:
            time.sleep(5)
            continue
        r.raise_for_status()
        return r.json().get("episodes", [])
    raise RuntimeError(f"429 after retries for submission {submission_id}")


def fetch_replay(session, episode_id):
    r = session.get(REPLAY_URL.format(id=episode_id), timeout=120)
    if r.status_code != 200:
        return None
    return r.content


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-new", type=int, default=300, help="replay download cap per run")
    ap.add_argument("--budget-min", type=int, default=45, help="minutes for the metadata crawl")
    args = ap.parse_args()

    RAW.mkdir(exist_ok=True)
    state = load_state()
    subs = list(dict.fromkeys(state["submissions"]))
    episodes = state["episodes"]  # id(str) -> metadata dict
    session = requests.Session()
    session.headers["User-Agent"] = "kaggriculture-dataset-builder (georgymamarin)"

    # 1. Refresh episode metadata, newest activity first, within a time budget.
    # The submission list only grows and the API throttles hard, so a full sweep
    # stopped fitting any single run; what is deferred the next run picks up.
    deadline = time.time() + args.budget_min * 60
    last_seen = {}
    for e in episodes.values():
        for a in e.get("agents", []):
            asid = a.get("submissionId")
            if asid:
                last_seen[asid] = max(last_seen.get(asid, ""), e.get("endTime") or "")
    order = sorted(subs, key=lambda s0: last_seen.get(s0, "9999"), reverse=True)

    crawled = limited = 0
    for sid in order:
        if time.time() > deadline:
            print(f"  crawl budget spent: {crawled} ok, {limited} limited, "
                  f"{len(order) - crawled - limited} deferred")
            break
        try:
            eps = list_episodes(session, sid)
        except Exception:
            limited += 1
            continue
        crawled += 1
        for e in eps:
            eid = str(e["id"])
            episodes[eid] = e
            for a in e.get("agents", []):
                asid = a.get("submissionId")
                if asid and asid not in subs:
                    subs.append(asid)          # discovered a new opponent
        if crawled % 25 == 0:
            print(f"  metadata: {crawled} ok / {limited} limited, {len(episodes)} episodes",
                  flush=True)
        time.sleep(1.2)
    print(f"metadata done: {len(subs)} submissions, {len(episodes)} episodes")

    # 2. Download missing replays (completed episodes only).
    import pyarrow.parquet as _pq
    have_pq = set()
    if (HERE / "replays.parquet").exists():
        have_pq = set(_pq.read_table(HERE / "replays.parquet",
                                     columns=["episode_id"])["episode_id"].to_pylist())
    # Newest first: with a backlog, insertion order starves the freshest days.
    missing = sorted(
        (eid for eid, e in episodes.items()
         if e.get("state") == "COMPLETED" and int(eid) not in have_pq
         and not (RAW / f"{eid}.json.gz").exists()),
        key=lambda eid: episodes[eid].get("endTime") or "", reverse=True)
    print(f"replays missing: {len(missing)} (cap {args.max_new})")
    got = 0
    for eid in missing[: args.max_new]:
        blob = fetch_replay(session, eid)
        if blob:
            (RAW / f"{eid}.json.gz").write_bytes(gzip.compress(blob, 6))
            got += 1
        else:
            print(f"  replay {eid}: not available")
        if got % 25 == 0 and got:
            print(f"  replays: {got}")
        time.sleep(0.8)
    print(f"replays downloaded this run: {got}")

    # 3. Flat tables.
    with open(HERE / "episodes.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["episode_id", "create_time", "end_time", "type", "state",
                    "sub_0", "team_0", "bank_0", "rating_0",
                    "sub_1", "team_1", "bank_1", "rating_1"])
        for eid, e in sorted(episodes.items()):
            ag = e.get("agents", [])
            row = [eid, e.get("createTime"), e.get("endTime"), e.get("type"), e.get("state")]
            for k in (0, 1):
                a = ag[k] if k < len(ag) else {}
                row += [a.get("submissionId"), a.get("teamId"),
                        a.get("reward"), a.get("updatedScore")]
            w.writerow(row)
    with open(HERE / "agents.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["episode_id", "agent_index", "submission_id", "team_id",
                    "final_bank", "rating_after"])
        for eid, e in sorted(episodes.items()):
            for k, a in enumerate(e.get("agents", [])):
                w.writerow([eid, a.get("index", k), a.get("submissionId"),
                            a.get("teamId"), a.get("reward"), a.get("updatedScore")])

    # Team names for readable charts, then pack replays for upload:
    # Kaggle decompresses .gz, parquet stays as-is (~340x smaller).
    subprocess.run([sys.executable, str(HERE / "teams.py")], check=False)
    subprocess.run([sys.executable, str(HERE / "repack.py")], check=True)
    subprocess.run([sys.executable, str(HERE / "features.py")], check=True)

    state["submissions"] = subs
    state["episodes"] = episodes
    save_state(state)
    have = len(list(RAW.glob("*.json.gz")))
    print(f"state saved: {len(subs)} submissions, {len(episodes)} episodes, {have} replays on disk")


if __name__ == "__main__":
    main()
