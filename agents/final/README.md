# Washamba Bots: final agents (Kaggriculture 2026)

The two submissions active at the 30 September 2026 deadline.

| file | what it is | sha256 (first 16) |
|---|---|---|
| `nikaangukia_meroni.py` | tetsutani's public Step1009 agent (Demand-Preserving Turn Sale Timing, Apache-2.0), unchanged apart from a Washamba header | see `sha256sum` |
| `washamba_bots_v1.py` | Step1009 plus a 2-day wheat purchase cap, switched off against exact copies of Step1009 | 96737e64f3298708 |

Local evidence for V1 (30 Sep): band panel 0.896 vs Step1009 0.856 (222 recorded ladder games, 9 better, 0 worse);
37.0 vs 35.0 points on Step1009's 48 replayed ladder games; 16 ties against Step1009. Full log:
`docs/endgame_2026-09/RESULTS_2026-09-28.md` (copy in `experiments/endgame_2026-09/tonight_0928/`).

`LICENSE.txt` and `NOTICE.txt` are the upstream Apache-2.0 licence and notices that ship with Step1009.
