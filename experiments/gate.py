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

SECOND MODE: `benchmark`, scored against destbreso's recorded-matchup
dataset (kaggle datasets download -d destbreso/kaggriculture-benchmark-
matchups -p data/benchmark --unzip) instead of against a live held-out
lineage. The three-lineage gate above stays the fast smoke check; this is
now the gate of record, because it plays a candidate at the exact seed and
seat of a REAL recorded ladder matchup against a scripted replay of that
matchup's real opponent, so a row is either a win we can bank on or a loss
against something an actual competitor did - not a mirror of ourselves or
a decoded lineage we've already looked at.

It runs an engine DIAGNOSTIC first (check_engine_self), always, but it does
not block anything: engine_fixture.json/exact_replay.json turned out to
reference action data outside this dataset entirely (an "actions_key" and a
results-only record respectively - see the ENGINE_CHECK_N comment below),
tracing back to a private research pool and a separate ~12GB Kaggle dataset
that isn't proportionate to fetch for 43 rows. So the diagnostic instead
reconstructs both sides' real tapes from matchups_all.parquet's own dual-
seat episodes and checks how well our engine reproduces
recorded_bank_opponent. Measured for real at n=40 across the full
opponent_rating range: 40/40 diverged, from single-digit deltas to six
figures on the SAME episode's other seat - not a construction bug (the
dataset's own cross-checks are exact every time) but evidence this corpus
mixes kaggriculture engine eras with no version stamp (CLAUDE.md already
documents one such patch with a same-seed 3x swing).

So recorded_bank_opponent is NOT the gate's ground truth. gate_benchmark
instead replays BOTH candidate and control against the SAME opponent tape
at the SAME seed/seat on OUR OWN engine (the one the ladder actually scores
on) and scores candidate against the control's own bank - the same paired-
difference logic paired_compare.py already relies on, so whichever era a
tape was recorded in cancels out exactly like seed noise does there. The
opponent tape is a valid sparring partner regardless of what engine
recorded it; only its absolute recorded bank isn't.

matchups_top.parquet needs exactly these columns (per row): `seed`,
`your_seat`, `opponent_actions` (a JSON-encoded or already-decoded list of
720 per-turn action dicts - the engine's normal agent-return shape),
`opponent_behaviour` (the 24-turn opening hash), `recorded_bank_opponent`
(present but unused as ground truth - see above).

A candidate is never filtered to rows its dataset "won" - the rows where
the recorded player LOST are the ones a candidate most needs to clear, so
they stay in.

Split discipline: opponent_behaviour hashes are partitioned into a gate
pool (scored here) and a disjoint train pool (TRAIN_HOLDOUT_FRACTION,
reserved for a future ranker), split by whole behaviour never by seed, so
a later ranker trained on the train pool can never have seen a behaviour
this gate already scored a candidate against. Nothing trains on it yet -
this just exposes the split so it's ready.

Usage:
    .venv/bin/python experiments/gate.py benchmark CANDIDATE.py [CONTROL.py] [PARQUET]

    .venv/bin/python experiments/gate.py benchmark agents/router_fam_yarn.py
    .venv/bin/python experiments/gate.py benchmark agents/router_selector.py
"""

import hashlib
import json
import math
import os
import random
import statistics
import sys
import importlib.util
from collections import defaultdict

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


# =============================================================================
# BENCHMARK MODE (`gate.py benchmark ...`) - see the module docstring's
# "SECOND MODE" section for the full picture. Everything below is additive:
# it does not change the three-lineage gate above, which stays available
# unchanged as the fast smoke check.
# =============================================================================

BENCHMARK_DATA_DIR = "data/benchmark"
ENGINE_FIXTURE_PATH = os.path.join(BENCHMARK_DATA_DIR, "engine_fixture.json")
EXACT_REPLAY_PATH = os.path.join(BENCHMARK_DATA_DIR, "exact_replay.json")
ALL_MATCHUPS_PARQUET = os.path.join(BENCHMARK_DATA_DIR, "matchups_all.parquet")
DEFAULT_PARQUET = os.path.join(BENCHMARK_DATA_DIR, "matchups_top.parquet")
BENCHMARK_DOWNLOAD_CMD = (
    "kaggle datasets download -d destbreso/kaggriculture-benchmark-matchups "
    "-p data/benchmark --unzip"
)

# STEP 1's cases are built from matchups_all.parquet itself, NOT from
# engine_fixture.json/exact_replay.json. Checked, not assumed: neither
# file embeds an action tape - engine_fixture.json's cases carry only an
# "actions_key" reference and exact_replay.json's rows carry only a result
# (recorded/replay bank, no actions at all). Both trace back to a private
# research pool and a separate ~12GB Kaggle dataset
# (georgymamarin/kaggriculture-episodes) that isn't part of this download
# and isn't proportionate to fetch just to check 43 rows. matchups_all.parquet
# often carries BOTH sides of one episode as separate rows (once from each
# side's own "your_seat"), so their full 720-turn tapes are already both
# sitting in this file - see _find_dual_seat_episodes.
ENGINE_CHECK_N = 40
ENGINE_CHECK_SAMPLE_SEED = 0
ENGINE_CHECK_MIN_DUAL_SEAT = 20
ENGINE_CHECK_TOLERANCE = 0

REQUIRED_MATCHUP_COLUMNS = (
    "seed", "your_seat", "opponent_actions", "opponent_behaviour",
    "recorded_bank_opponent",
)

# PASS bar for gate_benchmark. Named separately from PASS_SCORE_MARGIN /
# MAX_LINEAGE_REGRESSION above (not reusing those constants) because this
# gate measures against a different kind of ground truth - a recorded real
# bank, not a live control agent - and there's no reason to assume the same
# numeric bar transfers.
BENCHMARK_PASS_SCORE_MARGIN = 0.05
BENCHMARK_MAX_BEHAVIOUR_REGRESSION = 0.10

# SAMPLE AUDIT thresholds, declared here (not inline where they're checked)
# so they're visible before any number they gate is printed. PAIRED is the
# raw win/tie/loss rate; it's a binomial estimate over ROWS (each row is an
# independent played episode), so its power bar is a row count. OBJECTIVE
# is the mu/sigma/Phi model of the margin; it's only meaningful estimated
# per opponent_behaviour cluster, so its power bar is games *within one
# cluster* - not the distinct-behaviour count, which is a different axis
# (see the "effective count" note printed alongside it: 200 rows spread
# across a handful of behaviours still isn't 200 independent opponents).
PAIRED_MIN_ROWS = 200
OBJECTIVE_MIN_GAMES_PER_CLUSTER = 20

# Fraction of DISTINCT opponent_behaviour hashes permanently reserved for a
# future ranker's training pool. See split_behaviours() for why the split
# is by whole behaviour, never by row/seed, and why it's a hash rather than
# a sort-and-slice.
TRAIN_HOLDOUT_FRACTION = 0.20


def _require_files(paths):
    missing = [p for p in paths if not os.path.exists(p)]
    if missing:
        print("Benchmark dataset not found - stopping rather than fabricating rows.")
        for p in missing:
            print(f"  missing: {p}")
        print("\nRun this, then re-run the gate:")
        print(f"  {BENCHMARK_DOWNLOAD_CMD}")
        raise SystemExit(2)


def _load_json(path):
    with open(path) as f:
        return json.load(f)


def make_scripted_opponent(action_tape):
    """A live agent callable that ignores the observation entirely and
    replays a fixed, pre-recorded per-turn action tape. Indexes by the
    framework-supplied obs['step'] (0-indexed turn count; core.py sets
    observation.step = len(self.steps) at call time), clamped to the
    tape's last entry if the tape runs short. Pass it straight into
    head_to_head.play exactly like a real agent module or file path -
    kaggle_environments accepts a live callable anywhere it accepts a path
    (see wrap_for_fallback_log above for the same trick)."""
    def _scripted(observation, configuration=None):
        step = int((observation or {}).get("step", 0) or 0)
        idx = step if step < len(action_tape) else len(action_tape) - 1
        return action_tape[idx]
    return _scripted


def _parse_action_tape(raw):
    """opponent_actions as read out of the parquet/JSON: accept a JSON
    string (the usual parquet-safe encoding for a variable-shaped list of
    per-turn action dicts) or an already-decoded list/array."""
    if isinstance(raw, str):
        raw = json.loads(raw)
    if hasattr(raw, "tolist"):
        raw = raw.tolist()
    return list(raw)


def _find_dual_seat_episodes(parquet_path):
    """Episodes where BOTH players appear as `your_seat` in matchups_all.parquet
    - i.e. each side's own row records the OTHER side's full 720-turn tape,
    so between the two rows we already hold both complete action streams for
    that episode. Reads only the columns needed to find them; the much
    heavier opponent_actions column is read later, only for the sampled
    episodes (_load_dual_seat_rows). Returns [(episode_id, opponent_rating), ...]."""
    import pandas as pd
    df = pd.read_parquet(parquet_path, columns=["episode_id", "opponent_rating", "your_seat"])
    seats = df.groupby("episode_id")["your_seat"].agg(lambda s: frozenset(s.tolist()))
    dual = seats[seats == frozenset({0, 1})].index
    ratings = df[df["episode_id"].isin(dual)].groupby("episode_id")["opponent_rating"].first()
    return list(zip(ratings.index.tolist(), ratings.tolist()))


def _sample_dual_seat_episodes(both, n, sample_seed):
    """n episode ids, spread across opponent_rating: sort by rating, cut
    into n contiguous chunks spanning the full range, pick one per chunk
    with a fixed RNG so the sample is reproducible run to run."""
    if len(both) <= n:
        return [eid for eid, _ in both]
    ordered = sorted(both, key=lambda t: t[1])
    rng = random.Random(sample_seed)
    chunk = len(ordered) / n
    chosen = []
    for i in range(n):
        lo, hi = int(i * chunk), int((i + 1) * chunk)
        bucket = ordered[lo:hi] or [ordered[min(lo, len(ordered) - 1)]]
        chosen.append(rng.choice(bucket)[0])
    return chosen


def _load_dual_seat_rows(parquet_path, episode_ids):
    """Pull just the ~2*len(episode_ids) rows needed, with opponent_actions
    this time - a predicate pushdown filter, not a full-column scan of all
    45k rows' action strings."""
    import pandas as pd
    cols = ["episode_id", "seed", "your_seat", "opponent_actions",
            "recorded_bank_yours", "recorded_bank_opponent"]
    return pd.read_parquet(parquet_path, columns=cols,
                            filters=[("episode_id", "in", list(episode_ids))])


DIVERGENCE_SMALL_DELTA = 500  # dollars; see check_engine_self's docstring

def check_engine_self(parquet_path=ALL_MATCHUPS_PARQUET, n=ENGINE_CHECK_N,
                       sample_seed=ENGINE_CHECK_SAMPLE_SEED,
                       min_dual_seat=ENGINE_CHECK_MIN_DUAL_SEAT):
    """STEP 1, DIAGNOSTIC - not a hard gate on matching destbreso's recorded
    bank. It used to be: replay dual-seat episodes (both sides' real
    720-turn tapes, reconstructed from matchups_all.parquet's own rows - see
    the ENGINE_CHECK_N comment for why not engine_fixture.json/
    exact_replay.json) and require our engine reproduce recorded_bank_opponent
    to the dollar. Run for real at n=40, spread across the full
    opponent_rating range: 40/40 diverged, from single-digit-dollar deltas up
    to six figures on the same episode's OTHER seat. That is not a bug in
    this construction (the two seat-rows' recorded banks cross-check exactly
    against each other every time - the dataset is internally consistent)
    and not evidence our engine is broken - it is evidence this corpus mixes
    multiple kaggriculture engine eras with no version stamp to filter on
    (CLAUDE.md already documents one such patch, ~Aug 6 2026, changing Town
    Center demand and shop-unlock sampling, with a same-seed example
    swinging a bank 3x - consistent with the small-vs-large split this
    function still reports below).

    So recorded_bank_opponent is NOT used as gate_benchmark's ground truth -
    it can't be trusted absolutely across an unstamped multi-era corpus.
    What IS trustworthy: our own installed engine (1.32.7, the same one the
    ladder actually scores submissions on) is internally consistent with
    itself. gate_benchmark uses that instead - candidate and control both
    replayed on OUR engine against the SAME opponent tape at the SAME
    seed/seat, so whichever era the tape was recorded in cancels out of the
    paired difference exactly like seed noise does in paired_compare.py. The
    opponent tape is valid as a sparring partner regardless of what engine
    recorded it; only the absolute bank number it once produced is not.

    This function still runs first and still hard-stops on the two things
    that WOULD mean something is actually broken here, independent of which
    era anything was recorded in: the dataset's own two seat-rows
    disagreeing with each other (seed or cross-seat recorded-bank mismatch -
    a real data/construction bug, not engine drift), or an episode failing
    to finish DONE (checked per-row inside run_replays, not here)."""
    _require_files([parquet_path])
    print("=== STEP 1: ENGINE DIAGNOSTIC (not a hard gate - see docstring) ===")
    print(f"  sampling {os.path.basename(parquet_path)}'s own dual-seat episodes to see how")
    print("  well our installed engine reproduces destbreso's recorded_bank_opponent -")
    print("  informational only. gate_benchmark's actual ground truth is same-engine")
    print("  candidate-vs-control, which doesn't depend on this at all.")

    both = _find_dual_seat_episodes(parquet_path)
    print(f"  {len(both)} dual-seat episodes available")
    if len(both) < min_dual_seat:
        print(f"  only {len(both)} (< {min_dual_seat}) - skipping the diagnostic sample.\n")
        return {"checked": 0, "diverged": 0, "dual_seat_available": len(both)}

    chosen = _sample_dual_seat_episodes(both, n, sample_seed)
    pairs = _load_dual_seat_rows(parquet_path, chosen)
    checked = 0
    diverged = []
    for eid in chosen:
        pair = pairs[pairs.episode_id == eid]
        r0_rows, r1_rows = pair[pair.your_seat == 0], pair[pair.your_seat == 1]
        if len(r0_rows) != 1 or len(r1_rows) != 1:
            print(f"  SKIP episode {eid}: expected exactly one row per seat, "
                  f"found {len(r0_rows)}/{len(r1_rows)} - dataset inconsistency")
            continue
        r0, r1 = r0_rows.iloc[0], r1_rows.iloc[0]
        if r0.seed != r1.seed:
            print(f"  FAIL episode {eid}: seed mismatch between the two seat rows "
                  f"({r0.seed} vs {r1.seed}) - the dataset itself is inconsistent")
            raise SystemExit(1)
        if r0.recorded_bank_yours != r1.recorded_bank_opponent or \
           r1.recorded_bank_yours != r0.recorded_bank_opponent:
            print(f"  FAIL episode {eid}: recorded-bank cross-check failed between the "
                  "two seat rows - the dataset itself is inconsistent, not engine drift,")
            print("    and this function can't trust a case it can't even self-verify.")
            raise SystemExit(1)
        seat0_tape = _parse_action_tape(r1.opponent_actions)   # r1's opponent IS seat 0
        seat1_tape = _parse_action_tape(r0.opponent_actions)   # r0's opponent IS seat 1
        expect0, expect1 = r0.recorded_bank_yours, r1.recorded_bank_yours
        bank0, bank1 = play(make_scripted_opponent(seat0_tape),
                             make_scripted_opponent(seat1_tape), int(r0.seed))
        checked += 1
        d0, d1 = bank0 - expect0, bank1 - expect1
        if abs(d0) > ENGINE_CHECK_TOLERANCE or abs(d1) > ENGINE_CHECK_TOLERANCE:
            diverged.append((eid, int(r0.seed), d0, d1))

    small = [d for d in diverged if abs(d[2]) < DIVERGENCE_SMALL_DELTA and abs(d[3]) < DIVERGENCE_SMALL_DELTA]
    large = [d for d in diverged if d not in small]
    print(f"  {len(diverged)}/{checked} sampled episodes diverged from recorded_bank_opponent")
    if diverged:
        print(f"    {len(small)} within ${DIVERGENCE_SMALL_DELTA} on both seats "
              "(consistent with a same-era price/balance tweak)")
        print(f"    {len(large)} diverged by more (consistent with a different engine era)")
    print("  Not used as a gate: gate_benchmark scores candidate vs control on OUR OWN")
    print("  engine instead (see docstring) - proceeding.\n")
    return {"checked": checked, "diverged": len(diverged), "small": len(small) if diverged else 0,
            "large": len(large) if diverged else 0, "dual_seat_available": len(both)}


def split_behaviours(behaviours):
    """Partition opponent_behaviour hashes into (gate_pool, train_pool) -
    disjoint sets, split by WHOLE behaviour, never by seed or row, so a
    later ranker trained on train_pool can never have seen a behaviour this
    gate scored a candidate against (same reasoning as HOLDOUT_LINEAGES
    above, applied to behaviours instead of whole lineage files). The split
    is a deterministic hash of the behaviour string itself - not Python's
    randomized str hash, and not a sort-and-slice, which would reshuffle
    every assignment the moment a new behaviour is added to the dataset -
    so it's stable across runs, machines, and future dataset growth."""
    gate_pool, train_pool = set(), set()
    for b in set(behaviours):
        digest = hashlib.md5(str(b).encode()).hexdigest()
        frac = int(digest[:8], 16) / 0xFFFFFFFF
        (train_pool if frac < TRAIN_HOLDOUT_FRACTION else gate_pool).add(b)
    return gate_pool, train_pool


def _load_matchups(parquet_path):
    try:
        import pandas as pd
    except ImportError:
        print("pandas (+ pyarrow) is required for gate_benchmark: "
              "uv pip install --python .venv/bin/python pandas pyarrow")
        raise SystemExit(2)
    df = pd.read_parquet(parquet_path)
    missing = [c for c in REQUIRED_MATCHUP_COLUMNS if c not in df.columns]
    if missing:
        print(f"{parquet_path}: missing required column(s) {missing}")
        print(f"  columns present: {list(df.columns)}")
        raise SystemExit(2)
    return df


def _phi(z):
    """Standard normal CDF. math.erf only - no scipy/numpy anywhere in this
    tool, matching the constraint the agent side (router_selector.py) is
    held to."""
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def _win_prob(mu, sigma, n):
    """destbreso's OBJECTIVE measure: model the paired margin as
    Normal(mu, sigma) and report P(margin > 0) = Phi(mu/sigma) - the two
    are equal because Phi(-x) = 1 - Phi(x), so P(X>0) for X~N(mu,sigma^2)
    reduces to Phi(mu/sigma) directly. Degenerates without dividing by zero
    when sigma can't be estimated (n < 2) or came out exactly 0 (every
    margin in the sample was identical - a real possibility here, since the
    opponent side is a fully deterministic scripted replay): falls back to
    the sign of mu instead."""
    if n < 2 or not sigma:
        return 1.0 if mu > 0 else (0.0 if mu < 0 else 0.5)
    return _phi(mu / sigma)


def _play_checked(agent_a, agent_b, seed):
    """Like head_to_head.play, but also returns each side's terminal status,
    so run_replays' survives-a-season floor check has something real to
    check rather than assuming a bank number came from a completed game."""
    from kaggle_environments import make
    env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed}, debug=False)
    env.run([agent_a, agent_b])
    left, right = env.steps[-1]
    return left.reward, right.reward, left.status, right.status


def _replay_row(agent_callable, row):
    """Play `agent_callable` at (row.seed, row.your_seat) against a scripted
    replay of row.opponent_actions and return its own bank - not scored yet
    (see _score_against). The opponent tape is a sparring partner here, not
    a source of absolute ground truth (see check_engine_self)."""
    tape = _parse_action_tape(row.opponent_actions)
    scripted = make_scripted_opponent(tape)
    seat0, seat1 = ((agent_callable, scripted) if row.your_seat == 0
                     else (scripted, agent_callable))
    b0, b1, s0, s1 = _play_checked(seat0, seat1, row.seed)
    own_bank, own_status = (b0, s0) if row.your_seat == 0 else (b1, s1)
    if own_status != "DONE":
        print(f"FAIL: seed={row.seed} did not finish DONE (status={own_status}) - "
              "the survives-a-season floor check failed.")
        raise SystemExit(1)
    return own_bank


def run_replays(agent_callable, rows):
    """rows: an iterable of namedtuples from df.itertuples(). NOT filtered
    to rows the recorded player won - the rows it LOST are exactly the
    region a candidate most needs testing against, so they stay in. Returns
    one own-bank per row, aligned by position."""
    return [_replay_row(agent_callable, row) for row in rows]


def _score_against(own_banks, rows, ground_truths):
    """Tie-aware score of `own_banks` against `ground_truths` (both aligned
    to `rows` by position) - see gate_benchmark for what ground truth is
    (the control's own same-engine replay, permanently - not
    recorded_bank_opponent, per check_engine_self's docstring)."""
    out = []
    for bank, row, gt in zip(own_banks, rows, ground_truths):
        margin = bank - gt
        result = 1.0 if margin > 0 else (0.5 if margin == 0 else 0.0)
        out.append({"behaviour": row.opponent_behaviour, "own_bank": bank,
                     "recorded_bank_opponent": gt, "margin": margin, "result": result})
    return out


def _aggregate(results):
    """PAIRED (win/tie/loss -> score) and OBJECTIVE (mu/sigma -> win_prob)
    over the same margin list - one function so the two measures are always
    computed from identical rows, never from two slightly different filters."""
    matches = len(results)
    wins = sum(1 for r in results if r["result"] == 1.0)
    ties = sum(1 for r in results if r["result"] == 0.5)
    losses = matches - wins - ties
    score = (wins + 0.5 * ties) / matches if matches else float("nan")
    margins = [r["margin"] for r in results]
    mu = sum(margins) / matches if matches else float("nan")
    sigma = statistics.stdev(margins) if matches >= 2 else None
    win_prob = _win_prob(mu, sigma, matches) if matches else float("nan")
    return {"wins": wins, "losses": losses, "ties": ties, "matches": matches,
            "score": score, "mu": mu, "sigma": sigma, "win_prob": win_prob}


def _aggregate_by_behaviour(results):
    buckets = defaultdict(list)
    for r in results:
        buckets[r["behaviour"]].append(r)
    return {b: _aggregate(rs) for b, rs in buckets.items()}


def gate_benchmark(candidate_file, parquet=DEFAULT_PARQUET, control_file=DEFAULT_CONTROL):
    """STEPS 2-4. Score `candidate_file` against destbreso's recorded-
    matchup dataset - the gate of record (module docstring, "SECOND MODE").
    Runs the Step 1 engine diagnostic first (always - it's informational,
    not blocking; see check_engine_self). Ground truth here is PERMANENTLY
    the control's own same-engine replay of the same opponent tape at the
    same seed/seat, never destbreso's recorded_bank_opponent: that number
    isn't trustworthy across an unstamped multi-era corpus, but the paired
    difference between two agents replayed on OUR OWN engine (the one the
    ladder actually scores on) is exactly what paired_compare.py already
    relies on elsewhere in this repo, and the opponent tape is a valid
    sparring partner regardless of which era recorded it. Returns True on
    PASS, False on FAIL; raises SystemExit(2) if the dataset is missing or
    malformed, SystemExit(1) if an episode fails to finish DONE."""
    check_engine_self()

    _require_files([parquet])
    df = _load_matchups(parquet)

    all_behaviours = df["opponent_behaviour"].unique().tolist()
    gate_pool, train_pool = split_behaviours(all_behaviours)
    df_gate = df[df["opponent_behaviour"].isin(gate_pool)]

    print("=== STEP 4: SPLIT DISCIPLINE ===")
    print(f"  {len(all_behaviours)} distinct opponent_behaviour values in {os.path.basename(parquet)}")
    print(f"  gate pool:  {len(gate_pool):>3} behaviours, {len(df_gate):>4} rows  <- scored below")
    print(f"  train pool: {len(train_pool):>3} behaviours, {len(df) - len(df_gate):>4} rows"
          f"  (reserved for a future ranker; nothing trains on it yet)\n")

    print(f"=== STEP 2: BENCHMARK GATE  {os.path.basename(candidate_file)}"
          f"  vs control {os.path.basename(control_file)} ===")
    print("  ground truth: control's own same-engine replay of the same opponent tape")
    print("  (not destbreso's recorded bank - see Step 1 above).\n")

    candidate_agent = load_module(candidate_file).agent
    control_agent = load_module(control_file).agent

    rows = list(df_gate.itertuples())
    ground_truths = run_replays(control_agent, rows)
    cand_banks = run_replays(candidate_agent, rows)

    # ctrl_results is control scored against ITS OWN bank - trivially all
    # ties, margin 0. Kept and printed anyway as a visible self-consistency
    # check (same convention as rank_bases.py's/gate.py's other self-control
    # sanity lines), not because it carries information on its own.
    ctrl_results = _score_against(ground_truths, rows, ground_truths)
    cand_results = _score_against(cand_banks, rows, ground_truths)

    cand_agg = _aggregate(cand_results)
    ctrl_agg = _aggregate(ctrl_results)
    cand_by_b = _aggregate_by_behaviour(cand_results)
    ctrl_by_b = _aggregate_by_behaviour(ctrl_results)
    distinct_n = len(gate_pool)

    # SAMPLE AUDIT - declared and printed BEFORE any measure it gates, so an
    # underpowered result reads as "not enough evidence" the moment you see
    # it, never as a null finding sitting unlabelled next to a solid one.
    thin_clusters = [b for b in cand_by_b if cand_by_b[b]["matches"] < OBJECTIVE_MIN_GAMES_PER_CLUSTER]
    print("=== SAMPLE AUDIT (declared in advance) ===")
    print(f"  PAIRED (win rate) needs >= {PAIRED_MIN_ROWS} rows to trust.")
    print(f"  OBJECTIVE (mu/sigma/Phi) needs >= {OBJECTIVE_MIN_GAMES_PER_CLUSTER} games PER CLUSTER to trust.")
    print("  Effective count = distinct opponent_behaviour, not row count:")
    print(f"    headline PAIRED:    {len(rows)} rows"
          f"  [{'OK' if len(rows) >= PAIRED_MIN_ROWS else 'THIN'}]"
          f"  ({distinct_n} distinct behaviours behind them)")
    print(f"    headline OBJECTIVE: {len(rows)} games"
          f"  [{'OK' if len(rows) >= OBJECTIVE_MIN_GAMES_PER_CLUSTER else 'THIN'}]")
    print(f"    per-cluster OBJECTIVE: {len(thin_clusters)}/{distinct_n} clusters THIN"
          f" (< {OBJECTIVE_MIN_GAMES_PER_CLUSTER} games) - flagged individually below\n")

    print(f"=== STEP 2: BENCHMARK GATE  {os.path.basename(candidate_file)}"
          f"  vs control {os.path.basename(control_file)} ===")
    print("\n=== STEP 3.1: HEADLINE (ground truth = control's own same-engine replay) ===")
    print(f"  NOTE: {len(rows)} rows resolve to only {distinct_n} distinct opponent behaviours -")
    print(f"  read the headline against {distinct_n}, not {len(rows)}.")
    paired_thin = "" if len(rows) >= PAIRED_MIN_ROWS else " THIN"
    objective_thin = "" if len(rows) >= OBJECTIVE_MIN_GAMES_PER_CLUSTER else " THIN"
    for label, agg in (("candidate", cand_agg), ("control  ", ctrl_agg)):
        sigma_s = f"{agg['sigma']:.0f}" if agg["sigma"] is not None else "n/a"
        print(f"  {label}  PAIRED win rate {agg['score']:6.1%}{paired_thin}  "
              f"W-L-T {agg['wins']}-{agg['losses']}-{agg['ties']} (of {agg['matches']})   "
              f"OBJECTIVE Phi(mu/sigma) {agg['win_prob']:6.1%}{objective_thin}  "
              f"(mu {agg['mu']:+.0f}, sigma {sigma_s})")

    print(f"\n=== STEP 3.2: PER-BEHAVIOUR ({distinct_n} distinct opponent_behaviour values) ===")
    print(f"  {'behaviour':<18} {'n':>4} {'win% cand':>9} {'win% ctrl':>9} {'delta':>7}  "
          f"{'mu':>8} {'sigma':>8} {'Phi cand':>9} {'Phi ctrl':>9}  flag")
    for b in sorted(cand_by_b, key=lambda b: cand_by_b[b]["score"]):
        ca, ra = cand_by_b[b], ctrl_by_b[b]
        n = ca["matches"]
        sigma_s = f"{ca['sigma']:.0f}" if ca["sigma"] is not None else "n/a"
        flags = []
        if n < OBJECTIVE_MIN_GAMES_PER_CLUSTER:
            flags.append("THIN")
        if abs(ca["mu"]) < NEAR_TIE_BAND or abs(ra["mu"]) < NEAR_TIE_BAND:
            flags.append("near-tie noise")
        print(f"  {str(b)[:18]:<18} {n:>4} {ca['score']:>8.1%} {ra['score']:>9.1%} "
              f"{ca['score'] - ra['score']:>+6.1%}  {ca['mu']:>+8.0f} {sigma_s:>8} "
              f"{ca['win_prob']:>8.1%} {ra['win_prob']:>9.1%}  {', '.join(flags)}")

    worst = min(cand_by_b, key=lambda b: cand_by_b[b]["score"] - ctrl_by_b[b]["score"])
    wdelta = cand_by_b[worst]["score"] - ctrl_by_b[worst]["score"]
    print("\n=== STEP 3.3: WORST-CASE BEHAVIOUR ===")
    print(f"  {worst}: candidate {cand_by_b[worst]['score']:.1%} vs control {ctrl_by_b[worst]['score']:.1%}"
          f"  (delta {wdelta:+.1%}, candidate margin {cand_by_b[worst]['mu']:+.0f},"
          f" candidate Phi {cand_by_b[worst]['win_prob']:.1%})"
          f"{'  [THIN]' if worst in thin_clusters else ''}")

    # PASS/FAIL is unchanged from the three-lineage gate's rule: it still
    # runs on the PAIRED win-rate score. OBJECTIVE is reported alongside as
    # a second measure, not substituted in - see the module docstring.
    regressions = [b for b in cand_by_b
                   if cand_by_b[b]["score"] < ctrl_by_b[b]["score"] - BENCHMARK_MAX_BEHAVIOUR_REGRESSION]
    cleared_margin = (cand_agg["score"] - ctrl_agg["score"]) >= BENCHMARK_PASS_SCORE_MARGIN
    passed = cleared_margin and not regressions

    print("\n=== STEP 3.4: GATE RESULT ===")
    print(f"  headline: candidate {cand_agg['score']:.1%} vs control {ctrl_agg['score']:.1%}"
          f"  (need >= +{BENCHMARK_PASS_SCORE_MARGIN:.0%}, got {cand_agg['score'] - ctrl_agg['score']:+.1%})")
    if regressions:
        print(f"  regressed behaviours (> {BENCHMARK_MAX_BEHAVIOUR_REGRESSION:.0%} below control): "
              f"{', '.join(str(b) for b in regressions)}")
    else:
        print(f"  no behaviour regressed more than {BENCHMARK_MAX_BEHAVIOUR_REGRESSION:.0%} below control")
    if len(rows) < PAIRED_MIN_ROWS or thin_clusters:
        print("  NOTE: this verdict rests on THIN evidence somewhere above - "
              "read it as inconclusive, not as a clean PASS/FAIL.")
    print(f"\n  {'PASS' if passed else 'FAIL'}")
    return passed


def main_benchmark(args):
    if not args:
        print("usage: gate.py benchmark CANDIDATE.py [CONTROL.py] [PARQUET]")
        raise SystemExit(2)
    candidate_path = args[0]
    control_path = args[1] if len(args) > 1 else DEFAULT_CONTROL
    parquet_path = args[2] if len(args) > 2 else DEFAULT_PARQUET
    for p in (candidate_path, control_path):
        if not os.path.exists(p):
            print(f"missing file: {p}")
            raise SystemExit(2)
    passed = gate_benchmark(candidate_path, parquet=parquet_path, control_file=control_path)
    raise SystemExit(0 if passed else 1)


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        raise SystemExit(2)
    if args[0] == "benchmark":
        main_benchmark(args[1:])
        return

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
