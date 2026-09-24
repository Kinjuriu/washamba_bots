# Round 3 report: B, C, D overnight results — 24 September 2026

**Headline: no variant passed the gate, so E (combine) was not built.** But the diagnosis of *why* C fails is the most useful measurement of the night: a v15stack mirror is a pair of synchronized, mutually destructive premium dumps, and any deviation makes **both** players richer while making the deviator **relatively** poorer. Ratings count only the relative game.

All artifacts are under `experiments_r3/` (variants `B/ C1/ C2/ D4/ D8/`, results `mirror_*.jsonl`, `panel_*.jsonl`, diagnostics `diag_*`, logs). Engine: kaggle-environments 1.32.7; 7 workers; every game across 490 result rows ended `DONE`, 0 harness errors, and a full 720-turn game runs at ~2.5 ms per agent-turn (measured, `diag_C1_101.txt`) — gate 4 passes everywhere it was reached.

## One line per variant

| Variant | Change | Identity (off) | Mirror vs W0 (60 games, seeds 2001–2030) | Faithful top-six panel (paired vs W0, faithful under both) | Verdict |
|---|---|---|---|---|---|
| B | duplicate CARE → best same-tile action | PASS | 17-43-0, points 0.283, **mean −19** | n=34: delta **+10** mean / −8 median | FAIL (neutral micro-change loses the mirror tiebreak) |
| C1 | +2–3 geese from day 8, own coops, dedicated extra hand | PASS | 1-59-0, points 0.017, mean **−13,320** | n=25: delta **−6,587** mean; faithful drops to 25/38 | FAIL decisively |
| C2 | same, from day 4 | PASS | 1-59-0, mean −13,448 | identical to C1 (see below) | FAIL decisively |
| D4 | day-10+ wheat↔carrot substitution by marginal profit, ≤4 tiles | PASS | 16-44-0, points 0.267, mean −196 | n=38: delta −125 mean / −60 median | FAIL |
| D8 | same, ≤8 tiles | PASS | 13-47-0, points 0.217, mean −388 | n=38: delta −268 mean / −74 median | FAIL |

(W0 reference on the same faithful panel: 6 wins of 38, median −21,744 — reproduced exactly by our runner before comparing.)

## Measured evidence for B

- **No-op rate (5 real ladder games, W0 replays):** 2,020 CARE issued, 1,953 successful, **67 duplicates (3.3%)** ≈ 13 wasted actions per game. So the Round-2 audit's "1.04 CARE/animal-day" is ~97% real care.
- **After the fix (1 engine game, seed 101):** CARE issued drops 404→392 with successes unchanged at 391 (dedup works). But the 12 freed actions, redirected to COLLECT_FERTILIZER/HARVEST on the same tile, landed only **+1 additional successful action** — the duplicate CAREs sit on animals another worker already services that turn, so there is almost nothing to reclaim. Bank change in that game: −6/+9 coins.
- **Inference:** B's ceiling was ~13 actions/game and its realized value is ~1 action (~50 coins). Yet it still went 17-43 in mirrors at mean −19 — see the desync finding below.

## Measured evidence for C

- **W0 baseline (5 replays):** 0 geese until day 8, mean 2.8 from day 11.
- Three build revisions were needed; each earlier bug is itself evidence:
  - rev1 placed a goose **into a coop the tape had built for itself**, derailing the tape's herd bookkeeping (smoke seed 101: 88,727 vs 107,723 against a 96,073/96,073 baseline).
  - rev2 (own coops only) had geese **starve and escape 3–4 times per game** (feed wheat gated behind trough cash), with repeated re-purchases of the same coop's goose.
  - rev3 (buy only with ≥$1,500 cash, ≥2 feed wheat in shed, one attempt/day) is clean: **2 coops built, 2 geese bought, 2 placed, 0 escapes**, and the geese produce — **+29 eggs sold at ~52** vs baseline (~+1.5k gross), with +181 wheat bought as feed (diag, seed 101). The cash gates delayed C2 to the same start day as C1, making the two byte-identical in behavior.
- **And it still loses 1-59 with mean −13.3k.** The product-level diagnosis (`diag_C1_101.txt` vs `diag_w0_101.txt`, seed 101) shows why, and it is not the geese:

| Product | W0 mirror (each side) | C1 game: us | C1 game: opponent |
|---|---|---|---|
| MILK | 241u @ **98.2** | 236u @ **211.6** | 245u @ **212.7** |
| STRAWBERRY | 247u @ 154.4 | 180u @ 202.8 | 247u @ 201.4 |
| WOOL | 99u @ 55.4 | 84u @ 65.0 | 99u @ 55.4 |

  In the pure mirror both tapes dump the same product on the same turns and crush the price to 98. C's small cash/tile perturbation shifts our sell schedule off the synchronized dump, and **prices roughly double for both sides** (milk 98→212). The opponent keeps full volume (+36.9k total bank); our disturbed tape loses volume (−67 strawberry, −15 wool) and gains "only" +17.7k. Everyone gets richer; we lose the game. Faithfulness also collapses (25/38): our changed market behavior shifts what the replayed top-six tape experiences.

## Measured evidence for D

- The profit rule (engine price at drain-projected stock, yield/seed/days) fired only late game (turns ~591–616), always CARROT→WHEAT at value ~23 vs ~33, making 4 (D4) and 8 (D8) substitutions per game. Both directions of the gate never favored carrot — consistent with wheat sitting above base 96% of days.
- Effect is small and negative everywhere: mirrors −196/−388 mean, panel −125/−268 paired. **Inference:** within the safe substitution set (wheat↔carrot share the same maturity window, so the tape's recorded harvests still land), there is no money to move; the products with real gaps (tomato, strawberry timing) cannot be substituted under a tape whose harvest schedule assumes the original crop.

## The finding that matters

**Measured:** a 12-action change (B) loses the mirror 17-43 at −19 mean; a change that makes us +17.7k *absolutely* richer (C) loses 1-59. Combined with history (W2 selling planner 1-19, experiment A 0-10-30, six of seven past overlays failed), the pattern is now precise: **the v15stack mirror is a knife-edge synchronization game. Any deviation desynchronizes the mutual dump, raises both banks, and hands the relative win to the unperturbed side — unless the deviation itself front-runs the race.** W1 (sell one reservation-step earlier) is the only overlay class that wins mirrors because it deviates in the direction that wins the desync, not just causes it.

## What to do next

1. **Stop grafting board-state economics onto the tape.** B, C, D close the question: production overlays cannot pass the mirror gate regardless of their absolute economics. (C's +1.5k of egg income is real; it is simply irrelevant next to the ±19k desync swing it triggers.)
2. **The mirror-winning class is sell-race timing.** Next cheap tests, same harness, one constant each: `V9_RACE_DEFAULT` beyond 44 (46, 48 — W1 already validated 44), `V9_RACE_MARGIN`, and racing one more item class — these deviate *inside* the race framework the tape already wins with.
3. **C's diagnosis is a gift to Agent 2 (the reactive mid-game).** Desync premium is worth ~2× on milk/strawberry in mirror-heavy bands. A reactive agent that (a) natively owns its geese/labour instead of renting a marginal hand, and (b) deliberately sells premium *off* the tape-family dump turns while keeping volume, collects both sides of what C measured. That remains the only path that also moves the top-six panel, where tonight's best change was +10 coins.

**Not run:** E (nothing passed). **Not retested:** A, selling-only overlays, herd-swap disable (per brief).
