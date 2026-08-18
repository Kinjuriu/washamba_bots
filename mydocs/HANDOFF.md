# Session handoff — 2026-08-17

Personal file, historically not committed on other branches (see
`chore/env-bootstrap-v2-sync`'s pending `.gitignore` rule for `/mydocs/`,
not yet merged to `main`). **On this branch, `causality-mapping`, it and
the rest of `mydocs/` are deliberately committed** — this branch exists
specifically to archive the Fix B research trail so it survives even
though the underlying code changes did not. Read this before picking
work back up in a new chat.

## Session close-out (read this first)

Took the retry-2 assessment's own recommended "legitimate next step" —
fix `growth_days` for ongoing crops (TOMATO/STRAWBERRY) to reflect real
tile-occupancy instead of `max_yield_day` — implemented it, and measured
it properly. **It is also a decisive loss: -5,099 mean, 0/12 vs
`starter`; -7,116 mean, 0/12 vs `pass`.** Isolating the two crops shows
the loss is almost entirely **STRAWBERRY** (-5,593, 0/6, correcting it
alone) while correcting **TOMATO alone is a wash** (-104, 1/12, 10/12
seeds exact zero delta — the fix essentially never fires for TOMATO in
practice). Full write-up is in `CLAUDE.md`'s "Measured dead ends" section
on this branch.

**This closes the entire TOMATO/STRAWBERRY crop-scoring investigation —
four attempts deep (flat bonus, absolute gate, relative gate, growth_days
accuracy fix), each individually well-reasoned, each falsified on
measurement.** The user's own read on this, which this session concurs
with: the reasoning chain was buckling under its own complexity — every
failure produced a more elaborate theory to explain it rather than
questioning the premise that TOMATO/STRAWBERRY's low selection frequency
needs fixing at all. **Recommendation for the next chat: don't reopen
this without genuinely new evidence, and don't let a plausible-sounding
mechanism alone be the bar for trying again — every one of these four
was plausible and every one was wrong.**

**What actually happened to the code:** the `crop_growth_days()`
implementation and its tests were written, measured, and then fully
discarded (`git checkout -- main.py tests/test_nikaangukia_meroni.py`) —
not committed-then-reverted like the fertilizer-bonus attempt, since
there was no reason to preserve broken code in `main`'s history this
time. `main` itself is untouched by any of this session's work. Only
this `causality-mapping` branch carries the writeup + full mydocs/
archive (`FIX.md`, `FIX_B_FERTILIZER_YIELD_BONUS_EVALUATION.md`,
`FIX_B_RETRY_2_PROPOSAL.md`, `FIX_B_RETRY_2_ASSESSMENT.md`, this file,
and `scratch/` tracing scripts+data) — committed in full, deliberately,
per explicit instruction not to lose any of it. If a future chat wants
the `CLAUDE.md` dead-end entry on `main`, that's a small standalone
docs-only cherry-pick/PR from this branch's one commit (`68ca33a`).

**Original finding this session (1st pass, superseded above):** Fix B
had failed three separate retries (flat bonus, absolute gate, relative
gate), and a deeper diagnostic found a plausible root cause: TOMATO's
real tile-occupancy is ~12 days, not the 8 the score formula assumes,
because it's an "ongoing" crop that decays into a WEED after its last
tick instead of clearing on harvest. `mydocs/FIX_B_RETRY_2_ASSESSMENT.md`
recommended fixing `growth_days` instead of boosting TOMATO further —
that recommendation has now been tried and also failed, see above.

## Priority — do this first, before anything else next session

**Authenticate `gh`.** It's now installed (`winget install --id GitHub.cli`,
v2.97.0) but `gh auth status` reports not logged in, and `gh auth login` is
interactive (browser/device code) so it couldn't be run from a headless
background session. Run it yourself, or from inside a live session type
`! gh auth login`. Confirm with `gh pr view 13 --repo Kinjuriu/washamba_bots`
once done.

## Repo state right now

- `main` tip: `2114390` ("Merge forward pricing + opponent modelling (PR #12
  integrated)"). Nothing newer upstream as of this session.
- `chore/env-bootstrap-v2-sync`: clean, one commit ahead of where it
  started — `48358d9` (`.gitignore` +`/mydocs/`). Pushed status not
  re-checked this session; verify before assuming it's on `origin`.
- `fix/seed-plant-budget-batched-rebuy`: **PR #13 confirmed open** on
  GitHub (verified via `git ls-remote origin 'refs/pull/*'` — tip
  `506b770` matches `refs/pull/13/head`). The user opened it manually.
  Still awaiting review/merge as of this session.
- `fix/tomato-fertilizer-yield-bonus`: **pushed to origin**, net diff vs
  `main` is CLAUDE.md-only (the fertilizer-bonus code was implemented,
  measured, and reverted in the same branch — see the Fix B section
  below and CLAUDE.md's "Measured dead ends"). No PR opened; not worth
  merging as a fix, but the docs commit could go to `main` via a small
  docs-only PR if wanted.
- Environment fully bootstrapped: `.venv` (Python 3.13.7 via `uv`),
  `kaggle-environments`, all deps installed.
- Tests on `fix/seed-plant-budget-batched-rebuy`: **124 passing** (118
  baseline + 6 new `TestSeedRestockQuantity` cases), validation gate
  `['DONE','DONE']`.
- `causality-mapping` (this branch): one commit (`68ca33a`) ahead of
  `main` tip `2114390`, docs-only — the `CLAUDE.md` growth_days dead-end
  writeup plus the full `mydocs/` research archive. See "Session
  close-out" above.
- `fix/ongoing-crop-growth-days`: a leftover empty branch pointer, sitting
  at `main`'s tip with zero unique commits (the code that was briefly on
  it was discarded via `git checkout`, never committed). Harmless to
  delete whenever convenient; not cleaned up this session.

## Fix A (seed-overcommit bug / wheat-feed starvation) — COMPLETE

Implementation, verification, and documentation are done. Only remaining
step is opening the actual PR (blocked on `gh`, see priority above) and
getting it reviewed/merged.

**The bug:** `choose_unit_action`'s PLANT step had no shared per-turn seed
budget, so multiple units could each independently plant the same
understocked crop in one turn; the engine drops **all** that turn's PLANT
requests for the crop, not just the excess (`kaggriculture.py:920-931`).

**Why three earlier fix attempts all failed catastrophically** (this
session's first half wrongly blamed "accidental unit clustering" near the
animal — that theory is **retracted**, see below):

| Variant | Mean delta | Wins | Sheep survival |
|---|---|---|---|
| Seed budget + full-ladder-reentry fallback | −15,785 | 0/12 | dead 12/12 |
| Dedicated animal-keeper unit | −813 | 4/12 | moot — baseline never starved here |
| Hardened wheat buffer (reserve 2→6, batched buy) | −98 | 1/12 | moot — same reason |

**Real mechanism, confirmed by an instrumented turn-by-turn trace, not
inference:** the farmer never leaves its starting shed-adjacent tile in a
working season (FEED/CARE/PICKUP all resolve there daily), so the PLANT
step never touches the feeding unit regardless of routing. What actually
kills the sheep: once the overcommit bug is closed, a seed is *reliably
consumed* every turn, and the old `should_buy_seed()` re-buys at full price
every single time stock dips below the cap — for MELON (~$80/seed) that's
an $80/turn drain, crashing the bank to ~$25 by day 3-4. At that point the
wheat safety-net `BUY_PRODUCT` order is silently rejected (`money < price`,
no error raised, `kaggriculture.py:663`), the shed runs dry, and the sheep
misses two consecutive feeds. **A seed-repurchase cost spiral, not a
routing problem.**

**The fix that shipped:** shared per-turn `plant_budget` (closes the
overcommit bug) + `seed_restock_quantity` replacing `should_buy_seed` —
only restocks once a crop's seed is **fully exhausted** (not merely under
the cap), buys the whole gap back to `MAX_SEED_STOCKPILE` in one batched
order, and never lets a purchase drop the bank below
`MIN_CASH_RESERVE_FOR_SEED_BUYING`.

**Full benchmark record** (baseline = unmodified `main.py` at `2114390`):

| harness | result |
|---|---|
| `paired_compare.py` vs `starter`, 12 seeds | **+2,271 mean, 10/12 wins, t=3.70** |
| `seeded_batch.py` vs `pass`/`random`/`starter` | flat-to-up, but variance roughly 2-3x baseline's (unexplained, flagged as a gap) |
| `selfplay_bench.py`, 8 seeds | **46,105 → 42,546, a real regression** — MELON end price 129→53, a symmetric-oversupply effect specific to facing a mirror of yourself, not a competitive weakness |
| `head_to_head.py`, candidate vs baseline, 24 matches | **+2,220 mean, 20/24 won** — the closer proxy to a real (non-mirrored) ladder opponent, and it confirms the win |
| Sheep survival vs `starter`, 12 seeds | alive 12/12, both baseline and candidate |

`CLAUDE.md` has been updated with the full write-up (new lesson entry plus
three new "measured dead ends" bullets for the three failed variants above)
and committed alongside the fix on the fix branch.

**Loose end from this fix, not blocking:** the `seeded_batch.py` variance
increase (roughly 2-3x baseline across all three built-ins) isn't
explained. Plausible mechanism: a batched restock is lumpier turn-to-turn
than steady 1-unit buying. Worth a look if anyone has spare cycles, not
urgent.

## Fix B (tomato fertilizer bonus) — TRIED, MEASURED NEGATIVE, NOT SHIPPED

`gh` is now installed (`winget install --id GitHub.cli`, v2.97.0) but
**not authenticated** — `gh auth login` is interactive (browser/device
code), couldn't run it headless this session. Run it yourself next time
(or `! gh auth login` from inside a live session) before trying PR admin.

Implemented, tested, and measured against current `main` tip (`2114390`)
this session, on branch `fix/tomato-fertilizer-yield-bonus` (pushed to
origin). Full writeup is now in `CLAUDE.md`'s "Measured dead ends"
section — short version:

- Added `FERTILIZER_YIELD_BONUS = {"TOMATO": 1.0}` + `has_active_fertilizer_source(farm)`
  (gated on a placed/filled sheep, not held stock — see the CLAUDE.md
  comment for why), bumping TOMATO's `expected_yield` in `choose_crop`'s
  scoring loop when true.
- All local checks passed cleanly first: unit tests (123/123), the
  `['DONE','DONE']` validation gate, sheep survival, and it did fix the
  literal bug on some seeds (TOMATO plant/sell counts went from 0 to
  nonzero).
- But the actual measurement failed the repo's own win-count-first rule:
  `paired_compare.py` vs `starter` **2/12 wins** (mean -101), vs `pass`
  **2/12 wins** (mean +63); `head_to_head.py` **11/24 wins** (mean +386,
  propped up by a few big swings — self-control came back exactly at 0
  mean as expected, so the harness itself is trustworthy here).
- Root cause, confirmed via a per-seed action-histogram diff (not
  guessed): the bonus steals unit-turns from **WHEAT/CARROT**, not MELON
  like every earlier diversification attempt. TOMATO's seed costs 5x
  WHEAT's and ties up a tile for 8 days vs WHEAT's 4 — a flat yield bump
  doesn't account for the tile-time a fast, cheap crop would have cycled
  through instead. Raising the bonus value further would make this worse,
  not better, so that wasn't retried.
- Final branch state: implementation commit (`4bd053c`) + docs commit
  (`b1e943b`) + a `git revert` of the implementation (`404e94b`), so the
  branch's net diff against `main` is CLAUDE.md-only. Pushed to origin;
  **not** opened as a PR (nothing to merge functionally, just the
  dead-end writeup — worth a small docs-only PR if you want the
  writeup on `main` rather than parked on this branch).

**Retry #2 (relative-gate bonus, `bonus=1.5`) was proposed in
`mydocs/FIX_B_RETRY_2_PROPOSAL.md` and reviewed this session — rejected,
not implemented.** The proposal's own claimed intermediate step ("retry
#2a," gating on `SELL_PRICE_THRESHOLDS`, found inert) has no trace in
this repo's git history — it exists only as a narrative in that doc, from
outside this session's own work. Its core margin numbers were
independently re-derived and corroborated (closest-miss margin matched to
two decimal places), but the proposal's central calibration claim —
"TOMATO's price caps at $60, so `bonus=1.5` only flips the closest
miss" — is **false**: the engine prices *above* base when scarce, TOMATO's
forecast price ranged up to $144–$286 across seeds, and at `bonus=1.5`
the gate would actually flip 5%–67% of all losing decisions depending on
seed (not "rarely"). Full writeup: `mydocs/FIX_B_RETRY_2_ASSESSMENT.md`.

**Then a deeper diagnostic (requested: "run a diagnostic if the current
hypothesis still has more to it, like Fix A") found the real mechanism.**
TOMATO/STRAWBERRY are `"ongoing"` crops — `HARVEST` does **not** clear
their tile (`kaggriculture.py:467-468`); the tile only frees up later via
`_decay_plants`, which lets it rot into a `WEED` (needing a `DIG`) some
time after the last production tick. Measured directly against the
installed engine (deterministic, no RNG): TOMATO's real tile-occupancy is
**~12 days**, not the `8` (`max_yield_day`) the score formula uses as
`growth_days`; STRAWBERRY's is **~17**, not `10`. Corroborated by a real
episode replay. `main.py` also never proactively digs a still-growing
ongoing-crop tile — only `WEED`-kind tiles — so ~12 days is a floor on
real occupancy, not the average.

**This means the current formula already overvalues TOMATO** relative to
its real tile-time cost (corrected score ≈20 vs the formula's current
≈30 at baseline price) — every "boost TOMATO" attempt (all three retries)
was pushing an already-overvalued crop even higher, which is consistent
with why each one measured flat-to-negative. **Recommendation: stop
trying to make TOMATO sell more — it may be the correct economic outcome,
not a bug.** If pursuing anything in this area, the legitimate next step
is fixing `growth_days` for ongoing crops generally (use real
tile-occupancy, not `max_yield_day`) — a correctness fix that would likely
reduce TOMATO's (and maybe STRAWBERRY's) planting frequency further, not
increase it. Not implemented or measured yet.

Full detail, all verification steps, and the exact numbers:
`mydocs/FIX_B_RETRY_2_ASSESSMENT.md`.

## Other loose ends worth knowing about

- **No new checkpoint (V3) has been frozen** for the forward-pricing +
  opponent-modelling merge — `docs/checkpoints/` still stops at V2-sheep
  (`93d6bed`), which predates it. Not blocking, but the "frozen baseline"
  is stale relative to current `main`; both Fix A's measurements and any
  future work should keep comparing against `main` tip directly (per
  `CONTRIBUTING.md`'s own documented fallback) until someone freezes V3.
- Two remote branches exist that haven't been looked at:
  `experiment/forward-pricing-crop-selection`,
  `experiment/forward-pricing-integration`. Unexplored.
- `mydocs/rules.md`'s line-number pointers predate the forward-pricing
  merge — flagged multiple times now, still not re-verified. Worth doing
  before trusting it for a quick lookup.
