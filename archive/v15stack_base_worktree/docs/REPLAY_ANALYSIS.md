# What the top of the ladder actually does

Independent verification of the replay evidence in Kevin's `ROADMAP.md`, plus
what it means for the "measured dead ends" in `CLAUDE.md`.

**Verdict up front: the roadmap's evidence is sound, and it overturns two of
our biggest recorded conclusions.** `BUY_LAND` and multi-animal are not dead
ends. They are the strategy, and every test we ran against them was confounded
in the same way.

## Method

The host publishes daily dumps of top-rated ladder episodes as standard
`kaggle_environments` replays. They are listable and fetchable one at a time,
so there is no need to pull a whole ~450MB day:

```bash
kaggle datasets files    kaggle/kaggriculture-episodes-2026-08-16
kaggle datasets download kaggle/kaggriculture-episodes-2026-08-16 -f 93459920.json
```

`experiments/replay_shape.py` extracts the strategic shape from one of these.
Two episodes were sampled independently of Kevin's six, deliberately from
different dates and different teams:

| episode | date | teams | final money |
|---|---|---|---|
| 93459920 | Aug 16 | GUGUGAGA vs Peter Parker | **95,288 / 91,904** |
| 90849277 | Aug 8 | kakuteki vs Akhil Chinta | 54,528 / 52,963 |

**Both are contested markets between two different teams**, checked via
`info.TeamNames` — not self-play. That matters for what we compare against:
these numbers belong next to our **self-play ~41k**, not our ~58k against
`starter`, because the built-ins never sell.

## The shape, confirmed on both

| signal | Aug 16 | Aug 8 | us today |
|---|---|---|---|
| `BUY_LAND` | days **6, 11** | days **7, 11** | never |
| owned tiles | 25 -> 50 -> **75** | 25 -> **75** | **25** |
| animals | **COW x6, SHEEP x3** | **COW x5, SHEEP x3** | 1 sheep |
| `HIRE` orders | 277 | 263 | ~170 |
| crew held | 12-13, days 8-29 | 15, days 12-29 | ~6 |
| sell-heavy from | day 10 | day 10 | threshold-triggered |
| `SELL` orders | 501 | 175 | ~110 |
| `BUY_PRODUCT` | 71 | 165 | emergency only |
| MELON | days 0-7 (20) | days 0-11 (24) | all season |
| STRAWBERRY | days 5-12 (34) | days 7-11 (42) | all season |
| WHEAT | days 0-27 (127) | days 0-27 (108) | continuous - matches |
| CARROT | days 21-25 | none | no late role |
| TOMATO | **never** | **never** | rare |

Four different teams across two dates produce the same strategy *down to the
land-purchase days*. That is one dominant shared approach - almost certainly a
strong public notebook - not a diversity of independent solutions.

## Why our dead ends were wrong

**One line explains the whole gap: they own 75 tiles and run 13 units; we own
25 and run 6.**

Every test we ran moved one of those two numbers while holding the other
fixed, and each is genuinely a loss alone:

- `BUY_LAND` at a fixed crew: more ground, same hands, tested as a loss.
  Correct - at that crew size.
- `WORK_TILES_PER_HAND` 3 and 2 on 25 tiles: **-7,352 and -7,385, 0 of 16
  both**. Correct - surplus units on saturated land plant tiles the crew
  cannot water.

Those are the *same confound in mirror image*. The replay runs at roughly
**5.8 tiles per unit** on 75 tiles - a looser ratio than our 4 - so neither
knob is the ceiling. **The pair is.** Land and crew only pay together, which
is exactly the thesis in `ROADMAP.md` §3b, now with numbers behind it.

`MAX_HANDS_PER_DAY` being dead code at 25 tiles (12 and 16 both measure
*exactly* +0) is the same story from a third angle: `wanted = min(cap, work //
ratio)` and a tended 25-tile farm never generates enough pending work to reach
the cap. On 75 tiles it would bind immediately.

## Multi-animal: the blocker was cash, and it is now gone

Recorded as a heavy loss, and the *reason* recorded for it was wrong. Measured
today, a second sheep against `starter`:

| baseline | paired vs `starter` | head to head |
|---|---|---|
| before the seed-reserve fix | **-19,514, 0 of 12** - both sheep starve, pastures end empty | +3,623, 18/24 |
| on top of `MIN_CASH_RESERVE_FOR_SEED_BUYING = 450` (`3b8d36f`) | **+900, 8 of 12** (t = 0.61) | **+4,384, 14/16** |

The failure was never the animal - it was that buying it drained the days 3-7
cash trough to $5, leaving nothing for feed. Raising the seed reserve removed
that trough (day-5 bank $17 -> $392), and the sign flipped. A ~20,000 swing
from one constant.

Note what changed and what didn't: head to head liked the second animal all
along (+3,623 then, +4,384 now). The built-in harness is what moved, from
catastrophic to mildly positive - and it was the harness telling the truth
both times. It is still only t = 0.61, so this is **not yet shippable on its
own**; and two sheep is not what the ladder runs anyway - it runs **cow plus
sheep**, 8-9 animals. Which brings the blocking gap below.

## Blocking gap for Phase 3

**`ACTIVE_ANIMALS = ["SHEEP", "COW"]` cannot currently build a cow.**
`choose_animal_to_build` ranks by care-bank arithmetic and sheep wins every
slot, so that configuration builds two sheep and no cow - verified
byte-identical to the two-sheep variant. The recorded sheep-plus-cow dead end
(-16,634) never tested a cow at all.

Species diversity has to be forced before the replay's animal mix can be tried
at all. That is a code change, not a constant.

## Corrections to `ROADMAP.md`

The roadmap is one commit stale on the interaction it flags in §3c. It cites
Fix A as +2,271 isolated but +598 bundled with the hire gate, and treats the
sub-additivity as an open caveat. **That is now resolved**: the two were
competing for the same trough dollars, and retuning
`MIN_CASH_RESERVE_FOR_SEED_BUYING` from 100 to 450 (`3b8d36f`, shipped) fixes
it - **+4,166 winning 24 of 24 head to head, +5,389 (10/12, t=3.84) paired vs
`starter`**, both measured against the previously-live agent.

The "Us today" column also predates several changes: self-play is ~41k, not
$31,132, and against built-ins ~58k, not ~42k.

Everything else in the roadmap stands, and Phase 2 -> Phase 3 is the right
order for exactly the reason the phases give.

## Recommended sequence

1. **Crew size as a derived function of owned tiles** (roadmap Phase 2). No
   strategy change, and it is the precondition for everything else.
2. **`BUY_LAND` x2 targeting days 6-11, bundled with the crew scaling, as one
   paired comparison.** Never isolated - isolation is what produced the false
   dead end. Target 75 tiles and 13-15 units.
3. **Force species diversity**, then cow + sheep.
4. Per-crop planting windows (melon early, strawberry narrow, carrot late).
5. Selling cadence - the replay sells from day 10 onward at 15-48 orders/day
   with no day-22 cliff.

Steps 1 and 2 are the ones worth the remaining submission slots. They are
where the 2x money gap lives.
