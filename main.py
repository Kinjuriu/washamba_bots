"""
nikaangukia_meroni_v0
======================

Washamba Bots' first deterministic baseline agent for the Kaggriculture
competition.

This is deliberately NOT a sophisticated AI. It is a simple, readable,
rule-based farmer that:

  1. Harvests ripe crops.
  2. Waters crops that need it.
  3. Moves toward urgent tasks (saving a crop) before anything else.
  4. Digs weeds under its feet for free, reclaiming dead land.
  5. Plants a sensible crop when standing on an empty tile.
  6. Otherwise walks toward the next useful tile (preferring a weed to
     reclaim over aimless wandering).
  7. PASSes if there is genuinely nothing useful to do.

It also does simple, threshold-based market decisions: sell shed goods
when the price is good (capped per turn for premium goods so a big
harvest doesn't crash its own price), buy one seed at a time when we
need one and can afford it.

NOT implemented in this version (on purpose, to keep v0 simple):
  - Animals (COOP / PASTURE tiles), feeding, or collecting animal goods.
  - Hired hands ("hands" is always returned empty).
  - Buying land / unlocking new quadrants.
  - Any multi-turn planning, lookahead, or opponent modelling.

Every piece of environment metadata used here (CROPS, action names, the
observation shape) comes from the official Kaggriculture "Getting
Started" / Hosts notebook. Nothing is invented.
"""

# CROPS is the same environment-provided metadata table used in the
# official starter notebook's "Melon Maxxer" example. It tells us, per
# crop, the seed cost, how many days until it can be harvested, and how
# many units it yields - so we don't have to hard-code any of that
# ourselves.
try:
    from kaggle_environments.envs.kaggriculture.kaggriculture import CROPS
except ImportError:
    # Defensive fallback: if this ever runs somewhere the environment
    # package isn't importable (e.g. a stripped-down test sandbox), we
    # still don't want the whole agent to blow up at import time. With
    # an empty CROPS table the agent simply won't plant anything - it
    # will still harvest/water/sell/PASS safely.
    CROPS = {}

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


# The only crops the environment actually defines seed metadata for.
# (EGG / MILK / WOOL / FERTILIZER are products, not plantable crops -
# they come from animals, which v0 does not handle.)
PLANTABLE_CROPS = ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON"]

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

# Don't stockpile more seeds of one crop than this - keeps cash free for
# other things instead of hoarding.
MAX_SEED_STOCKPILE = 3

# The season is a fixed 30 days (0-indexed: day 0 through day 29), per the
# competition's hard constraints - not something that varies per episode.
SEASON_DAYS = 30

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
LIQUIDATION_START_DAY = 25

# Never spend more than this fraction of our current cash on a single
# seed purchase, so a bad crop pick can't wipe out our bank balance.
SEED_SPEND_CAP_FRACTION = 0.5

# Fertilizer. FERTILIZE marks a plant for `day`, `day+1`, `day+2` and only
# pays out on days the plant is also watered (kaggriculture.py: the bonus is
# gated on was_watered). What it's worth differs completely by crop type:
#
#   ONGOING crops bank +2 instead of +1 on every production tick inside the
#   window, so one $100 unit is worth roughly:
#     TOMATO      interval 1 -> catches 3 ticks -> +3 units
#     STRAWBERRY  interval 2 -> catches 2 ticks -> +2 units
#   Both trade well above base when nobody floods them, so this is the
#   strongest use of a fertilizer unit by a wide margin.
#
#   ONE-TIME crops only add to a yield that is already capped at max_yield:
#     WHEAT   +2 units (~$50-100 against a $100 unit - marginal)
#     CARROT  +1 unit  (a loss)
#     MELON   +0       - watering alone already reaches the cap of 6 exactly
#                        at first_yield_day, so fertilising it buys nothing
#
# So we only ever fertilise ongoing crops.
FERTILIZABLE_CROPS = ("TOMATO", "STRAWBERRY")

# Bought fertilizer lands in the shed, but FERTILIZE consumes from the
# acting unit's own inventory - so a unit has to stand shed-adjacent and
# PICKUP before it can fertilise anything. Carry a few at a time so one trip
# serves several plants instead of one.
FERTILIZER_CARRY_BATCH = 3

# Don't buy fertilizer we have no plant to use it on, and keep a lid on the
# stock so it doesn't crowd the shed or the cash.
MAX_FERTILIZER_STOCK = 6

# Fertilizer bought this late can't catch enough production ticks to repay
# itself before the season ends.
FERTILIZER_LAST_USEFUL_DAY = 24

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

# The engine processes at most this many market orders per player per turn
# and silently drops the rest (kaggriculture.json: maxMarketOrdersPerTurn),
# so going over the cap loses orders with no error to catch.
MAX_MARKET_ORDERS_PER_TURN = 10



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
    good enough for v0 since the board has no obstacles the farmer can't
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
      "harvest"      - a plant tile that's ready to pick right now.
      "water_urgent" - a plant tile that already missed a watering and
                        will turn into a weed if it's missed again today.
      "weed"         - a dead tile that can be dug back into plantable
                        ground.
      "any"          - anything at all worth walking to: a ripe plant,
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

            elif isinstance(tile, dict) and tile.get("kind") == "WEED" and task == "weed":
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

        score = (price * expected_yield - oversupply_penalty) / growth_days

      - price * expected_yield: rough revenue if we sell everything the
        plant produces at today's price.
      - oversupply_penalty: current market inventory of that product,
        scaled by its own price. This is what stops us from blindly
        planting strawberries just because their price *looks* high -
        a high price with a lot of stock already on the market is a
        sign the price is about to crash, not an opportunity.
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


def decide_market_actions(farm, private, market_state, day):
    """Build the list of ["SELL", ...] / ["BUY_SEED", ...] actions for this turn."""
    actions = []
    already_selling = set()

    # Sell anything sitting in the shed that's fetching a good price. Capped
    # per product (see MAX_SELL_PER_TURN) so a big harvest of a premium good
    # doesn't dump the whole stack into one price-crashing order.
    shed = private.get("shed", {})
    liquidating = day >= LIQUIDATION_START_DAY

    for product, quantity in shed.items():
        # Fertilizer is an input, not produce. It sits in the shed waiting
        # for a unit to PICKUP, and its price clears the default sell
        # threshold comfortably - so without this guard the agent buys it and
        # immediately sells it straight back, churning market-order slots and
        # never actually fertilising anything. Measured: 715 units sold in a
        # single season, with zero reaching a plant. Only dump it at the end,
        # when leftover stock scores nothing anyway.
        if product == "FERTILIZER" and not liquidating:
            continue

        # Near the end of the season, price thresholds stop mattering:
        # unsold stock scores nothing, so any sale beats holding out.
        if quantity > 0 and (liquidating or should_sell(product, quantity, market_state)):
            cap = MAX_SELL_PER_TURN.get(product, quantity)
            actions.append(["SELL", product, min(quantity, cap)])
            already_selling.add(product)

    # Shed is nearly full: anything not already being sold above would just
    # be discarded once the cap hits. Force a sale (still capped, so we
    # don't crash a premium good's price on the way out) rather than let it
    # evaporate for free.
    shed_total = sum(shed.values())
    if shed_total >= SHED_FORCE_SELL_THRESHOLD:
        for product, quantity in shed.items():
            if product in already_selling or quantity <= 0:
                continue
            cap = MAX_SELL_PER_TURN.get(product, quantity)
            actions.append(["SELL", product, min(quantity, cap)])

    # Buy exactly one seed of our preferred next crop, if it makes sense.
    preferred_crop = choose_crop(farm, market_state, private, day)
    if preferred_crop and should_buy_seed(preferred_crop, farm, private):
        actions.append(["BUY_SEED", preferred_crop, 1])

    # Fertilizer, but only against ongoing crops we actually have in the
    # ground - it's the one product where a unit has to fetch it from the
    # shed by hand, so buying speculatively wastes both money and turns.
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

def get_unit_inventory(private, unit_index):
    """What the given unit is carrying. inventories[0] is the main farmer."""
    inventories = private.get("inventories") or []
    if 0 <= unit_index < len(inventories):
        carried = inventories[unit_index]
        if isinstance(carried, dict):
            return carried
    return {}


def is_shed_adjacent(x, y, board_size):
    """
    The shed is not a tile and never appears in `tiles`. It is reachable
    from the four centre tiles, and only PICKUP/DROP need that adjacency -
    market orders work from anywhere.
    """
    half = board_size // 2
    return (x, y) in {
        (half - 1, half - 1), (half, half - 1),
        (half - 1, half), (half, half),
    }


def wants_fertilizer(tile, day):
    """
    True if fertilising this plant right now would actually pay.

    Only ongoing crops qualify (see FERTILIZABLE_CROPS), and only inside the
    stretch where the cover - today through day+2 - still catches production
    ticks. Fertiliser applied outside that window is simply thrown away.
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
    last_tick_age = first_yield_day + interval * (max_yield - 1)

    age = day - tile.get("planted_day", day)
    # Cover starts today and runs two more days, so applying just ahead of
    # the first tick still catches it.
    return (first_yield_day - 2) <= age <= last_tick_age


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


def choose_unit_action(state, ux, uy, claimed=None, unit_index=0):
    """
    Decide the single action for one unit - the main farmer or a hired
    hand - standing at (ux, uy), following the fixed priority order
    described at the top of this file.

    `claimed` is the set of (x, y) tiles other units have already taken
    this turn, and whatever this unit settles on is added to it. Without
    that bookkeeping every hand would independently pick the same nearest
    target and the whole crew would walk to one tile while the rest of
    the farm went to weeds - which defeats the point of hiring them.
    """
    claimed = claimed if claimed is not None else set()

    farm = state["farm"]
    if not farm:
        return ["PASS"]

    board_size = state["board_size"]
    day = state["day"]
    private = state["private"]
    seeds = private.get("seeds", {})
    tile = get_tile_at(farm, ux, uy)

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

    # 1. Harvest a ripe crop under our feet.
    if isinstance(tile, dict) and tile.get("kind") == "PLANT" and is_harvestable(tile, day):
        return act_here(["HARVEST"])

    # 2. Water a crop under our feet that hasn't been watered today.
    if isinstance(tile, dict) and tile.get("kind") == "PLANT" and not tile.get("watered_today", True):
        return act_here(["WATER"])

    # 2b. Fertilise the ongoing crop under our feet, if we're carrying any.
    #     Cheap - we're already standing here - and worth several hundred on
    #     a tomato or strawberry. Ranked below watering because the bonus
    #     only pays on days the plant is watered anyway.
    carried = get_unit_inventory(private, unit_index)
    if carried.get("FERTILIZER", 0) > 0 and wants_fertilizer(tile, day):
        return act_here(["FERTILIZE"])

    # 3. Something urgent elsewhere (a ripe crop, or a crop about to turn
    #    into a weed) beats anything else right now - preventing a new weed
    #    is worth more than reclaiming an old one.
    harvest_target = find_nearest_target(
        farm, board_size, ux, uy, "harvest", day, exclude=claimed
    )
    water_target = find_nearest_target(
        farm, board_size, ux, uy, "water_urgent", day, exclude=claimed
    )
    urgent_target = _closer_target(ux, uy, harvest_target, water_target)
    if urgent_target:
        moved = walk_to(urgent_target)
        if moved:
            return moved

    # 4. Reclaim a weed under our feet - free, and turns dead land back into
    #    something we can plant again instead of losing it for the rest of
    #    the season.
    if isinstance(tile, dict) and tile.get("kind") == "WEED":
        return act_here(["DIG"])

    # 5. Plant here if the tile is empty and unlocked, and we hold a seed.
    if tile is None:
        crop = choose_crop(farm, state["market_state"], private, day)
        if crop and seeds.get(crop, 0) > 0:
            return act_here(["PLANT", crop])

    # 5b. Fertiliser logistics. Bought fertilizer lands in the shed but
    #     FERTILIZE spends from the unit's own inventory, so this is a
    #     collect-then-deliver errand. Ranked below all the crop upkeep
    #     above: a plant that dies unwatered costs more than a fertiliser
    #     bonus is worth.
    shed_fertilizer = (private.get("shed") or {}).get("FERTILIZER", 0)
    carrying = carried.get("FERTILIZER", 0)

    if carrying > 0:
        fertilize_target = find_fertilizer_target(
            farm, board_size, ux, uy, day, exclude=claimed
        )
        if fertilize_target:
            moved = walk_to(fertilize_target)
            if moved:
                return moved

    elif shed_fertilizer > 0 and find_fertilizer_target(farm, board_size, ux, uy, day):
        # Collect a batch so one trip serves several plants.
        if is_shed_adjacent(ux, uy, board_size):
            return ["PICKUP", "FERTILIZER", min(shed_fertilizer, FERTILIZER_CARRY_BATCH)]

        half = board_size // 2
        direction = step_toward(ux, uy, half - 1, half - 1)
        if direction:
            return [direction]

    # 6. Reclaim the nearest weed elsewhere - dead land is a permanent loss
    #    until it's dug back to plantable ground, so don't just leave it.
    weed_target = find_nearest_target(
        farm, board_size, ux, uy, "weed", day, exclude=claimed
    )
    if weed_target:
        moved = walk_to(weed_target)
        if moved:
            return moved

    # 7. Nothing to do right here - walk toward the closest useful tile.
    fallback_target = find_nearest_target(
        farm, board_size, ux, uy, "any", day, seeds, exclude=claimed
    )
    if fallback_target and fallback_target != (ux, uy):
        moved = walk_to(fallback_target)
        if moved:
            return moved

    # 8. Genuinely nothing useful to do.
    return ["PASS"]


def choose_farmer_action(state, claimed=None):
    """Our main farmer's action - the shared unit logic, anchored at the farmer."""
    farm = state.get("farm")
    if not farm:
        return ["PASS"]

    farmer_pos = farm.get("farmer")
    if not farmer_pos or len(farmer_pos) != 2:
        return ["PASS"]

    return choose_unit_action(state, farmer_pos[0], farmer_pos[1], claimed, unit_index=0)


# ---------------------------------------------------------------------
# Agent entry point
# ---------------------------------------------------------------------

def nikaangukia_meroni(obs):
    """
    Washamba Bots' v0 baseline agent.

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
        claimed = set()
        farmer_action = choose_farmer_action(state, claimed)
        hands_actions = [
            # inventories[0] is the main farmer, so hand i is index i + 1.
            choose_unit_action(state, hand[0], hand[1], claimed, unit_index=index + 1)
            for index, hand in enumerate(farm.get("hands") or [])
            if isinstance(hand, (list, tuple)) and len(hand) == 2
        ]

        # Hires go first: they're a few dollars each and multiply how much
        # work the crew gets through, so they're the last orders we'd want
        # silently dropped if we ever brush the per-turn cap.
        market = decide_hire_orders(farm, board_size, day, hour, seeds)
        market += decide_market_actions(farm, private, state["market_state"], day)

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


# Kaggle environments calls the agent as a plain function of the
# observation, exactly as shown in the official starter notebook
# (e.g. `env.run([melon_maxxer, "random"])`).
agent = nikaangukia_meroni
