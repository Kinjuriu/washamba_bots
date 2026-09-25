"""Scratch analysis for docs/ENDGAME/field_families_2026-09-25.md.

Classifies the current top-100 ladder teams into "families" by their turn-1/turn-2 market
orders (per docs/research/TOP6_FINDINGS_2026-09-23.md and docs/ENDGAME/crosscheck_2026-09-25.md),
then builds a family-vs-family win-rate matrix from real games using:

  - georgymamarin/kaggriculture-episodes: episodes.csv (outcome per game, bank_0 vs bank_1,
    no replay parsing needed) + teams.csv (id -> name) + stream_hashes.csv (h24 clustering).
  - ashok205/kaggriculture-top10-replay-archive: replays_YYYY-MM-DD.parquet shards already
    cached in experiments/endgame/kaggle_ds/ (one row group per row - cheap targeted reads).
  - experiments/endgame/panel/*.json: single-seat tapes already cached locally from an earlier
    session's T4 task (free, zero new downloads).

Not used: ListEpisodes (forbidden by the task). Not touched: agents/, main.py.

Run interactively / in pieces - this is a scratch script, not a package.
"""
from __future__ import annotations

import glob
import json
import os
import sys
import time
import urllib.request

import pandas as pd
import pyarrow.parquet as pq

HERE = os.path.dirname(os.path.abspath(__file__))
KDS = os.path.join(HERE, "kaggle_ds")
REP = os.path.join(HERE, "rep")
PANEL = os.path.join(HERE, "panel")
OUT = os.path.join(HERE, "field_families_out")
os.makedirs(OUT, exist_ok=True)

# --------------------------------------------------------------- families

def market(action: dict) -> list:
    return [tuple(o[:3]) if len(o) >= 3 else tuple(o) for o in (action.get("market") or [])]


def canon(orders: list) -> tuple:
    """Canonical signature: sorted tuples, HIRE collapsed to a count."""
    hires = sum(1 for o in orders if o and o[0] == "HIRE")
    rest = sorted(o for o in orders if not (o and o[0] == "HIRE"))
    return (("HIRE", hires),) + tuple(rest)


FAMILY_SIGNATURES = {
    # name: (t1 canon, t2 canon)
    "v15stack": (
        canon([("BUY_PRODUCT", "WHEAT", 20), ("SELL", "WHEAT", 15), ("BUY_SEED", "WHEAT", 1)]),
        canon([("HIRE",)] * 5 + [("BUY_ANIMAL", "COW", 2), ("BUY_ANIMAL", "SHEEP", 2)]),
    ),
    "2945_farm": (
        canon([("BUY_PRODUCT", "WHEAT", 20), ("SELL", "WHEAT", 15)]),
        canon([("HIRE",)] * 5 + [("BUY_ANIMAL", "COW", 2), ("BUY_ANIMAL", "SHEEP", 2)]),
    ),
    "herd_safe": (
        canon([("BUY_PRODUCT", "WHEAT", 8), ("SELL", "WHEAT", 3), ("BUY_SEED", "WHEAT", 1)]),
        canon([("BUY_PRODUCT", "WHEAT", 8), ("SELL", "WHEAT", 3), ("BUY_SEED", "WHEAT", 1)]),
    ),
    "reactive_v7": (
        canon([("BUY_PRODUCT", "WHEAT", 10), ("SELL", "WHEAT", 10)]),
        canon([("SELL", "WHEAT", 13), ("BUY_PRODUCT", "WHEAT", 5)] + [("HIRE",)] * 5
              + [("BUY_ANIMAL", "COW", 2), ("BUY_ANIMAL", "SHEEP", 2)]),
    ),
    "top_six": (
        canon([("BUY_ANIMAL", "COW", 1), ("BUY_PRODUCT", "WHEAT", 5)]),
        canon([("SELL", "WHEAT", 1)] + [("HIRE",)] * 4
              + [("BUY_ANIMAL", "COW", 1), ("BUY_ANIMAL", "SHEEP", 3)]),
    ),
}


def classify(t1_orders: list, t2_orders: list) -> tuple[str, tuple, tuple]:
    """-> (family_label, t1_canon, t2_canon). Unknown -> 'unknown:<hash>' cluster key."""
    c1, c2 = canon(t1_orders), canon(t2_orders)
    for name, (s1, s2) in FAMILY_SIGNATURES.items():
        if c1 == s1 and c2 == s2:
            return name, c1, c2
    # loose family: yhay/aurax7-v5/flexonafft - t2 starts SELL WHEAT (13|1) then BUY WHEAT 5
    rest2 = [o for o in t2_orders if o and o[0] != "HIRE"]
    if len(rest2) >= 2 and rest2[0][:2] == ("SELL", "WHEAT") and rest2[1][:3] == ("BUY_PRODUCT", "WHEAT", 5):
        return "yhay_router_like", c1, c2
    return "unknown:%s|%s" % (c1, c2), c1, c2


# --------------------------------------------------------- panel/*.json cache

def tape_t1_t2(tape_path: str) -> tuple[list, list] | None:
    if not os.path.exists(tape_path):
        return None
    entries = json.load(open(tape_path, encoding="utf-8"))
    if len(entries) < 2:
        return None
    a1 = json.loads(entries[0]) if isinstance(entries[0], str) else entries[0]
    a2 = json.loads(entries[1]) if isinstance(entries[1], str) else entries[1]
    return market(a1), market(a2)


def load_panel_cache() -> dict:
    """{key: {...}} keyed by both team_id (int, if numeric) and team name (str) seen in
    panel/index.json, classified from the already-local single-seat tape files."""
    idx_path = os.path.join(PANEL, "index.json")
    if not os.path.exists(idx_path):
        return {}
    idx = json.load(open(idx_path, encoding="utf-8"))
    out = {}
    for fname, meta in idx.items():
        t1t2 = tape_t1_t2(os.path.join(PANEL, fname))
        if not t1t2:
            continue
        fam, c1, c2 = classify(*t1t2)
        key_id = meta.get("team_id")
        key_name = meta.get("team")
        row = {
            "family": fam, "t1": c1, "t2": c2, "sub": meta.get("sub"),
            "source": "panel_cache/" + fname, "seed": meta.get("seed"),
        }
        if key_id is not None:
            out.setdefault(int(key_id), row)
        if key_name:
            out.setdefault(str(key_name), row)
    return out


# --------------------------------------------------------- local shard index

def build_shard_index() -> dict:
    """{episode_id: shard_path} across every replays_*.parquet already cached locally."""
    index = {}
    for shard in sorted(glob.glob(os.path.join(KDS, "replays_*.parquet"))):
        pf = pq.ParquetFile(shard)
        col = pf.read(columns=["episode_id"]).column("episode_id").to_pylist()
        for i, eid in enumerate(col):
            index.setdefault(int(eid), (shard, i))  # row i == row group i (1 row/group)
    return index


def read_replay_row(shard_path: str, row_group: int) -> dict:
    pf = pq.ParquetFile(shard_path)
    tbl = pf.read_row_group(row_group, columns=["episode_id", "replay_json"])
    eid = tbl.column("episode_id")[0].as_py()
    blob = tbl.column("replay_json")[0].as_py()
    rep = json.loads(blob)
    if "replay" in rep:  # some dumps wrap it
        r = rep["replay"]
        rep = json.loads(r) if isinstance(r, str) else r
    return rep


def replay_t1_t2_both_seats(rep: dict) -> tuple[list, list, list, list]:
    steps = rep["steps"]
    a1_0 = (steps[1][0].get("action") or {})
    a1_1 = (steps[1][1].get("action") or {})
    a2_0 = (steps[2][0].get("action") or {})
    a2_1 = (steps[2][1].get("action") or {})
    return market(a1_0), market(a2_0), market(a1_1), market(a2_1)


# --------------------------------------------------------- targeted single-episode pulls

CDN_URL = "https://www.kaggleusercontent.com/episodes/{eid}.json"
UA = {"User-Agent": "washamba-endgame/1.0"}


def download_cdn(episode_id: int, timeout: int = 180) -> dict:
    req = urllib.request.Request(CDN_URL.format(eid=int(episode_id)), headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as h:
        blob = h.read()
    rep = json.loads(blob)
    if "replay" in rep:
        r = rep["replay"]
        rep = json.loads(r) if isinstance(r, str) else r
    return rep


def process_rep_file(path: str) -> dict | None:
    """Parse a cached experiments/endgame/rep/<eid>.json and return both seats'
    openings, classifications, TeamNames and final rewards. No episodes.csv join
    needed here - info.TeamNames + rewards is enough, and callers cross-check
    against episodes.csv's bank_0/bank_1 for a name<->seat sanity check."""
    with open(path, encoding="utf-8") as f:
        raw = json.load(f)
    rep = raw.get("replay")
    if isinstance(rep, str):
        rep = json.loads(rep)
    elif not isinstance(rep, dict):
        rep = raw
    steps = rep["steps"]
    info = rep.get("info") or {}
    teams = list(info.get("TeamNames") or ["", ""])
    rewards = rep.get("rewards") or [steps[-1][s].get("reward") for s in range(2)]
    t1_0, t2_0, t1_1, t2_1 = replay_t1_t2_both_seats(rep)
    fam0, c1_0, c2_0 = classify(t1_0, t2_0)
    fam1, c1_1, c2_1 = classify(t1_1, t2_1)
    eid = int(info.get("EpisodeId") or 0)
    return {
        "episode_id": eid, "teams": teams, "rewards": rewards,
        "seat0": {"family": fam0, "t1": c1_0, "t2": c2_0},
        "seat1": {"family": fam1, "t1": c1_1, "t2": c2_1},
    }


def resolve_batch(fetch_list, name2id: dict, id2name: dict) -> tuple[dict, list]:
    """fetch_list: [(tid, {episode_id, date, seat}), ...] (accepts .items() too).
    -> (results {team_id_str: row}, games [row, ...]) - classifies the requested
    team AND, for free, whichever opponent its downloaded replay names."""
    results, games, errors = {}, [], []
    for tid, r in fetch_list:
        eid = r["episode_id"]
        path = os.path.join(REP, "%d.json" % eid)
        try:
            d = process_rep_file(path)
        except Exception as e:
            errors.append((tid, eid, str(e)[:150]))
            continue
        teams = d["teams"]
        want_name = id2name.get(int(tid))
        seat_for_tid = next((s for s in (0, 1) if teams[s] == want_name), r["seat"])
        other_seat = 1 - seat_for_tid
        fam_mine = d["seat0" if seat_for_tid == 0 else "seat1"]["family"]
        fam_other = d["seat0" if other_seat == 0 else "seat1"]["family"]
        other_name = teams[other_seat]
        other_id = name2id.get(other_name)
        results[str(tid)] = {
            "family": fam_mine, "episode_id": eid, "date": r["date"],
            "team_name": teams[seat_for_tid], "seat": seat_for_tid,
            "reward": d["rewards"][seat_for_tid],
        }
        if other_id is not None and str(int(other_id)) not in results:
            results[str(int(other_id))] = {
                "family": fam_other, "episode_id": eid, "date": r["date"],
                "team_name": other_name, "seat": other_seat,
                "reward": d["rewards"][other_seat], "source": "bonus_opponent",
            }
        games.append({
            "episode_id": eid, "date": r["date"],
            "team_a_id": int(tid), "team_a_name": teams[seat_for_tid], "fam_a": fam_mine,
            "reward_a": d["rewards"][seat_for_tid],
            "team_b_id": int(other_id) if other_id is not None else None,
            "team_b_name": other_name, "fam_b": fam_other, "reward_b": d["rewards"][other_seat],
        })
    return results, games, errors


if __name__ == "__main__":
    print("import-only scratch module; see docs/ENDGAME/field_families_2026-09-25.md notes "
          "for the driver commands used interactively.")
