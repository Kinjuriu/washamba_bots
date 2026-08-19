"""
Issue #21, Track C, Experiment 5: a PACED animal-purchase ramp (4 -> 8), not
a single-step MAX_ANIMALS bump.

CONTEXT (see docs/candidate_reports/track_c_large_farm.md for the full log):
Experiments 0-4 last session all pushed MAX_ANIMALS from 4 straight to 8 in
one step - with no reserve floor (Exp 0), a flat $450 reserve floor (Exp 1),
a land-bought gate (Exp 2/3), and a land-bought-plus-$2,000-buffer gate
(Exp 4). All five reached at most $7,806 self-play mean, versus main.py's
own $59-63k at MAX_ANIMALS=4. Exp 3's per-turn trace proved the mechanism:
MAX_ANIMALS correctly stays at 4 through day 11 (identical to the working
baseline), then jumps straight to 8 the moment land is fully bought - and
that ONE-STEP jump, landing right on the second land payment, triggers a
cash crisis the crew/hiring machinery never recovers from for the rest of
the season, even though the days-0-11 trajectory was, by construction,
already proven-good.

Separately, `experiment/animal-cliff` (already merged as a branch, not into
main) tried a *scaling* reserve (`ANIMAL_FEED_RESERVE_PER_ANIMAL * (owned+1)`)
and also failed - 0/3 wins on every swept value, seed 1 collapsing to $443.
Reading that branch's own diff closely: the scaling reserve was added ONLY
to decide_animal_market_actions (the BUY step), while choose_animal_to_build
(the structure-build step) kept using the plain `filled >= MAX_ANIMALS`
check with MAX_ANIMALS already raised. That mismatch is exactly how you
strand a pasture: the build step is happy to start pasture #5 the instant
MAX_ANIMALS allows it, the buy step then refuses to fill it because the
reserve isn't clear yet, and choose_animal_to_build's own "don't build
another while one sits unfilled" guard then blocks all further animal
progress for the rest of the season - a real, identifiable implementation
bug in that experiment, not evidence the scaling-reserve idea itself is
unsound.

THIS EXPERIMENT tests a policy built from both lessons directly, not from
retuning a constant blindly:

  1. Preserve main.py's own proven 4-animal/land-gated behaviour exactly -
     MAX_ANIMALS effectively stays 4 (main.py's own shipped default) until
     BOTH land quadrants are bought (read straight from main.py's own
     `unlocked_quadrants` / `LAND_BUY_DAYS`, no separate land logic of our
     own - main.py already buys land natively via decide_land_orders, so
     this experiment does not touch land at all).
  2. Only once land is fully bought does the cap start rising, ONE slot at
     a time (5, 6, 7, 8) - never a single jump.
  3. Each additional slot requires ITS OWN, progressively larger cash
     reserve before it opens: reserve(slot k) = ANIMAL_RAMP_RESERVE_PER_SLOT
     * (k - MAX_ANIMALS_BASE), so slot 5 needs $500 free, slot 6 needs
     $1,000, slot 7 needs $1,500, slot 8 needs $2,000 - "a fresh economic
     condition before each additional animal," not one global gate, and
     escalating to reflect that a bigger herd's daily feed bill is bigger
     too.
  4. The SAME effective cap is read by BOTH choose_animal_to_build (build)
     and decide_animal_market_actions (buy), computed once per turn from
     live farm state - not two independently-tuned checks. This is the
     direct fix for animal-cliff's stranding bug: a pasture can never be
     started for a slot the buy step isn't also cleared to fill, because
     they consult the identical cap value.
  5. Nothing else changes. choose_animal_to_build's own existing "refuse
     while one structure sits unfilled" guard, its season-maturity check,
     and pick_next_animal_species (species selection) are copied verbatim,
     untouched - this experiment is isolated to WHEN the cap allows the
     next animal, not WHICH animal or WHETHER to build at all otherwise.

WHAT THIS EXPERIMENT DOES NOT TOUCH: crop scoring, pricing, hiring, selling,
land-purchase logic, or fertilizer/wheat feed-safety-net logic - all copied
verbatim from main.py where reused, so a Kaggle score change can be
attributed to the animal-ramp pacing policy specifically.

Usage:
    .venv/Scripts/python.exe experiments/candidates/large_farm_opponent_v5_paced_ramp.py   # self-test
    .venv/Scripts/python.exe experiments/selfplay_agent.py experiments/candidates/large_farm_opponent_v5_paced_ramp.py 6
    .venv/Scripts/python.exe experiments/head_to_head.py experiments/candidates/large_farm_opponent_v5_paced_ramp.py main.py 6
"""
import os
import sys


def _find_repo_root():
    """kaggle_environments' agent loader intermittently exec's this file
    into a namespace with no `__file__` present at all (observed directly
    last session - a fixed dirname()-hop-count fallback was silently wrong
    some fraction of the time and produced ModuleNotFoundError mid-episode).
    Walk up from cwd and verify against main.py instead of guessing."""
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

# ---------------------------------------------------------------------
# Paced animal ramp
# ---------------------------------------------------------------------
MAX_ANIMALS_BASE = 4        # main.py's own shipped default - unchanged below it
MAX_ANIMALS_CEILING = 8     # replay-observed range is 8-9; even split across 2 species
ANIMAL_RAMP_RESERVE_PER_SLOT = 500   # $ that must be free before slot k opens


def _land_fully_bought(farm):
    """Reads main.py's own LAND_BUY_DAYS length as "how many quadrants we
    intend to buy" rather than hardcoding a second copy of that number -
    this experiment does not define any land policy of its own."""
    bought = len(farm.get("unlocked_quadrants") or ["NW"]) - 1
    return bought >= len(base.LAND_BUY_DAYS)


def effective_animal_cap(farm):
    """
    The animal count we're allowed to build/buy toward THIS turn.

    Stays at MAX_ANIMALS_BASE (main.py's own default - byte-identical
    behaviour to shipped main.py) until land is fully bought. After that,
    opens one slot at a time, each gated on its own reserve requirement -
    slot k needs `ANIMAL_RAMP_RESERVE_PER_SLOT * (k - MAX_ANIMALS_BASE)`
    left over after paying for the animal itself. Recomputed fresh every
    turn from live cash, so if spending later drops cash below what a
    just-opened slot needed, the cap quietly retracts and no FURTHER slot
    opens - it never un-builds an animal or structure already committed to,
    it only gates the NEXT one, the same way the two decision points below
    always did for MAX_ANIMALS itself.
    """
    if not _land_fully_bought(farm):
        return MAX_ANIMALS_BASE

    money = farm.get("money", 0)
    cap = MAX_ANIMALS_BASE
    for k in range(MAX_ANIMALS_BASE + 1, MAX_ANIMALS_CEILING + 1):
        reserve_needed = ANIMAL_RAMP_RESERVE_PER_SLOT * (k - MAX_ANIMALS_BASE)
        if money < reserve_needed:
            break
        cap = k
    return cap


def _choose_animal_to_build(farm, private, board_size, day, pending_builds=0):
    """Verbatim copy of main.choose_animal_to_build, with the one bare
    `MAX_ANIMALS` read replaced by `effective_animal_cap(farm)`. Every
    other check - the unfilled-structure guard, the season-maturity gate,
    species selection - is untouched."""
    cap = effective_animal_cap(farm)
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
        if money >= cost and cost <= money * base.ANIMAL_SPEND_CAP_FRACTION:
            eligible.append(animal)
    return base.pick_next_animal_species(
        eligible, base.species_owned_counts(farm, private, board_size)
    )


def _decide_animal_market_actions(farm, private, board_size, day):
    """Verbatim copy of main.decide_animal_market_actions, with the same
    single substitution: `MAX_ANIMALS` -> `effective_animal_cap(farm)`,
    computed identically to the build-side check above so a structure is
    never started for a slot the purchase can't also clear. The feed
    BUY_PRODUCT safety net is untouched."""
    cap = effective_animal_cap(farm)
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


def large_farm_opponent_v5_paced_ramp(obs):
    return base.nikaangukia_meroni(obs)


def _self_test(seeds=(0, 1, 2)):
    from kaggle_environments import make

    for seed in seeds:
        env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})
        env.run([large_farm_opponent_v5_paced_ramp, large_farm_opponent_v5_paced_ramp])
        a, b = env.steps[-1]
        print(f"seed {seed}: seat0 {a.reward:>8.0f} [{a.status}]   seat1 {b.reward:>8.0f} [{b.status}]")


agent = large_farm_opponent_v5_paced_ramp

if __name__ == "__main__":
    _self_test()
