#!/usr/bin/env python3
"""
Rebuilds Switchboard's routing table to the corrected spec: three decision
points (72/144/216, freeze after 216), a 4-tier back-off (shops+seat+coarse
opponent descriptors -> shops+seat -> shops -> default), wins AND losses
(ties worth half) with Beta(1,1) smoothing, and a distinct-episode-count
support threshold (not trajectory count, since two rows can share one
episode when two target players faced each other).

Reuses build_atlas_profile.py's clustering (same 3 pure families already
selected - NOT re-clustered) and load_replay. Opponent descriptors are
built the same way CLAUDE.md documents obs["farms"] working: tiles/hands/
money are public for both farms, only obs["private"] (shed/seeds/carried
inventory) is ours alone - so land/crop-count/animal-count/workforce read
off the opponent's own obs["farms"][1-seat] are legitimate public reads,
never the opponent's shed/seeds/inventory, never future turns.

Run:
    python experiments/build_switchboard_routing_v2.py
"""
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_atlas_profile import load_and_cluster, REPLAY_DIR, load_replay  # noqa: E402

OUT_DIR = Path.home() / "KagricultureLocalData" / "episodes" / "switchboard_profiles"
DECISION_TURNS = [72, 144, 216]
FREEZE_TURN = 216
PURITY_BAR = 0.7
MIN_DISTINCT_EPISODES = 8
MIN_MARGIN = 0.10


def bucket(value, edges, labels):
    for e, lab in zip(edges, labels[:-1]):
        if value <= e:
            return lab
    return labels[-1]


def land_bucket(tiles_unlocked):
    return bucket(tiles_unlocked, [25, 50, 75], ["<=25", "<=50", "<=75", ">75"])


def crop_count_bucket(n):
    return bucket(n, [0, 9, 24], ["0", "1-9", "10-24", "25+"])


def animal_count_bucket(n):
    return bucket(n, [0, 3, 7], ["0", "1-3", "4-7", "8+"])


def workforce_bucket(n):
    if n is None:
        return "unknown"
    return bucket(n, [0, 4, 8], ["0", "1-4", "5-8", "9+"])


def opponent_descriptor_at(replay, seat, turn):
    """Coarse public descriptor of the OPPONENT's farm at `turn`, from
    obs["farms"][opponent] only (public - tiles/hands/money), never
    obs["private"] (which doesn't exist for the opponent in our own obs
    anyway), never a turn later than `turn`."""
    steps = replay["steps"]
    opp_seat = 1 - seat
    if turn >= len(steps) or seat >= len(steps[turn]):
        return None
    obs = steps[turn][seat].get("observation") or {}
    farms = obs.get("farms") or []
    if opp_seat >= len(farms):
        return None
    opp_farm = farms[opp_seat] or {}

    unlocked = opp_farm.get("unlocked_quadrants") or ["NW"]
    board_size = len(opp_farm.get("tiles") or []) or 10
    tiles_per_quadrant = (board_size * board_size) // 4
    land = len(unlocked) * tiles_per_quadrant

    crops = animals = 0
    for row in opp_farm.get("tiles") or []:
        for t in row:
            if not isinstance(t, dict):
                continue
            if t.get("kind") == "PLANT":
                crops += 1
            elif "animal" in t:
                animals += 1

    # Opponent workforce OBSERVED SO FAR: scan turns 0..turn for the
    # opponent's own hands length at any non-midnight hour (hour 0 is the
    # nightly-reset artifact for THEM too - same bug this whole repair is
    # about, applied symmetrically). None seen yet -> "unknown", never 0.
    max_hands_seen = None
    for t in range(min(turn, len(steps) - 1) + 1):
        if seat >= len(steps[t]):
            continue
        o = steps[t][seat].get("observation") or {}
        if o.get("hour") == 0:
            continue
        f = (o.get("farms") or [None] * (opp_seat + 1))
        if opp_seat >= len(f) or not f[opp_seat]:
            continue
        h = len(f[opp_seat].get("hands") or [])
        if max_hands_seen is None or h > max_hands_seen:
            max_hands_seen = h

    return {
        "land": land_bucket(land),
        "crops": crop_count_bucket(crops),
        "animals": animal_count_bucket(animals),
        "workforce": workforce_bucket(max_hands_seen),
    }


def shops_key(record, turn):
    cp = record["checkpoints"].get(turn)
    if not cp:
        return None
    # first_shop/second_shop only capture the first two - re-derive the
    # FULL revealed-so-far list the same way (cumulative, first-seen
    # order) by walking every earlier checkpoint's own first/second (a
    # cheap approximation bounded by how many checkpoints precede `turn`;
    # exact full history is available at checkpoint turns only, which is
    # exactly when routing decisions are made anyway).
    seen = []
    for t in [0, 72, 144, 216, 288]:
        if t > turn:
            break
        c = record["checkpoints"].get(t)
        if not c:
            continue
        for s in (c.get("first_shop"), c.get("second_shop")):
            if s and s not in seen:
                seen.append(s)
    return tuple(seen)


def outcome_weight(record):
    if record["result"] == "win":
        return 1.0
    if record["result"] == "tie":
        return 0.5
    return 0.0


def beta_smoothed_rate(successes, total):
    return (successes + 1.0) / (total + 2.0)  # Beta(1,1) posterior mean


def build_tier_table(records, family_labels, default_label, turn, key_fn):
    """tally[key][family_label] = {"weighted_wins": w, "n": n, "episodes": set()}"""
    tally = defaultdict(lambda: defaultdict(lambda: {"w": 0.0, "n": 0, "episodes": set()}))
    for r in records:
        lab = r.get("_cluster_label")
        if lab not in family_labels:
            continue
        key = key_fn(r, turn)
        if key is None:
            continue
        cell = tally[key][lab]
        cell["w"] += outcome_weight(r)
        cell["n"] += 1
        cell["episodes"].add(r["episode_id"])

    table = {}
    for key, per_family in tally.items():
        default_cell = per_family.get(default_label, {"w": 0.0, "n": 0, "episodes": set()})
        default_rate = beta_smoothed_rate(default_cell["w"], default_cell["n"])
        best_label, best_rate, best_n, best_eps = default_label, default_rate, default_cell["n"], len(default_cell["episodes"])
        for lab, cell in per_family.items():
            n_episodes = len(cell["episodes"])
            if n_episodes < MIN_DISTINCT_EPISODES:
                continue
            rate = beta_smoothed_rate(cell["w"], cell["n"])
            if rate > best_rate + MIN_MARGIN and rate > best_rate:
                best_label, best_rate, best_n, best_eps = lab, rate, cell["n"], n_episodes
        table[key] = {
            "family": best_label, "smoothed_win_rate": round(best_rate, 3),
            "default_smoothed_win_rate": round(default_rate, 3),
            "n_trajectories": best_n, "n_distinct_episodes": best_eps,
            "per_family": {
                str(lab): {"weighted_wins": cell["w"], "n": cell["n"], "n_episodes": len(cell["episodes"])}
                for lab, cell in per_family.items()
            },
        }
    return table


def main():
    records, candidates, dist, record_index, best_k, best_score = load_and_cluster()
    label_by_id = {}
    for c in candidates:
        for r in c["records"]:
            label_by_id[id(r)] = c["label"]
    for r in records:
        r["_cluster_label"] = label_by_id.get(id(r))

    pure = [c for c in candidates if c["purity"] >= PURITY_BAR]
    family_labels = [c["label"] for c in pure]
    pure_sorted = sorted(pure, key=lambda c: -c["win_rate"])
    default_label = pure_sorted[0]["label"]
    print(f"Families: {family_labels}, default: {default_label}")

    # Need opponent descriptors computed from raw replays - cache replay
    # objects per episode across records that share one (dedup work).
    print("Loading replays for opponent-descriptor extraction ...")
    replay_cache = {}
    for r in records:
        eid = r["episode_id"]
        if eid not in replay_cache:
            replay_cache[eid] = load_replay(REPLAY_DIR / f"{eid}.json.gz")

    tables = {}
    for turn in DECISION_TURNS:
        print(f"\n--- decision turn {turn} ---")

        def key_shops(r, t=turn):
            return shops_key(r, t)

        def key_shops_seat(r, t=turn):
            sk = shops_key(r, t)
            return None if sk is None else (sk, r["target_seat"])

        def key_shops_seat_opp(r, t=turn):
            sk = shops_key(r, t)
            if sk is None:
                return None
            opp = opponent_descriptor_at(replay_cache[r["episode_id"]], r["target_seat"], t)
            if opp is None:
                return None
            return (sk, r["target_seat"], opp["land"], opp["crops"], opp["animals"], opp["workforce"])

        t_shops = build_tier_table(records, family_labels, default_label, turn, key_shops)
        t_shops_seat = build_tier_table(records, family_labels, default_label, turn, key_shops_seat)
        t_shops_seat_opp = build_tier_table(records, family_labels, default_label, turn, key_shops_seat_opp)

        for name, t in [("shops", t_shops), ("shops+seat", t_shops_seat),
                        ("shops+seat+opponent", t_shops_seat_opp)]:
            non_default = {k: v for k, v in t.items() if v["family"] != default_label}
            print(f"  tier '{name}': {len(t)} contexts total, {len(non_default)} route to a non-default family")
            for k, v in list(non_default.items())[:10]:
                print(f"    {k} -> family {v['family']} "
                     f"(smoothed_wr={v['smoothed_win_rate']}, default_wr={v['default_smoothed_win_rate']}, "
                     f"n_traj={v['n_trajectories']}, n_episodes={v['n_distinct_episodes']})")

        tables[turn] = {
            "shops": {str(k): v for k, v in t_shops.items()},
            "shops_seat": {str(k): v for k, v in t_shops_seat.items()},
            "shops_seat_opp": {str(k): v for k, v in t_shops_seat_opp.items()},
        }

    out = {"default_family": default_label, "family_labels": family_labels, "tables_by_turn": tables}
    with open(OUT_DIR / "switchboard_routing_v2.json", "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2, default=str)
    print(f"\nWrote {OUT_DIR / 'switchboard_routing_v2.json'}")


if __name__ == "__main__":
    main()
