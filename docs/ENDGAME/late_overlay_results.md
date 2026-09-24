# T5 — the late-game overlay on `public_farm2945`: measured, and **both levers fail**

**Date 2026-09-21.** Base: `agents/public_farm2945.py` (thomastschinkel's "2945 Farm",
Apache-2.0, submission `56269928`), unmodified. Overlay: `agents/farm2945_late.py` — the
base verbatim with a post-processing layer appended; the base's `agent` is wrapped, never
edited. Tests: `tests/test_farm2945_late.py`. Spec: `docs/ENDGAME/day11_diagnosis.md` §5.

**Verdict: neither lever ships, and both flags in `agents/farm2945_late.py` are `False`.**
The file is kept because the overlay scaffolding, the guards and the invariant work are
reusable, and because the *reason* lever 1 loses is a structural fact about the base that
changes what the next attempt should be — see §5.

---

## 1. The episode set, and what the control proves

Every reachable `56269928` episode: the 4 `farm2945_losses` verified per-episode in
`experiments/endgame/panel/index.json`, the 3 further losses and 2 wins the diagnosis
found in `experiments/endgame/rep/`, and the 10 **team-name-matched** losses added to the
index while this work ran. **19 episodes, 17 losses and 2 wins**, every one confirmed a
loss/win by comparing the recorded reward against the opponent's in its own replay.

Before any lever was measured, the unmodified base was replayed in its recorded seat
against the frozen opponent tape on `info.seed` — the control:

| | |
|---|---|
| reproduces the recorded bank to **$0** | **17 of 19** |
| does not | 2, both **name-matched**: `109551974` (−212), `109793226` (+248) |

Both misses are a single `SELL MILK` / `SELL WOOL` quantity drifting at one step (308 and
151) and then propagating; everything else matches. So the seat, seed and index
conventions are right on all 19 and the 10 name-matched episodes really are this agent (or
a near-identical sibling). On those two rows the **control column, not the recorded
reward, is the reference** — the drift is ±$250 and explains nothing larger. A fourth
control — the overlay with both flags off — is bit-for-bit identical to the base on all
19, which is what makes the lever columns below attributable.

## 2. The two levers, as implemented

Both are implemented as a **1:1 rename**, not a prepend, and this is the load-bearing
design choice. `interpreter` (`kaggriculture.py:894-941`) runs `_apply_unit_action` for
every unit **before** `_process_market`, so a same-turn `BUY_SEED` settles *after* the
`PLANT` and cannot feed it. The diagnosis's rule therefore needs the buy one turn earlier
— but the tape already does that, and measuring it removed the need for any new order:

| verified on all 19 episodes | |
|---|---|
| seeds held at the start of every day | `{}` — the tape buys just in time |
| day 11 | `BUY_SEED STRAWBERRY` **13** == `PLANT STRAWBERRY` **13** |
| of those 13 plantings, on tiles LOCKED at day 10 h23 | **13 of 13**, 0 elsewhere |
| day 10 | `BUY_SEED WHEAT` **7** == `PLANT WHEAT` **7** |
| of those 7 plantings, on day-0 melon tiles | **7 of 7**, 0 elsewhere |
| day-0 melon tiles | **12** (7 → wheat, 5 → COOP/PASTURE) |

Renaming both sides of a balanced ledger preserves it exactly: no order is added (the
10-order cap is untouched), no order index moves (market orders settle in list-index
lockstep with the opponent), and the engine's atomic-PLANT rule — *all* `PLANT X` requests
drop when a turn's demand for `X` exceeds held seed, `kaggriculture.py:920-931` — is
satisfied identically to the recorded episode. TOMATO seed also costs $50 against
STRAWBERRY's $100, so lever 1 **saves $650** rather than spending $650.

Guards are **latched once per player** at the first observation of the lever's day. A
guard re-evaluated per turn could rename the buys at hour 1 and refuse the plants at hour
13 after a bank dip, which is the one failure mode that costs more than the lever is
worth: the whole turn's planting is dropped and the tape waters an empty tile all season.

* **L1** (day 11): live STRAWBERRY tiles ≥ 20 **and** bank ≥ $2,000. Measured at day 11
  h0: 20 tiles on 18 of 19 episodes, **19 on `109656980`** — so L1 is a deliberate no-op
  there — and bank $14,586–$18,923, never binding.
* **L2** (day 10): ≥1 remembered melon tile **and** bank ≥ $2,000. Measured at day 10 h0:
  **$1,867–$4,159**, so the bank guard *does* bind and L2 is a no-op on `110055611` and
  `109835653`.

## 3. Harness results — all 19 episodes

`experiments/endgame/ladder_replay.py`'s `run()` freezes the opponent's tape, so read
loss→win flips and any win→loss first; mean Δ bank is an upper bound. "d" below is the
change in **margin** (ours − theirs), which is what the tournament scores.

| episode | set | rec. margin | L1 cand. margin | L1 d | L2 cand. margin | L2 d | both cand. margin | both d | flip |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| 110055611 | loss (verified) | -16,326 | -13,841 | +2,485 | -16,326 | no-op | -13,841 | +2,485 |  |
| 109848580 | loss (verified) | -3,757 | -11,342 | -7,585 | -5,636 | -1,879 | -13,085 | -9,328 |  |
| 109821873 | loss (verified) | -1,048 | -14,289 | -13,241 | -4,598 | -3,550 | -18,348 | -17,300 |  |
| 109694364 | loss (verified) | -8,389 | -8,940 | -551 | -11,278 | -2,889 | -10,988 | -2,599 |  |
| 109766905 | loss (diagnosis) | -6,518 | -11,453 | -4,935 | -8,288 | -1,770 | -11,912 | -5,394 |  |
| 109666520 | loss (diagnosis) | -2,998 | -3,130 | -132 | -6,513 | -3,515 | -5,673 | -2,675 |  |
| 109727399 | loss (diagnosis) | -563 | -1,250 | -687 | -5,171 | -4,608 | -4,941 | -4,378 |  |
| 109551974 | loss (name-matched) | -2,646 | -9,713 | -7,067 | 3,953 | +6,599 | -10,910 | -8,264 | L2 loss->win |
| 109612131 | loss (name-matched) | -11,280 | -8,546 | +2,734 | -7,423 | +3,857 | -6,417 | +4,863 |  |
| 109618581 | loss (name-matched) | -16,832 | -10,433 | +6,399 | -19,224 | -2,392 | -11,737 | +5,095 |  |
| 109656980 | loss (name-matched) | -12,454 | -12,454 | no-op | -15,080 | -2,626 | -15,080 | -2,626 |  |
| 109663295 | loss (name-matched) | -18,129 | -11,827 | +6,302 | -11,937 | +6,192 | -5,979 | +12,150 |  |
| 109679411 | loss (name-matched) | -9,092 | -23,921 | -14,829 | -10,040 | -948 | -23,455 | -14,363 |  |
| 109745434 | loss (name-matched) | -10,230 | -12,554 | -2,324 | -11,740 | -1,510 | -14,346 | -4,116 |  |
| 109793226 | loss (name-matched) | -5,382 | -16,698 | -11,316 | -7,221 | -1,839 | -18,803 | -13,421 |  |
| 109798409 | loss (name-matched) | -9,066 | -1,649 | +7,417 | -10,741 | -1,675 | -2,795 | +6,271 |  |
| 109835653 | loss (name-matched) | -12,314 | -27,647 | -15,333 | -12,314 | no-op | -27,647 | -15,333 |  |
| 109856068 | **win** | 4,417 | 1,987 | -2,430 | -9,988 | -14,405 | -7,077 | -11,494 | L2 win->loss; BOTH win->loss |
| 109773242 | **win** | 7,113 | 3,931 | -3,182 | 5,087 | -2,026 | 1,455 | -5,658 |  |

| config | loss→win | win→loss | mean Δ bank | mean Δ margin | margin better / worse |
|---|---|---|---|---|---|
| **lever 1** (tomato) | **0** | 0 | −278 | **−3,067** | 5 / 13 |
| **lever 2** (melon) | 1 | **1** | −552 | −1,525 | 3 / 14 |
| **both** | **0** | **1** | −1,033 | **−4,531** | 5 / 14 |

Split by set, so a mismatch in the name-matched ten cannot hide a break:

| | L1 Δ bank | L1 Δ margin | L2 Δ bank | L2 Δ margin |
|---|---:|---:|---:|---:|
| 7 verified + diagnosis losses | −557 | −3,521 | −495 | −2,602 |
| 10 name-matched losses | +65 | −2,802 | +724 | +566 |
| **2 wins** | **−1,015** | **−2,806** | **−7,124** | **−8,216** |

**Neither close loss the diagnosis named as the one to flip does flip.** `109727399` goes
−563 → −1,250 under L1; `109821873` goes −1,048 → **−14,289**. The rule's own "must not
break" cases both get worse on margin, and lever 2 turns `109856068` (+4,417) into a
**−9,988 loss** outright. The one loss→win — lever 2 on `109551974`, +11,760 bank — is on
one of the two episodes the base does *not* reproduce and is roughly six times larger than
the lever's arithmetic can produce: exactly the kind of gain the harness docstring warns is
the frozen opponent going off-path, not a real flip. (Its control drift is −212, so the
non-reproduction is not what makes it untrustworthy — the frozen tape is.)

**Ship criteria (plan T5): flips the two named close losses — no. Breaks 0 wins — L1 yes,
L2 and both no. Mean Δ ≥ +1,000 — no, on any configuration.**

## 4. The action-stream diff is clean; the *consequences* are not

The per-day op diff confirms each lever emits only what it was meant to emit. Lever 1 on
`110055611`, day 11: `PLANT STRAWBERRY -> PLANT TOMATO` ×13 and
`MKT BUY_SEED STRAWBERRY -1 / BUY_SEED TOMATO +1` on 10 turns. Nothing else on day 11, and
nothing at all before it.

Everything after is downstream, and one entry is the story: **day 23,
`HARVEST -> DIG` ×13.** TOMATO's `max_yield` is 4 at `interval` 1, so a day-11 planting
reaches production 4 at the end of day 21 and `_daily_refresh_plants` sets
`max_lifespan_step = (22+1)*24`; from day 23 `_decay_plants` turns all 13 into WEEDs. The
tape's d23/d25/d27 `HARVEST` and its d24 `FERTILIZE` on those tiles are then spent on
nothing, and a reflex in the base digs them out. A STRAWBERRY there would have produced on
d21/23/25/27 and lived to day 28. **Lever 1 buys four days of tomato and pays five days of
tile-time for them** — the diagnosis's "zero labour change" is true of the *ops*, not of
what they are worth.

The second measured mechanism is the market. Our 52 strawberry units were part of what
floored the STRAWBERRY book (quote $1–5 from day 20 on `110055611`, against the
diagnosis's assumed $25–49). Withdrawing them lifts the price for the *opponent*, whose
frozen tape keeps selling the same quantities into a recovered book. That is why L1's own
bank rises on several episodes while its **margin** falls on 13 of 18: the book relief the
diagnosis called "the upside" is mostly a transfer to the other seller.

## 5. Why lever 1 is a −11,138 head to head — the finding worth keeping

Against live, responding opponents the lever is far worse than on the harness:

| 8 seeds (300–307) × 2 seats, `experiments/tapes/run_agents.py` | vs `router_yuan_nf_trim` | vs the base | self-play mean bank |
|---|---|---|---:|
| base `agents/public_farm2945.py` | **16–0, +15,982** | — | **89,667** (σ 21,173) |
| lever 1 | 9–7, +4,576 | **2–14, −11,138** | 85,294 (σ 14,840), **−4,373** |

That is an order of magnitude more than the day-11 trade can explain, and the cause is
structural:

> **`public_farm2945` already has a tomato program, and lever 1's own tomatoes are
> precisely what disqualify it.**

`_v219_qualifies` (line 1270) commits on **day 18** to `BUY_LAND` + `BUY_SEED TOMATO 10`
and works ten tiles of the fourth quadrant to the end of the season. One of its conditions
is `if any(isinstance(t,dict) and t.get('crop')=='TOMATO' ...): return False`. Telemetry
from a disposable instrumented copy, seed 300, same episode:

| | `_V219_REPORT` |
|---|---|
| overlay off | `commitments 1, plant_requests 10, confirmed_harvest_units 80, tomato_sale_requests 70` |
| lever 1 on | `commitments 0` (and `budget_declines 0` — it never reached the budget check) |

The tile census confirms it: with the overlay off both seats carry **10 TOMATO tiles from
day 20 through day 28**; with lever 1 on our seat carries 13 from day 12 and **0 from day
24**. Lever 1 trades ten tomato tiles that live to day 29 for thirteen that are dead by
day 23.

**This also corrects `day11_diagnosis.md` §4 M2, which classified tomato as "(c): no code
path exists."** A code path exists; it is *qualification*-gated, and the gate that bites is
the shop draw. Checking all five conditions at day 18 across the 19 episodes:

| day-18 qualification | episodes |
|---|---|
| **qualifies** | **4** — `109618581`, `109656980`, `109679411`, `109798409` |
| fails on `< 3` of {`PIZZA_SHOP`, `FARMERS_MARKET`} unlocked | 15 (14 on the shop count alone) |
| fails on quadrants / fourth quadrant not locked | 2 |
| fails on money (< $12,000) or TOMATO price | **0** |

All nine episodes the diagnosis sampled fall in the failing 15, which is why it measured 0
tomato in 9 of 9 and concluded the path did not exist.

**Checked from the other side, in the recordings themselves** — TOMATO tiles at day 20 /
24 / 28 in the recorded observations of our seat:

| episode | day 20 | day 24 | day 28 | quadrants at d20 |
|---|---:|---:|---:|---|
| `109618581` | **10** | 10 | 10 | NW NE SW **SE** |
| `109679411` | **10** | 10 | 10 | NW NE SW **SE** |
| `109798409` | **10** | 10 | 10 | NW NE SW **SE** |
| `109656980` | 0 | 0 | 0 | NW NE SW |
| any of the diagnosis's 9 (`110055611`, `109727399`, …) | 0 | 0 | 0 | NW NE SW |

So **3 of the 4 qualifying episodes really did buy the fourth quadrant and run the ten
tomato tiles to season end on the live ladder.** The mechanism is confirmed on real play,
not only in local self-play, and M2's "no code path exists" is definitively wrong.

`109656980` passes the five conditions checked here and still planted nothing, so **at
least one further condition binds** — most likely the route-key-dependent scan
`for tape in _IMPL.chassis.routes.values(): ... BUY_LAND / PLANT TOMATO in tape[432:719]`,
or the day-18 hand-count check. That is why the next line is a lead and not a conclusion:

> The shop count is the binding condition on **14 of 19** episodes, and it is the obvious
> place to look. But those two shops are the two that *consume* TOMATO, and the
> diagnosis's "the TOMATO quote rises monotonically, neither player moves it" was measured
> on episodes that all had ≤2 of them — that is the *opponents'* supply not moving the
> book, not ours on top of theirs. **Whether tomato pays without those shops is untested.**
> It is the next measurement, not a known win.

Generalises, and this repo has the pattern already: **a dead end is measured against a
base.** "No code path exists" was true of the 9 episodes it was measured on and false of
the agent.

## 6. What I could not determine

- **Whether relaxing `_v219_qualifies`' shop count pays.** Named above, not measured, and
  it is the single least certain thing in this document: the gate is not arbitrary, it is
  keyed on the two shops that consume TOMATO, so relaxing it sells into thinner demand. It
  needs the same four harnesses, and on the 3 episodes where tomato already runs it is a
  no-op, so its test set is the other 16.
- **What else blocks `_v219_qualifies` on `109656980`**, which passes all five conditions
  checked here and still plants no tomato. Until that is traced, "the shop count is the
  binding condition" is true of 14 of 19 and not of the qualification as a whole.
- **Whether a tomato block that dies with the season would pay.** The day-23 death is a
  property of planting an `interval`-1, `max_yield`-4 crop on day 11, not of tomato. A
  day-18 planting yields d26–d29 and never decays inside the season — which is exactly what
  V219 already does, so this points back at V219 rather than at a new overlay.
- **The two non-reproducing name-matched episodes.** ±$250 of base drift, cause not traced;
  they are the only two where a `SELL` quantity moves, which reads more like a different
  submission version of the same agent than a harness bug.
- **Lever 2 was predicted to lose before it ran and did, but not by the predicted amount.**
  MELON's `sq` curve floors ~158 units above `I0` and the book already sits ~135 units above
  it at $68 on day 20, so 42 more units floor it; wheat cycles the same tile ~5 times at
  $39. Predicted ≈ −2,000; measured −552 mean bank / −1,525 margin with a broken win. The
  per-episode swings (−14,405 to +6,599) are far outside that range, i.e. mostly
  frozen-opponent noise — so lever 2 is condemned by the broken win and by the arithmetic,
  not by its mean.
- **The harness cannot price the strawberry-book transfer honestly.** A live opponent would
  also sell into the recovered book, so the effect is real, but its *size* here is measured
  against a tape that cannot re-plan around it.

## Files

`agents/farm2945_late.py` (both flags `False`), `tests/test_farm2945_late.py` (12 tests).
Measurement scripts were throwaway, run from the session scratchpad against replays already
cached in `experiments/endgame/rep/`. `agents/public_farm2945.py`, `main.py` and every
existing tool are unmodified. No Kaggle API call was made and nothing was submitted.
