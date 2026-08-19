"""
Issue #21, Track C, Experiment 4: gate the animal-count bump on cash, not
just on land being bought.

v3 isolated the mechanism precisely (confirmed with a per-turn debug trace,
not inferred): land-gating MAX_ANIMALS (4 until both quadrants are bought,
then 8) buys land correctly and MAX_ANIMALS flips 4 -> 8 exactly on
schedule (day ~12, right after the day-11 second land purchase) - but the
final bank ($7,806 mean) is almost identical to MAX_ANIMALS=8 for the WHOLE
game ($418 mean is a different, worse number, but both are collapses; a
control test with MAX_ANIMALS hardcoded at 4 the entire game reproduces
bigfarm_opponent.py's own $59,018 exactly, confirming the wrapper mechanics
are not the bug).

So the collapse isn't from days 0-11 (identical to the working baseline
during that window, confirmed by trace) - it's triggered AT the moment
MAX_ANIMALS bumps, which lands right on top of the second $2,000 land
payment. This is the mechanism the issue brief named directly: "the day-11
land + crew expansion creates a poverty trap." Bumping animal-buying
urgency at the exact moment land has just drained cash re-triggers the same
cash-siphon v0/v1 already showed (animal buying eating every dollar the
instant it crosses an affordability threshold, at the expense of whatever
else needs that cash) - only now the something-else is the post-land crew
ramp instead of the land purchase itself.

Fix tested here: don't bump MAX_ANIMALS on the land-bought signal alone.
Require land bought AND a cash cushion (ANIMAL_RAMP_CASH_BUFFER) beyond
what land-buying itself needs, so the post-land crew/income has room to
recover before the animal count competes for cash again. Deliberately a
LARGE buffer for a first attempt at isolating this factor - if this
overshoots (ramp never fires, mirrors v3's MAX_ANIMALS=4-forever number),
that's still informative: it would mean timing alone isn't enough and the
ramp itself needs pacing (one animal every N days) rather than a single
gate.
"""
import os
import sys


def _find_repo_root():
    candidates = []
    if "__file__" in dir():
        this_dir = os.path.dirname(os.path.abspath(__file__))
        candidates.append(os.path.abspath(os.path.join(this_dir, "..", "..")))
    here = os.getcwd()
    for _ in range(4):
        candidates.append(here)
        here = os.path.dirname(here)
    for c in candidates:
        if os.path.isfile(os.path.join(c, "main.py")):
            return c
    return os.getcwd()


_ROOT = _find_repo_root()
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import experiments.bigfarm_opponent as base_opponent  # noqa: E402
import main as base  # noqa: E402

MAX_ANIMALS_BEFORE_RAMP = 4
MAX_ANIMALS_AFTER_RAMP = 8
ANIMAL_RAMP_CASH_BUFFER = 2000


def _land_fully_bought(farm):
    bought = len(farm.get("unlocked_quadrants") or ["NW"]) - 1
    return bought >= len(base_opponent.LAND_BUY_DAYS)


def _ready_for_animal_ramp(farm):
    return _land_fully_bought(farm) and farm.get("money", 0) >= ANIMAL_RAMP_CASH_BUFFER


def large_farm_opponent_v4(obs):
    try:
        farm = obs["farms"][obs["player"]]
        base.MAX_ANIMALS = (
            MAX_ANIMALS_AFTER_RAMP if _ready_for_animal_ramp(farm) else MAX_ANIMALS_BEFORE_RAMP
        )
    except (KeyError, IndexError, TypeError):
        base.MAX_ANIMALS = MAX_ANIMALS_BEFORE_RAMP
    return base_opponent.bigfarm_opponent(obs)


agent = large_farm_opponent_v4
