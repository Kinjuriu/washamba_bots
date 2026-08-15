# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

An agent for the Kaggle **Kaggriculture** simulation competition: two agents each manage a virtual farm over a 30-day season (720 turns, 24/day) and compete for the highest bank balance. There is no static train/test set — everything is scored via live episodes against other agents plus a final Bradley-Terry tournament.

**Current state:** `main.py` holds `nikaangukia_meroni` — a deterministic, rule-based agent (harvest → water → reclaim weeds via `DIG` → move-to-urgent → plant → walk → pass, plus threshold-based selling). `hands` is always returned empty. `tests/` carries a 34-case stdlib-`unittest` suite for its helpers. There is no `agent/` package — that part of the `README.md` layout is still aspirational. `experiments/` holds evaluation tooling (see below) and `notebooks/` has two working exploration notebooks.

**Current baseline — mean final bank over 12 seeded 720-turn seasons per opponent:**

| vs | mean | stdev | min | max | wins |
|---|---|---|---|---|---|
| `pass` | 5635 | ±744 | 4514 | 7045 | 12/12 |
| `random` | 5264 | ±410 | 4815 | 6209 | 12/12 |
| `starter` | 5555 | ±1128 | 4734 | 8757 | 12/12 |

Two later fixes moved the **floor** far more than the mean, which is where the real gain is: a **season-maturity gate** (`choose_crop` refuses crops whose `first_yield_day` can't land before day 29 — the agent used to bleed cash buying tomato seed it could never harvest) and a **shed-overflow valve** (force-sell at 90/100 items, since overflow is silently discarded). Minimums rose ~1,200 across every opponent and `starter` went 11/12 → 12/12.

**The weed cascade — fixed, and worth remembering.** The previous baseline lost to `pass` (an opponent that does nothing and banks $3000) on ~2/12 seeds, finishing *below* its own starting money. Root cause: one farmer planted more tiles than it could water, plants weeded out, and because the agent never emitted **`DIG`**, every weeded tile stayed dead for the rest of the season. The farm decayed to 23/25 weeds and sales starved to 3.9 `SELL` orders per season — zero on the losing seeds.

Adding `DIG` moved every metric at once: **SELL orders 3.9 → 22.9**, **end-of-season weeds 23.0 → 2.1**, and the sub-$3000 downside disappeared. The lesson generalizes: **tile upkeep capacity, not sell-price tuning, is what gates this agent's income.** Before optimizing thresholds, check how many tiles are alive at season end.

Still unimplemented (deliberately): animals, `FEED`/`CARE`, hired hands (`HIRE`), `FERTILIZE`, `BUY_LAND`, and shed transfers (`DROP`/`PICKUP`). Remaining known gap: still loses ~1/12 to `starter`.

## Sources of truth, in priority order

Kaggle staff, resolving a thread of documented-vs-actual mismatches: **"engine is the source of truth."** Follow that order here.

1. **The installed environment itself** — `.venv/Lib/site-packages/kaggle_environments/envs/kaggriculture/`. This is the code that actually scores you:
   - `kaggriculture.py` — the real interpreter. `MARKET_PARAMS` and the object tables live here; settle any mechanics dispute by reading it.
   - `AGENTS.md` — the official agent-authoring guide.
   - `README.md` — full rules, object/price/shop tables.
   - `kaggriculture.json` — config defaults + observation/action schema.
2. **`docs/kaggriculture_context.md`** — a compiled snapshot (Aug 15, 2026) of the competition pages. Its deadlines, prizes, submission limits, and compute budgets were re-verified verbatim against the live site on that date, and it postdates the balance patch. Its **mechanics** claims are second-tier — staff have corrected several doc-vs-engine mismatches over the season, so check the engine before trusting a mechanic here. Known gap: the **per-turn timeout** (see below). Section anchors: §3.2 crop & animal table, §3.10 market pricing, §3.12 observation schema.
3. `README.md` at the repo root — architecture diagrams (state manager → strategy → planner → executor) and competition dates.

Official starter notebook (pinned, Apache 2.0): <https://www.kaggle.com/code/bovard/kaggriculture-getting-started>.

The env also ships a second environment, **`kaggriculture_beginner`**. It is referenced nowhere on the competition site and the official starter notebook never calls it — always `make("kaggriculture", ...)`.

**Pin `kaggle-environments>=1.32.6`.** A mid-season balance patch (~Aug 6, 2026) cut Town Center demand to a flat 1×/day (was 2×/day with a 2×/4× late-game ramp) and made shop unlocks sample *with* replacement; staff told everyone to upgrade. The official starter notebook still pins `>=1.32.2`, which predates the patch — don't copy that pin. The env is patched mid-competition, so after any upgrade, re-read `kaggriculture.py` rather than trusting cached knowledge of the mechanics.

## Setup and commands

The environment is already built at `.venv/` (Python 3.12.3, provisioned by `uv`). `pyenv` is not installed on this machine and the README's `pyenv` + `.venv/bin/activate` instructions do not work here — on Windows it's `.venv/Scripts/`.

```bash
# Recreate from scratch if needed
uv venv --python 3.12.3 .venv
uv pip install --python .venv/Scripts/python.exe \
  kaggle-environments==1.32.7 kaggle==2.2.4 \
  numpy==2.4.6 pandas==3.0.5 matplotlib==3.11.1 seaborn==0.13.2 \
  jupyterlab==4.6.3 ipykernel==7.3.0

# Run the agent (built-in opponents: "pass", "random", "starter")
.venv/Scripts/python.exe -c "
from kaggle_environments import make
env = make('kaggriculture', configuration={'episodeSteps': 720}, debug=True)
env.run(['main.py', 'random'])
print([(i, s.reward) for i, s in enumerate(env.steps[-1])])
"

# PRE-SUBMIT GATE: Kaggle validates every upload with a self-play episode.
# A crash there rejects the submission no matter how good the strategy is.
.venv/Scripts/python.exe -c "
from kaggle_environments import make
env = make('kaggriculture', configuration={'episodeSteps': 720, 'seed': 0})
env.run(['main.py', 'main.py'])
print([s.status for s in env.steps[-1]])   # must be ['DONE', 'DONE']
"

# Submit
.venv/Scripts/kaggle.exe competitions submit kaggriculture -f main.py -m 'message'
.venv/Scripts/kaggle.exe competitions submissions kaggriculture
.venv/Scripts/kaggle.exe competitions logs <EPISODE_ID> 0   # debug a failed validation episode
```

A full 720-turn episode runs in **~6.8s**, so hundreds of local games is a matter of minutes, not hours. A replay JSON is ~4.9 MB — don't commit them.

`requirements.txt` is a broad 190-package `pip freeze` from a wider ML workspace (jax, flax, transformers, open-spiel, litellm, and `pokerkit`), **not** this agent's dependency set. Installing it wholesale is not required, and a package appearing there is no license to import it from `main.py`.

Tests are stdlib `unittest` — **pytest is not installed and the suite doesn't need it**. Don't reach for pytest idioms (fixtures, `assert` rewriting, parametrize); match the existing `unittest.TestCase` style. No linter or type checker is configured (ruff, mypy, black all absent).

```bash
.venv/Scripts/python.exe -m unittest discover -s tests          # whole suite
.venv/Scripts/python.exe -m unittest tests.test_nikaangukia_meroni.TestShouldSell -v   # one case
```

Unit tests only cover helpers in isolation. **The real verification for a strategy change is a seeded batch, never a single game.** Run-to-run spread is huge — the same `main.py` vs `random` matchup scored 5228 and 3776 on two unseeded runs, and stdev is ~±600 across every opponent. A single episode cannot tell an improvement from luck, and a one-off loss to `starter` means nothing.

Pass `seed` in the configuration to make episodes **fully deterministic** (verified: the same seed reproduces an identical final bank twice). Compare a change against the same seed set:

```bash
.venv/Scripts/python.exe experiments/seeded_batch.py   # mean/stdev/win-rate vs all 3 built-ins
.venv/Scripts/python.exe experiments/benchmark.py      # adds melon_maxxer from the official notebook
```

At ~7s per season, 12 seeds × 3 opponents is about 4 minutes. Report mean and win-rate, not a single score. `experiments/replay_diagnostics.py` breaks a single episode down by action histogram and end-of-farm state — that's what found the weed cascade. Replay JSONs it dumps are multi-MB and gitignored.

Kaggle CLI is authenticated (`~/.kaggle/credentials.json`) as `peterkibetspidey`, and the account is entered in the competition — verify with `kaggle competitions list --group entered` (expect `userHasEntered: True`). Re-auth with `kaggle auth login` if the session expires.

## Hard constraints (violating these silently breaks a submission, not just a test)

- Entrypoint must be `main.py` at the root (single file) or a `.tar.gz` with `main.py` at the root (multi-file). Max **100 MiB** total.
- **`actTimeout` is 1 second per turn**, with a 60-second overage bank for the episode (`obs["remainingOverageTime"]` tells you what's left). Set in `kaggriculture.json` and verified to resolve to `1` via `env.configuration`. The forum treats this as an open question — no staff answer — but per "engine is the source of truth" the spec is the better evidence. Budget for 1s: no per-turn deep search. Absent from `docs/kaggriculture_context.md`.
- **No network I/O inside the agent function** — episodes run with no ingress/egress. Anything the agent needs must be `obs`, bundled data, or a bundled model checkpoint.
- Per-episode compute budget: 8 GiB HDD, 6.5 GiB RAM, 1.6 vCPUs — factor this in before bundling large models.
- One action per farmer/hand per turn; **max 10 market orders per turn** (extras are silently dropped, not rejected — no error to catch).
- Only `WHEAT` and `FERTILIZER` can be bought back via `BUY_PRODUCT`; every other product is sell-only.
- 5 submissions/day; only your latest 2 stay active for matchmaking and final scoring.
- Scoring runs ~2 weeks past the Sept 30 final-submission deadline, then **one** Bradley-Terry tournament sets the final ranking — deliberately, to damp hot streaks. Late-season leaderboard position is noisy; don't over-tune on it.

## Agent I/O contract

**The entrypoint is the *last callable in the module namespace*, not a function named `agent`.** `kaggle_environments/agent.py:64` does `[v for v in env.values() if callable(v)][-1]`. A helper function — or a class, since classes are callable — defined below `agent()` silently becomes your submission. Keep `agent` last in `main.py`, and put helpers in an imported module or above it.

This fails **silently**, which makes it nasty to catch. Verified locally: with a helper defined after `agent()`, the episode still reports `status=DONE` with no error — the wrong callable returns garbage, every action is discarded as an invalid no-op, and the agent finishes on exactly `startingMoney`. **A local run that ends at exactly $3000 means your agent never actually acted.** Treat that number as a failure signal, not a bad strategy.

`main.py` satisfies the rule with a trailing `agent = nikaangukia_meroni` binding on the final line. **Keep that line last** — anything callable added below it silently hijacks the submission.

Both `def agent(obs)` and `def agent(obs, config)` work: the framework builds `[observation, configuration]` and truncates it to the function's `co_argcount` (`agent.py:151-153`). Taking `config` gets you `episodeSteps`, `boardSize`, `maxMarketOrdersPerTurn`, etc. rather than hardcoding defaults.

Return:

```python
{"farmer": [action, ...], "hands": [[action, ...], ...], "market": [[order, ...], ...]}
```

`obs` keys (verified against a live episode): `player`, `day`, `hour`, `step`, `farms`, `market`, `town`, `private`, `remainingOverageTime`. Note `step` and `remainingOverageTime` are supplied by the framework and are missing from the §3.12 schema in the docs.

Key fields: `obs["farms"][obs["player"]]` (own public farm state — tiles, money, farmer/hand positions), `obs["private"]` (own shed/seeds/inventories — opponent's shed is never visible), `obs["market"]` (inventory + prices per resource), `obs["town"]["unlocked_shops"]` (demand-side signal).

## Game mechanics an agent must get right

- **Watering/feeding**: miss 2 consecutive days → plant becomes a weed (must `DIG` to reclaim) or animal escapes (unrecoverable). A freshly planted seed already has `consecutive_unwatered = 1`, so **an unwatered new planting dies that same night** — no grace period. Animals do get a free first unfed day.
- **Fertilizer**: doubles the per-day yield bonus for 3 days, but only on days the plant is *also* watered — it's a multiplier on the watering baseline, not a substitute.
- **Care** (`CARE`, once/day): banks +1 only on days the animal was both fed and cared for; the whole bank pays out on the animal's next production day if fed that day, and resets to 0 either way after that day.
- **Selling mechanics**: sell price is quoted pre-sell, buy price post-buy; both players' orders process one unit at a time concurrently, so large simultaneous orders move price against each other mid-order. Premium goods (base price > $100: strawberry, melon, milk, wool) crash toward the $1 floor fast on oversupply — spread large sells rather than dumping them in one `SELL` order.
- **Hiring**: cost is `farmHandCostMult × fib(n)` (default mult 1) where `n` resets to 0 every day — cheap for the first hire of the day, expensive for the third+.

## Silent-failure gotchas

Every one of these is a no-op or a wrong answer with **no error raised**:

- **`tiles[y][x]` is row-major, but `farmer` and `hands` are `[x, y]`.** The axis flip between them is the classic hour-long debug.
- **The shed is not a tile** and never appears in `tiles`. "Shed-adjacent" is one of the four center tiles — `(4,4)`, `(5,4)`, `(4,5)`, `(5,5)` at the default board size. Shed actions work from there even if the tile is locked.
- **Only `PICKUP`/`DROP` require shed adjacency.** Market orders — `BUY_SEED`, `BUY_PRODUCT`, `BUY_ANIMAL`, `SELL`, `HIRE`, `BUY_LAND` — execute from anywhere on the board (staff-confirmed). Don't waste farmer turns walking to the shed to trade.
- **Locked tiles are passable** — units can walk across unbought quadrants — but every tile action no-ops there.
- **Farm hands vanish at end of day** and must be re-hired every single day.
- **Planting more seeds of a kind than you hold plants none of them**, not as many as possible.
- A tile is `None` (empty), `"LOCKED"`, a plant dict, a weed dict, or a coop/pasture dict — check `kind` before assuming shape.
- Shed capacity is 100 non-seed items; overflow at any point is discarded with no buffer.

## Repo conventions

- `docs/kaggriculture_context.md` is read-only research material; update it only if the competition rules themselves change.
- Don't commit replay JSONs (~4.9 MB each).
