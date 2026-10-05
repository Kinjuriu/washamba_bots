# Kaggriculture: a replayable benchmark

**45,404 recorded matchups you can replay exactly**, each carrying the resolved
episode seed, the seat, the opponent's full 720-turn action stream, and the bank
both sides actually banked. Point your agent at one and you get a paired
comparison against ground truth: same seed, same seat, same opponent, one game.

Built from the public episode corpus
[`georgymamarin/kaggriculture-episodes`](https://www.kaggle.com/datasets/georgymamarin/kaggriculture-episodes)
by `research/build_benchmark.py`.

## Which file

| file | rows | what it is |
|---|---|---|
| `matchups_top.parquet` | 421 | **start here.** Behaviour-stratified within the strong field, opponents rated 2,000+ |
| `matchups.parquet` | 6,288 | behaviour-stratified across the whole field |
| `matchups_all.parquet` | 45,404 | everything replayable, unfiltered, so you can build your own selection |
| `engine_fixture.json` | 3 | tiny known-answer cases, to check your engine matches the recordings |

Six small result files travel with it so that the notebooks built on this dataset
have no numbers pasted into their cells. Fork one, re-run it, and the figures come
from here rather than from a string literal somebody typed:

| file | what it holds |
|---|---|
| `objective_calibration.json` | 14 opponents at 20 games each: mean margin, spread, predicted and observed win rate |
| `instrument_selftest.json` | a null, an identity, a known-catastrophe and a retrodiction, with their verdicts |
| `instrument_validation.json` | nine agents' ladder scores against what several offline instruments said about them |
| `ladder_forecast.json` | a rating band by episode, built from the trajectories of comparable submissions |
| `exact_replay.json` | 40 recorded matchups replayed at their own seed and seat: recorded bank, replayed bank, and whether the outcome came back the same |
| `instrument.json` | one run of the harness: what each gate checked, what it found, and what sample each measure declared it needed |

**`matchups_top` is the one most people want**, and the reason is the single most
surprising number here. Above 2,000 rating there are 23,151 matchups and only
**112 distinct opening behaviours**. Below it, a similar number of matchups holds
3,027. The strong half of this ladder is 27 times less diverse than
the weak half, so a benchmark stratified across the *whole* field spends most of
its rows on opponents you will never be matched against. `matchups.parquet` has
5,229 rows under 1,000 rating and 25 above 2,800; `matchups_top` has 87 above
2,700 out of 421.

## Schema

| column | meaning |
|---|---|
| `episode_id` | the Kaggle episode this came from |
| `seed` | the **resolved** seed, which is what reproduces weeds and shop draws |
| `your_seat` / `opponent_seat` | 0 or 1 |
| `opponent_team` | the recorded team name |
| `opponent_rating` | that seat's rating at the time |
| `recorded_bank_yours` | what the seat you are taking over actually banked |
| `recorded_bank_opponent` | what the other side banked |
| `opponent_behaviour` | a hash of the opponent's first 24 turns |
| `opponent_actions` | the opponent's full action stream, JSON |

## How to use it

```python
import json, pandas as pd
m = pd.read_parquet("matchups_top.parquet")

wins = 0
for r in m.itertuples():
    actions = json.loads(r.opponent_actions)
    bank = play(my_agent, opponent=actions, seed=r.seed, seat=r.your_seat)
    wins += bank > r.recorded_bank_opponent           # paired, against ground truth
print(wins / len(m))
```

Because the recording replays exactly, **the recorded bank is the baseline**: you
do not need to run a second agent to have something to compare against.

## Four things worth knowing before you trust a number from it

**The behaviour hash is 24 turns.** Hashing 200 turns of exact actions makes a
different weed into a different strategy. Measured on 2,400 seats sampled across
the whole corpus:

| prefix | distinct behaviours | share of seats |
|---|---|---|
| turn 24 | 462 | 19 % |
| turn 50 | 521 | 22 % |
| turn 100 | 585 | 24 % |
| turn 200 | 712 | 30 % |

So 24 turns clusters about **1.5 times harder** than 200, which is a real effect
and a modest one. The stronger reason is that 24 turns is the length at which
this fingerprint identifies the AGENT: longer prefixes drift towards one distinct
hash per seat, at which point they identify the episode instead.

Note the largest cluster barely moves across those cuts, 535 seats at turn 24 and
501 at turn 200. A fifth of the field is playing one stream deep into the game,
and no choice of prefix separates them because there is nothing to separate.

**Neither selected file is filtered to games anyone won.** 52 % of `matchups.parquet`
were won by the recording side. A benchmark built from your own past victories
cannot falsify a claim about being behind, which is the region a new candidate
most needs testing in.

**Bigger is not broader, and how much worse depends on where you sit.** Drawing
40 opponents at random from the whole field yields about **18** distinct
behaviours. Drawing 40 from inside one 100-point rating band, which is what
matchmaking actually gives you, depends entirely on the band:

| band you are matched into | 40 opponents are really |
|---|---|
| 600-700 | 34 |
| 1000-1100 | 30 |
| 1500-1600 | 8 |
| 2300-2400 | 7 |
| 2800-2900 | 6 |

Near the bottom a pool of forty is very nearly forty different opponents. From
about 1,500 upwards it collapses to single digits and stays there. Quote the
effective count for **your** band, never the row count, and never a single
collapse figure as if it were a property of the game.

**"Behaviour" here means an exact hash of the first 24 turns**, and every count on this page is in those units. Clustering by turn-by-turn agreement over the whole episode is a different and equally defensible definition that yields a smaller number, because it merges streams that diverge slightly. Pick one and stay in it.

**The source corpus is ordered by strength.** Spearman between row position and
mean seat rating in `replays.parquet` is **+0.552**: the first 2,000 rows have a
median rating of 712, the last 2,000 have 2,395, and the whole file has 2,002. If
you prototype on `head(N)` of the source you will profile the bottom of the ladder
while believing you are profiling the field. This benchmark samples by stride for
that reason.

## Caveats

The corpus is a crawl, so these are rates over what was stored rather than over
the ladder. 381 of 23,083 replays were dropped for carrying no resolved seed;
replaying those at seed 0 would be a different game wearing the same id.

## Licence

CC0. The recordings are Kaggle episode data; the selection and the schema are the
contribution here.
