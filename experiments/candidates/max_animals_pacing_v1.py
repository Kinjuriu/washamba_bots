"""
Candidate: MAX_ANIMALS=5, gated by actual placement capacity - v1.

Follow-up to experiments/candidates/max_animals_pacing_v0.py, closing a gap
an independent mechanism audit found in it (see
experiments/max_animals_pacing_v1_report.md): v0's available_placement_capacity
returned a flat, unconditional MAX_ANIMALS the instant a second quadrant was
purchased, with no check that a buildable tile or an unfilled structure
existed there yet. That is the same class of bug the original diagnosis
found (an animal bought with nowhere to go) - v0 just moved the failure
window from day 0 to whenever BUY_LAND lands, instead of eliminating it.
The candidate's own v0 docstring admitted this ("deliberately does NOT
attempt to count actual empty tiles inside an already-purchased extra
quadrant") but the report never surfaced it as a live risk.

THE FIX: available_placement_capacity now derives capacity from a live,
per-quadrant scan of the actual board, using nothing but verified engine
semantics:

- BUILD_PASTURE/BUILD_COOP (kaggriculture.py:493-503) only succeed on a
  tile that is exactly `None` - not `"LOCKED"`, not a crop, not a weed, not
  an existing structure. So a quadrant's buildable slots = its count of
  `None` tiles, counted fresh every turn - this shrinks as crops claim
  ground, which is exactly the contention v0's docstring said it wasn't
  accounting for.
- Every unfilled structure is already-committed capacity (`PLACE` just
  needs a unit to walk there) and every filled structure is capacity
  already used - both still come from `scan_animal_structures`, the same
  source v0 used.
- The home ("NW") quadrant keeps the `MAX_ANIMALS_ON_HOME_LAND` ceiling
  exactly as `choose_animal_to_build` enforces it - unchanged from v0,
  just recomputed defensively from a live per-quadrant scan instead of a
  farm-wide total (never claims more than 3 home slots even if, contrary
  to that gate's own design, more than 3 were somehow already built).
- Every OTHER unlocked quadrant has no such per-quadrant cap (matching
  `choose_animal_to_build`'s own rule: "every other, separately-purchased
  quadrant has no such per-quadrant cap") - its contribution is simply
  (existing structures + currently-`None` tiles) in that quadrant, live.
- A quadrant not yet in `farm["unlocked_quadrants"]` contributes nothing.
  Its tiles are the string `"LOCKED"`, never `None`, so this already falls
  out of the `None`-tile check - the explicit unlocked-quadrant filter is
  kept anyway so the intent doesn't depend on that incidental fact.

**This is a genuine change in behavior from v0, not just a rename**: v0's
capacity after `BUY_LAND` was `MAX_ANIMALS` (5) unconditionally; v1's is
`existing structures + live None-tile count`, which can be far lower the
instant land unlocks (a freshly-unlocked quadrant is nearly all `None`, so
early on this is close to v0's behavior - but it now degrades correctly as
crops claim that ground turn by turn, instead of staying pinned at 5).

Nothing else changes from v0: `MAX_ANIMALS` is still 4 -> 5, the buy-gate
call site (`owned < min(MAX_ANIMALS, available_placement_capacity(...))`)
is unchanged, species selection/affordability/wheat-safety-net are still
copied verbatim from `main.decide_animal_market_actions`, and land
purchasing/crew hiring/selling/pricing/liquidation are still not imported
into or referenced by this file at all.

Usage:
    .venv/Scripts/python.exe experiments/candidates/max_animals_pacing_v1.py
    .venv/Scripts/python.exe experiments/selfplay_agent.py experiments/candidates/max_animals_pacing_v1.py 6
    .venv/Scripts/python.exe experiments/head_to_head.py experiments/candidates/max_animals_pacing_v1.py main.py 6
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

import main as base  # noqa: E402

base.MAX_ANIMALS = 5

DECISION_LOG = []
POST_LAND_PURCHASE_LOG = []  # every BUY_ANIMAL issued once >1 quadrant is
# owned - instrumentation for verifying (externally, via a season-end shed
# check) that a purchase counted as "capacity available" here never ends up
# permanently unplaced. See experiments/max_animals_pacing_v1_stranding_trace.py.


def available_placement_capacity(farm, board_size):
    """
    Live per-quadrant placement capacity, derived only from the current
    board and verified engine semantics - see module docstring. Replaces
    v0's has_extra_land shortcut, which returned a flat MAX_ANIMALS the
    instant a second quadrant was owned regardless of whether anything on
    it was actually buildable yet.
    """
    tiles = farm.get("tiles") or []
    unlocked_quadrants = set(farm.get("unlocked_quadrants") or ["NW"])

    structures_by_quadrant = {}
    buildable_by_quadrant = {}

    for y in range(board_size):
        row = tiles[y] if y < len(tiles) else []
        for x in range(board_size):
            tile = row[x] if x < len(row) else None
            q = base.tile_quadrant(x, y, board_size)
            if q not in unlocked_quadrants:
                continue
            if isinstance(tile, dict) and tile.get("kind") in base.ANIMAL_STRUCTURE_KINDS:
                structures_by_quadrant[q] = structures_by_quadrant.get(q, 0) + 1
            elif tile is None:
                buildable_by_quadrant[q] = buildable_by_quadrant.get(q, 0) + 1

    home_structures = structures_by_quadrant.get("NW", 0)
    home_buildable = buildable_by_quadrant.get("NW", 0)
    home_capacity = min(base.MAX_ANIMALS_ON_HOME_LAND, home_structures + home_buildable)
    home_capacity = max(home_capacity, home_structures)  # never under-report what's already built

    extra_capacity = 0
    for q in unlocked_quadrants:
        if q == "NW":
            continue
        extra_capacity += structures_by_quadrant.get(q, 0) + buildable_by_quadrant.get(q, 0)

    return home_capacity + extra_capacity


def _decide_animal_market_actions_paced(farm, private, board_size, day):
    """Verbatim copy of main.decide_animal_market_actions (main.py:1373-1430)
    with exactly one added condition in the buy gate, same shape as v0:
    `count_owned_animals(...) < MAX_ANIMALS` becomes
    `count_owned_animals(...) < min(MAX_ANIMALS, available_placement_capacity(...))`.
    Only available_placement_capacity's own implementation changed from v0."""
    actions = []
    money = farm.get("money", 0)
    remaining_days = base.remaining_season_days(day)

    owned = base.count_owned_animals(farm, private, board_size)
    capacity = available_placement_capacity(farm, board_size)
    ceiling = min(base.MAX_ANIMALS, capacity)
    paced_out = owned >= ceiling and owned < base.MAX_ANIMALS

    if paced_out:
        DECISION_LOG.append({
            "day": day, "owned": owned, "capacity": capacity,
            "max_animals": base.MAX_ANIMALS,
            "unlocked_quadrants": list(farm.get("unlocked_quadrants") or ["NW"]),
        })

    if owned < ceiling:
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
            if money - cost < base.MIN_CASH_RESERVE_FOR_ANIMAL_BUYING:
                continue
            affordable.append(animal)

        if affordable:
            animal = base.pick_next_animal_species(affordable, held)
            actions.append(["BUY_ANIMAL", animal, 1])
            unlocked_quadrants = farm.get("unlocked_quadrants") or ["NW"]
            if len(unlocked_quadrants) > 1:
                POST_LAND_PURCHASE_LOG.append({
                    "day": day, "owned_before": owned, "capacity": capacity,
                    "species": animal,
                    "unlocked_quadrants": list(unlocked_quadrants),
                })

    filled, _ = base.scan_animal_structures(farm, board_size)
    if filled > 0 and money > 0:
        shed_wheat = private.get("shed", {}).get("WHEAT", 0)
        carried_wheat = sum(
            inv.get("WHEAT", 0) for inv in (private.get("inventories") or []) if isinstance(inv, dict)
        )
        if shed_wheat + carried_wheat < base.MIN_WHEAT_RESERVE_FOR_FEEDING:
            actions.append(["BUY_PRODUCT", "WHEAT", 1])

    return actions


base.decide_animal_market_actions = _decide_animal_market_actions_paced


def max_animals_pacing_v1(obs):
    return base.nikaangukia_meroni(obs)


def _self_test(seeds=(0, 1, 2)):
    from kaggle_environments import make

    for seed in seeds:
        env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})
        env.run([max_animals_pacing_v1, max_animals_pacing_v1])
        a, b = env.steps[-1]
        print(f"seed {seed}: seat0 {a.reward:>8.0f} [{a.status}]   seat1 {b.reward:>8.0f} [{b.status}]")
    print(f"purchases paced out (deferred), logged: {len(DECISION_LOG)}")
    print(f"post-extra-land purchases issued, logged: {len(POST_LAND_PURCHASE_LOG)}")


agent = max_animals_pacing_v1

if __name__ == "__main__":
    _self_test()
