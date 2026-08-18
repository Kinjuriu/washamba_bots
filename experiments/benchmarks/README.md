# benchmarks/

Deliberately empty. The actual benchmark/evaluation-harness scripts
(`benchmark.py`, `head_to_head.py`, `ladder_episodes.py`, `market_probe.py`,
`paired_compare.py`, `seeded_batch.py`, `selfplay_bench.py`,
`replay_diagnostics.py`, `aggressive_opponent.py`) stay at `experiments/`
root, not here.

Why: they are tracked, actively-used tools, and root `CLAUDE.md`'s
Setup/commands section documents exact invocations against their current
paths (e.g. `experiments/paired_compare.py A.py B.py`,
`experiments/replay_diagnostics.py`). Moving them would silently break
every one of those documented commands for a purely cosmetic gain — see
`experiments/README.md`'s "Deliberately left in place" section for the
full reasoning.

This folder exists so the intended top-level layout is visible even
though nothing lives here today.
