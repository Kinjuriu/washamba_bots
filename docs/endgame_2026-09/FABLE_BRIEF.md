# Brief for Fable: how does Washamba Bots get from 2,424 to 3,000 in Kaggriculture?

You are a research strategist for Washamba Bots, a Kaggle team in the Kaggriculture simulation competition. Stephane leads the team. Your job in this session is to **think, analyse and propose**, not to build. Read the material below, run any read-only analysis you need, and write your conclusions to `~/KagricultureLocalData/FABLE_IDEAS.md`.

## Ground rules

- Read-only on everything that exists. You may create scripts and outputs only under `~/KagricultureLocalData/analysis/fable/`.
- Do not submit anything to Kaggle, do not edit any agent, do not push to git.
- Label every claim as **measured** (you or a file computed it; name the file) or **inference**. Quote numbers with their sample size.
- If something in this brief looks wrong after you check it, say so. The brief is a starting point, not the truth.

## Read first (in this order)

1. `~/KagricultureLocalData/Kaggriculture_and_Washamba_Bots overview & decision log.docx`: the game, the rules, the team's history.
2. `~/KagricultureLocalData/TOP6_FINDINGS_2026-09-23.md`: the latest findings; the numbers below come from here.
3. `~/KagricultureLocalData/episodes/20260923T153431Z_top6/fresh_top6_decision_report.md`: the current top six's decisions (360 trajectories). Its advice to copy Boey's selling rate was later shown to be wrong; see file 2.
4. `~/KagricultureLocalData/episodes/20260923T161855Z_washamba_vs_top6/washamba_vs_top6_report.md`: our four submissions against that corpus.
5. `~/KagricultureLocalData/public_notebooks/FINGERPRINTS.md`: 623 public notebooks fingerprinted; none share the top six's openings.
6. The engine itself, `kaggle_environments/envs/kaggriculture/kaggriculture.py` in the installed kaggle-environments 1.32.7 (find it with `python -c "import kaggle_environments,os;print(os.path.dirname(kaggle_environments.__file__))"`). Read `_process_market`, `market_price`, `_commit_unit`, the town and shop consumption code and the daily refresh. **The market rules are the heart of this game.**

## Hard facts (measured)

- **Scoring.** Win, loss or tie only; bank margin does not count. Final ranking is a Bradley-Terry tournament over the latest two submissions per team, played 1 to 15 October. Final submission deadline: **30 September 23:59 UTC**. Five uploads a day.
- **Agent constraints.** A single file, about 1 second per turn (60-second overage bank per game), no network, CPU only.
- **Our standing.** W0 (public "v15stack", unchanged) is rated 2,424 after 93 games. W1 (the same file with its premium-sale reservation horizon changed from 40 to 44) is rated 2,018 after 71 games, but it is younger and has met weaker opponents. The top ten are 2,985 to 3,100.
- **Two families of agent.** Every public agent (v15stack, V57, K0013, Fieldcraft) is a "tape" agent: it replays recorded 720-turn action streams chosen by the first shop unlocks, with repair layers on top. They all share one opening (turn 2: five hires, two cows, two sheep). None of the top six is a tape agent.
- **Top six vs tape agents: 79 wins, 1 loss, median margin +21,000** (80 games).
- **Where the ~21,000 comes from** (exact engine re-simulation, 14 top-six vs tape games; small sample):
  - Premium prices on the same volume: wool 135 vs 78 per unit (+4,600 per game), strawberry 133 vs 106 (+3,500).
  - More output in uncrowded markets: eggs +5,800 (about 6 geese vs 2), tomatoes +5,600 (about 19 seeds vs 2), carrots +5,000, wheat +4,600.
  - Melon is the one product where tapes do better (-4,000).
  - Revenue on days 0 to 9: 21,500 vs 12,500.
- **Boey's thousands of orders are churn.** Boey buys and sells about 4,000 wheat units a game at the same average price; its net wheat and fertilizer income matches everyone else's.
- **Openings spread by copying replays.** The DSM / DECEM / Unknown Mother-Goose turn-1 opening (buy 1 cow, buy 5 wheat) was used on 21 September by DSM (91 games), Vadim Vasilenko (83), Unknown Mother-Goose (75), QQ (14) and Orbital Terraformer (8). No public notebook has it. Openings are deterministic and copyable from replays; the reactive mid-game is not.
- **Our ladder band (2,000 to 2,500) is full of v15stack copies.** In W0's games against 2,200+ opponents, every product's revenue is within 1 to 3% of the opponent's.

## Tests already run (so you don't repeat them)

- **Top-six replay panel.** A recorded top-six game replayed as the opponent on its original seed reproduces their result closely, as long as our agent plays like their original opponent (Boey 103,548 vs original 103,662). 38 of 80 games stay "faithful" (tape bank within 5% of the original). On those, **W0 loses 32 of 38, median -21,700.** Only compare two candidates on games where the tape stays faithful under both. Tools are in `~/KagricultureLocalData/harness/`: `tapeopp.py`, `top6panel.py`, `top6_panel.json`, `faithful_eps.json`, `panelsum.py`.
- **Exact re-simulation** of any replay with every traded unit logged: `harness/resim_trades.py`. The results for 78 games are in `analysis/exact_trades_78games.jsonl`.
- **Keeping more geese** (turning off v15stack's herd swaps): no change on the panel.
- **Top-six games used as v15stack routes** (route generation seven): fails on new seeds (DSM routes 6-14 against W0, DECEM 4-16, Boey 0-20). Recorded moves from reactive agents don't transfer to new seeds.
- **Selling earlier** (W1, reservation horizon 44): a small edge in mirror games (36-28-24 on 88 fresh games).

## Questions to answer

1. **The price mechanism.** How do the top six sell wool at 135 while the tape opponent gets 78 for the same volume in the same game? Use the replays and the market code: when each side sells relative to the other, queue position within the turn, slice sizes, what the town and shops consumed between sales. Is this skill we can reproduce with a rule, and what would the rule be?
2. **The production mechanism.** How do the top six run about 6 geese, 19 tomato plants and more carrots on the same 75 tiles and about 11 to 14 hands? What does their labour allocation look like per day? What do they give up to get it?
3. **Approaches beyond tapes.** For each of: (a) new layers on v15stack; (b) a reactive heuristic agent written from scratch; (c) supervised learning of the top six's daily macro decisions from their trajectories, with a hand-written executor; (d) search or model-predictive control using the engine's exact price function inside the 1-second budget; (e) reinforcement learning. Give the expected gain, the days needed, the main risk, and how we would measure it with the tools above.
4. **Two agents to build in the next 48 hours.** One lower-risk and one ambitious. For each: what it changes, why the data says it should help, the local test that must pass (name the panel, the seeds and a pass threshold), and what result would kill the idea.
5. **Anything we are missing.** Mechanics in the engine that none of this uses, or a wrong assumption in this brief.

## Output format for FABLE_IDEAS.md

- A one-paragraph summary first.
- One section per question, each with measured evidence and inference kept separate.
- A final table of ideas ranked by expected rating gain per day of work.
- Keep it under about 2,500 words. Plain English.

---

# Update, 26 September 2026 (Fable 5.1 review session)

Full review: `review_fable/REVIEW.md` (audit, mistakes, plan); raw tables `review_fable/NUMBERS.md`; ideas `review_fable/IDEAS_2900.md`; behavioural inference of the top six `review_fable/POLICY_INFERENCE.md`. All numbers below are MEASURED by exact re-simulation unless marked inference.

## Corrections to the facts above
- The gap decomposition and the "days 0-9: 21,500 vs 12,500" figure came from 14 games. Over 1,268 games the early gap is 13.6k vs 13.2k (the 21.5k is Boey's wheat churn). Per-product medians, top six minus our seats: tomato +3.9k, egg +3.6k, wool +3.5k, wheat +2.7k, strawberry +2.2k, milk +1.9k, carrot +0.6k, melon -0.4k, fertilizer -2.2k.
- Top six vs tape family recomputed: 80-1, median +21,064 (n=81). W0 on the faithful top-six panel: 6 of 38, median -21,744 (confirmed).
- The top six DO buy the third quadrant (179 of 473 seats; DSM 26/26). "0/360" was wrong.
- DECEM does run the top-six opening (87 of 87 seats). The PR 61 "correction" used four stale games.
- The top-10 line (ranks 7-12) is closer than the top six: W3 wins 3 of 31 faithful ranks-7-12 replays, median -13,817; 0 of 22 vs THIRD FARM CLUB.
- W3 leaves $0 unsold at the end and loses about 5 units a game to the shed cap, the same as everyone. Neither is a lever.

## New signal: harvests are public, sales follow them
The opponent's farm is fully visible, including yield counters. A counter dropping to zero is a harvest. Opponent sales of wool/milk/strawberry follow their own visible harvest within a median 2-5 steps; 60-78% within 6 steps; melon 87-95%. This holds for tape-family opponents (32 games) and for the top six (24 seats). `review_fable/harvest_lag.py`.

## What the top six actually do (policy inference, `review_fable/POLICY_INFERENCE.md`)
- Scripted opening to about step 150 (land at fixed steps 150 / 220 / 254 for the DSM family), then a per-game-unique reactive controller (labour agreement across games 0.03-0.10 after step 144, whether or not the first shop matches). Not tapes, not shop-keyed routers.
- Herd sized by shop counts: about 3 sheep with no yarn store, 11-12 with one; 5-6 cows without milk shops, 9-10 with; 3-5 geese without egg shops, 6-8 with. Near-identical thresholds across six teams: a shared rule table.
- Selling: hold premium stock (median shed-to-sale lag 14 steps for wool, 10 strawberry), then at each post-drain tick sell a small fixed lot that roughly matches the shop drain (2 wool, 2 milk, 4-6 strawberry), 70-85% of lots at the post-drain hour; sell a larger fraction when price >= base. They do not react to the opponent's sales (3-8% of their lots are within 2 steps of an opponent lot; W3: 57-62% on the same step).
- W3 for contrast: sells 100% of shed stock per event, within 2 steps of it arriving; buys its second quadrant at step 266 with $18k idle, two days after the top teams (199-222); 16 animals at day 10 vs 19.
- Stranded-value curve: W3 is not slow to convert. At day 12 it holds 15.0k cash and 6.5k stranded (30%) vs the top six 11.8k cash and 11.3k stranded (53%). The lag hypotheses (inventory-to-cash, liquidation, overflow) are not where the gap is; price-per-unit (dumps vs metered lots) and earlier capital deployment are.

## Test in progress: W3 + harvest-triggered front-running (`review_fable/agents/w3_hf.py`)
Market-only overlay; flag off is byte-identical to W3 (verified). Interim, seeds 9101-9120 both seats: vs W3 30-10 (+362); vs hsv3 16-4, w0 17-3, v57 16-4, fieldcraft 16-4, k0013 19-1, farm2945 19-1 (n=20 each). Same-seed W3 references and the two replay panels are running; results will be appended to `review_fable/HF_RESULTS.md`.

## Result of the front-running test (26 September, later)
Full tables: `review_fable/HF_RESULTS.md`. Agents: `review_fable/agents/w3_hf*.py` (flag off = W3 byte for byte).
- In the tape band the harvest-triggered slot-0 sell is a real edge. Best variant (`w3_hf_early.py`, no firing after step 600), seeds 9101-9110 both seats: vs W3 18-2 (+358), vs v57 18-2 (+1,051), vs hsv3 18-2 (+631, better than W3 in 14 of 20 same-seed games), vs w0 17-3. Base overlay wins the W3 mirror 30-10 over 40 games.
- Against reactive opponents it costs money and changes no result: ranks-7-12 replay panel, paired with W3 on identical games, worse in 23 of 31 (mean -252) for the best variant, 25 of 31 (-418) for the base; wins stay at 3-4 of 31. Top-six panel neutral (+77 mean, -51 median, n=46).
- Making it conditional on a public-data dumper classifier failed as built: the verdict flips early, it fired in 52 of 60 panel games, and lost the mirror edge. An opening fingerprint (land at step 150/220 = DSM family; 151/266 = tape forks) is the more reliable switch and is untested.
- Behavioural inference of the top six (`review_fable/POLICY_INFERENCE.md`): scripted opening to step ~150, land on a clock, herd sized by shop counts, and premium goods sold as fixed 2-unit lots (4-6 strawberry) every post-drain tick, more when price >= base, with no reaction to the opponent. W3 sells its whole shed per event and lands on the opponent's step 60% of the time. W3 is not slow to convert; it is early-capital-idle (second quadrant at step 266 with $18k vs 199-222 at the top) and under-built (16 animals at day 10 vs 19).
- Ranking: the corpus on disk cannot reconstruct a Bradley-Terry board (40 teams with 4+ games; fit correlates 0.15 with the 24 September scores). A broad crawl is needed; the Kaggle CLI is not configured on this Mac.
