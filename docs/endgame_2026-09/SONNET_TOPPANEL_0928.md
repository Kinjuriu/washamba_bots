# Sonnet task, 28 September night: top-12 recording panel for Step1009 and W6

Run in VS Code in ~/KagricultureLocalData with .venv313/bin/python. No uploads. 2 workers only
(RAM). Runs about 45-60 minutes; it appends as it goes and can be restarted safely.

```
.venv313/bin/python harness/toppanel_mac.py episodes/20260928_ladder_check/toppanel.jsonl 2 \
    tetsu=tonight_0928/tetsu_step1009_full.py w6=submissions/w6_herdsafe_frontrun.py
```
(the replay paths in episodes/20260927T124109Z_top12_strat/nn_manifest.csv are relative to
that folder, e.g. replays/114062496.json.gz; tapeopp.py prints one JSON line per game.)

When done, write episodes/20260928_ladder_check/TOPPANEL.md: for each candidate, games run,
games where the recording stayed faithful (tape_bank within 5% of orig_tape_bank), wins, ties and
losses on the faithful games (win = ours_bank > tape_bank), and the same split by tape_rank 1-4
and 5-8. Tell Stephane when TOPPANEL.md is saved.
```
