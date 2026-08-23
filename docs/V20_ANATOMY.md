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
