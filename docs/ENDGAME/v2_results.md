# T5d — `agents/farm2945_v2.py`: three switchable overlays on `public_farm2945`, measured

**Date 2026-09-21.** Base: `agents/public_farm2945.py` (thomastschinkel's "2945 Farm",
Apache-2.0, submission `56269928`), **unmodified** — as are `agents/farm2945_late.py`,
every other agent and `main.py`. Overlay: `agents/farm2945_v2.py` (base embedded
byte-verbatim, overlay appended, `agent` the last callable binding, flags at the top of
the overlay). Tests: `tests/test_farm2945_v2.py` (24, stdlib `unittest`). Spec:
`docs/ENDGAME/traces_2026-09-21.md`. Nothing was committed and no Kaggle API call was made.

**Harness set:** the 17 `56269928` episodes that `public_farm2945.py` reproduces to $0
(15 losses, 2 wins); `109551974` and `109793226` are excluded because the base does not
reproduce them. **Control:** the overlay with every flag at the base's own value is
**bit-identical on all 17** — Δ bank $0, Δ margin $0, `first_divergence` `None` on every
episode, and the recorded margins come out exactly as `traces_2026-09-21.md` §1 lists them.
That is what makes every lever column below attributable.

> **Frozen-tape caveat.** `ladder_replay.run()` freezes the opponent's recorded tape, so a
> harness Δ is an **upper bound** and the trustworthy signals are the win/loss flips and the
> win count. Absolute self-play bank is the number that settles it.

---

## 0. Answers up front

| lever | verdict |
|---|---|
| **A - v219 off** | **Do not ship, and the traces' Trace 1 is contradicted by live play.** It reproduces the traces exactly on the frozen-tape harness (+2,480 bank / +1,867 margin on the 3 firing episodes, 3 of 3) - and **every harness with a responding opponent says the opposite**: self-play -1,074, head to head vs the base **0-2 of 16**, vs `router_yuan_nf_trim` +14,497 against the base's +15,982. All of it is one seed: seed 300 is the only one of 8 where v219 fires, and there disabling it costs **-8,497/seat in self-play and -10,076/seat head to head**. |
| **B - carrot gate** | **Do not ship.** The binding condition is the `CARROT/WHEAT` ratio, and on the 17 real episodes it reaches the shipped **1.8 on exactly one** of them. Widening to 1.5 is a **literal no-op on all 17**. Widening to 1.2 - below the ~1.44 per-tile break-even - is +773 mean d margin with **1 loss->win and 0 breaks**, but better on only **3 of 17** and worse on 4, and **1-9 of 16 head to head against the base**. |
| **C - melon stagger** | **Do not ship.** The brief's day-4 plant delay is **not implementable** on this tape (SS3.1); the implementable two-day *harvest* stagger executes exactly as designed and is a decisive loss anyway: **-4,128 mean d margin, better on 0 of 17, one recorded win broken, 0-16 of 16 head to head.** |
| **A + B(1.2)** | **Do not ship.** The only configuration that clears the harness bar (+1,094 d margin, 0 breaks, 1 loss->win) and it fails the other two: self-play **-405** and **0-10 of 16** against the base. |

**Nothing meets the ship criteria, so `agents/farm2945_v2.py` ships with every flag at the
base's own value and is bit-identical to `agents/public_farm2945.py`** - the same outcome
and the same convention as `agents/farm2945_late.py`. Seed-0 self-play gate on the shipped
file: **`['DONE','DONE']`, 72,101 / 72,762** - the base's own gate numbers, no $3,000.

The single most useful thing measured here is not a lever: **the frozen-tape harness and
three live harnesses disagree on lever A by about $10,000 a seed, and they disagree in the
direction that matters.** `ladder_replay.run()` cannot price a program whose value depends
on the opponent re-planning, and v219 is exactly such a program.

---

## 1. Lever A — v219 off

`_v219_qualifies` is evaluated **once**, at step 432 (`agents/public_farm2945.py:1427`), and
everything downstream reads `_V219_STATES[player]['committed'/'workers']`, which stay absent
when it returns `False`. So the cleanest possible disable is to rebind that one module
global — the base's own code does the rest, and the overlay is byte-identical on every
episode where v219 never qualified anyway. This is the same patch the traces used in memory;
here it is a flag (`V2_V219_OFF`) with the original predicate kept reachable.

### 1.1 Harness, all 17 episodes

| | mean d bank | mean d margin | margin better | flips | no-ops |
|---|---:|---:|---|---|---|
| **all 17** | **+437** | **+329** | 3 of 17 | 0 up, 0 down | 14 |
| the 3 episodes where v219 fires | **+2,480** | **+1,867** | **3 of 3** | - | - |
| the 2 wins | +0 | +0 | 0 of 2 | - | both exact no-ops |

Per firing episode - this reproduces `traces_2026-09-21.md` SS1.2 to the dollar:

| episode | d bank | d margin | first divergence |
|---|---:|---:|---:|
| `109618581` | +5,921 | +1,958 | step 433 |
| `109679411` | +459 | +2,074 | step 433 |
| `109798409` | +1,059 | +1,568 | step 433 |

**The disable is clean.** `first_divergence` is `None` on the 14 non-firing episodes and
**exactly step 433** (day 18, hour 1 - the step after `_v219_qualifies` is evaluated) on the
three that fire. The action diff on `109618581` touches **only days 18-29** and is entirely
v219's own footprint: the 21-22 extra hands disappear (so their whole op column goes away),
10 `PLANT TOMATO`, the `BUY_LAND`, the `BUY_SEED TOMATO`, the `SELL TOMATO`s and the
day-18+ `BUY_PRODUCT FERTILIZER`. **Nothing outside v219's op set moves** - no layer that is
gated on `_V219_STATES[...]['committed']` wakes up.

### 1.2 Every live harness says the opposite

| | base | lever A |
|---|---:|---:|
| self-play, 8 seeds x 2 seats (300-307) | **89,667** | **88,593** (-1,074) |
| head to head vs the base, 8 seeds x 2 seats | - | **0-2 of 16**, mean -1,259, worst -11,718 |
| vs `agents/router_yuan_nf_trim.py`, 8 seeds x 2 seats | **16-0, +15,982** | 16-0, **+14,497** |

**7 of the 8 self-play seeds are byte-identical** - v219 fires on seed 300 only - so the
whole effect is one draw, and on that draw it is unambiguous:

| seed 300 | base | lever A |
|---|---:|---:|
| self-play banks | 106,960 / 105,829 | **98,463 / 97,133** |
| head to head (A in one seat, base in the other) | - | **-10,076 both seats** |

Self-play seed 300's action diff is the same v219 footprint as the harness (first divergence
step 433: 17 fewer `HIRE`, one fewer `BUY_LAND`, one fewer `BUY_SEED TOMATO`, 10 fewer
`PLANT TOMATO`, 5 fewer `SELL TOMATO`), plus small market-driven reactions further down the
stack (`BUY_SEED CARROT` +-1, three `PLANT CARROT -> PLANT WHEAT`) that are the base's own
price-gated layers responding to a different book - not a leak.

**So the $4,000 quadrant plus ~17 extra fibonacci hires plus 10 tomato tiles is worth about
+$8,500 on that seed against an opponent that can respond**, and the frozen tape scored it
at -2,480 because the recorded opponent kept selling its tomato into a book we had vacated.
This is the mirror image of the caveat the traces themselves state, and it is why lever A is
not shipped despite being 3-of-3 on the harness.

---

## 2. Lever B — the carrot gate

### 2.1 What the gate currently requires

`agents/public_farm2945.py:3052-3098`, read verbatim:

| condition | value |
|---|---|
| `V9_CARROT_FIRST_DAY <= day <= V9_CARROT_LAST_DAY` | **days 10–23** |
| `wheat_held >= reserve` | **40** (`V9_CARROT_WHEAT_RESERVE`), or **10** in "boom" |
| `prices.CARROT / prices.WHEAT >= V9_CARROT_RATIO` | **1.8** |
| boom branch: ratio ≥ `V9_CARROT_BOOM_RATIO` | 3.5 — then the feed reserve is *bought* |

When it fires it renames `PLANT WHEAT` → `PLANT CARROT` for units already standing on a
tile and `BUY_SEED WHEAT n` → `BUY_SEED CARROT n` 1:1 in the same turn's market list, and
inserts a `SELL CARROT` at index 0 for the resulting stock.

**Seed backing is structural, not a guard we added.** The rename decrements a per-turn
`carrot_seeds` counter initialised from *held* CARROT seed minus the carrot plants already
in the action, and stops when it reaches 0. So no widening of the gate can make a turn
demand more seed than it holds, which is what matters: the engine drops **all** `PLANT X`
requests for a crop whose turn demand exceeds held seed (`kaggriculture.py:920-931`).
Two unit tests pin this (`test_widening_never_plants_more_carrot_than_held`,
`test_widening_renames_the_seed_buy_one_for_one`).

### 2.2 The ratio is the binding condition, and it almost never clears 1.8

Measured off the recorded observations of farm2945's own seat, the live
`CARROT/WHEAT` quote ratio at hour 0 of each day, all 17 episodes:

| ratio reached at any point in days 10–23 | episodes |
|---|---|
| ≥ 1.8 (the shipped gate) | **1** — `109694364` (days 18–23, peak 2.12) |
| 1.45–1.8 | 2 — `109663295` (peak 1.45), `109745434` (peak 1.48) |
| < 1.45 | **14**, spanning 0.64–1.42 |

The reason is not carrot: it is **wheat**. `traces_2026-09-21.md` §2.3 measures WHEAT ending
at **122% of base** (inventory below `I0`) against CARROT's 102%, so the denominator is the
elevated term and the ratio sits near 1.0 while the base prices imply 35/25 = 1.4.

### 2.3 Where break-even actually is

On the tape's rigid 4-day replant cycle a watered wheat tile yields 4 units for a $10 seed
and a carrot tile 3 units for a $20 seed (`CROPS`: WHEAT `max_yield` 6 / window ages 2–4,
CARROT `max_yield` 4 / window ages 2–3; the base's own comment states the realised 4-vs-3).
Break-even is `3·Pc − 20 = 4·Pw − 10`, i.e. **ratio ≈ 1.44** at a $30 wheat quote. So the
shipped 1.8 is conservative by ~25%, and anything **below ~1.45 plants a worse crop per
tile-cycle** — which is what the two settings below test.

### 2.4 Measured

| setting | harness: mean d bank / d margin | margin better | flips | self-play (base 89,667) | vs base | vs `nf_trim` |
|---|---:|---|---|---:|---|---|
| **1.5** | +0 / **+0** | 0 of 17 | 0 / 0 | 89,569 (**-98**) | *(no-op on the harness)* | *(not run)* |
| **1.2** | +824 / **+773** | **3 of 17** (4 worse, 10 no-ops) | **1 loss->win**, 0 down | **90,347 (+680)** | **1-9 of 16**, -601 | 16-0, **+15,621** |

**1.5 is a literal no-op on all 17 episodes** - `first_divergence` `None` everywhere - which
is the ratio table above made concrete: the only episode that clears 1.5 also clears 1.8.
(It is *not* a no-op in self-play: 3 of 8 seeds move, for -98 mean. The real ladder draws
and the self-play draws have different books.)

**1.2 is one seed wearing a mean.** The entire positive result is `109694364` - the one
episode whose carrot/wheat ratio runs 1.4-2.2 from day 14 - at **+15,297 bank / +14,170
margin, flipping a -8,389 loss into a +5,781 win**. The other 16 episodes are 2 small
positives, 4 negatives and 10 exact no-ops. Read win-count first, as this repo's own rule
says, and 3-better-4-worse is a coin flip; head to head against the base it is **1-9 of 16**
and it loses ground against `nf_trim` too (+15,621 against the base's +15,982).

Action diff on `109694364` confirms only intended ops move: `BUY_SEED WHEAT -> BUY_SEED
CARROT` on days 10-11, `PLANT WHEAT -> PLANT CARROT`, the base's own age-3
`WATER -> HARVEST` carrot rescue on day 13, then downstream `BUY_PRODUCT WHEAT` and
`FEED`/`PASS` differences that are the base's feed logic reacting to a different shed.

**Reading.** Opening the gate to break-even (~1.45) buys nothing on this episode set,
because the ratio rarely gets there; opening it *below* break-even buys one lucky seed and
loses small on four. The gate is not mis-set - the *market* is: WHEAT is the scarce book in
these games, which is precisely the condition under which the base is right to keep planting
it.

---

## 3. Lever C — the melon stagger

### 3.1 The brief's day-4 plant delay is not implementable on this tape

Stated first because it changes what was built. Three facts, each measured, not argued:

1. **`_new_plant` sets `consecutive_unwatered = 1`** (`kaggriculture.py:222`), and
   `_daily_refresh_plants` turns a plant into a WEED at `consecutive_unwatered >= 2`. So a
   planting that is **not watered the same day is dead by morning** — the delayed `PLANT`
   needs a same-day `WATER` on the same tile.
2. **The only day the tape gives these 7 tiles a `PLANT`-then-`WATER` pair by the same unit
   is day 0 itself.** Measured visit-by-visit: day 0 is `PLANT MELON` at hour *h* then
   `WATER` at *h+1*; **day 1 has no visit at all on 6 of the 7 tiles**; days 2–5 are a
   single `WATER` followed by a MOVE. Rewriting that MOVE would desynchronise every later
   position in that unit's route, which is the failure mode the whole route-tape
   architecture cannot survive.
3. The tape's **other** `PLANT`+`WATER` pair on these tiles is the day-10 wheat replant —
   renaming it to MELON is exactly lever 2 of `agents/farm2945_late.py`, already measured
   (−552 bank / −1,525 margin, one broken win).

The brief's expected mechanics were also wrong in two places, and both are checked in
`tests/test_farm2945_v2.py::TestEngineFactsTheLeversRestOn`:

| brief | engine |
|---|---|
| "MELON planted day 4 first-yields day 14, max day 16" | correct (`first_yield_day` 10, `max_yield_day` 12) **but the plant dies first**: `max_lifespan_step = (planted_day + 13)·24` |
| "the tape's 4-day wheat-cycle HARVEST on those tiles at day 14" | the tape's next HARVEST on those tiles is **day 12 (2 tiles) or day 13 (5 tiles)**, never day 14 |

"HARVEST on an unripe non-ongoing crop no-ops without clearing" **is** correct
(`kaggriculture.py:446-470`: `yield_units` starts at 1 for a non-ongoing crop, then
`day - planted_day < first_yield_day` returns before the tile is cleared).

### 3.2 What was built instead: a harvest stagger, bounded at two days

A day-0 melon's `max_lifespan_step` is `(0+12+1)·24`, so **day 12 is the last day it is
alive** and two days is the whole budget. The lever therefore:

1. **Day 10** — replaces `HARVEST` with `PASS` for any unit standing on one of the 7 tiles
   while it still holds a MELON. The tape's day-10 `PLANT WHEAT` then no-ops on the
   occupied tile, and crucially **consumes no seed**: `_apply_unit_action`'s PLANT branch
   returns at `if tile is not None` *before* touching `private["seeds"]`, so the
   atomic-PLANT rule is untouched and the wheat seed is simply carried forward.
2. **Day 12** — converts that day's `WATER` visit into `HARVEST` on those tiles. The base
   itself uses this exact WATER→HARVEST rescue for its swapped carrots, so it is the tape's
   own idiom.
3. **Selling** — appends (never inserts) a paced `SELL MELON` for shed surplus from day 12,
   capped at `V2_MELON_SELL_PER_TURN`. Appending means **no existing order's settle index
   moves**, which is what the order-lockstep market requires.

**Tile identification and the guard.** The 7 ex-melon wheat tiles are
`(0,4) (1,2) (1,3) (2,1) (2,2) (3,0) (3,1)` — **identical on all 17 harness episodes** and
in self-play, out of the 12 day-0 melon tiles (the other 5 become COOP/PASTURE on day 10).
**Every one of the 7 has a day-12 `WATER` visit on all 17 episodes**, so the rescue always
has a slot. The lever latches an abort at day 10 if the day-0 melon block is not exactly
those 7 tiles, and is then a literal no-op.

**Yield is not lost.** MELON caps at `max_yield` 6 and the tape's melons are already at 6 by
day 10 (72 units over 12 tiles in the recorded episodes), so harvesting on day 12 returns the
same 6 units per tile.

**Stated cost.** The 5 tiles whose next tape HARVEST is day 13 lose **one wheat cycle**: the
tile is empty from the day-12 rescue until the day-13 replant, where the base would have had
wheat growing from day 10. (The brief's variant would have left the 7 tiles empty on days
0–4; this one leaves 5 of them empty for about one day in mid-season instead.)

**Stated arithmetic, up front.** MELON appears in **no `SHOPS` entry** (`kaggriculture.py:103`),
so its only sink is the Town Centre's one unit a day. A two-day delay therefore buys about
**2 units of headroom** on a `sq` curve — this lever cannot be large, and it was built and
measured because the brief asked for it, not because the arithmetic predicts a win.

### 3.3 Measured

| | harness: mean d bank / d margin | margin better | flips | self-play (base 89,667) | vs base | vs `nf_trim` |
|---|---:|---|---|---:|---|---|
| **C** | **-2,679 / -4,128** | **0 of 17** | 0 up, **1 win->loss** (`109856068`, +4,417 -> -17,128) | 89,795 (+128) | **0-16 of 16**, -3,710 | 16-0, +12,168 |

**The lever executed exactly as designed - it is the economics that lose.** Action diff on
`110055611` (bank 81,680 -> 81,108), and this is the whole diff:

| count | op |
|---:|---|
| 7 | `d10 HARVEST -> PASS` |
| 7 | `d12 WATER -> HARVEST` |
| 7 | `d13 MKT +SELL MELON` |
| 3+3+1 | `d13/d14 MKT +-BUY_PRODUCT WHEAT` (the base's own feed top-up reacting to cash) |
| 1+1 | `d14 MKT +-SELL MILK`, `d29 MKT +-SELL WHEAT` |

Seven tiles suppressed, seven rescued, 42 units sold - `first_divergence` is step 245-246
(day 10, hour 5-6) on 17 of 17, exactly the first suppressed harvest, and the abort guard
never fired. No unintended op appears anywhere.

It still loses, for the reason stated before it was built: with a **1 unit/day** sink the
two days of delay recover ~2 units of book headroom, against a real cost in tile-time and in
the cash the day-10 sale was funding. The broken win (`109856068` -> -21,545 margin) is the
frozen-tape amplification of that same cash shift, on the one episode with 24 structures.

**This closes the melon question in the form the brief posed it.** A stagger that is worth
anything has to *add melon volume late*, not move a fixed volume two days - and adding it is
`agents/farm2945_late.py`'s lever 2, already measured a loss. The winners' +$5,819 comes
from planting melon the base never plants, on tiles it does not have free.

---

## 4. The combination

A and B(1.2) are independent (day 18 vs days 10-23, different crops), so the natural
combination is both on. It is the only configuration that clears the harness bar - and the
harness is the one measurement that cannot see what the other three see.

| | value | criterion |
|---|---:|---|
| harness, 17 episodes: mean d bank | +1,255 | - |
| harness: **mean d margin** | **+1,094** | >= +1,000 PASS |
| harness: margin better / worse / no-op | 6 / 3 / 8 | - |
| harness: flips | **1 loss->win, 0 win->loss** | breaks = 0 on the 2 wins PASS |
| **self-play, 8 seeds x 2 seats** | **89,262** (-405 vs base) | not below base by > $300 **FAIL** |
| **head to head vs the base** | **0-10 of 16** (6 ties), mean -1,822 | >= 8-8 **FAIL** |
| vs `router_yuan_nf_trim` | 16-0, +13,668 | (base: 16-0, +15,982) |

The two failures are A's seed-300 loss (-9,952 head to head) and B's four small negatives -
neither is cancelled by the other. **The combination passes the harness because the harness
is the harness that is wrong about A.**

---

## 5. Ship decision

| criterion | A | B(1.5) | B(1.2) | C | A+B(1.2) |
|---|---|---|---|---|---|
| self-play mean not below base by > $300 | FAIL -1,074 | pass -98 | pass **+680** | pass +128 | FAIL -405 |
| harness mean d margin >= +1,000, breaks = 0 | FAIL +329 | FAIL +0 | FAIL +773 | FAIL -4,128, **1 break** | pass **+1,094**, 0 breaks |
| >= 8-8 vs the base | FAIL 0-2 | - (no-op) | FAIL 1-9 | FAIL 0-16 | FAIL 0-10 |
| seed-0 self-play DONE/DONE, no 3000 | pass | pass | pass | pass | pass |

**No configuration meets the criteria. `agents/farm2945_v2.py` ships with
`V2_V219_OFF = False`, `V2_MELON_STAGGER = False`, `V2_CARROT_RATIO = 1.8` - bit-identical
to the base on all 17 episodes, DONE/DONE at 72,101 / 72,762 on the seed-0 gate.** The file
is kept for the same reason `farm2945_late.py` is: the flags, the guards, the tile
identification and the engine-fact tests are the reusable part, and the *reasons* these
three lost change what the next attempt should be.

---

## 6. What I could not determine

**The thing I am least sure about: whether lever A's live-harness losses are one seed's
luck or the real answer.** v219 fires on **exactly one of the eight self-play seeds** and on
three of the seventeen real episodes, so the live evidence against A is three readings of
one draw (self-play seed 300, head to head seed 300 x 2 seats) rather than three independent
samples. They are unanimous and large (-8,497 and -10,076 per seat, against a frozen-tape
+2,480), and a responding opponent is the more realistic setting - which is why I did not
**SETTLED 2026-09-21 (T5e). v219 pays, and the frozen tape is the harness that is wrong
about it.** The twenty minutes of compute this paragraph asks for below was spent: the
base and lever A played seeds **308-331, both seats**, through `experiments/tapes/run_agents.py`,
and firing was detected independently of the bank delta by probing base self-play on the
same seeds for a `BUY_LAND` order at step >= 432 - v219's own footprint, and unambiguous
because `_v219_qualifies` *refuses* when the tape itself buys land after 432. **It fires on
exactly 3 of the 24 seeds - 312, 328 and 330** - and on the other 21 lever A is a literal
no-op (delta exactly $0 on both seats; the +-762 and +-80 seen on seeds 310 and 313 are the
seat asymmetry of identical code, and both probe at zero firings). On the three firing
seeds, disabling v219 costs **-8,111 / -2,571 / -3,715 per seat, identical in both seats -
0 of 6 seat-results better, mean -4,799**. Together with seed 300 from SS1.2 that is **four
independent firing draws and four losses**, so the "n = 1 seed" caveat is closed in the
direction the live harnesses already pointed: **do not disable v219.** The frozen-tape
+2,480 remains the clearest example in this repo of `ladder_replay.run()` mispricing a
program whose value depends on the opponent re-planning. Original open question follows.

Seeds 308-331 on the
base and on A, counting how many fire and taking the mean over only those, would settle it,
and is about twenty minutes of compute nobody has spent.

Also unresolved:

- **Why v219 is worth ~$8,500 in a mirror.** Traces SS1.2 costs the program at $9.6-10k
  against $7-12.1k of tomato revenue - a +-2k line item. An +8,500 swing is four times that,
  so something other than the tomato P&L is carrying it (the 10 extra worked tiles of the SE
  quadrant for the last 11 days is the obvious suspect, and it is not measured here).
- **Whether B(1.2)'s one flip generalises.** `109694364` is the only episode in the set whose
  carrot/wheat ratio runs above 1.4, and it is worth +14,170 there. A larger episode set with
  more `PET_CAFE`/`FARMERS_MARKET` draws is the only way to know whether that is a real
  regime or a seed.
- **Whether the two-day harvest stagger would pay with the sale paced differently.**
  `V2_MELON_SELL_PER_TURN = 6` was picked, not tuned; the loss is large enough (0 of 17) that
  tuning it is unlikely to cross zero, but it was not swept.
- **The cash coupling in lever C.** Suppressing 42 units of the day-10 sale removes roughly
  $7k of cash on the day the tape buys and places its herd. The `BUY_PRODUCT WHEAT`
  differences on days 13-14 in the action diff are that coupling showing up, but I did not
  decompose how much of the -3,710 head-to-head loss is the delayed cash versus the lost
  wheat cycle.

## Files

`agents/farm2945_v2.py` (base verbatim + overlay), `tests/test_farm2945_v2.py`.
Measurement scripts were throwaway, run from the session scratchpad against the replays
already cached in `experiments/endgame/rep/`. `agents/public_farm2945.py`,
`agents/farm2945_late.py`, every other agent, `main.py` and every existing tool are
unmodified. Nothing was committed, nothing was submitted, and no Kaggle API or dataset call
was made.
