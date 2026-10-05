#!/usr/bin/env python3
"""
Offline tooling that builds Switchboard's multi-family profile set and its
shop-based routing table, reusing build_atlas_profile.py's extraction/
clustering pipeline so both agents are built from the identical corpus and
methodology (including the corrected, state-based daily crew schedule -
see build_atlas_profile.py's WORKFORCE_SAFE_HOUR note).

Families: every cluster with submission-purity >= 0.7 (dominated by one
real top-five submission, not a blend of different agents' policies) -
the same bar Atlas's own family had to clear. On the current corpus this
is 3 families (clusters 1, 3, 4), within the requested 2-4 range.

Routing table: built from ALL 300 trajectories (wins AND losses, not just
winners - a routing DECISION needs a win-rate comparison, which needs both
outcomes), keyed on the shop signal actually observed:
  - by step 72:  first unlocked shop (+ seat, if adequately supported)
  - by step 144: first two unlocked shops (+ seat, if adequately supported)
For each observed context, compare each family's win rate among
trajectories that saw that same context (using each trajectory's REAL
cluster membership as a proxy for "this shop context co-occurred with
this family's play" - not a claim about what a different family would
have scored under that context, which we cannot replay). A context routes
to a family only with a minimum sample size and a clear enough margin;
otherwise it falls back to the default family (whichever has the best
overall pure-cluster win rate - the same family Atlas already uses).

Run:
    python experiments/build_switchboard_profiles.py
"""
import json
from collections import defaultdict, Counter
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_atlas_profile import (  # noqa: E402
    load_and_cluster, pick_best_pure_cluster, build_family_output,
    OUT_DIR as ATLAS_OUT_DIR,
)

OUT_DIR = Path.home() / "KagricultureLocalData" / "episodes" / "switchboard_profiles"
PURITY_BAR = 0.7
MIN_CONTEXT_SAMPLE = 8   # per (context, family) - below this, don't trust the comparison
MIN_MARGIN = 0.12        # winning family's win rate must lead the default by this much


def shop_context(record, turn):
    cp = record["checkpoints"].get(turn)
    if not cp:
        return None
    return cp.get("first_shop"), cp.get("second_shop")


def build_routing_table(all_records, family_labels, default_label, turn, use_seat):
    """key -> {"family": label, "n": n, "win_rate": wr, "default_win_rate": dwr}
    key is (first_shop,) for turn 72, (first_shop, second_shop) for turn 144,
    optionally with seat appended when use_seat is True for that key."""
    # tally[key][family_label] = [wins, total]
    tally = defaultdict(lambda: defaultdict(lambda: [0, 0]))
    for r in all_records:
        lab = r.get("_cluster_label")
        if lab not in family_labels:
            continue
        ctx = shop_context(r, turn)
        if ctx is None or ctx[0] is None:
            continue
        key = (ctx[0],) if turn == 72 else ctx
        if use_seat:
            key = key + (r["target_seat"],)
        won = 1 if r["result"] == "win" else 0
        tally[key][lab][0] += won
        tally[key][lab][1] += 1

    table = {}
    for key, per_family in tally.items():
        default_wins, default_n = per_family.get(default_label, [0, 0])
        default_wr = default_wins / default_n if default_n else 0.0
        best_label, best_wr, best_n = default_label, default_wr, default_n
        for lab, (wins, n) in per_family.items():
            if n < MIN_CONTEXT_SAMPLE:
                continue
            wr = wins / n
            if wr > best_wr + MIN_MARGIN and wr > best_wr:
                best_label, best_wr, best_n = lab, wr, n
        table[key] = {
            "family": best_label, "n": best_n, "win_rate": round(best_wr, 3),
            "default_win_rate": round(default_wr, 3),
            "per_family": {str(lab): {"wins": w, "n": n} for lab, (w, n) in per_family.items()},
        }
    return table


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    records, candidates, dist, record_index, best_k, best_score = load_and_cluster()
    print(f"Selected k={best_k} (silhouette-like={best_score:.4f})")

    pure = [c for c in candidates if c["purity"] >= PURITY_BAR]
    pure.sort(key=lambda c: -c["win_rate"])
    print(f"\n{len(pure)} pure (purity >= {PURITY_BAR}) families available:")
    for c in pure:
        print(f"  cluster {c['label']}: n={c['n']} win_rate={c['win_rate']:.2f} "
             f"purity={c['purity']:.2f} top_submission={c['top_submission']}")

    family_labels = [c["label"] for c in pure]
    default_cluster = pick_best_pure_cluster(candidates)
    default_label = default_cluster["label"]
    print(f"\nDefault family (best pure win rate): cluster {default_label}")

    # Tag every record with its cluster label so the routing table can look
    # up "which family does this real trajectory's own play belong to."
    label_by_record_id = {}
    for c in candidates:
        for r in c["records"]:
            label_by_record_id[id(r)] = c["label"]
    for r in records:
        r["_cluster_label"] = label_by_record_id.get(id(r))

    families = {}
    for c in pure:
        out = build_family_output(c, records, candidates, dist, record_index)
        families[c["label"]] = out

    print("\nBuilding routing tables (both wins and losses, all 300 trajectories) ...")
    # First check whether seat is "adequately supported" (enough samples
    # per (context, seat) pair to split on it) before using it in the key.
    def seat_supported(turn):
        counts = Counter()
        for r in records:
            lab = r.get("_cluster_label")
            if lab not in family_labels:
                continue
            ctx = shop_context(r, turn)
            if ctx is None or ctx[0] is None:
                continue
            key = (ctx[0],) if turn == 72 else ctx
            counts[(key, r["target_seat"])] += 1
        # "adequately supported" - every (context, seat) combo that appears
        # at all clears the same minimum sample bar the routing decision
        # itself requires; otherwise seat just adds sparsity with no signal.
        return bool(counts) and min(counts.values()) >= MIN_CONTEXT_SAMPLE

    use_seat_72 = seat_supported(72)
    use_seat_144 = seat_supported(144)
    print(f"seat adequately supported at step 72: {use_seat_72}")
    print(f"seat adequately supported at step 144: {use_seat_144}")

    table_72 = build_routing_table(records, family_labels, default_label, 72, use_seat_72)
    table_144 = build_routing_table(records, family_labels, default_label, 144, use_seat_144)

    def fmt_table(t):
        return {str(k): v for k, v in t.items()}

    print(f"\nstep-72 routing table ({len(table_72)} contexts):")
    for k, v in table_72.items():
        if v["family"] != default_label:
            print(f"  {k} -> family {v['family']} (n={v['n']}, win_rate={v['win_rate']} "
                 f"vs default {v['default_win_rate']})")
    print(f"\nstep-144 routing table ({len(table_144)} contexts):")
    for k, v in table_144.items():
        if v["family"] != default_label:
            print(f"  {k} -> family {v['family']} (n={v['n']}, win_rate={v['win_rate']} "
                 f"vs default {v['default_win_rate']})")

    out = {
        "default_family": default_label,
        "family_labels": family_labels,
        "use_seat_72": use_seat_72,
        "use_seat_144": use_seat_144,
        "routing_table_72": fmt_table(table_72),
        "routing_table_144": fmt_table(table_144),
        "families": families,
    }
    with open(OUT_DIR / "switchboard_profiles_source.json", "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2, default=str)
    print(f"\nWrote {OUT_DIR / 'switchboard_profiles_source.json'}")


if __name__ == "__main__":
    main()
