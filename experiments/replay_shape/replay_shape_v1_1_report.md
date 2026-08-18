# Track C v1.1 — cash-aware crew hiring, isolated repair experiment

Scope: **`experiments/replay_shape_agent.py` only** — `decide_hire_orders`,
`_fib_hire_cost`, and the engine-metadata import block (added
`FARM_HAND_COST_MULT`). Nothing else in that file changed: land, animal,
crop, planting, harvesting, selling, and pricing logic are byte-identical
to the version scored in `replay_shape_validation_report.md`. `main.py` is
untouched (`git diff origin/main -- main.py` is empty). No merge, no
submission.

## Change made

`decide_hire_orders(farm, day)` now prices each candidate hire at its
**actual engine cost** before queuing it, instead of only checking a flat
`money >= MIN_MONEY_TO_HIRE` floor once per turn:

```python
def _fib_hire_cost(n_already_hired_today):
    a, b = 1, 1
    for _ in range(n_already_hired_today):
        a, b = b, a + b
    return FARM_HAND_COST_MULT * a

def decide_hire_orders(farm, day):
    money = farm.get("money", 0)
    if money < MIN_MONEY_TO_HIRE:
        return []
    target = crew_target_for(owned_tile_count(farm))
    already = len(farm.get("hands") or [])
    shortfall = max(0, target - already)
    n_to_try = min(shortfall, MAX_HIRES_PER_TURN)

    orders = []
    remaining_cash = money
    for k in range(n_to_try):
        cost = _fib_hire_cost(already + k)
        if remaining_cash - cost < MIN_MONEY_TO_HIRE:
            break
        remaining_cash -= cost
        orders.append(["HIRE"])
    return orders
```

`_fib_hire_cost` reproduces the engine's own recurrence exactly
(`kaggriculture.py` `_fib`/`_hire_cost`: `fib(0)=1, fib(1)=1, fib(2)=2,
fib(3)=3, fib(4)=5, ...`, cost `= mult * fib(hires_today)`) — no new cost
model. `already = len(farm.get("hands") or [])` is safe to use as
`hires_today` because hands clear to `[]` every night and only `HIRE`
appends to them, so the live hand count mid-day already **is** that day's
hire count.

## Exact economic rationale

`decide_hire_orders` previously computed a *shortfall* (`target - already`,
capped at `MAX_HIRES_PER_TURN=3`) and queued that many flat `["HIRE"]`
orders whenever the bank held at least `MIN_MONEY_TO_HIRE=$20`, with no
regard for what those hires actually cost. But hiring cost is not flat —
`hires_today` resets to 0 every morning (hands clear nightly), so the
15th hand of a day is `fib(14) = $610`, not "one more cheap hire." A crew
sustained at 15 hands pays `Σ_{k=0}^{14} fib(k) = $1,596/day` to rebuild
itself from scratch every morning — large enough by itself to explain the
~$20–34k final bank measured against `pass` in the prior report. The fix
walks the fib curve explicitly and stops queuing hires the moment the next
one would drop the bank below the same `$20` floor — reused as a
**post-hire** floor rather than only a pre-hire one. Cheap early hires
(`fib(0..3)` = `$1–3`) go through almost regardless of cash; the expensive
tail only fires once the bank can absorb it. The crew *target*
(`crew_target_for`, still 13–15 at 75 tiles) is completely unchanged — only
how fast the agent is willing to pay to reach it on a given day.

## Results — vs `pass` (6 seeds)

| seed | final bank (before → after) | animal_scale | no_feed_collapse |
|---|---|---|---|
| 0 | $33,965 → $34,180 | PASS (8/9) | **PASS** (was silent-pass before too — `pass` never triggered it) |
| 1 | $19,675 → $19,675 | PASS (8) | PASS |
| 2 | $33,882 → $33,882 | PASS (8) | PASS |
| 3 | (new) → $37,330 | PASS (9) | PASS |
| 4 | (new) → $34,396 | PASS (9) | PASS |
| 5 | (new) → $23,945 | PASS (9) | PASS |

Bank is essentially unchanged against `pass` (within a few hundred dollars
on the two previously-measured seeds) — expected, since the earlier
report never found a `pass`-matchup animal collapse to begin with (0
stranded, all seeds). The gate is a real, verified behavior change (see
the unit tests added: `test_cheap_early_hires_go_through_even_near_the_cash_floor`,
`test_expensive_tail_hire_is_refused_even_with_nominal_floor_met`,
`test_batch_is_truncated_mid_turn_once_unaffordable`), it just wasn't the
thing suppressing the `pass`-matchup bank.

## Results — self-play, replay-shape vs itself (6 seeds, 12 seat-runs)

**Unchanged, failure-for-failure identical to the pre-v1.1 report:**

| check | before | after |
|---|---|---|
| farm_scale | 12/12 | 12/12 |
| crew_scale | 12/12 | 12/12 |
| animal_scale | 0/12 | **0/12** |
| no_feed_collapse | 0/12 | **0/12** |
| selling_throughput | 12/12 | 12/12 |
| market_pressure | 12/12 | 12/12 |
| final_bank (evidenced range) | 0/12 | **0/12** |
| final bank mean | $2,496 | $2,364 |

Self-play final bank is not just still below range, it's statistically
indistinguishable from before the fix.

## Diagnosis — why the gate didn't touch self-play (the next bottleneck)

Traced days 0–29 for seeds 0, 1, 2 (seat 0). All three show the **same
shape**, day-for-day:

```
day 10   cash ~$188-400   crew 5    (last day before land+crew scale-up)
day 11   land jumps to 75, crew jumps to 15, cash spent down to ~$2,500
day 12   cash ~$750-820
day 13   cash crashes to $13-18   crew 14   <- ONE dollar short of $20
day 14   crew -> 0 (nightly wipe; $13-18 < MIN_MONEY_TO_HIRE=20, so
         decide_hire_orders' own ENTRY check - unchanged by v1.1 - refuses
         to hire even the $1 first hand)
day 14-21  cash FROZEN at the exact day-13 value for 8 straight days.
           crew stays 0 the entire time. Animals drop 8 -> 0-2 and never
           recover (starved: one farmer alone cannot feed multiple
           structures AND tend 75 tiles).
day 22   cash finally crosses $20 (scarcity-driven price recovery on
         whatever the lone farmer occasionally sells) and hiring resumes.
```

This is a **poverty trap**, not a hiring-cost problem, and v1.1's gate
cannot reach it: the gate only changes how many hires are queued once
`money >= MIN_MONEY_TO_HIRE`. It does nothing about the pre-existing
**entry** check (`if money < MIN_MONEY_TO_HIRE: return []`), which was
already in the file before this experiment and is explicitly out of scope
("do not change... cash reserve constants unrelated to crew" — this one
*is* crew-related, but changing its meaning from an entry floor is a
second, separate lever from the one this experiment was scoped to test).

The mechanism: the day-11 land+crew scale-up is a large, deliberate,
one-time capital spend (land $2,000 + rebuilding a 15-hand crew). In
self-play, revenue immediately after that spend is *structurally lower*
than against `pass`, because a second large seller is already contesting
the same thin markets (this is `validate_market_pressure` passing 12/12 —
working as designed) — so the post-spend cash trough lands closer to zero
and more often dips under $20 than it does against a non-competing
opponent. The instant that coincides with the nightly crew wipe (day 14
here, but the mechanism is date-independent), the farm is locked at **zero
crew** with **only the entry-level `$20` gate standing between it and
recovery**, and one farmer covering 75 tiles plus several hungry animals
cannot generate $20 of net cash fast enough to escape — not for a
coincidental few turns, but for over a week, every seed tested.

This is a different bug class from the fib-cost one, though related:
fib-cost pricing explains why the *marginal* hand is expensive once a
crew exists; the poverty trap explains why the crew can vanish **entirely
and stay at zero** once cash dips under a flat threshold with no scaled
alternative (e.g., "hire 1 hand for $1 even below the $20 floor" was never
on the table — the floor is binary, not graduated).

## Does self-play remain viable? Does market pressure remain?

- **Self-play viability: no.** All three explicit self-play acceptance
  criteria (maintain animals, bank moves toward range, no economic
  collapse) still fail on every seed tested, unchanged from before.
- **Market pressure: yes, undiminished.** 12/12 both before and after —
  the contested-market signature (premium prices crashing well below
  base, e.g. WOOL to $5 against a $200 base in the main.py matchup trace)
  is intact and is in fact part of *why* the trap is worse in self-play
  than against `pass`.

## Remaining bottleneck

The flat, binary `MIN_MONEY_TO_HIRE=$20` **entry** gate on hiring
(distinct from the graduated exit gate this experiment added), combined
with the nightly full-crew wipe: together they can strand the farm at
zero crew for over a week whenever a cash dip below $20 coincides with a
morning reset, and a single farmer cannot recover fast enough from a
75-tile, multi-animal farm alone. A graduated entry rule — e.g. always
permit hiring while its cost is below some small absolute floor (the
cheap early fib terms), rather than gating all hiring on a fixed cash
level the trough can dip under — is the natural next isolated experiment.
This was **not** implemented here, per this task's scope and the explicit
instruction to diagnose rather than patch further.

## Decision: **REJECT** (as a complete fix) — keep the change, it is real and correct, but it does not meet the self-play sustainability bar

The v1.1 gate is a verified, isolated, net-positive change — it fixes a
real fib-cost blind spot, is covered by regression tests, and does not
regress anything measured (farm/crew/selling/market-pressure all hold at
12/12 self-play, unchanged; `pass`-matchup bank unchanged; `main.py` still
wins 12/12 at +31,008 mean, t=13.15, statistically the same margin as
before the fix). But it does not move a single one of the three self-play
sustainability criteria this experiment was scoped to fix. The next
isolated experiment should target the entry-gate/poverty-trap mechanism
identified above, not another adjustment to the hiring-cost curve itself.
