# Why does MAX_ANIMALS 4→5 collapse the agent?

Diagnostic only. `main.py`, `pricing.py`, and Peter's route files are
untouched throughout (`git diff --stat -- main.py pricing.py` empty at
every step; Peter's files were only read via `git show` / run from a
`/tmp` scratch copy). No candidate implementation is created — per
instruction, that's gated on explicit approval of this diagnosis.

## Summary of the mechanism, stated up front

**`decide_animal_market_actions` (the function that issues `BUY_ANIMAL`
orders) paces purchases only against the flat `MAX_ANIMALS` ceiling and
cash affordability. It has no concept of "wait until there's somewhere to
put this one."** `choose_animal_to_build` (the function that decides
whether to build a *structure* for an animal) already has exactly that
restraint — `if unfilled > 0 ... return None`, i.e. refuse to build
another structure while any existing one sits empty — but that gate only
governs building, not buying. The two decisions are not paced together.
At `MAX_ANIMALS=4`, this asymmetry rarely bites because there's usually
enough land/crew slack for the animal count to stay roughly in step with
placement capacity. At `MAX_ANIMALS=5`, on the traced seed, it buys a
5th animal on day 0 — hours before any of the land it would need
(`MAX_ANIMALS_ON_HOME_LAND=3` forces animals 4 and 5 onto land not yet
purchased) even exists — and that animal then sits in the shed,
unplaced, for the **entire remaining 29 days of the season**, its full
purchase cost sunk for zero return, while the cash committed to it
collides with the land-purchase/crew-hiring window that used to have
slack to spare.

## 1. Day-by-day trace, MAX_ANIMALS=4 vs 5, vs `starter`, seed 0

`experiments/max_animals_cliff_trace.py` — both configurations run from a
fresh, independent copy of `main.py` (so neither shares module state),
against the same opponent, same seed, logging every action and a state
snapshot every turn.

```
final reward: MAX_ANIMALS=4 -> 76,637   MAX_ANIMALS=5 -> 50,942
```

| day | money (4 / 5) | animals placed (4 / 5) | hands (4 / 5) |
|---|---|---|---|
| 0 | 433 / 460 | {} / {} | 6 / 6 |
| 5 | 11 / 315 | SHEEP2,COW1 / SHEEP1 | 2 / 4 |
| 11 | 5,776 / 320 | SHEEP2,COW1 / **COW2,SHEEP2 (4)** | 12 / 12 |
| 12 | 4,048 / **20** | SHEEP2,COW2 (4) / COW2,SHEEP2 (4) | 12 / 11 |
| **13** | 6,104 / **113** | — | 12 / **12** |
| **14** | 4,968 / **10** | — | 12 / **7** |
| **15** | 3,828 / **10** | — | 12 / **0** |
| 16 | 4,814 / 390 | — | 12 / 9 |
| 18 | 11,468 / 10,201 | — | 12 / 12 |
| 29 (final) | 76,637 / 50,942 | SHEEP2,COW2 (4) / **COW2,SHEEP2 (4)** | 8 / 8 |

**`MAX_ANIMALS=5` never actually places a 5th animal on this seed.** Both
configurations end the game holding exactly 4 placed animals — the extra
purchase bought nothing extra, ever.

**First causal divergence, precisely**: the two trajectories are
structurally identical (same species, same purchase order, same early
land timing) through day 4. **The 5th `BUY_ANIMAL` order fires at day 0,
hour 4** (see section 2) — that is the actual first divergence in
*decisions*, four hours into the game. Its *consequence* doesn't show up
in money/crew until the day 12-15 window, when it collides with the
land-purchase and crew-scaling costs that a healthy MAX_ANIMALS=4 run
absorbs without incident.

## 2. The purchase itself, and where it goes

```
--- MAX_ANIMALS=4 ---
day=0 hour=0 money=3000  BUY_ANIMAL SHEEP
day=0 hour=1 money=2260  BUY_ANIMAL COW
day=0 hour=2 money=1856  BUY_ANIMAL SHEEP
day=0 hour=3 money=1340  BUY_ANIMAL COW
(stops - count_owned_animals has reached MAX_ANIMALS)

--- MAX_ANIMALS=5 ---
day=0 hour=0 money=3000  BUY_ANIMAL SHEEP
day=0 hour=1 money=2260  BUY_ANIMAL COW
day=0 hour=2 money=1856  BUY_ANIMAL SHEEP
day=0 hour=3 money=1340  BUY_ANIMAL COW
day=0 hour=4 money=913   BUY_ANIMAL COW   <-- the extra purchase
```

Direct confirmation the 5th (a COW) sits unplaced, every single day of
the season, extracted from `private["shed"]`:

```
day  1: shed_COW=3  placed={'SHEEP': 1}
day  9: shed_COW=2  placed={'COW': 1, 'SHEEP': 1}
day 12: shed_COW=1  placed={'COW': 2, 'SHEEP': 2}   <- 4th animal placed
day 13-29: shed_COW=1  placed={'COW': 2, 'SHEEP': 2}   <- STUCK. Never changes again.
```

One `COW` (cost ~$400) sits in the shed from day 1 through day 29,
contributing zero `MILK`, zero care-bank accrual, nothing — while its
purchase cost was real, spent, and gone.

## 3. Why this specific animal never gets placed — traced to the exact code asymmetry

`decide_animal_market_actions` (main.py:1373-1424), the function issuing
`BUY_ANIMAL`:

```python
if count_owned_animals(farm, private, board_size) < MAX_ANIMALS:
    ...
    actions.append(["BUY_ANIMAL", animal, 1])
```

`count_owned_animals`'s own docstring: *"bought-but-uncollected (shed),
carried by any unit, and already placed on the board"* — i.e. this gate
only asks "have we bought fewer than `MAX_ANIMALS` in total, anywhere,"
with **no reference to whether a place exists to put the next one.**

Contrast `choose_animal_to_build` (main.py:1297-1372), the function that
decides whether to **build a structure**:

```python
filled, unfilled = scan_animal_structures(farm, board_size)
if unfilled > 0 or pending_builds > 0 or filled >= MAX_ANIMALS:
    return None
```

This one explicitly refuses to build a *second* empty structure while a
*first* sits unfilled — the exact restraint the buying side lacks. And
separately, `MAX_ANIMALS_ON_HOME_LAND=3` (main.py:779) forces the 4th and
5th animal onto land that isn't purchased until `LAND_BUY_START_DAY=6` at
the earliest — so on this seed, animal 5 was bought **six days before any
land existed for it to go on**, while animals 1-4 already occupy every
buildable/affordable slot the crew reaches in time.

**The two decisions are not paced together.** Buying races ahead of
placement capacity by design (there's no check preventing it), and
whether the excess purchase eventually finds a home is a matter of
whether land, crew time, and cash all separately line up before the
season ends — not something the current code arranges deliberately.

## 4. The cash-flow collision, traced precisely

The unplaced animal's sunk cost (~$400-500) is small on its own. The
actual damage shows up when it collides with other costs already
scheduled for the same window:

- `MIN_CASH_RESERVE_FOR_LAND_BUYING=500` — the day ~6-12 land purchase.
- Ongoing crew hiring (fibonacci per-day cost).
- Seed restocking (`MIN_CASH_RESERVE_FOR_SEED_BUYING=450`).

At `MAX_ANIMALS=4`, these already coexist without incident (this is
exactly the trough `MIN_CASH_RESERVE_FOR_SEED_BUYING`'s earlier retune
closed — see `CLAUDE.md`). At `MAX_ANIMALS=5`, the extra ~$400-500
already spent on day 0 removes slack that window depended on, and on
this seed the agent falls into a **second, distinct trough at days
12-17** (money $10-113, vs. $3,828-6,104 for the 4-animal run in the same
window) that the 4-animal configuration does not experience at all. That
trough directly causes the **hands collapse to 0 at day 15** (vs. a
steady 12 for the baseline) — the crew becomes unaffordable to maintain,
which then throttles selling and production for the remainder of the
window shown.

## 5. Cross-checking against a real, competing opponent — and a caution about seat asymmetry

The task asked for heterogeneous-opponent evidence, not just `starter`.
A single seat-0 trace against `route_moon_md` (seed 0) showed the
*opposite* result — `MAX_ANIMALS=5` winning 36,119 to 8,085, with all 5
animals successfully placed by day 11, while the *baseline* (4 animals)
suffered repeated animal **escapes** instead (`SHEEP 2→1`, `COW 1→0`,
multiple times) from its own crew/cash pressure against a genuinely
competing seller. Taken alone, this looked like the cliff might be
opponent-shape-dependent rather than universal.

**It was not representative — verified by re-running properly seat-paired
across 6 seeds**, per `CLAUDE.md`'s own standing caution that identical
code can differ by a few hundred points seat-to-seat, and confirmed here
to matter far more than "a few hundred points" for this specific matchup:

```
experiments/max_animals_5_vs_route_moon_eval.py, main.py vs route_moon_md, 6 seeds, both seats averaged:

seed 0: -3,204   seed 1: +976   seed 2: -30,033   seed 3: -34,059   seed 4: -22,230   seed 5: -13,937
mean delta: -17,081        better on 1/6
```

Once seat asymmetry is controlled for, `MAX_ANIMALS=5` is a net loss
against `route_moon_md` too, consistent in direction and rough magnitude
with the `starter` result (-20,177/12) and the `main.py` head-to-head
result (-18,449/12, already seat-paired by that harness's own design).
**The cliff is not opponent-shape-dependent — it is real and consistent.**
The single seat-0 win is still useful evidence of a different kind,
covered in section 7: it shows that *when* the 5th animal does get
placed, the outcome can be excellent, which is exactly what the
"unpaced purchase, placement is a matter of luck" mechanism predicts.

## 6. Ruling the ten candidate mechanisms in or out, with evidence

| # | mechanism | verdict | evidence |
|---|---|---|---|
| 1 | feed/upkeep cost | **not implicated** | the unplaced animal never gets fed at all (it's never placed) — it costs nothing in upkeep, only in sunk purchase price and cash-flow collision timing (section 4). `MIN_WHEAT_RESERVE_FOR_FEEDING` already scales with *filled* animals only. |
| 2 | animal production timing | **not implicated** | the 4 animals that *do* get placed produce and sell normally (WOOL/MILK sell events continue on schedule in both configurations). |
| 3 | insufficient shed/storage capacity | **minor, secondary** | the stranded animal occupies one shed slot (of 100) for the whole game — real but small on its own. |
| **4** | **product-price depression** | **not the entry point** | no unusual price movement precedes the divergence; the failure is visible in money/hands/placement well before any selling anomaly would show up. |
| **5** | **selling/cash-flow timing** | **primary, confirmed** | section 4: the extra day-0 purchase collides with the day ~6-12 land/crew cash window, producing a second trough the baseline doesn't have. |
| 6 | crew allocation | **downstream consequence, not the cause** | hands collapse to 0 at day 15 *because* cash collapsed first (section 4) — crew size wasn't independently under-provisioned before that. |
| **7** | **land competition** | **primary, confirmed** | `MAX_ANIMALS_ON_HOME_LAND=3` structurally forces animals 4+5 onto land not yet purchased; buying ahead of that land's arrival is exactly what leaves the 5th stranded (section 3). |
| 8 | animal-species composition | **not implicated** | same SHEEP/COW mix and purchase order in both configurations; the extra purchase is simply one more of a species already being bought. |
| 9 | interaction with liquidation | **not implicated** | the whole failure plays out and resolves (or doesn't) well before `LIQUIDATION_START_DAY=19`. |
| 10 | other: **purchase/placement pacing gap** | **the actual root cause** | section 3 — `decide_animal_market_actions` has no placement-capacity gate; `choose_animal_to_build` does. This is the mechanism #5 and #7 both flow from. |

## 7. Why the route-based agents' much larger herds are economically viable — the mechanism, not just the headcount

Per instruction, not inferred from "they have more animals, so more must
be better." From `docs/architecture_comparison.md`'s own reading of the
decoded source: **the route-based agents' entire herd size, species mix,
and build order are baked into a single pre-recorded ~700-step action
schedule**, reconstructed from real games that were actually played out
successfully. Every `BUY_ANIMAL` and `BUILD_PASTURE`/`BUILD_COOP` order
in that schedule already happened at a specific step in a real reference
game where it worked — land was available when the schedule expected it
to be, and a hand was free to carry and place the animal when the
schedule called for it. **The route doesn't need a purchase/placement
pacing gate, because the pacing was already solved, once, by the actual
games it was copied from — it's baked into being a fixed schedule, not
computed live.** `main.py` reactively decides "buy if we're under the cap
and can afford it" every turn, independent of whether the *rest* of the
economy (land, crew, structures) is actually ready to absorb one more
animal — which is exactly the gap section 3 traced. Section 5's single
seat-0 win, where `MAX_ANIMALS=5`'s extra animal *did* get placed
successfully and the game went very well, is consistent with this: the
mechanism that makes bigger herds viable isn't the number 5 itself, it's
placement actually landing in time — the route agents guarantee that by
construction; `main.py` currently leaves it to chance.

## 8. Classification

**A — actionable mechanism identified; enough evidence to design one
narrowly scoped candidate.**

The root cause is precisely located (section 3, two named functions, one
missing condition) and cross-validated across three separate comparisons
(vs. `starter`, vs. `main.py` head-to-head, vs. `route_moon_md` properly
seat-paired) all pointing the same direction. The fix shape this evidence
points to is narrow and mirrors a restraint the codebase already applies
on the *building* side: **pace `BUY_ANIMAL` purchases against placement
capacity, not just against `MAX_ANIMALS` and cash** — e.g., don't buy the
`n`-th animal while an already-bought one is still unplaced, the same way
`choose_animal_to_build` already refuses to build a new structure while
one sits unfilled. This is not proposed or implemented here — per
instruction, that step waits for explicit approval — but it is the
concrete, evidence-backed candidate this diagnosis supports, should it be
approved.

No files were modified besides new diagnostic scripts and this report.
`main.py`, `pricing.py`, and Peter's route files remain untouched. Nothing
merged, nothing submitted. Waiting for approval before any implementation.
