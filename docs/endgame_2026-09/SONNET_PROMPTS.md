# Sonnet prompts, 23 September 2026

Run these in order in VS Code, in your `washamba_bots` checkout. Everything they need is already on your Mac under `~/KagricultureLocalData/`.

**Before you start:** the two submission files in `~/KagricultureLocalData/submissions/` are ready to upload to Kaggle as they are. You don't need to wait for Sonnet to upload them. Upload `w0_v15stack_control.py` first, then `w1_v15stack_race44.py`, so they become your two active submissions.

---

## Prompt 1: bring the v15stack base and the harness into the repo

```
Create a new branch `agent/v15stack-base` from main.

1. Copy these files into the repo, byte for byte (do not reformat, do not edit):
   ~/KagricultureLocalData/submissions/w0_v15stack_control.py -> agents/w0_v15stack_control.py
   ~/KagricultureLocalData/submissions/w1_v15stack_race44.py  -> agents/w1_v15stack_race44.py
   ~/KagricultureLocalData/agents/v57/main.py                 -> agents/public/v57.py
   ~/KagricultureLocalData/agents/k0013/main.py               -> agents/public/k0013.py
   ~/KagricultureLocalData/harness/pool_harness.py            -> experiments/pool_harness.py
   Fieldcraft needs two files in one folder:
   ~/KagricultureLocalData/agents/fieldcraft/main.py and mirror_plan.py -> agents/public/fieldcraft/

2. Verify the two submission files with sha256sum; they must match:
   w0_v15stack_control.py 73a70c4353ae92ce1e38a4075bbd983afa04eebba7caf6e7c28eafda43fef2a4
   w1_v15stack_race44.py  91b258ae8c39d8dfea1414e18c98144bb5034a3fc10dda2776f0bf5d86196dff
   If either differs, stop and tell me.

3. Make sure a Python 3.11+ virtual environment has kaggle-environments==1.32.7 installed
   (pip install kaggle-environments==1.32.7). Confirm the version with importlib.metadata.

4. Sanity-check the engine config: play 'starter' vs 'pass' with kaggle_environments.make('kaggriculture').
   Banks should be about [3506, 3000]; if the second number is not 3000 the config is wrong, stop.

5. Add a short section to agents/README.md: W0 is the public "kaggriculture v15stack" notebook by wzhengbiao
   (Apache-2.0), unchanged; W1 is the same file with one change, V9_RACE_DEFAULT 40 -> 44. The public agents under
   agents/public/ are Apache-2.0 notebooks (v15stack by wzhengbiao, V57 by Ahmed Berat Ozer, K0013 by
   ghazarosghazaros, Fieldcraft by hakdevelopment); keep all license headers inside the files.

Do not submit anything to Kaggle. Do not push yet. Show me git status and the sha256 check when done.
```

## Prompt 2: rerun the gate on your machine (uses all your cores)

```
Using experiments/pool_harness.py, run two gates and save the raw output under results/2026-09-23/.
Use --workers equal to (CPU cores - 1).

Gate A (mirror): W1 against W0 on fresh seeds 1001-1060, both seats (120 games):
python experiments/pool_harness.py \
  --agent w0=agents/w0_v15stack_control.py --agent w1=agents/w1_v15stack_race44.py \
  --candidates w1 --opponents w0 --seeds 1001-1060 --out results/2026-09-23/gate_a_mirror.jsonl

Gate B (pool): W0 and W1 against V57, K0013 and Fieldcraft on seeds 1101-1112 (both seats):
python experiments/pool_harness.py \
  --agent w0=agents/w0_v15stack_control.py --agent w1=agents/w1_v15stack_race44.py \
  --agent v57=agents/public/v57.py --agent k0013=agents/public/k0013.py \
  --agent fieldcraft=agents/public/fieldcraft/main.py \
  --candidates w0 w1 --opponents v57 k0013 fieldcraft --seeds 1101-1112 \
  --out results/2026-09-23/gate_b_pool.jsonl

Then write results/2026-09-23/GATES.md with: the W-L-T table printed by the harness, points share, mean margin,
any game that did not finish DONE, and a one-paragraph plain-English reading. Do not round away ties; a tie is
half a point. Do not change either agent file.
```

## Prompt 3: commit and push

```
Commit on agent/v15stack-base with the message
"Add v15stack base (W0), race44 candidate (W1), public pool agents and pool harness; gate results 2026-09-23".
Push the branch and open a PR to main titled "v15stack base + race44 candidate". In the PR body paste GATES.md.
Do not merge.
```

## Prompt 4: next candidates (for later today, one change at a time)

```
On a new branch agent/v15-sweep from agent/v15stack-base, build these single-change variants of
agents/w1_v15stack_race44.py (each changes exactly one constant; check the string occurs exactly once before
replacing). Put them in agents/sweep/:
  a) V9_RACE_MARGIN = 12 -> 10
  b) V9_RACE_MARGIN = 12 -> 14
  c) V9_CARROT_RATIO = 1.8 -> 1.6
  d) V9_HERD_MIN_WOOL = 150 -> 130
  e) V9_HERD_MIN_MILK = 150 -> 130

Rules, because picking the best of several on the same seeds inflates the result:
- Screen each variant against W1 on seeds 2001-2024 (both seats).
- Only a variant with points share >= 0.55 in the screen goes to confirmation.
- Confirm on fresh seeds 3001-3060 against W1, and seeds 3101-3112 against W0, V57, K0013 and Fieldcraft.
- Promote only if the confirmation points share against W1 is >= 0.55 and it loses no more games to the pool
  than W1 does.
Write results/2026-09-23/SWEEP.md with the screen table, the confirmation table, and which (if any) passed.
Do not submit anything.
```
