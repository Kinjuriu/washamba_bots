# Kaggriculture Farming Agents

An autonomous agent for [Kaggriculture](https://kaggle.com/competitions/kaggriculture), a Kaggle simulation competition: two agents each run a virtual farm for a 30-day season (720 turns) and compete head-to-head for the highest bank balance.

This file is a map. The detail lives in the documents it links to.

| I want to… | go to |
|---|---|
| know what the current agent is and what it scores | [docs/checkpoints/V2-sheep.md](docs/checkpoints/V2-sheep.md) |
| prove a change is actually better | [docs/CHECKPOINTS.md](docs/CHECKPOINTS.md) |
| contribute, and not repeat our mistakes | [CONTRIBUTING.md](CONTRIBUTING.md) |
| understand the game's mechanics and traps | [CLAUDE.md](CLAUDE.md) |
| read the compiled competition rules | [docs/kaggriculture_context.md](docs/kaggriculture_context.md) |
| see how the agent is built | [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) |
| explore results and charts | [notebooks/washamba_bots_experiments_v0.ipynb](notebooks/washamba_bots_experiments_v0.ipynb) |
| follow the experiment protocol step by step | [docs/EXPERIMENT_WORKFLOW.md](docs/EXPERIMENT_WORKFLOW.md) |
| run an LLM-based experiment | [docs/LLM_EXPERIMENT_WORKFLOW.md](docs/LLM_EXPERIMENT_WORKFLOW.md) |

## Current checkpoint

**V2 sheep** — commit `93d6bed`, frozen 2026-08-16. Crop economics, a sheep, daily feeding, fertilizer, day-19 liquidation, a denser crew, and demand-aware crop scoring. Self-play **35,583**. Full record with every metric: **[docs/checkpoints/V2-sheep.md](docs/checkpoints/V2-sheep.md)**.

V2 is the **deterministic control**. New strategy work is measured against that frozen commit, not against whatever happens to be on `main` today — otherwise someone else's merge lands inside your delta and you cannot see it. A frozen checkpoint is never edited.

> **Kaggle ratings are secondary evidence, and a single reading means nothing.** Every submission is seeded at **600** before it has played a game, then drifts ±120. One measured trajectory on unchanged code: `600 → 708 → 572 → 489 → 548 → 472`. Read the local self-play number; let the ladder confirm direction over days, not hours.

## How we evaluate a change

Control versus treatment: both versions play **the same seeds**, and you compare them to each other — never a mean against the across-seed spread, which measures how much *seasons* differ from each other and cancels out anyway. That mistake caused us to reject two real gains.

```
OBSERVE → HYPOTHESIZE → FREEZE CONTROL → CHANGE ONE THING
   → TEST → SELF-PLAY → SEEDED BATCH → DIAGNOSTICS
   → COMPARE → DOCUMENT → SUBMIT → NEW CHECKPOINT
```

Pick the harness by what you changed:

```bash
# farm upkeep, planting, movement, animals — paired, same seeds
.venv/Scripts/python.exe experiments/paired_compare.py /tmp/base_main.py main.py

# anything about SELLING — needs a contested market to be visible at all
.venv/Scripts/python.exe experiments/head_to_head.py variant.py main.py

# the headline number
.venv/Scripts/python.exe experiments/selfplay_bench.py

# wide regression sweep (inflated, but cheap)
.venv/Scripts/python.exe experiments/seeded_batch.py
```

**The built-in opponents never sell**, so they leave the market pristine and flatter us badly — and on selling changes they can point the *wrong way*, not merely overstate. Full reasoning and worked examples: [docs/CHECKPOINTS.md](docs/CHECKPOINTS.md).

Experiments — including the ones that lost — are recorded in [CLAUDE.md](CLAUDE.md) under "measured dead ends". **A negative result is worth as much as a feature, and only if it's written down.**

Deterministic and LLM experiments differ, and no LLM experiment has been run here yet — see [docs/EXPERIMENT_WORKFLOW.md](docs/EXPERIMENT_WORKFLOW.md) and [docs/LLM_EXPERIMENT_WORKFLOW.md](docs/LLM_EXPERIMENT_WORKFLOW.md).

## Repository layout

```text
washamba_bots/
├── main.py                     # The agent. This single file IS the submission.
├── tests/                      # stdlib-unittest cases for main.py's helpers
├── experiments/                # Evaluation tooling
│   ├── paired_compare.py       #   A/B two versions over one seed set
│   ├── head_to_head.py         #   two agents in one contested market
│   ├── selfplay_bench.py       #   the honest headline number
│   ├── seeded_batch.py         #   mean / stdev / win-rate vs the built-ins
│   ├── benchmark.py            #   adds melon_maxxer from the official notebook
│   ├── replay_diagnostics.py   #   action histogram + end-of-farm state
│   └── market_probe.py
├── notebooks/                  # Experiments notebook (charts, diagnostics)
├── docs/
│   ├── CHECKPOINTS.md          #   how we freeze, measure and compare
│   ├── checkpoints/            #   the frozen records themselves
│   ├── ARCHITECTURE.md         #   agent anatomy and repo structure
│   └── kaggriculture_context.md#   compiled competition reference
├── CLAUDE.md                   # Mechanics, gotchas, measured dead ends
├── CONTRIBUTING.md             # How we work; the silent-failure checklist
└── LICENSE
```

`main.py` is deliberately one file — the competition accepts a single `main.py` at the root, which avoids packaging a tarball. There is no `agent/` package.

> **The framework runs the *last callable in the module namespace*, not a function named `agent`.** A helper or class defined *below* the agent silently becomes the submission: the episode still reports `DONE`, every action is discarded, and the agent finishes on exactly its starting $3,000. The file ends with `agent = nikaangukia_meroni` — keep that line last, and treat a local score of exactly $3,000 as "my agent never acted".

## Setup

We use [`uv`](https://docs.astral.sh/uv/) — it manages the interpreter itself, so no `pyenv` needed:

```bash
uv venv --python 3.13.7 .venv
uv pip install --python .venv/Scripts/python.exe \
  "kaggle-environments>=1.32.6" kaggle \
  numpy pandas matplotlib seaborn jupyterlab ipykernel
```

On macOS the interpreter is `.venv/bin/python` instead of `.venv/Scripts/python.exe`. **Don't commit either path** — the team is split across macOS and Windows, and a hardcoded interpreter path silently breaks the other half: VS Code falls back to the system Python and every `import kaggle_environments` fails while the venv sits there working.

`kaggle-environments>=1.32.6` is not optional. Staff shipped a mid-season balance patch (Town Center demand, shop sampling with replacement); anything older simulates different rules. The official starter notebook still pins `>=1.32.2` — don't copy that.

`requirements.txt` is a broad 190-package `pip freeze` from a wider ML workspace, not this agent's dependency set. Installing it wholesale isn't required.

### Notebooks

Select the **`Python 3.13 (washamba_bots)`** kernel. Register it once:

```bash
.venv/Scripts/python.exe -m ipykernel install --user \
  --name washamba-bots --display-name "Python 3.13 (washamba_bots)"
```

A kernelspec whose launch command is the bare word `python` starts whatever is first on `PATH` — which is how a notebook ends up on system Python reporting `No module named kaggle_environments`. Note this venv ships **no `pip`** (uv provisions it), so `%pip install` silently no-ops here; install from a terminal with `uv pip install` instead.

Generate a Kaggle API token at kaggle.com/settings/api, or run `kaggle auth login`.

## Running and testing

```bash
.venv/Scripts/python.exe -m unittest discover -s tests

# The pre-submit gate. Kaggle validates every upload with a self-play
# episode; a crash rejects the submission regardless of strategy.
.venv/Scripts/python.exe -c "
from kaggle_environments import make
env = make('kaggriculture', configuration={'episodeSteps': 720, 'seed': 0})
env.run(['main.py', 'main.py'])
print([s.status for s in env.steps[-1]])   # must be ['DONE', 'DONE']
"
```

Built-in opponents are `pass`, `random` and `starter`. A full 720-turn episode takes about 7 seconds, so hundreds of games is minutes, not hours.

## Submitting

**Announce in the team channel first.** We get 5 submissions/day and **only the latest 2 stay active** — an upload can silently evict a better agent, with no undo. Keep one slot as an unchanged control while evaluating a new agent. Full protocol: [CONTRIBUTING.md](CONTRIBUTING.md).

```bash
kaggle competitions submit kaggriculture -f main.py -m "message"
kaggle competitions submissions kaggriculture
kaggle competitions logs <EPISODE_ID> 0    # debug a failed validation episode
```

## Competition snapshot

| | |
|---|---|
| Prizes | $50,000 — 10 places × $5,000 |
| Entry & team-merger deadline | Sept 23, 2026 |
| Final submission deadline | Sept 30, 2026 |
| Scoring | Live episodes, then one final Bradley-Terry tournament |
| Entrypoint | `main.py` at root, or `.tar.gz` with `main.py` at root. Max **100 MiB** |
| Per-turn budget | **1 second**, plus a 60-second bank per episode |
| Per-episode compute | 8 GiB HDD, 6.5 GiB RAM, 1.6 vCPUs |
| Network | **None during an episode** — the agent sees only `obs` |

Everyone contributing here must be on the Kaggle team: private sharing of competition code outside your team is a rules violation, and the roster cannot change after Sept 23.

## License

**Code in this repository is CC BY 4.0**, matching the competition's requirement that winning submissions be released under that license. **The Kaggriculture environment and its game data are Apache 2.0** and are not ours. See [LICENSE](LICENSE).
