# Checkpoint V1 — baseline

**Frozen. Never edit this file.** If a number here turns out to be wrong, note
the correction in the *next* checkpoint — other people's comparisons refer to
these figures.

| | |
|---|---|
| **Commit** | `df69f97` |
| **Measured at** | `d88e225595251a1920590e0e3b13ba62cdd57d60` |
| **Date frozen** | 2026-08-16 |
| **Agent** | `nikaangukia_meroni` (deterministic, rule-based) |
| **Engine** | `kaggle-environments` 1.32.7 |
| **Python** | 3.13.7 |

The measurements were taken at `d88e225`. The two commits differ only in
comments and documentation — `git diff d88e225 df69f97 -- main.py` contains no
executable change — so the numbers below describe this checkpoint.

## What it is

Deterministic agent, one shared 13-step priority ladder driving the main farmer
and every hired hand, coordinated by a per-turn claim set.

- **Crop economics** — crops scored on revenue per growing day, discounted by
  market glut relative to the engine's `I0` baseline and by our own incoming
  supply.
- **Labour** — up to four hands re-hired each morning; the fibonacci hire cost
  resets daily, so a full crew is about $7/day.
- **One goose** — coop, buy/pickup/place, fed and cared for **daily**, eggs
  harvested, fertilizer collected, with a two-unit wheat reserve held back so
  selling feed can never starve it.
- **Fertilizer** — applied to ongoing crops (tomato, strawberry) inside the
  window where the three-day cover still catches production ticks. Supplied
  free by the goose; the agent buys none for crop use.
- **Liquidation from day 19** — everything in the shed sells regardless of
  price from then on, because inventory scores nothing at turn 720.

## Self-play — the headline number

8 seeds, 16 agent-results, `experiments/selfplay_bench.py 8`.

| | |
|---|---|
| **mean** | **28,212** |
| stdev | 1,683 |
| min | 25,017 |
| max | 31,158 |

Mean end price: `WHEAT 48 · CARROT 56 · TOMATO 154 · STRAWBERRY 245 · MELON 25`

Sold mix (player 0): `MELON 1141 · FERTILIZER 926 · EGG 416 · STRAWBERRY 319 · CARROT 302 · WHEAT 231`

Melon finishing at **25** against a base of 250 is the signature of two agents
flooding the same market — it ends near 280 against a built-in opponent. This
is the number that predicts ladder placement.

## Seeded batch vs the built-ins

12 seeds per opponent, `experiments/seeded_batch.py`.

| vs | mean | stdev | min | max | wins | escapes |
|---|---|---|---|---|---|---|
| `pass` | 43,322 | 2,995 | 38,165 | 48,208 | 12/12 | 0 |
| `random` | 44,570 | 1,547 | 42,059 | 47,466 | 12/12 | 0 |
| `starter` | 44,429 | 2,460 | 41,060 | 48,053 | 12/12 | 0 |

**These numbers are inflated and must not be quoted as our strength.** `pass`
and `random` never sell at all and `starter` sells minimally, so the market
stays pristine and our prices never meet a competitor. The ~16,000 gap against
self-play is the whole reason a 40,000 local score becomes a ~500 ladder
rating.

## Validation gate

Self-play, seeds 0–4, both sides `main.py`. **PASS** — every seed returned
`['DONE', 'DONE']`.

| seed | banks |
|---|---|
| 0 | 27,046 / 27,200 |
| 1 | 28,732 / 28,732 |
| 2 | 25,356 / 25,017 |
| 3 | 27,635 / 27,635 |
| 4 | 29,402 / 29,402 |

## Behavioural diagnostics

Seed 0 vs `starter`. Final bank **41,680**, matching the seeded batch for that
seed — reproducible.

| end-of-season | |
|---|---|
| weeds | 2 |
| animals alive | 1 |
| plants standing | 1 |
| SELL orders issued | 177 |

Actions: `WEST 765 · NORTH 605 · WATER 575 · PASS 414 · EAST 316 · SOUTH 233 ·
HARVEST 149 · PLANT 132 · PICKUP 42 · CARE 30 · FEED 30 ·
COLLECT_FERTILIZER 29 · DIG 20 · FERTILIZE 9`

Sold: `MELON 183 · FERTILIZER 137 · CARROT 57 · EGG 52 · STRAWBERRY 27 · WHEAT 1`

`FEED 30` and `CARE 30` across a 30-day season is the intended once-daily
cadence. **2 weeds** at season end means the crew kept up with tile upkeep —
an earlier agent finished at 23 of 25 tiles dead.

## Timing headroom

`remainingOverageTime` at turn 720: **60 of 60 seconds** — the entire episode
bank untouched. The limit is 1 second per turn; nothing here is close to it.

## Kaggle

| | |
|---|---|
| Active submission | **55551524** (2026-08-16) |
| Rating at freeze | 497.3 — **still moving** |
| Team rank | 3,427 of 4,727 |
| Control submission | 55547718 at 452.3, kept active and unchanged |

Every submission is seeded at **600** before playing anything and drifts ±120.
The rating above is one reading and should not be treated as this checkpoint's
score.

## Known limitations

- **Below the leaderboard median** (744.5 at freeze). Top quartile is 1,648.
- **Tomato is never planted**, so it sells 0 units every season. Fertilizer's
  best case by far is tomato (interval 1, one unit covers three production
  ticks) and it is entirely untapped.
- **Melon collapses to near the $1 floor in self-play.** Three attempts to
  correct this by throttling or diversifying all lost badly — see CLAUDE.md.
- **~43 unit-turns a season wasted on blocked PLANT requests.** The engine
  drops *all* plant requests for a crop when a turn's demand exceeds held
  seeds; there is no per-turn seed budget.
- **Fertilizer is being arbitraged by accident**, netting about +2,517 a
  season. Nobody has tried sizing it deliberately.
- **One animal only.** More geese were tested at 2/3/4/6 and all lost.
- **No opponent modelling, no lookahead, no multi-turn planning.**

## What is not included

- `FERTILIZE` on one-time crops — the engine gives them no daily production
  at all, so it would do nothing.
- `BUY_LAND` — tested twice, lost twice.
- Cow and sheep. `ACTIVE_ANIMALS` is data-driven so enabling them is a config
  change, but it is untested beyond a single animal.
- Shed transfers beyond the fertilizer, wheat and animal paths.
- Any LLM component. None has been run in this repo.

## Reproducing

```bash
git checkout df69f97
.venv/Scripts/python.exe -m unittest discover -s tests      # 82 tests
.venv/Scripts/python.exe experiments/selfplay_bench.py 8
.venv/Scripts/python.exe experiments/seeded_batch.py
```

To compare something against this checkpoint, see
[../CHECKPOINTS.md](../CHECKPOINTS.md) — pick `paired_compare.py` or
`head_to_head.py` by what you changed, and never judge a delta against the
across-seed stdev.
