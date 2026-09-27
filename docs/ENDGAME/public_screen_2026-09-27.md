# Public-agent screen, 2026-09-27

13 candidates pulled -> 3 exact-duplicate groups collapse to 9 unique code bodies ->
1 dropped invalid (broken as published) -> 8 screened vs `agents/w3_herdsafe2700.py`
(seeds 900-915, both seats, 32 games each) -> top 2 also screened vs
`agents/w3_frontrun.py` (seeds 900-907, both seats, 16 games each).

**Headline: `demand-preserving-turn-sale-timing` beats W3 on both harnesses**
(30/32 vs W3, +616 mean margin; 14/16 vs w3_frontrun, +683 mean margin) but has a
timing red flag (see below) that must be resolved before anything is adapted from it.

## Dedup groups (byte- or functionally-identical, screened once)

| group | members | note |
|---|---|---|
| A | `kaggriculture-master-engine-v3` = `kaggriculture-multi-route-farming-agent` = `the-shepherds-ledger-herd-safe-sovereign` | identical after stripping comments (CRLF/header-only diffs); screened as `kaggriculture-master-engine-v3` |
| B | `the-2965-master-hybrid-engine` = `kaggriculture-top-2-master-engine-v4` | identical after stripping comments (header/attribution-only diffs); screened as `the-2965-master-hybrid-engine` |
| C | `kaggriculture-2026-v1` = `kaggriculture-version-31-26-09-bronze-going-up` | byte-identical (same SHA-256); screened as `kaggriculture-2026-v1` |

## Results table

| candidate | claimed LB | W3-fork? | valid? | max turn ms (720-step) | wins vs W3 (of 32) | mean cand bank | mean W3 bank | mean margin |
|---|---|---|---|---|---|---|---|---|
| **demand-preserving-turn-sale-timing** | none stated; author's own note: "leaderboard improvement is not established" | **Effectively W3 itself, plus an appended layer.** Confirmed line-for-line: comment-stripped lines 1-6356 match W3 almost exactly (2710 additions / 3 deletions vs W3's 6356 total — the 3 deletions are the same `_v92_predict` guard noted for four-turn-forecast below); from line 6356 onward it appends ~2708 new lines defining `_S720_PARENT = herdsafe_forecast_agent` (literally W3's own base agent function) wrapped by a `step720_final_sell_reorder_agent`-style chain that reorders contiguous SELL blocks from step >= 216 (day 9) onward — matches its own header: "Reproduce the credited tetsutani controller... final layer activates from turn 216 and reorders only contiguous sale blocks." Entrypoint resolves to `step1009_step1008_fortyfirst_final_fixedsell_closure_agent` (a wrapper chain, not a bug — verified). | yes | **1161.6ms @step600** (seed0, local 8-core box vs `pass`); recurs on other seeds up to 1335ms @step600 and 1072ms @step457 (2 of 4 seeds spot-checked show a >1s spike). Kaggle's episode runtime is 1.6 vCPU vs this box's 8 cores, so real spikes there are plausibly 2-3x longer; still only 1-2 per game against the 60s/episode overage bank, so not obviously fatal, but unverified in a contested (non-`pass`) game since W3's own 130-250ms/turn dominates total wall time there and the two can't be separated locally. | **30/32 (94%)** | 103,750 | 103,133 | **+616** |
| kaggriculture-master-engine-v3 (= group A) | "Proven 95.1% Win Rate, +17.5M Net Margin" (self-reported synthetic sim, not a live LB score) | Distant cousin: 1835/6356 lines differ (~29% match); same V39/yhay81/Gluzdov ancestor family as W3 but diverged early | yes | 244.7ms @step712 | 18/32 (56%) | 103,896 | 103,601 | +296 (also only 6/16, +76 vs w3_frontrun — inconsistent, not a robust win) |
| four-turn-forecast-notebook-version-2 | none stated (explicitly: "not established") | **Near-exact W3 fork**: only 4 lines differ out of 6354 comment-stripped lines (99.94% identical) — both explicitly descend from "Dmitrii Gluzdov's Herd-Safe Sale Window v2", same base as our own W3. The only functional diff is one `_v92_predict` candidate-filter guard W3 has and this doesn't (see diff below). | yes | 170.9ms @step150 | 7/32 (22%) | 104,146 | 104,358 | -212 (near-mirror-match noise) |
| the-2965-master-hybrid-engine (= group B) | "95.0% Win Rate ... +$39,882 margin", "20W/2L/18T, +$38,557 net margin" (self-reported synthetic sim) | Distant cousin: 919/6356 lines differ (~86% match); shares V39/yhay81/Gluzdov/prvsiyan lineage with W3 | yes | 269.2ms @step150 | 13/32 (41%) | 103,190 | 105,037 | -1847 |
| god-s-mode-hacked-stores (multi-file: main.py + base_agent.py + shop_overlay.py + shop_predictor.py) | none found | Distant cousin: base_agent.py 1331/6356 lines differ (~74% match) | yes | 201.1ms @step351 | 4/32 (13%) | 103,306 | 104,699 | -1393 (verified reproducible with one-fresh-process-per-game rerun: identical 4/32, -1393 — no cross-game state leakage from its sibling-module imports) |
| farmer-john-and-the-idle-seller | none stated | Distant cousin: 1272/6356 lines differ (~76% match) | yes | 77.5ms @step150 | 2/32 (6%) | 103,079 | 104,621 | -1542 |
| kaggriculture-harvest-ledger | none stated (holdout paired-margin stats quoted, no LB number) | Close-ish cousin: 511/5917 lines differ (~91% match); explicitly "keeps the complete original V54... adds one final queue mechanism" | yes | 155.7ms @step150 | 0/32 (0%) | 103,316 | 104,585 | -1268 |
| kaggriculture-2026-v1 (= group C) | "LB peak: ~2700" (quoting the ancestor Herd-Safe notebook's historical name, not a fresh score) | **Not a W3 fork** — much shorter file (2259 vs 6356 comment-stripped lines), different/simpler architecture entirely | yes | 58.4ms @step712 | 0/32 (0%) | 100,992 | 107,202 | **-6210 (worst)** |
| a-song-of-ice-and-fire-fixed-flexible | claims "93.8% Win Rate Public State Router" ancestry (Thomas Tschinkel) | Not a W3 fork (different lineage: Tschinkel's state router) | **NO — dropped** | n/a | n/a | n/a | n/a | n/a |

All candidates: Apache-2.0 (every one, including our own W3, traces to the same shared
public lineage — yhay81, Ahmed Berat Ozer, Dmitrii Gluzdov, thomastschinkel, prvsiyan,
tetsutani, aurax7, destbreso). No candidate reads hidden/opponent state, makes network
calls, or does process/frame introspection (checked via import list + targeted grep on
every extracted file and every god's-mode sibling module).

## Top 3, one line each

1. **demand-preserving-turn-sale-timing** — genuinely beats both W3 (30/32, +616) and
   w3_frontrun (14/16, +683), the only candidate that clears this repo's win-count bar
   on two independent harnesses that can disagree — but flagged for a real >1s
   per-turn timing spike (up to 1335ms, recurring near step ~600 on roughly half the
   seeds spot-checked); worth deeper study for the sale-timing idea itself, not a
   drop-in adoption until the timing issue is understood.
   Local file: `C:\Users\HP\Spidey-Hub\washamba_bots\agents\.pub_0927\demand-preserving-turn-sale-timing.py`
   **Caveat that changes the next step:** because this candidate literally contains
   W3's own `herdsafe_forecast_agent` as its base, and both opponents it was screened
   against (W3, w3_frontrun) are also W3-family, this result establishes "a
   sale-timing reorder layer beats a W3-shaped opponent whose sell schedule it
   effectively knows," not "beats the field." Per `experiments/splice/gate.py`,
   roughly half the real ladder is 2945-Farm/v15stack forks, a different family
   entirely (e.g. `agents/washamba_base_v1.py`) — that matchup is untested here and
   is the right next screen before drawing conclusions about adopting the idea.
2. **kaggriculture-master-engine-v3** — a coin-flip against W3 (18/32) and against
   w3_frontrun (6/16, margin ~0) — not a proven threat, but the only other candidate
   that isn't a clear loss.
   Local file: `C:\Users\HP\Spidey-Hub\washamba_bots\agents\.pub_0927\kaggriculture-master-engine-v3.py`
3. **four-turn-forecast-notebook-version-2** — not a win (7/32, -212 margin, likely
   mirror-match noise), but included because it is functionally near-identical to our
   own W3 (only 4 comment-stripped lines differ out of 6354, entrypoint resolves to
   `herdsafe_forecast_agent` — W3's own base function name) — useful as a sanity
   check on how close public play has converged to our own base, and the one code
   difference is worth a look:
   ```
   -    if not scored or scored[0][0] < 0:
   -        return [ev for _, ev in scored[:_V92_P_TOP]]
   -    return [ev for score, ev in scored[:3] if score >= scored[0][0] - 1.0]
   +    return [ev for _, ev in scored[:_V92_P_TOP]]
   ```
   Local file: `C:\Users\HP\Spidey-Hub\washamba_bots\agents\.pub_0927\four-turn-forecast-notebook-version-2.py`

## Flags / anything suspicious

- **a-song-of-ice-and-fire-fixed-flexible is a genuinely broken public submission.**
  As extracted (sha256-verified against the notebook's own embedded hash,
  `12ad317e...c2693`), the module's last NEW dict key inserted into the exec
  namespace is `install_water_repair_local_patch` (a def), not `agent` — because
  `agent` is reassigned (`agent = install_water_repair_local_patch(agent)`) to an
  *existing* key, which does not move it in Python dict insertion order. Kaggle's
  `get_last_callable` picks `env.values()[-1]`, which resolves to
  `install_water_repair_local_patch` itself (confirmed directly). Result: exactly
  `[3000.0, 3000.0]` in self-play — the agent never acts if submitted as-is, despite
  the notebook's own "Automated Integrity & Dual Entrypoint Verification" cell
  claiming to check this. Dropped as invalid per the task's validation gate. For
  curiosity, a local one-line fix (`kaggle_entry_point = agent` appended) makes it
  resolve correctly and finish with a normal ~103k bank — but even fixed it loses to
  W3 0/32 (-1559 mean), so it is not a masked threat either way.
- **demand-preserving-turn-sale-timing's timing spike** (see table) is the one real
  risk flag among the valid/winning candidates. Kaggle's `actTimeout` is 1s/turn with
  a 60s overage bank per episode, so one or two ~150-350ms overages per game is
  survivable, but this needs to be understood (what triggers it, whether it can
  compound) before treating the 30/32 result as fully trustworthy for adoption
  purposes.
- **god-s-mode-hacked-stores's `shop_predictor.py`** does something notable but not
  disqualifying: it reconstructs the engine's weed-draw RNG stream from consecutive
  *public* observations (hour-23/hour-0 farm-tile deltas) to narrow down the PRNG
  seed and predict future shop unlocks — a legitimate seed-inference side-channel
  attack using only public data, not a hidden-state read. Verified it imports no
  `kaggle_environments`/`kaggriculture` internals and touches only the `observation`
  argument.
- **Multi-file candidate**: god-s-mode-hacked-stores ships as 4 files
  (`main.py`, `base_agent.py`, `shop_overlay.py`, `shop_predictor.py`) that must stay
  together — `main.py` does `from base_agent import agent`. Kaggle's own loader adds
  the file's directory to `sys.path` before exec, so this works fine as a
  `.tar.gz`-style submission; local dir is
  `agents\.pub_0927\god-s-mode-hacked-stores_pkg\`. Re-ran its 32-game W3 screen with
  one fresh OS process per game (`max_tasks_per_child=1`) to rule out cross-game
  state leakage via its real Python imports (cached in `sys.modules` per worker
  process) — got the identical 4/32, -1393 result, so the original number is trustworthy.
- No candidate exceeded a hard 1s cap except the one noted above; no non-DONE episode
  statuses across any of the 256 W3-screen games or 64 frontrun/recheck/fixed games.
- Seat symmetry note: 14 of 16 seeds gave byte-identical cand/opp banks whether the
  candidate played seat 0 or seat 1 (only 2 of 16 seeds diverged by seat) — consistent
  with this repo's documented seat-asymmetry being small/seed-dependent, not a
  harness bug. Effective independent samples per candidate are closer to ~18 than 32
  for the W3 screen, and the same pattern holds for the w3_frontrun screen (14/16
  wins ~= 7/8 independent seeds), though the win counts above are large enough
  (0/32, 30/32, etc.) that this doesn't change any conclusion.
- Entrypoint sanity check on all 8 valid candidates (`get_last_callable(...).__name__`):
  all resolve to a real agent-shaped function (`step1009_..._agent`,
  `herdsafe_forecast_agent`, `_final_sell_block_reorder_entrypoint` x2, `ig_agent`,
  `optimized_agent`, `agent` x2) — none hit the a-song-of-ice-and-fire class of bug.
- `experiments/field_research/out_0927/` is a new directory and is **not** currently
  covered by an existing gitignore pattern — it will show as untracked in `git
  status`. Nothing was committed per instructions, but flagging this so the caller
  can gitignore it or clean it up deliberately.
