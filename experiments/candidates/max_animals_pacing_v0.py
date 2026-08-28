"""
Candidate: MAX_ANIMALS=5, gated by actual placement capacity.

Follow-up to experiments/max_animals_cliff_diagnosis.md (classification A):
`decide_animal_market_actions` issues `BUY_ANIMAL` against the flat
`MAX_ANIMALS` cap and cash affordability only - it never checks whether
the animal being bought has anywhere to go. `choose_animal_to_build`
already refuses to build a *second* empty structure while a first sits
unfilled (`if unfilled > 0: return None`) - the exact restraint the
buying side lacks. On the traced seed, the 5th animal was bought on day
0, six days before `LAND_BUY_START_DAY=6` even opens the land it would
need (`MAX_ANIMALS_ON_HOME_LAND=3` forces animals 4 and 5 onto land not
yet purchased), sat unplaced in the shed for the rest of the season, and
its sunk cost collided with the day ~6-12 land/crew cash window that a
healthy MAX_ANIMALS=4 run absorbs without incident.

THE ONE CHANGE: `decide_animal_market_actions`'s existing gate
(`count_owned_animals(...) < MAX_ANIMALS`) gets ONE additional condition -
never buy past what current land ownership can actually support. Nothing
else in the function changes: species selection (`pick_next_animal_species`),
affordability checks (`ANIMAL_SPEND_CAP_FRACTION`,
`MIN_CASH_RESERVE_FOR_ANIMAL_BUYING`), and the wheat safety net are all
copied verbatim. Land purchasing (`decide_land_orders`), crew hiring
(`decide_hire_orders`), selling (`decide_market_actions`), and liquidation
are completely untouched - this candidate imports `main` and patches
exactly two names: `MAX_ANIMALS` (4 -> 5) and
`decide_animal_market_actions`.

ENGINE SEMANTICS THIS CANDIDATE'S CAPACITY CALCULATION IS BUILT FROM
(verified against the installed engine before writing this, not assumed):

- `BUY_ANIMAL` (kaggriculture.py:679-687) only ever deposits into
  `private["shed"][item]` - it never touches a tile. A bought animal has
  no location at all until a unit carries and places it.
- `PLACE` (kaggriculture.py:377-392) only succeeds when the acting unit
  is standing on a tile that is already a matching structure
  (`tile["kind"] == ANIMALS[item]["structure"]`) with no `"animal"` key
  yet - i.e. an *unfilled* structure. There is no way to place an animal
  anywhere else.
- `BUILD_PASTURE`/`BUILD_COOP` (kaggriculture.py:493-503) only succeeds
  on a completely empty tile (`tile is None`) - not on a weed, not on a
  locked tile, not on an existing structure.
- `main.py`'s own `scan_animal_structures` (main.py:1216-1234) is the
  single source of truth this repo already uses for "how many structures
  exist, filled vs. not" - both `choose_animal_to_build`'s build-gate and
  this candidate's buy-gate are built directly on its `(filled, unfilled)`
  output, not a re-derived duplicate.
- `choose_animal_to_build`'s own eligibility rule (main.py:1297-1372) is
  the existing source of truth for land eligibility: any built-or-buildable
  slot on the home ("NW") quadrant is capped at
  `MAX_ANIMALS_ON_HOME_LAND`; every other, separately-purchased quadrant
  has no such per-quadrant cap (only the flat `MAX_ANIMALS` ceiling
  applies there). `farm["unlocked_quadrants"]` (always `["NW"]` until
  `BUY_LAND` lands, per `decide_land_orders`'s own established read of
  it) is what tells us whether that extra land exists yet.

`available_placement_capacity`, below, is a farm-wide, per-turn version
of exactly that same eligibility rule - not a new economic score, not a
new threshold, no unrelated engine field. It answers "how many
`ACTIVE_ANIMALS` structures could current land ownership support right
now" and nothing more. It deliberately does NOT attempt to count actual
empty tiles inside an already-purchased extra quadrant (crops may have
already claimed some of them) - that finer-grained contention is a
separate, broader question this candidate does not take on; see the
report's scope note.

Usage:
    .venv/Scripts/python.exe experiments/candidates/max_animals_pacing_v0.py   # self-test
    .venv/Scripts/python.exe experiments/selfplay_agent.py experiments/candidates/max_animals_pacing_v0.py 6
    .venv/Scripts/python.exe experiments/head_to_head.py experiments/candidates/max_animals_pacing_v0.py main.py 6
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


def available_placement_capacity(farm, board_size):
    """How many ACTIVE_ANIMALS structures current land ownership can
    support right now - existing structures (filled + unfilled, from
    main.py's own scan_animal_structures) if no extra land is owned yet,
    capped at MAX_ANIMALS_ON_HOME_LAND (mirroring choose_animal_to_build's
    own home-quadrant restriction exactly); once at least one extra
    quadrant has been purchased, that per-quadrant cap no longer applies
    anywhere, so the only remaining ceiling is MAX_ANIMALS itself.
    """
    filled, unfilled = base.scan_animal_structures(farm, board_size)
    existing_structures = filled + unfilled

    unlocked_quadrants = farm.get("unlocked_quadrants") or ["NW"]
    has_extra_land = len(unlocked_quadrants) > 1

    if has_extra_land:
        return base.MAX_ANIMALS
    return max(existing_structures, base.MAX_ANIMALS_ON_HOME_LAND)


def _decide_animal_market_actions_paced(farm, private, board_size, day):
    """Verbatim copy of main.decide_animal_market_actions
    (main.py:1373-1424) with exactly one added condition in the buy gate:
    `count_owned_animals(...) < MAX_ANIMALS` becomes
    `count_owned_animals(...) < min(MAX_ANIMALS, available_placement_capacity(...))`.
    Species selection, affordability checks, and the wheat safety net are
    unchanged."""
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


def max_animals_pacing_v0(obs):
    return base.nikaangukia_meroni(obs)


def _self_test(seeds=(0, 1, 2)):
    from kaggle_environments import make

    for seed in seeds:
        env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})
        env.run([max_animals_pacing_v0, max_animals_pacing_v0])
        a, b = env.steps[-1]
        print(f"seed {seed}: seat0 {a.reward:>8.0f} [{a.status}]   seat1 {b.reward:>8.0f} [{b.status}]")
    print(f"purchases paced out (deferred), logged: {len(DECISION_LOG)}")


agent = max_animals_pacing_v0

if __name__ == "__main__":
    _self_test()
