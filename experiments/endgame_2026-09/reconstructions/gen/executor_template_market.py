# =======================================================================
# MACRO ROUTE EXECUTOR - reconstruction from {PLAYER}'s own winning replays.
#
# METHOD: for each turn-72 opening key (the first shop the town unlocks),
# among {PLAYER}'s wins that drew that opening, take the MEDOID game -
# smallest total action-distance to every other win in that cluster - and
# extract a coordinate-discarded macro schedule from it: land-purchase
# days, a crew-size target per day, a per-species animal herd target by
# day, a day-indexed crop-planting histogram, and the exact turn-indexed
# SELL/BUY_SEED/BUY_PRODUCT schedule. One real coherent winning game per
# opening, never a blend of several - see the medoid selection in
# ~/KagricultureLocalData/reconstructions/analyze.py.
#
# EXECUTION: base_backbone.py's own choose_unit_action ladder above still
# decides every on-tile action and every walk-toward-a-target movement
# exactly as it always has - it is the "legality/movement/sanitizing
# layer" the reconstruction spec asked for. This section only answers,
# each turn, WHAT the macro route wants done (which crop, which species,
# hire how many, sell/buy what) - two small hooks (crop_picker,
# animal_picker) feed that answer into the unchanged ladder instead of
# base_backbone's own live-market heuristics; everything about HOW a unit
# reaches a legal tile to do it is untouched.
#
# An OPENING route (the medoid across ALL wins, distance measured only on
# steps 0-71) plays before any shop is known - {PLAYER}'s early game looks
# similar regardless of which opening it eventually draws, so this is
# real shared content, not a Frankenstein blend of two different families'
# strategies spliced at the handover. The agent switches to the specific
# shop-keyed route the moment a shop actually unlocks.
#
# Sell/buy timing is replayed at {PLAYER}'s own exact turn, sanitized to
# CURRENT holdings/affordability (sell min(planned, held), buy only what
# the running cash reserve allows) - a literal quantity replay would break
# the instant a different seed's economy diverges even slightly from the
# medoid's. base_backbone's own proven threshold-selling/seed-restock/
# fertilizer safety net still runs underneath every turn (skipping
# whatever the macro schedule already sold this turn), so a route/seed
# mismatch can degrade toward base_backbone's own economics, never toward
# stranded goods or an empty seed stockpile.
#
# Animal purchases are driven by a per-day CUMULATIVE herd TARGET per
# species, compared against the CURRENT live count - not a sequential
# purchase queue. A queue-position pointer would double-buy (or under-buy)
# the instant the OPENING route hands off to a shop-keyed route with its
# own, different event sequence; comparing live counts to a target is
# correct regardless of which route was active a moment ago.
#
# FLOOR: any exception anywhere in this section, or a genuinely unmatched
# opening (only reachable via a malformed observation - all 8 real shops
# are covered), falls back to _agent_fam_lead_floor(obs) - router_fam_lead
# unmodified, this repo's own strongest local base. Never an illegal,
# empty, or wrong-length action.
# =======================================================================

_ANIMAL_BUILD_LEAD_DAYS = 2  # start building a structure a bit ahead of the day it's needed

_recon_state = {"last_step": None, "route_key": None, "route": None}


def _reset_if_new_episode(step):
    if _recon_state["last_step"] is None or step < _recon_state["last_step"]:
        _recon_state["route_key"] = None
        _recon_state["route"] = None
    _recon_state["last_step"] = step


def _select_route(state):
    if _recon_state["route"] is None:
        _recon_state["route_key"] = "OPENING"
        _recon_state["route"] = _ROUTES.get("OPENING")
    if _recon_state["route_key"] == "OPENING":
        shops = list(state.get("unlocked_shops") or [])
        if shops:
            key = str(shops[0])
            if key in _ROUTES:
                _recon_state["route_key"] = key
                _recon_state["route"] = _ROUTES[key]
    return _recon_state["route"]


def _nearest_day_entry(mapping, day):
    """mapping: {"<day>": value}. Nearest recorded day <= `day`, else the
    earliest recorded day (for a day before anything was recorded yet)."""
    if not mapping:
        return None
    days = sorted(int(d) for d in mapping)
    le = [d for d in days if d <= day]
    chosen = max(le) if le else min(days)
    return mapping[str(chosen)]


def macro_choose_crop(
    route, farm, market_state, private, day, unlocked_shops=(), start_step=None,
    opponent_pipeline=None, require_held_seed=False,
):
    seeds = private.get("seeds", {})
    money = farm.get("money", 0)
    remaining_days = remaining_season_days(day)
    candidates = _nearest_day_entry(route["plan"]["crop_by_day"], day) if route else None
    if candidates:
        for crop, _count in candidates:
            crop_info = CROPS.get(crop)
            if not crop_info:
                continue
            first_yield_day = crop_info.get("first_yield_day")
            if first_yield_day is not None and first_yield_day > remaining_days:
                continue
            seed_cost = crop_info.get("seed")
            have_seed = seeds.get(crop, 0) > 0
            can_afford = seed_cost is not None and money >= seed_cost
            if require_held_seed:
                if not have_seed:
                    continue
            elif not have_seed and not can_afford:
                continue
            return crop
    # No macro guidance for this day, or nothing in it is plantable right
    # now - fall back to base_backbone's own live crop economics rather
    # than leaving the tile idle.
    return choose_crop(
        farm, market_state, private, day, unlocked_shops=unlocked_shops,
        start_step=start_step, opponent_pipeline=opponent_pipeline,
        require_held_seed=require_held_seed,
    )


def _placed_counts_by_species(farm, board_size):
    """How many structures actually hold each species right now - unlike
    species_owned_counts, this does NOT count shed-held (bought but not
    yet placed) or carried-but-not-placed animals. base_backbone's own
    species_owned_counts is right for base_backbone's small MAX_ANIMALS,
    where a placement backlog is transient; for a large reconstructed herd
    it is the wrong signal for "do we need more" - it lets a big shed
    backlog of un-placed purchases (produce nothing) satisfy the target and
    stop the pipeline, which is exactly the failure this function exists to
    avoid (measured: filled structures stuck at 1-3 all season while
    "owned" already matched the target)."""
    counts = {}
    tiles = farm.get("tiles") or []
    for y in range(board_size):
        row = tiles[y] if y < len(tiles) else []
        for tile in row:
            if isinstance(tile, dict) and tile.get("kind") in ANIMAL_STRUCTURE_KINDS and "animal" in tile:
                species = tile.get("animal")
                counts[species] = counts.get(species, 0) + 1
    return counts


def _any_animal_starving(farm, board_size):
    """True if any CURRENTLY PLACED animal has already missed a feeding
    (consecutive_unfed >= 1 - one more miss and it escapes for good)."""
    tiles = farm.get("tiles") or []
    for y in range(board_size):
        row = tiles[y] if y < len(tiles) else []
        for tile in row:
            if isinstance(tile, dict) and "animal" in tile and tile.get("consecutive_unfed", 0) >= 1:
                return True
    return False


def _animal_deficits(route, farm, private, board_size, day, lookahead=0, count_pending=True):
    """
    Species furthest below its day-`day` herd target, ranked by deficit.

    `count_pending=True` (buy-side): a species already fully covered by
    placed-plus-shed-held (bought, awaiting placement) animals is not
    bought again - it's already in the pipeline. `count_pending=False`
    (build-side): only PLACED counts, since shed-held stock sitting there
    unplaced is exactly the evidence more build capacity is needed, not
    less.

    Growing the herd further is paused entirely while any animal we
    already have is at risk of escaping (_any_animal_starving) - without
    this, a crew that's falling behind on feeding a large reconstructed
    herd escapes an animal, which frees its structure and reopens a
    "deficit" that immediately re-triggers another purchase, compounding
    the very overextension that caused the escape - measured directly: a
    buy/starve/re-buy loop that kept draining cash on repeat purchases of
    animals the crew could never actually keep fed.
    """
    if _any_animal_starving(farm, board_size):
        return []
    target = _nearest_day_entry(route["plan"]["animal_target_by_day"], day + lookahead) if route else None
    if not target:
        return []
    placed = _placed_counts_by_species(farm, board_size)
    shed = private.get("shed", {})
    money = farm.get("money", 0)
    remaining_days = remaining_season_days(day)
    deficits = []
    for species, want in target.items():
        have = placed.get(species, 0)
        if count_pending:
            have += shed.get(species, 0)
        if have >= want:
            continue
        info = ANIMALS.get(species)
        if not info:
            continue
        if info.get("first_yield_day", 0) > remaining_days:
            continue
        cost = info.get("cost")
        if cost is None or money < cost or cost > money * ANIMAL_SPEND_CAP_FRACTION:
            continue
        if money - cost < MIN_CASH_RESERVE_FOR_ANIMAL_BUYING:
            continue
        # Rank by RATIO (have/want), not absolute gap - matching
        # base_backbone's own pick_next_animal_species deficit_key. Two
        # species with different targets (e.g. COW wants 9, GOOSE wants 12)
        # otherwise starve whichever has the smaller target forever: an
        # absolute-gap sort always hands the single at-a-time build slot to
        # GOOSE (bigger raw number) even after COW's own dedicated PASTURE
        # has never once been built - measured directly: COW stuck at 0
        # placed all game while GOOSE reached its target under the old
        # absolute-gap ranking.
        deficits.append((have / want, species))
    deficits.sort()
    return deficits


def macro_choose_animal_to_build(route, farm, private, board_size, day, pending_builds=0, ux=None, uy=None):
    filled, unfilled = scan_animal_structures(farm, board_size)
    if unfilled > 0 or pending_builds > 0 or not route:
        return None
    deficits = _animal_deficits(
        route, farm, private, board_size, day,
        lookahead=_ANIMAL_BUILD_LEAD_DAYS, count_pending=False,
    )
    return deficits[0][1] if deficits else None


def macro_animal_market_orders(route, farm, private, board_size, day):
    if not route:
        return []
    filled, unfilled = scan_animal_structures(farm, board_size)
    if unfilled <= 0:
        return []
    deficits = _animal_deficits(route, farm, private, board_size, day, count_pending=True)
    if not deficits:
        return []
    species = deficits[0][1]
    actions = [["BUY_ANIMAL", species, 1]]
    money = farm.get("money", 0)
    if filled > 0 and money > 0:
        shed_wheat = private.get("shed", {}).get("WHEAT", 0)
        carried_wheat = sum(
            inv.get("WHEAT", 0) for inv in (private.get("inventories") or []) if isinstance(inv, dict)
        )
        if shed_wheat + carried_wheat < MIN_WHEAT_RESERVE_FOR_FEEDING:
            actions.append(["BUY_PRODUCT", "WHEAT", 1])
    return actions


def macro_land_orders(route, farm, day):
    if not route:
        return []
    land_days = sorted(route["plan"]["land_days"])
    unlocked = farm.get("unlocked_quadrants") or ["NW"]
    n_extra = len(unlocked) - 1
    if n_extra >= MAX_LAND_PURCHASES or n_extra >= len(land_days):
        return []
    if day < land_days[n_extra]:
        return []
    cost = LAND_PRICES[n_extra]
    money = farm.get("money", 0)
    if money - cost < MIN_CASH_RESERVE_FOR_LAND_BUYING:
        return []
    return [["BUY_LAND"]]


def macro_hire_orders(route, farm, day, hour):
    if hour >= HIRE_BEFORE_HOUR:
        return []
    if farm.get("money", 0) < MIN_MONEY_TO_HIRE:
        return []
    target = _nearest_day_entry(route["plan"]["crew_by_day"], day) if route else None
    if target is None:
        target = 4  # small safe default before any macro crew reading exists
    wanted_hands = max(0, target - 1)  # target includes the farmer
    already_working = len(farm.get("hands") or [])
    shortfall = min(max(0, wanted_hands - already_working), MAX_HIRES_PER_TURN)
    hires_today = farm.get("hires_today", 0)
    remaining_money = farm.get("money", 0)
    orders = []
    for i in range(shortfall):
        cost = _hire_cost(hires_today + i)
        if cost > remaining_money:
            break
        remaining_money -= cost
        orders.append(["HIRE"])
    return orders


_OPPONENT_SCARCITY_SKIP = ("WHEAT", "FERTILIZER")  # operational, not the timed-scarcity target
_OPPONENT_SCARCITY_LOOKAHEAD = 3  # days


def _opponent_imminent_products(obs, day, lookahead=_OPPONENT_SCARCITY_LOOKAHEAD):
    """
    Products the OPPONENT is about to put on the shared market from their
    own visible crops/animals within `lookahead` days - obs["farms"] is
    public for both players (only obs["private"]/shed is own-only), so
    this reads real, not estimated, opponent state.
    """
    try:
        farms = obs.get("farms") or []
        player = obs.get("player", 0)
        if len(farms) < 2:
            return set()
        opponent = farms[1 - player] or {}
    except Exception:
        return set()

    imminent = set()
    for row in (opponent.get("tiles") or []):
        for tile in row or []:
            if not isinstance(tile, dict):
                continue
            if tile.get("kind") == "PLANT":
                crop = tile.get("crop")
                crop_info = CROPS.get(crop) or {}
                first_yield_day = crop_info.get("first_yield_day")
                if first_yield_day is None:
                    continue
                planted_day = tile.get("planted_day", day)
                days_until = first_yield_day - (day - planted_day)
                if 0 <= days_until <= lookahead:
                    imminent.add(crop)
            elif "animal" in tile:
                info = ANIMALS.get(tile.get("animal")) or {}
                product = info.get("product")
                max_held = info.get("max_held", 1)
                held = tile.get("yield_units", 0)
                # Close to its held cap = due to be collected/harvested soon,
                # same "about to hit the market" signal as a maturing crop.
                if product and held >= max(0, max_held - 1):
                    imminent.add(product)
    return imminent


def macro_market_actions(
    route, farm, private, market_state, day, step, reserved_wheat=0,
    unlocked_shops=(), start_step=None, opponent_pipeline=None, obs=None,
):
    actions = []
    already_selling = set()
    shed = private.get("shed", {})
    money = farm.get("money", 0)

    # OPPONENT-SUPPLY-AWARE SELLING (the one change this file makes over
    # recon_dsm.py): sell into scarcity, before the opponent's own
    # imminent harvest crashes the shared order book. Both players sell
    # into the SAME market_price() curve, so a rival's harvest landing
    # tomorrow depresses OUR sale of the same product today's price
    # doesn't yet reflect - see base_backbone.py's own
    # count_opponent_pipeline for the same "their tiles are public" idea,
    # applied here to TIMING instead of crop-choice. Deliberately NOT the
    # "hold everything for one late wave" idea tried and rejected earlier
    # (it hit the shed's global 100-item cap and discarded harvest,
    # -17.5k measured) - this only ever sells EARLIER than the macro
    # schedule would have, from CURRENT holdings, never holds anything
    # back.
    if obs is not None:
        imminent = _opponent_imminent_products(obs, day)
        for product in imminent:
            if product in _OPPONENT_SCARCITY_SKIP or product in already_selling:
                continue
            if product not in MARKET_PARAMS:
                continue
            held = shed.get(product, 0)
            if held > 0:
                actions.append(["SELL", product, held])
                already_selling.add(product)

    if route:
        for t, product, qty in route["plan"]["sell_events"]:
            if t != step or product not in MARKET_PARAMS:
                continue
            held = shed.get(product, 0)
            if product == "WHEAT":
                held = max(0, held - reserved_wheat)
            amount = min(qty, held)
            if amount > 0:
                actions.append(["SELL", product, amount])
                already_selling.add(product)

        for t, kind, product, qty in route["plan"]["buy_events"]:
            if t != step:
                continue
            if kind == "BUY_SEED":
                crop_info = CROPS.get(product)
                seed_cost = crop_info.get("seed") if crop_info else None
                if seed_cost is None:
                    continue
                affordable_qty = 0
                remaining = money
                for _ in range(qty):
                    if seed_cost > remaining or seed_cost > remaining * SEED_SPEND_CAP_FRACTION:
                        break
                    if remaining - seed_cost < MIN_CASH_RESERVE_FOR_SEED_BUYING:
                        break
                    remaining -= seed_cost
                    affordable_qty += 1
                if affordable_qty > 0:
                    actions.append(["BUY_SEED", product, affordable_qty])
            elif kind == "BUY_PRODUCT" and product in ("WHEAT", "FERTILIZER"):
                price = market_state.get("prices", {}).get(product, 0)
                if price and money >= price * qty:
                    actions.append(["BUY_PRODUCT", product, qty])

    crop_picker = (lambda *a, **kw: macro_choose_crop(route, *a, **kw)) if route else None
    fallback = decide_market_actions(
        farm, private, market_state, day, reserved_wheat=reserved_wheat,
        unlocked_shops=unlocked_shops, start_step=start_step,
        opponent_pipeline=opponent_pipeline, crop_picker=crop_picker,
    )
    for order in fallback:
        if order and order[0] == "SELL" and order[1] in already_selling:
            continue
        actions.append(order)
    return actions


def recon_agent(obs):
    if not USE_RECON:
        return _agent_fam_lead_floor(obs)
    try:
        state = extract_state(obs)
        farm = state["farm"]
        if not farm:
            return {"farmer": ["PASS"], "hands": [], "market": []}

        board_size = state["board_size"]
        day = state["day"]
        hour = state["hour"]
        step = state["step"]
        private = state["private"]
        seeds = private.get("seeds", {})

        _reset_if_new_episode(step)
        route = _select_route(state)

        crop_picker = lambda *a, **kw: macro_choose_crop(route, *a, **kw)
        animal_picker = lambda *a, **kw: macro_choose_animal_to_build(route, *a, **kw)

        claimed = set()
        pending_builds = [0]
        feed_claimed = set()
        plant_budget = dict(seeds)
        wheat_budget = {"WHEAT": private.get("shed", {}).get("WHEAT", 0)}

        farmer_pos = farm.get("farmer")
        farmer_action = ["PASS"]
        if farmer_pos and len(farmer_pos) == 2:
            farmer_action = choose_unit_action(
                state, farmer_pos[0], farmer_pos[1], 0, claimed, pending_builds,
                feed_claimed, plant_budget, wheat_budget, crop_picker, animal_picker,
            )

        hands = [
            h for h in (farm.get("hands") or [])
            if isinstance(h, (list, tuple)) and len(h) == 2
        ]
        hands_actions = [
            choose_unit_action(
                state, h[0], h[1], idx + 1, claimed, pending_builds, feed_claimed,
                plant_budget, wheat_budget, crop_picker, animal_picker,
            )
            for idx, h in enumerate(hands)
        ]

        market = macro_hire_orders(route, farm, day, hour)
        filled_animals, _ = scan_animal_structures(farm, board_size)
        reserved_wheat = filled_animals * MIN_WHEAT_RESERVE_FOR_FEEDING
        market += macro_market_actions(
            route, farm, private, state["market_state"], day, step,
            reserved_wheat=reserved_wheat, unlocked_shops=state["unlocked_shops"],
            start_step=state["step"], opponent_pipeline=state.get("opponent_pipeline"),
            obs=obs,
        )
        market += macro_animal_market_orders(route, farm, private, board_size, day)
        market += macro_land_orders(route, farm, day)

        return {
            "farmer": farmer_action,
            "hands": hands_actions,
            "market": market[:MAX_MARKET_ORDERS_PER_TURN],
        }
    except Exception:
        return _agent_fam_lead_floor(obs)


# The framework picks the LAST callable in this module's namespace - not a
# function named `agent` (kaggle_environments/agent.py:64). Keep this last.
agent = recon_agent
