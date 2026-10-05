# Step 1: independent view, written before reading any team/assistant conclusions
(Fable 5.1 review, 2026-09-26. Sources: engine kaggriculture.py 1.32.7, submissions/*.py headers and diffs,
4 re-simulated ranks-7-12 replays, episodes/manifest.csv (300 ladder games of 5 top teams), leaderboard CSV 2026-09-24.)

1. What our agents are. MEASURED (diff --strip-trailing-cr): W0 = public v15stack unchanged; W1 = W0 with one
   constant (V9_RACE_DEFAULT 40->44); W3 = public "Herd-Safe LB 2700" notebook unchanged; W4 = W3 with two
   constants (RACE 44->48, _HP_WINDOW 4->6). Every line of economy, routing and tape is public and shared with
   hundreds of other teams. So our expected rating is the public agent's rating plus noise; W3's own title says
   "LB 2700". Rank 508 at 2,474 on 2026-09-24 is consistent with that.

2. What the game rewards. The market is shared between the two players; premium books (MELON, WOOL, MILK,
   STRAWBERRY) crash to $1 within ~60-160 units of glut and only recover through town/shop draws. Final rank is
   Elo from pairwise win/loss; banks of top-6 teams are ~100-125k with typical margins of a few thousand
   (manifest: 49 of 300 games decided by < $2,000). So the game at the top is: same lineage vs same lineage,
   decided by (a) route choice given shop draws, (b) who sells premium lots first, (c) small economy edges.

3. What limits us (INFERENCE from 1-2). Not the constants. A copy of a public agent cannot out-rate the public
   agent's own field; mirror matches are coin flips. The top-10 have private forks with real economy or timing
   advantages (DSM went 60-0 in the manifest sample, median bank 109k vs 92k for its opponents). Tuning a
   sale-horizon constant moves sale timing by a few turns and, against a diverse ladder, is inside noise.

4. Engine facts I would check nobody is exploiting (all MEASURED from kaggriculture.py):
   - Animals produce 1 FERTILIZER per day whether fed or not (only escape needs 2 consecutive unfed days), and
     scheduled production (egg/milk/wool) does not require feeding either; feeding only prevents escape and
     enables the CARE bonus. Feeding every other day is enough to keep the herd. Fertilizer sells ~$100 falling
     $0.2/unit, no town draw ever recovers it, so it is a ~$25k shared book; in the 4 replays it was 10-15%
     of revenue.
   - Hands cost fib(n): the 12th hand costs $144/day, 13 hands ~$375/day, so a 12-13 hand crew costs ~$8-10k a
     season, i.e. ~8-10% of a 100k bank. Whether the marginal hands earn that back is testable.
   - Sales at $1 do not raise market inventory; BUY_PRODUCT WHEAT is quoted at post-buy inventory.
   - Shops are drawn with replacement from a seed-keyed RNG at end of day 2,5,8,...; the whole product-demand
     schedule is known at day 3/6/9 boundaries, and both players see it.
   - Weeds: 0.5%/tile/day, negligible.

5. Is 3,000 reachable? INFERENCE, confidence ~85%: No, not with copies of public agents plus constant search,
   and not in 4 days with 5 uploads/day and a rating that needs many games to converge. Realistic best finish:
   the strongest public fork correctly chosen, ~2,600-2,750. Anything above needs an economy or timing edge over
   the private top-10 forks, which nobody on this team has demonstrated in any test I have seen so far.
