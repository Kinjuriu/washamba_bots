# Checkpoint V2 — sheep, denser crew, demand-aware scoring

**Frozen. Never edit this file.** If a number here turns out to be wrong, note the
correction in the *next* checkpoint — other people's comparisons refer to these
figures.

| | |
|---|---|
| **Commit** | `93d6bed` |
| **Date frozen** | 2026-08-16 |
| **Supersedes** | [V1 baseline](V1-baseline.md) (`df69f97`) |
| **Agent** | `nikaangukia_meroni` (deterministic, rule-based) |
| **Engine** | `kaggle-environments` 1.32.7 |
| **Python** | 3.13.7 |

## What changed since V1

Three strategy changes, each measured head-to-head **on its own** before being
stacked, plus two teammates' branches merged.

| change | delta | wins |
|---|---|---|
| `ACTIVE_ANIMALS` GOOSE → SHEEP | +1,332 | 15/16 |
| `WORK_TILES_PER_HAND` 6 → 4 | +1,910 | 16/16 |
| demand-aware `choose_crop` | +3,358 | 14/16 |
| **combined, vs V1** | **+12,698** | **14/16** |

- **Sheep.** The `CARE` bank accrues +1 per fed-and-cared day and pays out in full
  on the next production day, so a *longer* interval banks a bigger payout: a goose
  collects 2 units an event, a sheep 4, at four times the price. `WOOL` needed its
  own `SELL_PRICE_THRESHOLDS` and `MAX_SELL_PER_TURN` entries.
- **Crew.** Previously recorded as a dead end; that was judged against the
  across-seed stdev on a much older agent. The farm waters 19.2 tiles a day against
  24 planted, so hands were the right lever.
- **Demand.** `choose_crop` divides our own pipeline by market absorption **plus the
  demand that will still arrive**, read live from `obs["town"]["unlocked_shops"]`.
- **Billy's `choose_animal_to_build`** (PR #10) — season-maturity gate for animals,
  and species selection. `MAX_ANIMALS` stays at 1.
- **Steff's `pricing.py`** (PR #11) — research module, not wired into `main.py`.

## Self-play — the headline number

8 seeds, `experiments/selfplay_bench.py 8`.

| | |
|---|---|
| **mean** | **35,583** |
| stdev (as reported) | 3,678 |
| min | 28,362 |
| max | 41,149 |

Mean end price: `WHEAT 48 · CARROT 62 · TOMATO 190 · STRAWBERRY 241 · MELON 24`

Sold mix (player 0): `MELON 1304 · FERTILIZER 835 · STRAWBERRY 507 · WOOL 272 · CARROT 171 · WHEAT 111`

**Read that stdev with care.** The script pools both players' banks into one sample
set, but in a mirror match they are near-perfectly correlated — 4 of the 5 gate
seeds below return *byte-identical* banks for both sides. So the effective sample
is ~8, not 16, and the reported stdev overstates precision. V1's figure has the
same flaw; the two remain comparable to each other.

**Melon still finishes at 24 against a base of 250.** V2 did not fix that.

## Seeded batch vs the built-ins

12 seeds per opponent.

| vs | mean | stdev | min | max | wins | escapes |
|---|---|---|---|---|---|---|
| `pass` | 51,477 | ±3,400 | 45,312 | 55,562 | 12/12 | 0 |
| `random` | 51,123 | ±3,067 | 44,926 | 54,715 | 12/12 | 0 |
| `starter` | 51,358 | ±3,582 | 45,399 | 56,318 | 12/12 | 0 |

**Inflated — do not quote as our strength.** These opponents never sell, so the
market never faces a competitor. The ~16,000 gap against self-play is the point.

## Validation gate

Self-play, seeds 0–4, both sides `main.py`. **PASS** — all five `['DONE', 'DONE']`.

| seed | banks |
|---|---|
| 0 | 36,027 / 36,027 |
| 1 | 36,736 / 36,736 |
| 2 | 28,362 / 28,362 |
| 3 | 34,979 / 34,979 |
| 4 | 33,920 / 34,062 |

## Behavioural diagnostics

Seed 0 vs `starter`. Final bank **47,310**, matching the seeded batch for that seed.

| end-of-season | |
|---|---|
| weeds | **0** |
| animals alive | 1 |
| overage bank left | **60 of 60 s** |

Actions: `WEST 936 · PASS 829 · NORTH 709 · WATER 559 · PLANT 304 · EAST 303 ·
SOUTH 225 · HARVEST 115 · PICKUP 48 · DIG 33 · CARE 30 · FEED 30 ·
COLLECT_FERTILIZER 29 · FERTILIZE 18 · BUILD_PASTURE 1`

Sold: `MELON 183 · FERTILIZER 62 · STRAWBERRY 43 · WOOL 34 · CARROT 34`

`FEED 30` / `CARE 30` across 30 days is the intended once-daily cadence, and
**0 weeds** means the denser crew is keeping every tile alive — V1 finished with 2.

**`PASS` rose from 414 to 829.** The extra hands still paid for themselves, but
they idle roughly half the time they are on the field. That is the clearest
remaining inefficiency in the agent, and it is a routing problem, not a headcount
one.

Sold counts are *submitted* order quantities, not confirmed fills — the engine
silently drops market orders past 10 per turn, so treat them as an upper bound.

## Tests

**108 passing** (84 agent + 24 pricing). Animal tests derive species and structure
from `ACTIVE_ANIMALS` rather than hard-coding, so a species change no longer breaks
them.

## Kaggle

| | |
|---|---|
| Active submission | **55555766** at **603.8** |
| Control submission | 55551524 at 469.9, unchanged and deliberately kept |
| Team rank | 2,915 of 4,758 |
| Leaderboard median | 743 — we are still below it |

The +134 gap over an unchanged control is the first time a change has been visible
above the ±120 rating drift. The submission corresponds to this `main.py`
(byte-identical since `fca6d4b`), inferred from timestamp ordering and description
rather than a verified upload hash.

## Known limitations

- **Below the leaderboard median** (743). Top quartile is 1,649 — 3.1× away.
- **Melon oversupply is unsolved.** It appears in no town shop, so its only sink is
  ~30 units a season and we still sell ~183. The demand term pays but did *not*
  reduce melon volume (179 → 183); it moved carrot into strawberry. The mechanism
  behind the gain is therefore unconfirmed.
- **829 idle `PASS` turns** with the denser crew.
- **~43 unit-turns a season lost to blocked `PLANT` requests** — no per-turn seed
  budget.
- One animal only; more than one loses heavily, including two different species.
- No opponent modelling, lookahead, or multi-turn planning.

## What is not included

- `pricing.py` is **not** wired into `main.py`; it is research only.
- `BUY_LAND` — measured against, with a mechanism: we under-water what we own.
- COW (measured, +606 vs sheep's +1,332), and any second animal.
- Any LLM component.

## Reproducing

```bash
git checkout 93d6bed
.venv/Scripts/python.exe -m unittest discover -s tests      # 108 tests
.venv/Scripts/python.exe experiments/selfplay_bench.py 8
.venv/Scripts/python.exe experiments/seeded_batch.py
```

To compare a change against this checkpoint see [../CHECKPOINTS.md](../CHECKPOINTS.md)
— `paired_compare.py` for farm-side changes, `head_to_head.py` for anything about
selling, and never judge a delta against the across-seed stdev.
