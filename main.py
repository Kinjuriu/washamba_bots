"""
nikaangukia_meroni_v0
======================

Washamba Bots' first deterministic baseline agent for the Kaggriculture
competition.

This is deliberately NOT a sophisticated AI. It is a simple, readable,
rule-based farmer that:

  1. Harvests ripe crops.
  2. Waters crops that need it.
  3. Moves toward urgent tasks before doing anything else.
  4. Plants a sensible crop when standing on an empty tile.
  5. Otherwise walks toward the next useful tile.
  6. PASSes if there is genuinely nothing useful to do.

It also does simple, threshold-based market decisions: sell shed goods
when the price is good, buy one seed at a time when we need one and can
afford it.

NOT implemented in this version (on purpose, to keep v0 simple):
  - Animals (COOP / PASTURE tiles), feeding, or collecting animal goods.
  - Hired hands ("hands" is always returned empty).
  - Buying land / unlocking new quadrants.
  - Digging weeds (WEED tiles are simply avoided/ignored for now).
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

# Don't stockpile more seeds of one crop than this - keeps cash free for
# other things instead of hoarding.
MAX_SEED_STOCKPILE = 3

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


def find_nearest_target(farm, board_size, fx, fy, task, seeds=None):
    """
    Scan the whole farm grid and return the (x, y) of the closest tile
    matching `task`, or None if there isn't one.

    task options:
      "harvest"      - a plant tile that's ready to pick right now.
      "water_urgent" - a plant tile that already missed a watering and
                        will turn into a weed if it's missed again today.
      "any"          - anything at all worth walking to: a ripe plant,
                        an unwatered plant, or (if we're holding at
                        least one seed) an empty tile we could plant.
    """
    seeds = seeds or {}
    tiles = farm.get("tiles") or []
    have_any_seed = any(count > 0 for count in seeds.values())

    best_target = None
    best_distance = None

    for y in range(board_size):
        row = tiles[y] if y < len(tiles) else []
        for x in range(len(row)):
            tile = row[x]
            is_match = False

            if isinstance(tile, dict) and tile.get("kind") == "PLANT":
                is_ripe = tile.get("yield_units", 0) > 0
                needs_water = not tile.get("watered_today", True)
                missed_before = tile.get("consecutive_unwatered", 0) >= 1

                if task == "harvest" and is_ripe:
                    is_match = True
                elif task == "water_urgent" and needs_water and missed_before:
                    is_match = True
                elif task == "any" and (is_ripe or needs_water):
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

def choose_crop(farm, market_state, private):
    """
    Pick the crop we'd most like to plant next, or None if nothing makes
    sense right now (nothing affordable/held).

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
    can afford to buy one.
    """
    money = farm.get("money", 0)
    prices = market_state.get("prices", {})
    inventory = market_state.get("inventory", {})
    seeds = private.get("seeds", {})

    best_crop = None
    best_score = None

    for crop in PLANTABLE_CROPS:
        crop_info = CROPS.get(crop)
        if not crop_info:
            continue  # unknown crop metadata - skip rather than guess

        seed_cost = crop_info.get("seed")
        expected_yield = crop_info.get("max_yield")
        growth_days = crop_info.get("max_yield_day")
        if seed_cost is None or expected_yield is None or not growth_days:
            continue

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


def decide_market_actions(farm, private, market_state):
    """Build the list of ["SELL", ...] / ["BUY_SEED", ...] actions for this turn."""
    actions = []

    # Sell anything sitting in the shed that's fetching a good price.
    shed = private.get("shed", {})
    for product, quantity in shed.items():
        if should_sell(product, quantity, market_state):
            actions.append(["SELL", product, quantity])

    # Buy exactly one seed of our preferred next crop, if it makes sense.
    preferred_crop = choose_crop(farm, market_state, private)
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
    private = state["private"]
    seeds = private.get("seeds", {})
    tile = get_current_tile(farm)

    # 1. Harvest a ripe crop under our feet.
    if isinstance(tile, dict) and tile.get("kind") == "PLANT" and tile.get("yield_units", 0) > 0:
        return ["HARVEST"]

    # 2. Water a crop under our feet that hasn't been watered today.
    if isinstance(tile, dict) and tile.get("kind") == "PLANT" and not tile.get("watered_today", True):
        return ["WATER"]

    # 3. Something urgent elsewhere (a ripe crop, or a crop about to turn
    #    into a weed) beats planting a brand-new crop right now.
    harvest_target = find_nearest_target(farm, board_size, fx, fy, "harvest")
    water_target = find_nearest_target(farm, board_size, fx, fy, "water_urgent")
    urgent_target = _closer_target(fx, fy, harvest_target, water_target)
    if urgent_target:
        direction = step_toward(fx, fy, urgent_target[0], urgent_target[1])
        if direction:
            return [direction]

    # 4. Plant here if the tile is empty and unlocked, and we hold a seed.
    if tile is None:
        crop = choose_crop(farm, state["market_state"], private)
        if crop and seeds.get(crop, 0) > 0:
            return ["PLANT", crop]

    # 5. Nothing to do right here - walk toward the closest useful tile.
    fallback_target = find_nearest_target(farm, board_size, fx, fy, "any", seeds)
    if fallback_target and fallback_target != (fx, fy):
        direction = step_toward(fx, fy, fallback_target[0], fallback_target[1])
        if direction:
            return [direction]

    # 6. Genuinely nothing useful to do.
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
            "market": decide_market_actions(farm, state["private"], state["market_state"]),
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
