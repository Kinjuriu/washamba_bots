"""Offline pre-ladder gate for a selector candidate.

The gate every future agents/router_selector.py-style candidate goes through
before it is worth a submission slot. It is a thin wrapper: scoring is
rank_bases.pair_record (tie-aware, (wins + 0.5*ties)/matches, itself reading
head_to_head.play so a match is scored the same way everywhere in this repo)
and the near-tie diagnostic constant is opponent_strata.NEAR_TIE_BAND. This
file adds no new scoring logic - just the held-out split, the per-lineage
report shape, and the PASS/FAIL line.

WHY NOT opponent_strata.fetch_episodes(). That function pulls real, already-
played ladder episodes for a submission ID that already exists - useful for
diagnosing a live standing, useless for gating a candidate that has not been
submitted yet (no submission ID, no episodes, and it would make every gate
run depend on Kaggle auth and network access). What this file borrows from
opponent_strata.py instead is the one thing that transfers: NEAR_TIE_BAND,
for flagging a per-lineage result that was decided by noise on a ~90,000
economy rather than by anything the candidate did.

WHAT "LINEAGE" MEANS HERE. Not opponent_strata's rating bands - this repo's
own established sense (see agents/route_moon_md_floor_deficit.py: "the
opponents are three different route lineages rather than clones of us", and
docs/ROUTE_GENERATIONS.md): a genuinely different underlying route/strategy
family, not a retuned clone of one already held. The four route_moon_md_*.py
files are four tuning generations of ONE lineage - only one representative
is listed. TUNING_LINEAGES stay available for exploratory head-to-head work
outside this gate; HOLDOUT_LINEAGES are reserved for this gate call only -
never hand-played while iterating on a candidate, so a PASS here means the
candidate has not been tuned against the very thing that approved it. This
is also why the holdout is split by whole lineage, never by seed: splitting
seeds of the same lineage across tuning and holdout leaks that lineage's
behaviour into both sides of the check.

Usage, from the repo root:
    .venv/bin/python experiments/gate.py CANDIDATE.py [CONTROL.py] [seeds]

    .venv/bin/python experiments/gate.py agents/router_selector.py
    .venv/bin/python experiments/gate.py agents/router_selector.py agents/router_fam_yarn.py 12
"""

import os
import sys
import importlib.util

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from head_to_head import play  # noqa: E402  (path bootstrap must run first)
from rank_bases import pair_record  # noqa: E402
from opponent_strata import NEAR_TIE_BAND  # noqa: E402

DEFAULT_CONTROL = "agents/router_fam_yarn.py"
DEFAULT_SEEDS = 8

# See the module docstring for what "lineage" means and why the split is by
# whole file, never by seed. Edit these two dicts as new decoded/adopted
# routes become available - nothing else in this file needs to change.
TUNING_LINEAGES = {
    "route_v20": "agents/route_v20.py",
}
HOLDOUT_LINEAGES = {
    "yhay_tape": "agents/router_yhay.py",
    "moon_md_floor_deficit": "agents/route_moon_md_floor_deficit.py",
    "meta_lead3": "agents/meta_lead3.py",
}

# rank_bases.py's own self-control bar, repeated here as named constants
# (not reimplemented - same numbers as its inline `ok = ...` check) so this
# gate can fail loudly on the condition its own docstring calls for instead
# of printing "<-- CHECK" and moving on regardless.
SELF_CONTROL_SCORE_BAND = (0.35, 0.65)
SELF_CONTROL_MARGIN_ABS = 1500

# The PASS bar for a candidate. Named constants, not magic numbers:
#   PASS_SCORE_MARGIN    candidate's score, aggregated across the held-out
#                         lineages, must clear control's aggregated score by
#                         at least this much.
#   MAX_LINEAGE_REGRESSION  candidate's score on any ONE held-out lineage
#                         must not fall this far below control's score on
#                         that same lineage - one bad matchup should not be
#                         hidden by strength everywhere else.
PASS_SCORE_MARGIN = 0.05
MAX_LINEAGE_REGRESSION = 0.10


def load_module(path):
    name = "gate_target_" + os.path.splitext(os.path.basename(path))[0]
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def wrap_for_fallback_log(mod, log):
    """Wrap mod.agent so every post-opening decision it makes is recorded as
    a (fell_back_to_OPENING: bool) entry in `log`, via the module's OWN
    _which()/OPENING - not a reimplementation of the selection logic, just
    an observer. Falls through unchanged if the module doesn't expose them.
    Passing the wrapped callable straight into pair_record/play works because
    kaggle_environments accepts a live callable exactly like a file path."""
    which = getattr(mod, "_which", None)
    opening = getattr(mod, "OPENING", None)
    if which is None or opening is None:
        return mod.agent, False

    def inner(observation, configuration=None):
        try:
            step = int(observation.get("day", 0) or 0) * 24 + int(observation.get("hour", 0) or 0)
            shops = list((observation.get("town", {}) or {}).get("unlocked_shops", []) or [])
            if step >= 72 and shops:
                log.append(which(step, shops) == opening)
        except Exception:
            pass
        return mod.agent(observation, configuration)

    return inner, True


def check_self_control(control_path, seeds):
    ctrl_seeds = max(2, seeds // 2)
    w, l, t, m, mean = pair_record(control_path, control_path, ctrl_seeds)
    score = (w + 0.5 * t) / m
    lo, hi = SELF_CONTROL_SCORE_BAND
    ok = lo <= score <= hi and abs(mean) < SELF_CONTROL_MARGIN_ABS
    print("=== SELF-CONTROL SANITY CHECK (rank_bases.py's own bar) ===")
    print(f"  {os.path.basename(control_path)} vs itself, {ctrl_seeds} seeds x 2 seats")
    print(f"  score {score:6.1%}  W-L-T {w}-{l}-{t}  mean {mean:+9.0f}"
          f"  {'OK' if ok else 'FAIL'}")
    if not ok:
        print("\nFAIL: control does not tie itself within "
              f"{lo:.0%}-{hi:.0%} score / +-{SELF_CONTROL_MARGIN_ABS:.0f} margin.")
        print("The harness is lying (or the control file is broken) - fix that")
        print("before trusting anything else this gate reports. Aborting.")
        raise SystemExit(1)
    return score, mean


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        raise SystemExit(2)

    candidate_path = args[0]
    control_path = args[1] if len(args) > 1 else DEFAULT_CONTROL
    seeds = int(args[2]) if len(args) > 2 else DEFAULT_SEEDS

    for path in [candidate_path, control_path] + list(HOLDOUT_LINEAGES.values()):
        if not os.path.exists(path):
            print(f"missing file: {path}")
            raise SystemExit(2)
    overlap = set(TUNING_LINEAGES.values()) & set(HOLDOUT_LINEAGES.values())
    if overlap:
        print(f"TUNING_LINEAGES and HOLDOUT_LINEAGES overlap: {overlap} - fix the split.")
        raise SystemExit(2)

    print(f"gate: {candidate_path}  vs control  {control_path}")
    print(f"seeds 0-{seeds - 1}, both seats, {len(HOLDOUT_LINEAGES)} held-out lineages "
          f"({', '.join(HOLDOUT_LINEAGES)})\n")

    check_self_control(control_path, seeds)

    candidate_mod = load_module(candidate_path)
    fallback_log = []
    candidate_agent, has_fallback_signal = wrap_for_fallback_log(candidate_mod, fallback_log)

    # 1. headline: candidate vs control, direct
    print("\n=== CANDIDATE vs CONTROL (headline) ===")
    w, l, t, m, mean = pair_record(candidate_agent, control_path, seeds)
    headline_score = (w + 0.5 * t) / m
    print(f"  score {headline_score:6.1%}  W-L-T {w}-{l}-{t} (of {m})  mean {mean:+9.0f}"
          f"{'  (near-tie noise)' if abs(mean) < NEAR_TIE_BAND else ''}")

    # 2. per-lineage breakdown, held-out only
    print("\n=== PER-LINEAGE BREAKDOWN (held out, never tuned against) ===")
    print(f"  {'lineage':<24} {'candidate':>10} {'control':>10} {'delta':>8}   margin (cand / ctrl)")
    cand_rows = {}
    ctrl_rows = {}
    for lineage, path in HOLDOUT_LINEAGES.items():
        cw, cl, ct, cm, cmean = pair_record(candidate_agent, path, seeds)
        rw, rl, rt, rm, rmean = pair_record(control_path, path, seeds)
        cand_rows[lineage] = (cw, cl, ct, cm, cmean, (cw + 0.5 * ct) / cm)
        ctrl_rows[lineage] = (rw, rl, rt, rm, rmean, (rw + 0.5 * rt) / rm)
        cs, rs = cand_rows[lineage][5], ctrl_rows[lineage][5]
        flag = " (near-tie noise)" if abs(cmean) < NEAR_TIE_BAND or abs(rmean) < NEAR_TIE_BAND else ""
        print(f"  {lineage:<24} {cs:>9.1%} {rs:>9.1%} {cs - rs:>+7.1%}"
              f"   {cmean:+8.0f} / {rmean:+8.0f}{flag}")

    cand_total_wt = sum(cand_rows[l][0] + 0.5 * cand_rows[l][2] for l in HOLDOUT_LINEAGES)
    cand_total_m = sum(cand_rows[l][3] for l in HOLDOUT_LINEAGES)
    ctrl_total_wt = sum(ctrl_rows[l][0] + 0.5 * ctrl_rows[l][2] for l in HOLDOUT_LINEAGES)
    ctrl_total_m = sum(ctrl_rows[l][3] for l in HOLDOUT_LINEAGES)
    cand_agg = cand_total_wt / cand_total_m
    ctrl_agg = ctrl_total_wt / ctrl_total_m
    print(f"  {'AGGREGATE':<24} {cand_agg:>9.1%} {ctrl_agg:>9.1%} {cand_agg - ctrl_agg:>+7.1%}")

    # 3. worst-case lineage
    worst = min(HOLDOUT_LINEAGES, key=lambda l: cand_rows[l][5] - ctrl_rows[l][5])
    wdelta = cand_rows[worst][5] - ctrl_rows[worst][5]
    print("\n=== WORST-CASE LINEAGE ===")
    print(f"  {worst}: candidate {cand_rows[worst][5]:.1%} vs control {ctrl_rows[worst][5]:.1%} "
          f"(delta {wdelta:+.1%}, margin {cand_rows[worst][4]:+.0f})")

    # 4. fallback rate, only if the candidate exposes it
    print("\n=== FALLBACK RATE ===")
    if has_fallback_signal:
        if fallback_log:
            rate = sum(fallback_log) / len(fallback_log)
            print(f"  {sum(fallback_log)}/{len(fallback_log)} post-step-72 decisions "
                  f"fell back to OPENING ({rate:.1%}), across all games played above.")
        else:
            print("  candidate exposes _which()/OPENING but no post-step-72 decision "
                  "was logged (no shops ever unlocked by step 72 in these seeds).")
    else:
        print(f"  {os.path.basename(candidate_path)} does not expose _which()/OPENING - skipped.")

    # 5. mean bank margin, last, diagnostic only
    print("\n=== MEAN BANK MARGIN (diagnostic only - rating ignores margin) ===")
    print(f"  candidate vs control          {mean:+9.0f}")
    for lineage in HOLDOUT_LINEAGES:
        print(f"  candidate vs {lineage:<22} {cand_rows[lineage][4]:+9.0f}"
              f"   (control vs same: {ctrl_rows[lineage][4]:+9.0f})")

    # PASS/FAIL
    regressions = [l for l in HOLDOUT_LINEAGES
                   if cand_rows[l][5] < ctrl_rows[l][5] - MAX_LINEAGE_REGRESSION]
    cleared_margin = (cand_agg - ctrl_agg) >= PASS_SCORE_MARGIN
    passed = cleared_margin and not regressions

    print("\n=== GATE RESULT ===")
    print(f"  aggregate held-out score: candidate {cand_agg:.1%} vs control {ctrl_agg:.1%}"
          f"  (need >= +{PASS_SCORE_MARGIN:.0%}, got {cand_agg - ctrl_agg:+.1%})")
    if regressions:
        print(f"  regressed lineages (> {MAX_LINEAGE_REGRESSION:.0%} below control): "
              f"{', '.join(regressions)}")
    else:
        print(f"  no lineage regressed more than {MAX_LINEAGE_REGRESSION:.0%} below control")
    print(f"\n  {'PASS' if passed else 'FAIL'}")
    raise SystemExit(0 if passed else 1)


if __name__ == "__main__":
    main()
