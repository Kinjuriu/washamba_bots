"""Fit router_selector.py's first real branch from matchups.parquet.

Read AskUserQuestion history / conversation for the full design discussion
(not reproduced here); short version:

WHY matchups.parquet, NOT matchups_top.parquet. matchups_top's 421 rows give
at most ~6 games per opponent_behaviour - THIN against gate.py's own
OBJECTIVE_MIN_GAMES_PER_CLUSTER (20) bar, so fitting mu/sigma there is
fitting noise. matchups.parquet (6,288 rows, whole field) has 3,076 distinct
opponent_behaviour values, most with 1-2 rows - plenty of INDEPENDENT
opponents to pool across. matchups_top.parquet is the held-out set: never
read here, scored exactly once via gate_benchmark after this file's output
is hand-transcribed into router_selector.py.

WHY THE FIT IS GLOBAL, NOT PER-CLUSTER, DESPITE GROUPING BY opponent_behaviour.
_pick_continuation's routing key is the shop-unlock signature ("YARN_STORE",
"PET_CAFE__YARN_STORE", ...) - the only thing the live agent can actually
observe (obs["town"]["unlocked_shops"]). matchups.parquet carries no shop-
unlock info at all, and destbreso's opponent_behaviour hash (of the
opponent's raw actions) isn't computable live - you never see the other
player's issued actions in a real episode. So this fit cannot condition on
"which shop-key are we in"; it can only ask, pooling across many distinct
real opponents, "against the general field, is fam behind, and does some
already-designated y-tape clearly beat fam". opponent_behaviour is used as
the POOLING unit (one sampled row per distinct behaviour, so one common
opening can't dominate the statistics) - see sample_behaviours() - not as a
runtime lookup key. A tape that passes gets turned on for EVERY existing
CONTINUATIONS key that already designates it (per FIRST_ROUTES/SECOND_ROUTES);
a tape that fails is left unrouted everywhere.

ONLY 4 TAPES ARE REACHABLE AT ALL. router_selector.CONTINUATIONS only has 16
keys (all YARN_STORE-involving, since YHAY_FIRST=YHAY_ANY=['YARN_STORE']),
and their candidates[0] values are only ever y1 (9 keys), y2 (5), y8 (1), y9
(1) - checked, not assumed. The other six embedded tapes (y0, y3-y7) are
never a candidate[0] for on any current key, so fitting them would be
answering a question _pick_continuation can never ask. Only y1/y2/y8/y9 are
fit here.

METHOD, per sampled row (one distinct opponent_behaviour each):
  1. Replay fam (agents/router_fam_yarn.py) against the recorded opponent
     tape at that row's (seed, your_seat) on OUR OWN engine -> (fam_bank,
     opp_bank). Margin = fam_bank - opp_bank. Pooled mu/sigma/Phi over all
     sampled rows answers "is fam behind against the general field" -
     engine-consistent because both banks come from the SAME single replay,
     never destbreso's recorded_bank_opponent (see gate.py's Step 1 for why
     that number isn't trustworthy across this corpus's mixed engine eras).
  2. Only if fam is behind overall (pooled mu < 0): for each of the 4
     reachable tapes, replay that tape (not fam) against the SAME opponent
     tape at the SAME (seed, seat) -> tape_bank. Margin = tape_bank -
     fam_bank, paired row-by-row against fam's own replay - the standard
     paired-difference design this repo already uses elsewhere
     (paired_compare.py), just with the opponent tape as the common-random-
     numbers device instead of a shared seed on a live opponent.
  3. A tape PASSES iff its pooled Phi(mu/sigma) clears a coin flip by
     gate.py's own BENCHMARK_PASS_SCORE_MARGIN (0.5 + 0.05 = 0.55) AND the
     sample size clears gate.py's own OBJECTIVE_MIN_GAMES_PER_CLUSTER (20)
     distinct behaviours - trivially satisfied at the chosen sample size,
     checked anyway rather than assumed.

OUTPUT: printed fit-split summary (fam's pooled numbers, each tape's pooled
numbers, pass/fail) and the literal SCORE_TABLE entries for tapes that
passed, meant to be hand-transcribed into router_selector.py - this script
does not edit the agent file itself, so a fit run can never silently change
what ships without a diff to review.

Usage:
    .venv/bin/python experiments/fit_branch.py [N]
"""

import importlib.util
import os
import random
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gate import play, make_scripted_opponent, _parse_action_tape, _phi  # noqa: E402
from gate import BENCHMARK_PASS_SCORE_MARGIN, OBJECTIVE_MIN_GAMES_PER_CLUSTER  # noqa: E402

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIT_PARQUET = os.path.join(REPO_ROOT, "data", "benchmark", "matchups.parquet")
FAM_PATH = os.path.join(REPO_ROOT, "agents", "router_fam_yarn.py")
FIT_SAMPLE_N_DEFAULT = 150
FIT_SAMPLE_SEED = 0


def load_agent(path):
    spec = importlib.util.spec_from_file_location("fit_" + os.path.splitext(os.path.basename(path))[0], path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.agent


def sample_behaviours(df, n, seed):
    """One row per distinct opponent_behaviour (so one common opening can't
    dominate the pooled statistics), spread across opponent_rating: sort by
    rating, cut into n contiguous chunks spanning the full range, pick one
    per chunk with a fixed RNG - same construction as
    gate.py's _sample_dual_seat_episodes, for the same reason."""
    first_per_b = (df.sort_values("opponent_rating")
                     .drop_duplicates("opponent_behaviour", keep="first")
                     .reset_index(drop=True))
    if len(first_per_b) <= n:
        return first_per_b
    rng = random.Random(seed)
    chunk = len(first_per_b) / n
    idxs = []
    for i in range(n):
        lo, hi = int(i * chunk), int((i + 1) * chunk)
        hi = max(hi, lo + 1)
        idxs.append(rng.randrange(lo, min(hi, len(first_per_b))))
    return first_per_b.iloc[idxs]


def replay_own_bank(agent_fn, row):
    """(own_bank, opponent_bank) for `agent_fn` at (row.seed, row.your_seat)
    against a scripted replay of row.opponent_actions, on OUR engine."""
    tape = _parse_action_tape(row.opponent_actions)
    scripted = make_scripted_opponent(tape)
    if row.your_seat == 0:
        own, opp = play(agent_fn, scripted, int(row.seed))
    else:
        opp, own = play(scripted, agent_fn, int(row.seed))
    return own, opp


def _stats(margins):
    mu = statistics.mean(margins)
    sigma = statistics.stdev(margins) if len(margins) > 1 else None
    if sigma is None or sigma == 0:
        phi = 1.0 if mu > 0 else (0.0 if mu < 0 else 0.5)
    else:
        phi = _phi(mu / sigma)
    return mu, sigma, phi


def main():
    import pandas as pd
    n = int(sys.argv[1]) if len(sys.argv) > 1 else FIT_SAMPLE_N_DEFAULT

    df = pd.read_parquet(FIT_PARQUET, columns=["seed", "your_seat", "opponent_actions",
                                                "opponent_behaviour", "opponent_rating"])
    print(f"matchups.parquet: {len(df)} rows, {df['opponent_behaviour'].nunique()} distinct behaviours")
    sample = sample_behaviours(df, n, FIT_SAMPLE_SEED)
    rows = list(sample.itertuples())
    print(f"fit sample: {len(rows)} rows, each a distinct opponent_behaviour, "
          f"spread across opponent_rating (fixed seed={FIT_SAMPLE_SEED})\n")

    fam_agent = load_agent(FAM_PATH)

    print("=== PASS 1: fam vs the general field (on OUR engine) ===")
    fam_banks, opp_banks = [], []
    for i, row in enumerate(rows):
        fam_bank, opp_bank = replay_own_bank(fam_agent, row)
        fam_banks.append(fam_bank)
        opp_banks.append(opp_bank)
        if (i + 1) % 10 == 0 or i + 1 == len(rows):
            print(f"  [{i + 1}/{len(rows)}] last: fam={fam_bank:.0f} opp={opp_bank:.0f}", flush=True)

    fam_margins = [f - o for f, o in zip(fam_banks, opp_banks)]
    fam_mu, fam_sigma, fam_phi = _stats(fam_margins)
    sigma_s = f"{fam_sigma:.0f}" if fam_sigma is not None else "n/a"
    print(f"\nFAM vs general field: mu={fam_mu:+.0f} sigma={sigma_s} Phi={fam_phi:.1%} "
          f"(n={len(rows)} distinct behaviours)")

    if fam_mu >= 0:
        print("\nfam is NOT behind on average against this fit sample (mu >= 0) - "
              "no branch qualifies under the accepted design ('a shop-key where fam "
              "is already ahead does not get rerouted'). Stopping - no SCORE_TABLE "
              "entries to add.")
        return

    print("\nfam IS behind on average (mu < 0) - testing the 4 reachable tapes...\n")

    sys.path.insert(0, os.path.join(REPO_ROOT, "agents"))
    import router_selector as rs
    tape_keys = {}
    for key, cont in rs.CONTINUATIONS.items():
        tape_keys.setdefault(cont["candidates"][0], []).append(key)
    print(f"tapes reachable via CONTINUATIONS: "
          f"{ {t: len(ks) for t, ks in sorted(tape_keys.items())} }\n")

    tape_agent_cache = {}

    def get_tape_agent(tape_name):
        if tape_name not in tape_agent_cache:
            tape_agent_cache[tape_name] = make_scripted_opponent(rs._TAPES[tape_name])
        return tape_agent_cache[tape_name]

    print("=== PASS 2: each reachable tape vs fam, same rows/seeds/seats ===")
    results = {}
    for tape in sorted(tape_keys):
        print(f"\n-- {tape} ({len(tape_keys[tape])} existing keys: {tape_keys[tape]}) --")
        tape_banks = []
        for i, row in enumerate(rows):
            tape_bank, _ = replay_own_bank(get_tape_agent(tape), row)
            tape_banks.append(tape_bank)
            if (i + 1) % 25 == 0 or i + 1 == len(rows):
                print(f"  [{i + 1}/{len(rows)}]", flush=True)
        margins = [t - f for t, f in zip(tape_banks, fam_banks)]
        mu, sigma, phi = _stats(margins)
        passed = (phi >= 0.5 + BENCHMARK_PASS_SCORE_MARGIN) and (len(rows) >= OBJECTIVE_MIN_GAMES_PER_CLUSTER)
        sigma_s = f"{sigma:.0f}" if sigma is not None else "n/a"
        print(f"  {tape} vs fam: mu={mu:+.0f} sigma={sigma_s} Phi={phi:.1%} "
              f"(n={len(rows)}, need Phi>={0.5 + BENCHMARK_PASS_SCORE_MARGIN:.0%} "
              f"and n>={OBJECTIVE_MIN_GAMES_PER_CLUSTER})  -> {'PASS' if passed else 'FAIL'}")
        results[tape] = {"mu": mu, "sigma": sigma, "phi": phi, "passed": passed,
                          "keys": tape_keys[tape]}

    print("\n\n=== FIT-SPLIT SUMMARY ===")
    print(f"fam vs general field: mu={fam_mu:+.0f} sigma={sigma_s} Phi={fam_phi:.1%} "
          f"(n={len(rows)} distinct behaviours)")
    for tape, r in sorted(results.items()):
        sigma_s2 = f"{r['sigma']:.0f}" if r["sigma"] is not None else "n/a"
        print(f"  {tape}: mu={r['mu']:+.0f} sigma={sigma_s2} Phi={r['phi']:.1%} "
              f"n={len(rows)} distinct behaviours -> {'PASS' if r['passed'] else 'FAIL'} "
              f"(keys: {r['keys']})")

    passing = {t: r for t, r in results.items() if r["passed"]}
    print("\n=== SCORE_TABLE entries to transcribe into router_selector.py ===")
    if not passing:
        print("  none - no tape cleared the bar. router_selector.py stays behaviour-neutral.")
    else:
        for tape, r in sorted(passing.items()):
            for key in r["keys"]:
                print(f"    SCORE_TABLE[({tape!r}, {key!r})] = ({r['mu']:.1f}, {r['sigma']:.1f})")


if __name__ == "__main__":
    main()
