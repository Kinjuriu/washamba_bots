# The sell-advance rim on `public_farm2945` — the base already has it, at K = 40-48

**Date 2026-09-21.** Base: `agents/public_farm2945.py` (thomastschinkel's "2945 Farm",
Apache-2.0, submission `56269928`), **unmodified** — as are every other agent and
`main.py`. New: `agents/farm2945_rim.py` (base embedded byte-verbatim below an 8-line
header, one overlay appended, `agent` the last callable, both levers flags at the top of
the overlay) and `tests/test_farm2945_rim.py` (19 stdlib `unittest` tests). Nothing was
committed, nothing was submitted, and no Kaggle API or dataset call was made.

`agents/farm2945_rim.py` sha256 `1f3603ef45054071cd95493466f9662c52a11326b7536ef78f603463d2d62850`
(866,587 bytes); base `agents/public_farm2945.py` sha256
`b50ccd3c72f87171eac8af0cbb9c11966ee1a3dee0412a3862e03631af4ea5ee`, unchanged.
Full suite after this work: **254 tests, OK (1 skipped)**.

---

## 0. Answers up front

| question | answer |
|---|---|
| **What does the base's own "sale lead" layer already do?** | Three layers, not one. A one-step `_sell_lead` with a quantity-conserving suppression pass; a **multi-step `_r36_reserve`** that is the brief's `_advance_sells` already written, with a superset of its guards and a per-due-step debt ledger; and `_v224_sales_first`, which is `MARGIN_LEVERS.md` lever 2 verbatim. **The horizon is not 6 — the v9 RACE layer pins it at `min(48, max(40, rival_lead + 12))` on every step.** The base ships a K = 40-48 rim. |
| **Is the opening trick available?** | **It is already in the base.** Step 0 emits `[['BUY_PRODUCT','WHEAT',20], ['SELL','WHEAT',15]]` — Özer's V45 wheat round trip, the mechanism jaxa623's "2802" notebook documents. Only its *size* is untested. |
| **Does any K clear the mirror bar (≥ 22-10 of 32)?** | **No.** The best value, K = 96, reads **21-11, mean +100** — and the control's own identical-code noise on the same harness is **±1,131 on a single seat-result**, so +100 is not a measurement. |
| **Ship anything?** | **No.** `agents/farm2945_rim.py` ships with `RIM_K = None` and `RIM_OPENING_N = 0`, at which it is behaviourally identical to the base (seed-0 gate `['DONE','DONE']`, **72,101 / 72,762**, the base's own banks to the dollar). |
| **What this changes beyond this task** | The brief's premise — "a rim that beats copies is the one lever the field cannot answer after the freeze" — **is false on this base.** The field's `farm2945` copies carry the *adaptive* answer: RACE reads the rival's observed sell lead and sets its own horizon to that lead + 12. A fixed K is out-led automatically by every copy. See §10. |

---

## 1. What the base's own sale-lead layer already does

`agents/public_farm2945.py`'s header advertises "Shop0908 production, sale lead". That is
three separate layers, and together they are already `_advance_sells(K)` with a larger K
than anything the router lineage has ever shipped.

**(a) `Chassis._sell_lead` (l.636) — the one-step lead.** Sells what `tape[step+1]` plans
to sell, now, for any product other than WHEAT/FERTILIZER that the projected shed already
holds, and records the lot in `next_sup["suppress"]` so `Chassis._apply_suppression`
(l.607) nets it out of step+1's own SELL. Quantity conserved. Gated off when
`step % 4 == 0` (the town consumes every 4 steps, so leading across a consumption tick
buys nothing) and at shop-unlock boundaries (`step % 72 == 0`). Two later layers wrap it:
`_r36_native_lead` (l.1667) restricts the native path to `288 <= step < 696`, and
`_v9_racepx_lead` (l.3923) runs its own copy that only leads items quoted at or above
their base price (`V9_RACEPX_BASE`).

**(b) `_r36_reserve` (l.1683) — the multi-step advance.** This is the brief's
`_advance_sells`, already written. Window `192 <= step < 696`. For every product it walks
the tape's own future steps `step+1 .. step+horizon`, reserves at each due step the
quantity that step planned to SELL minus what is already owed there, caps the total by
the projected shed, and emits the sum as one merged `['SELL', item, qty]` now. Every
reserved lot is written into
`players[seat]['sell_state']['r36_debts'][due_step][item]`, and `_r36_suppress` (l.1671)
subtracts that debt from the emitted SELL when the episode reaches that step.

Its guards are a superset of the ones the brief asked for:

| brief's guard | the base's implementation |
|---|---|
| never for WHEAT/FERTILIZER round trips | `break` at a future `BUY_PRODUCT item`; skip any item with a `BUY_PRODUCT` in this turn's market |
| never ahead of a same-turn `BUY_PRODUCT` of the same item | the same `blocked` set, plus items with a pending courier `PICKUP` |
| never exceeding the 10-order cap | `if not available or len(market) >= 10: continue` |
| quantities unchanged | the `r36_debts` ledger, netted out by `_r36_suppress` |
| sells at the FRONT, relative order preserved | `_v224_sales_first`, see (d) |

**(c) The horizon *is* K, and it is 40-48, not 6.** `_r36_reserve` reads
`_V9_ITEM_HZ[seat]` when set and `_R37_HORIZONS[seat]` otherwise. `_R37_HORIZONS`
(l.1904-1918) is 2, raised to 3 on a six-turn rival-similarity streak, to 4 on a probe
match, and hard-set to 4 for `288 <= step < 696`. But the v9 RACE layer (l.3853-3869)
overwrites `_V9_ITEM_HZ[seat]` on **every** step with

    horizon = min(V9_RACE_MAX, max(V9_RACE_DEFAULT, observed_rival_lead + V9_RACE_MARGIN))
            = min(48, max(40, lead + 12))

for CARROT, TOMATO, STRAWBERRY, MELON, EGG, MILK and WOOL. `end` is
`step + max(horizon.values())`, so WHEAT and FERTILIZER ride along at the same number.
**The shipped base is already a K = 40-48 rim, and the brief's sweep values {3, 6, 9, 12}
are all shorter than what it does today.**

**(d) Order index is handled too.** `_v224_sales_first` (l.1501) is
`docs/MARGIN_LEVERS.md` lever 2 verbatim: bubble every SELL to the front of the market
list, preserving relative order, refusing to move one past a `BUY_PRODUCT`/`BUY_ANIMAL`
of the same item. It runs at `step >= 144` (l.1524) and again at `step >= 288` (l.1739),
and `_r37_reorder_sales` runs a quote-aware reorder at `step >= 288` as well. There is no
front-placement left to add.

**(e) The opening trick is in the base as well.** Step 0's emitted market is, on both
seats, `[['BUY_PRODUCT','WHEAT',20], ['SELL','WHEAT',15]]` — Ahmed Berat Özer's V45
first-turn wheat round trip, the exact mechanism jaxa623's "2802" notebook documents and
sweeps ("EXP-173 isolate opening market sequence" appears in this file's own header). It
sits at n = 20 against jaxa623's swept plateau of 25-50, so the only untested thing is
the size, not the trick.

---

## 2. What was built, and why it is two knobs rather than a second ledger

Porting `router_yuan_nf_trim._advance_sells` onto this base as written would be a
**double-advance by construction**: two ledgers reserving the same tape lots, with only
the base's ledger able to suppress them. So `agents/farm2945_rim.py` exposes two knobs on
the base's own rim:

* **`RIM_K`** — `None` leaves the adaptive band alone (the control); an int collapses
  `V9_RACE_DEFAULT` and `V9_RACE_MAX` onto it, which makes
  `min(MAX, max(DEFAULT, lead + MARGIN))` identically K for every raced item and every
  observed rival lead. `RIM_K = 0` disables the multi-step reservation entirely
  (`end <= step` returns immediately); the base's own one-step `_sell_lead` survives.
  It does not touch the `_R37_HORIZONS` fallback (2/4), which only fires if the RACE
  layer raises.
* **`RIM_OPENING_N`** — `0` leaves step 0 alone; an int rewrites the quantity of the
  step-0 index-0 `BUY_PRODUCT WHEAT` order **in place**, so no base order moves and
  nothing can be displaced past index 9. (If the base ever stopped emitting the pair the
  overlay inserts it at 0/1, and refuses when that would not fit in 10 orders.) The
  paired SELL is deliberately not resized: the base buys 20 and sells 15, and the 5 WHEAT
  it keeps is day-0 animal feed.

Sweep variants are generated by substituting those two lines; nothing else in the file
differs between them.

---

## 3. The prediction, written before the results landed

`_v9_race_update` *observes the rival's lead* and sets the horizon to
`min(48, max(40, rival_lead + 12))`. In a mirror against `public_farm2945`, every K < 40
is therefore answered by a rival sitting at 40-48, and K = 96 meets a rival pinned at 48.
Predicted: K ∈ {0, 3, 6, 9, 12, 24} lose the mirror; K = 96 is the only value that *can*
clear 22-10, and if it does it is Lever-3 shaped — price taken off a copy rather than
bank added — so the absolute self-play column decides it.

**The data agrees with all of it.**

---

## 4. Mirror — candidate vs `agents/public_farm2945.py`, seeds 300-315, both seats

`experiments/tapes/run_agents.py`, 32 seat-results per row.

| K | record | mean | median | worst seat-result |
|---|---|---|---|---|
| **control (`RIM_K = None`)** | **3-3 of 32** (26 exact ties) | **+0** | +0 | −1,131 |
| 0 (reservation off) | 6-26 | **−507** | −405 | −3,192 |
| 3 | 16-14 | −201 | +22 | −2,552 |
| 6 | 16-16 | −114 | −2 | −2,291 |
| 9 | 14-18 | −222 | −61 | −2,167 |
| 12 | 19-13 | −84 | +83 | −2,273 |
| 24 | 15-13 | −41 | +0 | −1,121 |
| **96** | **21-11** | **+100** | +98 | −1,118 |

**Read the control row first.** Identical code against identical code is 3-3 with a mean
of exactly **+0** and a per-seed delta of exactly zero on all 16 seeds — the six non-ties
are three pairs of exact seat mirrors, the same seat asymmetry `v3_results.md` §1.2
records. That is the harness telling the truth. But its **worst single seat-result is
−1,131**: on this harness, identical code can differ by eleven hundred dollars on one
seat. Every row above except K = 0 has a mean inside that band.

So: **K = 0 is a real, decisive loss** (6-26, −507 mean, and the worst floor of the
sweep) — which is the sweep's one positive finding, because it proves the base's
reservation layer is load-bearing rather than decorative. Everything from K = 3 to K = 24
is a coin flip with a negative mean. K = 96 is the best row at 21-11 / +100, **one win
short of the 22-10 ship bar and a tenth of the harness's own noise floor.**

The monotone shape 0 → 96 is exactly what §3 predicted: the further below the rival's
adaptive 40-48 you pin your own horizon, the more of your lots price *after* theirs.

---

## 5. Absolute self-play bank — candidate vs itself, seeds 300-307, both seats

| K | mean | median | floor | vs base |
|---|---|---|---|---|
| **control (`RIM_K = None`)** | **89,667** | 90,443 | 61,836 | — |
| 12 | 90,082 | 90,856 | 61,963 | **+415** |
| 24 | 89,732 | 90,594 | 61,868 | +65 |
| 96 | 89,731 | 90,350 | 61,685 | +64 |

**The control reproduces `v3_results.md`'s base reference of 89,667 to the dollar**, which
is what makes this column readable at all — the harness and the seed set are the same ones
every other Phase-3 measurement used.

Note the sign flip against §4: **K = 12 loses the mirror (19-13, −84) and banks the most
in absolute terms (+415)**, while K = 96 wins the most mirror games and banks +64. That is
`MARGIN_LEVERS.md` "Lever 3 that is not a lever" reproducing itself on a different base:
the mirror record is price taken off a copy, not bank added. Neither delta is outside the
harness's own noise, so neither is a finding — but the *shape* is the one that file already
warns about, and it is the reason the mirror record alone must not pick K.

## 6. vs `agents/router_yuan_nf_trim.py`, seeds 300-307, both seats

| K | record | mean | worst |
|---|---|---|---|
| **control** | **16-0 of 16** | **+15,982** | +5,395 |
| 12 | 16-0 | +15,913 | +5,406 |
| 24 | 16-0 | +15,965 | +5,426 |
| 96 | 16-0 | +16,035 | +5,403 |

The control again reproduces the recorded base figure (16-0, +15,982) exactly. The rim is
invisible on this harness: `nf_trim` is 15,900-16,000 behind at every K, so the `>= 14-2`
bar is met by everything and separates nothing.

## 7. The opening trick

Already in the base at n = 20 (§1e). Resized to jaxa623's swept optimum n = 30 —
`BUY_PRODUCT WHEAT 30` at index 0, the paired `SELL WHEAT 15` untouched — mirror against
`public_farm2945`, seeds 300-315, both seats:

| build | record | mean | worst |
|---|---|---|---|
| `RIM_K = None`, `RIM_OPENING_N = 30` | **0-32 of 32** | **−4,797** | −8,890 |
| `RIM_K = 96`, `RIM_OPENING_N = 30` | **0-32 of 32** | **−4,702** | −8,666 |

**A decisive, unanimous loss, and the mechanism is the one jaxa623's own notebook warns
about.** The attack works by making the *rival's index-1 order* dearer, and it pays when
that order is a **BUY** an exactly-funded opponent then cannot afford. Against this base
the rival's index-1 order is `SELL WHEAT 15`. A bigger index-0 buy depletes market wheat
inventory, which **raises the price their sell clears at** — we pay the spread on ten
extra units and hand them the proceeds. jaxa623's own generalisation applies verbatim:
*"an optimum measured against one opponent is not an optimum."* His n = 30 was swept
against a 70-unit rival whose index-1 was a purchase.

So: the trick is present, it is sized for the field the base was tuned against, and **it
must not be resized upward for a mirror match.** Whether n = 20 is right against the
*non*-`farm2945` half of the ladder is untested here and would need a panel opponent whose
day-0 index-1 order is a buy.

## 8. Gates

Seed-0 pre-submit gate, `agents/farm2945_rim.py` (shipped flags) against itself:
`['DONE','DONE']`, **72,101 / 72,762** — the base's own banks, and not $3,000.

Per-turn timing, one full 720-turn episode (seed 305), every emitted observation replayed
through a fresh module instance:

| build | turns | max | p99 | mean | import |
|---|---|---|---|---|---|
| `agents/public_farm2945.py` | 719 | 61.7 ms | 6.1 ms | 1.25 ms | 38-50 ms warm |
| `agents/farm2945_rim.py` (flags off) | 719 | **56.6 ms** | 6.0 ms | 1.29 ms | **38.7 ms warm** |
| `RIM_K = 96` | 719 | 48.8 ms | 5.9 ms | 1.26 ms | ~123 ms cold |

Against the 1,000 ms `actTimeout` and the brief's 500 ms bar there is no exposure: the
worst turn in the whole season is 57 ms and the 99th percentile is 6 ms. The three maxima
differ by more than the overlay could plausibly cost, so the spread is machine noise, not
a lever cost. The base carries no base85+zlib tape blob, so its import is tens of
milliseconds rather than the 1.4 s the router lineage pays.

**Sell volume, measured rather than argued.** The structural proof that this is not a
double-advance is that there is only one ledger: the overlay tunes `r36_debts` rather than
adding a second reserve pass. The empirical check is total SELL units per product over a
whole self-play episode (seed 305):

| build | WHEAT | CARROT | TOMATO | STRAWBERRY | MELON | EGG | MILK | WOOL | FERT |
|---|---|---|---|---|---|---|---|---|---|
| flags off | 17,363 | 17,066 | 6,000 | 6,340 | 6,072 | 8,096 | 8,340 | 6,239 | 10,351 |
| K = 96 | 17,363 | 17,066 | 6,000 | 6,344 | 6,072 | 8,096 | 8,342 | **6,226** | 10,351 |
| K = 12 | 17,373 | 17,066 | 6,000 | 6,372 | 6,072 | 8,098 | 8,374 | 6,240 | 10,351 |

The movers are WOOL −13, STRAWBERRY +4/+32, MILK +2/+34 and WHEAT +10 — **under 0.5% on
every line, and not all of one sign.** That last part is the tell: a double-advance would
raise *every* premium product, because every one of them would be sold twice. What this is
instead is route drift — RACE reads the rival, a K-changed rival behaves differently, the
shop draw and downstream harvest schedule shift slightly, and the tape sells marginally
different totals. **K changes when lots price, not how many are sold.**

## 9. Ship decision

| criterion | best candidate (K = 96) | verdict |
|---|---|---|
| mirror ≥ 22-10 of 32 | **21-11** | **FAIL** |
| absolute self-play ≥ 89,667 − 500 | 89,731 | pass |
| vs `nf_trim` ≥ 14-2 | 16-0 | pass |
| no step over 500 ms | 56.6 ms max | pass |

**21-11 is not "one game short."** The mean behind that record is **+100** against an
identical-code noise floor of **±1,131 per seat-result** (§4, control row). At that mean the
record is a coin toss that happened to land 21-11; re-sampling on four more seeds could as
easily land 16-16 as 24-8, and a 22-10 obtained that way would be a sampling artefact, not
a lever. **Do not re-run this sweep with more seeds hoping to clear the bar** — the thing to
measure is not K.

**Shippable configuration: none.** `agents/farm2945_rim.py` stays at `RIM_K = None`,
`RIM_OPENING_N = 0`, where it is the base. The opening trick is a decisive loss in the
mirror and is not a candidate at any K.

## 10. What this changes beyond this task

The brief's premise was that *"a rim that beats copies in the mirror, at near-zero absolute
cost, is the one lever the field cannot answer after the freeze."* **On this base that is
false, and the reason is worth carrying into T8/T9.**

`_v9_race_update` does not use a fixed lead. It **watches the rival's sells, measures how
far ahead of the tape's own schedule they landed, and sets its own horizon to that lead
plus 12**, clamped to 40-48. Every `farm2945` copy in the frozen field therefore carries
the answer to a fixed-K rim already compiled in: lead them by K and they lead you by
K + 12, up to the clamp. That is why the sweep is monotone in K and why even K = 96 —
double the clamp — buys 21-11 and $64.

Three consequences:

1. **`docs/superpowers/plans/2026-09-21-endgame.md` Task T8 ("final K sweep") is answered
   for this base, and the answer is "no K".** The lever exists on the router lineage
   (`LEAD_K` in `router_yuan_nf_trim.py`) because that base has a *fixed* rim.
   `farm2945` does not.
2. **The residual is the reservation's window, not its horizon.** `_r36_reserve` (rebound
   at l.3991 to `_v9_racegate_reserve`, a price-gated wrapper sharing the same `r36_debts`
   ledger and the same `_V9_ITEM_HZ` horizon, so `RIM_K` governs both) returns immediately
   outside `192 <= step < 696`. `_r36_native_lead` likewise disables the one-step
   `_sell_lead`'s native path outside `288 <= step < 696`, and `_SETTINGS` has
   `terminal_liquidation` **off**. So **no tape-driven advance of any kind runs before step
   192 or after 696** — days 0-7, the phase `day11_diagnosis.md` says we *win*, and the last
   22 steps of the season. Caveat before anyone cites this as free money: the file carries
   roughly twenty *opportunistic* sell layers (surplus/credit/dead-stock passes at
   l.3012, 3122, 3229, 3534, 3702, 4713, 5111, 5472, 5754 and others, several of which
   `market.insert(0, ...)`), so the early game is not silent — it simply is not running the
   tape-reservation machinery. Widening the window is a one-constant change to a function an
   overlay can rebind, it is untested, and it is a better next probe than another K.
3. **All six levers tried on this base today failed the same way**: the base is already at
   or past the local optimum on everything cheap. What is left is structural (the days 11+
   adaptivity `public_panel.md` names), not a margin knob.

---

## Reproduce

```bash
# Variants are agents/farm2945_rim.py with the two flag lines substituted:
#   RIM_K = None | 0 | 3 | 6 | 9 | 12 | 24 | 96 ;  RIM_OPENING_N = 0 | 30
timeout 2400 .venv/Scripts/python.exe experiments/tapes/run_agents.py \
  "<comma-separated variant paths>" 300 316 agents/public_farm2945.py out/mirror.jsonl
timeout 2400 .venv/Scripts/python.exe experiments/tapes/run_agents.py \
  "<one variant>" 300 308 "<the same variant>" out/selfplay.jsonl      # absolute bank
timeout 2400 .venv/Scripts/python.exe experiments/tapes/run_agents.py \
  "<variants>" 300 308 agents/router_yuan_nf_trim.py out/nftrim.jsonl
.venv/Scripts/python.exe -m unittest discover -s tests
```
