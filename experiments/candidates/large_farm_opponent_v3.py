"""
Issue #21, Track C, Experiment 3: land-gated animal cap, WITHOUT the reserve
floor - isolating the gating idea from v2's reserve-floor addition.

v2 (land-gated animal count, PLUS a $450 post-purchase reserve floor copied
from v1) fixed land (0 -> 75 tiles, confirming the land-vs-animal cash
competition diagnosis) but animal count went to material bank ($7,779 mean,
up from ~$425) - a big improvement but still nowhere near
bigfarm_opponent.py's own $59,018 baseline, and animals=0 at episode end.

Suspect: v1/v2's added MIN_CASH_RESERVE_FOR_ANIMAL_BUYING=450 floor, which
never appears in bigfarm_opponent.py's own (working) animal-buying logic,
is now ALSO blocking the first 4 animals - the ones already proven to work
fine without any floor at all. Testing the reserve floor in isolation (v1,
MAX_ANIMALS=8 with the floor, no land gate) already showed 0 animals as
well, which is consistent with this: the floor may simply be too aggressive
whenever land-saving is competing for the same cash pool.

This experiment removes the copy-pasted decide_animal_market_actions /
choose_animal_to_build entirely and instead does the minimal thing: adjust
the plain MAX_ANIMALS constant dynamically, based on whether land is fully
bought yet, right before each call into the untouched bigfarm_opponent /
main.py logic. No function bodies are duplicated, so there is no risk of a
copy having silently drifted from what's actually proven to work - this is
the same "override tuning constants, don't rewrite" discipline
bigfarm_opponent.py itself already uses successfully.

Hypothesis: land-gating the animal *count* alone (not touching the
affordability logic at all) should recover something close to
bigfarm_opponent.py's $59,018 while also reaching land + a bigger crew, then
grow past 4 animals once land is secured.
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

MAX_ANIMALS_BEFORE_LAND = 4   # bigfarm_opponent.py's own proven count
MAX_ANIMALS_AFTER_LAND = 8


def _land_fully_bought(farm):
    bought = len(farm.get("unlocked_quadrants") or ["NW"]) - 1
    return bought >= len(base_opponent.LAND_BUY_DAYS)


def large_farm_opponent_v3(obs):
    try:
        farm = obs["farms"][obs["player"]]
        base.MAX_ANIMALS = (
            MAX_ANIMALS_AFTER_LAND if _land_fully_bought(farm) else MAX_ANIMALS_BEFORE_LAND
        )
    except (KeyError, IndexError, TypeError):
        base.MAX_ANIMALS = MAX_ANIMALS_BEFORE_LAND
    return base_opponent.bigfarm_opponent(obs)


agent = large_farm_opponent_v3
