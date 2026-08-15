# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

An agent for the Kaggle **Kaggriculture** simulation competition: two agents each manage a virtual farm over a 30-day season (720 turns, 24/day) and compete for the highest bank balance at the end. There is no static train/test set — everything is scored via live episodes against other agents plus a final Bradley-Terry tournament.

**`docs/kaggriculture_context.md` is the source of truth** for rules, mechanics, and pricing formulas. It's long; consult it before implementing or changing anything scoring-sensitive (yield math, market pricing, care/fertilizer bonuses) rather than relying on the summary below. The cheat sheet here exists to avoid re-reading that file for routine work.

## Commands

```bash
# Local test run against a built-in opponent ("pass", "random", "starter")
python -c "
from kaggle_environments import make
env = make('kaggriculture', configuration={'episodeSteps': 720}, debug=True)
env.run(['main.py', 'random'])
print(env.steps[-1])
"

# Submit
kaggle competitions submit kaggriculture -f main.py -m 'message'
kaggle competitions submissions kaggriculture
kaggle competitions logs <EPISODE_ID> 0   # debug a failed validation episode
```

## Hard constraints (violating these silently breaks a submission, not just a test)

- Entrypoint must be `main.py` at the root (single file) or a `.tar.gz` with `main.py` at the root (multi-file). Max **100 MiB** total.
- **No network I/O inside the agent function** — episodes run with no ingress/egress. Anything the agent needs must be `obs`, bundled data, or a bundled model checkpoint.
- Per-episode compute budget: 8 GiB HDD, 6.5 GiB RAM, 1.6 vCPUs — factor this in before bundling large models.
- One action per farmer/hand per turn; **max 10 market orders per turn** (extras are silently dropped, not rejected — no error to catch).
- Only `WHEAT` and `FERTILIZER` can be bought back via `BUY_PRODUCT`; every other product is sell-only.

## Agent I/O contract

The agent function receives `obs` (see full schema in `docs/kaggriculture_context.md` §3.12) and returns:

```python
{"farmer": [action, ...], "hands": [[action, ...], ...], "market": [[order, ...], ...]}
```

Key fields on `obs`: `obs["farms"][obs["player"]]` (own public farm state — tiles, money, farmer/hand positions), `obs["private"]` (own shed/seeds/inventories — opponent's shed is never visible), `obs["market"]` (inventory + prices per resource), `obs["town"]["unlocked_shops"]` (demand-side signal).

`tiles[y][x]` is `None` (empty), `"LOCKED"`, a plant dict, a weed dict, or a coop/pasture dict — check `kind` before assuming shape.

## Game mechanics an agent must get right

- **Watering/feeding**: miss 2 consecutive days → plant becomes a weed (must `DIG` to reclaim) or animal escapes (unrecoverable). A freshly planted seed already has `consecutive_unwatered = 1`, so **an unwatered new planting dies that same night** — no grace period. Animals do get a free first unfed day.
- **Fertilizer**: doubles the per-day yield bonus for 3 days, but only on days the plant is *also* watered — it's a multiplier on the watering baseline, not a substitute.
- **Care** (`CARE`, once/day): banks +1 only on days the animal was both fed and cared for; the whole bank pays out on the animal's next production day if fed that day, and resets to 0 either way after that day.
- **Selling mechanics**: sell price is quoted pre-sell, buy price post-buy; both players' orders process one unit at a time concurrently, so large simultaneous orders move price against each other mid-order. Premium goods (base price > $100: strawberry, melon, milk, wool) crash toward the $1 floor fast on oversupply — spread large sells rather than dumping them in one `SELL` order.
- **Hiring**: cost is `farmHandCostMult × fib(n)` where `n` resets to 0 every day — cheap for the first hire of the day, expensive for the third+.

## Repo layout

- `docs/kaggriculture_context.md` — full competition rules, mechanics, pricing formulas, observation schema, and a reference starter agent. Treat as read-only research material; update it only if the competition rules themselves change.
- `main.py` (once added) — the submitted agent entrypoint.

The planned agent workspace is organized as follows:

```text
washamba_bots/
├── main.py                 # Actual competition agent
├── agent/
│   ├── __init__.py
│   ├── state.py
│   ├── strategy.py
│   ├── economy.py
│   ├── movement.py
│   └── planner.py
├── experiments/             # Baselines and experiments
├── notebooks/               # Kaggriculture exploration notebooks
├── tests/
├── README.md
└── requirements.txt
```

## Iteration workflow

```text
GitHub → VS Code → write/modify agent →
run hundreds of local Kaggriculture games → inspect results/replays →
improve agent → submit to Kaggle → face real opponents → leaderboard
```

Use this loop for strategy work: validate changes locally across many games and inspect replays before submitting to the live competition.
