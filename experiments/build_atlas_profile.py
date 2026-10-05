#!/usr/bin/env python3
"""
Offline tooling that extracts a macro strategy profile from the current
top-five replay corpus and writes it as a compact Python literal, to be
pasted into agents/atlas_profile.py's PROFILE constant.

This is analysis tooling, not the agent - numpy/scipy are fine here even
though the agent itself must be stdlib-only.

Win/loss is read from each replay's real terminal `rewards` (bank), never
from requested market orders - a requested SELL/BUY can be rejected by the
engine with no error raised (see CLAUDE.md's silent-failure gotchas), so
only realized bank differences count as evidence of a win.

Clustering uses ONLY the macro state features below - never exact tile
coordinates, team name, submission ID, episode ID, terminal bank, or any
information from a later point in the same trajectory than the feature
itself. Submission ID is checked only AFTER clustering, to see which real
top-five submission(s) a behaviorally-discovered cluster maps back to.

Run:
    python experiments/build_atlas_profile.py
"""
import csv
import gzip
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from scipy.cluster.hierarchy import linkage, fcluster
from scipy.spatial.distance import pdist, squareform

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from pull_episodes import validate_replay_structure  # noqa: E402

try:
    from kaggle_environments.envs.kaggriculture.kaggriculture import ANIMALS, CROPS
except ImportError:
    ANIMALS, CROPS = {}, {}

# Hands are cleared at midnight and rehired each morning (CLAUDE.md), so
# CHECKPOINTS (all exact multiples of 24 -> all hour 0) sample the crew
# size at the one moment per day it is GUARANTEED to read zero, before
# that morning's hiring has landed. Verified against raw replay state
# (medoid 111457276 seat 1 + two more cluster members): HIRE orders land
# the same turn they're submitted (observation at row t already reflects
# row t's own action - obs(t) is post-action(t), not pre-action(t) - see
# module docstring in agents/atlas_profile.py), the morning hiring burst
# is consistently settled by hour 2-4, and the crew holds flat through the
# rest of the day. SAFE_HOUR reads the settled, realized daily crew.
WORKFORCE_SAFE_HOUR = 12
SEASON_DAYS = 30

DATA_DIR = Path.home() / "KagricultureLocalData" / "episodes"
MANIFEST_PATH = DATA_DIR / "manifest.csv"
REPLAY_DIR = DATA_DIR / "replays"
OUT_DIR = DATA_DIR / "atlas_profile"

CHECKPOINTS = [0, 72, 144, 216, 288, 360, 432, 504, 576, 648, 696]
ANIMAL_STRUCTURE_KINDS = {info["structure"] for info in ANIMALS.values() if info.get("structure")}


def load_manifest():
    with open(MANIFEST_PATH, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    for r in rows:
        r["episode_id"] = int(r["episode_id"])
        r["player_seat"] = int(r["player_seat"])
    return rows


def load_replay(gz_path):
    with gzip.open(gz_path, "rt", encoding="utf-8") as fh:
        data = json.load(fh)
    ok, reason = validate_replay_structure(data)
    if not ok:
        raise ValueError(reason)
    return data


def is_harvest_ready(tile, day):
    if tile.get("yield_units", 0) <= 0:
        return False
    info = CROPS.get(tile.get("crop"))
    if not info:
        return tile.get("yield_units", 0) > 0
    first_yield_day = info.get("first_yield_day", 0)
    return day - tile.get("planted_day", day) >= first_yield_day


def checkpoint_features(replay, seat, turn, shops_seen):
    steps = replay["steps"]
    if turn >= len(steps) or seat >= len(steps[turn]):
        return None
    obs = steps[turn][seat].get("observation") or {}
    farms = obs.get("farms") or []
    farm = farms[seat] if seat < len(farms) else {}
    private = obs.get("private") or {}
    town = obs.get("town") or {}
    day = obs.get("day", turn // 24)

    for s in town.get("unlocked_shops") or []:
        if s not in shops_seen:
            shops_seen.append(s)

    tiles = farm.get("tiles") or []
    usable_land = 0
    planted_by_crop = Counter()
    harvest_ready_by_crop = Counter()
    animal_structures = 0
    living_animals = Counter()
    for row in tiles:
        for t in row:
            if t == "LOCKED":
                continue
            usable_land += 1
            if not isinstance(t, dict):
                continue
            kind = t.get("kind")
            if kind == "PLANT":
                crop = t.get("crop")
                planted_by_crop[crop] += 1
                if is_harvest_ready(t, day):
                    harvest_ready_by_crop[crop] += 1
            elif kind in ANIMAL_STRUCTURE_KINDS:
                animal_structures += 1
                animal = t.get("animal")
                if animal:
                    living_animals[animal] += 1

    shed = private.get("shed") or {}
    carried_total = sum(
        sum(v for v in inv.values() if isinstance(v, (int, float)))
        for inv in (private.get("inventories") or [])
        if isinstance(inv, dict)
    )

    return {
        "turn": turn,
        "day": day,
        "seat": seat,
        "first_shop": shops_seen[0] if len(shops_seen) >= 1 else None,
        "second_shop": shops_seen[1] if len(shops_seen) >= 2 else None,
        "bank": farm.get("money", 0.0),
        "usable_land": usable_land,
        "n_hands": len(farm.get("hands") or []),
        "planted_by_crop": dict(planted_by_crop),
        "harvest_ready_by_crop": dict(harvest_ready_by_crop),
        "animal_structures": animal_structures,
        "living_animals_by_species": dict(living_animals),
        "shed_by_product": dict(shed),
        "carried_total": carried_total,
    }


def build_trajectory_record(manifest_row, replay, gz_path):
    seat = manifest_row["player_seat"]
    eid = manifest_row["episode_id"]
    rewards = replay.get("rewards") or [None, None]
    opp_seat = 1 - seat
    my_bank = rewards[seat] if seat < len(rewards) else None
    opp_bank = rewards[opp_seat] if opp_seat < len(rewards) else None
    if my_bank is None or opp_bank is None:
        result = "unknown"
    elif my_bank > opp_bank:
        result = "win"
    elif my_bank < opp_bank:
        result = "loss"
    else:
        result = "tie"

    shops_seen = []
    checkpoints = {}
    for c in CHECKPOINTS:
        feat = checkpoint_features(replay, seat, c, shops_seen)
        if feat is not None:
            checkpoints[c] = feat

    # Milestones provable from the sequence of checkpoint states themselves
    # (checkpoint-resolution, not turn-resolution - see module docstring).
    milestones = {}
    ordered = [checkpoints[c] for c in CHECKPOINTS if c in checkpoints]
    if ordered:
        base = ordered[0]
        milestones["first_land_expansion_turn"] = next(
            (f["turn"] for f in ordered if f["usable_land"] > base["usable_land"]), None)
        milestones["first_hire_turn"] = next(
            (f["turn"] for f in ordered if f["n_hands"] > 0), None)
        milestones["first_harvest_ready_turn"] = next(
            (f["turn"] for f in ordered if sum(f["harvest_ready_by_crop"].values()) > 0), None)
        milestones["first_animal_present_turn"] = next(
            (f["turn"] for f in ordered if sum(f["living_animals_by_species"].values()) > 0), None)

    return {
        "trajectory_id": f"{eid}:{seat}",
        "episode_id": eid,
        "target_submission": manifest_row["player_submission"],
        "target_team": manifest_row["player"],
        "target_seat": seat,
        "result": result,
        "final_bank": my_bank,
        "opponent_final_bank": opp_bank,
        "replay_sha256": None,  # filled by caller if needed
        "checkpoints": checkpoints,
        "milestones": milestones,
    }


NUMERIC_FIELDS = [
    "bank", "usable_land", "n_hands",
]


def feature_vector(record):
    """Standardization-ready raw feature vector: 9 numeric summaries per
    checkpoint x 11 checkpoints. Categorical shop identity is deliberately
    excluded from the clustering vector (kept in the record for reporting
    only) - at this per-checkpoint granularity shop identity was already
    shown, in the prior reconstruction task, to fragment into hundreds of
    near-unique signatures and would dominate a mixed distance metric with
    noise rather than signal."""
    vec = []
    for c in CHECKPOINTS:
        cp = record["checkpoints"].get(c)
        if cp is None:
            vec.extend([0.0] * 9)
            continue
        vec.append(float(cp["bank"]))
        vec.append(float(cp["usable_land"]))
        vec.append(float(cp["n_hands"]))
        vec.append(float(sum(cp["planted_by_crop"].values())))
        vec.append(float(sum(cp["harvest_ready_by_crop"].values())))
        vec.append(float(cp["animal_structures"]))
        vec.append(float(sum(cp["living_animals_by_species"].values())))
        vec.append(float(sum(cp["shed_by_product"].values())))
        vec.append(float(cp["carried_total"]))
    return vec


def silhouette_like(dist, labels):
    """Manual mean silhouette score (sklearn is not installed) - standard
    definition: for each point, (b-a)/max(a,b), a = mean intra-cluster
    distance, b = mean distance to the nearest other cluster."""
    n = len(labels)
    labels = np.asarray(labels)
    unique = np.unique(labels)
    if len(unique) < 2:
        return -1.0
    scores = []
    for i in range(n):
        same = labels == labels[i]
        same[i] = False
        if not same.any():
            continue
        a = dist[i, same].mean()
        b = min(
            dist[i, labels == other].mean()
            for other in unique if other != labels[i]
        )
        scores.append((b - a) / max(a, b) if max(a, b) > 0 else 0.0)
    return float(np.mean(scores)) if scores else -1.0


def extract_daily_crew_schedule(records_with_replay, safe_hour=WORKFORCE_SAFE_HOUR):
    """Realized daily peak crew size, read from state (len(farm['hands']))
    at a safe mid-day hour for every day 0-29, median across the given
    trajectories. State-based, not requested HIRE-order counts - a
    requested HIRE can fail on affordability with no error raised."""
    per_day = defaultdict(list)
    for eid, seat, replay in records_with_replay:
        for row in replay["steps"]:
            if seat >= len(row):
                continue
            obs = row[seat].get("observation") or {}
            if obs.get("hour") != safe_hour:
                continue
            day = obs.get("day")
            farms = obs.get("farms") or []
            farm = farms[seat] if seat < len(farms) else {}
            per_day[day].append(len(farm.get("hands") or []))

    schedule = {}
    for day in range(SEASON_DAYS):
        vals = per_day.get(day)
        schedule[day] = round(float(np.median(vals))) if vals else 0
    return schedule, {day: len(vals) for day, vals in per_day.items()}


def load_and_cluster():
    """Load the full corpus, cluster on macro features, and score every
    resulting cluster. Reusable by anything that needs more than one
    family (e.g. Switchboard) without re-paying the ~50s replay-load cost
    per caller. Returns (records, candidates, dist, record_index, best_k,
    best_score) - candidates carries every cluster's own record list, not
    just the one Atlas ends up selecting."""
    manifest_rows = load_manifest()
    by_episode = defaultdict(list)
    for r in manifest_rows:
        by_episode[r["episode_id"]].append(r)

    records = []
    for eid, rows in sorted(by_episode.items()):
        gz_path = REPLAY_DIR / f"{eid}.json.gz"
        if not gz_path.exists():
            continue
        replay = load_replay(gz_path)
        for row in rows:
            records.append(build_trajectory_record(row, replay, gz_path))

    print(f"Loaded {len(records)} trajectories from {len(by_episode)} episodes.")

    X = np.array([feature_vector(r) for r in records], dtype=np.float64)
    mu, sigma = X.mean(axis=0), X.std(axis=0)
    sigma[sigma == 0] = 1.0
    Xz = (X - mu) / sigma

    dist_condensed = pdist(Xz, metric="euclidean")
    dist = squareform(dist_condensed)
    Z = linkage(dist_condensed, method="ward")

    best_k, best_score, best_labels = None, -2.0, None
    for k in (5, 6, 8, 10, 12, 16, 20):
        labels = fcluster(Z, t=k, criterion="maxclust")
        score = silhouette_like(dist, labels)
        print(f"  k={k:2d}  silhouette-like={score:.4f}  "
              f"cluster sizes={sorted(Counter(labels).values(), reverse=True)}")
        if score > best_score:
            best_k, best_score, best_labels = k, score, labels

    print(f"\nSelected k={best_k} (silhouette-like={best_score:.4f})")

    record_index = {id(r): i for i, r in enumerate(records)}
    clusters = defaultdict(list)
    for rec, lab in zip(records, best_labels):
        clusters[int(lab)].append(rec)

    # --- apply the selection priority ------------------------------------
    candidates = []
    for lab, recs in clusters.items():
        n = len(recs)
        wins = sum(1 for r in recs if r["result"] == "win")
        losses = sum(1 for r in recs if r["result"] == "loss")
        win_rate = wins / n if n else 0.0
        sub_counts = Counter(r["target_submission"] for r in recs)
        top_sub, top_sub_count = sub_counts.most_common(1)[0]
        purity = top_sub_count / n

        idxs = [record_index[id(r)] for r in recs]
        sub_dist = dist[np.ix_(idxs, idxs)]
        cohesion = 1.0 / (1.0 + sub_dist.mean()) if len(idxs) > 1 else 1.0

        candidates.append({
            "label": lab, "records": recs, "n": n, "wins": wins, "losses": losses,
            "win_rate": win_rate, "top_submission": top_sub, "purity": purity,
            "cohesion": cohesion,
        })
        print(f"  cluster {lab}: n={n} wins={wins} losses={losses} "
              f"win_rate={win_rate:.2f} top_submission={top_sub} "
              f"purity={purity:.2f} cohesion={cohesion:.3f}")

    return records, candidates, dist, record_index, best_k, best_score


def pick_best_pure_cluster(candidates, exclude_labels=()):
    """Priority: (1) dominated by one real top-five submission - purity >=
    0.7; (2) >=10 winners if any qualifying cluster clears that bar; (3)
    tighter internal consistency preferred; (4) win rate, then sample
    size; (5) never average across clusters - the pick IS one cluster, and
    its schedule is the median WITHIN it, not a blend across clusters."""
    pool = [c for c in candidates if c["label"] not in exclude_labels]
    pure = [c for c in pool if c["purity"] >= 0.7]
    pool = pure if pure else pool
    have_10 = [c for c in pool if c["wins"] >= 10]
    pool2 = have_10 if have_10 else pool
    pool2.sort(key=lambda c: (-c["win_rate"], -c["n"], -c["cohesion"]))
    return pool2[0]


def build_family_output(selected, records, candidates, dist, record_index):
    """Build one family's full profile output dict (medoid, per-checkpoint
    median schedule, corrected daily crew schedule) from an already-scored
    cluster. Does not write to disk - callers decide the filename."""
    print(f"\nBuilding family for cluster {selected['label']}: n={selected['n']} "
         f"wins={selected['wins']} win_rate={selected['win_rate']:.2f} "
         f"top_submission={selected['top_submission']} purity={selected['purity']:.2f}")

    sel_recs = selected["records"]
    sel_idxs = [record_index[id(r)] for r in sel_recs]
    sub_dist = dist[np.ix_(sel_idxs, sel_idxs)]
    medoid_local = int(np.argmin(sub_dist.sum(axis=1)))
    medoid_record = sel_recs[medoid_local]
    print(f"Medoid trajectory: {medoid_record['trajectory_id']} "
         f"(episode {medoid_record['episode_id']}, result={medoid_record['result']})")

    # --- build the compact target schedule: per-checkpoint MEDIAN within
    # the one selected, already-coherent cluster (not an average across
    # clusters/policies) ----------------------------------------------------
    winners_only = [r for r in sel_recs if r["result"] == "win"]
    schedule_source = winners_only if len(winners_only) >= 5 else sel_recs
    print(f"Schedule built from {len(schedule_source)} trajectories "
         f"({'winners only' if schedule_source is winners_only else 'whole cluster'}).")

    all_crops = sorted({c for r in schedule_source for cp in r["checkpoints"].values()
                        for c in cp["planted_by_crop"]})
    all_species = sorted({s for r in schedule_source for cp in r["checkpoints"].values()
                          for s in cp["living_animals_by_species"]})
    all_products = sorted({p for r in schedule_source for cp in r["checkpoints"].values()
                           for p in cp["shed_by_product"]})

    schedule = []
    for c in CHECKPOINTS:
        cps = [r["checkpoints"][c] for r in schedule_source if c in r["checkpoints"]]
        if not cps:
            continue

        def med(getter):
            vals = [getter(cp) for cp in cps]
            return float(np.median(vals))

        entry = {
            "turn": c,
            "bank": round(med(lambda cp: cp["bank"]), 1),
            "usable_land": round(med(lambda cp: cp["usable_land"])),
            "n_hands": round(med(lambda cp: cp["n_hands"])),
            "planted_by_crop": {
                crop: round(med(lambda cp, crop=crop: cp["planted_by_crop"].get(crop, 0)))
                for crop in all_crops
            },
            "animals_by_species": {
                sp: round(med(lambda cp, sp=sp: cp["living_animals_by_species"].get(sp, 0)))
                for sp in all_species
            },
            "shed_by_product": {
                p: round(med(lambda cp, p=p: cp["shed_by_product"].get(p, 0)))
                for p in all_products
            },
        }
        schedule.append(entry)

    print("\nExtracting corrected daily crew schedule (state-based, safe-hour "
         f"sampling, not the buggy hour-0 checkpoints) from {len(schedule_source)} "
         "trajectories ...")
    records_with_replay = []
    for r in schedule_source:
        gz_path = REPLAY_DIR / f"{r['episode_id']}.json.gz"
        records_with_replay.append((r["episode_id"], r["target_seat"], load_replay(gz_path)))
    daily_crew_schedule, daily_crew_sample_sizes = extract_daily_crew_schedule(records_with_replay)
    print("day -> median realized crew (state-based):")
    for day in range(SEASON_DAYS):
        print(f"  day {day:2d}: {daily_crew_schedule[day]:2d}  (n={daily_crew_sample_sizes.get(day, 0)})")

    # Overwrite each checkpoint's n_hands with the corrected day-indexed
    # value - the old hour-0-sampled median is a known artifact (always
    # ~0, the exact moment hands are guaranteed cleared) and must not be
    # embedded in the agent.
    for entry in schedule:
        day = entry["turn"] // 24
        entry["n_hands"] = daily_crew_schedule.get(day, entry["n_hands"])

    out = {
        "daily_crew_schedule": daily_crew_schedule,
        "daily_crew_sample_sizes": daily_crew_sample_sizes,
        "selected_cluster": {
            "label": selected["label"], "n": selected["n"], "wins": selected["wins"],
            "losses": selected["losses"], "win_rate": selected["win_rate"],
            "top_submission": selected["top_submission"], "purity": selected["purity"],
            "member_trajectory_ids": [r["trajectory_id"] for r in sel_recs],
            "schedule_source": "winners_only" if schedule_source is winners_only else "whole_cluster",
            "schedule_source_n": len(schedule_source),
        },
        "medoid": {
            "trajectory_id": medoid_record["trajectory_id"],
            "episode_id": medoid_record["episode_id"],
            "target_submission": medoid_record["target_submission"],
            "target_seat": medoid_record["target_seat"],
            "result": medoid_record["result"],
        },
        "schedule": schedule,
    }
    return out


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    records, candidates, dist, record_index, best_k, best_score = load_and_cluster()
    print(f"\nSelected k={best_k} (silhouette-like={best_score:.4f})")

    selected = pick_best_pure_cluster(candidates)
    out = build_family_output(selected, records, candidates, dist, record_index)
    out["clustering"] = {
        "k": best_k, "silhouette_like": best_score,
        "all_clusters": [
            {"label": c["label"], "n": c["n"], "wins": c["wins"],
             "losses": c["losses"], "win_rate": c["win_rate"],
             "top_submission": c["top_submission"], "purity": c["purity"]}
            for c in candidates
        ],
    }

    with open(OUT_DIR / "atlas_profile_source.json", "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2, default=str)
    print(f"\nWrote {OUT_DIR / 'atlas_profile_source.json'}")
    print(f"Schedule has {len(out['schedule'])} checkpoints.")


if __name__ == "__main__":
    main()
