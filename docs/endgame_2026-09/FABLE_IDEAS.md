# From 2,424 to 3,000: Fable's analysis, 23 September 2026

**Summary.** The engine's price function is closed-form and computable in-agent in microseconds, and the whole 21,000-coin gap reduces to two uses of it that the tapes cannot make: selling premium goods early, in 1–2 unit slices, on a four-hour cadence phase-locked to shop consumption, while inventory is still on the scarcity side of the curve; and producing into the products whose curves cannot crash (eggs, wheat) or that spend most of the game above base price (tomato, carrot). The top six do this with the *same* crew size as everyone else — the edge is allocation and timing, not headcount. Neither behaviour needs learning; both are rules we can write this week. The lower-risk build is a market-orders-only overlay on v15stack (sell side is pure market orders, so it avoids the known overlay-perturbation failure). The ambitious build keeps v15stack's opening through day ~8 and hands over to a reactive mid-game controller, which is the fam_yarn splice idea pointed at a policy instead of another tape. Two brief numbers need correcting: the early-revenue gap (21,500 vs 12,500) is specific to tape opponents and does not generalize, and the goose gap is 5 vs 2, not 6 vs 2. One mechanic nobody has mentioned — the CARE bonus bank — can multiply wool output per cycle up to 4× and is worth checking before anything else ships.

---

## 1. The price mechanism: how wool sells at 135 vs 78

**Measured (engine source, kaggle-environments 1.32.7, `kaggriculture.py`):**

- `market_price` (line 192) is a pure function of shared inventory. Wool above I0=10,000 falls **quadratically**: price = 200 − 0.058·x² (x = units above I0). +33 units → 135; +46 → 78. The entire 135-vs-78 gap is ~13 units of net inventory position at the moment of sale. Strawberry and milk fall **linearly** (−1.92 and −2.10 per unit); ~63 strawberry or ~76 milk above I0 reach the $1 floor. Below I0 every product pays *above* base.
- Demand drain is deterministic and observable: town centre 1/day per product; each shop instance consumes its products every 4th step (6×/day), double for single-product shops (`_town_consume`, line 728). One YARN_STORE = 12 wool/day of price recovery; `town.unlocked_shops` is in the observation, so drain is exactly computable in-agent.
- Orders resolve in per-unit lockstep, **paired by order-slot index** (`_process_market`, lines 563–627). Both players' slot-0 orders run to completion before slot 1 starts. Two same-slot sells are quoted identical prices per unit; a sell in slot 0 fully executes before an opponent's sell sitting in slot 5 — *within-turn front-running is a slot-index game, not a turn-timing game*.
- Sales at the $1 floor do **not** add inventory (`_commit_unit`, line 659): endgame liquidation at floor is impact-free.
- Timing of top-five premium sells (sells.csv, 44,920 wool/milk/strawberry sell orders, old top-5 corpus): six sharp peaks at hours 2, 6, 10, 14, 18, 22 — **a 4-hour cadence, phase +2 after each shop consumption tick**. Only 13% of sells land on tick hours (uniform would be 25%). Script: `analysis/fable/q3_timing_scarcity.py`.
- Season shape (same file): median wool price d10–14 = **220 (above base)**, d25–29 = **43**. Milk 194 → 45. Modal slice size 1–2 units for all three premium goods. Whoever sells early sells on the scarcity side; whoever dumps late sells into the accumulated glut.
- Fresh 78-game exact re-simulation (`analysis/exact_trades_78games.jsonl`): top six average wool 141/unit (9,287 units) vs 123 for all other opponents (16,452 units); strawberry 144 vs 118. The brief's 135-vs-78 is the tape-family-only subset (14 games), which is the relevant one for us since W0 is tape family.

**Inference.** The skill is fully reproducible as a rule, because everything it needs is public and closed-form:

> Per premium product each day: budget = today's computable drain + small share of scarcity headroom. Sell in 1–2 unit slices, one slice per 4-hour window at hour ≡ 2 (mod 4), in **market slot 0**, only when the locally computed quote ≥ threshold (e.g. 0.55×base early, decaying toward the floor by day ~27). Start as soon as stock exists — the scarcity premium is largest early. Liquidate all remaining stock into the floor in the last day, highest-priced items in earliest slots.

The tape gets 78 because its recorded schedule dumps 6-unit slices at fixed turns with no knowledge of inventory — after day 15 that means selling into the glut it and its opponent jointly created.

## 2. The production mechanism: geese, tomatoes, carrots on the same 75 tiles

**Measured (`analysis/pairs.csv`, fresh corpus, 144 top-six vs 396 opponent trajectories; medians):**

- Geese **5 vs 2** at day 12 and still 5 vs 2 at day 18; cows 9 vs 8; sheep equal. Eggs sold per game **166 vs 23**; carrots 129 vs 70; wheat 467 vs 331; tomato 41 vs 22. Melon slightly conceded: 42 vs 54 units.
- **Hands: 11 vs 11.** The crews are the same size. This is allocation, not headcount.
- Egg is glut-proof by construction: above-shape log, price 39 even at +2T=664 units over baseline; and eggs spend 49% of game-days *above* base (max seen 108). Tomato spends 84% of days above base and has spiked to **409** (hinge scarcity, base 60); carrot 76% of days above base, max 87. The "uncrowded markets" are literally markets where measured price sits above base most of the season because shop demand outruns everyone's supply.
- Goose economics (engine): 300 cost, 1 egg/day from day 4, feed 1 wheat/day. With daily CARE+FEED the care bank pays +1 on each production day → ~2 eggs/day ≈ 100 gross/day per goose against ~36/day feed (measured average wheat trade price), payback under a week.
- What they give up: the melon race (−4,000/game, tapes dump melon earlier), the third quadrant (0/360 ever buy it; we buy it in 23–33% of games), and the cash buffer — top-six trough is $3–47 vs our $212–218 (washamba_vs_top6 report §4).

**Inference.** Labour arithmetic: 12 units × 24 turns ≈ 288 actions/day against roughly 60–70 water actions, ~14 feeds, ~14 cares, ~14 fertilizer collections, harvests and movement. The slack fits ~4 more animals' upkeep easily; the binding constraint is the day-3–7 cash trough, which is why the early-goose teams (Boey, M&M&P&Q, day 1–2 geese) run it to near zero. Their day-by-day labour split is not directly logged in our CSVs; extracting per-unit action histograms per day from the 360 trajectories is a ~half-day Sonnet task if we want it, but the composition and outputs above already pin down the answer.

## 3. Approaches beyond tapes

**(a) New layers on v15stack.** Expected +100–250 rating (turns mirror ties into wins inside the 2,000–2,500 band; W1's single-constant change already showed 36-28-24 in mirrors). ~1–2 days each. Risk: overlay perturbation — six of seven tape overlays failed historically; only market-order-side changes are safe (they alter cash upward, never board state). Measure: 80+ fresh-seed mirrors vs W0 plus the 38-episode faithful panel. **This cannot close −21,700; it defends rating, nothing more.**

**(b) Reactive heuristic from scratch.** The only demonstrated route to 3,000 (all six at the top are reactive rule agents; community consensus agrees). Expected: 2,600–3,000 *if* both the sell rule (§1) and the goose/staple economy (§2) execute cleanly; main.py's plateau at ~600 was a route generation behind and tuned against non-selling built-ins, so it understates the approach, not the ceiling. 4–6 days full-time — tight against the 30 Sep deadline. Measure: top6 panel faithful subset, staged thresholds (see §4).

**(c) Supervised macro-policy + hand-written executor.** Labels exist (360 trajectories give daily buy/plant/sell targets), and daily-granularity macro decisions transfer better than raw actions (the gen-7 failure was literal-action transfer). But the top six's macro choices assume *their* executor; ours would execute the same targets worse, and the 21-Sep corpus already showed checkpoint-compatible material barely exists. 2–3 days, medium risk, expected below (b) — the macro decisions are nearly uniform across the six anyway (same land day, same herd), so a lookup table of §1/§2 rules captures most of what a model would learn.

**(d) Search/MPC with the exact price function.** As full-game search: infeasible in 1s. As **market-order MPC**: trivially feasible — the price function is closed-form, drain is deterministic, so "optimal slice pacing over the next K hours given opponent stock estimate" is a few hundred float ops. This is not a separate agent; it is the right implementation of §1's rule inside (a) and (b). Cost: absorbed into those builds. Risk: near zero.

**(e) Reinforcement learning.** Rule out for this cycle. No one in the field has shown RL beating the tape ceiling; infra alone (fast engine, self-play pool) consumes the remaining seven days; and the reward signal (win/loss at turn 720) is exactly the hard case. Days: >7. Expected gain before the deadline: ~0.

## 4. Two agents for the next 48 hours

**W2 (lower-risk): v15stack + paced-premium market layer.** One flag; off = byte-identical. Replaces the tape's premium sell orders (wool, milk, strawberry) with §1's rule: computed quote, 1–2 unit slices, hour ≡ 2 mod 4, slot 0, drain-budgeted, floor liquidation on day 29. Touches market orders only — no unit actions, so the tape's board state is untouched and the only perturbation is *extra* cash, which never blocks a scripted purchase. Why the data says it helps: the tape's wool realizes 78–123/unit where paced selling realizes 135–141 on the same volume (§1), worth roughly +4,600 (wool) +3,500 (strawberry) per game vs tape-family mirrors — and our ladder band is full of tape mirrors where every product currently ties within 1–3%.
*Test:* (i) 80 fresh-seed mirrors vs W0 (same harness as the W1 race44 test): pass ≥ W1's bar, i.e. wins−losses ≥ +8; (ii) `harness/top6panel.py` on the 38 `faithful_eps.json` episodes, compared with W0 only on episodes faithful under both: pass = median margin improves ≥ +5,000 from −21,700 and no loss of mirror wins.
*Kill:* mirror record ≤ W0's (the layer costs more in disturbed cash timing than it earns), or faithful count under W2 drops below ~28 of 38 (we perturbed the tape after all).

**W3 (ambitious): opening splice into a reactive mid-game.** Keep v15stack verbatim through day 8 (openings are deterministic and already competitive — every day-6 checkpoint in both corpora is near-identical anyway), then hand over to a written-from-scratch controller: daily plan = hire to 12–13, water/feed/care everything, 4–6 geese, wheat+carrot filler on free tiles, tomato from day ~8, no third quadrant, melon left to the tape's early dump; selling = §1's rule on all nine products including staple scarcity-taking (sell staples aggressively whenever quote > 1.3×base). This is the fam_yarn splice pattern — the one lever that has ever produced +600 rating — pointed at a policy instead of a tape.
*Why the data says it should help:* the handover point is exactly where reactive agents diverge from tapes (largest exact-prefix family at turn 144 is 6/300); the mid-game is where the generalized revenue gap lives (rev_d10 47.8k vs 39.7k, rev_d20 52.0k vs 35.6k, pairs.csv medians); and every component rule is measured, not guessed.
*Test:* staged on the same 38-episode faithful panel. Stage 1 (viability): ≥10 wins of 38 and median margin ≥ −10,000 (halves the gap). Stage 2 (submit-worthy): ≥19/38 and 80-game mirror vs W0 ≥ 45% (must not be farmed by our own band). *Kill:* Stage 1 fails after the sell rule and goose economy are both confirmed firing in logs — that would mean execution quality, not strategy, is the gap, and the remaining days go to W2-class layers instead.

Timing: hold both behind the harness gate; ladder-read W2 by ~27 Sep, keep W3 for the final-day pair per the existing plan.

## 5. What we are missing, and where the brief is off

1. **The CARE bank (engine lines 824–830).** Care banks +1 per fed+cared day, paid on the next fed production day, capped at `max_held`. A sheep on interval 3 yields up to **4 wool per cycle instead of 1**; a cow 3 milk instead of 1; a goose 2 eggs instead of 1. Nobody's reports mention care rates. If v15stack's tape misses CARE on even some days, this is thousands of coins for free. *First check tomorrow:* count CARE actions per animal-day in one W0 replay vs one Boey replay (an hour of work).
2. **Fertilizer is a daily free coin.** `fertilizer_available` resets to True every day for every placed animal, fed or not (line 831). 12 animals ≈ 12 collectable fertilizer/day ≈ $560/day gross at measured prices, labour permitting. Worth confirming our collection rate matches the top six's (their fert revenue: 23k vs our band's 30k — we may already do this fine).
3. **Floor sales add no inventory** — endgame dumping is impact-free, and a "make the opponent poorer" gate cannot push a market below floor. Already partially exploited by v15stack's min-price gate; the liquidation ordering (premium first, slot 0) is not.
4. **Slot-index front-running** (§1) — the docs' "sell one step earlier" framing understates it; you can front-run *within the same turn* by slot placement.
5. **Brief correction — early revenue.** "Days 0–9: 21,500 vs 12,500" is the 14-game tape-family subset. Across all 78 re-simulated games, median day-0–9 revenue is 13,870 (top six) vs 13,320 (all others) — essentially no early gap vs the general field; the generalized gap is mid/late game. Against *us* (tape family) the early gap is real; just don't design as if the top six have a magic opening. Their openings are ordinary; their mid-game isn't.
6. **Brief correction — magnitudes.** Median geese 5 vs 2 (not "about 6"); "19 tomato plants" is cumulative seeds bought in the small subset, not concurrent tiles (snapshot medians: 0 at day 12, 6 at day 18 for both sides).
7. **Scarcity spikes are harvestable.** Tomato has traded at 409, egg at 108, carrot at 87 in real games (daily.csv maxima). A one-line reactive rule — sell any staple when quote > 1.3–1.5×base — collects money no tape can see. Wheat sits above base 96% of days: the feed buy-back loop is cheaper than it looks and selling surplus wheat is better than it looks.

## Ranked ideas (expected rating gain per day of work)

| # | Idea | Expected gain | Days | Gain/day |
|---|------|-------------|------|----------|
| 1 | CARE-rate audit of W0 vs Boey (then fix if deficient) | up to +100–300 if deficit found | 0.5 | very high, cheap to falsify |
| 2 | W2: paced-premium market layer on v15stack (§4) | +100–250 in-band | 1.5 | ~100 |
| 3 | Staple scarcity-taking sells (>1.3×base rule, market-only layer) | +50–150 | 0.5 | ~100–300 |
| 4 | Endgame liquidation ordering (premium first, slot 0, floor-aware) | +30–80 | 0.5 | ~60–160 |
| 5 | W3: opening splice → reactive mid-game (§4) | +300–600 if Stage 2 passes | 4–5 | ~60–120, high variance |
| 6 | Third-quadrant cap flag (match top six's 0/360) | 0–50, sign unresolved | 0.3 | speculative |
| 7 | Supervised macro-policy (c) | ≤ W3, same executor risk | 3 | dominated by 5 |
| 8 | RL (e) | ~0 before deadline | >7 | ~0 |

Items 1–4 are independent, mostly market-order-side, and together fit in the first 48 hours alongside starting item 5. Everything above gates on the existing harness: mirrors vs W0 on fresh seeds, and the 38-episode faithful top-six panel compared only on games faithful under both candidates.

---

# Round 2 — 23 September 2026, late evening

New scripts: `analysis/fable/r2_q2_engine_timing.py`, `r2_q2_slots_drops.py`, `r2_q3_labour.py`. Samples: 12 top-six replays (2/team, fresh corpus) for slots/drops/labour, 6 W0 replays for the executor baseline, one full replay for consumption timing.

## R2.1 The care-vs-herd trade, and the herd to target

The audit settles it: no care deficit. W0's 1.04 CARE per animal-day is *above* 1, which the engine cannot bank — a second CARE on the same animal-day is a silent no-op (`cared_today` guard, line 527) — so W0 issues ~4% duplicate care actions, pure waste. The top six's 0.74–0.82 coverage on 16+ animals gives them **about the same total care actions as W0** (16.3×0.82 ≈ 13.4 vs 13.0×1.04 ≈ 13.5). They did not trade care away for animals; they added animals at constant care effort and let per-animal coverage dilute.

**Is that worth it? (engine rules + measured prices; arithmetic is inference)**

- One CARE action = exactly +1 unit of that animal's product on its next fed production day (lines 824–830, cap permitting). Value per action: sheep ≈ wool price (141 early / 43 late), cow ≈ milk (~105–160), goose ≈ egg (~47). Care is the highest-value action in the game per unit-turn while premium prices hold — **but it saturates at 1/animal/day.** Once every animal is cared daily, the only way to spend more labour on animals is to own more animals.
- One marginal *uncared* animal nets, per day, after feed at the measured ~38/wheat buy price: goose ≈ +56, cow ≈ +64, sheep ≈ +56, **plus ~+47/day of free collectable fertilizer** (`fertilizer_available` resets daily regardless of feeding, line 831), for ~2.5–3 unit-turns of service. Payback on the purchase price: goose ~4–5 days, cow ~6–8, sheep ~8–10.
- So the trade is real and correct: care first (up to saturation, sheep→cow→goose order), then spend remaining capital and labour on more animals. The top six do exactly this; the residual 0.78 coverage is what fits after travel. W0's mistake is not care rate — it is holding 3–4 fewer animals and re-caring ones already cared.

**Target herd by day (inference from engine payback cutoffs + the measured top-six template; prices decay per §1):**

| Day | Action | Rationale |
|---|---|---|
| 0 | 2 COW + 3 SHEEP (~$2,300 of $3,000) | universal top-six opening template |
| 1–2 | +1–2 GOOSE *only if* selling from day 0 (Boey profile); otherwise skip | goose is trough-safe only with early cash flow |
| 6 | land ($1,000) — the fixed branch point | 360/360 trajectories |
| 7–9 | land #2 ($2,000); GOOSE → 5–6; COW → 6–7 | post-trough ramp; goose payback ~5 days |
| 10–13 | COW → 8–9; SHEEP → +1 per unlocked YARN_STORE instance, else hold at 3 | cow buy cutoff ~day 13–14 (first yield lag 8d); wool T=105 — extra sheep glut their own market without a yarn store |
| 14–17 | last GOOSE purchases (cutoff ~day 17–18: 300 cost vs ~94/day cared eggs) | eggs are glut-proof; only the calendar kills the payback |
| 18+ | buy nothing; from ~day 26 stop feeding any animal whose next production lands after turn 720 | feed at ~38 with no future yield is a pure loss |

Sheep and cow counts should be conditioned on unlocked shops (milk drain = 6/day per pizza/ice-cream/smoothie instance +1 town; wool = 12/day per yarn store +1) — that is the reactive part no tape can do. Cash floor through days 3–7: near zero is what all six run (measured $3–47); the buffer we hold ($212+) is dead capital.

## R2.2 The 4-hour cadence: verified, and it is deliberate

**Measured (`r2_q2_engine_timing.py`, replay 112194936, rows 2–400):**

- Consumption-only inventory drops (rows where neither player traded the product) land **exclusively at rows t with (t−1) % 4 == 0** — shops fire inside the interpreter call with step counter s where s % 4 == 0, *after* that call's market processing, and are recorded at row s+1 (54/54 tomato, 82/82 strawberry, 61/61 wool drops; town-centre melon 15/15 at (t−1) % 24 == 0).
- Therefore the **first sell quoted on the drained inventory is the action recorded at row ≡ 2 (mod 4)** — the agent choosing it saw the post-drain obs at row ≡ 1, and its sale executes in the next call. That is exactly the measured peak (59% of top-six premium sells at hour ≡ 2 mod 4 in the fresh sample too, n=3,385). The cadence is not approximately right; it is the provably earliest post-drain quote. Selling at row ≡ 1 mod 4 would execute *before* that turn's consumption tick and get the stale price.
- **It is not a shed-logistics side effect:** DROP actions are flat across the phase (26–28% per mod-4 class vs the sells' 59% spike). Goods also auto-drop to the shed at midnight regardless. The timing is a choice.

**Correction to Round 1's slot claim (measured, `r2_q2_slots_drops.py`):** top-six premium sells show **no slot-position edge** — median slot 0, 62% in slot 0, for both the top-six seat and their opponents; in 1,098 same-turn same-product collisions the slots are equal 66% of the time and the top six are *earlier* only 203 vs 168. Slot-0 front-running remains a real engine lever (slot i pairs with the opponent's slot i), but it is not something the top six exploit and not where their money comes from. Keep it in W2 as free insurance; stop expecting rating from it.

## R2.3 Agent 2 controller spec

**Executor targets (measured, 12 top-six games + 6 W0 games, `r2_q3_labour.py`):** idle (PASS) 1.7–4.5% for five of the six (吃白饭的大肥鱼 11.1%), movement 40–45% of all unit-turns, waters 34–44/day (0.14–0.19 per unit-turn), harvest 15–20/day, feed ≈ care ≈ 9–13/day, collect-fertilizer 12–16/day, DIG ≈ 1/day (weeds are negligible). **W0 already sits inside this envelope** (idle 6.9%, move 42.5%, waters 36.6/day) — so executor mechanics are not the moat; the plan being executed is. Pass bar for our executor: idle ≤ 5%, move ≤ 45%, waters ≥ 40/day on 75 tiles, care ≥ 0.8/animal-day with zero duplicates.

**Spec (pseudo-code):**

```
DAWN (hour 0 of day D):
  read obs                      # complete: tiles carry planted_day, yield_units,
                                # watered_today, consecutive_unwatered, fed/cared flags;
                                # shed, seeds, money private; market inv + shops public
  drain[p]   = 6*Σ shop instances wanting p * (2 if single-product) + 1   # exact
  sell_plan  = paced slices per §1 (quote-gated, hour ≡ 2 mod 4)
  herd_plan  = R2.1 table row for day D;  crop_plan = replant one-time crops,
               tomato from d8, no 3rd quadrant, melon only pre-d10
  TASKS = [
    FEED(a)    val = escape_risk ? animal_replacement : product_ev - 38   # mandatory tier
    WATER(t)   val = survival (consecutive_unwatered==1 → full remaining EV)
                     else +1..2 units * price if inside yield window       # wheat d2-4,
                     else maintenance                                      # carrot d2-3, melon d6-12
    CARE(a)    val = product price (sheep > cow > goose), skip if cared_today
    HARVEST(t) val = units*price; deadline = max_held cap / melon decay step
    COLLECT_FERT(a) val ≈ 47 or fertilize-EV if crop_plan wants it
    PLANT(c)+same-day WATER pair                # unwatered planting day = weed tonight
    PICKUP/DROP prerequisites (wheat circuit; drop harvest before sell ticks)
    BUILD coop/pasture per herd_plan ]
  HIRE n while fib_cost(n) < uncovered_task_value(n-1)   # ≈11-13; 13th costs 233/day
       # order-slot budget: 10 market orders/turn — 12 hires need 2 turns; don't
       # let hour-0 hires crowd out a scheduled premium sell slice
  ROUTES: seed unit→cluster assignment (Hungarian on cluster centroids, one-off),
          then cheapest-insertion route per unit with deadline penalties (VRP-lite);
          farmer takes the shed-adjacent logistics route
PER TURN:
  each unit pops next route step; event-driven replan (yield ready, weed, animal
  unfed and hour > 18, plan invalidated) or every 4 hours, aligned to sell cadence
```

**Assignment choice:** rolling-horizon day routes, not per-turn Hungarian. All maintenance demand is known at dawn (flags reset at midnight, deadlines are end-of-day), so the problem is a small vehicle-routing instance, and per-turn Hungarian is myopic about travel amortization — it will send a unit 3 tiles for one water when a snake route waters 10 for 13 unit-turns. Greedy-with-lookahead is an acceptable fallback (~same quality at this scale); Hungarian earns its O(n³) only as the once-a-day unit→cluster seeding. All variants cost ≪ 1s.

**Handover from v15stack at day 8 (verified against engine state):** the observation is sufficient — tiles expose `planted_day`, `yield_units`, `watered_today`, `consecutive_unwatered`, `fertilized_until_day`; animals expose `fed_today`, `cared_today`, `consecutive_unfed`, `yield_units`; private gives shed/seeds; `hires_today` is public. No internal tape state is needed. Handover checklist: (1) first pass services every `consecutive_unwatered==1` plant and `consecutive_unfed==1` animal before anything else; (2) respect same-day flags to avoid duplicate feed/care/water no-ops; (3) hands hired by the tape that morning persist until midnight — inherit them, don't re-hire; (4) hand over at hour 0 of day 8, not mid-day, so route planning starts from the deterministic shed spawn.

## R2.4 Engine facts that make the executor easier or harder

**Easier than it looks (all read from engine source):**
- No unit collision and locked tiles are walkable — pathing is pure Manhattan distance, no obstacle logic at all (lines 323–331).
- No carry capacity on unit inventories — one feeder can carry a whole day's wheat; only the shed caps at 100.
- Watering/feeding deadlines are "by midnight", not per-hour — batching and snake routes are free; flags (`watered_today` etc.) make idempotence checks trivial.
- Illegal actions are silent no-ops — a buggy route step costs one unit-turn, never a crash.
- Midnight auto-drops every unit inventory to the shed — un-dropped harvest still becomes sellable next morning.
- Full observability of everything that matters (own farm micro-state and the opponent's board) — the controller can be stateless.

**Harder than it looks:**
- Market resolves *after* unit actions in the same call: seeds bought this turn plant next turn; a hand hired at hour h first acts at h+1. One-turn pipeline everywhere.
- A seed planted and not watered the same day weeds overnight (`consecutive_unwatered` starts at 1) — PLANT must be paired with a same-day WATER by another unit or a later turn.
- The 10-order/turn market cap collides with the morning hire burst and with sell slices — the order-slot budget needs explicit scheduling (12 hires alone take two turns).
- Everyone teleports at midnight (farmer to shed spawn, hands gone) — no overnight positioning; every day pays the fan-out travel tax again, which is why movement is 40–45% for even the best teams.
- FERTILIZE and FEED need the item in the *unit's* inventory — pickup/collect legs must be in the routes, not an afterthought.
- Atomic PLANT validation: over-requesting one crop in a turn voids *all* of that crop's plants that turn.

**Bottom line for Agent 2:** the top six's executor is matchable — W0's own action-mix already is — and the scheduling problem is a dawn-planned VRP on a 10×10 grid with end-of-day deadlines, well inside budget. The rating lives in the plan layer: the R2.1 herd schedule, shop-conditioned production, and §1's verified sell cadence.
