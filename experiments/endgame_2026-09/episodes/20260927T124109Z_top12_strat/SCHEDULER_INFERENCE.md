# How the top 12 schedule labour, and where W3 differs

27 September 2026 (evening). Data: exact replays, `episodes/20260927T124109Z_top12_strat/` (347 games, 30/team stratified by seat/opponent-rating-band/time window) and a 30-game random sample of our W3 (`w3_herdsafe2700.py`) seats from `episodes/20260924T161358Z_washamba_0924b/`. Positions come straight from the observation (`farms[seat]['farmer'|'hands']`); tile/animal/plant state (watered_today, fed_today, yield_units, consecutive_unfed, etc.) is likewise read directly, not re-derived. Everything below is MEASURED unless marked INFERENCE; n = games unless stated. Method validated by checking every non-move action in 2 games against the engine's legality rules (episode 112879208 seat 0, episode 112880347 seat 1, both Boey): 0/2,000 illegal in each — the same check on a weak opponent in the first game caught it repeatedly issuing CARE on a permanently locked tile (483/2,000), confirming the checker works and it's a real agent defect, not a tracking bug.

Teams are grouped by opening family per `review_fable/POLICY_INFERENCE.md`: **DSM** = DECEM, M & M & P & Q, Unknown Mother-Goose, Azat Akhtyamov (4 teams, n=120 games); **Boey** = Boey alone (n=30); **other** = the 7 teams new to this top-12 snapshot with no prior opening classification — Majkel1337, Vadim Vasilenko, Fourth Quadrant, Just A game on your lips, Anton Tikhonov, KawattaTaido, 有辣条有权 (n=210). Table rows are the pooled-game median (IQR available in `analysis/scheduler/family_summaries.json`).

**Key engine fact that reframes "capacity":** hands are wiped to zero every single day (`_end_of_day` resets `farm["hands"]=[]`) and the Fibonacci hire-cost ladder resets with them. Holding an 11-hand crew is not a one-time purchase — it's paid for fresh every morning. WANTAM's "capacity planner (dawn)" framing already assumes this; the numbers below confirm it's the right model.

## 1. Capacity

| | crew d0-7 | crew d8-14 | crew d15-22 | crew d23-29 | hires/day d8-14 | land Q1 / Q2 / Q3 (day) |
|---|---|---|---|---|---|---|
| DSM | 6.48 | 10.93 | 11.68 | 11.19 | 10.4 | 6 / 8 / 10 |
| Boey | 6.24 | 10.87 | 11.57 | 11.00 | 10.4 | 6 / 8 / 14.5 |
| other | 6.61 | 11.38 | 12.09 | 11.39 | 11.0 | 6 / 9 / 10 |
| **W3** | **5.64** | **9.71** | 11.32 | 11.50 | **9.1** | 6 / **11** / **18** |

Land quadrant 1 is bought day 6 by every team, top-12 and W3 alike (zero IQR spread) — not a discriminator. Quadrants 2 and 3 are where W3 lags: 2-3 days late on Q2, 4-8 days late on Q3, each time sitting on more idle cash than the top 12 (consistent with `POLICY_INFERENCE.md`'s $18k-idle finding, now confirmed on a fresh, different top-12 roster). Crew also builds faster for the top 12 in the first two weeks: by days 8-14 they're at ~10.9-11.4 hands, W3 at 9.7 — about 1.2-1.7 hands behind at the same point, even though day-29 crew size ends up similar.

## 2. Zones

| | Jaccard (day-to-day tile overlap) | zone size (tiles/hand/day) | specialisation (share of a hand's actions in its dominant category) |
|---|---|---|---|
| DSM | 0.16 | 6.14 | 0.66 |
| Boey | **0.29** | 6.14 | 0.72 |
| other | 0.16 | 6.23 | 0.67 |
| W3 | 0.11 | 6.05 | 0.73 |

Territorial stability is low everywhere (0.11-0.29) and is *not* a clean top-12-vs-W3 split: only Boey is notably zone-stable; DSM and "other" are barely more stable than W3. WANTAM's Layer 3 assumption of "each worker owns a contiguous zone that changes only when the farm changes" is stricter than what most winning agents actually do — they re-cut tile assignments daily and it doesn't cost them, because task-type specialisation (feed vs water) stays high (0.66-0.73) even when the specific tiles change.

## 3. Routes and batching

| | actions/visit (median) | moves/useful-action, d15-22 | idle share, d8-14 | idle share, d15-29 |
|---|---|---|---|---|
| DSM | 2 | 0.70 | 0.02 | 0.01-0.02 |
| Boey | 2 | 0.71 | 0.03 | 0.01-0.02 |
| other | 2 | 0.66 | 0.01 | 0.00-0.01 |
| **W3** | **1** | **0.81** | **0.07** | **0.03-0.05** |

Two clean gaps. First, walking efficiency: top-12 groups keep *improving* as the game matures, reaching 0.60-0.71 moves per useful action by days 15-22; W3 plateaus around 0.81-0.82 for the whole back half of the game and never gets there. Second, idle turns: from day 8 on, top-12 hands are almost never idle (1-3% of turns); W3 sits at 3-7%, two to five times higher, for the rest of the game. Both point at the same thing — W3's per-turn routing doesn't get more efficient as the farm grows, the top 12's does.

## 4. Deadlines

| | FEED hour (med) | CARE hour (med) | WATER hour (med) | escapes/game | weeds/game | frac. animal-days starting 1 day already unfed |
|---|---|---|---|---|---|---|
| DSM | 8 | 9 | 15 | 8 | 8 | 0.18 |
| Boey | 11 | 11 | 13 | 6 | 10.5 | 0.13 |
| other | 8 | 9 | 15 | 8 | 20 | 0.20 |
| W3 | 9 | 10 | 16 | **0** | 19 | 0.16 |

Feed and care cluster hours 8-11; watering happens 4-7 hours later (13-16) — a near-universal task-ordering fixed rule (see §8). The escape number is the surprise: the top 12 lose 6-8 animals a game to starvation, W3 loses none, yet the *risk exposure* is similar everywhere (13-20% of animal-days already have one missed feed). Since the engine has no sell/release action for an animal, starving it for two days is the *only* way to shrink or recompose a herd — read as INFERENCE, the top 12 are using escapes as a deliberate lever, and W3 currently never does.

## 5. Replanting

| | HARVEST→PLANT lag (steps, med) | same-hand-same-visit share | wheat plantings/day, d15-22 | wheat plantings/day, d23-29 |
|---|---|---|---|---|
| DSM | 1 | 0.88 | 7.6-8.3 | 5.4-6.4 |
| Boey | 1 | 0.88 | 7.8 | 4.9 |
| other | 1 | 0.87 | 6.4-10.5 | 4.6-8.1 |
| W3 | 1 | 0.85 | 7.5 | **3.1** |

Near-universal 1-step replant lag and ~85-88% same-hand-same-visit — this is already what WANTAM's Layer 2 replant rule targets, and the measurement confirms it's the right target, not an aspiration. The one real gap: in the final week, the top 12 keep replanting wheat close to their mid-game rate (4.6-8.1/day); W3 drops to 3.1/day, well below its own days-15-22 level of 7.5.

## 6. Carrying

Pickup-repeat share (fraction of hand-days with more than one WHEAT/FERTILIZER pickup) is low and similar everywhere: DSM 0.09, Boey 0.13, other 0.10, W3 0.11. 87-91% of hand-days involve exactly one fetch. This matches WANTAM's "pick up once at dawn" design directly — no gap here, W3 already does this.

## 7. Order within a day

Every group's single most common per-hand daily pattern is `WATER, HARVEST, PLANT, WATER[, HARVEST, PLANT, WATER...]` — harvest, replant, and water the new seedling in the same visit, repeated tile after tile. The animal round differs by team: DSM/other hands often interleave `CARE, FEED` with crop tasks in the same day; W3's most common long pattern is a pure herding round (`PICKUP, FEED, CARE, COLLECT_FERTILIZER` repeated with no crop actions mixed in), consistent with W3's slightly higher specialisation score above.

## 8. Fixed rules found (beyond §1-7)

- Land quadrant 1 always day 6, cash 1,900-2,700ish, never earlier or later — a clock, not a cash trigger (n=390 games, IQR=0 every group).
- Feed/care before hour 11; watering after hour 13, for every team measured, top-12 and W3 alike.
- Hires cluster at hour 0 of the day everywhere (75-85% of all hires), but a substantial minority (15-25%) happen intraday.
- Not probed this pass, flagged for follow-up: TOMATO/STRAWBERRY/MELON never clear their tile on harvest (`ongoing=True` in the engine), so "replanting" as measured here only applies to WHEAT/CARROT; the ongoing crops' watering/fertilising cadence deserves its own pass.

## The 10 clearest gaps (top 12 vs W3), with evidence

1. **Land Q2/Q3 come 2-8 days later for W3** (day 11/18 vs 8-9/10-14.5), sitting on more idle cash each time (§1).
2. **Crew build-up is slower for W3 in weeks 2** (9.7 hands at d8-14 vs 10.9-11.4 for the top 12) despite similar day-29 totals (§1).
3. **W3's route efficiency plateaus; the top 12's keeps improving** — 0.60-0.71 moves/useful-action by d15-22 for the top 12 vs W3 flat at ~0.81 the whole back half (§3).
4. **W3 is idle 2-5x more often from day 8 onward** (3-7% of turns vs 1-3% for every top-12 group) (§3).
5. **Escapes: top 12 average 6-8/game, W3 averages 0**, despite similar feeding risk — inference: the top 12 use starvation as a herd-recomposition tool the engine forces on everyone, and W3 doesn't use it (§4).
6. **Wheat replanting drops off harder for W3 in the final week** (3.1/day vs 4.6-8.1/day for the top 12) (§5).
7. Zone stability is *slightly* higher for the top 12 on average (0.16 vs 0.11) but the real outlier is Boey (0.29) — a soft, not clean, gap (§2).
8. Feed/care/water hour-of-day ordering, replant lag/same-hand share, and pickup-once discipline are **already matched by W3** — these are universal engine-shaped rules, not competitive edges, and confirm three of WANTAM's design assumptions are correctly targeted (§4, §5, §6).
9. Specialisation by task type (0.73) and zone size (6.05) are **already fine for W3** — the gap is in routing/idle efficiency, not in what each hand specialises in (§2, §3).
10. Land Q1 timing, hire-hour clustering, and the WATER-after-HARVEST-after-PLANT batching pattern are universal fixed rules every team (including W3) already follows — safe defaults for WANTAM to hard-code rather than search for (§7, §8).

## Parameters for WANTAM

- **Crew target by phase** (hands, not counting farmer): ~6-7 by day 7, ~11 by day 14, ~12 by day 22, ~11 by day 29. W3's own current levels (5.6/9.7/11.3/11.5) show where to close the gap first: days 8-14.
- **Hire timing:** plan for ~75-85% of the day's hires at hour 0; leave capacity for a further ~15-25% intraday top-up.
- **Land clock:** buy Q1 day 6 unconditionally (cash ~1,900-2,700 will be there); target Q2 by day 8-9 and Q3 by day 10 — both several days earlier than W3's current 11/18.
- **Moves-per-useful-action gate:** WANTAM's Gate 1 currently targets *matching W3* (~0.91 in days 14-29 on one seed). That's an easy bar — the top 12 reach 0.60-0.71 by days 15-22. Raise the gate.
- **Idle-turn budget:** top 12 run 1-3% idle from day 8 on; treat >5% idle after day 8 as a scheduler defect, not slack.
- **Replant rule:** same-hand, same-visit, ≤1-2 step lag is already right (85-88% match); the fix needed is *not letting the wheat replant rate fall off in the last week* — hold ≥4.6/day through day 29, not W3's current 3.1.
- **Escape policy (new):** since there is no direct "release animal" action, treat a deliberate 2-day starvation as the shrink/recompose primitive for herd management, budgeted at ~6-8 uses/game, rather than treating every escape as a scheduling failure (WANTAM's current zero-escapes gate may be stricter than the top 12 itself plays to).
- **Task-hour priors:** schedule FEED/CARE before hour 11, WATER after hour 13, as a soft ordering constant, not something to re-derive per turn.
- **Carrying:** one WHEAT/FERTILIZER fetch per hand per day covers 87-91% of cases; keep the "once at dawn" carrying rule as designed.
