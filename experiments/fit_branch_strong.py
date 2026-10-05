"""Re-fit router_selector.py's branch strictly on the strong field.

The previous fit (fit_branch.py, matchups.parquet, median opponent ~712) found
no branch: fam curb-stomped a mostly-weak field (mu=+138,514, Phi=100%, n=150),
so the mu<0 precondition never fired. That result was correct given its input,
but the input was the wrong population - we don't play a median-712 opponent
on the ladder. This file re-fits against matchups_top.parquet's strong field
instead (opponents rated 2,000+, matchups_top's own floor).

IDENTIFIER LIMITATION. The live meta-report's team handles and stream_hash
lineages are NOT a verified crosswalk to this benchmark's opponent_behaviour
column (stream-hash coverage is below its own 95% gate). This file never
claims an opponent_behaviour is a specific team or stream_hash - grouping
identity is opponent_behaviour and nothing else.

WHY STILL POOLED, NOT PER-SHOP-KEY. Same limitation as fit_branch.py:
_pick_continuation's routing key is the shop-unlock signature, which
matchups_top.parquet does not record at all. The fit still can't condition
on "which shop-key are we in" - it pools the strong-field panel and asks,
per already-reachable tape (y1/y2/y8/y9 - see fit_branch.py for why only
these four), whether fam is behind and the tape clearly beats it. A tape
that passes is turned on for every EXISTING CONTINUATIONS key that already
designates it.

RATING FLOOR. Try opponent_rating >= 2400 first. matchups_top.parquet's own
floor is already 2,000 (README: "opponents rated 2,000+"), so ">= 2000" here
is a no-op widen (whole file) - kept anyway per the instructions, and
reported as a no-op if it triggers.

WHOLE-BEHAVIOUR FIT/HOLD-OUT SPLIT. A hash-based 50/50 split of the panel's
distinct opponent_behaviour values (never by seed - splitting a seed off its
own behaviour's other rows would leak that behaviour into both sides). Only
attempted if BOTH resulting halves clear OBJECTIVE_MIN_GAMES_PER_CLUSTER (20)
distinct behaviours; otherwise this file says so plainly and falls back to
fit-only + PROVISIONAL, deferring the honest score to the ladder.

PER-BEHAVIOUR AVERAGING. A behaviour with multiple rows in the panel (up to 6
here) is replayed on ALL its rows, then averaged into ONE data point for that
behaviour before pooling - so a heavily-repeated opponent can't outweigh a
singleton one in the pooled mu/sigma, matching fit_branch.py's convention.

Two phases, run separately because phase 2 needs router_selector.py hand-
edited with phase 1's fitted numbers first (see that file's SCORE_TABLE
comment) - this script never edits the agent itself, so a fit run can't
silently change what ships without a diff to review:

    .venv/bin/python experiments/fit_branch_strong.py fit
    ... hand-edit agents/router_selector.py's SCORE_TABLE per the printed entries ...
    .venv/bin/python experiments/fit_branch_strong.py holdout
"""

import hashlib
import importlib.util
import os
import statistics
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gate import play, make_scripted_opponent, _parse_action_tape, _phi  # noqa: E402
from gate import BENCHMARK_PASS_SCORE_MARGIN, OBJECTIVE_MIN_GAMES_PER_CLUSTER  # noqa: E402
from gate import run_replays, _score_against, _aggregate, _aggregate_by_behaviour  # noqa: E402
from gate import load_module, NEAR_TIE_BAND  # noqa: E402

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STRONG_PARQUET = os.path.join(REPO_ROOT, "data", "benchmark", "matchups_top.parquet")
FAM_PATH = os.path.join(REPO_ROOT, "agents", "router_fam_yarn.py")
SELECTOR_PATH = os.path.join(REPO_ROOT, "agents", "router_selector.py")

RATING_FLOOR_PRIMARY = 2400
RATING_FLOOR_WIDE = 2000
SPLIT_FRACTION = 0.5          # fit vs hold-out, by whole opponent_behaviour
SPLIT_SALT = "fit-strong-v1"  # distinct from gate.py's own TRAIN_HOLDOUT split - different purpose


def load_agent(path):
    spec = importlib.util.spec_from_file_location(
        "fit_strong_" + os.path.splitext(os.path.basename(path))[0], path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.agent


def split_by_behaviour(behaviours, fraction, salt):
    """Deterministic hash-based split - same mechanism as gate.split_behaviours
    (stable across runs, independent of Python's randomized str hash) but with
    a configurable fraction and a distinct salt, since this is a fit/hold-out
    split for THIS exercise, not gate.py's gate/train reserve."""
    a, b = set(), set()
    for beh in sorted(set(behaviours)):
        digest = hashlib.md5((salt + str(beh)).encode()).hexdigest()
        frac = int(digest[:8], 16) / 0xFFFFFFFF
        (a if frac < fraction else b).add(beh)
    return a, b


def build_panel():
    """(panel_df, floor_used, fit_behaviours, hold_behaviours, do_holdout)."""
    import pandas as pd
    df = pd.read_parquet(STRONG_PARQUET, columns=["seed", "your_seat", "opponent_actions",
                                                    "opponent_behaviour", "opponent_rating"])
    print(f"matchups_top.parquet: {len(df)} rows, {df['opponent_behaviour'].nunique()} "
          f"distinct behaviours total")

    panel = df[df["opponent_rating"] >= RATING_FLOOR_PRIMARY]
    floor_used = RATING_FLOOR_PRIMARY
    n_beh = panel["opponent_behaviour"].nunique()
    print(f"rating >= {RATING_FLOOR_PRIMARY}: {len(panel)} rows, {n_beh} distinct behaviours")
    if n_beh < OBJECTIVE_MIN_GAMES_PER_CLUSTER:
        print(f"  below the {OBJECTIVE_MIN_GAMES_PER_CLUSTER}-behaviour floor - "
              f"widening to >= {RATING_FLOOR_WIDE}")
        panel = df[df["opponent_rating"] >= RATING_FLOOR_WIDE]
        floor_used = RATING_FLOOR_WIDE
        n_beh = panel["opponent_behaviour"].nunique()
        print(f"  rating >= {RATING_FLOOR_WIDE}: {len(panel)} rows, {n_beh} distinct behaviours")

    behaviours = panel["opponent_behaviour"].unique().tolist()
    fit_b, hold_b = split_by_behaviour(behaviours, SPLIT_FRACTION, SPLIT_SALT)
    do_holdout = (len(fit_b) >= OBJECTIVE_MIN_GAMES_PER_CLUSTER and
                  len(hold_b) >= OBJECTIVE_MIN_GAMES_PER_CLUSTER)
    print(f"\nwhole-behaviour 50/50 split attempt: {len(fit_b)} fit / {len(hold_b)} hold-out behaviours")
    if do_holdout:
        print(f"  both sides clear the {OBJECTIVE_MIN_GAMES_PER_CLUSTER}-behaviour floor - "
              "running a real fit/hold-out split.\n")
    else:
        print(f"  too thin to split ({len(fit_b)}/{len(hold_b)} vs floor "
              f"{OBJECTIVE_MIN_GAMES_PER_CLUSTER}) - PROVISIONAL: fit-only on the full panel, "
              "no held-out score; defer the honest score to the ladder.\n")
        fit_b = set(behaviours)
        hold_b = set()

    return panel, floor_used, fit_b, hold_b, do_holdout


def replay_own_bank(agent_fn, row):
    tape = _parse_action_tape(row.opponent_actions)
    scripted = make_scripted_opponent(tape)
    if row.your_seat == 0:
        own, opp = play(agent_fn, scripted, int(row.seed))
    else:
        opp, own = play(scripted, agent_fn, int(row.seed))
    return own, opp


def _pooled_stats(per_behaviour_values):
    vals = list(per_behaviour_values)
    mu = statistics.mean(vals)
    sigma = statistics.stdev(vals) if len(vals) > 1 else None
    if sigma is None or sigma == 0:
        phi = 1.0 if mu > 0 else (0.0 if mu < 0 else 0.5)
    else:
        phi = _phi(mu / sigma)
    return mu, sigma, phi


def _fmt_sigma(sigma):
    return f"{sigma:.0f}" if sigma is not None else "n/a"


def main_fit():
    panel, floor_used, fit_b, hold_b, do_holdout = build_panel()
    fit_panel = panel[panel["opponent_behaviour"].isin(fit_b)]
    fit_rows = list(fit_panel.itertuples())
    print(f"FIT panel: {len(fit_rows)} rows across {len(fit_b)} distinct behaviours "
          f"(rating floor used: {floor_used})\n")

    fam_agent = load_agent(FAM_PATH)

    print("=== PASS 1: fam vs the strong-field FIT panel (on OUR engine) ===")
    per_row = {}   # index in fit_rows -> dict(behaviour, fam_bank, opp_bank)
    for i, row in enumerate(fit_rows):
        fam_bank, opp_bank = replay_own_bank(fam_agent, row)
        per_row[i] = {"behaviour": row.opponent_behaviour, "fam_bank": fam_bank, "opp_bank": opp_bank}
        if (i + 1) % 10 == 0 or i + 1 == len(fit_rows):
            print(f"  [{i + 1}/{len(fit_rows)}] behaviour={row.opponent_behaviour} "
                  f"fam={fam_bank:.0f} opp={opp_bank:.0f}", flush=True)

    by_behaviour = defaultdict(list)
    for r in per_row.values():
        by_behaviour[r["behaviour"]].append(r)

    fam_beh_margin = {b: statistics.mean(x["fam_bank"] - x["opp_bank"] for x in rs)
                       for b, rs in by_behaviour.items()}
    fam_beh_fambank = {b: statistics.mean(x["fam_bank"] for x in rs) for b, rs in by_behaviour.items()}
    fam_beh_oppbank = {b: statistics.mean(x["opp_bank"] for x in rs) for b, rs in by_behaviour.items()}

    fam_mu, fam_sigma, fam_phi = _pooled_stats(fam_beh_margin.values())
    print(f"\nFAM vs strong-field FIT panel: mu={fam_mu:+.0f} sigma={_fmt_sigma(fam_sigma)} "
          f"Phi={fam_phi:.1%} (n={len(fam_beh_margin)} distinct behaviours)")

    # most frequent / most damaging, within the FIT panel (the only data we
    # have full margins for) - reported regardless of the mu<0 outcome below.
    counts = {b: len(rs) for b, rs in by_behaviour.items()}
    most_frequent = max(counts, key=lambda b: counts[b])
    most_damaging = min(fam_beh_margin, key=lambda b: fam_beh_margin[b])
    print(f"\nmost frequent opponent_behaviour in FIT panel: {most_frequent} "
          f"({counts[most_frequent]} rows) - fam mean bank {fam_beh_fambank[most_frequent]:.0f} "
          f"vs opponent mean bank {fam_beh_oppbank[most_frequent]:.0f} "
          f"(margin {fam_beh_margin[most_frequent]:+.0f})")
    print(f"most damaging opponent_behaviour to fam in FIT panel: {most_damaging} "
          f"({counts[most_damaging]} rows) - fam mean bank {fam_beh_fambank[most_damaging]:.0f} "
          f"vs opponent mean bank {fam_beh_oppbank[most_damaging]:.0f} "
          f"(margin {fam_beh_margin[most_damaging]:+.0f})")
    print("(opponent_behaviour is a hash from the benchmark only - not a claimed team or stream_hash.)")

    if fam_mu >= 0:
        print("\nfam is NOT behind on average against the strong-field FIT panel (mu >= 0) - "
              "no branch qualifies under the accepted design. Stopping - no SCORE_TABLE "
              "entries to add. (Held-out phase is moot; router_selector.py stays unchanged.)")
        return

    print("\nfam IS behind on average against the strong field (mu < 0) - testing the 4 "
          "reachable tapes...\n")

    sys.path.insert(0, os.path.join(REPO_ROOT, "agents"))
    import router_selector as rs
    tape_keys = {}
    for key, cont in rs.CONTINUATIONS.items():
        tape_keys.setdefault(cont["candidates"][0], []).append(key)
    print(f"tapes reachable via CONTINUATIONS: { {t: len(ks) for t, ks in sorted(tape_keys.items())} }\n")

    tape_agent_cache = {}

    def get_tape_agent(tape_name):
        if tape_name not in tape_agent_cache:
            tape_agent_cache[tape_name] = make_scripted_opponent(rs._TAPES[tape_name])
        return tape_agent_cache[tape_name]

    print("=== PASS 2: each reachable tape vs fam, same rows/seeds/seats ===")
    results = {}
    tape_beh_bank = {}   # tape -> behaviour -> mean bank (for frequent/damaging reporting)
    for tape in sorted(tape_keys):
        print(f"\n-- {tape} ({len(tape_keys[tape])} existing keys: {tape_keys[tape]}) --")
        tape_bank_by_row = {}
        for i, row in enumerate(fit_rows):
            tape_bank, _ = replay_own_bank(get_tape_agent(tape), row)
            tape_bank_by_row[i] = tape_bank
            if (i + 1) % 25 == 0 or i + 1 == len(fit_rows):
                print(f"  [{i + 1}/{len(fit_rows)}]", flush=True)

        beh_rows = defaultdict(list)
        for i, row in enumerate(fit_rows):
            beh_rows[row.opponent_behaviour].append((tape_bank_by_row[i], per_row[i]["fam_bank"]))
        beh_margin = {b: statistics.mean(t - f for t, f in vals) for b, vals in beh_rows.items()}
        beh_bank = {b: statistics.mean(t for t, f in vals) for b, vals in beh_rows.items()}
        tape_beh_bank[tape] = beh_bank

        mu, sigma, phi = _pooled_stats(beh_margin.values())
        n_beh = len(beh_margin)
        passed = (phi >= 0.5 + BENCHMARK_PASS_SCORE_MARGIN) and (n_beh >= OBJECTIVE_MIN_GAMES_PER_CLUSTER)
        print(f"  {tape} vs fam: mu={mu:+.0f} sigma={_fmt_sigma(sigma)} Phi={phi:.1%} "
              f"(n={n_beh} distinct behaviours, need Phi>={0.5 + BENCHMARK_PASS_SCORE_MARGIN:.0%} "
              f"and n>={OBJECTIVE_MIN_GAMES_PER_CLUSTER})  -> {'PASS' if passed else 'THIN-not-routed' if n_beh < OBJECTIVE_MIN_GAMES_PER_CLUSTER else 'FAIL'}")
        results[tape] = {"mu": mu, "sigma": sigma, "phi": phi, "passed": passed,
                          "n": n_beh, "keys": tape_keys[tape], "beh_margin": beh_margin}

    print("\n\n=== FIT-SPLIT SUMMARY (strong field, rating >= {}) ===".format(floor_used))
    print(f"fam vs strong field: mu={fam_mu:+.0f} sigma={_fmt_sigma(fam_sigma)} Phi={fam_phi:.1%} "
          f"(n={len(fam_beh_margin)} distinct behaviours)")
    for tape, r in sorted(results.items()):
        verdict = "PASS" if r["passed"] else ("THIN-not-routed" if r["n"] < OBJECTIVE_MIN_GAMES_PER_CLUSTER else "FAIL")
        print(f"  {tape}: mu={r['mu']:+.0f} sigma={_fmt_sigma(r['sigma'])} Phi={r['phi']:.1%} "
              f"n={r['n']} distinct behaviours -> {verdict} (keys: {r['keys']})")

    print(f"\nmost frequent behaviour ({most_frequent}, {counts[most_frequent]} rows) bank by tape:")
    for tape in sorted(tape_beh_bank):
        b = tape_beh_bank[tape].get(most_frequent)
        print(f"  {tape}: {b:.0f}" if b is not None else f"  {tape}: n/a (behaviour not in fit panel for this tape)")
    print(f"most damaging behaviour to fam ({most_damaging}, {counts[most_damaging]} rows) bank by tape:")
    for tape in sorted(tape_beh_bank):
        b = tape_beh_bank[tape].get(most_damaging)
        print(f"  {tape}: {b:.0f}" if b is not None else f"  {tape}: n/a (behaviour not in fit panel for this tape)")

    passing = {t: r for t, r in results.items() if r["passed"]}
    print("\n=== SCORE_TABLE entries to transcribe into router_selector.py ===")
    if not passing:
        print("  none - no tape cleared the bar. router_selector.py stays behaviour-neutral.")
    else:
        for tape, r in sorted(passing.items()):
            for key in r["keys"]:
                print(f"    SCORE_TABLE[({tape!r}, {key!r})] = ({r['mu']:.1f}, {r['sigma']:.1f})")

    print(f"\ndo_holdout={do_holdout} - if True, run: "
          f".venv/bin/python experiments/fit_branch_strong.py holdout  (after hand-editing router_selector.py)")


def main_holdout():
    panel, floor_used, fit_b, hold_b, do_holdout = build_panel()
    if not do_holdout:
        print("PROVISIONAL run (see fit phase output) - there is no hold-out partition to score. "
              "Nothing to do here; defer the honest score to the ladder.")
        return

    hold_panel = panel[panel["opponent_behaviour"].isin(hold_b)]
    rows = list(hold_panel.itertuples())
    print(f"HOLD-OUT panel: {len(rows)} rows across {len(hold_b)} distinct behaviours "
          f"(rating floor used: {floor_used}, never seen during fitting)\n")

    candidate_agent = load_module(SELECTOR_PATH).agent
    control_agent = load_module(FAM_PATH).agent

    print("replaying control (fam) on the hold-out panel...")
    ctrl_banks = run_replays(control_agent, rows)
    print("replaying candidate (router_selector) on the hold-out panel...")
    cand_banks = run_replays(candidate_agent, rows)

    ctrl_results = _score_against(ctrl_banks, rows, ctrl_banks)
    cand_results = _score_against(cand_banks, rows, ctrl_banks)
    cand_agg = _aggregate(cand_results)
    ctrl_agg = _aggregate(ctrl_results)

    print("\n=== HELD-OUT SCORE (strong-field hold-out partition, ground truth = "
          "control's own same-engine replay) ===")
    distinct_n = hold_panel["opponent_behaviour"].nunique()
    print(f"  {len(rows)} rows / {distinct_n} distinct behaviours, never read during fitting")
    for label, agg in (("candidate", cand_agg), ("control  ", ctrl_agg)):
        sigma_s = _fmt_sigma(agg["sigma"])
        print(f"  {label}  PAIRED win rate {agg['score']:6.1%}  "
              f"W-L-T {agg['wins']}-{agg['losses']}-{agg['ties']} (of {agg['matches']})   "
              f"OBJECTIVE Phi(mu/sigma) {agg['win_prob']:6.1%}  (mu {agg['mu']:+.0f}, sigma {sigma_s})")

    cand_by_b = _aggregate_by_behaviour(cand_results)
    ctrl_by_b = _aggregate_by_behaviour(ctrl_results)
    print(f"\n  per-behaviour ({distinct_n} distinct):")
    for b in sorted(cand_by_b, key=lambda b: cand_by_b[b]["score"]):
        ca, ra = cand_by_b[b], ctrl_by_b[b]
        flag = " (near-tie noise)" if abs(ca["mu"]) < NEAR_TIE_BAND else ""
        print(f"    {b}  n={ca['matches']}  cand {ca['score']:.1%}  ctrl {ra['score']:.1%}  "
              f"mu {ca['mu']:+.0f}{flag}")

    from gate import BENCHMARK_PASS_SCORE_MARGIN, BENCHMARK_MAX_BEHAVIOUR_REGRESSION
    regressions = [b for b in cand_by_b
                   if cand_by_b[b]["score"] < ctrl_by_b[b]["score"] - BENCHMARK_MAX_BEHAVIOUR_REGRESSION]
    cleared = (cand_agg["score"] - ctrl_agg["score"]) >= BENCHMARK_PASS_SCORE_MARGIN
    passed = cleared and not regressions
    print(f"\n  headline: candidate {cand_agg['score']:.1%} vs control {ctrl_agg['score']:.1%} "
          f"(need >= +{BENCHMARK_PASS_SCORE_MARGIN:.0%}, got {cand_agg['score'] - ctrl_agg['score']:+.1%})")
    print(f"  regressed behaviours: {regressions if regressions else 'none'}")
    print(f"\n  {'PASS' if passed else 'FAIL'}")


if __name__ == "__main__":
    phase = sys.argv[1] if len(sys.argv) > 1 else "fit"
    if phase == "fit":
        main_fit()
    elif phase == "holdout":
        main_holdout()
    else:
        print("usage: fit_branch_strong.py [fit|holdout]")
        raise SystemExit(2)
