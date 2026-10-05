# Checklist, Monday 28 September 2026

MEASURED means run and saved with file and sample size; INFERENCE means judgement.

## Where we are tonight

- Active pair: Peter's `w3_dp_saletiming.py` and our `w3_dp_rebuild.py`, uploaded tonight, which retired W6. Both are W3 plus the tetsutani demand-preserving selling layer, so the pair is one lineage.
- MEASURED (wantam/m_dp_w6.txt and m_dp_w3.txt, seeds 900-915, both seats, 32 games each): the rebuild beats W6 18-14 (mean margin +189) and beats W3 19-13 (+245). The two seats give almost identical games, so this is really about 16 independent seeds, and margins are a few hundred coins: slightly ahead, within noise. Retiring W6 cost nothing measurable; it did not prove a gain either.
- MEASURED (self-play, seed 7): the rebuild's step 0 takes 0.14 s, its slowest later turn 76 ms, and the whole game 1.7 s of compute; W6 is the same order.
- WANTAM is off the final path: 2-30 against W6, and Sonnet's two v2 builds went 1-31 and 0-32 against W3.

## Morning

- [ ] Tell Peter and Billy: the rebuild is uploaded, W6 is retired, and nobody uploads again without agreeing first (any new upload now retires Peter's dp_saletiming, the older active one).
- [ ] Ask Peter one question: does his `w3_dp_saletiming.py` differ from the public tetsutani notebook? He reported 26-6 against W3; our rebuild measures 12-8 (Sonnet) and 19-13 (tonight).
- [ ] Read the ladder about two hours after the upload, once the rebuild has its first 20 or so games: compare it with dp_saletiming at equal game counts and similar opponent ratings; a gap under 100 points means nothing.
- [ ] Band panel (the test that matches how the final is scored): rebuild, W6 and W3, plus dp_saletiming if Peter shares it, on the 222 recorded ladder games against tape-family opponents rated 2,200 to 2,800 (`review_claude/results/bandpanel.py`). Report points share, games flipped better and worse, and the sign test.
- [ ] One cheap new candidate: W3 + demand-preserving + W6's front-running together, only if the two market layers do not fight over the same premium sales. Build it, self-play check, band panel, and 32 head-to-head games against the rebuild. Bar: band-panel share above the rebuild's, more games flipped better than worse, and at least 18 of 32 head to head.

## Afternoon

- [ ] Decide which agent carries which final name: Washamba Bots V1 for the best band-panel result, Nikaangukia Meroni for the second (a different lineage if the two are close, as insurance against a bug in one). Your call.
- [ ] Prepare the two final files, `washamba_bots_v1.py` and `nikaangukia_meroni.py`: Apache-2.0 attribution headers (v15stack Herd-Safe, tetsutani, PR 63 as they apply), self-play seed 0 DONE/DONE, last-callable check, timing check, sha256 logged in `docs/ENDGAME/submissions_log.md`.
- [ ] No upload on the 28th unless the band panel produces a clear winner.

## Tuesday 29 September

- [ ] 12:00 Nairobi: final pair decided.
- [ ] Evening: upload the two named files, second-best first, keeper last. Uploading a day early gives their ratings a day to settle and leaves the 30th for repairs only.

## Wednesday 30 September (deadline 23:59 UTC, 02:59 on 1 October in Nairobi)

- [ ] Repairs only: if an upload fails validation, fix and re-upload before 20:00 UTC (23:00 Nairobi), keeper last.
- [ ] Confirm both named agents show as active on the submissions page.

## Bradley-Terry: what we have learnt, and what it means for the agents

- The final ranking is one Bradley-Terry fit on win, tie or loss (a tie counts as half); coin margins count for nothing (the team measured corr(rating, margin) = +0.002). It uses games between submissions still active at the deadline, mostly the 1 to 15 October games, and the team scores the better of its two.
- MEASURED (local fit on 186,348 ladder results): W6 about 2,124 and W3 about 2,109 on the fit's scale; against opponents rated 2,000 to 2,300 we win exactly what the model expects, and above 2,300 we won 1 of 56. W3's residuals by opponent family and band are within noise, so there is no hidden matchup where we underperform; non-transitive matchups exist but only above about 2,800, where we rarely play.
- MEASURED: about 96% of the opponents we meet between 2,000 and 2,800 are tape-family agents, and 36 to 44% of W3's games against them end within 500 coins. Near a 50% win rate, one extra percentage point of wins is worth about 7 rating points.
- MEASURED tonight (32 games): a harness that compares only our own bank is misleading; WANTAM lost 2.9k of its own bank but handed the rival 7.7k. Only the head-to-head result counts.
- What it means: optimise the chance of winning each game, not the average bank. The edge is in the near-ties, which is why market-only layers that sell just before the rival (W6, demand-preserving) are the only things that have measured positive. Judge every candidate by games won on the band panel and head to head, with games flipped better against worse, never by mean margin.

## The 1-second rule

- Each turn has 1 second, plus a 60-second overage bank for the whole game (`obs["remainingOverageTime"]`). A timeout ends the game badly for us; INFERENCE, since we have never seen one, that it is scored as a loss.
- Our finalists sit far inside it: 1.7 s of compute for the whole game and 76 ms at worst per turn locally. Kaggle's 1.6 vCPU machine may be slower (INFERENCE), so the rule for anything new is: heavy work once at dawn, every other turn under 100 ms, the whole file under 500 ms on any turn locally, and fall back to W3's own action if the overage bank drops low.
