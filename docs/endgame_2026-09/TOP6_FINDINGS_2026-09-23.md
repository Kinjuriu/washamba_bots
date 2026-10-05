# What separates the top six from us: findings, 23 September 2026 (evening)

Sources: Sonnet's two corpora in `episodes/20260923T153431Z_top6/` (360 top-six trajectories) and
`episodes/20260923T161855Z_washamba_vs_top6/` (290 of our games); 78 of those games re-simulated
exactly through the engine (kaggle-environments 1.32.7) with every traded unit logged.

## 1. Corrections to Sonnet's reports

- **Boey's order rate is churn, not the edge.** Boey buys and sells 3,000 to 4,600 wheat units a game at the
  same average price (for example 39.4 bought, 39.4 sold), plus about 1,000 fertilizer each way. Its net income
  from wheat and fertilizer (about $21k to $27k) matches DSM, Mother-Goose and our W0. Copying the order rate
  copies noise.
- **The cash-trough advice points at `main.py`.** Our submitted agents are v15stack; `MIN_CASH_RESERVE_FOR_SEED_BUYING`
  does not exist in them.
- **W1 at 2,018 is not worse than W0 at 2,424.** W1 is younger and has mostly met 1,500 to 2,000 opponents;
  W0 has met 49 opponents above 2,000. Compare at equal episode counts.

## 2. What the data shows

- **Every public agent is one family.** v15stack, V57, K0013 and Fieldcraft all open with the same tape
  (turn 2: five hires, two cows, two sheep). None of the top six do. DSM, DECEM and Unknown Mother-Goose share
  an identical opening of their own (turn 1: buy 1 cow, buy 5 wheat; turn 2: sell 1 wheat, 4 hires, 1 cow,
  3 sheep), so they probably come from one common ancestor.
- **Our ladder band is mirrors.** In W0's games against 2,200+ opponents, every product's revenue is within 1 to 3%
  of the opponent's. The 2,000 to 2,500 band is full of v15stack copies.
- **The top six crush the tape family:** 79 wins, 1 loss, median margin +21,000 against tape-family opponents.
- **Where the ~21,000 comes from** (exact engine logs, top six vs tape-family opponents, per game):
  - Premium prices, same volume: wool 135 vs 78 per unit (+4,600), strawberry 133 vs 106 (+3,500).
  - More output in uncrowded markets: eggs +5,800 (about 6 geese vs 2), tomatoes +5,600 (about 19 seeds vs 2),
    carrots +5,000, wheat +4,600.
  - Melon is the one product where the tapes do better (-4,000).
  - Early revenue, days 0 to 9: 21,500 vs 12,500.

## 3. Local tests tonight

- **Top-six replay panel.** A recorded top-six game replayed as the opponent on its original seed and seat
  reproduces the original bank closely when our agent plays like the original opponent (Boey: 103,548 vs 103,662).
  38 of 80 games stay faithful (tape bank within 5% of the original). On those, **W0 loses 32 of 38, median
  -21,700.** Tools: `harness/tapeopp.py`, `harness/top6panel.py`, `harness/top6_panel.json`, `harness/faithful_eps.json`.
  Only compare candidates on games where the tape stays faithful under both.
- **Keeping geese (turning off v15stack's herd swaps):** no change (median identical, better in 3 of 32).
- **Route generation seven (today's top-six games as v15stack routes, keyed by first two shops):** fails on new seeds.
  Against W0 over 20 games each: DSM routes 6-14, DECEM routes 4-16, Boey routes 0-20. The top six are reactive
  agents; their recorded moves do not transfer to a new seed.

## 4. What this means

v15stack tweaks cannot close a 21,000-coin gap. There are two tracks:

- **Rating now (tape ceiling, about 2,600 to 2,700):** win the mirrors in the 2,000 to 2,500 band (W1-style edges).
- **The 3,000 path:** a reactive economy like the top six (more geese, tomatoes and carrots; premium sales timed ahead
  of the opponent). Fastest start: find the public ancestor of the DSM / DECEM / Mother-Goose opening, if one exists,
  and build on it, measured on the top-six replay panel.
