"""
nikaangukia_meroni_v1
======================

Washamba Bots' deterministic agent for the Kaggriculture competition.

This is deliberately NOT a sophisticated AI. Every unit - the main farmer
and any hired hands - shares one reactive, rule-based priority list, and
they coordinate through a per-turn claim set so two units never spend
their turns on the same tile:

  1. Feeds an animal under its feet - ahead of even a ready harvest. A
     missed feeding is a permanent loss (the animal escapes for good),
     and it silently costs the CARE bank too, which only pays out on a
     day the animal was also fed.
  2. Harvests a ripe crop, or an animal whose held yield is near its cap
     (collecting its fertilizer first, since that is a separate output).
  3. Waters a crop, or cares for an already-fed animal, under its feet.
  4. Places a carried animal on the empty coop/pasture under its feet.
  5. Runs shed errands: collects a bought animal waiting for its home, or
     several days of wheat to go feed an animal elsewhere.
  6. Moves toward urgent work elsewhere (an animal to feed, a ripe crop,
     a crop about to weed out) before anything below.
  7. Carries a picked-up animal toward its coop/pasture if not there yet.
  8. Digs a weed under its feet for free, reclaiming dead land.
  9. Builds a coop (if still growing the animal side of the farm) or
     plants a sensible crop when standing on empty ground.
  10. Runs the fertilizer errand - collects a batch from the shed and
     carries it to an ongoing crop that is inside its payout window.
  11. Reclaims the nearest weed elsewhere - dead land is a permanent loss.
  12. Otherwise walks toward the closest useful tile.
  13. PASSes if there is genuinely nothing useful to do.

It also does simple, threshold-based market decisions: sell shed goods
when the price is good (capped per turn for premium goods so a big
harvest doesn't crash its own price), buy one seed at a time when we
need one and can afford it, hire farm hands early each day against how
much work is actually pending, and buy one GOOSE at a time (see
ACTIVE_ANIMALS) plus a small wheat safety net for feeding it. Everything
still in the shed from LIQUIDATION_START_DAY on is sold regardless of
price - inventory scores nothing once the season ends.

The one piece of real economics is choose_crop(). It scores a crop by
revenue per growing day, discounted both by how oversupplied that market
already is and by how much of that crop we are *ourselves* about to
deliver. That second term matters more than it sounds: a melon planted
today sells twelve days from now, into the price our own harvest creates.
See the docstring there before touching the formula - an earlier version
of it ranked crops by cheapness and never planted a melon all season.

NOT implemented in this version (on purpose, to keep V1 simple):
  - COW / SHEEP (the animal logic is data-driven off ACTIVE_ANIMALS, so
    enabling them is a config change, not new logic - though their
    products, MILK and WOOL, still need SELL_PRICE_THRESHOLDS/
    MAX_SELL_PER_TURN entries of their own before that's a good idea).
  - Buying land / unlocking new quadrants.
  - Any multi-turn planning, lookahead, or opponent modelling.

Every piece of environment metadata used here (CROPS, action names, the
observation shape) comes from the official Kaggriculture "Getting
Started" / Hosts notebook. Nothing is invented.
"""

# ---------------------------------------------------------------------
# Environment metadata (read from the engine, never hardcoded)
# ---------------------------------------------------------------------

# CROPS is the same environment-provided metadata table used in the
# official starter notebook's "Melon Maxxer" example. It tells us, per
# crop, the seed cost, how many days until it can be harvested, and how
# many units it yields - so we don't have to hard-code any of that
# ourselves.
try:
    from kaggle_environments.envs.kaggriculture.kaggriculture import ANIMALS, CROPS
except ImportError:
    # Defensive fallback: if this ever runs somewhere the environment
    # package isn't importable (e.g. a stripped-down test sandbox), we
    # still don't want the whole agent to blow up at import time. With
    # an empty CROPS table the agent simply won't plant anything - it
    # will still harvest/water/sell/PASS safely.
    CROPS = {}
    ANIMALS = {}

# Baseline market stock per product (the engine's I0, 10,000 for every
# product at time of writing). Crop scoring needs it to tell a real glut
# from the normal starting inventory.
try:
    from kaggle_environments.envs.kaggriculture.kaggriculture import MARKET_PARAMS

    MARKET_BASELINE_STOCK = {
        product: params.get("I0")
        for product, params in MARKET_PARAMS.items()
    }
except ImportError:
    MARKET_BASELINE_STOCK = {}

DEFAULT_BASELINE_STOCK = 10000

# How many units a product's market absorbs before its price falls apart
# (the engine's per-resource T). This varies hugely and is the difference
# between a crop being worth growing in bulk or not: at T units above the
# baseline, WHEAT still fetches $20 of its $25 base, while MELON goes from
# $250 to $1 and STRAWBERRY from $120 to $1.
try:
    from kaggle_environments.envs.kaggriculture.kaggriculture import MARKET_PARAMS as _MP

    MARKET_ABSORPTION = {product: params.get("T") for product, params in _MP.items()}
except ImportError:
    MARKET_ABSORPTION = {}

DEFAULT_ABSORPTION = 300

# How hard our own incoming supply discounts a crop. Higher means the agent
# diversifies sooner rather than pouring an entire season into one market.
SELF_SUPPLY_EXPONENT = 2.0

# Floor on the glut discount, so even a badly oversupplied crop keeps some
# score rather than dropping out of consideration entirely.
MIN_GLUT_DISCOUNT = 0.1


# ---------------------------------------------------------------------
# Season
# ---------------------------------------------------------------------

# The season is a fixed 30 days (0-indexed: day 0 through day 29), per the
# competition's hard constraints - not something that varies per episode.
SEASON_DAYS = 30

# ---------------------------------------------------------------------
# Crop selection
# ---------------------------------------------------------------------

# The only crops the environment actually defines seed metadata for.
# (EGG / MILK / WOOL / FERTILIZER are products, not plantable crops -
# they come from animals rather than seeds.)
PLANTABLE_CROPS = ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON"]

# ---------------------------------------------------------------------
# Selling and the shed
# ---------------------------------------------------------------------

# Minimum market price we're willing to sell a product at. These are
# simple, per-product thresholds so the team can tune them independently
# as we learn more about how each product's price tends to move.
# Any product not listed here falls back to DEFAULT_SELL_THRESHOLD.
SELL_PRICE_THRESHOLDS = {
    "WHEAT": 20,
    "CARROT": 25,
    "TOMATO": 40,
    "STRAWBERRY": 90,
    "MELON": 180,
    "EGG": 35,
}
DEFAULT_SELL_THRESHOLD = 50

# Premium goods (base price > $100) crash hard toward the $1 floor when a
# large quantity is sold in one order, and there's no buy-back to undo it
# (BUY_PRODUCT only works for WHEAT/FERTILIZER) - the market only recovers
# gradually, via town shop/town-centre consumption between turns. Cap how
# much of these we sell in a single turn so a big harvest doesn't crater the
# price it would otherwise have fetched; the remainder stays in the shed and
# sells on a later turn once the price has had a chance to recover.
MAX_SELL_PER_TURN = {
    "STRAWBERRY": 10,
    "MELON": 15,
}

# The shed holds at most 100 non-seed items - anything harvested past that
# cap is silently discarded at end of day, with no error and no way to
# recover it (see docs/kaggriculture_context.md). should_sell() alone can
# hold a slow-moving product indefinitely while price stays below
# threshold, right up until it overflows and evaporates for free. Once the
# shed gets this full, force a sale regardless of price - a mediocre sale
# beats a guaranteed $0.
SHED_FORCE_SELL_THRESHOLD = 70

# Anything still sitting in the shed when the season ends is worth exactly
# nothing - there is no scoring credit for inventory, only for bank balance.
# Measured on a real season: the shed sat at its 100-item cap on day 28
# holding 95 melons, because the price had drifted below the sell threshold
# and the agent kept waiting for a recovery that the season had no time
# left to deliver. From this day on, sell everything regardless of price.
# Still spread across turns via MAX_SELL_PER_TURN so the last few days
# don't dump the whole stock into one price-crashing order.
#
# Day 19, not 25, and the two evaluations disagree about that - which is the
# whole reason it is 19. Against `starter`, which never sells, holding out
# for a better price wins: day 19 is -440 there, worse on 10 of 12 seeds.
# Head to head against a copy of ourselves, where the order book is actually
# contested, day 19 is +617 and wins 21 of 24 matches. Selling into a market
# a competitor is also selling into is a race for the town's daily demand,
# and the loser gets the crashed price. The ladder is contested, so the
# head-to-head number is the one that predicts it (experiments/head_to_head.py).
#
# Swept 13/16/19/21/23/25/27: 19 is an interior peak, not an edge effect.
LIQUIDATION_START_DAY = 19

# ---------------------------------------------------------------------
# Seed buying
# ---------------------------------------------------------------------

# Don't stockpile more seeds of one crop than this - keeps cash free for
# other things instead of hoarding.
MAX_SEED_STOCKPILE = 3

# Never spend more than this fraction of our current cash on a single
# seed purchase, so a bad crop pick can't wipe out our bank balance.
SEED_SPEND_CAP_FRACTION = 0.5

# ---------------------------------------------------------------------
# Fertilizer
# ---------------------------------------------------------------------

# FERTILIZE marks a plant for `day`, `day+1` and `day+2`, and the bonus is
# paid only on days the plant is *also* watered - `_daily_refresh_plants`
# gates it on `was_watered`. It is a multiplier on watering, never a
# substitute for it.
#
# Only ongoing crops can use it at all. `_daily_refresh_plants` skips
# one-time crops outright (`if not cd["ongoing"]: continue`), so a unit of
# fertilizer spent on wheat, carrot or melon is simply thrown away. That
# leaves the two ongoing crops, where each covered production tick banks
# +2 instead of +1:
#
#   TOMATO      interval 1 -> the 3-day cover catches 3 ticks
#   STRAWBERRY  interval 2 -> catches 2 ticks
FERTILIZABLE_CROPS = ("TOMATO", "STRAWBERRY")

# Bought fertilizer lands in the shed, but FERTILIZE spends from the acting
# unit's own inventory - so a unit has to stand shed-adjacent and PICKUP
# before it can fertilise anything. Carry a few at a time so one trip serves
# several plants instead of one.
FERTILIZER_CARRY_BATCH = 3

# Don't buy fertilizer we have no plant to use it on, and keep a lid on the
# stock so it doesn't crowd the shed or the cash. The Goose also produces
# fertilizer for free via COLLECT_FERTILIZER, so this cap is mostly a brake
# on buying what the animal already supplies.
MAX_FERTILIZER_STOCK = 6

# Fertilizer bought this late can't catch enough production ticks to repay
# itself before the season ends.
FERTILIZER_LAST_USEFUL_DAY = 24

# ---------------------------------------------------------------------
# Labour
# ---------------------------------------------------------------------

# Farm hands. The n-th hire of a day costs farmHandCostMult * fib(n) with
# fib indexed 1, 1, 2, 3, 5, 8, ... (kaggriculture.py:_fib / _hire_cost), and
# the counter resets every morning - so the first hand of the day costs $1
# and four hands cost $7 total. That is trivial against a ~$5,000 bank, and
# a single farmer's upkeep capacity (watering and digging) is what actually
# caps this agent's income: plant more tiles than one unit can water and the
# surplus weeds out. Hands are the cheapest way to raise that ceiling.
# Cumulative day cost by crew size: 4 hands $7, 6 hands $20, 8 hands $54.
# Even eight is under $1,700 for a full season, which is small against the
# extra tiles they keep alive.
MAX_HANDS_PER_DAY = 8

# Hands are cleared at the end of every day and must be re-hired each
# morning, so hire in the first few turns - a hand bought at hour 20 costs
# the same as one bought at hour 0 but does a fraction of the work.
HIRE_BEFORE_HOUR = 4

# HIRE competes with SELL/BUY_SEED for the 10 market orders we get each
# turn, and surplus orders are dropped silently. Spread the morning's hiring
# across the first few turns instead of emitting the whole crew at once and
# pushing the day's sales off the end of the list.
MAX_HIRES_PER_TURN = 3

# Roughly how many tiles needing attention justify one more hand. This is
# the ratio that actually sets crew size; MAX_HANDS_PER_DAY is only a
# ceiling for when we own more land. Measured on the opening 25-tile
# quadrant: a ratio of 4 (about 6 hands) is clearly worse than a ratio of 6
# (about 4 hands) - roughly 1,300 to 2,600 bank worse per season. Surplus
# units do not idle politely, they plant tiles the crew then cannot water
# and spend seed money doing it.
WORK_TILES_PER_HAND = 6

# Don't spend our last coins on labour - seed money matters more.
MIN_MONEY_TO_HIRE = 150

# ---------------------------------------------------------------------
# Market order budget
# ---------------------------------------------------------------------

# The engine processes at most this many market orders per player per turn
# and silently drops the rest (kaggriculture.json: maxMarketOrdersPerTurn),
# so going over the cap loses orders with no error to catch.
MAX_MARKET_ORDERS_PER_TURN = 10


# ---------------------------------------------------------------------
# Animal husbandry
# ---------------------------------------------------------------------

# Animal husbandry (V1 scope: just GOOSE). It's the cheapest animal ($300),
# has the fastest payback (first_yield_day=4), and produces every day
# (interval=1) - the fastest way to prove the whole build -> buy -> pickup
# -> place -> feed -> care -> harvest -> sell pipeline actually works before
# committing to COW/SHEEP. The logic below is written generically against
# this list, so extending it later is a config change, not new logic - see
# choose_animal_to_build for the priority order multiple species use.
ACTIVE_ANIMALS = ["GOOSE"]
ANIMAL_STRUCTURE_KINDS = {ANIMALS[a]["structure"] for a in ACTIVE_ANIMALS if a in ANIMALS}

# Cap on total animals we'll commit to (built structures, filled or not).
#
# Stays at 1. Three Geese were measured at +14% self-play on the pre-fertilizer,
# pre-day-19 agent (PR #10) and that measurement was correct for the agent it
# was taken on - but the agent moved underneath it. Re-measured on current
# main, with the fertilizer errand competing for the same unit-turns, three
# animals lose **-9,787 head to head, winning 0 of 16 matches**, and self-play
# is flat (27,983 against 28,206).
#
# Note the two harnesses disagreeing again, in the direction that matters:
# self-play changes BOTH sides, so a revenue stream that doesn't compete for
# a scarce market lifts both banks and looks free. Head to head is what shows
# the cost, and the cost is real - every coop takes a tile out of crop
# production and a share of the crew's upkeep capacity, which is the same
# ceiling BUY_LAND and a denser crew both ran into.
#
# The choose_animal_to_build() gate below is kept even though it cannot fire
# at MAX_ANIMALS = 1 (measured: gate-only is +0 against main, an exact no-op).
# It is correct, it costs nothing, and it is the thing that makes raising this
# number safe to try again.
MAX_ANIMALS = 1

# Never buy an animal that eats more than this fraction of current cash in
# one shot - same reasoning as SEED_SPEND_CAP_FRACTION.
ANIMAL_SPEND_CAP_FRACTION = 0.5

# Keep at least this much WHEAT on hand (shed + carried) whenever we own a
# placed animal, buying more via BUY_PRODUCT if it ever hits zero. A missed
# feeding is not a recoverable loss like a weed (DIG reclaims those) - the
# animal escapes for good - so feed supply can't be left to chance on
# however wheat farming happens to be going that day.
MIN_WHEAT_RESERVE_FOR_FEEDING = 2

# Feeding spends wheat from the acting unit's own inventory, not the shed,
# so every meal otherwise costs a fresh shed round-trip. Carry a few days'
# worth per trip instead.
WHEAT_CARRY_BATCH = 3


# ---------------------------------------------------------------------
# Observation readers
#
# These small helpers pull pieces out of the observation defensively
# (using .get() and length checks) so a missing key, a None tile, or an
# unexpected shape never crashes the agent - it just falls back to "no
# information available" and lets the higher-level logic PASS safely.
# ---------------------------------------------------------------------

def get_player_farm(obs):
    """Return our own player's farm dict, or None if it can't be found."""
    farms = obs.get("farms")
    player = obs.get("player")
    if not isinstance(farms, list) or not isinstance(player, int):
        return None
    if player < 0 or player >= len(farms):
        return None
    return farms[player]


def get_tile_at(farm, x, y):
    """
    Return the tile dict/None/"LOCKED" at (x, y), or None if that's off the
    board. Note tiles are row-major - tiles[y][x] - while unit positions are
    [x, y]; mixing the two up is the classic silent bug in this game.
    """
    tiles = farm.get("tiles") if farm else None
    if not tiles or y < 0 or y >= len(tiles):
        return None
    row = tiles[y]
    if x < 0 or x >= len(row):
        return None
    return row[x]


def get_current_tile(farm):
    """Return the tile dict/None/"LOCKED" the farmer is currently standing on."""
    farmer_pos = farm.get("farmer") if farm else None
    if not farmer_pos or len(farmer_pos) != 2:
        return None
    return get_tile_at(farm, farmer_pos[0], farmer_pos[1])


def shed_access_tiles(board_size):
    """
    The four inner-corner tiles adjacent to the shed, matching the engine's
    own placement rule (kaggriculture.py: _shed_access_tiles /
    _is_shed_adjacent) - not exposed directly on `obs`, so we replicate the
    formula rather than guess at it.
    """
    half = board_size // 2
    return [(half - 1, half - 1), (half, half - 1), (half - 1, half), (half, half)]


def is_shed_adjacent(x, y, board_size):
    return (x, y) in shed_access_tiles(board_size)


def wants_fertilizer(tile, day):
    """
    True if fertilising this plant right now would actually pay.

    Only ongoing crops qualify (see FERTILIZABLE_CROPS), and only inside the
    stretch where the three-day cover still catches production ticks.
    Fertilizer applied outside that window is thrown away.

    The window edges come straight out of `_daily_refresh_plants`, which
    computes `days_since_first = (day + 1) - planted_day - first_yield_day`
    and produces while that is a non-negative multiple of `interval` with
    `days_since_first // interval + 1 <= max_yield`. Rewriting in terms of
    the age this function has (`age = day - planted_day`) puts the final
    tick at `first_yield_day - 1 + interval * (max_yield - 1)`.

    That `- 1` matters: without it the agent buys and applies a unit a day
    after the last tick it could possibly pay for.
    """
    if not (isinstance(tile, dict) and tile.get("kind") == "PLANT"):
        return False

    crop = tile.get("crop")
    if crop not in FERTILIZABLE_CROPS:
        return False

    if tile.get("fertilized_until_day", -1) >= day:
        return False  # already covered today

    crop_info = CROPS.get(crop) or {}
    first_yield_day = crop_info.get("first_yield_day")
    if first_yield_day is None:
        return False

    interval = crop_info.get("interval") or 1
    max_yield = crop_info.get("max_yield") or 1
    last_tick_age = first_yield_day - 1 + interval * (max_yield - 1)

    age = day - tile.get("planted_day", day)
    # Cover starts today and runs two more days, so applying just ahead of
    # the first tick still catches it.
    return (first_yield_day - 3) <= age <= last_tick_age


def find_fertilizer_target(farm, board_size, ux, uy, day, exclude=None):
    """Nearest plant worth fertilising, or None."""
    exclude = exclude or set()
    tiles = farm.get("tiles") or []

    best_target = None
    best_distance = None
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
    """Closest of the four shed-access tiles to (fx, fy)."""
    tiles = shed_access_tiles(board_size)
    return min(tiles, key=lambda t: abs(t[0] - fx) + abs(t[1] - fy))


def get_market_state(obs):
    """Return {"prices": {...}, "inventory": {...}}, defaulting to empty dicts."""
    market = obs.get("market") or {}
    return {
        "prices": market.get("prices") or {},
        "inventory": market.get("inventory") or {},
    }


def extract_state(obs):
    """
    Pull everything the rest of the agent needs out of the raw
    observation, once, defensively. Downstream functions work off this
    tidy "state" dict instead of poking at obs directly everywhere.
    """
    obs = obs or {}
    farm = get_player_farm(obs)
    private = obs.get("private") or {}
    tiles = farm.get("tiles") if farm else None

    return {
        "farm": farm,
        "private": private,
        "market_state": get_market_state(obs),
        "board_size": len(tiles) if tiles else 0,
        "day": obs.get("day", 0),
        "hour": obs.get("hour", 0),
    }


# ---------------------------------------------------------------------
# Movement
# ---------------------------------------------------------------------

def step_toward(fx, fy, tx, ty):
    """
    Return a single direction ("NORTH"/"SOUTH"/"EAST"/"WEST") that moves
    one step closer to (tx, ty), or None if we're already there.

    This is simple Manhattan-distance movement, not real pathfinding -
    good enough for V1 since the board has no obstacles the farmer can't
    just walk around a tile at a time.
    """
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
    """
    True if a PLANT tile is actually ready to pick right now.

    yield_units > 0 alone is NOT enough: a freshly planted non-ongoing crop
    (WHEAT/CARROT/MELON) starts with yield_units=1 the instant it's
    planted - a placeholder for its eventual payout, not a "ready now"
    signal. The environment separately gates HARVEST on
    `day - planted_day >= first_yield_day` and silently no-ops otherwise.
    Without checking that gate too, we'd repeatedly attempt (and fail) to
    harvest a still-growing crop every turn - and because that check runs
    before watering in the priority order, the crop never gets watered and
    dies before it ever matures.
    """
    if tile.get("yield_units", 0) <= 0:
        return False
    crop_info = CROPS.get(tile.get("crop"))
    if not crop_info:
        return False
    first_yield_day = crop_info.get("first_yield_day", 0)
    return day - tile.get("planted_day", day) >= first_yield_day


def remaining_season_days(day):
    """Days left, inclusive of today, before the season's last day (29)."""
    return (SEASON_DAYS - 1) - day


def has_plantable_seed(seeds, day):
    """
    True if at least one held seed belongs to a crop that could still
    reach first_yield_day before the season ends.

    Without this check, "any" targeting below would send the farmer
    walking toward an empty tile on the strength of a seed it can never
    usefully plant (choose_crop() would just refuse it again on arrival,
    per the same season-maturity gate) - not a money loss, but a wasted
    turn wandering toward a tile with nothing useful to do there.
    """
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
    """
    Scan the whole farm grid and return the (x, y) of the closest tile
    matching `task`, or None if there isn't one.

    `exclude` is a set of (x, y) tiles another unit has already claimed
    this turn. Without it, every hand would pick the same nearest target
    and they'd all walk to one tile while the rest of the farm rotted.

    task options:
      "harvest"        - a plant or animal tile that's ready to pick right
                          now.
      "water_urgent"   - a plant tile that already missed a watering and
                          will turn into a weed if it's missed again today.
      "feed"    - an animal tile that already missed a feeding and
                          will escape for good if it's missed again today.
      "weed"           - a dead tile that can be dug back into plantable
                          ground.
      "empty_structure" - a built COOP/PASTURE with no animal in it yet.
      "any"            - anything at all worth walking to: a ripe plant,
                          an unwatered plant, or (if we're holding at
                          least one seed that can still mature) an empty
                          tile we could plant.
    """
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

            elif (
                isinstance(tile, dict)
                and tile.get("kind") in ANIMAL_STRUCTURE_KINDS
                and "animal" not in tile
                and task == "empty_structure"
            ):
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
    """Pick whichever of two (possibly-None) targets is nearer to (fx, fy)."""
    if target_a is None:
        return target_b
    if target_b is None:
        return target_a

    dist_a = abs(target_a[0] - fx) + abs(target_a[1] - fy)
    dist_b = abs(target_b[0] - fx) + abs(target_b[1] - fy)
    return target_a if dist_a <= dist_b else target_b


# ---------------------------------------------------------------------
# Animals
# ---------------------------------------------------------------------

def unit_inventory(private, unit_idx):
    """
    The specific unit's own carried inventory (private["inventories"][idx],
    idx 0 = main farmer, idx i = the (i-1)th hand - matching the engine's
    own indexing). What a unit is carrying, not what's in the shed, is what
    FEED/PLACE actually consume.
    """
    inventories = private.get("inventories") or []
    if 0 <= unit_idx < len(inventories) and isinstance(inventories[unit_idx], dict):
        return inventories[unit_idx]
    return {}


def carried_animal(inv):
    """Which ACTIVE_ANIMALS item (if any) this unit is currently carrying."""
    for animal in ACTIVE_ANIMALS:
        if inv.get(animal, 0) > 0:
            return animal
    return None


def scan_animal_structures(farm, board_size):
    """
    One pass over the board counting ACTIVE_ANIMALS structures, split into
    filled (has an animal) and unfilled (built, waiting for one). A single
    scan avoids walking the whole grid separately for every related
    decision (build gating, buy gating).
    """
    tiles = farm.get("tiles") or []
    filled = 0
    unfilled = 0
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
    """
    Total ACTIVE_ANIMALS we've committed to: bought-but-uncollected (shed),
    carried by any unit, and already placed on the board. Used to gate
    buying - without counting the in-transit ones we'd keep overbuying past
    the cap while one is still being carried to its coop.
    """
    shed = private.get("shed", {})
    total = sum(shed.get(a, 0) for a in ACTIVE_ANIMALS)
    for inv in private.get("inventories") or []:
        if isinstance(inv, dict):
            total += sum(inv.get(a, 0) for a in ACTIVE_ANIMALS)
    filled, unfilled = scan_animal_structures(farm, board_size)
    return total + filled + unfilled


def choose_animal_to_build(farm, board_size, day, pending_builds=0):
    """
    Pick which ACTIVE_ANIMALS species to build a structure for next, or
    None if we shouldn't build one right now.

    Same season-maturity gate choose_crop() uses for seeds: a species
    whose first_yield_day can't land before day 29 is refused, the same
    way a too-slow crop is - building for it would tie up a tile and
    ANIMAL_SPEND_CAP_FRACTION of our cash for a guaranteed dead loss with
    no offsetting revenue. This gate matters as MAX_ANIMALS or
    ACTIVE_ANIMALS grows enough that a build could land late in the season.

    Also picks *which* species: the first one (in ACTIVE_ANIMALS order)
    that's both affordable and has time left to pay off, rather than
    always building whatever ACTIVE_ANIMALS[0] happens to be regardless of
    season or affordability - matters once more than one species is
    active, since the structure kind for the wrong species is a wasted
    build.

    Under the cap, and only when every structure we've already built
    already has an animal in it (stops us tying up more than one tile at a
    time waiting on the buy/pickup/place chain to catch up) - same
    affordability bar as actually buying the animal (see
    decide_animal_market_actions), so we never build ahead of our ability
    to fill it.

    `pending_builds` is how many other units have already decided to build
    one THIS SAME TURN (see choose_unit_action) - every unit sees the same
    pre-turn board, so without this a farmer plus several hands can each
    independently see "no coop built yet" and all build one in the same
    turn, blowing straight through the cap in one shot.
    """
    filled, unfilled = scan_animal_structures(farm, board_size)
    if unfilled > 0 or pending_builds > 0 or filled >= MAX_ANIMALS:
        return None

    money = farm.get("money", 0)
    remaining_days = remaining_season_days(day)
    for animal in ACTIVE_ANIMALS:
        info = ANIMALS.get(animal)
        if not info:
            continue
        cost = info.get("cost")
        first_yield_day = info.get("first_yield_day")
        if cost is None or first_yield_day is None:
            continue
        if first_yield_day > remaining_days:
            continue  # can't reach even a first harvest before season end
        if money >= cost and cost <= money * ANIMAL_SPEND_CAP_FRACTION:
            return animal
    return None


def decide_animal_market_actions(farm, private, board_size, day):
    """
    Build the list of BUY_ANIMAL / feed-safety-net BUY_PRODUCT orders for
    this turn.
    """
    actions = []
    money = farm.get("money", 0)
    remaining_days = remaining_season_days(day)

    if count_owned_animals(farm, private, board_size) < MAX_ANIMALS:
        for animal in ACTIVE_ANIMALS:
            info = ANIMALS.get(animal)
            cost = info.get("cost") if info else None
            first_yield_day = info.get("first_yield_day") if info else None
            if cost is None or first_yield_day is None:
                continue
            if first_yield_day > remaining_days:
                continue  # can't reach even a first harvest before season end
            if cost > money or cost > money * ANIMAL_SPEND_CAP_FRACTION:
                continue
            actions.append(["BUY_ANIMAL", animal, 1])
            break  # one purchase at a time, same cadence as seed buying

    filled, _ = scan_animal_structures(farm, board_size)
    if filled > 0 and money > 0:
        shed_wheat = private.get("shed", {}).get("WHEAT", 0)
        carried_wheat = sum(
            inv.get("WHEAT", 0) for inv in (private.get("inventories") or []) if isinstance(inv, dict)
        )
        if shed_wheat + carried_wheat < MIN_WHEAT_RESERVE_FOR_FEEDING:
            actions.append(["BUY_PRODUCT", "WHEAT", 1])

    return actions


# ---------------------------------------------------------------------
# Labour
# ---------------------------------------------------------------------

def count_pending_work(farm, board_size, day, seeds=None):
    """
    How many tiles currently need a unit standing on them: a ripe crop to
    pick, a thirsty crop to water, a weed to dig, or plantable ground we
    hold a usable seed for.

    This is the demand side of the hiring decision - hire against real
    work, not against a fixed schedule.
    """
    seeds = seeds or {}
    tiles = farm.get("tiles") or []
    have_any_seed = has_plantable_seed(seeds, day)

    work = 0
    for y in range(board_size):
        row = tiles[y] if y < len(tiles) else []
        for x in range(len(row)):
            tile = row[x]
            if isinstance(tile, dict):
                kind = tile.get("kind")
                if kind == "PLANT":
                    if is_harvestable(tile, day) or not tile.get("watered_today", True):
                        work += 1
                elif kind == "WEED":
                    work += 1
            elif tile is None and have_any_seed:
                work += 1
    return work


def decide_hire_orders(farm, board_size, day, hour, seeds=None):
    """
    Decide how many farm hands to hire this turn, as ["HIRE"] market orders.

    Hands vanish at the end of every day, so this only fires in the first
    few turns of a day: same price, far more work out of them. The count is
    driven by how much work is actually waiting, capped by MAX_HANDS_PER_DAY
    because the cost sequence is Fibonacci within a day.
    """
    if hour >= HIRE_BEFORE_HOUR:
        return []
    if remaining_season_days(day) < 0:
        return []
    if farm.get("money", 0) < MIN_MONEY_TO_HIRE:
        return []

    work = count_pending_work(farm, board_size, day, seeds)
    wanted = min(MAX_HANDS_PER_DAY, work // WORK_TILES_PER_HAND)
    already_working = len(farm.get("hands") or [])
    shortfall = max(0, wanted - already_working)

    return [["HIRE"]] * min(shortfall, MAX_HIRES_PER_TURN)


# ---------------------------------------------------------------------
# Crop selection
# ---------------------------------------------------------------------

def count_pipeline_supply(farm, private):
    """
    Units of each crop we are already committed to selling: everything
    growing on our own tiles, plus whatever is already in the shed.

    This is the supply that will hit the market *because of us*, and it is
    the number the planting decision has to respect. Spot price says what a
    unit fetches today; it says nothing about what it will fetch after our
    own harvest lands.
    """
    supply = {}

    for product, quantity in (private.get("shed") or {}).items():
        if quantity:
            supply[product] = supply.get(product, 0) + quantity

    for row in (farm.get("tiles") or []):
        for tile in row:
            if isinstance(tile, dict) and tile.get("kind") == "PLANT":
                crop = tile.get("crop")
                crop_info = CROPS.get(crop) or {}
                supply[crop] = supply.get(crop, 0) + (crop_info.get("max_yield") or 1)

    return supply


def choose_crop(farm, market_state, private, day):
    """
    Pick the crop we'd most like to plant next, or None if nothing makes
    sense right now (nothing affordable/held, or nothing left has time to
    mature).

    Deliberately simple scoring - no profit projection or lookahead:

        score = price * yield * glut_discount * self_supply_discount
                / growth_days

      - price * expected_yield: rough revenue if we sell everything the
        plant produces at today's price.
      - glut_discount: how oversupplied this product already is, measured
        *relative* to the market's baseline stock. It must be relative:
        every product starts at an inventory of 10,000, so an absolute
        `stock * price` penalty term is not a tie breaker, it is the whole
        score - and it ranks crops by cheapness, which is how an earlier
        version planted wheat all season and never once planted a melon.
      - self_supply_discount: what we have already committed to selling,
        growing on our own tiles plus sitting in the shed, weighted by how
        much punishment that particular market takes. Spot price says what
        a unit fetches today; a melon planted now sells twelve days from
        now, after our own harvest has landed.
      - growth_days: how long we have to wait for the payoff, so we
        don't favor a slow crop just because its total payout is bigger.

    A crop is only considered if we already hold a seed for it, or we
    can afford to buy one - AND it can reach first_yield_day before the
    season's last day (29). Diagnosed from a real lost game: without this
    check, the agent kept planting TOMATO (first_yield_day=8) as late as
    day 29, spending seed money on plants that mathematically could never
    produce a single unit - a guaranteed loss with no offsetting revenue.
    """
    money = farm.get("money", 0)
    prices = market_state.get("prices", {})
    inventory = market_state.get("inventory", {})
    seeds = private.get("seeds", {})
    remaining_days = remaining_season_days(day)
    pipeline = count_pipeline_supply(farm, private)

    best_crop = None
    best_score = None

    for crop in PLANTABLE_CROPS:
        crop_info = CROPS.get(crop)
        if not crop_info:
            continue  # unknown crop metadata - skip rather than guess

        seed_cost = crop_info.get("seed")
        expected_yield = crop_info.get("max_yield")
        growth_days = crop_info.get("max_yield_day")
        first_yield_day = crop_info.get("first_yield_day")
        if seed_cost is None or expected_yield is None or not growth_days:
            continue
        if first_yield_day is not None and first_yield_day > remaining_days:
            continue  # can't reach even a first harvest before season end

        have_seed = seeds.get(crop, 0) > 0
        can_afford = money >= seed_cost
        if not have_seed and not can_afford:
            continue  # can't get hold of this crop right now

        price = prices.get(crop, 0)
        stock = inventory.get(crop, 0)

        # Glut discount, measured *relative* to the market's baseline stock
        # rather than as a raw unit count. Every product starts at an
        # inventory of 10,000, so an absolute penalty term is not a tie
        # breaker - it is the whole score. The previous form,
        # (price*yield - stock*price)/days, collapsed to about
        # -price*10000/days, which ranks crops by cheapness: it planted
        # WHEAT (37.5 value per tile-day) and scored MELON (125.0, the best
        # crop in the game by 2.6x) dead last, so melon was never planted.
        #
        # The quoted price already encodes supply - the engine derives it
        # from inventory - so this only needs to discount a genuine glut,
        # and never to outweigh revenue.
        baseline = MARKET_BASELINE_STOCK.get(crop) or DEFAULT_BASELINE_STOCK
        glut = max(0.0, stock / baseline - 1.0) if baseline else 0.0
        glut_discount = max(1.0 - glut, MIN_GLUT_DISCOUNT)

        # Our own incoming supply. Spot price is what a unit fetches today,
        # but a melon planted now sells 12 days from now - after our own
        # harvest has hit the market. Measured: growing melon on most tiles
        # drives the melon price from $250 to about $4 by season end with no
        # opponent involved at all, so the back half of every harvest sells
        # for nearly nothing.
        #
        # Weight that pressure by how much punishment the specific market
        # takes: at T units above baseline WHEAT still fetches $20 of $25,
        # while MELON goes to $1. So this pushes volume toward crops that
        # absorb it and keeps the fragile, high-value ones scarce enough to
        # stay valuable.
        absorption = MARKET_ABSORPTION.get(crop) or DEFAULT_ABSORPTION
        pressure = pipeline.get(crop, 0) / absorption if absorption else 0.0
        self_supply_discount = 1.0 / (1.0 + pressure) ** SELF_SUPPLY_EXPONENT

        score = price * expected_yield * glut_discount * self_supply_discount / growth_days

        if best_score is None or score > best_score:
            best_score = score
            best_crop = crop

    return best_crop


# ---------------------------------------------------------------------
# Market decisions
# ---------------------------------------------------------------------

def should_sell(product, quantity, market_state):
    """
    True if we should sell `quantity` units of `product` right now.

    Kept deliberately simple and easy to tune: sell only when the
    current price clears a fixed per-product threshold. We do NOT sell
    everything blindly just because we have it - a poor price means we
    hold and wait.
    """
    if quantity <= 0:
        return False

    price = market_state.get("prices", {}).get(product, 0)
    threshold = SELL_PRICE_THRESHOLDS.get(product, DEFAULT_SELL_THRESHOLD)
    return price >= threshold


def should_buy_seed(crop, farm, private):
    """
    True if it's sensible to buy one more seed of `crop` right now:
    we're not already stockpiling it, we can afford it, and it won't
    eat an unreasonable chunk of our cash.
    """
    seeds = private.get("seeds", {})
    if seeds.get(crop, 0) >= MAX_SEED_STOCKPILE:
        return False

    crop_info = CROPS.get(crop)
    if not crop_info:
        return False
    seed_cost = crop_info.get("seed")
    if seed_cost is None:
        return False

    money = farm.get("money", 0)
    if seed_cost > money:
        return False
    if seed_cost > money * SEED_SPEND_CAP_FRACTION:
        return False  # would eat too much of our cash reserve

    return True


def decide_market_actions(farm, private, market_state, day, reserved_wheat=0):
    """Build the list of ["SELL", ...] / ["BUY_SEED", ...] actions for this turn."""
    actions = []
    already_selling = set()

    # Sell anything sitting in the shed that's fetching a good price. Capped
    # per product (see MAX_SELL_PER_TURN) so a big harvest of a premium good
    # doesn't dump the whole stack into one price-crashing order.
    shed = private.get("shed", {})
    liquidating = day >= LIQUIDATION_START_DAY

    for product, quantity in shed.items():
        # Fertilizer is an input, not produce - and with a Goose on the farm
        # it arrives free via COLLECT_FERTILIZER. Its price clears the default
        # sell threshold comfortably, so without this guard the agent dumps
        # every unit the animal makes (and buys more, then sells those too:
        # 715 units round-tripped in one measured season with zero reaching a
        # plant). Hold it for the crops and only liquidate at season end,
        # when leftover stock scores nothing anyway.
        if product == "FERTILIZER" and not liquidating:
            continue

        # Hold back the wheat earmarked for feeding. Wheat is animal feed,
        # and an animal that misses two consecutive days escapes for good -
        # so selling the feed can permanently destroy a 300-cost asset for
        # a few dollars of wheat. The reserve is kept even while
        # liquidating: the animal still produces right up to the last day.
        sell_quantity = quantity
        if product == "WHEAT":
            sell_quantity = max(0, quantity - reserved_wheat)

        # Near the end of the season, price thresholds stop mattering:
        # unsold stock scores nothing, so any sale beats holding out.
        if sell_quantity > 0 and (
            liquidating or should_sell(product, sell_quantity, market_state)
        ):
            cap = MAX_SELL_PER_TURN.get(product, quantity)
            actions.append(["SELL", product, min(sell_quantity, cap)])
            already_selling.add(product)

    # Shed is nearly full: anything not already being sold above would just
    # be discarded once the cap hits. Force a sale (still capped, so we
    # don't crash a premium good's price on the way out) rather than let it
    # evaporate for free.
    shed_total = sum(shed.values())
    if shed_total >= SHED_FORCE_SELL_THRESHOLD:
        for product, quantity in shed.items():
            # Same exclusion as the main sell loop - the overflow valve
            # must not become the back door that dumps the fertilizer.
            # Fertilizer is an input, not produce - and with a Goose on the farm
            # it arrives free via COLLECT_FERTILIZER. Its price clears the default
            # sell threshold comfortably, so without this guard the agent dumps
            # every unit the animal makes (and buys more, then sells those too:
            # 715 units round-tripped in one measured season with zero reaching a
            # plant). Hold it for the crops and only liquidate at season end,
            # when leftover stock scores nothing anyway.
            if product == "FERTILIZER" and not liquidating:
                continue

            if product in already_selling or quantity <= 0:
                continue
            sell_quantity = quantity
            if product == "WHEAT":
                sell_quantity = max(0, quantity - reserved_wheat)
            if sell_quantity <= 0:
                continue
            cap = MAX_SELL_PER_TURN.get(product, quantity)
            actions.append(["SELL", product, min(sell_quantity, cap)])

    # Buy exactly one seed of our preferred next crop, if it makes sense.
    preferred_crop = choose_crop(farm, market_state, private, day)
    if preferred_crop and should_buy_seed(preferred_crop, farm, private):
        actions.append(["BUY_SEED", preferred_crop, 1])

    # Fertilizer, but only against ongoing crops we actually have in the
    # ground - it's the one product a unit has to fetch from the shed by
    # hand, so buying speculatively wastes both money and turns. A Goose
    # supplies it free, so in practice this only tops up when the crops
    # want more than the animal produced.
    #
    # Leave this rule alone in BOTH directions - it has been pushed each way
    # and both lost.
    #
    # It looks like churn: from LIQUIDATION_START_DAY the sell loop stops
    # exempting FERTILIZER, so we buy and sell the same product on the same
    # day (111 bought, 137 sold in one measured season). Blocking the buy
    # during liquidation lost -529 head to head, winning 1 of 16 matches.
    #
    # It also looks like arbitrage, and it is not. Buy and sell both average
    # $97.0; the round trip on those 111 units nets -$4. The apparent profit
    # is the 26 units the Goose produced free. Fertilizer is linear both ways
    # with target 0.40, so price = 100 - 0.2 x excess and every unit we trade
    # moves the price $0.20 against us, while sell price is quoted pre-sell
    # and buy price post-buy - a same-day round trip pays and receives the
    # same number by construction. Trading it deliberately (buy <=97 in
    # batches, release >=99) bought 573 units at 97.8 and sold 591 at 97.0,
    # losing -1,486 head to head, winning 0 of 16.
    #
    # See CLAUDE.md, "There is no fertilizer arbitrage".
    if day <= FERTILIZER_LAST_USEFUL_DAY:
        held = shed.get("FERTILIZER", 0) + sum(
            (carried or {}).get("FERTILIZER", 0)
            for carried in (private.get("inventories") or [])
            if isinstance(carried, dict)
        )
        if held < MAX_FERTILIZER_STOCK:
            fertilizer_price = market_state.get("prices", {}).get("FERTILIZER", 0)
            wanted = sum(
                1
                for row in (farm.get("tiles") or [])
                for tile in row
                if wants_fertilizer(tile, day)
            )
            if wanted > held and fertilizer_price and farm.get("money", 0) >= fertilizer_price * 2:
                actions.append(["BUY_PRODUCT", "FERTILIZER", 1])

    return actions


# ---------------------------------------------------------------------
# Farmer decision
# ---------------------------------------------------------------------

def choose_unit_action(
    state, ux, uy, unit_idx, claimed=None, pending_builds=None, feed_claimed=None
):
    """
    Decide the single action for one unit - the main farmer or a hired
    hand - standing at (ux, uy), following the fixed priority order
    described at the top of this file.

    `unit_idx` is this unit's index into private["inventories"] (0 = main
    farmer, i = the (i-1)th hand), needed to know what it's personally
    carrying - FEED and PLACE consume from that, not the shed.

    `claimed` is the set of (x, y) tiles other units have already taken
    this turn, and whatever this unit settles on is added to it. Without
    that bookkeeping every hand would independently pick the same nearest
    target and the whole crew would walk to one tile while the rest of
    the farm went to weeds - which defeats the point of hiring them.

    `pending_builds` is a shared one-item counter ([n]) of how many
    structures other units have already decided to build this same turn.
    Every unit sees the same pre-turn board, so without this a farmer plus
    several hands could each independently see "no coop built yet" and all
    build one in the same turn, blowing straight through MAX_ANIMALS.
    """
    claimed = claimed if claimed is not None else set()
    pending_builds = pending_builds if pending_builds is not None else [0]
    feed_claimed = feed_claimed if feed_claimed is not None else set()

    farm = state["farm"]
    if not farm:
        return ["PASS"]

    board_size = state["board_size"]
    day = state["day"]
    private = state["private"]
    seeds = private.get("seeds", {})
    inv = unit_inventory(private, unit_idx)
    tile = get_tile_at(farm, ux, uy)

    # Another unit already acted on this tile this turn. Every tile action is
    # either once-per-day (WATER, CARE, FEED) or consumes its target outright
    # (HARVEST, DIG, PLANT, COLLECT_FERTILIZER), so a second unit acting here
    # spends its whole turn on an engine no-op. Units decide from a shared
    # observation snapshot, so without this they all see `cared_today: False`
    # and all pick CARE - measured at 76 CARE actions across only 30 distinct
    # days, i.e. 46 turns burned, with multiple units caring for the same
    # goose on 30 separate turns.
    #
    # Standing in for the tile with a sentinel makes the whole local-action
    # ladder below fall through (it is all `isinstance(tile, dict)` and
    # `tile is None` checks), so the unit goes and finds real work instead.
    if (ux, uy) in claimed:
        tile = "TAKEN"

    is_animal_tile = isinstance(tile, dict) and "animal" in tile

    def act_here(action):
        """Take an action on our own tile, and reserve it against other units."""
        claimed.add((ux, uy))
        return action

    def walk_to(target):
        """Step toward a target and reserve it, so no one else heads there."""
        direction = step_toward(ux, uy, target[0], target[1])
        if not direction:
            return None
        claimed.add((target[0], target[1]))
        return [direction]

    # 1. Feed an animal before any harvest/care task. A Goose with
    # consecutive_unfed == 1 can escape at the next day boundary, so this
    # safety action must outrank even a ready harvest.
    if is_animal_tile and not tile.get("fed_today"):
        if inv.get("WHEAT", 0) > 0:
            feed_claimed.add((ux, uy))
            return act_here(["FEED"])

    # 2. Harvest a ripe crop or an animal whose held yield is close to its
    # capacity. Animal goods do not decay, so do not spend one action
    # harvesting a single Egg every day.
    if isinstance(tile, dict) and tile.get("kind") == "PLANT" and is_harvestable(tile, day):
        return act_here(["HARVEST"])
    if is_animal_tile:
        animal = ANIMALS.get(tile.get("animal"), {})
        max_held = animal.get("max_held", 1)
        held = tile.get("yield_units", 0)
        if held >= max_held:
            return act_here(["HARVEST"])

        # Fertilizer is a separate non-stacking daily output. Collect it
        # before care/harvest whenever the animal has room for another yield.
        if tile.get("fertilizer_available"):
            return act_here(["COLLECT_FERTILIZER"])

        # Leave enough room for the next Goose production, but cash out near
        # season end so output cannot be stranded on the tile.
        if held > 0 and (held >= max_held - 2 or day >= SEASON_DAYS - 2):
            return act_here(["HARVEST"])

    # 3. Water a crop under our feet, or care for an already-fed animal under
    #    feet. Feed always wins over care when only one action is possible:
    #    a missed feeding is a permanent loss (the animal escapes for good
    #    - see _daily_refresh_animals), care is just a bonus multiplier.
    if isinstance(tile, dict) and tile.get("kind") == "PLANT" and not tile.get("watered_today", True):
        return act_here(["WATER"])
    if is_animal_tile:
        if not tile.get("cared_today"):
            return act_here(["CARE"])

    # 3b. Fertilise the ongoing crop under our feet, if we're carrying any.
    #     Free in movement terms - we are already standing here - and worth
    #     several hundred on a tomato or strawberry. Ranked below watering
    #     because the bonus only pays on days the plant is watered anyway,
    #     so watering first is strictly better when we can only do one.
    if inv.get("FERTILIZER", 0) > 0 and wants_fertilizer(tile, day):
        return act_here(["FERTILIZE"])

    # 4. Place a carried animal on the empty structure under our feet.
    animal_in_hand = carried_animal(inv)
    if animal_in_hand and isinstance(tile, dict) and "animal" not in tile:
        structure = ANIMALS.get(animal_in_hand, {}).get("structure")
        if structure and tile.get("kind") == structure:
            return act_here(["PLACE", animal_in_hand])

    # 5. Shed errands: collect a bought animal waiting for its home, or
    #    wheat we need to go feed a starving animal elsewhere.
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
                # Collect several days of feed in one trip. Feeding needs
                # wheat in the acting unit's own inventory, so picking up a
                # single grain means a fresh shed round-trip for every meal.
                return act_here(
                    ["PICKUP", "WHEAT", min(shed.get("WHEAT", 0), WHEAT_CARRY_BATCH)]
                )

    # 6. Something urgent elsewhere - a ripe crop/animal, a crop about to
    #    weed out, or an animal about to escape - beats anything below.
    #    Preventing a loss is worth more than reclaiming one already lost.
    #    If the winning target needs feeding and we're not carrying wheat,
    #    detour to the shed instead of arriving empty-handed (only if the
    #    shed actually has wheat - otherwise there's nothing to do about it
    #    this turn).
    # Feed is a daily errand, not a rescue. An earlier version only walked to
    # an animal that had ALREADY missed a day, which self-oscillates: feeding
    # resets consecutive_unfed, so the next day never looks urgent and the
    # animal is fed every OTHER day - 15 meals in a 30-day season, measured.
    # That left the Goose permanently one blocked turn from escaping for good,
    # and threw away most of the CARE bank, which only accrues on days the
    # animal was also fed and is discarded unpaid if its production day is not
    # (see _daily_refresh_animals in the engine).
    #
    # Feed is also a separate reservation class. A crop worker without Wheat
    # must not claim the Goose tile for HARVEST/WATER movement before a
    # different unit carrying Wheat has a chance to reach it.
    feed_target = find_nearest_target(farm, board_size, ux, uy, "feed", day, exclude=set())
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

    # 7. Carrying an animal we haven't placed yet - go find it a home.
    if animal_in_hand:
        structure_target = find_nearest_target(
            farm, board_size, ux, uy, "empty_structure", day, exclude=claimed
        )
        if structure_target:
            moved = walk_to(structure_target)
            if moved:
                return moved

    # 8. Reclaim a weed under our feet - free, and turns dead land back into
    #    something we can plant again instead of losing it for the rest of
    #    the season.
    if isinstance(tile, dict) and tile.get("kind") == "WEED":
        return act_here(["DIG"])

    # 9. Empty ground under our feet: build a coop/pasture if we're still
    #    growing the animal side of the farm and don't already have one
    #    waiting for a tenant, otherwise plant a crop.
    if tile is None:
        animal_to_build = choose_animal_to_build(farm, board_size, day, pending_builds[0])
        if animal_to_build:
            pending_builds[0] += 1
            structure = ANIMALS[animal_to_build]["structure"]
            return act_here([f"BUILD_{structure}"])
        crop = choose_crop(farm, state["market_state"], private, day)
        if crop and seeds.get(crop, 0) > 0:
            return act_here(["PLANT", crop])

    # 10. Fertilizer logistics. Fertilizer reaches the shed either by
    #     purchase or free from the Goose, but FERTILIZE spends from the
    #     unit's own inventory - so this is a collect-then-deliver errand.
    #     Deliberately ranked below every crop-upkeep step above: a plant
    #     that dies unwatered costs far more than a fertilizer bonus is
    #     worth, and the bonus only pays on watered days regardless.
    shed_fertilizer = (private.get("shed") or {}).get("FERTILIZER", 0)

    if inv.get("FERTILIZER", 0) > 0:
        fertilize_target = find_fertilizer_target(
            farm, board_size, ux, uy, day, exclude=claimed
        )
        if fertilize_target:
            moved = walk_to(fertilize_target)
            if moved:
                return moved

    elif shed_fertilizer > 0 and find_fertilizer_target(
        farm, board_size, ux, uy, day, exclude=claimed
    ):
        # Collect a batch so one trip serves several plants.
        if is_shed_adjacent(ux, uy, board_size):
            return act_here(
                ["PICKUP", "FERTILIZER", min(shed_fertilizer, FERTILIZER_CARRY_BATCH)]
            )
        moved = walk_to(nearest_shed_tile(ux, uy, board_size))
        if moved:
            return moved

    # 11. Reclaim the nearest weed elsewhere - dead land is a permanent loss
    #    until it's dug back to plantable ground, so don't just leave it.
    weed_target = find_nearest_target(
        farm, board_size, ux, uy, "weed", day, exclude=claimed
    )
    if weed_target:
        moved = walk_to(weed_target)
        if moved:
            return moved

    # 12. Nothing to do right here - walk toward the closest useful tile.
    fallback_target = find_nearest_target(
        farm, board_size, ux, uy, "any", day, seeds, exclude=claimed
    )
    if fallback_target and fallback_target != (ux, uy):
        moved = walk_to(fallback_target)
        if moved:
            return moved

    # 13. Genuinely nothing useful to do.
    return ["PASS"]


def choose_farmer_action(state, claimed=None, pending_builds=None, feed_claimed=None):
    """Our main farmer's action - the shared unit logic, anchored at the farmer."""
    farm = state.get("farm")
    if not farm:
        return ["PASS"]

    farmer_pos = farm.get("farmer")
    if not farmer_pos or len(farmer_pos) != 2:
        return ["PASS"]

    return choose_unit_action(
        state, farmer_pos[0], farmer_pos[1], 0, claimed, pending_builds, feed_claimed
    )


# ---------------------------------------------------------------------
# Agent entry point
# ---------------------------------------------------------------------

def nikaangukia_meroni(obs):
    """
    Washamba Bots' V1 agent.

    Always returns a well-formed action dict, even for a missing or
    malformed observation - if anything goes wrong we fall back to a
    safe PASS instead of crashing.
    """
    try:
        state = extract_state(obs)
        farm = state["farm"]
        if not farm:
            return {"farmer": ["PASS"], "hands": [], "market": []}

        board_size = state["board_size"]
        day = state["day"]
        hour = state["hour"]
        private = state["private"]
        seeds = private.get("seeds", {})

        # One shared claim set across every unit this turn, so the farmer and
        # each hand pick different tiles instead of piling onto the same one.
        # pending_builds is the same idea for coop/pasture construction - see
        # choose_unit_action's docstring.
        claimed = set()
        pending_builds = [0]
        feed_claimed = set()
        farmer_action = choose_farmer_action(state, claimed, pending_builds, feed_claimed)
        hands_actions = [
            choose_unit_action(
                state, hand[0], hand[1], idx + 1, claimed, pending_builds, feed_claimed
            )
            for idx, hand in enumerate(farm.get("hands") or [])
            if isinstance(hand, (list, tuple)) and len(hand) == 2
        ]

        # Hires go first: they're a few dollars each and multiply how much
        # work the crew gets through, so they're the last orders we'd want
        # silently dropped if we ever brush the per-turn cap. Animal orders
        # go last - buying one or topping up feed reserve is less
        # time-critical turn-to-turn than hiring or selling at a good price.
        market = decide_hire_orders(farm, board_size, day, hour, seeds)
        filled_animals, _ = scan_animal_structures(farm, board_size)
        reserved_wheat = filled_animals * MIN_WHEAT_RESERVE_FOR_FEEDING
        market += decide_market_actions(
            farm,
            private,
            state["market_state"],
            day,
            reserved_wheat=reserved_wheat,
        )
        market += decide_animal_market_actions(farm, private, board_size, day)

        return {
            "farmer": farmer_action,
            "hands": hands_actions,
            "market": market[:MAX_MARKET_ORDERS_PER_TURN],
        }
    except Exception:
        # Last line of defense: an agent that crashes forfeits the match,
        # so an unexpected observation shape should always fall back to
        # a harmless PASS rather than raising.
        return {"farmer": ["PASS"], "hands": [], "market": []}


# The framework picks the LAST callable in this module's namespace - not a
# function named `agent` (kaggle_environments/agent.py:64). Anything callable
# defined below this line silently becomes the submission instead, the episode
# still reports DONE, every action is discarded as invalid, and the agent
# finishes on exactly its starting money. Keep this binding last.
agent = nikaangukia_meroni
