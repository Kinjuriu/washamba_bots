# Submitted agents kept out of `main.py`

`main.py` is our own agent, the one the whole `CLAUDE.md` research log is about.
This directory holds agents we have actually *submitted* that are not it, so a
ladder result stays reproducible after the session that produced it is gone.

Everything here is public, Apache-2.0-licensed third-party work plus a stated
change of ours. Nothing private and nothing another competitor shared with us.

## `route_v20.py` - the route upgrade, and the current best base

boatlee's [V20-Adaptive-R1 multi-route agent][v20], **Apache 2.0** (licence read
off the notebook page 2026-08-23), decoded from its base85+zlib payload and
verified byte-for-byte against the SHA-256 the notebook publishes. **Submitted
unmodified on purpose**, to find where this route lands for us before anything
is changed on top of it.

Head to head, contested market, both seats:

| matchup | matches | mean | wins |
|---|---|---|---|
| v20 vs our tuned v16 route | 24 | **+8,855** | 18/24 |
| v20 vs the stock v16 route | 16 | +9,288 | 13/16 |
| HarvestForge-X vs our tuned v16 route | 16 | +10,997 | 16/16 |
| **HarvestForge-X vs v20** | 16 | **-7,972** | **0/16** |

The last row is why this one and not the other: `salemali7/3094-score-kaggriculture`
also beats us on every match, and loses to v20 on every match. Its title
oversells it - the notebook's real Best Score is 2,684.1, and from an earlier
version than the one published. v20's is 2,578.2. Ours is 1,687.5.

**Caveat worth keeping in view:** this is 148 KB of decoded third-party source
we have measured but not read. Tuning it the way we tuned v16 needs that reading
first - see `docs/ROUTE_GENERATIONS.md`.

[v20]: https://www.kaggle.com/code/boatlee/v20-adaptive-r1-multi-route-agent

## `meta_per_item_lead.py` - the previous candidate

Same base, one step further: the lead becomes **per item** rather than one
constant. STRAWBERRY and WOOL go to 6; MILK and MELON stay at 3. Repayment moves
to a per-step ledger because two pulls can now fall due on different steps -
measured behaviour-identical to the single-due version at equal leads, so it is
machinery, not a second change.

**23/24 wins, +1,306 mean** against `meta_lead3.py` at 12 seeds x 2 seats, with
an exact-copy control returning 6/24 and +0 on the same seeds. See
`docs/PUBLIC_META.md` for each item's curve, including the two null results that
matter: MILK is already right at 3, and MELON is never front-run at any lead.

## `meta_lead3.py` - submission `55650592`, our best ever

Derived from [`boatlee/v16-rc5-high-score-8c-4s-premium-market-lead`][nb]
(Apache 2.0, on the competition's public Code tab). The file's own header
carries the attribution and states the change, as the licence requires.

**The change: the premium-goods market lead goes from one step to three.**
`_LEAD = 3`; `_future_quantity()` looks that many steps ahead and `_front_run()`
sets the repayment step to match, so total sell volume is unchanged and only the
timing moves earlier.

**Why there is an edge to find in a published route at all.** The notebook has
~222 copy-and-edits, so a large share of the ladder runs this exact schedule and
a large share of our matches are mirrors of it. Two agents on an identical
schedule bank almost identical money; what separates them is who reaches the
order book first. That makes the lead length the contested parameter, and
nobody else is moving it.

Local sweep against the stock one-step route, 4 seeds x 2 seats each:

| lead | beats stock | margin |
|---|---|---|
| 2 | 8/8 | +1,540 |
| **3** | **8/8** | **+1,646** |
| 4 | 8/8 | +1,358 |
| 6 | 7/8 | +670 |
| 8 | 2/8 | -285 |

Lead 3 also beats lead 2 head to head 8/8 by +1,905 - an interior optimum, not
"more is better".

**Confirmed on the ladder, and not by the rating.** See
`docs/PUBLIC_META.md` for the stratified read: the rating gap over the stock
control is 54 points, which is inside our own measured noise floor and proves
nothing. The evidence is the near-tie conversion rate in the rating band we
actually play in.

Reproduce the base with `python experiments/meta_opponent.py`, which fetches the
notebook on demand; the only diff from it is `_LEAD`.

**Do not "fix" the repayment clobbering in this file.** `_front_run` overwrites
its pending due wholesale, so a pull inside another pull's repayment window
cancels it - a real defect, and automated review flags it. It is left in place
for two reasons. First, this file must stay byte-identical to what was submitted
as `55650592`, or it stops being a record of what scored 1755.5. Second, it was
measured: a per-step ledger that removes the clobbering entirely plays
byte-identical episodes (same banks, every seed and seat), because the un-repaid
order asks for goods the shed no longer holds and the engine drops it. The
correct queue is implemented in `meta_per_item_lead.py`, where per-item leads
make it necessary rather than cosmetic.

## `w0_v15stack_control.py` / `w1_v15stack_race44.py` - the v15stack base and its one-constant edge

**Provenance note: these files' own header comments describe them more
precisely than "v15stack by wzhengbiao, unchanged."** Despite the filename,
each is a locally-packaged composite of several public, Apache-2.0-licensed
Kaggriculture notebooks layered over many `EXP-*` iterations - not a single
untouched notebook. The in-file header attributes layers to (at least)
thomastschinkel, yhay81, destbreso, aurax7, tetsutani, Ahmed Berat Ozer,
prvsiyan, Dmitrii Gluzdov and lucifer19, on top of a wzhengbiao-derived base,
with "Local packaging modifications, 2026-09-20" noted at the top. All
attribution and Apache-2.0 notices are retained in-file, per this directory's
convention - read the header comments in the file itself for the authoritative
lineage rather than this summary.

**`w0_v15stack_control.py` is the control: packaged as received, no strategy
change.** It is the strongest agent measured so far, not `main.py` -
`main.py` (`nikaangukia_meroni`, the subject of the root `CLAUDE.md` log) has
peaked around 535-650 on the ladder, while adopting a stronger public route is
what has produced every ladder result above 2,000. In a 144-game round robin
of current public agents on engine 1.32.7 (both seats), v15stack scored a
0.917 points share against V57 (0.722), K0013 (0.236) and Fieldcraft (0.125) -
the strongest agent in the pool by a wide margin, which is why it is the base
here rather than another one-off structural edge on `main.py`.

**`w1_v15stack_race44.py` is the one real edge on top of it: `V9_RACE_DEFAULT`
40 -> 44** (deeper premium-sale reservation), a single-constant diff verified
against W0. Confirmed as a genuine improvement, not a copy: mirrored against
W0 it ties exactly (same base, same tape), and W1 went 36-28-24 against W0 on
88 fresh games. [[feedback_no-reconstruction-copies]]'s rule - a copy at best
ties the thing it copies - is exactly why W1 exists as a distinct file: W0 is
the tie-point control, W1 is the measured edge on top of it.

Both files verified byte-for-byte by SHA-256 against the versions already
uploaded to Kaggle as submissions.

## `public/` - reference agents for pool benchmarking

`v57.py` (Ahmed Berat Ozer), `k0013.py` (ghazarosghazaros) and
`fieldcraft/` (`main.py` + `mirror_plan.py`, hakdevelopment) are public
Apache-2.0 notebooks kept unmodified as opponents for `experiments/pool_harness.py`,
not as submission candidates. License headers are retained inside each file.

[nb]: https://www.kaggle.com/code/boatlee/v16-rc5-high-score-8c-4s-premium-market-lead
