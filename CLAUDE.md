# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## How we build (from 2026-09-01)

Shape is specified in **`mydocs/FACTS.md`**, not as slogans (Path A–C) or
knob sweeps. Method: `mydocs/AGENT_BUILDING_PROTOCOL.md`. Diary:
`mydocs/HANDOFF.md`.

Before a shape edit: add / remove / supplement a row in `FACTS.md`, then
diff a throwaway `experiments/_*.py` against **every** row, then measure
the named counters. Do not patch shipped `main.py` until those counters
hold. `docs/EXPERIMENT_WORKFLOW.md` is for knobs **inside** a fact-set
that already holds — not a substitute for writing the facts.

Path A **is** shipped `main.py`. Path C is parked. Do not paste v20 tape
orders onto crop-first gates. Do not paste Path A crop-first gates into
the animal-first throwaway (same failure as Path C). Do not use `bptk.py`
for animal cadence.

**A row is judged contested against `agents/route_v20.py` on seeds 0 and
8, not against `starter` (2026-09-05).** Seven sessions of "audit CLEAR"
on the built-in judge sat on top of a contested bank falling from ~51k to
~8k: the shape was right in composition and **4–6 days late on every
producing asset**, and no counter in `FACTS.md` measured *when*. The four
dollar gaps (STRAWBERRY −29.6k, WOOL −25.3k, WHEAT-net −20k, FERTILIZER
−4.1k on seed 0) each trace to a row added as an escape-defence patch
against the tape, and the "STRAW acreage bind" three sessions chased was
self-inflicted by two of them. `experiments/tape_profile.py` now diffs
crew, herd, plantings and sells per engine day against the tapes — run it
before the bank. Live next lever: **timing card T1** in `mydocs/FACTS.md`
(rows 9/15/17/21/22/27/28/39 + 43). Facts 40–42 are closed, not paused.

## What this repo is

An agent for the Kaggle **Kaggriculture** simulation competition: two agents each manage a virtual farm over a 30-day season (720 turns, 24/day) and compete for the highest bank balance. There is no static train/test set — everything is scored via live episodes against other agents plus a final Bradley-Terry tournament.

**Current state:** `main.py` holds `nikaangukia_meroni` — a deterministic, rule-based agent (harvest → water → reclaim weeds via `DIG` → move-to-urgent → plant → walk → pass, plus threshold-based selling). One shared, inventory-aware `choose_unit_action` ladder drives the main farmer **and every hired hand**, with a per-turn claim set so units spread out instead of converging on the same tile.

The animal rollout is **four animals across two species** (`ACTIVE_ANIMALS = ["SHEEP", "COW"]`, `MAX_ANIMALS = 4`), on a **75-tile** farm bought as two `BUY_LAND` quadrants and worked by a crew of up to 15: build a pasture, buy/pick up/place it, feed and care for it daily, collect fertilizer, harvest wool, and hold back a wheat reserve so selling feed can't starve it. **One** is a cash constraint, not a market one — a second animal is a large *win* head to head and a **-19,514, 0-of-12 disaster** against a built-in, because buying it drains the days 3-7 cash trough and both sheep then starve (see below). The **species** is chosen by care-bank arithmetic, not base price (see below). The logic is data-driven off the engine's `ANIMALS` table, so switching species is a config change.

`tests/` carries a stdlib-`unittest` suite. There is no `agent/` package — that part of the `README.md` layout is still aspirational. `experiments/` holds evaluation tooling (see below) and `notebooks/` has one working experiments notebook.

**Current local benchmark** (crop economics + goose, measured at `ebc8212`). Two separate tables, because they measure different things — **read the self-play one.**

Against the built-ins, 12 seeded 720-turn seasons each. **Inflated: these three never sell**, so the market stays pristine and our prices never meet a competitor.

| vs | mean | stdev | min | max | wins |
|---|---|---|---|---|---|
| `pass` | 41,969 | ±2,206 | 38,524 | 46,198 | 12/12 |
| `random` | 42,812 | ±1,926 | 40,929 | 45,922 | 12/12 |
| `starter` | 43,105 | ±1,740 | 40,949 | 46,028 | 12/12 |

Self-play, 6 seeds / 12 agent-results — **the ladder proxy**, and the number to quote:

| | mean | stdev | min | max |
|---|---|---|---|---|
| self-play | **31,132** | ±1,880 | 27,836 | 33,777 |

The ~15,000 gap between the two tables is the whole story of why a 33,000 local score became 289.3 on the ladder. Melon finishes near $280 against a built-in and at the **$1 floor** in self-play.

**The single biggest win was a scoring bug, not a strategy.** `choose_crop` subtracted an absolute oversupply term: `(price*yield - stock*price)/days`. Every product starts with market inventory of 10,000, so that term was not a tie-breaker — it *was* the score, collapsing to roughly `-price*10000/days`, which ranks crops by **cheapness**. Melon is the strongest crop in the game at 125.0 value per tile-day (wheat 37.5) and it scored dead last, so the agent planted wheat all season and never once planted a melon. Discounting glut *relative to the engine's `I0` baseline* took the mean from ~7,000 to ~28,800. Generalise it: **when a score mixes a revenue term with a penalty term, check their magnitudes against real game data, not just their signs.**

**Unsold inventory scores nothing** — only bank balance counts at turn 720. The shed used to finish pegged at its 100-item cap holding 95 melons, because price had drifted below a fixed sell threshold and the agent waited for a recovery the season had no time to deliver. Selling regardless of price from `LIQUIDATION_START_DAY` added ~4,400 and *narrowed* the spread, since the loss it removes concentrates in the worst seeds.

**Hiring is the single highest-ROI mechanic in the game, by a wide margin.** The n-th hire of a day costs `farmHandCostMult × fib(n)` with the counter resetting each morning, so four hands cost **$1+$1+$2+$3 = $7/day — about $210 for the whole season.** That bought roughly **+1,400 mean bank** (`pass` 5635 → 6864, `random` 5264 → 7357, `starter` 5555 → 6609). Hands are cleared every night, so re-hire each morning (`HIRE_BEFORE_HOUR`); a hand bought at hour 20 costs the same and does a fraction of the work.

The reason it pays so well is the same one behind the weed cascade below: **a single farmer's upkeep capacity is what caps income.** More units means more tiles watered and dug, while three Geese add a maintained animal revenue stream without the escape failures seen in the four-Goose experiment.

**Because a hand is that cheap, any cash gate in front of hiring is mispriced.** `MIN_MONEY_TO_HIRE` sat at **150** while the first hand of the day costs **$1** — reserving seed money against a purchase two orders of magnitude smaller. It matters because there is a **cash trough on roughly days 3-7**, after the seed/pasture/animal spend and before the first real harvest lands, and the gate locked the crew out for entire days inside it. Dropping it to **20** is **+1,025 head to head (19/24, worst match -102)** and **+2,072 paired against a built-in (9/12, t = 3.09)** — the first change in a while that two harnesses which *can* disagree both call a win.

Dose-response is monotone in how much of the trough the gate still blocks: 60 is +402 (10/16), 20 is +1,025, 0 is +1,144. 20 and 0 tie because the trough bottoms out near $20 anyway.

The mechanism was verified against the counter it was meant to move, not the bank delta: total hires barely shift (**170 → 173**) and early-season hiring is *identical*. The whole effect is **three hires on one day, costing $4**, at the moment young plants need watering. And the trough predicts the outcome on every seed — **10 of 12 dip below 150 during hiring hours and all 10 improve; the 2 that never dip are exact no-ops.** Generalises: **price a gate against the thing it is actually gating.** A flat cash floor in front of a fibonacci-priced purchase is a bug waiting for someone to measure it.

Two earlier fixes moved the **floor** rather than the mean: a **season-maturity gate** (`choose_crop` refuses crops whose `first_yield_day` can't land before day 29 — the agent used to bleed cash buying tomato seed it could never harvest) and a **shed-overflow valve** (force-sell once the shed passes `SHED_FORCE_SELL_THRESHOLD`, since overflow past 100 items is silently discarded).

**The weed cascade — fixed, and worth remembering.** The previous baseline lost to `pass` (an opponent that does nothing and banks $3000) on ~2/12 seeds, finishing *below* its own starting money. Root cause: one farmer planted more tiles than it could water, plants weeded out, and because the agent never emitted **`DIG`**, every weeded tile stayed dead for the rest of the season. The farm decayed to 23/25 weeds and sales starved to 3.9 `SELL` orders per season — zero on the losing seeds.

Adding `DIG` moved every metric at once: **SELL orders 3.9 → 22.9**, **end-of-season weeds 23.0 → 2.1**, and the sub-$3000 downside disappeared. The lesson generalizes: **tile upkeep capacity, not sell-price tuning, is what gates this agent's income.** Before optimizing thresholds, check how many tiles are alive at season end.

**A trigger keyed on a counter that its own action resets will oscillate.** The feed rule fired only when `consecutive_unfed >= 1` — i.e. only once the animal had *already* missed a meal. Feeding resets that counter, so the next day never looked urgent, and the agent settled into feeding every *other* day: exactly 15 meals in a 30-day season, stable and invisible. It cost more than a skipped meal. The Goose sat permanently one blocked turn from escaping for good, and most of the `CARE` bank was discarded — per `_daily_refresh_animals`, the bank only accrues on days the animal was **also fed**, and a production day that isn't fed throws the whole bank away unpaid. Feeding daily took `FEED` 15 → 30, **EGG sold 26 → 52**, and **0 animal escapes across 48 episodes**. Generalise it: if the condition that triggers an action is the same state the action clears, check the duty cycle you actually get — don't assume it fires whenever it's needed.

This one was first reported as *"a wash on bank balance, ships for the risk"* because its deltas sat inside the across-seed stdev. **That was wrong, and the fault was the test, not the change.** Re-run as a paired comparison (`experiments/paired_compare.py`), it is **+1,657 mean, better on 12 of 12 seeds, t = 9.9** — one of the largest gains in the agent. See the paired-comparison note under evaluation below before you label anything a wash.

**A green suite is not evidence the fix worked.** An earlier attempt at this same low `FEED` count batched wheat pickups, on the theory that a one-grain-per-trip shed round-trip was the bottleneck. Tests passed, the mean moved, and `FEED` stayed at **exactly 15** — the real cause was untouched. Always measure the specific counter the change was supposed to move.

`BUY_LAND` shipped 2026-08-18 (see below). Still unimplemented: shed transfers beyond the fertilizer/wheat/animal paths. `FERTILIZE` and the sheep shipped in V2; a per-turn seed budget (see below) shipped later; `pricing.py` exists as research but is **not** wired into `main.py`.

**`bptk.py` (repo root) is a whole-economy structural model, for when a 720-turn episode (~7s) is still too slow to explore.** Same "research only, not imported by `main.py`" convention as `pricing.py`. It exists because three successive wrapper-around-`choose_crop` experiments (the fill-priority tests, below) all failed for reasons that only showed up after a full paired-comparison run — the explicit call was to stop patching the score function blind and model the economy structurally first, then diagnose. The load-bearing design choice: it does **not** reimplement engine mechanics — it directly imports and calls the installed engine's own private state-mutation functions (`_apply_unit_action`, `_commit_unit`, `_do_hire`, `_do_buy_land`, `_daily_refresh_plants`, `_decay_plants`, `_daily_refresh_animals`, `market_price`) against a real `farm["tiles"]` grid, and calls `main.py`'s real decision functions (`choose_crop`, `decide_hire_orders`, `choose_animal_to_build`, etc.) as the policy under test. The only genuinely custom logic is `_assign_crew`, a priority-ranked scan substituting for spatial pathing (the turn's crew acts on the top-N highest-priority tiles directly — no walking, no shed-adjacency, no multi-turn carry trips) — a deliberate, documented abstraction, since spatial/pathing questions are `experiments/replay_diagnostics.py`'s job, not this model's.

**Consequence of the abstraction, stated up front so it isn't mistaken for a bug:** absolute bank figures from `bptk.py` run **~1.5-2x above real episodes** (~$100-124k vs ~$55-66k) because the model has zero travel-time cost. Every number out of it is a *directional* signal, never a bank-balance prediction — `bptk.py --validate`'s own scenarios are all read as relative comparisons for exactly this reason, and anything surprising gets traced against the real engine or a real `selfplay_bench.py` run before it's trusted, not just accepted or dismissed on its face.

**Validated against 7 already-documented mechanisms across 7 seeds before it was trusted for anything new** — the closed `growth_days`/`CROP_PLANTING_WINDOWS` dead ends, the second-sheep cash-trough pre/post fix, the `MAX_ANIMALS` cliff, `BUY_LAND` 2-vs-3-quadrants — all reproduce the correct *direction*. It then ran three diagnostic sweeps (crew capacity × STRAWBERRY window, cash reserve × STRAWBERRY's seed cost, crop↔animal cash contention) that **correctly found no new lever** — each confirmed an already-correct tradeoff rather than turning up a bug, which matters as much as the one it did find: the model is as trustworthy saying "no bug here" as it is at surfacing one.

**The one real, novel finding — confirmed on a real engine trace, then fixed and shipped (`5bdd327`).** `choose_crop()` can name a crop via its `can_afford` branch (money available, zero held seed) at the PLANT call site, but `plant_budget` is seeded only from currently-held seed counts and can never satisfy that pick — the turn plants nothing. `bptk.py` surfaced ~1,100-1,150 such events per season (inflated by the model's own abstraction, not trusted as a real count); a disposable instrumented copy of the real engine (`experiments/debug_main.py`, deleted after use) confirmed it's real, not a model artifact — **185-308 crew-turns a season** across 3 seeds vs `starter` hit this, MELON dominating. Fixed via `choose_crop(require_held_seed=True)`, called as a fallback at the PLANT call site only when the unrestricted pick can't be planted — same glut-aware score, just restricted to what's actually holdable, and deliberately **not** a fixed priority order like the already-failed price-blind fallback (Test 1a, below). Post-fix, zero-seed-held events dropped 5-48% on the same 3 seeds. Four-harness result vs a frozen control: paired vs `starter` -646/6-12 (coin flip), paired vs `pass` +374/8-12, head-to-head +2,621/14-24, `selfplay_bench.py` +1,979 (+3.4%) — **never a loss on any harness**, though no single one clears this repo's usual decisive bar; shipped anyway on that basis, unlike the "positive everywhere, convincing nowhere" bundles below that always had at least one clearly negative reading.

**A contested-market mode (two `EconomyModel` instances sharing one market/town, replicating the engine's real `_process_market` order-lockstep) closes `bptk.py`'s one remaining blind spot** — no competing seller meant price-impact/selling-cadence questions had to go straight to a real 720-turn self-play episode. Its own validation produced a result that looked backwards at first (contested MELON ending *higher* than solo, $280 vs $156) and was traced rather than accepted: both sides collapse into the same days 6-18 hire-gate cash-trough this file already documents, `SELL_MELON` sits at 0 on both sides all season, and with nobody selling the market recovers instead of crashing — an amplification of the 1.5-2x inflation caveat above, not a new bug, but a sign the *shipped* selling/hiring policy may be more fragile under real contested play than built-in-opponent benchmarks reveal (not yet cross-checked against a real `selfplay_bench.py` run at the same seed). Intended use: a cheap screen before spending a real episode on a selling-cadence hypothesis — the sell-or-hold cadence model below was tried twice on two different bases without this tool; re-screening ideas like it here first is the whole reason contested mode was built.

**Count plants that *land*, not `PLANT` actions issued.** The engine drops **all** `PLANT` requests for a crop when a turn's demand exceeds held seeds (`kaggriculture.py:920-931`) — not just the excess — so five units picking melon while holding one melon seed plants nothing and burns five turns. This makes the raw `PLANT` count in an action histogram actively misleading. Seed 0 vs `starter`:

| build | requested | blocked | **landed** |
|---|---|---|---|
| `a0e9703` | 214 | 144 (67%) | **70** |
| `ebc8212` | 138 | 43 (31%) | **95** |

The daily-feed change *looked* like a 35% drop in planting and was in fact a 36% **rise** in plants landed. A per-turn seed budget shared across units, so a crop is only chosen while uncommitted seed remains, is now implemented — closing it cleanly turned out to require fixing seed-purchase cadence in the same change, not just the budget itself; see the seed-budget entry below. (An older review put the block rate at 93%; that was a different build.)

**Each market's decay shape decides how much it can absorb — this is not in the docs and it drives everything.** Above the `I0` baseline, `price = base - above_target * base / shape(T,T) * shape(excess, T)`. The *shape* matters more than the base price. Total revenue extractable before a market hits the $1 floor, computed from `MARKET_PARAMS`:

| market | shape | units to floor | total $ | $/unit |
|---|---|---|---|---|
| EGG | log | 2000+ | 77,171 | 39 |
| WHEAT | log | 2000+ | 39,018 | 20 |
| MELON | **sq** | **158** | 26,236 | 166 |
| TOMATO | sqrt | 529 | 11,069 | 21 |
| CARROT | sqrt | 842 | 10,646 | 13 |
| STRAWBERRY | **linear** | **62** | 3,690 | 60 |

Melon collapses quadratically — unit 50 fetches $225, unit 150 fetches $25, everything past 158 is $1. **But do not conclude melon should be throttled: the town consumes inventory daily, so a market recovers between sales and the static numbers above are a floor, not a budget.** Three attempts to act on this table directly all lost (below). Treat it as an explanation of *why spreading sales over time works*, not as a quota.

**Use `head_to_head.py` for anything that changes selling.** Built-in opponents never sell, so market-timing changes look free against them; only a contested order book can price them. Seats are not symmetric — identical code gives seat 0 a few hundred less — so the harness plays both seats and averages. Always include the baseline against itself as a control; it must come out at ~0.

**There is no fertilizer arbitrage — the round trip is structurally break-even.** This was briefly recorded here as a +2,517 profit. That was wrong, and the way it was wrong is worth keeping.

From `LIQUIDATION_START_DAY` the sell loop stops exempting fertilizer, so the agent buys and sells it on the same days: one season spent ~10,767 on 111 units and received ~13,284 for 137. The gap looks like trading profit. It isn't — **buy and sell average exactly $97.0**, the round trip on the 111 bought units nets **-$4**, and the whole +2,517 is the **26 units the goose produced free**. Decomposing by unit rather than eyeballing the totals is what shows it.

It cannot work, for a reason visible in `MARKET_PARAMS`: fertilizer is `linear` both ways with target 0.40, so `price = 100 - 0.2 x excess` — **every unit we trade moves the price $0.20 against us**. Sell price is quoted pre-sell and buy price post-buy, which makes a same-day round trip pay and receive the identical number. Profit would need price drift between buying and selling, and there is none: across a whole season inventory moves 10,000 → 10,019, and even in self-play the price only ranges **93-100**. A 35-unit position moves the price by the entire seasonal range.

Measured, not just argued. A deliberate buy-the-dip / sell-the-recovery rule (buy ≤97 in batches of 4 up to 40 held, release ≥99) bought 573 units at an average of **97.8** and sold 591 at **97.0** — buying high and selling low, exactly as the price impact predicts — and lost **-1,486 head to head, winning 0 of 16 matches.**

**Do not remove the incidental buying either.** Blocking it during liquidation also lost, **-529, winning 1 of 16** (`af2a7e4` reverted that fix). Current behaviour is a local optimum in both directions; the mechanism behind the -529 is not established, and a plausible story for it is not evidence.

Generalises: **in a market this thin, your own order is the price move.** Before assuming a spread is harvestable, check it against the price impact of the position you would need to take.

**Demand is wildly uneven, and MELON has none.** `SHOPS` in the engine lists which products each shop consumes; shops fire every **4 steps** against the Town Centre's **24**, a **single-product shop consumes at double rate**, and shops unlock **with replacement** so the same one can land several times. So one unlocked shop is worth roughly six Town Centres.

Read the table and melon is in **no shop at all**. Its only sink is the Town Centre's one unit a day - about **30 units for the whole season** - and we were selling **183** into it. Carrot, by contrast, with `PET_CAFE` (single-product, 2x) unlocked twice, can be pulling ~37 a day.

`choose_crop` now divides our own pipeline by absorption **plus the demand that will still arrive** before the season ends, read live from `obs["town"]["unlocked_shops"]`. Worth **+3,358, 14/16 head to head** - the largest single change measured. Note this is *not* the same as the earlier failed attempt to diversify off melon by raising `SELF_SUPPLY_EXPONENT`: that was a blunt penalty on anything we already grow, this is a measurement of where the buyers actually are.

**Pick the animal by care-bank arithmetic, not by base price.** The `CARE` bank accrues +1 per fed-and-cared day and pays out **in full** on the next production day, so a **longer interval banks a bigger payout**. A goose collects 2 units per event; a sheep collects 4, at four times the unit price. Modelled net per season - and the model predicts 52 egg units against 52 measured, so it is calibrated:

| animal | events | per event | units | net |
|---|---|---|---|---|
| GOOSE | 26 | 2 | 52 | $2,023 |
| COW | 11 | 3 | 33 | $3,704 |
| **SHEEP** | 8 | **4** | 32 | **$5,236** |

`ACTIVE_ANIMALS = ["SHEEP"]` is worth **+1,332, 15/16**. A new species needs its own `SELL_PRICE_THRESHOLDS` and `MAX_SELL_PER_TURN` entries or it falls back to the default threshold and dumps into a curve that floors after 58 units.

**A second sheep is the sharpest two-harness disagreement we have found, and it is why one harness is not enough.** Head to head against this agent it looks like one of the largest gains available: **+5,119 (14/16)** on 8 seeds, **+3,623 (18/24)** on 12, with the counters all confirming it — 2 pastures built, 2 animals bought and placed, `FEED` 30 -> 58, **wool sold 34 -> 67**, against a cost of only 10 crop harvests.

Paired against the `starter` built-in the same change is **-19,514, losing 0 of 12 seeds, t = -20.0.**

**The built-in is right, and the failure is real.** Buying the second animal lands in the same **days 3-7 cash trough** that `MIN_MONEY_TO_HIRE` is tuned around, and empties it. Seed 0 against `starter`, one sheep against two:

| | money d5 | money d10 | `FEED` | pastures at season end | wool sold | bank |
|---|---|---|---|---|---|---|
| one sheep | $17 | $482 | 29 | `{PASTURE, animal: SHEEP}` | 32 | **52,981** |
| two sheep | **$5** | **$9** | **10** | `{PASTURE}`, `{PASTURE}` — **both empty** | **0** | **37,978** |

With no cash there is no feed, so **both sheep starve and escape** - unrecoverable - and the two pastures sit empty for the rest of the season producing nothing. The crew is starved too: `HIRE` 165 -> 112, `WATER` 611 -> 466.

This is **not** an artefact of the lowered hire gate, which was the obvious suspicion since both spend the same trough. Checked: at the old `MIN_MONEY_TO_HIRE = 150` the second sheep costs **-31,059 (0/12)**, *worse* than the -19,514 it costs at 20. Cheap hands cushion the collapse rather than causing it, so the two constants are independent.

It survives head to head *only* because that opponent crowds the market exactly the way we do, which shifts our cash timing enough to clear the trough. **The ladder is full of differently-shaped opponents.** Generalise it: **head to head can bless a change that only works because the opponent is a copy of us.** That is the mirror image of the built-ins' known flaw, and the reason the standard is now *two harnesses that can disagree* - the hire-gate fix passing both is what made it trustworthy.

Raising `MAX_ANIMALS` is only safe once the *n*-th purchase is gated on surviving the trough (a bank floor or a day gate), then re-measured on both harnesses. Past 2 the count itself is the problem regardless: 3 is **-2,618 (6/16)** and 4 is **-16,121 (0/16)** even head to head.

**Correction, 2026-08-17 (`3b8d36f`, `da8cdea` on `origin/main`): the trough this section is built around is now closed by a different fix, and the second-sheep numbers above are stale.** Retuning `MIN_CASH_RESERVE_FOR_SEED_BUYING` 100 → 450 (a seed-purchase-cadence fix, not an animal fix) removed the days 3-7 cash trough directly — day-5 bank $17 → $392 on seed 0 vs `starter`. Re-measured with that fix in place, a second sheep is **+900 (8/12)** vs `starter`, not -19,514 (0/12) — a ~20,000 swing from one unrelated constant, confirming the mechanism this section already names (cash starvation, not opportunity cost). Head to head still likes it, both before and after (+3,623 then, +4,384 now). Still only **t = 0.61**, so this is not yet a "ship `MAX_ANIMALS = 2`" result — but the *reason* to hold it at 1 has changed from "a second animal is a heavy loss" to "not yet proven a clean win post-trough-fix." Two independently-sampled contested top-ladder replays (`docs/REPLAY_ANALYSIS.md`) also show every strong player running COW+SHEEP (8-9 animals total) on a 12-15 unit crew — see `docs/ROADMAP.md` Phase 2/3 before re-testing this.

**Correction, 2026-08-23: the shipped `ACTIVE_ANIMALS = ["SHEEP", "COW"]`, `MAX_ANIMALS = 4` configuration is now a confirmed win on every harness available, closing the "not yet proven" status above.** Measured against the actual pre-diversification baseline (`ACTIVE_ANIMALS = ["SHEEP"]`, `MAX_ANIMALS = 1`, commit `ec38fc5^` — not `78745f3`, a later refactor whose parent already carried the multi-species config):

| harness | mean delta | wins |
|---|---|---|
| paired vs `starter`, 12 seeds | +11,120 | 10/12, t=4.30 |
| paired vs `pass`, 12 seeds | +14,017 | 12/12, t=6.82 |
| `head_to_head.py` vs baseline, 12 seeds x 2 seats | +12,887 | **24/24** |

Self-control (`main.py` vs itself) read +0 on 3/6, confirming the harness. All three clear this repo's decisive bar — including the contested head-to-head, the harness that would be needed to catch a trough-starvation failure the never-selling built-ins can't see.

`bptk.py`'s first dedicated animal/land diagnosis pass (never run before now) supplies the mechanism, not just the number. Against a `bptk.py`-only hypothetical (4 SHEEP, no COW, same `MAX_ANIMALS = 4` — never applied to real `main.py`), across 5 seeds, the single-species variant doesn't just underperform, it starves structurally: 4 animal escapes on every seed in solo mode (vs 0 for the shipped diverse roster), and the fourth pasture never gets built, because concentrated single-species spend blows the cash floor through the entire `LAND_BUY_START_DAY`-`LAND_BUY_LAST_USEFUL_DAY` (6-18) window, permanently missing that season's land purchase (`BUILD_PASTURE` stalls at 3, never 4, since `money - cost < MIN_CASH_RESERVE_FOR_LAND_BUYING` never clears in that window). The two rosters' total dollar cost is nearly identical (~$2,000 vs ~$1,800) — it's the *timing* of the spend relative to the land-buying window that flips the outcome. Same "gate priced against the wrong thing" pattern already named for `MIN_MONEY_TO_HIRE`, showing up again in `MIN_CASH_RESERVE_FOR_LAND_BUYING`, which is not gated on animal-herd composition at all. This single-species collapse is a **bptk.py-only signal** (its zero-travel-time abstraction inflates magnitudes 1.5-2x, and the variant was never run on the real engine) — real in direction, not yet trusted in magnitude without a real-engine trace.

This pass also retires `bptk.py`'s own `validate()` scenario 5 (`5_second_sheep_trough`) framing as stale: under the shipped `ACTIVE_ANIMALS`, `MAX_ANIMALS = 2` now reliably builds one SHEEP and one COW (`pick_next_animal_species`'s fewest-owned tie-break), not two sheep, on all 5 seeds tested.

A real-engine `selfplay_bench.py` cross-check (seeds 0-2: mean 65,672, stdev 2,810, min 62,497, max 67,841) shows no cash-trough collapse signal under the shipped config — a real mixed herd selling both WOOL (191) and MILK (165) across those seeds — consistent with the harness numbers above and with nothing like the single-species hypothetical's collapse.

**Verdict: animal-side tuning is closed for now.** `MAX_ANIMALS = 2` was the open question in the previous correction; the shipped config has moved past it to 4 with two species, and wins cleanly on every measure available. The next open lever is `docs/ROADMAP.md`'s Phase 4 (crop `occupancy_kind`), not this.

**Do not blame market depth - that theory is wrong and not worth re-testing.** The static curve says WOOL floors 58 units above `I0` (`sq`, T=105), so a premium crash looks like the binding constraint. Measured end-of-season it is not: at one, two *and* three sheep the market ends with inventory **below** the 10,000 baseline (9,822 / 9,855 / 9,743) at a price **above** the $200 base (244 / 243 / 248), with **zero** wool unsold. The town eats wool faster than three sheep can make it.

**Do not blame market depth - that theory is wrong and not worth re-testing.** The static curve says WOOL floors 58 units above `I0` (`sq`, T=105), so a premium crash looks like the binding constraint. Measured end-of-season it is not: at one, two *and* three sheep the market ends with inventory **below** the 10,000 baseline (9,822 / 9,855 / 9,743) at a price **above** the $200 base (244 / 243 / 248), with **zero** wool unsold. The town eats wool faster than three sheep can make it.

**A denser crew is now a WIN, and the old entry here was wrong twice over.** It was rejected against the across-seed stdev (the wrong test) on a far older agent. `WORK_TILES_PER_HAND` 6 -> 4 is **+1,910, winning 16 of 16**. At the time the farm watered **19.2 tiles a day against 24 planted** - it could not keep alive the land it already held, so hands were exactly the right lever.

**That shortfall is now closed, which re-opens the land question.** Re-measured after the hire-gate fix with `experiments/ceiling.py`, and it holds in a *contested* market as well as self-play (checked, because self-play flatters anything that doesn't compete for a scarce sink): the farm runs **24 of 25 tiles planted from day 4 to day 19**, at **water/planted = 1.00** through mid-season, with near-zero weeds and **13% of unit-turns idle on `PASS`**. Season-wide the ratio moved **0.80 -> 0.94**. We now keep alive everything we own. Note *how* it closed - watering per day is unchanged at ~19; the agent stopped over-planting past what it could tend.

That same measurement used to settle **`BUY_LAND`**: acreage cannot be the ceiling while we are under-watering what we own.

**That argument has expired, and `BUY_LAND` still loses - for a different reason.** We now water 100% of what we plant, so the old mechanism no longer applies. The replacement test is whether the crew can absorb *more* work, and it cannot: on the current 25 tiles a denser crew is now a **heavy loss in both directions** - `WORK_TILES_PER_HAND` 3 is **-7,352 (0/16)** and 2 is **-7,385 (0/16)**, against the 4 the agent uses. Surplus units do not idle politely; they plant tiles the crew then cannot water and spend seed money doing it.

`MAX_HANDS_PER_DAY` is **dead code at 25 tiles** - 12 and 16 both measure at *exactly* +0. `decide_hire_orders` computes `wanted = min(MAX_HANDS_PER_DAY, work // WORK_TILES_PER_HAND)`, and a farm that is already tended has little pending work, so `work // 4` lands near 6 and never reaches the cap. **The ratio, not the cap, is the knob that scales the crew** - don't reach for the cap when you mean the ratio.

So more ground would need more hands, and more hands were measurably harmful at 25 tiles.

**That precondition is now met, and `BUY_LAND` ships (2026-08-18).** The error in everything above was moving one knob at a time: every `BUY_LAND` test held the crew fixed while adding tiles, and every crew-density test held tiles fixed while adding units. Neither is the ceiling - **the pair is**, plus the animals to use the ground and thresholds low enough to sell what it all produces. Shipped as one change:

| | |
|---|---|
| `decide_land_orders` | two quadrants, days 6 and 11, **25 tiles -> 75** |
| `MAX_HANDS_PER_DAY` | 8 -> **15** (the cap finally binds; at 25 tiles it was dead code) |
| `MAX_ANIMALS` | 3 -> **4** |
| `LIQUIDATION_START_DAY` | 19 -> **10** |
| `SELL_PRICE_THRESHOLDS` | **halved** |

**The local harnesses did not like it and the ladder did.** Paired vs `starter` +4,828 (8/12, t=2.18), head to head +1,652 (14/24), self-play mean up but stdev 1.8x - positive everywhere, convincing nowhere. On the ladder it became **our best agent ever: 623-635 over 29 episodes against a previous best of 612.5**, banking **55,182 against opponents averaging 65,326**, the strongest field any of our submissions has drawn.

Trust the ladder over the local harnesses **for this class of change specifically**, and the reason is documented rather than a hunch: every local opponent is a 25-tile farm, and `pass`/`random`/`starter` never sell at all, so they are structurally incapable of seeing a scale change pay off. That is what `experiments/bigfarm_opponent.py` exists to fix.

**One number did not improve: self-play stdev, 6,329 against 3,481.** Bradley-Terry punishes variance, so closing that gap is the open work - not another scale increase.

**Closing the seed-overcommit bug requires fixing purchase cadence in the same change, not routing.** The PLANT step's seed check (`seeds.get(crop, 0) > 0`) has no shared per-turn budget, so multiple units can each independently choose the same understocked crop in one turn; the engine drops **all** PLANT requests for that crop when demand exceeds held seed (`kaggriculture.py:920-931`), not just the excess. Three independent fixes that added a shared per-turn budget — denied units walking away, passing in place, or falling through the full priority ladder — **all starved the sheep to death by day 7 on every seed tested** (worst: -15,785 mean, 0/12 wins) and looked like a routing problem. It wasn't: an instrumented turn-by-turn trace showed the farmer never leaves its starting shed-adjacent tile in a working season - FEED/CARE/PICKUP all resolve there daily - so the PLANT step never touches the feeding unit at all, regardless of what a denied unit does next.

The real mechanism: once the overcommit bug is closed, a seed is reliably *consumed* every turn, and the old buy rule (`should_buy_seed`, restock the instant held stock dips under `MAX_SEED_STOCKPILE`) re-fires every single turn. For MELON (~$80/seed) that's an $80/turn drain - the bank crashed from ~$2,160 to ~$25 by day 3-4 in every failed variant. At that point the wheat safety-net `BUY_PRODUCT` order is silently rejected every turn (`kaggriculture.py:663`, `money < price`, no error raised), the shed runs dry, and the sheep misses two consecutive feeds. **It's a seed-repurchase cost spiral, not unit contention** - a unit dedicated full-time to animal upkeep didn't fix it either (see dead ends), because that doesn't touch purchase cadence.

The fix that actually works: keep the shared per-turn budget (`plant_budget`, closing the overcommit bug), but only trigger a restock once a crop's held stock is **fully exhausted** (`SEED_REBUY_TRIGGER = 0`, not "under the cap"), buy the whole gap back to `MAX_SEED_STOCKPILE` in one batched order (`seed_restock_quantity`), and add `MIN_CASH_RESERVE_FOR_SEED_BUYING` so a restock batch can never drop the bank below what the wheat safety net needs. **+2,271 mean, 10/12 wins, t=3.70** - same total seed volume bought roughly a third as often. Generalise it: when closing a bug changes how often a *downstream* rule fires (here, a purchase-trigger check), audit that rule's frequency assumptions too - the bug may have been silently rate-limiting something expensive.

**Measured dead ends — don't re-run these without changing something first.** All lost on the full batch:

- **Path C (STRAW-pin + 3→10 animal sequencing) loses even after its feed-system failure is repaired — closed 2026-08-26, and its bptk evaluation needed repairing first.** The real-engine diagnosis (`e0ce6c2`: −5,698 paired vs `pass`, 17–20 escapes/12 episodes) blamed the STRAW pin starving shed WHEAT to its reserve floor plus a toothless `wheat_stock > 0` scale gate. Both mechanism claims verified true in traces, and implementing the fixes (`pin_wheat_valve` + owned-keyed `scale_wheat_buffer`, now cfg keys in `bptk.py`) measurably repaired the feed system: BUY_PRODUCT WHEAT 186 → 91 (Path A: 90), shed WHEAT off the floor, herd past beach-head. **It still lost: −3,110 mean, 5/12 vs Path A**, with a −79,182 tail seed. The diagnosis's own prescription (buffer ≥ reserve × scale_max = 20) stranded the herd at 3 animals on 12/12 seeds — the recorded hard-buffer-before-scale failure mode (F8-class), exactly as predicted; only the owned-keyed flavour avoids it. Per the pre-agreed close-out gate, `PATH_C_CORE_ENABLED = False` in `main.py`; full tables in `mydocs/PATH_C_RESEARCH_LOG.md` §11. Reopen only via a different mechanism (routes/L3), not another sequencing tweak.
  - Two transferable lessons from the pass. **(1) An override wrapper that mutates a module constant goes silently dead when `main.py` grows inline policy that bypasses that constant**: with `PATH_C_CORE_ENABLED = True`, `path_c_animal_cap()` never reads `MAX_ANIMALS`, so every bptk cfg arm ran byte-identical while *looking* differentiated — several ablation conclusions in `e0ce6c2`'s message were artifacts. Always verify a knob moves the counter it targets before reading any ablation table built on it. **(2) In solo uncontested bptk, releasing the STRAW pin changes nothing** — `choose_crop` re-picks strawberry on its own scoring, so valve-open episodes were byte-identical to pinned ones; the pin's harm (and the best bptk mean of any arm, `no_straw_pin` 115,887) is real but does not clear the win-count bar either.

- **`CROP_PLANTING_WINDOWS` is no longer the clear loss it is recorded as above - re-measure before acting on that entry.** The window gate is recorded here as **-3,689 mean, 3/12** paired vs `starter`. That number was measured on a base *without* `choose_crop(require_held_seed=True)`. Re-measured on current `main` with the fix in place, 12 seeds:

  | harness | removing the windows |
  |---|---|
  | `paired_compare.py` vs `starter`, 12 seeds | **+2,125 mean, 7/12, t=1.20** |
  | `head_to_head.py` vs current `main`, 12 seeds x 2 seats | **-1,368 mean, 7/24** |

  **The two harnesses disagree and neither clears a bar**, so by this repo's win-count-first rule there is no case for reverting the gate *and* no case for calling it a proven win. It is unresolved on the current base.

  The plausible reason they interact: the recorded mechanism for why windows lost was that freed tile-time gets refilled with cheap, fast-cycling WHEAT. `require_held_seed` changes exactly what fills a turn when the top pick has no seed in hand, so it is not surprising that it moves the windows result - but that link is a hypothesis, not something measured. Deltas here are enormously noisy (sd 6,129, seed 4 alone swings +19,178), so anything conclusive needs more seeds than 12.

  Generalises, and this repo now has several instances of it: **a dead end is measured against a base, not in the abstract.** When a fix lands that plausibly touches the same mechanism, the recorded verdict is a hypothesis again, not a conclusion. Do not revert on a stale number - and do not trust one either.

- **Aggressive selling on the Phase 3 base does not clear the bar, in either of the two forms it was tried — and the second form fails the same way on two independent bases.** Both were run by @future-centaur on `experiment/phase3-aggressive-selling` against a frozen Phase 3 control, on all three harnesses.

  **Variant A, four constants** (`SELL_PRICE_THRESHOLDS` halved again, `DEFAULT_SELL_THRESHOLD` 50→25, `SHED_FORCE_SELL_THRESHOLD` 70→40, `LIQUIDATION_START_DAY` 19→10): **+1,685 mean but 17/24 head to head**, -538 (7/12, t=-0.29) paired vs `starter`, self-play mean 63,982 / floor 48,170. 17/24 is between this repo's clean-win bar and a coin flip. The `starter` result is the built-in-flattery pattern already documented for selling changes, not a corroborating loss — it is an uninformative harness on this question. **Inconclusive, not shipped.**

  **Variant B, the continuous cadence model** (`estimate_sell_or_hold_value` / `inventory_pressure` / `cadence_urgency` replacing `should_sell`'s fixed thresholds, with the liquidation cliff disabled by design): **12/24 head to head — an exact coin flip** — **-2,531 (3/12, t=-1.74) paired vs `starter`**, self-play stdev 11,123 / floor 45,360. Worse than Variant A on every axis.

  **Variant B has now lost on two different bases, which is suggestive - but the two results are not measured the same way, so do not over-read it.** The same model was ported once before onto a different base (post-PR29 `main`, pre-land, commit `9a6a5c6`) and rejected there on a **self-play paired** comparison: +1,345 mean (8/14) bought at the cost of a **7,777-unit floor**. The Phase 3 port's decisive number is a **paired-vs-`starter`** loss (-2,531, 3/12), and its self-play run reports only stdev and floor at 8 seeds - there is no matched self-play mean against a control at the same seed count. So the honest claim is **two losses, not one reproduced mechanism**: the mean-vs-floor tradeoff is established on the first base and merely consistent with the second.

What would settle it is cheap and nobody has run it: `selfplay_bench.py` on the Phase 3 Variant B build and its own control at the same seeds, reporting **mean and floor for both**. Until then treat this as "lost twice, direction unattractive", not "structurally closed" - and note that a floor loss still matters more than a mean gain here, because Bradley-Terry counts pairwise wins.

  Generalises: **a mean gain paid for with a floor loss is not a gain in a tournament that scores pairwise wins.** Check the floor before the mean on anything that changes selling timing.

- **A herd-scaled cash floor does not move the animal cliff; it breaks the agent.** `MAX_ANIMALS` is a cliff rather than a dial (4 works, 5 collapses to 356) and top-ladder agents run 8-9, so the obvious suspect is that `ANIMAL_SPEND_CAP_FRACTION` is proportional to cash - it says the same thing at one animal as at eight, while the feed bill scales with the herd. Gating the *n*-th purchase on leaving `reserve * (owned + 1)` behind loses **0 of 3 on all 8 variants** (animals 4/5/6/8 x reserve 300/600), most banking **~2,000**. Once the gate binds, `MAX_ANIMALS` never binds, so every count collapses to the same agent. The failure is violent and seed-dependent: seed 0 stays competitive (65,900 vs 69,723) while **seed 1 ends at $443**, below the $3,000 starting stake. **And on seed 0 against `starter` that same variant banks 83,617, beating the shipped build's 77,577** - one seed plus one never-selling built-in would have shipped a catastrophe. Mechanism: the gate blocks a purchase during the days 3-7 trough, a pasture is built but never filled, and `choose_animal_to_build` refuses to build another while one sits unfilled, stranding the tile for the season. The cliff is real and **still unexplained**.

- **A shared per-turn seed budget alone, however the denial is handled, is a catastrophic loss without also fixing purchase cadence.** Three variants - denied units walk away, pass in place, or fall through the full priority ladder - scored -15,635 to -15,785, losing every match (0/12 in the cleanest test) and starving the season's one sheep to death on every seed. The denial *behavior* was never the variable; closing the overcommit bug at all triggers the $80/turn seed-repurchase spiral above - fix the cadence in the same change or don't ship the budget at all.
- **Dedicating a unit full-time to animal upkeep is a pure loss when the animal wasn't actually starving.** -813 mean, 4/12 wins. Against `starter`, the unmodified baseline never loses the sheep on any of 12 seeds, so the dedicated keeper paid a real opportunity cost (the same "single farmer's upkeep capacity" mechanism as the hiring/crew-density lessons above) fixing a problem that wasn't present in that matchup.
- **A bigger wheat reserve alone (2 → 6, batched into one purchase) is a small, real, statistically significant loss with no offsetting safety benefit measured.** -98 mean, 1/12 wins, t=-7.71 - parking 4 extra wheat units off the market all season costs roughly what they'd have sold for, and (per the point above) there was no starvation in this harness for the bigger buffer to prevent.

- **More than one animal is a heavy loss — but the recorded *reason* was wrong, and so was one of the measurements.** `MAX_ANIMALS` 2/3/4/6 as geese scored 38,413 / 33,983 / 33,617 / 21,749 against 43,099 for one. Two is not opportunity cost, it is **cash starvation in the days 3-7 trough** (see the second-sheep section above) — and it *wins* head to head, so it is only visible on the built-in harness. Three and four are opportunity cost, as recorded.

  The **sheep-plus-cow** result (-16,634, 0 of 16) is **unreproducible as written**: `ACTIVE_ANIMALS = ["SHEEP", "COW"]` with `MAX_ANIMALS = 2` builds **two sheep and no cow** — `choose_animal_to_build` ranks by care-bank arithmetic and sheep wins both slots (verified: `BUY_ANIMAL SHEEP x2`, `PASTURE x2`, byte-identical episode to the two-sheep variant). **Two independent deep markets remains untested, not refuted.** Testing it needs species diversity forced, which the current code does not do.

- **Diversifying away from melon is a large loss.** Raising `SELF_SUPPLY_EXPONENT` from 2.0 to 3.0/4.0/6.0 scored **-6,883 / -5,594 / -9,858** head-to-head against the current agent, losing every match. Melon concentration survives its own price crash.
- **Selling melon in smaller slices is a large loss.** `MAX_SELL_PER_TURN["MELON"]` from 15 to 6: **-5,958, 0/8 matches.**

- ~~**`BUY_LAND` is a loss, even when rich.**~~ **Retracted 2026-08-18 - it ships, together with the crew, animals and selling cadence it needs.** Kept visible because it is the third dead end in this file that turned out to be a measurement artefact, and all three had the same shape: one variable moved while the variable it depends on was pinned. Original entry follows.

  **`BUY_LAND` is a loss, even when rich.** Tested at a ~7k bank (mean roughly halved, win rate 12/12 → 6/12) and again at a ~29k bank where the $1k/$2k/$4k quadrants are pocket change (still ~2,000–2,900 worse). More ground spreads a fixed crew thinner, and melon needs sustained watering to reach full yield. **The crew, not the acreage, is the ceiling** — revisit only alongside a genuine upkeep increase.

  **Correction, 2026-08-17 (`da8cdea` on `origin/main`): this was measured entirely at a fixed 6-unit/25-tile crew, and that confound is now the point, not a footnote.** Two contested top-ladder replays sampled independently of each other (`docs/REPLAY_ANALYSIS.md`, corroborating the six in `docs/ROADMAP.md`) show every strong player buying land exactly twice (days 6-11, 25 → 75 tiles) while running a 12-15 unit crew — a looser 5.8 tiles/unit than our 25/6. Every `BUY_LAND` test here held crew size fixed while adding tiles; every crew-density test (`WORK_TILES_PER_HAND` 2/3 at 25 tiles) held tiles fixed while adding units. Both are the same confound in mirror image, and neither knob alone is the ceiling — the pair is. Not retracted (still a real loss *at this crew size*), but "the crew, not the acreage, is the ceiling" should now read as "the crew is *sized for* this acreage" — see `docs/ROADMAP.md` Phase 2 (crew size as a derived function) before re-testing `BUY_LAND` in isolation again.
- ~~**A denser crew is a loss.**~~ **Retracted — it is a win.** This claimed `WORK_TILES_PER_HAND` 4 cost 1,300–3,400. It was judged against the across-seed stdev, which is the wrong test, and measured on a far older agent. Re-run head to head it is **+1,910, 16 of 16**. Kept here as a visible correction rather than deleted, because it is the second dead end this repo recorded that was really a measurement error.

- **A fertilizer-aware yield bonus for TOMATO in `choose_crop` is a wash-to-loss, and not for the reason the original plan (`mydocs/FIX.md`) worried about.** The idea: TOMATO (interval=1) benefits more per fertilizer application than any other crop, so bump its `expected_yield` when a placed/filled sheep gives a reliable, renewing `FERTILIZER` source (deliberately *not* gated on held stock, which is a one-time balance already claimed by existing tiles — see `FERTILIZER_YIELD_BONUS`'s comment in `main.py`). Implemented as `expected_yield += 1.0` for TOMATO only, guarded by `has_active_fertilizer_source(farm)`.

  Measured `paired_compare.py` vs `starter`, 12 seeds: **-101 mean, 2/12 wins**. Vs `pass`, 12 seeds: **+63 mean, 2/12 wins**. `head_to_head.py`, 12 seeds × 2 seats: **+386 mean but only 11/24 wins** (self-control came back at exactly 0/24-mean as expected, so the harness itself isn't lying). By this repo's own rule — read win-count before mean — 2/12, 2/12, and 11/24 are all losses or, at best, coin-flips propped up by a few large swings.

  **The mechanism isn't melon competition** (the thing three earlier diversification attempts all died to) — a per-seed action-histogram diff showed the swapped-out crop was **WHEAT and CARROT**, not MELON, every time. TOMATO's seed costs 5x WHEAT's and ties up a tile for 8 days per planting against WHEAT's 4; a fast-turnover cheap crop replanted repeatedly can out-earn one slower, pricier planting even at a higher per-unit price, because total units cycled through the tile is what the season actually pays for. One seed (`seed=2` vs `starter`) made this concrete: candidate planted 7 TOMATO / 24 WHEAT where baseline planted 0 TOMATO / 45 WHEAT — total units sold dropped from 35 (all WHEAT) to 18 (15 WHEAT + 3 TOMATO), for **-655**.

  Generalises: **a yield-per-application bonus isn't the same as a yield-per-tile-day bonus.** The `growth_days` denominator in `score = future_price * expected_yield / growth_days` already prices in how long a tile is committed — a flat additive bump to the numerator doesn't account for what a fast crop would have cycled through that same tile-time instead. Raising the bonus further would not fix this (the diagnostic shows displacement, not insufficient signal), so this wasn't retried at 1.5/2.0. Not shipped; see git history on `fix/tomato-fertilizer-yield-bonus` (commit `4bd053c`) for the full implementation if a future attempt wants to start from it with a smarter gate (e.g. only prefer TOMATO when WHEAT/CARROT are *also* in glut, closer to `FIX.md`'s original "crossover" framing).

- **A `growth_days` "correctness" fix for TOMATO/STRAWBERRY's crop score is also a loss — this closes out the whole TOMATO-scoring investigation.** `choose_crop`'s score (`future_price * expected_yield / growth_days`) uses `CROPS[crop]["max_yield_day"]` as `growth_days` for every crop. For TOMATO/STRAWBERRY ("ongoing" crops) that's wrong: the engine's `HARVEST` op does **not** clear an ongoing crop's tile, so it keeps producing `interval`-spaced ticks past `max_yield_day` and only starts decaying to a `WEED` after the *last* tick. Measured directly against the engine's `_daily_refresh_plants`/`_decay_plants`: TOMATO's tile really frees up around **day 12**, not the formula's 8; STRAWBERRY's around **day 17**, not 10. A fertilizer-bonus attempt for TOMATO had already failed three ways (flat bonus, absolute gate, relative gate — each displaced WHEAT/CARROT for a net loss), and this looked like the explanation why: the *current* formula already overvalues both crops, so every "boost TOMATO" attempt was pushing an already-overvalued pick even higher.

  Implemented the fix (`crop_growth_days()` in `main.py`, deriving `first_yield_day + (max_yield-1)*interval + 1` for ongoing crops instead of `max_yield_day`, unchanged for one-shot crops) and measured it properly — and it is a **decisive loss**, not the "legitimate lever" it looked like on paper:

  | variant | opponent, seeds | mean delta | wins |
  |---|---|---|---|
  | both crops corrected | `starter`, 12 | **-5,099** | **0/12** |
  | both crops corrected | `pass`, 12 | **-7,116** | **0/12** |
  | STRAWBERRY corrected, TOMATO untouched | `starter`, 6 | **-5,593** | **0/6** |
  | TOMATO corrected, STRAWBERRY untouched | `starter`, 12 | -104 | 1/12 |

  Isolating the two crops shows the loss is almost entirely **STRAWBERRY** — correcting it alone reproduces nearly the whole effect. Correcting **TOMATO alone is a wash**: 10 of the 12 seeds show an *exact* zero delta, meaning the corrected TOMATO score essentially never flips a real decision in practice — consistent with the earlier relative-gate assessment's own finding that TOMATO's flip rate is small on most seeds.

  Mechanism (seed 0 vs `starter`, action histogram): with STRAWBERRY corrected, its plant count goes **14 → 0** for the whole season (baseline sold 77 STRAWBERRY units), and CARROT floods in to fill the gap (**13 → 158 plantings, only 50 sold** — oversupplied and mostly wasted), while `FERTILIZER` sales collapse **114 → 37** (fewer ongoing-crop tiles left to fertilize). STRAWBERRY's `growth_days=10` looks like a bug next to its ~17-day real tile-occupancy, but empirically it is **load-bearing**: the more mechanically accurate number makes the heuristic score *worse* at predicting real profit, not better, because the score is a rough proxy and STRAWBERRY's premium price outperforms what an honest denominator would suggest.

  Generalizes past this specific fix: **"more mechanically accurate" is not the same as "a better predictor of real profit" for a hand-built heuristic score.** A correction that is true of the underlying mechanic can still make the score's *ranking* worse, because the original (wrong) constant may have been implicitly compensating for something the formula doesn't model elsewhere — here, STRAWBERRY's price ceiling and the fact that a CARROT glut is a worse outcome than an "inaccurate" STRAWBERRY denominator. Four attempts across this investigation (flat bonus, absolute gate, relative gate proposal, and now this accuracy fix) have all failed for different, specific, measured reasons. **Treat TOMATO/STRAWBERRY crop-selection scoring as closed** unless genuinely new evidence appears — a plausible mechanism is not enough on its own, as this entry itself demonstrates.

- **A crop-planting-window gate (`CROP_PLANTING_WINDOWS`: MELON days 0-11, STRAWBERRY 5-12, CARROT 21-25, TOMATO excluded, derived from real top-ladder replays) is a clear loss on its own, for the same displacement reason as the `growth_days` fix above.** `paired_compare.py` vs `starter`, 12 seeds: **-3,689 mean, 3/12 wins**; `head_to_head.py` vs a frozen control: +343/12-24, a coin flip that doesn't rescue the paired loss. Mechanism, confirmed via action-histogram diagnostics: TOMATO landings go to 0 as designed, STRAWBERRY landings roughly halve from the narrower window, but **WHEAT landings jump 4-5x (24→105, 42→133)** — cutting STRAWBERRY's window frees real tile-time, and the agent fills it with cheap, fast-cycling WHEAT instead of the higher-value crop it used to hold. Same trap as the `growth_days` dead end just above: freeing tile-time doesn't help if what fills it is worth less per tile-day. The windows survive as shared groundwork for the two fill-priority tests below (which fix what fills the freed time, not the windows themselves) — not reopened on their own.

- **Two attempts to fix what fills the tile-time `CROP_PLANTING_WINDOWS` frees up — a priority-ordered fallback and a target-slot allocation — are both clear losses, and neither touches the real constraint.** Both wrap `choose_crop`'s output after the fact rather than fixing its scoring, which discards the function's existing glut-aware price comparison for the crops they override rather than adding anything to it:
  - **Test 1a — price-blind fallback (WHEAT's default pick tries MELON, then CARROT, before falling back to WHEAT).** `paired_compare.py` vs `starter`, 12 seeds: **-5,775 mean, 2/12 wins, t=-3.11**; `head_to_head.py` vs control: +81/12-24, an exact coin flip. Mechanism: the fallback has no glut check, so it forces MELON/CARROT into the exact gluts the day-windows were meant to prevent — WHEAT itself still lands at 72-90 per traced seed, well above the pre-window baseline of ~24-42.
  - **Test 1b — target-slot allocation (STRAWBERRY capped at 50% of owned tiles, MELON at 30%, `choose_crop` skips a crop once its target is met).** `paired_compare.py` vs `starter`, 12 seeds: **-7,664 mean, 0/12 wins, t=-3.50**, negative on every single seed; `head_to_head.py` vs control: -993/11-24. Mechanism: **a slot cap is a ceiling, not a floor.** MELON's target binds cleanly, but STRAWBERRY's live count peaks at 26 against a target of 38 — its own 8-day window plus early-season crew/cash constraints already cap it below the target, so the gate never fires and the freed tile-time still defaults to WHEAT exactly as in the window-gate dead end above.

  Both results point at the same unaddressed constraint: **STRAWBERRY's own window plus early-season crew/cash capacity caps how much of it can land, regardless of what fallback/allocation logic does with what's left over.** A priority order and a slot cap both operate strictly *after* that ceiling is already hit — they redirect leftovers, they don't raise the ceiling. Any future fix here likely belongs in what feeds `choose_crop`'s comparison (seed-buying cadence, hiring cadence) rather than in another policy layered on top of its output.

- **A continuous sell-or-hold cadence model, replacing the fixed per-product sell threshold with a day-based urgency ramp, is a decisive loss — tried twice, on two different bases, with the same failure mode both times.** First port (`9a6a5c6`, onto pre-land `main`): self-play paired mean 61,024 → 62,369 (+1,345, 8/14) but floor 52,636 → 44,859 (**-7,777**) — a worse floor for a smaller mean gain, the wrong trade for a Bradley-Terry final. Second port (onto the post-`BUY_LAND` Phase 3 base): `head_to_head.py` vs control +364/12-24 (an exact coin flip, not even a win), `paired_compare.py` vs `starter` **-2,531 mean, 3/12 wins, t=-1.74** (a decisive loss, not the wash the first port's self-play number suggested it might be), self-play stdev 11,123 in the same wide-and-low shape as the first port's floor problem. **The mean-vs-floor tradeoff is a structural property of the cadence-urgency model itself, not an artifact of which base it's ported onto** — don't try a third port without a different mechanism than a smooth urgency ramp.

## Sources of truth, in priority order

Kaggle staff, resolving a thread of documented-vs-actual mismatches: **"engine is the source of truth."** Follow that order here.

1. **The installed environment itself** — `.venv/Lib/site-packages/kaggle_environments/envs/kaggriculture/`. This is the code that actually scores you:
   - `kaggriculture.py` — the real interpreter. `MARKET_PARAMS` and the object tables live here; settle any mechanics dispute by reading it.
   - `AGENTS.md` — the official agent-authoring guide.
   - `README.md` — full rules, object/price/shop tables.
   - `kaggriculture.json` — config defaults + observation/action schema.
2. **`docs/kaggriculture_context.md`** — a compiled snapshot (Aug 15, 2026) of the competition pages. Its deadlines, prizes, submission limits, and compute budgets were re-verified verbatim against the live site on that date, and it postdates the balance patch. Its **mechanics** claims are second-tier — staff have corrected several doc-vs-engine mismatches over the season, so check the engine before trusting a mechanic here. Known gap: the **per-turn timeout** (see below). Section anchors: §3.2 crop & animal table, §3.10 market pricing, §3.12 observation schema.
3. `README.md` at the repo root — architecture diagrams (state manager → strategy → planner → executor) and competition dates.

Official starter notebook (pinned, Apache 2.0): <https://www.kaggle.com/code/bovard/kaggriculture-getting-started>.

The env also ships a second environment, **`kaggriculture_beginner`**. It is referenced nowhere on the competition site and the official starter notebook never calls it — always `make("kaggriculture", ...)`.

**Pin `kaggle-environments>=1.32.6`.** A mid-season balance patch (~Aug 6, 2026) cut Town Center demand to a flat 1×/day (was 2×/day with a 2×/4× late-game ramp) and made shop unlocks sample *with* replacement; staff told everyone to upgrade. The official starter notebook still pins `>=1.32.2`, which predates the patch — don't copy that pin. The env is patched mid-competition, so after any upgrade, re-read `kaggriculture.py` rather than trusting cached knowledge of the mechanics.

## Setup and commands

The environment is already built at `.venv/` (Python 3.13.7, provisioned by `uv`). `pyenv` is not installed on this machine and the README's `pyenv` + `.venv/bin/activate` instructions do not work here — on Windows it's `.venv/Scripts/`.

For notebooks, select the **`Python 3.13 (washamba_bots)`** Jupyter kernel. Register it with `.venv/Scripts/python.exe -m ipykernel install --user --name washamba-bots --display-name "Python 3.13 (washamba_bots)"`. This matters: a kernelspec whose `argv[0]` is the bare word `python` (rather than an absolute path) launches whatever is first on `PATH` — which is how a notebook ends up on system Python reporting `No module named kaggle_environments` while the venv sits there working. For the same reason, use `%pip install` in notebooks, never `!pip install`: `%pip` targets the running kernel, `!pip` shells out to `PATH`.

**The team is split across macOS and Windows — never commit an OS-specific interpreter path.** Binaries live in `.venv/bin/` on macOS and `.venv/Scripts/` on Windows, so a hardcoded path breaks the other half of the team *silently*: VS Code falls back to the system Python, and every `import kaggle_environments` fails with "could not be resolved" while the venv sits there working fine. This already happened once via `.vscode/settings.json`. Let the Python extension auto-discover `.venv/`, and keep committed tooling path-agnostic (`sys.executable`, not a literal path).

```bash
# Recreate from scratch if needed
uv venv --python 3.13.7 .venv
uv pip install --python .venv/Scripts/python.exe \
  "kaggle-environments>=1.32.6" kaggle \
  numpy pandas matplotlib seaborn jupyterlab ipykernel

# Run the agent (built-in opponents: "pass", "random", "starter")
.venv/Scripts/python.exe -c "
from kaggle_environments import make
env = make('kaggriculture', configuration={'episodeSteps': 720}, debug=True)
env.run(['main.py', 'random'])
print([(i, s.reward) for i, s in enumerate(env.steps[-1])])
"

# PRE-SUBMIT GATE: Kaggle validates every upload with a self-play episode.
# A crash there rejects the submission no matter how good the strategy is.
.venv/Scripts/python.exe -c "
from kaggle_environments import make
env = make('kaggriculture', configuration={'episodeSteps': 720, 'seed': 0})
env.run(['main.py', 'main.py'])
print([s.status for s in env.steps[-1]])   # must be ['DONE', 'DONE']
"

# Submit
.venv/Scripts/kaggle.exe competitions submit kaggriculture -f main.py -m 'message'
.venv/Scripts/kaggle.exe competitions submissions kaggriculture
.venv/Scripts/kaggle.exe competitions logs <EPISODE_ID> 0   # debug a failed validation episode
```

A full 720-turn episode runs in **~6.8s**, so hundreds of local games is a matter of minutes, not hours. A replay JSON is ~4.9 MB — don't commit them.

`requirements.txt` is a broad 190-package `pip freeze` from a wider ML workspace (jax, flax, transformers, open-spiel, litellm, and `pokerkit`), **not** this agent's dependency set. Installing it wholesale is not required, and a package appearing there is no license to import it from `main.py`.

Tests are stdlib `unittest` — **pytest is not installed and the suite doesn't need it**. Don't reach for pytest idioms (fixtures, `assert` rewriting, parametrize); match the existing `unittest.TestCase` style. No linter or type checker is configured (ruff, mypy, black all absent).

```bash
.venv/Scripts/python.exe -m unittest discover -s tests          # whole suite
.venv/Scripts/python.exe -m unittest tests.test_nikaangukia_meroni.TestShouldSell -v   # one case
```

Unit tests only cover helpers in isolation. **The real verification for a strategy change is a seeded batch, never a single game.** Run-to-run spread is huge — the same `main.py` vs `random` matchup scored 5228 and 3776 on two unseeded runs. **Stdev scales with the score**: it was ~±600 at the ~5,000 era and is ~±1,600–2,200 now, so a "+1,000" on one seed is well inside noise. A single episode cannot tell an improvement from luck, and a one-off loss to `starter` means nothing.

Pass `seed` in the configuration to make episodes reproducible — but **only against `pass` and `starter`**. Verified: on a fixed seed, those two reproduce an identical final bank exactly, while `random` does not (5169 vs 5120 on the same seed). `seed` controls environment stochasticity — weed spawns, shop unlocks — not the built-in `random` agent's own RNG. The drift is ~1%, far inside its ±410 stdev, so the `random` column is still usable; just **A/B strategy changes against `pass`/`starter`**, where a difference is signal rather than opponent noise.

**Judge a change with a paired comparison, not against the across-seed stdev.** `seeded_batch.py` reports a spread of roughly ±2,000, but that mostly measures how much *seasons* differ from each other — kinder weeds, luckier shop unlocks. Both versions play the same fixed seeds, so that variance is common to both arms and cancels. Testing a delta against it is far too strict and has already caused us to mislabel two real gains as noise.

```bash
git show main:main.py > /tmp/base_main.py
.venv/Scripts/python.exe experiments/paired_compare.py /tmp/base_main.py main.py
```

Same episodes, read both ways:

| change | across-seed view | paired view |
|---|---|---|
| daily feeding | +1,657 vs stdev 1,740 → "a wash" | +1,657, **12/12 seeds**, t = 9.9 |
| fertilizer | +1,764 vs stdev 2,206 → "within noise" | +1,764, **12/12 seeds**, t = 5.5 |

**Read the win count before any t-value.** Better on 12 of 12 needs no statistics; better on 7 of 12 is not rescued by one. Only pair against `pass`/`starter` — `random`'s own RNG is not seed-controlled, so the same seed does not reproduce the episode and the pairing is invalid.

Compare a change against the same seed set:

```bash
.venv/Scripts/python.exe experiments/seeded_batch.py    # mean/stdev/win-rate vs all 3 built-ins
.venv/Scripts/python.exe experiments/benchmark.py       # adds melon_maxxer from the official notebook
.venv/Scripts/python.exe experiments/selfplay_bench.py  # both sides run main.py - the honest number
.venv/Scripts/python.exe experiments/paired_compare.py A.py B.py  # A/B two versions on one seed set
```

At ~7s per season, 12 seeds × 3 opponents is about 4 minutes. Report mean and win-rate, not a single score. `experiments/replay_diagnostics.py` breaks a single episode down by action histogram and end-of-farm state — that's what found the weed cascade. Replay JSONs it dumps are multi-MB and gitignored.

**Benchmark against `route_v20`, not just the never-selling built-ins and self-play mirror matches.** `agents/route_v20.py` is a genuinely strong external opponent (see `agents/README.md`) — measured but not read, a yardstick, not a base to build on. Decode it once (requires the Kaggle CLI and network access; writes to the gitignored `experiments/.v20_agent.py`, never committed) and reuse the same decoded file for every future comparison:

```bash
.venv/Scripts/python.exe experiments/route_v20.py                                    # decode + self-test, once
.venv/Scripts/python.exe experiments/head_to_head.py experiments/.v20_agent.py main.py 12   # main.py's real change vs a genuinely strong opponent
```

Read it the same way as any other harness: win count first, both seats (`head_to_head.py` averages seat 0/1 since they aren't symmetric), and always run the self-control (same file both sides) once as a sanity check that must land at ~0.

**The built-in opponents never sell anything, so every number they produce is inflated.** `pass`, `random` and `starter` leave the market at its pristine starting inventory all season, and our sales never compete with a rival's. Measured on the same agent: ~41,000 against the built-ins versus ~28,000 in self-play. Use the built-in batch to A/B a change (it is cheap and the seeds are fixed), but treat **`selfplay_bench.py` as the number that predicts the ladder** — it is the only local setup where a second trader is crowding the same order book. Its `end price` line is the tell: MELON finishes around $280 against a built-in and near the **$1 floor** in self-play, so any strategy that leans on premium-crop prices looks far better locally than it will score.

**Two seed sets, never reuse the dev set for confirmation.** All three harness scripts (`paired_compare.py`, `head_to_head.py`, `selfplay_bench.py`, plus `seeded_batch.py`) take `--seed-set {dev,holdout}`. The default is `dev` — the same 12 seeds (`range(12)`) that every prior iteration has used. **`HOLDOUT_SEEDS = range(100, 112)` is reserved for confirmation only**, the same way the held-out set in any ML pipeline is: once a candidate passes the dev set, run it once on holdout to check it generalises. **Do not run anything against `--seed-set holdout` while iterating.** Reusing the dev set for both dev and confirmation is the classic double-dip that manufactures a ~2,000-bank "win" inside the noise floor — the "green suite is not evidence" lesson already lives in this file, and seed-set discipline is its prevention on the harness side. Definition lives in `experiments/seeds.py`; the dev/holdout split is the single source of truth and any new harness must import it, not redefine the seeds.

**A submission's ladder episodes arrive as one burst, then almost stop — so the public score is a ~22-episode sample, not a converging measurement.** Measured across all eight submissions with `experiments/ladder_episodes.py`:

| submission | total episodes | in first 2h | span |
|---|---|---|---|
| `55547718` | 20 | 18 | 6.0h |
| `55551524` | 24 | 21 | 5.5h |
| `55559761` | 31 | 22 | 16.0h |
| `55567833` | 41 | 25 | 25.0h |
| `55578910` | 34 | 21 | 25.5h |
| `55591700` | 23 | 22 | 9.8h |

**Every submission gets 18-25 episodes within two hours, then trickles at roughly 0.4/hour while active and freezes the moment it is evicted.** Three consequences, all of which reverse the obvious intuition:

- **Waiting does not accumulate data.** A submission idle for four hours has gained nothing. Planning to "let it converge overnight" buys ~10 episodes, not a settled number.
- **Eviction is nearly free.** The latest-2-active rule sounds expensive, but the submission being displaced has already delivered ~90% of the episodes it will ever get. Holding a slot back to protect an old reading protects almost nothing.
- **Slots are the information channel and they do not roll over.** Five submissions a day is ~110 contested episodes a day if used, and zero if not.

**Read the per-episode record, never the public score alone.** The score is a rating seeded near 600, it converges slowly, and it folds opponent strength into one number. Two failures in one day: `55591700` read **637.1 at episode 11 and 587.6 at episode 22** (a 56-point swing, no change to the agent), and comparing its 587.6 against the previous submission's 612.5 looked like a 25-point regression when the two had simply played **22 and 33 episodes**. At an equal 22 the gap was 587.6 vs 601.7 — inside the per-episode swing of both series.

What the per-episode record gives instead, per submission: our bank, the opponent's bank, the **margin**, the win rate, and **the opponent's rating**. That last one is the control the raw score lacks:

| submission | n | win rate | margin (mean) | opponent rating |
|---|---|---|---|---|
| hire gate `55567833` | 40 | 45.0% | −14,111 | 587.9 |
| seed reserve `55578910` | 33 | 54.5% | −2,056 | 584.2 |
| species `55591700` | 22 | 45.5% | −8,298 | **612.3** |

Species banks **more** than seed reserve (52,517 vs 50,015 mean) but posts a **worse** margin and win rate, against opponents rated **28 points higher**. Whether the harder draw fully explains the gap is not resolvable at n=22 — **the honest verdict is unresolved**, and that is the point: at these sample sizes the ladder cannot separate two agents that differ by a few thousand bank. Reserve ladder slots for **structural** changes big enough to clear that floor, and settle threshold tuning with `paired_compare.py`, which controls seed variance properly.

**The ladder's error bar, measured directly rather than argued about.** On 2026-08-18 two submissions of *byte-identical* agent code ran simultaneously (`55591700` and `55606684`, both `main.py` at `5486566` - the second submitted by accident as a "baseline, no changes" test). Anything they differ by is pure instrument noise, and the answer is: **a lot, for a long time.**

Same code, same day, read three times over about an hour:

| read | `55591700` | `55606684` | apart |
|---|---|---|---|
| at n=6 | 635.1 | 595.1 | **40** |
| n=23 vs n=7 | 598.0 | 595.1 | 2.9 |
| n=23 vs n=8 | 598.0 | **512.4** | **86** |

**One episode moved `55606684` by 83 points.** It opened at 690.2, fell to 595.1 by episode 7 and to 512.4 by episode 8. The 2.9-point reading in the middle was a coincidence of timing, not convergence - and it is worth recording precisely because it was briefly written up here as evidence the score had settled. **Two identical agents can agree to within 3 points and disagree by 86 an episode later.**

Per-episode banks say the same thing less dramatically: mean 51,983 vs 52,886 (**903 apart**) against a per-episode sd of ~6,000, and margins **3,177 apart** (-7,670 vs -4,493).

What follows:

- **Below ~10 episodes the rating carries no information at all.** Every number quoted from a fresh submission this week - the 637.1 that looked like a win, the 587.6 that looked like a regression - sits inside this range.
- **Never compare two submissions at different episode counts.** The pair above is n=23 against n=8. **And equal episode count is not sufficient either - check the opponent field.** Matchmaking does not hand two submissions the same opposition: `55650592`'s first 52 episodes averaged an opponent rating of **1,684**, with 41 of them above 1700, while `55687852`'s first 52 averaged **1,211** with **none** above 1700. Their ratings at n=52 read **1,774 against 1,443** on near-identical banks (93,582 and 93,935) and a *worse* win rate for the higher-rated one (28/52 against 45/52). Beating a 1,200 opponent barely moves a rating; that gap is a difference in draw, not in agent. `experiments/ladder_episodes.py` now prints the mean opponent rating alongside each score and refuses to let the comparison pass silently when the two fields differ by more than 150 points.
- **A change worth less than ~1,000 bank is invisible here** regardless of patience, because identical code varies by 903. Settle anything smaller with `paired_compare.py`, which controls seed variance by construction.
- We do **not** yet have a converged estimate of the gap between two identical agents; `55606684` needs ~20 episodes before the pair can be compared honestly. Until then, treat every ladder delta under ~100 points as unmeasured.

**The ladder burst is also the only harness we own with real, selling opponents.** Be precise about the size of the gap, because it is easy to overstate and the overstatement changes what you build for. Across our own episodes:

| | our bank | opponent bank |
|---|---|---|
| mean | 52,517 | **60,815** — 16% ahead |
| max | 63,489 | **114,678** — 2x ahead |

**We are mid-field, not half-size.** The mean opponent banks about 16% more than us; it is the *top* of the field that is roughly double, and `docs/REPLAY_ANALYSIS.md`'s 95,288 / 91,904 are drawn from that top end rather than from a typical opponent. A reference opponent built to the 2x number would be modelling the best team in the competition, not the field we are actually matched against.

Kaggle CLI is authenticated (`~/.kaggle/credentials.json`) as `peterkibetspidey`, and the account is entered in the competition — verify with `kaggle competitions list --group entered` (expect `userHasEntered: True`). Re-auth with `kaggle auth login` if the session expires.

## Hard constraints (violating these silently breaks a submission, not just a test)

- Entrypoint must be `main.py` at the root (single file) or a `.tar.gz` with `main.py` at the root (multi-file). Max **100 MiB** total.
- **`actTimeout` is 1 second per turn**, with a 60-second overage bank for the episode (`obs["remainingOverageTime"]` tells you what's left). Set in `kaggriculture.json` and verified to resolve to `1` via `env.configuration`. The forum treats this as an open question — no staff answer — but per "engine is the source of truth" the spec is the better evidence. Budget for 1s: no per-turn deep search. Absent from `docs/kaggriculture_context.md`.
- **No network I/O inside the agent function** — episodes run with no ingress/egress. Anything the agent needs must be `obs`, bundled data, or a bundled model checkpoint.
- Per-episode compute budget: 8 GiB HDD, 6.5 GiB RAM, 1.6 vCPUs — factor this in before bundling large models.
- One action per farmer/hand per turn; **max 10 market orders per turn** (extras are silently dropped, not rejected — no error to catch).
- Only `WHEAT` and `FERTILIZER` can be bought back via `BUY_PRODUCT`; every other product is sell-only.
- 5 submissions/day; only your latest 2 stay active for matchmaking and final scoring.
- Scoring runs ~2 weeks past the Sept 30 final-submission deadline, then **one** Bradley-Terry tournament sets the final ranking — deliberately, to damp hot streaks. Late-season leaderboard position is noisy; don't over-tune on it.

## Agent I/O contract

**The entrypoint is the *last callable in the module namespace*, not a function named `agent`.** `kaggle_environments/agent.py:64` does `[v for v in env.values() if callable(v)][-1]`. A helper function — or a class, since classes are callable — defined below `agent()` silently becomes your submission. Keep `agent` last in `main.py`, and put helpers in an imported module or above it.

This fails **silently**, which makes it nasty to catch. Verified locally: with a helper defined after `agent()`, the episode still reports `status=DONE` with no error — the wrong callable returns garbage, every action is discarded as an invalid no-op, and the agent finishes on exactly `startingMoney`. **A local run that ends at exactly $3000 means your agent never actually acted.** Treat that number as a failure signal, not a bad strategy.

`main.py` satisfies the rule with a trailing `agent = nikaangukia_meroni` binding on the final line. **Keep that line last** — anything callable added below it silently hijacks the submission.

Both `def agent(obs)` and `def agent(obs, config)` work: the framework builds `[observation, configuration]` and truncates it to the function's `co_argcount` (`agent.py:151-153`). Taking `config` gets you `episodeSteps`, `boardSize`, `maxMarketOrdersPerTurn`, etc. rather than hardcoding defaults.

Return:

```python
{"farmer": [action, ...], "hands": [[action, ...], ...], "market": [[order, ...], ...]}
```

`obs` keys (verified against a live episode): `player`, `day`, `hour`, `step`, `farms`, `market`, `town`, `private`, `remainingOverageTime`. Note `step` and `remainingOverageTime` are supplied by the framework and are missing from the §3.12 schema in the docs.

Key fields: `obs["farms"][obs["player"]]` (own public farm state — tiles, money, farmer/hand positions), `obs["private"]` (own shed/seeds/inventories — opponent's shed is never visible), `obs["market"]` (inventory + prices per resource), `obs["town"]["unlocked_shops"]` (demand-side signal).

## Game mechanics an agent must get right

- **Watering/feeding**: miss 2 consecutive days → plant becomes a weed (must `DIG` to reclaim) or animal escapes (unrecoverable). A freshly planted seed already has `consecutive_unwatered = 1`, so **an unwatered new planting dies that same night** — no grace period. Animals do get a free first unfed day.
- **Fertilizer**: doubles the per-day yield bonus for 3 days, but only on days the plant is *also* watered — it's a multiplier on the watering baseline, not a substitute.
- **Care** (`CARE`, once/day): banks +1 only on days the animal was both fed and cared for; the whole bank pays out on the animal's next production day if fed that day, and resets to 0 either way after that day.
- **Selling mechanics**: sell price is quoted pre-sell, buy price post-buy; both players' orders process one unit at a time concurrently, so large simultaneous orders move price against each other mid-order. Premium goods (base price > $100: strawberry, melon, milk, wool) crash toward the $1 floor fast on oversupply — spread large sells rather than dumping them in one `SELL` order.
- **Hiring**: cost is `farmHandCostMult × fib(n)` (default mult 1) where `n` resets to 0 every day — cheap for the first hire of the day, expensive for the third+.

## Silent-failure gotchas

Every one of these is a no-op or a wrong answer with **no error raised**:

- **`tiles[y][x]` is row-major, but `farmer` and `hands` are `[x, y]`.** The axis flip between them is the classic hour-long debug.
- **The shed is not a tile** and never appears in `tiles`. "Shed-adjacent" is one of the four center tiles — `(4,4)`, `(5,4)`, `(4,5)`, `(5,5)` at the default board size. Shed actions work from there even if the tile is locked.
- **Only `PICKUP`/`DROP` require shed adjacency.** Market orders — `BUY_SEED`, `BUY_PRODUCT`, `BUY_ANIMAL`, `SELL`, `HIRE`, `BUY_LAND` — execute from anywhere on the board (staff-confirmed). Don't waste farmer turns walking to the shed to trade.
- **Locked tiles are passable** — units can walk across unbought quadrants — but every tile action no-ops there.
- **Farm hands vanish at end of day** and must be re-hired every single day.
- **Planting more seeds of a kind than you hold plants none of them**, not as many as possible.
- A tile is `None` (empty), `"LOCKED"`, a plant dict, a weed dict, or a coop/pasture dict — check `kind` before assuming shape.
- Shed capacity is 100 non-seed items; overflow at any point is discarded with no buffer.

## Repo conventions

- `docs/kaggriculture_context.md` is read-only research material; update it only if the competition rules themselves change.
- Don't commit replay JSONs (~4.9 MB each).
