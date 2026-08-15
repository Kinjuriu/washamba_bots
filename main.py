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
SHED_FORCE_SELL_THRESHOLD = 90

# Never spend more than this fraction of our current cash on a single
# seed purchase, so a bad crop pick can't wipe out our bank balance.
SEED_SPEND_CAP_FRACTION = 0.5


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


def get_current_tile(farm):
    """Return the tile dict/None/"LOCKED" the farmer is currently standing on."""
    tiles = farm.get("tiles") if farm else None
    farmer_pos = farm.get("farmer") if farm else None
    if not tiles or not farmer_pos or len(farmer_pos) != 2:
        return None

    fx, fy = farmer_pos
    if fy < 0 or fy >= len(tiles):
        return None
    row = tiles[fy]
    if fx < 0 or fx >= len(row):
        return None
    return row[fx]


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


def find_nearest_target(farm, board_size, fx, fy, task, day, seeds=None):
    """
    Scan the whole farm grid and return the (x, y) of the closest tile
    matching `task`, or None if there isn't one.

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
    tiles = farm.get("tiles") or []
    have_any_seed = has_plantable_seed(seeds, day)

    best_target = None
    best_distance = None

    for y in range(board_size):
        row = tiles[y] if y < len(tiles) else []
        for x in range(len(row)):
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
# Crop selection
# ---------------------------------------------------------------------

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
        oversupply_penalty = stock * price

        score = (price * expected_yield - oversupply_penalty) / growth_days

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
    for product, quantity in shed.items():
        if should_sell(product, quantity, market_state):
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

    return actions


# ---------------------------------------------------------------------
# Farmer decision
# ---------------------------------------------------------------------

def choose_farmer_action(state):
    """
    Decide the single action for our main farmer this turn, following
    the fixed priority order described at the top of this file.
    """
    farm = state["farm"]
    if not farm:
        return ["PASS"]

    farmer_pos = farm.get("farmer")
    if not farmer_pos or len(farmer_pos) != 2:
        return ["PASS"]
    fx, fy = farmer_pos

    board_size = state["board_size"]
    day = state["day"]
    private = state["private"]
    seeds = private.get("seeds", {})
    tile = get_current_tile(farm)

    # 1. Harvest a ripe crop under our feet.
    if isinstance(tile, dict) and tile.get("kind") == "PLANT" and is_harvestable(tile, day):
        return ["HARVEST"]

    # 2. Water a crop under our feet that hasn't been watered today.
    if isinstance(tile, dict) and tile.get("kind") == "PLANT" and not tile.get("watered_today", True):
        return ["WATER"]

    # 3. Something urgent elsewhere (a ripe crop, or a crop about to turn
    #    into a weed) beats anything else right now - preventing a new weed
    #    is worth more than reclaiming an old one.
    harvest_target = find_nearest_target(farm, board_size, fx, fy, "harvest", day)
    water_target = find_nearest_target(farm, board_size, fx, fy, "water_urgent", day)
    urgent_target = _closer_target(fx, fy, harvest_target, water_target)
    if urgent_target:
        direction = step_toward(fx, fy, urgent_target[0], urgent_target[1])
        if direction:
            return [direction]

    # 4. Reclaim a weed under our feet - free, and turns dead land back into
    #    something we can plant again instead of losing it for the rest of
    #    the season.
    if isinstance(tile, dict) and tile.get("kind") == "WEED":
        return ["DIG"]

    # 5. Plant here if the tile is empty and unlocked, and we hold a seed.
    if tile is None:
        crop = choose_crop(farm, state["market_state"], private, day)
        if crop and seeds.get(crop, 0) > 0:
            return ["PLANT", crop]

    # 6. Reclaim the nearest weed elsewhere - dead land is a permanent loss
    #    until it's dug back to plantable ground, so don't just leave it.
    weed_target = find_nearest_target(farm, board_size, fx, fy, "weed", day)
    if weed_target:
        direction = step_toward(fx, fy, weed_target[0], weed_target[1])
        if direction:
            return [direction]

    # 7. Nothing to do right here - walk toward the closest useful tile.
    fallback_target = find_nearest_target(farm, board_size, fx, fy, "any", day, seeds)
    if fallback_target and fallback_target != (fx, fy):
        direction = step_toward(fx, fy, fallback_target[0], fallback_target[1])
        if direction:
            return [direction]

    # 8. Genuinely nothing useful to do.
    return ["PASS"]


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

        return {
            "farmer": choose_farmer_action(state),
            "hands": [],  # v0 doesn't hire any farm hands yet
            "market": decide_market_actions(farm, state["private"], state["market_state"], state["day"]),
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
