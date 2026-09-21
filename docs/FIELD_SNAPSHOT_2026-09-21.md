# Field snapshot, 2026-09-21: the tapes are beaten, and the public frontier is 600 points above us

**For Peter and Stephane, from Billy.** Nine days to the final deadline. Everything
below was pulled on 2026-09-21 from Kaggle's public endpoints (leaderboard, per-submission
episodes, replays, notebook source). Scripts are in `experiments/field_research/`.
**Nothing has been submitted.**

## Where we are

Rank **1,491 of 9,771 at 2,144.7**. Active pair:

| submission | agent | rating | note |
|---|---|---|---|
| `56431632` | `washamba_base_v1.py` (Peter, 13:35 UTC) | 2,145, still settling | **not in the repo** |
| `56441221` | `atlas_profile.py` (Stephane, 18:36 UTC) | < 500 | banks ~42k, 4-4 vs opponents rated ~476 |

Atlas banks what the old `main.py` line banked. It does not lower the team score (best
of two), but it holds a slot. **The next submission evicts the OLDER of the two, which
is the 2,145 base, not Atlas** - check the pair before anyone submits.

## Why the tapes collapsed: same code, -1,000 points, engine unchanged

| agent | first run | resubmitted unchanged |
|---|---|---|
| `router_fam_yarn.py` | 2,722 (Aug 31) | **1,352** (Sep 9) |
| `router_yuan_nf.py` | 2,432 (Sep 3) | **1,298** (Sep 13) |

Ladder replays and local both report engine 1.32.7, so this is the field, not a patch.
`router_yuan_nf.py`, steady state:

| | our bank | opponent bank | opponent rating | win rate |
|---|---|---|---|---|
| Sep 3-5 (n=268) | 95,621 | 81,043 | 2,367 | 61% |
| Sep 13-21 (n=193) | 88,360 | **90,049** | **1,401** | 34% |

By mid-September a 1,400-rated opponent out-banks our best tape. The field forked
stronger public notebooks; a frozen tape cannot answer that.

## `washamba_base_v1.py` is a coin flip against its own field

84 episodes, opponents rated 2000+ (n=69): **31-32-6, median margin $0**, six exact ties.
From 32 replays: in ~25 the opponent plays our schedule action for action (unit-action
agreement 1.00 through step 400). In the 16 mirrors where we sell premium goods ~20-35
steps earlier than they do, we went **5-11**; in the 6 mirrors with identical timing the
results are +/-$60. n=16, so a hypothesis - but it matches Peter's own K=12 finding that
the lead has a cost. I could not match this agent to anything in `agents/` (<= 6%
agreement everywhere except 44% with `router_yhay.py` in the opening), so it cannot be
tested locally until it is pushed.

## What the top of the field does

Top teams vs opponents rated 2,700+:

| team | record | median margin | bank / opp bank |
|---|---|---|---|
| #1 DSM | 78-0 | +16,120 | 113k / 96k |
| #8 Kaggledew Valley | 45-1 | +12,331 | 114k / 100k |
| #3 Unknown Mother-Goose | 61-7 | +8,250 | 103k / 95k |
| #5 Vadim Vasilenko | 46-6 | +10,390 | 110k / 100k |

They are **not tapes**: across six games each, a top-8 team agrees with itself on 3-10%
of unit actions after step 144. Economy per game from 48 replays, top 8 vs us: geese
6-8 (6 of 8 teams) vs 2; tomato seed 10-20 vs 1; `FERTILIZE` 164-230 vs 117; fertilizer
*bought* 0-27 vs 83; idle `PASS` 148-176 for DSM/Vadim vs 551 for us; harvests 565 (DSM)
vs 483. (My SELL counts are requested orders, not landed trades - not quoted here.)

## The public frontier, measured

Best public notebooks by Kaggle's own best-score field: **V56 (ahmedberatozer) 2,771**,
"A Smaller Market Shock" 2,715, V55 / V47 2,686, Master Engine V3 2,661. V56's author
sits at **rank 179, 2,751**; their live submission after the opening burst is **31-10
(76%) against a field rated 2,658, median margin +$155**.

All decoded without executing the notebooks (AST parse of the payload literal, SHA-256
verified), scanned for I/O (none live), stdlib only. Round-robin, seeds 500-507, both
seats, contested market, 16 games per pairing - win count first:

| agent | W-L | win % |
|---|---|---|
| **V56** | **85-11** | **88.5** |
| Master Engine V3 | 77-19 | 80.2 |
| V55 | 71-25 | 74.0 |
| Farmer John and the Idle Seller | 55-41 | 57.3 |
| `router_fam_lead.py` | 32-64 | 33.3 |
| `router_fam_yarn.py` | 16-80 | 16.7 |

- Every public agent beats both of our routers **16-0**; V56's median margin over them
  is **+22,236** (e.g. seed 500: 160k vs 137k). All 96 of V56's games ended `DONE/DONE`.
- V56 beats V55 **12-4** and Master V3 **11-5** by a median of ~$155. V55 vs Master V3 is
  9-7, median $1. Seat 0 won 22 of 48 games among the three - no seat bias visible.
- Raw results: `experiments/field_research/rr_results.jsonl` (includes 96 void rows for
  "A Smaller Market Shock": it banked exactly $3,000 = never acted, a decode fault on my
  side, not a result).

## Caveats

- 16 games per pairing supports "V56 is at least as good as its siblings", not the 12-4.
- The panel is one lineage plus our tapes. It says nothing about the private top-10.
- `washamba_base_v1.py` is not in the comparison because it is not in the repo.
- V56's source declares Apache-2.0 with upstream notices retained; **the licence field
  on the notebook page still needs a human read** before a derivative is submitted.

## Proposal

This is the move that paid twice before (v16 -> v20, Moon -> router): change the base.

1. Peter pushes `washamba_base_v1.py`; run it in the same round-robin.
2. If V56 still leads, submit it **unmodified** once to find where it lands, per the
   `route_v20.py` protocol - timed so it evicts Atlas, not the 2,145 base.
3. Tune on top. V56 re-plans every turn, so unlike a tape it can take overlays. First
   candidates: the near-tie sell race (games at this level are decided by ~$150), then
   the geese / tomato / fertilize-own-crops profile of the top 8.

Reproduce: `python experiments/field_research/fetch_public_v56.py`, then
`python experiments/field_research/round_robin.py 8 6`.
