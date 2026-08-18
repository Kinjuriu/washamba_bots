# archive/

Deliberately empty of code. This folder is a pointer index for rejected
research that exists only as git branch history, not as files in this
working tree — so "archiving" them means recording where they are, not
moving anything.

Both branches below are already pushed to `origin` (GitHub), so the
research is not at risk even though nothing sits in this directory.

## second-animal (`MAX_ANIMALS = 2`)

- Branch: `experiment/second-animal` (unmerged, on GitHub as
  `origin/experiment/second-animal`)
- Tip commit: `85fbbc2` — "experiment: raise MAX_ANIMALS to 2, now the
  cash trough is gone"
- Status: **REJECTED**. Full writeup and numbers are in root `CLAUDE.md`
  under "A second sheep is the sharpest two-harness disagreement we have
  found" — paired against `starter`: **-19,514, 0 of 12 seeds, t = -20.0**.
  Both sheep starve to death in the days 3-7 cash trough. It only looks
  like a win head-to-head against a copy of itself, which is exactly the
  failure mode that motivated requiring two disagreeing harnesses before
  trusting any change.
- Recovering it: `git show experiment/second-animal:main.py` (stale
  relative to current `main.py` - do not apply directly).

## tomato-fertilizer-yield-bonus

- Branch: `fix/tomato-fertilizer-yield-bonus` (unmerged, on GitHub as
  `origin/fix/tomato-fertilizer-yield-bonus`)
- Commits: `4bd053c` (the experiment) → `b1e943b` ("docs: record the
  fertilizer-yield-bonus attempt as a measured dead end") → `404e94b`
  (self-reverted)
- Status: **REJECTED**, and already reverted on its own branch by the
  people who ran it. Also badly stale relative to current `main.py` (missing
  ~970 lines of later work - `ladder_episodes.py`, `replay_shape.py`,
  large parts of `main.py` itself) - not cleanly applicable today even if
  it had won.
- Recovering it: `git show fix/tomato-fertilizer-yield-bonus~1:main.py`
  (the commit before the revert) - for historical reading only, not for
  reapplying.
