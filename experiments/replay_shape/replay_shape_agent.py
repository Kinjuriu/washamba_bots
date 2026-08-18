"""Reference opponent — Track C, Issue #21 (experiments/replay_shape_spec.md).

Reproduces the STRUCTURAL SHAPE real strong ladder agents exert — a big
farm, a scaling crew, animals that survive, and continuous high-throughput
selling — so a local experiment whose advantage only shows up against that
pressure (a bigger contested market, a farm that isn't starved for
capacity) becomes measurable at all. `starter`/`pass`/`random`/our own
~25-tile agent are all too small for this.

**This is a benchmarking tool, not a strategy to compete with main.py.**
Deliberately simple on crop selection (spec priority 5, lowest) so
complexity stays where the evidence says it should: farm scale, crew
scale, animal survival, selling throughput (priorities 1-4).

Standalone: does not import main.py. Every constant below is tagged HARD
or SOFT exactly as in replay_shape_spec.md, with a section reference, so a
reader can see which numbers are load-bearing and which are a reasonable
guess inside an evidenced range.

NOT wired into main.py. NOT a submission. NOT tuned toward a Kaggle score.
"""

# ---------------------------------------------------------------------
# Engine metadata (never hardcoded beyond this fallback - same convention
# as main.py/pricing.py: prefer the installed engine, reproduce only if
# the import path ever moves).
# ---------------------------------------------------------------------
try:
    from kaggle_environments.envs.kaggriculture.kaggriculture import (
        ANIMALS,
        CROPS,
        FARM_HAND_COST_MULT,
        LAND_ORDER,
        LAND_PRICES,
    )
except ImportError:
    CROPS = {
        "WHEAT":      {"seed": 10, "first_yield_day": 2, "max_yield_day": 4, "interval": 0, "max_yield": 6, "ongoing": False},
        "CARROT":     {"seed": 20, "first_yield_day": 2, "max_yield_day": 3, "interval": 0, "max_yield": 4, "ongoing": False},
        "TOMATO":     {"seed": 50, "first_yield_day": 8, "max_yield_day": 8, "interval": 1, "max_yield": 4, "ongoing": True},
        "STRAWBERRY": {"seed": 100, "first_yield_day": 10, "max_yield_day": 10, "interval": 2, "max_yield": 4, "ongoing": True},
        "MELON":      {"seed": 80, "first_yield_day": 10, "max_yield_day": 12, "interval": 0, "max_yield": 6, "ongoing": False},
    }
    ANIMALS = {
        "GOOSE": {"cost": 300, "structure": "COOP", "first_yield_day": 4, "interval": 1, "max_held": 4, "product": "EGG"},
        "COW":   {"cost": 400, "structure": "PASTURE", "first_yield_day": 8, "interval": 2, "max_held": 6, "product": "MILK"},
        "SHEEP": {"cost": 500, "structure": "PASTURE", "first_yield_day": 6, "interval": 3, "max_held": 6, "product": "WOOL"},
    }
    LAND_ORDER = ["NE", "SW", "SE"]
    LAND_PRICES = [1000, 2000, 4000]
    FARM_HAND_COST_MULT = 1

SEASON_DAYS = 30
TURNS_PER_DAY = 24
PLANTABLE_CROPS = ["WHEAT", "STRAWBERRY", "MELON"]  # no TOMATO, no CARROT - see spec §4
ACTIVE_ANIMALS = ["COW", "SHEEP"]
ANIMAL_STRUCTURE_KINDS = {ANIMALS[a]["structure"] for a in ACTIVE_ANIMALS if a in ANIMALS}

# ---------------------------------------------------------------------
# 1. FARM SCALE — spec §1, HARD
# ---------------------------------------------------------------------
# Two purchases only, targeting exactly 75 tiles (start 25 + 2*25). Never
# buys the third quadrant (SE, $4,000) - no replay episode in the audit
# ever went past 75.
LAND_PURCHASE_MIN_DAY = [6, 11]   # HARD floor day for purchase 1, 2
LAND_PURCHASES_TARGET = 2         # HARD - exactly two, not three

# ---------------------------------------------------------------------
# 2. CREW SCALE — spec §2, SOFT target via a HARD derivation rule
# ---------------------------------------------------------------------
# Derived from owned tiles, not a fixed cap - the shape Track A's own
# retry (1d5be21) used and mechanically reproduced the replay's crew
# curve with. TILES_PER_HAND=5 gives 5 hands at 25 tiles (today's
# baseline), 15 at 75 - the top of the spec's 12-15 SOFT range.
TILES_PER_HAND = 5
MAX_HANDS_TARGET = 15
MAX_HIRES_PER_TURN = 3
# NOT the same reserve as land/seed/animal purchases. This was the first
# bug this file shipped with: gating a $1-13 (fib-cost) hire behind the
# same $450 floor used for $1,000+ purchases is exactly the "mispriced
# cash gate" CLAUDE.md documents for this codebase's own history
# (MIN_MONEY_TO_HIRE 150 -> 20) - it silently blocked every hire for the
# whole first half of the season (measured: hands stayed at 0 through day
# 13 on seed 0). A hire is cheap; only the reserve needs to match that.
MIN_MONEY_TO_HIRE = 20
# v1.1 CASH-AWARE HIRING GATE (see experiments/replay_shape_v1_1_report.md).
#
# MIN_MONEY_TO_HIRE alone assumes every hire is cheap. It isn't: the
# engine resets `hires_today` to 0 every morning (kaggriculture.py
# `_do_hire`/`_hire_cost`), so hiring the 15th hand of a day is not "one
# more $1 hire" - it's fib(14) = 610, on top of every hire that came
# before it that same morning. A crew built up to 15 hands has, by the
# season's own arithmetic, paid roughly $1,596/day to REBUILD it from
# scratch every single morning (sum of fib(0..14)) - large enough by
# itself to explain the $20-34k final bank measured against a non-selling
# built-in, and the complete animal-scale/no-feed-collapse failure
# measured in self-play (replay_shape_validation_report.md).
#
# The fix is not a lower crew target - spec priority 2 is still 13-15
# crew "when economically feasible". It's pricing each candidate hire at
# its ACTUAL engine cost before queuing it, and refusing to queue it if
# paying that cost would drop the bank below MIN_MONEY_TO_HIRE. Concretely,
# in decide_hire_orders(): the number of hands already hired TODAY (not
# ever - hands clear nightly, so `len(farm["hands"])` mid-day already
# equals `hires_today`) fixes where on the fib curve the next hire falls;
# walk forward from there, one candidate at a time, and stop the moment
# `cash_so_far - next_cost < MIN_MONEY_TO_HIRE`. Cheap hires (fib(0..3) =
# $1-3) go through almost regardless of cash; the expensive tail
# (fib(10+) = $55+) only fires once the bank can actually absorb it. No
# new constant is introduced - MIN_MONEY_TO_HIRE is reused as the
# POST-hire floor instead of only a pre-hire floor, which is what "cash-
# aware" means here: the target (crew_target_for) never changes, only how
# fast the agent is willing to pay to reach it on a given day.

# ---------------------------------------------------------------------
# 3. ANIMAL SCALE — spec §3, SOFT total/species, HARD survival behaviour
# ---------------------------------------------------------------------
TARGET_TOTAL_ANIMALS = 9   # SOFT, top of the 8-9 evidenced range
MIN_SHEEP = 3              # SOFT floor so the roster stays COW-majority,
                            # not COW-only, matching the ~5-6:3 split
ANIMAL_SPEND_CAP_FRACTION = 0.6
# Implements the stated priority order (farm scale > crew scale > animal
# survival) as a real sequencing rule, not just a comment. First run of
# this file had no floor here at all: animals started buying on day 0,
# before land/crew or any production income existed, and burned ~$1,500
# on 3 sheep in the first 3 turns alone - the dominant cause of a
# measured $0 cash trough on days 8-12 that then stunted BOTH land
# (stuck at 50 tiles, second purchase never affordable) and crew (hands
# crashed from 5 to 0 and only recovered to 10, never reaching the
# derived 15-hand target). Day 5 gives WHEAT's first harvest
# (first_yield_day=2) a few days to land before animal spending starts
# competing with land/crew for the same early cash.
ANIMAL_PURCHASES_MIN_DAY = 5
MIN_WHEAT_RESERVE_FOR_FEEDING = 6
WHEAT_CARRY_BATCH = 3
# HARD behavioral constraint: never buy an animal (or a hand, above) if
# doing so would leave less than this in the bank - the mechanism behind
# our own repo's measured "second animal" false-negative was exactly a
# purchase that then couldn't be fed (85fbbc2).
MIN_CASH_RESERVE_FOR_ANIMALS = 450

# ---------------------------------------------------------------------
# 4. MARKET SELLING THROUGHPUT — spec §6, SOFT shape, no liquidation state
# ---------------------------------------------------------------------
# Deliberately no day-gated branch anywhere in this file. "Meaningful
# selling from ~day 10" is expected to emerge from when MELON/STRAWBERRY
# actually become harvestable (first_yield_day=10 for both), not from an
# explicit day check - matching the spec's own state-machine instruction
# ("achieved by NOT having a liquidation state, rather than by tuning a
# threshold").
SELL_FLOOR_PRICE = 2       # near the engine's $1 floor - throughput over
                            # price-picking, priority 4 > priority 5
SELL_CAP_PER_TURN = 40     # generous relative to main.py's own 10-15, to
                            # avoid the cap itself becoming the bottleneck
                            # this experiment exists to expose

# ---------------------------------------------------------------------
# 5. CROP MIX — spec §4, SOFT windows, HARD exclusions
# ---------------------------------------------------------------------
MELON_WINDOW = (0, 9)          # SOFT - inside the evidenced 0-7..0-11 span
STRAWBERRY_WINDOW = (5, 12)    # SOFT - matches spec directly
# WHEAT has no window - continuous fallback, HARD per spec §4.
# TOMATO is not in PLANTABLE_CROPS at all - HARD exclusion.


# =======================================================================
# Engine-interaction primitives (standalone reimplementation - see
# CLAUDE.md's silent-failure gotchas for why these exact semantics matter:
# tiles are row-major [y][x], units are [x, y]; shed adjacency is the four
# inner-corner tiles; a fresh planting with 0 waterings dies that night).
# =======================================================================

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


def shed_access_tiles(board_size):
    half = board_size // 2
    return [(half - 1, half - 1), (half, half - 1), (half - 1, half), (half, half)]


def is_shed_adjacent(x, y, board_size):
    return (x, y) in shed_access_tiles(board_size)


def nearest_shed_tile(fx, fy, board_size):
    tiles = shed_access_tiles(board_size)
    return min(tiles, key=lambda t: abs(t[0] - fx) + abs(t[1] - fy))


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


def owned_tile_count(farm):
    """Non-LOCKED tiles - the live "how big is our farm" figure everything
    in §1/§2 derives from."""
    tiles = farm.get("tiles") or []
    return sum(1 for row in tiles for t in row if t != "LOCKED")


def unit_inventory(private, unit_idx):
    inventories = private.get("inventories") or []
    if 0 <= unit_idx < len(inventories) and isinstance(inventories[unit_idx], dict):
        return inventories[unit_idx]
    return {}


def carried_animal(inv):
    for animal in ACTIVE_ANIMALS:
        if inv.get(animal, 0) > 0:
            return animal
    return None


def scan_animal_structures(farm, board_size):
    tiles = farm.get("tiles") or []
    filled, unfilled = 0, 0
    for y in range(board_size):
        row = tiles[y] if y < len(tiles) else []
        for tile in row:
            if isinstance(tile, dict) and tile.get("kind") in ANIMAL_STRUCTURE_KINDS:
                if "animal" in tile:
                    filled += 1
                else:
                    unfilled += 1
    return filled, unfilled


def count_owned_animals(farm, private, board_size):
    shed = private.get("shed", {})
    total = sum(shed.get(a, 0) for a in ACTIVE_ANIMALS)
    for inv in private.get("inventories") or []:
        if isinstance(inv, dict):
            total += sum(inv.get(a, 0) for a in ACTIVE_ANIMALS)
    filled, unfilled = scan_animal_structures(farm, board_size)
    return total + filled + unfilled


def count_animals_by_species(farm, private, board_size):
    counts = {a: 0 for a in ACTIVE_ANIMALS}
    shed = private.get("shed", {})
    for a in ACTIVE_ANIMALS:
        counts[a] += shed.get(a, 0)
    for inv in private.get("inventories") or []:
        if isinstance(inv, dict):
            for a in ACTIVE_ANIMALS:
                counts[a] += inv.get(a, 0)
    tiles = farm.get("tiles") or []
    for y in range(len(tiles)):
        for tile in tiles[y]:
            if isinstance(tile, dict) and tile.get("kind") in ANIMAL_STRUCTURE_KINDS:
                species = tile.get("animal")
                if species in counts:
                    counts[species] += 1
    return counts


def find_nearest_target(farm, board_size, fx, fy, task, day, seeds=None, exclude=None):
    """Simplified from main.py's version - drops fertilizer handling (out
    of scope). Keeps an "empty" task (nearest unclaimed empty tile) even
    though the first draft of this file dropped it as "just logistics":
    without it, a unit only ever plants or builds when it happens to
    already be standing on empty ground, which on a 75-tile farm is close
    to never - measured directly (only 4-9 of 75 tiles ever held a PLANT
    at once, and the second PASTURE didn't get built until day ~20 despite
    being allowed from day 5). This is the same class of bug CLAUDE.md
    already documents as the "weed cascade": a missing seek-target turns a
    priority into something that only fires by accident."""
    exclude = exclude or set()
    tiles = farm.get("tiles") or []
    best_target, best_distance = None, None

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
            elif isinstance(tile, dict) and "animal" in tile:
                is_ripe = tile.get("yield_units", 0) > 0
                needs_feed = not tile.get("fed_today", True)
                if task == "harvest" and is_ripe:
                    is_match = True
                elif task == "feed" and needs_feed:
                    is_match = True
            elif isinstance(tile, dict) and tile.get("kind") == "WEED" and task == "weed":
                is_match = True
            elif (
                isinstance(tile, dict)
                and tile.get("kind") in ANIMAL_STRUCTURE_KINDS
                and "animal" not in tile
                and task == "empty_structure"
            ):
                is_match = True
            elif tile is None and task == "empty":
                is_match = True

            if is_match:
                distance = abs(x - fx) + abs(y - fy)
                if best_distance is None or distance < best_distance:
                    best_distance = distance
                    best_target = (x, y)
    return best_target


def _closer_target(fx, fy, a, b):
    if a is None:
        return b
    if b is None:
        return a
    da = abs(a[0] - fx) + abs(a[1] - fy)
    db = abs(b[0] - fx) + abs(b[1] - fy)
    return a if da <= db else b


# =======================================================================
# 1. FARM SCALE - land decisions
# =======================================================================

def decide_land_orders(farm, day):
    """At most one BUY_LAND per turn. HARD per spec §1: exactly two
    purchases, floor-gated on day AND cash (not a blind one-shot on the
    day alone - Issue #21's own question 3 asks about cash-relative
    timing, so this checks both rather than assuming the day is enough).
    """
    unlocked_extra = len(farm.get("unlocked_quadrants") or []) - 1  # NW is free
    unlocked_extra = max(0, unlocked_extra)
    if unlocked_extra >= LAND_PURCHASES_TARGET:
        return []
    if unlocked_extra >= len(LAND_PRICES):
        return []
    min_day = LAND_PURCHASE_MIN_DAY[unlocked_extra] if unlocked_extra < len(LAND_PURCHASE_MIN_DAY) else 10**9
    if day < min_day:
        return []
    price = LAND_PRICES[unlocked_extra]
    if farm.get("money", 0) < price:
        return []
    return [["BUY_LAND"]]


# =======================================================================
# 2. CREW SCALE - hiring decisions
# =======================================================================

def crew_target_for(owned_tiles):
    """HARD derivation rule, SOFT resulting number - see §2 constants."""
    return min(MAX_HANDS_TARGET, max(1, owned_tiles // TILES_PER_HAND))


def _fib_hire_cost(n_already_hired_today):
    """The engine's own recurrence (kaggriculture.py `_fib`): fib(0)=1,
    fib(1)=1, fib(2)=2, fib(3)=3, fib(4)=5, ... Reproduced, not
    reinvented - `_hire_cost` in the engine is `mult * _fib(hires_today)`,
    and this is that same formula."""
    a, b = 1, 1
    for _ in range(n_already_hired_today):
        a, b = b, a + b
    return FARM_HAND_COST_MULT * a


def decide_hire_orders(farm, day):
    """Cash-aware (v1.1): prices each candidate hire at its actual fib
    cost before queuing it, using the correct "hires so far today" index
    (hands clear nightly, so the current hand count mid-day already IS
    that count - no separate counter needed). Queues hires one at a time,
    walking up the fib curve, and stops the moment paying for the next one
    would drop the bank below MIN_MONEY_TO_HIRE. Still targets the full
    crew_target_for() ceiling - this only throttles how many of today's
    candidate hires are affordable today, it never lowers the target
    itself. See the CASH-AWARE HIRING GATE comment above MIN_MONEY_TO_HIRE
    for the full rationale."""
    money = farm.get("money", 0)
    if money < MIN_MONEY_TO_HIRE:
        return []
    target = crew_target_for(owned_tile_count(farm))
    already = len(farm.get("hands") or [])
    shortfall = max(0, target - already)
    n_to_try = min(shortfall, MAX_HIRES_PER_TURN)

    orders = []
    remaining_cash = money
    for k in range(n_to_try):
        cost = _fib_hire_cost(already + k)
        if remaining_cash - cost < MIN_MONEY_TO_HIRE:
            break
        remaining_cash -= cost
        orders.append(["HIRE"])
    return orders


# =======================================================================
# 3. ANIMAL SCALE - build/buy decisions
# =======================================================================

def choose_animal_to_build(farm, private, board_size, day, pending_builds):
    if day < ANIMAL_PURCHASES_MIN_DAY:
        return None
    filled, unfilled = scan_animal_structures(farm, board_size)
    if unfilled > 0 or pending_builds > 0:
        return None
    # One structure holds exactly one animal - `max_held` (ANIMALS table)
    # is the yield-accumulation cap before a forced harvest, not a
    # per-structure headcount; dividing by it in an earlier draft targeted
    # 2 structures for 9 animals instead of 9, and both built pastures
    # sat permanently full while 7 purchased animals stayed stranded in
    # the shed for the rest of the season (measured).
    if filled >= TARGET_TOTAL_ANIMALS:
        return None

    # An already-bought animal sitting in the shed needs a home regardless
    # of current cash - BUILD/PICKUP/PLACE are all free farm actions, only
    # BUY_ANIMAL costs money. The first draft of this file gated building
    # on the same cash reserve as buying, which stranded 7 of 9 purchased
    # animals in the shed for the rest of the season (measured: COW 5 +
    # SHEEP 2 sitting unplaced from day 15 through day 29) because cash
    # spent elsewhere never recovered above the reserve again.
    shed = (private or {}).get("shed", {})
    for animal in ACTIVE_ANIMALS:
        if shed.get(animal, 0) > 0:
            return animal

    money = farm.get("money", 0)
    if money < MIN_CASH_RESERVE_FOR_ANIMALS:
        return None
    remaining_days = remaining_season_days(day)
    for animal in ACTIVE_ANIMALS:
        info = ANIMALS.get(animal, {})
        cost, first_yield_day = info.get("cost"), info.get("first_yield_day")
        if cost is None or first_yield_day is None or first_yield_day > remaining_days:
            continue
        if money - cost >= MIN_CASH_RESERVE_FOR_ANIMALS and cost <= money * ANIMAL_SPEND_CAP_FRACTION:
            return animal
    return None


def decide_animal_market_actions(farm, private, board_size, day):
    actions = []
    money = farm.get("money", 0)
    remaining_days = remaining_season_days(day)

    if day >= ANIMAL_PURCHASES_MIN_DAY and count_owned_animals(farm, private, board_size) < TARGET_TOTAL_ANIMALS:
        held = count_animals_by_species(farm, private, board_size)
        # SOFT species mix: keep at least MIN_SHEEP, otherwise prefer COW -
        # matches the ~5-6:3 cow:sheep split without hardcoding an exact
        # ratio the n=2 evidence can't really support to the unit.
        if held.get("SHEEP", 0) < MIN_SHEEP:
            preferred_order = ["SHEEP", "COW"]
        else:
            preferred_order = ["COW", "SHEEP"]
        for animal in preferred_order:
            info = ANIMALS.get(animal, {})
            cost, first_yield_day = info.get("cost"), info.get("first_yield_day")
            if cost is None or first_yield_day is None or first_yield_day > remaining_days:
                continue
            if money - cost < MIN_CASH_RESERVE_FOR_ANIMALS or cost > money * ANIMAL_SPEND_CAP_FRACTION:
                continue
            actions.append(["BUY_ANIMAL", animal, 1])
            break

    filled, _ = scan_animal_structures(farm, board_size)
    if filled > 0 and money > 0:
        shed_wheat = private.get("shed", {}).get("WHEAT", 0)
        carried_wheat = sum(
            inv.get("WHEAT", 0) for inv in (private.get("inventories") or []) if isinstance(inv, dict)
        )
        if shed_wheat + carried_wheat < MIN_WHEAT_RESERVE_FOR_FEEDING:
            actions.append(["BUY_PRODUCT", "WHEAT", 1])

    return actions


# =======================================================================
# 4. MARKET SELLING THROUGHPUT
# =======================================================================

def decide_sell_orders(private, market_state):
    """No liquidation-day branch anywhere - continuous, price-permissive,
    throughput-first (spec §6/priority 4). Reserves a small wheat buffer
    for feeding, same mechanism as main.py's, since selling the feed
    reserve out from under a hungry animal is a 300-500 cost mistake this
    experiment isn't testing."""
    actions = []
    shed = private.get("shed", {})
    prices = market_state.get("prices", {})
    for product, quantity in shed.items():
        if quantity <= 0:
            continue
        if product in ACTIVE_ANIMALS:
            continue  # not a sellable market product - it's livestock in transit
        sell_quantity = quantity
        if product == "WHEAT":
            sell_quantity = max(0, quantity - MIN_WHEAT_RESERVE_FOR_FEEDING)
        if sell_quantity <= 0:
            continue
        price = prices.get(product, 0)
        if price < SELL_FLOOR_PRICE:
            continue
        actions.append(["SELL", product, min(sell_quantity, SELL_CAP_PER_TURN)])
    return actions


# =======================================================================
# 5. CROP MIX - deliberately simple, window-gated, no economic scoring
# =======================================================================

def choose_crop(day, seeds, money, remaining_days):
    """Fixed priority MELON > STRAWBERRY > WHEAT inside each crop's
    window, gated only by season-maturity and affordability - no price,
    no forecast, no glut discount. Priority 5 says don't over-optimize
    this; the interesting parts of this agent are §1-4 above."""
    candidates = []
    if MELON_WINDOW[0] <= day <= MELON_WINDOW[1]:
        candidates.append("MELON")
    if STRAWBERRY_WINDOW[0] <= day <= STRAWBERRY_WINDOW[1]:
        candidates.append("STRAWBERRY")
    candidates.append("WHEAT")  # always-available fallback, HARD continuous

    for crop in candidates:
        info = CROPS.get(crop)
        if not info:
            continue
        first_yield_day = info.get("first_yield_day")
        if first_yield_day is not None and first_yield_day > remaining_days:
            continue
        have_seed = seeds.get(crop, 0) > 0
        can_afford = money >= info.get("seed", 10**9)
        if have_seed or can_afford:
            return crop
    return None


MAX_SEED_STOCKPILE = 3
SEED_SPEND_CAP_FRACTION = 0.5


def decide_seed_orders(farm, private, day):
    """Buy one seed of the currently-preferred crop at a time, same
    cadence-safe pattern as main.py's should_buy_seed (batch-restock
    trigger, not "buy the instant stock dips" - CLAUDE.md documents that
    naive version as an ~$80/turn repurchase spiral). Without this
    function at all, choose_crop()'s window logic has nothing to act on:
    PLANT only ever consumes an ALREADY-HELD seed, and a fresh game holds
    zero - this was the file's dominant bug on the first run (0 crop
    income for the whole season, verified)."""
    money = farm.get("money", 0)
    seeds = private.get("seeds", {})
    crop = choose_crop(day, seeds, money, remaining_season_days(day))
    if not crop:
        return []
    held = seeds.get(crop, 0)
    if held >= MAX_SEED_STOCKPILE:
        return []
    info = CROPS.get(crop, {})
    cost = info.get("seed")
    if cost is None or cost > money or cost > money * SEED_SPEND_CAP_FRACTION:
        return []
    return [["BUY_SEED", crop, 1]]


# =======================================================================
# Per-unit action ladder - the engine-interaction plumbing every priority
# above needs to actually execute. Simplified from main.py's: no
# fertilizer logistics, no forward pricing, no plant_budget beyond a
# simple per-turn seed count (kept, because the engine drops ALL plant
# requests for an oversubscribed crop, not just the excess - a real
# correctness trap, not a strategy choice, so it stays even in a
# "don't over-optimize" agent).
# =======================================================================

def choose_unit_action(state, ux, uy, unit_idx, claimed, pending_builds, feed_claimed, plant_budget):
    farm = state["farm"]
    board_size = state["board_size"]
    day = state["day"]
    private = state["private"]
    seeds = private.get("seeds", {})
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

    # 1. Feed - outranks even a ready harvest (missing it twice is permanent).
    if is_animal_tile and not tile.get("fed_today") and inv.get("WHEAT", 0) > 0:
        feed_claimed.add((ux, uy))
        return act_here(["FEED"])

    # 2. Harvest.
    if isinstance(tile, dict) and tile.get("kind") == "PLANT" and is_harvestable(tile, day):
        return act_here(["HARVEST"])
    if is_animal_tile:
        animal_info = ANIMALS.get(tile.get("animal"), {})
        max_held = animal_info.get("max_held", 1)
        held = tile.get("yield_units", 0)
        if held > 0 and (held >= max_held - 1 or day >= SEASON_DAYS - 2):
            return act_here(["HARVEST"])

    # 3. Water / care.
    if isinstance(tile, dict) and tile.get("kind") == "PLANT" and not tile.get("watered_today", True):
        return act_here(["WATER"])
    if is_animal_tile and not tile.get("cared_today"):
        return act_here(["CARE"])

    # 4. Place a carried animal.
    animal_in_hand = carried_animal(inv)
    if animal_in_hand and isinstance(tile, dict) and "animal" not in tile:
        structure = ANIMALS.get(animal_in_hand, {}).get("structure")
        if structure and tile.get("kind") == structure:
            return act_here(["PLACE", animal_in_hand])

    # 5. Shed errands: collect a bought animal, or wheat for feeding.
    if is_shed_adjacent(ux, uy, board_size):
        shed = private.get("shed", {})
        if animal_in_hand is None:
            _, unfilled = scan_animal_structures(farm, board_size)
            if unfilled > 0:
                for animal in ACTIVE_ANIMALS:
                    if shed.get(animal, 0) > 0:
                        return act_here(["PICKUP", animal, 1])
        if inv.get("WHEAT", 0) <= 0 and shed.get("WHEAT", 0) > 0:
            if find_nearest_target(farm, board_size, ux, uy, "feed", day, exclude=claimed):
                return act_here(["PICKUP", "WHEAT", min(shed.get("WHEAT", 0), WHEAT_CARRY_BATCH)])

    # 6. Move toward urgent work elsewhere: feed first, then harvest/water.
    feed_target = find_nearest_target(farm, board_size, ux, uy, "feed", day)
    if feed_target in feed_claimed:
        feed_target = None
    if feed_target:
        if inv.get("WHEAT", 0) <= 0:
            if private.get("shed", {}).get("WHEAT", 0) > 0:
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

    # 7. Carrying an unplaced animal - go find it a home.
    if animal_in_hand:
        structure_target = find_nearest_target(farm, board_size, ux, uy, "empty_structure", day, exclude=claimed)
        if structure_target:
            moved = walk_to(structure_target)
            if moved:
                return moved

    # 8. Reclaim a weed under our feet.
    if isinstance(tile, dict) and tile.get("kind") == "WEED":
        return act_here(["DIG"])

    # 9. Empty ground: build an animal structure if still growing that
    #    side of the farm, else plant.
    if tile is None:
        animal_to_build = choose_animal_to_build(farm, private, board_size, day, pending_builds[0])
        if animal_to_build:
            pending_builds[0] += 1
            return act_here([f"BUILD_{ANIMALS[animal_to_build]['structure']}"])
        crop = choose_crop(day, seeds, farm.get("money", 0), remaining_season_days(day))
        if crop and plant_budget.get(crop, 0) > 0:
            plant_budget[crop] -= 1
            return act_here(["PLANT", crop])

    # 10. Reclaim the nearest weed elsewhere.
    weed_target = find_nearest_target(farm, board_size, ux, uy, "weed", day, exclude=claimed)
    if weed_target:
        moved = walk_to(weed_target)
        if moved:
            return moved

    # 11. Walk toward the nearest unclaimed empty tile to build or plant
    #     on - without this, step 9 only fires when a unit happens to
    #     already be standing on empty ground, which on a large farm with
    #     far more tiles than units is close to never (see
    #     find_nearest_target's docstring for the measured effect of
    #     leaving this out). Only worth seeking if there's actually
    #     something to do there once we arrive.
    # (No "is there actually a seed for this" pre-check: private["seeds"]
    # is a dict of every crop at 0 by default - always truthy - so that
    # would silently never filter anything anyway. Step 9's own
    # choose_crop()/plant_budget checks already no-op harmlessly if there's
    # nothing plantable on arrival; worst case is one wasted walk turn.)
    empty_target = find_nearest_target(farm, board_size, ux, uy, "empty", day, exclude=claimed)
    if empty_target:
        moved = walk_to(empty_target)
        if moved:
            return moved

    # 12. Nothing useful - pass.
    return ["PASS"]


# =======================================================================
# Top-level agent
# =======================================================================

def extract_state(obs):
    obs = obs or {}
    farm = get_player_farm(obs)
    private = obs.get("private") or {}
    tiles = farm.get("tiles") if farm else None
    return {
        "farm": farm,
        "private": private,
        "market_state": {
            "prices": (obs.get("market") or {}).get("prices") or {},
            "inventory": (obs.get("market") or {}).get("inventory") or {},
        },
        "board_size": len(tiles) if tiles else 0,
        "day": obs.get("day", 0),
        "hour": obs.get("hour", 0),
    }


def replay_shape_agent(obs):
    """Deterministic, standalone. Same last-callable-in-module contract as
    main.py (see CLAUDE.md) - keep `agent = replay_shape_agent` last."""
    try:
        state = extract_state(obs)
        farm = state["farm"]
        if not farm:
            return {"farmer": ["PASS"], "hands": [], "market": []}

        day = state["day"]
        private = state["private"]
        seeds = private.get("seeds", {})

        claimed = set()
        pending_builds = [0]
        feed_claimed = set()
        plant_budget = dict(seeds)

        farmer_action = choose_unit_action(
            state, farm["farmer"][0], farm["farmer"][1], 0,
            claimed, pending_builds, feed_claimed, plant_budget,
        )
        hands_actions = [
            choose_unit_action(
                state, hand[0], hand[1], idx + 1,
                claimed, pending_builds, feed_claimed, plant_budget,
            )
            for idx, hand in enumerate(farm.get("hands") or [])
            if isinstance(hand, (list, tuple)) and len(hand) == 2
        ]

        market = decide_hire_orders(farm, day)
        market += decide_land_orders(farm, day)
        market += decide_seed_orders(farm, private, day)
        market += decide_sell_orders(private, state["market_state"])
        market += decide_animal_market_actions(farm, private, state["board_size"], day)

        return {
            "farmer": farmer_action,
            "hands": hands_actions,
            "market": market[:10],  # engine silently drops orders past 10
        }
    except Exception:
        return {"farmer": ["PASS"], "hands": [], "market": []}


# The framework runs the LAST callable in this module's namespace, not a
# function named `agent` (kaggle_environments/agent.py:64) - keep this
# binding last, same contract as main.py.
agent = replay_shape_agent
