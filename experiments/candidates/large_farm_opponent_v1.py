"""
Issue #21, Track C, Experiment 1: a cash-reserve floor on animal purchases.

v0 (large_farm_opponent_v0.py) isolated the collapse to MAX_ANIMALS alone:
raising it 4 -> 8 with everything else identical to the already-healthy
bigfarm_opponent.py (self-play mean $59,018, 0 collapses, 6/6 seeds) crashes
self-play bank to $290-441 on every one of 6 seeds - below the $3,000
starting stake, on every seed, no exceptions. That is a total, not a
gradual, failure.

Mechanism, read straight off main.py: `decide_animal_market_actions` and
`choose_animal_to_build` gate a purchase only on
`cost <= money * ANIMAL_SPEND_CAP_FRACTION` - a fraction of *current* cash,
which supplies no floor at the fraction's own boundary (money == cost /
FRACTION leaves exactly $0 behind). This is the *exact* bug CLAUDE.md
already documents and fixed for seed buying
(MIN_CASH_RESERVE_FOR_SEED_BUYING, +2,271/10-12) and that the unmerged
refactor/phase3-land-and-second-animal branch already fixed for animal
buying the same way (+9,004/10-12 paired, in a bundle with other changes).
It was never ported to shipped main - main.py has no
MIN_CASH_RESERVE_FOR_ANIMAL_BUYING at all (grep confirms).

This file ports ONLY that one fix, isolated from phase3's other changes
(home-quadrant gating, derived crew ceiling) so it can be measured on its
own. Same reserve value phase3 used and justified: $450 - above COW's $400
(so it doesn't block every purchase), at/below SHEEP's $500 (so it doesn't
over-restrict the fraction cap already allows).

Hypothesis: with animals bought one at a time (`decide_animal_market_actions`
already does this - "one purchase at a time, same cadence as seed buying"),
a floor that keeps $450 behind after each purchase should mean the agent
stops buying animals once cash gets thin, rather than draining to zero
buying the 5th/6th/7th/8th while feed and hiring still need money too.

Structural checks to watch: animal count at episode end (does it still
reach 8, or does the floor cap it lower - which would itself be useful
information about MAX_ANIMALS=8's real cost), and whether the collapse
moves from "every seed" to "some seeds," which would point at day-11
land+crew timing as a second, independent factor still to isolate.
"""
import os
import sys


def _find_repo_root():
    """See large_farm_opponent_v0.py's copy of this function for why: the
    kaggle_environments agent loader intermittently exec's this file into a
    namespace with no `__file__` at all, and a fixed dirname()-hop-count
    fallback is silently wrong when that happens - walk up from cwd and
    verify against main.py instead of guessing a hop count."""
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

MAX_ANIMALS = 8
MIN_CASH_RESERVE_FOR_ANIMAL_BUYING = 450

base.MAX_ANIMALS = MAX_ANIMALS


def _choose_animal_to_build(farm, private, board_size, day, pending_builds=0):
    """Copy of main.choose_animal_to_build with one added condition: the
    purchase must leave MIN_CASH_RESERVE_FOR_ANIMAL_BUYING behind. See
    module docstring for why - same shape as
    MIN_CASH_RESERVE_FOR_SEED_BUYING, ported from phase3's unmerged fix."""
    filled, unfilled = base.scan_animal_structures(farm, board_size)
    if unfilled > 0 or pending_builds > 0 or filled >= MAX_ANIMALS:
        return None

    money = farm.get("money", 0)
    remaining_days = base.remaining_season_days(day)
    eligible = []
    for animal in base.ACTIVE_ANIMALS:
        info = base.ANIMALS.get(animal)
        if not info:
            continue
        cost = info.get("cost")
        first_yield_day = info.get("first_yield_day")
        if cost is None or first_yield_day is None:
            continue
        if first_yield_day > remaining_days:
            continue
        if (
            money >= cost
            and cost <= money * base.ANIMAL_SPEND_CAP_FRACTION
            and money - cost >= MIN_CASH_RESERVE_FOR_ANIMAL_BUYING
        ):
            eligible.append(animal)
    return base.pick_next_animal_species(
        eligible, base.species_owned_counts(farm, private, board_size)
    )


def _decide_animal_market_actions(farm, private, board_size, day):
    """Copy of main.decide_animal_market_actions with the same reserve
    floor added to the BUY_ANIMAL branch. The feed BUY_PRODUCT safety net
    below it is untouched - Experiment 1 tests the purchase floor alone."""
    actions = []
    money = farm.get("money", 0)
    remaining_days = base.remaining_season_days(day)

    if base.count_owned_animals(farm, private, board_size) < MAX_ANIMALS:
        held = base.species_owned_counts(farm, private, board_size)
        affordable = []
        for animal in base.ACTIVE_ANIMALS:
            info = base.ANIMALS.get(animal)
            cost = info.get("cost") if info else None
            first_yield_day = info.get("first_yield_day") if info else None
            if cost is None or first_yield_day is None:
                continue
            if first_yield_day > remaining_days:
                continue
            if cost > money or cost > money * base.ANIMAL_SPEND_CAP_FRACTION:
                continue
            if money - cost < MIN_CASH_RESERVE_FOR_ANIMAL_BUYING:
                continue
            affordable.append(animal)

        if affordable:
            animal = base.pick_next_animal_species(affordable, held)
            actions.append(["BUY_ANIMAL", animal, 1])

    filled, _ = base.scan_animal_structures(farm, board_size)
    if filled > 0 and money > 0:
        shed_wheat = private.get("shed", {}).get("WHEAT", 0)
        carried_wheat = sum(
            inv.get("WHEAT", 0) for inv in (private.get("inventories") or []) if isinstance(inv, dict)
        )
        if shed_wheat + carried_wheat < base.MIN_WHEAT_RESERVE_FOR_FEEDING:
            actions.append(["BUY_PRODUCT", "WHEAT", 1])

    return actions


base.choose_animal_to_build = _choose_animal_to_build
base.decide_animal_market_actions = _decide_animal_market_actions


def large_farm_opponent_v1(obs):
    return base_opponent.bigfarm_opponent(obs)


agent = large_farm_opponent_v1
