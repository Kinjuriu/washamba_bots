# What is actually inside the v20 route

Read from the decoded source (`python experiments/route_v20.py`, then read
`experiments/.v20_agent.py` — gitignored, never committed). 1,012 lines, 42
top-level functions, 44 constants. Apache 2.0.

Its own docstring: *"BL-MDgogo-10C4S-R0: public-replay consensus route with
generic execution guards. This is a behavioral reconstruction from twelve public
traces, not either team's hidden source policy."*

**`salemali7`'s "3094 score" notebook decodes to a source with the same opening
docstring.** They are the same lineage; v20 is 148 KB against its 62 KB, and
beats it 16-0 head to head. Treat "new notebook" and "new route" as different
claims.

## Shape

A fixed 720-step recorded route, wrapped in a stack of guards. `agent()` applies
them in a fixed order:

```
_kawa_actions      -> pick one of five routes
_weed_repair_action
_v17_feed_guard    -> DISABLED (_V17_FEED_GUARD = False)
_v17_room_evac
_repay_shift       -> give back what preemption borrowed
_rank_sell_slots   -> order the <=10 market slots by price impact
_preempt_shift     -> THE MIRROR TIEBREAK (see below)
_v17_r5_counter
_v17_md_counter
_v17_room_guard
_terminal_liquidation
```

## Five routes, chosen by the first three shop unlocks

`_kawa_route_label` reads `obs["town"]["unlocked_shops"]`:

| condition | route |
|---|---|
| `YARN_STORE` is first | `6c12s_4q_first_yarn` |
| `YARN_STORE` in first 2 | `6c12s_4q_second_yarn` |
| `YARN_STORE` in first 3 | `6c8s_3q` |
| a milk shop (PIZZA/ICE_CREAM/SMOOTHIE) in first 3 | `10c4s_3q` |
| otherwise | `8c6s_3q` (default) |

The names encode herd and land: `6C12S_4Q` is **6 cows, 12 sheep, 4 quadrants**.
So the top of this meta runs up to **18 animals on 100 tiles**. Our own agent
tops out at 4 animals on 75, and `CLAUDE.md` records a hard cliff at 5 animals
that we never explained. These routes do not hit it, which means the cliff was
a property of *our* economy, not of the game.

There is also `_kawa_use_legacy_layout`, which between steps 24-72 fingerprints
the opponent's tiles and switches to a parallel set of five legacy routes if it
sees **exactly** `{WHEAT 5, MELON 5, COW 1, SHEEP 4, PASTURE 0}` and money <= 12.
That is a hard-coded counter to one specific opponent build.

## `_preempt_shift` is the same mechanism we spent a day tuning on v16

It pulls premium sells forward, then `_repay_shift` cancels the same volume at
the original step — volume-neutral, timing-only. Exactly the shape of v16's
`_front_run`, with two differences that matter:

1. **It is clone-gated.** It only fires when `_clone_distance(obs) <= 6`, where
   the distance compares hand count, quadrants owned, and per-crop/per-animal
   tile counts between the two public farms. Against a non-clone it does
   nothing. This is a sharper version of the thing we discovered from our own
   ladder record — that 80% of our matches were mirrors decided by a rounding
   error — and they built the gate for it.
2. **It has no clobbering bug.** `if state.get("due") ... return action` blocks a
   second preempt while one is pending, which is precisely the per-step ledger
   we independently built and measured as inert on v16.

**The lead is still 1.** `_future_sells` reads `step + 1` and `due_step` is set to
`step + 1`.

That is the transfer. On v16 we measured lead 1 -> 3 at **+1,646 (8/8)**, and
then per-item (STRAWBERRY 6, WOOL 6) at a further **+1,306, 23/24**. `_PREMIUM`
here is the identical four items — `("STRAWBERRY", "MELON", "MILK", "WOOL")`. The
same edit applies: make `_future_sells` look ahead per item and set `due_step`
to match.

## Untouched tunables, in rough order of promise

| constant | value | note |
|---|---|---|
| lead inside `_future_sells` / `due_step` | **1** | the one we already know moves |
| `_PREEMPT_MAX_BATCH` | 12 | our v16 volume sweep was inert because stock-bound; this route holds far more |
| `_PREEMPT_FRACTION` | 1.0 | |
| `_PREEMPT_MAX_CLONE_DISTANCE` | 6 | how similar an opponent must look before preempting |
| `_PREEMPT_START` / `_PREEMPT_STOP` | 120 / 680 | |
| `_PREEMPT_MIN_FUTURE_QUANTITY` | 4 | |
| `_PREEMPT_MIN_PRICE_RATIO` | 0.0 | gate present but disabled |
| `_V17_R5_FRACTION` | 0.5 | |
| `_V17_MD_FRACTION` | 2.0 | |
| `_V17_FEED_GUARD` | **False** | a guard that ships switched off |

Two things in here contradict the file's own prose: the docstring says *"Clone
preemption is disabled in this experiment"* while `_PREEMPT_ENABLED = True`, and
`_V17_FEED_GUARD` is off. Read the constants, not the comments.

## Why this is the right place to work

56 forks of this notebook exist. Every one of them inherits `lead = 1`, a
12-unit batch cap, and a feed guard switched off. The mirror-tiebreak argument
that made STRAWBERRY-6 worth +1,306 applies with more force here, because the
route itself detects mirrors and the field is larger.

**Measure before assuming transfer.** v16's volume knob was inert because the
shed was empty at pull time; a 10-cow route may behave completely differently.
The method carries over, the constants do not.

## Measured 2026-08-29: four more dead ends, and one methodology lesson

Following the shipped tuning's own method (find a gate that looks almost
always shut, measure whether opening it moves anything), four candidates from
this doc's own "untouched tunables" list plus the feed guard flagged above
were tested against the current `agents/route_moon_tuned.py` control. All
four are dead ends - recorded so nobody re-runs them.

| candidate | change | wins | mean | verdict |
|---|---|---|---|---|
| `_V17_FEED_GUARD` | False -> True | n/a | byte-identical bank, 3 seeds x 2 seats x 2 variants | dead - see below |
| `_PREEMPT_START` | 120 -> 60 | 3/16 | +0 | dead - exact-control signature |
| `_PREEMPT_STOP` | 680 -> 705 | 3/16 | +0 | dead - exact-control signature |
| `_PREEMPT_MIN_FUTURE_QUANTITY` | 4 -> 2 | 5/16 | +49 | inconclusive-leaning-dead, mean an order of magnitude below anything worth confirming |

**`_V17_FEED_GUARD`: the analogy to `main.py`'s own daily-feed fix looked strong and didn't hold.** This repo's `main.py` history records a feed-cadence bug worth +1,657 mean, 12/12 wins - a trigger that only fired after an animal had *already* missed a meal, so it settled into feeding every other day. `_v17_feed_guard` (this file, lines ~958-1035) is shaped the same way: at hour>=18, rescue any animal with `consecutive_unfed>=1 and not fed_today`. It is switched off (`_V17_FEED_GUARD = False`), which is exactly the shape of a bug worth finding.

Live instrumentation *inside* the function itself, across 3 seeds x 2 seats x both variants (6 independent checks), found its `threats` list empty on every single call, every turn, both guard-on and guard-off - bank came back identical to the decimal in all 6. The route's regular scripted feeding already covers every animal before this last-resort path ever has anything to catch, at least in self-play. The analogy to `main.py`'s bug doesn't transfer: that bug was a cadence that genuinely failed; this one is a rescue for a failure that doesn't happen here.

**The methodology lesson, worth keeping regardless of this specific result.** A first-pass diagnostic re-scanned `env.steps`' post-action observations for the pre-action `consecutive_unfed`/`fed_today` condition and found 6 "threats" per seed - a false positive. `CLAUDE.md` already documents this exact trap for our own replay tooling ("a replay row shows the observation *after* the action"), and it reproduced independently here on a completely different codebase. **Instrument the actual computation the agent performs, not a re-derivation from replay rows** - the two disagreed by a wide margin, and only the live in-function count was trustworthy.

**`_PREEMPT_START`/`_PREEMPT_STOP`: the operating window is not the binding constraint.** Both widened arms returned wins/mean byte-identical to the documented self-control signature (3/16, +0, the same exact seat-asymmetry pattern already on record for `_ADAPT_MAX_OPP_HORIZON` and `_PREEMPT_MAX_CLONE_DISTANCE`) - every preemptable opportunity this route ever finds already falls inside steps 120-680. `_PREEMPT_MIN_FUTURE_QUANTITY` 4->2 did change something (5/16, not the exact-control pattern) but the mean, +49, is roughly two orders of magnitude below any result in this codebase's history worth shipping - not confirmed at 12 seeds.

Generalises: the shipped tuning found the one real gate on this mechanism (`_ADAPT_MIN_EVIDENCE`); the remaining constants around it are not additional gates, they're slack. Don't assume a mechanism has more than one binding constraint just because it has several knobs.

## Measured 2026-08-29: `_v17_md_counter` fires on every seed, and its multiplier is already at the local optimum

A 30-seed census (self-play, `experiments/.moon_census.py`) resolved the
"needs more seeds" status the anatomy fork above left on several gates.
Result for the eight mechanisms censused:

| mechanism | seeds active / 30 | category |
|---|---|---|
| **`_v17_md_counter`** | **30/30**, ~7.9 order-modifications/season, family gate latches ~step 172 | live, universal |
| `_v71_route_carrots` | 2/30 | genuinely rare (4-condition AND) |
| `_v38_farm_pair_tomatoes` | 1/30 | genuinely rare shop-RNG |
| `_v73_route_tomatoes` | 0/30 | likely rare (compounding ANDs), not proven impossible |
| `_v79_rival_strawberry_flush` | 0/30 | structural — needs an exact 3-shop permutation |
| `_v17_r5_counter` | 0/30 | structural against a Moon mirror (targets a sheep-heavy, cow<=3 opponent; this route builds cow-heavy) — untested against a real sheep-heavy opponent |
| `_v65_decision` (feeds `_v88_late_tomato_overlay`/`_v88_capacity_overlay`) | 0/30 | structural-looking — see below |

`_v17_md_counter` firing on every single seed, with its amplification constant
`_V17_MD_FRACTION = 2.0` never tuned, was the closest match yet to the shape
of Peter's own proven fix (a live-but-untouched multiplier) - stronger, even,
since his gate was *usually* shut and this one never is. Swept 0.0 (disable),
1.0, 4.0, 6.0 against the shipped 2.0, 8 seeds x 2 seats:

| `_V17_MD_FRACTION` | wins | mean |
|---|---|---|
| 0.0 (disabled) | 2/16 | **-208** |
| 1.0 | 3/16 | -29 |
| **2.0 (shipped)** | — | control |
| 4.0 | 5/16 | +8 |
| 6.0 | 5/16 | +47 |

**Disabling it is a real, clear loss (-208, 2/16) - the mechanism is genuinely
load-bearing, not dead weight.** But every other tested value is a coin flip
or worse against the shipped 2.0. Read together with the batch above: this
constant is a rare case of a knob that is *already* at its local optimum,
not merely untested. Closed for further tuning in this range.

**What's still open, and looks like the bigger prize.** `_v65_decision`
(~line 2316) never returns a nonzero `quantity` across all 30 seeds, which
means the entire subsystem hanging off it - `_v66_capacity_reserve`,
`_v68_fertilizer_horizon`/`_v68_needs_fertilizer`, and the two `_v88` overlay
functions it feeds, roughly 600 lines - reads as completely inert every time
it was checked. That is the `_ADAPT_MIN_EVIDENCE` shape (an always-shut gate
worth real money once opened) at ten times the scale.

## Measured 2026-08-29: `_v65_decision`'s deficit floor is two gates, not one, and only the second one is soft

Read closely, `_v65_decision` (STRAWBERRY -> TOMATO late-game replant, priced
at step 360 only) is blocked by two independent conditions: a `$3200`
`operating_reserve` (a real, cost-justified estimate of the temp-hire cost to
execute the conversion - left alone), and a separate
`_V88_MIN_POST_SUPPLY_DEFICIT = 300` floor requiring the projected TOMATO
deficit to clear 300 units, with no fallback to a smaller, still-profitable
quantity if it doesn't. That second floor is commented only as "generic" in
the source - weak justification next to the reserve's real cost accounting -
and it turned out to be the one actually blocking real trigger cases.

**Census, seeds 0-49: the `$3200` reserve clears on 12 of 50 seeds (24%)** -
`10, 13, 18, 32, 33, 34, 39, 40, 41, 42, 45, 47`. Candidate at
`experiments/.moon_v65_candidate.py`, one line changed:
`_V88_MIN_POST_SUPPLY_DEFICIT` 300 -> 0.

| test | seeds | wins | mean |
|---|---|---|---|
| trigger seeds only | 12 x 2 seats = 24 | **21/24** | **+1,677** |
| unselected range (seeds 0-23) | 24 x 2 seats = 48 | 14/48 | +27 - diluted, 21 of those 24 seeds are provably untouched (see below) |

**On a non-trigger seed a loss is structurally impossible, not just
unlikely** - `_v65_decision` only evaluates the deficit check `if quantity >
0`, and the `$3200` reserve alone already forces every candidate quantity's
NPV negative there, so the code path this fix touches is unreached. That is
why the 76% non-trigger population is exactly zero-risk by construction, and
why the diluted 24-seed number looks like the same "inert control" signature
already on record for a truly dead knob elsewhere in this file - it isn't
dead, it's just gated to the 24% that can ever reach it.

**Not loss-free within that 24%, though - two of twelve trigger seeds are
real, reproducible losses.** Seed 18: seat0 -5,064 / seat1 +2,750 (net
-2,314). Seed 47: both seats exactly -432 (a clean symmetric loss, not seat
noise). The obvious hypothesis - a thinner safety margin causing a TOMATO
oversupply crash - does not hold: seed 13, the cleanest winner, has the
*smallest* post-supply deficit of any seed checked (53), smaller than both
losers (176, 158). Deficit size does not predict win or loss. The more likely
mechanism is the STRAWBERRY-side opportunity cost interacting with a
*contested* market - a static step-360 snapshot can't price what the
opponent does with the STRAWBERRY output being given up - and no
single-constant fix for that was found in this pass.

**Verdict: a real, positive-expectation change, not an unconditionally safe
one.** 87.5% win rate on the seeds it can affect, several six-figure-swing
wins, zero risk everywhere else by construction - clearer than several
already-shipped results on this file (the shipped Moon tuning itself
confirmed at 19/24, 79%). But it is not loss-free, and that claim would be
false if made. Ship on the win-rate case if that is the team's bar; do not
claim zero downside; the two losing seeds are an open mechanism, not a
solved one, if someone wants to chase a cleaner exclusion criterion later.
