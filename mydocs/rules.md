# Rules — quick index (personal, not shared)

Thin pointer file. No content is duplicated here — read the line, don't trust
this summary of it. Everything below is a `file:line` into the repo as of
`d88e225`/`34696c2` (2026-08-16); re-check line numbers after any edit to
`main.py`, they drift.

## Process (already documented in full — don't re-derive)

- Experiment loop (OBSERVE→NEW CHECKPOINT), comparison-harness table,
  checkpoint table: `docs/CHECKPOINTS.md:26-146`
- Team workflow, evidence standard, PR gate, submission etiquette, Kaggle
  team-merge deadline: `CONTRIBUTING.md`

## Sources of truth (priority order)

`CLAUDE.md:100-116` — engine (`.venv/Lib/site-packages/kaggle_environments/envs/kaggriculture/kaggriculture.py`)
beats `docs/kaggriculture_context.md` beats root `README.md`. Pin
`kaggle-environments>=1.32.6` — `CLAUDE.md:116`.

## Hard constraints (silent breakage if violated)

`CLAUDE.md:202-211` — single `main.py` entrypoint / 100 MiB, 1s/turn +
60s overage bank, no network I/O, 8GiB/6.5GiB RAM/1.6 vCPU, 10 market
orders/turn cap, only WHEAT+FERTILIZER buyable back, 5 submits/day (latest
2 active).

## Agent I/O contract

`CLAUDE.md:213-231` — entrypoint = last callable in module, not name
`agent` (`kaggle_environments/agent.py:64`); keep `agent = nikaangukia_meroni`
last in `main.py:1502`. A local score of exactly $3000 = agent never acted.

## Mechanics an agent must get right

`CLAUDE.md:233-239` — watering/feeding 2-miss death, no grace period on
fresh plantings, fertilizer multiplies watering (doesn't replace it), CARE
bank payout rule, sell-price-pre/buy-price-post concurrency, hiring fib cost.

## Silent-failure gotchas

`CLAUDE.md:241-249` — `tiles[y][x]` row-major vs `farmer`/`hands` `[x,y]`;
shed isn't a tile (shed-adjacent = center 4 tiles); only PICKUP/DROP need
shed adjacency; locked tiles are walkable but inert; hands vanish nightly;
over-requesting seed plants **nothing** not "as many as held".

## Key tunable constants in `main.py`

- `SELF_SUPPLY_EXPONENT = 2.0` — `main.py:113` (raising it is a measured loss)
- `MAX_SELL_PER_TURN` — `main.py:162` (smaller MELON slices = measured loss)
- `SHED_FORCE_SELL_THRESHOLD = 70` — `main.py:174`
- `LIQUIDATION_START_DAY = 19` — `main.py:195`
- `HIRE_BEFORE_HOUR = 4` — `main.py:263`
- `WORK_TILES_PER_HAND = 6` — `main.py:278` (denser crew = measured loss)
- `ACTIVE_ANIMALS = ["GOOSE"]`, `MAX_ANIMALS = 1` — `main.py:305,312`
  (more animals = measured loss, see dead ends)
- `choose_crop` — `main.py:867`; `should_sell` — `main.py:978`;
  `choose_unit_action` — `main.py:1144`; `wants_fertilizer` /
  `find_fertilizer_target` — `main.py:389,432`

## Measured dead ends — don't re-run without changing something first

`CLAUDE.md:93-98` — more animals (2/3/4/6 all lose to 1 goose, `main.py:312`),
diversifying off melon (`SELF_SUPPLY_EXPONENT` 3/4/6 all lose, `main.py:113`),
smaller MELON sell slices (`main.py:162`), `BUY_LAND` (loses rich or poor),
denser crew (`WORK_TILES_PER_HAND=4`, `main.py:278`). Fertilizer round-trip
arbitrage: does not exist, structurally break-even — `CLAUDE.md:79-89`.

## Eval commands

`CLAUDE.md:187-196` — `seeded_batch.py` (broad, inflated), `paired_compare.py`
(farm/upkeep changes), `head_to_head.py` (anything touching selling, rule at
`CLAUDE.md:77`), `selfplay_bench.py` (the honest/ladder-predicting number),
`replay_diagnostics.py` (action histogram + end-state, found the weed
cascade).
