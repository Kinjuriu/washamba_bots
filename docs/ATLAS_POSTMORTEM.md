# Atlas / Switchboard postmortem

**2026-09-21. Ladder result: Atlas at rank ~424 (sinking).** Diagnosis
below is from reading Atlas's own two-seat 720-step logs plus its source,
not from guessing at the ladder score alone.

## First, what isn't wrong

Atlas is mechanically healthy: max turn time ~0.15s at warmup, 1-15ms
steady-state, no stderr, `DONE` on both seats, no crashes, no timeouts.
**It is losing on strategy alone**, which narrows the diagnosis to the
decision logic, not the executor.

## Why it loses, worst first

**1. It copies a destination, not a route, so its ceiling is a tie with
the agent it copied.** Atlas chases the per-checkpoint median of 41
winning trajectories from one family (submission 56401905, "Unknown
Mother-Goose," 85% of cluster 4). Copying can at best tie the thing you
copy - that's this repo's own standing axiom. Unknown Mother-Goose sits
around rank 4; a perfect copy lands near there, a degraded copy lands
well below, and the ladder is already full of similar copies - so a
slightly worse copy loses the near-ties. That's the whole story of a
sinking rank in the 400s.

**2. The median target is a Frankenstein state no real winner ever held.**
The turn-216 (day 9) target: 75 usable land, 11 hands, 7 cows + 1 goose +
3 sheep, wheat + strawberry + melon all planted at once, $365 bank. That's
the median of each field taken *separately* across 41 trajectories, so no
single winning game ever actually passed through that exact combined
state. `agents/atlas_profile.py`'s own docstring claims this avoids
"averaging incompatible policies," but a per-field median across 41
trajectories is itself an average - it produces a herd/crop mix that is
nobody's real strategy. Chasing an incoherent target produces incoherent
play.

**3. It front-loads a spend with no margin, then a greedy executor
sequences it badly.** Reaching 3 quadrants + 7 cows + melons by day 9 at
a $365 bank means near-zero cash buffer through the most fragile phase of
the season. The executor fills these deficits greedily with no lookahead,
so its ordering diverges from real winners in exactly the ways this
repo's own history already warns about: land bought before the crew can
work it, animals bought before they can be reliably fed, tiles planted
beyond watering capacity. With no cash buffer, any one slip snowballs.

**4. It reproduces the winner's *stuff*, not their *money*.** The
embedded profile carries a bank target that climbs to ~$94k, but bank is
never used as a control signal anywhere in the decision code - every
decision chases a physical target (land, hands, animals, crops, shed
level), and selling only ever releases the excess above a shed snapshot.
Atlas tries to *look like* a rich farm without the mechanism that made
the original rich, which was selling. Matching a winner's incidental
inventory levels cannot, by construction, reach the winner's bank.

**Switchboard inherits all four**, because on the current corpus it *is*
Atlas almost all the time: per its own build report, exactly one context
cell ever clears the routing bar (step 72, YARN_STORE opening -> family
1); every other context falls back to Atlas. It occasionally switches to
another median-blend copy with the same structural problem, not to
something structurally different.

## The lesson, and what's next

**Do not submit another reconstruction.** The next agent builds on
Peter's `washamba_base_v1` - the proven base that had this team ranked
high in the first place, and which already encodes a coherent route
(the thing Atlas threw away by chasing a blended destination instead).
Then add exactly one real edge on top of that coherent route - not
another copied destination.

Pick, in order:
1. **Hungarian task-assignment executor** - pure upside on the base we
   already trust, no strategy change. Spec below, ready to fire the
   moment the base is committed.
2. **Win/tie/loss variance rule** - the edge that *beats* near-ties
   instead of tying them.

**Status as of 2026-09-21: blocked.** `washamba_base_v1.py` is not yet
committed anywhere findable (checked: full history of every local and
remote-tracking branch on `origin/Kinjuriu/washamba_bots`, and Peter's
own GitHub account - see the build attempt in the session log for the
exact commands run). Waiting on Peter to commit it before starting.

---

## Ready-to-fire build spec: `washamba_base_v1` + Hungarian executor

The full spec below is unchanged from what was drafted and ready to run
the moment the base lands - paste it back in once `washamba_base_v1.py`
(or whatever the current strongest base `main.py` turns out to be) exists
in the repo.

> We need a Kaggriculture submission that builds on our proven base agent and
> changes ONE thing: it assigns the crew to tasks optimally each turn instead of
> greedily. The deliverable is a runnable, submit-ready agent, not a report.
>
> Read CLAUDE.md completely, then run git status --short and preserve every
> existing change. Do NOT modify any existing agent. Do NOT commit, push, or
> submit.
>
> **BASE**
> Start from Peter's proven base agent, washamba_base_v1.py (find it in the
> repo; if the exact filename differs, use the current strongest base main.py
> that CLAUDE.md points to). Copy it to a new file for a new agent, e.g.
> `agents/washamba_hungarian.py`. Keep its entry-point / last-callable
> convention EXACTLY as the base uses it. Keep the base's strategy 100%
> unchanged: task priorities, crop/animal/land choices, all market decisions
> (hiring, buying, selling, seeds), and the per-unit action ladder. You are not
> changing WHAT the farm does, only WHICH unit does which of the tasks the base
> already wants done.
>
> **THE ONE CHANGE: OPTIMAL TASK ASSIGNMENT (HUNGARIAN ALGORITHM)**
> Today the base chooses each unit's action independently and de-conflicts with
> a greedy "claimed" set: a far unit can grab a task a nearer unit should have
> done, leaving the nearer unit's better task undone. Replace that
> WHO-does-WHICH step, and only that step, with a globally optimal assignment.
>
> Each turn:
> 1. Collect the actable units: the farmer plus every hand (their grid
>    positions).
> 2. Collect candidate field tasks from the SAME task types the base already
>    recognizes (feed animal, harvest crop, harvest animal, water/care,
>    place/collect, weed, plant, fill structure, shed errand). To keep the
>    matrix small and fast, take only the nearest few candidates of each type
>    (e.g. up to the nearest 4-6 per type).
> 3. Build a cost matrix C[unit][task] = manhattan_distance(unit, task) minus a
>    large priority bonus for the task's type, where the priority ordering is
>    COPIED from the base's existing action ladder (feeding a hungry animal
>    must outrank harvesting, which outranks watering, and so on, EXACTLY as
>    the base already prioritizes). Use manhattan distance, matching the base's
>    own movement cost, so behavior stays consistent.
> 4. Solve the assignment that maximizes total (priority_bonus - distance) with
>    a pure-Python Hungarian / Kuhn-Munkres algorithm (O(n^3), n <= ~16 units,
>    so microseconds). Handle the rectangular case (units != tasks) by padding.
>    Implement it inline; NO numpy, scipy, or any import.
> 5. For each unit, given its assigned task, produce the action via the base's
>    OWN per-unit executor (act if standing on the task tile, else step toward
>    it) so legality, movement, and action shapes are produced by the proven
>    code. A unit with no assigned task falls back to the base's original
>    single-unit action for that unit unchanged (which may be a shed errand, a
>    macro action, or PASS).
>
> **SAFETY AND FALLBACK (non-negotiable, an illegal action is a silent loss)**
> - Add a module-level flag USE_HUNGARIAN = True. When False, delegate ENTIRELY
>   to the base's original per-unit assignment, so the agent is byte-identical
>   to the base. This is the off-means-off switch.
> - If anything about the assignment is degenerate (no tasks, matrix build
>   issue, any exception), fall straight back to the base's original per-unit
>   logic for the whole turn.
> - After assignment, if a unit's assigned target is unreachable or its step
>   would be illegal or empty, fall back to the base's action for that unit.
> - Never emit an empty, malformed, or wrong-length hands array. The farmer
>   action and the hands list must be shaped exactly as the base produces them.
> - Keep all of the base's market/hire/land/animal/sell decisions completely
>   untouched.
> - Standard library only. No filesystem, network, numpy, scipy, pandas,
>   sklearn, kaggle_environments, or any import of this repo's own code at
>   inference.
>
> **CHECKS (required, do only these)**
> 1. Compilation/import; confirm zero imports and no repo dependency at
>    inference.
> 2. One full 720-turn season in seat 0 and one in seat 1: DONE/DONE, a legal,
>    correctly-shaped action every turn, and record the maximum per-turn
>    runtime.
> 3. Off means off: with USE_HUNGARIAN=False, actions are byte-identical to the
>    base over a full replay (0 differences over 720 turns, both seats).
> 4. With USE_HUNGARIAN=True: no two units are assigned the same tile, no unit
>    is assigned an illegal/occupied target, and hands do real work (high
>    non-PASS mix). Replay a recorded base game and confirm the flag-off bank
>    reconciles to the dollar.
> 5. Confirm runtime stays far under the ~1s per-turn budget.
>
> Do NOT rank it against old agents and do NOT reject it on a local bank or
> local win rate. Kaggle is the judge.
>
> End by reporting: file path and SHA-256, both-seat smoke-test results and max
> turn runtime, the off-means-off diff result, and the exact Kaggle submission
> command. Stop after the agent exists and passes the two-seat smoke test. Do
> not submit.
