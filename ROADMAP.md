# Architecture Roadmap

## What this document is

This is not a critique of `main.py`, and it is not a list of things not to
do. It's a description of how to structure the agent's decision logic so
that the failure modes we've already paid for — the TOMATO/STRAWBERRY
four-attempt saga, the BUY_LAND and multi-animal "dead ends," the seed
overcommit bug, the feed-oscillation bug — become structurally unreachable
going forward, instead of individually patched and individually re-broken
in a new shape a few weeks later.

**Code structure is necessary, not sufficient.** The right structure
prevents a *class* of bug from recurring — a shared per-turn ledger makes
unit-collision bugs structurally unreachable, for example. But structure
alone doesn't supply the correct thresholds, weights, or target values that
live inside it. Those still have to come from evidence — measured against
real data, not guessed. This roadmap holds both together: every phase below
states the structural change *and* the evidence that justifies pointing it
where it's pointed. Neither half is the pitch on its own.

---

## 1. Evidence base

Two sources, cited by name so nothing here reads as opinion:

- **Our own measured history** — `CLAUDE.md`'s "Measured dead ends" and
  lesson entries, built from `paired_compare.py` / `head_to_head.py` /
  `selfplay_bench.py` runs against our own agent over the life of the
  project.
- **Direct analysis of real top-ladder episodes.** This session pulled six
  replay files from the host-maintained
  [`kaggriculture-episodes-index`](https://www.kaggle.com/datasets/kaggle/kaggriculture-episodes-index)
  Kaggle dataset — daily dumps of the top-rated episodes on the live
  ladder — spanning **Aug 1, Aug 10, and Aug 16 (×3)**, eight distinct
  player pairings. Five of the six were near-identical down to exact unit
  counts (127 WHEAT plants, 34 STRAWBERRY plants, 20 MELON plants, in more
  than one unrelated pairing) — evidence that most of the top of the ladder
  is running one dominant shared strategy, not a diversity of approaches.
  This is the first time this project has looked outward instead of only
  at our own local benchmarks.

The dataset is cheap to sample without pulling a whole day's ~21GB:
`kaggle datasets files kaggle/kaggriculture-episodes-<date>` lists
individual per-episode JSON files (~25-32MB each, standard
`kaggle_environments` replay format — the same shape `replay_diagnostics.py`
already parses), then
`kaggle datasets download kaggle/kaggriculture-episodes-<date> -f <episode_id>.json`
pulls exactly one.

---

## 2. The target shape, empirically

Descriptive, not prescriptive — this is what we measured six real episodes
actually doing, not a design proposal:

| Signal | Observed (6 episodes, Aug 1–16) | Us today |
|---|---|---|
| Final money | $71,757 – $126,015 | $31,132 (self-play) / ~$42k (vs built-ins) |
| `BUY_LAND` | exactly 2×, every episode, always day 6–11 | 0 (measured dead end) |
| Hands sustained | ramps to 10–14 by day ~8, held through ~day 27 | small fixed cap |
| Animals | COW + SHEEP together (sometimes + GOOSE), every episode | 1 sheep only (2+ measured a heavy loss) |
| MELON planting | days 0–7 only, then stops for the rest of the season | plants all season, gated only by season-maturity |
| STRAWBERRY planting | days 5–12 only — planted once per tile, never replanted | treated as a repeatable per-tile choice all season |
| CARROT planting | days 21–25 only — a late-game filler crop | no explicit late-game role |
| WHEAT planting | continuous, days 0–27 | continuous — matches |
| TOMATO planting | **never, in any of the 6 episodes** | rare — this independently validates the just-closed TOMATO/STRAWBERRY investigation's conclusion to leave TOMATO alone |
| Selling | ramps starting day ~10, stays heavy (15–48 orders/day) straight through day 29 — no discontinuity at day 22 | infrequent, threshold-triggered |
| `BUY_PRODUCT` (wheat buybacks) | used heavily in some episodes (up to 361 orders) — wheat treated as a standing supply line for animal feed, not an emergency-only fallback | emergency-only safety net |

Two shape observations worth calling out explicitly because they cut
against what the Strategic Brief assumed going in:

- **All infrastructure spend (land, pasture, animals) is compressed into
  day 0–11 and never happens again after that.** That's a real phase
  boundary — just later than the brief's proposed day-0-7 SETUP window.
- **There is no day-22 "LIQUIDATE" cliff.** Selling ramps hard around day
  10 and simply stays high for the rest of the game. The only true
  late-game signal is per-crop: CARROT gets introduced specifically in the
  day 21-25 window as a short-cycle filler, and hiring/planting taper
  softly in the final one to two days. A single global day-gated
  `SETUP → GROWTH → LIQUIDATE` state machine would mis-model this — the
  real structure is per-crop timing windows layered on top of one early
  infrastructure window, not one global phase variable.

---

## 3. The core thesis: structure prevents recurrence, evidence aims it

For each failure mode we've already paid for, here is the structural
presence that would have made it a non-issue — paired with the evidence
that shows the structure is aimed at the right target.

### a. The TOMATO/STRAWBERRY saga

Four separate attempts (flat bonus, absolute gate, relative gate, a
"more accurate" `growth_days`) patched `choose_crop` because its scoring
formula's `growth_days` term didn't distinguish crops whose tile frees up
at harvest (one-shot: wheat, carrot, melon) from crops whose tile persists
and keeps producing past `max_yield_day` (ongoing: tomato, strawberry).
Each attempt special-cased the fix per crop, and each one measured false —
including the mechanically "correct" fix, because correcting one input in
isolation doesn't compose safely with everything else an ad-hoc heuristic
was implicitly compensating for.

**The structural fix**: give every crop an explicit `occupancy_kind`
(one-shot / ongoing) as a first-class property that the *same* formula
reads for every crop — so the distinction is derived once, structurally,
rather than re-invented per crop, per attempt. The replay evidence
independently confirms this is the right axis: STRAWBERRY gets planted
once per tile in a narrow window (because it's ongoing and one planting
keeps paying out), while WHEAT gets replanted continuously (because it's
one-shot). That's a structural distinction the top-ladder strategy has
already encoded — not a tuned constant.

### b. BUY_LAND / multi-animal "dead ends"

Both were tested as independent on/off toggles held against a *fixed*
crew size, and both lost — correctly, at that crew size. Land spreads a
fixed crew thinner; a second animal eats a tile and a share of upkeep
capacity a fixed crew can't spare. Both conclusions were true statements
about the agent as it was configured when tested.

**The structural fix**: make crew size a *derived* value — a function of
current unlocked-tile count and animal upkeep needs, weighed against the
fib hiring-cost curve — instead of a constant chosen once and left stale.
If hiring reads live tile/animal state every time it runs, land and
multi-animal decisions can never again be tested (or shipped) against a
stale crew; the confound that produced both "dead end" conclusions becomes
structurally unreachable rather than something to remember not to repeat.
The replay evidence is what justifies revisiting this at all: every
top-ladder episode buys both land expansions and runs two-plus animal
species, sustained by a crew that scales into double digits — the losing
conclusion was correct for an undersized crew, not for the game.

### c. Fix A (seed overcommit) — the pattern already proven, worth reusing

Already shipped and merged (PR #13, merged into `main` via PR #14,
`8477dfe`): a shared per-turn `plant_budget` that every unit consults
before proposing a `PLANT` action, closing the bug where the engine drops
*all* of a turn's plant requests for a crop once demand exceeds held seed
stock, not just the excess.

This is the shape to reuse anywhere multiple units compete for one finite
shared thing — hire slots, a wheat-feed reserve. A shared, consulted-before-
acting ledger object structurally prevents the collision; independent
per-unit decisions can't.

**One caveat surfaced during that merge, worth carrying into Phase 1
below:** PR #14 bundled Fix A with an unrelated hire-gate change
(`MIN_MONEY_TO_HIRE` 150→20) and found the two measure **sub-additive**
together — +598/7-12 combined versus Fix A's own isolated +2,271/10-12.
Two independently-good changes didn't compose cleanly here; that's a
reason to re-measure the bundle, not evidence against the shared-ledger
pattern itself, but Phase 1 shouldn't assume extending the pattern to
hiring is automatically additive with whatever hiring logic already
changed underneath it.

### d. The feed-oscillation bug

Caused by gating a periodic action (`FEED`) on a counter
(`consecutive_unfed`) that the action itself resets — invisible from a
static read of the code, and it produced a stable, silent every-other-day
feeding cadence that discarded most of the CARE bank.

**The structural rule**: schedule recurring maintenance actions by "time
since last performed, versus an intended cadence," never by a state
variable that the action being considered also mutates. Any trigger keyed
on a counter its own action resets will oscillate — check the duty cycle
you actually get, don't assume it fires whenever it's needed.

### e. Evaluation methodology (two real wins mislabeled "a wash")

Not agent code, but the same category of problem: measuring a change
against across-seed variance instead of a paired comparison mislabeled the
daily-feeding fix and the `WORK_TILES_PER_HAND` change as noise, when both
were large, consistent wins (12/12 and 16/16 respectively).

**The structural rule**: paired comparison is the only sanctioned way to
judge a change — already the standard in `CONTRIBUTING.md`. The corollary
this session adds: a **bundled** change (land + crew + a second animal,
all scaling together) needs a bundle-level paired test, not three separate
isolated ones. Isolated testing of resources that only pay off jointly is
exactly what produced the two false-negative dead ends in §b.

### f. Missing concepts, discovered at real cost

The ongoing-crop tile lifecycle, the CARE-bank accrual/payout timing, the
plant-request-drop-on-oversupply mechanic, and melon's zero-shop-demand
structure were each found the hard way — a losing measurement, hours of
instrumented tracing, or a shipped submission — and none of them are
indexed anywhere. They exist only as prose scattered through `CLAUDE.md`.
This is what `docs/CONCEPTS.md` (see §5) exists to fix: not to prevent the
bug from being written, but to prevent the same discovery cost from being
paid twice.

---

## 4. Roadmap phases

Sequenced. Each phase states its evidence, the existing pattern it extends,
and how success will be measured — bundle paired comparison, never
across-seed stdev.

**Phase 0 — Clear the queue.** No strategy change. PR #13 (Fix A) is
**already merged** (via PR #14). Still open: freeze a V3
checkpoint reflecting current `main` post PR #14. This clears the deck so
nothing below conflicts with unmerged work.

**Phase 1 — Generalize the shared-ledger pattern.** Extend `plant_budget`'s
shape (§3c) to hiring and to wheat-feed reservation, so no two units can
ever collide over a shared finite resource. Pure structural work, no new
strategy content, directly reuses a pattern already proven to work — but
re-measure the bundle rather than assuming it, per the sub-additive
interaction noted in §3c: the last time a proven pattern met an unrelated
hiring change, the combination underperformed either half alone.

**Phase 2 — Crew size as a derived function.** Replace the fixed hand cap
with a live computation from unlocked-tile count and animal upkeep, weighed
against fib hiring cost. This is the prerequisite Phase 3 depends on — it's
what makes land and multi-animal decisions safe to re-test at all.

**Phase 3 — Bundled re-test: land + second animal, post-Phase-2.** Re-run
`BUY_LAND` (both purchases, targeting the day 6–11 window the evidence
shows) together with a second animal species, as **one** paired-comparison
experiment, now that crew size auto-scales with them. This is the first
phase that touches strategy content, and it's the direct empirical test of
§3b's thesis: does the "dead end" go away once the confound is removed?

**Phase 4 — Crop `occupancy_kind` as a structural property.** Implements
§3a. Closes the TOMATO/STRAWBERRY investigation by removing the structural
gap that caused four different tuning attempts to fail, rather than tuning
around it a fifth time. Validate against the replay shape: strawberry
narrow-window-once, wheat continuous.

**Phase 5 — Per-crop timing windows, not a global day-gated phase machine.**
Melon early-only (front-load before the market it crashes recovers),
carrot late-filler (day 21-25), wheat always — each derived from the
crop's own market economics, not a shared day cutoff. Matches the replay
evidence directly: there is no day-22 liquidation cliff to build a state
machine around.

**Phase 6 — Selling cadence.** Raise sell-order frequency once production
ramps — observed top-ladder rate is 15-48 orders/day starting around day
10 — while keeping the already-validated "spread, don't dump" rule for
premium goods intact.

**Phase 7 — `docs/CONCEPTS.md` as an ongoing practice.** Not a one-time
document — the discipline of updating it the moment a new mechanic is
discovered via tracing or replay analysis, so a discovery cost like §3f's
four examples is paid once per mechanic, ever, instead of being
re-discovered by a future session.

---

## 5. `docs/CONCEPTS.md` — recommended, being created alongside this roadmap

Yes, this project should keep one. Reasoning:

- The Strategic Brief already specced this exact artifact in its §6.2, and
  it's the one piece of that brief that's low-risk, low-cost, and requires
  no architecture change to adopt on its own.
- This session independently rediscovered the need for it: at least four
  mechanics (§3f) were each found at real cost and are recorded only as
  prose scattered through `CLAUDE.md` — not indexed anywhere for lookup
  before starting new work.
- It is **not** a replacement for `CLAUDE.md`'s narrative lessons.
  `CLAUDE.md` stays the reasoning trail — what was tried, why, what the
  measurement showed. `CONCEPTS.md` is the structured lookup table
  extracted from it: constants, causal links, synergies/anti-synergies,
  each entry citing how it was verified (engine source, instrumented
  trace, or replay observation), matching the "engine is the source of
  truth" convention `CLAUDE.md` already follows.
- It lives in `docs/` — not `mydocs/` — because its whole value depends on
  being a permanent, continuously-updated, team-shared reference, the same
  role `docs/ARCHITECTURE.md` and `docs/CHECKPOINTS.md` already play.
