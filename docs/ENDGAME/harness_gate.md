# T3 — Replay-the-ladder harness: gate report

**Gate: PASS, 30 / 30 episodes reproduce the recorded bank exactly ($0 error, both seats).**
Bar was ≥ 27 of 30 within $1. Nothing was tuned to get there — the first episode tried
(`111577671`) reproduced to the dollar on the first run.

Date 2026-09-21. Engine `kaggle-environments` 1.32.7 locally; every replay in the set
carries `module_version: "1.32.7"`, so there is no engine drift to account for.

## What the harness is

Our ladder episodes are public replays. The engine's only stochasticity is
`random.Random((seed * 1_000_003) ^ day)` in `_end_of_day` (`kaggriculture.py:871`) —
weed spawns and shop unlocks — so **seed + both action streams fully determine an
episode**. A recorded opponent is therefore a fixed tape. Seat that tape in its recorded
seat on the recorded seed, seat our real agent file in ours, and the episode replays
exactly. That converts ~500 real contested games into a deterministic local test set,
which is the only harness we own with genuinely selling, genuinely strong opponents.

Files: `experiments/endgame/replay_tools.py`, `make_tape_agent.py`, `ladder_replay.py`,
`tests/test_endgame_replay.py`. Replays cache in `experiments/endgame/rep/` (gitignored).

```bash
.venv/Scripts/python.exe experiments/endgame/ladder_replay.py gate 30
.venv/Scripts/python.exe experiments/endgame/ladder_replay.py index
.venv/Scripts/python.exe experiments/endgame/ladder_replay.py run agents/<candidate>.py
```

## Where the seed lives — and why `configuration.seed` is null

`resolve_episode_seed` (`kaggle_environments/utils.py:199`) takes the seed from
`env.info["seed"]`, else `configuration["seed"]`, else a random 31-bit int — then
**deliberately scrubs it out of the configuration** so agents cannot read it from the
observation, and stores it on `env.info["seed"]` "so it persists into the replay".

So in every downloaded replay:

| field | value |
|---|---|
| `configuration.seed` | **always `null`** — scrubbed, by design, not a missing field |
| `info.seed` | the real seed (e.g. `116495659` for episode `111577671`) |

Passing it back as `configuration={'seed': N}` on a fresh env is equivalent: `env.info`
is empty on a fresh env, so the config value is promoted into it unchanged.

Two other replay-shape facts worth recording, both of which cost a debugging cycle:

- The replay's top-level `id` is a **run uuid** (`42f969a4-b5a3-11f1-…`), not the
  episode id. The episode id is `info.EpisodeId`.
- `kaggleusercontent.com/episodes/{id}.json` serves the replay **bare** — there is no
  `replay` wrapper field here, though `lossdiff.py` handles dumps that have one, so
  `parse()` unwraps a str-or-dict `replay` field if present and falls through otherwise.

## Index convention and seat

`steps[i][seat]["action"]` is the action decided **from `steps[i-1]`'s observation**.
Confirmed against a known constant rather than assumed: `router_yuan_nf`'s header
records that its step-0 order is `BUY_PRODUCT WHEAT 13`, and that order appears at
`steps[1][seat1]["action"]` in episode `111577671`. So `tape[k] = steps[k+1][seat].action`
is the action taken at observation step `k` (= `day*24 + hour`), and `tape[719]` is
`None` — no action follows the final observation.

Seat is taken from the ListEpisodes `index` field (**absent for seat 0** — protobuf
default, not zero) and cross-checked two ways on every episode: final-reward match, and
`info.TeamNames.index("washamba_bots")`. All three agreed on 30/30.

Actions are embedded **verbatim** — no canonicalisation. Market orders settle in
list-index lockstep, so sorting or de-duplicating them would change the episode. The only
normalisation is `None → {"farmer":["PASS"],"hands":[],"market":[]}`, plus
`router_surge`'s hand pad/truncate guard.

## The 30-episode set

The **15 most recent wins + the 15 most recent losses** across both live submissions
(`56202213` = `agents/router_yuan_nf.py`, 14 episodes; `56202203` =
`agents/router_yuan_nf_trim.py`, 16). No episode had a recorded reward of exactly 3000
and no status was anything but `DONE`.

| episode | sub | seat | seed | recorded | replayed | opp rec | opp replayed | W/L | |
|---|---|---|---|---|---|---|---|---|---|
| 110996585 | 56202203 | 1 | 1510410391 | 99362 | 99362 | 98248 | 98248 | W | ok |
| 111003172 | 56202213 | 1 | 113578973 | 93320 | 93320 | 90046 | 90046 | W | ok |
| 111123163 | 56202203 | 1 | 586250190 | 110506 | 110506 | 89710 | 89710 | W | ok |
| 111130830 | 56202213 | 0 | 2106803030 | 53131 | 53131 | 48630 | 48630 | W | ok |
| 111171646 | 56202203 | 0 | 1743031640 | 90527 | 90527 | 88781 | 88781 | W | ok |
| 111204048 | 56202203 | 1 | 1453577271 | 103589 | 103589 | 90216 | 90216 | W | ok |
| 111206985 | 56202213 | 1 | 1520736151 | 110619 | 110619 | 92762 | 92762 | W | ok |
| 111333851 | 56202213 | 1 | 605483202 | 141860 | 141860 | 139058 | 139058 | W | ok |
| 111348987 | 56202203 | 1 | 140347009 | 88278 | 88278 | 100384 | 100384 | L | ok |
| 111373751 | 56202213 | 0 | 1514305575 | 127487 | 127487 | 126021 | 126021 | W | ok |
| 111375573 | 56202203 | 0 | 1760789429 | 88089 | 88089 | 94747 | 94747 | L | ok |
| 111386927 | 56202203 | 0 | 1218691032 | 100584 | 100584 | 87680 | 87680 | W | ok |
| 111394601 | 56202213 | 1 | 889854809 | 118086 | 118086 | 122967 | 122967 | L | ok |
| 111407785 | 56202213 | 1 | 95126202 | 122777 | 122777 | 106645 | 106645 | W | ok |
| 111421353 | 56202213 | 1 | 964837676 | 93025 | 93025 | 92433 | 92433 | W | ok |
| 111425309 | 56202213 | 0 | 735168140 | 48827 | 48827 | 89355 | 89355 | L | ok |
| 111425762 | 56202203 | 0 | 167371723 | 101553 | 101553 | 98251 | 98251 | W | ok |
| 111433063 | 56202213 | 0 | 817761539 | 93133 | 93133 | 111757 | 111757 | L | ok |
| 111450117 | 56202203 | 1 | 127483718 | 96560 | 96560 | 109708 | 109708 | L | ok |
| 111465222 | 56202213 | 1 | 656535240 | 39488 | 39488 | 60518 | 60518 | L | ok |
| 111468533 | 56202203 | 1 | 1206285870 | 89741 | 89741 | 100792 | 100792 | L | ok |
| 111474079 | 56202213 | 1 | 112916447 | 104830 | 104830 | 118947 | 118947 | L | ok |
| 111478570 | 56202203 | 1 | 339150682 | 96502 | 96502 | 122941 | 122941 | L | ok |
| 111490728 | 56202203 | 0 | 1200979484 | 91142 | 91142 | 101198 | 101198 | L | ok |
| 111499902 | 56202203 | 1 | 1570037562 | 134764 | 134764 | 84238 | 84238 | W | ok |
| 111514681 | 56202213 | 1 | 1935863529 | 123608 | 123608 | 110329 | 110329 | W | ok |
| 111531881 | 56202203 | 0 | 857556051 | 86616 | 86616 | 104327 | 104327 | L | ok |
| 111554692 | 56202213 | 1 | 1690307195 | 79221 | 79221 | 117353 | 117353 | L | ok |
| 111566342 | 56202203 | 0 | 262077888 | 102003 | 102003 | 112306 | 112306 | L | ok |
| 111577671 | 56202203 | 1 | 116495659 | 72514 | 72514 | 92819 | 92819 | L | ok |

## `harness_index.json` — the farm-state facts T5 needs

`experiments/endgame/harness_index.json` (20 KB, not gitignored - commit it) carries, per episode:
recorded banks, seat, seed, win/loss, opponent submission id and rating — plus
PASTURE/COOP structure counts, how many hold an animal (`"animal" in tile`,
`kaggriculture.py:488`), and money, read from the **recorded** observations of our seat
at day 6, day 12 and end. Day *d* is probed at `steps[d*24]`, the first observation of
day *d* — i.e. *after* night *d-1*'s `_end_of_day`, which is where an unfed animal
escapes.

**A clean signal falls straight out of it.** Empty structures at end of season track the
result:

| empty structures at end | episodes | wins |
|---|---|---|
| 1 | 5 | 3 / 5 |
| 2 | 19 | 12 / 19 |
| 3 | 5 | **0 / 5** |
| 8 | 1 | **0 / 1** |

Every episode that finished with ≥ 3 empty pastures/coops was a loss — though that tail
is only **n = 6** (5 at three empty, 1 at eight), so read it as a target list, not a law.

### `111554692` traced, not inferred

The extreme case is **`111554692`** (sub `56202213`, seat 1, seed `1690307195`, 79,221
vs 117,353): 6 structures but only **4** filled at day 6, **10 of 17** at day 12, **10
of 18** at end — against a typical `6/6` and `13/15`. Money $137 at day 6 against a
typical $240–340, $5,222 at day 12 against a typical $12–16k.

Two mechanisms could produce that (a failed purchase, or an animal escaping at a night
boundary) and **both are present**. Walking the recorded tape's 11 `BUY_ANIMAL` orders
and checking the shed animal count on the next step:

| step | order | cost | money at top of turn | that turn's market | landed? |
|---|---|---|---|---|---|
| 1 | COW x2 | 800 | 2630 | SELL, **BUY_ANIMAL**, … | ok |
| 1 | SHEEP x2 | 1000 | 2630 | SELL, **BUY_ANIMAL**, … | ok |
| 65 | COW x1 | 400 | 126 | SELL, **BUY_ANIMAL** | ok |
| 88 | COW x1 | 400 | 60 | SELL, **BUY_ANIMAL** | **FAILED** |
| 150 | SHEEP x2 | 1000 | 2 | SELL, BUY_PRODUCT, BUY_LAND, **BUY_ANIMAL** | ok |
| 169 | COW x1 | 400 | 51 | HIRE, **BUY_ANIMAL** | **FAILED** |
| 176 | COW x1 | 400 | 208 | SELL, **BUY_ANIMAL** | **FAILED** |
| 195 | SHEEP x2 | 1000 | 277 | SELL, BUY_PRODUCT, BUY_SEED, **BUY_ANIMAL** | ok |
| 217 | SHEEP x2 | 1000 | 297 | HIRE, SELL, **BUY_ANIMAL** | **FAILED** |
| 241 | SHEEP x2 | 1000 | 1834 | HIRE, **BUY_ANIMAL**, BUY_PRODUCT | ok |
| 265 | SHEEP x1 | 500 | 8303 | HIRE, HIRE×6, BUY_LAND, **BUY_ANIMAL** | ok |

**Four `BUY_ANIMAL` orders failed outright — 5 animals never bought** — silently
(`money < price`, `_commit_unit`, no error raised). Separately, `filled` drops **4 → 3
between day 1 and day 2**: one animal also escaped at a night boundary. The two compound.

The table also confirms `ar2`'s own header: money at the *top of the turn* is not the
settlement condition — steps 65, 150 and 195 all succeeded at $126, $2 and $277 because
a `SELL` earlier in the same turn's order list funded them first. Which is why the
failures cluster on turns whose list is `[HIRE, BUY_ANIMAL]` or a SELL too small to
cover it.

**This is now reproducible deterministically at a single seed**, which is what the Sept
13 audit could not do. That is the T5 target list.

## `run()` demo — `ar2` against the `nf_trim` episodes

`ladder_replay.run(candidate, episodes)` reseats a candidate in our recorded seat with
the opponent's tape frozen. **Read the flips, not the mean:** once the candidate
diverges, the frozen opponent is playing a schedule it would not have played against the
new us, so mean Δ bank is an upper bound. The trustworthy signals are loss→win flips
and — the hard gate — whether any win flips to a loss.

`agents/router_yuan_nf_trim_ar2.py` is byte-identical to `router_yuan_nf_trim.py` unless
a scheduled `BUY_ANIMAL` would be unfunded in its own turn's order list. The number of
harness episodes where its actions differ *at all* is therefore itself the finding, and
the Sept 13 audit could not find one anywhere locally.

Run on all 16 `56202203` episodes in the harness:

| | |
|---|---|
| episodes | 16 |
| loss → win | **0** |
| win → loss | **0** |
| mean Δ bank | **0.0** — every episode reproduced its recorded bank to the dollar |
| episodes where any action differed | **1 of 16** |

**`ar2` fires exactly once in 16 real contested games, and in that one it cannot help.**
Episode `111478570`, step **169** (day 7, hour 1), and nowhere else in 11,504 agent
turns:

```
recorded  [["HIRE"], ["BUY_ANIMAL", "COW", 1]]
ar2       [["BUY_ANIMAL", "COW", 1], ["HIRE"]]
```

Money at that step is **$350**; a COW costs **$400**. The `HIRE` cost **$21** (measured:
money 350 → 329 across the step — a later, fib-priced hire of the day, not the $1 first
one), so the COW is unfunded in either order: the reorder is a genuine no-op and the
bank is byte-identical.
The shortfall is $50 of *real money*, not order position, and `ar2` deliberately touches
nothing upstream of the turn. Structures go `8 of 13 filled` into that step and `8 of 13`
out of it: the purchase silently no-ops (`money < price`, `_commit_unit`, no error).

That settles the Sept 13 question — the failure `ar2` was written for **is real and is
now reproducible at a fixed seed**, but `ar2`'s lever is the wrong one for it.

It also prices T5's "sell-to-fund" rule against the one case we can see: at step 169 the
shed holds **only 20 WHEAT** and nothing else (MELON, WOOL, MILK, EGG all at 0). A rule
that prepends a `SELL` of held **non-wheat, non-fertilizer** product would also have
emitted nothing here. Whatever T5 ships has to reach back further than the turn — this
turn had no funding available inside it.



## Caveats

- The harness measures **our real losses against the field we actually drew**. It does
  not measure what those opponents would do differently against a changed us. It is a
  regression net and a diagnosis tool, not a ladder predictor.
- `ListEpisodes` budget for this task was exactly 2 calls (`56202213`, `56202203`),
  both spent, no 429. Results cached in `experiments/endgame/episodes_<id>.json`
  (gitignored) — 247 and 255 completed episodes, 500 distinct, so the harness can be
  widened to ~500 episodes without another call.
- `experiments/endgame/rep/` is **5.4 GB** on disk (shared with T4's downloads) and
  gitignored. Replays are ~30 MB each and take ~10 s to fetch; downloaded at 6 threads, 30 replays
  in 277 s. A reproduce run is ~40 s per episode (episode ~7 s plus loading the 455 KB
  tape router), so the 30-episode gate is ~20 minutes.
