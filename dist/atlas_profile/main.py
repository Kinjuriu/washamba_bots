#!/usr/bin/env python3
"""
atlas_profile - a state-aware Kaggriculture agent whose macro strategy is
reconstructed from the current top-five ladder leaders' own replays, not
hand-tuned or copied from any prior agent in this repo.

WHERE THE STRATEGY COMES FROM
------------------------------
experiments/build_atlas_profile.py pulled the manifest + replay corpus at
~/KagricultureLocalData/episodes, extracted state-derived macro features
(bank, usable land, hand count, planted/harvest-ready crop counts, animal
structures, living animals by species, shed inventory, carried inventory)
at turns 0/72/144/216/288/360/432/504/576/648/696 for every target-player
trajectory, clustered trajectories on THOSE macro features alone (never
exact coordinates, team name, submission ID, episode ID, terminal bank, or
future information), and picked ONE cluster by: (1) dominated by a single
real top-five submission (purity >= 0.7, so this is not a blend of
different agents' policies), (2) >=10 winning trajectories, (3) tightest
internal cohesion among qualifying clusters, (4) highest win rate with a
preference for a larger sample. Win/loss came from each replay's real
terminal bank, never from requested market orders (a requested SELL/
BUY_PRODUCT can be silently rejected by the engine - see CLAUDE.md).

Selected: cluster 4, n=54 (41 wins / 13 losses, 76% observed win rate),
85% of its members from submission 56401905 ("Unknown Mother-Goose").
PROFILE_SCHEDULE below is the per-checkpoint MEDIAN of that cluster's 41
winning trajectories (a robust central value within one already-coherent
family, not an average across incompatible policies). Medoid episode:
111457276, seat 1.

WORKFORCE CORRECTION (2026-09-21, post-review): the first version of this
profile reported the selected family's hand count as 0 throughout - wrong,
and the error was in the sampling, not the data. Every one of the 11
checkpoints (0/72/144/216/.../696) is an exact multiple of 24, i.e. every
single one lands on hour 0 - the one moment per day hands are GUARANTEED
to read 0, because the engine clears the crew at midnight and hands are
rehired each morning (CLAUDE.md). Checking hour 0 exclusively measured the
reset, not the strategy. Verified directly against raw replay state
(medoid 111457276 seat 1, plus two more cluster members, at hours
0/1/2/4/6/12/23): this family hires HEAVILY - 4 hands by day 0, ramping to
11 by day 9 and holding there. HIRE orders land the same turn they're
submitted (a replay row's observation already reflects that row's own
action - obs(t) is post-action(t), confirmed by money/hands continuity
across turns, not assumed from array position), the morning hiring burst
is consistently settled within a few hours, and the crew then holds flat
for the rest of the day. DAILY_CREW_TARGET below is the REAL, corrected
signal: state-based (len(farm["hands"]) at hour 12, a safe post-burst
sample), median across the same 41 winning trajectories, per day - not
interpolated through the midnight zero, and not a fixed constant (a
different selected family would produce a different ramp through the same
code). decide_hire_orders_atlas rehires toward that day's integer target
every morning, gated by the engine's real fib hire-cost progression,
available cash, and the market-order-per-turn budget - exactly as
instructed, not by copying the replay's own occasionally-overshooting
request pattern (the real family sometimes requests more hires than it
can afford in one turn and lets the engine silently drop the excess;
computing affordability up front, as this file does, never wastes an
order slot on a doomed request).

WHAT IS AND ISN'T "the strategy" HERE
--------------------------------------
Reused from main.py, unmodified: pure legality/execution machinery (tile
lookup, movement, the per-unit action-priority ladder, market-order
sanitizing) and mechanical engine-mirrors (hire cost is Fibonacci, land
quadrant order/price, shed cap, price-crash math) - none of that is a
"strategy claim" copied from any agent, it is how the game itself works
and would be identical for any policy. New in this file: every place a
NUMBER decides what to do (how much land/hands/animals/crop/shed
inventory to aim for, and when) is driven by PROFILE_SCHEDULE, interpolated
to the current turn, compared against the ACTUAL live farm state - never a
fixed constant asserting "buy land on day X" or "hire N hands" or "plant
crop Y". This file does not hard-code, and does not need, any claim about
wheat frequency, a land-purchase day window, or an optimal hand count -
those would-be priors are exactly what got replaced by reading the
schedule below.

Standard library only - zero imports at all. No filesystem, network,
pandas, NumPy, sklearn, kaggle_environments, or any import of this
repository's own code at inference time: CROPS/ANIMALS/MARKET_PARAMS/
PRICE_FLOOR below are inlined directly from the engine's own tables
rather than imported, so this file has no runtime dependency on the
environment package being present, on any path, under any version.
"""

# Inlined directly from the engine's own tables (kaggle_environments'
# kaggriculture.CROPS / ANIMALS / MARKET_PARAMS / PRICE_FLOOR), not
# imported: this file has zero runtime dependency on the environment
# package being importable at all, in any path, under any version.
# Reproduced, not guessed - cross-checked field-for-field against the
# installed engine (2026-09-21).
PRICE_FLOOR = 1
CROPS = {
    "WHEAT":      {"seed": 10,  "first_yield_day": 2,  "max_yield_day": 4,  "interval": 0, "max_yield": 6, "ongoing": False},
    "CARROT":     {"seed": 20,  "first_yield_day": 2,  "max_yield_day": 3,  "interval": 0, "max_yield": 4, "ongoing": False},
    "TOMATO":     {"seed": 50,  "first_yield_day": 8,  "max_yield_day": 8,  "interval": 1, "max_yield": 4, "ongoing": True},
    "STRAWBERRY": {"seed": 100, "first_yield_day": 10, "max_yield_day": 10, "interval": 2, "max_yield": 4, "ongoing": True},
    "MELON":      {"seed": 80,  "first_yield_day": 10, "max_yield_day": 12, "interval": 0, "max_yield": 6, "ongoing": False},
}
ANIMALS = {
    "GOOSE": {"cost": 300, "structure": "COOP",    "first_yield_day": 4, "interval": 1, "max_held": 4, "product": "EGG"},
    "COW":   {"cost": 400, "structure": "PASTURE", "first_yield_day": 8, "interval": 2, "max_held": 6, "product": "MILK"},
    "SHEEP": {"cost": 500, "structure": "PASTURE", "first_yield_day": 6, "interval": 3, "max_held": 6, "product": "WOOL"},
}
MARKET_PARAMS = {
    "WHEAT": {"base": 25}, "CARROT": {"base": 35}, "TOMATO": {"base": 60},
    "STRAWBERRY": {"base": 120}, "MELON": {"base": 250}, "EGG": {"base": 50},
    "MILK": {"base": 160}, "WOOL": {"base": 200}, "FERTILIZER": {"base": 100},
}

# ---------------------------------------------------------------------
# Season / board mechanics (engine facts, not strategy)
# ---------------------------------------------------------------------
SEASON_DAYS = 30
TURNS_PER_DAY = 24
PLANTABLE_CROPS = ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON"]
FERTILIZABLE_CROPS = ("TOMATO", "STRAWBERRY")  # the only "ongoing" crops - engine fact
LAND_ORDER = ["NE", "SW", "SE"]
LAND_PRICES = [1000, 2000, 4000]
MAX_MARKET_ORDERS_PER_TURN = 10
FARM_HAND_COST_MULT = 1
ANIMAL_STRUCTURE_KINDS = {info["structure"] for info in ANIMALS.values() if info.get("structure")}

# ---------------------------------------------------------------------
# Generic execution-safety constants. These are prudence/mechanics, not
# behavioral claims reconstructed from any specific agent: a cash floor so
# an order is never attempted against a negative balance, a per-turn sell
# cap so a big harvest can't crash its own price in one order (the price-
# crash math itself is engine mechanics, not a per-product opinion), and a
# liquidation window near the literal end of the season, because unsold
# shed inventory scores exactly zero - true for any agent, not a
# reconstructed preference.
# ---------------------------------------------------------------------
CASH_RESERVE_FLOOR = 15
MAX_SELL_PER_TURN_GENERIC = 15
HIRE_BEFORE_HOUR = 6
MAX_HIRES_PER_TURN_GENERIC = 12  # >= the largest observed DAILY_CREW_TARGET (11);
# the real constraints are affordability (checked below via the real fib
# cost progression) and the shared 10-market-order-per-turn cap applied at
# the end of atlas() - not an arbitrary per-turn throttle.
LIQUIDATION_START_DAY = 27
SEED_BATCH_CAP = 5

# A dedicated, higher reserve for animal purchases specifically (not the
# feed safety net below, which deliberately has none - a starved animal is
# a bigger loss than its wheat). Mechanical fix, not a strategy choice:
# without this, an uncoordinated BUY_ANIMAL order ($300-500) and the seed
# purchase decided in the very same turn both read the same pre-turn cash
# snapshot, and animal spending can strand seed-buying below its own
# reserve floor for the rest of the game once cash never recovers. Same
# failure class CLAUDE.md documents for MIN_CASH_RESERVE_FOR_ANIMAL_BUYING
# in main.py - the fix here is the same shape, sized generically rather
# than copied from that file's swept value.
ANIMAL_CASH_RESERVE_FLOOR = 60


def _hire_cost(n_already_today):
    """Mirrors the engine's own fib-indexed hire cost exactly (mechanics,
    not strategy) - the n-th hire of a day costs mult * fib(n), fib(0)=1."""
    a, b = 1, 1
    for _ in range(n_already_today):
        a, b = b, a + b
    return FARM_HAND_COST_MULT * a


# =======================================================================
# PROFILE - the reconstructed macro schedule. Generated by
# experiments/build_atlas_profile.py from ~/KagricultureLocalData/episodes
# on 2026-09-21; see that script and its JSON output
# (~/KagricultureLocalData/episodes/atlas_profile/atlas_profile_source.json)
# for full provenance. Median, per checkpoint, over the 41 winning
# trajectories of the selected cluster (see module docstring).
# =======================================================================
PROFILE_META = {
    "selected_cluster_label": 4,
    "cluster_n": 54,
    "cluster_wins": 41,
    "cluster_losses": 13,
    "cluster_win_rate": 0.76,
    "top_submission": "56401905",
    "purity": 0.85,
    "medoid_trajectory_id": "111457276:1",
    "medoid_episode_id": 111457276,
    "schedule_source": "median of 41 winning trajectories in the selected cluster",
}

DAILY_CREW_TARGET = [
    4, 4, 6, 5, 5, 5, 8, 8, 8, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11,
    11, 11, 11, 11, 11, 11, 11, 11, 11, 11,
]  # index = day 0-29. State-based median crew size at hour 12 across the
   # 41 winning trajectories - see WORKFORCE CORRECTION note above.

PROFILE_SCHEDULE = [
    {"turn": 0,   "bank": 3000.0, "usable_land": 25, "n_hands": 4,
     "planted_by_crop": {"WHEAT": 0, "CARROT": 0, "TOMATO": 0, "STRAWBERRY": 0, "MELON": 0},
     "animals_by_species": {"COW": 0, "GOOSE": 0, "SHEEP": 0},
     "shed_by_product": {"WHEAT": 0, "CARROT": 0, "TOMATO": 0, "STRAWBERRY": 0, "MELON": 0,
                          "EGG": 0, "MILK": 0, "WOOL": 0, "FERTILIZER": 0}},
    {"turn": 72,  "bank": 63.0, "usable_land": 25, "n_hands": 5,
     "planted_by_crop": {"WHEAT": 7, "CARROT": 0, "TOMATO": 0, "STRAWBERRY": 3, "MELON": 10},
     "animals_by_species": {"COW": 2, "GOOSE": 0, "SHEEP": 3},
     "shed_by_product": {"WHEAT": 6, "CARROT": 0, "TOMATO": 0, "STRAWBERRY": 0, "MELON": 0,
                          "EGG": 0, "MILK": 0, "WOOL": 0, "FERTILIZER": 0}},
    {"turn": 144, "bank": 732.0, "usable_land": 25, "n_hands": 8,
     "planted_by_crop": {"WHEAT": 0, "CARROT": 0, "TOMATO": 0, "STRAWBERRY": 10, "MELON": 10},
     "animals_by_species": {"COW": 2, "GOOSE": 0, "SHEEP": 3},
     "shed_by_product": {"WHEAT": 8, "CARROT": 0, "TOMATO": 0, "STRAWBERRY": 0, "MELON": 0,
                          "EGG": 0, "MILK": 0, "WOOL": 0, "FERTILIZER": 1}},
    {"turn": 216, "bank": 365.0, "usable_land": 75, "n_hands": 11,
     "planted_by_crop": {"WHEAT": 10, "CARROT": 0, "TOMATO": 0, "STRAWBERRY": 16, "MELON": 12},
     "animals_by_species": {"COW": 7, "GOOSE": 1, "SHEEP": 3},
     "shed_by_product": {"WHEAT": 18, "CARROT": 0, "TOMATO": 0, "STRAWBERRY": 0, "MELON": 0,
                          "EGG": 0, "MILK": 0, "WOOL": 0, "FERTILIZER": 7}},
    {"turn": 288, "bank": 12820.0, "usable_land": 75, "n_hands": 11,
     "planted_by_crop": {"WHEAT": 29, "CARROT": 0, "TOMATO": 1, "STRAWBERRY": 18, "MELON": 2},
     "animals_by_species": {"COW": 8, "GOOSE": 3, "SHEEP": 3},
     "shed_by_product": {"WHEAT": 51, "CARROT": 0, "TOMATO": 0, "STRAWBERRY": 0, "MELON": 6,
                          "EGG": 0, "MILK": 0, "WOOL": 0, "FERTILIZER": 10}},
    {"turn": 360, "bank": 29187.0, "usable_land": 75, "n_hands": 11,
     "planted_by_crop": {"WHEAT": 21, "CARROT": 0, "TOMATO": 2, "STRAWBERRY": 26, "MELON": 2},
     "animals_by_species": {"COW": 8, "GOOSE": 3, "SHEEP": 3},
     "shed_by_product": {"WHEAT": 47, "CARROT": 0, "TOMATO": 0, "STRAWBERRY": 9, "MELON": 0,
                          "EGG": 4, "MILK": 1, "WOOL": 4, "FERTILIZER": 12}},
    {"turn": 432, "bank": 45828.0, "usable_land": 75, "n_hands": 11,
     "planted_by_crop": {"WHEAT": 19, "CARROT": 0, "TOMATO": 4, "STRAWBERRY": 26, "MELON": 0},
     "animals_by_species": {"COW": 8, "GOOSE": 3, "SHEEP": 5},
     "shed_by_product": {"WHEAT": 41, "CARROT": 0, "TOMATO": 0, "STRAWBERRY": 14, "MELON": 0,
                          "EGG": 4, "MILK": 0, "WOOL": 7, "FERTILIZER": 10}},
    {"turn": 504, "bank": 60756.0, "usable_land": 75, "n_hands": 11,
     "planted_by_crop": {"WHEAT": 25, "CARROT": 1, "TOMATO": 6, "STRAWBERRY": 18, "MELON": 0},
     "animals_by_species": {"COW": 8, "GOOSE": 3, "SHEEP": 5},
     "shed_by_product": {"WHEAT": 42, "CARROT": 0, "TOMATO": 4, "STRAWBERRY": 8, "MELON": 0,
                          "EGG": 4, "MILK": 7, "WOOL": 5, "FERTILIZER": 9}},
    {"turn": 576, "bank": 72159.0, "usable_land": 75, "n_hands": 11,
     "planted_by_crop": {"WHEAT": 28, "CARROT": 12, "TOMATO": 4, "STRAWBERRY": 14, "MELON": 0},
     "animals_by_species": {"COW": 8, "GOOSE": 3, "SHEEP": 6},
     "shed_by_product": {"WHEAT": 43, "CARROT": 0, "TOMATO": 4, "STRAWBERRY": 12, "MELON": 0,
                          "EGG": 4, "MILK": 2, "WOOL": 6, "FERTILIZER": 8}},
    {"turn": 648, "bank": 83977.0, "usable_land": 75, "n_hands": 11,
     "planted_by_crop": {"WHEAT": 29, "CARROT": 16, "TOMATO": 3, "STRAWBERRY": 8, "MELON": 0},
     "animals_by_species": {"COW": 8, "GOOSE": 3, "SHEEP": 6},
     "shed_by_product": {"WHEAT": 39, "CARROT": 17, "TOMATO": 6, "STRAWBERRY": 10, "MELON": 0,
                          "EGG": 0, "MILK": 5, "WOOL": 5, "FERTILIZER": 5}},
    {"turn": 696, "bank": 93875.0, "usable_land": 75, "n_hands": 11,
     "planted_by_crop": {"WHEAT": 17, "CARROT": 6, "TOMATO": 1, "STRAWBERRY": 8, "MELON": 0},
     "animals_by_species": {"COW": 7, "GOOSE": 3, "SHEEP": 1},
     "shed_by_product": {"WHEAT": 33, "CARROT": 11, "TOMATO": 4, "STRAWBERRY": 4, "MELON": 0,
                          "EGG": 2, "MILK": 5, "WOOL": 5, "FERTILIZER": 2}},
]


def _lerp(a, b, frac):
    return a + (b - a) * frac


def _lerp_dict(a, b, frac, keys):
    return {k: _lerp(a.get(k, 0), b.get(k, 0), frac) for k in keys}


def profile_target_at(turn):
    """Linearly interpolate PROFILE_SCHEDULE to any turn 0-719. Turns past
    the last checkpoint (696) hold that checkpoint's values - the schedule
    doesn't extrapolate past what was actually observed."""
    sched = PROFILE_SCHEDULE
    if turn <= sched[0]["turn"]:
        return sched[0]
    if turn >= sched[-1]["turn"]:
        return sched[-1]
    for i in range(len(sched) - 1):
        lo, hi = sched[i], sched[i + 1]
        if lo["turn"] <= turn <= hi["turn"]:
            span = hi["turn"] - lo["turn"]
            frac = (turn - lo["turn"]) / span if span else 0.0
            return {
                "turn": turn,
                "bank": _lerp(lo["bank"], hi["bank"], frac),
                "usable_land": _lerp(lo["usable_land"], hi["usable_land"], frac),
                "n_hands": _lerp(lo["n_hands"], hi["n_hands"], frac),
                "planted_by_crop": _lerp_dict(lo["planted_by_crop"], hi["planted_by_crop"], frac, PLANTABLE_CROPS),
                "animals_by_species": _lerp_dict(lo["animals_by_species"], hi["animals_by_species"], frac, ANIMALS.keys()),
                "shed_by_product": _lerp_dict(lo["shed_by_product"], hi["shed_by_product"], frac, MARKET_PARAMS.keys()),
            }
    return sched[-1]


# ---------------------------------------------------------------------
# Observation readers, movement, tile targeting - legality/execution
# machinery, reused from main.py (this repo's proven executor). None of
# this decides WHAT to build/plant/sell, only HOW to legally do it once a
# profile-driven decision names a target.
# ---------------------------------------------------------------------
def get_player_farm(obs):
    farms = obs.get("farms")
    player = obs.get("player")
    if not isinstance(farms, list) or not isinstance(player, int):
        return None
    if player < 0 or player >= len(farms):
        return None
    return farms[player]


def get_tile_at(farm, x, y):
    tiles = farm.get("tiles") if farm else None
    if not tiles or y < 0 or y >= len(tiles):
        return None
    row = tiles[y]
    if x < 0 or x >= len(row):
        return None
    return row[x]


def get_current_tile(farm):
    farmer_pos = farm.get("farmer") if farm else None
    if not farmer_pos or len(farmer_pos) != 2:
        return None
    return get_tile_at(farm, farmer_pos[0], farmer_pos[1])


def shed_access_tiles(board_size):
    half = board_size // 2
    return [(half - 1, half - 1), (half, half - 1), (half - 1, half), (half, half)]


def is_shed_adjacent(x, y, board_size):
    return (x, y) in shed_access_tiles(board_size)


def step_toward(fx, fy, tx, ty):
    if fx > tx:
        return "WEST"
    if fx < tx:
        return "EAST"
    if fy > ty:
        return "NORTH"
    if fy < ty:
        return "SOUTH"
    return None


def is_harvestable(tile, day):
    if tile.get("yield_units", 0) <= 0:
        return False
    crop_info = CROPS.get(tile.get("crop"))
    if not crop_info:
        return False
    first_yield_day = crop_info.get("first_yield_day", 0)
    return day - tile.get("planted_day", day) >= first_yield_day


def remaining_season_days(day):
    return (SEASON_DAYS - 1) - day


def has_plantable_seed(seeds, day):
    remaining_days = remaining_season_days(day)
    for crop, count in seeds.items():
        if count <= 0:
            continue
        crop_info = CROPS.get(crop)
        if not crop_info:
            continue
        first_yield_day = crop_info.get("first_yield_day")
        if first_yield_day is None or first_yield_day <= remaining_days:
            return True
    return False


def find_nearest_target(farm, board_size, fx, fy, task, day, seeds=None, exclude=None):
    seeds = seeds or {}
    exclude = exclude or set()
    tiles = farm.get("tiles") or []
    have_any_seed = has_plantable_seed(seeds, day)

    best_target = None
    best_distance = None

    for y in range(board_size):
        row = tiles[y] if y < len(tiles) else []
        for x in range(len(row)):
            if (x, y) in exclude:
                continue
            tile = row[x]
            is_match = False

            if isinstance(tile, dict) and tile.get("kind") == "PLANT":
                is_ripe = is_harvestable(tile, day)
                needs_water = not tile.get("watered_today", True)
                missed_before = tile.get("consecutive_unwatered", 0) >= 1
                if task == "harvest" and is_ripe:
                    is_match = True
                elif task == "water_urgent" and needs_water and missed_before:
                    is_match = True
                elif task == "any" and (is_ripe or needs_water):
                    is_match = True
            elif isinstance(tile, dict) and "animal" in tile:
                is_ripe = tile.get("yield_units", 0) > 0
                needs_feed = not tile.get("fed_today", True)
                if task == "harvest" and is_ripe:
                    is_match = True
                elif task == "feed" and needs_feed:
                    is_match = True
            elif isinstance(tile, dict) and tile.get("kind") == "WEED" and task == "weed":
                is_match = True
            elif (isinstance(tile, dict) and tile.get("kind") in ANIMAL_STRUCTURE_KINDS
                  and "animal" not in tile and task == "empty_structure"):
                is_match = True
            elif tile is None and task == "any" and have_any_seed:
                is_match = True

            if is_match:
                distance = abs(x - fx) + abs(y - fy)
                if best_distance is None or distance < best_distance:
                    best_distance = distance
                    best_target = (x, y)

    return best_target


def _closer_target(fx, fy, target_a, target_b):
    if target_a is None:
        return target_b
    if target_b is None:
        return target_a
    dist_a = abs(target_a[0] - fx) + abs(target_a[1] - fy)
    dist_b = abs(target_b[0] - fx) + abs(target_b[1] - fy)
    return target_a if dist_a <= dist_b else target_b


def wants_fertilizer(tile, day):
    """Only ongoing crops (TOMATO/STRAWBERRY) ever benefit - engine fact,
    not a preference - and only inside the window where the 3-day cover
    still catches a production tick."""
    if not (isinstance(tile, dict) and tile.get("kind") == "PLANT"):
        return False
    crop = tile.get("crop")
    if crop not in FERTILIZABLE_CROPS:
        return False
    if tile.get("fertilized_until_day", -1) >= day:
        return False
    crop_info = CROPS.get(crop) or {}
    first_yield_day = crop_info.get("first_yield_day")
    if first_yield_day is None:
        return False
    interval = crop_info.get("interval") or 1
    max_yield = crop_info.get("max_yield") or 1
    last_tick_age = first_yield_day - 1 + interval * (max_yield - 1)
    age = day - tile.get("planted_day", day)
    return (first_yield_day - 3) <= age <= last_tick_age


def find_fertilizer_target(farm, board_size, ux, uy, day, exclude=None):
    exclude = exclude or set()
    tiles = farm.get("tiles") or []
    best_target, best_distance = None, None
    for y in range(board_size):
        row = tiles[y] if y < len(tiles) else []
        for x in range(len(row)):
            if (x, y) in exclude or not wants_fertilizer(row[x], day):
                continue
            distance = abs(x - ux) + abs(y - uy)
            if best_distance is None or distance < best_distance:
                best_distance = distance
                best_target = (x, y)
    return best_target


def nearest_shed_tile(fx, fy, board_size):
    tiles = shed_access_tiles(board_size)
    return min(tiles, key=lambda t: abs(t[0] - fx) + abs(t[1] - fy))


def get_market_state(obs):
    market = obs.get("market") or {}
    return {"prices": market.get("prices") or {}, "inventory": market.get("inventory") or {}}


def extract_state(obs):
    obs = obs or {}
    farm = get_player_farm(obs)
    private = obs.get("private") or {}
    tiles = farm.get("tiles") if farm else None
    day = obs.get("day", 0)
    hour = obs.get("hour", 0)
    return {
        "farm": farm,
        "private": private,
        "market_state": get_market_state(obs),
        "board_size": len(tiles) if tiles else 0,
        "day": day,
        "hour": hour,
        "turn": obs.get("step", day * TURNS_PER_DAY + hour),
    }


def unit_inventory(private, unit_idx):
    inventories = private.get("inventories") or []
    if 0 <= unit_idx < len(inventories) and isinstance(inventories[unit_idx], dict):
        return inventories[unit_idx]
    return {}


def carried_animal(inv):
    for animal in ANIMALS:
        if inv.get(animal, 0) > 0:
            return animal
    return None


def scan_animal_structures(farm, board_size):
    tiles = farm.get("tiles") or []
    filled = unfilled = 0
    for y in range(board_size):
        row = tiles[y] if y < len(tiles) else []
        for tile in row:
            if isinstance(tile, dict) and tile.get("kind") in ANIMAL_STRUCTURE_KINDS:
                if "animal" in tile:
                    filled += 1
                else:
                    unfilled += 1
    return filled, unfilled


_animal_pace_tracker = {"day": None, "count": 0}


def _animal_commitments_today(day):
    """How many new animal commitments (BUILD or BUY) we've already started
    today, in this process. A real capacity signal: with hands paced by
    the profile (0 for the selected family), one farmer physically cannot
    onboard several animals - each a standing daily FEED/CARE obligation -
    in the same day without crop upkeep collapsing, since the tile schema
    doesn't record a build day for an empty structure we could otherwise
    read this straight from state. Resets on a new day; safe if the
    process restarts (worst case, undercounts and repaces from 0)."""
    if _animal_pace_tracker["day"] != day:
        _animal_pace_tracker["day"] = day
        _animal_pace_tracker["count"] = 0
    return _animal_pace_tracker["count"]


def _record_animal_commitment(day):
    _animal_commitments_today(day)
    _animal_pace_tracker["count"] += 1


def farm_has_unaddressed_neglect(farm, board_size):
    """True if there's already a WEED tile or an unfed placed animal on the
    farm right now. A real capacity signal, not a strategy preference: with
    the profile's own hands target driving crew size (0 for the selected
    family - see module docstring), a single farmer has finite daily
    capacity, and every additional animal structure adds a standing daily
    FEED/CARE obligation that competes with watering. Taking on a new
    animal while existing obligations are already being missed just moves
    the neglect somewhere else rather than fixing it."""
    tiles = farm.get("tiles") or []
    for y in range(board_size):
        row = tiles[y] if y < len(tiles) else []
        for tile in row:
            if not isinstance(tile, dict):
                continue
            if tile.get("kind") == "WEED":
                return True
            if tile.get("kind") in ANIMAL_STRUCTURE_KINDS and "animal" in tile:
                if not tile.get("fed_today") or not tile.get("cared_today"):
                    return True
    return False


def species_owned_counts(farm, private, board_size):
    counts = {a: 0 for a in ANIMALS}
    shed = private.get("shed", {})
    for a in ANIMALS:
        counts[a] += shed.get(a, 0)
    for inv in private.get("inventories") or []:
        if isinstance(inv, dict):
            for a in ANIMALS:
                counts[a] += inv.get(a, 0)
    tiles = farm.get("tiles") or []
    for y in range(board_size):
        row = tiles[y] if y < len(tiles) else []
        for tile in row:
            if isinstance(tile, dict) and tile.get("kind") in ANIMAL_STRUCTURE_KINDS:
                species = tile.get("animal")
                if species in counts:
                    counts[species] += 1
    return counts


def tile_quadrant(x, y, board_size):
    half = board_size // 2
    return ("N" if y < half else "S") + ("W" if x < half else "E")


def current_planted_by_crop(farm):
    counts = {c: 0 for c in PLANTABLE_CROPS}
    for row in farm.get("tiles") or []:
        for t in row:
            if isinstance(t, dict) and t.get("kind") == "PLANT":
                crop = t.get("crop")
                if crop in counts:
                    counts[crop] += 1
    return counts


# ---------------------------------------------------------------------
# Market mechanics mirror (price formula + price-path-aware sell pacing).
# Needed so selling toward a profile target doesn't crash a premium
# product's own price in one order - mechanics, not a per-product opinion.
# ---------------------------------------------------------------------
def market_price(item, inventory):
    params = MARKET_PARAMS.get(item) or {}
    base = params.get("base", 50)
    # Without the full shape table (fallback path only) fall back to a
    # flat base price - still legal, just not price-impact-aware.
    return max(PRICE_FLOOR, int(round(base)))


def recommend_sell_quantity(item, current_inventory, available_quantity, min_acceptable_price, max_per_turn=None):
    available_quantity = int(round(available_quantity))
    if max_per_turn is not None:
        max_per_turn = int(round(max_per_turn))
    """How many units of `item` to sell this turn before the price would
    drop under `min_acceptable_price`, capped by what we hold and an
    optional per-turn pacing cap. A simplified, monotone-decreasing model
    of the engine's real per-unit price walk (exact formula/state is not
    exposed on `obs`): each unit sold nudges price down a fixed fraction,
    which is enough to decide *how many* units to include in one order
    without ever dumping an unbounded quantity into a thin market."""
    if available_quantity <= 0 or min_acceptable_price <= 0:
        return 0
    cap = available_quantity
    if max_per_turn is not None:
        cap = min(cap, max_per_turn)
    price = market_price(item, current_inventory)
    count = 0
    for _ in range(cap):
        if price < min_acceptable_price:
            break
        count += 1
        price = max(PRICE_FLOOR, int(price * 0.985))
    return count


# ---------------------------------------------------------------------
# PROFILE-DRIVEN POLICY - the new part. Every decision below compares the
# ACTUAL live state to profile_target_at(turn), and acts on the deficit -
# no fixed day windows, no fixed hand-count constant, no fixed crop
# priority order.
# ---------------------------------------------------------------------
def decide_land_orders_atlas(farm, board_size, turn):
    target = profile_target_at(turn)
    target_tiles = target["usable_land"]
    tiles_per_quadrant = (board_size * board_size) // 4 if board_size else 25
    unlocked = farm.get("unlocked_quadrants") or ["NW"]
    current_tiles = len(unlocked) * tiles_per_quadrant
    if current_tiles >= target_tiles:
        return []
    n_extra = len(unlocked) - 1
    if n_extra < 0 or n_extra >= len(LAND_ORDER):
        return []
    cost = LAND_PRICES[n_extra]
    money = farm.get("money", 0)
    if money - cost < CASH_RESERVE_FLOOR:
        return []
    return [["BUY_LAND"]]


def decide_hire_orders_atlas(farm, day, hour, turn):
    if hour >= HIRE_BEFORE_HOUR:
        return []  # hands vanish at day end - hire early or waste the purchase (mechanic)
    # DAILY_CREW_TARGET is a real, integer, day-indexed target (see the
    # WORKFORCE CORRECTION note at the top of this file) - deliberately NOT
    # interpolated turn-by-turn like the other profile fields, because
    # hands are wiped to 0 every midnight and rebuilt fresh each morning;
    # interpolating through that zero would misread a nightly reset as a
    # strategy of not hiring.
    target = DAILY_CREW_TARGET[min(day, len(DAILY_CREW_TARGET) - 1)] if day >= 0 else 0
    hands_field = farm.get("hands")
    if hands_field is None:
        return []  # "hands" key missing entirely (malformed obs) - unknown
        # crew size, not zero; don't hire against an assumed headcount.
    current = len(hands_field)
    if current >= target:
        return []
    money = farm.get("money", 0)
    hires_today = farm.get("hires_today", 0)
    shortfall = min(target - current, MAX_HIRES_PER_TURN_GENERIC)
    orders = []
    remaining_money = money
    for i in range(shortfall):
        cost = _hire_cost(hires_today + i)
        if remaining_money - cost < CASH_RESERVE_FLOOR:
            break
        remaining_money -= cost
        orders.append(["HIRE"])
    return orders


def choose_animal_to_build_atlas(farm, private, board_size, day, turn, pending_builds=0, ux=None, uy=None):
    filled, unfilled = scan_animal_structures(farm, board_size)
    if unfilled > 0 or pending_builds > 0:
        return None
    targets = profile_target_at(turn)["animals_by_species"]
    total_target = sum(targets.values())
    if total_target <= 0 or filled >= total_target:
        return None
    if filled > 0 and farm_has_unaddressed_neglect(farm, board_size):
        return None  # catch up on existing obligations before adding another
    if _animal_commitments_today(day) >= 1:
        return None  # one new animal commitment (build or buy) per day
    owned = species_owned_counts(farm, private, board_size)
    money = farm.get("money", 0)
    remaining_days = remaining_season_days(day)
    best_species, best_deficit = None, 0
    for species, info in ANIMALS.items():
        cost = info.get("cost")
        first_yield_day = info.get("first_yield_day")
        if cost is None or first_yield_day is None or first_yield_day > remaining_days:
            continue
        if money < cost or money - cost < ANIMAL_CASH_RESERVE_FLOOR:
            continue
        deficit = targets.get(species, 0) - owned.get(species, 0)
        if deficit > best_deficit:
            best_deficit = deficit
            best_species = species
    return best_species


def decide_animal_market_actions_atlas(farm, private, board_size, day, turn):
    actions = []
    targets = profile_target_at(turn)["animals_by_species"]
    total_target = sum(targets.values())
    filled_now, _ = scan_animal_structures(farm, board_size)
    blocked = (
        (filled_now > 0 and farm_has_unaddressed_neglect(farm, board_size))
        or _animal_commitments_today(day) >= 1
    )
    if total_target > 0 and not blocked:
        owned = species_owned_counts(farm, private, board_size)
        if sum(owned.values()) < total_target:
            money = farm.get("money", 0)
            remaining_days = remaining_season_days(day)
            best_species, best_deficit = None, 0
            for species, info in ANIMALS.items():
                cost = info.get("cost")
                first_yield_day = info.get("first_yield_day")
                if cost is None or first_yield_day is None or first_yield_day > remaining_days:
                    continue
                if cost > money or money - cost < ANIMAL_CASH_RESERVE_FLOOR:
                    continue
                deficit = targets.get(species, 0) - owned.get(species, 0)
                if deficit > best_deficit:
                    best_deficit = deficit
                    best_species = species
            if best_species:
                actions.append(["BUY_ANIMAL", best_species, 1])
                _record_animal_commitment(day)

    # Feed safety net: a placed animal that misses two consecutive feeds
    # escapes for good - keep at least a little wheat on hand whenever we
    # own a placed animal, regardless of what the profile's shed target
    # says (losing the animal is strictly worse than a small wheat surplus).
    filled, _ = scan_animal_structures(farm, board_size)
    if filled > 0 and farm.get("money", 0) > 0:
        shed_wheat = private.get("shed", {}).get("WHEAT", 0)
        carried_wheat = sum(
            inv.get("WHEAT", 0) for inv in (private.get("inventories") or []) if isinstance(inv, dict)
        )
        if shed_wheat + carried_wheat < 2:
            actions.append(["BUY_PRODUCT", "WHEAT", 1])
    return actions


def choose_crop_atlas(farm, private, day, turn, require_held_seed=False):
    """Prioritize whichever crop is furthest below the profile's current
    target, subject to being able to mature before the season ends.
    `require_held_seed` mirrors main.py's own fix for the same real bug:
    a crop named via can_afford with zero held seed can silently fail to
    plant if several units target it in one turn - this restricts
    eligibility to what we can actually plant right now (an execution-
    correctness fix, not a strategy choice)."""
    money = farm.get("money", 0)
    seeds = private.get("seeds", {})
    remaining_days = remaining_season_days(day)
    targets = profile_target_at(turn)["planted_by_crop"]
    current = current_planted_by_crop(farm)

    best_crop, best_deficit = None, 0
    for crop in PLANTABLE_CROPS:
        info = CROPS.get(crop)
        if not info:
            continue
        first_yield_day = info.get("first_yield_day")
        if first_yield_day is not None and first_yield_day > remaining_days:
            continue
        have_seed = seeds.get(crop, 0) > 0
        if require_held_seed:
            if not have_seed:
                continue
        else:
            can_afford = money >= (info.get("seed") or 0)
            if not have_seed and not can_afford:
                continue
        deficit = targets.get(crop, 0) - current.get(crop, 0)
        if deficit > best_deficit:
            best_deficit = deficit
            best_crop = crop
    return best_crop


def seed_restock_quantity_atlas(crop, farm, private, deficit):
    """How many units of `crop` seed to buy right now, or 0. Only fires
    once the held stock is FULLY exhausted (not merely low), and buys a
    batch toward the live deficit in one order rather than one unit at a
    time - the same anti-spiral shape main.py's seed_restock_quantity
    uses, for the same reason: repurchasing a single seed every time one
    gets consumed re-pays the purchase overhead on every planting instead
    of once per batch, and was measured elsewhere in this repo to crash a
    bank from ~$2,160 to ~$25 in 3-4 days when left unbatched."""
    seeds = private.get("seeds", {})
    if seeds.get(crop, 0) > 0:
        return 0
    info = CROPS.get(crop)
    if not info:
        return 0
    seed_cost = info.get("seed")
    if not seed_cost:
        return 0
    money = farm.get("money", 0)
    wanted = max(1, min(int(round(deficit)), SEED_BATCH_CAP))
    quantity = 0
    while quantity < wanted:
        if seed_cost > money:
            break
        remaining_after = money - seed_cost
        if remaining_after < CASH_RESERVE_FLOOR:
            break
        money = remaining_after
        quantity += 1
    return quantity


def decide_market_actions_atlas(farm, private, market_state, day, turn, reserved_wheat=0):
    actions = []
    shed = private.get("shed", {})
    inventory = market_state.get("inventory", {})
    liquidating = day >= LIQUIDATION_START_DAY
    full_target = profile_target_at(turn)
    targets = full_target["shed_by_product"]

    for product in MARKET_PARAMS:
        if product == "FERTILIZER" and not liquidating:
            continue  # input, not produce - hold it for crops (mechanic)
        quantity = shed.get(product, 0)
        if quantity <= 0:
            continue
        sell_quantity = quantity
        if product == "WHEAT":
            sell_quantity = max(0, quantity - reserved_wheat)
        if sell_quantity <= 0:
            continue

        target = 0 if liquidating else targets.get(product, 0)
        excess = sell_quantity - target
        if excess <= 0:
            continue

        base_price = (MARKET_PARAMS.get(product) or {}).get("base", 50)
        min_price = PRICE_FLOOR if liquidating else max(PRICE_FLOOR, int(base_price * 0.15))
        amount = recommend_sell_quantity(
            product, inventory.get(product, 10000), excess,
            min_acceptable_price=min_price, max_per_turn=MAX_SELL_PER_TURN_GENERIC,
        )
        if amount > 0:
            actions.append(["SELL", product, amount])

    preferred_crop = choose_crop_atlas(farm, private, day, turn)
    if preferred_crop:
        crop_deficit = (full_target["planted_by_crop"].get(preferred_crop, 0)
                        - current_planted_by_crop(farm).get(preferred_crop, 0))
        qty = seed_restock_quantity_atlas(preferred_crop, farm, private, crop_deficit)
        if qty > 0:
            actions.append(["BUY_SEED", preferred_crop, qty])

    held_fert = shed.get("FERTILIZER", 0) + sum(
        (inv or {}).get("FERTILIZER", 0) for inv in (private.get("inventories") or [])
        if isinstance(inv, dict)
    )
    if day <= SEASON_DAYS - 6 and held_fert < 6:
        wanted = sum(1 for row in (farm.get("tiles") or []) for tile in row if wants_fertilizer(tile, day))
        fert_price = market_state.get("prices", {}).get("FERTILIZER", 0)
        if wanted > held_fert and fert_price and farm.get("money", 0) - fert_price >= CASH_RESERVE_FLOOR:
            actions.append(["BUY_PRODUCT", "FERTILIZER", 1])

    return actions


# ---------------------------------------------------------------------
# Per-unit executor - the same priority ladder as main.py's
# choose_unit_action, reused because it is legality/execution machinery,
# with only the WHAT-to-build/plant calls swapped for the profile-driven
# versions above.
# ---------------------------------------------------------------------
def choose_unit_action(state, ux, uy, unit_idx, claimed=None, pending_builds=None,
                        feed_claimed=None, plant_budget=None, wheat_budget=None):
    claimed = claimed if claimed is not None else set()
    pending_builds = pending_builds if pending_builds is not None else [0]
    feed_claimed = feed_claimed if feed_claimed is not None else set()

    farm = state["farm"]
    if not farm:
        return ["PASS"]

    board_size = state["board_size"]
    day = state["day"]
    turn = state["turn"]
    private = state["private"]
    seeds = private.get("seeds", {})
    plant_budget = plant_budget if plant_budget is not None else dict(seeds)
    wheat_budget = (wheat_budget if wheat_budget is not None
                    else {"WHEAT": private.get("shed", {}).get("WHEAT", 0)})
    inv = unit_inventory(private, unit_idx)
    tile = get_tile_at(farm, ux, uy)

    if (ux, uy) in claimed:
        tile = "TAKEN"

    is_animal_tile = isinstance(tile, dict) and "animal" in tile

    def act_here(action):
        claimed.add((ux, uy))
        return action

    def walk_to(target):
        direction = step_toward(ux, uy, target[0], target[1])
        if not direction:
            return None
        claimed.add((target[0], target[1]))
        return [direction]

    # 1. Feed before anything else - a missed feed is a permanent loss.
    if is_animal_tile and not tile.get("fed_today"):
        if inv.get("WHEAT", 0) > 0:
            feed_claimed.add((ux, uy))
            return act_here(["FEED"])

    # 2. Harvest.
    if isinstance(tile, dict) and tile.get("kind") == "PLANT" and is_harvestable(tile, day):
        return act_here(["HARVEST"])
    if is_animal_tile:
        animal = ANIMALS.get(tile.get("animal"), {})
        max_held = animal.get("max_held", 1)
        held = tile.get("yield_units", 0)
        if held >= max_held:
            return act_here(["HARVEST"])
        if tile.get("fertilizer_available"):
            return act_here(["COLLECT_FERTILIZER"])
        if held > 0 and (held >= max_held - 2 or day >= SEASON_DAYS - 2):
            return act_here(["HARVEST"])

    # 3. Water / care.
    if isinstance(tile, dict) and tile.get("kind") == "PLANT" and not tile.get("watered_today", True):
        return act_here(["WATER"])
    if is_animal_tile and not tile.get("cared_today"):
        return act_here(["CARE"])

    # 3b. Fertilize what we're standing on.
    if inv.get("FERTILIZER", 0) > 0 and wants_fertilizer(tile, day):
        return act_here(["FERTILIZE"])

    # 4. Place a carried animal.
    animal_in_hand = carried_animal(inv)
    if animal_in_hand and isinstance(tile, dict) and "animal" not in tile:
        structure = ANIMALS.get(animal_in_hand, {}).get("structure")
        if structure and tile.get("kind") == structure:
            return act_here(["PLACE", animal_in_hand])

    # 5. Shed errands.
    if is_shed_adjacent(ux, uy, board_size):
        shed = private.get("shed", {})
        if animal_in_hand is None:
            _, unfilled = scan_animal_structures(farm, board_size)
            if unfilled > 0:
                for animal in ANIMALS:
                    if shed.get(animal, 0) > 0:
                        return act_here(["PICKUP", animal, 1])
        available_wheat = wheat_budget.get("WHEAT", 0)
        if inv.get("WHEAT", 0) <= 0 and available_wheat > 0:
            if find_nearest_target(farm, board_size, ux, uy, "feed", day, exclude=claimed):
                batch = min(available_wheat, 3)
                wheat_budget["WHEAT"] = available_wheat - batch
                return act_here(["PICKUP", "WHEAT", batch])

    # 6. Urgent work elsewhere.
    feed_target = find_nearest_target(farm, board_size, ux, uy, "feed", day, exclude=set())
    if feed_target in feed_claimed:
        feed_target = None
    if feed_target:
        if inv.get("WHEAT", 0) <= 0:
            if wheat_budget.get("WHEAT", 0) > 0:
                moved = walk_to(nearest_shed_tile(ux, uy, board_size))
                if moved:
                    return moved
        else:
            feed_claimed.add(feed_target)
            moved = walk_to(feed_target)
            if moved:
                return moved

    non_feed_exclude = set(claimed)
    if feed_target is not None:
        non_feed_exclude.add(feed_target)
    harvest_target = find_nearest_target(farm, board_size, ux, uy, "harvest", day, exclude=non_feed_exclude)
    water_target = find_nearest_target(farm, board_size, ux, uy, "water_urgent", day, exclude=non_feed_exclude)
    urgent_target = _closer_target(ux, uy, harvest_target, water_target)
    if urgent_target:
        moved = walk_to(urgent_target)
        if moved:
            return moved

    # 7. Carrying an animal - find it a home.
    if animal_in_hand:
        structure_target = find_nearest_target(farm, board_size, ux, uy, "empty_structure", day, exclude=claimed)
        if structure_target:
            moved = walk_to(structure_target)
            if moved:
                return moved

    # 8. Dig a weed underfoot.
    if isinstance(tile, dict) and tile.get("kind") == "WEED":
        return act_here(["DIG"])

    # 9. Build or plant on empty ground - profile-driven.
    if tile is None:
        animal_to_build = choose_animal_to_build_atlas(
            farm, private, board_size, day, turn, pending_builds[0], ux, uy
        )
        if animal_to_build:
            pending_builds[0] += 1
            _record_animal_commitment(day)
            structure = ANIMALS[animal_to_build]["structure"]
            return act_here([f"BUILD_{structure}"])
        crop = choose_crop_atlas(farm, private, day, turn)
        if crop and plant_budget.get(crop, 0) <= 0:
            crop = choose_crop_atlas(farm, private, day, turn, require_held_seed=True)
        if crop and plant_budget.get(crop, 0) > 0:
            plant_budget[crop] -= 1
            return act_here(["PLANT", crop])

    # 10. Fertilizer logistics.
    shed_fertilizer = (private.get("shed") or {}).get("FERTILIZER", 0)
    if inv.get("FERTILIZER", 0) > 0:
        fertilize_target = find_fertilizer_target(farm, board_size, ux, uy, day, exclude=claimed)
        if fertilize_target:
            moved = walk_to(fertilize_target)
            if moved:
                return moved
    elif shed_fertilizer > 0 and find_fertilizer_target(farm, board_size, ux, uy, day, exclude=claimed):
        if is_shed_adjacent(ux, uy, board_size):
            return act_here(["PICKUP", "FERTILIZER", min(shed_fertilizer, 3)])
        moved = walk_to(nearest_shed_tile(ux, uy, board_size))
        if moved:
            return moved

    # 11. Reclaim a weed elsewhere.
    weed_target = find_nearest_target(farm, board_size, ux, uy, "weed", day, exclude=claimed)
    if weed_target:
        moved = walk_to(weed_target)
        if moved:
            return moved

    # 12. Walk toward the closest useful tile.
    fallback_target = find_nearest_target(farm, board_size, ux, uy, "any", day, seeds, exclude=claimed)
    if fallback_target and fallback_target != (ux, uy):
        moved = walk_to(fallback_target)
        if moved:
            return moved

    # 13. Nothing to do.
    return ["PASS"]


def choose_farmer_action(state, claimed=None, pending_builds=None, feed_claimed=None,
                          plant_budget=None, wheat_budget=None):
    farm = state.get("farm")
    if not farm:
        return ["PASS"]
    farmer_pos = farm.get("farmer")
    if not farmer_pos or len(farmer_pos) != 2:
        return ["PASS"]
    return choose_unit_action(state, farmer_pos[0], farmer_pos[1], 0, claimed, pending_builds,
                               feed_claimed, plant_budget, wheat_budget)


# ---------------------------------------------------------------------
# Agent entry point
# ---------------------------------------------------------------------
def atlas(observation, configuration=None):
    """Always returns a well-formed action dict, even for a missing or
    malformed observation - any unexpected shape falls back to a safe
    PASS/empty response instead of crashing (a crash forfeits the match)."""
    try:
        obs = observation or {}
        state = extract_state(obs)
        farm = state["farm"]
        if not farm:
            return {"farmer": ["PASS"], "hands": [], "market": []}

        board_size = state["board_size"]
        day = state["day"]
        hour = state["hour"]
        turn = state["turn"]
        private = state["private"]
        seeds = private.get("seeds", {})

        claimed = set()
        pending_builds = [0]
        feed_claimed = set()
        plant_budget = dict(seeds)
        wheat_budget = {"WHEAT": private.get("shed", {}).get("WHEAT", 0)}

        farmer_action = choose_farmer_action(
            state, claimed, pending_builds, feed_claimed, plant_budget, wheat_budget
        )
        hands_actions = [
            choose_unit_action(
                state, hand[0], hand[1], idx + 1, claimed, pending_builds, feed_claimed,
                plant_budget, wheat_budget,
            )
            for idx, hand in enumerate(farm.get("hands") or [])
            if isinstance(hand, (list, tuple)) and len(hand) == 2
        ]

        market = decide_hire_orders_atlas(farm, day, hour, turn)
        filled_animals, _ = scan_animal_structures(farm, board_size)
        reserved_wheat = filled_animals * 2
        market += decide_market_actions_atlas(
            farm, private, state["market_state"], day, turn, reserved_wheat=reserved_wheat
        )
        market += decide_animal_market_actions_atlas(farm, private, board_size, day, turn)
        market += decide_land_orders_atlas(farm, board_size, turn)

        return {
            "farmer": farmer_action if isinstance(farmer_action, list) else ["PASS"],
            "hands": hands_actions,
            "market": market[:MAX_MARKET_ORDERS_PER_TURN],
        }
    except Exception:
        return {"farmer": ["PASS"], "hands": [], "market": []}


# The framework picks the LAST callable in this module's namespace, not a
# function literally named `agent` - keep this binding last (see main.py's
# own comment on this: anything callable defined below it silently hijacks
# the submission, with no error raised).
agent = atlas
