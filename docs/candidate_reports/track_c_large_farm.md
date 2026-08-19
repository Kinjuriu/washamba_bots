# Issue #21, Track C — replay analysis → executable large-farm opponent

Branch: `track-c/large-farm-reference-opponent` (off `origin/main` @ `33a96d9`).
`main.py` is untouched throughout - grep/diff confirms zero changes.

## TL;DR

- **`experiments/bigfarm_opponent.py` (already in the repo, unmodified) is
  the credible reference opponent** - self-play mean **$59,018** (stdev
  6,329), 6/6 seeds, zero collapses, 75 tiles, 4 animals, crew present every
  seed. Use it today.
- **Pushing animal count from 4 to 8-9 (the replay-observed range) collapses
  the agent economically in self-play, every time, regardless of which of
  four escalating fixes was applied.** Best result reached: $7,806 mean (a
  real 18x improvement over the naive attempt, but nowhere near
  bigfarm_opponent.py's own $59,018, let alone the $90-100k target).
- The mechanism is now precisely isolated (not guessed): animal buying is an
  **unpaced, opportunistic, per-turn purchase** that competes for cash with
  whatever else needs it at that moment. At 4 animals it empties its
  "budget" quickly and stops, leaving room for land/crew. At 8, a slot stays
  open roughly twice as long, and the purchase re-fires **right on top of**
  the day-11 second land payment - which is the exact "day-11 poverty trap"
  named in the issue brief, now confirmed structurally rather than assumed.
- Four one-factor fixes were tried and none closed the gap. This is now a
  genuinely open problem, independently corroborated by
  `experiments/candidates` from an earlier session (deleted, uncommitted,
  recovered only as `.pyc` filenames - see "prior art" below) and by the
  already-merged `experiment/animal-cliff` branch, which hit the same
  animal-count-5 cliff via a **different** mechanism (pasture
  serialization, not cash timing). Two independent causes, same wall.

## Files

| File | Purpose |
|---|---|
| `experiments/bigfarm_opponent.py` | **The reference opponent to use now.** Pre-existing, unmodified. |
| `experiments/selfplay_agent.py` | New. Generic `agent_path vs itself` harness with structural checks (tiles/animals/hands at episode end), parametrized so a candidate under `experiments/candidates/` can be self-play tested without editing the hardcoded `selfplay_bench.py`. |
| `experiments/candidates/large_farm_opponent_v0.py` | Exp 0: `MAX_ANIMALS` 4→8, nothing else. Isolates the collapse to animal count alone. |
| `experiments/candidates/large_farm_opponent_v1.py` | Exp 1: v0 + `MIN_CASH_RESERVE_FOR_ANIMAL_BUYING=450` (the seed-buying fix pattern, ported from the unmerged `phase3` branch). |
| `experiments/candidates/large_farm_opponent_v2.py` | Exp 2: land-gated animal cap (4 until both land quadrants bought, then 8) + the v1 reserve floor, via copied+modified functions. |
| `experiments/candidates/large_farm_opponent_v3.py` | Exp 3: same land gate as v2, but as a **pure constant override** (no copied function bodies) - isolates the gating idea from the reserve-floor addition. **Best result: $7,806 mean.** |
| `experiments/candidates/large_farm_opponent_v4.py` | Exp 4: v3 + a $2,000 cash buffer before the ramp fires (not just "land bought"). No improvement over v3 - identical numbers. |
| `docs/candidate_reports/track_c_large_farm.md` | This file. |

All five candidates follow `bigfarm_opponent.py`'s own established pattern:
`import main as base`, override tuning constants/functions, never rewrite
the unit-action ladder. None of them touch `main.py`.

## Prior art note

The issue brief describes a "previous replay-shape opponent" that failed at
self-play bank $589-$4,604 with animal/crew collapse. That code is **not in
git history** (checked: `git log --all` on `experiments/candidates/` and
`experiments/replay_shape/` show nothing matching) - it existed only as
local, uncommitted files on this machine in a prior session, evidenced by
orphaned `.pyc` bytecode (`replay_shape_agent.cpython-313.pyc`,
`replay_shape_instrumentation.cpython-313.pyc`,
`replay_shape_matchup.cpython-313.pyc`) whose `.py` sources are gone. The
number range in the brief ($589-$4,604) is close to but not identical to
what Exp 0/1 reproduced here ($390-$450) - consistent with a similar but not
identical mechanism, which is exactly what an independent re-derivation
should look like if the underlying problem is real rather than one script's
bug.

## Experiment log

### Exp 0 - isolate the collapse to `MAX_ANIMALS` alone

**Hypothesis:** if `bigfarm_opponent.py` (75 tiles, 15-crew cap, day-10
selling, `MAX_ANIMALS=4`) is already healthy, changing exactly one constant
- `MAX_ANIMALS` 4→8 - should show whether animal count by itself causes the
brief's described collapse, or whether it needs land/crew scaling too.

**Change:** `base.MAX_ANIMALS = 8`, nothing else, in
`large_farm_opponent_v0.py`.

**Why it should isolate the mechanism:** every other constant
(`MAX_HANDS_PER_DAY=15`, `LIQUIDATION_START_DAY=10`, land timing, sell
thresholds) stays at bigfarm_opponent.py's own already-measured-healthy
values.

**Seeds:** 0-5, self-play (agent vs itself), `experiments/selfplay_agent.py`.

**Self-play result:** mean **$418**, stdev $38, every seed $341-$441 -
**below the $3,000 starting stake on all 6 seeds.**

**Structural checks:** `tiles=25` (land never bought), `animals=0`,
`hands=0`, at episode end, every seed. Not a gradual degradation - a total
failure to execute the rest of the strategy at all.

**Worst seed:** all six are essentially tied at total failure; seed 0 is
nominally worst at $341 (min of the pair).

**Robust:** yes - reproduced across two separate runs (see "tooling bug"
below) with identical per-seed numbers both times, and again in the
isolated-constant retest under Exp 4's writeup.

**Verdict: REJECTED as-is, but this is the most informative result in the
whole log** - it precisely pins the failure on animal count, not on land or
crew, which the brief's diagnosis had bundled together.

---

### Exp 1 - cash-reserve floor on animal purchases

**Hypothesis:** `choose_animal_to_build`/`decide_animal_market_actions` gate
a purchase only on `cost <= money * ANIMAL_SPEND_CAP_FRACTION` (0.5) - a
fraction of *current* cash with no floor at the fraction's own boundary.
This is the exact bug already fixed for seed buying
(`MIN_CASH_RESERVE_FOR_SEED_BUYING`, +2,271/10-12 per `CLAUDE.md`) and for
animal buying on the unmerged `refactor/phase3-land-and-second-animal`
branch (+9,004/10-12, in a bundle). `main.py` on `origin/main` has **no**
`MIN_CASH_RESERVE_FOR_ANIMAL_BUYING` at all (confirmed by grep) - it was
never ported from phase3.

**Change:** ported *only* that one fix (not phase3's other changes) into
`large_farm_opponent_v1.py` by monkeypatching
`choose_animal_to_build`/`decide_animal_market_actions` with copies adding
`money - cost >= 450` (phase3's own reserve value: above COW's $400, at/below
SHEEP's $500).

**Seeds:** 0-5, self-play.

**Self-play result:** mean **$431**, stdev $8 - statistically indistinguishable
from Exp 0's $418. **No improvement.**

**Structural checks:** identical to Exp 0 - `tiles=25`, `animals=0`,
`hands=0`.

**Robust:** yes, same pattern every seed.

**Verdict: REJECTED.** The fix that worked for seed buying and (in a bundle)
for phase3's animal buying does nothing here in isolation. This was the
first sign the mechanism is not simply "no floor" - see Exp 3's precise
diagnosis.

---

### Exp 2 / Exp 3 - land-gated animal cap

**Hypothesis:** `land_order()` needs a $1,450 lump sum
(`LAND_PRICES[0]=1000 + LAND_CASH_RESERVE=450`) before it fires at all, while
animal buying fires opportunistically the instant cash crosses roughly
$450-500 (2x an animal's cost, per `ANIMAL_SPEND_CAP_FRACTION=0.5`). At
`MAX_ANIMALS=8` a purchase slot stays open roughly twice as long as at 4, so
cash gets siphoned into another animal before it can ever accumulate to
land's much bigger threshold - land never gets bought, hiring demand (driven
by tile count) never grows, and the farm is stuck at 25 tiles forever. Gate
the animal count itself: hold at 4 (bigfarm_opponent.py's own proven number)
until both land quadrants are bought, then allow 8.

**Change, Exp 2** (`large_farm_opponent_v2.py`): land-gated cap **combined
with** Exp 1's reserve floor, via copied+modified functions.

**Change, Exp 3** (`large_farm_opponent_v3.py`): the **same gate, alone** -
just `base.MAX_ANIMALS` set dynamically (4 or 8) each turn based on
`len(farm["unlocked_quadrants"])`, no copied function bodies, no reserve
floor. Isolates the gating idea from Exp 1's addition.

**Seeds:** 0-5, self-play, both.

**Self-play result, Exp 2:** mean **$7,779**, stdev $346, range
$7,452-$8,245.
**Self-play result, Exp 3:** mean **$7,806**, stdev $321, range
$7,500-$8,245. **Nearly identical to Exp 2** - confirms the reserve floor
was never the active ingredient; the land gate is.

**Structural checks:** `tiles=75` in both - **land buying now works**,
confirming the diagnosis's first half. But `animals=0`, `hands=0` at episode
end in both - still no crew, still no animals, despite `MAX_ANIMALS`
correctly sitting at 4 (matching the known-good baseline) for the entire
first 11 days. Verified with a per-turn debug trace
(`base.MAX_ANIMALS` printed every ~100 calls): it reads exactly 4 through
day 8, flips to 8 at day 12 - one turn after the real second land purchase
- precisely on schedule, no bug in the gate logic itself.

**A control test matters here:** a wrapper that does nothing but call
`bigfarm_opponent.bigfarm_opponent(obs)` unchanged reproduces
bigfarm_opponent.py's own numbers byte-for-byte ($59,018 mean, animals=4).
A wrapper that hardcodes `base.MAX_ANIMALS = 4` every turn (functionally
identical to the default, but via the same per-turn-reassignment code path
as Exp 3) also reproduces ~$63k. Only the **transition** from 4 to 8
mid-game collapses the result - even though the first 11 days are, by
construction, identical to the working case.

**Worst seed:** seed 4, $7,423 (Exp 3).

**Robust:** yes, reproduced across two independent implementations (Exp 2's
copied-function approach and Exp 3's pure-constant approach) landing within
$30 of each other.

**Verdict: Exp 2 REJECTED** (reserve floor adds nothing, more code for zero
gain). **Exp 3 REJECTED** but retained as the clearest diagnostic result:
land buying is fixed, but the animal-count bump landing at the exact moment
of the second land payment (day 11) triggers a **second** cash crisis that
the crew/hiring machinery never recovers from for the remaining ~18 days -
this is a mid-game collapse, not a start-of-game one, and it erases what
should have been an $59k-shaped trajectory. This is the issue brief's
"day-11 poverty trap" mechanism, now shown structurally rather than assumed.

---

### Exp 4 - delay the ramp with a cash buffer, not just a land-bought flag

**Hypothesis:** if the ramp trigger fires the instant land is fully bought,
it lands on top of the payment with no recovery time. Require a cash
cushion (`ANIMAL_RAMP_CASH_BUFFER=2000`) on top of "land bought" before
allowing `MAX_ANIMALS` to rise, giving the post-land crew/income time to
recover first.

**Change:** `large_farm_opponent_v4.py` - same gate as Exp 3, plus
`farm["money"] >= 2000` required before the ramp fires.

**Seeds:** 0-5, self-play.

**Self-play result:** mean **$7,806**, stdev $321 - **identical to Exp 3 to
the dollar on every seed.** The buffer never changed the outcome at all.

**Structural checks:** same as Exp 3.

**Robust:** yes (exact match across all 6 seeds is itself the signal - the
buffer condition and the land-bought condition are resolving at
indistinguishable times in practice, or the collapse doesn't depend on
*when* the ramp fires within the range this buffer could have delayed it to).

**Verdict: REJECTED, no improvement over Exp 3.** This is useful negative
information: a one-time cash gate on *when* the ramp starts is not the
right shape of fix. The remaining hypothesis, untested in this session for
time: **pace the ramp itself** - one additional animal every N days with a
fresh affordability+reserve check each time, rather than raising the cap in
one step and letting the existing opportunistic buy-loop run freely against
it. That is the next experiment, not yet built.

## Correction found during the final sanity check: `bigfarm_opponent.py` is now redundant with `main.py`

Ran `head_to_head.py experiments/bigfarm_opponent.py main.py` (6 seeds) as a
close-out sanity check, expecting `bigfarm_opponent.py` to win clearly per
its own docstring (+7,181 mean, 6/6, measured against an older `main.py`).
Instead: **mean bank difference +0, 6/12 wins - statistically a coin flip.**

Checked why: `main.py vs main.py` self-play (`selfplay_agent.py main.py 3`)
reproduces `bigfarm_opponent.py vs itself`'s numbers **to the exact dollar**
on every seed (62887/68859/56151/53400/68336/68204). `bigfarm_opponent.py`
predates the `BUY_LAND` merge into `main.py` (2026-08-18) - it was written
specifically to be a scaled-up sparring partner because `main.py` at the
time was still a 25-tile, single-animal agent. Every constant it overrides
(`LIQUIDATION_START_DAY=10`, `MAX_HANDS_PER_DAY=15`, `MAX_ANIMALS=4`) is now
**already `main.py`'s own shipped default** - the override is a no-op, and
its custom `land_order()` duplicates logic `main.py`'s own
`decide_land_orders` already does natively. The wrapper adds nothing
anymore; it just calls `main.py` with extra steps.

**This does not change any conclusion above** - every experiment here (Exp
0-4) built on `bigfarm_opponent.py`, so they were really testing "current
`main.py`'s own behaviour, with `MAX_ANIMALS` pushed past its shipped
default of 4." That is exactly the right experiment for this issue. What
it does change: the framing of `bigfarm_opponent.py` as *the* reference
opponent going forward. Recommend either retiring it or updating its
docstring/overrides to something that's actually still ahead of `main.py`
(e.g. push toward `MAX_HANDS_PER_DAY` beyond 15, or a genuinely different
sell cadence) - as shipped today it is not exercising anything `main.py`
doesn't already do on its own, which anyone reusing it for A/B work should
know before trusting its numbers.

## Experiment 5 (new session) - paced animal ramp: EXPERIMENT ABORTED, root cause found, not a pacing result

**File:** `experiments/candidates/large_farm_opponent_v5_paced_ramp.py`. **Test
suite:** `tests/test_large_farm_opponent_v5_paced_ramp.py` (17 tests, all
pass; full repo suite 148/148 pass). **Diagnostics:**
`experiments/track_c_exp5_diagnostics.py`.

**Hypothesis tested:** hold `MAX_ANIMALS` at main.py's own proven default
of 4 until land is fully bought (read from `unlocked_quadrants`, no new
land logic), then open one additional slot at a time (5, 6, 7, 8), each
gated on its own escalating cash reserve (`$500 * (k-4)`) rather than one
global gate - directly addressing Exp 3/4's finding (a single-step jump to
8 collapses the agent) and animal-cliff's stranding bug (build and buy must
agree on the same cap every turn, which this implementation guarantees by
construction - verified with a dedicated regression test,
`TestBuildAndBuySagreeOnTheSameCap`).

**Unit-level result:** all 17 new tests pass - `effective_animal_cap`,
`_choose_animal_to_build`, and `_decide_animal_market_actions` behave
exactly as designed in isolation.

**Self-play result (6 seeds): mean $7,806 - identical to Exp 3/4.** Full
day-by-day trace (`track_c_exp5_diagnostics.py`) shows why: on **every one
of 6 seeds**, the moment the ramp opens past 4 animals (day 12-13, right
after the second land quadrant), the agent's bank goes **bit-identically
frozen** for the remaining ~17 days - `PASS`/no hands/no market orders,
every turn, no exceptions - while 4-5 pastures sit permanently unfilled and
31+ tiles sit as un-dug weeds.

**Root cause, confirmed by direct reproduction (not inferred):**

```
>>> base.decide_market_actions(farm, private, market_state, day=13, reserved_wheat=0)
KeyError: 'SHEEP'
  File "main.py", line 1730, in decide_market_actions
  File "main.py", line 419, in recommend_sell_quantity
  File "main.py", line 200, in market_price
    p = (params or MARKET_PARAMS)[item]
```

`main.py`'s `decide_market_actions` iterates the shed's contents and calls
`market_price()` on every key, including a **live animal token** (a bought
BUY_ANIMAL sitting in the shed, waiting to be carried to a pasture) -
`"SHEEP"`/`"COW"` are not in `MARKET_PARAMS` (only their *products*, WOOL
and MILK, are tradeable), so this is a genuine `KeyError` in unmodified
`main.py`. It is caught by `nikaangukia_meroni`'s own top-level
`except Exception: return {"farmer": ["PASS"], "hands": [], "market": []}`
(main.py:2222-2226, a deliberate "never forfeit the match" safety net) -
which is why no traceback ever surfaces and the episode reports `DONE`, not
`ERROR`. The bug isn't the fallback - the fallback is good engineering.
**The problem is that the fallback discards the PICKUP action too, so the
stuck shed item is never resolved, and the identical KeyError recurs every
single turn for the rest of the season - a one-time bug becomes a permanent
freeze.** Reproduced identically on seed 0 (`shed={"SHEEP": 1, ...}`) and
seed 1 (`shed={"SHEEP": 1, ...}`, same `KeyError('SHEEP')`).

**This is not new** - it's the exact defect `refactor/phase3-land-and-second-animal`
already found and fixed (commit message: *"a live animal sitting in the
shed... was a valid shed key but not a market product... crashed with a
silent KeyError"*), guarded there with `if product not in MARKET_PARAMS:
continue` in both of `decide_market_actions`'s shed loops. **That fix was
never ported to `origin/main`.** At `MAX_ANIMALS=4` (main.py's shipped
default) it is apparently rare enough never to have been noticed - Exp 5's
land-gated ramp is the first thing in this repo to reliably produce the
exact precondition (an animal purchased after land is bought, walking a
longer distance to newly-unlocked ground, sitting in the shed long enough
to overlap a sell-decision turn).

**Correction to Exp 0-4 above:** those experiments' near-identical
$7,779-$8,245 results (Exp 2/3/4) and $418-$431 results (Exp 0/1) were very
likely hitting this same bug, not the "cash-siphon vs. land" mechanism
described at the time. The cash-competition story is not necessarily wrong
as a secondary effect, but it was never isolated from this crash - the
trajectory evidence gathered this session (frozen money to the exact
dollar, every seed, starting the turn a live animal lingers in the shed) is
a more direct and better-supported explanation for all five prior results.
Not re-verified against Exp 0/1 in this session; flagged here rather than
silently corrected.

**Per the experiment brief's own instruction ("if the experiment fails,
STOP and report the failure rather than automatically creating another
variant"): STOPPING HERE.** No head-to-head or paired comparison was run
against `main.py` - doing so would only measure how large a bank a
permanently-frozen agent accumulates before the freeze, which is not
informative about the pacing hypothesis. **The paced-ramp hypothesis was
never actually tested.** A candidate that first ports the two-line
`MARKET_PARAMS` guard (proven safe and already measured in `phase3`, though
in a bundle there) would be the natural next step, but building it was
explicitly out of scope for this stop-and-report.

## Experiment 2 (new session) - port ONLY the shed-animal KeyError fix: SUBMIT

**File:** `experiments/candidates/shed_animal_keyerror_fix.py`. **Tests:**
`tests/test_shed_animal_keyerror_fix.py` (7 tests). **Full suite:** 155/155
pass (148 pre-existing + 7 new).

**Scope, deliberately minimal:** copies `main.decide_market_actions`
verbatim and adds exactly one line, twice - `if product not in
MARKET_PARAMS: continue` - at the top of both shed-iteration loops (the
main sell loop and the `SHED_FORCE_SELL_THRESHOLD` overflow valve). Nothing
else changes: `MAX_ANIMALS`, land timing, crop scoring, hiring, and sell
thresholds are all main.py's own unmodified code, reached by calling
`base.nikaangukia_meroni(obs)` after monkeypatching only this one function.
No paced ramp, no cash-logic change - this candidate exists solely to
answer "does preventing the live-animal-in-shed KeyError improve or
preserve current performance."

**Regression tests, including a positive control:**
`TestUnmodifiedMainCrashesOnAnimalInShed` reproduces the exact shed shape
observed live in Experiment 5's crash trace (`{"WHEAT": 2, "FERTILIZER": 1,
"SHEEP": 1}`) against a *captured reference to main.py's true, unpatched*
`decide_market_actions` and asserts it raises `KeyError` - confirming the
bug is real, not assumed. Four more tests confirm the fix doesn't crash on
the same shed, doesn't silently skip selling other real products in that
same shed, and covers both iteration sites. Two equivalence tests assert
byte-identical output between the fix and the true original on an ordinary
shed and an empty shed.

**A real test-isolation bug found and fixed along the way:** the first
version of this test file imported `main as base` and then imported the
candidate module, whose top-level code monkeypatches `base.decide_market_actions`
in place (same shared module object via `sys.modules`) - so by the time the
positive-control test ran, `base.decide_market_actions` was silently
already the *fixed* version, and the test that was supposed to prove the
bug exists passed for the wrong reason (it didn't raise, because it wasn't
testing the original anymore). Fixed by capturing
`_ORIGINAL_DECIDE_MARKET_ACTIONS = base.decide_market_actions` before
importing the candidate. Worth knowing for any future candidate test in
this repo that imports more than one monkeypatching module in one process.

**Benchmarks against unmodified `main.py`, all show exact parity:**

| harness | seeds | result |
|---|---|---|
| self-play (candidate vs itself) | 6 | mean $59,018 - **byte-identical** to main.py's own self-play numbers, every seed |
| `head_to_head.py` vs `main.py` | 6 (12 matches) | **+0 mean, 6/12** |
| `paired_compare.py` vs `starter` | 12 | **+0 delta on all 12 seeds, sd=0** |

Exact parity is the expected and correct result, not a null finding: at
`MAX_ANIMALS=4` (main.py's own shipped default, unchanged here), the
precondition for the bug - an animal lingering in the shed across a
sell-decision turn - essentially never arises, so the fix has nothing to
do on these benchmarks. The evidence that the fix matters is the
regression test's positive control, not a self-play delta; the evidence
that it's *safe* is the exact parity above.

**Verdict: SUBMIT.** This is a strictly dominant change on every harness
tested - never behaves differently under current settings, and eliminates
a confirmed crash class that would otherwise cause a silent, permanent,
season-long freeze the moment anything (a future experiment, or a ladder
opponent's own animal timing crowding ours) causes an animal to sit in the
shed at the wrong moment. Ships the correctness fix `phase3` already found
and validated, without any of that branch's other, larger, unvalidated
changes.

## Experiment 2, packaging correction - Kaggle validation failed, root cause confirmed and fixed

**Kaggle validation on the submitted `experiments/candidates/shed_animal_keyerror_fix.py`
failed:** `AttributeError: module 'main' has no attribute 'nikaangukia_meroni'`
at `return base.nikaangukia_meroni(obs)`.

**Root cause, empirically reproduced (not just theorized):** the original
candidate used the `import main as base` / monkeypatch wrapper pattern
already established in this repo (`bigfarm_opponent.py`, the Exp 0-5
candidates) - valid for *local* testing, where `main.py` is a real sibling
file on `sys.path`. It is not valid for a Kaggle upload: Kaggle loads the
uploaded file itself as the module `main`, so `import main as base` inside
that same file resolves to a self-referential, still-being-executed
reference to itself - which has not yet defined `nikaangukia_meroni` at
that point (the wrapper never defines that name at all; it only ever
delegates to it). Reproduced exactly: a minimal file with the same
`import main as base` / `base.nikaangukia_meroni(obs)` pattern, run from an
isolated directory as `main.py` via `kaggle_environments`, throws the
identical traceback, including the identical final line
(`AttributeError: module 'main' has no attribute 'nikaangukia_meroni'`).

**Fix:** `experiments/candidates/shed_animal_keyerror_fix.py` is no longer a
wrapper. It is now a byte-for-byte copy of `main.py` (`cp main.py ...`,
verified with `diff`) with exactly two insertions - `if product not in
MARKET_PARAMS: continue` at the top of both of `decide_market_actions`'s
shed-iteration loops, nothing else. `diff main.py
experiments/candidates/shed_animal_keyerror_fix.py` shows only those two
additions. No `import main` anywhere in the file (grepped and confirmed).
`agent = nikaangukia_meroni` remains the final binding, matching
`main.py`'s own documented I/O contract (kaggle_environments picks the last
callable in the module namespace).

**Standalone validation, reproducing Kaggle's actual loading behaviour:**
ran the candidate from a directory containing *only* that one file (no
`main.py`, no `experiments/` package, no repo on `sys.path`) two ways -
under its own filename, and renamed literally to `main.py` (the closest
local reproduction of how Kaggle treats an uploaded single-file
submission). Both: `status=['DONE', 'DONE']`, `reward=[62887.0, 68859.0]` -
matching the known-good seed-0 self-play baseline exactly, no exceptions.

**Tests:** `tests/test_shed_animal_keyerror_fix.py` rewritten for the new
architecture (10 tests, up from 7) - the same positive-control and
equivalence tests as before, plus three new tests specifically regression-
testing the packaging bug itself: no `import main`/`from main` anywhere in
the module source, `agent is nikaangukia_meroni`, and `agent` is the *last*
callable in the module namespace (mirrors kaggle_environments' own
selection rule exactly: `[v for v in env.values() if callable(v)][-1]`).
Full suite: **158/158 pass** (148 pre-existing + 10).

**Benchmarks, re-run against the corrected file - identical results to
before the packaging fix, as expected** (the fix only touches packaging,
not the guard logic itself, which was already correct): self-play mean
$59,018, byte-identical to main.py's own numbers on every seed;
head-to-head vs `main.py`, +0 mean, 6/12.

**Verdict: SUBMIT.** `experiments/candidates/shed_animal_keyerror_fix.py` is
now genuinely standalone, validated under Kaggle's actual module-loading
behaviour, and unchanged in every other respect.

## Tooling bug found and fixed along the way

Not a game/strategy finding, but worth recording since it produced
misleading intermittent crashes during Exp 0/1: the candidate files'
`sys.path` bootstrap used a fixed `dirname()` hop count from `__file__` to
find the repo root, with a fallback to `os.getcwd()` when `__file__` wasn't
present in the exec'd namespace. `kaggle_environments`' agent loader
(`kaggle_environments/agent.py`'s `get_last_callable`) does **not always**
provide `__file__` in the namespace it execs an agent file into - observed
to vary between an identical command run twice, and between `-c` and
`python file.py` invocation of the *orchestrating* script (not the agent
itself). When the fallback fired, `os.path.dirname(os.path.dirname(cwd))`
landed two directories above the actual repo root, `import
experiments.bigfarm_opponent` raised `ModuleNotFoundError`, and the episode
ended with `status=ERROR`, `reward=None` on both seats. Fixed in all
candidate files (`_find_repo_root()`): try `__file__` if present, then walk
up from `cwd`, and **verify** each candidate directory actually contains
`main.py` before trusting it, rather than assuming a fixed hop count either
way. `experiments/selfplay_agent.py` was also hardened to pass an absolute
agent path (this turned out not to be the actual cause, but is a cheap
robustness improvement worth keeping).

## What this means for the issue's acceptance bar

| Bar | Status |
|---|---|
| 75 tiles | ✅ met (bigfarm_opponent.py and all land-gated candidates) |
| 13-15 crew | ⚠️ partial - `MAX_HANDS_PER_DAY=15` is the cap, but observed hands-in-play across seeds is 4-8, not consistently 13-15 (see bigfarm_opponent.py's own self-play trace) |
| 8-9 animals | ❌ not met by any tested candidate without an economic collapse |
| No feed collapse | ✅ at 4 animals, ❌ at 8 (herd starves along with everything else) |
| Sustained selling | ✅ (day-10 aggressive selling is inherited from bigfarm_opponent.py in every candidate) |
| Market pressure | ✅ per bigfarm_opponent.py's own measurement (MELON end price 94 vs 138 against main.py) |
| No day-22 cliff | ✅ (`LIQUIDATION_START_DAY=10`, no separate cliff logic) |
| Self-play ~$90-100k | ❌ best reached: $7,806 (bigfarm_opponent.py itself, at 4 animals not 8-9, reaches $59,018 - closer but still short of the target and not at the target animal count) |

**Revised recommendation, after the redundancy finding above: `main.py`
itself is already the reference opponent for 5 of these 8 bars** - it
natively reaches 75 tiles, sells hard from day 10, holds no cliff, and
banks $59-63k in self-play with no collapse, with no wrapper needed.
`bigfarm_opponent.py` as currently written adds nothing on top of that.
"8-9 animals without collapse" is the one bar nothing in this repo has ever
cleared (confirmed independently by the unmerged `experiment/animal-cliff`
branch hitting the same wall a different way) - treat it as a separate,
harder, still-open problem for a follow-up session, not a blocker for using
`main.py` directly as today's evaluation baseline.
