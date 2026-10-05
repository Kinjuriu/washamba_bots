#!/usr/bin/env python3
"""Extracts per-seat behavioral features from every replay into episode_features.csv.

The point of the table: replay JSONs are heavy, and questions like "how big a crew
does the winner run" should not require parsing gigabytes. One row per (episode, seat).
Hires come from farm state (hires_today), not submitted HIRE orders — the engine
rejects orders once money runs short, so orders overcount.
"""
import csv
import hashlib
import json
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq

HERE = Path(__file__).parent
PARQUET = HERE / "replays.parquet"
OUT = HERE / "episode_features.csv"
HASH_OUT = HERE / "stream_hashes.csv"

# Turns at which the action-stream hash is snapshotted. Proposed by destbreso in the
# dataset discussion (topic 734833) together with this exact normalisation: canonical
# JSON per action, NUL between turns, first 16 hex characters. Keeping it byte for byte
# is the point, otherwise hashes computed elsewhere stop being comparable with these.
PREFIXES = (24, 100, 200, 400, 719)


def stream_hashes(replay):
    """One row per seat: sha256 over that seat's action stream, cut at each prefix.

    Two seats sharing a value at turn N submitted identical actions through turn N,
    which turns "these two agents run the same line" into an observation rather than a
    distance threshold. Prefixes past the end of a short episode come out empty.
    """
    steps = replay["steps"]
    rows = []
    for seat in (0, 1):
        h = hashlib.sha256()
        row = {"seat": seat, "turns": max(0, len(steps) - 1)}
        for t, step in enumerate(steps):
            if not t:    # steps[0] holds the engine's opening pass; skipped by
                continue # convention, so hashes stay comparable across tools
            a = step[seat].get("action") or {}
            h.update(json.dumps(a, sort_keys=True, separators=(",", ":")).encode())
            h.update(b"\0")
            if t in PREFIXES:
                row[f"stream_h{t}"] = h.hexdigest()[:16]
        rows.append(row)
    return rows


# Crop vocabulary from the engine: a malformed order once produced plants_west /
# plants_north columns, so the parser now only counts real crops.
CROPS = {"CARROT", "MELON", "STRAWBERRY", "TOMATO", "WHEAT"}


def features(episode_id, replay):
    steps = replay["steps"]
    rows = []
    # market prices are shared between seats; summarize once per episode
    prices = {}
    for s in steps:
        for prod, price in s[0]["observation"]["market"]["prices"].items():
            lo, hi = prices.get(prod, (price, price))
            prices[prod] = (min(lo, price), max(hi, price))
    for seat in (0, 1):
        crops, first_land, peak_crew, hires_by_day = {}, None, 0, {}
        money = []
        for t, step in enumerate(steps):
            farm = step[0]["observation"]["farms"][seat]
            day = t // 24
            money.append(farm["money"])
            hires_by_day[day] = max(hires_by_day.get(day, 0), farm["hires_today"])
            peak_crew = max(peak_crew, len(farm["hands"]))
            a = step[seat].get("action") or {}
            for order in (a.get("market") or []):
                if isinstance(order, list) and order and order[0] == "BUY_LAND" \
                        and first_land is None:
                    first_land = day
            for unit in [a.get("farmer") or []] + list(a.get("hands") or []):
                if isinstance(unit, list) and unit and unit[0] == "PLANT" and len(unit) > 1 \
                        and unit[1] in CROPS:
                    crops[unit[1]] = crops.get(unit[1], 0) + 1
        final = money[-1] if money else None
        elbow = None
        if final and final > 0:
            cross = next((t for t, m in enumerate(money) if m > final * .1), None)
            elbow = None if cross is None else cross // 24
        row = {"episode_id": episode_id, "seat": seat, "final_money": final,
               "peak_crew": peak_crew, "total_hires": sum(hires_by_day.values()),
               "first_land_day": first_land, "elbow_day": elbow,
               "tiles_planted": sum(crops.values())}
        for c, n in crops.items():            # crop vocabulary comes from the data
            row[f"plants_{c.lower()}"] = n
        for prod, (lo, hi) in sorted(prices.items()):
            row[f"price_{prod.lower()}_min"] = lo
            row[f"price_{prod.lower()}_max"] = hi
        rows.append(row)
    return rows


def main():
    have = {}
    if OUT.exists():        # incremental: keep rows for episodes already done
        old = pd.read_csv(OUT)
        have = {int(e) for e in old.episode_id.unique()}
    old_hash, have_hash = None, set()
    if HASH_OUT.exists():   # the hash table fills in its own pass, so track it apart
        old_hash = pd.read_csv(HASH_OUT)
        have_hash = {int(e) for e in old_hash.episode_id.unique()}
    pf = pq.ParquetFile(PARQUET)
    new_rows, new_hash_rows, done = [], [], 0
    for batch in pf.iter_batches(batch_size=20):
        tbl = batch.to_pydict()
        for eid, blob in zip(tbl["episode_id"], tbl["replay_json"]):
            if eid in have and eid in have_hash:
                continue
            try:
                replay = json.loads(blob)
                if eid not in have:
                    new_rows.extend(features(eid, replay))
                if eid not in have_hash:
                    new_hash_rows.extend(dict(episode_id=eid, **r)
                                         for r in stream_hashes(replay))
            except Exception as e:
                print(f"  episode {eid}: skipped ({e})")
            done += 1
            if done % 50 == 0:
                print(f"  parsed {done} new replays")
    if new_hash_rows:
        h = pd.DataFrame(new_hash_rows)
        h = pd.concat([old_hash, h], ignore_index=True) if old_hash is not None else h
        h = h.sort_values(["episode_id", "seat"])
        h = h[["episode_id", "seat", "turns"] + [f"stream_h{t}" for t in PREFIXES]]
        h.to_csv(HASH_OUT, index=False)
        print(f"stream_hashes.csv: {h.episode_id.nunique()} episodes, {len(h)} rows")
    if have and not new_rows:
        print(f"episode_features.csv: up to date ({len(have)} episodes)")
        return
    new = pd.DataFrame(new_rows)
    out = pd.concat([old, new], ignore_index=True) if have else new
    out = out.sort_values(["episode_id", "seat"])
    plant_cols = [c for c in out.columns if c.startswith("plants_")]
    out[plant_cols] = out[plant_cols].fillna(0).astype(int)
    lead = ["episode_id", "seat", "final_money", "peak_crew", "total_hires",
            "first_land_day", "elbow_day", "tiles_planted"]
    out = out[lead + sorted(plant_cols) + sorted(c for c in out.columns
                                                 if c.startswith("price_"))]
    out.to_csv(OUT, index=False)
    print(f"episode_features.csv: {out.episode_id.nunique()} episodes, {len(out)} rows, "
          f"{len(out.columns)} columns")


def write_daily_stats(here):
    """daily_stats.csv: one row per UTC day — the meta's longitudinal series.
    Everything derives from episodes.csv, so the whole history rebuilds every run."""
    import pandas as pd
    eps = pd.read_csv(here / "episodes.csv")
    eps["end"] = pd.to_datetime(eps.end_time, format="mixed", utc=True)
    eps["winner_bank"] = eps[["bank_0", "bank_1"]].max(axis=1)
    lad = eps[eps.type.eq("EPISODE_TYPE_PUBLIC") & eps.state.eq("COMPLETED")
              & eps.winner_bank.gt(0)].copy()
    lad["day"] = lad.end.dt.date
    feats = here / "episode_features.csv"
    have_replay = set()
    if feats.exists():
        have_replay = set(pd.read_csv(feats).episode_id.unique())
    rows = []
    for day, g in lad.groupby("day"):
        rows.append({
            "date": day, "ladder_games": len(g),
            "teams_active": pd.unique(g[["team_0", "team_1"]].values.ravel()).size,
            "median_winner_bank": round(g.winner_bank.median(), 1),
            "p90_winner_bank": round(g.winner_bank.quantile(.9), 1),
            "record_bank": g.winner_bank.max(),
            "replay_coverage": round(g.episode_id.isin(have_replay).mean(), 3),
        })
    pd.DataFrame(rows).to_csv(here / "daily_stats.csv", index=False)
    print(f"daily_stats.csv: {len(rows)} days")


if __name__ == "__main__":
    main()
    write_daily_stats(HERE)
