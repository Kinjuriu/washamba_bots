# Fix Plan: Seed Budget (3b) + Tomato Fertilizer Bonus (3a)

*Frozen V2-baseline: commit `93d6bed`, self-play mean 35,583. Every change below is measured against that checkpoint via `paired_compare.py` or `selfplay_bench.py`, never a single episode.*

---

## Order of operations

1. **Fix A: Per-turn seed budget** — pure bug fix, more urgent now (denser crew).
2. **Fix B: Tomato fertilizer bonus** — builds on clean seed-budget foundation.
3. *(Follow-up)* Strawberry fertilizer bonus — once tomato results are in.

The fertilizer off-by-one from an earlier plan is **already fixed in current `main.py`** (`wants_fertilizer` line 424, documented at lines 397–405). It is not repeated here.

---

## Out of scope (valid, scheduled later)

These are real inefficiencies confirmed in V2. They are intentionally not
included in this plan to keep each change isolated and measurable.

- **Idle-crew routing (3d).** `PASS` rose from 414 (V1) to 829 (V2) with the
denser crew. The priority ladder + `find_nearest_target("any")` fallback
leaves hands idle once urgent work is claimed. This is a routing redesign,
not a headcount question (4 tiles/hand is correct). Next priority after
Fix B lands.

- **pricing.py integration.** Steff's forward-pricing module (`tests/test_pricing.py`,
24 tests) is not imported by `main.py`. Wiring it into `decide_market_actions()`
is a research→engineering pass that needs its own benchmark cycle. Not
blocked on A or B; can proceed in parallel by whoever owns it.

---

## What changed since V1

V2 (`93d6bed`) shipped three measured changes:

| change | delta | wins |
|---|---|---|
| `ACTIVE_ANIMALS` GOOSE → SHEEP | +1,332 | 15/16 |
| `WORK_TILES_PER_HAND` 6 → 4 | +1,910 | 16/16 |
| demand-aware `choose_crop` | +3,358 | 14/16 |
| **combined** | **+12,698** | **14/16** |

Self-play mean: **35,583** (was 28,212). Built-ins inflated to ~51,000. Leaderboard: 603.8, still below median (743).

This plan updates the FIX.md baseline from V1 to V2 and adjusts the fertilizer guard for the new animal species.

---

## Fix A: Per-turn seed budget (SETUP_PLAN 3b)

### Root cause

`seeds` is a static snapshot from `private`, taken once per turn in `nikaangukia_meroni`. Every unit (farmer + each hand) independently checks `seeds.get(crop, 0) > 0` against that **same, unchanged snapshot**. Nothing decrements it as units "spend" seeds.

If you hold 2 wheat seeds and 4 units all reach the PLANT step, all 4 emit `["PLANT", "WHEAT"]`. The engine drops **all** requests for a crop when turn demand exceeds held supply — not a partial fill.

### Why this is more urgent in V2

`WORK_TILES_PER_HAND` dropped from 6 → 4, so the crew is denser. More units acting per turn means **more overcommitting** on the same thin seed stock. The V1 figure of ~43 wasted unit-turns/season was against a sparser crew. The actual waste in V2 is likely higher.

### Mechanism

Add a mutable `seed_budget` dict, same coordination pattern already used for:
- `claimed` — prevents double-work on tiles
- `pending_builds` — prevents double-building
- `feed_claimed` — prevents double-feeding

```python
# nikaangukia_meroni(), once per turn, alongside claimed/pending_builds/feed_claimed:
seed_budget = dict(private.get("seeds", {}))  # mutable copy, decremented per PLANT

# Pass through choose_farmer_action -> choose_unit_action
# In choose_unit_action(), PLANT step (currently line 1446-1448):
if crop and seed_budget.get(crop, 0) > 0:
    seed_budget[crop] -= 1
    return act_here(["PLANT", crop])
```

### Signature changes

| Function | New param | Default |
|---|---|---|
| `choose_farmer_action` | `seed_budget=None` | `None` |
| `choose_unit_action` | `seed_budget=None` | `None` |

All call sites update:
- `nikaangukia_meroni`: create `seed_budget`, pass to `choose_farmer_action` and each `choose_unit_action` call
- Tests: every test that calls `choose_farmer_action` or `choose_unit_action` directly needs the new param (or accept the `None` default, which falls back to the old behavior for backward compatibility)

### Test to add

```python
def test_seed_budget_prevents_overcommitting_plants(self):
    # Two units, one wheat seed: only one may PLANT.
    tiles = [
        [None, None],  # (0,0) and (1,0) both empty
    ]
    private = {"seeds": {"WHEAT": 1}, "shed": {}, "inventories": [{}]}
    state = self._state(tiles, board_size=2, farmer=(0, 0), hands=[(1, 0)], private=private)

    seed_budget = {"WHEAT": 1}
    claimed = set()

    first = choose_unit_action(state, 0, 0, 0, claimed, seed_budget=seed_budget)
    second = choose_unit_action(state, 1, 0, 1, claimed, seed_budget=seed_budget)

    plant_actions = [a for a in [first, second] if a == ["PLANT", "WHEAT"]]
    self.assertEqual(len(plant_actions), 1, "only one unit should get the single seed")
    self.assertEqual(seed_budget["WHEAT"], 0, "budget should be exhausted")
```

### Measurement

- `paired_compare.py` against V2-baseline (`93d6bed`). This is a planting/movement change — not a selling change — so `paired_compare.py` is the right harness.
- Expectation: small but consistent gain. Recovered unit-turns should translate to more watering/harvesting.
- Diagnostic: pull action histogram from `replay_diagnostics.py` and confirm fewer `PLANT` attempts relative to `PLANT` successes.

### Risk

Very low. Pure bookkeeping, no logic changes. If it breaks, tests fail or `DONE/DONE` breaks.

---

## Fix B: Tomato fertilizer bonus in `choose_crop` (SETUP_PLAN 3a)

### Root cause

`choose_crop()` scores by `price * expected_yield * glut_discount * self_supply_discount / growth_days`. Fertilizer's best target — tomato (interval=1, 3 production ticks per 3-day cover) — gets zero score boost for being fertilizable. Under normal market conditions, tomato never outranks strawberry or melon.

V2-baseline records: **0 tomato sold every season**. Fertilizer only hits strawberry.

### Engine metadata (for reference)

| Crop | seed | first_yield | max_yield_day | interval | max_yield | ongoing |
|---|---|---|---|---|---|---|
| WHEAT | 10 | 2 | 4 | 0 | 6 | False |
| CARROT | 20 | 2 | 3 | 0 | 4 | False |
| **TOMATO** | **50** | **8** | **8** | **1** | **4** | **True** |
| **STRAWBERRY** | **100** | **10** | **10** | **2** | **4** | **True** |
| MELON | 80 | 10 | 12 | 0 | 6 | False |

A 3-day fertilizer application catches production ticks within `[apply_day, apply_day+2]`:
- **Tomato** (interval=1): ticks at ages 7, 8, 9, 10 -> one well-timed app catches **3 ticks** -> **+3 units**
- **Strawberry** (interval=2): ticks at ages 9, 11, 13, 15 -> one app catches **2 ticks** -> **+2 units**

### Mechanism

Add tunable fertilizer bonus constants and a guard that only boosts when fertilizer access is reliable:

```python
# New constants (tunable via paired_compare.py)
FERTILIZER_BONUS_TOMATO = 3
FERTILIZER_BONUS_STRAWBERRY = 2  # reserved for follow-up; tomato-only in this fix

def _has_fertilizer_access(farm, private):
    # True if fertilizer is or will soon be reliably available.
    # V2: ACTIVE_ANIMALS = ["SHEEP"], not hardcoded "GOOSE".
    shed_fert = (private.get("shed") or {}).get("FERTILIZER", 0)
    carried_fert = sum(
        (inv or {}).get("FERTILIZER", 0)
        for inv in (private.get("inventories") or [])
    )
    has_animal = any(
        isinstance(tile, dict) and tile.get("animal") in ACTIVE_ANIMALS
        for row in (farm.get("tiles") or [])
        for tile in (row or [])
    )
    return shed_fert > 0 or carried_fert > 0 or has_animal
```

In `choose_crop()`, after computing `expected_yield`:

```python
expected_yield = crop_info.get("max_yield", 0)

# Fertilizer bonus: only for fertilizable crops when access is reliable
if crop in FERTILIZABLE_CROPS and _has_fertilizer_access(farm, private):
    if crop == "TOMATO":
        expected_yield += FERTILIZER_BONUS_TOMATO
    # STRAWBERRY follow-up: elif crop == "STRAWBERRY": expected_yield += FERTILIZER_BONUS_STRAWBERRY

score = price * expected_yield * glut_discount * self_supply_discount / growth_days
```

### Why the animal check matters (V2 update)

V2 uses `ACTIVE_ANIMALS = ["SHEEP"]`. The guard must not hardcode "GOOSE" — it needs to check membership in `ACTIVE_ANIMALS` so the bonus works regardless of which species is active. Without the guard, the bonus flickers on/off as shed inventory empties and refills, causing erratic crop switching mid-season. A placed animal is a reliable signal: fertilizer starts flowing from day 4 and continues for the rest of the season.

### Current vs adjusted scoring (at baseline market, no glut)

| Crop | Current score | With tomato bonus | Change |
|---|---|---|---|
| Melon | 250 * 6 / 12 = **125** | 125 | — |
| Strawberry | 120 * 4 / 10 = **48** | 48 | — |
| **Tomato** | 60 * 4 / 8 = **30** | 60 * 7 / 8 = **52.5** | **+75%** |
| Carrot | 35 * 4 / 3 = 46.7 | 46.7 | — |
| Wheat | 25 * 6 / 4 = 37.5 | 37.5 | — |

Tomato is now competitive with strawberry. In a market where strawberry is oversupplied (`glut_discount ~ 0.7`) and tomato is at baseline:
- Strawberry: 48 * 0.7 = **33.6**
- Tomato: 52.5 * 1.0 = **52.5** <- wins

This is the crossover: tomato becomes a viable diversification play when melon/strawberry are flooded, which is exactly when the self-play market needs it.

### Measurement

1. `paired_compare.py` against V2-baseline (`93d6bed`) — this is a planting change.
2. `selfplay_bench.py` to confirm it does not crash the melon market harder.
3. Key metric: **sold mix must show TOMATO > 0**. If tomato still sells 0, the bonus is too small or the guard too strict.
4. Watch melon end-price: if it drops below ~20 (from current ~24), the bonus may be pulling too many unit-turns away from melon upkeep.

### Risk

Medium. Changes what gets planted, which changes the whole season trajectory. Could backfire if:
- The bonus overvalues tomato and it steals too many unit-turns from melon watering
- The guard fires too early (pre-animal-placement) and the agent plants tomato before fertilizer is available

Mitigation: `FERTILIZER_BONUS_TOMATO` is a tunable constant. If `paired_compare.py` shows a loss at 3, try 2 or 1 before abandoning the approach.

### Follow-up: Strawberry bonus

Once tomato results are in, apply the same pattern to strawberry with `FERTILIZER_BONUS_STRAWBERRY = 2`. This makes strawberry slightly more competitive vs melon, further diversifying the crop mix. Do not ship both bonuses in the same PR — isolate the tomato effect first.

---

## V2-specific notes

- `choose_crop` signature in V2: `choose_crop(farm, market_state, private, day, town=None)`. Any direct test calls need the `town` param.
- `choose_animal_to_build` is new in V2 and replaces the direct `ACTIVE_ANIMALS[0]` lookup for structure building. It does not affect our fixes but the PLANT step now calls `choose_animal_to_build(farm, board_size, day, pending_builds[0])` before `choose_crop`.
- `WORK_TILES_PER_HAND = 4` means more units per tile of work, amplifying the seed-budget waste. Fix A is higher priority than it was against V1.

---

## Implementation checklist

### Fix A (seed budget)
- [ ] Add `seed_budget` parameter to `choose_farmer_action` and `choose_unit_action`
- [ ] Create `seed_budget = dict(private.get("seeds", {}))` in `nikaangukia_meroni`
- [ ] Pass `seed_budget` through all call sites
- [ ] Decrement `seed_budget[crop]` in `choose_unit_action` PLANT step
- [ ] Add `test_seed_budget_prevents_overcommitting_plants`
- [ ] Run full test suite: `python -m unittest discover -s tests` (expect 108 passing)
- [ ] Run `paired_compare.py` against V2-baseline (`93d6bed`)
- [ ] PR, announce in team channel, keep one control submission slot

### Fix B (tomato bonus)
- [ ] Add `FERTILIZER_BONUS_TOMATO` constant
- [ ] Add `_has_fertilizer_access()` helper with `ACTIVE_ANIMALS` membership check
- [ ] Modify `choose_crop()` to apply bonus when guard is true
- [ ] Run full test suite
- [ ] Run `paired_compare.py` against V2-baseline
- [ ] Run `selfplay_bench.py` — confirm TOMATO > 0 in sold mix, melon end-price stable
- [ ] PR, announce in team channel

### Follow-up (strawberry bonus)
- [ ] Add `FERTILIZER_BONUS_STRAWBERRY = 2`
- [ ] Extend `choose_crop()` to apply strawberry bonus
- [ ] Same measurement pipeline as Fix B
- [ ] PR

---

## Dead ends to avoid (already documented in CLAUDE.md)

- Do not attempt `BUY_LAND` — tested twice, lost twice.
- Do not attempt more animals (2/3/4/6 or mixed species) — tested, all lost.
- Do not attempt melon throttling/diversification — three attempts, all lost badly.
- Do not judge a delta against across-seed stdev (~3,600 in V2). Use paired difference.

---

## References

- `docs/checkpoints/V2-sheep.md` — current metrics, known limitations
- `docs/checkpoints/V1-baseline.md` — predecessor
- `docs/CHECKPOINTS.md` — workflow, harness selection
- `CLAUDE.md` — engine mechanics, measured dead ends, axis-flip warning
- `SETUP_PLAN.md` — prioritized backlog (3a-3c)
