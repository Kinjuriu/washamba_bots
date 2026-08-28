"""
Candidate B (architecture experiment) - a generic opponent-state
representation, wired into exactly two existing decisions.

CONTEXT: docs/architecture_comparison.md found `main.py` has zero cross-turn
memory and reads the opponent's public farm for exactly one narrow purpose
(a crude standing-crop count feeding crop-choice's price forecast). This
candidate tests the isolated hypothesis: does giving *already-existing*
decision logic a fuller, generic, directly-observable picture of the
opponent change what it decides, without inventing any new decision axis?

HYPOTHESIS (bidirectional, must be able to fail, per the task): "Our agent
is disadvantaged because its decisions are insufficiently conditioned on the
actual opponent. Giving the agent a structured representation of observable
opponent state should allow existing decision logic to react differently to
different opponent behaviors." Might not hold - if the two decisions this
candidate enriches never actually receive opponent state different enough to
matter, or if reacting to it doesn't help, both are real, reportable
answers. See the report for which one this is.

WHAT IS EXPLICITLY OUT OF SCOPE HERE (per the task's own constraints):
mirror-aware sell timing (candidate D), adaptive routing/land-shape switching
(candidate C), any hardcoded competitor fingerprint, any code copied from
route_moon_*/route_v20. Nothing here reads a competitor's identity or a
specific known build signature - every signal is a generic aggregate
(tile counts, yields, money, hand count) that would be computed the same way
against any opponent, including one that has never been observed before.

TWO existing decisions are touched, and only two - "minimize the number of
changed decisions," per the task:

1. **Crop choice** (`choose_crop`, called from both `choose_unit_action`'s
   PLANT branch and `decide_market_actions`'s BUY_SEED restock call - both
   call sites are UNPATCHED, and both already thread an `opponent_pipeline`
   argument through `state["opponent_pipeline"]`, which is built once per
   turn by `count_opponent_pipeline`). This candidate patches
   `count_opponent_pipeline` to return the *exact* standing yield
   (`tile["yield_units"]`, the quantity HARVEST would actually move to
   inventory right now - see experiments/opponent_supply_forecast_audit.md
   and experiments/opponent_aware_sell_gate_exact_yield_report.md, both from
   an earlier session today) instead of a flat `crop_info["max_yield"]`
   ceiling assumed the instant any tile of that crop exists. Same call
   sites, same parameter, richer input - no new decision, a more accurate
   version of the one crop choice already made.

2. **Animal species choice** (`pick_next_animal_species`, called from inside
   `choose_animal_to_build`, itself called from `choose_unit_action`'s empty-
   ground branch - UNPATCHED). Previously ranked eligible species purely by
   which we own fewest of, with zero opponent awareness at all - this
   candidate adds the opponent's per-species tile count as a SECONDARY
   tiebreak only: prefer the species the opponent has fewer of, but only
   when our own herd is already tied on the primary criterion. This directly
   generalises the same "don't pile into what's already crowded" principle
   `choose_crop`'s own demand-absorption term already uses for crops, to
   animals, where no such signal existed before.

ARCHITECTURE: exactly the shape the task asked for - a single
`extract_opponent_state(obs)` snapshot, computed once per turn as a side
effect of the one function (`count_opponent_pipeline`) `main.py` already
calls once per turn, cached in a module-level slot, and read by the two
patched decision functions. No new parameter is threaded through
`choose_unit_action`/`decide_market_actions`/`nikaangukia_meroni` - none of
those are patched at all, so this candidate's total surface area is three
functions: `count_opponent_pipeline`, `choose_crop` (wrapped, not
reimplemented - see below), and `pick_next_animal_species`.

INSTRUMENTATION: both patched decision functions call the ORIGINAL,
unmodified logic a second time with what the OLD, opponent-blind baseline
would have seen, and log a record whenever the two decisions actually
differ, with the specific opponent-state fact that caused it. This is what
answers "which decisions changed because of opponent state" in the report -
not inferred after the fact, computed at decision time.

Usage:
    .venv/Scripts/python.exe experiments/candidates/opponent_state_v0.py   # self-test
    .venv/Scripts/python.exe experiments/selfplay_agent.py experiments/candidates/opponent_state_v0.py 12
    .venv/Scripts/python.exe experiments/head_to_head.py experiments/candidates/opponent_state_v0.py main.py 12
"""
import os
import sys


def _find_repo_root():
    """Same defensive walk-up as every other candidate in this directory -
    see opponent_aware_sell_gate.py's docstring for why a fixed
    dirname()-hop-count fallback is unsafe here."""
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
# 1. Generic opponent-state extraction
# ---------------------------------------------------------------------

def extract_opponent_state(obs):
    """A single, generic snapshot of everything genuinely observable about
    the opponent this turn, from `obs["farms"][1-player]` - the exact same
    public object main.py's own `count_opponent_pipeline` already reads,
    widened to cover more of what's actually sitting in it. Nothing here
    reads `obs["private"]` for the opponent (impossible - a live agent
    never receives it, only its own), nothing infers past actions, and
    nothing is keyed to a specific competitor's identity or a hardcoded
    signature - nothing here would behave any differently against an
    opponent nobody on this team has ever seen before.

    Deliberately NOT included, and why:
    - opponent shed/inventory: private, never visible to a live agent.
    - opponent recent actions/sales: `obs` carries no action log (see
      experiments/opponent_supply_forecast_audit.md's observability
      section) - reconstructing this from turn-to-turn market-inventory
      deltas would require cross-turn memory this repo's architecture
      doesn't have yet, and conflating "add state" with "add memory" in
      one candidate would make it impossible to attribute a result to
      either change cleanly. Left for a dedicated follow-up candidate,
      not silently assumed away.

    Returns None if the opponent's farm isn't present in this observation
    at all (defensive - matches main.py's own `count_opponent_pipeline`
    guard).
    """
    farms = obs.get("farms") or []
    player = obs.get("player", 0)
    if len(farms) < 2:
        return None
    opponent = farms[1 - player] or {}
    tiles = opponent.get("tiles") or []

    crop_standing_yield = {}
    crop_tile_count = {}
    animal_standing_yield = {}
    animal_tile_count = {}
    land_tiles_owned = 0

    for row in tiles:
        for tile in row:
            if tile == "LOCKED":
                continue
            land_tiles_owned += 1
            if not isinstance(tile, dict):
                continue
            if tile.get("kind") == "PLANT":
                crop = tile.get("crop")
                crop_tile_count[crop] = crop_tile_count.get(crop, 0) + 1
                crop_standing_yield[crop] = crop_standing_yield.get(crop, 0) + tile.get("yield_units", 0)
            elif "animal" in tile:
                species = tile.get("animal")
                animal_tile_count[species] = animal_tile_count.get(species, 0) + 1
                animal_standing_yield[species] = animal_standing_yield.get(species, 0) + tile.get("yield_units", 0)

    total_planted = sum(crop_tile_count.values())
    # Herfindahl-style concentration over PLANTED tiles (0 = perfectly
    # diversified across every crop, 1 = a monoculture) - "opponent crop
    # concentration" from the task's own list, computed generically from
    # whatever crops happen to be present, not a fixed crop list.
    crop_concentration = (
        sum((count / total_planted) ** 2 for count in crop_tile_count.values())
        if total_planted else 0.0
    )

    return {
        "land_tiles_owned": land_tiles_owned,
        "hand_count": len(opponent.get("hands") or []),
        "money": opponent.get("money", 0),
        "crop_standing_yield": crop_standing_yield,
        "crop_tile_count": crop_tile_count,
        "animal_standing_yield": animal_standing_yield,
        "animal_tile_count": animal_tile_count,
        "crop_concentration": crop_concentration,
        "dominant_crop": (max(crop_tile_count, key=crop_tile_count.get) if crop_tile_count else None),
        "dominant_animal": (max(animal_tile_count, key=animal_tile_count.get) if animal_tile_count else None),
    }


def _exact_crop_supply(opponent_state):
    """The crop-side piece of extract_opponent_state, in the exact shape
    choose_crop already expects (a plain {crop: units} dict) - reused
    directly as the new opponent_pipeline value, not a second copy of the
    tile-scanning loop."""
    if not opponent_state:
        return {}
    return dict(opponent_state.get("crop_standing_yield") or {})


# ---------------------------------------------------------------------
# 2. Side channel: one snapshot per turn, cached where the two patched
#    decisions can read it without any new parameter threaded through
#    choose_unit_action / decide_market_actions / nikaangukia_meroni.
# ---------------------------------------------------------------------

_last_opponent_state = None
_last_crude_pipeline = None
_original_count_opponent_pipeline = base.count_opponent_pipeline


def _count_opponent_pipeline_opponent_state_v0(obs):
    """Wraps the ORIGINAL count_opponent_pipeline: computes the generic
    opponent-state snapshot and the exact-yield crop supply as side
    effects, caches both, and returns the exact-yield supply as this
    turn's opponent_pipeline - the one deliberate behavioural change to
    crop choice's existing opponent-aware input. The ORIGINAL (crude,
    max_yield-per-tile) computation is preserved unchanged and cached too,
    purely so choose_crop's wrapper (below) can log when the richer signal
    actually would have changed the decision."""
    global _last_opponent_state, _last_crude_pipeline
    _last_opponent_state = extract_opponent_state(obs)
    _last_crude_pipeline = _original_count_opponent_pipeline(obs)
    return _exact_crop_supply(_last_opponent_state)


base.count_opponent_pipeline = _count_opponent_pipeline_opponent_state_v0


# ---------------------------------------------------------------------
# 3. Instrumentation logs - what changed, and why
# ---------------------------------------------------------------------

CROP_DECISION_LOG = []
ANIMAL_DECISION_LOG = []


# ---------------------------------------------------------------------
# 4. Crop choice: same call sites, richer opponent_pipeline, logged
# ---------------------------------------------------------------------

_original_choose_crop = base.choose_crop


def _choose_crop_opponent_state_v0(
    farm, market_state, private, day, unlocked_shops=(), start_step=None,
    opponent_pipeline=None,
):
    """Thin wrapper, not a reimplementation: calls the ORIGINAL choose_crop
    unchanged, with whatever opponent_pipeline it was actually given (which
    is now the exact-yield version, because count_opponent_pipeline is
    patched above - this function does not need to know that). Separately,
    for logging only, calls the same original function again with the
    cached CRUDE pipeline to see what the opponent-blind-upgrade baseline
    would have picked, and records a trace entry when the two disagree."""
    real_decision = _original_choose_crop(
        farm, market_state, private, day,
        unlocked_shops=unlocked_shops, start_step=start_step,
        opponent_pipeline=opponent_pipeline,
    )

    crude_pipeline = _last_crude_pipeline or {}
    exact_pipeline = opponent_pipeline or {}
    if crude_pipeline != exact_pipeline:
        baseline_decision = _original_choose_crop(
            farm, market_state, private, day,
            unlocked_shops=unlocked_shops, start_step=start_step,
            opponent_pipeline=crude_pipeline,
        )
        if baseline_decision != real_decision:
            CROP_DECISION_LOG.append({
                "day": day,
                "baseline_decision": baseline_decision,
                "candidate_decision": real_decision,
                "exact_opponent_supply": dict(exact_pipeline),
                "crude_opponent_supply": dict(crude_pipeline),
            })

    return real_decision


base.choose_crop = _choose_crop_opponent_state_v0


# ---------------------------------------------------------------------
# 5. Animal species choice: opponent-count tiebreak, logged
# ---------------------------------------------------------------------

_original_pick_next_animal_species = base.pick_next_animal_species


def _pick_next_animal_species_opponent_state_v0(eligible, owned_counts):
    """Identical to the original whenever `owned_counts` alone already
    breaks the tie among `eligible` species - the opponent's counts are
    consulted ONLY as a secondary key, after our own herd balance, before
    the final ACTIVE_ANIMALS-order tiebreak the original used. This is the
    property tests/test_opponent_state_v0.py's identical-when-irrelevant
    tests check directly."""
    if not eligible:
        return None

    baseline_pick = _original_pick_next_animal_species(eligible, owned_counts)

    order = {animal: i for i, animal in enumerate(base.ACTIVE_ANIMALS)}
    opponent_counts = (_last_opponent_state or {}).get("animal_tile_count") or {}
    candidate_pick = min(
        eligible,
        key=lambda a: (owned_counts.get(a, 0), opponent_counts.get(a, 0), order[a]),
    )

    if candidate_pick != baseline_pick:
        ANIMAL_DECISION_LOG.append({
            "eligible": list(eligible),
            "owned_counts": dict(owned_counts),
            "opponent_animal_counts": dict(opponent_counts),
            "baseline_pick": baseline_pick,
            "candidate_pick": candidate_pick,
        })

    return candidate_pick


base.pick_next_animal_species = _pick_next_animal_species_opponent_state_v0


# ---------------------------------------------------------------------
# 6. Agent entrypoint
# ---------------------------------------------------------------------

def opponent_state_v0(obs):
    return base.nikaangukia_meroni(obs)


def _self_test(seeds=(0, 1, 2)):
    from kaggle_environments import make

    for seed in seeds:
        env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})
        env.run([opponent_state_v0, opponent_state_v0])
        a, b = env.steps[-1]
        print(f"seed {seed}: seat0 {a.reward:>8.0f} [{a.status}]   seat1 {b.reward:>8.0f} [{b.status}]")
    print(f"crop decision changes logged: {len(CROP_DECISION_LOG)}")
    print(f"animal decision changes logged: {len(ANIMAL_DECISION_LOG)}")


agent = opponent_state_v0

if __name__ == "__main__":
    _self_test()
