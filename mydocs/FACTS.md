# Farm fact-set (living spec)

Canonical shape for the agent under construction. Method:
`mydocs/AGENT_BUILDING_PROTOCOL.md`. Session diary: `mydocs/HANDOFF.md`.
Mechanisms and dead ends: `CLAUDE.md`.

This file is the spec. `HANDOFF.md` does not duplicate it.

**Equilibrium:** animal-first / v20 cadence. Broke on purpose after day 0.
Crop-first Path A is shipped `main.py`. These rows are what a throwaway
must afford; they are not a description of shipped `main.py`.

Pointers are **function + rule**, never line numbers.

## How to change this file

A shape edit starts here. Three operations only:

- **Add** a row (invariant + when + counter + code rule).
- **Remove** a row when two facts fight. Do not average them into a knob.
- **Supplement** a row (same invariant, tighter rule — e.g. wheat reserve
  on buy *and* sell, both keyed on owned).

Then: fact card → diff the throwaway against **every** row →
`tape_profile.py` and a contested episode vs `route_v20.py` on seeds 0
and 8, read the named counters → only then bank / harnesses / shipped
`main.py`. (`starter` is a smoke check now, not the judge — see the
acceptance bar below.)

Knob edits (`MAX_ANIMALS`, sell thresholds, `WORK_TILES_PER_HAND`) do
**not** get a row unless they rewrite a shape invariant. They use
`docs/EXPERIMENT_WORKFLOW.md` and must leave every row below still true.

A slogan (“match v20”, “STRAW pin”, “raise the cap”) is not a row.

## Acceptance bar (rewritten 2026-09-05)

**A row is judged on contested bank vs `agents/route_v20.py`, seeds 0
and 8, seat 0.** A fact edit that lowers either seed's contested bank is
a **fail**, not “soft” — even when every unit counter in this file still
passes. `starter` is a crash / escape smoke check only: it never sells
and never buys wheat, so it cannot price a sell path, a feed bill, or a
production-timing slip.

This replaces seven sessions of “audit CLEAR” under which the contested
bank fell **51,421 → 26,429** (seed 0) and **51,951 → 8,269** (seed 8)
while `d0 4/4`, `unlock ≥ 14`, `NW STRAW = 0` and `0 escapes` all held.
Unit counts at named moments cannot see a shape that is right in
composition and **4–6 days late** on every producing asset.

So every row now names its **day**, and the day is checked against the
tapes with `experiments/tape_profile.py` — crew, herd, plantings by crop
and sells by product, per engine day, candidate against tape mean and
against the live opponent in the same episode. Run it before the bank:

```bash
.venv/Scripts/python.exe experiments/tape_profile.py experiments/_facts_v20.py --seed 0
.venv/Scripts/python.exe experiments/_trace_cashflow_v20.py 0 8
```

Two escape hatches this bar closes:

- **“Contested is noisy, starter is reproducible.”** Both built-in and
  contested episodes are seeded and reproducible. Reproducible against an
  opponent that cannot lose money is not a measurement.
- **“The counters moved, the bank is a later problem.”** The counters are
  proxies for the bank. When a counter passes and the contested bank
  falls, the counter was the wrong proxy — fix the row, not the bank.

The shape throwaway `experiments/_facts_v20.py` is **tracked in git** as
of 2026-09-05. It was gitignored while the regression above accumulated,
so there was no revision to bisect. Commit it with each fact card.

## Status vs shipped `main.py`

| | Meaning |
|---|---|
| `false` | Rule in shipped code fights this fact. Throwaway must change it. |
| `partial` | Some of the invariant holds; the named counter still fails. |
| `true` | Shipped code already affords it. Throwaway must not break it. |

## Throwaway status (2026-09-06, T1 vs v20 still ~75k)

`experiments/_facts_v20.py` has the funding stack, the d5–d6 STRAW/wheat
supplement, and fact 44 (shop mix picks species; no yarn → sheep stay at
2). Contested vs `route_v20` **banks: 40,236 / 55,411**. That is
**−74k / −78k versus v20** (114,305 / 133,123). The fact-44 **−570**
is only versus our prior throwaway (40,806), not versus v20 — park it.
Two WHEN supplements of the d11 burst failed (hold-burst: shop reroll;
d12h0 slack: escapes). Do not revert the yarn lock. Do not hunt a
third fert-only bind. Throwaway is back on hold-6 + `MAX_ANIMALS=18`
(15/17 align dropped). Fact 33 first-buy reserve 0 is dropped
(same 28,751 / 36,766 / herd 18 as the land-reserve bundle).
Fact 20 harvest-before-collect is dropped (39,690 / 55,210, land
[7, 11], seed 0 herd 18). Shop+post-sell rewrite of 15/44 is dropped
(38,649 / 46,533; seed 0 herd 4 through d17; land [7, 11]).

Timing both seeds (same shape): wheat **d0 = 7** (tape 7); STRAW d5
**1/4**, d6 **5/8**, d7 **0/4**, d8 **1/4**; d11 carpet **15**; MELON after
d0 = 0; land **[8, 11]**. Seed-8 town/yarn split is closed by fact 44.

**Contested executed `$` (2026-09-06, `_trace_cashflow_v20.py`):**

| stream | seed 0 gap | seed 8 gap | vs pre-T1 | next? |
|---|---|---|---|---|
| STRAWBERRY | **−43.5k** (18.3 / 61.8) | **−38.7k** (20.3 / 59.0) | widened (−29.6k) | **live** (27/30) |
| WHEAT net | −12.2k | −16.6k | smaller (−20k) | after STRAW `$` |
| MILK | −5.6k | **−11.4k** | new (no-yarn cows) | with herd (15) |
| WOOL | −6.5k | −3.0k | smaller (−25.3k) | with herd (15) |
| MELON | −3.2k | −3.2k | smaller (−5.3k) | parked |
| FERTILIZER | −1.4k | −1.4k | smaller (−4.1k) | parked — no third fert bind |

The pre-T1 table (STRAW 17.3/46.9, WOOL 21.6/46.9, wheat −16.2/+3.7,
MELON 12.5/17.7, fert 10.5/14.6) is **stale**. Do not judge against it.
Funding-stack seed 0 was STRAW −19.8k / WOOL −3.5k / wheat −9.7k /
fert −3.0k at bank 16,628 — streams better, bank worse. The d5–d6
supplement raised the bank and **widened STRAW `$`**.

`tape_profile.py` still: crew ±2; **herd −8 at d10** (held at 6; tape
14); STRAW d6 holds half-tape, d7/d8 miss; d5=1 is structural (2
empties + BUILD — do not judge d5 against half-tape); wheat d0 holds;
MELON after d0 = 0. Do not reopen 40–42 (crew-wide walk / DROP / SW
fert).

**Live card: produce funds the calendar; a miss is a diagnosis.**
Keep `calendar_owned_target` and land windows. When a buy does not
emit, name the missing inflow and rearrange that activity — do not
replace the gate. Collect-then-harvest is dropped (inflow held,
land [7, 11]; ungated walk 40,033/61,130 with 1 escape, or
+11,783/+5,719 with Stage 2 then 1 escape; unfed-gated walk
39,587/52,878, 0 dips). Do not retry that bind, harvest-before-
collect, freeze-until-milk, first-land without d6, first-buy
waive, the bundle, d6 wool DROP, the tape ladder, or cap 14 alone.
Throwaway still hold-6 + cap 18 (40,236 / 55,411, land [8, 11]).
Fact 44 −570 is parked. **Do not merge Path A.** Do not port
`main.py`.

The `Shipped` column below is still about **shipped `main.py`**, not the
throwaway. Do not read throwaway-clear as shipped. K=3; fact 32 bar ≥14.

## Fact card (paste at session start)

```text
Kind: add | remove | supplement (fact N)
Was:
Now:
Fights: (dropped row, or none)
Throwaway: experiments/_*.py
Pre-run: every row still true in source? (not just the one you touched)
Counters: the ones this card names, plus d0 pens/herd ≠ 1/1
```

Half-stack rule: a subset of rows is allowed only if every *other* row
still holds. Calendar-only was legal until it broke 8–11. Hour-0 batch
was illegal because it broke 2.

---

## Beach-head (end of day 0)

| ID | Invariant | When | Counter | Code that must afford it | Shipped |
|---|---|---|---|---|---|
| 1 | 4 animals owned, mix 2 cows + 2 sheep, paid from the starting $3,000. No 5th. | end of day 0 | owned = 4 (2C2S); `BUY_ANIMAL` count | `decide_animal_market_actions` / calendar: hour-0 batch or same-day 2C2S; cap does not fire a 5th. `MAX_ANIMALS` is the *season* cap, not “buy whenever cash allows.” | partial (2S2C over hours 0–3, not a batch) |
| 2 | 4 pastures built. `BUILD_PASTURE` is free; it must not wait on animal-purchase cash. | end of day 0 | d0 pens/herd ≠ **1/1**; pens ≥ 4 | `choose_animal_to_build`: do **not** apply `ANIMAL_SPEND_CAP_FRACTION` or `MIN_CASH_RESERVE_FOR_ANIMAL_BUYING` to a build. Those bars are for `BUY_ANIMAL` only. | false (build uses the same cash bar as buy → freeze) |
| 3 | Those 4 animals are placed. Shed stock does not collect, eat, or produce fertilizer. | end of day 0 | placed = 4, not just bought | `choose_unit_action`: pickup → walk → place; enough crew (fact 4). Serial `unfilled > 0` return-None cannot leave 3 animals in the shed. | partial (d0 **3/2**; 4/4 by day 12) |
| 4 | Several hands exist so the farmer is not the only unit doing build/pickup/place. | hour 0 of day 0 | hires land (v20: 5); 4 round trips finish the same day | `decide_hire_orders` / `nikaangukia_meroni` market list: hour-0 hires happen; they must not consume the slots fact 6 needs for `BUY_ANIMAL`. | false (work-driven; `MAX_HIRES_PER_TURN = 3`; not a day-0 opening book) |
| 5 | Wheat for 4 mouths is in the shed, bought day 0, and **not sold** while animals are still in inventory. | day 0 | shed WHEAT ≥ feed need; no same-day sell of that wheat | `decide_animal_market_actions` (`BUY_PRODUCT WHEAT`); `decide_market_actions` wheat sell reserve. Reserve keys on **owned** (shed + carried + placed), not `scan_animal_structures` filled-only. `nikaangukia_meroni` today: `reserved_wheat = filled_animals * MIN_WHEAT_RESERVE_FOR_FEEDING`. | false (flat 2; keyed on placed) |
| 6 | The 10 market-order cap did not drop the animal buys. | hour 0 of day 0 | `BUY_ANIMAL` ×4 (or 2+2) actually lands | `nikaangukia_meroni` order list vs `MAX_MARKET_ORDERS_PER_TURN`. v20 hour 0 is exactly 10 (5 hire + 2 animal + 2 seed + 1 wheat). Extra hires or seeds in front silently truncate `BUY_ANIMAL`. | false (hire first, animals last) |

## Later buy days (3 / 5 / 7 / 9+)

| ID | Invariant | When | Counter | Code that must afford it | Shipped |
|---|---|---|---|---|---|
| 7 | Previous beach-head still alive. | every later buy morning | 0 escapes; `FEED` daily | facts 18–20; `choose_unit_action` FEED before CARE | true at cap 4 |
| 8 | Collected fertilizer is in the shed (~1 / placed animal / day). Day 3’s cow is sized to **4 fert ≈ $400**. | days 1–3 | `COLLECT_FERTILIZER`; shed FERT ≥ ~4 by day 3 | `choose_unit_action` collect; facts 1–3 (if only 1–2 placed, nothing to sell) | partial (collect exists;  d0 placement lag cuts inflow) |
| 9 | **Collected fertilizer is sold the day it is collected, every day from d1** (tape: 3/5/4/6/6/8/8/11/13… units a day, unbroken to d29). It is not banked for STRAW. The round trip is structurally break-even (`CLAUDE.md`: linear both ways, buy and sell average $97), so **held fert is not saved value — it is only foregone liquidity**, and liquidity in d1–d10 is what buys fact 15's herd. The existence-hold (“keep it while any live STRAW is on the board”) cost **−4.1k** contested on seed 0 and bought nothing measurable. Selling still lists **before** `BUY_ANIMAL` on emit turns (fact 10). Fact 37's parked surplus valves were attempts to leak past this hold; with the hold gone they are moot. | daily from d1 | `SELL FERTILIZER` on **every day d1–d29** (no dry spell > 1 day); `tape_profile.py` SELL FERTILIZER row within ~±4/day of tape; `SELL FERTILIZER` still before `BUY_ANIMAL` on emit turns | `decide_market_actions`: sell collected fert each turn it exists, subject only to the 10-order cap and fact 10's ordering. Delete the live-STRAW existence-hold. Fact 21 is the buy-back half. | false (hold until liquidation) |
| 10 | `SELL FERTILIZER` is listed before `BUY_ANIMAL` on the turn the calendar buy actually emits, not only hour 0. | the turn `BUY_ANIMAL` for a day-3/5/7 (or catch-up that day) is listed | order list position; cow lands that turn | `nikaangukia_meroni`: if this turn’s animal list contains `BUY_ANIMAL`, concat sell → animal → hire/seeds. Catch-up hours must not fall back to hire-first. | false |
| 11 | The buy decision uses **post-sell** cash, not `obs["money"]`. | same turns as 10 | cow emits even when observation < $850 | `decide_animal_market_actions` must not gate on raw `farm["money"]` when this turn’s sells fund the buy. | false |
| 12 | Hires do not run before that buy on those turns. | same turns as 10 | hire after sell+buy, or not at all this hour | `nikaangukia_meroni` today always hires first. v20 day 3: sell fert, buy cow, *then* hire. Catch-up hours follow the same order. | false |
| 13 | Seed restock does not run between the fert sell and the animal buy. | same turns | no `BUY_SEED` between those two orders | `decide_market_actions` currently emits seeds before animals are even appended. | false |

## Calendar

| ID | Invariant | When | Counter | Code that must afford it | Shipped |
|---|---|---|---|---|---|
| 14 | No 5th animal on day 0. A 4-animal dump that leaves ~$456 also freezes if fact 2 is false. | day 0 | owned = 4; cash after buys still lets pens start **or** fact 2 holds | calendar in `decide_animal_market_actions`; not “buy up to cap whenever affordable” | true (only because `MAX_ANIMALS = 4`) |
| 15 | **Herd rides the tape's days, and the season ceiling is a ceiling, not a target.** Owned by engine day: **4** d0, **5** d2, **6** d3, **8** d6, **10** d7, **12** d8, **13** d9, **14** d10 — then flat. Held at 6 through d10 (the old row) costs ~5 production days on 8 head; measured **−25.3k WOOL** contested on seed 0. The d6–d10 ramp is funded by the tape's own inflows on those days — d6 `SELL WOOL` from the day-0 sheep (first yield d6), plus daily fert (fact 9) — not by a cash floor, so it is a *sequencing* claim (facts 10–12), not a bigger reserve. Nothing is bought after d10: the old row's d11+ shop-mix ramp bought **21 head against an 18 cap** on contested seed 0 and still ended the season **losing placed animals (18 → 16 over d25–27)**, because the late herd arrives with no wheat behind it. Prefix-affordable still applies; unlock-h0 animal deferral still holds. | those days | `tape_profile.py` herd row within **±1 of the tape on every day d0–d10**; owned ≤ 14 after d10; **`BUY_ANIMAL` total ≤ 14** (not ≤ cap); 0 escapes **contested** as well as vs `starter` | calendar / day gate. `calendar_owned_target` = the tape ladder above, terminating at 14. Prefix: `_animal_can_pay` per unit. No d11+ shop-mix ramp. | false |
| 16 | Pens exist for the new animals. Parallel pens up to the day’s target. Home-quadrant cap cannot block pen 4–5 if land is not bought until day 6. Same-day placement when an **empty unlocked tile** exists; if home is full of crops, wait for the next `BUY_LAND`, not past it. | buy day; by next land unlock if home is full | unplaced animals do not sit in the shed all season; a day-5 extra is placed by d6h23 once NE unlocks | `choose_animal_to_build`: parallel `pending_builds` up to target; `MAX_ANIMALS_ON_HOME_LAND = 3` must not refuse pen 4 on NW before `BUY_LAND`. Do not pretend a 6th pen fits on 25 planted tiles. | false (serial unfilled; home cap 3) |
| 17 | Cap is **14** and it binds nothing, because fact 15's ladder tops out there. A cap set above the ladder (18) let the d11+ ramp buy 21 head contested. Do not start at 10 on day 0. | season | end herd **= 14**; d0 still 4; species mix follows the tape (roughly 8C6S / 6C8S — the shop mix picks *which*, never *how many more*) | `MAX_ANIMALS = 14`; calendar (15) is what actually paces buying. Do not raise the shipped cap as the first edit. | false (`MAX_ANIMALS = 4`) |

## Feed

| ID | Invariant | When | Counter | Code that must afford it | Shipped |
|---|---|---|---|---|---|
| 18 | Wheat buffer scales with **owned** animals, not a flat 2 for the farm. | every wheat buy/sell | shed wheat tracks owned; not pegged at 2 | `MIN_WHEAT_RESERVE_FOR_FEEDING` used as a per-head multiplier on **owned**; both `decide_animal_market_actions` buy trigger and `decide_market_actions` sell exemption. | false (flat 2; sell keyed on filled) |
| 19 | Feed wheat is not gated behind `MIN_CASH_RESERVE_FOR_SEED_BUYING`. | anytime cash is $9–$375 | `BUY_PRODUCT WHEAT` still emits | wheat buy lives in `decide_animal_market_actions` (no seed reserve today — **keep it that way**). Do not add the seed floor to this path. | true (buy path); still loses if fact 13 spends the bank first |
| 20 | FEED happens every day: units on the animal tiles, wheat in the acting inventory. A walker must not `claimed`-steal an occupied unfed tile from a unit already on it with wheat. Walking to an unfed animal outranks local CARE / COLLECT on a different tile; it does **not** outrank WATER or crop HARVEST underfoot. Nearest-unfed skips already-assigned tiles; it does not drop feed. **Harvest-before-collect (`yield_units > 0` before COLLECT) is dropped.** **Collect-then-harvest (any yield after COLLECT + walk-back) is dropped** — inflow held, land [7, 11]; ungated 40,033/61,130 with 1 escape, Stage 2 52,019/61,130 with 1 escape, unfed-gated 39,587/52,878. Do not retry either harvest reorder. | every day | `FEED` ≈ owned × days; 0 escapes; far pens fed after the free first miss | `choose_unit_action`: FEED-underfoot ignores `claimed`; occupied unfed+wheat tiles are pre-marked into `feed_claimed`; `find_nearest_target(..., exclude=feed_claimed)`; feed `walk_to` does not add to `claimed`; crop HARVEST / WATER underfoot, then feed-walk, then CARE/COLLECT. A market order alone is not this fact. | true at cap 4; false at cap 8 without the walk/claim rules |
| 21 | **Buy fertilizer back to apply it, in the tens per season** (tape: 35–64 `BUY_PRODUCT FERTILIZER`, alongside 280–360 sold). Fact 9 sells the flow because holding it is a liquidity cost; this row buys the few units a tile actually wants at the hour it wants them. That is not the arbitrage `CLAUDE.md` rules out (buy-the-dip / sell-the-recovery, −1,486), and not shipped `main.py`'s liquidation-era incidental buying — it is fert-on-demand for `FERTILIZE`. | when a tile is fertilized and the shed is empty of fert | `BUY_PRODUCT FERTILIZER` between ~20 and ~70 for the season; `FERTILIZE` count does not fall when fact 9 starts selling the flow | `decide_market_actions` top-up sized to the turn's `FERTILIZE` demand, never to a stock target. | false |
| 22 | **WHEAT is the default crop on any empty tile, from day 0** (tape: 7 on d0, then a continuous 3–14/day to d28, ~190 plantings and ~190 `BUY_SEED WHEAT` a season). Its harvest is what feeds the herd; `BUY_PRODUCT` (facts 5, 18, 19) is the top-up, not the supply. Buying every mouthful instead cost **−20k net** contested on seed 0 (we paid 16.9k for wheat and sold 0.7k; v20 paid 47.4k and sold 51.1k — and its churn is what pushes the price we pay). Still forbidden, and this is the distinction the row exists for: no wrapper that force-plants because **stock is low** or `tiles < animals` (Path C F7), and no blocked-MELON→WHEAT mapping. Default-crop-on-empty is keyed on the **tile**, not on the shed. **d0 leftover after the melon opening (~12) is WHEAT** — fact 36's bulk and this restock are not exclusive; an `if melon_opening: elif wheat` chain left 9 NW tiles empty on d0 (measured seed 0). Plant falls through to WHEAT when melon budget is exhausted. | season, every empty tile without a window occupant | `tape_profile.py` PLANT WHEAT within ~±3/day of tape from d0 (d0 itself > 0); `PLANT WHEAT` does not scale with herd size; `SELL WHEAT` > 0 by d2 | `choose_crop` / empty-tile plant: WHEAT is the fallback pick everywhere, including SW and NE, whenever no window occupant (27) claims the tile. `BUY_SEED WHEAT` follows plantings and emits **alongside** d0 `BUY_SEED MELON`, not behind it. | partial (no force-wheat; fact 38 plant half is home-only and d13+) |
| 23 | Never plant TOMATO. | season | `PLANT TOMATO` = 0 | `CROP_PLANTING_WINDOWS["TOMATO"] is None` / `choose_crop`. Independent of carrying the rest of the window gate as a fact. | true |
| 24 | Do not skip CARE to free crop turns. | daily | wool/milk sold does not collapse | `choose_unit_action`: no “skip CARE if STRAW ready / bonus ≥ 2” (Path C F5). | true |
| 25 | Do not mutate `WORK_TILES_PER_HAND` or inject forced extra `HIRE`s. | ever | no F6 spiral | `decide_hire_orders` stays work+ceiling+affordability. Facts 4 and 12 are *when* hires list relative to buys, not a density mutation. | true |
| 26 | Do not gate the n-th animal on `wheat ≥ reserve × (owned+1)` or `k × (owned+1)` cash. | buy days | calendar (15) still fires | no F8-class floor in `decide_animal_market_actions`. Soft `wheat_stock ≤ 0` as escape-prevention is allowed; a hard buffer before scale is not. | true |
| 27 | **STRAW is an early crop on home and the first extra, and the SW carpet is its second wave, not its only one.** Tape: STRAW plantings **d5 ≈4, d6 ≈8, d7 ≈4, d8 ≈4** on NW/NE, then the d11 carpet ≈15. STRAW first-yields 10 days out, so a d5 planting sells from ~d15 (tape `SELL STRAWBERRY` starts d15) and a d11 one from ~d21 — the early wave is where the season's strawberry money is. Carpet-only cost **−29.6k** contested on seed 0 (peak field 22 vs 34). **MELON is planted once, on d0 (12), and never replanted** — the old row's NE-refill-during-window put 31 extra melons in the ground on d7–11 that ripen into the market our own d10 wave just crashed, for **−5.3k on 23 extra seeds**. Not a pin of 50. **d5=1 is structural** (2 empty NW tiles, BUILD takes 1 for the pen — fights fact 16); do not judge d5 against half-tape. | d5–8 on NW/NE; d11 carpet on SW | `tape_profile.py` PLANT STRAWBERRY ≥ half the tape on **each** of d6–d8 (d5 is 1 by construction); d11 carpet still ≥14; **PLANT MELON after d0 = 0**; STRAW field peak ≥ 30 | empty-tile PLANT prefers STRAW on home/NE leftover d5–8 and on SW on the carpet day; MELON is a d0-only opening (fact 36) and is never re-preferred; WHEAT (22) fills whatever STRAW's seed budget does not. BUILD still beats PLANT (fact 16). **K units** may walk to first-extra empty when occupant is STRAW (d5–8); not a crew-wide walk (fact 42). | false |
| 28 | When a unit **stands on** empty leftover, it plants that quadrant's window occupant (STRAW d5–8 / d11 carpet per 27, CARROT d21–25) and otherwise **WHEAT** (fact 22) — tiles no longer wait empty between windows, which is what left SW producing nothing for most of the season. Do **not** walk the whole crew onto a far quadrant ahead of local first-water (that is the fact 40/42 escape mode, and it stays closed). | any quadrant; underfoot | SW `PLANT WHEAT` > 0 between windows; end SW weeds not a cascade; 0 escapes contested | `leftover_occupant` plus WHEAT fallback on every quadrant; no crew-wide walk to a far empty. | false |
| 29 | At most **K** units (start K=2) may work later-extra leftover in a turn **while SW is still locked** (before the engine day of the second `BUY_LAND`). Each plants only if it can water that tile before day end (`hour <= 21`: plant this hour, water next). After `PLANT`, WATER underfoot before walking to another empty. Everyone else keeps NE/home upkeep. On the **unlock day** (fact 32), K does not cap planters — full crew may carpet SW. Assignment, not hire-density (fact 25). | later extras; occupant windows; hour ≤ 21; pre-unlock only for K | d12 SW STRAW occupancy > 0 on seeds 0 and 8; each landed SW plant is watered the same day (0 night deaths from that day’s SW plants); NE STRAW > 0 by d8 (fact 27) without a crew-wide walk; NE weeds not a cascade vs ~5 at d12; d0 4/4; 0 escapes contested | `sw_slots` pre-unlock; K-unit later-extra empty walk after urgent water/harvest, **before** fert/weed; local WATER ignores `claimed`; refuse SW `PLANT` at `hour >= 22`. Unlock day uses fact 32, not `sw_slots`. | false |
| 30 | **STRAW seed cadence (unlock halves):** held STRAW must not sit at **0** across whole days while SW still needs seed — pre-unlock dribble so ≥1 `BUY_SEED STRAW` lands before unlock day, and when SW is unlocked with empty later-extra STRAW occupant, restock outranks MELON. **Widened by T1:** STRAW seed must also be held from ~d4 so fact 27's NW/NE d5–8 wave can land, not only for the SW carpet — the “dribble” is now a real early demand. Sized to **empty STRAW-occupant tiles** (cap ~8, tape d6), not `MAX_SEED_STOCKPILE=3`. Do **not** apply `MIN_CASH_RESERVE_FOR_SEED_BUYING` (450) — that MELON-trough floor is why d5 `buyS=0` at $527 with 5 empty NW tiles (need $550 for one $100 seed). Same-turn `plant_budget` credit, not only unlock morning. Not `straw_seed_supplement` (blunt always-buy). Not a STRAW pin. Do not reorder around the d5 cow (facts 10–13 stay). | d5–12; especially pre-unlock + d9–11 SW empty | `tape_profile.py` PLANT STRAW ≥ half the tape on **each** of d6–d8 (d5=1 structural); held STRAW > 0 on ≥1 turn/day in d5–10; ≥1 `BUY_SEED STRAW` before SW unlock day; with SW unlocked d9–11: held STRAW > 0 before first SW `PLANT` attempt; MELON restock does not block those buys | `fact30_wants_straw_seed` + `straw_wave_restock_quantity`: empty STRAW-occupant demand, no 450 floor; `plant_budget` credits same-turn `BUY_SEED STRAW`. | false |
| 31 | **SW unlock morning (market preamble):** on the engine day of the second `BUY_LAND`, hour-0 market sells **MELON then FERT** (fund the sprint), then bulk `BUY_SEED STRAWBERRY`, then hires; second `BUY_LAND` emits within ~1 hour using **post-sell** cash (pair with `land_first` reorder). v20 tapes: bulk **×23** on 9/10 tapes at tape d12 h0 (engine d11 h0); tape_5 uses ×5 but same shape. | engine day of 2nd `BUY_LAND`; hour 0–1 | on unlock day: `SELL MELON` + `SELL FERT` before bulk `BUY_SEED STRAW`; bulk ≥5 same day as 2nd `BUY_LAND`; land emits when post-sell affords even if pre-turn cash < reserve | `nikaangukia_meroni` market assembly: unlock-day sell block → seed bulk → hires → land; `_estimated_post_sell_cash` on `decide_land_orders`. | false |
| 32 | **SW carpet day:** on the engine day SW unlocks, plant STRAW on SW empty leftover until seed or window exhausted — **full crew**, not K-limited (fact 29). WATER underfoot same day for every landed plant (`hour ≤ 21`). v20 tape_0: **18** SW STRAW landings unlock day; 9/10 tapes bulk-buy then carpet same day. | 2nd `BUY_LAND` day; SW quadrant; hour ≤ 21 | SW STRAW occupancy EOD unlock day **≥14** (K=3; seed 0 hits 14 under $100 STRAW + land floor — do not waive land reserve to chase 15); sw_landed unlock day >> K; 0 night deaths from that day’s SW plants; d9–11 SW `plant_actions` > 0 once facts 30–31 hold | unlock-day bypass of `sw_slots`; crew already sized by facts 4/12/25 (no `WORK_TILES_PER_HAND` mutation); carpet outranks BUILD while STRAW budget remains; `plant_budget` credits the unlock bulk `BUY_SEED` | false |
| 33 | **Land timing:** first `BUY_LAND` engine **d6–7** preferred for NE (catch-up through **d10** if still NW-only); second engine **d11–12** (SW). Second purchase must not lose to same-turn animal spend (`land_first` + post-sell emit). SW must unlock with ≥1 STRAW-window day left (window ends engine d12). **No third buy (SE)** — v20 scale to ~14 animals runs on 3 quads; the $4k SE spend is not part of this shape. While NE is still pending, animal emits defer so the land drawer is not spent first. Counters tie facts 27–32 together. **First-buy reserve 0 is dropped** (28,751 / 36,766, herd 18 — same as the land-reserve bundle). Do not waive the $500 floor on either buy. | d6–10 and d11–12 | `sw_unlock_day` ≤ 11; straw-eligible days on SW ≥ 1; unlocked **= 3** by late season (not 4); 1st land d6–10; 2nd land d11–12; both seeds 0 and 8 pass fact 27/28/29/30 counters | `decide_land_orders` (`MAX_LAND_PURCHASES=2`, `LAND_PURCHASE_DAY_WINDOWS`) + `nikaangukia_meroni` land-before-animals; `pending_second_land` / unlock helpers stay keyed on the **2nd** buy; reserve priced against post-sell need, not raw pre-turn cash; first-buy floor stays 500. | false |
| 34 | **Mid-season MELON cash wave (sell):** MELON matures at `first_yield_day=10`. Engine **d9–12**, MELON sold into cash (not held for $180). HARVEST → unit inventory; SELL reads shed only. Contested bind: ripe/HIRE/HARVEST match v20 but held≈60 shed=0 → d10 `$0` vs v20 ~$15k. **Same-day path:** force-sell qty = shed+held; on **d10 hour≥16** (after feed), all carriers walk-to-shed and DROP capped to shed room minus wheat reserve (shared budget). Sell-cap 60 drains fruit. Uncapped/early DROP walk → escapes (shed flood or crew diversion). Other wave days: shed-adj DROP only. Fact 35 crew required. | engine d9–12 sell | vs `starter` 0+8: sold d9–11 ≥20; SELL on **d10**; 0 escapes; fact 32 ≥14; **contested 0+8:** d10 `SELL_MELON` `$` ≫ 0; day-10 MELON widen not ~−15k | force-sell shed+held; d10 h≥16 room-capped DROP walk; shed-adj DROP other wave days | false |
| 35 | **MELON-wave crew:** on cash-wave mornings when ripe MELON is on the board, `MIN_MONEY_TO_HIRE` must not strand the farm at **0 hires**. Contested seed 0: unlock bulk leaves ~$15 (< gate 20) on d10 with **6 ripe NW MELON** and hire=0 all day — only the farmer acts, one HARVEST at h23, bank stuck at $15 while v20 hires ~11 and dumps ~60. First hire costs $1; the flat $20 floor is mispriced against that (same pattern as the original hire-gate bug). Do not inject forced hires or mutate `WORK_TILES_PER_HAND` (fact 25). Re-check with cashflow: d10 MELON `$` still opens the contested gap after prior hire waiver. | d9–12, hour < `HIRE_BEFORE_HOUR`, when any MELON is harvestable | contested seed 0: d10 `HIRE` count > 0; d10 MELON `HARVEST` ≥ 3 (or MELON sold d10 > 0); 0 escapes; fact 32 unlock landed ≥14; fact 34 sell counters still hold vs `starter`; contested day-10 widen not dominated by missing `SELL_MELON` | `decide_hire_orders`: when `in_melon_cash_wave` and ripe MELON exists, skip `MIN_MONEY_TO_HIRE` — still stop when fib hire cost > money | false |
| 36 | **Early MELON acreage:** day-0 `BUY_SEED MELON` is sized to beach-head field scale (~12, tape/v20 opening), not `MAX_SEED_STOCKPILE=3`. Same-turn `plant_budget` credits the bulk so hour-0 plants land. After opening the farm is ~$0 (v20 too); until first extra land unlocks, wheat restock tops **1× owned** (daily feed) so fert income is not absorbed into `BUY_PRODUCT WHEAT` and land/hires can recover. NW plant via `choose_crop` when seed held. **MELON is a day-0 opening only** — rewritten fact 27 stops the NE refill during the window, which was buying 23 extra seeds to sell into our own crashed d10 market. Contested pre-36: field MELON EOD d5 ≈7 vs v20 ≈12. Not a STRAW pin; do not raise hire density (fact 25); do not truncate `BUY_ANIMAL` (fact 6). | engine d0 (opening); NW+NE through MELON window; wheat 1× until first land | vs `starter` and contested seeds 0+8: field MELON EOD d5 ≥12; d0 `BUY_SEED MELON` bulk ≥10 or `PLANT MELON` d0 ≥10; d0 4/4; 0 escapes; fact 32 unlock ≥14; fact 34 sold d9–11 ≥20; fact 35 d10 HIRE>0; **`PLANT MELON` after d0 = 0**; 1st land d6–7 | `decide_market_actions` / `melon_opening_restock_quantity`; `decide_animal_market_actions` wheat 1× pre-land; `nikaangukia_meroni` credits same-turn `BUY_SEED MELON` into `plant_budget` | false |
| 37 | **Surplus FERT sell — PARKED.** Contested gap harness showed us ~180 vs v20 ~2k FERT sold; that v20 figure is **order qty**, not executed (v20 collect ~346, oversized SELL orders). Throwaway already sells ~186 executed with existence-hold. Absorbable/stock-cap surplus caused **1 escape** (seed 0); market-list reorders to protect wheat **zeroed BUY_LAND**. Do not re-open without a new mechanism that keeps 0 escapes and land days. | — | — | parked | false |
| 38 | **FOLDED INTO FACT 22 (2026-09-05).** This row allowed product wheat only on home leftover, only from d13, and its own sell bar (≥200 exec) was parked as unreachable — correctly, because a d13+ home-only trickle *is* unreachable. The tape plants wheat everywhere from d0; that is fact 22 now, and the sell bar follows the crop rather than being chased on its own. Kept for the record and for its two live constraints: sell shed WHEAT only above the `owned ×` feed reserve (fact 18), and never force-plant from low stock. Original row: | NW leftover d13+ | (superseded — use fact 22's counters) | (superseded) | false |
| 38-orig | **Wheat as product (not feed flood):** v20 plants and sells WHEAT from early season (tapes: `BUY_SEED WHEAT` + `PLANT WHEAT` + `SELL WHEAT` dribbles). Contested we sell ≈ 5 vs v20 800–1600. Allow honest `choose_crop` / `BUY_SEED WHEAT` product path on **home (NW)** leftover when MELON does not claim the tile; sell shed WHEAT above `owned ×` feed reserve. Feed still `BUY_PRODUCT` (5, 18, 19). Do **not** force-plant from low stock, map MELON→WHEAT, or wheat-fill later-extra (28 waits empty between STRAW/CARROT). Fact 36 MELON d5 ≥12 still binds. **Plant half holds** (d13+ home-only; starter NW WHEAT 41/31). Fact 39 stopped STRAW refill. **Sell ≥200 PARKED as bank lever** (2026-09-05 cashflow): leftover + `owned×2` reserve cannot match v20’s ~130-plant wheat crop; even 200 units ≪ contested bank gap. | NW leftover d13+; sell above reserve; season | NW `PLANT WHEAT` > 0; SW WHEAT = 0; field MELON EOD d5 ≥12; d7–11 NE STRAW = 0; d0 4/4; 0 escapes; fact 32 ≥14; **do not chase** contested `sold_exec` ≥200 for bank | `wheat_product_restock_quantity` / home prefer after d12 melon window; refuse WHEAT off-home; `decide_market_actions` sells above reserve; later-extra leftover skip unchanged | false |
| 39 | **REWRITTEN 2026-09-05 — the “NW STRAW = 0” claim is withdrawn.** It was added to stop STRAW refilling melon-freed NW tiles ahead of a feed-safe wheat open, and it holds on `starter` (NW WHEAT 41/31), but on the tape NW/NE **is** where STRAW lands on d5–8 (fact 27) and the row is half of the −29.6k strawberry gap. What survives is only the part that was actually load-bearing: **home leftover never waits empty** — it takes the window occupant (STRAW d5–8, MELON only on d0) and WHEAT otherwise (fact 22). Feed still tops up via `BUY_PRODUCT`; still no force-wheat from low stock. The escapes that this row was patching came from *crew walks* (facts 40/42), not from what NW was planted with — fix those in fact 20/28, not by banning a crop. | home leftover, all season | NW `PLANT STRAW` > 0 on d5–8; NW `PLANT WHEAT` > 0 from d0; no NW tile empty for a whole day after d1; 0 escapes contested; contested STRAWBERRY `$` gap ≪ −29.6k | home plant: window occupant, else WHEAT; delete the “refuse STRAW on NW” branch and the wait-empty branch. | false |
| 40 | **STRAW drip sell — PARKED.** Contested STRAW season gap ~−20–28k. Tried fact-34-shaped held→DROP→SELL (d16+, force-sell shed+held, room-capped DROP). DROP was blocked by all-fed / feeder gates; when forced, diverted SW harvest and **worsened** season STRAW `$` (seed 0 −28k → −32k). Real bind is **acreage/timing**: peak field 22 vs 34 (seed 0) / 19 vs 42 (seed 8) — v20 plants NW+NE STRAW from d5; our 27/39 forbid that. Reopen only with a new acreage fact that does not fight 27/39, or a yield/fert lever on existing SW carpet. | — | — | parked | false |
| 41 | **Post-carpet SW STRAW fert — PARKED.** Tried elevating FERTILIZE before DIG when carpet done + SW wants fert + SW prefer_quadrant. FERTILIZE rose ~13→19/21 (seeds 0/8) but season STRAW `$` flat/worse (−28.8k→−29.6k / −19.6k→−21.7k); peak field unchanged 22|34 / 19|42. Yield lever on SW carpet does not close the acreage bind. Fact 42 NE carve also parked (escape). Helpers may remain in the throwaway. | — | — | parked | false |
| 43 | **Crew is sustained, not work-derived:** tape hires **4–5/day d0–d5**, then **8–11/day from d6 to the end** — the ramp lands the day the first extra quadrant does. Contested `tape_profile.py` shows the throwaway already within ±2 of this, so the row exists to stop a future edit trading it away (a fact-15 herd ramp with no crew to feed it is how the d11+ ramp produced escapes), not because it currently fails. Still no `WORK_TILES_PER_HAND` mutation and no forced hires (fact 25). | daily, before `HIRE_BEFORE_HOUR` | `tape_profile.py` crew row within ±2 of tape on every day; `MIN_MONEY_TO_HIRE` never strands a day at 0 hires (fact 35) | `decide_hire_orders` work+ceiling+affordability, with the ceiling following the tape ramp. | false (shipped is work-driven, ~6) |
| 42 | **Bounded NE STRAW after MELON wave — PARKED (superseded).** The mechanism it was reaching for is now fact 27 as rewritten; do not re-run *this* version (a mid-season crew walk onto NE), which escaped. Tried NE leftover STRAW d11–12 after the d10 wave (d7–10 stay MELON; no NW refill). Seed 0: **1 escape** (6a walk to NE stole feeders). d11–12 NE STRAW landings **0 / 1** (SW carpet ate seed; occupant=STRAW blocked opportunistic d12 choose_crop). Same crew-diversion failure as fact 40 DROP. Reopen only with a mechanism that does not walk the crew off feed. | — | — | parked | false |
| 44 | **The town is the demand schedule.** After the first shop (d3), produce what `unlocked_shops` eat; do not produce what they do not. **Count stays the calendar (15)** — shop mix picks *which* species, never *how many more*. No `YARN_STORE` → sheep stay at the day-0 beach-head (2); later slots are cows. `YARN_STORE` → existing yarn-heavy mix. Leftover STRAW/CARROT only while a shop consumes that crop; otherwise WHEAT (22). MELON/fert exempt (no shop / fact 9). Day 0 is still 2C2S (1) — no shop has opened. Not a sell-into-the-floor rule (that bind moved nothing). Not the d11+ count ramp. Not “hold the d11 burst” (shop reroll). Not d12h0 yarn slack (escapes). | d3+ buys; leftover plant | no-yarn seed: end `SHEEP` = 2 and `BUY_ANIMAL SHEEP` after d0 = 0; yarn seed: end `SHEEP` > 2; herd **count** is fact 15's ladder, cap 14; `PLANT STRAW` d6–8 ≥ half-tape when a straw shop is out (d5=1 structural); `PLANT CARROT` > 0 in the carrot window when `PET_CAFE`/`FARMERS_MARKET` is out; `PLANT TOMATO` = 0; d0 2C2S; 0 escapes contested; **contested bank not down** vs 40,806 / 34,567 | `shop_mix_target` + post-d0 `BUY_ANIMAL` follows mix at `calendar_owned_target`; `leftover_occupant(..., unlocked_shops)` | false |

**Tape index:** `mydocs/tape_transcripts/tape_0.txt` … `tape_9.txt`, `all_tapes_turns.csv`. Transcript **day N = engine day N−1** (tape d12 = engine d11).

## Timing card T1 — rewrite 9/15/17/21/22/27/28/39, add 43 (2026-09-05)

```text
Kind: rewrite (facts 9, 15, 17, 21, 22, 27, 28, 39) + add (43)
Was: five escape-defence rows that each moved the shape off the tape —
     herd held at 6 through d10 then ramped past the cap to 21;
     STRAW only as the d11 SW carpet; MELON refilled on NE d7–11;
     all feed wheat bought, tiles never planted with it; fert held for
     STRAW and never bought back; NW banned from STRAW and left empty.
     Every unit counter passed; contested bank fell 51k → 26k / 8k.
Now: each row names the tape's day and is checked with tape_profile.py.
     Herd 4/5/6/8/10/12/13/14 on d0/d2/d3/d6/d7/d8/d9/d10, then flat at
     14 (cap 14). STRAW d5–8 on NW/NE plus the d11 SW carpet. MELON d0
     only. WHEAT the default crop on any empty tile from d0. Fert sold
     daily from d1, bought back in tens to apply. Crew 4–5 then 8–11
     from d6.
Fights: the parked acreage/sell/fert patches (40, 41, 42) — they were
     buying back what these rows gave away; fact 38's d13+ home-only
     wheat (folded into 22); fact 39's NW STRAW ban (withdrawn);
     "hold 6 through d10" and the d11+ shop-mix ramp (both in 15)
Throwaway: experiments/_facts_v20.py (now tracked in git — commit per card)
Pre-run: facts 1–8, 10–14, 16, 18–20, 23–26, 29–36 still true in source;
     d0 pens/herd 4/4; 0 escapes **contested**, not only vs starter
Counters: tape_profile.py seeds 0+8 — crew ±2/day; herd ±1/day d0–d10 and
     ≤14 after; PLANT WHEAT within ±3/day from d0; PLANT STRAW ≥ half the
     tape on each of d6–d8 (d5=1 is structural); PLANT MELON after d0 = 0; SELL FERTILIZER no
     dry spell > 1 day. Then _trace_cashflow_v20.py: STRAWBERRY, WOOL,
     WHEAT-net and FERTILIZER gaps all smaller than −29.6k / −25.3k /
     −20k / −4.1k, and **contested bank up on both seeds**.
```

**Order of work.** The rows are one failure. Two fert-only landings
(sell-all + buy-back; surplus-above-6) asked 9+21 to hold the full-season
contested bank while 22/27/28/39 stayed on the escape-defence shape —
the BUY_LAND-at-fixed-crew error. The five-step + per-step bank kill
switch is withdrawn.

1. **Funding stack** — 9 + 21 + 22 + 28 + 27 + 39 is in the throwaway.
   Then the d5–d6 STRAW / wheat-d0 supplement and fact 44 (no-yarn
   sheep stay at 2). Banks **40,236 / 55,411** versus v20 **114k /
   133k**. Wheat d0 holds. Yarn lock stays (seed 8 +20,844 vs the
   pre-44 supplement). Hold-the-burst and d12h0 slack both failed —
   do not retry. The −570 self-nick is parked.
2. **STRAW d5–8 / STRAW `$` (27/30) — four supplements dropped.**
   Land-reserve bundle; seed-before-cow; leftover walk; d8 land-hour
   seed + hold-6 pin. Do not retry. d5=1 is structural (stop judging
   it against half-tape). Sequencing 27/30 before 15 was the Path C
   pattern (STRAW asked to hold the bank while 15 stayed false).
3. **15/17 align dropped (both binds).** Ladder: seed 0 −13k and
   STRAW 0. Cap 14 only: seed 8 −8.7k (yarn d13 +4 was load-bearing).
   Next ≠ those two. Re-judge STRAW `$` is still the hole, not
   another calendar open. Then wheat net. Then crew (43). MELON
   −3.2k and FERT −1.4k stay parked. Bank must not fall vs
   40,236 / 55,411.
4. **Fact 33 first-buy reserve dropped.** Waive $500 on the first
   `BUY_LAND` only: land [7, 11], STRAW 1/5/2/0, banks **28,751 /
   36,766**, herd 6 through d10 then **12 / 18**. Same pair as the
   bundle. STRAW `$` narrowed (−35.2k / −33.9k) and d7 us hit $0.
   Do not retry. Next ≠ another reserve waive, ≠ d6 wool DROP.
5. **Fact 20 harvest-before-collect dropped.** Land [7, 11], STRAW
   1/5/3/1, banks 39,690 / 55,210, seed 0 herd 18. Counters (sheep
   yld=0, wool 7, d7 land) held; bank bar did not. The nick was a
   shop-draw reroll, not the waive’s $0 dump. Do not retry.
6. **Rewrite 15/44 dropped — and it was the wrong idea.** Emitter
   replaced the calendar (38,649 / 46,533; herd 4 through d17). The
   direction we needed: keep the tape calendar; produce funds it; a
   miss names the inflow, then rearrange that activity. Next ≠ the
   emitter-rewrite, ≠ freeze-until-milk, ≠ first-land without d6.
7. **Collect-then-harvest dropped.** Inflow held (yld=0, wool 7,
   land [7, 11]). Ungated walk −203 / +5,719 with 1 escape; Stage 2
   +11,783 / +5,719 still 1 escape; unfed gate 0 dips but
   **39,587 / 52,878**. Same shop-draw class as harvest-before-
   collect (STRAW d7 0→3). Do not retry.

## Produce funds the calendar — collect-then-harvest (2026-09-07) **← failed, reverted**

```text
Kind: supplement (facts 15, 33; 44 rider) — dropped
Was: after COLLECT, HARVEST only if yield >= max_held-2 (sheep=4);
     yield=3 sits through d7; d7 post-sell $1,374 vs $1,500;
     land [8, 11]
Tried: COLLECT still first; HARVEST at any yield>0; walk-back
     above K-STRAW. No d6 DROP, no day-gate rewrite, $500 stayed.
     Stage 2: no-yarn mix table cows 10/8 not cap-2 (yarn left
     the early draw). Unfed gate on the walk (1 cow escaped).
Result: inflow held (sheep yld=0 d6 EOD; shed wool 7 d7h00);
     land [7, 11]; STRAW 1/5/3/1; MELON after d0=0.
     Stage1: 40,033 / 61,130 (−203 / +5,719); seed 8 1 escape
     d24. Stage2: 52,019 / 61,130; seed 0 10C4S=14; seed 8
     still 1 escape. Unfed-gated walk: 39,587 / 52,878
     (−649 / −2,533); 0 dips; seed 0 yarn d12 restored.
Now: revert. Do not retry collect-then-harvest, harvest-before-
     collect, no-yarn cap-fill cut, freeze-until-milk, land
     without d6, first-buy waive, d6 wool DROP, ladder, cap 14.
Fights: d7 land vs shop-draw (20); harvest-walk vs feed (20)
Throwaway: experiments/_facts_v20.py (reverted)
Counters: land [8, 11]; wheat d0; MELON after d0=0; STRAW d6
     half-tape; bank 40,236 / 55,411
```

## Shop + post-sell emit the calendar (2026-09-07) **← failed, reverted**

```text
Kind: rewrite (facts 15, 44) — dropped
Was: calendar_owned_target(day) buys; shop_mix picks which inside
     that count; land windows by engine day; no-yarn fills cows to 18
Tried: post-d0 BUY_ANIMAL iff shed wool+fert post-sell covers it AND
     a shop eats the product; mix-table cow count not cap-2; first
     land when shed wool+fert vs $1,500, not day >= 6. $500 floor
     stayed. Not harvest-before-collect, not waive, not ladder, not
     cap 14.
Result: banks 38,649 / 46,533 (−1,587 / −8,878). 0 dips. MELON after
     d0=0; wheat d0=7. Seed 0: herd 4 through d17 then 10 (8C2S);
     land [7, 11]; STRAW 5/4/12/4; yarn lost (shops rerolled). Seed 8:
     land [8, 11]; STRAW 1/5/0/1; yarn d21; end 10C4S=14; cow_d13+=0.
Now: revert. That bind replaced the emitter; the direction is
     produce-funds-the-calendar (see card above). Do not retry
     freeze-until-milk or first-land without the d6 day floor.
Fights: hold-6 cows need a slot before milk is in the first 3 shops;
     d7 land + extra NE STRAW is the same shop-draw reroll as
     harvest-before-collect.
Throwaway: experiments/_facts_v20.py (reverted)
Counters: land [8, 11]; wheat d0=7; MELON after d0=0; STRAW d6
     half-tape; bank 40,236 / 55,411
```

## Fact 20 harvest-before-collect (2026-09-07) **← failed, reverted**

```text
Kind: supplement (fact 20) — dropped
Was: HARVEST only if yield >= max_held or >= max_held-2; sheep (4,4)
     holds 3 wool through d7; d7 post-sell $1,374 vs $1,500; land [8, 11]
Tried: underfoot HARVEST if yield_units > 0, before COLLECT. $500
     reserve stayed. Not d6 wool DROP, not waive, not calendar.
Result: both sheep yld=0 d6 EOD; wool d7 4→7; land [7, 11]; STRAW
     1/5/3/1; wheat d0=9; MELON after d0=0; 0 dips. Banks 39,690 /
     55,210 (−546 / −201). Seed 0 end herd 18; seed 8 end 14.
     d7h01 leftover $573 (not the waive's $0). Dump still came.
Now: revert. Do not retry harvest-before-collect, first-buy waive,
     the bundle, d6 wool DROP, ladder, cap 14.
Fights: 15 (d11+ dump once land is d7)
Throwaway: experiments/_facts_v20.py (reverted)
Counters: land [8, 11]; wheat d0; MELON after d0 = 0; STRAW d6
     half-tape; bank 40,236 / 55,411
```

## Fact 33 first-buy reserve (2026-09-06) **← failed, reverted**

```text
Kind: supplement (fact 33) — dropped
Was: land [8, 11]; d7 post-sell $1,374 vs $1,500 floor
Tried: first-buy reserve 0 in decide_land_orders (n_extra == 0).
     Second buy kept $500. Not the bundle, not d6 wool DROP.
Result: land [7, 11]; STRAW 1/5/2/0; wheat d0=7; MELON after d0=0;
     d11 carpet 15; 0 escapes. Banks 28,751 / 36,766. Herd 6
     through d10 then 12 / 18. d7 us $0. STRAW $ −35.2k / −33.9k
     (narrowed) but milk/wool/melon/fert widened. Same banks as
     the dropped land-reserve bundle.
Now: revert. Do not retry first-buy waive, the bundle, d6 wool
     DROP, ladder, cap 14, seed-before-cow, leftover walk,
     land-hour seed.
Fights: 15 (d11 dump once land is early); bank bar
Throwaway: experiments/_facts_v20.py (reverted)
Counters: land [8, 11]; wheat d0; MELON after d0 = 0; STRAW d6
     half-tape; bank 40,236 / 55,411
```

## Fact 15/17 throwaway align (2026-09-06) **← both binds failed, reverted**

```text
Kind: remove (throwaway hold-6 + d11 ramp) — dropped
Was: calendar holds 6 through d10, then 12 / MAX_ANIMALS=18
Tried: (1) tape ladder + cap 14 — seed 0 27,204 (−13,032), seed 8
     65,431. Land [7, 11]. STRAW d5–8 → 0/0/0/0 and 0/0/1/0.
     (2) cap 14 only, hold-6 kept — seed 0 43,361 (+3,125), seed 8
     46,746 (−8,665). Land [8, 11]. STRAW 1/5/0/1. Herd 14/14.
Now: revert both. Throwaway back on hold-6 + MAX_ANIMALS=18.
     Written 15/17 stay the spec. Do not retry the ladder without a
     fact-33 land/deferral bind. Do not retry cap 14 alone (yarn
     seed 8's d13 +4 is load-bearing vs 55,411).
Fights: opening the ladder while land is d8; cutting yarn seed 8 to 14
Throwaway: experiments/_facts_v20.py (reverted)
Counters: land [8, 11]; wheat d0; MELON after d0 = 0; STRAW d6
     half-tape; bank 40,236 / 55,411
```

## Fact 30 d8 land-hour seed + hold-6 pin (2026-09-06) **← failed, reverted**

```text
Kind: supplement (fact 30) — dropped
Was: d8h00 SELL FERT | BUY_LAND (NE still LOCKED, buyS=0). d8h01 cow
     catch-up + BUY_SEED STRAW ×6; cow takes the ~$703 drawer; pltS=1.
Tried: land-hour BUY_SEED STRAW ×7 sized to post-land cash (pending
     LOCKED NE counted); list after land before hires; calendar stays
     6 until owned>=6.
Result: d8 plants 1→3 both seeds (half-tape). Land [8,11]; wheat d0=7;
     MELON after d0=0; d11 carpet 15. Seed 0 bank 40,646 (+410),
     STRAW gap −35.0k (was −43.5k). Seed 8 bank 34,287 (−21,124).
     The 6th animal still lands d10, so the pin releases and d11
     opens: herd 6 through d10 then 12 / 14 (seed 0) and 12 / 18
     (seed 8). Same dump class as seed-before-cow. Do not retry.
Now: revert. Next ≠ land-hour seed, ≠ hold-6-until-owned pin, ≠
     list reorder, ≠ land-reserve waiver, ≠ leftover walk.
Fights: 15 (d11 open once the 6th exists); seed 8 bank
Throwaway: experiments/_facts_v20.py (reverted)
```

## Fact 27 home leftover walk (2026-09-06) **← failed, reverted**

```text
Kind: supplement (fact 27) — dropped
Was: K units walk to first-extra empty (incl. LOCKED pending NE) when
     occupant is STRAW d5–8. On d7 that walk goes onto LOCKED NE while
     1 empty NW sits all day (heldS=1) and pltS = 0/4.
Tried: K-walk home leftover before first-extra. Ungated: d7h23 plant
     dies overnight; d8 pltS 1→0; banks 32,928 / 63,418. Hour-21
     arrive/water gate: d7 plant stays 0 (walk sits behind all-fed);
     pltS back to 1/5/0/1; banks 23,735 / 44,211.
Now: revert. Walk-after-feed cannot plant-and-water the sitting NW
     the same day. Raising it above FEED reopens 40/42. Do not retry.
Fights: 20 (all-fed before leftover walk); 7 (h23 night death)
Throwaway: experiments/_facts_v20.py (reverted)
```

## Fact 44 WHEN supplements (2026-09-06) **← both failed**

```text
Kind: supplement (fact 44) — both arms reverted
Was: no-yarn lock fills the whole d11 cap-12 burst with cows (after
     carpet, ~h13); yarn first visible d12h0 with slots already 0;
     extra sheep wait until d13. Seed 0 −570 vs live 40,806.
Tried:
  1. Hold calendar at 6 on d11, spend the burst on d12. Failed —
     different d11 None-tiles change `_spawn_weeds` RNG calls before
     the shop draw; yarn vanished; both seeds dumped to 18;
     25,417 / 34,074.
  2. Spend the d11 burst; open calendar to 14 once yarn is visible
     so extra sheep emit d12h0. Failed — yarn held, sheep landed
     d12, seed 8 no-op at 55,411, but seed 0 owned 14→13 twice
     (escapes) and bank 36,885 (−3,351 vs fact 44).
Now: leave fact 44 as written. Do not retry hold-the-burst or
     d12h0 slack. Next ≠ those two, ≠ leftover, ≠ hold-2, ≠ herd.
Fights: 7 (escapes); shop draw (weed-RNG); d11+ count dump
Throwaway: experiments/_facts_v20.py (reverted)
```

## Scale card B — rewrite 15/17/33 (2026-09-04) **← closed**

```text
Kind: rewrite (facts 15, 17, 33) — scale animals; land stays 2 buys
Was: MAX_ANIMALS=8; calendar holds 6 through d8; end placed 7–8;
     MAX_LAND_PURCHASES=2 (then briefly raised to 3 / SE — dropped)
Now: season ceiling = shop-mix total (14/18); hold 6 through d10;
     d11+ shop-mix toward 12 then cap; MAX_LAND_PURCHASES=2 (NE+SW only,
     no SE — matches v20 14-on-3-quads measure); land-before-animals
Fights: pre-SW d7 dump toward 10; SE $4k after carpet (dropped);
     fact 26 k×(owned+1); WORK_TILES mutation
Throwaway: experiments/_facts_v20.py
Pre-run: every other row still true; d0 4/4; fact 32 ≥14; 0 escapes
Counters: seeds 0+8 vs starter: d7 BUY quiet; EOD d18 owned≥12;
     end herd≥12; sw_unlock≤11; land1 d6–10; land2 d11–12;
     unlocked==3 (not 4); facts 34–36 still hold; then _facts_v20_gap.py
```

**Result:** 36/36 clear. Contested seed 0 ~45k (no SE) vs ~6k (with SE).
Fact 37 tried and **parked** (session below). Next: fact 38.

## Fact 37 — surplus FERT sell (2026-09-04) **← PARKED**

```text
Kind: add (fact 37) — PARKED after throwaway attempts
Was: hold whole shed FERT while any live STRAW exists
Tried: absorbable-demand surplus; stock-cap surplus; wheat/land slot
     reorders on the non-buy market list
Result: absorbable surplus → 1 escape seed 0, SELL≈169 (existence-hold
     already SELL≈186, 0 escapes). Stock-cap alone → early fert held →
     BUY_LAND never fires. Market reorders → unlock=None / 8–24 escapes.
     Contested “v20 sold 2k FERT” is order-qty inflation (collect≈346).
Now: leave fact 9 existence-hold; do not port. Next contested lever is
     fact 38 (wheat product) or remeasure executed FERT/WHEAT vs v20.
Fights: 7 (escapes), 33 (land), 19 (wheat vs 10-slot)
Throwaway: experiments/_facts_v20.py (reverted)
```

## Fact 38 — wheat as product (2026-09-04) **← PARTIAL (sell ≥200 PARKED)**

```text
Kind: add (fact 38); supplement (fact 22 wording — product ≠ force)
Was: no force-wheat (22) + leftover later-extra wait-empty (28) left
     product WHEAT near zero; contested SELL WHEAT ≈ 5 vs v20 856–1,648
Tried: d13+ home-only BUY_SEED sized to NW empties + prefer WHEAT when
     seeded; refuse WHEAT off-home; sell above owned×reserve (unchanged).
     d12 open / fact30 override → seed 0 escape + d18 herd 11.
     Fact 39 stopped STRAW refill (starter NW WHEAT 41/31, NW STRAW=0).
     Sell-path probe: reserve pegs shed; best starter exec 34 ≪ 200;
     v20 plants ~130 wheat. Cashflow: even 200 units ~$5–10k vs ~$50–100k
     contested bank gaps.
Now: plant half holds. **Sell ≥200 PARKED as bank lever** — leftover
     shape cannot match v20 wheat crop; not the next edit.
Fights: Path C F7 force-wheat; fill-priority 1a; SW wheat-fill (28); early
     open fights 7/15
Throwaway: experiments/_facts_v20.py
Pre-run: facts 1–36 + 39 starter claim; d0 4/4;
     field MELON d5 ≥12; fact 32 ≥14; SW WHEAT = 0; 0 escapes; NW STRAW=0
Counters: NW PLANT WHEAT > 0 (hold); SW WHEAT = 0 (hold); starter audit
     CLEAR; sold_exec ≥200 not a bank success bar
```

**Superseded 2026-09-05 (timing card T1).** The sell bar was unreachable
because the plant half was: a d13+ home-only trickle cannot produce 200
units. Fact 22 now plants wheat everywhere from d0 and the sell volume
follows the crop. Do not port `main.py`.

## Fact 39 — NW post-MELON leftover claim (2026-09-05) **← holds starter**

```text
Kind: add (fact 39); supplement (fact 30 unlock halves only)
Was: fact 30 home-NW STRAW seed-habit (d5+) plus choose_crop STRAW refill
     melon-freed NW tiles before fact 38’s feed-safe d13+ wheat open;
     contested sold_exec WHEAT ≈ 9 ≪ 200. Blunt d12 wheat / full fact30
     override → escape (fact 7/15).
Now: after MELON no longer claims home leftover, home (NW) empty
     leftover waits empty or takes product WHEAT (fact 38 d13+) — not
     STRAW refill. Keep fact 30 load-bearing halves: held STRAW > 0 before
     SW unlock; SW empty → STRAW (facts 27/31/32). Feed still BUY_PRODUCT;
     no force-wheat from low stock; no SW/NE wheat-fill; MELON d5 ≥12.
Fights: Path A gate paste; Path C STRAW pin; blunt fact30 kill; d12
     wheat without feed-safe gate
Throwaway: experiments/_facts_v20.py
Pre-run: facts 1–36 + 38 plant half; d0 4/4; 0 escapes; land [7,11];
     unlock ≥14; MELON d5 ≥12; SW WHEAT = 0; fact 30 pre-unlock
     BUY_SEED STRAW still lands
Counters: starter NW STRAW=0; NW WHEAT 41/31 (was ~10–17); fact 30
     unlock halves hold; fact 38 sell bar parked (not this row’s job)
```

**Superseded 2026-09-05 (timing card T1).** The starter claim held and the
contested bank fell anyway: banning STRAW from NW is half the −29.6k
strawberry gap. The card below is kept as the record of how a `starter`-
only judge blesses a losing row.

**Starter clear (2026-09-05):** NW STRAW=0; NW WHEAT 41/31; 27/27 source,
74/74 counter; fact 30 pre-unlock buys still land. Fact 38 sell ≥200
parked as bank lever. Do not port `main.py`.

## Fact 40 — session card (2026-09-05) **← PARKED**

```text
Kind: add (fact 40) — PARKED after throwaway attempts
Was: contested STRAW gap ~−20–28k; d21 held≈20 shed=0 while v20 sells
Tried: fact-34-shaped force-sell shed+held + DROP walk (all-fed / feeder
     soft / unconditional h≥14 / late h≥20)
Result: when DROP actually fired, season STRAW $ worsened (seed 0
     −28k → −32k) — harvest diversion / contested dump. Acreage bind:
     peak field 22|34 and 19|42; v20 NW+NE STRAW from d5 (fights 27/39).
Next (superseded): 41 fert then 42 NE carve — both parked. Not more DROP.
Throwaway: experiments/_facts_v20.py (reverted)
```

## Fact 41 — post-carpet SW STRAW fert coverage (2026-09-05) **← PARKED**

```text
Kind: add (fact 41) — PARKED after throwaway measure
Was: fert errand below DIG/weed; FERTILIZE ≈13–14/season on SW carpet
Tried: sw_straw_wants_fert + fact41_post_carpet_fert; DIG skip when
     post-carpet; prefer_quadrant=SW on find_fertilizer_target
Result: audit CLEAR (28/28 source, 74/74 counter, 0 escapes).
     FERTILIZE 19/21 (↑) but season STRAW $ worsened slightly
     (−28.8k→−29.6k / −19.6k→−21.7k); peak field unchanged 22|34 / 19|42.
Now: park. Helpers remain in throwaway (harmless). Fact 42 NE carve
     also parked (escape). Next ≠ more fert or NE walk.
Fights: none of 27/39 (held); yield alone ≠ acreage bind
Throwaway: experiments/_facts_v20.py
```

## Fact 42 — bounded NE STRAW after MELON wave (2026-09-05) **← PARKED**

```text
Kind: add (fact 42); supplement (fact 27) — PARKED
Was: NE leftover MELON through window; opportunistic d12 STRAW ~3–4
Tried: leftover_occupant NE → STRAW d11–12; restock; 6a walk after carpet
Result: seed 0 escape (feed walk stolen); d11–12 NE STRAW 0/1; SW carpet
     ate seed; occupant=STRAW blocked d12 choose_crop fallback.
Now: revert throwaway. Next = contested WOOL `$` (not another NE walk).
     STRAW acreage vs 27/39 accepted for now.
Fights: 7 (escapes); 27 d7–11=0 if walk fires early; 20 feed-first
Throwaway: experiments/_facts_v20.py (reverted)
```

## Fact 36 — session card (2026-09-04)

```text
Kind: add (fact 36)
Was: MELON restock follows MAX_SEED_STOCKPILE=3; d0 buys ~3; field MELON
     EOD d5 ~7 contested; NE empty leftover often unplanted (no seed)
Now: day-0 (opening) BUY_SEED MELON sized to beach-head acreage (~12);
     same-turn plant_budget credit so bulk lands as PLANT; until first
     extra land, wheat restock is 1× owned so fert income recovers toward
     land/hires (v20 also opens broke). NW+NE prefer MELON when seed held.
     Not a STRAW pin; not raise hire density.
Fights: none of 1–35 if order-cap (6) and wheat reserve (5) still hold;
     do not blunt always-buy STRAW; do not waive land reserve
Throwaway: experiments/_facts_v20.py
Pre-run: every row still true in source (esp. 6, 27–35)
Counters: contested (and vs starter) seeds 0+8: field MELON EOD d5 ≥12;
     d0 BUY_SEED MELON bulk lands (≥10) or PLANT MELON d0 ≥10;
     d0 4/4; 0 escapes; fact 32 unlock ≥14; fact 34 sold d9–11 ≥20;
     fact 35 d10 HIRE>0; d7–11 NE STRAW = 0
```

## Fact 35 — session card (2026-09-04)

```text
Kind: add (fact 35)
Was: MIN_MONEY_TO_HIRE=20 blocks all d10 hires when unlock leaves ~$15;
     6 ripe MELON sit unharvested (contested: HARVEST=0 until h23)
Now: during MELON cash wave, if any MELON is harvestable, waive the flat
     hire floor — still afford each fib hire from remaining money
Fights: none; does not force-hire or change WORK_TILES_PER_HAND (fact 25);
     does not reorder harvest above FEED (fact 34 lesson)
Throwaway: experiments/_facts_v20.py
Pre-run: facts 1–34 hold; d0 4/4; fact 32 ≥14; 0 escapes
Counters: contested seed 0 d10 HIRE>0; d10 MELON HARVEST≥3 or sold d10>0;
     starter fact 34 still ≥20 sold d9-11; then _facts_v20_gap.py
```

**2026-09-05:** hire waiver may hold unit counters while contested day-10
`SELL_MELON` `$` still opens ~−15k vs v20 — re-diagnose with
`_trace_cashflow_v20.py` before another supplement.

## Fact 34 — session card (2026-09-04; supplement 2026-09-05)

```text
Kind: supplement (fact 34) — same-day held→DROP→SELL
Was: d9–12 force-sell shed only; DROP only if already shed-adj + all fed;
     contested d10 ripe=12 HIRE/HARV≈v20 but held≈60 shed=0 → SELL_$=0
     (~−15k widen); d11 auto-drop sells into crashed price
Now: force-sell qty = shed + Σ unit-held; d10 hour≥16 after all-fed,
     carriers walk-to-shed; DROP shared-capped to shed room − wheat
     reserve; MELON_CASH_WAVE_SELL_CAP=60. Early/uncapped DROP → escapes.
Fights: pre-feed MELON walk; prefer-MELON-over-water; uncapped DROP flood
Throwaway: experiments/_facts_v20.py
Pre-run: every row still true; d0 4/4; fact 32 ≥14; 0 escapes; fact 35/36
Counters: starter sold d9–11 ≥20 + SELL on d10 + 0 escapes; contested 0+8:
     d10 SELL_MELON gap ~−1.7k/−3.1k (was ~−15k); cashflow tracer
```

## SW recipe — session pickup cards (2026-09-02)

**Closed 2026-09-04** in `experiments/_facts_v20.py` (all 36 facts clear;
34–36 = MELON wave sell/hire + early acreage; 15/17/33 = animal scale on
2 land buys / 3 quads, **no SE**). Cards A–D below are historical pickup
notes. Scale card B is closed — see session card above. Port throwaway →
`main.py` only with explicit go.

Paste one card per throwaway edit. Source: tape transcripts + seed-0 trace vs `_facts_v20.py`. Do not patch shipped `main.py` until counters hold.

### Card A — supplement fact 30 (seed cadence) **← start here**

```text
Kind: supplement (fact 30) — new row
Was: STRAW seed restock follows MELON `choose_crop` / generic restock; held STRAW = 0 d9–11 while SW unlocked
Now: from engine d5, dribble `BUY_SEED STRAW` (1–3) when window open and affordable; when SW unlocked and later-extra STRAW occupant empty, STRAW restock outranks MELON restock that turn
Fights: straw_seed_supplement (blunt patch); STRAW pin; fact 22 wheat-fill
Throwaway: experiments/_facts_v20.py
Pre-run: facts 27–29 unchanged; land_first + post-sell emit still on
Counters: held STRAW > 0 d9–11; d9–11 SW plant > 0; ne STRAW d7–14 = 0; sw landed ↑ vs current; both seeds 0 and 8
```

### Card B — supplement fact 31 (unlock morning)

```text
Kind: supplement (fact 31) — new row
Was: unlock-day market = hires/seeds/land like any other day; no bulk STRAW buy; no sell-first preamble
Now: 2nd `BUY_LAND` day h0: SELL MELON + SELL FERT → BUY_SEED STRAW bulk (target 23, afford-scaled) → hires → BUY_LAND (post-sell emit + land_first)
Fights: fact 9 hold-fert (sell on unlock is deliberate funding, not liquidation); defer_d9_cash
Throwaway: experiments/_facts_v20.py
Pre-run: fact 30 holds (seed path works without bulk alone)
Counters: bulk STRAW buy same day as 2nd BUY_LAND; SELL MELON before bulk seed; sw landed unlock day ≥15; 0 night deaths
```

### Card C — supplement fact 32 (carpet day)

```text
Kind: supplement (fact 32) — new row; supplement fact 29 (K pre-unlock only)
Was: K=2 caps all later-extra work; unlock day lands ~7 SW STRAW
Now: K limit until unlock day; on unlock day full crew may PLANT/WATER SW (fact 29 K bypass)
Fights: raising K globally; hire-density (fact 25)
Throwaway: experiments/_facts_v20.py
Pre-run: facts 30–31 hold (seed on unlock day)
Counters: sw landed unlock day ≥15; water/planted = 1.0 for that day’s SW plants; d7–11 NE STRAW = 0
```

### Card D — verify fact 33 (land timing)

```text
Kind: verify (fact 33) — mostly implemented (land_first + post-sell emit)
Was: 2nd BUY_LAND d11; SW idle d9–11 for seed not land
Now: confirm sw_unlock_day ≤ 11 and straw-eligible days ≥ 1; tune unlock day d11 vs d12 if bulk preamble needs the hour
Fights: raw defer_d9_cash; reserve ladder (dead)
Throwaway: experiments/_facts_v20.py
Pre-run: cards A–C
Counters: sw_unlock_day; straw-eligible days; fact 27/28/29 counters both seeds; then 12-seed H2H vs main
```

**Implementation order:** A → B → C → D. **Do not** re-run 12-seed until A counters pass on seeds 0 and 8.

## Open hole (not a fact yet)

**The hole is T1 versus v20 (~75k), led by STRAW `$` (−43.5k /
−38.7k) and the d7/d8 half-tape miss** (d5=1 is structural). Fact
44's −570 is a self-nick versus 40,806, not a v20 stream — parked.
Two WHEN binds on the d11 burst stay dropped (shop reroll; escapes).
15/17 throwaway align is dropped (ladder and cap-14 both failed
a seed). Fact 33 first-buy reserve is dropped (same dump as the
bundle). Re-judge STRAW `$` is still the hole, not another
reserve waive or calendar open.

After T1, and only after: later-extra CARROT d21–25 (tape plants ~7 over
d21–27), post-d12 STRAW harvest slices (`docs/PUBLIC_META.md`
STRAWBERRY-6), and the order-book timing edge that `PUBLIC_META.md`
measures — in the 1700–1900 band 80% of matches are decided by under
5,000 bank, so selling a step or three early is worth more there than
yield. That is stage 2; T1 is stage 1 and is worth ~85k on seed 0
against v20's ~5k, so it goes first.

K is a knob only after the duty cycle holds. A STRAW pin of 50 is still
Path C and still fights 1–3. **Do not merge Path A** (shipped crop-first
`main.py`) into this table. SE / 3rd `BUY_LAND` is Dropped. Tools:
`tape_profile.py` (timing, run first), `_trace_cashflow_v20.py`
(dollars), `_trace_straw_wool.py`, `_trace_d10_melon.py`.

## Dropped (cannot coexist with this table)

Do not re-add without removing the rows they fight.

| Dropped | Fights | Why |
|---|---|---|
| Path A gates pasted onto animal-first buy/build/sell | whole table | Crop-first and animal-first cannot share the same gates (Path C mode). Path A **is** shipped `main.py`. |
| First-buy land reserve waive (fact 33 one-bind) | 15, bank | Same 28,751 / 36,766 / herd 18 as the land-reserve bundle. Land [7, 11]; d7 us $0; d11 dump. STRAW `$` narrowed and still failed the bank bar. |
| SE / 3rd `BUY_LAND` ($4k) | 33, cash after carpet | v20 scale runs on 3 quads; with-SE contested seed 0 bank ~6k, no-SE ~45k. Re-add only with a new fact card + contested proof. |
| MELON walk-to-shed **before/during feed** or uncapped multi-day DROP | 7, 18–20, 34 | Pre-feed / uncapped DROP starved herd or flooded shed. Fact 34 keeps **d10 hour≥16 room-capped** DROP only. |
| STRAW held→DROP→SELL drip (fact 40) | STRAW `$` | When DROP fired, season STRAW `$` worsened (harvest diversion). The acreage it was compensating for is now fact 27 as rewritten. |
| Hold the d11 cap-12 burst until yarn is known | 44, 7 | Different d11 empty-tile count changes `_spawn_weeds` RNG calls before the shop draw; yarn vanished; both seeds dumped to 18 (25,417 / 34,074). |
| Open two slots on d12h0 once yarn is visible | 7, 44 | Sheep land d12 and seed 8 is a no-op, but seed 0 escapes (owned 14→13 twice) and bank 36,885. |
| Post-d10 animal buying of any kind (the old d11+ shop-mix ramp) | 15, 17, 7 | Bought 21 head against an 18 cap contested and still lost placed animals late (18 → 16, d25–27): the late herd arrives with no wheat behind it. Policy ceiling is 14 / no d11+ *ramp* — not a tape claim. 5/10 tapes buy after engine d10 (usually +1 sheep on d11); live v20 on seeds 0/8 buys +2 on d11 to reach 14. |
| Pause buys until STRAW threshold / day 12–15 | 1–3, 15 | Straw-first pause: −20,707, 2/12; STRAW plantings went *down*. |
| Scale only after `straw_tiles ≥ 50` | 15 | Calendar is day 3/5/7, not carpet-done. |
| Apply fert to STRAW; gate `SELL FERT` while STRAW wants it | 8–11 | Day-3 cow is sized to selling ~4 fert. |
| Holding collected fert for STRAW (the fact 9 existence-hold) | 9, 21 | Break-even round trip, so the hold is pure foregone liquidity in the days that buy the herd: −4.1k contested. Fact 37's surplus valves were leaks around this hold and are moot once it is gone. |
| Hold fert until liquidation and also buy more | 9, 21 | Shipped Path A. Fact 21 now buys fert *to apply*, in tens, which is not this. |
| Force-wheat from low stock / MELON→WHEAT fallback / melon-pause wheat cycle | 22, early MELON | F7 / F12. Fact 22's default-crop-on-empty is keyed on the tile, not the shed — that is the difference, and it is the whole difference. |
| MELON replanted after day 0 | 27, 34, 36 | 23 extra seeds ripening into the market our own d10 wave just crashed: −5.3k contested while spending 2.4x v20 on melon seed. |
| Price-blind MELON→CARROT→WHEAT fallback | 22 | Fill-priority 1a. |
| STRAW/MELON tile-share *caps* as a way to grow a carpet | — | A cap is a ceiling, not a floor (1b). |
| `CROP_PLANTING_WINDOWS` as the crop spec | 22 | Replay-shaped; lost via wheat filler. TOMATO-never (23) is the only row kept. |
| Mechanically true `growth_days` / `occupancy_kind` as a score patch | — | More accurate, worse ranking (STRAW 14→0). |
| `k × (owned+1)` cash/wheat floor | 15, 26 | F8 strands the herd. |
| Path C / “port Path A” | whole table | Path A **is** shipped `main.py`. Path C parked 6/12. |

## Pre-run audit

Before any episode, read the throwaway against this file. If a row is
`false` in source, the run is not a test of this shape.

**Run `experiments/tape_profile.py` on both seeds before the episode's
bank means anything.** A row whose day is off the tape is a failing row
even when its own yes/no counter passes — that is what this section
missed for seven sessions.

Minimum checks that caught the last two throwaways:

- [ ] Fact 2: `choose_animal_to_build` does not use animal-purchase cash for a build
- [ ] Fact 5 / 18: wheat sell reserve counts **owned**
- [ ] Fact 15: herd ladder 4/5/6/8/10/12/13/14 on d0/d2/d3/d6/d7/d8/d9/d10, flat after; no post-d10 buying; prefix still not all-or-nothing
- [ ] Facts 9–13: the turn `BUY_ANIMAL` emits is sell fert → buy animal → (hire/seeds after), including catch-up hours; on every other day fert still sells the day it is collected (fact 9 — no existence-hold)
- [ ] Fact 27: STRAW lands on NW/NE d6–8 at ≥ half-tape **and** as the d11 SW carpet (d5=1 structural); `PLANT MELON` after d0 = 0
- [ ] Fact 28: leftover is planted underfoot — window occupant, else WHEAT (fact 22); no tile waits empty between windows; no crew-wide walk to a far quadrant
- [ ] Fact 29: at most K=2 units walk/plant later-extra **pre-unlock**; unlock day bypasses K (fact 32); local WATER ignores claimed; no SW `PLANT` at hour ≥ 22
- [ ] Fact 30: held STRAW > 0 before SW unlock; SW empty → STRAW restock (not post-MELON home refill)
- [ ] Fact 31: unlock day sell MELON+FERT before bulk STRAW seed; bulk buy same day as 2nd `BUY_LAND`
- [ ] Fact 32: unlock-day SW carpet (full crew); sw landed unlock day ≥14; 0 night deaths from SW plants that day
- [ ] Fact 33: 1st land d6–10, 2nd d11–12; MAX_LAND_PURCHASES=2 (no SE); unlocked=3; post-sell land emit + land_first; sw_unlock_day ≤ 11
- [x] Fact 34: d9–12 force-sell MELON shed+held; d10 h≥16 room-capped DROP walk; 0 escapes; contested d10 MELON widen not ~−15k
- [ ] Fact 35: MELON-wave hire — waive MIN_MONEY_TO_HIRE when ripe MELON exists; no forced-hire / no WORK_TILES mutation
- [ ] Fact 36: day-0 MELON opening seed (~12) + plant_budget credit; field MELON EOD d5 ≥12
- [ ] Fact 38 is folded into 22 — check 22, not a d13+ home-only path
- [ ] Fact 39: home leftover takes the window occupant (STRAW d5–8) else WHEAT; the NW STRAW ban is withdrawn
- [ ] Fact 43: crew 4–5/day to d5, 8–11/day from d6 (`tape_profile.py` crew row)
- [ ] Fact 16: home-quadrant cap does not block pen 4–5 before land; no empty tile ⇒ wait for `BUY_LAND`, not all season
- [ ] Fact 21: `BUY_PRODUCT FERTILIZER` sized to the turn's `FERTILIZE` demand (tens/season), never to a stock target
- [ ] Fact 22: WHEAT is the empty-tile default from d0, keyed on the tile; still no force wrapper keyed on shed stock (F7)
- [ ] d0 pens/herd will not be 1/1 if the above hold **and** fact 4’s crew exists
- [ ] Do not paste Path A crop-first gates into this throwaway

Then run **contested vs `agents/route_v20.py`, seeds 0 and 8** — that is
the judge (see the acceptance bar). `starter` stays as a crash/escape
smoke check. Read `tape_profile.py`, then `_trace_cashflow_v20.py`, then
the bank. Do not patch shipped `main.py` until the throwaway shows the
rows *and* the contested bank rises. `bptk.py` cannot see this cadence.
