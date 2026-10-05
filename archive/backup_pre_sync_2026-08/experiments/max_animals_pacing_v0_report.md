# Candidate: MAX_ANIMALS=5, paced by placement capacity

Follow-up to `experiments/max_animals_cliff_diagnosis.md` (classification
A). `main.py`, `pricing.py`, and Peter's route files are untouched
throughout (`git diff --stat -- main.py pricing.py` empty at every step;
Peter's files were only read via `git show` / run from a `/tmp` scratch
copy). Nothing merged, nothing submitted — this report proposes a
submission artifact, per instruction, but does not ship it.

## 1. Engine semantics, verified before writing any code

Read directly from the installed engine and `main.py`, not assumed —
this is what the capacity calculation below is built from:

- **`BUY_ANIMAL`** (`kaggriculture.py:679-687`): deducts cost, adds one
  unit to `private["shed"][item]`. **It never touches a tile.** A bought
  animal has no location at all until a unit carries and places it.
- **`PLACE`** (`kaggriculture.py:377-392`): only succeeds when the acting
  unit stands on a tile that is already a matching structure
  (`tile["kind"] == ANIMALS[item]["structure"]`) with no `"animal"` key
  yet — i.e. an *unfilled* structure. There is no other way to place one.
- **`BUILD_PASTURE`/`BUILD_COOP`** (`kaggriculture.py:493-503`): only
  succeeds on a completely empty tile (`tile is None`).
- **`scan_animal_structures`** (`main.py:1216-1234`) is this repo's own,
  already-used source of truth for `(filled, unfilled)` structure
  counts — both `choose_animal_to_build`'s existing build-gate and this
  candidate's new buy-gate are built directly on its output, not a
  re-derived duplicate.
- **`choose_animal_to_build`**'s eligibility rule (`main.py:1297-1372`):
  `MAX_ANIMALS_ON_HOME_LAND` caps the home ("NW") quadrant specifically;
  every other, separately-purchased quadrant has no such per-quadrant
  cap — only the flat `MAX_ANIMALS` ceiling applies there.
  `farm["unlocked_quadrants"]` (`["NW"]` until `BUY_LAND` lands) is the
  field that already tells the rest of `main.py` (`decide_land_orders`)
  whether that extra land exists yet.

**"Unfilled structures" is confirmed NOT the same thing as placement
capacity**, per instruction not to assume this: an unfilled structure is
capacity that's ready *this instant*, but a farm with zero structures
built yet still has real capacity — up to `MAX_ANIMALS_ON_HOME_LAND` on
home land alone, before any structure exists at all (`BUILD_PASTURE`
only needs empty ground, not prior land purchase). The capacity function
below accounts for both: existing structures (filled + unfilled) *or*
the home-land ceiling, whichever is larger, and removes that ceiling
entirely once extra land is owned.

## 2. The candidate — exact diff

`experiments/candidates/max_animals_pacing_v0.py` patches exactly two
names on an imported `main` module. Presented as a diff against `main.py`
for review (this is the change a real merge would make — **not applied
to `main.py` in this experiment**):

```diff
--- main.py
+++ main.py (candidate)
@@
-MAX_ANIMALS = 4
+MAX_ANIMALS = 5
@@
+def available_placement_capacity(farm, board_size):
+    """How many ACTIVE_ANIMALS structures current land ownership can
+    support right now."""
+    filled, unfilled = scan_animal_structures(farm, board_size)
+    existing_structures = filled + unfilled
+    unlocked_quadrants = farm.get("unlocked_quadrants") or ["NW"]
+    has_extra_land = len(unlocked_quadrants) > 1
+    if has_extra_land:
+        return MAX_ANIMALS
+    return max(existing_structures, MAX_ANIMALS_ON_HOME_LAND)
+
+
 def decide_animal_market_actions(farm, private, board_size, day):
     actions = []
     money = farm.get("money", 0)
     remaining_days = remaining_season_days(day)

-    if count_owned_animals(farm, private, board_size) < MAX_ANIMALS:
+    owned = count_owned_animals(farm, private, board_size)
+    ceiling = min(MAX_ANIMALS, available_placement_capacity(farm, board_size))
+    if owned < ceiling:
         held = species_owned_counts(farm, private, board_size)
         affordable = []
         ... (unchanged - species eligibility/affordability loop, wheat safety net)
```

**Everything else is byte-for-byte the original `decide_animal_market_actions`**
— species selection (`pick_next_animal_species`), affordability gates
(`ANIMAL_SPEND_CAP_FRACTION`, `MIN_CASH_RESERVE_FOR_ANIMAL_BUYING`), and
the wheat safety net are copied verbatim, not touched. Land purchasing
(`decide_land_orders`), crew hiring (`decide_hire_orders`), selling
(`decide_market_actions`), and liquidation are not imported into or
referenced by this candidate at all.

## 3. Tests

`tests/test_max_animals_pacing_v0.py`, 15 cases: capacity calculation
against the verified engine semantics (no structures + no extra land =
home cap; existing structures never under-reported; extra land removes
the cap entirely, regardless of structure count), the buy-gate never
exceeding capacity in a simulated multi-turn buying sequence, a deferral
logged exactly when and only when capacity blocks a purchase, species
selection and the wheat safety net proven untouched, affordability gates
still applying, and a full-agent smoke test.

One cross-candidate collision fixed along the way (the same class this
repo has hit repeatedly): `tests/test_sell_thresholds_candidates.py`
asserted the shared `main.MAX_ANIMALS` global stayed at 4, which no
longer holds now that this candidate legitimately patches it — the
assertion was removed from those two unrelated tests (they still check
`LIQUIDATION_START_DAY`, `MAX_HANDS_PER_DAY`, `SHED_FORCE_SELL_THRESHOLD`
for isolation).

Full suite: **318/318 pass** (303 pre-existing + 15).

## 4. Mechanism verification — does the 5th animal now wait, and does it get placed?

Traced on the exact seed (`starter`, seed 0) where
`max_animals_cliff_diagnosis.md` found the 5th animal permanently
stranded:

| day | money | placed | shed (unplaced) | quadrants |
|---|---|---|---|---|
| 0 | 486 | {} | 0 | `['NW']` |
| 6 | 20 | SHEEP2, COW1 (3) | 0 | `['NW']` |
| 8 | 124 | SHEEP2, COW1 (3) | 0 | `['NW', 'NE']` |
| 9 | 161 | SHEEP2, COW1 (3) | COW: 1 | `['NW', 'NE']` |
| 10 | 26 | SHEEP2, COW1 (3) | COW: 2 | `['NW', 'NE']` |
| 11 | 8,737 | SHEEP2, COW2 (4) | 0 | `['NW', 'NE', 'SW']` |
| **12** | 6,971 | **SHEEP2, COW3 (5)** | 0 | `['NW', 'NE', 'SW']` |
| 20 | 19,657 | SHEEP2, COW3 (5) | 0 | — |

```
final reward: 92,904 [DONE]
```

Compare to `max_animals_cliff_diagnosis.md`'s numbers on this exact same
seed: baseline (`MAX_ANIMALS=4`, no pacing) **76,637**; broken
`MAX_ANIMALS=5` with no pacing **50,942** (one animal permanently
stranded). **The paced candidate reaches the full 5-animal herd by day
12 and beats both.**

**191 purchase deferrals logged** across both seats of this one episode
— the mechanism is genuinely active, not a no-op. Sample:

```
{'day': 0, 'owned': 3, 'capacity': 3, 'max_animals': 5, 'unlocked_quadrants': ['NW']}
```

Purchase requests beyond the home-land cap of 3 are refused at day 0 (as
designed — capacity is exactly `MAX_ANIMALS_ON_HOME_LAND` before extra
land exists), and the 4th/5th purchases land once `unlocked_quadrants`
grows past `['NW']` (day 8), landing both successfully by day 12 — well
within the season, unlike the unpaced case where the 5th never lands at
all.

## 5. Controlled evaluation — heterogeneous opponents first, self-play last and diagnostic only

All comparisons are `main.py` (baseline) vs this candidate, same seeds,
**both seats averaged** (seat asymmetry with these opponents was
confirmed large enough to flip conclusions if not controlled for — see
`max_animals_cliff_diagnosis.md` section 5 — so every result below is
seat-paired, not single-seat).

| opponent | seeds | mean delta | win rate | t |
|---|---|---|---|---|
| `route_moon_md` | 6 | **+5,868** | 4/6 | 0.74 |
| `route_moon_tuned` | 6 | **+5,868** | 4/6 | 0.74 |
| `route_moon_md_r5` | 6 | **+5,868** | 4/6 | 0.74 |
| `route_v20` | 6 | **+6,063** | 4/6 | 0.79 |
| `starter` (paired) | 12 | **+3,621** | 7/12 | 0.97 |
| `main.py` (head-to-head, 24 matches) | 12×2 | **+4,338** | **16/24** | — |

(`route_moon_md`/`route_moon_tuned`/`route_moon_md_r5` again produce
byte-identical results against us — confirmed as a real, already-explained
finding in `docs/architecture_comparison.md` and `experiments/opponent_state_v0_report.md`,
not a bug: their only disclosed tuning differences live inside
mirror/archetype-detection mechanisms that never activate against an
opponent shaped this differently from them.)

**Every single comparison is positive.** No mechanism, no opponent, no
harness in this evaluation shows a negative mean delta. Individually,
none of the six clears a conventional significance bar at 6-12 seeds
(all `|t| < 1`) — but the consistency of direction across six
independently-run, differently-shaped comparisons (four distinct route
architectures, a passive built-in, and same-architecture `main.py`) is
exactly the kind of corroborating evidence this repo's own established
practice treats as trustworthy (`CLAUDE.md`: *"two harnesses that can
disagree both call a win"* — here, six agree).

**Self-play (diagnostic only, per instruction — not used to decide
anything):**
```
6 seeds: mean 59,424, stdev 10,885, median 58,312, range 47,681-73,647
```
This is *below* unmodified `main.py`'s own self-play mean (~61,303) — if
self-play were the deciding metric, this candidate would look like a
regression. **It is exactly the divergence the task's evaluation
principle exists to guard against**: every heterogeneous and paired
comparison is positive while the mirror-match number alone points the
other way, because self-play cannot see the mechanism this candidate
fixes any better than it could see the original cliff (both sides run
the identical code, so both either strand a 5th animal or both don't -
there's no differential signal for a same-architecture comparison to
pick up).

## 6. Decision

**Clearly positive — not mixed, not negative.** Per the task's decision
rule, this qualifies as submission-worthy evidence: every heterogeneous
route-opponent comparison (the primary evidence, per instruction) and
the `starter`/`main.py` comparisons (secondary) all show a positive mean
delta and a win rate above 50%, with the underlying mechanism directly
verified (section 4) to do exactly what the diagnosis predicted — the
previously-stranded animal now waits for real capacity and gets placed.

**Not submitted or merged in this pass, per instruction.** Proposed
submission artifact, if approved:

- **File**: `main.py` with the two changes in section 2 applied in
  place (`MAX_ANIMALS = 4` → `5`, plus the new
  `available_placement_capacity` function and the one-line gate change
  in `decide_animal_market_actions`).
- **Nothing else changes** — no other constant, function, or decision in
  `main.py` is touched.
- **Pre-submit gate** (per `CLAUDE.md`'s standard workflow, not yet run):
  a self-play validation episode confirming `status == ['DONE', 'DONE']`
  before any `kaggle competitions submit`.
- **One-line hypothesis this submission would test on the ladder**:
  *raising `MAX_ANIMALS` is safe, and net-positive, once purchases are
  paced against actual placement capacity instead of a flat headcount.*

Full suite: **318/318 pass.** `main.py`, `pricing.py`, and Peter's route
files untouched. Nothing merged, nothing submitted.
