# ---- cell 0
# Kaggriculture: Agent Selection Harness & Engine Analysis

Competition run, August-September 2026. Rating went from 300 to a peak of 2,666.

This notebook is not an agent. It's the measurement system I built to choose between
agents, plus the engine behavior that made the measurement trustworthy.

My local tests disagreed with the ladder four separate times before I found why. Each
one silently invalidated days of work. Those four traps are documented below, along
with a replay analysis showing what actually decides a game.

# ---- cell 1
## Four traps that break local testing

**1. Last-callable entrypoint.** Kaggle's file runner picks the last callable bound in
the module namespace, not the function named `agent`. A notebook ending on an assignment
passes every turn and banks exactly the starting money. This cost me a submission that
scored 143. Rebinding the entrypoint took the same file to 1,705.

**2. Package version.** The competition ran engine 1.32.7. My notebook defaulted to
1.32.6, and every published agent went bankrupt locally while scoring normally on the
ladder.

**3. Config defaults.** Package defaults were `farmHandCostMult 10, startingMoney 2000`.
The competition used `1` and `3000`. Check with `starter` against `pass`: it must return
`[3509, 3000]`.

**4. Module state.** Trajectory agents hold globals across runs. Load a fresh module per
game or the second game is poisoned by the first.

# ---- cell 2


# ---- cell 5
## What decides a game

Two of my own games, same agent, same tile layout, same sales volumes:

| | Best (183,898) | Worst (29,521) |
|---|---|---|
| Strawberry sold | 254 | 252 |
| Milk sold | 279 | 278 |
| Strawberry price | 236 | 3 |
| Milk price | 278 | 1 |

Identical production, 6x difference in bank. The town shop draw sets which products have
buyers, and price follows demand almost exactly. Premium demand of 3 gave 42k; demand of
13 gave 134k.

## Ranking by money picks the wrong agent

One agent scored highest against a passive opponent (191,525) and won 7 of 30 contested
games. Another scored lowest (86,837) and won 29 of 30. Rating comes from wins, so
contested win rate is the metric, not bank.

Margin size predicts rating movement:

| Local margin | Rating change |
|---|---|
| +31,577 | +500 |
| +3,346 | +150 |
| +1,921 | none |

Below roughly +5,000 is noise.

# ---- cell 7
## Attribution

My final submissions used agents published by other competitors under Kaggle's code
sharing rules. The harness, the engine findings and the replay analysis in this notebook
are my own work.