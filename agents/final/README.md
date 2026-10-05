# Washamba Bots: final agents (Kaggriculture 2026)

The two submissions active at the 30 September 2026 deadline.

| file | what it is | sha256 (first 16) |
|---|---|---|
| `nikaangukia_meroni.py` | tetsutani's public Step1009 agent (Demand-Preserving Turn Sale Timing, Apache-2.0), unchanged apart from a Washamba header | aeb47c2c02734596 |
| `washamba_bots_v1.py` | the file in the local submissions folder at the deadline: Step1009 with a Washamba header only (the wheat-cap file never replaced it on disk) | 97ecf538c0c26619 |
| `washamba_bots_v1_wheatcap.py` | the tested candidate: Step1009 plus a 2-day wheat purchase cap, switched off against exact copies of Step1009 | 96737e64f3298708 |

Local evidence for the wheat-cap version (30 Sep): band panel 0.896 vs Step1009 0.856 (222 recorded ladder games, 9 better, 0 worse);
37.0 vs 35.0 points on Step1009's 48 replayed ladder games; 16 ties against Step1009. Full log:
`docs/endgame_2026-09/RESULTS_2026-09-28.md` (copy in `experiments/endgame_2026-09/tonight_0928/`).

`LICENSE.txt` and `NOTICE.txt` are the upstream Apache-2.0 licence and notices that ship with Step1009.

Check which of the two V1 files went to Kaggle by comparing the submission's download with these hashes.
