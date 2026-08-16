# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

An agent for the Kaggle **Kaggriculture** simulation competition: two agents each manage a virtual farm over a 30-day season (720 turns, 24/day) and compete for the highest bank balance. There is no static train/test set — everything is scored via live episodes against other agents plus a final Bradley-Terry tournament.

**Current state:** `main.py` holds `nikaangukia_meroni` — a deterministic, rule-based agent (harvest → water → reclaim weeds via `DIG` → move-to-urgent → plant → walk → pass, plus threshold-based selling). One shared, inventory-aware `choose_unit_action` ladder drives the main farmer **and every hired hand**, with a per-turn claim set so units spread out instead of converging on the same tile.

The animal rollout is capped at **three geese** (`MAX_ANIMALS`): build coops, buy/pick up/place geese, feed and care for them, collect fertilizer, harvest eggs, and hold back a two-unit-per-animal wheat reserve so selling feed can't starve them. Three is the measured zero-escape sweet spot; four increased the mean slightly but produced escapes. The animal logic is data-driven off the engine's `ANIMALS` table, so cow and sheep need no new code — only a change to `ACTIVE_ANIMALS`.

`tests/` carries a stdlib-`unittest` suite. There is no `agent/` package — that part of the `README.md` layout is still aspirational. `experiments/` holds evaluation tooling (see below) and `notebooks/` has one working experiments notebook.

**Current local benchmark** (crop economics + goose, measured at `ebc8212`). Two separate tables, because they measure different things — **read the self-play one.**

Against the built-ins, 12 seeded 720-turn seasons each. **Inflated: these three never sell**, so the market stays pristine and our prices never meet a competitor.

| vs | mean | stdev | min | max | wins |
|---|---|---|---|---|---|
| `pass` | 41,969 | ±2,206 | 38,524 | 46,198 | 12/12 |
| `random` | 42,812 | ±1,926 | 40,929 | 45,922 | 12/12 |
| `starter` | 43,105 | ±1,740 | 40,949 | 46,028 | 12/12 |

Self-play, 6 seeds / 12 agent-results — **the ladder proxy**, and the number to quote:

| | mean | stdev | min | max |
|---|---|---|---|---|
| self-play | **31,132** | ±1,880 | 27,836 | 33,777 |

The ~15,000 gap between the two tables is the whole story of why a 33,000 local score became 289.3 on the ladder. Melon finishes near $280 against a built-in and at the **$1 floor** in self-play.

**The single biggest win was a scoring bug, not a strategy.** `choose_crop` subtracted an absolute oversupply term: `(price*yield - stock*price)/days`. Every product starts with market inventory of 10,000, so that term was not a tie-breaker — it *was* the score, collapsing to roughly `-price*10000/days`, which ranks crops by **cheapness**. Melon is the strongest crop in the game at 125.0 value per tile-day (wheat 37.5) and it scored dead last, so the agent planted wheat all season and never once planted a melon. Discounting glut *relative to the engine's `I0` baseline* took the mean from ~7,000 to ~28,800. Generalise it: **when a score mixes a revenue term with a penalty term, check their magnitudes against real game data, not just their signs.**

**Unsold inventory scores nothing** — only bank balance counts at turn 720. The shed used to finish pegged at its 100-item cap holding 95 melons, because price had drifted below a fixed sell threshold and the agent waited for a recovery the season had no time to deliver. Selling regardless of price from `LIQUIDATION_START_DAY` added ~4,400 and *narrowed* the spread, since the loss it removes concentrates in the worst seeds.

**Hiring is the single highest-ROI mechanic in the game, by a wide margin.** The n-th hire of a day costs `farmHandCostMult × fib(n)` with the counter resetting each morning, so four hands cost **$1+$1+$2+$3 = $7/day — about $210 for the whole season.** That bought roughly **+1,400 mean bank** (`pass` 5635 → 6864, `random` 5264 → 7357, `starter` 5555 → 6609). Hands are cleared every night, so re-hire each morning (`HIRE_BEFORE_HOUR`); a hand bought at hour 20 costs the same and does a fraction of the work.

The reason it pays so well is the same one behind the weed cascade below: **a single farmer's upkeep capacity is what caps income.** More units means more tiles watered and dug, while three Geese add a maintained animal revenue stream without the escape failures seen in the four-Goose experiment.

Two earlier fixes moved the **floor** rather than the mean: a **season-maturity gate** (`choose_crop` refuses crops whose `first_yield_day` can't land before day 29 — the agent used to bleed cash buying tomato seed it could never harvest) and a **shed-overflow valve** (force-sell once the shed passes `SHED_FORCE_SELL_THRESHOLD`, since overflow past 100 items is silently discarded).

**The weed cascade — fixed, and worth remembering.** The previous baseline lost to `pass` (an opponent that does nothing and banks $3000) on ~2/12 seeds, finishing *below* its own starting money. Root cause: one farmer planted more tiles than it could water, plants weeded out, and because the agent never emitted **`DIG`**, every weeded tile stayed dead for the rest of the season. The farm decayed to 23/25 weeds and sales starved to 3.9 `SELL` orders per season — zero on the losing seeds.

Adding `DIG` moved every metric at once: **SELL orders 3.9 → 22.9**, **end-of-season weeds 23.0 → 2.1**, and the sub-$3000 downside disappeared. The lesson generalizes: **tile upkeep capacity, not sell-price tuning, is what gates this agent's income.** Before optimizing thresholds, check how many tiles are alive at season end.

**A trigger keyed on a counter that its own action resets will oscillate.** The feed rule fired only when `consecutive_unfed >= 1` — i.e. only once the animal had *already* missed a meal. Feeding resets that counter, so the next day never looked urgent, and the agent settled into feeding every *other* day: exactly 15 meals in a 30-day season, stable and invisible. It cost more than a skipped meal. The Goose sat permanently one blocked turn from escaping for good, and most of the `CARE` bank was discarded — per `_daily_refresh_animals`, the bank only accrues on days the animal was **also fed**, and a production day that isn't fed throws the whole bank away unpaid. Feeding daily took `FEED` 15 → 30 and **EGG sold 26 → 52**. Bank deltas were inside stdev (a wash), so it ships for the risk, not the mean: **0 animal escapes across 48 episodes.** Generalise it: if the condition that triggers an action is the same state the action clears, check the duty cycle you actually get — don't assume it fires whenever it's needed.

**A green suite is not evidence the fix worked.** An earlier attempt at this same low `FEED` count batched wheat pickups, on the theory that a one-grain-per-trip shed round-trip was the bottleneck. Tests passed, the mean moved, and `FEED` stayed at **exactly 15** — the real cause was untouched. Always measure the specific counter the change was supposed to move.

Still unimplemented: `FERTILIZE` (see PR #5), `BUY_LAND`, cow/sheep (`ACTIVE_ANIMALS`), and shed transfers beyond the fertilizer/animal path.

**Count plants that *land*, not `PLANT` actions issued.** The engine drops **all** `PLANT` requests for a crop when a turn's demand exceeds held seeds (`kaggriculture.py:920-931`) — not just the excess — so five units picking melon while holding one melon seed plants nothing and burns five turns. This makes the raw `PLANT` count in an action histogram actively misleading. Seed 0 vs `starter`:

| build | requested | blocked | **landed** |
|---|---|---|---|
| `a0e9703` | 214 | 144 (67%) | **70** |
| `ebc8212` | 138 | 43 (31%) | **95** |

The daily-feed change *looked* like a 35% drop in planting and was in fact a 36% **rise** in plants landed. Still on the table: a per-turn seed budget shared across units, so a crop is only chosen while uncommitted seed remains — worth ~43 unit-turns a season now, down from 144. (An older review put the block rate at 93%; that was a different build.)

**Measured dead ends — don't re-run these without changing something first.** Both were plausible and both lost, twice each, on the full 12-seed batch:

- **`BUY_LAND` is a loss, even when rich.** Tested at a ~7k bank (mean roughly halved, win rate 12/12 → 6/12) and again at a ~29k bank where the $1k/$2k/$4k quadrants are pocket change (still ~2,000–2,900 worse). More ground spreads a fixed crew thinner, and melon needs sustained watering to reach full yield. **The crew, not the acreage, is the ceiling** — revisit only alongside a genuine upkeep increase.
- **A denser crew is a loss.** `WORK_TILES_PER_HAND` of 4 (about 6 hands) instead of 6 (about 4 hands) cost 1,300–3,400 depending on the era it was tested in. Surplus units don't idle politely: they plant tiles the crew then can't water, and spend seed money doing it.

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

The environment is already built at `.venv/` (Python 3.13.7, provisioned by `uv`). `pyenv` is not installed on this machine and the README's `pyenv` + `.venv/bin/activate` instructions do not work here — on Windows it's `.venv/Scripts/`.

For notebooks, select the **`Python 3.13 (washamba_bots)`** Jupyter kernel. Register it with `.venv/Scripts/python.exe -m ipykernel install --user --name washamba-bots --display-name "Python 3.13 (washamba_bots)"`. This matters: a kernelspec whose `argv[0]` is the bare word `python` (rather than an absolute path) launches whatever is first on `PATH` — which is how a notebook ends up on system Python reporting `No module named kaggle_environments` while the venv sits there working. For the same reason, use `%pip install` in notebooks, never `!pip install`: `%pip` targets the running kernel, `!pip` shells out to `PATH`.

**The team is split across macOS and Windows — never commit an OS-specific interpreter path.** Binaries live in `.venv/bin/` on macOS and `.venv/Scripts/` on Windows, so a hardcoded path breaks the other half of the team *silently*: VS Code falls back to the system Python, and every `import kaggle_environments` fails with "could not be resolved" while the venv sits there working fine. This already happened once via `.vscode/settings.json`. Let the Python extension auto-discover `.venv/`, and keep committed tooling path-agnostic (`sys.executable`, not a literal path).

```bash
# Recreate from scratch if needed
uv venv --python 3.13.7 .venv
uv pip install --python .venv/Scripts/python.exe \
  "kaggle-environments>=1.32.6" kaggle \
  numpy pandas matplotlib seaborn jupyterlab ipykernel

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

Unit tests only cover helpers in isolation. **The real verification for a strategy change is a seeded batch, never a single game.** Run-to-run spread is huge — the same `main.py` vs `random` matchup scored 5228 and 3776 on two unseeded runs. **Stdev scales with the score**: it was ~±600 at the ~5,000 era and is ~±1,600–2,200 now, so a "+1,000" on one seed is well inside noise. A single episode cannot tell an improvement from luck, and a one-off loss to `starter` means nothing.

Pass `seed` in the configuration to make episodes reproducible — but **only against `pass` and `starter`**. Verified: on a fixed seed, those two reproduce an identical final bank exactly, while `random` does not (5169 vs 5120 on the same seed). `seed` controls environment stochasticity — weed spawns, shop unlocks — not the built-in `random` agent's own RNG. The drift is ~1%, far inside its ±410 stdev, so the `random` column is still usable; just **A/B strategy changes against `pass`/`starter`**, where a difference is signal rather than opponent noise.

Compare a change against the same seed set:

```bash
.venv/Scripts/python.exe experiments/seeded_batch.py    # mean/stdev/win-rate vs all 3 built-ins
.venv/Scripts/python.exe experiments/benchmark.py       # adds melon_maxxer from the official notebook
.venv/Scripts/python.exe experiments/selfplay_bench.py  # both sides run main.py - the honest number
```

At ~7s per season, 12 seeds × 3 opponents is about 4 minutes. Report mean and win-rate, not a single score. `experiments/replay_diagnostics.py` breaks a single episode down by action histogram and end-of-farm state — that's what found the weed cascade. Replay JSONs it dumps are multi-MB and gitignored.

**The built-in opponents never sell anything, so every number they produce is inflated.** `pass`, `random` and `starter` leave the market at its pristine starting inventory all season, and our sales never compete with a rival's. Measured on the same agent: ~41,000 against the built-ins versus ~28,000 in self-play. Use the built-in batch to A/B a change (it is cheap and the seeds are fixed), but treat **`selfplay_bench.py` as the number that predicts the ladder** — it is the only local setup where a second trader is crowding the same order book. Its `end price` line is the tell: MELON finishes around $280 against a built-in and near the **$1 floor** in self-play, so any strategy that leans on premium-crop prices looks far better locally than it will score.

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
