# Sonnet prompts, Thursday 24 September 2026 (evening)

Run in VS Code from `~/KagricultureLocalData`. None of these submits anything to Kaggle. Run them in this order: A starts a long background job, so B and C can run while it works.

---

## Prompt A: the "RL test" as a black-box search over W3's constants (runs overnight)

```
Run a black-box search over the tunable constants of our W3 agent and report which settings,
if any, beat W3 on fresh seeds. Do not submit anything; do not edit files outside
~/KagricultureLocalData/harness/es_w3/.

Context: harness/es_search.py treats W3's market-race constants (V9_RACE_*, _V92_P_H/K, _HP_WINDOW,
V9_COURIER_FROM_HOUR) as policy parameters. It makes random variants of W3, screens them against an
opponent pool on a small seed block (both seats; win 1, tie 0.5), then replays the best 5 on fresh
seeds. Only the confirm stage counts; the screen is a noisy filter.

1. Use the Python that has kaggle-environments==1.32.7 (check importlib.metadata.version). Run
   `python -c "import os;print(os.cpu_count())"` and use cores - 1 workers.
2. Time ONE game first:
     cd harness && time python play.py ../submissions/w3_herdsafe2700.py ../submissions/w1_v15stack_race44.py 5001
   (if play.py takes different arguments, read it and adapt). Call the time T seconds.
3. Choose --n so that the screen, (n+1) x 3 opponents x 4 seeds x 2 seats games, takes about
   5 hours with the workers you have: n = 5*3600*workers / (24*T) - 1, capped at 60, at least 20.
   Tell me n, T and the expected screen and confirm hours before starting.
4. Start it in the background from harness/:
     nohup python es_search.py --base ../submissions/w3_herdsafe2700.py \
       --opp w3=../submissions/w3_herdsafe2700.py \
       --opp w1=../submissions/w1_v15stack_race44.py \
       --opp hsv3=../agents/herdsafev3/main.py \
       --screen-seeds 5001-5004 --confirm-seeds 6001-6020 --n <n> --top 5 --workers <w> \
       --workdir es_w3 --out es_w3/results.jsonl > es_w3/run.log 2>&1 &
   Then check back with long sleeps (sleep 1800); don't print game logs into the conversation.
5. When run.log shows the CONFIRM table, write es_w3/REPORT.md (plain English, under 600 words):
   - the confirm table: base and top 5, points share, mean margin, per-opponent points, parameters;
   - for each candidate, points share minus base's points share, with the number of games;
   - count any rows in results.jsonl with "error" or ok=false.
6. If a candidate beats base on the confirm stage by at least 0.06 points share AND is not worse
   than base against any single opponent by more than 0.10, run a second confirm for base and that
   candidate only on seeds 7001-7030 against the same three opponents (use pool_harness.py or a copy
   of es_search's run function) and add the result to REPORT.md. Do not do anything else with it.
```

---

## Prompt B: GitHub, get PR #56 onto main and put our agents on a branch from main

```
Fix the repository state. Do not force-push and do not merge anything into main yourself;
open pull requests for Stephane to merge.

1. git fetch --all. Confirm that PR #56 was merged into agent/sell-price-floor, not main, and show
   `git log --oneline main..origin/agent/sell-price-floor`.
2. Open a PR from agent/sell-price-floor into main titled "Bring PR #56 (2945 Farm adoption and
   endgame research) onto main". If there is a conflict, it should only be .gitignore: resolve it on
   a new branch (merge-56-into-main) by keeping both sets of lines, with no duplicates, and open
   the PR from that branch instead. If any file other than .gitignore conflicts, stop and tell me.
3. Create the branch washamba/submissions-0924 from origin/main and add:
   - submissions/w0_v15stack_control.py, w1_v15stack_race44.py, w3_herdsafe2700.py (unchanged;
     sha256 prefixes 73a70c43, 91b258ae, 8bbf4a28; check them before committing);
   - harness/: play.py, pool_harness.py, tapeopp.py, top6panel.py, top6_panel.json,
     faithful_eps.json, panelsum.py, resim_trades.py, diag_products.py, es_search.py;
   - docs/SUBMISSIONS_2026-09-24.md listing each submission, its file, sha256 and ladder rating
     (W0 about 2,350 retired; W1 re-upload 2,155 active; W3 2,470 active; Peter's v3 retired).
   Do not commit replays, logs, episodes/ or anything over 5 MB other than the three submissions.
   If the submissions exceed GitHub's file limit, commit them gzipped with a one-line note.
4. Open a PR from washamba/submissions-0924 into main. Send me both PR links.
```

---

## Prompt C: our current games and the 2,900 band

```
Download and analyse games. Read-only research; no submissions, no git.

1. Our active submissions: the W1 re-upload (w1_v15stack_race44.py, uploaded 24 Sep) and W3
   (main.py = w3_herdsafe2700.py, uploaded 24 Sep). Resolve their submission IDs from our
   submissions list, matching by date and description, and print them. Also include the retired
   W0 (56487592) and first W1 (56491123) if their episodes are not already on disk.
2. Download every completed episode Kaggle exposes for them (paginate to the end, exclude
   validation), with a frozen manifest.csv written before downloading, into
   episodes/<UTC timestamp>_washamba_0924b/. Our own logs too; skip opponent logs (403).
3. Then run Prompt 1 from SONNET_PROMPTS_0924.md (leaderboard ranks 7 to 12), if not already done.
4. For W3 and the W1 re-upload, report: W-L-T; results by opponent rating band (below 2,000;
   2,000-2,500; 2,500-2,800; above 2,800); by opponent family (tape, DSM, Boey, other, using the
   fingerprints in SONNET_PROMPTS_0924.md prompt 1 step 3); ties and near-ties (|margin| < 500)
   against tape opponents.
5. For every W3 loss against an opponent rated above 2,500, run harness/resim_trades.py and list the
   three products where W3 lost the most revenue, and the day the opponent's bank first led by
   more than 3,000.
6. Write episodes/<timestamp>_washamba_0924b/report.md, plain English, under 1,500 words, with the
   tables and the clearest patterns. Label each claim measured or inference.
```
