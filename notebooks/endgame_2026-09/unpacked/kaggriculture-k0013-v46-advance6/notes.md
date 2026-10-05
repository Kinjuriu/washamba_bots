# ---- cell 0
# Kaggriculture: K0013 — V46 + earlier ready-stock sales

This notebook packages the **selected live submission** from
[our submissions page](https://www.kaggle.com/competitions/kaggriculture/submissions):
ref [`56306096`](https://www.kaggle.com/competitions/kaggriculture/submissions) scored **2644.2**
public Bradley–Terry skill on 2026-09-17.

The ladder is matchmaking, not a fixed dataset. The same bytes can print a different
skill on a later requeue (K0013 re-rolls: 2499.6 / 2109.8 / 1342.6 / 1200.4). That is
opponent-pool variance, not a new tape. The selected peak remains **2644.2**.

**Copy & Edit → Run All → Save Version.** Run All writes `main.py` and a deterministic
`submission.tar.gz`. It does not submit. Attach the output archive on the competition
submit form if you want a scored copy.

## What this agent is

Parent: Ahmed Berat Özer **V46** (published, Apache-2.0) — Shop0909-line tapes, V46
opening `[BUY WHEAT 7, SELL WHEAT 2]`, CARE / fruit / herd floor already in the parent.

Leftover (this copy only): Alperen [`ready-stock-earlier-sales`](https://www.kaggle.com/code/alperen5252525)
`_ADV_LOOK` **3 → 6**. Ready stock may be sold up to six turns earlier. No slack-lift,
no K0011 race-lead, no V47 herd lockstep, no V48 queue-clear.

`main.py` sha256 `45628c719dc967f81655c19f70e579c55a5758b9fe75a5fcdad9193eebf6a017` (337 376 bytes). Same bytes as the 2644.2 archive.

## Live submissions this notebook is based on

Official public scores from this account (2026-09-18 dump). Latest-two seats rotate;
peak is what we keep selected.

| Ref | Date | Public | What it is |
|---|---|---:|---|
| **56306096** | 2026-09-17 | **2644.2** | **Selected.** V46 + `_ADV_LOOK=6` only |
| 56130016 | 2026-09-09 | 2564.8 | Seven-turn + JitRL on Shop0909 (previous floor) |
| 56079538 | 2026-09-07 | 2559.2 | Thomas public-state router fork |
| 56327693 | 2026-09-18 | 2499.6 | Same K0013 bytes, later skill |
| 56302215 | 2026-09-17 | 2496.0 | K0010: V46 + jaxa623 slack-lift |
| 56306101 | 2026-09-17 | 2419.0 | K0014: slack-lift-only on V46 |
| 56328366 | 2026-09-18 | 2109.8 | Same K0013 bytes, later skill |
| 56277076 | 2026-09-16 | 1600.2 | Seven-turn requeue (E5 variance) |
| 56305939 | 2026-09-17 | 835.2 | K0012 combo (advance6 **and** slack-lift) |
| 56302274 | 2026-09-17 | 125.4 | K0011 synthesis (priced-n / race-lead) |

Closed on this tape: mixing advance6 with slack-lift (K0012 835), K0011 synthesis,
planner/APC leftovers, and treating a warm 600 or a 1200 re-roll as a tape fail.

Promote a new leftover only if official public **≥ 2564.8**. Offline coins are not
a ranker.

## Credits

- Ahmed Berat Özer V46 and the Shop0909 / v31 chassis (Apache-2.0)
- Yusuke Hayashi shop-router routes
- alperen5252525 ready-stock-earlier-sales (`_ADV_LOOK`)
- jaxa623 2802 paper (slack-lift is **not** in this copy)
- aurax7, thomastschinkel, destbreso, tetsutani, prvsiyan, Dmitrii Gluzdov — retained
  notices in `main.py`

Engine: `kaggle-environments==1.32.7`. Scored box: CPU, no internet, `agent(obs)`.


# ---- cell 1
## Environment

Pin the engine used for these live scores.


# ---- cell 4
## Selected agent

Collapsed `main.py` is the exact K0013 file from submission `56306096`.


# ---- cell 6
## Pack `submission.tar.gz`

Single-root `main.py`. Stored gzip so the bytes do not depend on zlib.


# ---- cell 8
## Load check

Confirms `agent` imports. Not a leaderboard forecast.
