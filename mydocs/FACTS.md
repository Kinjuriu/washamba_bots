# Farm fact-set (living spec)

Canonical shape for the agent under construction. Method:
`mydocs/AGENT_BUILDING_PROTOCOL.md`. Live board: `mydocs/HORIZON.md`
(actual farm vs next required state — overwrite, don’t append). Session
diary: `mydocs/HANDOFF.md`. Mechanisms and dead ends: `CLAUDE.md`.

This file is the **required** calendar. It is not a snapshot of the
throwaway today. `HORIZON.md` is that snapshot. `HANDOFF.md` does not
duplicate either.

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

Then: fill `mydocs/HORIZON.md` Actual (seeds 0 and 8 at the previous
state) → fact card → if Actual cannot fund the row as written, change
the row first → diff the throwaway against **every already-landed** row
→ `tape_profile.py` and contested vs `route_v20.py` on seeds 0 and 8 →
only then bank / harnesses / shipped `main.py`.

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

## Throwaway status (2026-09-05, after the timing diagnosis)

`experiments/_facts_v20.py` clears facts **1–36 + 38 plant half + 39
starter claim** on seeds 0 and 8 (`_facts_prerun_audit.py`: 28/28 source,
74/74 counter) — **and loses contested by ~85k / ~51k.** The audit is not
wrong; it measures the wrong thing. See the acceptance bar above.

**Contested (seed 0, executed `$`, `_trace_cashflow_v20.py`):** the whole
gap is four inflow streams, and each one traces to a row in this file
that was written *against* the tapes as an escape-defence patch:

| stream | us | v20 | gap | row that causes it |
|---|---|---|---|---|
| STRAWBERRY | 17.3k | 46.9k | **−29.6k** | 27 + 39 (SW carpet only; NW/NE forbidden) |
| WOOL | 21.6k | 46.9k | **−25.3k** | 15 (herd 6 through d10; tape is 14 by d10) |
| WHEAT net | −16.2k | +3.7k | **−20k** | 22 (all feed bought; tape grows it from d0) |
| MELON | 12.5k (40 seeds) | 17.7k (17 seeds) | −5.3k | 27 (NE refills d7–11 into the crashed post-wave market) |
| FERTILIZER | 10.5k | 14.6k | −4.1k | 9 + 21 (hold for STRAW, never buy back) |

`tape_profile.py` seed 0 says the same thing in timing: crew matches
(±2), **herd −7 at d10** then overshoots — **21 `BUY_ANIMAL` against an
18 cap**, with the placed herd *falling* 18 → 16 over d25–27 (animals
lost late, contested; `starter` reads 0 escapes on the same build) —
**WHEAT −7 on d0 and −5…−13 every day after**, **STRAW −4/−8/−4/−4 on
d5–8**, **MELON +8/+3/+20/+7 replanted d7–11 against a tape that plants
melon once**.

The acreage bind the last three sessions chased (facts 40/41/42, peak
STRAW field 22|34) was therefore **self-inflicted by rows 27/39**, not a
crew or yield limit. Do not reopen 40–42 as written; they are attempts to
buy back with sell paths and fert what the timing rows gave away.

**Live card: timing card T1**, landed as sequential states S1→S4 (not
one commit). **S1 reverted** (facts 9 + 21). **S2 pictures held** on
`experiments/_facts_v20_s2.py` (d0 WHEAT 7, 4/4, d3 cow, land d7);
seed 0 bank vs S0 fell because the d10 handoff still refills MELON.
**S2h reverted** (27/36 MELON d0-only via wheat-fill NE) — seed 0
8,713 → 3,096. **S3 not landed** (27 STRAW underfoot): seed 0 8,713 → 27,289; seed 8
−146; d6 STRAW=0. Keep `_facts_v20_s3.py`. **S3d6 reverted** (fact 33
wool-walk): seed 0 27,289 → 2,301. **S3home reverted** (27+28 prefix):
d6 STRAW still 0; seed 0 27,289 → 16,527. **S3roles pictures held**
(land d6; 45,154 / 53,578). **S3ne pictures held** (NE bootstrap after
land; 67,325 / 72,410). **S4 dump-to-14 failed** (seed 8 59,203).
**S4 cap-14-on-BUILD failed** (seed 8 56,444, pens 16→14). **S4
buy-stop 14 + pen-lead pictures held** on `_facts_v20_s4_lead.py`
(67,325 / 72,410; seed 8 pens 16). Do not retry 8-at-once. Do not clip
pens. **Fact 27 d6 half-tape waived while NE is locked;
after land, bootstrap K-walk (not occupation).** Do not
retry the prefix lift or a home-empty walk. **Do not merge Path A.** Do
not port `main.py`. Named mix **fallback 2026-09-17**. **S4 lead holds.**
d1h0 BUY×4 at $24 / px $28 is a no-op (aff 0). Overnight leftover extra
d0h0 wheat **failed the bank** (hire-floor flavour 44,677 / 52,807;
sheep-first 32k / 49k). Same-tile CARE before feed-walk failed at 5+5.
Leftover seed cap failed (24,740 / 70,300). Extra runner cannot mint wool.
Keep `_facts_v20_s4_lead.py`. Do not recode `shop_mix_target`. Do not
paste 8-by-d6 onto $177. Do not retry leftover-2 at h0. **d1-feed hours
snapshotted 2026-09-17:** d0h11–h15 sit at $114 / aff=4 / held=0 after
the last feed; h15 `BUY_SEED WHEAT` ×9 is the spend that closes it.
Skip-seed would drop d0 PLANT WHEAT 9→0. v20 leftover 3 is mid-day
top-up after a h1 sell, then d1h18 ×5 after fert sell (S1, reverted).

The `Shipped` column below is still about **shipped `main.py`**, not the
throwaway. Do not read throwaway-clear as shipped. K=3; fact 32 bar ≥14.

## Fact card (paste at session start)

```text
Kind: add | remove | supplement (fact N)
Previous state / next state: (S0 → S1, …)
HORIZON Actual filled for seeds 0 and 8? (yes — or stop)
Gap: (one sentence, or “Actual cannot fund this row as written”)
Was:
Now:
Fights: (dropped row, or none)
Throwaway: experiments/_*.py
Pre-run: every already-landed earlier state still true in source?
Counters: this state’s picture + next state’s handoff, plus d0 pens/herd ≠ 1/1
```

**Session card 2026-09-17 — supplement facts 5 + 36 (d1 leftover) DROP**

```text
Kind: supplement (facts 5, 36) — DROP
Previous state / next state: S4 lead → d1 leftover wheat
HORIZON Actual filled for seeds 0 and 8? yes
Gap: d1h0 $24 / wheat $28 / aff=0 / held=0; BUY×4 fill 0. Affordable qty=0.
Was: d0h0 BUY_PRODUCT WHEAT = owned (4); d1h0 emergency ×4 when empty
Tried: d0h0 owned+2 leftover (6); clamp unaffordable BUY; hire-floor seed cap;
     sheep-first (dropped first)
Result: leftover 2 lands; hire-floor flavour land d6 / NE STRAW 2 / yield 5+5
     / bank 44,677 / 52,807 (−22k / −19k). Sheep-first: both sheep d1 FEED,
     yield 4+2, land miss, 32k / 49k. Extra h0 wheat is not payable.
Fights: d1h0 BUY of 4; leftover-2 at h0; CARE-before-feed-walk; S1 sell-fert
Throwaway: experiments/_facts_v20_s4_lead_d1wheat.py (failed)
Keep: experiments/_facts_v20_s4_lead.py
```

**Session card 2026-09-17 — supplement fact 20 (feeder-stay CARE) DROP**

```text
Kind: supplement (fact 20) — DROP
Previous state / next state: S4 lead → (4,4) d0 CARE after FEED
HORIZON Actual filled for seeds 0 and 8? yes
Gap: FEED clears the stay trigger; feed-walk outranks CARE; first-fed
     sheep ((4,4) h5) never CARES d0. Last-fed ((3,3)) does.
Was: feed-walk outranks local CARE; CARE-before-feed-walk pulled walkers
Tried: feeder stays one hour for CARE on that sheep; claimed via
     act_here; other units do not walk in. Sheep-only.
Result: (4,4) d0 FEED h5 CARE h6 (counter moved). d6h0 5+5 (was 5+4).
     land d6. NE STRAW 0. 0 escapes. bank 22,311 / 62,543
     (−45k / −10k). Same tripwire as walker CARE.
Fights: CARE-before-feed-walk; leftover-2 at h0; d1h0 BUY of 4
Throwaway: experiments/_facts_v20_s4_lead_care_stay.py (failed)
Keep: experiments/_facts_v20_s4_lead.py
Next: d1 feed (not leftover extra-buy, not morning BUY×4)
```

**Horizon judge (replaces whole-set half-stack, 2026-09-16).** Sequential
states require later rows to still be false. A subset is legal when:

- every **already-landed earlier** state still holds (do not eat S0 to
  buy S1 — hour-0 batch → d0 **1/1** is still a fail);
- **this** state’s picture and the **next** state’s handoff counters
  hold on contested seeds 0 and 8;
- later states may remain false;
- contested bank vs `route_v20` on 0 and 8 is **not down**. Bank is the
  tripwire that the handoff was wrong, not the thing S1 is scored on.
  `starter` stays a crash / escape smoke check.

`tape_profile.py` is the picture. `_trace_cashflow_v20.py` is the
tripwire. Neither replaces the other.

---

## Sequential states (branched calendar)

Work the next **timed state** on the farm the previous state actually
left — not one lever, not a 100-step suffix. The calendar is the spine.
**Headcount** is one ladder (fact 15: 4→14 by d10, then flat). **Species
mix / goose / 4th quadrant** are named branches only after shops are
public (~d11). Do not open a branch before S4 holds. Do not port
`main.py`. Rules that produce a state must be **day-gated** so a later
patch cannot rewrite an earlier one (fact 39’s NW STRAW ban is the
exhibit).

Each card names this day’s picture **and** the fuel the next state
spends.

| ID | Window | Picture | Handoff (next state spends this) | Status |
|---|---|---|---|---|
| **S0** | EOD d0 | 4 placed (2C2S), 4 pens, wheat in shed not sold, hour-0 hires, MELON ~12, cash ~0 | fert will collect/sell d1; no 5th animal | landed (beach-head facts 1–6) |
| **S1** | d1–d3 | fert sold the day it is collected (no live-STRAW hold); d3 cow from **post-sell** cash; sell→buy→hire on that turn | herd 5, wheat for 5, trough survived | **reverted 2026-09-16** — seed 8 −1,154 with or without buy-back. Actual: d0–d3 identical on 0 and 8; STRAW=0 and `FERTILIZE`=0 through d10; hold only binds d11+ as unused liquidity. Do not retry 9+21 as written. |
| **S2** | d5–d7 | herd 6, first `BUY_LAND` NE, WHEAT empty-tile default from d0, STRAW seed held | NE exists, tiles not waiting empty | **pictures held** on `_facts_v20_s2.py` (d0 WHEAT 7 both seeds). Seed 0 bank vs S0 26,429 → 8,713 is a poisoned *handoff*, not a wheat fail. Do not put wait-empty back. |
| **S2h** | d7–11 | MELON is the d0 opening of 12 and is **never replanted** | NE leftover is WHEAT (S2), d10 wave is those 12, S3 STRAW can land | **reverted 2026-09-16** — `PLANT MELON` after d0 = 0 both seeds, but seed 0 bank 8,713 → **3,096**. Extra melon was load-bearing d10 cash; wheat-fill NE is not the replacement. Do not retry window (0, 0) + underfoot WHEAT on NE as written. |
| **S3** | d5–8 + d11 carpet | STRAW on NW/NE those days, SW carpet ≥14 on unlock | strawberry money in the ground, not only carpeted | **not landed 2026-09-16** — pictures mostly held (`PLANT MELON` after d0 = 0; d5–8 STRAW 18 vs 19; d11=17; peak 35). Seed 0 8,713 → **27,289**. Seed 8 20,764 → **20,618 (−146)** tripwire. **d6 STRAW=0 waived while NE locked** (S3home prefix failed). Keep throwaway; do not port. |
| **S3d6** | d6 | first `BUY_LAND` engine d6, funded by same-turn WOOL | NE exists on d6 so fact 27 can plant STRAW | **reverted 2026-09-16** — land executed d6h8 both seeds, d6 STRAW still 0, seed 0 **27,289 → 2,301**. Wool-holder walk-to-shed before feed-walk is the fact 40/42 steal. Do not retry the walk. |
| **S3home** | d5–8 home leftover | underfoot STRAW PLANT above feed-walk on wheat-harvest empties; hour ≤ 21; no walk | d6 STRAW ≥ half tape without unlocking NE | **reverted 2026-09-16** — d5 STRAW 2→4, **d6 still 0**, d5–8 total 18, 0 escapes; seed 0 **27,289 → 16,527**. Do not retry the lift. Do not add a home-empty walk. |
| **S3roles** | d5–d6 | feed first, then ≤1 wool runner (`PLACE WOOL`); d5 cow deferred while NE pending | first land d6 (or accept d7h0 night dump); 0 escapes; bank vs S3 27,289/20,618 not down | **pictures held 2026-09-16** — land d6 both seeds; d5 cow deferred; 0 escapes; d0 4/4 WHEAT 7 MELON 12; d6 STRAW 3; seed 0 **27,289 → 45,154**; seed 8 **20,618 → 53,578**. Keep throwaway. Do not port. |
| **S3ne** | d6 afternoon | after first land, K≤3 **bootstrap** onto **NE** empty STRAW until the first NE plant lands (feed first, hour ≤ 21, water underfoot) | d6 STRAW ≥ 4; NE STRAW EOD d6 > 0; 0 escapes; bank vs S3roles 45,154/53,578 not down | **pictures held 2026-09-16** — d6 STRAW 5; NE STRAW 3; d5–8 3/5/9/4; d11 15; 0 escapes; seed 0 **45,154 → 67,325**; seed 8 **53,578 → 72,410**. Occupation (K all of d6–8) failed seed 8 milk. Keep throwaway. Do not port. |
| **S4** | d11–d13 | hold 6 through d10; after land2 + carpet, **12** that afternoon; **14 from d13**; **stop buying**; pens may **lead** (16 pens / 14 placed on seed 8) | shops public, SW ready, 14 mouths, pen-lead intact | **pictures held 2026-09-16** — dump-8 failed; cap-14-on-BUILD failed; buy-stop 14 + BUILD toward 18: seed 0 **67,325 / 67,325**; seed 8 **72,410 / 72,410**; pens 16 on seed 8; 0 escapes. On 0 and 8 the 18 *buy* ramp was already dead (mix totals 14; d19 cow is a replacement). Keep `_facts_v20_s4_lead.py`. Do not port. Do not retry 8-at-once. Do not clip pens. |

**Named branches (after S4 — snapshot 2026-09-17):** yarn mix (6c12s /
6c8s) · milk mix (10c4s) · goose pair (egg shops, no opponent goose) ·
**fallback (chosen).** Headcount stays 14. On seeds 0 and 8,
`shop_mix_target` already lands milk **10C4S** and yarn-in-3 **6C8S**.
**6c12s cannot fund** (totals 18). Goose pair is seed-0-only (BRUNCH in
first 3; seed 8 first 3 has no egg shop). Recoding the table is not a
fact. The old d11+ *count* ramp is dropped.

Throwaway `calendar_owned_target` on `_facts_v20_s4_lead.py` is hold-6
through d10, 12 after carpet, 14 from d13 (BUY). `calendar_pen_target`
stays 18 from d13 so pens can lead. Dump-8 and cap-14-on-BUILD both
failed seed 8. Do **not** paste the tape 8/10/12/13/14 onto EOD d6 $177.

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
| 15 | **Herd is 4 d0, 5 d3, 6 from d5 held through d10.** The tape's 8/10/12/13/14 on d6–d10 cannot fund on this farm (EOD d6 **$177 / herd 6**). After d10 melon + second land: **12** the afternoon carpet clears (d11h15), **14 from d13**, **stop buying**. Pens may lead (S3ne seed 8: 16 pens / 14 placed). Dump-8 **failed seed 8**. Cap-14 on buy *and* BUILD **failed seed 8** (pens 16→14, STRAW/milk after d20). Do not retry 8-at-once. Do not clip pens. | d0/d3/d5 hold; d11–12 owned=12; d13+ owned=14; EOD pens ≥ 16 on seed 8 | EOD d10 owned=6; EOD d11 owned=12 (not 14); EOD d13 owned=14; later BUY_ANIMAL none past 14; seed 8 EOD pens ≥ 16; 0 escapes **contested**; S0+S2+S3roles+S3ne pictures; bank vs S3ne 67,325 / 72,410 not down | `calendar_owned_target` paces **BUY** (4/5/6/12/14). `calendar_pen_target` / `choose_animal_to_build` still toward 18 so pens can lead. Prefix: `_animal_can_pay`. Keep land2/carpet defer. Mix picks *which*. | false |
| 16 | Pens exist for the new animals. Parallel pens up to the **pen** target, which may **lead** owned after the buy ladder stops at 14 (S3ne seed 8: 16 pens / 14 placed). Cap-14 on BUILD clipped that lead and failed seed 8. Home-quadrant cap cannot block pen 4–5 if land is not bought until day 6. Same-day placement when an **empty unlocked tile** exists; if home is full of crops, wait for the next `BUY_LAND`, not past it. | buy day; after owned=14, pens still build toward 16–18 | unplaced animals do not sit in the shed all season; seed 8 EOD pens ≥ 16 with owned=14; a day-5 extra is placed by d6h23 once NE unlocks | `choose_animal_to_build` uses `calendar_pen_target` (not the buy-14 cap); parallel `pending_builds`; `MAX_ANIMALS_ON_HOME_LAND = 3` must not refuse pen 4 on NW before `BUY_LAND`. | false (serial unfilled; home cap 3) |
| 17 | **Owned** cap is **14** (fact 15's buy ladder). It does not cap pens — those may lead (fact 16). A cap set above the *buy* ladder (18) let the d11+ ramp buy 21 head contested. Do not start at 10 on day 0. | season | end **owned** = 14; pens may be 16; d0 still 4; mix picks *which* | `calendar_owned_target` = 14 from d13 for BUY. `MAX_ANIMALS` stays the pen ceiling (18). Do not route BUILD through 14. | false (`MAX_ANIMALS = 4`) |

## Feed

| ID | Invariant | When | Counter | Code that must afford it | Shipped |
|---|---|---|---|---|---|
| 18 | Wheat buffer scales with **owned** animals, not a flat 2 for the farm. | every wheat buy/sell | shed wheat tracks owned; not pegged at 2 | `MIN_WHEAT_RESERVE_FOR_FEEDING` used as a per-head multiplier on **owned**; both `decide_animal_market_actions` buy trigger and `decide_market_actions` sell exemption. | false (flat 2; sell keyed on filled) |
| 19 | Feed wheat is not gated behind `MIN_CASH_RESERVE_FOR_SEED_BUYING`. | anytime cash is $9–$375 | `BUY_PRODUCT WHEAT` still emits | wheat buy lives in `decide_animal_market_actions` (no seed reserve today — **keep it that way**). Do not add the seed floor to this path. | true (buy path); still loses if fact 13 spends the bank first |
| 20 | FEED happens every day: units on the animal tiles, wheat in the acting inventory. A walker must not `claimed`-steal an occupied unfed tile from a unit already on it with wheat. Walking to an unfed animal outranks local CARE / COLLECT on a different tile; it does **not** outrank WATER or crop HARVEST underfoot. Nearest-unfed skips already-assigned tiles; it does not drop feed. | every day | `FEED` ≈ owned × days; 0 escapes; far pens fed after the free first miss | `choose_unit_action`: FEED-underfoot ignores `claimed`; occupied unfed+wheat tiles are pre-marked into `feed_claimed`; `find_nearest_target(..., exclude=feed_claimed)`; feed `walk_to` does not add to `claimed`; crop HARVEST / WATER underfoot, then feed-walk, then CARE/COLLECT. A market order alone is not this fact. | true at cap 4; false at cap 8 without the walk/claim rules |

## Crop constraints that coexist with this equilibrium

These are not a STRAW pin. They stop Path B’s hole (herd exists, leftover
tiles wheat-flood) without importing Path C.

| ID | Invariant | When | Counter | Code that must afford it | Shipped |
|---|---|---|---|---|---|
| 21 | **Buy fertilizer back to apply it, in the tens per season** (tape: 35–64 `BUY_PRODUCT FERTILIZER`, alongside 280–360 sold). Fact 9 sells the flow because holding it is a liquidity cost; this row buys the few units a tile actually wants at the hour it wants them. That is not the arbitrage `CLAUDE.md` rules out (buy-the-dip / sell-the-recovery, −1,486), and not shipped `main.py`'s liquidation-era incidental buying — it is fert-on-demand for `FERTILIZE`. | when a tile is fertilized and the shed is empty of fert | `BUY_PRODUCT FERTILIZER` between ~20 and ~70 for the season; `FERTILIZE` count does not fall when fact 9 starts selling the flow | `decide_market_actions` top-up sized to the turn's `FERTILIZE` demand, never to a stock target. | false |
| 22 | **WHEAT is the default crop on any empty tile, from day 0** (tape: 7 on d0, then a continuous 3–14/day to d28, ~190 plantings and ~190 `BUY_SEED WHEAT` a season). Its harvest is what feeds the herd; `BUY_PRODUCT` (facts 5, 18, 19) is the top-up, not the supply. Buying every mouthful instead cost **−20k net** contested on seed 0 (we paid 16.9k for wheat and sold 0.7k; v20 paid 47.4k and sold 51.1k — and its churn is what pushes the price we pay). Still forbidden, and this is the distinction the row exists for: no wrapper that force-plants because **stock is low** or `tiles < animals` (Path C F7), and no blocked-MELON→WHEAT mapping. Default-crop-on-empty is keyed on the **tile**, not on the shed. | season, every empty tile without a window occupant | `tape_profile.py` PLANT WHEAT within ~±3/day of tape from d0; `PLANT WHEAT` does not scale with herd size; `SELL WHEAT` > 0 by d2 | `choose_crop` / empty-tile plant: WHEAT is the fallback pick everywhere, including SW and NE, whenever no window occupant (27) claims the tile. `BUY_SEED WHEAT` follows plantings. | partial (no force-wheat; fact 38 plant half is home-only and d13+) |
| 23 | Never plant TOMATO. | season | `PLANT TOMATO` = 0 | `CROP_PLANTING_WINDOWS["TOMATO"] is None` / `choose_crop`. Independent of carrying the rest of the window gate as a fact. | true |
| 24 | Do not skip CARE to free crop turns. | daily | wool/milk sold does not collapse | `choose_unit_action`: no “skip CARE if STRAW ready / bonus ≥ 2” (Path C F5). | true |
| 25 | Do not mutate `WORK_TILES_PER_HAND` or inject forced extra `HIRE`s. | ever | no F6 spiral | `decide_hire_orders` stays work+ceiling+affordability. Facts 4 and 12 are *when* hires list relative to buys, not a density mutation. | true |
| 26 | Do not gate the n-th animal on `wheat ≥ reserve × (owned+1)` or `k × (owned+1)` cash. | buy days | calendar (15) still fires | no F8-class floor in `decide_animal_market_actions`. Soft `wheat_stock ≤ 0` as escape-prevention is allowed; a hard buffer before scale is not. | true |
| 27 | **STRAW is an early crop on home and the first extra, and the SW carpet is its second wave, not its only one.** Tape: STRAW plantings **d5 ≈4, d6 ≈8, d7 ≈4, d8 ≈4** on NW/NE, then the d11 carpet ≈15. STRAW first-yields 10 days out, so a d5 planting sells from ~d15 (tape `SELL STRAWBERRY` starts d15) and a d11 one from ~d21 — the early wave is where the season's strawberry money is. Carpet-only cost **−29.6k** contested on seed 0 (peak field 22 vs 34). **MELON is planted once, on d0 (12), and never replanted** — the old row's NE-refill-during-window put 31 extra melons in the ground on d7–11 that ripen into the market our own d10 wave just crashed, for **−5.3k on 23 extra seeds**. Not a pin of 50. | d5–8 on NW/NE; d11 carpet on SW | `tape_profile.py` PLANT STRAWBERRY ≥ half the tape on each of **d5, d7, d8**; **d6 waived while NE locked**; after first land, fact 29 K-walk onto NE (S3ne) — not S3home prefix lift, not 6a above feed; d11 carpet still ≥14; **PLANT MELON after d0 = 0**; STRAW field peak ≥ 30 | empty-tile PLANT prefers STRAW on home/NE leftover d5–8 and on SW on the carpet day; MELON is a d0-only opening (fact 36) and is never re-preferred; WHEAT (22) fills whatever STRAW's seed budget does not. BUILD still beats PLANT (fact 16). Do not lift underfoot STRAW above feed-walk. | false |
| 28 | When a unit **stands on** empty leftover, it plants that quadrant's window occupant (STRAW d5–8 / d11 carpet per 27, CARROT d21–25) and otherwise **WHEAT** (fact 22) — tiles no longer wait empty between windows, which is what left SW producing nothing for most of the season. Do **not** walk the whole crew onto a far quadrant ahead of local first-water (that is the fact 40/42 escape mode, and it stays closed). | any quadrant; underfoot | SW `PLANT WHEAT` > 0 between windows; end SW weeds not a cascade; 0 escapes contested | `leftover_occupant` plus WHEAT fallback on every quadrant; no crew-wide walk to a far empty. Underfoot plant stays at step 9 (S3home lift reverted). | false |
| 29 | At most **K** units (start K=2) may work later-extra leftover in a turn **while SW is still locked** (before the engine day of the second `BUY_LAND`). Each plants only if it can water that tile before day end (`hour <= 21`: plant this hour, water next). After `PLANT`, WATER underfoot before walking to another empty. Everyone else keeps NE/home upkeep. On the **unlock day** (fact 32), K does not cap planters — full crew may carpet SW. Assignment, not hire-density (fact 25). | later extras; occupant windows; hour ≤ 21; pre-unlock only for K | d12 SW STRAW occupancy > 0 on seeds 0 and 8; each landed SW plant is watered the same day (0 night deaths from that day’s SW plants); NE STRAW > 0 by d8 (fact 27) without a crew-wide walk; NE weeds not a cascade vs ~5 at d12; d0 4/4; 0 escapes contested | `sw_slots` pre-unlock; K-unit later-extra empty walk after urgent water/harvest, **before** fert/weed; after first `BUY_LAND`, the same K walks onto **NE** empty STRAW until the first NE plant lands (d5–8, after feed, hour ≤ 21) — not 6a, not a hire, not a multi-day occupation; local WATER ignores `claimed`; refuse SW `PLANT` at `hour >= 22`. Unlock day uses fact 32, not `sw_slots`. | false |
| 30 | **STRAW seed cadence (unlock halves):** held STRAW must not sit at **0** across whole days while SW still needs seed — pre-unlock dribble so ≥1 `BUY_SEED STRAW` lands before unlock day, and when SW is unlocked with empty later-extra STRAW occupant, restock outranks MELON. **Widened by T1:** STRAW seed must also be held from ~d4 so fact 27's NW/NE d5–8 wave can land, not only for the SW carpet — the “dribble” is now a real early demand. Not `straw_seed_supplement` (blunt always-buy). Not a STRAW pin. | d5–12; especially pre-unlock + d9–11 SW empty | held STRAW > 0 on ≥1 turn/day in d5–10; ≥1 `BUY_SEED STRAW` before SW unlock day; with SW unlocked d9–11: held STRAW > 0 before first SW `PLANT` attempt; MELON restock does not block those buys | `fact30_wants_straw_seed`: SW-empty or pre-unlock seed-habit only — not post-MELON home refill; same post-sell cash rules as facts 10–11 when buys compete with sells. | false |
| 31 | **SW unlock morning (market preamble):** on the engine day of the second `BUY_LAND`, hour-0 market sells **MELON then FERT** (fund the sprint), then bulk `BUY_SEED STRAWBERRY`, then hires; second `BUY_LAND` emits within ~1 hour using **post-sell** cash (pair with `land_first` reorder). v20 tapes: bulk **×23** on 9/10 tapes at tape d12 h0 (engine d11 h0); tape_5 uses ×5 but same shape. | engine day of 2nd `BUY_LAND`; hour 0–1 | on unlock day: `SELL MELON` + `SELL FERT` before bulk `BUY_SEED STRAW`; bulk ≥5 same day as 2nd `BUY_LAND`; land emits when post-sell affords even if pre-turn cash < reserve | `nikaangukia_meroni` market assembly: unlock-day sell block → seed bulk → hires → land; `_estimated_post_sell_cash` on `decide_land_orders`. | false |
| 32 | **SW carpet day:** on the engine day SW unlocks, plant STRAW on SW empty leftover until seed or window exhausted — **full crew**, not K-limited (fact 29). WATER underfoot same day for every landed plant (`hour ≤ 21`). v20 tape_0: **18** SW STRAW landings unlock day; 9/10 tapes bulk-buy then carpet same day. | 2nd `BUY_LAND` day; SW quadrant; hour ≤ 21 | SW STRAW occupancy EOD unlock day **≥14** (K=3; seed 0 hits 14 under $100 STRAW + land floor — do not waive land reserve to chase 15); sw_landed unlock day >> K; 0 night deaths from that day’s SW plants; d9–11 SW `plant_actions` > 0 once facts 30–31 hold | unlock-day bypass of `sw_slots`; crew already sized by facts 4/12/25 (no `WORK_TILES_PER_HAND` mutation); carpet outranks BUILD while STRAW budget remains; `plant_budget` credits the unlock bulk `BUY_SEED` | false |
| 33 | **Land timing:** first `BUY_LAND` engine **d6** (tape hour ~4–6; catch-up through **d10** if still NW-only); second engine **d11–12** (SW). Tape funds the first buy with **same-turn `SELL WOOL`** (12 units then `BUY_LAND`). SELL reads shed only — wool sitting on units is not cash (S3: d6 held 4→9, shed 0, post-sell $657, land d7h1). Cap-5 wool sell on d7 still leaves ~$190 after $1000, below the $500 floor. **Keep the $500 first-land floor** (4 wool would buy land at $19 with no STRAW seed). There is no unit-to-unit handoff; `DROP` dumps the whole inventory. **Turn roles:** reserve feed labor first (fact 20), then **at most one** wool holder (closest to shed, already holding wool) walks and `PLACE WOOL n` (not full `DROP`). Pending first land only. Pair with **d5 cow defer** while NE is pending (the d6–d10 animal defer left d5 as the hole: owned 6 / placed 5, ~$400 ornament). Raise the wool cap to the tape’s 12 on pending-first-land turns. Second purchase must not lose to same-turn animal spend (`land_first` + post-sell emit). **No third buy (SE)**. Do not retry all-holders walk (S3d6) or waive the floor. | d6–10 and d11–12 | 1st land **d6** both contested 0+8; d6 `PLANT STRAW` waived while NE locked unless land is early enough to plant; `sw_unlock_day` ≤ 11; unlocked **= 3** (not 4); 2nd land d11–12; 0 escapes; bank vs S3 27,289/20,618 not down | `decide_land_orders` + `assign_wool_runner` PLACE/SELL cap 12; d5 slots=0 while NW-only; keep `MIN_CASH_RESERVE_FOR_LAND_BUYING` on the first buy; land-before-animals | false |
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

**Tape index:** `mydocs/tape_transcripts/tape_0.txt` … `tape_9.txt`, `all_tapes_turns.csv`. Transcript **day N = engine day N−1** (tape d12 = engine d11).

## Timing card T1 — rewrite 9/15/17/21/22/27/28/39, add 43 (2026-09-05) **← live**

```text
Kind: rewrite (facts 9, 15, 17, 21, 22, 27, 28, 39) + add (43)
Was: five escape-defence rows that each moved the shape off the tape —
     herd held at 6 through d10 then ramped past the cap to 21;
     STRAW only as the d11 SW carpet; MELON refilled on NE d7–11;
     all feed wheat bought, tiles never planted with it; fert held for
     STRAW and never bought back; NW banned from STRAW and left empty.
     Every unit counter passed; contested bank fell 51k → 26k / 8k.
Now: each row names the tape's day and is checked with tape_profile.py.
     Herd 4 d0 / 5 d3 / 6 through d10; tape 8-by-d6 cannot fund; first
     rewrite (dump 8 to 14 after land2) failed seed 8. Next pace: 12
     after carpet, 14 from d13, cap 14. STRAW d5–8 on NW/NE plus the
     d11 SW carpet. MELON d0 only. WHEAT the default crop on any empty
     tile from d0. Fert sold daily from d1, bought back in tens to apply.
     Crew 4–5 then 8–11 from d6.
Fights: the parked acreage/sell/fert patches (40, 41, 42) — they were
     buying back what these rows gave away; fact 38's d13+ home-only
     wheat (folded into 22); fact 39's NW STRAW ban (withdrawn);
     "hold 6 through d10" and the d11+ shop-mix ramp (both in 15)
Throwaway: experiments/_facts_v20.py (now tracked in git — commit per card)
Pre-run: facts 1–8, 10–14, 16, 18–20, 23–26, 29–36 still true in source;
     d0 pens/herd 4/4; 0 escapes **contested**, not only vs starter
Counters: tape_profile.py seeds 0+8 — crew ±2/day; herd ±1/day d0–d10 and
     ≤14 after; PLANT WHEAT within ±3/day from d0; PLANT STRAW ≥ half the
     tape on each of d5–d8; PLANT MELON after d0 = 0; SELL FERTILIZER no
     dry spell > 1 day. Then _trace_cashflow_v20.py: STRAWBERRY, WOOL,
     WHEAT-net and FERTILIZER gaps all smaller than −29.6k / −25.3k /
     −20k / −4.1k, and **contested bank up on both seeds**.
```

**Order of work.** Same five steps, now named as states: **S1** (9 + 21
fert, **skipped** — Actual cannot fund) → **S2** (22 + 28 wheat,
**pictures held**) → **S2h** (27/36 MELON d0-only via wheat-fill NE,
**reverted** — seed 0 bank down) → **S3** (27 STRAW on those NE/home
tiles, **not landed** — seed 8 −146; **d6 waived while NE locked**) →
**S3home reverted** → **S3roles** (33: feed-first ≤1 wool `PLACE` + d5 cow defer) → **S3ne** (29/27: K-walk onto NE after land) → **S4 dump-to-14 failed** → **S4 cap-14-on-BUILD failed** → **S4 lead pictures held** (buy 14, pens lead). Do not
put wait-empty back. Do not retry S2h, S3d6, S3home, 8-at-once, or cap-14 that clips pens. Do not paste
the tape 8/10/12/13/14 onto EOD d6 $177. After each state: horizon judge, not
the whole-season audit.

## S2h session card — MELON d0-only (2026-09-16) **← reverted**

```text
Kind: supplement (facts 27 + 36) — MELON-after-d0 half only
Previous / next: S2 → S2h
HORIZON Actual filled? yes (seeds 0 and 8, `_trace_horizon_s2.py`)
Gap: leftover_occupant returns MELON on NE through window (0, 11);
     PLANT MELON after d0 = 31|35 vs v20 0; d9 field 33 vs 12;
     d10 SELL_MELON $9.2k vs $15.6k; extra seed $2.2k.
Tried: MELON window (0, 0); leftover_occupant never returns MELON;
     no leftover_seed MELON restock; NE leftover takes S2 underfoot WHEAT.
Result: PLANT MELON after d0 = 0 both seeds; d0 12 / 4/4 / WHEAT 7;
     d3 cow; land d7; 0 escapes; BUY_SEED MELON $960=$v20.
     d7 NE wheat flood PLANT WHEAT=22; d9 melon field 12.
     Contested bank seed 0 **3,096** (was 8,713) / seed 8 32,457
     (was 20,764). Seed 0 tripwire FAIL. Extra melon was the d10
     drawer ($10,198 → $5,184). STRAW units 86→85 but $ 5,380→1,702.
     Do not retry wheat-fill NE. Next candidate is STRAW on those
     tiles (S3), not empty, not wheat.
Fights: none dropped. Calendar still hold-6.
Throwaway: experiments/_facts_v20_s2h.py (failed copy; S2 file unchanged)
```

## S3 session card — STRAW on home/NE leftover d5–8 (2026-09-16) **← not landed**

```text
Kind: supplement (facts 27 + 39); fact 30 seed cadence for the early wave
Previous / next: S2 → S3
HORIZON Actual filled? yes (S2 vs route_v20, seeds 0 and 8)
Gap: leftover_occupant is MELON on NE / None on home, so d5–8 STRAW = 0
     and d7–11 refill 31|35 extra melon. $450 seed floor sits on d5 cash
     $405 so fact30 dribble cannot buy STRAW. 6a walk-to-NE is the fact
     40/42 escape — S3 is underfoot only. S2h wheat-fill of the same
     tiles failed seed 0 (8,713 → 3,096).
Tried: leftover_occupant STRAW on home and NE d5–8; never MELON on NE;
     delete 6a walk; no leftover_seed MELON; early BUY_SEED STRAW d5–8
     sized to those empties, waives $450, cap 8; plant_budget credits STRAW
Result: PLANT MELON after d0 = 0; d0 4/4 WHEAT 7; d3 cow; land d7;
     0 escapes; d11 carpet 17; peak field 35; d5–8 STRAW 18 vs 19 but
     d6 = 0 (home full, NE locked until d7). Seed 0 8,713 → **27,289**.
     Seed 8 20,764 → **20,618 (−146)**. Tripwire letter fails. Keep
     throwaway (do not undo seed 0). Do not port. Do not call landed.
Fights: S2h wheat-fill NE; fact 39's old NW STRAW ban; crew walk onto NE
Throwaway: experiments/_facts_v20_s3.py
```

## S3d6 session card — first BUY_LAND engine d6 from WOOL (2026-09-16) **← reverted**

```text
Kind: supplement (fact 33)
Previous / next: S3 → S3d6
HORIZON Actual filled? yes (`_trace_d6_land.py` + tape_profile, seeds 0 and 8)
Gap: window already allows d6; v20 buys d6h4; we buy d7h1 because d6 wool
     is on units (shed 0, post-sell $657 < $1500) and d7 cap-5 wool sell
     leaves ~$190 after land, below the $500 floor. Home 5 d6 empties are
     not the tape’s ~8 (those are NE after land). Seed 8 −146 vs S2 is
     STRAW $ up (7.9k→10.9k); remaining letter is book, not a plant miss.
Now: pending first land → after-feed room-capped WOOL DROP (shed-adj, or
     walk only holders, never while unfed); SELL WOOL shed+held cap 12;
     keep $500 land floor so 4 wool cannot land broke. Occupant already
     STRAW on NE d5–8.
Result: v1 (DROP after all-fed) never dropped; phantom SELL WOOL ×143 and
     BUY_LAND every d6 hour; land still d7; seed 0 27,289 → 16,978.
     v2 (walk holders to shed before feed-walk) land **executed d6h8**,
     NE empty EOD, d6 STRAW still 0, d7 STRAW 13. Seed 0 **2,301**.
     Seed 8 43k then 58k. Walk stole feed. Do not retry the walk.
Fights: waiving first-land reserve to 0; crew walk onto home empties;
        fact 40 STRAW DROP drip; S4 herd ladder
Throwaway: experiments/_facts_v20_s3d6.py (failed copy; S3 unchanged)
Counters: first BUY_LAND d6 both seeds; d6 STRAW ≥ 4; d0 4/4 WHEAT 7 MELON 12;
     PLANT MELON after d0 = 0; d11 carpet ≥14; 0 escapes; bank vs 27289/20618
     not down
```

## S3home session card — underfoot STRAW above feed-walk (2026-09-16) **← reverted**

```text
Kind: supplement (facts 27 + 28)
Previous / next: S3 → S3home
HORIZON Actual filled? yes (S3 vs route_v20, seeds 0 and 8)
Gap: 5 home empties exist d6–8 (wheat-harvest leftovers); underfoot
     occupant PLANT sits below feed-walk so harvesters leave; 6a walk-back
     is deleted. Half-tape of ~8 is 4 — those 5 tiles fund d6 STRAW
     without unlocking NE. S3d6 wool-walk killed seed 0 and still left
     d6 STRAW=0.
Tried: on home / first extra, d5–8, standing on empty leftover whose
     occupant is STRAW, hour ≤ 21, plant_budget STRAW > 0 → PLANT before
     feed-walk. No walk. BUILD and WHEAT fallback stay at step 9.
Result: d0 4/4 WHEAT 7 MELON 12; PLANT MELON after d0 = 0; land d7;
     0 escapes; d11 carpet 17; d5–8 total 18. d5 STRAW 2→4 (lift fired);
     **d6 still 0**. Seed 0 **27,289 → 16,527** (STRAW $ 21.6k → 12.0k).
     Seed 8 20,618 → 35,204. Do not retry the lift. Do not add a
     home-empty walk (bank already failed). Waive fact 27 d6 while NE locked.
Fights: wool-walk S3d6; 6a walk-to-empty; waiving first-land reserve;
        lifting WHEAT fallback above feed
Throwaway: experiments/_facts_v20_s3_home.py (failed copy; S3 unchanged)
```

## S3roles session card — feed first, ≤1 wool PLACE + d5 defer (2026-09-16) **← pictures held**

```text
Kind: supplement (fact 33)
Previous / next: S3 → S3roles
HORIZON Actual filled? yes (`_trace_d5_d6_roles.py`, seeds 0 and 8)
Gap: $1500 is wool not in the shed plus a $400 shed cow. SELL reads shed
     only; no unit-to-unit handoff; DROP dumps wheat. d5h0 BUY_ANIMAL COW
     (owned 6/placed 5 until h6). d6h6 u2 already shed-adj with 4 wool,
     wheat=0, not on unfed; 2 unfed remain; crew 7; shed wheat 0. 4 wool
     at ~$206 is $19 short of $1500 without the defer; both halves needed.
     All-holders walk (S3d6) killed seed 0. Prefix lift (S3home) missed d6.
Now: d5 animal slots=0 while NE pending; precompute roles — reserve feed
     labor, then ≤1 closest wool holder PLACE WOOL n (not DROP); SELL cap
     12 credits only that PLACE; keep $500 land floor.
Result: first BUY_LAND d6 both seeds; d5 BUY_ANIMAL=[]; PLACE+SELL 4 wool
     d6h4 then land d6h10; d0 4/4 WHEAT 7 MELON 12; PLANT MELON after d0=0;
     0 escapes; d5–8 STRAW 3/3/9/4 (d6=3); d11=16. Seed 0 **27,289 →
     45,154**. Seed 8 **20,618 → 53,578**. Tripwire pass. Keep throwaway.
     Do not port. Snapshot of this farm at d9–d10: S4 as written blocked.
Fights: all-holders walk; waiving first-land reserve; S4 herd ladder;
        S3home prefix lift
Throwaway: experiments/_facts_v20_s3_roles.py
Counters: first BUY_LAND d6 both contested 0+8; d0 4/4 WHEAT 7 MELON 12;
     PLANT MELON after d0 = 0; 0 escapes; bank vs 27289/20618 not down
```

## S3ne session card — K-walk onto NE after land (2026-09-16) **← pictures held**

```text
Kind: supplement (facts 29 + 27)
Previous / next: S3roles → S3ne
HORIZON Actual filled? yes (`_trace_horizon_s3roles.py`, seeds 0 and 8)
Gap: land d6h10–11; 10 STRAW seed already bought; EOD d6 NE 25 empty /
     0 STRAW; occupant is already STRAW; 6a walk deleted; fact 29 K-walk
     is SW later-extra only. Hires cannot fire after h4. Underfoot-only
     plants the seed on d7 (8 NE), a day late.
Now: after first extra unlocks, K<=3 units walk onto NE empty STRAW
     until the first NE plant lands, after feed, hour <= 21, water
     underfoot. Same sw_slots. Occupation (K all of d6–8) failed seed 8
     (milk −11k, STRAW −6.7k, bank 53,578 → 48,461). Bootstrap holds.
     Not 6a above feed. Not S3home lift. Not forced hires. Not S4.
Result: d6 STRAW 5; EOD d6 NE STRAW 3; d5–8 3/5/9/4; d11 15; d0 WHEAT 7
     MELON 12; PLANT MELON after d0=0; first land d6; 0 escapes.
     Seed 0 **45,154 → 67,325**. Seed 8 **53,578 → 72,410**. Keep
     throwaway. Do not port. EOD d6 still $177 — S4 as written still
     cannot fund.
Fights: 6a crew walk; S3d6 wool-before-feed; S3home prefix; hire-density;
        multi-day NE occupation
Throwaway: experiments/_facts_v20_s3_ne.py
Counters: d6 STRAW >= 4; EOD d6 NE STRAW > 0; PLANT MELON after d0 = 0;
     d0 4/4 WHEAT 7 MELON 12; first land d6; 0 escapes contested;
     bank vs 45154/53578 not down
```

## d6 leftover snapshot — seed-on-land-hour cannot fund as written (2026-09-17)

```text
Kind: snapshot (S4 lead → leftover); did not code; change the row
Previous / next: S4 lead → grow d6 leftover
HORIZON Actual filled? yes (`_trace_horizon_s4_lead_d6.py`, seeds 0 and 8)
Gap: EOD d6 $177 vs v20 $1561. Same executed $ as S3roles (wool -624,
     STRAW seed -700, cow -400) but the hours moved: first land **d6h10**
     (not h11); sSeed at land hour **1** (EOD d5 leftover), no buy that
     hour; **h11** COW1 + STRAW 7 because NE empties=25; then dribble +3
     = 10/$1000 vs v20 3/$300 at **h0**. h5 woolS/H already 0/0 — the
     extra 3 wool is not sitting in shed/inventory. Post-land $1430
     still clears the $500 floor. d7 BUY_ANIMAL none (EOD d7 $3); v20
     buys 4 head from $1561.
Now: "STRAW seed 10 on the land hour" is false. Rewrite: after first
     land, early STRAW restock must not treat NE empties as an 8-pack
     (cap held ~3 / K). Keep the cow. Keep the floor. If cutting the
     7-pack zeros NE STRAW EOD d6, change the row again. Not wool this
     copy. Throwaway unchanged until that rewrite is coded.
Fights: 8-by-d6 on $177; waiving the floor; S3d6 wool walk; mix recode
Throwaway: experiments/_facts_v20_s4_lead.py (unchanged)
Counters: snapshot only — S4 pictures still hold; NE STRAW EOD d6 = 3;
     d0 4/4 MELON 12; land d6; 0 escapes; bank 67,325 / 72,410
```

## d6 wool drawer — extra runner / PLACE cannot fund (2026-09-17)

```text
Kind: snapshot (S4 lead → leftover wool); did not land wool
Previous / next: S4 lead → grow d6 leftover
HORIZON Actual filled? yes (`_trace_horizon_s4_lead_d6_wool.py`, 0 and 8)
Gap: h0 sheep tile yield already 5+4=9 vs v20 6+6=12. HARVEST then
     PLACE+SELL clears all of it (h4 sell 4, h10 sell 5). Non-runner
     held on PLACE hours: none. Tiles 0 after sells.
Now: extra runner after feed / shed-adj PLACE cannot mint 3 wool.
     Care-bank miss, not a PLACE miss. Drop the wool leftover row.
Fights: S3d6 all-holders walk; DROP
Throwaway: experiments/_facts_v20_s4_lead.py (unchanged)
Counters: snapshot only — 0 escapes; bank 67,325 / 72,410
```

## d6 leftover seed cap — d6 3-buy holds, bank fails (2026-09-17) **← failed**

```text
Kind: add (post-land STRAW restock cap, d6 afternoon only)
Previous / next: S4 lead → leftover
HORIZON Actual filled? yes (wool drawer + leftover hours)
Gap: land-hour sSeed=1; h11 buys 7 from NE empties. Wool never-produced.
Tried: after first land on d6, fill held to 4 (buy 3) at h11, stop h12+;
     fact30 / leftover-seed STRAW blocked that afternoon; d7+ unchanged.
Result: d6 BUY_SEED STRAW 3; EOD d6 $877; NE STRAW 2; d6 STRAW plants 4;
     land d6; cow d6h11; 0 escapes. d7h1 STRAW ×8 eats leftover;
     d7 BUY_ANIMAL none. Seed 0 **67,325 → 24,740**. Seed 8 **72,410 →
     70,300**. Bank tripwire fail. Keep S4-lead.
Fights: 8-by-d6; extra wool runner; waiving floor
Throwaway: experiments/_facts_v20_s4_lead_d6seed.py (failed copy)
Counters: d6 STRAW>=4; NE STRAW EOD d6>0; d0 4/4 MELON 12; land d6;
     0 escapes; bank vs 67325/72410 not down — FAIL
```

## S4 snapshot card — 8-by-d6 / 13-by-d9 cannot fund (2026-09-16) **← blocked**

```text
Kind: snapshot (S3roles → S4); did not code; change the row
Previous / next: S3roles → S4 as written
HORIZON Actual filled? yes (`_trace_horizon_s3roles.py`, seeds 0 and 8)
Gap: EOD d6 $177 / herd 6. Confirmed d6 executed $ (both seeds):
     SELL_WOOL 9/$1815 vs v20 12/$2439; SELL_FERT 4/$369 vs 5/$466;
     BUY_LAND $1000 both; BUY_ANIMAL COW $400 vs $0; STRAW seed 10/$1000
     vs 3/$300. v20 EOD $1561 is wool minus land, no extra animal.
     EOD d9 $1.4k / herd 6; 13-by-d9 needs ~7 head.
Now: S4 as written blocked. Do not reconcile calendar_owned_target.
     Throwaway unchanged. Rewrite S4 or pick a different next state
     (d6 leftover vs v20 $1,561, or pace the d11 dump after melon $)
     before touching code.
Fights: opening d6–d8 buys on this cash; waiving first-land $500 floor;
        crew walk onto NE
Throwaway: experiments/_facts_v20_s3_roles.py (unchanged)
Counters: snapshot only — S3roles pictures still hold; 0 escapes;
     bank 45,154 / 53,578
```

## S4 rewrite card — dump 8 after land2/carpet (2026-09-16) **← failed**

```text
Kind: rewrite (facts 15 + 17)
Previous / next: S3ne → S4
HORIZON Actual filled? yes (`_trace_horizon_s3ne.py`, seeds 0 and 8)
Gap: 8-by-d6 still cannot fund (EOD d6 $177 / herd 6). After d10 melon:
     EOD d10 $8603|$7881 herd 6; SELL_MELON d10 $8099/40u | $6564/29u;
     land2 d11h1 leftover after floor $6151|$5215; 8 cows $3200 FITS.
     Current dump d11h15 to 12 then shop-mix toward 18.
Tried: hold 6 through d10; after second land + SW carpet, prefix toward
     14; stop. Cap 14. Mix may pick which. Keep land2/carpet defer.
     Not 8-by-d6. Not 13-by-d9.
Result: pictures held — EOD d10 herd 6; d11h1 land2; d11h15 → 14; stop;
     BUY_ANIMAL total 14; d0 4/4; PLANT MELON after d0=0; d6 STRAW 5;
     0 escapes. Seed 0 **67,325 → 67,177 (−148)**. Seed 8 **72,410 →
     59,203 (−13,207)** FAIL (milk 23,554 → 13,506). EOD d11–12 owned
     14 / placed 6 / pens 6. Do not retry 8-at-once. Keep S3ne.
Fights: tape 8/10/12/13/14 on this cash; shop-mix count ramp to 18;
        waiving first-land $500 floor; NE carpet
Throwaway: experiments/_facts_v20_s4.py (failed copy; S3ne unchanged)
Pre-run: S0 d0 4/4; S2 wheat; S3roles land/roles; S3ne bootstrap
Counters: EOD d10 herd=6; after d11 land+carpet owned→14; owned≤14 after;
     BUY_ANIMAL total ≤14; PLANT MELON after d0=0; d0 4/4 WHEAT 7 MELON 12;
     first land d6; d6 STRAW≥4 NE STRAW>0; 0 escapes contested;
     bank vs 67325/72410 not down — seed 8 FAIL
```

## S4 pace card — 12 after carpet, 14 from d13 (2026-09-16)

```text
Kind: rewrite (facts 15 + 17)
Previous / next: S3ne → S4
HORIZON Actual filled? yes (`_trace_horizon_s3ne.py` + failed dump-8)
Gap: dump-8 on d11h15 left 14 owned / 6 placed; seed 8 milk −10k.
     S3ne already buys 6 at d11h15 (owned 12 / pens 6) and +2 on d13
     to 14; leftover after land2+$500 $6.2k/$5.2k funds that. The
     failed copy only flattened those two steps into one afternoon.
Now: hold 6 through d10; after land2+carpet target 12 (d11–12);
     target 14 from d13; cap 14; stop. Mix picks which. Not dump-8.
     Not 8-by-d6. Not shop-mix count ramp to 18.
Result: pictures held — EOD d10 herd 6; d11h15 → 12; d13 → 14; stop;
     no d19 extra; d0 4/4; MELON after d0=0; d6 STRAW 5; 0 escapes.
     Seed 0 **67,325 → 68,768 (+1,443)** (skipped d19 cow). Seed 8
     **72,410 → 56,444 (−15,966)** FAIL. Identical through d15
     (14 owned / 13 placed / 13 pens). S3ne then builds pens to **16**;
     cap-14 stops at 14. d20 cash still ~tied; d21–d29 STRAW 29.5k→22.2k
     and milk 23.6k→15.7k. Do not clip the pen-lead. Keep S3ne.
Fights: tape 8/10/12/13/14 on this cash; dump-8 after carpet;
        shop-mix count ramp to 18; waiving first-land $500 floor
Throwaway: experiments/_facts_v20_s4_pace.py (failed copy; S3ne unchanged)
Pre-run: S0 d0 4/4; S2 wheat; S3roles land/roles; S3ne bootstrap
Counters: EOD d10 herd=6; EOD d11 owned=12 not 14; EOD d13 owned=14;
     BUY_ANIMAL none past 14; PLANT MELON after d0=0; d0 4/4 WHEAT 7
     MELON 12; first land d6; d6 STRAW≥4 NE STRAW>0; 0 escapes;
     bank vs 67325/72410 not down — seed 8 FAIL
```

## S4 lead card — buy-stop 14, pens still lead (2026-09-16)

```text
Kind: rewrite (facts 15 + 16 + 17)
Previous / next: S3ne → S4
HORIZON Actual filled? yes (`_trace_s4_pace_vs_s3ne.py`)
Gap: 12-then-14 cap-14 clipped BUILD (pens 16→14); seed 8 STRAW/milk
     collapsed after d20. d15 farms were identical. S3ne seed 8 already
     stops *buying* at 14 and ends 14 owned / 16 pens. Seed 0 extra is
     a d19 cow toward 18.
Now: BUY calendar 4/5/6/12/14 (stop owned). BUILD uses pen target 18
     so pens can lead. Mix picks which. Not dump-8. Not cap-14-on-BUILD.
Result: pictures held. Seed 0 **67,325** (same). Seed 8 **72,410**
     (same). EOD d11 owned=12; d13 owned=14; seed 8 pens **16**; 0 escapes.
     d0 4/4; MELON after d0=0; d6 STRAW 5. On these seeds mix already
     totals 14 — the d19 cow is a replacement (cumulative BUY 15, EOD 14
     then 13), not a 15th head. The 18 buy ramp is now closed in code.
     Keep throwaway. Do not port.
Fights: dump-8; routing BUILD through the owned-14 cap; tape 8-by-d6;
        shop-mix *count* ramp past 14 owned
Throwaway: experiments/_facts_v20_s4_lead.py
Pre-run: S0 d0 4/4; S2 wheat; S3roles land/roles; S3ne bootstrap
Counters: EOD d10 herd=6; EOD d11 owned=12 not 14; EOD d13 owned=14;
     later BUY_ANIMAL none past 14 except replacement; seed 8 pens ≥ 16;
     PLANT MELON after d0=0; d0 4/4 WHEAT 7 MELON 12; first land d6;
     d6 STRAW≥4 NE STRAW>0; 0 escapes; bank vs 67325/72410 not down
```

## S2 session card — wheat empty-tile default (2026-09-16) **← reverted**

```text
Kind: supplement (facts 22 + 28); fact 38 plant-half is already folded
Previous / next: S0 → S2
HORIZON Actual filled? yes (seeds 0 and 8)
Gap: field WHEAT EOD d0 is 0 vs v20 7; leftover wait-empty; $450 seed floor
     blocks BUY_SEED WHEAT while the farm is broke-on-purpose
Was: leftover_occupant returns None between windows; home wheat only d13+;
     refuse WHEAT off-home; fact39_home_wait; prerun still wants SW WHEAT=0
Tried: underfoot empty → window occupant else WHEAT from d0; BUY_SEED WHEAT
     follows empties; waive $450 on wheat seed only; no K-walk for wheat
Result: d0 field WHEAT 7 (was 0); PLANT WHEAT d0=9 both seeds; d0 4/4;
     d3 cow yes; land d7; 0 escapes. Contested bank seed 0 **8,713**
     (was 26,429) / seed 8 20,764 (was 8,269). Seed 0 tripwire FAIL.
     Throwaway restored.
Fights: fact 38 d13+ home-only; Path C F7 force-wheat-from-low-stock;
        prerun_audit "fact22 SW WHEAT=0" (stale vs T1)
Throwaway: experiments/_facts_v20.py (restored)
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

**The hole is still T1, now worked as sequential states.** Working farm:
`experiments/_facts_v20_s4_lead.py` (**67,325 / 72,410**). **S1 reverted.**
**S2 pictures held, bank tripwire failed as written.** **S2h / S3d6 /
S3home reverted.** S3 not landed (seed 8 −146 vs S2). **S3roles pictures
held.** **S3ne pictures held.** **S4 dump-8 failed. S4 cap-14-on-BUILD
failed. S4 lead pictures held** — buy 12 then 14, pens lead (seed 8:
16 pens); bank not down vs S3ne. Do not retry 8-at-once. Do not clip
pens. Do not carpet NE. Do not port `main.py`. Named mix **fallback**.
**S4 lead holds.** d1h0 BUY×4 is a no-op (aff 0). Overnight leftover
extra-buy **failed the bank** (44,677 / 52,807 with hire floor; 32k / 49k
with sheep-first). Same-tile CARE before feed-walk failed at 5+5. Extra
runner cannot mint wool. Leftover seed cap failed (24,740 / 70,300).
Keep `_facts_v20_s4_lead.py`. Not leftover-2 at h0. Not 8-by-d6. Not
S3d6 walk. Not S1 sell-fert. Not CARE-before-feed-walk. First wool 9 vs
12 is not payable on this farm as written.

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
| SE / 3rd `BUY_LAND` ($4k) | 33, cash after carpet | v20 scale runs on 3 quads; with-SE contested seed 0 bank ~6k, no-SE ~45k. Re-add only with a new fact card + contested proof. |
| MELON walk-to-shed **before/during feed** or uncapped multi-day DROP | 7, 18–20, 34 | Pre-feed / uncapped DROP starved herd or flooded shed. Fact 34 keeps **d10 hour≥16 room-capped** DROP only. |
| STRAW held→DROP→SELL drip (fact 40) | STRAW `$` | When DROP fired, season STRAW `$` worsened (harvest diversion). The acreage it was compensating for is now fact 27 as rewritten. |
| Shop-mix *count* ramp after d10 (cap 18, 21 head) | 15, 17, 7 | Bought 21 head against an 18 cap contested and still lost placed animals late (18 → 16, d25–27): the late herd arrives with no wheat behind it. Rewritten S4 pace-to-14 from melon $ after second land is not this ramp. |
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
- [ ] Fact 15: herd 4 d0 / 5 d3 / 6 through d10, 12 after carpet (d11–12), 14 from d13 stop *buying*; pens may lead; no dump-8
- [ ] Facts 9–13: the turn `BUY_ANIMAL` emits is sell fert → buy animal → (hire/seeds after), including catch-up hours; on every other day fert still sells the day it is collected (fact 9 — no existence-hold)
- [ ] Fact 27: STRAW lands on NW/NE d5–8 **and** as the d11 SW carpet; `PLANT MELON` after d0 = 0
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
