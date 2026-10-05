# Local Bradley-Terry fit, 27 September 2026

Data: Sonnet's results-only crawl, 186,348 completed public episodes, 7,337 teams (episodes/20260927T125004Z_bt_crawl). Model: one strength per submission, P(i beats j) = logistic(strength_i - strength_j), ties counted as half a win for each side, fitted by maximum likelihood with a very light ridge (0.01) so submissions with one or two games stay finite. MEASURED unless marked.

## Calibration to the live leaderboard

Best submission per team (30+ games in the crawl) against the team's live score: correlation 0.82 over 745 teams; one logit is about 130 leaderboard points on this crawl (Elo's convention would be 174). The live leaderboard is Kaggle's sequential rating for matchmaking, not the final fit, so this only tells us the two agree on the order.

## Where we stand

| submission | games | fitted score | rank among 745 teams |
|---|---|---|---|
| W6 (ours, 56601524) | 84 | 2,124 | 236 |
| W6 (Peter's, 56596297) | 90 | 2,118 | 241 |
| W3 (first upload, 56518334) | 106 | 2,109 | 250 |
| W1 (first upload) | 152 | 1,967 | 359 |
| W0 | 157 | 1,957 | 370 |

The crawl was seeded from our band and the top 12, so ranks here are relative to that sample, not the whole leaderboard. The top of the fitted scale is stretched (DSM 3,918, the tenth team 3,179), because the top teams mostly beat everyone they meet.

## Expected versus actual, by opponent strength (W3 and both W6 copies, 280 games)

| opponent fitted score | games | actual wins | expected | residual |
|---|---|---|---|---|
| below 2,000 | 75 | 71.0 | 68.8 | +2.2 |
| 2,000 to 2,300 | 149 | 69.5 | 69.8 | -0.3 |
| 2,300 to 2,500 | 19 | 1.0 | 1.8 | -0.8 |
| 2,500 to 2,700 | 32 | 0.0 | 1.0 | -1.0 |
| above 2,700 | 5 | 0.0 | 0.0 | 0.0 |

No band where we play above our strength. Above 2,300 we won 1 game of 56.

## Upsets (won or tied when the model gave us under 35%)

Ten in 280 games. Nine are near-ties against 2,200 to 2,300 agents (margins +72 to +1,555). One is real: **W3 beat AI是我的豆包 (fitted 2,460 over 162 games; live rating 2,817 on 24 September) by +5,697, episode 112920040**, with a 6% expected chance.

What happened (exact re-simulation, both sides):
- The opponent is reactive, not a tape (its own opening; tomatoes, geese). It built tomatoes to 22 tiles by day 22 and let wheat fall from 19 tiles to 2. It sold 145 tomatoes for 12,773, but it had to buy 122 wheat and grew less of everything else.
- W3 kept 24 to 26 wheat tiles and 9 sheep (the opponent 6), and sold 218 wool at 135 (the opponent 140 at 147): +8,900 on wool. Milk +5,700, wheat +5,300, fertiliser +3,500. The opponent won strawberry (99.9 vs 74.4 per unit), tomato and egg.
- So the upset was the opponent over-investing in one crop and starving its wheat base. W3 did not play better than usual; it held a steady base while the rival broke its own. The inverse lesson for any new agent: capacity added to one product must not come out of the wheat base (the same failure Peter's controller shows).

## What Kaggle's final fit depends on (INFERENCE, not verifiable offline)

1. Which games count: only games between submissions still active at the deadline, and the October 1 to 15 games will dominate.
2. Outcome coding: win, loss, tie at half; bank margins ignored (stated by Kaggle).
3. Estimation: plain maximum likelihood or a Bayesian prior. A prior mostly affects submissions with few games, which is why a late upload is not penalised much once October's games arrive.
4. Scale and anchor: some mapping from logits to the familiar 600 to 3,000 numbers.
5. Team score: the better of the two active submissions. A second, different agent is a free extra draw; two identical copies add little.

## What it takes to reach 2,900

On this fit, a rank-10 team sits about 8 logits above W6. Against such a team, W6's modelled chance of winning is under 1 in 1,000, and the observed record agrees (0 of 37 above 2,500). Reaching that band needs an agent that wins a real share of games against reactive teams, not a better tape.
