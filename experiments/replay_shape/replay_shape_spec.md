# Reference Opponent Specification (Issue #21, Track C → executable spec)

Derived from `experiments/track_c_replay_audit.md` — every number below cites
back to that document's confidence rating, not restated from memory. **This
specifies a scripted, deterministic reference opponent for local
benchmarking, not a change to our own strategy.** Its only job is to exert
the same *structural pressure* real large ladder agents exert — a big farm,
a big crew, real selling volume — so an experiment whose advantage only
shows up against that pressure (throughput fixes, market-flooding
sensitivity, anything currently invisible against `starter`/`pass`/`random`)
becomes measurable at all.

**Not implemented here. No code. `main.py` untouched. Not merged.**

## How to read this document

Every numeric claim is tagged:

- **HARD** — the reference opponent's script must satisfy this exactly (or
  as a strict bound). Reserved for claims the audit rated **High
  confidence** and corroborated across independent sources.
- **SOFT** — a target range or shape to aim for, not a pass/fail gate.
  Used for anything the audit rated **Medium confidence** or below, or
  anything that was only ever observed as a correlation.
- **OMITTED** — a number that appeared in the original hypothesis list but
  that the audit found the evidence does not support as stated. Named
  explicitly so it isn't silently dropped, with the reason.

Section numbers match the ask; §8 (validation) reuses these same tags rather
than restating a separate, possibly-inconsistent list.

---

## 1. Farm scale

**HARD**
- Reaches land ownership via **exactly two `BUY_LAND` purchases**, not a
  single jump or a gradual buy-out. (Audit A.3 — 6+2 episodes agree
  tightly on "exactly 2×.")
- Final owned tiles: **75** (the ceiling of buying both purchasable
  quadrants at the default board size — audit A.3, confirmed in 2/2
  independently-checked episodes and mechanically reproduced in
  `experiment/land-and-crew`'s `1d5be21`).

**SOFT**
- First purchase around **day 6–7**; second around **day 11** (audit
  claim 4, High confidence, but a 1-day spread was directly observed —
  don't gate on the exact day).
- Land trajectory shape: `25 → 50 → 75`, i.e. two roughly-equal-sized
  jumps, not 25→75 in one step (observed in both spot-check episodes).

**OMITTED**
- No evidence supports a tile count *between* 75 and any other value as a
  meaningful intermediate target beyond the two-purchase staging above —
  the audit found no replay ever stopped at, e.g., 50 tiles permanently.

---

## 2. Crew scale

**HARD**
- None. The audit rates crew size a **strong correlation, not an
  independently-verified target** (audit B.1) — it's coupled to land, and
  our own Track A test showed a *derived* crew formula
  (`max(MAX_HANDS_PER_DAY, owned_tiles // 5)`) reproduces the observed
  shape mechanically. The reference opponent should use a **derived**
  formula, not a hardcoded crew-size gate.

**SOFT**
- Crew held (simultaneous hands) target: **12–15**, sustained from
  roughly day 8–12 through day ~27–29 (audit claim 2, Medium confidence,
  n=2: "12–13, days 8–29" / "15, days 12–29").
- Hiring trajectory: ramps as land unlocks work, not before — `1d5be21`'s
  derived formula is a no-op at 25 tiles by construction (crew stays at
  the pre-land baseline until land fires), then climbs as owned-tile
  count rises.
- Cash constraint: hiring must not starve the days-3–7 cash trough (see
  §7) — this is a *behavioral* constraint on the hiring formula, not a
  crew-size number.
- Utilization target: **not independently evidenced**. No replay data in
  the audit measures idle-hand rate for opponents; do not invent a
  utilization percentage.

**Explicitly distinct from a number easy to confuse with this one**: total
season **`HIRE` order count** was measured at 263–277 (audit claim 2) — this
is *not* a crew-size target, it's a re-hiring frequency consequence of hands
being cleared nightly. The reference opponent's hire-order count is an
*output* of the day-by-day crew-target formula, not a target to hit
directly.

---

## 3. Animal scale

**HARD**
- None. Audit B.3/C.6: 8–9 total animals is a correlation at n=2, and our
  own measured sweep (`ec38fc5`) found scaling animals past the
  farm's current upkeep capacity is a **heavy loss**, not a free win — the
  same coupling problem as land. A hard animal-count gate would encode an
  unverified assumption.

**SOFT**
- Total animals target: **8–9**, split roughly **5–6 cow : 3 sheep**
  (audit claim 3, Medium confidence, n=2 — both episodes agree on the
  total and the cow-majority split).
- Purchase/build timing: not independently timed in the audit's sources —
  treat as coupled to the pasture-structure build rate, itself gated by
  the same cash-trough survival constraint as crew (see below). No
  specific day-by-day animal-acquisition schedule is evidenced.

**Feed-cost survival requirement (behavioral, not numeric)**
- The reference opponent's animal-acquisition logic must **not** be
  allowed to drain cash below whatever reserve its own feed/water
  maintenance needs to survive the days-3–7 trough. This is not a replay
  observation — it's a mechanistic requirement carried over from our own
  measured failure mode (`85fbbc2`: an under-reserved second animal
  starved and escaped, recorded as a "heavy loss" that was actually a
  cash-timing bug, not an animal-count problem). Any reference-opponent
  implementation should treat this as a HARD internal invariant even
  though no replay directly measures it, because its absence is what
  produced a known false-negative in our own history.

---

## 4. Crop mix

**HARD**
- **Never plants TOMATO.** (Audit A.1 — 8/8 episodes across both
  independent sources, the single most robust finding in the whole
  audit.)
- **Plants WHEAT continuously**, days 0–27 at minimum. (Audit A.2 — 8/8
  agreement on the window; only unit *volume* varies.)

**SOFT**
- MELON: planted only early, roughly **days 0–7 through 0–11** — the
  audit found the exact right edge varies between checked episodes (one
  stops at day 7, one continues to day 11), so the window's *end* should
  be a soft boundary, not hardcoded to day 7. (Audit B.4 / claim 6,
  Medium confidence.)
- STRAWBERRY: narrow mid-season window, roughly **days 5–12** (audit B.2,
  well-corroborated at n=2 inside ROADMAP's stated window, but still only
  n=2 for the exact edges).

**OMITTED**
- **CARROT as a day-21–25 late filler.** The audit found this present in
  only **one of two** independently-checked episodes (the other planted
  zero carrot at all). Per the explicit instruction not to invent
  thresholds the evidence doesn't support, this is *not* included as
  even a soft target — if a reference opponent happens to plant carrot
  late, that's acceptable, but the spec doesn't require or expect it.

---

## 5. Production

**SOFT** (no HARD claims — the audit has no directly-measured production
*rate*, only outcomes)

- Planting behaviour should follow the crop-mix windows in §4, not a
  fixed planting cadence.
- Harvesting behaviour: not separately evidenced beyond "enough to sustain
  the sell volume in §6" — no replay data isolates harvest timing from
  planting/selling.
- Expected production scale: only indirectly evidenced via final
  crop-mix unit counts from the two verification episodes — **WHEAT
  ~108–127 units/season, STRAWBERRY ~34–51 units/season (also seen in the
  land-and-crew retry), MELON ~20–24 units/season.** These are *outputs*
  of the farm-scale and crop-window targets above, not independent
  targets to hit directly — listed here only so an implementation has a
  sanity-check ballpark, not a gate.

---

## 6. Market pressure

**HARD**
- None. Even "selling starts ~day 10" is corroborated but not tight
  enough (audit claim 5: independently reconfirmed via `replay_shape.py`'s
  own "first sell-heavy day" computation, both spot-check episodes said
  10) to gate a HARD pass/fail on — treating it as SOFT.

**SOFT**
- First meaningful selling day: **around day 10** (Medium-high
  confidence — independently reconfirmed, but only n=2 for the exact
  value).
- Orders/day during the active selling period: **roughly 15–48** — audit
  explicitly flags this as the **weakest-verified numeric claim in the
  whole hypothesis list** (traceable only to ROADMAP.md's 6-episode
  summary; never independently re-derived from either spot-check
  episode's raw per-day data — see `track_c_replay_audit.md` §5 and §F.1).
  **Use this as a loose shape target only.** Do not treat 15 or 48 as
  precise bounds until `experiments/replay_shape.py` is extended to emit
  a real per-day series (audit's own recommended next step, §G.1).
- Seasonal selling profile: **ramps starting ~day 10, then stays elevated
  for the rest of the season** — no single spike, no late-game falloff.
- **Absence of an artificial liquidation cliff**: the reference opponent's
  selling logic should **not** be a hard day-gated switch (e.g. "hold
  below threshold until day N, then dump everything"). This is as much a
  *design instruction* as a data claim — ROADMAP.md argues directly
  against a single global day-gated phase variable, and this repo's own
  unrelated finding (day-19 beats day-25 liquidation cutoff, head-to-head)
  independently supports smooth-over-cliff behaviour, even though that
  finding comes from our own agent, not the replay.
- Inventory trajectory: not directly evidenced (opponent shed contents are
  never observable — audit §F.5) — the only inventory-adjacent signal is
  that production and selling stay roughly in balance long enough to reach
  the bank figures in §7, which implies inventory does *not* pile up
  indefinitely. Treat "shed doesn't accumulate a large unsold pile" as a
  soft, indirectly-implied target, not a measured one.

---

## 7. Economic performance

**SOFT — and one figure explicitly corrected from the input hypothesis**

- **Final bank: the evidence supports a much wider range than "$90k–100k."**
  Across all three independent sources in the audit (ROADMAP.md's 6
  episodes, REPLAY_ANALYSIS.md's 2 spot-checks, and a live-ladder data
  point from `ladder_episodes.py`'s commit message), the actually-observed
  range is **roughly $53k to $126k** — more than 2× wide. $90k–100k sits
  inside that band but does not define it; one of the two directly-checked
  episodes finished at ~$53k/$55k, well below $90k. **Do not gate
  validation on $90k–100k specifically** (see §8). If a single number is
  wanted for a rough sanity check, use the wider evidenced band.
- Survival through the day-3–7 cash trough is treated as a **behavioral
  HARD constraint** (not a bank-number target): the reference opponent
  must not let any purchase (land, seed, animal, hire) drop cash low
  enough to miss an animal feed cycle or starve a hire during that window.
  This mirrors our own repo's directly-measured failure mode (`3b8d36f`,
  `85fbbc2`) — a bought asset that then can't be maintained is worse than
  not buying it, and this is the mechanism, not a replay-observed number.
- Intermediate bank trajectory: **not evidenced** beyond the trough-survival
  requirement above and the two purchase days in §1 (which imply cash is
  available again by day 6–7 and day 11). No replay source gives a
  day-by-day bank curve for opponents.

---

## 8. Validation criteria

Restating the input hypothesis list's own validation bullets, each
re-tagged against the audit rather than accepted at face value, per the
instruction not to invent thresholds the evidence doesn't support:

| criterion | tag | as specified in this document |
|---|---|---|
| ~75 tiles | **HARD** | exact target, two-purchase trajectory (§1) |
| ~13–15 crew | **SOFT** | 12–15 range, derived-not-hardcoded (§2) |
| ~8–9 animals | **SOFT** | correlation only, coupled to farm scale (§3) |
| meaningful selling from ~day 10 | **SOFT** | corroborated but n=2 (§6) |
| ~15–48 orders/day | **SOFT, weakly evidenced** | flagged as the weakest numeric claim in the audit — treat as a loose shape, not a bound (§6) |
| no artificial day-22 liquidation cliff | **SOFT (design instruction)** | smooth ramp, not a hard cutoff (§6) |
| survival through the early cash trough | **HARD (behavioral)** | must not starve a maintenance cost during days 3–7 (§7) |
| final bank ~90k–100k | **CORRECTED — SOFT, wider band** | real evidenced range is ~$53k–$126k; $90k-100k is not representative of the low end actually observed (§7) |

**A reference-opponent build should be considered successful if it satisfies
every HARD constraint and falls within the SOFT ranges' broad shape** — not
an exact numeric match on every soft figure. Missing a soft target by a
wide margin is a signal to investigate, not an automatic failure; missing a
HARD constraint (wrong final tile count, starving during the trough, ever
planting TOMATO, never reaching continuous WHEAT) means the opponent isn't
reproducing the structural shape at all and shouldn't be used for
benchmarking until fixed.

---

## Minimal state-machine description

Deliberately **not** a single global day-gated phase machine — ROADMAP.md
argues directly against that shape, and the audit's own evidence (per-crop
windows with different, inconsistently-timed edges) backs that up. Instead:
one coarse **infrastructure** state that only fires twice, plus several
independent **per-crop windows** that overlap it, plus one **selling**
mode that's continuous rather than phase-gated.

```
INFRASTRUCTURE (fires at most twice, not a persistent state)
  day ~6-7  -> BUY_LAND (quadrant 1)     [HARD: exactly one purchase here]
  day ~11   -> BUY_LAND (quadrant 2)     [HARD: exactly one purchase here]
  (no further land purchases; both are one-shot triggers, not a loop)

CREW (continuous, derived every day - not a discrete state)
  crew_target(day) = f(owned_tiles(day), pending_work)
  re-hire toward crew_target every morning
  [HARD invariant: never hire past the point where cash can't survive
   the days-3-7 trough]

ANIMALS (continuous, gated by cash headroom - not a discrete state)
  build pasture / buy animal only if:
    - MAX_ANIMALS not yet reached, AND
    - purchase would not drop cash below the trough-survival reserve
  species: prefer COW, maintain a SHEEP minority (~5-6 : 3 ratio, soft)

CROP WINDOWS (independent per-crop, all active simultaneously - not
sequential phases)
  WHEAT:      active days 0-27+ (continuous)                 [HARD window]
  MELON:      active days 0-(7..11)                          [SOFT edge]
  STRAWBERRY: active days ~5-12                               [SOFT window]
  TOMATO:     never active                                    [HARD: excluded]
  (no CARROT window - evidence doesn't support one, see §4 OMITTED)

SELLING (continuous ramp from ~day 10, no phase transition)
  day 0-~10:  selling light/threshold-driven (shape only, not zero)
  day ~10-29: selling stays elevated - NOT a step function, and NOT
              reset or intensified by a fixed day cutoff
  [SOFT: no day-22 (or any single day) liquidation cliff by construction -
   this is achieved by NOT having a liquidation state at all, rather than
   by tuning a threshold]
```

The key structural decision this encodes: **land and crew-target are the
only true "trigger once" events**; everything else (crop windows, animal
acquisition, selling) is a continuously-evaluated condition, matching the
audit's finding that a single global day-gated phase machine would
mis-model the observed shape.
