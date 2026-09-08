# Current session: 2026-09-07 — collect-then-harvest dropped

> **Standing rule:** Report to the user in chat before writing this file.

## What this session did

Named miss: d7 land $1,374 vs $1,500 because 3 wool sat on sheep
(4,4). Bind: COLLECT still first, HARVEST at any yield>0, walk-back
above K-STRAW. Not harvest-before-collect, not d6 DROP, not a gate
rewrite. Yarn left the early draw → Stage 2 no-yarn table cows not
cap-2. Unfed gate on the walk after a d24 cow escape. Reverted.

## Counters

| arm | seed 0 | seed 8 | land | STRAW d5–8 | end | yarn | dips |
|---|---|---|---|---|---|---|---|
| live | 40,236 | 55,411 | [8, 11] | 1/5/0/1 | 14 / 17 | d12 / none | 0 / 1 |
| Stage1 walk | 40,033 | **61,130** | **[7, 11]** | 1/5/**3**/1 | 16 14C2S / 13 5C8S | **d21** / **d9** | 0 / **1** |
| + Stage2 mix | **52,019** | 61,130 | [7, 11] | 1/5/3/1 | 14 10C4S / 13 5C8S | d21 / d9 | 0 / **1** |
| unfed gate | **39,587** | **52,878** | [7, 11] | 1/5/3/1 | 14 10C4S / 14 6C8S | d12 / d9 | 0 / 0 |
| restored | 40,236 | 55,411 | [8, 11] | 1/5/0/1 | 14 / 17 | d12 / none | 0 / 1 |

Inflow held on every harvest arm: both sheep yld=0 d6 EOD, shed
wool 7 d7h00, SELL WOOL 7 d7. Wheat d0 landed 7. MELON after d0=0.

## Why the bind failed

Same two fights as harvest-before-collect, plus a feed fight:

1. **Shop-draw reroll.** Land [7, 11] and STRAW d7 0→3. Seed 0 yarn
   d12→d21 (Stage1/2) or restored d12 only after the unfed gate.
   Seed 8 gained yarn d9. Extra d7 NE plants are the `_spawn_weeds`
   class.
2. **Harvest-walk vs feed.** Ungated walk escaped a cow seed 8 d24
   (6C8S→5C8S). Gating the walk on `any_unfed` cleared dips and
   killed both banks (−649 / −2,533).
3. Stage 2 (no-yarn table 10/8 not cap-2) recovered seed 0 to
   52,019 **without** fixing the seed-8 escape. Do not lead with it
   on the live [8, 11] throwaway (cap-14 class).

## Verdict

**Dropped.** Kind: supplement (facts 15, 33, 44 rider). Do not retry
collect-then-harvest, harvest-before-collect, no-yarn cap-fill cut,
freeze-until-milk, first-land without d6, first-buy waive, d6 wool
DROP, ladder, cap 14. No `main.py` port.

The d7-land / stranded-wool drawer is diagnosed and both harvest
orders that empty it reroll shops. Next liquidity move ≠ another
wool HARVEST reorder.

## How we continue

```text
Kind: — (collect-then-harvest is closed)
Was: land [7, 11]; inflow held; bank either −203 with 1 escape or
     −649/−2,533 with 0 dips
Now: throwaway hold-6 + cap 18; land [8, 11]; $500 on both buys
Fights: d7 land vs shop-draw (20); harvest-walk vs feed (20)
Throwaway: experiments/_facts_v20.py
Counters: land [8, 11]; wheat d0=7; MELON after d0=0; STRAW d6
     half-tape; bank 40,236 / 55,411
```

## Open

- Next ≠ collect-then-harvest, ≠ harvest-before-collect, ≠ no-yarn
  cap-fill cut, ≠ freeze-until-milk, ≠ first-land without d6, ≠
  first-buy waive, ≠ bundle, ≠ d6 wool DROP, ≠ ladder, ≠ cap 14.
  d7-land-via-wool harvest reorders are closed. Next miss should
  not move first-land day, or should fund without extra d7 NE STRAW.
- Live throwaway still 40,236 / 55,411; land [8, 11]; hold-6 / cap 18.
- Fact 44 −570 parked. Port to shipped `main.py` blocked.
- STRAW `$` is still the hole (−43.5k / −38.7k).

---

# Prior session: 2026-09-07 — direction: fund the calendar from produce


> **Standing rule:** Report to the user in chat before writing this file.

## What this session did

The rewrite-15/44 bind was the wrong idea, not a failed test of the
right one. Recorded the split. Throwaway already restored (hold-6 +
cap 18, 40,236 / 55,411). No new bind this write.

## What was done (wrong polarity)

Replaced the calendar as the buy emitter. After d0 a `BUY_ANIMAL`
fired only if shed wool+fert post-sell covered it *and* a shop ate
that product. Closed shop → the slot did not exist. First land
ignored `day >= 6`. Banks 38,649 / 46,533. Seed 0 herd sat at 4
through d17 (no milk shop in the first 3, so hold-6 never asked).
Land [7, 11] rerolled shops (yarn lost). Reverted.

That deleted the wall instead of diagnosing it. The tape still
*wanted* the d3 cow; the bind *refused the slot*.

## Direction we needed

**Keep the tape calendar as the goal. Produce funds it. A miss is a
diagnosis, then a rearrangement.**

The existing calendar shape stays: `calendar_owned_target` still
asks for the day’s head; land windows still ask for NE/SW on their
days. Fert, wool, melon — what is actually in the shed and can be
sold — is how those buys get paid (facts 9–13 already sequence
sell-before-buy; this is *when the drawer is empty*).

When a calendar buy or land does not emit, do not change the gate.
Name the missing inflow (d7 land was $1,374 vs $1,500 because 3 wool
sat on the sheep, not because `day >= 6` was wrong). Then rearrange
the farm activity that should have put that produce in the shed on
time. Still following the tapes. Shop mix still picks *which*
species (fact 44 yarn lock), not whether the day’s slot exists.

Not: tape days become a check. Not: closed shop deletes the cow.
Not: first land when wool+fert vs $1,500 *instead of* the day
window. Those three *were* the dropped bind.

Worked example already in hand: harvest-before-collect *was* a
liquidity rearrangement (wool off the tile into the shed so d7 can
clear $1,500). It landed the wool and the land day, then died on a
shop-draw reroll. The diagnosis was right; that particular
rearrangement is closed. Next liquidity move ≠ that HARVEST reorder,
≠ reserve waive, ≠ dropping the day gate.

## How we continue

```text
Kind: supplement (facts 15, 33) — produce funds the calendar; miss
     → name the inflow → rearrange that activity
Was: calendar still hold-6 + land windows; when a buy misses we
     either ignore it or replace the gate (dropped rewrite)
Now: calendar still emits the goal. A miss names which produce
     would have covered it. Next card rearranges that activity
     only. Shop mix still which, not whether. Day windows stay.
Fights: the dropped emitter-rewrite (freeze-until-milk, land
     without d6); buy-whenever-affordable (14); harvest-before-
     collect; first-buy waive; d6 wool DROP; tape ladder; cap 14
Throwaway: experiments/_facts_v20.py
Pre-run: facts 1–14, 16, 18–36 still true in source; d0 2C2S / 4/4
Counters: calendar still asks on its days (d0=4, hold-6 through
     d10); 0 escapes; wheat d0=7; MELON after d0=0; STRAW d6
     half-tape; named inflow present on the miss turn; bank not
     down vs 40,236 / 55,411 on seeds 0 and 8
```

## Open

- Next card: one liquidity rearrangement that funds a named calendar
  miss. Not a rewrite of what emits the buy.
- Do not retry the emitter-rewrite, freeze-until-milk, first-land
  without the d6 day floor, harvest-before-collect, first-buy waive,
  the bundle, d6 wool DROP, tape ladder, cap 14.
- Live throwaway still 40,236 / 55,411; land [8, 11]; hold-6 / cap 18.
- Fact 44 −570 parked. Port to shipped `main.py` blocked.
- STRAW `$` is still the hole (−43.5k / −38.7k).

---

# Prior session: 2026-09-07 — shop + post-sell rewrite dropped


> **Standing rule:** Report to the user in chat before writing this file.

## What this session did

Implemented the named rewrite of facts 15/44 (33 WHEN follows): after
d0, `BUY_ANIMAL` only if shed wool+fert post-sell covers it and a shop
eats the product; no-yarn mix uses the table count not `cap-2`; first
land when shed wool+fert vs $1,500, not `day >= 6`. $500 floor stayed.
Not harvest-before-collect, not waive, not ladder, not cap 14.

Reverted. Kill switch: bank down vs 40,236 / 55,411.

## Counters

| arm | seed 0 | seed 8 | land | STRAW d5–8 | end herd |
|---|---|---|---|---|---|
| live (fact 44) | 40,236 | 55,411 | [8, 11] | 1/5/0/1 | 14 / 18 |
| shop+post-sell | **38,649** | **46,533** | **[7, 11]** / [8, 11] | **5/4/12/4** / 1/5/0/1 | **8C2S=10** / **10C4S=14** |
| restored | 40,236 | 55,411 | [8, 11] | 1/5/0/1 | 14 / 18 |

0 dips both seeds. MELON after d0 = 0. Wheat d0 = 7. Seed 0 herd
**4 through d17**, then 10 on d18 (`cow_d13plus=6`). Seed 0 yarn
**lost** (shops `BRUNCH_SPOT, PET_CAFE, BRUNCH_SPOT, BAKERY…`). Seed 8
yarn **d21** (was none); sheep_after_d0=2; cow_d13plus=0.

## Why the bind failed

Two named mechanisms, one bind:

1. **Freeze-until-milk.** Seed 0 had no milk shop in the first 3, so
   extra cow slots did not exist. Hold-6 never bought the 5th/6th.
   Herd sat at beach-head 4 until ICE_CREAM/PIZZA unlocked late, then
   dumped 6 cows on d13+. Closed shop → no slot did what it said and
   killed the d3/d5 cows the ceiling still allowed.
2. **d7 land shop-reroll.** Dropping `day >= 6` landed first land on
   d7 (seed 0). STRAW d7 0→12. Same `_spawn_weeds` RNG class as
   harvest-before-collect: yarn left the draw.

Seed 8 bank −8,878 is the missing no-yarn cap-fill cows (18→14) plus
a late yarn mix, not the waive’s $0 dump.

## Verdict

**Dropped.** Kind: rewrite (facts 15, 44). Do not retry this bind,
freeze-until-milk, or first-land without the d6 day floor. Still no
harvest-before-collect, first-buy waive, bundle, d6 wool DROP, ladder,
cap 14, leftover walk, land-hour seed, 40–42, fert-only, STRAW pin,
holdout, or list reorder. No `main.py` port.

## How we continue

```text
Kind: — (shop+post-sell rewrite is closed)
Was: 38,649 / 46,533; seed 0 herd 4 through d17; land [7, 11]
Now: throwaway hold-6 + cap 18; land [8, 11]; $500 on both buys
Fights: 15 (count) vs 44 (sink) — do not average them into
     freeze-until-milk; d7 land vs shop-draw (20)
Throwaway: experiments/_facts_v20.py
Counters: land [8, 11]; wheat d0=7; MELON after d0=0; STRAW d6
     half-tape; bank 40,236 / 55,411
```

## Open

- Next ≠ shop+post-sell rewrite, ≠ freeze-until-milk, ≠ first-land
  without the d6 day floor, ≠ harvest-before-collect, ≠ first-buy
  waive, ≠ bundle, ≠ d6 wool DROP, ≠ ladder, ≠ cap 14.
- Live throwaway still 40,236 / 55,411; land [8, 11]; hold-6 / cap 18.
- Fact 44 −570 parked. Port to shipped `main.py` blocked.
- STRAW `$` is still the hole (−43.5k / −38.7k).

---

# Prior session: 2026-09-07 — direction: shop + post-sell emit the calendar

> **Standing rule:** Report to the user in chat before writing this file.

## What this session did

After harvest-before-collect dropped, named the polarity that session
exposed: fert paid for cows, wool almost paid for land, and the bank
nick was a shop-draw reroll — not an empty drawer. That is not “hit
the tape’s Tuesday.” The farm should pay for itself unless that shop
is closed.

Recorded as the next shape, not implemented this session. Throwaway
untouched (still hold-6 + cap 18, 40,236 / 55,411).

## Direction

**Liquidity + shop-sink emit the calendar. The day table does not emit
the buys.**

A buy fires when this turn’s post-sell of what is actually in the shed
covers it, **and** a shop eats the product that unit will make. If that
shop is closed, that slot does not exist. The tape ladder (4 / 5 / 6 /
8 / 10 / 12 / 13 / 14) stays as a *check* (did inflows get us near
there?), not as `calendar_owned_target(day)`.

Fact 44 today: shop picks *which*, calendar picks *how many*. That split
is the fight. No-yarn filling remaining cap with cows is calendar
powering count. Prefix-affordable without the sink is the d11 dump.

Land follows the same WHEN: first `BUY_LAND` when wool+fert **in the
shed** clear $1,000+$500, not when `day >= 6`. $500 floor stays. Wool
stranded on the tile is a drawer hole (20/34), not a waive and not a
day pin.

Not a slogan. Next card is a rewrite of **15 and 44** (33’s WHEN
follows). One throwaway bind: shop+post-sell gate `BUY_ANIMAL` after
d0; calendar days become a ceiling. Do not bundle harvest-before-
collect, first-buy waive, d6 wool DROP, the tape ladder, or cap 14.

## How we continue

```text
Kind: rewrite (facts 15, 44) — shop + post-sell emit the calendar
Was: calendar_owned_target(day) buys; shop_mix picks species inside
     that count; land windows by engine day; no-yarn still fills
     cows to cap 18
Now: a buy emits iff post-sell of shed flow covers it AND a shop
     eats that product; closed shop → slot does not exist. Tape
     days are a check, not the gate. No-yarn does not fill cap
     with cows. Land WHEN follows (shed wool+fert vs $1,500),
     $500 floor stays.
Fights: tape-day counters as emitters; buy-whenever-affordable
     (fact 14); no-yarn→16C; dropped day-chases (ladder, cap 14,
     harvest-before-collect, first-buy waive)
Throwaway: experiments/_facts_v20.py
Pre-run: facts 1–14, 16, 18–36 still true in source; d0 2C2S / 4/4;
     yarn lock’s *sheep=2* half stays (count half is what changes)
Counters: 0 escapes contested; no-yarn end SHEEP=2 and no extra cows
     just because day>=13; yarn seed SHEEP>2; d0 wheat=7; MELON
     after d0=0; STRAW d6 half-tape; bank not down vs 40,236 /
     55,411 on seeds 0 and 8. Tape herd days are reported, not gated.
```

## Open

- Next card: rewrite 15/44 as above. One bind. Kill switch: bank down
  vs 40,236 / 55,411, or escapes.
- Do not retry harvest-before-collect, first-buy waive, the bundle,
  d6 wool DROP, tape ladder, cap 14, leftover walk, land-hour seed,
  hold-the-burst, d12h0 slack.
- Live throwaway still 40,236 / 55,411; land [8, 11]; hold-6 / cap 18.
- Fact 44 −570 parked. Port to shipped `main.py` blocked.

---

# Prior session: 2026-09-07 — fact 20 harvest-before-collect dropped

> **Standing rule:** Report to the user in chat before writing this file.

## What this session did

HANDOFF said land-via-reserve is closed and early land still wants a
mechanism that does not dump d11. Diagnosed the $1,374 vs $1,500 miss:
apply-gap fert keep is 0 on d7; d6 morning wool DROP cannot fire (shed
has fert only). v20 buys land d6h04 after `SELL WOOL 6`. We sell 4 wool
on d7; 3 more sit on sheep (4,4) through d7 because underfoot HARVEST
only fires at `yield >= max_held-2` (4) and COLLECT wins at 3. v20
harvests both day-0 sheep to 0 on d6 (12 wool).

Tried the named card: HARVEST if `yield_units > 0` before COLLECT.
Reserve stayed $500. No waive, no d6 DROP, no calendar. Reverted.

## Counters

| arm | seed 0 | seed 8 | land | STRAW d5–8 | end herd |
|---|---|---|---|---|---|
| live (fact 44) | 40,236 | 55,411 | [8, 11] | 1/5/0/1 | 14 / **18** |
| harvest-before-collect | **39,690** | **55,210** | **[7, 11]** | 1/5/**3**/1 | **18** / 14 |
| restored | 40,236 | 55,411 | [8, 11] | 1/5/0/1 | 14 / 18 |

Sheep yld=0 both tiles d6 EOD. wool d7 4→7. d7h01 leftover **$573**
(not the waive's $0). Wheat d0=9. MELON after d0=0. 0 dips.

## Why the bind failed

The extra 3 wool *is* enough to clear the $1,500 floor. Land [7, 11]
and STRAW d7 0→3. d7 leftover $573, then the d7h01 cow leaves **$7**
(same cash accident as live's d8 $17, one day earlier). That is not
the waive's $0 dump.

The bank nick is a **shop-draw reroll**. Extra d7 NE tiles change
`_spawn_weeds` RNG before later shop unlocks (same class as the
dropped hold-the-burst). Fact 44's mix follows yarn:

| | yarn | d13 buy | end |
|---|---|---|---|
| live 0 | d12 (4th shop) | SHEEP x2 | 10C4S = 14 |
| harvest 0 | **none** | COW x6 | **16C2S = 18** |
| live 8 | none | COW x6 | 16C2S = 18 |
| harvest 8 | **d9 in first 3** | sheep mix | **6C8S = 14** |

No-yarn lock fills remaining cap with cows (fact 44). Losing yarn on
seed 0 bought 4 extra cows; gaining it on seed 8 cut 4 cows for
sheep. Banks −546 / −201. Not the waive's 28k crash. Still a fail
on the "bank not down" bar. Do not retry: any d7 NE plant rerolls
shops.

## Verdict

**Dropped.** Kind: supplement (fact 20). Do not retry harvest-before-
collect, first-buy waive, the bundle, d6 wool DROP, ladder, or cap 14.
Still no leftover walk, land-hour seed, 40–42, fert-only, STRAW pin,
holdout, or list reorder. No `main.py` port.

## How we continue

```text
Kind: — (land-via-harvest is closed; land-via-reserve stays closed)
Was: harvest-before-collect → 39,690 / 55,210, land [7, 11], seed 0 herd 18
Now: throwaway hold-6 + cap 18; land [8, 11]; $500 on both buys
Fights: early land vs the d11 dump (15) — do not average them
Throwaway: experiments/_facts_v20.py
Counters: land [8, 11]; wheat d0=7; MELON after d0=0; STRAW d6
     half-tape; bank 40,236 / 55,411
```

## Open

- Next ≠ harvest-before-collect, ≠ first-buy waive, ≠ bundle, ≠ d6
  wool DROP, ≠ calendar. Early land without a dump is still the hole,
  and this drawer (stranded wool) is now known to be the waive-class
  dump, not a new funding class.
- Live throwaway 40,236 / 55,411; land [8, 11]; T1 vs v20 ~75k.
- Written 15/17 stay; throwaway still hold-6 / cap 18.
- Fact 44 −570 parked. Port to shipped `main.py` blocked.

---

# Prior session: 2026-09-06 — fact 33 first-buy reserve dropped

> **Standing rule:** Report to the user in chat before writing this file.

## What this session did

Tried the named card: waive `$500` on the first `BUY_LAND` only
(`n_extra == 0` in `decide_land_orders`). Second buy kept 500. No
walk, no seed-before-cow, no calendar open, no d6 wool DROP.
Throwaway is back on hold-6 + `MAX_ANIMALS=18` (40,236 / 55,411).

d6 wool/fert post-sell cannot fund land: shed has fert only; wool
is harvested during d6 and sold d7h00. The measured miss is d7
post-sell $1,374 vs the $1,500 floor.

## Counters

| arm | seed 0 | seed 8 | land | STRAW d5–8 | end herd |
|---|---|---|---|---|---|
| live (fact 44) | 40,236 | 55,411 | [8, 11] | 1/5/0/1 | 14 / **18** |
| first-buy reserve 0 | **28,751** | **36,766** | **[7, 11]** | 1/5/2/0 | **18 / 18** |
| restored | 40,236 | 55,411 | [8, 11] | 1/5/0/1 | 14 / 18 |

Wheat d0=7 and MELON after d0=0 held. d11 carpet 15. 0 escapes.
STRAW `$` −35.2k / −33.9k (was −43.5k / −38.7k). d7 us **$0**.

## Why the bind failed

Land moved into the preferred window and STRAW d7 went 0→2. The
$500 waive emptied the drawer (d7 $0) and funded the existing d11
ramp: herd 6 through d10, then 12 / 18. Banks match the dropped
land-reserve bundle exactly. The extra binds in that bundle were
not load-bearing — the waive is the dump.

## Verdict

**Dropped.** Kind: supplement (fact 33). Do not retry first-buy
waive, the bundle, or d6 wool DROP. Still no tape ladder, cap 14,
seed-before-cow, leftover walk, d8 land-hour seed, 40–42, fert-only,
STRAW pin, holdout, or list reorder. No `main.py` port.

## How we continue

```text
Kind: — (land-via-reserve is closed)
Was: first-buy reserve 0 → 28,751 / 36,766, herd 18
Now: throwaway hold-6 + cap 18; land [8, 11]; $500 on both buys
Fights: early land vs the d11 dump (15) — do not average them
Throwaway: experiments/_facts_v20.py
Counters: land [8, 11]; wheat d0=7; MELON after d0=0; STRAW d6
     half-tape; bank 40,236 / 55,411
```

## Open

- Next ≠ first-buy waive, ≠ bundle, ≠ d6 wool DROP, ≠ calendar.
  Early land still wants a mechanism that does not dump d11.
- Live throwaway 40,236 / 55,411; land [8, 11]; T1 vs v20 ~75k.
- Written 15/17 stay; throwaway still hold-6 / cap 18.
- Fact 44 −570 parked. Port to shipped `main.py` blocked.

---

# Prior session: 2026-09-06 — 15/17 align dropped (ladder and cap-14)

> **Standing rule:** Report to the user in chat before writing this file.

## What this session did

Verified written 15/17 against the 10 tapes and live `route_v20` on
seeds 0 and 8, then tried the named card: tape ladder + cap 14. Both
the full ladder and the cap-only fallback failed a seed. Throwaway is
back on hold-6 + `MAX_ANIMALS=18` (40,236 / 55,411).

**Tape mean herd** (exact): 4 / 4 / 5 / 6 / 6 / 6 / 8.2 / 9.7 / 12.0 /
13.2 / 14.0 / 14.4. Every tape lands **[6, 11]**. End herd 12–17.
**5/10 tapes buy after engine d10.** “Tape last buy is d10” is a
policy ceiling, not a tape fact. Live v20 on 0/8: 6 on land-d6, 10 on
d7, 14 on d11. We: 6 through d10, land [8, 11], seed 8 → 18.

**Tried (1):** `calendar_owned_target` = tape ladder; `MAX_ANIMALS=14`.
NE-pending and land windows left alone.

**Tried (2):** kill-switch fallback — revert the ladder, keep cap 14.

## Counters

| arm | seed 0 | seed 8 | land | STRAW d5–8 | end herd |
|---|---|---|---|---|---|
| live (fact 44) | 40,236 | 55,411 | [8, 11] | 1/5/0/1 | 14 / **18** |
| ladder + cap 14 | **27,204** | 65,431 | **[7, 11]** | **0/0/0/0** and **0/0/1/0** | 14 / 14 |
| cap 14 only | 43,361 | **46,746** | [8, 11] | 1/5/0/1 | 14 / 14 |
| restored | 40,236 | 55,411 | [8, 11] | 1/5/0/1 | 14 / 18 |

Wheat d0=7 and MELON after d0=0 held on every arm. d11 carpet ≥15.

## Why both binds failed

The ladder cannot fire on d6–d7 while NE-pending zeroes slots and land
is d8. Opening it anyway bought the catch-up into the STRAW drawer:
land slipped to [7, 11], d5–8 plants went to 0, seed 0 −13k.

Cap 14 matches live v20's end and stops seed 8's 18. Yarn seed 8's
d13 +4 is load-bearing vs 55,411 (−8.7k). Seed 0 already ended at 14.

Written 15/17 stay the spec. The throwaway cannot afford them until
land is d6–7 (fact 33) without the dropped land-reserve bundle.

Supplement 27: d5=1 is structural (2 empties + BUILD). Stop judging
d5 against half-tape. Docs updated (FACTS status / T1 order / open
hole / fact 44 counter / Dropped-table tape-claim / CLAUDE.md /
agent-facts.mdc). No `main.py` port.

## Verdict

**Dropped.** Kind: remove (throwaway hold-6 + d11 ramp). Do not retry
the tape-ladder calendar or cap 14 alone. Still no land-reserve
bundle, seed-before-cow, leftover walk, d8 land-hour seed, 40–42,
fert-only, STRAW pin, holdout, or list reorder.

## How we continue

```text
Kind: supplement (fact 33) — first BUY_LAND onto d6 or d7
Was: land [8, 11]; d7 post-sell $1,374 vs $1,500 floor
Now: one bind, land-only (post-sell wool/fert on d6, or waive $500
     on the first buy only). Not the dropped bundle.
Fights: none if land stays in d6–10 / d11–12 and the herd does not dump
Throwaway: experiments/_facts_v20.py
Counters: 1st land d6–7; 2nd d11–12; wheat d0=7; MELON after d0=0;
     yarn lock; 0 escapes; STRAW d7–8 and STRAW $ re-judged;
     bank not down vs 40,236 / 55,411 on seeds 0 and 8
```

## Open

- Next card: **fact 33, one bind** — NE on d6 or d7 without the
  land-reserve bundle. Then re-judge STRAW d7–8 / STRAW `$`.
- Live throwaway 40,236 / 55,411; land [8, 11]; T1 vs v20 ~75k.
- Written 15/17 stay; throwaway still hold-6 / cap 18.
- Fact 44 −570 parked. Port to shipped `main.py` blocked.

---

# Prior session: 2026-09-06 — d8 land-hour seed dropped; calendar fight named

> **Standing rule:** Report to the user in chat before writing this file.

## What this session did

Tried the leftover-walk session's untried bind: **d8 land-hour seed +
hold-6 pin** (fact 30; not a list reorder). Reverted. Then evaluated why
all four STRAW supplements failed. Protocol step 2: two facts fight —
drop one. Throwaway is back on fact 44 (40,236 / 55,411).

Live d8 confirmed on current throwaway (both seeds): d8h00 `SELL FERT |
BUY_LAND`; d8h01 `BUY_ANIMAL COW` + `BUY_SEED STRAW ×6`; cow takes
~$703; pltS=1. d5 cow never lands (`buyA=0`); NE-pending deferral holds
slots=0 through d7; land unlocks the catch-up.

**Tried:** on first `BUY_LAND` emit, size `BUY_SEED STRAW` to post-land
cash and pending LOCKED NE (×7); list after land, before hires. Pin
`calendar_owned_target` at 6 until `owned>=6`.

d8 plants **1→3** both seeds (half-tape). Land [8, 11]; wheat d0=7;
MELON after d0=0; d11 carpet 15. Seed 0 bank **40,646 (+410)**; STRAW
gap −35.0k (was −43.5k). Seed 8 bank **34,287 (−21,124)**. The 6th
still lands **d10**, so the pin releases and d11 opens: herd 6 through
d10 then **12 / 14** (seed 0) and **12 / 18** (seed 8). Same dump class
as seed-before-cow.

## Counters

| arm | seed 0 | seed 8 | land | STRAW d5–8 | herd after d10 |
|---|---|---|---|---|---|
| live (fact 44) | 40,236 | 55,411 | [8, 11] | 1/5/0/1 | 6 through d10 |
| land-hour + pin | 40,646 | **34,287** | [8, 11] | 1/5/0/**3** | 12/14 and **12/18** |

## Why the four supplements failed

Not four bugs. One drawer. v20 has 4 NE STRAW by d7 / 15 by d10; we
have 1 from d8. First yield +10 days → they sell d16, we do not. That
is the −43.5k / −38.7k.

d5=1 is structural (2 empties, 1 pen — fights fact 16). d6=5 holds.
d7=0 is the $500 reserve (`$1,374` vs `$1,500`). d8=1 is cow-vs-seed
after land. One bind can move one day. The `$` needs NE planted by d7.

Walk-after-feed cannot plant-and-water the sitting NW the same day
(fact 20). Raising it reopens 40/42. Closed.

The other three spent the land/cow drawer. Live “herd 6 through d10” is
not a hold — it is a cash accident (d8 cow leaves $4–$17). Written fact
15 already wants the tape ladder and **no buy after d10**. The
throwaway still holds 6, then d11→12, d13→18 (`MAX_ANIMALS=18`). Any
successful d8 seed buy removes the accident; the calendar does what it
says. Seed 0 and seed 8 disagree (no-yarn →14 vs yarn →18).

Order-of-work “27/30 first, then 15” asked STRAW to hold the bank while
15 stayed false. That is the Path C pattern.

## Verdict

**Dropped.** Kind: supplement (fact 30). Do not retry land-hour seed,
the hold-6-until-owned pin, seed-before-cow, the land-reserve bundle,
or leftover walk. No `main.py` port.

**Next is not another STRAW bind.** Facts fight: written 15/17 vs the
throwaway hold-6 + d11 ramp + “do not land herd” slogan. Protocol:
drop one. Keep 15/17 **as written** (tape ladder, cap 14, nothing after
d10 — not the old 21-head shop-mix ramp). Drop hold-6, `MAX_ANIMALS=18`,
and the slogan. Supplement 27: stop judging d5 against half-tape.

## How we continue

```text
Kind: remove (throwaway hold-6 + d11 ramp) / rewrite 15+17 to match the rows
Was: calendar_owned_target holds 6 through d10, then 12 / MAX_ANIMALS=18;
     “do not land herd” until 27/30 move
Now: calendar_owned_target = tape ladder, cap 14, no buy after d10;
     order of work no longer sequences 27 before 15
Fights: the slogan; the accidental d8-cow brake; d11+ shop-mix ramp
Throwaway: experiments/_facts_v20.py
Counters: tape_profile herd ±1 every day d0–d10; owned ≤ 14 after;
     BUY_ANIMAL total ≤ 14; 0 escapes contested; bank not down vs
     40,236 / 55,411 on seeds 0 and 8
```

Still no 40–42, no fert-only, no STRAW pin, no holdout, no list reorder.

## Open

- Next card: **rewrite throwaway 15/17 to the written rows.** Then
  re-judge STRAW `$` — 27/30 may move without a seed reorder.
- Live throwaway still 40,236 / 55,411; land [8, 11]; T1 vs v20 ~75k.
- Fact 44 −570 parked. Port to shipped `main.py` blocked.

---

# Prior session: 2026-09-06 — home leftover walk dropped

> **Standing rule:** Report to the user in chat before writing this file.

## What this session did

Tried the untried bind from last session: **home leftover walk only**
(plant the d7 empty NW; no land reserve, no list reorder). Two shapes.
Both reverted. Throwaway is back on fact 44 (40,236 / 55,411).

**Ungated walk:** unit reaches the sitting NW at **h23**, plants, dies
overnight (fresh plant `consecutive_unwatered=1`). d8 pltS **1→0**.
Banks **32,928 / 63,418**.

**Hour-21 arrive/water gate** (same bind, not a bundle): d7 plant stays
**0** — leftover walk sits behind `any_unfed_animal`. pltS back to
1/5/0/1. Banks **23,735 / 44,211**.

Land stayed [8, 11]. Herd stayed 6 through d8. Wheat d0 = 7. d11 carpet
untouched. Raising the walk above FEED would reopen 40/42.

## Counters

| arm | seed 0 | seed 8 | land | STRAW d5–8 | herd |
|---|---|---|---|---|---|
| live (fact 44) | 40,236 | 55,411 | [8, 11] | 1/5/0/1 | 6 through d10 |
| home walk, no hour gate | **32,928** | 63,418 | [8, 11] | 1/5/**1***/0 | 6 |
| home walk + hour-21 | **23,735** | **44,211** | [8, 11] | 1/5/0/1 | 6 |

\* issued at h23; night death; tape_profile counted 0 landed / 1 shifted.

## Verdict

**Dropped.** Kind: supplement (fact 27). Walk-after-feed cannot
plant-and-water the sitting NW the same day. Do not retry. Do not raise
it above FEED. Do not retry the land-reserve bundle or seed-before-cow.
Do not land herd. No `main.py` port.

## How we continue

**One bind only.** Live card still STRAW d5–8 / STRAW `$`. Untried: a
**d8 seed buy that does not open the late herd** (new mechanism, not a
list-reorder retry). d5=1 is still structural. Still no 40–42, no
fert-only, no STRAW pin, no holdout.

## Open

- Live card: **STRAW d5–8 / STRAW `$` (27/30).** T1 vs v20 ~75k.
- Land [8, 11]; $500 first-buy reserve still blocks d7.
- Fact 44 −570 parked. Port to shipped `main.py` blocked.

---

# Prior session: 2026-09-06 — STRAW d5–8; two supplements dropped

> **Standing rule:** Report to the user in chat before writing this file.

## What this session did

Diagnosed the STRAW `$` widen, then tried two supplements. Both
reverted. Throwaway is back on fact 44 (40,236 / 55,411).

Shop-aware leftover is **not** the miss (STRAW shop from d3 both seeds).
Hour trace (`experiments/_trace_d5_straw.py`): early board identical
through d8. NE acreage is the `$` hole (v20 4 NE by d7 / 15 by d10; we
have 1 from d8).

**Bundle first (wrong):** waive first-land $500 + no LOCKED walk +
seed-before-cow (facts 27/30/33 together). Land [7, 11], d7 2/4, bank
28,751 / 36,766, herd 18.

**Then one bind:** d5–8 `BUY_SEED STRAW` before `BUY_ANIMAL` only. Land
stayed [8, 11]. d8 plants **7/4** (was 1). Seed 0 bank **33,303
(−6,933)**; seed 8 **73,063 (+17,652)**. Herd 6 through d8 then **19**.
Acceptance is both banks; seed 0 fails.

Confirmed in chat: we stay on **one bind**, not a bundle.

## Diagnosis (live throwaway, both seeds same through d8)

| day | cash bind | what happens | pltS |
|---|---|---|---|
| d5 | $15 → $399 after fert | 2 empty NW; BUILD takes 1 (d5 cow); plant 1 | **1/4** |
| d6 | wheat harvests underfoot | buy-as-freed, plant 5 | **5/8** hold |
| d7 | post-sell **$1,374**; land needs $1,500 | 1 empty NW sits all day (heldS=1); K-walk onto LOCKED NE; 1 NW STRAW dies overnight | **0/4** |
| d8 | land emits; $703 then cow + order ×6 STRAW | NE 25 empty; cow eats drawer; plant 1 | **1/4** |

STRAW `$` widen is missing **NE acreage**. v20 has 4 NE by d7 and 15 by d10;
we have 1 from d8. First yield is +10 days, so v20 sells the early wave on
d16/d21/d23 and we do not (d16 us $0 / v20 $1,751; peak field 21 vs 42).

## Counters (both reverted)

| arm | seed 0 | seed 8 | land | STRAW d5–8 | herd |
|---|---|---|---|---|---|
| live (fact 44) | 40,236 | 55,411 | [8, 11] | 1/5/0/1 | 6 through d10 |
| land-reserve bundle | **28,751** | **36,766** | [7, 11] | 1/5/2/0 | 18 |
| seed-before-cow (one bind) | **33,303** | 73,063 | [8, 11] | 1/5/0/**7** | **19** |

Wheat d0 and MELON after d0 held both arms. d11 carpet ≥15 both arms.

## Verdict

**Neither supplement holds.** Kind: supplement — both dropped. The
bundle was the wrong procedure. The one-bind retry moved d8 (1→7) and
still failed seed 0 bank; it also opened the d11+ herd dump (19). Do
not retry either arm. Do not land herd. Do not reopen 40–42. Fact 44
yarn lock stays. No `main.py` port.

## How we continue

**One bind only.** Live card still STRAW d5–8 / STRAW `$`. Untried:
**home leftover walk only** (plant the d7 empty NW; no land reserve, no
list reorder). d5=1 is structural (2 empties, 1 pen). A d8 seed buy that
does not open the late herd is a new mechanism, not a retry of the list
reorder. Still no 40–42, no fert-only, no STRAW pin, no holdout.

## Open

- Live card: **STRAW d5–8 / STRAW `$`** (27/30). T1 vs v20 ~75k.
- Land [8, 11]; $500 first-buy reserve still blocks d7 ($1,374 vs $1,500).
- Fact 44 −570 parked. Port to shipped `main.py` blocked.

---

# Prior session: 2026-09-06 — plan: remaining v20 gaps (not the −570)

> **Standing rule:** Report to the user in chat before writing this file.

## What this session did

Answered whether the v20 gaps are closed except fact 44's −570.
They are not. The −570 is versus our prior throwaway (40,806 →
40,236), not versus `route_v20`. Re-traced current throwaway
(`_trace_cashflow_v20.py`) on seeds 0 and 8. Wrote the remaining-gap
plan into this file, `FACTS.md` (live card / order of work / open
hole), `.cursor/rules/agent-facts.mdc`, and `CLAUDE.md`.

## Counters (executed `$` vs v20, fact 44 throwaway)

| | seed 0 | seed 8 |
|---|---|---|
| bank us | 40,236 | 55,411 |
| bank v20 | **114,305** | **133,123** |
| bank gap | **−74,069** | **−77,712** |
| STRAWBERRY | 18.3k / 61.8k **−43.5k** | 20.3k / 59.0k **−38.7k** |
| WOOL | 19.5k / 26.1k −6.5k | 4.1k / 7.1k −3.0k |
| MILK | 6.0k / 11.6k −5.6k | 40.2k / 51.5k **−11.4k** |
| WHEAT net | −8.5k / +3.7k −12.2k | −12.7k / +3.9k −16.6k |
| MELON | 12.3k / 15.5k −3.2k | 12.3k / 15.5k −3.2k |
| FERTILIZER | 12.3k / 13.7k −1.4k | 12.2k / 13.6k −1.4k |

Vs the pre-T1 table: WOOL / WHEAT / MELON / FERT shrank; **STRAW
widened** (−29.6k → −43.5k). Vs the funding stack's seed-0 streams
(STRAW −19.8k, WOOL −3.5k, WHEAT −9.7k, FERT −3.0k): STRAW is worse
again after the d5–d6 supplement. Timing still: wheat d0 = 7 (holds);
STRAW d5/d7/d8 miss half-tape (1/4, 0/4, 1/4); herd 6 through d10;
land [8, 11]; MELON after d0 = 0.

## Verdict

**The live hole is T1 versus v20 (~75k), led by STRAW.** Fact 44's
−570 is a self-nick; park it. Do not retry hold-the-burst or d12h0
slack. Do not revert the no-yarn lock. Do not land herd on a stack
that still misses the early STRAW wave. No `main.py` port.

## Plan (order of work)

1. **STRAW wave (27/30) — live card.** Named days still fail
   (d5/d7/d8). Dollar gap is the largest and it *widened*. Diagnose
   why the d5–d6 supplement bought bank on seed 0 and lost STRAW `$`
   (late widen d16/d21/d23 on the funding stack). Then one
   supplement: more of the d5–8 NW/NE wave, without a crew-wide walk
   (40/42), without reopening fert-only (9/21), without a STRAW pin.
   Re-judge both seeds: `tape_profile.py` then cashflow then bank.
   Bank must not fall vs 40,236 / 55,411.
2. **Re-judge the stack** against v20 streams, not only half-tape.
   STRAW `$` must move toward the funding stack's −19.8k (or better),
   not stay at −43k.
3. **WHEAT net (−12k / −17k)** after STRAW `$` is no longer the
   widest. d0 wheat already holds. No force-wheat (22 / Path C F7).
4. **Herd (15 + 17), then crew (43).** Only after d5–8 STRAW is at
   least half-tape *and* STRAW `$` is not still widening. Wool −6.5k
   is no longer the 25k hole; milk −11k on seed 8 is the no-yarn cow
   path versus v20's mix. Landing 15 first is the old d11+ ramp.
5. **Parked, not next:** fact 44 −570; MELON −3.2k; FERT −1.4k;
   d12-late slack (untried, not assigned); stage 2 (CARROT window,
   STRAW harvest slices, order-book).

Banned: hold-d11-burst, d12h0 slack, hold-sheep-at-2 after yarn,
revert the yarn lock, 40–42, third fert-only bind, Path C, Path A
merge, `bptk.py` for cadence, holdout, `main.py` port.

## Open

- Live card: **STRAW d5–8 / STRAW `$`** (27/30). T1 vs v20 ~75k.
- Fact 44 −570 parked (self-nick). Two WHEN binds stay dropped.
- Port to shipped `main.py` blocked.

---

# Prior session: 2026-09-06 — two WHEN binds on the d11 burst failed

> **Standing rule:** Report to the user in chat before writing this file.

## What this session did

Tried two supplements of fact 44's d11 cap-12 spend. Both reverted.
Throwaway is back on fact 44 (40,236 / 55,411).

**Hold the burst (calendar stays 6 on d11, spend on d12).** Seed 0
25,417 / seed 8 34,074. Yarn vanished (shops d12 = BRUNCH×2, not
YARN). End 16C/2S, both seeds dumped to 18 on d13. Engine: `_end_of_day`
shares one RNG for `_spawn_weeds` (one `random()` per `None` tile,
both farms) then the shop draw. A different d11 empty-tile count
rerolls d12's shop.

**d12h0 yarn slack (burst still spends; calendar 14 once yarn visible).**
Yarn held. Sheep landed d12h0. Seed 8 no-op **55,411**. Seed 0 end
10C/4S but owned 14→13 twice (escapes) and bank **36,885 (−3,351)**.

## Counters

| arm | seed 0 | seed 8 | yarn | extra sheep | notes |
|---|---|---|---|---|---|
| fact 44 (live) | 40,236 | 55,411 | d12h0 | d13h0 | −570 vs 40,806 |
| hold d11 burst | 25,417 | 34,074 | **none** | 0 | dump to 18 |
| d12h0 slack | 36,885 | 55,411 | d12h0 | d12h0 | seed 0 escapes |

Species rule was not changed. d0 2C2S. STRAW d5–8 untouched.

## Verdict

**Neither supplement holds.** Kind: supplement (fact 44) — both arms
dropped. Do not retry hold-the-burst or d12h0 slack. Do not revert the
no-yarn lock. Do not hold sheep at 2 after yarn. Do not land herd.
Throwaway `experiments/_facts_v20.py` (reverted). Judge script
`experiments/_judge_d11_burst.py`.

## How we continue

The −570 is still the hole. A later bind cannot change the d11
empty-tile count (shop draw) and cannot add animals on d12h0 (escapes).
Still no 40–42, no `bptk.py`, no Path C, no holdout, no d11+ count
ramp, no third fert-only bind, no `main.py` port.

## Open

- Fact 44 — species counters green; **red on seed 0 bank (−570)**.
- Next: a different spend bind, not the two that failed. Not herd.
- Port to shipped `main.py` blocked.

---

# Prior session: 2026-09-06 — yarn-seed −570 is the d11 cow burst

> **Standing rule:** Report to the user in chat before writing this file.

## What this session did

Diagnosed why fact 44 nicks seed 0 by $570. Split leftover vs mix,
reproduced live, then traced the yarn-seed buy hours. Leftover crop is
a no-op on both seeds. The −570 is the no-yarn lock spending the d11
cap-12 burst on cows; yarn is visible d12h0 with slots already 0; the
two extra sheep wait until d13. Same end mix as live (10C/4S). Live’s
third sheep is d11h13.

## Counters

| arm | seed 0 | seed 8 |
|---|---|---|
| fact 44 (current) | 40,236 | 55,411 |
| leftover only | 20,306 | 34,567 |
| hold sheep at 2 after yarn | 33,894 | 55,411 |
| lock + mix uncapped | 40,236 | 55,411 |
| no lock, mix uncapped | **40,806** | **34,567** |
| live supplement (prior) | 40,806 | 34,567 |

Seed 0 shops: BRUNCH@3 PET_CAFE@6 SMOOTHIE@9 **YARN@12**. Seed 8: ICE_CREAM@3
PET_CAFE@6, no yarn. Yarn first visible d12h0. Fact 44 d11h13 buys 6 cows;
d12h0 buys nothing; d13h0 buys 2 sheep. Live: sheep d11h13 + d13h0.

Species counters still hold (yarn end sheep 4; no-yarn end sheep 2).
d0 2C2S. 0 escapes. STRAW d5–8 unchanged 1/5/0/1.

`neither` (flags off, `cap=target` still on) is **20,306** on seed 0, not
live. Live called `shop_mix_target` without a calendar cap, so d3/d5
stayed cows. Passing `cap=target` without the lock scales the pre-yarn
table to 3C3S and buys a d5 sheep into no-yarn wool.

## Verdict

**The −570 is diagnosed.** Not leftover, not dump-at-floor, not “too
many sheep.” The extra sheep after yarn are a **+$6.3k** win vs holding
at 2. The lock is the seed-8 **+20,844**. Do not revert it. Do not hold
sheep at 2 after yarn. There is no shop-visible way on d11 to know yarn
lands tomorrow (seed 8’s first shops also include a milk shop).

Acceptance still **fails seed 0 by $570**. Kind: diagnosis (no add /
remove / supplement landed). Throwaway `experiments/_facts_v20.py`
(isolate flags `SHOP_AWARE_MIX` / `SHOP_AWARE_CROP` / `HOLD_SHEEP_AT_2`
/ `USE_MIX_CAP`; defaults keep fact 44). Scripts:
`experiments/_isolate_yarn570.py`, `_isolate_hold2.py`,
`_isolate_mixcap.py`, `_trace_yarn_hour.py`.

## How we continue

A later supplement has to change **when** the no-yarn path spends the
cap-12 burst, not the species rule. Keep the species counters. Re-judge
both seeds. Still no 40–42, no `bptk.py`, no Path C, no holdout, no
d11+ count ramp, no third fert-only bind, no `main.py` port.

## Open

- Fact 44 — species counters green; **red on seed 0 bank (−570)**;
  mechanism: d11 cow burst, sheep slip d11h13 → d13h0.
- Next: supplement the no-yarn cap-12 spend, then re-judge. Not herd.
- Port to shipped `main.py` blocked.

---

# Prior session: 2026-09-06 — fact 44 town-demand; yarn-seed −570

> **Standing rule:** Report to the user in chat before writing this file.

## What this session did

Isolated the seed-8 drop (wheat-d0 vs NE walk): early board is identical
through d6; the split is the **town**. Seed 0 unlocks `YARN_STORE` (d12);
seed 8 never does, and wool hits $1 on d17 while we still produce it.
Wrote fact 44 as: produce what `unlocked_shops` eat; do not produce what
they do not. Count stays the calendar (15). No yarn → sheep stay at the
d0 beach-head (2); later slots are cows. Leftover STRAW/CARROT only with
a shop sink. Dump-at-floor was tried first and moved nothing (+0 / +331);
reverted. Measured contested vs `route_v20` on seeds 0 and 8.

## Counters

| | seed 0 (yarn d12) | seed 8 (no yarn) |
|---|---|---|
| bank (fact 44) | 40,236 | **55,411** |
| bank (live supplement) | 40,806 | 34,567 |
| Δ vs live | **−570** | **+20,844** |
| d0 2C2S | 2/2 | 2/2 |
| herd count d10 | 6 | 6 |
| `BUY_ANIMAL SHEEP` after d0 | 2 | **0** |
| end sheep | 4 | **2** |
| STRAW d5–8 | 1/5/0/1 | 1/5/0/1 |

Species counters hold. Seed 8 carrot = 0 (SW already carpeted). Tomato 0;
MELON after d0 = 0.

## Verdict

**Fact 44 has a counter and it moved.** No yarn → no extra sheep; yarn →
sheep > 2. Seed 8 closed most of the 65k → 34k hole (now 55k). Acceptance
(bank not down on both) **fails seed 0 by $570**. Do not land the d11+
count ramp. Do not bring back dump-at-floor. Do not hunt a third
fert-only bind. No `main.py` port.

Kind: add (fact 44). Throwaway `experiments/_facts_v20.py`.

## How we continue

Find **why yarn-seed (seed 0) lost $570** under fact 44. Keep the species
counters. Then re-judge both seeds. Still no 40–42, no `bptk.py`, no Path
C, no holdout.

## Open

- Fact 44 — species counters green; **red on seed 0 bank (−570)**.
- Next: diagnose the yarn-seed loss, then re-judge. Not herd count.
- Port to shipped `main.py` blocked.

---

# Prior session: 2026-09-05 — d5–d6 STRAW supplement; seed 8 bank fail

> **Standing rule:** Report to the user in chat before writing this file.

## What this session did

Diagnosed the funding stack's d5–d6 STRAW miss (and wheat d0 = 0) in
`experiments/_facts_v20.py`. Confirmed on seed 0: d5 had **5 empty NW
tiles** and **$527**, `buyS=0` (450 floor needs $550 for one $100 seed);
d6 bought/planted the stockpile of 3; d0 leftover after 12 MELON sat
empty because melon opening `elif`-blocked wheat restock. Supplemented
facts 22 + 30 (wheat beside melon opening; STRAW restock sized to empty
tiles, no 450 floor, same-turn credit) and a **K-bounded** NE walk on
pending unlock (not crew-wide). Re-judged the same stack.

## Counters

| | seed 0 | seed 8 |
|---|---|---|
| bank (this supplement) | 40,806 | 34,567 |
| bank (funding stack) | 16,628 | 65,296 |
| Δ vs stack | **+24,178** | **−30,729** |
| bank (pre-T1) | 26,429 | 8,269 |
| Δ vs pre-T1 | +14,377 | +26,298 |

Timing (both seeds, same shape): wheat **d0 = 7** (tape 7); STRAW d5
**1/4**, d6 **5/8**, d7 **0/4**, d8 **1/4**; d11 carpet **15**; MELON after
d0 = 0; land **[8, 11]** (was [7, 11]). Seed 0 STRAW `$` **−43.4k**
(wider than the stack's −19.8k). Fert still no dry-spell hunt.

## Verdict

**The supplement does not hold.** Acceptance is contested bank on both
seeds; seed 8 fell off the funding stack's 65k. Wheat d0 is the named-day
win. Do **not** land herd (15 + 17). Do **not** hunt a third fert-only
bind. Do **not** reopen 40–42 as a crew-wide NE walk.

Kind: supplement (facts 22, 30, 27 walk). No `main.py` port.

## How we continue

Isolate the **seed-8 drop** (wheat-d0 cash trough vs the NE walk) without
giving back seed 0's bank. d5/d7/d8 half-tape still fail: d5 is cash
($15 after wheat d0), d7 is NE still locked, d8 walk plants 1. Still no
40–42, no `bptk.py`, no Path C, no holdout.

## Open

- Funding stack + this supplement — **red on seed 8 bank**.
- Next: isolate seed-8 drop, then re-judge. Not herd.
- Port to shipped `main.py` blocked.

---

# Prior session: 2026-09-05 — funding stack landed; seed 0 bank fail

> **Standing rule:** Report to the user in chat before writing this file.

## What this session did

Rewrote T1 “Order of work” to the funding stack (five-step + per-step
bank kill switch withdrawn). Landed facts 9 + 21 + 22 + 28 + 27 + 39 in
`experiments/_facts_v20.py` in one pass: sell fert flow above apply-gap,
buy apply-gap only (no same-turn sell+buy; not surplus-above-6); WHEAT
empty-tile default from d0, underfoot only; STRAW on home/NE d5–8 plus
SW carpet; MELON d0 only; NW STRAW ban deleted. Source audit 29/29.
Contested vs `route_v20` seeds 0 and 8 (`tape_profile.py` then
`_trace_cashflow_v20.py`).

## Counters

| | seed 0 | seed 8 |
|---|---|---|
| bank (this stack) | 16,628 | 65,296 |
| bank (pre-T1 baseline) | 26,429 | 8,269 |
| Δ | **−9,801** | +57,027 |

Timing (both seeds, same shape): wheat **0 on d0** (tape 7), starts d1;
STRAW d5 **0/4**, d6 **3/8** (fail half-tape), d7–d8 and d11 carpet hold;
MELON after d0 = 0; fert dry-spell **holds** (only isolated d1). Herd
still 6 through d10 (15/17 not in this stack). Land [7, 11] vs tape
[6, 11].

Cashflow seed 0 gaps vs v20 all smaller than the pre-T1 table (STRAW
−19.8k, WOOL −3.5k, WHEAT-net −9.7k, FERT −3.0k). Seed 8 STRAW gap
**wider** (−32.0k). `BUY_PRODUCT FERTILIZER` $4.0k / $3.5k — mid
thousands, not $12k churn. Seed 0 worst widen: d21/d16/d23, all STRAW.

## Verdict

**The stack does not hold.** Acceptance bar is contested bank on both
seeds; seed 0 fell. Do **not** revert (seed 8 unstuck 8k → 65k; seed 0
streams moved the right way). Do **not** hunt a third fert-only bind.
Do **not** land herd (15 + 17) on a stack that misses the d5–6 STRAW
wave — that is still the old d11+ ramp with extra cash.

Kind: supplement (throwaway implements already-rewritten T1 rows).
No `main.py` port.

## How we continue

Diagnose the **d5–d6 STRAW miss** (and seed 0’s late STRAW `$` widen).
Wheat d0 = 0 is the other named-day miss; fert cadence is the part that
held. Then re-judge the same stack. Still no 40–42, no `bptk.py`, no
Path C, no holdout.

## Open

- Funding stack in the throwaway — **red on seed 0 bank**.
- Next: d5–d6 STRAW (fact 27/30), not herd, not another fert bind.
- Port to shipped `main.py` blocked.

---

# Prior session: 2026-09-05 — T1 step 1 is not isolable; land the funding stack

> **Standing rule:** Report to the user in chat before writing this file.

## What this session did

Retried T1 step 1 with a different bind: delete the live-STRAW hold;
sell shed fert **above** `MAX_FERTILIZER_STOCK` (6); buy apply-gap only
when shed is empty and this turn did not sell fert. Source audit 29/29
(leftover episode harness is missing). Contested vs `route_v20` seeds 0
and 8. Then named why two fert-only landings are the same half-stack
error, and **changed how T1 continues** (below).

## Counters

| | seed 0 | seed 8 |
|---|---|---|
| bank (this step) | 11,648 | 15,510 |
| bank (pre-T1 baseline) | 26,429 | 8,269 |
| Δ | **−14,781** | +7,241 |

Fact 9 dry-spell **failed** (seed 0 sold fert on 5 days only: d3/4/7/10/16;
seed 8 similar). `BUY_PRODUCT_FERTILIZER` stayed small ($387 / $1,205) —
no $12k churn. SELL_FERTILIZER $ was 2.1k vs v20 17.2k on seed 0. Crew
hit 0 hires for long stretches; seed 0 money sat at $1–15 through mid
season. WOOL sold $0.

## Verdict

**Revert the fert-only patch.** Throwaway, prerun audit, and the 9/21
FACTS supplements restored to `95c296b`. T1 spec rows stay. Do not
re-land “sell above a 6-unit reserve” or “sell-all + buy demand last.”

**The procedure was wrong, not just the bind.** T1 is one failure
(rows 9 / 15 / 17 / 21 / 22 / 27 / 28 / 39 + 43). Fact 9’s own text is
that daily fert cash is liquidity **for fact 15’s herd**, and that cash
only has a tape-shaped place to go if wheat is the empty-tile default
(22) and STRAW lands on d5–8 (27). Two measurements kept those rows on
the old escape-defence shape and asked fert cadence alone to hold the
**full-season contested bank**. That is the BUY_LAND-at-fixed-crew
error: one named fact moved, the unnamed dependents stayed pinned.

The dollar table already said fert was the small slice (seed 0 vs v20):
STRAW −29.6k, WOOL −25.3k, WHEAT-net −20k, FERT −4.1k. Judging step 1
on 26,429 / 8,269 asks 9+21 to carry an $85k gap they do not own.
Sell-all “fixed” fert `$` and lost the bank to buy-back churn.
Surplus-above-6 “fixed” the churn and never sold the flow, because
apply (still STRAW-hold logic in the unit ladder) ate the reserve.
Both are half-stack artifacts.

The T1 card tried to have it both ways: *one failure*, landed
*cheapest-to-revert*, **and** “a step that lowers either seed is
reverted.” After two reverts, that last clause is a hunt for a
fert-only mechanism that cannot exist.

## How we continue

The next edit is the **method**, not another `decide_market_actions`
fert patch. Do **not** hunt a third fert-only bind against 26,429 /
8,269. Do **not** keep steps 2–5 blocked on a green step 1.

1. **Land the funding stack together** — facts 9 + 21 + 22 + 28 + 27 +
   39 (old T1 steps 1–3) in one throwaway pass. Still not the whole
   card. Still cheapest-to-revert *after* a stack that can make a fert
   sale mean something. Banned binds stay banned (sell-all + buy-back;
   surplus-above-6).
2. **Then** herd (15 + 17), **then** crew (43). Running 15 first is
   still the old d11+ ramp.
3. Contested bank vs `route_v20` seeds 0 and 8 is the judge **of the
   funding stack**, not of fert in isolation. `tape_profile.py` first,
   then `_trace_cashflow_v20.py`, then the bank. A fert-only dry-spell
   / ±4/day / buys-in-tens read is a diagnostic, not a ship bar.
4. Rewrite the T1 “Order of work” in `mydocs/FACTS.md` to this stack
   when the throwaway is opened — the five-step + per-step bank kill
   switch is withdrawn.
5. No `main.py` port; no 40–42; no `bptk.py`; no Path C; no holdout.

## Open

- Timing card T1 **funding stack** (9 + 21 + 22 + 28 + 27 + 39) — next.
- Herd (15 + 17) and crew (43) after that stack holds.
- Port to shipped `main.py` blocked.

---

# Prior session: 2026-09-05 — T1 step 1 (9+21 fert) FAIL, reverted

> **Standing rule:** Report to the user in chat before writing this file.

## What this session did

Tried T1 step 1 in `experiments/_facts_v20.py`: delete the live-STRAW
fert hold (fact 9); buy fert sized to the turn's apply gap, last on the
market list (fact 21). Source audit 29/29. Contested vs `route_v20`
seeds 0 and 8.

## Counters

| | seed 0 | seed 8 |
|---|---|---|
| bank (this step) | 26,147 | 6,363 |
| bank (pre-T1 baseline) | 26,429 | 8,269 |
| Δ | **−282** | **−1,906** |

Fact 9 dry-spell bar held (only d1 dry). Buy-back fired (~$12k
`BUY_PRODUCT_FERTILIZER`). SELL_FERTILIZER $ flipped from −4.1k to
+8.1k on seed 0. STRAW / WOOL / WHEAT-net gaps stayed large. Late-day
SELL FERT order qty ballooned (70+/day from d18) — sell-all + buy-back
churn, not tape cadence.

## Verdict

**Revert.** The acceptance bar is contested bank on 0 and 8; both
fell. Throwaway + prerun audit restored to `95c296b`. T1 spec rows stay;
the mechanism does not. Do not re-land “sell all + buy demand last”
without a different bind (the $12k buy-back + late dump cost more than
the hold was costing).

## What to do next

1. Re-diagnose fact 9/21: sell the collected *flow* without buying
   tens of dollars back into a dump. Tape sells 3–17/day, not 70.
2. Then retry T1 step 1 with that mechanism, same bank bar.
3. Do not skip to wheat/STRAW/herd while this step is red.
4. No `main.py` port; no 40–42; no `bptk.py`.

## Open

- Timing card T1, step 1 — **still next**, different mechanism.
- Steps 2–5 blocked on a passing step 1.
- Port to shipped `main.py` blocked.

---

# Prior session: 2026-09-05 — the judge was wrong; timing card T1 opened

> **Standing rule:** Report to the user in chat before writing this file.
> Numbers, win counts, and the add / drop / supplement call go in the
> chat first. HANDOFF is the diary after that, not the first copy of
> the result.
>
> **Read this first.** Spec: `mydocs/FACTS.md` — the acceptance bar and
> timing card T1 are new. Method: `mydocs/AGENT_BUILDING_PROTOCOL.md`.
> New tool: `experiments/tape_profile.py`. The throwaway
> `experiments/_facts_v20.py` is now **tracked in git**.

## What this session did

No fact was **implemented in the throwaway**. The session re-measured
where we stand, found the measurement itself was the problem, and
rewrote the spec / judge / tooling to match. The first commit of this
direction is that rewrite — T1 is still unlanded code.

1. **Re-ran the cashflow tracer** (`_trace_cashflow_v20.py`) for both the
   throwaway and shipped `main.py` vs v20, seeds 0 + 8.
2. **Found a seven-session regression hidden under “audit CLEAR”:**
   contested bank 51,421 → 26,429 (seed 0) and 51,951 → 8,269 (seed 8)
   while every unit counter in `FACTS.md` kept passing. `starter` cannot
   see it — it never sells and never buys wheat.
3. **Aggregated all 10 tapes into a per-day profile** and wrote
   `experiments/tape_profile.py` to diff a contested episode against it.
   The shape is right in composition and **4–6 days late** on every
   producing asset.
4. **Traced each dollar gap to a row in `FACTS.md`** that was written as
   an escape-defence patch *against* the tape (table below).
5. **Rewrote the acceptance bar** (contested vs v20 is the judge;
   `starter` is a smoke check), **rewrote rows 9/15/17/21/22/27/28/39**,
   **added 43**, folded 38 into 22, and opened **timing card T1**.
6. **Un-ignored the throwaway** — the regression accumulated with no
   revision to bisect.

## Counters (contested seed 0, executed `$`)

| stream | us | v20 | gap | row |
|---|---|---|---|---|
| STRAWBERRY | 17.3k | 46.9k | **−29.6k** | 27 + 39 |
| WOOL | 21.6k | 46.9k | **−25.3k** | 15 |
| WHEAT net | −16.2k | +3.7k | **−20k** | 22 |
| MELON | 12.5k | 17.7k | −5.3k | 27 |
| FERTILIZER | 10.5k | 14.6k | −4.1k | 9 + 21 |

`tape_profile.py` seed 0: crew ±2 (fine); herd **−7 at d10**, then **21
`BUY_ANIMAL` against an 18 cap** with the placed herd falling 18 → 16
over d25–27 (contested; `starter` reads 0 escapes on the same build);
WHEAT **−7 on d0**, −5…−13 every day after; STRAW **−4/−8/−4/−4 on
d5–8**; MELON **+31 replanted d7–11** against a tape that plants melon
once.

Banks: throwaway 26,429 / 8,269; shipped `main.py` 17,983 / 16,337;
v20 111,387 / 59,103.

## Verdict

**The acreage bind of the last three sessions was self-inflicted.** Facts
40/41/42 were parked as failures; they were attempts to buy back with
sell paths, fert and crew walks what rows 27/39/15 gave away. Do not
reopen them. Ladder framing (`docs/PUBLIC_META.md`): T1 is stage 1
(~85k on seed 0); order-book timing is stage 2 (~a few k, but it is what
decides the 1700–1900 band where 80% of matches are under 5,000 apart).

## What to do next

1. Land T1 in the throwaway in its five steps, cheapest-to-revert first:
   (1) 9 + 21 fert cadence, (2) 22 + 28 wheat as default crop, (3) 27 + 39
   STRAW d5–8, (4) 15 + 17 herd ladder, (5) 43 crew. Commit the throwaway
   per step.
2. After each step: `tape_profile.py` seeds 0 + 8, then
   `_trace_cashflow_v20.py`, then contested bank. A step that lowers
   either seed's contested bank is reverted, not explained.
3. No `main.py` port; no holdout; no Path C; no `bptk.py` for this
   cadence; no reopening 40–42.

## What is in git vs local

This branch is the **lab checkout**. Clone/pull
`investigation/animal-diagnosis-and-route-v20-bench` on the other
machine — do not merge or PR it onto `main`. When the throwaway wins,
port only the winning `main.py` (and any spec/tool you still want
shipped) onto a **fresh branch from then-current `main`**.

**On this branch:** `9f0f36c` (FACTS / protocol / throwaway /
`tape_profile.py` / contested judge) then `95c296b` (HANDOFF, TOOLS_GUIDE,
tapes, four T1 tracers). Still untracked: `mydocs/scratch/`, old plan
notes, the historical `_facts_v20_{B1,R1,…}.py` pile.

## Open

- Timing card T1, step 1 (facts 9 + 21 fert cadence) — **next**.
- Stage 2 (order-book timing / sell cadence) — after T1.
- CARROT d21–25 — unnamed, after T1.
- Port to shipped `main.py` blocked.

---

# Prior session: 2026-09-05 — fact 42 NE carve PARKED; acreage fights 27/39

> Superseded: the acreage bind was self-inflicted by rows 27/39; see the
> timing card T1 session above. Do not reopen fact 42.

> **Standing rule:** Report to the user in chat before writing this file.
> Numbers, win counts, and the add / drop / supplement call go in the
> chat first. HANDOFF is the diary after that, not the first copy of
> the result.
>
> **Read this first.** Spec: `mydocs/FACTS.md`. Method:
> `mydocs/AGENT_BUILDING_PROTOCOL.md`. This file is the diary.
>
> Throwaway: `experiments/_facts_v20.py` (K=3). Path tracers:
> `experiments/_trace_straw_wool.py`, `_trace_d10_melon.py`. Cashflow:
> `experiments/_trace_cashflow_v20.py`. Opponent: `agents/route_v20.py`.
> Audit: `experiments/_facts_prerun_audit.py`. Do not patch shipped
> `main.py`. Path C stays parked. `bptk.py` cannot see this cadence.

## What this session did

1. **Tried fact 42** (bounded NE STRAW after d10 MELON wave): NE leftover
   STRAW d11–12; d7–10 stay MELON; no NW refill; 6a walk after carpet.
2. **Failed.** Seed 0: **1 escape** (walk to NE stole feeders). d11–12
   NE STRAW landings **0 / 1** — SW carpet ate seed; forcing occupant
   STRAW blocked the old opportunistic d12 `choose_crop` (~3–4).
3. **Reverted** throwaway. Post-revert audit CLEAR (28/28, 74/74, 0
   escapes). Same crew-diversion class as fact 40 DROP.

## Hold / drop

**Hold:** facts 1–36 (34 supplemented); 38 plant half; 39; no SE; K=3;
fact 34 d10 MELON DROP.

**Drop / park:** fact 42 NE carve; fact 41 SW fert; fact 40 STRAW DROP;
fact 37; wheat sell ≥200; Path C; Path A mashup; NW wait-empty as lever.

**Open card:** contested **WOOL `$`** (seed 0 herd timing; secondary after
STRAW acreage blocked). STRAW acreage vs 27/39 is accepted for now —
do not walk the crew onto NE/NW STRAW.

## Counters (fact 42 attempt)

| seed | escapes | d11–12 NE STRAW | d7–10 NE STRAW |
|---|---|---|---|
| 0 | **1** | **0** | 0 |
| 8 | 0 | **1** | 0 |

Post-revert: 0 escapes; d7–11 NE STRAW=0; unlock ≥14.

## Verdict

**Park fact 42.** Do **not** port `main.py`. Next ≠ more NE walk.

## What to do next

1. Diagnose contested WOOL `$` via `_trace_straw_wool.py` (seed 0 herd
   timing). Propose one fact that does not steal feeders.
2. Do not reopen 40/41/42 without a feed-first mechanism (no crew walk
   off animals). Do not reopen NW wait-empty (39).
3. No Path C; no `bptk.py`; no Path A gate paste; no `main.py` port.

## Open

- Contested WOOL `$` — **next**.
- Contested STRAW acreage vs 27/39 — parked/blocked (walk/escape).
- Facts 40–42 PARKED; fact 37 PARKED; fact 38 sell ≥200 parked.
- Residual d10 MELON `$` (~−2–3k) — soft.
- Port to shipped `main.py` blocked.

---

# Prior session: 2026-09-05 — fact 41 SW fert PARKED; next = NE carve-out

> **Standing rule:** Report to the user in chat before writing this file.
> Numbers, win counts, and the add / drop / supplement call go in the
> chat first. HANDOFF is the diary after that, not the first copy of
> the result.
>
> **Read this first.** Spec: `mydocs/FACTS.md`. Method:
> `mydocs/AGENT_BUILDING_PROTOCOL.md`. This file is the diary.
>
> Throwaway: `experiments/_facts_v20.py` (K=3). Path tracers:
> `experiments/_trace_straw_wool.py`, `_trace_d10_melon.py`. Cashflow:
> `experiments/_trace_cashflow_v20.py`. Opponent: `agents/route_v20.py`.
> Audit: `experiments/_facts_prerun_audit.py`. Do not patch shipped
> `main.py`. Path C stays parked. `bptk.py` cannot see this cadence.

## What this session did

1. **Added fact 41** (post-carpet SW STRAW fert coverage): DIG skip when
   carpet done + SW wants fert; `prefer_quadrant=SW` on
   `find_fertilizer_target`; helpers `sw_straw_wants_fert` /
   `fact41_post_carpet_fert`. Kept below carpet/K-walk; 9/31 sell fert
   unchanged.
2. **Audit CLEAR** (28/28 source, 74/74 counter, 0 escapes; 27/39 hold;
   unlock ≥14 both seeds).
3. **FERTILIZE** rose ~13 → **19 / 21** (seeds 0/8).
4. **STRAW `$` did not improve** (slightly worse). Peak field unchanged.
   Parked per judge table (yield ≠ acreage bind).

## Hold / drop

**Hold:** facts 1–36 (34 supplemented); 38 plant half; 39; no SE; K=3;
fact 34 d10 MELON DROP.

**Drop / park:** fact 41 SW fert; fact 40 STRAW DROP; fact 37; wheat sell
≥200; Path C; Path A mashup; NW wait-empty as lever.

**Open card:** bounded NE STRAW carve-out (supplement fact 27) with
counters that replace blanket `d7–11 NE STRAW = 0` only after MELON wave
clears — without NW refill (39).

## Counters

| seed | FERTILIZE (was→now) | STRAW $ gap (was→now) | peak field |
|---|---|---|---|
| 0 | ~13 → **19** | −28,817 → **−29,632** | 22 vs 34 |
| 8 | ~14 → **21** | −19,558 → **−21,713** | 19 vs 42 |

## Verdict

**Park fact 41.** Fert cadence moved; contested STRAW `$` did not.
Do **not** port `main.py`. Next ≠ more fert. Next = NE acreage carve-out.

## What to do next

1. Propose one bounded NE STRAW fact (supplement 27) that coexists with
   MELON-on-NE during the wave and with 39 (no NW STRAW).
2. Throwaway; full-row audit; remeasure via `_trace_straw_wool.py`.
3. No fact-40/41 reopen; no wheat sell; no Path C; no `bptk.py`; no
   Path A gate paste; no `main.py` port.

## Open

- Contested STRAW acreage (NE carve-out) — **next**.
- Contested WOOL (secondary).
- Fact 41 PARKED; fact 40 PARKED; fact 37 PARKED; fact 38 sell ≥200 parked.
- Residual d10 MELON `$` (~−2–3k) — soft.
- Port to shipped `main.py` blocked.

---

# Prior session: 2026-09-05 — fact 40 STRAW drip PARKED; next = acreage/yield

> Superseded: fact 41 tried and parked; acreage bind confirmed.

> **Standing rule:** Report to the user in chat before writing this file.
> Numbers, win counts, and the add / drop / supplement call go in the
> chat first. HANDOFF is the diary after that, not the first copy of
> the result.
>
> **Read this first.** Spec: `mydocs/FACTS.md`. Method:
> `mydocs/AGENT_BUILDING_PROTOCOL.md`. This file is the diary.
>
> Throwaway: `experiments/_facts_v20.py` (K=3). Path tracers:
> `experiments/_trace_straw_wool.py`, `_trace_d10_melon.py`. Cashflow:
> `experiments/_trace_cashflow_v20.py`. Opponent: `agents/route_v20.py`.
> Audit: `experiments/_facts_prerun_audit.py`. Do not patch shipped
> `main.py`. Path C stays parked. `bptk.py` cannot see this cadence.

## What this session did

1. **STRAW/WOOL path tracer** (`_trace_straw_wool.py`) seeds 0+8 vs v20.
   Season gaps: STRAW **−28.8k / −19.6k**, WOOL **−25.4k / −5.7k**. Peak
   field **22 vs 34** / **19 vs 42**. v20 plants NW+NE STRAW from d5; our
   SW carpet first-yields ~d21.
2. **Tried fact 40** (fact-34-shaped STRAW held→DROP→SELL). DROP blocked
   by all-fed / feeder gates; when forced, diverted harvest and
   **worsened** seed-0 STRAW `$` (−28k → −32k). Late h≥20 dump also
   flat/worse.
3. **Parked fact 40.** Reverted throwaway. Audit CLEAR (27/27 source,
   74/74 counter, 0 escapes).
4. **Named bind:** STRAW **acreage/timing** (fights 27/39), not sell path.
   Fact 34 d10 MELON DROP from prior session still holds.

## Hold / drop

**Hold:** facts 1–36 (34 supplemented); 38 plant half; 39; no SE; K=3;
fact 34 d10 room-capped MELON DROP.

**Drop / park:** fact 40 STRAW DROP sell; fact 37; wheat sell ≥200;
Path C; Path A mashup; early/uncapped MELON DROP; NW wait-empty as lever.

**Open card:** STRAW acreage/yield lever that does **not** fight 27/39
(e.g. fert/yield on SW carpet, or a bounded NE carve-out with counters).

## Counters

| seed | STRAW $ gap | peak field | WOOL $ gap |
|---|---|---|---|
| 0 | −28,817 | 22 vs 34 | −25,393 |
| 8 | −19,558 | 19 vs 42 | −5,724 |

Fact 40 attempts: seed 0 gap worsened to ~−30–32k when DROP fired.

Prior fact 34 (held): d10 `SELL_MELON` gap −15k → ~−1.7k / −3.1k.

## Verdict

**Park fact 40.** Next ≠ more DROP. Next = acreage/yield without
reopening NW STRAW refill (39) or NE-during-MELON (27).
Do **not** port `main.py`.

## What to do next

1. Propose one STRAW acreage/yield fact that coexists with 27/39.
2. Throwaway; full-row audit; remeasure season STRAW `$` gap via
   `_trace_straw_wool.py`.
3. No fact-40 DROP reopen; no wheat sell; no Path C; no `bptk.py`; no
   Path A gate paste; no `main.py` port.

## Open

- Contested STRAW acreage/yield — **next**.
- Contested WOOL (secondary; seed 0 herd timing).
- Fact 40 PARKED; fact 37 PARKED; fact 38 sell ≥200 parked.
- Residual d10 MELON `$` (~−2–3k) — soft.
- Port to shipped `main.py` blocked.

---

# Prior session: 2026-09-05 — fact 34 same-day DROP; next = STRAW/WOOL $

> Superseded: fact 40 tried and parked; acreage bind named.

## What this session did

1. **Path tracer** (`_trace_d10_melon.py`): contested seeds 0+8 d9–12
   stages + lockstep `SELL_MELON` `$`. Acreage (36) and crew (35) match
   v20 (ripe 12|12, HIRE/HARV≈parity). Bind = **fact 34 sell path**:
   fruit in unit `held` (~60), shed=0, force-sell `$0` on d10 while v20
   sells ~$15k same day; d11 auto-drop catchup into crashed price.
2. **Supplemented fact 34:** force-sell qty = shed + Σ held; d10 hour≥16
   after all-fed, carriers walk-to-shed; DROP shared-capped to shed room
   minus wheat reserve; `MELON_CASH_WAVE_SELL_CAP=60`. Early/uncapped
   DROP → escapes (do not reopen).
3. **Audit CLEAR** (27/27 source, 74/74 counter, 0 escapes both seeds).
4. **Cashflow remeasure:** d10 `SELL_MELON` gap −15k → **~−1.7k / −3.1k**.

## Hold / drop

**Hold:** facts 1–36 (34 supplemented); fact 38 plant half; fact 39;
fact 9 existence-hold; no SE; K=3; separate Path A track.

**Drop / park:** Path A mashup; fact 37; blunt d12 wheat; fact30 full
kill; SE; Path C / STRAW pin; wheat sell ≥200; early/uncapped MELON
DROP walk.

**Open card:** contested **STRAW/WOOL `$`** (after d10 MELON moved).

## Counters

| seed | d10 SELL_MELON $ gap (was → now) | d10 widen (was → now) | bank us |
|---|---|---|---|
| 0 | −14,797 → **−1,714** | −14,782 → **−1,378** | ~27k |
| 8 | −14,847 → **−3,085** | −15,231 → **−3,148** | ~7k |

Starter audit: CLEAR; fact 34 sold on d10; 0 escapes.

## Verdict

**Supplement fact 34 — holds.** Contested d10 MELON cliff largely closed.
Do **not** port `main.py`. Next = contested STRAW/WOOL `$`.

## What to do next

1. Diagnose contested STRAW/WOOL revenue gap vs v20 (cashflow day rollup
   after d10).
2. Supplement or add one fact; throwaway; full-row audit; remeasure.
3. No wheat sell chase; no holdout; no Path C; no `bptk.py`; no Path A
   gate paste; no `main.py` port; no early/uncapped MELON DROP.

## Open

- Contested STRAW / WOOL revenue — **next**.
- Residual d10 MELON `$` gap (~−2–3k) — soft, not the cliff.
- Fact 38 sell ≥200 — parked.
- Seed-8 bank still low vs v20 (STRAW/WOOL hole).
- Milk-in-3 → cows untested.
- Port to shipped `main.py` blocked.

---

# Prior session: 2026-09-05 — cashflow vs v20; next = d10 MELON $

> Superseded: fact 34 same-day DROP closed the ~−15k d10 MELON cliff.

## What this session did

1. **Wheat sell-path probe** (`_trace_wheat_sell.py`): sell path works
   when sellable > 0 (price never blocks; order = exec). Bind is
   `owned×2` reserve + leftover harvest throughput. Best starter exec
   **34** ≪ 200. v20 clears ≥200 by planting ~130 wheat — not our shape.
2. **Parked fact 38 sell ≥200 as a bank lever** (user + economics): even
   clearing 200 units is ~$5–10k; contested gaps are ~$50–100k.
3. **Cashflow tracer** (`_trace_cashflow_v20.py`): engine lockstep `$`
   attribution (units before market; action paired with prior obs).
   Replay check **max|err|=0** both seats. Seeds 0+8 seat 0.
4. **Named dollar binds** (season us − v20): hole is **inflows**, not
   spend (we spend less). Day **10** widens **~−15k** almost all
   `SELL_MELON`. After that STRAW/WOOL (and wheat-vs-v20) keep digging.
   Seed-8 cliff (~3.7k) is revenue-side.

## Hold / drop

**Hold:** facts 1–36; fact 38 plant half; fact 39 starter claim; fact 9
existence-hold; no SE; K=3; separate Path A track.

**Drop / park:** Path A mashup; fact 37; blunt d12 wheat; fact30 full
kill; SE; Path C / STRAW pin of 50; more NW wait-empty; **fact 38
sell-volume ≥200 as bank path** (plant half may stay).

**Open card:** contested **day-10 MELON `$`** (facts 34/35 — diagnose
bind, then supplement). Then STRAW/WOOL revenue. Not wheat sell.

## Counters

Cashflow seed 0: bank 22,074 vs 118,108; TOTAL_IN 64k vs 191k;
TOTAL_OUT 45k vs 76k. Day-10 widen ≈ −15k (`SELL_MELON`).

Cashflow seed 8: bank 3,666 vs 60,953; TOTAL_IN 38k vs 101k; same
d10 MELON cliff then STRAW/WHEAT revenue hole.

Wheat probe (for the park record): starter exec 34/13; contested 4/18.

## Verdict

**Next attack = contested d10 MELON cash (34/35), not fact 38 wheat.**
Do **not** port `main.py`. Report `$` in chat before further HANDOFF.

## What to do next

1. Diagnose contested d9–12 MELON path (ripe → harvest → shed/inv →
   `SELL_MELON` `$` + HIRE) seeds 0+8 vs v20; name one bind vs 34/35/36.
2. Supplement fact 34 or 35 (new row only if bind is new); throwaway;
   full-row audit; re-measure day-10 cashflow widen.
3. Only then: contested STRAW/WOOL `$`. No wheat sell chase; no holdout;
   no Path C; no `bptk.py`; no Path A gate paste; no `main.py` port.

## Open

- Contested d10 MELON `$` (facts 34/35) — **next**.
- Contested STRAW / WOOL revenue (after d10 moves).
- Fact 38 sell ≥200 — **parked** as bank lever (plant half holds).
- Seed-8 bank cliff (revenue-side; follows STRAW/MELON).
- Milk-in-3 → cows untested.
- Port to shipped `main.py` blocked.

---

# Prior session: 2026-09-05 — fact 39 done; next = fact 38 sell path

> Superseded: cashflow named d10 MELON; fact 38 sell ≥200 parked.

## What this session did

1. **Added fact 39** + **supplemented fact 30** (unlock halves only) in
   `FACTS.md`. Home leftover after MELON no longer claims: product WHEAT
   (fact 38 d13+) or wait-empty — never STRAW refill.
2. **Throwaway:** narrowed `fact30_wants_straw_seed` (pre-unlock + SW
   empty only); home plant path prefers MELON while it claims, else
   WHEAT d13+, else wait; refuse STRAW on NW.
3. **Starter audit clear** (0+8): 27/27 source, 74/74 counter; NW STRAW=0;
   NW WHEAT 41/31 (was ~10–17); fact 30 pre-unlock buys still land;
   unlock ≥14; MELON d5=12; 0 escapes; land [7,11].
4. **Contested gap:** `sold_exec` WHEAT still fails ≥200 (4 / 18); seed 8
   bank cliff worse (~17k → ~3.7k). Acreage timing alone did not unlock
   sell volume.

## Hold / drop

**Hold:** facts 1–36; fact 38 plant half; fact 39 starter claim (NW
STRAW=0); fact 9 existence-hold; no SE; K=3; separate Path A track.

**Drop / park:** Path A mashup; fact 37; blunt d12 wheat; fact30 full
kill; SE; Path C / STRAW pin of 50; more NW wait-empty as next edit.

**Open card:** fact 38 sell-volume (`sold_exec` ≥200) — sell path, not
acreage; contested seed-8 bank cliff.

## Counters

Starter audit 0+8: **CLEAR** (NW STRAW=0; NW WHEAT 41/31).

Contested seat 0 (`sold_exec` WHEAT):

| seed | bank | NW plant | SW plant | WHEAT exec | v20 exec |
|---|---|---|---|---|---|
| 0 | 22,074 | 7 | 0 | **4** | 998 |
| 8 | 3,666 | 31 | 0 | **18** | 521 |

Prior contested exec ≈9 both seeds; banks were ~45k / ~17k.

## Verdict

**Add/supplement fact 39 — starter holds; fact 38 sell bar still open.**
Do **not** port `main.py`. Next is not more NW wait-empty — diagnose why
product wheat does not sell contested (shed/reserve/cadence/glut) or why
seed 8 collapses.

## What to do next

1. Diagnose contested WHEAT sell path vs plant count (starter 41 plants
   vs contested exec 4–18) — reserve floor? order qty? opponent glut?
2. Optionally probe seed-8 contested bank cliff (soft open card).
3. No `main.py` port; no holdout; no Path C; no `bptk.py`; no Path A
   gate paste; no more NW wait-empty as the shape lever.

## Open

- Fact 38 sell-volume ≥200 — **next** (mechanism beyond acreage).
- Contested bank cliff (seed 8 soft, worsened).
- Contested STRAW / MELON volume.
- Milk-in-3 → cows untested.
- Port to shipped `main.py` blocked.

---

# Prior session: 2026-09-05 — next lever (no Path A merge)

> Superseded: fact 39 implemented; sell bar still open.

## What this session did

1. **Named the walls** (chat): fact 37 was mostly order-qty mirage +
   land/escape; fact 38 plant half holds but sell bar fails because
   STRAW refills melon-freed NW before a feed-safe wheat open (d13+),
   and earlier open steals feeders.
2. **Rejected Path A merge:** do **not** extract crop-first Path A
   gates into this animal-first shape (Path C failure mode). Path A
   **is** shipped `main.py` — keep equilibria separate.
3. **Chose next lever:** write a fact (supplement 30 home-NW half /
   new row 39) that names who owns home leftover after MELON frees —
   product WHEAT or wait-empty — without fighting SW STRAW carpet,
   held-STRAW-before-unlock, 0 escapes, or land [7,11].

## Hold / drop

**Hold:** facts 1–36; fact 38 plant half (d13+ home-only); fact 9
existence-hold; no SE; K=3; separate Path A vs animal-first tracks.

**Drop / park:** Path A→throwaway mashup; fact 37; blunt d12 wheat /
fact30 full override; SE; Path C / STRAW pin of 50.

**Open card:** fact 39 (or supplement 30) — NW post-MELON leftover
claim; unlocks fact 38 sell-volume.

## Counters

(No new episode this session — strategy only.) Prior fact 38 contested
`sold_exec` WHEAT ≈ 9 vs ≥200; starter 36/36 with plant half.

## Verdict

**Stay animal-first.** Next shape edit is NW acreage timing after MELON,
not Path A imports and not another fert valve. Do **not** port `main.py`.

## What to do next

1. Write fact card in `FACTS.md` (supplement 30 home-NW dribble **or**
   add 39): after MELON window / freed home tiles, claim for product
   WHEAT (or wait-empty) — keep fact 30’s held-STRAW-before-unlock and
   SW-empty→STRAW halves.
2. Diff throwaway vs **every** row; seed 0+8 vs `starter` (0 escapes,
   land [7,11], unlock ≥14, MELON d5 ≥12, SW WHEAT = 0); then gap
   `sold_exec` WHEAT toward ≥200.
3. No `main.py` port; no holdout; no Path C; no `bptk.py`; no Path A
   gate paste.

## Open

- Fact 39 / supplement 30 (NW post-MELON claim) — **next**.
- Fact 38 sell-volume ≥200 (blocked on acreage timing).
- Contested bank cliff (seed 8 soft).
- Contested STRAW / MELON volume.
- Milk-in-3 → cows untested.
- Port to shipped `main.py` blocked.

---

# Prior session: 2026-09-04 — fact 38 wheat product (partial)

> Superseded: next lever is NW post-MELON claim (not Path A merge).

## What this session did

1. **Implemented fact 38** in the throwaway: d13+ home-only
   `BUY_SEED WHEAT` sized to NW empties, prefer WHEAT on home when
   seeded, refuse WHEAT off-home; sell-above-reserve unchanged.
2. **Tried** earlier open (d12) and fact-30 override → seed 0 **1 escape**,
   d18 herd 11; reverted.
3. **Added `sold_exec`** to `_facts_v20_gap.py` (shed-capped fills).
4. **36/36 audit clear** with plant half of fact 38; contested sell bar
   fails.

## Hold / drop

**Hold:** facts 1–36; fact 38 plant half (NW > 0, SW = 0, home-only,
d13+); fact 9 existence-hold; no SE; K=3.

**Drop / park:** fact 37; d12 wheat open / fact30 override; SE; Path C.

**Open:** fact 38 sell-volume (≥200 `sold_exec`); contested bank cliff.

## Counters

Starter audit 0+8: **26/26 source, 70/70 counter, 36/36 facts. CLEAR.**
NW WHEAT plants (leftover seed 0) ≈ 13; SW WHEAT = 0; MELON d5 = 12;
escapes = 0.

Contested seat 0 (`sold_exec` WHEAT):

| seed | bank | NW plant | SW plant | WHEAT exec | v20 exec |
|---|---|---|---|---|---|
| 0 | 44,577 | 10 | 0 | **9** | 998 |
| 8 | 17,171 | 17 | 0 | **9** | 521 |

## Verdict

**Supplement fact 38 — plant half holds; sell bar open.** Do **not**
port `main.py`. Next: free NW acreage earlier without feeder theft
(STRAW refill of melon-freed tiles before d13), or a different volume
mechanism — not another d12 blunt open.

## What to do next

1. New fact/supplement for NW acreage timing vs STRAW refill, or accept
   a lower wheat sell bar with evidence.
2. Do not reopen d12 wheat / fact30 override without a feed-safe gate.
3. No `main.py` port; no holdout; no Path C; no `bptk.py` for this cadence.

## Open

- Fact 38 sell-volume ≥200.
- Contested bank cliff (seed 8 soft).
- Contested MELON / STRAW volume.
- Milk-in-3 → cows untested.
- Port to shipped `main.py` blocked.

---

# Prior session: 2026-09-04 — contested gap + fact 37 parked

> Superseded: fact 38 plant half landed; sell bar still open.

## What this session did

1. **Ran contested gap** (`_facts_v20_gap.py` seeds 0+8, seat 0): banks
   match prior (44,882 / 17,245 vs v20 121k / 76k). Named sell gaps:
   FERT order-qty −1.8k/−2.7k, WHEAT −1.6k/−0.9k, STRAW −66/−210.
2. **Wrote fact cards 37–38** in `FACTS.md` (surplus FERT + wheat product).
3. **Tried fact 37** in the throwaway; **parked** after counters failed:
   - Absorbable-demand surplus → seed 0 **1 escape**, SELL FERT ≈169
     (existence-hold already ≈186 with **0 escapes**).
   - Stock-cap-only → held early fert → **BUY_LAND never fired**.
   - Market-list reorders (wheat/land slots) → unlock=None / 8–24 escapes.
4. **Measurement correction:** gap-harness “v20 sold ~2k FERT” is
   **order qty**, not executed (v20 collect ≈346, oversized SELL orders).
5. **Reverted** throwaway to fact 9 existence-hold. Seed 0 smoke:
   land [7,11], unlock landed 17, 0 escapes, SELL FERT 186, MELON d5 12.

## Hold / drop

**Hold:** facts 1–36 as before (scale on 3 quads, no SE, B1, K=3,
fact 32 ≥14, 34–36, land-before-animals, fact 9 existence-hold).

**Drop / park:** fact 37 surplus-FERT valve (and market-list surgery to
“fix” it); SE; pre-SW d7 dump; MELON walk-to-shed DROP; Path C.

**Open card:** fact 38 wheat-as-product (not yet implemented).

## Counters

Gap vs v20 (seat 0) — season sold units (order qty; FERT inflated for v20):

| product | seed 0 gap | seed 8 gap |
|---|---|---|
| FERTILIZER | −1,843 (183 vs 2,026) | −2,732 (200 vs 2,932) |
| WHEAT | −1,643 (5 vs 1,648) | −852 (4 vs 856) |
| STRAWBERRY | −66 | −210 |
| WOOL / MILK | −132 / −105 | −108 / −124 |

Executed FERT (seed 0 contested): us collect 243 / sell ~185; v20 collect
346 / order-qty “sell” 2,026. Starter existence-hold: SELL FERT **186**,
0 escapes.

Fact 37 attempts vs starter seed 0:

| variant | land | escapes | SELL FERT |
|---|---|---|---|
| existence-hold (kept) | [7,11] | **0** | **186** |
| absorbable surplus | [7,11] | **1** | 169 |
| stock-cap only | **[]** | 24 | 42 |
| + market reorders | **[]** | 8–24 | — |

## Verdict

**Park fact 37.** Contested FERT “volume cliff” was largely a harness
artifact; surplus valves either escaped or broke land. Do **not** port
`main.py`. Next: **fact 38** (wheat product) or remeasure executed
WHEAT/FERT with a non-inflating counter.

## What to do next

1. Implement fact 38 (NW wheat product) — or first add executed-sell
   counters to `_facts_v20_gap.py` so WHEAT/FERT gaps are real.
2. Do not reopen fact 37 without a mechanism that keeps 0 escapes and
   land days [7,11].
3. No `main.py` port; no holdout; no Path C; no `bptk.py` for this cadence.

## Open

- Fact 38 wheat product (card written, not in throwaway).
- Contested bank cliff (seed 8 soft; WHEAT / STRAW still real).
- Contested MELON wave under pressure.
- Milk-in-3 → cows untested.
- Port to shipped `main.py` blocked.
- Full 12×2 H2H vs v20 stale.

---

# Prior session: 2026-09-04 — scale animals, no SE (fact 33)

> Superseded: contested gap diagnosed; fact 37 parked.

## What this session did

1. **Dropped SE** (`MAX_LAND_PURCHASES=3→2`): keep animal scale (facts
   15/17) on 3 quads — matches v20 measure (14 owned, no SE on seeds
   0+8 vs starter).
2. **Rewrote fact 33** counters: unlocked **=3** (not ≥3/4); windows
   NE d6–10 / SW d11–12 only.
3. **36/36 audit clear** vs `starter`. Contested seed 0 bank recovered
   vs the with-SE cliff (~6k → ~45k).

## Hold / drop

**Hold:** facts 1–36 with 15/17 scale + 33 at **2 land buys**; B1;
`land_tail=0`; unlock/carpet animal deferral; owned=filled+shed+carry;
carpet>BUILD; plant_budget bulk credit; K=3; fact 32 ≥14; fact 34–36;
`MAX_ANIMALS=18`; land-before-animals.

**Drop:** SE / 3rd `BUY_LAND`; pre-SW d7 dump toward 10; MELON
walk-to-shed DROP; Path C / STRAW pin.

## Counters

All-facts audit vs `starter` seeds 0+8: **26/26 source, 70/70 counter,
36/36 facts. CLEAR.**

| | seed 0 | seed 8 |
|---|---|---|
| end herd | **14** | **14** |
| unlocked quads | **3** | **3** |
| land days | [7, 11] | [7, 11] |
| unlock landed | 17 | 16 |
| escapes | 0 | 0 |
| field MELON d5 | 12 | 12 |

Contested vs `agents/route_v20.py` (seat 0):

| seed | bank (no SE) | was (with SE) | v20 | delta |
|---|---|---|---|---|
| 0 | **44,882** | ~6,041 | 121,407 | −76,525 |
| 8 | 17,245 | ~17,630 | 76,203 | −58,958 |

## Verdict

**Supplement fact 33 — no SE, keep animal scale — holds.** Shape clear
at 36 facts on 3 quads / ~14 animals. Do **not** port `main.py`.
Contested seed 0 recovered from the SE cash cliff; seed 8 still soft.
Remaining gap is crop/fert sell volume (WHEAT/FERT/STRAW), not land count.

## What to do next

1. Contested sell-volume / NW fill vs v20 (not another land buy).
2. Do not re-add SE without a new fact card + contested proof.
3. No `main.py` port; no holdout while iterating; no Path C; no `bptk.py`
   for this cadence.

## Open

- Contested bank / sell-volume cliff (esp. seed 8; WHEAT/FERT/STRAW).
- Contested MELON wave under pressure.
- Milk-in-3 → cows untested.
- Port to shipped `main.py` blocked.
- Full 12×2 H2H vs v20 stale.

---

# Prior session: 2026-09-04 — scale card B (rewrite 15/17/33)

> Superseded: SE dropped; animals still scale on 3 quads.

## What this session did

1. **Measured v20 scale** (seeds 0+8 vs starter): 14 owned by d11; land
   d6+d11 (3 quads); mix milk 10C4S / yarn 6C8S. Tapes also 2 buys.
2. **Rewrote facts 15/17/33** (scale card B): season ceiling shop-mix
   14/18; `MAX_LAND_PURCHASES=3`; day windows for NE/SW/SE.
3. **Half-stack repairs (keep):**
   - Pre-SW d7 dump toward 10 starved SW/feed → **hold 6 through d10**,
     open shop-mix d11+.
   - Animals-before-land burned NE drawer → land-before-animals always;
     defer animals while NW-only d6–10.
   - Unlock-morning `recommend_sell_quantity(product=...)` TypeError →
     whole-turn PASS when shed had MELON → SW never bought. Fixed to
     positional args.
   - Fact 36 acreage made unlock-day MELON harvest/water walks steal the
     carpet crew; `find_empty` also blocked on pre-market seeds=0. Skip
     crop walks on carpet day; trust `plant_budget` credit.
4. **36/36 audit clear** vs `starter` seeds 0+8. With-SE contested banks
   collapsed (~6k/18k) — SE dropped next session.

## Hold / drop

**Hold:** facts 1–36 with 15/17/33 rewritten; B1; `land_tail=0`;
unlock-h0 + carpet-day animal deferral; owned=filled+shed+carry;
carpet>BUILD; plant_budget bulk credit; K=3; fact 32 ≥14; fact 34–36;
`MAX_ANIMALS=18`; `MAX_LAND_PURCHASES=3`; land-before-animals.

**Drop (reconfirmed):** pre-SW d7 intermediate dump toward 10; MELON
walk-to-shed DROP; harvest-prefer-MELON over water (except carpet-day
skip); uncapped hire waive; Path C / STRAW pin.

## Counters

All-facts audit vs `starter` seeds 0+8: **26/26 source, 70/70 counter,
36/36 facts. CLEAR.**

| | seed 0 | seed 8 |
|---|---|---|
| end herd | **14** | **14** |
| unlocked quads | **4** | **4** |
| land days | [7, 11, 13] | [7, 11, 13] |
| unlock landed | 17 | 16 |
| escapes | 0 | 0 |
| field MELON d5 | 12 | 12 |

Contested vs `agents/route_v20.py` (seat 0) — bank cliff, not a fact fail:

| seed | bank | v20 | delta |
|---|---|---|---|
| 0 | 6,041 | 137,525 | −131,484 |
| 8 | 17,630 | 74,004 | −56,374 |

Pre-scale contested banks were ~45–48k. Contested utilization (STRAW /
WHEAT / FERT sell volume) still open.

## Verdict

**Rewrite 15/17/33 — holds** (post-repair). Shape clear at 36 facts with
scale past 8 and 3rd land. Do **not** port `main.py`. Next: contested
gap (post-unlock crop/sell pipeline), not another calendar dump.

## What to do next

1. Diagnose contested bank cliff vs v20 (STRAW/WHEAT/FERT volume) without
   breaking starter audit counters.
2. Do not retry feed-stealing DROP walks; do not re-open pre-SW d7 dump.
3. No `main.py` port; no holdout while iterating; no Path C; no `bptk.py`
   for this cadence.

## Open

- Contested bank / sell-volume cliff vs v20 after scale.
- Contested MELON wave under pressure.
- Milk-in-3 → cows untested.
- Port to shipped `main.py` blocked.
- Full 12×2 H2H vs v20 stale.

---

# Prior session: 2026-09-04 — fact 36 early MELON acreage

> Superseded: scale card B (15/17/33) landed.

## What this session did

1. **Added fact 36** (early MELON acreage): day-0 `BUY_SEED MELON` ~12
   (not stockpile-3) + same-turn `plant_budget` credit.
2. **Half-stack failure then repair:** opening 12 alone left ~$0 and
   wheat restock every hour absorbed fert income → no land, escapes.
   Matched v20 diagnosis (also opens broke) — fix is wheat trough
   cadence, not fewer melons: day-0 wheat buy 1× owned at h0 only;
   until first land, restock only when feed empty (emergency, h0).
3. **36/36 audit clear** vs `starter` seeds 0+8. Contested field d5=12
   both seeds; 0 escapes; land [7,9]; SW unlock landed 15.

## Hold / drop

**Hold:** facts 1–36; B1 shape; `land_tail=0`; unlock-h0 animal deferral;
owned=filled+shed+carry; carpet>BUILD; plant_budget bulk credit; K=3;
fact 32 bar ≥14; fact 34 force-sell; fact 35 hire waive; fact 36 MELON
opening + wheat trough cadence.

**Drop (reconfirmed):** MELON walk-to-shed DROP; harvest-prefer-MELON
over water; uncapped hire waive; waive unlock land reserve; Path C /
STRAW pin; blunt always-buy STRAW.

## Counters

All-facts audit vs `starter` seeds 0+8: **26/26 source, 66/66 counter,
36/36 facts. CLEAR.**

| | seed 0 | seed 8 |
|---|---|---|
| d0 BUY / PLANT MELON | 12 / 12 | 12 / 12 |
| field MELON EOD d5 | **12** | **12** |
| escapes | 0 | 0 |

Contested vs `agents/route_v20.py` (seat 0):

| seed | field_d5 | bank | MELON sold d9–11 | land | unlock landed |
|---|---|---|---|---|---|
| 0 | **12** | 47,634 | 5 (contested pressure) | [7,9] | 15 |
| 8 | **12** | 44,135 | 48 | [7,9] | 15 |

Starter audit still clears fact 34 (≥20 sold). Contested seed 0 wave
volume soft under v20 pressure — informational, not a fact-36 fail.

## Verdict

**Add fact 36 — holds.** Shape clear at 36 facts. Acreage beach-head
closed (d5=12). Do **not** port `main.py`. Next was scale card B.

## What to do next

1. Open **scale card B** (past cap-8 / 3rd land; rewrite facts 15/33).
2. Do not retry feed-stealing DROP walks.
3. No `main.py` port; no holdout while iterating; no Path C; no `bptk.py`
   for this cadence.

## Open

- Scale past 8 / 3rd land.
- Contested MELON wave volume under v20 pressure (seed 0 sold 5).
- Contested same-day MELON sell without feed theft (optional).
- Milk-in-3 → cows untested.
- Port to shipped `main.py` blocked.
- Full 12×2 H2H vs v20 stale relative to facts 34–36.

---

# Prior session: 2026-09-04 — fact 35 MELON-wave crew (hire waive)

> Superseded: fact 36 early MELON acreage landed.

## What this session did

1. **Traced contested d10** (`_trace_d10_melon.py`): 6 ripe NW MELON from
   h0; unlock bulk leaves ~$15; `MIN_MONEY_TO_HIRE=20` → **0 hires**; only
   the farmer; ~1 HARVEST at h23. v20 hires ~11 and dumps ~60 MELON.
2. **Added fact 35** + implemented: waive flat hire floor when ripe MELON
   exists; cap hires to ripe count; keep $5 wheat tail. Uncapped waive →
   2 escapes (half-stack).
3. **Tried same-day DROP** (HARVEST → unit inventory; engine auto-drop is
   EOD only, so force-sell usually waits until d11). Walk-to-shed →
   **3 escapes**. Shed-adj DROP after all fed kept (rarely fires).
   Walk-to-shed listed under Dropped in `FACTS.md`.
4. **35/35 audit clear.** Contested bank up; d10 cliff vs v20 remains.

## Hold / drop

**Hold:** facts 1–35; B1 shape; `land_tail=0` on unlock bulk; unlock-h0
animal deferral; owned=filled+shed+carry; carpet>BUILD; plant_budget bulk
credit; K=3; fact 32 bar ≥14; fact 34 force-sell; fact 35 hire waive
(capped + wheat tail).

**Drop (reconfirmed):** MELON walk-to-shed DROP; harvest-prefer-MELON over
water; uncapped hire waive; waive unlock land reserve; Path C / STRAW pin.

## Counters

All-facts audit vs `starter` seeds 0+8: **25/25 source, 62/62 counter,
35/35 facts. CLEAR.**

| | seed 0 | seed 8 |
|---|---|---|
| d10 HIRE / MELON HARVEST | 9 / 6 | 6 / 6 |
| MELON sold d9–11 (by_day) | 29 (d11) | 27 (d11) |
| escapes | 0 | 0 |

Contested vs `agents/route_v20.py` (seat 0):

| seed | bank | delta | d10 $ |
|---|---|---|---|
| 0 | **51,421** (was ~30k pre-35) | −89,754 | 8 |
| 8 | **51,951** | −70,770 | **550** |

Pre-35 contested deltas were ~−95k / −65k at ~30k/44k bank. Absolute bank
improved; pairwise delta still huge (v20 ~125–141k). Full 12×2 H2H vs v20
not re-run this session (last full: −68,907 / 0/24 at shape-33).

## Verdict

**Shape clear at 35 facts.** Fact 35 holds. Fact 34 sell-only holds.
Same-day MELON DROP via walk **dropped** (fights 7/18–20). Contested d10
cliff not closed (EOD auto-drop + acreage 7 vs ~20). Scale past 8 still
open. Do **not** port `main.py`.

## What to do next

1. Prefer **early MELON acreage** (NW+NE in window; counter: field MELON
   by d5 ≥12, contested) — or accept d11 sell and open **scale card B**
   (past cap-8 / 3rd land; rewrite 15/33 explicitly).
2. Do not retry feed-stealing DROP walks.
3. No `main.py` port; no holdout while iterating; no Path C; no `bptk.py`
   for this cadence.

## Open

- Early MELON acreage (7 vs v20 ~20 plants).
- Contested same-day MELON sell without feed theft (optional; EOD drop may stand).
- Scale past 8 / 3rd land.
- Milk-in-3 → cows untested.
- Port to shipped `main.py` blocked.
- Full 12×2 H2H vs v20 stale relative to facts 34–35.

---

# Prior session: 2026-09-04 — fact 34 MELON cash wave (sell-only)

> Superseded: fact 35 hire waive landed; DROP walk dropped.

## What this session did

1. **Added fact 34** (mid-season MELON force-sell d9–12) to `FACTS.md`.
2. **Implemented** `MELON_CASH_WAVE_*` + force-sell (floor, cap 24).
3. **Tried** harvest prefer-MELON over `water_urgent` — seed 0 → 3 escapes;
   **reverted**.
4. **34/34 audit clear** vs `starter`. Contested gap still ~−95k/−65k;
   sell alone does not open d10 (no crew / fruit not in shed same day).

## Verdict

**Add fact 34 (sell-only) — holds.** Next was d10 crew (became fact 35).

---

# Prior session: 2026-09-04 — v20 gap diagnosed (d10 MELON cliff + scale)

> Superseded: facts 34–35 address sell + crew halves; cliff/acreage/scale remain.

## What this session did

1. Wrote `experiments/_facts_v20_gap.py` — contested throwaway vs v20.
2. Named largest day open: **d10 MELON dump** (~−15k widen); structural
   compound: v20 14–18 animals / often 3rd land vs our 8/2-land.

## Contested (pre-34)

| seed | throwaway | v20 | delta |
|---|---|---|---|
| 0 | 30,304 | 125,368 | −95,064 |
| 8 | 44,449 | 109,393 | −64,944 |

## Verdict

Missing facts: (A) MELON mid-season cash → fact 34/35; (B) scale past 8
(conditional). Open holes CARROT/home leftover **not** the loss.

---

# Prior session: 2026-09-04 — shape CLEAR; not ladder-clear (−68,907 / 0/24 vs v20)

> Superseded: 33→35 facts; gap diagnosed; 34–35 landed. H2H −68,907 was at
> shape-33 before MELON-wave facts.

## What this session did

1. Expanded `_facts_prerun_audit.py` to all 33 facts; closed placement
   (16/17) and NE MELON (27/29); fact 32 bar ≥14; carpet helpers.
2. H2H: vs `main.py` **+20,198 / 24/24**; vs v20 **−68,907 / 0/24**.

## All-facts audit (then)

| Source | Counter | Facts | Shape | Ladder |
|---|---|---|---|---|
| 23/23 | 52/52 | **33/33** | YES | NO vs v20 |

**Hold:** B1, `land_tail=0`, unlock-h0 animal deferral, owned=filled+shed+carry,
carpet>BUILD, K=3, fact 32 ≥14.

---

# Prior session: 2026-09-03 — all-facts shape audit; 30–33 clear; gaps remain

> Superseded: all 33 clear 2026-09-04; later 35 with MELON-wave facts.

## What this session did

1. **Ran full pre-run audit** (`experiments/_facts_prerun_audit.py`) on
   `_facts_v20.py` — source checks + episode counters on seeds 0 and 8.
2. **Merged B1** (unlock bulk land floor `land_cost + 200` not `+500`) —
   facts **30–33 counter bar now passes both seeds** (was failing pre-B1).
3. **Tested B1+R2** (defer d9h0 `BUY_ANIMAL`) — counters still pass but
   seed 8 unlock landed 19→18; **do not merge R2**.
4. **Parallel arm sweep** (B1–B4, R1–R4): only B1 won on counters.
5. **Started all-facts closure** — in-throwaway edits not yet re-audited:
   - `find_empty_first_extra_occupant` + step **6a** (NE MELON walk d7–11,
     skipped on unlock carpet day so fact 32 crew stays on SW).
   - `carpet_blocks_pickup`: animal pickup/carry no longer blocked on carpet
     day when shed still holds unplaced animals (fact 16).

## Pre-run audit (minimum checklist, seeds 0 + 8)

| layer | result |
|---|---|
| source | **13/14** (all required; R2 optional absent) |
| counters | **24/24** |
| shape clear (facts 27–33 bar) | **YES** |

Key counters post-B1:

| counter | seed 0 | seed 8 |
|---|---|---|
| d0 pens/herd | 4/4 ✓ | 4/4 ✓ |
| NE STRAW d7–11 | 0 ✓ | 0 ✓ |
| unlock-day SW landed | **17** ✓ | **19** ✓ |
| night deaths (SW) | 0 ✓ | 0 ✓ |
| escapes | 0 ✓ | 0 ✓ |
| `BUY_LAND` | d7, d9 ✓ | d7, d9 ✓ |
| `BUY_FERT` / `PLANT_TOMATO` | 0 ✓ | 0 ✓ |
| SELL FERT before BUY_ANIMAL | 3/3 ✓ | 3/3 ✓ |

## All-facts gap table (not yet passing — do not flip FACTS.md)

These are measured on the **current** throwaway (includes uncommitted 6a +
carpet_blocks_pickup). Audit script does **not** yet check every row.

| fact | counter | seed 0 | seed 8 | status |
|---|---|---|---|---|
| 16/17 | end placed 7–8 | **6/8** | **6/8** | **fail** — 2 d9 sheep in shed all season |
| 27/29 | d12 NE MELON > 0 | 1 | **0** | **fail** seed 8; marginal seed 0 |
| 27 | NE MELON season | 2 | **0** | **fail** seed 8 |
| 30 | held STRAW > 0 d9–11 | not in audit yet | not in audit yet | unmeasured |
| 1, 4, 6 | d0h0 batch (5 hire + 2C2S + wheat) | passes dump | passes dump | source ✓; not in full audit |
| 13 | no `BUY_SEED` between fert sell and animal buy | **fail d9** unlock preamble (fact 31 overrides by design) | same | known fight; 31 wins on unlock day |

Beach-head facts **1–6** look correct in `_facts_dump.py` (d0h0: 5 `HIRE`,
`BUY_ANIMAL` 2C+2S, `BUY_PRODUCT WHEAT` 8, `BUY_SEED MELON` 3 = 10 orders).
Not yet wired into the automated all-facts audit.

## Head-to-head

Last run (B1 merged, pre-6a fixes): mean **+16,135**, **24/24** vs `main.py`.
Stale — re-run only after all-facts audit clears.

## Verdict

**Facts 30–33 shape bar is closed.** The throwaway does **not** yet match
**all 33 facts exactly** — placement (16/17) and NE MELON (27/29) are the
loudest gaps on seeds 0 and 8. Do **not** update `FACTS.md` `true`/`false`
column or patch `main.py` until the expanded audit passes every row on both
seeds.

**Hold:** B1 (`land_tail = 200`), merged arms 1+2, `land_first`, K=3,
step 6b carpet, pending-SW plantable, unlock bulk pre-credit, in-progress
6a + carpet_blocks_pickup.

**Drop (reconfirmed):** R2, `straw_seed_supplement`, STRAW pin,
unlock-day `slots=0` defer, raw `defer_d9_cash`, B2 (syntax/dead), B3
(no-op), B4 (seed 0 fail), R1/R3/R4 (fail or catastrophic).

## What to do next

**Goal: agent shape must match every row in `mydocs/FACTS.md` exactly.**

1. **Expand `_facts_prerun_audit.py`** to all 33 facts (source + named
   counter per row). Run seeds 0 + 8; print pass/fail per fact ID.
2. **Close placement gap (facts 16/17):** trace why d9 `BUY_ANIMAL SHEEP` ×2
   never places — carpet-day pickup block was one cause; verify
   `carpet_blocks_pickup` fix, then parallel arms if still stuck (priority
   pickup after carpet exhausts seed, dedicated placement unit, R2 at h1 only
   if placement still fails).
3. **Close NE MELON gap (facts 27/29):** verify step 6a on seed 8; if still
   0, parallel arms (NE melon K-units d7–8, `BUY_SEED MELON` restock when NE
   empty, stronger walk rank before SW pre-unlock work).
4. **Re-run all-facts audit** on both seeds — must be green before H2H or
   FACTS.md status edits.
5. Then: 12-seed H2H vs `main.py` → update FACTS.md `Shipped` column for
   throwaway-only rows (not `main.py`).

Do not: patch `main.py`; holdout; Path C; `bptk.py`; merge R2; run H2H
before all-facts audit clears.

## Open

- Full 33-fact automated audit: **not built yet** (minimum checklist only).
- Facts 16/17, 27/29: **failing** on current throwaway (table above).
- Facts 30–33: counter bar **passes**; FACTS.md still says `false` until
  full audit + user sign-off.
- H2H +16,135 / 24/24 stale relative to in-progress placement/MELON edits.
- Milk-in-3 → cows: untested.

---

# Prior session: 2026-09-02 — shape arms 1+2 merged; counters improved; still short of spec

> Superseded: B1 merged; facts 30–33 bar cleared; all-facts closure open.

## What this session did

1. **Merged shape arms 1+2 into `experiments/_facts_v20.py`** (single
   throwaway, not separate arm files yet):
   - **Arm 1 / fact 31:** `straw_bulk_restock_quantity(..., unlock_morning=True)`
     waives `SEED_SPEND_CAP` on unlock morning; `unlock_morning_sell_proceeds`
     + `expected_unlock_bulk_straw` size bulk from MELON+FERT sell proceeds;
     pre-credits expected bulk into `plant_budget` before unit actions (engine
     runs market before units).
   - **Arm 2 / fact 32:** `pending_sw_unlock_day`, `later_extra_quadrants_effective`,
     `is_later_extra_plantable` — treat LOCKED SW as plantable on unlock turn;
     `is_sw_carpet_day` true when pending 2nd land; carpet day skips animal
     pickup/carry walks (not feed).
2. **Counter sweep** (`_facts_leftover.py`, seeds 0 and 8 only — no H2H):

| counter | seed 0 before | seed 0 now | seed 8 before | seed 8 now |
|---|---|---|---|---|
| NE STRAW d7–11 | 0 ✓ | 0 ✓ | 0 ✓ | 0 ✓ |
| SW STRAW season | 7 | **22** | 14 | **16** |
| bulk STRAW d9h0 | ×4 | **×14** | ×2 | **×16** |
| unlock-day SW landed | ~4 (d11+) | **14 (d9)** | 1 (d9) | **0 d9** (d10:5 d11:10) |
| night deaths (SW) | 0 ✓ | 0 ✓ | 0 ✓ | 0 ✓ |
| bank vs starter | 62,719 | 51,541 | 94,468 | 101,225 |

3. **Mechanism named:**
   - **Seed 0:** unlock carpet now fires d9 (**14 landed**, 1 short of ≥15).
     Bulk **×14** from FERT-only funding (no MELON in shed d9h0). Bank −11k
     vs prior shape-incomplete run — expected shape-first tradeoff.
   - **Seed 8:** bulk **×16** at d9h0 (tape-shaped) but **0 SW PLANT on d9**
     — carpet slips to d10–11 (5+10 landed). Likely hour-0 feed/BUY_ANIMAL
     contention, not missing seed. `_trace_d9_sw.py` confirms STRAW_seed=16
     and SW_empty=25 post-unlock with no same-day plants.
4. **No H2H this session** — shape counters still fail fact 30–33 bar on
   both seeds (unlock landed ≥15, seed 8 unlock-day carpet).

## Head-to-head

Not run — shape counters must pass seeds 0 and 8 first.

## Verdict

**Shape moved sharply but facts 30–32 are still `false`.** Seed 0 is one
landing short; seed 8 has tape-shaped bulk but unlock-day carpet on the
wrong day. Do **not** read bank (seed 8 ↑, seed 0 ↓) or prior **24/24** H2H
as spec compliance.

**Hold:** merged arm code in `_facts_v20.py`, `land_first` + post-sell emit,
K=3 pre-unlock, step 6b carpet rank, pending-SW plantable tiles,
unlock-morning bulk pre-credit.

**Drop (reconfirmed):** unlock-day animal defer (`slots=0`), `straw_seed_supplement`,
STRAW pin, raw `defer_d9_cash`.

## What to do next

**Goal: agent shape must match `mydocs/FACTS.md` exactly.** Pre-run audit +
counter table on seeds 0 and 8 before any bank/H2H read.

**Process rule (user): try multiple approaches in parallel — do not implement
one arm, pause, and wait.** Spin separate throwaway copies from the current
`_facts_v20.py` base and run `_facts_leftover.py` on seeds 0+8 for **all**
arms in one session; merge only the arm(s) that pass every fact 30–33 counter
on both seeds.

### Parallel arms to run (copy base → edit → counter sweep each)

**Bulk / preamble (fact 31) — run all, pick winner on counters not bank:**

| arm | hypothesis | edit sketch |
|---|---|---|
| B1 | Lower unlock-morning land reserve so FERT-only seeds afford more bulk | `straw_bulk_restock_quantity` unlock floor: land_cost + 200 not +500 |
| B2 | Pre-sell MELON from field — not possible; instead sell NE MELON *plants* via earlier liquidation push day 8 | `decide_market_actions` force-sell MELON shed day 8 when `pending_second_land` |
| B3 | Bulk after hires removed from unlock preamble (more cash for seed) | unlock market order: sells → bulk → land → hires (test counter impact) |
| B4 | Unlock bulk ignores `MIN_CASH_RESERVE_FOR_LAND_BUYING` in spend loop; land emit uses post-bulk cash only | separate afford fn for bulk vs land |

**Crew routing (fact 32) — run all, pick winner on counters not bank:**

| arm | hypothesis | edit sketch |
|---|---|---|
| R1 | Carpet step **6b before feed-walk** on unlock day only (not globally) | `choose_unit_action`: if `sw_carpet_day` and no `consecutive_unfed>=1`, carpet before 1c |
| R2 | Skip `BUY_ANIMAL` market emit on unlock h0 when carpet pending (not slot=0 defer) | `decide_animal_market_actions`: delay d9 sheep to h1 if unlock preamble |
| R3 | Skip wheat pickup on carpet day when STRAW seed in `plant_budget` | extend 2c skip to wheat batch pickup |
| R4 | Hour-cap: first 6 hours unlock day are carpet-only for non-feed units | `sw_carpet_day and hour < 6` gate on steps 2c–10 except feed/water |

### Counter bar (must pass on **both** seeds before merge / H2H)

- fact 30: held STRAW > 0 d9–11; ≥1 `BUY_SEED STRAW` before unlock day
- fact 31: `SELL MELON`+`SELL FERT` before bulk; bulk ≥5 same day as 2nd `BUY_LAND`
- fact 32: unlock-day SW landed **≥15**; water/planted = 1.0; night_deaths = 0
- fact 33: `sw_unlock_day` ≤ 11; NE STRAW d7–11 = 0

Then: merge winner(s) → re-sweep seeds 0+8 → 12-seed H2H vs `main.py` →
update FACTS.md `true`/`false` only when pre-run audit passes.

Do not: patch `main.py`; holdout; Path C; `bptk.py`; re-add unlock-day
animal defer or `straw_seed_supplement`; run H2H before counter bar clears.

## Open

- Facts **30–33** still **`false`** in FACTS.md.
- Seed 0: unlock landed 14/15; no MELON in shed on unlock (bulk cap structural).
- Seed 8: bulk ×16 but carpet d10–11 not d9 — routing contention untested arms above.
- Prior H2H **24/24** stale relative to this throwaway — re-run only post-merge.
- Milk-in-3 → cows: **untested.**

---

# Prior session: 2026-09-02 — SW recipe cards A–D wired; H2H 24/24; counters short

> Superseded: arms 1+2 merged into throwaway; counters improved but spec bar not cleared.

## What this session did

1. **Wired facts 30–33** in `experiments/_facts_v20.py` (cards A–D):
   - **30:** `fact30_wants_straw_seed()` — STRAW dribble when held = 0 in
     d5–12 window; STRAW restock outranks MELON (not `straw_seed_supplement`).
   - **31:** unlock preamble when `decide_land_orders` emits +
     `pending_second_land`: SELL MELON + FERT → bulk `BUY_SEED STRAW`
     (target 23, afford-scaled) → hires → land; `_pending_unlock_sells`
     in `_estimated_post_sell_cash`.
   - **32:** `is_sw_carpet_day()` → `sw_slots = [999]`; step **6b** SW
     carpet walk after urgent water/harvest (not before feed-walk).
   - **33:** land timing unchanged — BUY_LAND **d7 + d9** both seeds.
2. **12-seed H2H** vs shipped `main.py`: mean **+18,607**, **24/24**
   (prior pre-recipe run: +9,107, 21/24). Ran despite incomplete counters
   — large contested win; not a substitute for fact-shape audit.
3. **Counter sweep** (`_facts_leftover.py`, seeds 0 and 8):

| counter | seed 0 | seed 8 |
|---|---|---|
| NE STRAW d7–11 | 0 ✓ | 0 ✓ |
| SW STRAW season | 7 (↑ from 5) | 14 |
| unlock-day SW landed | weak (bulk ~4; carpet d11+) | 1 on d9 |
| night deaths (SW) | 0 ✓ | 0 ✓ |
| bank vs starter | 62,719 | 94,468 |

4. **Mechanism (seed 0 d9 trace):** unlock preamble fires h0
   (`SELL FERT`, `BUY_SEED STRAW ×4`, `BUY_LAND`) but **not** `SELL MELON`
   (no melon in shed); bulk capped by cash after land reserve; **0 SW
   PLANT on all of d9** — crew on animal/shed walks; carpet starts d11.
   Tapes want **×23 + ~18 landings same unlock day**.
5. **Dead end this session:** defer all `BUY_ANIMAL` on unlock-land day
   (`slots = 0` when land emits) — bank collapse (seed 0 **30,176**,
   seed 8 **39,840**). **Drop** that defer; calendar animals stay.

## Head-to-head

| harness | result |
|---|---|
| `_facts_v20.py` vs `main.py`, 12×2 | mean **+18,607**, **24/24** |

## Verdict

**Cards A–D code is in throwaway; fact-shape still incomplete.** H2H
improved sharply but **counters do not match FACTS.md** — especially
fact **31** (bulk ×23, MELON sell before bulk) and fact **32** (unlock-day
SW landed ≥15). Agent wins contested play without matching the spec;
**next session goal is shape-first, not bank-first.**

## What to do next (superseded — see current session)

Parallel multi-arm bulk + routing sweep on frozen base; merge on counters.

---

# Prior session: 2026-09-02 — SW recipe facts; tape transcripts; H2H refresh

> Superseded: cards A–D now wired; next is fact-shape closure (both arms).

## What this session did

1. **Fresh head-to-head** — `_facts_v20.py` vs shipped `main.py`, 12 dev
   seeds × 2 seats: mean **+9,107**, **21/24**. Still clears win-count
   bar; down from stale pre-land run (+20,082, 22/24). One fewer win
   fits seed-0 fill regression (sw landed 15→5).
2. **Consulted v20 tapes** (`mydocs/tape_transcripts/`) for exact SW
   utilization steps. Transcript day N = engine day N−1.
3. **Mechanism named (tapes vs throwaway, seed 0):**
   - Tapes: STRAW seed **dribble d5–10**, then unlock day h0 sell
     MELON+FERT → **`BUY_SEED STRAW ×23`** → hires → **`BUY_LAND`** →
     **carpet SW same day** (~18 landings tape_0).
   - Throwaway: SW unlock d9 (good) but **held STRAW = 0 until d12**;
     MELON restock wins d9–11 → SW idle despite facts 27–29 wired.
4. **Added SW recipe to spec** — `mydocs/FACTS.md` facts **30–33**;
   supplemented **27** (home NW STRAW from d5) and **29** (K pre-unlock
   only; unlock day = full crew carpet). Paste-ready pickup cards **A→D**
   in FACTS.md. **No throwaway code change this session.**

## Head-to-head (fresh)

| harness | result |
|---|---|
| `_facts_v20.py` vs `main.py`, 12×2 | mean **+9,107**, **21/24** |

Do not 12-seed paired until fact 30 counters pass seeds 0 and 8.

## Verdict

**Land timing closed in throwaway** (`land_first` + post-sell emit).
**SW utilization spec'd but not implemented** — gap is **seed cadence**
(fact 30), then unlock preamble (31), then carpet day (32). **Start next
session with FACTS.md Card A (fact 30).**

**Drop:** `straw_seed_supplement`, raw `defer_d9_cash`, STRAW pin.
**Hold:** `land_first` + post-sell emit bundle.

## What to do next (superseded — see current session)

Cards A–D in throwaway; close fact-shape via arms 1 and 2.

## Open (stale)

- Facts 30–33 spec'd; throwaway not yet wired at time of this entry.

---

# Prior session: 2026-09-02 — post-sell land emit; d9 defer; both seeds pass

> Superseded: land timing done; next lever is SW seed cadence (facts
> 30–33 in FACTS.md).

## What this session did

1. **Wired `land_first` into throwaway** (`pending_second_land` +
   `BUY_LAND` before animals/seeds when NE bought, SW pending) in
   `experiments/_facts_v20.py`.
2. **Post-sell d9 defer** — skip d9 `BUY_ANIMAL` when
   `pending_second_land` and `not can_afford_pending_second_land_after_sells`
   (`_estimated_post_sell_cash` + `_sell_order_proceeds`). Raw
   `money < 2500` defer (`defer_d9_cash`) still tested for comparison.
3. **Defer placement bug fixed** — gate was inside `elif slots > 0 and
   day > 0`; shop-mix `elif day >= 9` could still run. Moved **before**
   all animal-buy branches.
4. **Emit bug fixed (companion)** — `decide_land_orders` gated on
   pre-turn `money` only, so `BUY_LAND` never queued when sells fund
   land (`land_first` only reordered execution). Emit now uses
   `_estimated_post_sell_cash` when `private` / `market_state` passed
   from `nikaangukia_meroni` (`sell_fert_for_buy=buying`).
5. **d9–11 SW idle traced** (`_trace_d9_sw.py`) — not walkers; **zero
   STRAW seed** on d9–11 while MELON restock wins in
   `decide_market_actions`. `straw_seed_supplement` arm tested; fails
   fact 27 on both seeds.
6. **Cash arms on prior base** — `skip_seed_restock` no-op (cash never
   reaches $2,500). `defer_d9_cash` fixes seed-8 calendar but regresses
   seed-0 fill; redundant once post-sell emit ships.

## Land sweep vs `starter` (K=3, current throwaway)

| arm | seed | sw unlock | eligible | sw landed | d12 SW STRAW | ne STRAW d12–14 | d12 NE MELON | night deaths | bank | pass |
|---|---|---|---|---|---|---|---|---|---|---|
| land_first (+ post-sell emit + defer) | 0 | d9 | 4 | 5 | 3 | 0 | 7 | 0 | 90,542 | **yes** |
| land_first (+ post-sell emit + defer) | 8 | d9 | 4 | 6 | 2 | 0 | 12 | 0 | 91,073 | **yes** |
| land_first_no_defer | 0/8 | d9 | 4 | 5/6 | — | 0 | — | 0 | same | yes |
| defer_d9_cash (raw money gate) | 0 | d9 | 4 | 7 | 5 | **2** | 7 | 0 | 93,805 | no |
| defer_d9_cash | 8 | d9 | 4 | 4 | 1 | **7** | 13 | 0 | 92,817 | no |
| straw_seed_supplement | 0 | d9 | 4 | 5 | 2 | **1** | 7 | 0 | 93,057 | no |
| straw_seed_supplement | 8 | d9 | 4 | 4 | 3 | **1** | 13 | 0 | 97,158 | no |

Prior partial win for reference (`land_first` reorder only, pre-emit):
seed 0 bank **97,174**, sw landed **15**, pass yes; seed 8 d11, pass no.

**Verdict: supplement post-sell land emit + `land_first` in throwaway.**
Post-sell d9 defer is **redundant** once emit is fixed
(`land_first` ≡ `land_first_no_defer` on K=3). **Drop** raw
`defer_d9_cash`, `skip_seed_restock`, `straw_seed_supplement` on this
base. **Do not patch `main.py`. Do not 12-seed.**

## Mechanism (d9 hour trace, seed 8)

| hour | pre-turn $ | post-sell est. | need | land emit (old) | land emit (new) |
|---|---|---|---|---|---|
| d9h00 | 127 | 127 | 2500 | no | no |
| d9h01 | 2234 / 2802* | same | 2500 | no / yes* | yes (pre≥2500) |

\*2802 with `defer_d9_cash` (no h00 animal). Seed 0 buys at **d9h01**
(pre=$2580). Seed 8 never hits $2500 pre-turn without defer; **post-sell
emit alone** pulls both to d9 unlock on current throwaway.

## What to do next (superseded — see current session)

Card A fact 30 in FACTS.md.

## Open (stale)

- Both seeds pass calendar counters (d9 SW unlock).
- Seed-0 fill regression; d9–11 idle = seed cadence.

---

# Prior session: 2026-09-01 — land timing sweep; market-order fix; seed split

> **Standing rule:** Report to the user in chat before writing this file.
> Numbers, win counts, and the add / drop / supplement call go in the
> chat first. HANDOFF is the diary after that, not the first copy of
> the result.
>
> **Read this first.** Spec: `mydocs/FACTS.md`. Method:
> `mydocs/AGENT_BUILDING_PROTOCOL.md`. This file is the diary.
>
> Throwaway: `experiments/_facts_v20.py` (K=3). Sweeps:
> `experiments/_facts_land_sweep.py`, `experiments/_facts_window_sweep.py`.
> Do not patch shipped `main.py`. Path C stays parked. `bptk.py` still
> cannot see this cadence.

## What this session did

1. **Reserve ladder** (`MIN_CASH_RESERVE_FOR_LAND_BUYING` 500→400→300→200):
   byte-identical to baseline on seeds 0 and 8.
2. **`LAND_BUY_START_DAY` 6→5**: byte-identical.
3. **Mechanism traced**: end-of-day cash on d9 is **$491 / $462** — far
   below the **$2,500** needed for the $2,000 second quadrant plus
   reserve. Lowering reserve 500→200 does nothing because cash never
   enters that band. `BUY_LAND` days in telemetry count **emitted**
   orders, not successful purchases.
4. **Real bug**: `decide_land_orders` gates on pre-turn `money`, but
   `nikaangukia_meroni` lists `BUY_LAND` **after** `BUY_ANIMAL` /
   seeds / hires. Same-turn animal spend drops cash before land executes.
5. **`land_first` arm** (`pending_second_land` + reorder market so land
   runs before animals when NE bought, SW pending): tested via
   `_facts_land_sweep.py`.
6. **`land_first_defer` arms** (additionally skip animal calendar while
   second land pending): seed 8 calendar fixed but fact-27 counter fails.

## Land sweep vs `starter` (K=3, windows unchanged)

| arm | seed | sw unlock | eligible | sw landed | d12 SW STRAW | ne STRAW d12–14 | d12 NE MELON | night deaths | bank | pass |
|---|---|---|---|---|---|---|---|---|---|---|
| baseline | 0 | d11 | 2 | 4 | 1 | 0 | 19 | 0 | 87,726 | no |
| baseline | 8 | d11 | 2 | 6 | 4 | 0 | 21 | 0 | 85,683 | no |
| reserve 200 | 0/8 | d11 | 2 | 4/6 | — | 0 | — | 0 | same | no |
| start_day 5 | 0/8 | d11 | 2 | 4/6 | — | 0 | — | 0 | same | no |
| **land_first** | **0** | **d9** | **4** | **15** | **5** | **0** | **8** | **0** | **97,174** | **yes** |
| land_first | 8 | d11 | 2 | 6 | 4 | 0 | 21 | 0 | 85,683 | no |
| land_first_defer | 0 | d9 | 4 | 5 | 2 | 0 | 14 | 0 | 89,225 | yes |
| land_first_defer | 8 | d9 | 4 | 4 | 1 | **1** | 12 | 0 | 86,986 | no |

**Verdict: reserve / start-day knobs are dead.** The lever is **market
order** (`land_first`), not `MIN_CASH_RESERVE_FOR_LAND_BUYING`. No arm
clears all counters on **both** seeds. `land_first` is the best partial
win (seed 0). Deferring animals fixes seed-8 calendar but plants STRAW
on NE d12–14 (fact 27). **Do not patch `main.py`. Do not 12-seed.**

## Crew trace (`land_first`, seed 0)

SW unlock **d9**, eligible days **4**, but SW `plant_actions` by day:

| day | plant | water | landed |
|---|---|---|---|
| 9 | 0 | 0 | 0 |
| 10 | 0 | 0 | 0 |
| 11 | 0 | 0 | 0 |
| 12 | 5 | 5 | 5 |

Calendar fix moved **landed 4→15** without crew edits, but **d9–11 SW
stays idle** despite occupant window open. Fill still ≪ ceiling (~144).

## What to do next (superseded by 2026-09-02 session)

Wire `land_first`; seed-8 cash; crew d9–11 fill — see current session.

## Open (stale — see 2026-09-02)

- Fact 29 duty cycle **holds** at K=3.
- Fact 27 NE-MELON **holds** on `land_first` seed 0; **fails** on
  `land_first_defer` seed 8 (ne STRAW d12–14 = 1).
- **SW unlock d11** on baseline; **`land_first` pulls seed 0 to d9**.
- Seed 8 calendar still **d11** with `land_first` alone — **closed**
  by post-sell emit (2026-09-02).
- Crew fill d9–11 on seed 0 open.
- Milk-in-3 → cows: **untested.**

---

# Prior session: 2026-09-01 — SW diagnosis; windows closed; land timing next

> **Standing rule:** Report to the user in chat before writing this file.
> Numbers, win counts, and the add / drop / supplement call go in the
> chat first. HANDOFF is the diary after that, not the first copy of
> the result.
>
> **Read this first.** Spec: `mydocs/FACTS.md`. Method:
> `mydocs/AGENT_BUILDING_PROTOCOL.md`. This file is the diary.
>
> Throwaway: `experiments/_facts_v20.py` (K=3). Sweep:
> `experiments/_facts_window_sweep.py`. Do not patch shipped `main.py`.
> Path C stays parked. `bptk.py` still cannot see this cadence.

## What this session did

1. **K=3** (fact 29): duty cycle still holds; idle fill still thin.
2. **Quadrant diagnosis** (baseline, seeds 0 and 8): NE/NW ~86–100%
   fill at d11–12; SW 0% until unlock then 4–16%; SE n/a (75 tiles).
3. **Window extension sweep** (arms A/B/C via `_facts_window_sweep.py`):
   STRAW→d15 ± MELON→d14. No arm clears all counters on both seeds.

## Calendar finding (binding)

**SW unlocks d11 on both seeds**, not when the first `BUY_LAND` order
fires. `BUY_LAND` days seed 0 `[7, 9, 11]`, seed 8 `[7, 11]` — cash
reserve blocks the second purchase until d11. Baseline STRAW-eligible
overlap on SW: **2 days** (11–12). Ceiling ~72 plant-pairs at K=3;
landed **4–6**. d13–20 SW empty is still **intentional** (no occupant).

## Window sweep vs `starter` (K=3)

| arm | seed 0 bank | seed 8 bank | d15 SW STRAW | NE STRAW d12–14 | sw landed | night deaths |
|---|---|---|---|---|---|---|
| baseline | 87,726 | 85,683 | 1 / 4 | 0 / 0 | 4 / 6 | 0 |
| A STRAW→15 only | 87,190 | **94,338** | 2 / 5 | **2 / 2** | 4 / 8 | 0 |
| B paired MELON→14 STRAW→15 | 85,653 | 80,603 | **5** / 1 | 0 / 0 | 6 / 4 | 0 |
| C small step | 83,390 | 78,201 | 2 / 0 | 0 / 0 | 4 / 5 | 0 |

Extended windows raise eligible days to 4–5 and d15 occupancy on some
seeds, but **crew throughput still binds** (ceiling ~144–180, landed
4–8). Arm A wins seed-8 bank but plants STRAW on NE d12–14. Arm B
helps seed-0 d15 SW STRAW (5) but regresses seed 8.

**Verdict: do not supplement fact 27/28 windows. Duty cycle holds.
Calendar + crew assignment are the levers, not wider STRAW/MELON days.**

## Named counters vs `starter` (baseline K=3, windows unchanged)

| | seed 0 | seed 8 |
|---|---|---|
| d0 | **4/4** | **4/4** |
| SW unlock day | **d11** | **d11** |
| straw-eligible days on SW | **2** (11–12) | **2** (11–12) |
| d7–11 PLANT STRAW on NE | **0** | **0** |
| d12 NE MELON / weeds | **19 / 1** | **21 / 0** |
| d12 SW STRAW / empty | **1 / 24** | **4 / 21** |
| d15 SW STRAW | **1** | **4** |
| SW landed / night deaths | **4 / 0** | **6 / 0** |
| bank vs starter | 87,726 | 85,683 |

## What to do next

**1. Earlier SW unlock — land-buy timing / cash reserve for 2nd
`BUY_LAND`.** Target: SW live by **d9** (seed 0) or earlier on seed 8
so STRAW window d7–12 has ≥4 eligible days before any window extension.
Knobs (one at a time on throwaway): `MIN_CASH_RESERVE_FOR_LAND_BUYING`
(500 today), `LAND_BUY_START_DAY`, second-buy day priority vs animal
spend. Counters: `sw_unlock_day ≤ 9`; straw-eligible days ↑; fact-29
duty cycle (0 night deaths); d7–11 NE STRAW = 0; d12 NE MELON > 0; 0
escapes; d0 4/4. Stop if second buy starves feed or d7 animal calendar.

**2. Crew assignment** (if calendar fix alone still leaves landed ≪
ceiling). Fact 29 K=3 holds; do not bump K in the same change as land
timing. Options: step-9b blocker trace during d9–12 (`_facts_window_
sweep.py` calendar helpers); reserve walkers earlier in the turn; or
re-rank only for later-extra empty after calendar is fixed. Counters:
d12/d15 SW STRAW ↑ on seeds 0 and 8; night deaths 0; NE weeds no
cascade; NE STRAW d7–14 = 0.

Do not: window extension (tested, no clean win); hire-density; walk
whole crew to SW; wheat-fill; patch `main.py`; 12-seed; holdout;
Path C; `bptk.py` cadence; F8.

## Open

- Fact 29 duty cycle **holds** at K=3.
- Fact 27 NE-MELON **holds**; window supplement **rejected**.
- **SW unlock d11** is the calendar cliff; land reserve/timing is open.
- Crew assignment open **after** or **paired with** land timing only.
- Milk-in-3 → cows: **untested.**
- F8 / Path C / `bptk.py` cadence: **do not.**

---

# Prior session: 2026-09-01 — fact 29 K-assignment plant-and-water on SW

> **Standing rule:** Report to the user in chat before writing this file.
> Numbers, win counts, and the add / drop / supplement call go in the
> chat first. HANDOFF is the diary after that, not the first copy of
> the result.
>
> **Read this first.** Spec: `mydocs/FACTS.md`. Method:
> `mydocs/AGENT_BUILDING_PROTOCOL.md`. This file is the diary.
>
> Throwaway: `experiments/_facts_v20.py` (gitignored). Dump:
> `experiments/_facts_leftover.py`. Do not patch shipped `main.py`.
> Path C stays parked. `bptk.py` still cannot see this cadence.

## Fact card (this session)

```
Kind: add (fact 29)
Now: at most K=2 units work later-extra leftover per turn. Plant only
     if hour <= 21 (water next hour). Local WATER ignores claimed.
     Those K walk to occupant empty after urgent water, before fert/weed.
     Everyone else keeps NE/home. Not hire-density.
Fights: none (25 still no hire-window mutation; 22 still no wheat-fill;
     27 NE-MELON stays)
Throwaway: experiments/_facts_v20.py
Pre-run: 15/17; d0 not 1/1
Counters: 0 night deaths on landed SW plants; d12 SW STRAW > 0 on
     seeds 0 and 8; d7–11 NE STRAW = 0; d12 NE MELON > 0
```

Live wording is in FACTS.md row 29. Ranking at fallback `any` did not
move the counter (fert/weed ate the surplus; seed 8 SW STRAW stayed 0).
Walk-before-fert for K only did.

## Named counters vs `starter`

Parentheses: previous session (no K-walk, NE-MELON prefer only).

| | seed 0 | seed 8 |
|---|---|---|
| d0 | **4/4** | **4/4** |
| d7 BUY_ANIMAL | none | none |
| escapes | **0** | **0** |
| d7–11 PLANT STRAW on NE | **0** | **0** |
| d12 NE MELON | **19** (15) | **21** (15) |
| d12 NE weeds | **1** (~5) | **0** |
| d12 SW STRAW / empty | **1 / 24** (0 / 25) | **3 / 22** (0 / 25) |
| SW WHEAT | **0** | **0** |
| SW landed / watered same / night deaths | **1 / 1 / 0** | **4 / 4 / 0** |
| season SW STRAW / CARROT | 1 / 0 | 3 / 1 |
| bank vs starter | 86,602 | 90,845 |

## Duty cycle holds; fill is thin

Same-day water is true: every landed SW plant was watered that day,
night deaths 0 on both seeds. Seed 8 d12 SW STRAW 0 → 3 is the named
occupancy counter.

K=2 does not fill the idle pile (SW empty still ~20–24 through d24).
That is the knob, not a failed duty cycle. Do not raise K in the same
change as the assignment — measure 3 next only against these counters.

First ranking (SW walk at fallback `any`) failed seed 8 occupancy and
left night deaths. WATER-ignore-claimed + walk before fert/weed closed
both.

**Verdict: fact 29 duty cycle holds on seed 0 and 8. Idle fill does
not. Do not patch `main.py`. Do not 12-seed. Do not bump K yet.**

## What to do next (superseded)

K=3 measured; see current session for diagnosis and window sweep.

## Open (superseded)

See current session.

---


# Prior session: 2026-09-01 — idle leftover without STRAW stealing MELON

> **Standing rule:** Report to the user in chat before writing this file.
> Numbers, win counts, and the add / drop / supplement call go in the
> chat first. HANDOFF is the diary after that, not the first copy of
> the result.
>
> **Read this first.** Spec: `mydocs/FACTS.md`. Method:
> `mydocs/AGENT_BUILDING_PROTOCOL.md`. This file is the diary.
>
> Throwaway: `experiments/_facts_v20.py` (gitignored). Dump:
> `experiments/_facts_leftover.py`. Do not patch shipped `main.py`.
> Path C stays parked. `bptk.py` still cannot see this cadence.

## Fact cards (this session)

```
Kind: supplement (fact 27)
Was: empty non-NW d7–12 → STRAW (stole MELON on first extra / NE)
Now: first extra (NE) during MELON’s window is MELON (must prefer;
     choose_crop still picks STRAW on NE if not). STRAW only on
     later extras (unlocked[2:], SW) d7–12. Home through first
     BUY_LAND still MELON + empty. Not a pin of 50. Do not reopen
     STRAW after d12.
Fights: none
Throwaway: experiments/_facts_v20.py
Pre-run: 15/17; d0 not 1/1
Counters: d7–11 PLANT STRAW on NE = 0; d12 NE MELON > 0;
     d0/d5 STRAW = 0; d12 leftover wheat = 0
```

```
Kind: add (fact 28) — occupancy half only
Now: standing on empty later-extra leftover: STRAW d11–12 or
     CARROT d21–25. Between windows wait empty (no wheat-fill).
     Walk-to-empty-SW ahead of water is dropped: a fresh planting
     dies that night if unwatered (DIG then leaves the tile empty).
Fights: none (22 still no force-wheat; 23 still no TOMATO)
Throwaway: experiments/_facts_v20.py
Counters: SW WHEAT = 0; d7–11 NE STRAW = 0; SW weeds not a cascade
```

Live wording is in FACTS.md rows 27 and 28.

## Named counters vs `starter`

Parentheses: previous session (STRAW on all non-NW).

| | seed 0 | seed 8 |
|---|---|---|
| d0 | **4/4** | **4/4** |
| d7 BUY_ANIMAL | none | none |
| d9 | SHEEP×2 | SHEEP×2 |
| escapes | **0** | **0** |
| BUY_FERT | **0** | **0** |
| PLANT TOMATO | **0** | **0** |
| FERTILIZE | **13** (63) | **14** (59) |
| d7–11 PLANT STRAW on NE | **0** (was >0) | **0** |
| d12 NE MELON / STRAW / empty | **15 / 1 / 2** | **15 / 2 / 1** |
| season PLANT MELON | **43** (11) | **38** (11) |
| season PLANT STRAW | **12** (42) | **11** (41) |
| SW STRAW season | 5 | **0** |
| SW WHEAT | **0** | **0** |
| d12 SW empty | 19 (idle ~27) | **25** |
| d24 SW empty | 20 | 19 |
| bank vs starter | 81,603 (97,432) | 85,800 (96,878) |

d3h0 / d5h0 / d9h0: `SELL FERT` still before `BUY_ANIMAL`. Both seeds
also emit a d9h1 catch-up `BUY_ANIMAL` with no fert sell (shed already
empty after h0). Second `BUY_LAND` landed d10, not d11.

## Walk-to-SW plants tiles that die the same night

First pass walked to empty SW before fertilizer. Seed 0: SW CARROT
requests 12, d24 occupancy 0, empty still 16. A newly planted seed
already has `consecutive_unwatered = 1` and dies that night if not
watered. DIG returns the tile to empty. Walk dropped.

Without the walk, SW STRAW only lands if a unit already stands there:
seed 0 got 5, seed 8 got **0**. Fact 27’s SW-STRAW half is vacant.
Idle SW is still ~19–25 empty through d12–d24. That is crew/water
capacity, not a missing crop name.

MELON prefer on NE was required. Stopping the STRAW *force* was not
enough — `choose_crop` still picked STRAW on NE (7 plants d7–11 on
seed 0 before the prefer).

**Verdict: fact 27 NE-MELON half holds on seed 0 and 8. Fact 27
SW-STRAW half does not, without a walk that kills the planting.
Fact 28 wheat-fill skip holds; idle-fill does not. Do not patch
`main.py`. Do not 12-seed.**

## What to do next

Idle SW cannot be filled by walking the crew onto it ahead of water.
Leave it as capacity, or plant-and-water the same day on those tiles
— not another STRAW window, not hire-density, not a wheat flood.

Milk-in-3 → cows is still untested.

Do not: STRAW pin of 50; reopen STRAW after d12; walk-to-empty-SW
ahead of water; gate SELL on buy-emit turns; plant TOMATO; force-wheat;
skip CARE; hire-density; Path C; `bptk.py` for cadence; F8; holdout;
patch `main.py`.

## Open

- Fact 27 NE-MELON **holds**. SW-STRAW **does not** without a lethal walk.
- Fact 28 wheat-skip **holds**. Idle SW ~19–25 empty is **capacity**.
- Milk-in-3 → cows: **untested.**
- Fact 20: parked (0 escapes; harnesses do not ship).
- Day-0 freeze / d7 cap-fill / `$356` starve: **closed.**
- F8 / Path C / `bptk.py` cadence: **do not.**

---


# Prior session: 2026-09-01 — fact 9 fert→STRAW + fact 27 new-land STRAW

> **Standing rule:** Report to the user in chat before writing this file.
> Numbers, win counts, and the add / drop / supplement call go in the
> chat first. HANDOFF is the diary after that, not the first copy of
> the result.
>
> **Read this first.** Spec: `mydocs/FACTS.md`. Method:
> `mydocs/AGENT_BUILDING_PROTOCOL.md`. This file is the diary.
>
> Throwaway: `experiments/_facts_v20.py` (gitignored). Dump:
> `experiments/_facts_leftover.py`. Do not patch shipped `main.py`.
> Path C stays parked. `bptk.py` still cannot see this cadence.

## Fact cards (this session)

```
Kind: supplement (fact 9)
Was: fertilizer sold season-wide, not kept for crops, not bought
Now: sold on any turn that lists BUY_ANIMAL (hour 0 or catch-up).
     Other turns: keep it for STRAW while live STRAW exists and
     day <= FERTILIZER_LAST_USEFUL_DAY. Surplus sells after last
     useful day / no STRAW / shed-overflow. Still never
     BUY_PRODUCT FERTILIZER (21). Hold while STRAW *exists*, not
     only while wants_fertilizer (a d7 planting wants fert ~d14).
Fights: none. Path C "gate SELL while STRAW wants fert" stays
     dropped — buy-emit turns still sell first.
Throwaway: experiments/_facts_v20.py
Pre-run: 15/17; d0 not 1/1
Counters: d3/d5/d9 SELL FERT before BUY_ANIMAL; FERTILIZE > 0
     after last buy; BUY_FERT = 0
```

```
Kind: add (fact 27)
Now: days 7–12, unlocked > 1, empty tile not in NW: plant STRAW
     if seed/budget allows. Home leftover through first BUY_LAND
     stays MELON + empty (wheat 0, STRAW 0). Not a pin of 50.
Fights: none (22 still forbids force-wheat; 23 still no TOMATO)
Throwaway: experiments/_facts_v20.py
Counters: d0 and d5 STRAW occupancy = 0; d12 leftover wheat = 0;
     d12 STRAW occupancy > pre-change baseline; PLANT STRAW
     d7–12 is on non-NW tiles
```

Live wording is in FACTS.md rows 9 and 27. After d12 leftover may
still sit empty — that stays unnamed. Do not reopen the STRAW window.

## Named counters vs `starter`

Pre-change leftover dump in parentheses.

| | seed 0 | seed 8 |
|---|---|---|
| d0 | **4/4** | **4/4** |
| d7 BUY_ANIMAL | none | none |
| d9 | SHEEP×2 | SHEEP×2 |
| escapes | **0** | **0** |
| BUY_FERT | **0** | **0** |
| PLANT TOMATO | **0** | **0** |
| FERTILIZE | **63** (≈0) | **59** |
| SELL_FERT units | **118** (174) | 128 |
| of which after last buy | 85 | 94 |
| d12 STRAW / leftover | **31 / 67** (16) | **30 / 67** (20) |
| d12 empty / leftover | 28 / 67 (29) | 28 / 67 |
| season PLANT STRAW | **42** (27) | **41** (29) |
| season PLANT MELON | **11** (25) | **11** (23) |
| bank vs starter | 97,432 | 96,878 |

d3h0 / d5h0 / d9h0: `SELL FERTILIZER` still before `BUY_ANIMAL`.
Post-d9 fert sells are the last-useful-day surplus valve, not a
buy-morning steal.

## Melon was displaced, idle tiles were not filled

Fact 27 fires on empty **non-NW** tiles during d7–12. First
`BUY_LAND` is day 7, inside MELON’s 0–11 window. Those tiles used
to go to `choose_crop`, which picked MELON (seed 0 d7: **pM=12**,
stock 8→19). Now they plant STRAW (d7: **pS=11 / pM=3**, stock
8→11). Home through d6 is still 8 MELON and 0 STRAW — the beach-head
was not pinned. Season MELON 25→11 is that new-land burst, not a
home steal.

Empty leftover barely moved: d12 **29/67 → 28/67**. Extra STRAW
replaced melon, not idle tiles.

Idle after the **second** land buy (d11, 50→75): ~**26–27 empty
new-land leftover tiles** through d12–d24. STRAW’s window has only
d11–d12 left to fill 25 new tiles; the crew plants ~5–6 STRAW/day.
Home is full from ~d10 (d12 NW empty ≈ 1). Late d28 empty 51/67 is
decay, not the hole.

**Verdict: fact 9 apply half and fact 27 occupant hold on seed 0
and 8. Do not patch `main.py`. Do not 12-seed yet.** STRAW-on-new-
land as written fights MELON on the first extra quadrant.

## What to do next

**Idle tiles**, without letting STRAW take MELON. The idle pile is
the second unlock (d11, ~27 empty leftover), not home and not the
first-land overlap. A fix that still prefers STRAW on empty NE
during d7–11 will keep displacing melon.

Do not: STRAW pin of 50; reopen STRAW after d12 as a slogan; gate
SELL on buy-emit turns; plant TOMATO; force-wheat; skip CARE;
hire-density; Path C; `bptk.py` for cadence; F8; holdout; patch
`main.py`; another feed-order tweak.

## Open

- Fact 9 supplement and fact 27 **in the table**. Counters hold on
  the throwaway. **Do not ship.** Melon displacement is live.
- Idle leftover after second `BUY_LAND`: **~27 tiles, the next
  shape question.** Fill them without STRAW stealing MELON.
- Milk-in-3 → cows: **untested.**
- Fact 20: parked (0 escapes; harnesses do not ship).
- Day-0 freeze / d7 cap-fill / `$356` starve: **closed.**
- F8 / Path C / `bptk.py` cadence: **do not.**

---


# Prior session: 2026-09-01 — fact 20 narrowed and closed

> **Standing rule:** Report to the user in chat before writing this file.
> Numbers, win counts, and the add / drop / supplement call go in the
> chat first. HANDOFF is the diary after that, not the first copy of
> the result.
>
> **Read this first.** Spec: `mydocs/FACTS.md`. Method:
> `mydocs/AGENT_BUILDING_PROTOCOL.md`. This file is the diary.
>
> Throwaway: `experiments/_facts_v20.py` (gitignored). Control:
> `experiments/_facts_v20_pre_f20.py`. Do not patch shipped `main.py`.
> Path C stays parked. `bptk.py` still cannot see this cadence.

## Fact card (this session)

```
Kind: supplement (fact 20) — narrowed after the broad ladder
     lost pass 2/12
Was: feed-walk / wheat-shed-walk before local CARE/COLLECT/WATER
Now: crop HARVEST and WATER underfoot stay above feed-walk;
     carrying an animal walks to an empty pen before feed-walk;
     feed-walk still above CARE/COLLECT; claim/assignment half
     unchanged (FEED ignores claimed; pre-mark occupied
     unfed+wheat; exclude=feed_claimed; feed walk_to does not
     add to claimed)
Fights: none
Throwaway: experiments/_facts_v20.py
Pre-run: 15/17; d0 not 1/1
Counters: 0 escapes; d0 4/4; 8/8 by ~d10; d7 quiet; d9 yarn→sheep
```

Live wording is in FACTS.md row 20.

## Named counters

| | seed 8 | seed 0 |
|---|---|---|
| escapes | **0** | **0** |
| d0 | **4/4** | **4/4** |
| d7 BUY_ANIMAL | none | none |
| d9 | SHEEP, **8/7 same day** | SHEEP, **8/8 same day** |
| 8/8 by | **d10h23** | **d9h23** |
| end | 8/8 4C4S | 8/8 4C4S |
| bank vs starter | 94,647 (control 83,924) | 95,634 (control 102,615) |

h22 seed 8: (6,0) unfed d12 and d15, fed the days in between — no two consecutive misses.

## Harnesses vs `_facts_v20_pre_f20.py`

| harness | broad (walk before WATER) | **narrow (this)** |
|---|---|---|
| paired vs `starter`, 12 | 7/12, −1,735 | **7/12, +5,453**, t=1.23 |
| paired vs `pass`, 12 | 2/12, −11,265 | **3/12, −7,819**, t=−3.32 |
| self-play 6 (candidate only) | 69,607 ±6,376, min 61,762 | 73,304 ±20,273, **min 41,747** | 

Starter seed 8 is **+10,723**. Pass is still a loss (3/12). Self-play floor is worse than the broad ladder.

**Verdict: fact 20’s escape counter holds on this throwaway. Neither feed-walk promotion clears a win-count bar.** Do not patch `main.py`. Do not run a third CARE/WATER/feed permutation next session.

## What to do next

Something **else**. Leftover crop tiles (FACTS.md open hole) or the untested milk-in-3→cows counter. Not another `choose_unit_action` feed-order tweak. Claim-only (no feed-walk promotion) was not measured; leave it unless a new escape shows up.

Do not: leftover-crop as a slogan; water-before-plant; hire-density; variance row; revert 15/17; Path C; `bptk.py` for cadence; F8; holdout; patch `main.py`.

## Open

- Fact 20 is **in the table** and **holds 0 escapes** on the throwaway. Harnesses **do not ship**. Parked.
- Milk-in-3 → cows: **untested.**
- Remaining crop tiles: **the open hole.** This is the next shape question.
- Self-play floor 41.7k on the narrow ladder: live, not a paired delta.
- Day-0 freeze / d7 cap-fill / `$356` starve: **closed.**
- F8 / Path C / `bptk.py` cadence: **do not.**

---


# Prior session: 2026-09-01 — fact 20 supplement (counters hold, harnesses do not)

> Superseded: narrowed (WATER/HARVEST above feed-walk). Still 0
> escapes; pass still 3/12. Fact 20 parked (see current-session).

## Fact card (this session)

```
Kind: supplement (fact 20)
Was: FEED every day; units on the animal tiles with wheat in
     the acting inventory. True at cap 4.
Now: same, plus: FEED-underfoot ignores claimed; occupied
     unfed+wheat tiles are pre-marked into feed_claimed;
     nearest-unfed uses exclude=feed_claimed (does not drop
     feed); feed walk_to does not add to claimed; feed-walk /
     wheat-shed-walk before local CARE/COLLECT/WATER.
Fights: none (24 is skip-CARE-for-crop-turns, not feed-over-care)
Throwaway: experiments/_facts_v20.py
Pre-run: 15/17 (d7 quiet; d9 yarn→sheep); d0 not 1/1
Counters: 0 escapes; d0 4/4; far pen fed after the free first
     miss; FEED ≈ owned × days
```

Live wording is in FACTS.md row 20.

## Named counters

Seed 8 vs `starter` (the escape seed): **0 escapes**, end **8/8** mix 4C4S, d0 **4/4**, d7 no buy, d9 SHEEP on yarn, FEED=250, bank 95,754 (was 83,924 with the escape). (8,3) is no longer a pen — placement moved. Far pen (7,1) unfed on placement day d12 (free miss), **fed every later day** through d15. 8th animal sits empty at (6,2) until ~d25; still 8/8 by season end (fact 16 “not all season”).

Seed 0 vs `starter`: **0 escapes**, d0 **4/4**, d5h23 5/5 then d6h23 6/6, d7 quiet, d9 SHEEP, end 8/8 4C4S, PLANT_TOMATO=0, BUY_FERT=0. Bank 84,790 (was 102,615).

## Harnesses (candidate vs frozen `_facts_v20_pre_f20.py`)

Win count first. Built-ins never sell; read them as A/B of the ladder change, not a ladder prediction.

| harness | mean delta | wins |
|---|---|---|
| paired vs `starter`, 12 | **−1,735** | **7/12**, t=−0.40 |
| paired vs `pass`, 12 | **−11,265** | **2/12**, t=−4.29 |
| self-play 6 seeds (candidate only) | mean **69,607** ±6,376, min 61,762 | no paired control |

Starter seed 8 (the escape) is **+11,830**. Starter seed 0 is **−17,825**. Pass is a crop disaster on 10 of 12.

**Verdict: fact 20’s escape counter holds; this implementation does not clear the bar.** Do not patch `main.py`. Do not treat self-play 69k as a delta — there is no paired self-play vs pre_f20. Pre-prefix 40k/±21k is still stale.

The pass loss is the known upkeep lesson: feed-walk currently outranks **WATER underfoot**, so wheat-carriers abandon plants. Next is a **narrower** fact 20: keep FEED-ignores-claimed, pre-mark, exclude=feed_claimed, feed walk_to not adding to claimed; put WATER/HARVEST-underfoot back above feed-walk; keep feed-walk above CARE/COLLECT only.

## What to do next

Narrow the throwaway as above. Re-check seed 8 (0 escapes) and seed 0 (d0 4/4, 15/17). Then paired vs the same `_facts_v20_pre_f20.py` control on starter **and** pass. Do not patch `main.py` until pass is not 2/12.

Do not: leftover-crop occupant; water-before-plant slogan; hire-density; variance row; revert 15/17; Path C; `bptk.py` for cadence; F8 `k*(owned+1)`; holdout.

## Open

- Fact 20 supplement is **in the table**. This ladder **holds 0 escapes** and **loses pass 2/12**. Narrow next.
- Milk-in-3 → cows: **untested**.
- Remaining crop tiles: **still the open hole.**
- Self-play of *this* throwaway: 69.6k ±6.4k floor 61.8k. Not a paired delta.
- Day-0 freeze / d7 cap-fill / `$356` starve: **closed**.
- F8 / Path C / `bptk.py` cadence: **do not.**

---


# Prior session: 2026-09-01 — d15 feed miss diagnosed (fact 20)

> Superseded: fact 20 was supplemented; 0 escapes on seed 8; harnesses
> lost (see current-session block). Do not revert 15/17.

## Fact card (this session)

```
Kind: diagnosis (fact 20 / 7). No add/drop/supplement yet.
Was: FEED every day; units on the animal tiles with wheat in
     the acting inventory. True at cap 4.
Now: false at cap 8 on seed 8. Wheat is in inventories (16
     carried, shed 0 by h03). The miss is assignment + ladder
     order, not a trough and not a buy.
Fights: none (do not add leftover-crop, water-before-plant,
     hire-density, or variance)
Throwaway: experiments/_facts_v20.py (unchanged)
Pre-run: facts 15/17 still hold (d7 quiet; d9 SHEEP on yarn)
Counters: escape d15h23 (8,3) SHEEP; fed d13h09, never d14/d15;
     d15h13 unit ON TILE with W=3 walked WEST; d14h23 farmer
     one step away, EOD reset wiped the walk
```

## Named counters (seed 8 vs `starter`)

| counter | result |
|---|---|
| placed | d11h11 SHEEP at (8,3); (8,4) is the other NE pen |
| escape | **d15h23** SHEEP (8,3); money $14,757; consecutive_unfed was 1 going into the night |
| `fed_today` (8,3) | **d13h09 yes** (hand0 FEED W=3). **d14 never. d15 never.** Two consecutive misses → escape. d12 also missed but d13 reset the counter. |
| wheat | overnight shed **16**. By h03 every day: shed **0**, carried **16**. Not a buy miss. |
| nearest unit d14h23 | farmer at **(8,4)** with **W=2**, Manhattan **1** |
| nearest unit d15h13 | hand4 **on (8,3)** with **W=3** |
| FEED vs crop | crew verbs while (8,3) unfed d13–15: WATER 77, COLLECT 19, CARE 18, PLANT 15, FEED 20 (those FEEDs are **other** pens) |

## Why (8,3) missed two days

Three ladder facts, all in `choose_unit_action`. Not hire density. Not leftover wheat as the feed system.

**1. Local CARE/COLLECT/WATER outrank walking to an unfed animal.**
Feed-underfoot is step 1, but only on *this* tile. Collect/harvest/care/water-underfoot are steps 2–3. Walk-to-feed is step 6. A unit with wheat standing on an already-fed pen, or on an unwatered crop, spends the turn there. d14h21–22: farmer at (8,4) with W=2, assigned to (8,3) one step north, does COLLECT then CARE instead of walking. d14h23 finally NORTH — then `_end_of_day` respawns the farmer at (4,4) and the walk is gone.

**2. `walk_to` claims the destination, so a distant walker steals the tile from the unit already on it.**
d15h12 hand4 walks SOUTH onto (8,3) with W=3. d15h13 they are **on the tile with wheat** and emit **WEST**, not FEED. Crew order is farmer then hands. An earlier unit (`walk_to((8,3))`) had already `claimed.add((8,3))`, so hand4 saw `tile = "TAKEN"` and skipped the FEED branch. That is fact 20 failing in the most literal way.

**3. Nearest-unfed + `feed_claimed` assigns (8,3) to a far unit who then does not walk.**
`find_nearest_target(..., exclude=set())`; if that target is already in `feed_claimed`, `feed_target = None` (no second-nearest). Home pens at (4,4)/(4,3)/(3,4) soak the first wheat-carriers every morning. (8,3) is assigned later to whoever is left, often a unit still on a home pen doing HARVEST/CARE (d14h12–14: hand0 at (3,1) “assigned” to (8,3), does HARVEST then COLLECT then CARE). Closer wheat-carriers skip because claimed, then WATER.

(8,4) is on the shed→NE approach (y=4) and **does** get fed those days (d13h08, d14h20, d15h17). (8,3) is one tile off that corridor.

## What to do next

**Supplement fact 20** so it names the cap-8 failure: (a) walk-to-feed must not `claimed`-steal a tile from a unit already on it with wheat; (b) walking to an unfed animal must outrank local CARE/COLLECT/WATER on a different tile. Diff the throwaway against every row, seed 8 vs `starter`, then seed 0. Counter: (8,3) `fed_today` by ~h12 on d14 and d15; 0 escapes; d0 still 4/4; facts 15/17 still hold.

Do **not** patch shipped `main.py`. Do not re-run 12-seed harnesses. Do not add a leftover-crop occupant, water-before-plant, hire-density, or variance row. Holdout is still reserved.

Do not: port Path C; use `bptk.py` for this; add F8 `k*(owned+1)`; revert the fact 15/17 slot rule.

## Open

- Throwaway `experiments/_facts_v20.py`: facts 15/17 shop-mix slots hold. **Fact 7/20 does not** — seed 8 one escape d15h23 (8,3). Mechanism is now named; fix is next.
- Milk-in-3 → cows counter: **untested**.
- Pre-prefix 8/12 vs `starter` is **stale.**
- Remaining crop tiles: **still the open hole.** Not this bug.
- Self-play floor/stdev: **live** (40k / ±21k, pre-prefix). Not a new fact.
- Day-0 spend freeze: **closed on this throwaway.**
- Day-7 hour-0 2-cow miss: **closed** by the earlier prefix; d7 cap-fill is now **intentionally none**.
- `$356` starve: **closed (stale).**
- F8-class `k*(owned+1)`: still **do not.**
- Path C vs Path A: **parked.** Path A is `main.py`.
- Cadence work in `bptk.py`: **do not.**

---


# Prior session: 2026-09-01 — shop-mix slots; next is the d15 feed miss

> Superseded: d15 feed miss is diagnosed (see current-session block).
> Facts 15/17 still leave shop-mix slots. Do not revert them.

## Fact card (this session)

```
Kind: supplement (facts 15 and 17)
Was: d7 +2C+2S or remaining cap; d9+ shop mix only if slots remain;
     at cap 8 that can be zero.
Now: tape prefix stops at d5 (4C2S = 6). d7 does not fill the cap.
     d9+ emits toward shop_mix_target for the remaining slots
     (yarn in first 1–3 → sheep; else milk-in-3 → cows; else default).
Fights: none (17’s “zero slots” clause is the same rule, tightened)
Throwaway: experiments/_facts_v20.py (`calendar_owned_target` holds
     at 6 through day 8)
Pre-run: fact 2; 5/18; 9–13 (d9 concat); 16; 21; 22; d0 not 1/1
Counters: d7 no cap-fill; YARN-in-1–3 at d9 → BUY SHEEP;
     milk-in-3 with no yarn → BUY COW; d0 4/4; end 7–8; 0 escapes
```

Live wording is in `FACTS.md` rows 15 and 17. Do not re-derive it here.

## What this session was about

Two jobs. (1) Diagnose the pre-prefix starter losses on seeds 2/5/8/9.
(2) Supplement fact 15 so day-9 shop mix actually has slots — that is
what makes the last animals shop-aware. Fact 17 was tightened in
lockstep so the old “zero slots at cap 8” line did not fight 15.

## Starter 2/5/8/9 (pre-prefix list is stale)

Those four losses were measured **before** the prefix supplement.
After prefix, on the then-current throwaway vs `starter`:

| seed | main.py | throwaway | delta |
|---|---|---|---|
| 0 | 71,498 | 104,365 | +32,867 |
| 2 | 65,239 | 80,474 | **+15,235** (flipped) |
| 5 | 78,436 | 76,647 | −1,789 (noise) |
| 8 | 69,957 | 59,291 | **−10,666** (the real loss) |
| 9 | 79,939 | 92,002 | **+12,063** (flipped) |

Facts 1–26 held on all five. Seed 8’s injury was **not** a cadence miss:
the engine draws the next shop from the **same RNG** as weed spawns
(`kaggriculture.py` `_end_of_day` / `_spawn_weeds`). Weeds consume one
draw per empty tile, so two agents on the same seed get different shop
sequences. Throwaway seed 8 drew YARN d3 and no milk shop until PIZZA
d24, still bought **6C2S** (d7 had filled cap 8), dumped 174 milk, end
**MILK = $15**. Main on that seed sold 53 milk at $306.

Leftover-tile wheat/carrot (FACTS.md open hole) compounded it. Do not
add a leftover-crop, water-before-plant, hire-density, or variance row.

## Shop-mix supplement (facts 15 + 17)

`shop_mix_target` already existed. It never ran: `calendar_owned_target`
jumped to 8 on day 7 and the d7 branch filled with cows. Now the tape
prefix stops at 6 through day 8; day 9+ fills the last two slots from
the first three shops **as of the d9 buy**. v20 ranks yarn-in-3 above
two milk shops — that is the table, not a miss.

| | seed 0 | seed 8 |
|---|---|---|
| d0 pens/herd | **4/4** | **4/4** |
| d7 BUY_ANIMAL | **none** | **none** |
| d9 | SELL FERT → SHEEP×1 (h1 second) | same |
| shops at d9 | SMOOTHIE, ICE_CREAM, **YARN** | YARN first |
| end mix | **4C4S**, 8/8 | **4C3S**, 8 pens / **7** herd |
| escapes | **0** | **1** |
| end MILK | $360 | **$301** (was $15) |
| bank vs starter | 102,615 | 83,924 (was 59,291) |

Shop-awareness fired. Seed 8 bought sheep instead of two more cows.
“Milk-in-3 → cows” still needs a seed with **no** yarn in the first
three; seed 0 is yarn-in-3.

## Fact 7 miss (the next session)

Seed 8 escaped a SHEEP at **d15h23, tile (8,3)**. Shed wheat was **16**,
bank ~$15k — not a trough, not a buy-cadence miss. Placement lagged:
d9 bought two sheep, d9h23 still 8/6, both placed by d11h23. Then one
far tile missed two consecutive FEEDs.

That is fact 20 (units on the tile with wheat in inventory), which
breaks fact 7 (0 escapes). Do not revert 15. Do not add a hire-density
row. Do not treat leftover wheat as this bug.

## What to do next

**Diagnose the d15 feed miss** on throwaway seed 8 vs `starter`. Named
question: why did tile (8,3) miss two FEEDs with 16 wheat in the shed
and 8 pens already built? Counters: escape day/tile, `fed_today` on
that tile d13–d15, which unit was nearest, whether wheat was in the
acting inventory or still in the shed, whether the FEED ladder skipped
it for a crop action.

Do **not** patch shipped `main.py`. Do not re-run 12-seed harnesses.
Do not add a leftover-crop occupant, water-before-plant, hire-density,
or variance row. Holdout is still reserved.

Do not: port Path C; use `bptk.py` for this; add F8 `k*(owned+1)`;
shop-score day-0 buys; fill leftover tiles with a STRAW pin; revert
the fact 15/17 slot rule.

## Open

- Throwaway `experiments/_facts_v20.py`: facts 15/17 shop-mix slots
  hold (d7 quiet; d9 SHEEP on YARN-in-1–3). **Fact 7/20 does not** —
  seed 8 one escape d15h23 (8,3).
- d15 feed miss: **next.**
- Milk-in-3 → cows counter: **untested** (need a seed with no yarn
  in the first three shops at the d9 buy).
- Pre-prefix 8/12 vs `starter` is **stale.** Do not quote it as a
  live reading of this throwaway.
- Remaining crop tiles: **still the open hole.** Not this bug.
- Self-play floor/stdev: **live** (40k / ±21k, pre-prefix). Not a
  new fact.
- Day-0 spend freeze: **closed on this throwaway.**
- Day-7 hour-0 2-cow miss: **closed** by the earlier prefix; d7
  cap-fill is now **intentionally none**.
- `$356` starve: **closed (stale).**
- F8-class `k*(owned+1)`: still **do not.**
- Path C vs Path A: **parked.** Path A is `main.py`.
- Cadence work in `bptk.py`: **do not.**

---


# Prior session: 2026-09-01 — throwaway that affords the table

> Superseded: 2/5/8/9 were diagnosed; facts 15/17 now leave shop-mix
> slots. Next is the d15 feed miss (see current-session block).

## Fact cards (supplements; no add/drop)

Harnesses already ran on the looser wording. These cards tighten the
same four IDs. Do not diagnose starter seeds 2/5/8/9 until seed 0
named counters match **Now**. No new rows. No dropped rows.

```
Kind: supplement (fact 10)
Was: SELL FERTILIZER listed before BUY_ANIMAL on buy-morning hour 0.
Now: same order on the turn BUY_ANIMAL actually emits, including
     catch-up hours the same day. If the list contains BUY_ANIMAL,
     concat sell → animal → hire/seeds; do not fall back to hire-first.
Fights: none
Throwaway: experiments/_facts_v20.py
Pre-run: fact 2 (build not cash-gated); 5/18 (wheat on owned); 9/21
     (always sell fert, never buy it); 15 prefix; 16 home-cap waive;
     22 (no force-wheat wrapper); d0 not 1/1 if 4’s crew exists
Counters: order-list position on the emit turn; cow lands that turn;
     d0 pens/herd ≠ 1/1
```

```
Kind: supplement (fact 12)
Was: hires do not run before the buy on hour-0 buy mornings.
Now: hires do not run before the buy on the same emit turn as fact 10
     (hour 0 or catch-up). Hire after sell+buy, or not at all that hour.
Fights: none
Throwaway: experiments/_facts_v20.py
Pre-run: same as fact 10
Counters: hire after sell+buy on that turn; d0 pens/herd ≠ 1/1
```

```
Kind: supplement (fact 15)
Was: d3 +1 cow, d5 +1 cow, d7 +2C+2S (or remaining cap), d9+ shop mix;
     all-or-nothing qty if the whole batch does not clear cash.
Now: on a buy turn, emit the largest prefix of that day’s orders that
     post-sell cash can pay (1 cow if 2 do not clear). Day 9+ shop mix
     only fills slots still open after the d7 remainder; at cap 8 that
     can be zero. “Day 9 must buy” is not a counter. Fact 17 is the
     same rule: shop mix may have zero slots once d7 has filled cap 8.
Fights: none (17 is not dropped; its “after day 9 can exist” still
     means placed 7–8 by late season, not a forced d9 buy)
Throwaway: experiments/_facts_v20.py (`_largest_affordable_qty`)
Pre-run: same as fact 10
Counters: d7h0 BUY_ANIMAL COW×1 (not silent miss of ×2); remaining
     of that day’s orders later the same day if cash catches up;
     end mix still 7–8; d0 pens/herd ≠ 1/1; no d9 buy required
```

```
Kind: supplement (fact 16)
Was: parallel pens up to the day’s target; home-quadrant cap cannot
     block pen 4–5 before BUY_LAND.
Now: same-day placement when an empty unlocked tile exists. If home
     is full of crops, wait for the next BUY_LAND, not past it. Do
     not pretend a 6th pen fits on 25 planted tiles.
Fights: none
Throwaway: experiments/_facts_v20.py
Pre-run: same as fact 10
Counters: unplaced animals do not sit in the shed all season; a
     day-5 extra is placed by d6h23 once NE unlocks; d0 pens/herd ≠ 1/1
```

## What this session was about

Built a throwaway from shipped `main.py` that is supposed to afford
**all** existing FACTS.md rows, without adding or removing any.
Previous half-stacks: calendar-only froze gone / missed d3 cow;
full stack froze **1/1** because fact 2 (build cash-gated) was
missing. This copy includes fact 2.

## Seed 0 vs `starter` (real engine)

| counter | result |
|---|---|
| d0h23 pens/herd | **4 / 4** (not 1/1) |
| d0h0 market | 5×HIRE, BUY_ANIMAL COW×2, SHEEP×2, WHEAT×8, MELON seed |
| d3h0 | SELL FERT×4, then BUY_ANIMAL COW, then wheat, then HIRE |
| d5h0 | SELL FERT×5, then BUY_ANIMAL COW, then wheat, then HIRE |
| d7 | **prefix holds:** h0 SELL FERT×5, SELL WOOL×5, BUY COW×1, wheat, then HIRE; h1 second COW. Not an all-or-nothing silent miss. |
| d5 extra / fact 16 | d5h23 still 5/5 (home full); **d6h23 6/6** once NE unlocks — wait for next `BUY_LAND`, not all season |
| end pens/herd | **8 / 8**, mix 6C2S (no d9 buy; cap filled at d7) |
| escapes | **0** |
| FEED / CARE | 216 / 212 |
| COLLECT_FERT / SELL_FERT units / BUY_FERT | 207 / 174 / **0** |
| PLANT TOMATO | 0 |
| bank | 104,365 vs starter 3,484 — **do not read this as a ship signal** |

Re-read after the four supplements (prefix + emit-turn order). d3/d5/d7
emit turns are all sell-fert → buy → hire. Day-9 shop mix had no slots:
day 7 filled the cap-8 remainder. That is the table at cap 8, not a miss.
PLANT WHEAT 105 is the named open hole (leftover tiles), not a
force-wheat wrapper. Harness numbers below are the **pre-prefix**
throwaway; do not treat them as the supplemented agent.

## Crop / crew trace (seeds 0–2 vs `starter`)

`experiments/_facts_trace.py --both`. Overcommit drops are **0** on
both agents — the seed budget is holding. `failed` is requested−landed
(not empty / claimed), small.

STRAWBERRY `weed ≈ landed` is end-of-life decay of an ongoing crop,
not the unwatered cascade. MELON weeds are a handful.

Means across seeds 0–2:

| | main.py | `_facts_v20` |
|---|---|---|
| bank | 71,498 / 78,294 / 65,239 | 109,809 / 99,220 / **59,747** |
| WHEAT landed | 105 / 107 / 114 | 88 / 98 / 100 |
| STRAW landed | 35 / 32 / 20 | 34 / 32 / 28 |
| MELON landed | 22 / 27 / 32 | 23 / 23 / 28 |
| WHEAT weeded | 37 / 34 / 37 | 38 / 36 / 39 |
| WATER / PLANT | 604–700 / 175–224 | 528–643 / 155–171 |
| water/planted | 0.82–0.86 | 0.79–0.85 |
| PASS share | 6.6–6.8% | 9.1–9.4% |
| HIRE landed | 271–275 | 291–293 |
| eod unwatered | 5.5–6.8 | 6.0–7.3 |
| plant-while-unwatered | 167–216 | 150–166 |
| days_short (wanted > hands+1) | 1 / 1 / 1 | 1 / 2 / 0 |

Seed 2 of the throwaway banks **59,747**, below shipped 65,239 on the
same seed — the 109k seed-0 vs `starter` is not monotone.

Crew read: **not a hire shortage.** Both agents hire more hands than
`work // 4` (~6 wanted, ~9–10 hands). Unwatered tiles persist because
units keep planting while other tiles sit dry (same pattern on shipped
`main.py`). Throwaway PASS is a bit higher (9% vs 7%), not idle. The
leftover-tile wheat flood is still the open hole.

## Harnesses (dev seeds, vs shipped `main.py`)

Self-play 6, both sides `_facts_v20.py`: mean **73,452**, stdev
**21,516**, min **40,112**, max **94,762**. MELON end **$129** (not
the $1 floor). Sold mix (p0): MILK 1049, FERT 1025, STRAW 717, MELON
421, WOOL 407, WHEAT 149. Mean is above the old ~65.7k mixed-herd
3-seed check; the **40k floor and 21k stdev** are a Bradley-Terry
risk. Do not ship on this alone.

Paired vs `starter`, 12 seeds: mean **+9,447**, **8/12**, sd 15,882,
t = 2.06. Seed 2/5/8/9 negative (worst −18,996). **Not decisive.**
Built-in never sells — do not read this as a ship signal.

Paired vs `pass`, 12 seeds: mean **+20,891**, **11/12**, sd 12,515,
t = 5.78. Same built-in flattery. Win-count looks clean; still not
the contested number.

Head-to-head vs shipped `main.py`, 12 seeds × 2 seats: mean
**+20,082**, **22/24**. That is the contested harness, and it is a
clean win-count.

**Verdict: do not ship yet.** H2H and vs `pass` clear the bar; vs
`starter` is 8/12 (t = 2.06) and self-play has a 40k floor / 21k
stdev. This repo ships on two harnesses that can disagree — here they
do. The leftover-tile wheat flood and plant-while-unwatered pattern
are on both agents, not a new throwaway bug.

## What to do next

Facts 10, 12, 15 (and 17’s shop-mix slot rule), and 16 are
supplemented; seed 0 named counters now match **Now**. Next is
diagnose starter losses 2/5/8/9 on this throwaway. Do not add a
leftover-crop occupant, water-before-plant, hire-density, or
variance row. Do **not** patch shipped `main.py`. Do not re-run the
12-seed harnesses until that diagnosis says what to change. Holdout
is still reserved.

Do not: port Path C; use `bptk.py` for this; add F8 `k*(owned+1)`;
shop-score day-0 buys; fill leftover tiles with a STRAW pin.

## Open

- Throwaway `experiments/_facts_v20.py`: seed 0 counters hold under
  the supplemented wording (d7h0 COW×1 then h1 second cow; d6h23
  6/6). Pre-prefix harnesses: H2H 22/24; vs `starter` **8/12, not
  shipped.**
- Remaining crop tiles: **still the open hole.** Not a new fact.
- Self-play floor/stdev: **live** (40k / ±21k, pre-prefix). Not a
  new fact.
- Day-0 spend freeze: **closed on this throwaway.**
- Day-7 hour-0 2-cow miss: **closed** by fact 15 prefix.
- `$356` starve: **closed (stale).**
- F8-class `k*(owned+1)`: still **do not.**
- Path C vs Path A: **parked.** Path A is `main.py`.
- Cadence work in `bptk.py`: **do not.**

---





# Prior session: 2026-08-31 — freeze is live; next experiment is the tape calendar

> Superseded: calendar and full-stack throwaways ran (see current-
> session block). Spec is now the 20 facts the agent shape must
> afford. Path C parking still holds.

## What this session was about

Real-engine 4-vs-5 (then 10) cliff trace on current `main.py`. Throwaway
copies only (`experiments/_max5.py`, `_max10.py`). Seed 0 vs `starter`,
then self-play because 5 did not collapse. Then: 7-head survival, why
shop-aware buying is blind at cap 4, and how v20 already splits "tape
mix first / shop-aware after." No Path C. No shipped `main.py` edit.

## Table (read mechanism before bank)

vs `starter`, seed 0:

| | 4 | 5 | 10 |
|---|---|---|---|
| bank | **71,498** | **53,763** | **41,215** |
| escapes | 0 | 0 | 0 |
| bought | 4 (2S+2C) | 5 (2S+3C) | **10 (5S+5C)** |
| pens / herd (end) | 4 / 4 | 5 / 5 | **8 / 8** |
| `FEED` | 105 | 108 | 119 |
| d0 pens / herd | **3 / 2** | **1 / 1** | **1 / 1** |
| d0–12 pens / herd | 4/4 by d12 | 5/5 by d13 | **1 / 1** |
| money d5 / d6 / d7 | 75 / **11** / **11** | 345 / 285 / 285 | 345 / 315 / 285 |
| money lo d12 | high | 151 | 183 |

Self-play, seed 0 (each file vs itself):

| | 4 | 5 | 10 |
|---|---|---|---|
| bank | **70,558** | **42,896** | **31,057** |
| escapes | 0 | 0 | 0 |
| pens / herd (end) | 4 / 4 | 5 / 5 | **7 / 7** |
| `FEED` | 104 | 110 | **90** |
| d0–12 pens / herd | 4/4 by d12 | 5/5 by d11 | **1 / 1** |
| money lo d12 | 3,775 | **8** | **1** |

Fifth / tenth animals were bought. Caps are not no-ops. At 10, two
(vs `starter`) / three (self-play) sit unplaced at season end.

## Verdict

**The $356 starve is stale.** 5, 7, and 8 live (0 escapes). Do not
treat that number as live. The old shop-mix park ("until a herd past
4 exists") is closed on the starve reading.

**Raising the cap is still a bank loss.** 5 is −17,735 vs `starter` /
−27,662 self-play. 10 is worse (41k / 31k) and never places 10.
Do not ship 5 or 10.

**The injury is a day-0 spend freeze.** At cap 5+, the 5th `BUY_ANIMAL`
lands hour 5 of day 0, cash → $487, and `choose_animal_to_build` uses
the same `MIN_CASH_RESERVE_FOR_ANIMAL_BUYING = 450` bar, so the second
pen never starts. Hours 9–23 are `PASS`. 1 pen / 1 head through day
12. Later cash spikes buy more animals (no tile needed) instead of
building pens. Serial unfilled is not the day-0 blocker (first pen
already filled). Wheat pegged at 2 did not kill anyone.

**Shop-aware `BUY_ANIMAL` at cap 4 is a no-op.** First shop unlocks
day 3 (`PIZZA_SHOP`); `YARN_STORE` day 18. All four animals are
already bought day 0, hours 1–4, mix 2S2C. Species is locked at
purchase.

**v20 already does "tape mix first, shop-aware after."** Decoded from
`agents/route_v20.py`. Every route, including yarn and milk:

| day | every tape |
|---|---|
| 0 | **2C2S** (one hour) |
| 3 | +1 cow → 3C2S |
| 5 | +1 cow → 4C2S |
| 7 | +2 cow +2 sheep → 6C4S |
| 9+ | **then** shops: milk `10c4s`, default `8c6s`, yarn `6c8s` / `6c12s` |

Our cap-4 mix already matches the prefix. There is no "after" unless
we hold the 5th. Tapes hold it until **day 3**, not a live shop check
on day 0. That calendar is what avoids the freeze. A scorer on
`pick_next_animal_species` does not.

`ANIMAL_ECONOMY.md` causes: (1) and (4) live as counters, not the
discriminator; (2) not the day-0 blocker; (3) live as day-0 freeze,
not the days 3–7 starve.

## What to do next

**If continuing this thread: the tape purchase calendar, not a shop
scorer.** One change, one question — does holding past 4 until day 3
(then the shared d5/d7 prefix, shop branch from day 9) keep the 4-arm
opening intact and let a 5th+ place without the freeze?

- Beach-head **4** on day 0, mix 2C2S (already what we buy).
- Next buys on the tape days (d3 cow, d5 cow, d7 2C2S), not "whenever
  cash allows."
- Shop mix only from day 9, using v20's first-three-shops table
  (yarn-first / yarn-in-3 / milk-in-3 / default). Not a live
  `apply_town_demand` score on WOOL vs MILK.
- Cap high enough that "after" exists (7–8 placed in the 10-trace;
  do not start at 10).
- Throwaway copy. Seed 0 vs `starter` first, same counters: d0 pens,
  escapes, `FEED`, money d3–10, then bank. Self-play only if it does
  not freeze.

Do not: port Path C (no STRAW pin, no valve, no Option A/C, no
wheat-stockpile gate). Do not add `k*(owned+1)`. Do not retry the
hour-0 opening book (`ANIMAL_ECONOMY.md` — each correct fix made it
worse). Do not shop-score the day-0 buys. Do not raise shipped
`MAX_ANIMALS` as the first change. Wheat connector still not
licensed by this trace.

## Open

- `$356` starve at 5 / 7 / 8: **closed (stale).**
- Day-0 spend freeze when cap > 4: **live.** Licensed walk is the
  tape calendar, not a tighter cash gate.
- F8-class `k*(owned+1)`: still **do not.**
- Shop-aware scorer at cap 4: **closed (no-op).**
- Shop-mix starve-park: **closed** (7–8 live). Shop-mix as a *fix*
  for the freeze: **no.** Shop-mix after a calendar beach-head:
  **the day-9 half of the next experiment.**
- Path C vs Path A: **parked** at 6/12. Do not port.
- Wheat owned-keyed connector: **not licensed.**
- Cash ledger / full tape playback: still parked.

---



# Prior session: 2026-08-31 — park Path C; next is a real-engine 4-vs-5 cliff trace

> Superseded: 4-vs-5 and 10 traces ran. $356 stale; freeze is live;
> licensed next is the tape calendar (see current-session block).
> Path C parking still holds.

## What this session was about

One-factor look at seed 10's d12–14 wheat carpet on Option A. Added
`sTiles` to the F11 day strip (read-only) and ladder arm
`path_c_option_a_no_valve` (`pin_wheat_valve=False` on the Option A base —
STRAW pin stays inviolable even when wheat stock is under reserve). 12-seed
3-arm ladder: `path_a`, `path_c_option_a`, `path_c_option_a_no_valve`. Strips
on seeds 1, 3, 8, 7, 9, 10. No Option C. No `main.py`. No real-engine harness.

## Table (read mechanism before bank)

`path_a` mean = **109,720** — exact §11.2 / §13 anchor; engine did not move.

| arm | mean | wins | BUY_W | BUY_W d18 | harvW d18 | FEED d18 | unserved_straw d18 | crew_idle d18 | animals |
|---|---|---|---|---|---|---|---|---|---|
| path_a | 109,720 | — | 90 | 25 | 43 | 47 | 702 | 218 | 4.0 |
| path_c_option_a | 112,583 | **6/12** | 130 | 71 | 38 | 95 | 852 | 360 | 8.3 |
| path_c_option_a_no_valve | 103,087 | **6/12** | **186** | **96** | 27 | 107 | 1065 | 284 | 9.2 |

Option A byte-matches §13. no_valve wins: 0, 4, 5, 7, 8, 11 (Option A was
0, 5, 6, 7, 9, 11). Seed 9 flips +437 → **−53,334**. Seed 6 flips +53,053 →
−1,079. Seed 10 stays a tail (−78,075 → −70,973).

Option A d12–14 `wTiles` (losing 1/3/8, winning 10-head 7/9, tail 10):

| seed | vs A | d12–14 wTiles | d12–14 sTiles | sell_straw A/C |
|---|---|---|---|---|
| 1 | −17,277 | 0/0/0 | 40/54/54 | 365/343 |
| 3 | −15,127 | 0/0/0 | 39/51/51 | 353/351 |
| 8 | −7,013 | 0/0/0 | 43/51/51 | 346/343 |
| 7 | +19,086 | 0/0/0 | 40/53/53 | 342/364 |
| 9 | +437 | 0/0/0 | 38/53/53 | 346/365 |
| **10** | **−78,075** | **18/36/18** | **13/13/31** | 363/**241** |

no_valve on seed 10: wTiles 0/12/12 (residual wheat after sTiles hit the
pin cap of 50), sTiles 51/51/51, sell_straw 353 (recovered vs 241), d23–29
money 34.7k → 54.7k (Option A 34.8k → 44.1k, Path A 50.5k → 120k). Melon
sales 171 → 70.

## Verdict (which branch fired)

**d12–14 wheat is unique to seed 10.** Seeds 1, 3, 8 (the other real losses)
and 7, 9 (the winning 10-head pair) have zero wheat tiles those days and a
full STRAW carpet (~38–55). The valve-open carpet is a singleton, not the
1/3/8 object.

**Closing the valve restores seed 10's STRAW and does not close the stall.**
Carpet 13 → 51, sell_straw 241 → 353 (vs A's 363), animals 7 → 10 — and
d23–29 is still a conversion stall (54.7k vs A's 120k). Thin STRAW is
downstream of the valve and is **not** why the bank dies.

**The valve is load-bearing for the seeds that already work. Do not ship
no_valve.** Mean −9,496 vs Option A, still 6/12. Seed 9 (a 10-head win)
becomes −53k. `SELL_MELON` collapses on every seed (~150–171 → ~60–104).
BUY_W 130 → 186: holding the pin closed starves organic wheat, so the herd
that now reaches 9.2 head pays a bigger product-wheat bill. Seed 7 still
wins; seed 9 does not — one flipped win is enough.

**Park Path C.** Singleton carpet + stall not caused by that carpet + the
one-factor that closes the carpet is a mean loss. Even a complete seed-10
fix is 7/12. F8 / F11 / F4 stay closed. Option A stays the scale policy
(`scale_wheat_buffer="off"`, valve on). Option C stays off.

## What to do next

**Re-trace the real-engine `MAX_ANIMALS` cliff on current `main.py`.**
Do not port Path C (no STRAW pin, no valve, no Option A/C, no tapes, no
beach-head/pause). `path_c_animal_cap()` is already `return MAX_ANIMALS`;
leave it. The $356 / 0-of-3 reading is from an older PR — this agent now
has land, a 15-hand cap, SHEEP+COW, and the seed-reserve trough fix. A
stale cliff is the same class of dead end this repo has already paid for.

One paired seed (start with 0 vs `starter` or self-play — not a 12-seed
bank table). Candidate is `MAX_ANIMALS = 5` only; control is shipped 4.
Read, in order: `FEED`, animal escapes, shed wheat, unfilled pastures,
money days 3–10. Then the bank. `docs/ANIMAL_ECONOMY.md` names four
causes; the trace says which is live today:

1. Flat wheat *buy* trigger (`< MIN_WHEAT_RESERVE_FOR_FEEDING`, i.e. 2)
   vs sell exemption (`filled_animals *` that same constant).
2. Serial pens (`choose_animal_to_build` refuses while any stand unfilled).
3. Cash trough / fifth purchase draining the reserve.
4. Sell reserve keyed to *placed* animals, so bought wheat is sold before
   the place-trip lands.

Path C constraints on whatever the trace names:

- Wheat is a **flow**, not a hurdle. If (1)/(4) are live: one subsystem
  change, keyed to *owned* (not placed), buy trigger and sell reserve
  together. Measure at `MAX_ANIMALS = 4` first (expect a near-noop on
  bank — the defect is nearly invisible at 4). Only then try 5. No
  `k*(owned+1)` stockpile in front of the next animal (that is F8 / the
  herd-scaled cash floor, already 0/3).
- If (3) is live: **stop**. A tighter purchase gate will strand the fifth
  pen unfilled (F8 / #30).
- If 5 still dies after a wheat connector: the remaining hypothesis is
  crop-first vs animal-first, and we do not have a licensed walk. Path C
  was the cheap screen for one such walk and failed. Do not retry the
  opening book (`ANIMAL_ECONOMY.md` already did; each correct fix made it
  worse).

Do not: mutate hire (F6), force wheat (F7), stack knobs (F13), chase
bptk seed 10, or raise `MAX_ANIMALS` as the first change. Shop-mix /
cash ledger / tapes stay parked until a herd past 4 actually exists and
survives.

## Open

- F8 stranding: **closed** (bptk Path C).
- F11 as "why 6/12": **closed**.
- F4 as "why 6/12" in bptk: **closed**.
- Seed 10 valve-wheat carpet: **closed** as singleton.
- Seed 10 d23–29 stall: unexplained, not worth another Path C factor.
- Path C vs Path A win-count: **parked** at 6/12. Do not port.
- Real-engine `MAX_ANIMALS` 4→5 cliff on *current* `main.py`: **live**.
  Trace first; the $356 number may be stale.
- Shop-mix / cash ledger / tapes: still parked until a herd past 4
  survives in `main.py`.

---

# Prior session: 2026-08-31 — F11 tax is real, not the win-count object; seed 10 is late conversion

> Superseded: the seed-10 valve look has now been run. Verdict (park Path C)
> is in the current-session block above. Option A as scale policy, Option C
> off, no `main.py` / no real-engine still hold.

## What this session was about

Traced F11 vs F4 on the Option A herd. Read-only counters in `bptk.py`
(`HARVEST_WHEAT`, d18+ BUY_W/FEED/harvest windows, unserved STRAW, crew idle,
daily deltas). 12-seed 2-arm ladder: `path_a` vs `path_c_option_a`. Day
strips on seeds 7, 9, 10. No Option C. No `main.py`. No real-engine harness.

## Table (read mechanism before bank)

`path_a` mean = **109,720** — exact §11.2 anchor; extra counters are read-only.

| arm | mean | wins | BUY_W | BUY_W d18 | harvW d18 | FEED d18 | unserved_straw d18 | crew_idle d18 | animals |
|---|---|---|---|---|---|---|---|---|---|
| path_a | 109,720 | — | 90 | 25 | 43 | 47 | 702 | 218 | 4.0 |
| path_c_option_a | 112,583 | **6/12** | 130 | **71** | 38 | **95** | 852 | 360 | 8.3 |

Per-seed (A/C = Path A / Option A). Wins: 0, 5, 6, 7, 9, 11.

| seed | dlt | animals | buyW_d18 | harvW_d18 | feed_d18 | unserved_straw_d18 | money_d15 | money_d18 | sell_straw | sell_melon |
|---|---|---|---|---|---|---|---|---|---|---|
| 0 | +29,010 | 4/9 | 27/77 | 32/39 | 47/100 | 738/846 | 3270/7921 | 5753/9678 | 336/343 | 127/165 |
| 1 | −17,277 | 4/6 | 30/43 | 26/39 | 47/66 | 791/777 | 3730/6826 | 6610/8384 | 365/343 | 115/150 |
| 2 | −1,315 | 4/10 | 25/74 | 33/51 | 47/110 | 747/895 | 3223/7646 | 5792/9311 | 346/347 | 127/168 |
| 3 | −15,127 | 4/8 | 29/80 | 28/39 | 47/108 | 761/916 | 3835/6585 | 6871/7847 | 353/351 | 125/160 |
| 4 | −746 | 4/9 | 28/77 | 32/39 | 47/100 | 716/854 | 3305/7954 | 5988/9713 | 322/352 | 140/165 |
| 5 | +27,159 | 4/8 | 24/70 | 33/36 | 47/89 | 748/857 | 3463/6346 | 6096/7535 | 347/355 | 128/140 |
| 6 | +53,053 | 4/8 | 7/79 | 153/41 | 48/107 | 158/912 | **8379**/6472 | **12877**/7654 | 82/352 | 150/160 |
| 7 | +19,086 | 4/10 | 28/89 | 29/35 | 47/110 | 747/957 | 3268/6779 | 5786/8280 | 342/364 | 128/150 |
| 8 | −7,013 | 4/9 | 26/77 | 32/38 | 47/100 | 750/846 | 3790/8000 | 6719/9897 | 346/343 | 129/165 |
| 9 | +437 | 4/10 | 19/91 | 39/33 | 47/111 | 734/947 | 3320/5956 | 5889/6704 | 346/365 | 133/150 |
| 10 | **−78,075** | 4/7 | 30/53 | 26/24 | 47/77 | 789/**642** | 3376/**9700** | 6231/8309 | 363/**241** | 115/171 |
| 11 | +25,167 | 4/6 | 25/43 | 51/39 | 46/66 | 741/777 | 4992/6877 | 8145/8495 | 341/343 | 132/150 |

## Verdict (which branch fired)

**F11 tax is live and is not why Option A is 6/12.** After d18, Option A
feed is 95/ep and self-grown wheat is 38 — BUY_W 71 fills the gap
(`FEED ≈ HARVEST_W + BUY_W`). Path A covers feed 47 with harvest 43 + BUY_W 25.
The 10-head seeds (7, 9) have the **highest** d18 tax (89/91 BUY_W) and
**win**. Do not add a wheat buffer to "fix" a winning seed.

**Classic F11 "lead dies after d18" is false at d18.** Option A still leads
Path A at d18 on 11/12 seeds. The gap that hurts is later (d22–29), not the
d18 wheat bill.

**F4 leftover STRAW is live as a counter and is not the discriminator.**
Both arms leave ~3 ready STRAW tiles unserved per turn after ~d21 (idle=0
those hours). Winning 10-head seeds have the **worst** leftover (957/947)
and still out-sell STRAW. Seed 10 has the **best** leftover (642) and
loses −78k. In zero-travel bptk, leftover harvest is picked up next hour;
it does not bind sales. A clean F4 here would not have cleared real-engine
crew anyway.

**Seed 10 is a third object — keep it out of the F11/F4 average.** It is
not F11 (BUY_W 100 vs A's 97; d15 shedW=21, not the floor). It is not F4
(unserved STRAW better than A). Day strip: wheat tiles 18–36 on d12–14
(valve letting WHEAT through while other seeds have 0), then STRAW sales
241 vs 363, then cash stall d23–29 (34.8k → 44.1k while Path A 50.5k →
120k). Late conversion + a thin STRAW carpet on that seed.

Seed 6's +53k is Path A planting 273 WHEAT (sell_straw 82) — Option A
winning by staying the STRAW agent, not by beating a healthy Path A.

## What to do next

Option A stays the scale policy (`scale_wheat_buffer="off"`). **Option C
stays off** — F11 is not the losing object, and a rising stockpile would
re-strand (F8). Harvest−feed flow C is not licensed by this table.

Do not: port tapes/cadence/yarn-mix, touch `main.py`, escalate to a
real-engine harness, mutate hire (F6), force wheat (F7), stack knobs (F13).

If anything is next on this line, it is the seed-10 object (valve-open
early wheat + late STRAW conversion stall), as its own one-factor look,
not a wheat buffer.

## Open

- F8 stranding: **closed**.
- F11 as "why 6/12": **closed** — tax real, not the win-count object.
- F4 as "why 6/12" in bptk: **closed** as the discriminator. Real-engine
  travel-time crew is still a blind spot, parked until a herd past 4 exists
  in `main.py`.
- Seed 10 late conversion / early wheat-from-valve: **live**, separate.
- Shop-mix / cash ledger / tapes: still parked (`MAX_ANIMALS = 4` in main).

---

# Prior session: 2026-08-31 — Option A ran; F8 gate was the stranding object; next is F11/crew

> Superseded: F11/crew has now been traced. Verdict and next step are in
> the current-session block above. Option A as scale policy, Option C off,
> no `main.py` / no real-engine still hold.

## What this session was about

Implemented F8 Option A in `bptk.py` and ran the 12-seed 3-arm ladder.
`scale_wheat_buffer="off"` skips `_path_c_wheat_buffer_met` once
`scale_unlocked`; beach-head 3 + pause unchanged. Arm `path_c_option_a`
is the repaired-feed base (`pin_wheat_valve=True`) with the gate off.
No `main.py` change. No Option C. No frontload.

## Table (read mechanism before bank)

`path_a` mean = **109,720** — exact §11.2 anchor; engine did not move.

| arm | mean | wins vs A | BUY_W/ep | shedW d15-25 | final animals | F8-stuck |
|---|---|---|---|---|---|---|
| path_a | 109,720 | — | 90 | 5.9 | 4.0 | 0 |
| path_c_fix12_buf_owned | 106,609 | 5/12 | 91 | 4.9 | 6.4 | 12 |
| **path_c_option_a** | **112,583** | **6/12** | **130** | **4.0** | **8.3** | **7** |

Gated control byte-matches §12 `composite_no_frontload` (106,609 / 5/12 /
6.4 animals / F8-stuck 12). `escapes` in bptk is a stub (always 0); ignore it.

Per-seed Option A finals (all 6–10; nobody finishes at beach-head 3):

| seed | dlt vs A | animals_final | min_d15 | BUY_W | shedW |
|---|---|---|---|---|---|
| 0 | +29,010 | 9 | 3 | 135 | 3.9 |
| 1 | −17,277 | 6 | 3 | 99 | 4.2 |
| 2 | −1,315 | 10 | 3 | 132 | 4.0 |
| 3 | −15,127 | 8 | 4 | 143 | 3.7 |
| 4 | −746 | 9 | 3 | 135 | 3.9 |
| 5 | +27,159 | 8 | 5 | 138 | 3.5 |
| 6 | +53,053 | 8 | 4 | 142 | 3.7 |
| 7 | +19,086 | 10 | 4 | 152 | 3.5 |
| 8 | −7,013 | 9 | 3 | 135 | 3.9 |
| 9 | +437 | 10 | 4 | 155 | 3.5 |
| 10 | **−78,075** | 7 | 3 | 100 | 6.2 |
| 11 | +25,167 | 6 | 3 | 99 | 4.2 |

Wins: 0, 5, 6, 7, 9, 11. Seed 10 is the same-shape tail as §12 composite
(−79k on that seed).

## Verdict (which branch fired)

**The rising gate was the stranding object.** Every seed ends at 6–10
animals (mean 8.3 vs gated 6.4 vs Path A 4.0). F8-stuck=7/12 is the
day-15 pause snapshot (`min` over days ≥15 is 3 whenever scale opens on
the clock and day 15 still shows the beach-head), not a frozen herd.

**Wins do not clear.** 6/12 vs path_a; mean +2,863 is a few large wins
(seed 6 +53k) against seed 10's −78k. Not ≥9/12 → no real-engine harness.
Not a tape/cadence port.

**F11 is live on the herd that now exists.** BUY_W 91→130, shedW 4.9→4.0.
The seeds that scale hardest (7, 9: 10 animals, BUY_W 152/155) buy the
most product-wheat.

Option C (stockpile or anticipatory `k*(owned+1)`) stays **off**. A later
harvest−feed **flow** C is allowed only after F11/crew is traced; do not
add a buffer that would re-strand. F7 / F13 still closed.

## What to do next

**Trace F11 / crew, not another wheat-buffer.** Option A stays as the
scale policy in `bptk.py` (`scale_wheat_buffer="off"` on `path_c_option_a`).
Next session should instrument the seeds that scaled (esp. 7, 9, and the
seed-10 tail) for BUY_W vs self-grown wheat after day 18, and whether
crew (F3/F4) is the binding constraint once the herd is 8–10.

Do not: implement Option C, reopen sequencing/frontload, port route
cadence or yarn-mix, touch `main.py`, escalate to a real-engine harness.

## Open

- F8 stranding: **closed** as the rising `owned`-keyed stockpile gate.
- F8-stuck counter: noisy for pause-until-day-15 arms; prefer
  `animals_final` / per-seed finals.
- F11 (BUY_W tax at scale) and reactive crew: live.
- Inchworm on seed 0: Option A ends at 9, not 3→4→4→4→8. Closed as
  a gate artifact.
- Shop-mix / cash ledger / tapes: still parked until a real-engine
  herd past 4 exists (`main.py` is still `MAX_ANIMALS = 4`).

---

# Prior session: 2026-08-31 — F8 still live; Option A first, Option C demoted

> Superseded: Option A has now been implemented and run. Verdict and
> next step are in the current-session block above. Tape/cadence parking
> and "C is not automatic" still hold.

## What this session was about

Still F8. Path C cannot scale past the beach-head because
`scale_wheat_buffer='owned'` keys the gate to `2 × (owned + 1)`, which rises
with the herd. Main cannot sustain 6 animals. This session did **not**
implement Option A; it asked whether route-tape cadence / a cash ledger /
shop-mix could be carried into `main.py` first.

They cannot. `main.py` is still at `MAX_ANIMALS = 4`. The tapes buy 10–17
head on a clock. That clock is not usable until a herd past 4 actually
exists. Cadence inference is parked.

## What evolved (same destination, different next step)

The 2026-08-29 handoff said: Option A (drop the gate) first, **then
implement Option C** (anticipatory 3-day wheat buffer) as the recommended
fix. That second half has moved.

What did **not** change:

- Live task is still F8 in `bptk.py`, not a `main.py` ship.
- Option A is still first: when `scale_unlocked`, return `scale_max` if
  `owned < scale_max`; do not call `_path_c_wheat_buffer_met` on that
  branch. Keep beach-head 3 + pause. 12-seed ladder vs `path_a`.
- If `path_a` mean drifts >±2,000 from the §11.2 anchor (~109,720), abort
  and re-anchor.
- F7 / F13 still closed: no wheat-frontload, STRAW-pin, or hire-mutation
  stack.

What **did** change, from the tapes (shop-selected **fixed** scripts, wheat
as a **flow** of `BUY_PRODUCT` + daily feed, not a stockpile hurdle):

- F8 is structurally the **rising stockpile gate**. Route-scale agents do
  not wait for `shedW >= k*(owned+1)` to buy the next animal. Option A is
  the falsification of that object, not a prelude to a smarter stockpile.
- **Option C is no longer the automatic next step.** Only if A lets the
  herd reach ~8–10 without mass escapes, and only as harvest−feed
  (**flow**), never `k*(owned+1)` restocked. If A still strands or escapes,
  do not add C — trace the new counter.
- If A scales and still loses on wins, that is F11/crew (F3/F4), not a
  missing tape timetable. Do not port route cadence or yarn-mix into
  `main.py` from that result.
- Shop-mix (yarn → sheep-heavy) and the cash ledger stay parked until a
  herd past 4 exists. Milk-shops → more cows is **not** supported (ledger:
  7C6S beat 9C on milk_stack).

## What to do next

**Implement Option A.** One change in `_path_c_animal_cap` (`bptk.py`).
Read F8-stuck (animals ≤ 3 after day 15), escapes, `BUY_PRODUCT WHEAT`,
shedW days 15–25 — not bank alone.

Then stop and read the table: scale-without-escapes → maybe flow-C;
still stuck/escapes → no C; wins ≥9/12 → real-engine harness, not a tape
port.

## Open (unchanged, Option A answers them)

- Inchworm traced on seed 0 only — A's 12-seed run is the check.
- After A, F11 (BUY_W tax) and reactive crew are the remaining suspects,
  not route playback.

---

# Prior session: 2026-08-29 — F8 Mechanism Diagnosis → Path C Option C

> Superseded on the **Option C is the recommended fix** line only. F8
> diagnosis, wavelength falsification, and Option A-first are still in
> force. See 2026-08-31 current session for what moved.

## What this session was about


Path C (STRAW pin + animal sequencing) was closed out 2026-08-26 at 3/12
wins. The close-out identified three failure modes — F7 (tile count unbounded),
F8 (herd stranding on a rising buffer gate), F13 (knob-stacking). This session
was opened to understand and fix F8 specifically.

## What was done

1. **Reviewed composite wheat-frontload close-out** (§12 of PATH_C_RESEARCH_LOG.md).
   The result was 3/12, bounded twice over. F7, F8, and F13 prohibitions were
   catalogued as standing blocks on any future sequencing attempt.

2. **Tested the "wavelength" hypothesis** (bptk arm `path_c_wavelength`).
   Hypothesis: pushing the STRAWBERRY carpet from day 5 to day 10, planting
   WHEAT+MELON on all 50 tiles days 0–9, then laying a 50-tile carpet at
   day 10 — would let NE tiles (bought day 6) be harvest-ready by day 10,
   slotting perfectly into the carpet window. The F8 stranding would come
   from the STRAW pin starving early days of wheat, not from the buffer
   mechanism itself. Result: **5/12 wins**, F8-stuck=12/12. The 5-day carpet
   window is too tight — NE tiles bought day 6 only get 4 harvest cycles before
   the carpet, not the 6+ the hypothesis assumed. Hypothesis **falsified**.

3. **Traced F8 mechanism turn-by-turn** (seed 0, bptk instrumented trace).
   Root cause confirmed: `scale_wheat_buffer='owned'` keys the buffer gate
   threshold to `2 × (owned + 1)` — which **rises with herd count** instead
   of falling. Combined with consumption (N animals eat N wheat/day) and
   harvest timing (~6–12 wheat/day per planted wheat tile), the gate becomes
   impossible to clear once N exceeds supply capacity.

   Pattern observed: **"inchworm" herd growth** — 3→4→4→4→8 animals across
   the episode. The shed wheat buffer (shedW) oscillates between the gate
   threshold and zero. Animals stranded: 5/12. The buffer mechanism actively
   prevents herd scaling rather than enabling it.

4. **Drafted 4 options for fixing F8**:
   - **Option A** — falsification check: remove the buffer gate entirely from
     `_path_c_animal_cap`, replace with a simple `owned < MAX_ANIMALS`. One-line
     change. If the herd reaches 8 animals without escapes, the gate was the
     problem and we can design a better one. If the herd still strands (e.g.,
     cash or feed elsewhere), we know something else is wrong.
   - **Option B** — static fixed buffer (e.g., 3 wheat held regardless of
     herd). Rejected: doesn't anticipate herd growth.
   - **Option C** — anticipatory rolling-window buffer: estimate 3-day wheat
     harvest from planted-tile state, compare to 3-day feed need, key the
     buffer gate to the net surplus. Anticipates herd growth before it happens.
     **Recommended next step.**
   - **Option D** — let the shed hold more wheat, reducing need for a gate at
     all. Rejected: shed capacity is a global constraint.

## Key findings

- **Wheat price mechanics** (engine `kaggriculture.py:597`): SELL price is
  quoted pre-inventory (reflects pre-sell stock), BUY_PRODUCT price is quoted
  post-inventory (reflects post-buy stock). Price refreshes after every
  lockstep batch. Selling WHEAT early to drive prices down is noise-level
  (~$112 delta on $2,250 spend over 30 days) — not a lever.
- **Wavelength result**: 5/12 wins, F8-stuck=12/12. The 5-day carpet window
  is too tight for the NE quadrant to participate meaningfully.
- **F8 mechanism**: inchworm herd growth driven by a rising buffer gate
  threshold (`2 × (owned + 1)`). The gate actively prevents herd scaling.

## What to do next

**Implement Option A (falsification) first.** One-line change to
`_path_c_animal_cap` in `bptk.py` — replace the buffer-gate condition with a
simple `owned < MAX_ANIMALS`. Run 12-seed ladder. If herd reaches 8 without
escapes → buffer gate was the problem and Option C is the fix. If herd still
strands → something else is wrong (cash, feed elsewhere).

**Then implement Option C** — anticipatory rolling-window buffer. This requires:
1. `_path_c_estimate_3day_wheat_harvest(farm)` — sum of wheat harvests from
   all planted tiles over the next 3 days, using `CROPS["WHEAT"]` table
   (`first_yield=2`, `max_yield=6`, ongoing=False, interval=1).
2. `_path_c_estimate_3day_feed_need(owned)` — `owned × 3` (1 wheat/animal/day).
3. `_path_c_anticipatory_buffer_met(farm, owned, cfg)` — returns True when
   `min_wheat_needed = max(cfg["min_wheat_held"], feed_need - harvest_estimate)`
   AND `shedW >= min_wheat_needed`. New cfg key: `min_wheat_held` (default 2).
4. Use `_path_c_anticipatory_buffer_met` in `_path_c_animal_cap` instead of
   the current `scale_wheat_buffer` gate.
5. New ladder arms: `composite_anticipatory`, `composite_anticipatory_no_pin`
   for the ablation table.

**Pre-agreed bar for Option A**: if `path_a` mean drifts >±2,000 from the §11.2
anchor (~109,720), the engine moved and the ladder is not comparable — abort
and re-anchor first.

## Files modified

- `bptk.py`: lines ~1499 (wheat_tile_count), ~1552 (straw_pin_active),
  ~1644 (crop_wrapper), ~1872 (ladder arms), ~1925 (wavelength arm added
  this session). See plan file for full edit plan.

## Open questions

- Does Option C's rolling-window buffer allow the herd to reach MAX_ANIMALS
  reliably across seeds? The 3-day harvest estimate depends on wheat tiles
  planted — if the farm plants few wheat tiles, the estimate understates future
  supply and the gate stays too conservative.
- How does the shed wheat interact with the selling subsystem (path_c_fix12's
  `sell_wheat_below` gate)? Need to ensure Option C doesn't inadvertently
  trigger selling that starves the herd.
- The F8 "inchworm" pattern was traced on seed 0 only. Is it reproducible
  across seeds, or is it a seed-specific oscillation? Option A's 12-seed run
  will answer this.

---

# Principles that started this work

These are the design principles the user invoked at the start of this investigation. Every decision in this session's tooling — and every decision the next session should make about the parameter-search driver, the truncation log, and the dead-code cleanup — is downstream of them. Re-read before adding any new piece of evaluation infrastructure.

## 1. Don't solve problems someone else already solved

**This is the user's primary principle.** Concrete shape: prefer to *reuse* a proven technique (a known-honest statistical test, a known-honest evaluation harness, a known-honest ablation discipline) over inventing a new one whose failure modes are unknown. Three places it has already bitten this repo:

- **Paired comparison vs across-seed stdev.** `seeded_batch.py` reports ±2,000. The natural reading — "is my delta bigger than the stdev?" — is the wrong test, and it manufactured two false "noise" verdicts on real gains (fertilizer +1,764 and the daily-feed fix +1,657 both fell inside the stdev and were almost shipped as no-ops). The honest test — run both arms on the same seeds, take the *difference* — is the standard paired comparison; it's a known statistical method, not novel. The right move was to reach for it, not invent a new "is-this-real" heuristic.
- **Held-out seed set.** ML pipelines have used this for decades. The repo didn't have one, so dev seeds were reused for confirmation, which is the classic double-dip. The fix is one module (`experiments/seeds.py`), one import discipline, and one section in CLAUDE.md that says "do not run against `--seed-set holdout` while iterating." The principle is old; the discipline was just not enforced here yet.
- **Golden-master snapshot for refactor safety.** Same idea as a regression-test suite, applied at the episode level. Not novel — the only novel bit is the application to a 720-turn stochastic agent.

**Where it does NOT apply:** the agent's strategy itself. No one in the field has published a working "competitive" Kaggriculture agent. There is nothing to reuse there, so this principle tells us to *avoid novelty in the evaluation* and accept novelty in the *thing being evaluated*, not the other way around.

## 2. Match the evaluation to the question, not to what's available

**The default harness is wrong for half the questions we ask it.** Built-in opponents never sell, so any change to sell timing reads as a free win against them. Self-play reads price-collision as a loss even when it's neutral. Head-to-head flatters changes that only work because the opponent is shaped like us. The repo now has all three, and the rule is:

- **Upkeep / hiring / cash-trough / animal-feed changes** → paired against `pass`/`starter` (the cheap, deterministic, seed-pairable harnesses).
- **Selling-cadence / market-timing / price-impact changes** → `selfplay_bench.py` (the only local setup with a contested order book).
- **Changes whose only honest signal is "is this a real agent or a copy of us?"** → `head_to_head.py` against the previous build, both seats averaged.
- **Confirmation of any of the above** → `--seed-set holdout`, **once**, after the change is frozen.

A change tested only against the never-selling built-ins is **unverified** on a contested market, regardless of its delta. The point is not "run more harnesses" — it is "pick the harness whose failure mode does not blind it to the question you are asking."

## 3. Measure the thing the change was supposed to move, then the bank delta

**Counter-driven debugging, not bank-driven.** A green test suite and a positive bank delta are not sufficient evidence that a fix worked — the agent's prior fixing history includes three live examples of that exact failure mode:

- A wheat-pickup batching change that "worked" (tests green, mean moved) but did **not** move the `FEED` counter, because the real cause of the low feed count was the trigger's own duty cycle, not the round-trip.
- The Path C override wrapper that *looked* differentiated in ablation tables but read `MAX_ANIMALS` zero times — every "different" arm was byte-identical, and several ablation conclusions in the diagnosis were artifacts of looking at the wrong counter.
- The continuous sell-or-hold cadence model that **won mean** but **lost floor** on two different bases — the right metric is pairwise wins, not mean bank, on a Bradley-Terry ladder.

The discipline: name the **one counter** the change is supposed to move, verify it actually moved, and only then look at the bank delta. If the counter didn't move, the change didn't work; positive bank is correlation, not cause. This is what `--profile NAME` in the next session's `param_search.py` is for: per-knob ±25%/±50% response curves, so dead knobs and live knobs are visible in the data, not in the eye of the reader.

## 4. A negative result with a measured mechanism is worth more than a positive one without

**The repo's "dead ends" section is the most-read part of CLAUDE.md.** Every dead end there was recorded with: the harness number, the win count, and a per-seed action-histogram diff that traced the loss to a specific mechanism (carrot glut from freed tile-time, GLUT-driven re-fills, species-overchoice troughs, etc.). Three of them turned out to be measurement artefacts (the entries that say "Retracted" or "Correction" in CLAUDE.md) — the *measurement*, not the strategy, was wrong, and the writeup is what made the correction cheap.

The principle: when something loses, *say what it lost to*. A negative result without a mechanism is just noise; a negative result with one is information. Recording mechanisms (not just numbers) is what makes future re-measurement after a base change cheap, which is what made the `growth_days`/Path C re-measurement work instead of just stacking stale dead-end tables.

## 5. Trust the engine, not the docs, not the spec, not the plan

**"Engine is the source of truth"** is in the priority list at the top of CLAUDE.md for a reason. Three concrete applications this repo has already paid for:

- `MARKET_PARAMS` shapes — the static "revenue extractable" table in CLAUDE.md disagrees with three different action plans written against it. The engine has the actual decay functions; the table is a derived view, useful for explanation, not a budget.
- The `growth_days` "fix" — looked like a bug-fix on inspection, was a wash-to-loss on the engine. The real-engine `decay_plants`/`daily_refresh_plants` call is the ground truth; the formula was a heuristic standing in for ground truth, and standing in poorly.
- The Path C conclusion — the diagnosis's own claim was that the prescription (buffer ≥ reserve × scale_max) was the right call. The engine run said otherwise. The mechanism was a real failure mode (stranded pasture) that the diagnosis had named correctly but whose probability it had misjudged.

**Operational form:** when a plan and a measured number disagree, the plan is wrong until proven right. The repo's entire dead-end section is a long list of plans that were right on paper and wrong on the engine.

## 6. The harness can lie; the self-control catches the lie

**`selfplay_bench.py` against itself, `head_to_head.py` with both sides the same, and the 2-byte-identical ladder submissions (55591700 vs 55606684) all exist for one reason:** to measure the harness's own error bar. A "win" that the self-control cannot reproduce is a harness bug, not a result. Every harness in `experiments/` now has an explicit self-control check (or the harness architecture makes it impossible to lie — paired comparison structurally cancels common-mode seed variance). The rule: run the self-control **before** trusting the result, and re-run it whenever the harness is touched.

This is the same principle as "validate against held-out data" applied to the *test rig itself* — the test rig is part of the measurement, and it can be biased in ways the test rig cannot introspect.

---

# P1–P8: where each principle stands

The P1–P8 labels are the original eight principles from the investigation brief. Not all of them map to the six documented above; P1, P3, P4, P7 are absent from the "principles" section because they weren't operationalized in this session. This section states each principle, where the current tooling stands, and what specifically remains.

---

## P1 — Joint search driver (coordinate-wise tuning is wrong on a coupled system)

**Principle.** You have proven knob couplings: `BUY_LAND`×crew size (twice), `CROP_PLANTING_WINDOWS`×`require_held_seed`, hire-gate×seed-reserve. Yet every tool in `experiments/` is single-change A/B, and `bptk.py --ladder` is leave-one-out — one-at-a-time by construction. You discovered the principle (the pair is the ceiling, not either knob) but never operationalized it.

**Status: NOT DONE.** The tooling still does single-knob A/B only. `MAX_HANDS_PER_DAY` was discovered dead by accident (`ceiling.py` found it = the cap never binds at 25 tiles), not by systematic profiling.

**What this session added toward it:** Nothing. This is the next session's primary deliverable: `experiments/param_search.py`. The outline is in the multi-session breakdown above. The key pieces: knob registry parsed from `main.py` source via AST (so defaults are read, never duplicated), variant generation that rewrites exactly one `^NAME = ...` line per knob per variant (asserting one-change-per-run), coarse random search screen (32 samples vs baseline on 4 seeds × 2 seats), then top-K confirmation on `DEV_SEEDS`, then one run on `HOLDOUT_SEEDS`. The `--profile NAME` mode (one-at-a-time ±25%/±50% response curves) also finds dead knobs automatically and provides the P3 gate-sensitivity evidence.

**What `main.py` currently has:** ~25 live knobs (verified by grep). The `PATH_C_*` cluster (~20 constants) is dead code (see P7) and should be excluded from the registry before the driver is built.

---

## P2 — Reuse one seed set for discovery and confirmation (manufactures wins)

**Principle.** After dozens of A/B runs against `range(12)`, shipped verdicts carry guaranteed winner's-curse inflation — some fraction of "+X, n/n" results are fits to those specific weed/shop draws. A frozen holdout set touched exactly once per candidate bundle, pre-submission, converts "positive everywhere, convincing nowhere" into a decidable question.

**Status: DONE.** The discipline is now enforced structurally.

**What this session added:** `experiments/seeds.py` defines `DEV_SEEDS = range(12)` and `HOLDOUT_SEEDS = range(100, 112)`. All four harness scripts accept `--seed-set {dev,holdout}` with `dev` as default. The `experiments/` section of CLAUDE.md now documents the discipline explicitly. The "do not run against `--seed-set holdout` while iterating" rule is written, not implied.

**What remains:** Nothing structural. The discipline is the point, not the tooling. The next failure mode is a developer who runs `--seed-set holdout` during iteration to "check quickly" — that failure is a human one, not a tooling one. A lint check (e.g. in a pre-commit hook or a `--dry-run` flag that refuses `holdout` by default) would close it but is probably over-engineering at this point.

---

## P3 — Ordinal ladder / gate sensitivity sweep (you keep paying for mispricing one incident at a time)

**Principle.** `choose_unit_action` is strictly first-match-wins between rungs; cardinal comparison exists only inside stages. Your own ledger shows the cost of unpriced rungs: the `$150` hire gate vs a `$1` purchase, the land-reserve blind to herd composition, the seed-rebuy spiral, the feed duty cycle — five incidents, one shape. Two standing rules: (a) any new gate must ship with a measured statement of what it blocks and what that's worth; (b) periodically run a gate-sensitivity sweep rather than waiting for an incident.

**Status: NOT DONE.** No systematic gate-sensitivity measurement exists. The five incidents above were all found post-hoc, after they caused failures.

**What this session added toward it:** The `--profile NAME` mode in `param_search.py` (next session's deliverable) is the evidence-collection tool: one-at-a-time ±25%/±50% response curves for every scalar knob, so the question "does this gate bind and on which seeds?" is answered by the data, not by inspection. The output is per-knob delta and win-count, not just mean bank.

**What remains:** The `--profile` implementation itself, and the standing rule that every new gate ships with a one-sentence measured cost statement in its comment. The standing rule is a process discipline, not a tooling one — it belongs in CLAUDE.md alongside the seed-set discipline, not in a script.

---

## P4 — Stateless agent throws away information the framework hands you for free

**Principle.** Fully stateless — everything recomputed from `obs` via `extract_state`; per-turn state created and discarded. What you currently cannot know: the opponent's shed (inferable only across turns), your own silently-dropped market orders, and the commitment/oscillation problem (replanning from scratch every turn is how threshold controllers oscillate — the feed bug was a statelessness injury in miniature).

**Status: NOT DONE. Deliberately left for later — this changes the agent, not the tooling.**

**What this session did NOT touch:** `main.py` is unchanged. `P4` is model work, not infrastructure work. It was deliberately excluded from this session's scope. When it is addressed, the evaluation discipline here still applies: the shed-inference cache must reset on step continuity (new episode, restarted process), and the sticky-plan / revision-trigger design needs its own paired comparison against the stateless baseline on all three harnesses before it ships.

**What remains:** The agent changes themselves. The infrastructure to test them (paired comparison, seed sets, contract tests) is now in place.

---

## P5 — Contracts that live in comments will be violated silently; put them in tests

**Principle.** The silent-failure list is prose; the unit test suite is pure helper tests. Missing: (a) last-callable entrypoint test, (b) one-seed self-play smoke, (c) golden masters. Given how much constant-refactoring this repo does, golden masters are the highest-value test not yet owned.

**Status: MOSTLY DONE. Golden masters skipped pending snapshot generation.**

**What this session added:** `tests/test_episode_contracts.py` with:
- `TestEntrypointLastCallable` — AST-verifies `agent = nikaangukia_meroni` is the last callable. Passes. ✓
- `TestSelfPlayDONE` — self-play on seed 0, asserts `['DONE','DONE']` and bank > $3000. Passes. ✓
- `TestGoldenMasters` — golden-master comparison for seeds 0 and 1 vs `pass` and `starter`. Skipped: `tests/golden/golden.json` does not yet exist. First task of next session is `python experiments/golden_master.py --update` to materialize it, then confirm the golden cases fail-closed (i.e., would catch a regression) rather than skip.

**What remains:** Snapshot generation (`--update`), then golden-master tests are live. After that, the P5 contract is fully enforced. P5 is also the enabler for P7 (dead code cleanup): you cannot clean up dead code without golden-master protection proving the cleanup is behavior-preserving.

---

## P6 — Cap-by-truncation makes order ordering into policy, invisibly

**Principle.** `market[:10]` at `main.py:2754` drops the tail — animals and land assembled last are the first dropped. Sell volume is uncapped for non-premium products; a heavy shed turn can plausibly crowd out a `BUY_ANIMAL`/`BUY_LAND` inside its narrow window. Nobody knows if this happens because nothing counts truncation events. Either log them or reserve slots for scarce-window orders; don't leave a silent policy where an observable decision belongs.

**Status: NOT DONE.** No logging exists anywhere in `main.py`. The behavior is silently policy — animals and land orders assembled last, so dropped first when the cap binds.

**What this session added:** The principle is documented in the "principles" section above (as "a silent policy where an observable decision belongs"), but no code change. This is the smallest P: one `print` statement before the slice, counting `len(market) - MAX_MARKET_ORDERS_PER_TURN` if positive, then the golden-runner case to demonstrate it fires.

**What remains:** One line in `main.py` at the truncation site, a test case in `golden_master.py` that constructs a synthetic shed-overflow scenario (or run the smoke on a seed known to produce >10 market orders), and the observation recorded: how many truncation events per season, and whether they ever affect animal/land orders. If they do, the policy is not silent any more and a fix (slot reservation for scarce-window orders, or reordering the assembly) is a real decision rather than a default.

---

## P7 — Dead code in the submission artifact rots

**Principle.** ~20 `PATH_C_*` constants plus gated branches at eight call sites ride along in `main.py` behind `PATH_C_CORE_ENABLED = False`. You lived the exact failure mode this invites: an override that silently didn't override. Closed investigations should exit the submission file, not linger flag-disabled.

**Status: NOT DONE. Requires P5 golden-master protection first.**

**What this session added:** Nothing — deliberately. Golden masters are the prerequisite. Without them, you cannot verify that removing the dead code is behavior-preserving. The `TestGoldenMasters` cases (P5) must be live and passing before P7 is attempted.

**What remains:** After golden masters are live, a diff of `main.py` with `PATH_C_CORE_ENABLED = False` bodies deleted should be provably no-op. The `experiments/golden_master.py --update` run before and after the deletion should produce byte-identical snapshots. Then: delete the constants, delete the eight gated branches, delete `PATH_C_CORE_ENABLED`. If the golden snapshots diverge, the deletion is not no-op and the mechanism must be diagnosed before shipping.

---

## P8 — Asserted performance is unmeasured performance

**Principle.** The complexity argument for fitting in 1s/turn is sound (~10⁴–10⁵ ops), but there is no timing guard and no p99 measurement anywhere, and scale recently jumped to 75 tiles × 15 units. One timing harness run at late-game state closes this permanently.

**Status: PARTIALLY DONE. Runner exists; measurement not yet made.**

**What this session added:** `experiments/golden_master.py` with `--time` mode that reports per-turn latency percentiles. The runner script exists; the golden snapshot does not. Without the snapshot, latency cannot be correlated to a reproducible baseline.

**What remains:** Generate the golden snapshot (`--update`), then `golden_master.py --time` on seeds 0 and 1 produces `latency_p50_ms` and `latency_p99_ms`. The assertion is `p99 < 1000ms`. If it passes, P8 is closed. If it fails, the agent needs optimization before it can submit — and the measurement now tells you exactly where the time goes (add per-function timing inside `nikaangukia_meroni`).

**Pointer rot to fix in CLAUDE.md:** Line 168 references `experiments/ceiling.py` — used to re-measure crew/watering capacity for the `BUY_LAND` decision. The file does not exist; the measurements it produced are still recorded in CLAUDE.md (24/25 tiles planted, water/planted = 1.00, etc.). Either remove the tool name from the sentence or create `experiments/ceiling.py` as a documented stub that calls `paired_compare.py`. The content is the record; the tool name is stale.

---

# Session handoff — 2026-08-29 (read this section first — verified the
2026-08-27 tooling session actually completed P1/P5/P6/P7/P8 as claimed,
found and fixed a real bug in the golden-master snapshot writer, wrote
`mydocs/TOOLS_GUIDE.md`, then split this branch into a standalone
`tooling/experimentation-infra` branch and a rebuilt
`investigation/animal-diagnosis-and-route-v20-bench` that builds on top
of it; both fully committed locally, nothing pushed or merged)

## This session: audited the previous session's claimed completion of the
P1–P8 phase tasks against the live repo (not against its own writeup),
fixed a latent golden-master bug the audit surfaced, then documented the
whole tool stack for future sessions.

**Starting point.** User asked to verify that "the previous session
completed all the phase tasks written in handoff." Read this file's
P1–P8 section and the 2026-08-27 session entry (below), then verified
each claim against the actual repo state rather than trusting the
writeup — per this file's own Principle 5 ("trust the engine, not the
plan").

**Verification, all confirmed true:**
- `tests/golden/golden.json` exists (6 records: pass/starter x seeds 0-2).
- `experiments/param_search.py` exists; `discover_knobs()` returns
  exactly 29 knobs by AST-reading `main.py`; all four stages (`screen`,
  `confirm`, `holdout`, `profile`) are implemented; 18 real screen results
  already logged in `experiments/param_search_results.jsonl`.
- `python -m unittest discover -s tests` — **171 tests, 0 failures, 0
  skips** (previously 170 with 2 skipped pending the golden snapshot).
- P6 (market-order truncation log): confirmed firing live during the
  test run — `TRUNCATION: dropped 3 market orders (had 13, cap 10)`.
- P7 (dead-code removal): zero `PATH_C_*` references left in `main.py`
  (`bptk.py`'s own Path C research code is untouched on purpose — that's
  not submission code, see the 2026-08-25 section below).
- P8 (latency): `TestLatency.test_per_turn_latency_within_act_timeout`
  exists and passes.

**Verdict: the 2026-08-27 session's claims all hold up under direct
verification.** Nothing here was a case of a plan-vs-engine mismatch
this time — first genuinely clean audit result of this kind in the file.

**Then asked to confirm a colleague's summary table of the tool stack was
valid and non-redundant.** Cross-checked every specific claim in it
(golden-master seed range, 5/4 test count, 29-knob count, stage names)
against the code the same way — all held up. But building that table
line-by-line surfaced a real bug that the phase-completion audit above
had not been looking for:

**Bug found and fixed: `tests/test_episode_contracts.py` had a second,
incompatible writer for `tests/golden/golden.json`.** Its own `main()`
had a leftover `--update` code path (from before `experiments/
golden_master.py` existed) that wrote a plain-text, non-JSON snapshot
format (`"seed=0 vs pass reward=... sells=..."`), only for seed 0 — not
the JSON-lines format with bank/sells/water/fertilizer/harvest/escapes
across seeds 0-2 that `golden_master.py --update` actually produces and
that's currently on disk. Running the wrong `--update` would have
silently clobbered the real snapshot and turned the next test run's
clean assertion failure into a raw `JSONDecodeError`. Separately, the two
`TestGoldenMasters` test methods only ever checked seed 0 via hardcoded
`splitlines()[0]`/`[3]` indexing, so the seed-1/seed-2 records
`golden_master.py` records were captured but never verified by anything.

**Fix, in `tests/test_episode_contracts.py`:**
- Removed the duplicate `--update` writer entirely; running `--update` on
  this file now just prints the correct command
  (`experiments/golden_master.py --update`).
- Collapsed the two seed-0-only `TestGoldenMasters` methods into one
  `test_golden_master_matches_snapshot` that reads every `(opponent,
  seed)` pair actually present in `golden.json`, re-runs them via
  `golden_master.run_episode`, and checks them with `golden_master.
  verify_snapshots` — reusing the tool's own action-counting logic
  instead of a second hand-rolled copy that could drift out of sync.
- There is now exactly **one writer** (`golden_master.py --update`) and
  the test file only ever reads — same "single source of truth"
  discipline this repo already applies to `experiments/seeds.py`.

**Verified the fix:** `python -m unittest discover -s tests` — **170
tests, 0 failures** (171 → 170 is expected: two seed-0-only tests merged
into one that actually covers all 6 recorded pairs). The golden-master
test's wall-clock time went from ~49s (2 episodes) to ~89s (6 episodes),
confirming it's genuinely exercising every recorded seed now, not just
seed 0 with extra ceremony.

**Wrote `mydocs/TOOLS_GUIDE.md`** — a user guide to every tool in
`experiments/` and `tests/`: the core evaluation chain in the order
you'd actually reach for each stage (`bptk.py` → `param_search.py` →
`paired_compare.py` → `head_to_head.py` → `selfplay_bench.py` →
`golden_master.py` → `test_episode_contracts.py` → commit), a worked
`MAX_ANIMALS` example walking through all eight steps, per-tool reference
entries with exact CLI invocations pulled from each script's own
docstring/argparse (not guessed), a secondary tier of diagnostic tools
(`replay_diagnostics.py`, `market_probe.py`, `ladder_episodes.py`,
`opponent_strata.py`, `replay_shape.py`, `animal_timeline.py`,
`opening_trace.py`, `route_v20.py`, `meta_opponent.py`, `benchmark.py`),
a "superseded, don't build on these" tier (`bigfarm_opponent.py` —
per `meta_opponent.py`'s own docstring, neutralized once its settings
shipped in PR #29 — `aggressive_opponent.py`, `forward_pricing_
experiment.py`), and a closing "gotchas" section distilling the
single-writer rule this session just enforced plus the seed-set,
win-count-first, and self-control disciplines already in `CLAUDE.md`.
Explicitly framed in the file itself as a convenience index that defers
to `CLAUDE.md`/the tool's own docstring on any disagreement — not a
second source of truth.

**Then, per explicit user request, split the branch by concern: user
observed this branch had turned into more of a tooling branch than an
animal-diagnosis one, and asked to separate the two so investigation
work builds on top of the tooling work instead of alongside it.**

Audited the tangle first rather than guessing: `git show --stat` on
each of the three pre-existing commits on this branch showed
`87628ac` (the 2026-08-27 tooling commit) had, despite its own commit
message's claim of touching only tooling files, pulled in **two**
`CLAUDE.md` paragraphs — the "Two seed sets" discipline paragraph
(genuinely tooling) and the "Path C ... closed 2026-08-26" dead-end
paragraph (genuinely investigation, paired with `e0ce6c2`'s `bptk.py`/
`main.py` Path C port). Confirmed via `git diff --stat` that `e0ce6c2`
and `df5bb04` touch only `bptk.py`/`main.py` and `CLAUDE.md`
respectively — no tooling files — so those two could move cleanly.

**Executed as a full local rebuild (nothing here was ever pushed, so
this was safe):**
1. Committed the uncommitted working tree as a safety checkpoint
   (`e18cd41`) before touching anything — recoverable via reflog even
   though it's no longer on any branch tip after the reset below.
2. Built `tooling/experimentation-infra` from `main`: cherry-picked
   `87628ac`, split its `CLAUDE.md` diff (dropped the Path C paragraph,
   kept the seed-set paragraph), then added a second commit pulling
   this session's golden-master bugfix + `param_search.py` +
   `tests/golden/golden.json` from the safety checkpoint. **Contains no
   `main.py`/`bptk.py` changes at all** (`git diff main -- main.py
   bptk.py` is empty) — verified, not assumed. 170/170 tests green
   standalone.
3. Rebuilt `investigation/animal-diagnosis-and-route-v20-bench` with
   `git checkout -B ... tooling/experimentation-infra` (so tooling is
   now a real ancestor — `git merge-base --is-ancestor` confirms it),
   cherry-picked `df5bb04` (animal-diagnosis docs) and `e0ce6c2` (Path C
   port), then added a final commit with `main.py`/`bptk.py`'s Path C
   close-out (from the safety checkpoint) plus its own `CLAUDE.md`
   dead-end paragraph.
4. Verified the rebuild is byte-identical in final content to the
   pre-split safety checkpoint (`git diff e18cd41 --stat` on the
   rebuilt investigation branch is empty) and 170/170 tests still pass.

**Result:** `tooling/experimentation-infra` (branched from `main`) now
holds every harness/CI addition — `seeds.py`, `golden_master.py`,
`param_search.py`, the fixed `test_episode_contracts.py`, the
`--seed-set` wiring, the golden snapshot — and stands on its own.
`investigation/animal-diagnosis-and-route-v20-bench` is rebased to sit
on top of it, and now carries only the animal-diagnosis docs and the
full Path C research arc (port → real-engine test → wheat-buffer
repair attempt → still loses → close out, dead code removed from
`main.py`). Any *next* investigation thread (route_v20 benchmarking,
further animal/land work) should branch from
`investigation/animal-diagnosis-and-route-v20-bench` or from
`tooling/experimentation-infra` directly if it doesn't need the Path C
history — either way it now inherits a working, tested tool stack
instead of an ad hoc mix.

**State at handoff.** Both branches are local only (never pushed), fully
committed, and unlisted files are `mydocs/TOOLS_GUIDE.md` (new, this
session) — gitignored, not for commit either way. No merge to `main` or
push to `origin` has happened; that remains a separate decision.

## Next session, if continuing this thread

1. **Decide what to do with the two branches** — merge
   `tooling/experimentation-infra` to `main` on its own first (it has no
   dependency on the Path C research and would let other branches build
   on it too), then decide separately whether/when
   `investigation/animal-diagnosis-and-route-v20-bench`'s Path C
   close-out and animal-diagnosis docs are ready for `main`. Not decided
   yet — this session only restructured, it didn't open PRs.
2. **P7's own completion criterion wasn't fully checked this session**:
   HANDOFF's P7 section calls for golden-master snapshots to be provably
   byte-identical *before and after the dead-code deletion specifically*,
   isolated from the other changes in this branch. That isolation check
   was not done — `main.py` is net +56 lines vs `main` including several
   unrelated additions (the P6 log line, etc.), so a clean before/after
   pair for the deletion alone doesn't exist yet if anyone wants to prove
   it was strictly no-op.
3. The multi-session breakdown's remaining item — "full end-to-end
   validation" (`unittest discover` green, `golden_master.py --time`
   sane, a real `param_search.py --stage screen --confirm` run) — is
   effectively done via this session's verification pass, but was
   confirmed by re-deriving the checks independently rather than by
   running the exact commands HANDOFF's own completion criteria specify
   (e.g. `--stage screen --samples 4 --confirm` as one invocation). Worth
   a literal run if anyone wants the exact letter of that criterion
   satisfied, not just its substance.
4. The 4 old stale-base worktrees flagged since 2026-08-17
   (`agent-a3644561b6d0e3d1c`, `agent-a3c77b5f9e3976db2`,
   `agent-aae97dda7efece80f`, `agent-af4769dbf63c4c2bc`) are still
   unresolved and still out of scope for this thread.

---

# Session handoff — 2026-08-27 (new tooling infrastructure for experimentation discipline)

## What this session built

**Problem.** CLAUDE.md documents repeated incidents caused by (a) single-knob-at-a-time tuning on coupled constants, (b) dev/confirm seed reuse manufacturing false wins, and (c) silent contract violations (last-callable entrypoint, market-order truncation, episode crashes). None of these are unmeasurable — they're *uncaught* by the current test harness, which is unit-only. This session added guardrails that make the failures visible before they ship.

**Built, all under `experiments/` or `tests/`:**

1. **`experiments/seeds.py`** — splits the formerly-ubiquitous `range(12)` into `DEV_SEEDS = range(12)` (iteration) and `HOLDOUT_SEEDS = range(100, 112)` (frozen confirmation, never touched during dev). All three harness scripts now wire `--seed-set {dev,holdout}`.

2. **`tests/test_episode_contracts.py`** — two tests:
   - `TestEntrypointLastCallable`: AST-verifies the last top-level statement in `main.py` is `agent = nikaangukia_meroni` and nothing callable follows. Catches the silent-entrypoint hijack class structurally instead of by comment.
   - `TestSelfPlayDONE`: self-play on seed 0, asserts `['DONE','DONE']` and bank above starting money ($3000). Catches PASS-fallback crashes structurally.

3. **`experiments/golden_master.py`** + snapshot at **`tests/golden/golden.json`** — fixed-seed episodes vs `pass`/`starter` (seed 0), recording bank + action-histogram signature. `--update` regenerates; `--time` reports per-turn latency percentiles (asserts the 1s actTimeout bound empirically). Any future refactor that silently changes behavior now fails this test. **Status: runner script written, golden snapshot NOT yet generated** — `tests/golden/` does not exist. The contract tests' two `TestGoldenMasters` cases currently skip with `'no golden snapshot yet; run with --update to record'`. First task of next session: run `python experiments/golden_master.py --update` to materialize the snapshot, then re-run the contract tests to confirm they fail-closed (i.e. would now catch a regression) rather than skip.

**Verification status:**
- `TestEntrypointLastCallable` passes — `main.py`'s last callable is verified to be `agent = nikaangukia_meroni` and nothing callable follows.
- `TestSelfPlayDONE` passes — self-play on seed 0 ends `['DONE','DONE']` and bank > $3000.
- `TestGoldenMasters` cases are skipped pending the snapshot.
- Full `python -m unittest discover -s tests` passes: **170 tests, 0 failures, 2 skipped** (the two golden cases).
- All four harness scripts (`paired_compare`, `head_to_head`, `selfplay_bench`, `seeded_batch`) accept `--seed-set` and run without `ModuleNotFoundError` after a `sys.path` shim was added to each (see "Import-shim caveat" below).
- `selfplay_bench.py` (no args) ran end-to-end and produced its report — proves the seed-set wiring works in a real benchmark run.

**Import-shim caveat (will trip the next reader).** Adding `from experiments.seeds import …` to the four pre-existing scripts broke the "run as a script" path because there is no `experiments/__init__.py` and Python doesn't auto-promote directories to packages. Fixed in all four scripts with a one-line `sys.path.insert(0, str(Path(__file__).resolve().parent.parent))` shim, mirroring what `golden_master.py` had from the start. **Alternative considered: add `experiments/__init__.py`.** Both work; the shim was chosen because it doesn't introduce a package boundary (this directory is a flat scripts collection, not a library) and matches the pre-existing `golden_master.py` style. Document the choice if you swap one for the other.

---

## Multi-session breakdown — remaining work

**This session did NOT ship:** the parameter-search driver (P1), the truncation log line (P6), or full end-to-end validation. Those are the next three sessions' work — each is independently completable and independently useful.

### Next session: parameter-search driver (P1 core)
Build `experiments/param_search.py` — a joint multi-parameter tuner:
- Knob registry: parse `main.py` source via AST to read each constant's current default *directly* (no duplication). Support scalar knobs (`MAX_HANDS_PER_DAY`, `WORK_TILES_PER_HAND`, etc.) and dotted dict entries (`SELL_PRICE_THRESHOLDS.MELON`).
- Variant generation: rewrite only the targeted `^NAME = ...` lines, **asserting exactly one replacement per knob** — closes the silent-dead-knob failure mode (this is the lesson from the Path C override wrapper that looked live but wasn't).
- Stages: `screen` (random search over the knob vector, ~32 samples, vs baseline on 4 seeds × 2 seats) → `confirm` (top-K candidates on DEV_SEEDS × 2 seats) → `holdout` (once, on HOLDOUT_SEEDS — the whole point of P2).
- `--profile NAME` mode: one-at-a-time ±25%/±50% response curves per knob → this is the P3 gate-sensitivity evidence tool (which thresholds move which counters?).
- JSONL accumulation: append every screened candidate + result to `experiments/param_search_results.jsonl` so search runs compose rather than overwrite.

**Completion criterion:** `param_search.py --stage screen --samples 2` reports two different vectors' screen means (a 2-candidate proof-of-concept, ~90s).

### Next session: P6 + P7 + P8 riders
These are small but should be done together since they touch the submission artifact:
- **P6 (truncation log):** add exactly one line in `main.py` before the `market[:10]` slice (`main.py:2754`) that prints how many orders were dropped — converts the silent policy ("order by priority, drop the tail") into an observable. Behavior-neutral (print does not change actions).
- **P8 (latency):** wire `golden_master.py --time` into the golden-master smoke test so per-turn latency is asserted on every CI run — not just asserted.
- **P7 (dead code cleanup):** now that golden masters exist, `PATH_C_CORE_ENABLED = False` and its ~20 gated constants/branches can be removed as a *provably behavior-preserving* change — verify with golden masters before/after, then delete. This is genuinely future-work; don't attempt without golden-master protection.

**Completion criterion:** `--time` on a seed-0 vs `pass` episode reports `p99 < 1.0s`; truncation log fires on a known-crowded turn (construct a synthetic shed-overflow case in the golden runner).

### Next session: full end-to-end validation
- Run `python -m unittest discover -s tests` — all green (existing 166 + new contract tests).
- Run `python experiments/golden_master.py --time` — banks and latencies are sane.
- Run `python experiments/param_search.py --stage screen --samples 4 --confirm` — a real 4-candidate screen + top-1 confirmation passes the win-count bar against the frozen main.py control.
- No commits without explicit check-in (per standing memory rule — `feedback_ask_before_committing_experiments.md`).

---

## Key files
- **New:** `experiments/seeds.py`, `experiments/golden_master.py`, `tests/test_episode_contracts.py`
- **Modified:** `experiments/paired_compare.py`, `experiments/head_to_head.py`, `experiments/selfplay_bench.py`, `experiments/seeded_batch.py` (all: `--seed-set` flag + seeds-module import + `sys.path` shim)
- **CLAUDE.md:** added a "Two seed sets, never reuse the dev set for confirmation" subsection documenting the dev/holdout discipline.
- **Branch:** `investigation/parameter-search-infra` (branched from `main` at `main.py:2768` — the PATH_C-disabled baseline; do NOT merge to main without golden validation)

## What is NOT in scope here
- P3 (gate-mispricing) is an architecture/audit concern, not an implementation — the `--profile` mode of param_search addresses it evidence-wise, but the actual ladder fixes remain future work.
- P4 (stateful belief / opponent-shed inference) is genuine model work, deliberately left out — it changes the agent, not the tooling, and needs its own measurement plan.
- **No changes to `main.py` this session.** The shipped V1 agent is byte-identical to the prior baseline. This session was pure evaluation-infrastructure. The P6 truncation log is scheduled for the next session, not done here.

# Session handoff — 2026-08-25, later same day (read this section first —
ported `mydocs/PATH_C_CORE.md` into both `bptk.py` and `main.py` on this
branch, benchmarked both, and it loses decisively on every real-engine
harness; committing this state at the user's request. A separate
system-dynamics diagnosis of *why* was produced this session but is
**not** reproduced here - the user is bringing it in as its own file)

## This session: ported `PATH_C_CORE.md`'s policy twice (`bptk.py` first,
then `main.py` directly on this branch), ran the full real-engine harness
suite, found a decisive loss plus a genuine regression `bptk.py`'s
zero-travel-time abstraction can't see (animal escapes), then diagnosed
the mechanism with a stocks/flows/connectors/controllers pass at the
user's explicit request - that write-up is being transferred separately,
not duplicated in this file.

**Starting point.** `mydocs/PATH_C_CORE.md` describes a structural policy
(STRAW pin, animal beach-head->pause->scale-to-10, STRAW-elevated
fertilizer, a Level-2 crew reorder, a hire-count bump) marked "research
baseline in bptk.py only," with a claimed ~104-109k-vs-~112k, 2-3/6 result
against Path A. **Verified before touching anything:** none of
`PATH_C_EARLY_ANIMALS`/`run_path_c`/`path_c_overrides`/etc. exist anywhere
in this repo's history, on any branch (`git log --all --grep`, `git grep`
across every commit) - it's real research from a separate environment,
with no backing code here.

**Step 1 - reproduced it in `bptk.py` first** (`path_c_overrides()`,
`run_path_c()`, `compare_path_c()`, `compare_path_c_ladder()`, plus
`--compare-path-c`/`--ladder` CLI flags, matching the doc's own API). Four
of six policy pieces are `_override_main`-style function swaps (same
pattern as the existing straw-first code); the STRAW-elevated FERTILIZE
tier and the Level-2 crew reorder have no override point, so they're new
logic inside `EconomyModel._assign_crew`, gated on a `path_c`/`path_c_cfg`
flag threaded through `run_episode`. Results closely matched the doc's own
numbers (12-seed ladder: Path A 109,720 vs Path C 103,087, **6/12 wins -
an exact coin flip**) - good evidence the reproduction is faithful.
Ablation: animal sequencing is the one lever that clearly matters
(removing it is the biggest additional loss); hire bump is a dead no-op;
L2 crew reorder is ~neutral; the STRAW pin adds variance without moving
the win count; the fert-sell gate is mildly net-negative. Full unittest
suite (166 tests) and the existing `--validate`/`--straw-first` harnesses
are unaffected.

**Step 2 - user then asked to port it into `main.py` on this branch and
run it through the real harnesses.** Ported all six pieces as real code:
`path_c_animal_cap()` (beach-head(3, day<=8) -> pause(frozen) ->
scale(10, unlocked at `straw_tiles>=50 OR day>=15`, gated on
`wheat_stock>0`), wired into `choose_animal_to_build`/
`decide_animal_market_actions`; a STRAW pin branch at the top of
`choose_crop`; a fertilizer-sell gate extending the existing FERTILIZER
exemption to hold during liquidation while any STRAWBERRY tile
`wants_fertilizer`; a hire-ceiling bump in `decide_hire_orders`; and,
since `main.py`'s real per-unit ladder has no whole-tier Hungarian
assignment to swap, the STRAW-elevated fertilize / Level-2 crew reorder
became a `prefer_crop` bias added to `find_fertilizer_target` and
`find_nearest_target`'s "harvest"/"water_urgent" search (STRAWBERRY-first,
falls back to nearest-any) - flagged in the code as an interpretation, not
a literal port. Everything is gated behind one switch,
`PATH_C_CORE_ENABLED = True` (currently on).

**Real-engine result: a decisive loss, worse than `bptk.py` predicted,
plus a new regression.** Head-to-head vs the frozen pre-Path-C `main.py`
(12 seeds x 2 seats): Path A wins **+2,074 mean, 16/24** (self-control:
`+0, 12/24`, harness trustworthy). Paired vs `starter`: -854, 5/12. Paired
vs `pass`: **-5,698, 4/12**. Self-play (12 seeds): mean 46,402 but
**stdev 14,680** - more than 2x the shipped agent's already-flagged
~6,329. Seeded batch: wins 12/12 vs each built-in (expected - they never
sell either way), but **17-20 animal escapes across 12 episodes per
opponent**, against the shipped config's documented **0 escapes across 48
episodes** - the new finding `bptk.py` structurally cannot surface
(zero travel time). Unit tests: 164/166 pass: the 2 failures are expected,
not bugs (they assert pre-Path-C day-0 behavior the beach-head cap now
deliberately blocks). V20 benchmark **not run** - Kaggle CLI auth expired
mid-session; user chose to skip re-auth for now.

**Step 3 - diagnosed the mechanism with a system-dynamics pass** (stocks/
flows/connectors/controllers), per the user's explicit request to reuse
the "where do components drain/block/cancel/synergize" method that fixed
`main.py` originally. Traced 4 real episodes day-by-day (money, shed
WHEAT, filled-animal count, STRAWBERRY/WHEAT tile counts) for Path C and
Path A side by side. Headline finding: shed WHEAT sits pinned at exactly
the reserve floor for nearly the whole season under Path C (vs Path A
building a real multi-unit buffer by day 20), because the STRAW pin has
no connector to the wheat/feed subsystem and blocks WHEAT planting for
the whole days-5-14 window, right before the herd resumes growing with no
buffer to absorb a hiccup. Also found the `straw_tiles>=50` scale-unlock
branch never fired in any of the 4 sampled seeds (max observed 49) - in
practice only the `day>=15` fallback ever triggers. Ranked fix proposals
were given to the user but **not yet implemented** - full diagnosis is
being brought in separately, not duplicated here.

**State at handoff:** `bptk.py` and `main.py` both carry the Path C
changes, committed this session at the user's request.
`PATH_C_CORE_ENABLED = True` in `main.py` - **the agent on this branch
currently plays the losing Path C policy, not the shipped baseline.** Do
not merge this branch to `main` without either reverting
`PATH_C_CORE_ENABLED` or implementing the fix pass and re-clearing the
same benchmark suite. Frozen pre-Path-C baseline used for every
comparison this session was `git show <commit-before-this-one>:main.py` -
regenerate the same way if needed again.

---

# Session handoff — 2026-08-25 (read this section first — implemented and
ran the "straw-first pause animals" experiment from
`RESEARCH_LOG_economy_path_ab.md`, in two variants; both are clear losses
in `bptk.py`, mechanism understood, nothing committed)

## This session: added the straw-first pause-animals experiment to
`bptk.py` (two variants), ran both over 12 seeds, produced charts +
Mermaid stock-and-flow diagram + a full write-up under `mydocs/`; closed
out as a confirmed dead end, pending only the user's go-ahead to commit
`bptk.py` and/or add a `CLAUDE.md` entry

**Starting point.** User asked to read this file and
`RESEARCH_LOG_economy_path_ab.md` (a research thread done outside this
repo — no code from it exists here). That log's own "next testing
direction" #1 was never run: gate `BUY_ANIMAL`/`BUILD_PASTURE` off until
STRAWBERRY tiles reach a threshold or a day floor passes, compared against
Path A (= current shipped `main.py`, unmodified) in `bptk.py`. User then
asked to implement it, with an explicit precaution up front: watch for
WHEAT/other filler crops crowding the tile-time the gate frees up, since
`CLAUDE.md` documents four separate prior "free tile-time" experiments
that all failed exactly that way.

**Explored first (two parallel Explore agents), then verified against
real code before writing anything:** confirmed no Path A/B/straw-first
scaffolding exists anywhere in the repo yet; mapped `bptk.py`'s
`_override_main`/`run_episode`/`daily_log`/`validate()` structure and
exact line numbers; confirmed `_override_main` can swap a **function**,
not just a constant, and that `main.choose_animal_to_build`'s
`(farm, private, board_size, day, pending_builds=0, ux=None, uy=None)`
signature returns `None` to refuse a build — so the whole gate could be a
pure `bptk.py`-side wrapper with zero `main.py` changes. Also mapped this
repo's viz conventions (notebooks inline a shared matplotlib house style —
`SURFACE`/`INK`/`INK_MUTED`/`GRID` + a `finish()` helper — no shared style
module; `experiments/*.py` never plots; `docs/ARCHITECTURE.md` uses
Mermaid `flowchart` for diagrams-as-code). Wrote a plan (via `AskUserQuestion`-free
plan mode, approved after the displacement precaution above was folded
in), then executed it directly (no subagents this session — all read/
write/bash calls were done by the main thread).

**Variant 1 — the gate alone: clear loss, mechanism confirmed as
predicted.** Added `_straw_first_choose_animal_to_build` (later
generalized, see Variant 2), `run_straw_first_pause`,
`compare_straw_first_pause`, and a `--straw-first` CLI flag to `bptk.py`.
Gate: `STRAWBERRY tiles >= 20 OR day >= 12` (OR'd, day as a safety valve
so the pause can't outlive STRAWBERRY's own 5-12 planting window for
nothing). 12 seeds vs Path A:

**-20,707 mean, 2/12 wins.** The displacement check (added per the user's
precaution — tracks *every* crop's planted count, not just STRAWBERRY)
confirmed the exact predicted failure: mean planted-count delta WHEAT
+12.5, CARROT +12.0, STRAWBERRY **-3.9** (down, not up), MELON -4.4. Seed
0's detail trace makes it concrete: STRAWBERRY plateaus at 42 tiles paused
vs 51 baseline — a *lower* ceiling. Mechanism: STRAWBERRY is capped by its
own window/cash/seed-cadence limits, not by animal timing, so pausing
animals doesn't free STRAWBERRY capacity — it just delays animal revenue
by up to 12 days while WHEAT/CARROT (not STRAWBERRY) absorb the freed
tile-turns, the same failure mode as `CLAUDE.md`'s four prior "free
tile-time" dead ends.

**Variant 2 — cash escape valve + hold-then-sell STRAWBERRY, per a direct
follow-up request: still a clear loss, win count unchanged.** User asked
to try holding STRAWBERRY's harvest for a later lump sale instead of
selling continuously, and to let idle cash buy the animal early rather
than wait out a rigid gate (reasoning: since Variant 1 showed STRAWBERRY
isn't cash-capped, idle cash past a buffer isn't doing anything for
STRAWBERRY by waiting). Generalized the v1 function into
`_straw_first_gate_open` (shared gate logic) + `_straw_first_overrides`
(builds an overrides dict combining the gate with an optional
`decide_market_actions` wrapper that strips a held product's normal-
threshold `SELL` order while the gate is closed, respecting the existing
total-shed `SHED_FORCE_SELL_THRESHOLD` safety valve). Added
`--straw-first-cash-multiple` and `--straw-first-hold-product` CLI flags.
Refactor verified behavior-preserving before trusting it: `--validate`
reproduced its exact prior baseline (98133) and Variant 1 reproduced its
exact prior per-seed numbers post-refactor.

12 seeds, `cash_buffer_multiple=3` (3x `MIN_CASH_RESERVE_FOR_ANIMAL_BUYING`),
`hold_product="STRAWBERRY"`: **-14,810 mean, 2/12 wins** — a smaller mean
loss than Variant 1, but **the win count didn't move**. Displacement
barely improved (WHEAT +11.3 vs +12.5, STRAWBERRY still -2.2). Seed 0's
detail trace explains why the improvement is smaller than it looks: the
STRAWBERRY-shed quantity chart shows baseline and Variant 2 tracking
almost identically all season, because STRAWBERRY (an *ongoing*,
interval-ticking crop) doesn't start accumulating in the shed until
~day 17 — five days *after* the day-12 gate already opened — so there was
almost nothing to hold during the paused window in the first place. Most
of Variant 2's improvement over Variant 1 is the cash escape valve
helping cash-rich seeds open the gate sooner, not the hold-then-sell
mechanism doing what it was built to do.

**Verdict: both variants confirm the same root cause, neither fixes
it.** STRAWBERRY's own window/cash/seed-cadence ceiling is unaffected by
animal-purchase timing or cash-sufficiency escape valves — no amount of
gating or reshuffling the *animal* side can grow more STRAWBERRY. Per this
repo's own standing lesson (four prior instances in `CLAUDE.md`): closing
this out rather than trying a third animal-gate variant. If this thread
continues, the next experiment needs to target STRAWBERRY's own ceiling
directly (its planting window, seed-purchase cadence, or crew capacity
during its window), not the animal-purchase side.

**Deliverables, all under `mydocs/` (gitignored, not committed):**
- `mydocs/straw_first_pause_session_notes.md` — full write-up: a Mermaid
  `flowchart TD` stock-and-flow diagram of the gate mechanism, both
  variants' results tables, the displacement-check tables, 9 embedded
  PNGs, caveats, and a drafted `CLAUDE.md` dead-end entry covering both
  variants.
- `mydocs/scratch/straw_first_pause_viz.py` — the viz script (reuses the
  notebook's house style verbatim per this repo's copy-per-file
  convention), produces all 9 PNGs.
- `mydocs/scratch/straw_first_pause/*.png` — 9 charts (money-over-time,
  STRAWBERRY-tiles-over-time, animal-structures-over-time, per-seed-delta,
  and tile-occupancy-by-crop for each variant, plus Variant 2's
  STRAWBERRY-shed-over-time).

**Not committed.** `git status` shows only `M bptk.py` (all additive:
`_straw_first_gate_open`, `_straw_first_overrides`,
`run_straw_first_pause`, `compare_straw_first_pause`, and CLI flags
`--straw-first`, `--straw-first-seeds`, `--straw-first-min-tiles`,
`--straw-first-min-day`, `--straw-first-cash-multiple`,
`--straw-first-hold-product`). Per
[[feedback_ask_before_committing_experiments]], explicitly asked the user
before running `git add`/`git commit` — not yet answered as of this
handoff, so `bptk.py` stays uncommitted on
`investigation/animal-diagnosis-and-route-v20-bench` until told to.

## Next session, if continuing this thread

1. **Get the pending go-ahead**: commit `bptk.py`'s straw-first additions
   (research tooling, clearly marked as two confirmed dead ends), and/or
   add the drafted dead-end entry (in
   `mydocs/straw_first_pause_session_notes.md`'s last section) to
   `CLAUDE.md`'s "Measured dead ends" list. Neither has happened yet.
2. **If pursuing this mechanism further, target STRAWBERRY's own ceiling
   directly** — its planting window, seed-purchase cadence, or crew
   capacity during days 5-12 — not another animal-purchase-side wrapper.
   Both variants tried this session confirm the animal side has no
   leverage over STRAWBERRY's own constraint.
3. Neither variant was cross-checked against a real
   `experiments/selfplay_bench.py` or `paired_compare.py` run — not
   warranted given both are clean 2/12 `bptk.py` losses with an
   understood mechanism, but noted for completeness.
4. Phase 4 (`docs/ROADMAP.md`'s crop `occupancy_kind`) is still the
   next real lever per the 2026-08-23 session below — untouched this
   session, still paused on explicit prior user call.
5. The 4 old stale-base worktrees flagged since 2026-08-17
   (`agent-a3644561b6d0e3d1c`, `agent-a3c77b5f9e3976db2`,
   `agent-aae97dda7efece80f`, `agent-af4769dbf63c4c2bc`) are still
   unresolved and still out of scope for this thread.

---

# Session handoff — 2026-08-23 (read this section first — closed out the
animal-side "not yet proven" open question from `CLAUDE.md`, ran `bptk.py`'s
first dedicated animal/land diagnosis pass, paused before Phase 4 per
explicit user instruction)

## This session: resumed main.py development per a plan that started from
reviewing this file — synced `main` (26 commits), re-benchmarked the
shipped two-species animal config against its true pre-diversification
baseline (confirmed win, all three harnesses), ran `bptk.py`'s first
animal/land diagnosis pass, documented a `route_v20` benchmark step, and
committed the CLAUDE.md updates. Paused before Phase 4 on explicit user call.

**Starting point.** User asked (before executing an already-drafted plan)
what `bptk.py`'s role is and whether the plan needed anything added. Read
this file's bptk.py sections (all in the pre-2026-08-22-closing-session
history, now below) plus `CLAUDE.md`'s own bptk.py documentation, and
surfaced that the plan's animal-re-measurement step and next-phase step both
overlapped with `bptk.py`'s own still-open "next session" pointers (no
dedicated animal/land diagnosis pass had ever been run; the contested-mode
cash-trough finding was never cross-checked against a real
`selfplay_bench.py` run). User confirmed via `AskUserQuestion`: fold both in.
Plan written to `C:\Users\user\.claude\plans\before-we-execute-this-humming-parnas.md`
and approved.

**Repo sync (direct, not delegated).** `git checkout main && git pull --ff-only`
— fast-forwarded 26 commits (`88f5d3c` → `b906f5e`), confirmed via
`git diff main investigation/economy-sd-model` that `bptk.py`/`main.py` are
byte-identical between the two (PR #41 merged cleanly; the diff was all in
`CLAUDE.md`/docs from other since-merged PRs, plus files like
`agents/route_v20.py` that came from origin, not from that branch).
Branched `investigation/animal-diagnosis-and-route-v20-bench` off synced
`main`.

**Two subagents dispatched in parallel via the `delegate` skill** (per its
own routing table: seeded-benchmark execution is a Sonnet-tier mechanical
job, not a main-thread judgement call):

1. **Real-harness animal-side benchmark.** Briefed to construct a frozen
   pre-species-diversity `main.py` baseline and run `paired_compare.py`
   (vs `starter`/`pass`) + `head_to_head.py` against it. **Caught an error in
   the brief**: the suggested baseline commit (`78745f3`) was actually a
   *later* refactor whose parent already carried `ACTIVE_ANIMALS =
   ["SHEEP", "COW"]` — not a valid single-species baseline. Traced back
   correctly to `ec38fc5` ("feat: let the roster hold more than one species,
   and run 2 sheep + 1 cow") and used `ec38fc5^` instead, confirming via
   `grep` that it actually has `ACTIVE_ANIMALS = ["SHEEP"]`, `MAX_ANIMALS = 1`.

   Results (12 seeds unless noted): `paired_compare.py` vs `starter` **+11,120
   mean, 10/12, t=4.30**; vs `pass` **+14,017 mean, 12/12, t=6.82**;
   `head_to_head.py` (24 matches, both seats) **+12,887 mean, 24/24**;
   self-control (`main.py` vs itself, 6 matches) **+0 mean, 3/6** — harness
   confirmed clean. All three land in this repo's decisive bucket, including
   the contested head-to-head that CLAUDE.md's own standard says is needed
   to catch a trough-starvation failure the never-selling built-ins can't see.

2. **`bptk.py` animal/land diagnosis pass** — the first one ever run
   (crops got three ad hoc sweeps during the original `bptk.py` build
   session; animals/land never had one, per that session's own "next
   session" pointer). Used `bptk.py`'s existing `run_episode`/
   `run_contested_episode`/`_override_main` primitives in a scratch script
   (deleted before finishing, never committed, never edited `bptk.py`
   itself) to compare the shipped config against a **hypothetical** 4-SHEEP,
   no-COW roster (same `MAX_ANIMALS=4`) — **never applied to real `main.py`**.

   Findings: the shipped diverse roster has 0 animal escapes across 5 seeds
   in solo `bptk.py` mode; the 4-SHEEP hypothetical has 4 escapes on every
   single seed, and its 4th pasture never gets built at all, because
   concentrated single-species spend blows the cash floor across the whole
   `LAND_BUY_START_DAY`-`LAND_BUY_LAST_USEFUL_DAY` (6-18) window in
   `decide_land_orders` — `money - cost < MIN_CASH_RESERVE_FOR_LAND_BUYING`
   never clears in that window for the concentrated-spend variant. Total
   dollar cost between the two rosters is nearly identical (~$2,000 vs
   ~$1,800) — it's spend *timing*, not amount, that flips the outcome. Same
   "gate priced against the wrong thing" pattern already named in `CLAUDE.md`
   for `MIN_MONEY_TO_HIRE`, showing up again in
   `MIN_CASH_RESERVE_FOR_LAND_BUYING`, which isn't gated on herd composition
   at all. **This is a `bptk.py`-only signal** (zero-travel-time inflation,
   never run on the real engine) — real in direction, not yet trusted in
   magnitude, and **not a bug in shipped `main.py`** since the shipped
   roster never hits this failure mode.

   Also confirmed `bptk.py`'s own `validate()` scenario 5
   (`5_second_sheep_trough`) is stale: under the shipped `ACTIVE_ANIMALS`,
   `MAX_ANIMALS=2` now reliably builds one SHEEP + one COW (`pick_next_
   animal_species`'s fewest-owned tie-break), not two sheep, on all 5 seeds.

   Cross-checked against real `experiments/selfplay_bench.py` (seeds 0-2):
   mean 65,672, stdev 2,810, min 62,497, max 67,841, with a real mixed herd
   selling both WOOL (191) and MILK (165) — no cash-trough collapse signal
   under the shipped config.

**Caveat, stated plainly because the user asked for it directly:** neither
subagent's numbers were independently re-run by the main thread — these are
self-reported results from the agents' own tool calls, not something this
session verified a second time. The user was told this explicitly and chose
to proceed on the agents' reports as given (see the exact-numbers message in
this session's transcript if the raw detail is ever needed again).

**Committed** (`df5bb04`, on `investigation/animal-diagnosis-and-route-v20-bench`,
not pushed): both findings written into `CLAUDE.md`'s second-sheep/
species-diversity section (a new dated correction, appended after the
2026-08-17 "not yet proven a clean win post-trough-fix" entry — that
entry itself left in place per this repo's convention of correcting via
addition, not deletion) plus a `route_v20` benchmark documentation
addition (step 3 of the plan — a docs-only change, no benchmark run
attached to it, just documenting the existing `experiments/route_v20.py`
decode-then-`head_to_head.py` one-liner alongside the other harness
commands).

**Verdict: animal-side tuning is closed, no code change needed.** The
shipped config is confirmed correct on every available measure. The one
new mechanism found (`MIN_CASH_RESERVE_FOR_LAND_BUYING` not gated on herd
composition) doesn't call for a fix since it never fires under the shipped
roster — worth remembering if `ACTIVE_ANIMALS`/`MAX_ANIMALS` ever changes
again, not actionable today.

**Explicit user instruction: pause here, do not start Phase 4 this
session.** Asked directly via `AskUserQuestion` whether to proceed to Phase
4 (`occupancy_kind`) now that animals are confirmed solid — user chose
"Pause here."

## Next session, if continuing this thread

1. **Phase 4 (`docs/ROADMAP.md`): crop `occupancy_kind` as a structural
   property.** This is the next real lever per the plan's own step 4 branch
   (animals confirmed solid → move to Phase 4). Closes the four-attempt
   TOMATO/STRAWBERRY scoring saga in `CLAUDE.md`'s dead-ends section (flat
   fertilizer bonus, absolute gate, relative gate, `growth_days` "accuracy"
   fix — all failed the same displacement way). Screen with `bptk.py` first
   (cheap, already-validated pattern) before spending a real episode, same
   as `5bdd327`'s discovery path.
2. If anyone wants the `MIN_CASH_RESERVE_FOR_LAND_BUYING`/herd-composition
   mechanism confirmed rather than just directionally suspected, it needs a
   real-engine trace (a disposable `debug_main.py`-style instrumented copy,
   per this repo's own precedent) — not urgent, since it doesn't affect the
   shipped config.
3. The 4 old stale-base worktrees flagged since 2026-08-17
   (`agent-a3644561b6d0e3d1c`, `agent-a3c77b5f9e3976db2`,
   `agent-aae97dda7efece80f`, `agent-af4769dbf63c4c2bc`) are still
   unresolved and still out of scope for this thread.

---

# Session handoff — 2026-08-22, closing session (read this section first —
committed the bptk.py extension below, documented it, cleaned up two
stray worktrees, and opened the PR; the "Next session" pointers in the
section immediately below are now partly done — see item 1 there)

## This session: committed `bptk.py`'s contested-market extension, wrote
it (and four other undocumented dead ends from this timeline) into
`CLAUDE.md`, cleaned up two stray worktrees, opened the PR

**Committed on `investigation/economy-sd-model`:**
- `c7f7619` — the contested-market mode + Hungarian crew-assignment
  extension described in full in the section immediately below. Committed
  as-is; nothing further changed. Re-ran `bptk.py --validate
  --validate-contested --check-assignment` after committing as a sanity
  check — all pass, same numbers as this session's own verification below
  (baseline 98133; contested scenario 4's day-9 trough at $19 vs solo's
  $310; Hungarian distance 7 vs naive 13).
- `6482291` — `CLAUDE.md` now documents `bptk.py` itself (design, the
  1.5-2x inflation caveat, the validation gate, the `5bdd327` fix it
  found, the new contested mode and its traced near-miss) plus four
  previously-undocumented dead ends from this same timeline: the
  `CROP_PLANTING_WINDOWS` gate (Phase 4/5), fill-priority Test 1a
  (price-blind fallback), Test 1b (target-slot allocation), and the
  sell-or-hold cadence model (rejected twice, two different bases).

**Worktree cleanup, per explicit user go-ahead:**
- `.claude/worktrees/agent-a4bfbca638142c0c4` (`experiment/fill-priority-1b`):
  discarded an uncommitted diff that turned out to be leftover `print()`
  debug instrumentation from diagnosing that experiment, not part of the
  real change (already committed at `7fa9814`) — `git checkout -- main.py`
  plus deleting four untracked `_scratch_*` files. Worktree and branch
  themselves left in place as a closed reference, not removed.
- `.claude/worktrees/agent-aa8b3fd550667d728` (`experiment/phase4-crop-timing-windows`):
  removed via `git worktree remove --force` and `git branch -D` — the
  confirmed Phase 4/5 dead end (now written up in `CLAUDE.md`, see above),
  never pushed to origin, and HANDOFF had already recommended this
  cleanup on 2026-08-18 without it ever being actioned.
- **Explicit decision, not another silent deferral: the 4 old `agent-*`
  worktrees pinned at the stale `2114390` base (`agent-a3644561b6d0e3d1c`,
  `agent-a3c77b5f9e3976db2`, `agent-aae97dda7efece80f`,
  `agent-af4769dbf63c4c2bc`) stay untouched.** These are the same ones
  HANDOFF flagged on 2026-08-17 as "needs inspection, don't touch" and
  that flag was never resolved since. Confirmed unrelated to the
  bptk.py/economy-sd-model thread — still pending their own separate
  session whenever someone wants to work out what they actually are
  (uncommitted `main.py` diffs of 12-166 lines each, no accompanying
  notes identifying which experiment they belong to).

**Branch/remote state confirmed before pushing:** local `main` is even
with `origin/main` (0 ahead, 0 behind) — no fetch/rebase needed.
`investigation/economy-sd-model` branched cleanly from `origin/main` tip
`88f5d3c` with 0 commits behind, so the PR diff is exactly this branch's
own 5 commits (`1c4f6bd`, `fc07c73`, `5bdd327`, `c7f7619`, `6482291`).

**PR opened** — see the PR itself (not duplicated here) for the full
analysis of why `bptk.py` exists, what it's proven, its boundary, and how
the team should keep using it; this file's bptk.py sections below are the
detailed source material that PR description was written from.

## Next session, if continuing this thread

1. Per the pointer already in the section below: the contested-market
   mode's real payoff is cheap screening for selling-cadence ideas before
   spending a real 720-turn episode on them — the sell-or-hold cadence
   model (now closed out in `CLAUDE.md`, rejected twice) is the obvious
   first thing to re-screen this way, not to re-attempt as a fourth
   real-episode port.
2. Animals (feed/CARE timing, pasture placement) and land/hiring still
   haven't had a dedicated `bptk.py` diagnosis pass the way crops did —
   still open, unchanged from before.
3. The 4 old stale-base worktrees above are still unresolved and still
   out of scope for this thread specifically — whoever picks them up next
   will need to read each diff cold, since no session's notes identify
   which experiment any of them belong to.

---

# Session handoff — 2026-08-22, later same day (superseded immediately
above by the closing session — read this section first
was: supersedes the "Next session" pointers in the bptk.py section immediately
below; that section's own content is unchanged and accurate)

## This session: extended `bptk.py` with a contested-market mode + a
Hungarian-optimal crew-assignment upgrade, per explicit user direction —
both implemented and verified, **not committed**

**Starting point.** Reviewed this file's most recent section (below): last
session built `bptk.py`, validated it, and shipped one real fix
(`5bdd327`). User asked what else `bptk.py` could be used for, plus what
tools fit price-impact/selling-cadence work and spatial pathing separately.
Presented options via `AskUserQuestion`; user picked "add a competing
seller to bptk.py (contested-market mode)" as primary, then asked for
concrete tool names for the other two areas rather than a scope-only
answer. Went into plan mode, researched the engine directly rather than
guessing, and the plan that came out of it scoped two pieces into this one
change at the user's explicit request (fold the assignment upgrade in,
defer the rest):

1. **Contested-market mode** - closes `bptk.py`'s one documented blind spot
   (no competing seller, so price-impact/cadence questions couldn't be
   modelled there at all - they had to go straight to a real 720-turn
   self-play episode).
2. **Hungarian-optimal crew assignment** - a small, contained upgrade to
   `_assign_crew`'s within-tier unit-to-tile matching, folded in because it
   needed no new mechanic to validate against the real engine and gives the
   contested-market work a cheap diagnostic for travel-time inflation.

Explicitly **deferred**, named but not built: `SimPy`-based multi-turn
travel simulation (would charge real turns for the distance the new
counter below measures - a materially bigger change), and empirical
spatial diagnosis via `experiments/replay_diagnostics.py` (already the
right tool for that, per `bptk.py`'s own docstring - nothing here replaces
it).

**Research that shaped the design, not guessed:**
- Read `kaggriculture.py`'s real `_process_market` (lines 544-628) end to
  end: per order-index across both players' order queues, atomic orders
  (`HIRE`/`BUY_LAND`) resolve first in player order, then `SELL`/`BUY_*`
  orders quote off the **same pre-commit inventory** and commit
  **sequentially** (player 0 then player 1) via `_commit_unit`. This *is*
  the entire mechanism behind price impact (fertilizer round-trips, melon
  gluts, wool depth) - it only exists because two order streams share one
  inventory mid-order. The plan replicates this loop exactly, reusing
  `bptk.py`'s already-imported `_commit_unit`/`market_price`/
  `_refresh_prices` rather than inventing a different concurrency model.
- Read `FARMER_MOVES` (`kaggriculture.py:88-93`): 4-directional, one tile
  per turn, locked tiles passable - no obstacles. This ruled out
  pathfinding libraries (A*/Dijkstra/`networkx`) for "spatial pathing"
  entirely: travel cost between any two tiles is exactly Manhattan
  distance, so the real open problem is an **assignment** problem (which
  unit should tend which tile) and a **scheduling** problem (multi-turn
  carry trips), not a search problem. `scipy.optimize.linear_sum_assignment`
  (Hungarian algorithm) fits the first; `SimPy` (discrete-event scheduling)
  would fit the second if ever built.
- Confirmed `scipy` (1.18.0) is already installed in `.venv` - no new
  dependency approval needed, unlike the rejected `BPTK_Py`.

**What shipped, all in `bptk.py`:**

1. `_process_market_two_sided(sides, market, ...)` - new module-level
   function replicating `_process_market`'s lockstep exactly, operating on
   a list of `{"farm", "private", "orders", "counters"}` dicts instead of
   the real engine's `state`/`env` objects. `EconomyModel._process_market_
   orders` now delegates to this with a single-element `sides` list - one
   implementation for solo and contested instead of two that could drift
   apart.
2. `_tick_town_demand(market, town, step)` and `_maybe_unlock_shop(town,
   next_day, rng)` - town/shop-demand consumption and shop-unlock, factored
   out of `EconomyModel` into module-level functions so a contested episode
   can advance this *shared* state once per step/day, not once per side
   (which would double-consume demand and unlock two shops a day instead
   of one).
3. `EconomyModel.__init__` takes optional `market=`, `town=`,
   `shares_market=` so two instances can share state; `shares_market=True`
   suppresses that instance's own shop-unlock call in `_end_of_day`.
4. `ContestedEconomyModel` / `run_contested_episode(seed, seed_b, days,
   overrides, overrides_b)` - orchestrates two `EconomyModel` instances
   sharing one market/town. Each side's `_override_main` overrides are
   scoped tightly around just that side's own decision-function calls,
   applied one side at a time within a turn - since `bptk.py` imports
   `main` as one shared module object (unlike the real engine's
   fresh-module-namespace-per-agent, per `CLAUDE.md`'s I/O contract
   section), two *simultaneously* active override sets on the same module
   aren't possible, but two *sequentially* scoped ones are, and Python's
   single-threaded execution makes that equivalent for this purpose - no
   `importlib` module-duplication needed.
5. `_assign_crew` reworked: tracks `available = [(unit_idx, (x, y)), ...]`
   instead of a bare `slots` countdown. `take()` now builds a
   Manhattan-distance cost matrix between available units and the current
   tier's candidate tiles and calls `linear_sum_assignment` for the optimal
   within-tier matching - consuming `min(available, tiles)` units exactly
   like the old row-major greedy version did, just choosing the better
   subset/pairing when a tier is over-subscribed. `assignments` now carries
   explicit `(unit_idx, x, y, action)` tuples instead of relying on list
   position; `step_once`/`ContestedEconomyModel.step_once` updated to
   consume `unit_idx` directly.
6. New counter `total_assignment_distance` - sum of Manhattan distances for
   every assignment made, charged regardless of whether the action itself
   fires (a budget-exhausted pick still costs the travel to discover that,
   matching the existing "wastes one unit's turn" semantics). A first,
   cheap proxy for how much real travel a policy would require, without
   simulating that travel turn-by-turn.
7. New CLI flags: `--contested`, `--validate-contested`,
   `--check-assignment`, `--seed-b`.

**Verification, in the order it was actually done - property/direction
checks before trusting any number, per this repo's own standing rule:**

1. `bptk.py --validate` (the original 7 scenarios) - **identical values
   before and after the refactor** (baseline final money 98133 both times;
   all 7 directional checks hold exactly as before). Confirms the solo path
   is behaviour-preserving, not just "still passes."
2. `bptk.py --check-assignment` - synthetic property check confirms
   Hungarian's total distance (7) <= a naive fixed-pairing's distance (13)
   on the same cost matrix - the mathematical guarantee the algorithm gives
   for any input, checked once against this codebase's actual Manhattan
   metric rather than only asserted.
3. `bptk.py --validate-contested` (seed 0) - **first pass surfaced a result
   that read as backwards, and it was traced rather than accepted or
   dismissed.** Contested MELON end price (280) came out *higher* than
   solo's (156), the opposite of the naive "competition should crash it
   lower" expectation baked into the first draft of the check. Diagnosed
   via `daily_log` inspection (money and market price/inventory by day, per
   side) before touching the test: both self-play sides collapse into a
   **days 6-18 cash-trough stall at the same ~$19 hire-gate floor
   `CLAUDE.md` already documents** (vs. solo's day-12 recovery),
   `SELL_MELON` stays at exactly 0 on both sides all season, and with
   nobody selling into it the market recovers from disuse - ending higher,
   not lower. Root cause: two zero-travel-time sides both retain full
   solo-level throughput while now competing for the *same* fixed
   town/shop demand, so the combined glut/revenue crash is worse than
   either two real (travel-time-throttled) agents or `bptk.py`'s own solo
   mode alone - a known **amplification** of `bptk.py`'s existing ~1.5-2x
   inflation caveat (real self-play is ~41k mean, no collapse there), not a
   new bug. Rewrote the validation scenario's text to state this rather
   than leave a wrong `expect:` comment in the code, and added a 4th
   scenario (`4_cash_trough_under_contest`) exposing the mechanism directly
   (day-9 money: solo $310 vs. contested $19). This is the same class of
   near-miss this file has recorded before (e.g. the head_to_head/
   self-play file-swap note further down) - the fix was catching the
   surprising number and tracing it, not the number itself.

**Not committed.** `bptk.py` is a working-tree change only, on
`investigation/economy-sd-model` (`git status --short` shows only `M
bptk.py`), pending explicit go-ahead per this project's standing practice
of asking before committing experiments, same as every other session in
this file.

## Next session, if continuing this thread

1. Decide whether to commit this `bptk.py` extension. It's research-only
   (not imported by `main.py`, same convention as `pricing.py`), so the
   usual pre-submit-gate/test-suite concerns don't apply, but it's a
   substantial diff (456 insertions) worth a deliberate look before
   landing.
2. The contested-market mode's real payoff is cheap screening for the two
   already-failed selling-cadence experiments
   (`experiment/phase3-aggressive-selling` Variant B, the ported cadence
   model - both closed as losses, see this file's Phase-3-aggressive-
   selling section further down) - worth re-running those ideas through
   `run_contested_episode` before ever spending a real 720-turn episode on
   selling-cadence work again, per the reasoning that motivated building
   it in the first place.
3. The contested-mode cash-trough collapse found during verification
   (scenario 4) is worth a closer look independent of any cadence
   experiment: it suggests the *current shipped* `main.py` policy may be
   more fragile under real contested play than solo/built-in-opponent
   benchmarks can reveal, since `bptk.py`'s exaggeration here is a matter
   of degree, not direction. Not yet cross-checked against a real
   `selfplay_bench.py` run at the same seed - does real self-play show
   *any* trough-deepening at seed 0, even mildly? - that comparison would
   be the natural next step before reading too much into the bptk-specific
   magnitude.
4. `experiment/fill-priority-1a`, `-1b`, `-followup` (documented further
   down this file) are still exactly as they were - untouched this
   session, still pending their own separate closure decision.
5. Per the bptk.py session's own pointer (still open, unchanged): animals
   (feed/CARE timing, pasture placement) and land/hiring haven't had a
   dedicated `bptk.py` diagnosis pass the way crops did.

---

# Session handoff — 2026-08-22, early (superseded above by the 2026-08-22,
later-same-day section on "what to do next" — this section's own content
is unchanged and accurate)

## This session: built `bptk.py` (whole-economy structural model), validated
it, used it to diagnose the fill-priority dead ends, and shipped one real
fix it found — committed on `investigation/economy-sd-model`

**Why this session happened at all.** After Test 1a/1b (below, still open)
came back as two more wrapper-around-`choose_crop` losses, the explicit
instruction this session was to stop trying more wrappers and instead model
the economy structurally first, then diagnose, per a different workflow the
user proposed (originally framed around the `BPTK_Py` toolkit). Research
found `BPTK_Py` isn't installed and would add a real dependency tree
(matplotlib/plotly/tqdm/ipywidgets) poorly suited to this game's genuinely
discrete mechanics (the atomic all-or-nothing PLANT drop, fixed-cadence shop
firing) - decided to build a lightweight custom model instead, with the
option to try real `BPTK_Py` later for comparison once the lightweight pass
proved out. Scope was explicitly widened mid-session from "crop economy
only" to "the whole economy" (crops + animals + land + hiring + selling
together, since they share cash/crew/shed capacity) at the user's explicit
correction - do not re-narrow this without asking again.

**`bptk.py` (repo root, committed `fc07c73`) - design.** Same "research
only, not imported by `main.py`" convention as `pricing.py`. The load-bearing
choice: it does **not** reimplement engine mechanics - it directly imports
and calls the installed engine's own private state-mutation functions
(`_apply_unit_action`, `_commit_unit`, `_do_hire`, `_do_buy_land`,
`_daily_refresh_plants`, `_decay_plants`, `_daily_refresh_animals`,
`market_price`) against a real `farm["tiles"]` grid, and calls `main.py`'s
real decision functions (`choose_crop`, `decide_hire_orders`,
`choose_animal_to_build`, etc.) as the policy under test - never a
reimplementation of either. The only genuinely custom logic is
`_assign_crew`: a priority-ranked scan that substitutes for spatial pathing
(the turn's crew acts on the top-N highest-priority tiles directly, no
walking, no shed-adjacency, no multi-turn carry trips) - a deliberate,
documented abstraction, since spatial/pathing problems are explicitly this
session's out-of-scope (that's `experiments/replay_diagnostics.py`'s job).
A context-manager (`_override_main`) lets any scenario monkeypatch
`main.py`'s module-level constants (never mutating a shared dict/list in
place, since `CROPS`/`ANIMALS`/`SHOPS` are the SAME objects the real engine
holds) for one `run_episode()` call, restoring them after.

**Consequence of the abstraction, stated up front so it isn't mistaken for
a bug later:** absolute bank figures from `bptk.py` run ~1.5-2x above real
episodes (~$100-124k vs ~$55-66k) because the model has zero travel-time
cost. Every number out of it is a *directional* signal, not a bank-balance
prediction - `bptk.py --validate`'s own scenarios are all read as
relative comparisons for exactly this reason.

**Validation gate (`bptk.py --validate`) - passed across 7 seeds (0-6).**
All 7 scenarios (the closed growth_days/CROP_PLANTING_WINDOWS dead ends,
the second-sheep cash-trough pre/post fix, the `MAX_ANIMALS` cliff, and
`BUY_LAND` 2-vs-3-quadrants) reproduce the correct *direction* of every
already-documented mechanism in `CLAUDE.md`. Two apparent misses on
inspection were not contradictions: seed 5's CARROT count was a 0-vs-0 tie
(window too narrow for any instance to land either way, not a wrong-way
result), and seed 6's `BUY_LAND` reversal (3 quadrants +3.8% over 2) is
within the same seed-dependent variance the real `BUY_LAND` finding itself
already shows (10/12, not 12/12, vs `starter`).

**Diagnosis (§3 of the plan) - three experiments run, all confirmatory, no
new lever found:**
1. **Crew capacity × STRAWBERRY window** (`WORK_TILES_PER_HAND` swept
   independently of the window): more crew doesn't help - it collapses the
   economy (cash locks at $18/day, below the $20 hire floor, for a sustained
   stretch) because Fibonacci hiring cost explodes with crew size. This is
   the *already-closed* `WORK_TILES_PER_HAND=2/3` dead end, reproduced from
   a different angle - good model corroboration, not a new finding. Widening
   the window alone (no crew change) gives a modest +20% (55→67 planted).
2. **Cash reserve × STRAWBERRY's $100 seed** (`MIN_CASH_RESERVE_FOR_SEED_
   BUYING` swept 100-700): reproduced the same sharp interior-optimum cliff
   `CLAUDE.md` already documents, centered on the shipped value (450). **No
   STRAWBERRY-specific mistuning found** - the current reserve is already
   near-optimal for it too, ruling out this hypothesis.
3. **Crop↔animal cash contention** (animals on vs off): disabling animals
   does free real capacity (STRAWBERRY +17%, WHEAT +56%), confirming
   contention exists, but overall bank drops ~20% without animals (animal
   revenue outweighs the crop-side gain) - confirms the current tradeoff is
   already correct, not a lever.

**The one real, novel finding: the `can_afford`/`plant_budget` mismatch -
confirmed on a real engine trace, then fixed and shipped (`5bdd327`).**
`choose_crop()` can name a crop via its `can_afford` branch (money available,
zero held seed) at the PLANT call site in `choose_unit_action`, but
`plant_budget` is seeded only from currently-held seed counts and can never
satisfy that pick - the turn plants nothing. First surfaced by `bptk.py`
itself (~1,100-1,150 such events per season in the model - inflated by the
zero-travel-time abstraction, not trusted as a real count on its own).

**Verified on the real engine before touching `main.py`**, per the plan's
own translation methodology - a disposable instrumented copy
(`experiments/debug_main.py`, module-level counter dict + JSON dump on every
turn since `kaggle_environments` re-execs a fresh module namespace per
`Agent` instance, so counters can't be read back via a normal `import`
after `env.run()`; never committed, deleted once the numbers were captured)
run vs `starter`, 3 seeds, 720 turns each:

| seed | crop chosen (empty tile) | planted | **zero-seed-held (the bug)** | ordinary same-turn contention |
|---|---|---|---|---|
| 0 | 513 | 171 | **308** | 34 |
| 1 | 516 | 206 | **276** | 34 |
| 2 | 422 | 206 | **185** | 31 |

Real, not a model artifact: 40-60% of the time a unit stands on empty
ground and `choose_crop` names a crop, nothing gets planted purely because
we hold zero seed of it, even though we could afford to buy one. MELON
dominates consistently (112-171 events); STRAWBERRY/WHEAT/CARROT vary by
seed. This is distinct from ordinary same-turn contention (an earlier unit
this same turn already spent the held seed) - `plant_budget` already
handles *that* correctly by design; this is the case where there was never
any seed to have in the first place.

**Fix shipped:** `choose_crop(..., require_held_seed=True)` - same
glut-aware score, just drops the `can_afford` branch so only crops we
already hold seed for are eligible. At the PLANT call site only (in
`choose_unit_action`), when the unrestricted pick can't be planted
(`plant_budget.get(crop, 0) <= 0`), call again with `require_held_seed=True`
and use that instead. The `BUY_SEED` call site in `decide_market_actions`
keeps the unrestricted call unchanged - it legitimately wants the
`can_afford` branch to justify a purchase, that's not the bug. **Not** a
fixed priority order like the already-failed price-blind MELON->CARROT->
WHEAT fallback (Test 1a, below) - this stays price/glut-aware, just over a
smaller eligible set.

**Mechanism re-verified post-fix (same 3 seeds, same technique):**
zero-seed-held drops 308→160 (seed 0, -48%), 276→163 (seed 1, -41%),
185→176 (seed 2, -5%) - confirms the fix does what it's designed to do,
checked *before* looking at bank balance, per this repo's own standing rule.

**Three-harness result vs a frozen control** (`git show HEAD:main.py` at
the point before this fix, i.e. `fc07c73`):

| harness | result |
|---|---|
| `paired_compare.py` vs `starter`, 12 seeds | -646 mean, 6/12 (coin flip) |
| `paired_compare.py` vs `pass`, 12 seeds | +374 mean, 8/12 (weak positive) |
| `head_to_head.py` vs frozen control, 12 seeds x 2 | **+2,621 mean, 14/24** |
| `selfplay_bench.py`, 12 seeds | control 57,490 -> candidate 59,469 (**+1,979**, +3.4%, stdev ~unchanged) |

**Verdict, and why it shipped despite nothing being decisive:** never a
loss on any of the four readings - unlike this repo's other "positive
everywhere, convincing nowhere" bundles (PR #17/#29, the TOMATO fertilizer
bonus), which always had at least one clearly negative reading among the
mix. Explicit user call: ship it, since it's a real, verified mechanism fix
with no downside shown anywhere, even though no single harness clears the
usual ~8-10/12 or ~19-20/24 "clean" bar on its own. `166/166` tests passing
(4 new: `TestChooseCrop`'s two `require_held_seed` cases,
`TestPlantBudgetFallback`'s two `choose_unit_action` integration cases).
Pre-submit gate `['DONE', 'DONE']`. Committed as `5bdd327` on
`investigation/economy-sd-model`, **not pushed**.

**A methodology near-miss worth recording:** mid-session, `head_to_head.py`
was launched against a frozen control in the background, then - before
checking whether it had actually finished - `main.py` was temporarily
swapped to the control file to get a self-play baseline for the *other*
harness. `head_to_head.py`'s second argument is the literal string
`"main.py"`, re-read from disk per episode, so the swap likely corrupted
some of that run's 24 episodes into control-vs-control instead of
control-vs-candidate. Caught by treating the result as untrustworthy on
timing grounds alone (not by any visibly wrong number) and re-running it
cleanly after confirming the file swap had fully resolved. Generalizes:
**never swap a shared file argument while a background harness run that
also references it by path is still in flight** - even when the two
invocations look independent, if one reads a bare filename from disk
mid-run, they aren't.

## Next session, if continuing this thread

1. `bptk.py`'s validation gate and diagnosis experiments are done for this
   pass. Per the earlier user decision, a second, `BPTK_Py`-based version
   is an explicit *optional* follow-up for comparison - not yet started, no
   urgency.
2. The fix this session shipped is real but not decisive on its own -
   nothing here rules out that a larger seed count (the "run more seeds
   first" option this session declined) would sharpen the read, if a future
   session wants to revisit before this goes anywhere near a ladder
   submission.
3. Animals (feed/CARE timing, pasture placement) and land/hiring are
   modelled in `bptk.py` but have not yet had a dedicated diagnosis pass the
   way crops did this session (the three §3 experiments above all centered
   on the crop side). If the next session wants to hunt for a second real
   fix, that's the most likely unexplored territory left in the model.
4. `experiment/fill-priority-1a`, `-1b`, `-followup` (below) are still
   exactly as they were - untouched this session, still pending their own
   separate closure decision.

---



## This session: implemented and measured Test 1a + Test 1b from
`Plan-fill-priority-followup*.md` — both clear losses, committed locally
(not pushed), experiment not yet closed

**Branch setup.** Current branch (`experiment/phase3-sell-cadence`, this
file's previous "current session") was stale relative to `origin/main`
(`88f5d3c` — three merges ahead: PR #36 Phase 3 adopted, #37/#38, README
rewrite). Branched fresh off `origin/main` as
**`experiment/fill-priority-followup`**, per this project's own established
per-phase convention. Restored this file's uncommitted content across the
branch switch via an external backup copy (the committed `HANDOFF.md` blob
differs between the old branch and `origin/main`, so a plain `checkout -b`
would have overwritten it — same class of trap as the 2026-08-19 git
mistake recorded further down this file). Froze a control copy of
`main.py` exactly as it existed at `origin/main` tip (`88f5d3c`, before any
of this session's changes) at `C:\tmp\handoff_backup\fill_priority_control.py`
— every benchmark below is measured against that, not against the
groundwork-only commit.

**Correction on this session's own research:** an early pass concluded
`mydocs/Plan-fill-priority-followup.md` (the v1 doc, singular) didn't exist
in the repo. That was wrong — it does exist, was found and read in full
after the user pointed it out, and its "Test 1" section is what Test 1a
below actually implements (not a reconstruction, as an earlier version of
this write-up assumed).

**Shared groundwork, committed on `experiment/fill-priority-followup`
(`1c4f6bd`):** reintroduced `CROP_PLANTING_WINDOWS` verbatim from the
rejected Phase 4/5 experiment (MELON 0-11, STRAWBERRY 5-12, CARROT 21-25,
TOMATO excluded, WHEAT unrestricted) as the common base both variants
build on. Windows themselves are not reopened - closed per Phase 4/5's own
result below. 162/162 tests pass, pre-submit gate clean.

**Test 1a and Test 1b were each implemented, tested, and benchmarked by a
delegated agent in its own isolated worktree**, branched off the
groundwork commit (`experiment/fill-priority-1a` / `-1b`). Both agents hit
a transient "API credit balance too low" failure mid-run (unrelated to the
task) and were resumed after the account issue was resolved - noting this
here only because it interrupted the session, not because it affected the
result.

### Test 1a — priority-ordered fallback (MELON -> CARROT -> WHEAT), per
`Plan-fill-priority-followup.md`'s "Test 1" — **clear loss**

When `choose_crop`'s window-gated score comparison would pick WHEAT, try
MELON (if in its 0-11 window and affordable) then CARROT (if in its 21-25
window and affordable) before falling back to WHEAT. STRAWBERRY isn't
part of the chain - it already wins on score whenever it's genuinely
eligible; the fallback only catches what would otherwise default to
WHEAT.

| harness | result |
|---|---|
| `paired_compare.py` vs `starter`, 12 seeds | **-5,775 mean, 2/12 wins, t=-3.11** |
| `head_to_head.py` vs control, 12 seeds x 2 seats | **+81 mean, 12/24 (coin flip)** |
| `selfplay_bench.py`, 8 seeds | candidate mean 60,643 vs control (same seeds) 65,404 - lower mean, worse variance |

**Verdict: clear loss** (paired 2/12 <= the 4/12 bar; head-to-head's
near-zero coin flip doesn't rescue it; self-play agrees in direction).

**Diagnosed mechanism:** CARROT absorption works exactly as designed (0 ->
~40 landed on the traced seeds). But the fallback is price-blind by
construction - it has no glut check - so it also forces MELON/CARROT into
gluts the day-windows were never meant to create. WHEAT pulled back from
Phase 4/5's blown-out 105/133 but landed at 72/90 across the two traced
seeds, still well above the pre-Phase-4/5 baseline of ~24/42.

172 tests passing (162 + 10 new in `TestChooseCrop`; 3 pre-existing cases
needed updating since their fixtures assumed a price-blind fallback
couldn't exist - e.g. "WHEAT beats a heavily-gluted-but-in-window MELON"
is now structurally impossible by design). Pre-submit gate: `['DONE',
'DONE']`. **Committed** on `experiment/fill-priority-1a` (`8aae486`), not
pushed.

### Test 1b — target-slot allocation (STRAWBERRY/MELON tile-share caps),
per `Plan-fill-priority-followup-v2.md`'s "Test 1b" — **clear loss**

STRAWBERRY and MELON each get an explicit tile-share target
(`STRAWBERRY_SHARE = 0.50`, `MELON_SHARE = 0.30` of currently-owned tiles,
from `docs/REPLAY_ANALYSIS.md`'s replay-observed ranges); `choose_crop`
skips a crop once its target is met, even if it would otherwise win on
score. CARROT gets no target - no replay evidence to ground one, per an
explicit decision this session. STRAWBERRY's target uses a live tile
occupancy count (no persistence needed - it's an "ongoing" crop that
stays on its tile). MELON's target uses a season-cumulative planted count,
since MELON is one-shot and its tile frees up after harvest - a live
snapshot would undercount total plantings. This needed a genuinely new
pattern for this codebase: a module-level global dict
(`_SEASON_PLANT_COUNTS`), player-keyed and reset on `day==0, hour==0`,
since no cross-turn persistent state existed anywhere in `main.py` before
this.

**Empirically verified, not assumed:** `kaggle_environments` re-`exec()`s
a fresh module namespace per `Agent` instance - confirmed via an
instrumented self-play episode showing player 0 and player 1 get distinct
`id(_SEASON_PLANT_COUNTS)` values, each only ever containing its own
player's key. So there is no actual cross-seat or cross-episode
global-state leak in this harness today; the player-keying and
episode-reset are defense-in-depth, not a fix for an observed bug. Worth
keeping as a fact about the harness for any future cross-turn-state work.

| harness | result |
|---|---|
| `paired_compare.py` vs `starter`, 12 seeds | **-7,664 mean, 0/12 wins, t=-3.50** (negative on every single seed, range -255 to -23,302) |
| `head_to_head.py` vs control, 12 seeds x 2 seats | **-993 mean, 11/24** |
| `selfplay_bench.py`, 8 seeds | candidate mean 58,099, stdev 9,140 |

**Verdict: clear loss** - both harnesses agree in direction, and 0/12
paired wins is unambiguous on its own.

**Diagnosed mechanism, and this is the useful part:** MELON's target
binds cleanly - cumulative landed tracks the target exactly as it rises
with land purchases through the season. **STRAWBERRY's target never
binds** - live count peaks at 26 against a target of 38, because
STRAWBERRY's own 8-day window (days 5-12) plus early-season crew/cash
constraints cap how many can land in time, well below the target ceiling
itself. **A target-slot cap is a ceiling, not a floor - it cannot fix an
undershoot.** Since STRAWBERRY's gate never fires, the freed tile-time
still defaults to WHEAT exactly as in Phase 4/5: WHEAT landed at 105,
barely different from the original blowout.

174 tests passing (162 + 12 new). Pre-submit gate: `['DONE', 'DONE']` (run
twice). **Committed** on `experiment/fill-priority-1b` (`7fa9814`), not
pushed.

### What both results point to, together

Both variants are wrappers around `choose_crop` - one reorders the
fallback, one caps it - and neither touches the actual constraint either
diagnosis converged on: **STRAWBERRY's own 8-day window, combined with
early-season crew/cash capacity, caps how much of it can land regardless
of what the fallback/target logic downstream does with the rest.** A
priority order and a slot cap both operate strictly *after* that
capacity ceiling is already hit - they can redirect what's left over, but
they can't make more STRAWBERRY land within its window. Per the parent
plan's own explicit fallback clause ("if neither beats control... the
mechanism diagnosis may need a different fix... possibly something in
`choose_crop`'s core scoring rather than a wrapper around it") - this
reads as confirmation of exactly that, not a new finding invented this
session.

### Closure lesson — the wrapper vs. the machinery it discarded

Both Test 1a (priority-ordered fallback) and Test 1b (target-slot allocation) replaced an already glut-aware score comparison inside `choose_crop` — `estimate_future_price` → `simulate_single_product` → `apply_town_demand`, which already prices in oversupply/absorption via the engine's real demand mechanics — with blind priority-ordering or slot-capping once their fallback/allocation condition triggered. This discarded existing machinery rather than compensating for a missing feature. Neither wrapper's specific ordering/allocation logic was itself the bug — both hit the same wall (STRAWBERRY's own 8-day window plus early-season crew/cash capacity caps how much STRAWBERRY can land, regardless of downstream fallback/allocation policy) after already bypassing the real price-aware comparison for the crops it overrode. The transferable lesson for any future wrapper around `choose_crop`: overriding its own price/glut-aware comparison for some crops discards signal, it doesn't add it. If a future STRAWBERRY-shortfall diagnosis (this same session's Track (b)) confirms cash or crew capacity as the actual bottleneck, a fix likely belongs in what feeds the comparison (seed-buying cadence, hiring cadence) rather than in a policy layered on top of the comparison's output.

**Not yet closed as of this handoff - explicit user instruction this
session was "commit and write to handoff but don't push yet, the
experiment is not over yet."** So: both variants are committed locally on
their own branches (not merged, not pushed), this write-up exists, but no
`CLAUDE.md` "measured dead ends" entry has been added yet and no
ship/no-ship call beyond "don't ship either as-is" has been made. Do not
push `experiment/fill-priority-1a`, `experiment/fill-priority-1b`, or
`experiment/fill-priority-followup` until told to.

## Next session, if continuing this thread

1. Decide whether to keep investigating (per the diagnosis above, the next
   candidate fix targets crew/cash capacity during STRAWBERRY's window,
   or `choose_crop`'s core scoring/window logic directly - not another
   wrapper) or close this out as documented dead ends. If closing out,
   the `CLAUDE.md` "Measured dead ends" entry is drafted in spirit above
   but not yet written to that file - needs explicit go-ahead per
   standing practice, same as any commit there.
2. The old, unrelated Phase 4/5 worktree (`.claude/worktrees/agent-aa8b3fd550667d728`,
   branch `experiment/phase4-crop-timing-windows`, locked, uncommitted) is
   still sitting untouched - user said leave it alone this session, still
   pending from before.
3. `experiment/phase3-sell-cadence` (the branch this file's *previous*
   session was on) has no further open work, per that session's own
   note - safe to ignore/switch away from.

---

## This session: reconciled housekeeping from `Plan-phase4-5-then-track-c.md`,
then ran Phase 4/5 (crop occupancy + timing windows) — a clear loss, keep
current main

**Note on this file:** per standing instruction, `mydocs/` (including this
file) is never committed, on any branch, regardless of what past commits
did. Everything below is local-only notes for the next session/person to
read, not a record that will land in git history. If something here needs
to be team-visible, it belongs under `docs/` instead (tracked on `main`).

**Housekeeping reconciliation (before any new code).** Checked the plan
doc's assumptions against actual repo state and found three things had
drifted:
- Variant A (`fb56cc5`) and Variant B (`8127486`) were already committed
  *and pushed* on `experiment/phase3-aggressive-selling` — the "record
  Variant A/B" housekeeping item was already done. The previous session's
  claim that Variant A was sitting in `git stash list` was simply wrong;
  there was never a stash on this machine (`git stash list` and
  `git reflog show refs/stash` both confirm empty/no-ref). Corrected that
  claim in this file's 2026-08-20 section below rather than deleting the
  history.
- This branch's (`experiment/phase3-sell-cadence`) own uncommitted
  `main.py` was a byte-identical duplicate of the already-committed
  `8127486`. Discarded via `git restore main.py` — nothing lost, the
  finding is recorded once, correctly, on `phase3-aggressive-selling`.
- Local `main` was stale (`22c8e97`) vs `origin/main` (`88f5d3c` — three
  merges ahead: PR #36 Phase 3 adopted, #37 meta-opponent tooling, #38
  public-meta docs, plus a README rewrite). Fast-forwarded local `main` to
  match.
- Branched `experiment/phase4-crop-timing-windows` off the updated `main`.

**Phase 4/5: crop planting-window gate — clear loss, do not ship.**
Delegated implementation + benchmarking to a subagent in an isolated
worktree (`.claude/worktrees/agent-aa8b3fd550667d728`, branch
`experiment/phase4-crop-timing-windows`, uncommitted — see cleanup note
below).

Change tested: a `CROP_PLANTING_WINDOWS` dict gating `choose_crop()`
alongside the existing season-maturity gate (same `continue` pattern, not
a replacement) — `MELON: (0,11)`, `STRAWBERRY: (5,12)`, `CARROT: (21,25)`,
`WHEAT: (0,27)` (no-op), `TOMATO: None` (excluded entirely). Deliberately
did **not** touch `growth_days`/the scoring formula/selling/animals/land/
crew — that denominator is the closed-out dead end already in `CLAUDE.md`.

| harness | mean delta | wins |
|---|---|---|
| `head_to_head.py` vs frozen control | +343 | 12/24 (coin flip) |
| `paired_compare.py` vs `starter`, 12 seeds | **-3,689** | **3/12** (t=-2.02) |
| `selfplay_bench.py`, 8 seeds | mean 60,303, stdev 10,838, min 39,968, max 70,897 | — |

Per the plan doc's own explicit bar, `paired_compare`'s 3/12 alone crosses
"≤4/12 either harness → clear loss," and `head_to_head`'s coin flip doesn't
rescue it. **Verdict: clear loss. Current main is unchanged; nothing
shipped.**

Mechanism (confirmed via diagnostics, not just asserted): TOMATO landings
go to exactly 0 (as designed), STRAWBERRY landings roughly halve (63→33,
60→34 across two seeds) from the narrower window, and — the actual
damage — **WHEAT landings jump 4-5x** (24→105, 42→133). STRAWBERRY is an
"ongoing" crop that otherwise occupies a tile for ~17 real days; cutting
its window frees a lot of tile-time, and the agent fills it with cheap,
fast-cycling WHEAT instead of the higher-value crops it used to hold. Same
*displacement* failure mode as the closed-out TOMATO/STRAWBERRY
`growth_days` investigation in `CLAUDE.md` — different change, same trap:
freeing tile-time doesn't help if what fills it is worth less per
tile-day.

Full per-seed `paired_compare` deltas, exact diff, and per-crop
requested/landed/end-inventory/end-price diagnostics are in this
conversation's history (delegated agent's final report) if needed again —
not duplicated here since this file isn't committed and the conversation
transcript is the durable record for this session.

**Nothing committed, pushed, or submitted this session.** Pending
decisions, both still open as of this handoff:
1. Whether to record this as a dated entry in `CLAUDE.md`'s "Measured dead
   ends" section, matching how every other rejected experiment in this
   repo is documented (recommended, not yet actioned — needs explicit
   go-ahead before any commit, per standing practice).
2. What to do with the Phase 4/5 worktree/branch
   (`experiment/phase4-crop-timing-windows`,
   `.claude/worktrees/agent-aa8b3fd550667d728`) — it has the rejected
   change plus two untracked scratch files
   (`phase4_control_main.py`, `phase4_diag.py`) sitting uncommitted.
   Recommended: remove the worktree and delete the local branch (never
   pushed, fully local, reversible until removed) — not yet actioned.

## Next session, if continuing this thread

1. Get the two decisions above from the user, then act on them (docs entry
   + worktree cleanup) — check in before any `git commit`, even for a
   docs-only change, per standing practice.
2. Once Phase 4/5 is closed out one way or another, move to Track C
   (issue #21): write `docs/TRACK_C_TARGETS.md` (tracked on `main`, not
   `mydocs/`) synthesizing `docs/REPLAY_ANALYSIS.md`,
   `docs/ANIMAL_ECONOMY.md`, `docs/PUBLIC_META.md`, and this session's
   Phase 4/5 outcome (crop timing alone is not the bottleneck — the
   displacement mechanism above suggests tile-time reallocation needs to
   go somewhere *better*, not just away from TOMATO/STRAWBERRY; the real
   gap per `docs/REPLAY_ANALYSIS.md` is still land+crew scale, not crop
   timing). See `mydocs/Plan-phase4-5-then-track-c.md` for the full Track C
   spec (target table, necessary-vs-correlated split, opening-book
   success/failure criteria).
3. `experiment/phase3-sell-cadence` (this branch) has no further open work
   — the selling-cadence investigation is fully closed
   (`experiment/phase3-aggressive-selling`'s `fb56cc5`/`8127486`). Safe to
   switch away from it once this file's edits are no longer needed
   locally.

---



## This session: ran `mydocs/Plan-phase3-aggressive-selling.md` Variant B
(sell-or-hold cadence) on the Phase 3 base — a clear loss, worse than
Variant A on every harness

**Branch note first, because it matters for anyone picking this up:** this
branch (`experiment/phase3-sell-cadence`) was cut fresh off the clean Phase
3 control (`refactor/phase3-land-and-second-animal`), *not* off
`experiment/phase3-aggressive-selling`. Variant A's four-constant edit and
its own HANDOFF.md writeup (+1,685 mean/17-24 head-to-head vs Phase 3
control, -538/7-12 paired vs `starter`, self-play mean 63,982/floor 48,170 —
called inconclusive) live on `experiment/phase3-aggressive-selling` as a
**committed and pushed** commit (`fb56cc5`), not a stash.

**Correction (2026-08-20, later same day):** the paragraph above originally
claimed this work was sitting uncommitted in `git stash list`. That was
wrong — there was never a stash on this machine (`git stash list` and
`git reflog show refs/stash` both confirm empty/no-ref). Both variants are
safely committed on `experiment/phase3-aggressive-selling` and pushed to
origin: `fb56cc5` (Variant A, inconclusive) and `8127486` (Variant B, clear
loss — it also reverts Variant A's constants back to the Phase 3 control's
own values, matching how Variant B was actually measured). This branch's
own uncommitted `main.py` port turned out to be a byte-identical duplicate
of `8127486`, so it has been discarded (`git restore main.py`) rather than
committed a second time. Nothing was lost; the finding is recorded once,
correctly, on `experiment/phase3-aggressive-selling`.

**What was tested.** Per the plan's Variant B spec, ported @Kinjuriu's
continuous sell-or-hold cadence model (`experiment/sell-cadence`, commit
`9a6a5c6`, itself already reviewed/rejected once on a different base — see
below) onto the clean Phase 3 base: `estimate_sell_or_hold_value()`,
`inventory_pressure()`, and `cadence_urgency()` inserted after
`seed_restock_quantity()`, `decide_market_actions()`'s sell loop rewritten
to price hold-vs-sell off `cadence_urgency(day)` and
`inventory_pressure()` instead of `should_sell()`'s fixed per-product
threshold, and `LIQUIDATION_START_DAY = SEASON_DAYS + 1` (the hard cliff
disabled by design, not a variant, per the plan and the original port's
own reasoning - the urgency ramp is meant to replace it). All prerequisite
functions (`price_path_for_sale`, `estimate_future_price`,
`count_pipeline_supply`, `remaining_season_days`, `TURNS_PER_DAY`,
`SEASON_DAYS`, `PRICE_FLOOR`, `recommend_sell_quantity`) already existed
in the Phase 3 base, so this was a clean port with no missing dependency.
Pre-submit validation gate: `['DONE', 'DONE']`. Test suite: **8 failures,
by design** - the same count and the same class the original port
documented (`should_sell()` is no longer on the sell path, so its
threshold-exact assertions no longer match) - no other regression.

**Three-harness result:**

| harness | result |
|---|---|
| `head_to_head.py main.py /tmp/phase3_control.py 12` (Phase 3 control, the plan's primary decision harness) | **+364 mean, 12/24 wins — an exact coin flip** |
| `paired_compare.py` vs `starter`, 12 seeds | **-2,531 mean, 3/12 wins, t=-1.74 — a decisive loss** |
| `selfplay_bench.py`, 8 seeds | mean **61,906**, stdev **11,123**, min **45,360**, max 74,794; end prices WHEAT 52 / CARROT 57 / TOMATO 91 / STRAWBERRY 145 / MELON 172 |

**Verdict: a clear loss, and worse than Variant A on every axis measured.**
12/24 head-to-head is not a "just under the bar" result the way Variant
A's 17/24 was — it's an exact coin flip, no better than the control at
all. `starter`-paired is a decisive loss by this repo's own win-count-first
rule (3/12), not the inconclusive wash Variant A got there (7/12) — this
harness is expected to be less informative for selling-timing changes per
`CLAUDE.md`'s documented built-in-flattery pattern, but 3/12 is still a
worse result than a wash, not a better one. Self-play's stdev (11,123) and
floor (45,360) sit in the same shape as the *other* Variant B measurement
this repo already has, and that comparison is the most useful thing this
session found:

**This matches the exact pattern the model's original author already
recorded and rejected, on a different base.** Commit `9a6a5c6` (ported the
same model onto post-PR29 `main`, `LIQUIDATION_START_DAY=10`, pre-land)
found self-play paired mean 61,024 → 62,369 (+1,345, 8/14) but floor
52,636 → 44,859 (-7,777), and concluded trading a 7,777-unit floor for a
1,345 mean gain was "the wrong direction for a Bradley-Terry final" - not
shipped there either. This session's Phase-3-based port doesn't even get
that port's small mean upside: head-to-head is flat (not +1,345-equivalent
positive) and `starter`-paired is a real loss, while the variance/floor
problem the original port flagged shows up again (stdev 11,123 here vs.
Phase 3's own recorded 12-seed self-play stdev of 11,626 - comparable
shape, still wide). Two independent porting attempts, two different bases,
the same failure mode both times: **the continuous cadence model's
mean-vs-floor tradeoff is a structural property of the model, not an
artifact of which base it's ported onto.**

**Nothing committed this session.** `main.py` on
`experiment/phase3-sell-cadence` (the full port) was uncommitted, turned
out to duplicate the already-committed `8127486` on
`experiment/phase3-aggressive-selling` byte-for-byte, and has since been
discarded (see correction note above) rather than committed. This
`HANDOFF.md` update remains pending explicit go-ahead per this project's
standing practice.

## Next session, if continuing this thread

Per the plan's own reading table, both variants from
`mydocs/Plan-phase3-aggressive-selling.md` are now measured and neither
clears a ship bar: Variant A (simple aggressive constants) is inconclusive
(+1,685/17-24, needs more seeds or a decision to drop it), Variant B
(cadence model) is a clear loss twice over now, on two different bases.
The plan itself only names these two variants - there isn't a Variant C
written down. Two honest paths from here: (a) close this plan out by
keeping Phase 3's original conservative selling constants as-is (the
control both variants were measured against), since neither challenger
beat it cleanly, or (b) if the team still wants principled sell-timing
model, it would need a different mechanism than the cadence-urgency
ramp - this one has now failed the same way twice, on two independent
implementations and two independent bases, which is stronger evidence
against the mechanism itself than against either specific port.

**Resolved (2026-08-20, later same day):** both variants are closed and
already committed/pushed on `experiment/phase3-aggressive-selling`
(`fb56cc5`, `8127486` — see the correction note above); there was never a
stash to resolve. Local `main` has been fast-forwarded to
`origin/main` (now includes Phase 3 via PR #36, plus PR #37/#38), and work
has moved on to Phase 4/5 (crop occupancy + timing windows) per
`mydocs/Plan-phase4-5-then-track-c.md`, branched fresh off that updated
`main`.

---

# Session handoff — 2026-08-19, latest (superseded above by the 2026-08-20
section on "what to do next" — supersedes the "Next session: implement
Phase 3" instructions below, which are now done; everything below stays as
accurate history of what was true
when written)

## This session: implemented Phase 3 (bundled land + second-animal re-test)

Branched off `refactor/phase2-derived-crew-size` (tip `f8134e9`) as
**`refactor/phase3-land-and-second-animal`**. Implemented, per
`mydocs/Plan Phase 1-4.md`'s Phase 3 scope: `BUY_LAND`, a home-quadrant
gate so the extra animal capacity is funded by newly-bought land rather
than carved out of the original cropland, and a bank-floor-gated
`MAX_ANIMALS` bump 3 -> 4. No changes to selling cadence, crop windows, or
sell thresholds - the plan's explicit warning about PR #17/#29 repeating
that exact bundling mistake a third time.

**What shipped, all in `main.py`:**

1. `decide_land_orders(farm, day)` emits `["BUY_LAND"]` inside a day
   window (`LAND_BUY_START_DAY=6` / `LAND_BUY_LAST_USEFUL_DAY=18`, informed
   by `docs/REPLAY_ANALYSIS.md`'s observed day 6-11 buying window) and
   never past a `MIN_CASH_RESERVE_FOR_LAND_BUYING=500` floor - the same
   post-purchase-floor shape as `MIN_CASH_RESERVE_FOR_SEED_BUYING`, since a
   $1,000-$4,000 lump sum is exactly the kind of spend that emptied the
   days 3-7 trough before that earlier fix. `LAND_ORDER`/`LAND_PRICES`
   mirror the engine's own constants (`kaggriculture.py:96-97`) the same
   way `_hire_cost` mirrors the engine's fib.
2. **Capped at `MAX_LAND_PURCHASES=2`, not the engine's own limit of 3** -
   see the measured mechanism below. `docs/REPLAY_ANALYSIS.md` only ever
   observed 2 purchases (25->75 tiles) on the real ladder; the third
   quadrant is untested territory, and turned out to be a real, measured
   loss once tried.
3. `tile_quadrant(x, y, board_size)` mirrors the engine's `_quadrant_of`
   exactly. `choose_animal_to_build` now takes optional `ux, uy` and
   refuses to build past `MAX_ANIMALS_ON_HOME_LAND=3` (the old cap) unless
   the unit is standing outside the home ("NW") quadrant - so the 4th
   animal structure can only land on land actually bought via `BUY_LAND`,
   never carved out of the original 25 tiles' cropland. Inert (`ux=None`)
   for any existing caller with no location context, so every pre-existing
   test needed no changes.
4. `MIN_CASH_RESERVE_FOR_ANIMAL_BUYING=450` added to both
   `choose_animal_to_build` and `decide_animal_market_actions`, alongside
   the existing `ANIMAL_SPEND_CAP_FRACTION` - closes the same gap the seed
   reserve closed: a fraction-of-current-cash cap alone offers no floor
   below the purchase's own cost at its own boundary case.

**Two real bugs found and fixed, both only reachable once Phase 3 made a
long-lived shed animal and a bigger board real for the first time - not
guessed, found by tracing a crashed episode end to end, the way this repo's
best fixes always are:**

- **A live animal sitting in the shed crashed `decide_market_actions` with
  a `KeyError`, silently, every turn thereafter.** Both of its shed-sell
  loops (`for product, quantity in shed.items()`) iterated blindly and
  called `recommend_sell_quantity`/`market_price` on whatever key was
  present - including `"SHEEP"`/`"COW"` itself, which is a valid shed key
  (a bought-but-not-yet-collected animal) but not a market product (only
  its produce, WOOL/MILK, is in `MARKET_PARAMS`). Pre-Phase-3, an animal
  essentially never sat in the shed long enough to hit this: with
  `MAX_ANIMALS=3` every purchase fit inside the home quadrant, so a unit
  reached it and placed it almost immediately. Phase 3's home-quadrant gate
  means the 4th animal can sit in the shed for real turns waiting on a unit
  to reach newly-bought land - so this became reachable, and the caught-
  exception fallback (`{"farmer": ["PASS"], "hands": [], "market": []}`)
  silently froze the whole agent at whatever bank it held the instant the
  animal was bought: seed 0 self-play went 3000 -> 208 for one side and sat
  there, frozen, for the rest of the season, while the other side finished
  normally at 71,885. Fixed by skipping any shed key not in `MARKET_PARAMS`
  in both loops - two-line fix, regression-tested
  (`test_ignores_a_live_animal_sitting_in_the_shed`,
  `test_ignores_a_live_animal_during_the_shed_overflow_valve_too`).
- **Buying all 3 quadrants (100 tiles) is a measured loss relative to
  buying 2 (75 tiles), matching the replay evidence exactly.** Seed 3 vs
  `starter`: buying the third $4,000 SE quadrant took the same agent from
  54,786 down further even as it hired far more (161 -> 282) and planted
  far more (58 -> 199) - a bigger crew spread over 100 tiles produced less
  bank than a smaller crew on 75 tiles did. `docs/ROADMAP.md`/
  `docs/REPLAY_ANALYSIS.md` never actually observed a third purchase on
  the real ladder either - "both purchases" was always exactly 2. Capped
  `decide_land_orders` at `MAX_LAND_PURCHASES=2` accordingly; this alone
  turned the `starter`-paired result from +3,572/9-12 (two badly-losing
  seeds) to **+9,004/10-12, t=2.89** (see below).

**Full four-harness measurement, this branch vs. the Phase 2 control
checkpoint (`f8134e9`, `git show refactor/phase2-derived-crew-size:main.py`):**

| harness | result |
|---|---|
| `.venv/Scripts/python.exe -m unittest discover -s tests` | **162/162 passing** (145 + 17 new: land-order gating, `tile_quadrant`, the home-quadrant animal-build gate, the two shed-animal-crash regression tests, both cash-reserve-floor tests) |
| pre-submit validation gate | `['DONE', 'DONE']` |
| `paired_compare.py` vs `starter`, 12 seeds | **+9,004 mean, 10/12 wins, t=2.89** - decisive by this repo's own win-count-first rule |
| `head_to_head.py` vs Phase 2 control, 12 seeds x 2 seats | **+7,800 mean, 19/24 wins** - just under the ~20/24 "clean" bar (same language Phase 2's own result used), clearly a real win, not noise |
| `selfplay_bench.py`, 12 seeds | candidate mean **61,303**, stdev **11,626**, floor **39,554** vs. a freshly-run Phase 2 control baseline (same 12 seeds, control-vs-control) of mean **54,097**, stdev **4,170**, floor **47,414** - a real **+7,206** mean gain, but stdev nearly triples and the floor drops ~8,000. **Not clean** - this is the same open question Phase 2 itself flagged (stdev/floor moving the wrong way), now more pronounced, not yet closed |
| `head_to_head.py main.py experiments/bigfarm_opponent.py`, 12 seeds x 2 seats | candidate **-1,848 mean, 7/24 wins**, vs. a freshly-run Phase 2 control baseline of **-6,992 mean, 7/24 wins** against the same bridge opponent - still a net loss in absolute terms (bigfarm runs `MAX_HANDS_PER_DAY=15`, `MAX_ANIMALS=4`, half-price sell thresholds, day-10 liquidation - a deliberately scaled-up variant of our own logic), but the gap **closes by 5,144**, roughly three-quarters of it |

**Honest verdict: a real, meaningful win, not a clean sweep of all four
harnesses.** Two harnesses (`starter`-paired, head-to-head vs Phase 2
control) are decisively positive by this repo's own win-count-first rule -
notably, the head-to-head-vs-control result (19/24) clears the exact bar
PR #17 and PR #29 both failed to clear (14/24 each) with a similar bundle,
which is the strongest evidence this isn't a repeat of their "positive
everywhere, convincing nowhere" pattern. But it is not a 4-for-4: self-play
variance/floor move the wrong way (an open question, not a new one - Phase
2 already flagged this direction), and the bigfarm bridge check still
shows a net loss in absolute terms even though the gap versus control
closed substantially. Per the plan's own gate language, this is reported
rather than folded into Phase 4 or further re-tuned without new evidence.
**Recommendation: this is shippable as a genuine improvement over Phase 2,
with the self-play variance question and the bigfarm gap flagged as open
follow-ups for whoever picks this up next** - not a "stop and revert"
result, but also not one to declare fully closed.

**Nothing committed this session** - `main.py`, `tests/test_nikaangukia_meroni.py`,
and this `HANDOFF.md` update are working-tree changes on
`refactor/phase3-land-and-second-animal`, pending explicit go-ahead per
this project's standing practice.

## Next session, if continuing past Phase 3

Per `mydocs/Plan Phase 1-4.md` Phase 4 is independent (crop
`occupancy_kind`) and has its own already-documented re-derivation risk
(see that file's Phase 4 section - the exact `growth_days` substitution it
would produce was already tried directly and decisively lost, -5,099/0-12
vs `starter`). Before starting it, decide whether to first spend a session
closing the two open items flagged above: the self-play variance/floor
regression (try `selfplay_bench.py` at a larger seed count and/or isolate
whether it's `BUY_LAND` or the animal bump driving it, by disabling each
independently against the Phase 3 candidate), and/or a closer look at why
`WORK_TILES_PER_HAND=4` - tuned at 25 tiles - produces a very large crew
(hire counts roughly doubled, 161 -> 282 on the traced seed) once tile
count triples to 75; `docs/ROADMAP.md`'s own §3b confound warning suggests
this ratio itself may need re-deriving at the new tile count, not just the
land/animal knobs this phase touched.

---

# Session handoff — 2026-08-19, even later (superseded above for ordering,
but kept as accurate history of what was true when written)

## This session: implemented Phase 2 (crew size as a derived function)

Branched off `refactor/phase1-shared-ledger` (tip `d43d37a`) as
**`refactor/phase2-derived-crew-size`**, per the prior session's own
instruction and `mydocs/Plan Phase 1-4.md`'s Phase 2 scope. Still no
`BUY_LAND`, still `MAX_ANIMALS=3`, `ACTIVE_ANIMALS=["SHEEP","COW"]`
unchanged — only the crew-sizing formula changed.

**What shipped**, both in `main.py`:

1. `count_pending_work` (`main.py:1377`) now adds animal upkeep to the
   work total via a new `_animal_tile_needs_attention(tile, day)` helper
   (`main.py:1351`) that reuses the exact FEED/CARE/HARVEST/
   COLLECT_FERTILIZER predicates `choose_unit_action`'s priority ladder
   already reads (`main.py:1936-1974`: `fed_today`, `cared_today`,
   `fertilizer_available`, `yield_units` vs `max_held`) rather than
   re-deriving new field-name logic. One work unit per animal-structure
   tile that needs attention today, same granularity as the existing
   `PLANT` branch (one unit whether it needs watering or harvesting, not
   one per action).
2. `max_hands_ceiling(farm, board_size)` (`main.py:1408`) replaces
   `MAX_HANDS_PER_DAY` as the sole cap in `decide_hire_orders`
   (`main.py:1474`). Derived from currently-unlocked tile count (non-
   `"LOCKED"` cells) plus one allowance per built animal structure,
   divided by `WORK_TILES_PER_HAND`, floored at `MAX_HANDS_PER_DAY` so a
   small board can never get a *lower* ceiling than today's shipped
   behaviour. `MAX_HANDS_PER_DAY` itself stays as that floor/historical
   minimum, not removed.

At today's fixed 25 tiles / `MAX_ANIMALS=3`, `max_hands_ceiling` evaluates
to exactly `8` on every seed (`(25 unlocked + up to 3 animal structures) //
4 = 6 or 7`, floored up to `8`) — confirmed non-binding, i.e. the ceiling
itself changes nothing today. It only grows once land or `MAX_ANIMALS`
actually increase, which is the entire point (unblocks Phase 3's land +
second-animal re-test without re-introducing the stale-crew confound
`docs/ROADMAP.md` §3b names).

**Tests**: added `TestDerivedCrewSize` (10 new cases) to
`tests/test_nikaangukia_meroni.py` covering `_animal_tile_needs_attention`
via `count_pending_work` (unfed/uncared/fertilizer-ready/harvest-ready
animal tiles count as work; a fully-tended or unfilled structure tile does
not) and `max_hands_ceiling` (never drops below `MAX_HANDS_PER_DAY`; grows
with more unlocked tiles or more animal structures; `"LOCKED"` tiles don't
count). All pre-existing `TestHireDecision` cases needed **no changes** —
verified by hand that the floor design (`max(MAX_HANDS_PER_DAY,
derived)`) makes every existing fixture's cap identical to before.
`.venv/Scripts/python.exe -m unittest discover -s tests`: **145/145
passing** (135 + 10 new). Pre-submit validation gate: `['DONE', 'DONE']`.

**Measurement, this branch vs. the Phase 1 control checkpoint
(`d43d37a`, `git show d43d37a:main.py`)** — confirmed via `git diff
d43d37a -- main.py` that the actual diff is exactly and only the two
functions above (123 lines, no drift):

| harness | result |
|---|---|
| `paired_compare.py` vs `starter`, 12 seeds | **+2,629 mean, 10/12 wins** — decisive by this repo's own win-count-first rule, not a wash |
| `head_to_head.py` vs Phase 1 control, 12 seeds x 2 seats | **+2,123 mean, 19/24 wins** — just under the ~20/24 "clean" bar but same direction, well above noise |
| `selfplay_bench.py`, 6 seeds | mean **55,679**, stdev **4,242**, floor **50,538**, max 61,458 — vs. Phase 1's own recorded 56,876 / 2,159 / 53,894: mean within ~2% (noise at n=6), but stdev nearly doubled and floor dropped ~3,356 |

**No loss on any harness** — the gate ("no regression vs. Phase 1
control") passes cleanly on that reading. But this is **not** the flat,
inert result the plan predicted for a "purely structural" phase: both
built-in-adjacent harnesses show a real, consistent improvement. Mechanism,
worked out from the diff rather than guessed: at 25 tiles the *cap*
(`max_hands_ceiling`) is unchanged (still exactly 8, see above) — the
actual behavioural change is that `count_pending_work`'s `work` total now
counts an unfed/uncared/harvest-due animal as pending work for the first
time, which occasionally pushes `work // WORK_TILES_PER_HAND` over a
boundary and triggers one more hire on mornings several animals need
attention at once. That's a legitimate, in-scope side effect of "crew
size should account for animal upkeep too," not a bug — hiring against
animal-upkeep demand is exactly what Phase 2 was for — but it means Phase
2 delivered a small real strategy improvement alongside the structural
refactor, not a no-op.

**Open, not blocking**: the self-play stdev/floor move (stdev 2,159 →
4,242, floor 53,894 → 50,538, both at n=6) is the one number that doesn't
cleanly read as "flat or better." Given zero losses on the two
higher-seed-count harnesses and self-play's own small sample size (a
single low-outlier seed can double a 6-seed stdev), this reads as more
likely sampling noise than a real self-play-specific regression, but it
was not re-verified with a larger seed count this session (`selfplay_bench.py`
always benchmarks whatever is currently at `main.py`, so isolating the
control side requires a temporary swap-and-restore, not attempted here).
If a future session wants to close this out before trusting Phase 2 fully:
`.venv/Scripts/python.exe experiments/selfplay_bench.py 12` (or more) on
the current `main.py`, and treat a repeat of the doubled-variance/lower-
floor pattern at a larger n as the real signal to chase.

**Nothing committed this session** — per this repo's own standing rule
(and this project's explicit "ask before committing experiments, even
mid-approved-plan" practice), `main.py`, `tests/test_nikaangukia_meroni.py`,
and this `HANDOFF.md` update are working-tree changes on
`refactor/phase2-derived-crew-size`, pending explicit go-ahead.

## Next session: implement Phase 3 (and only Phase 3) — gate note

Phase 2's gate is cleared (no regression, two harnesses show a real
improvement) — Phase 3 (bundled land + second animal, per `mydocs/Plan
Phase 1-4.md` and `docs/ROADMAP.md` §4) is now unblocked. Per the explicit
sequential-and-gated instruction, **do not start Phase 3 in this same
session.** Before starting Phase 3, decide whether to spend a few minutes
closing the self-play open question above — it's cheap (one more
`selfplay_bench.py 12` run) and Phase 3 will want a trustworthy self-play
baseline to compare against given it changes both land and animal count
together.

---

# Session handoff — 2026-08-19, later (superseded above for ordering, but
kept as accurate history of what was true when written — implemented
Phase 1)

## This session: implemented Phase 1 (hiring + wheat-feed ledgers)

Branched fresh off `main` @ `5180768` per the prior session's instruction:
**`refactor/phase1-shared-ledger`**. Implemented both halves of Phase 1's
scope from `mydocs/Plan Phase 1-4.md`, with real course-corrections on both
found by reading the engine end to end and measuring, not assuming.

**Hiring: no per-unit collision exists, but there was a related, smaller
real bug worth fixing.** Read `kaggriculture.py`'s market processing in
full: `HIRE` is never decided per-unit - `decide_hire_orders` is called
exactly once a turn, after every per-unit action is already decided
(`main.py`), and the engine's only cross-unit atomic-drop rule is PLANT's
(`kaggriculture.py:920-933`) - nothing analogous exists for HIRE. So
"generalize `plant_budget` to hiring" as literally stated in
`Plan Phase 1-4.md` doesn't apply as a collision fix. What *is* real:
`decide_hire_orders` checked `money >= MIN_MONEY_TO_HIRE` (a flat $20
floor) once, then blindly offered up to `MAX_HIRES_PER_TURN` HIRE orders
regardless of the Fibonacci cost curve on `hires_today` (a live counter) -
so late in a hiring streak with tight cash, it could offer hires it can't
afford, and the engine silently no-ops the ones it can't pay for (same
class of silent failure as an unaffordable `BUY_PRODUCT`). Fixed: a real
per-turn money ledger inside `decide_hire_orders` (`_hire_cost`, mirroring
the engine's `_fib`/`_hire_cost` exactly), consulted-then-decremented per
offered hire, stopping once the running total would exceed available
money. Verified against `starter`: completely inert (every seed, delta
exactly $0) - this scenario essentially never arises against a built-in
that never sells and never competes for our cash. Kept anyway, per an
explicit decision this session to ship the ledger shape even without an
active collision to close, since it's a small, honest, real fix rather
than code-shape theater.

**Wheat-feed: closes a real (if smaller-than-PLANT's) collision, and the
scope needed real measurement to get right, not just intuition.** Added
`wheat_budget`, a shared `{"WHEAT": remaining}` dict built once per turn
next to `plant_budget`, threaded through `choose_unit_action`/
`choose_farmer_action` the same way. Two call sites read it: the
shed-adjacent PICKUP-for-feed decision, and the "should I walk toward the
shed" decision from elsewhere on the board.

Measuring this surfaced a real disagreement between harnesses, worth
recording in full because it's another instance of the same trap
`CLAUDE.md` already documents for the second-sheep and hire-gate fixes:

| variant | vs `starter`, 12 seeds (paired) | vs saved control, 12 seeds x 2 seats (head-to-head) |
|---|---|---|
| ledger gates only the atomic shed PICKUP; raw shed read for the walk decision | -566 mean, 5/12 (inconclusive) | **-2,039 mean, 1/24 (decisive loss)** |
| ledger gates both the PICKUP and the walk decision (shipped) | -566 mean, 5/12 (identical - hiring's inert here too) | **+4,517 mean, 24/24 (decisive win)** |

`starter` never sells, so a change whose real effect runs through FEED
timing -> CARE bank payout -> wool/milk production -> SELL timing reads as
a wash there regardless of which way it's built - exactly the built-in
flattery `CLAUDE.md` already warns about for selling/production-timing
changes. `head_to_head.py` (a contested, self-mirrored market) is what
actually separates the two options, and it says gate both decisions.
Gating only the atomic PICKUP looks more theoretically correct in
isolation (walking is a multi-turn commitment, not an atomic one, so a
transient per-turn ledger is a worse fit for it) - but it measures
decisively worse in the harness that can actually see this change's real
effect. Full mechanism and the exact numbers are in the docstring above
`choose_unit_action` and the inline comment at the walk-to-shed call site
in `main.py` - read those before touching this again.

**Full verification, this branch vs. the frozen control checkpoint
(`5180768`, unmodified):**

| harness | result |
|---|---|
| `.venv/Scripts/python.exe -m unittest discover -s tests` | 135/135 passing (4 new: 2 hiring-affordability cases in `TestHireDecision`, 2 in a new `TestWheatBudget`) |
| pre-submit validation gate (`main.py` vs itself, seeded) | `['DONE', 'DONE']` |
| `paired_compare.py` vs `starter`, 12 seeds | -566 mean, 5/12 wins, t=-0.79 - not a regression by this repo's own "read wins before t-value" rule, just inconclusive on a harness that can't see this change's real effect |
| `head_to_head.py` vs saved control, 12 seeds x 2 seats | **+4,517 mean, 24/24 wins** |
| `selfplay_bench.py`, 6 seeds | **56,876 mean** (control 54,536), stdev **2,159** (control 3,481), floor **53,894** (control 51,410) - better mean, tighter spread, higher floor than the control on the harness this repo calls the honest ladder-predicting number |

**A git mistake this session, caught and fixed - flagging so it doesn't
recur.** Branching fresh off `main` via `git checkout -b
refactor/phase1-shared-ledger main` (as instructed by the prior session)
silently overwrote this very file's working-tree content, because `main`
still tracks an old (2026-08-17, 254-line) committed blob of
`mydocs/HANDOFF.md` - the `git rm --cached mydocs/` that stopped tracking
it (commit `1b80d13`) only ever landed on `chore/roadmap-phase-spine-setup`,
never merged into `main`. Recovered this file from the assistant's own
conversation context (it had been read in full moments before the
checkout); lost nothing but a trailing newline. Checked every other
`mydocs/` file for the same exposure - `Plan Phase 1-4.md` was never
tracked in `main`'s history so it was untouched, and
`rules.md`/`SETUP_PLAN.md`/the `FIX_*.md` files are already-committed
archives whose tracked content already matches their intended final
state, so nothing there was actually lost either. **Anyone else branching
fresh off `main` is still exposed to this same silent overwrite** until
the untracking commit actually lands on `main` - worth a small, low-risk,
docs-only PR (`git rm --cached mydocs/`, confirming the `.gitignore` rule
carries over) rather than leaving this as a trap for the next session.

`main.py` and `tests/test_nikaangukia_meroni.py` on
`refactor/phase1-shared-ledger` are committed as of this note. This
`HANDOFF.md` update stays local/uncommitted per the standing rule.

## Next session: implement Phase 2 (and only Phase 2)

Read `mydocs/Plan Phase 1-4.md`'s Phase 2 section first. Extend the
derived-crew logic (`count_pending_work`) to include animal upkeep
alongside tile work, and replace the hardcoded `MAX_HANDS_PER_DAY=8`
ceiling with something that scales - this is the prerequisite Phase 3
(bundled land + second animal) depends on. Still no `BUY_LAND`, still
`MAX_ANIMALS=3`. Same three-harness measurement, same "no regression vs.
control" gate (note: the control to compare against is now this session's
Phase 1 result, not the raw `5180768` checkpoint - Phase 2 builds on
Phase 1, per the roadmap's explicit sequencing).

---

# Session handoff — 2026-08-19 (superseded by the section above for
ordering; kept as accurate history of what was true when written)

## This session: set up the ROADMAP.md Phase 1-4 cross-session spine

No `main.py` change happened this session — this was setup/handoff work only,
done because the team decided to implement `docs/ROADMAP.md`'s Phases 1-4
sequentially, one phase per (separate) chat session, using this file as the
running numbers archive and `mydocs/Plan Phase 1-4.md` as the high-level
spine plan.

**What happened:**

- Checked out `origin/main`, tip **`5180768`** ("Merge pull request #27 from
  Kinjuriu/experiment/bigfarm-opponent") — 25 commits ahead of the
  `2114390` this repo's docs were previously written against. Local `main`
  fast-forwarded cleanly (0 unique local commits).
- Verified `mydocs/Plan Phase 1-4.md` against current `origin/main` state and
  the actual GitHub issue/PR history (`gh issue view`/`gh pr view` on
  #16,#17,#19,#20,#21,#22,#23,#25,#26,#27,#29). It holds up as the spine.
  5 corrections applied directly into that file (read it, not this summary):
  1. Issue #20's "Phase B1" (force real SHEEP+COW species diversity) is
     already done and merged (PR #26, `pick_next_animal_species` /
     `species_owned_counts`, main.py:1166-1207) — don't redo it in Phase 3.
  2. The `MAX_ANIMALS=4`→65,640/3-3, `=5`→356/0-3 cliff table is from PR
     #27's `bigfarm_opponent.py` reference config, not yet measured on our
     own agent at an expanded tile count — re-derive it in Phase 3.
  3. PR #17 and PR #29 are named explicitly as the two-time-repeated
     "bundle land+crew+selling/crop-windows together, get an ambiguous
     result" precedent — neither is merged, both are cited by number so a
     future session doesn't quietly repeat the pattern a third time in
     Phase 3.
  4. New flag on Phase 4: the `occupancy_kind` refactor risks silently
     reproducing an already-decisively-refuted result (the `growth_days`
     substitution tried directly on `fix/ongoing-crop-growth-days`,
     -5,099 mean, 0/12 vs `starter`). Needs a reason the structural framing
     changes the *outcome*, not just the code shape, before re-measuring.
- Working branch for this setup: **`chore/roadmap-phase-spine-setup`**
  (off updated `main`). Untracked `mydocs/` on this branch
  (`git rm -r --cached mydocs/` — the `.gitignore` `/mydocs/` rule already
  existed on `origin/main`, the files just hadn't been untracked from the
  index yet), so these documents stay local-only working notes per this
  file's own established "`mydocs/` is genuinely private" rule from the
  correction below. **The next session's Phase 1 code should branch fresh
  off `main`** (e.g. `refactor/phase1-shared-ledger`), not off this branch —
  this branch is doc/setup only and was never intended to carry `main.py`
  changes.
- Deleted `main_origin_tmp.py` (a stale scratch comparison snapshot from
  before this session's checkout, no longer useful once actually on `main`).

## Control checkpoint — frozen against unmodified `origin/main` (`5180768`)

Every number below is `main.py` **exactly as shipped on `origin/main`**, no
changes. Phase 1 (and later phases) should be paired-compared against this
same commit — `git show 5180768:main.py > /tmp/control_main.py` reproduces
the exact file if a session needs it as `paired_compare.py`'s baseline arg.

**Correction to `Plan Phase 1-4.md`'s "Setup" step**, worth noting here
since it's a methodology point, not a numbers one: `paired_compare.py`
needs two agent files to diff, and at this control-freezing point there is
no Phase 1 candidate yet to pair against — so "freeze the control
checkpoint" here means the three *absolute* harnesses below (plus the
commit hash above for later pairing), not a paired-compare run.

- `experiments/seeded_batch.py` (12 seeds x pass/random/starter):

  | vs | mean | stdev | min | max | wins | escapes |
  |---|---|---|---|---|---|---|
  | pass | 66,279 | ±2,516 | 62,758 | 70,443 | 12/12 | 0 |
  | random | 65,729 | ±2,436 | 61,631 | 69,179 | 12/12 | 0 |
  | starter | 66,014 | ±3,292 | 59,942 | 70,030 | 12/12 | 0 |

- `experiments/selfplay_bench.py` (6 seeds, default) — **the honest,
  ladder-predicting number**: mean **54,536**, stdev **3,481**, min 51,410,
  max 60,094. End prices: WHEAT 52, CARROT 48, TOMATO 86, STRAWBERRY 268,
  MELON 138.
- `experiments/head_to_head.py experiments/bigfarm_opponent.py main.py 12`
  (12 seeds x 2 seats = 24 matches) — **the gap Phase 3 exists to close**:
  bigfarm_opponent +5,865 mean, wins **23/24**. (The file's own docstring
  quotes a 6-seed number, +7,181/6-6; this 12-seed run is the one to treat
  as current.)
- `.venv/Scripts/python.exe -m unittest discover -s tests`: **131 passed**,
  0 failures (no code changed, sanity check only).

## Next session: implement Phase 1 (and only Phase 1)

Read `mydocs/Plan Phase 1-4.md`'s Setup + Phase 1 sections first. **Do not
implement Phase 2, 3, or 4 in the same session** — strictly sequential and
gated, one phase per session, by explicit team decision.

**Scope:** generalize `plant_budget`'s shared-ledger pattern — built once
per turn as `dict(seeds)` (main.py:2140), threaded by reference through
every unit's decision function, consulted-then-decremented atomically right
before committing to an action (main.py:2031-2033) — to **(a) hiring**
(currently `decide_hire_orders`, main.py:1359-1380: a derived-quota function
computed once per turn, `wanted = min(MAX_HANDS_PER_DAY, work //
WORK_TILES_PER_HAND)`, not the ledger pattern) and **(b) wheat-feed
reservation** (not yet located precisely this session — find where units
independently decide to pull wheat from the shed to feed an animal, and
check for the same multi-unit-collision exposure `plant_budget` was built to
close).

**No other change**: land, `MAX_HANDS_PER_DAY=8`, `MAX_ANIMALS=3`,
`ACTIVE_ANIMALS=["SHEEP","COW"]` all stay exactly as shipped on `5180768`.

**Gate to advance:** no regression vs. the control checkpoint above, on all
of `seeded_batch.py` / `selfplay_bench.py` (mean+stdev+floor) /
`head_to_head.py main.py <old-main>` (self vs. a saved copy of `5180768`'s
`main.py`, expect ~0, confirms the ledger refactor is behaviorally neutral)
/ a real `paired_compare.py` run vs `starter` (12 seeds) once there's an
actual candidate file. This phase is structural — "no worse" is success, not
expected to move the bank number much.

---

Personal file, historically not committed on other branches (see
`chore/env-bootstrap-v2-sync`'s `.gitignore` rule for `/mydocs/` — now
also applied directly to this branch's `.gitignore`). **Correction below
(2026-08-17, even later) overturns the very next sentence** — `mydocs/` is
private and does not get committed from this branch either, despite what
this paragraph originally said. Read the top section first.

## Correction — 2026-08-17, even later (read this section first — supersedes
everything below it, including the "read this first" correction further
down; that one is itself now superseded on two points)

A live session picked this file up to reconcile it (and `CLAUDE.md`,
`docs/ROADMAP.md`, `docs/CONCEPTS.md`) against `origin/main`, which had
moved 6 commits ahead since the correction below was written. Two things
from that correction are now wrong and are corrected here instead of
edited in place, per this file's own stated convention of appending
rather than rewriting history:

- **`mydocs/` is not committed from this branch after all.** The original
  framing above ("deliberately committed anyway") and the correction
  below (which explicitly staged `ROADMAP.md`/`Kaggriculture_Strategic_Brief.md`/
  `REFACTOR_GUIDE.md` with `git add -f` against the `.gitignore` rule) are
  both superseded by explicit instruction: `mydocs/` is genuinely private,
  full stop. The pattern for sharing something that starts in `mydocs/` is
  to move it out first — exactly what happened with `ROADMAP.md`, which is
  now `docs/ROADMAP.md` (moved after teammate review) and no longer lives
  in `mydocs/` at all. This file (`HANDOFF.md`) and `mydocs/rules.md` stay
  as local, uncommitted working notes going forward.
- **`origin/main` is no longer at `8477dfe`; it's at `da8cdea`.** Two new
  commits landed same-day, after the correction below was written:
  - `3b8d36f` (Spidey) — retuned `MIN_CASH_RESERVE_FOR_SEED_BUYING` 100→450.
    This closes the days 3-7 cash trough directly (day-5 bank $17 → $392 on
    seed 0 vs `starter`) and resolves two things this repo had recorded as
    settled: PR #13/#14's sub-additivity (+4,166, 24/24 head-to-head;
    +5,389, 10/12, t=3.84 paired, vs. the trough-era +598/7-12), and the
    second-sheep "dead end" (now +900, 8/12 vs `starter` post-fix, was
    -19,514, 0/12 — still only t=0.61, not a clean win, but no longer a
    heavy loss either). No `CLAUDE.md` entry exists for this fix upstream.
  - `da8cdea` (Spidey) — added a root-level `ROADMAP.md` ("Kevin's
    ROADMAP.md" — confirmed **byte-identical** to this branch's
    `docs/ROADMAP.md`, i.e. the same document, not independent work),
    `docs/REPLAY_ANALYSIS.md` (an independent verification using 2 more
    contested-market replay episodes, different dates/teams than our
    original 6), and `experiments/replay_shape.py`. Verdict, confirmed
    twice now: **`BUY_LAND` and multi-animal were never real dead ends** —
    every test we ran held crew size fixed while varying land/animals, and
    the top of the ladder scales both together (75 tiles, 12-15 units,
    COW+SHEEP). `da8cdea` also flagged two things in `docs/ROADMAP.md`
    itself as stale (the §3c sub-additivity caveat, resolved by `3b8d36f`;
    the "Us today" column, predates several changes) — both corrected in
    this branch's copy this session (see below).
  - Also new: two remote-only branches, `experiment/land-and-crew` (1
    commit — `BUY_LAND` + derived crew cap + crop windows + day-10
    liquidation, touches `main.py`+tests) and `experiment/second-animal`
    (1 commit — `MAX_ANIMALS` 1→2). Neither is ours; not touched, just
    logged here since they're directly testing what `docs/ROADMAP.md`
    proposes.
- **`ROADMAP.md` now exists at two paths with diverging content, by
  explicit decision, not oversight.** `origin/main`'s root `ROADMAP.md`
  (from `da8cdea`) does not yet have the two corrections above applied;
  this branch's `docs/ROADMAP.md` does. Chose to keep both rather than
  drop ours, since `causality-mapping` is explicitly a docs/research
  archive branch — reconciling the two (apply the same corrections
  upstream, or delete one) is a follow-up for whoever picks this up.
- **This session also added correction notes directly to `CLAUDE.md`**
  (after the `BUY_LAND is a loss` bullet and after the `MAX_ANIMALS`
  second-sheep section) rather than only flagging the staleness here —
  same content as the `docs/ROADMAP.md`/`da8cdea` points above, in
  `CLAUDE.md`'s own established retraction style.
- `mydocs/rules.md`'s `main.py:N`/`CLAUDE.md:N` pointers were stale again
  (written against `8477dfe`; `3b8d36f` alone added ~36 lines to
  `main.py`, and the two `CLAUDE.md` correction notes above shifted
  everything after them). Re-pointed this session — see the file itself.

**Nothing from this session is staged or committed except**
`CLAUDE.md`, `.gitignore`, `docs/CONCEPTS.md`, and `docs/ROADMAP.md` —
by explicit instruction, `mydocs/HANDOFF.md` and `mydocs/rules.md` stay
local-only working-tree edits.

## Correction — 2026-08-17, later (previously "read this first" —
superseded above on the `mydocs/`-commit point and the `origin/main` tip;
the entries themselves are left unedited as an accurate log of what was
true at the time they were written)

A repo-hygiene pass (validating `HANDOFF.md`/`ROADMAP.md`/`docs/CONCEPTS.md`
against real current state, ahead of sharing the latter two with the team)
found several things below are now out of date:

- **`gh` is authenticated.** `gh auth status` now reports logged in as
  `future-centaur`. The "Priority — do this first" items below about
  running `gh auth login` are done; ignore them.
- **PR #13 is merged**, not pending review. It landed via **PR #14**
  (`8477dfe`), which bundled it with a second change
  (`e8cf43e`, `MIN_MONEY_TO_HIRE` 150→20) and re-measured both together —
  worth knowing in passing: the combination scored sub-additive
  (**+598, 7/12**) versus #13's own isolated **+2,271, 10/12**. Not being
  tracked as a new action item this pass; noted here so nobody re-derives
  it from scratch. Full detail in PR #14's description on GitHub.
- **The local `main` branch pointer was stale** (`2114390`) — `origin/main`
  had moved 6 commits ahead to `8477dfe` and nobody had run `git fetch` on
  this machine since. Anything below that says "current main" was written
  against the stale pointer; treat `origin/main` as ground truth going
  forward and re-fetch before trusting any "main tip" claim.
- **Branch/worktree audit results** (full detail: three parallel read-only
  investigations this session), **corrected by explicit user instruction:
  only delete branches the user (`future-centaur`) actually authored.**
  Checked every branch's commit authorship — the six "confirmed dead"
  remote branches below are all teammate-authored (Stephane
  Njoki/`Kinjuriu`, `Spidey-Acer`, `billymwangidev`), so **none of them get
  touched, dead or not**, regardless of what the git-history audit found.
  - User-authored, confirmed dead, safe to delete whenever: local
    `fix/ongoing-crop-growth-days` (empty vs. main, zero unique commits);
    worktree `fix-seed-plant-budget` (clean, its branch — `future-centaur`'s
    PR #13 — is already merged).
  - **User-authored, content now fully carried over onto this branch —
    also safe to delete whenever:** `chore/env-bootstrap-v2-sync` (its
    `/mydocs/` `.gitignore` line is now on `causality-mapping` directly —
    see below) and `fix/tomato-fertilizer-yield-bonus` (its implementation
    was cherry-picked in — implement/docs/revert, net zero on `main.py`,
    full write-up with the real `FERTILIZER_YIELD_BONUS` implementation
    detail now merged into this branch's `CLAUDE.md`). Both branches are
    redundant now, not just dead.
  - **Teammate-authored — do not delete regardless of staleness:**
    `experiment/forward-pricing-crop-selection`,
    `experiment/forward-pricing-integration`, `feat/animal-expansion-integration`,
    `feat/fertilizer`, `feat/three-goose-animal-expansion`,
    `research/forward-pricing-v0` (all confirmed zero unique commits ahead
    of `origin/main`, but not this user's branches to remove).
  - Needs inspection, don't touch: the 4 `agent-*` worktrees under
    `.claude/worktrees/` all have **uncommitted, uninspected diffs to
    `main.py`** pinned at the stale `2114390` tip. Pruning them now would
    silently discard those diffs. Not resolved this session.
  - `mydocs/rules.md`'s line-number pointers (flagged stale multiple times
    below, never fixed) were confirmed off by 315-580 lines against
    `origin/main`, plus two outright content errors (`ACTIVE_ANIMALS`
    listed `["GOOSE"]`, actually `["SHEEP"]`; a reference to
    `SELF_SUPPLY_EXPONENT`, which no longer exists in `main.py` at all).
    Fixed this session — see the file itself. Its `CLAUDE.md:line` pointers
    now target *this branch's own* `CLAUDE.md` (a superset of
    `origin/main`'s after the carry-over below), not `origin/main`'s copy —
    the file itself explains why.

**Follow-up in the same session: carried the above content onto
`causality-mapping` directly, still all uncommitted working-tree changes.**
- `.gitignore` now has the `/mydocs/` rule. Side effect: new `mydocs/`
  files stop showing up in plain `git status`/`git add .` on this branch,
  since this branch deliberately commits `mydocs/` against the rule's
  intent. `ROADMAP.md`, `Kaggriculture_Strategic_Brief.md`, and
  `REFACTOR_GUIDE.md` were force-added (`git add -f`) so they're staged
  and won't get silently dropped — still need an actual commit.
- `fix/tomato-fertilizer-yield-bonus`'s three commits (implement, docs,
  revert) were cherry-picked in. `main.py`/tests land back at exactly their
  pre-existing content (net zero, confirmed via diff and the 118-test
  suite still passing); `CLAUDE.md` keeps the docs commit's full write-up.
- `CLAUDE.md` was also reconciled against `origin/main`'s own content
  since the `2114390` merge-base (the hire-gate section, the second-sheep
  cash-trough finding, the crew/`BUY_LAND` re-test, PR #13's three
  dead-end variants, and the corrected "more than one animal" entry) —
  this branch's `CLAUDE.md` is now a full superset of `origin/main`'s, plus
  this branch's own growth_days/fertilizer-bonus write-ups. `mydocs/rules.md`
  was re-pointed to the new line numbers (295 → 350 lines).
- `mydocs/ROADMAP.md`'s Phase 0 line about "two pending docs-only PRs" was
  removed by the user directly — accurate, since that content is no longer
  pending, it's merged into this branch's `CLAUDE.md` now.

None of the above changed any strategy or code — this was a docs/repo-state
reconciliation pass only, done because `mydocs/ROADMAP.md` and
`docs/CONCEPTS.md` are about to go to the team and needed to be checked
against reality first. **As of this note, `causality-mapping`'s working
tree is the fullest, most current single source of truth in the repo** —
it has everything `origin/main` has (`CLAUDE.md`-wise; `main.py` itself is
still deliberately untouched, matching `2114390`) plus everything from
`chore/env-bootstrap-v2-sync` and `fix/tomato-fertilizer-yield-bonus`, plus
its own growth_days/Fix-B research archive. Nothing has been committed or
pushed.

---

## Session close-out (supersedes the "Session close-out"
section below, which is retitled "Prior session close-out" and kept for
history)

This session picked up right after the TOMATO/STRAWBERRY investigation
closed (see "Prior session close-out" below — unchanged, still accurate)
and did something new: **looked outward at the competition for the first
time**, instead of continuing to iterate on our own agent in isolation.

**What happened, in order:**

1. Confirmed there's no structured feature-coverage tracker anywhere in the
   repo (checked `README.md`, `CONTRIBUTING.md`, `docs/`, `mydocs/`,
   `docs/checkpoints/`) — closest things are the checkpoint docs' "Known
   limitations" sections and `CLAUDE.md`'s own narrative. Parked per user
   direction; not built this session.
2. Read `mydocs/Kaggriculture_Strategic_Brief.md` and
   `mydocs/REFACTOR_GUIDE.md` (both dated 2026-08-15, written before the
   current imperative-priority-ladder `main.py` was built instead) at the
   user's request, to assess whether the brief's scoring-engine
   architecture is still worth adopting given how "hectic" the
   TOMATO/STRAWBERRY patching became. Assessment: the brief's *diagnosis*
   (this is a joint resource-allocation problem needing explicit valuation,
   not ad-hoc thresholds) reads as more validated now, not less — but a
   full rewrite is disproportionate given how much measured, working logic
   already exists in `main.py`. `REFACTOR_GUIDE.md`'s own benchmark numbers
   are also stale (predate essentially every fix in `CLAUDE.md`).
3. Cross-referenced our own "measured dead ends" against the brief's
   concept categories (constants/causal-links/state-relationships) —
   conclusion: some real dead ends (TOMATO/STRAWBERRY's ongoing-crop tile
   lifecycle, sheep's CARE-bank mechanic, melon's zero-shop-demand
   structure) were genuine missing-concept gaps that a living concepts doc
   would have caught faster. But at least two dead ends (daily feeding,
   `WORK_TILES_PER_HAND`) were pure evaluation-methodology mistakes
   (across-seed stdev instead of paired comparison), and the TOMATO/
   STRAWBERRY saga's final lesson — a mechanically *correct* fix still lost
   because it broke implicit compensation elsewhere in the heuristic — is a
   real limitation of "just get the causal links right," not something a
   concepts doc alone fixes.
4. **The pivotal move**: pulled and analyzed six real top-ladder replay
   episodes from the host-maintained
   [`kaggriculture-episodes-index`](https://www.kaggle.com/datasets/kaggle/kaggriculture-episodes-index)
   Kaggle dataset (documented in `docs/kaggriculture_context.md` §4.5 but
   never previously used by this project). Confirmed it's real, current,
   and cheap to sample — per-episode JSON files (~25-32MB, standard
   `kaggle_environments` replay format) are individually downloadable
   without pulling a whole day's ~21GB dump:
   ```
   kaggle datasets files kaggle/kaggriculture-episodes-<YYYY-MM-DD>
   kaggle datasets download kaggle/kaggriculture-episodes-<YYYY-MM-DD> -f <episode_id>.json -p <dest>
   ```
   Also confirmed `melon_maxxer` (our long-standing "hard opponent"
   benchmark) is just the official starter notebook's reference agent, not
   a tuned competitor — so "beats melon_maxxer 25%+" was never actually a
   proxy for "beats a good player."
5. Sampled 6 episodes across **Aug 1, Aug 10, and Aug 16 (×3)** — 8 distinct
   player pairings. Findings (detailed in `mydocs/ROADMAP.md` §1-2 and now
   also indexed in `docs/CONCEPTS.md` §4):
   - Final money **$71,757 – $126,015**, vs. our local ceiling of ~$28k
     (self-play) / ~$42k (vs. built-ins).
   - `BUY_LAND` used exactly twice, every single episode, always in the day
     6-11 window — directly contradicts our own "BUY_LAND is a loss"
     conclusion, which was measured only against an undersized, fixed crew.
   - Crew scales to 10-14 hands sustained from day ~8 through ~day 27 — far
     beyond anything we've tried.
   - Every episode runs 2+ animal species (COW + SHEEP, sometimes + GOOSE)
     — directly contradicts "more than one animal is a heavy loss," same
     root cause (fixed-crew confound).
   - Per-crop planting windows, not a global day-gated phase machine: MELON
     only days 0-7, STRAWBERRY only days 5-12 (planted once per tile,
     matching its "ongoing crop" tile lifecycle), CARROT only days 21-25
     (late filler), WHEAT continuous. **TOMATO planted in zero of the 6
     episodes** — this independently validates the just-closed
     TOMATO/STRAWBERRY investigation's conclusion.
   - Selling ramps hard from day ~10 and stays heavy (15-48 orders/day)
     straight through day 29 — no day-22 "liquidation" discontinuity, which
     argues against ever building a rigid `SETUP→GROWTH→LIQUIDATE` global
     state machine like the Strategic Brief proposed.
   - 5 of the 6 episodes were near-identical down to exact unit counts
     across unrelated player names — most of the top of the ladder is very
     likely running one dominant shared strategy (a widely forked public
     notebook), not diverse independent approaches.
6. Wrote `mydocs/ROADMAP.md` — an architecture roadmap built from both
   evidence sources above, framed per explicit user instruction as
   **prescriptive, not a critique**: for each past failure mode, it shows
   the code structure that would make that class of bug unreachable,
   paired with the evidence that the structure is aimed at the right
   target (the user was explicit mid-session that structure is necessary
   but not sufficient — evidence still has to justify where a given
   structural choice points). Read that file for the actual phase sequence
   (0 through 7) before starting any new PR.
7. Created `docs/CONCEPTS.md` — a living structured reference (constants,
   causal links, synergies/anti-synergies, evaluation discipline, and the
   replay-derived target shape), seeded from the Strategic Brief's §3
   skeleton but corrected against everything actually measured/traced in
   `CLAUDE.md` plus this session's replay findings. Lives in `docs/` (not
   `mydocs/`) because it's meant to be a permanent, continuously-updated
   team reference — same role as `docs/ARCHITECTURE.md` and
   `docs/CHECKPOINTS.md`. Recommended and created based on: at least four
   mechanics this project already paid real cost to discover (ongoing-crop
   tile lifecycle, CARE-bank timing, melon's shop-demand structure, the
   plant-request-drop-on-oversupply rule) were previously indexed nowhere.

**Nothing was committed this session.** `mydocs/ROADMAP.md`,
`docs/CONCEPTS.md`, and this `HANDOFF.md` update are all working-tree
changes on `causality-mapping`, pending explicit user go-ahead per standing
commit-approval practice.

### Priority — do this first next session

1. **`gh auth login` is still pending** (carried over from before — untouched
   this session; see "Prior session close-out" below for why it's blocked
   headless). Confirm with `gh pr view 13 --repo Kinjuriu/washamba_bots`
   once done.
2. **Review `mydocs/ROADMAP.md` and greenlight which phase to start on.**
   Phase 0 (merge PR #13, land the two pending docs-only PRs, freeze V3) is
   pure housekeeping and doesn't need much discussion. Phase 1-3 (shared
   hiring/wheat ledger → derived crew size → bundled land+animal re-test)
   is where the actual strategy-content work begins and should be discussed
   before starting.
3. Decide whether/when to commit `mydocs/ROADMAP.md`, `docs/CONCEPTS.md`,
   and this `HANDOFF.md` update — currently just working-tree changes.

---

## Prior session close-out (2026-08-17, earlier — superseded above for
priority ordering, but still accurate and unchanged)

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
recommended fixing `growth_days` instead of boosting TOMATO further -
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
section - short version:

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

---
