# Brief for Peter: final uploads, 29-30 September 2026

From Stephane (with Claude). Deadline: 30 September 23:59 UTC (02:59 on 1 October, Nairobi).

## The one-line version

Upload Step1009 under Stephane's two final names, Washamba Bots V1 and Nikaangukia Meroni (Nikangu Kia Meroni), this evening, then stop.

## Why (MEASURED)

- Your `agents/w3_dp_saletiming.py` is byte-identical to tetsutani's Step1009 (sha256 starts 55be5d5f124c8daa), so the current active pair (your DP-B and Stephane's `tetsu_step1009_full.py`) is one agent twice; their ratings (about 1,968 and 1,762) differ only by ladder noise.
- Step1009 is the strongest agent we have: 0.855 of points on the 221-game band panel (W6 0.670, W3 0.604); 28-4 against W6 and 16-0 against the W3 + DP rebuild on paired seeds; 34-12-2 in its first 48 ladder games with no errors or timeouts.
- About a dozen Step1009 variants were tested on 28-29 Sep (lead-selling off or wider, a mirror-aware selector, four final-day selling changes, and Fable's herd changes and front-running graft): none beat Step1009 out of sample. Copies of Step1009 tie each other, and every deviation tried loses those mirrors.

## Files

- `submissions/nikangu_kia_meroni.py`: Step1009 with a three-line Washamba header on top; behaviour identical (sha256 aeb47c2c02734596, entrypoint `step1009_step1008_fortyfirst_final_fixedsell_closure_agent`). Stephane may upload this one tonight as a test.
- For Washamba Bots V1: the same Step1009 bytes (your `agents/w3_dp_saletiming.py` or `tonight_0928/tetsu_step1009_full.py`, sha256 55be5d5f124c8daa), or the Nikangu file with its header changed.

## Before each upload

1. sha256 matches the file above.
2. Self-play seed 0 finishes DONE/DONE; the last callable is the step1009 entrypoint.
3. Timing: whole game about 3 s of compute; slowest turn measured 0.28 to 0.66 s locally (under the 1 s limit, plus the 60 s overage bank; no timeouts in 106 ladder games of the two copies).

## Order and slots

- Each upload retires the older active agent. Two uploads leave exactly the two finals active.
- Upload both this evening so their young ratings get games before the deadline; ratings start near 600 and climb, so a low reading after two hours means nothing.
- No uploads after the finals unless one fails validation; fix and re-upload before 20:00 UTC on 30 September.

## Only open question

Sonnet is checking whether tetsutani has published a step newer than 1009 (`SONNET_NEWSTEP_0929.md`). If one exists, Claude tests it against Step1009 on 32 paired games; it replaces Step1009 only if it clearly wins. Details: project doc `claude/results-2026-09-28.md`.
