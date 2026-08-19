"""
Issue #21, Track C, Experiment 2: sequence animal expansion behind land.

v0 isolated the collapse to MAX_ANIMALS alone (4 -> 8, nothing else changed):
self-play mean ~$418, EVERY seed ending at 25 tiles / 0 hands / $3,000
starting stake barely touched. v1 added a cash-reserve floor on animal
purchases (the fix that worked for seed buying and for phase3's animal
buying) - it did NOT help (mean ~$431, same 25-tile/0-hand collapse).

Read directly off the end-of-episode structural state (not inferred): land
is never bought, hands are never hired. That is a different mechanism than
the brief's "Fibonacci hiring cost" and "day-11 poverty trap" - the crew and
land purchases documented as already working (bigfarm_opponent.py alone: 75
tiles, 4 animals, self-play mean $59,018, 6/6 seeds, 0 collapses) never even
get a chance to run, because a HIGHER MAX_ANIMALS changes something upstream
of them.

The mechanism, read off decide_animal_market_actions and land_order:
  - Animal buying fires every turn: "one purchase at a time" whenever
    count_owned_animals < MAX_ANIMALS and the next species clears
    ANIMAL_SPEND_CAP_FRACTION (a 2x-cost affordability bar, cost <=
    money * 0.5) - a LOW bar an early trickle of crop income crosses
    constantly.
  - land_order needs a much bigger lump sum: LAND_PRICES[0] (1000) +
    LAND_CASH_RESERVE (450) = $1,450 before it fires at all.
  - At MAX_ANIMALS=4, four purchases (~$400-500 each, ~$1,800 total) empty
    the slots quickly and then STOP, letting cash accumulate toward land's
    $1,450 bar. At MAX_ANIMALS=8, a slot is open for roughly twice as long,
    so every time cash crosses ~$450-500 it gets siphoned into another
    animal instead of accumulating - land's bar is never reached, hiring
    demand (driven by tile count) never grows past a 25-tile farm, and the
    agent is stuck.

v1's $450 reserve floor doesn't fix this: $450 left over is nowhere close
to land's $1,450 requirement, so the siphon still empties every dollar the
moment the next animal is affordable again.

Hypothesis for this experiment: don't remove the fraction-of-cash
opportunism (that's proven to work for the FIRST 4 animals, per
bigfarm_opponent.py's own measurement, and per the docs, "4 works, 5
collapses" against main.py too). Instead, sequence it - hold animal count
at MAX_ANIMALS_BEFORE_LAND (4) until BOTH land quadrants are bought, then
let it run to MAX_ANIMALS (8). This lets the already-proven early economy
(4 animals + 2 land buys + up-to-15 crew, worth $59,018 self-play alone)
establish itself first, and only spends the *surplus* income a bigger farm
produces on the extra animals - which is also closer to what
docs/REPLAY_ANALYSIS.md actually shows (land bought days 6-11, animal count
building out over the following weeks, not competing with land for the
same early dollars).

Structural checks: does land get bought this time (tiles should hit 75)?
Does hand count recover? Does animal count still reach somewhere near 8, or
does the new gate itself become a new bottleneck (worth knowing either way)?
"""
import os
import sys


def _find_repo_root():
    """See large_farm_opponent_v0.py's copy of this function - the
    kaggle_environments agent loader intermittently exec's this file with
    no `__file__` present, so a fixed dirname()-hop-count guess is wrong
    some fraction of the time. Verify against main.py instead."""
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
MAX_ANIMALS_BEFORE_LAND = 4          # bigfarm_opponent.py's own proven count
MIN_CASH_RESERVE_FOR_ANIMAL_BUYING = 450   # v1's fix, kept - see its docstring

base.MAX_ANIMALS = MAX_ANIMALS


def _land_fully_bought(farm):
    # bigfarm_opponent.py caps purchases at len(LAND_BUY_DAYS) == 2 quadrants
    # (see its own module docstring/comments) - there's no separately named
    # constant for that count, so mirror the same number here.
    bought = len(farm.get("unlocked_quadrants") or ["NW"]) - 1
    return bought >= len(base_opponent.LAND_BUY_DAYS)


def _animal_cap(farm):
    return MAX_ANIMALS if _land_fully_bought(farm) else MAX_ANIMALS_BEFORE_LAND


def _choose_animal_to_build(farm, private, board_size, day, pending_builds=0):
    cap = _animal_cap(farm)
    filled, unfilled = base.scan_animal_structures(farm, board_size)
    if unfilled > 0 or pending_builds > 0 or filled >= cap:
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
    cap = _animal_cap(farm)
    actions = []
    money = farm.get("money", 0)
    remaining_days = base.remaining_season_days(day)

    if base.count_owned_animals(farm, private, board_size) < cap:
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


def large_farm_opponent_v2(obs):
    return base_opponent.bigfarm_opponent(obs)


agent = large_farm_opponent_v2
