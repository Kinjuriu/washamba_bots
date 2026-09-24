# T5 — Why `public_farm2945` loses after day 11: measured diagnosis

**Date 2026-09-21.** Base: `agents/public_farm2945.py` (thomastschinkel's "2945 Farm",
Apache-2.0, submission `56269928`). Everything below is measured off real recorded
ladder episodes of that submission. No number here comes from a local self-play run or
from the author's notebook text.

Method: `experiments/endgame/replay_tools.py` + the T3 harness convention
(`steps[i][seat]["observation"]` is the state after `i` actions; day *d* starts at
`steps[d*24]`; a step's cash/tile delta is attributed to the day that *decided* it,
`(i-1)//24`). **Both seats' observations carry their own `private`**, so shed, seeds and
per-unit inventories are visible for the opponent too — the copyability doc's assumption
that the opponent's shed is invisible is wrong for a downloaded replay.

The decomposition reconciles exactly: per seat, `Σ daily Δmoney + 3000 = recorded reward`
to the dollar on all 9 episodes, and
`Δbank = Δmarket_net − Δspend` = `−10,861 + 5,203` = **−5,658** against a measured mean
margin of **−5,657** ($1 of rounding).

---

## 1. Reproduction verdict: PASS, 4/4 to the dollar — and byte-identical actions

| episode | seed | f2945 seat | recorded f2945 | replayed | recorded opp | replayed | first action divergence |
|---|---:|---:|---:|---:|---:|---:|---|
| 109694364 | 1361507966 | 0 | 66,533 | **66,533** | 74,922 | **74,922** | **none in 720 steps** |
| 109821873 | 1203526051 | 1 | 111,067 | **111,067** | 112,115 | **112,115** | **none in 720 steps** |
| 109848580 | 1225767790 | 0 | 78,960 | **78,960** | 82,717 | **82,717** | **none in 720 steps** |
| 110055611 | 1520555243 | 1 | 81,680 | **81,680** | 98,006 | **98,006** | **none in 720 steps** |

`agents/public_farm2945.py` replayed in its recorded seat against the recorded opponent
tape on `info.seed` reproduces both banks exactly, and its emitted action stream matches
the recorded one at **every one of the 720 steps** on all four episodes. So:

- **The base is deterministic.** No RNG (`grep` finds no `random` import anywhere in the
  5,766 lines) and no wall-clock branch — the one `perf_counter` (line 1027, the exec'd
  terminal planner) only fills a `planning_ms` telemetry field; the planner's bound is
  `max_simulations`, not time. Nothing reads `remainingOverageTime`.
- **The published notebook is the submitted agent.** The header says v9/3 and the
  notebook text says v9/4; the version question is moot — this file reproduces
  `56269928`'s recorded episodes action-for-action.
- All four replays carry `module_version: 1.32.7`, matching the local engine.

This is the strongest reproduction result in the repo: the T3 gate matched banks but not
action streams (our own agents were the ones being replayed). Here the whole stream
matches, so the harness can be used to attribute a divergence to a specific step.

---

## 2. The episode set

Nine episodes of `56269928` are reachable (4 from `panel/index.json`'s
`farm2945_losses` — re-checked at the end of this work, still 4 — plus 5 more found in
`experiments/endgame/tschinkel_scan_hits.json` and already cached in
`experiments/endgame/rep/`). The record is **2–7**, not 4 losses:

| episode | opponent | opp rating | f2945 | opp | margin |
|---|---|---:|---:|---:|---:|
| 110055611 | ymg_aq | 3041.6 | 81,680 | 98,006 | **−16,326** |
| 109694364 | ymg_aq | 3026.4 | 66,533 | 74,922 | **−8,389** |
| 109766905 | THIRD FARM CLUB | 2985.0 | 123,038 | 129,556 | **−6,518** |
| 109848580 | SpaTaro | 3051.7 | 78,960 | 82,717 | **−3,757** |
| 109666520 | Otter Vibe | 2970.0 | 77,267 | 80,265 | **−2,998** |
| 109821873 | ymg_aq | 3030.3 | 111,067 | 112,115 | **−1,048** |
| 109727399 | Otter Vibe | 2973.5 | 101,926 | 102,489 | **−563** |
| 109856068 | Orbital Terraformer | 3011.1 | 121,286 | 116,869 | **+4,417** |
| 109773242 | mikelou1 | 2953.3 | 115,371 | 108,258 | **+7,113** |

Losses n=7, mean margin **−5,657**. Wins n=2, mean **+5,765**. The two wins are against
2,953 and 3,011, so both clear the 2,700 bar the task allowed; there is no fourth win to
be had in the reachable set.

---

## 3. When the gap opens — day 13, not day 11

Cumulative market-cash gap (farm2945 − opponent), mean over the 7 losses. `market_net` is
exact cash: `Δmoney + hire + land + seed + animal spend`.

| band | farm2945 | opponent | Δ | cumulative Δ |
|---|---:|---:|---:|---:|
| d0–7 | 5,717 | 7,371 | −1,655 | −1,630 |
| d8–10 | 20,330 | 11,140 | **+9,190** | **+7,560** |
| d11–13 | 9,973 | 6,716 | +3,256 | **+11,357 (peak, end of d12)** |
| d14–20 | 35,276 | 48,645 | **−13,369** | +2,861 → −2,553 |
| d21–29 | 38,647 | 46,955 | **−8,308** | **−10,861** |

The author's "we lead until day 10 and lose it all after day 11" is **half right**. The
lead is real and it is the melon race (+9,190 in d8–10). But the lead keeps *growing*
through day 12; the first losing day is **day 13**, erosion is monotone from **day 14**,
and the cumulative gap crosses zero on **day 19**. Peak lead is **+11,357**.

farm2945 also *out-saves* its opponents by **$5,203** a season (hire −2,455, animal
−2,357, seed −391, land ±0), which is why a −10,861 revenue gap becomes only a −5,657
bank gap. It is not losing on cost. It is losing on production after day 13.

---

## 4. Ranked mechanisms

Season revenue by product, mean over the 7 losses (units in brackets):

| product | farm2945 | opponent | Δ$ |
|---|---:|---:|---:|
| TOMATO | **0** (0 u) | 5,990 (90 u) | **−5,990** |
| CARROT | 4,974 (106 u) | 8,682 (189 u) | −3,708 |
| WOOL | 22,496 (179 u) | 25,676 (183 u) | −3,181 |
| WHEAT | 12,885 (350 u) | 15,725 (457 u) | −2,840 |
| EGG | 3,437 (73 u) | 5,512 (120 u) | −2,075 |
| MILK | 19,587 (204 u) | 19,031 (178 u) | +557 |
| STRAWBERRY | 18,032 (248 u) | 17,330 (161 u) | +702 |
| MELON | 15,371 (72 u) | 13,167 (86 u) | +2,204 |
| FERTILIZER | 13,159 (290 u) | 9,714 (208 u) | +3,445 |
| **TOTAL** | **109,942** | **120,827** | **−10,886** |

Ranked by mean bank explained per loss episode, with the day it starts and the
classification against farm2945's own code:

### M1 — the melon program is a single day-0 block: **−6,722/episode, 7 of 7 losses**

`MELON` revenue from day 11 to the end: farm2945 **$0 in 9 of 9 episodes**; opponents
$813–$12,008 (mean $6,722). farm2945 plants **12 melon tiles on day 0**, harvests all 72
units on **day 10**, and holds **0 melon tiles from day 11 to day 29 in 9 of 9 episodes**.
The opponents *stagger* their melon: 4 tiles on day 1 ramping to 13 by day 9, harvested in
waves on days 10–18.

**Split this line before acting on it — the two halves are reachable from completely
different places:**

| window | Δ$ | where the opponent's melon comes from |
|---|---:|---|
| d14–20 | **−6,559** | tiles they planted on **days 4–6** (`first_yield_day` 10 → yields d14–16) |
| d21–29 | −689 | late tiles |

So **97% of M1 is a day-0..6 opening-stagger difference, not a day-11 replant.** Reaching
it means planting fewer melons on day 0 — trading directly against the melon race, which
is the one thing farm2945 currently wins: it realises **$213/unit** on melon against the
opponents' $153 and is **+$2,204** on the melon book season-wide. Not proposed here.

Note also what the 12 melon tiles actually become — traced tile-by-tile, identical in
9 of 9 episodes: **7 WHEAT (planted days 12–13) + 5 COOP/PASTURE structures**. They do
*not* become strawberry.

**Classification (a): a scheduled decision in the tape.** Decoded from
`_ROUTES` (41 route tapes, 719 steps each): across all 41 routes there are **492 `PLANT
MELON` ops and every single one is on day 0**. No melon is planted after day 0 on any
route, under any shop key. No reflex layer plants anything (`V9_CARROT` only rewrites
`PLANT WHEAT` → `PLANT CARROT`).

### M2 — TOMATO is never planted at all: **−5,990/episode, 6 of 7 losses (0 in the 7th)**

farm2945 sells **0 tomato units in 9 of 9 episodes**. The winners hold ~3 tomato tiles by
day 9, ~6 by day 12, **~10 by day 19**, and sell 90 units for $5,990. Per-episode cost
ranges $0–$14,487.

**Classification (c): no code path exists.** Across all 41 route tapes there are **zero
`PLANT TOMATO` ops and zero `BUY_SEED TOMATO` orders**, and no reflex layer can introduce
one — `V9_CARROT` is the only crop-substituting layer and it only maps WHEAT→CARROT. The
agent is structurally incapable of planting a tomato.

This is also the author's own diagnosis, and he records three failed fixes. **The first
one is now mechanically explained, and the explanation is the most useful thing in this
document.** "A tomato overlay on the route's wheat tiles from day 13: 0 gained / 85 lost."
Traced on the 7 ex-melon tiles (episode `110055611`, representative), the tape runs a
tight wheat cycle on them:

```
day 10  HARVEST 7  PLANT WHEAT 7      day 17  HARVEST 3  PLANT WHEAT 3
day 12  HARVEST 2  PLANT WHEAT 2      day 20  HARVEST 4  PLANT WHEAT 4
day 13  HARVEST 5  PLANT WHEAT 5      day 21  HARVEST 3  PLANT WHEAT 3
day 16  HARVEST 4  PLANT WHEAT 4      day 24  HARVEST 4  PLANT WHEAT 4 … to day 28
```

TOMATO is `ongoing`, so the engine's `HARVEST` **does not clear the tile**
(`kaggriculture.py`, `_apply_unit_action`). Put a tomato on a wheat-cycle tile and every
later `PLANT WHEAT` on it no-ops for the rest of the season (`tile is not None`). The
overlay does not add a tomato to a spare tile — it **deletes a 4-day wheat cycle** running
to day 28. That is the −85, and it is why no gate tuning would have rescued it.

M3 is where the only labour-compatible tile-time actually is.

### M3 — the day-11 new quadrant is planted as STRAWBERRY into a book farm2945 then floors

On day 11 the tape performs its only mass planting after day 8: **11 `PLANT WHEAT` + 13
`PLANT STRAWBERRY` per route** (451 and 533 ops across the 41 routes, all on day 11).
Traced tile-by-tile: **all 13 of those strawberry tiles were `LOCKED` at day 10** — they
are the third quadrant, bought that morning. Identical in 9 of 9 episodes, same 13
coordinates. This is new ground, not the melon block, and it is the **only** block of
tiles the tape commits to a single crop for the rest of the season.

The crop mix is then **frozen at 24 WHEAT + 33 STRAWBERRY + 0 of everything else from day
13 to day 21** while the opponents run 14 WHEAT / 4 CARROT / 9 TOMATO / 22 STRAWBERRY /
8 MELON.

STRAWBERRY is `ongoing`, `first_yield_day` 10, `interval` 2 — so the 13 tiles planted on
day 11 deliver on days **21, 23, 25, 27**, exactly into the trough that the earlier
day-5–8 block has already dug:

| day | f2945 STRAW units sold | f2945 $/unit | opp units | opp $/unit | book price |
|---|---:|---:|---:|---:|---:|
| 17 | 16.0 | 150 | 22.9 | 167 | 160 |
| 19 | 17.4 | 92 | 17.9 | 117 | 103 |
| 21 | 26.9 | 39 | 15.4 | 43 | **48** |
| 23 | 20.1 | 18 | 8.4 | 27 | **25** |
| 24 | 21.4 | 18 | 3.9 | 42 | **22** |
| 26 | 17.4 | 50 | 5.0 | 57 | 46 |

farm2945 sells **146 strawberry units on days 21–29 at a mean $40/unit**; the opponent
sells 58 and withdraws. Season-wide farm2945 realises **$73/unit against the opponent's
$104, in 9 of 9 episodes**, while selling 87 more units — the surplus is worth about
**$15/unit at the margin** (18,032 − 161×104 over 87 units). The comparison rate on the
same days is melon at $77/unit and tomato at $67/unit for the opponent.

**Classification (a): tape.** Both the day-11 plantings and the day-21+ SELL schedule are
in the route tapes; the reactive `sell_lead`/`RACE`/`RACEPX` layers move sale *timing*,
not the tile the crop grows on.

### M4 — CARROT arrives on day 23 instead of day 11: −3,708/episode, but only 5 of 7 positive

Tape carrot: **7 ops on day 23, then 156 / 574 / 453 / 82 on days 24–27.** The `V9_CARROT`
reflex (gate: day 10–23, `CARROT/WHEAT` quote ratio ≥ 1.8, ≥ 40 wheat held) fires rarely —
observed 0.3–0.4 tiles/day around days 16 and 20. The opponents carrot continuously from
day 11. Sign-inconsistent (−991 and −721 on two episodes), so this is real but noisy.
**Classification (b): a reflex exists and its gate is too tight**, on top of (a).

### M5 — structure count frozen at 17 from day 16: animal revenue −4,699/episode

farm2945 finishes with **exactly 17 structures in 8 of 9 episodes** (23 once), all filled;
opponents mean **20.4 by day 20** (range 14–25). It spends $2,357 less on animals and
earns $4,699 less from EGG+MILK+WOOL in the losses. In the 2 **wins** the same 17-structure
program is farm2945's margin (MILK +6,184, WOOL +7,885) — so this is a ceiling, not a
defect. **Classification (a): tape** (`BUILD_PASTURE`/`BUILD_COOP` and `BUY_ANIMAL` are
scripted; `V9_HERD` changes only the *species* of the day-10 animals, not the count).

### M6 — about one hand/day fewer on days 14–21

farm2945 runs 10.4–11.3 hands against 11.6–12.3, and spends **$2,455 less on hiring all
season**. Given fibonacci hire pricing this is a few hundred dollars of labour buying an
opponent several hundred extra unit-turns a day. **Classification (a): tape** (`HIRE`
orders are scripted; `R53_LABOR` aligns hands to the tape, it does not size the crew).

### What the wins prove

M1 (no melon after day 10) and M2 (no tomato ever) are present in **both wins** as well as
all seven losses — they are invariants of farm2945, not situational errors. In the wins
farm2945 still forgoes $985–$4,627 of tomato and $-261–$3,659 of late melon and wins
anyway, on animal revenue. **So the mechanisms above are a standing liability that only
bites against an opponent who works the tomato and late-melon books** — which is exactly
what the 3,000+ band does and what `mikelou1` and Orbital Terraformer did not.

---

## 5. The intervention — one rule, on 13 tiles, worth about $2,000

**There is exactly one labour-compatible place to put a different crop**, and it is much
smaller than the mechanisms above. Stating that plainly is the point of this section: M1
and M2 are worth $6,722 and $5,990 a season, but almost none of that is reachable without
rewriting the labour tape.

Why only one place. A crop substitution is free only if the tape's existing `WATER` /
`HARVEST` / `PLANT` schedule on that tile still makes sense for the new crop:

| candidate block | tiles | verdict |
|---|---:|---|
| ex-melon tiles, days 12+ | 7 | **blocked** — a 4-day `HARVEST`+`PLANT WHEAT` cycle to day 28. An ongoing crop is never cleared by `HARVEST`, so every later `PLANT WHEAT` no-ops. This is the author's −85. |
| day-5–8 strawberry block | 20 | **not worth it** — yields d15–21 at $150–174/unit ($560/tile). Tomato would return ~$270/tile. |
| melon block on day 0 | 12 | reachable, but it is the melon race farm2945 wins (+$2,204 season). Out of scope. |
| **day-11 third-quadrant strawberry** | **13** | **the one free slot** — see below |

The tape's own schedule on those 13 tiles (traced from the recorded action stream,
episode `110055611`): `PLANT STRAWBERRY` + `WATER` on day 11, `WATER` on almost every day
after, `FERTILIZE` on d20 and d24, `HARVEST` on d21/22/23/24/25/27/29, then **`DIG` on
days 27–28** and 5 `PLANT WHEAT`. TOMATO is also `ongoing`, so every one of those ops is
still valid for it: watered daily, harvested on the same cadence, dug out at the same
time. **Zero labour change.**

### The rule

> **At day 11, when the tape issues `PLANT STRAWBERRY` on a tile that was `LOCKED` on
> day 10 (the freshly bought quadrant), plant `TOMATO` instead** — all 13 — **and prepend
> `BUY_SEED TOMATO 13` ($650) to that turn's market list.** Guard: only while the live
> STRAWBERRY tile count is already ≥ 20 (measured: it is exactly 20 at day 11 in 9 of 9)
> and bank ≥ $2,000 (measured day-11 bank: $15,231–$18,923 across the 9 episodes).

Measured arithmetic, from the engine rules and the observed price path:

- **What the 13 strawberries actually earn.** 4 ticks each (d21/23/25/27) = 52 units, at
  the measured book prices $48 / $25 / $30 / $49 → **≈ $1,976**.
- **What 13 tomatoes earn instead.** Planted day 11, `first_yield_day` 8, `interval` 1,
  `max_yield` 4 → ticks at the start of days 19, 20, 21, 22. The tape's day-21 `HARVEST`
  collects the first three (`yield_units` accumulates while unharvested); the 4th tick's
  unit is largely lost to `max_lifespan_step` decay from day 23. So ~3 units × 13 = 39
  units at the measured TOMATO quote of **$72** → **≈ $2,808**.
- **Plus strawberry-book relief.** Removing 52 units from our own d21–27 selling should
  lift the price on the 94 units that remain; our realised rate there is $40/unit against
  the opponents' $104. Not modelled precisely — call it the upside, not the case.

Net expectation: **roughly +$800 direct, +$1,000–2,000 with the book relief.** That is
below this repo's usual bar and it will not by itself close a −5,657 mean margin.

**The TOMATO book is the reason to try it anyway.** Its quote **rises monotonically from
$60 to $75 across all 30 days in every episode** — neither player ever moves it, because
the town consumes more tomato than both sides supply. It is the only book in the game
where farm2945 can add supply without paying price impact. Every other book it touches it
floors (STRAWBERRY $184 → $22, MELON $271 → $84, MILK $200 → $41).

**Harness read.** 13 tiles is small, so expect this to move only the close games. Should
flip: `109727399` (−563) and `109821873` (−1,048); possibly `109666520` (−2,998). Must not
break: the two wins `109773242` (+7,113) and `109856068` (+4,417). Near-no-op expected on
`109848580` (−3,757) — the one opponent that *also* ignored tomato, so the book there is
even emptier; if the rule **hurts** on that episode the pricing above is wrong. It should
not be expected to rescue `110055611` (−16,326) or `109694364` (−8,389).

**Read the harness the way T3's docstring says:** loss→win flips and any win→loss, not
mean Δ bank — the opponent tape is frozen and goes off-path the moment we diverge.

### The bigger lever, named but not proposed

The −6,559 of d14–20 melon is the largest single reachable number in this diagnosis and it
lives at **day 0**: plant 6 melons instead of 12, and the other 6 on days 4–6, so they
yield on days 14–16 the way the winners' do. It is not proposed because (a) it trades
against the melon race, the only phase farm2945 wins, (b) it needs day-0..6 labour
rerouting, not a crop-name substitution, and (c) nothing here measures what the day-8–10
melon price would do at 36 units instead of 60. It should be screened in `bptk.py`'s
contested mode before a real episode is spent on it.

---

## 6. What I could not determine

- **Whether the rule actually pays.** This is a diagnosis; nothing was implemented or run.
  The mechanism bank figures are the *opponents'* revenue on books farm2945 ignores — an
  upper bound on what exists, not a prediction of what farm2945 would capture. The
  intervention arithmetic in §5 is derived from the engine's yield rules plus the measured
  price path; the tomato-yield figure (~3 units/tile) in particular is **derived, not
  simulated** — the exact interaction between tomato's `max_lifespan_step` decay from day
  23 and the tape's day-23/25 `HARVEST` on those tiles should be checked by running it.
- **The strawberry-book relief is not modelled.** It is the larger half of the rule's
  claimed value and it is the half I did not compute — it needs the actual `market_price`
  curve run against the counterfactual selling schedule, or just a harness run.
- **n = 9, and 3 of the 7 losses share one opponent** (ymg_aq, submission `56265958`).
  The three ymg_aq episodes are also where the melon gap is largest (10,080–12,008), so
  M1's mean is partly one opponent's style. M2 is spread more evenly (6 different
  opponents show a tomato gap).
- **Whether the day-11 branch differs by shop key.** The crop counts are summed over all
  41 routes; the day-11 totals divide evenly (533/41 = 13, 451/41 = 11) and the 13
  strawberry coordinates are identical in all 9 episodes, which spanned 4 different
  `key144` shop keys — but I did not enumerate all 41 routes individually.
- **The melon quote at day 11 varies more than the mean suggests**: per episode it is
  $131, 156, 178, 178, 178, 188, 226, 226, 226. A melon-based rule with a $150 gate would
  not fire on `109773242`. This is why §5's rule is tomato, whose quote is $61–71 with no
  downside tail.
- **Per-product revenue is attributed, not exact.** Daily `market_net` is exact cash;
  splitting a day's cash across products uses units × the day-start quote. Within-order
  price movement is not modelled, so a single product-day figure can be off by a few
  percent. Unit counts *are* exact (recovered from the stock identity, not from SELL
  orders, which request 10,000 at liquidation).
- **Whether the structure ceiling (M5) or the crew size (M6) is worth touching.** Both are
  measured gaps, but farm2945 wins its two wins on exactly that animal program, so the
  17-structure schedule may be at its own optimum. Untested.
- **No 3,000+ *win* exists in the reachable set**, so "what winners do" is measured only
  from the loser's side of 7 games. Getting more `56269928` episodes (or its successor)
  would strengthen every number here.

## Files

Analysis was done with throwaway scripts under `experiments/endgame/` (`_tmp_*`), deleted
after use, on replays already cached in `experiments/endgame/rep/`. Nothing in `agents/`,
`main.py` or any existing tool was modified. No Kaggle API call was made.
