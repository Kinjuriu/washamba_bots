# Sonnet prompts, Friday 25 September 2026

Run in VS Code from `~/KagricultureLocalData`. No Kaggle submissions, no git, no edits to existing agents. Claude has already put three new files in place:

- `submissions/w4_herdsafe_race48_hp6.py`: W3 with the two constants from the winning search candidate c042 (`V9_RACE_DEFAULT` 44 to 48, `_HP_WINDOW` 4 to 6) and an updated attribution header. Its sha256 starts with c5f8e1c2.
- `harness/es_search.py` (updated): new options `--space` (a JSON file of constants and choices), `--max-changes`, and a middle "halving" stage (`--halving-seeds`, `--halving-top`) that gives the best screened candidates more games before the confirm stage.
- `harness/es_space_gen2.json`: the generation-2 search space, centred on c042.

Run A and B at the same time if the Mac has the cores (split the workers), otherwise A first.

---

## Prompt A: wider gate for W4 against opponents the search never saw

```
Check that W4 (submissions/w4_herdsafe_race48_hp6.py) is not worse than W3 against opponents the
search did not train on. Read-only; write results under harness/gate_w4/.

1. Check the sha256 of W4 starts with c5f8e1c2, and that `diff submissions/w3_herdsafe2700.py
   submissions/w4_herdsafe_race48_hp6.py` shows only the header and the two constants.
2. From harness/, run pool_harness.py with W4 and W3 both as candidates against:
   w0=../submissions/w0_v15stack_control.py, w1=../submissions/w1_v15stack_race44.py,
   v57=../agents/v57/main.py, k0013=../agents/k0013/main.py, fieldcraft=../agents/fieldcraft/main.py,
   hsv3=../agents/herdsafev3/main.py, farm2945=../agents/farm2945/main.py (check the path),
   and w3 as an opponent for w4 (the mirror).
   Seeds 8001-8020, both seats, cores - 1 workers, output gate_w4/pool.jsonl. Run it in the
   background with nohup and check back with sleep 1200.
3. Write gate_w4/REPORT.md: for each opponent, W4's points share (win 1, tie 0.5), W3's points share,
   the difference, mean margins, and the number of games. Count any errors or non-DONE statuses and
   the slowest average seconds per turn for W4.
4. Verdict line at the top: PASS if W4 is not below W3 by more than 0.10 against any single opponent
   and its overall points share is at least W3's; otherwise FAIL, naming the opponent.
```

## Prompt B: generation 2 of the search, centred on W4

```
Run generation 2 of the black-box search with W4 as the new base. Read-only apart from
harness/es_gen2/.

From harness/, in the background:
  nohup python es_search.py --base ../submissions/w4_herdsafe_race48_hp6.py \
    --space es_space_gen2.json --max-changes 3 \
    --opp w4=../submissions/w4_herdsafe_race48_hp6.py \
    --opp w3=../submissions/w3_herdsafe2700.py \
    --opp w1=../submissions/w1_v15stack_race44.py \
    --opp hsv3=../agents/herdsafev3/main.py \
    --opp v57=../agents/v57/main.py \
    --screen-seeds 5101-5104 --halving-seeds 5105-5112 --halving-top 12 \
    --confirm-seeds 6101-6120 --n 80 --top 5 --workers <cores - 1> \
    --workdir es_gen2 --out es_gen2/results.jsonl > es_gen2/run.log 2>&1 &
Check back with sleep 1800. Do not print game logs.

When it finishes, write es_gen2/REPORT.md in the same format as es_w3/REPORT.md: the halving and
confirm tables, the difference from base in points share with game counts, per-opponent results,
and errors. Then:
- If a candidate beats base (W4) on the confirm stage by at least 0.06 points share and is not worse
  than base against any single opponent by more than 0.10, run a second confirm of base against that
  candidate on seeds 7101-7130 with the same five opponents, and add it to the report.
- Also list which constants appear in the top 12 of the halving stage and how often, so we can see
  which levers matter. Label that part inference.
```

## Prompt C: check the wheat finding before anyone acts on it

```
The 0924b report says W3 lost 284,220 of WHEAT sell revenue against 2,500+ opponents in its 17
close losses. SELL revenue alone can mislead, because some agents buy wheat and resell it (churn).
Read-only; use the existing replays in episodes/20260924T161358Z_washamba_0924b/.

For the same 17 losses, from harness/resim_trades.py output, report per side: wheat units sold,
wheat SELL revenue, wheat units bought, wheat BUY spend, net wheat cash (revenue minus spend),
wheat harvested from own tiles, and wheat fed to animals if available. Do the same for FERTILIZER.
Then say in one paragraph whether the wheat gap survives as a net cash gap, labelled measured.
Write it to episodes/20260924T161358Z_washamba_0924b/wheat_check.md.
```
