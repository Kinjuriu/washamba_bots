# Submitted agents kept out of `main.py`

`main.py` is our own agent, the one the whole `CLAUDE.md` research log is about.
This directory holds agents we have actually *submitted* that are not it, so a
ladder result stays reproducible after the session that produced it is gone.

Everything here is public, Apache-2.0-licensed third-party work plus a stated
change of ours. Nothing private and nothing another competitor shared with us.

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

[nb]: https://www.kaggle.com/code/boatlee/v16-rc5-high-score-8c-4s-premium-market-lead
