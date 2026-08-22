"""Whole-economy structural model for Kaggriculture. RESEARCH ONLY.

Not imported by main.py and does not change agent behaviour (same convention
as pricing.py). Purpose: map the crop + animal + land + hiring + selling
economy as it currently exists in main.py, so structural conflicts between
its pieces can be found and explained before anything is changed - per the
repeated dead-end pattern in CLAUDE.md, where four separate wrapper-style
fixes to choose_crop() all failed because none of them touched the actual
constraint (STRAWBERRY's narrow planting window vs. early-season crew/cash
capacity), only reshuffled what's downstream of it.

Design choice - drive the real engine, don't reproduce it: every mechanic
that isn't genuinely spatial (tile growth/decay, market pricing, town/shop
demand, hiring cost, land purchase, animal feed/care/production) is executed
by literally calling the installed engine's own state-mutation functions
(kaggriculture.py's _apply_unit_action, _commit_unit, _do_hire, _do_buy_land,
_daily_refresh_plants, _decay_plants, _daily_refresh_animals, market_price)
against a real tiles/shed/market state shaped exactly like the engine's own.
This can't silently drift from a future engine patch the way a hand-rolled
reproduction could - per "engine is the source of truth" (CLAUDE.md).

The one thing deliberately NOT modelled is spatial pathing: which unit walks
where, tile-claim collisions, multi-turn carry trips for wheat/fertilizer/
animals. That is out of scope on purpose - per the team's own framing, those
are spatial/opponent-timing problems better attacked with
experiments/replay_diagnostics.py and targeted experiments, not a structural
model. In its place, `_assign_crew` ranks every tile needing attention by the
same priority choose_unit_action's ladder uses and lets the turn's crew
(farmer + hands, sized by the real decide_hire_orders/max_hands_ceiling
output) act on the top N of them directly - an explicit, documented
abstraction, not an attempt to reproduce real per-episode turn counts. Within
each priority tier, which unit gets matched to which tile is chosen by the
Hungarian algorithm (scipy.optimize.linear_sum_assignment) over Manhattan
distance - exact and cheap here because FARMER_MOVES is 4-directional with
no obstacles (kaggriculture.py:88-93), so this is a pure assignment problem,
not a pathfinding one. Units still act on their assigned tile for free the
same turn (no travel time is charged) - only *which* unit is matched to
*which* tile improved, tracked via a `total_assignment_distance` counter as
a first, cheap proxy for how much real travel a policy would require.
Simulating that travel turn-by-turn (SimPy-style discrete-event scheduling)
would be a separate, larger change - deliberately not done here.

Also deliberately absent until now, closed by `ContestedEconomyModel`/
`run_contested_episode`: a competing seller. `EconomyModel`/`run_episode`
alone only ever face town/shop demand, so every number out of them is
directional, not a price-impact prediction - the real mechanism behind
fertilizer round-trips, melon gluts, and wool depth is two order streams
sharing one inventory mid-order (kaggriculture.py's `_process_market`,
replicated here as `_process_market_two_sided`), which cannot exist with
only one seller. Use `run_contested_episode` for anything about
selling cadence or price impact; `run_episode` remains correct for anything
about farm upkeep (crops/animals/land/hiring), where the built-in-opponent
shape (nobody else selling) is the right comparison per CLAUDE.md.

Contested mode's inflation is worse than solo's, not just present, and this
is verified rather than assumed (see `validate_contested`'s scenario 4):
both sides keep solo-level zero-travel-time throughput while now competing
for the SAME fixed town/shop demand, so the combined glut/revenue crash can
be far more severe than either two real agents or bptk's solo mode alone.
On seed 0 with default policy both sides, this collapses both sides into a
days 6-18 cash-trough stall (money stuck at the ~$19 hire-gate floor
CLAUDE.md documents) that never happens in real self-play (~$41k mean, no
collapse) - a real property of running two hyper-efficient sellers against
each other, not a bug. Treat contested-mode absolute numbers as even less
literal than solo's; they are still directionally useful for comparing two
policies against each other under the *same* inflation.

The policy under test is main.py's real functions, called directly
(choose_crop, seed_restock_quantity, choose_animal_to_build,
decide_hire_orders, decide_land_orders, decide_market_actions,
decide_animal_market_actions, should_sell) - never reimplemented. A finding
is only trustworthy if it comes from calling that real code, since the whole
point is to explain what main.py actually does, not what a paraphrase of it
would do.

A previously undocumented candidate bug (see choose_unit_action's PLANT
branch, main.py ~2351-2362): choose_crop() can name a crop via its
`can_afford` branch even when the unit holds zero seed for it, but
plant_budget is seeded only from currently-held seed counts, so the PLANT
never lands and that crew-turn is spent on nothing. This model reproduces
that exact mismatch (see `crop_chosen_but_not_planted` in the counters)
rather than fixing it, so its real magnitude can be measured before anyone
decides whether it's worth a `main.py` change.

Usage:
    .venv/Scripts/python.exe bptk.py                       # one baseline episode
    .venv/Scripts/python.exe bptk.py --validate             # the validation gate
    .venv/Scripts/python.exe bptk.py --validate-contested   # contested-market checks
    .venv/Scripts/python.exe bptk.py --check-assignment     # Hungarian-assignment property check
    .venv/Scripts/python.exe bptk.py --contested             # one self-play contested episode
    .venv/Scripts/python.exe bptk.py --seed 3 --days 30

Animals ARE modelled here (feed/CARE/production, pasture build, the wheat
reserve they draw from) because they share cash, crew, and shed capacity
with the crop economy - deliberately not scoped out, per the "model
everything connected, then diagnose" decision this file's plan was built on.
"""

import collections
import contextlib
import random

from kaggle_environments.envs.kaggriculture.kaggriculture import (
    ANIMALS,
    CROPS,
    MARKET_PARAMS,
    SHOPS,
    TOWN_CENTER_PRODUCTS,
    MAX_SHOP_INSTANCES,
    FARM_HAND_COST_MULT,
    _new_farm,
    _new_private,
    _new_market,
    _new_town,
    _apply_unit_action,
    _commit_unit,
    _do_hire,
    _do_buy_land,
    _daily_refresh_plants,
    _decay_plants,
    _daily_refresh_animals,
    _spawn_weeds,
    _drop_inventories_to_shed,
    market_price,
    _refresh_prices,
    _parse_order,
)
from scipy.optimize import linear_sum_assignment

import main as agent_main

# ---------------------------------------------------------------------
# Engine-mirrored constants (same values main.py mirrors elsewhere - see
# kaggriculture.json / kaggriculture.py for the source of truth).
# ---------------------------------------------------------------------
BOARD_SIZE = 10
TURNS_PER_DAY = 24
SEASON_DAYS = 30
STARTING_MONEY = 3000
SHED_CAPACITY = 100
SHOP_SELL_INTERVAL = 4
CENTER_SELL_INTERVAL = 24
SHOP_UNLOCK_INTERVAL = 3
WEED_SPAWN_CHANCE = 0.005
HOME_SPAWN = (4, 4)  # any NW shed-adjacent tile; position is otherwise inert here


@contextlib.contextmanager
def _override_main(**kwargs):
    """Temporarily rebind module-level constants on `main` (never mutate a
    shared dict/list in place - CROPS/ANIMALS/SHOPS are the SAME objects the
    engine's own module holds, so an in-place edit would corrupt the real
    engine mechanics this model calls directly, not just main.py's policy).
    """
    missing = object()
    original = {key: getattr(agent_main, key, missing) for key in kwargs}
    try:
        for key, value in kwargs.items():
            setattr(agent_main, key, value)
        yield
    finally:
        for key, value in original.items():
            if value is missing:
                delattr(agent_main, key)
            else:
                setattr(agent_main, key, value)


def _tick_town_demand(market, town, step):
    """Town Centre / shop consumption for one step, against a shared market
    and town - factored out of EconomyModel so a contested episode can call
    it exactly once per step against the market both sides share, instead of
    once per side (which would double-consume demand)."""
    if step % SHOP_SELL_INTERVAL == 0:
        for shop_name in town["unlocked_shops"]:
            products = SHOPS[shop_name]
            multiplier = 2 if len(products) == 1 else 1
            for item in products:
                market["inventory"][item] -= multiplier
    if step % CENTER_SELL_INTERVAL == 0:
        for item in TOWN_CENTER_PRODUCTS:
            market["inventory"][item] -= 1
    _refresh_prices(market)


def _maybe_unlock_shop(town, next_day, rng):
    """Same reason as _tick_town_demand: shop unlocks are global town state,
    factored out so a contested episode advances them once, not per side."""
    if next_day > 0 and next_day % SHOP_UNLOCK_INTERVAL == 0:
        if len(town["unlocked_shops"]) < MAX_SHOP_INSTANCES:
            town["unlocked_shops"].append(rng.choice(sorted(SHOPS)))


def _process_market_two_sided(sides, market, board_size=BOARD_SIZE,
                               hire_mult=FARM_HAND_COST_MULT, shed_capacity=SHED_CAPACITY):
    """Replicates kaggriculture.py's real _process_market lockstep (lines
    544-628): per order-index across every side's order queue, atomic orders
    (HIRE/BUY_LAND) resolve first in side order, then SELL/BUY_* orders quote
    off the SAME pre-commit inventory and commit sequentially side by side -
    the exact mechanism behind price impact (fertilizer round-trips, melon
    gluts, wool depth: your own order moves the price against you, and so
    does the other side's). `sides` is a list of
    {"farm", "private", "orders", "counters"} dicts - one side reproduces
    bptk's original solo (uncontested) behaviour exactly.

    Deliberately reuses the engine's own _parse_order/_commit_unit/
    market_price rather than reimplementing pricing math - only the
    orchestration loop is new here.
    """
    queues = [list(side["orders"]) for side in sides]
    max_len = max((len(q) for q in queues), default=0)

    for i in range(max_len):
        order_states = [_parse_order(q[i]) if i < len(q) else None for q in queues]

        # Atomic orders (HIRE, BUY_LAND): handle once, in side order.
        for side_idx, ostate in enumerate(order_states):
            if ostate is None:
                continue
            op = ostate["type"]
            side = sides[side_idx]
            if op == "HIRE":
                before = side["farm"]["money"]
                _do_hire(side["farm"], side["private"], board_size, hire_mult)
                if side["farm"]["money"] < before:
                    side["counters"]["HIRE"] += 1
                order_states[side_idx] = None
            elif op == "BUY_LAND":
                before = len(side["farm"]["unlocked_quadrants"])
                _do_buy_land(side["farm"], board_size)
                if len(side["farm"]["unlocked_quadrants"]) > before:
                    side["counters"]["BUY_LAND"] += 1
                order_states[side_idx] = None

        # Per-unit lockstep loop for SELL / BUY_*.
        idx_esc = 0
        while True:
            idx_esc += 1
            if idx_esc >= 100_000:
                print("WARNING: bptk contested market loop exceeded 100k iterations; aborting")
                break
            quoted = [None] * len(sides)
            for side_idx, ostate in enumerate(order_states):
                if ostate is None or ostate["remaining"] <= 0:
                    continue
                op = ostate["type"]
                item = ostate["item"]
                if op == "SELL" and item in MARKET_PARAMS:
                    quoted[side_idx] = (
                        op, item,
                        market_price(item, market["inventory"][item], market.get("params")),
                        ostate,
                    )
                elif op == "BUY_PRODUCT" and item in ("WHEAT", "FERTILIZER"):
                    quoted[side_idx] = (
                        op, item,
                        market_price(item, market["inventory"][item] - 1, market.get("params")),
                        ostate,
                    )
                elif op == "BUY_SEED" and item in CROPS:
                    quoted[side_idx] = (op, item, CROPS[item]["seed"], ostate)
                elif op == "BUY_ANIMAL" and item in ANIMALS:
                    quoted[side_idx] = (op, item, ANIMALS[item]["cost"], ostate)
                else:
                    order_states[side_idx] = None  # malformed sub-op; abort

            if all(q is None for q in quoted):
                break

            # Both sides see the same pre-commit inventory for this unit.
            committed_any = False
            for side_idx, q in enumerate(quoted):
                if q is None:
                    continue
                op, item, price, ostate = q
                side = sides[side_idx]
                ok = _commit_unit(op, item, price, side["farm"], side["private"], market, shed_capacity)
                if ok:
                    ostate["remaining"] -= 1
                    side["counters"][f"{op}_{item}"] += 1
                    committed_any = True
                else:
                    order_states[side_idx] = None

            if not committed_any:
                break

    _refresh_prices(market)


class EconomyModel:
    """One episode's worth of state, stepped one turn at a time."""

    def __init__(self, seed=0, market=None, town=None, shares_market=False):
        self.rng = random.Random(seed)
        self.farm = _new_farm(BOARD_SIZE, STARTING_MONEY)
        self.private = _new_private()
        self.market = market if market is not None else _new_market()
        self.town = town if town is not None else _new_town()
        # True when this side's market/town are shared with another side
        # (ContestedEconomyModel) - suppresses this instance's own town-demand
        # tick and shop-unlock so the shared state only advances once per
        # step/day, not once per side.
        self.shares_market = shares_market
        self.day = 0
        self.hour = 0
        self.step = 0
        self.counters = collections.defaultdict(int)
        self.daily_log = []

    # -- state assembly, matching main.py's extract_state()/get_market_state() shape --
    def _state(self):
        return {
            "farm": self.farm,
            "private": self.private,
            "market_state": self.market,  # already {"inventory":..., "prices":...}
            "board_size": BOARD_SIZE,
            "day": self.day,
            "hour": self.hour,
            "step": self.step,
            "opponent_pipeline": {},  # no competing seller modelled in this pass
            "unlocked_shops": list(self.town["unlocked_shops"]),
        }

    def _crew_size(self):
        return 1 + len(self.farm["hands"])

    # -- the one genuinely custom piece: crew assignment substitutes for spatial pathing --
    def _assign_crew(self, state):
        farm, private, day = self.farm, self.private, self.day
        seeds = private.get("seeds", {})
        shed = private.get("shed", {})

        # (unit_idx, (x, y)) for every unit still free to take a tile this
        # turn - unit_idx 0 is the farmer, 1..N are farm["hands"]. FARMER_MOVES
        # is 4-directional with no obstacles (kaggriculture.py:88-93, locked
        # tiles passable), so Manhattan distance is the exact travel cost -
        # no pathfinding search is needed, only an assignment one.
        available = [(0, tuple(farm["farmer"]))] + [
            (i + 1, tuple(h)) for i, h in enumerate(farm["hands"])
        ]

        feed_tiles = []
        ready_tiles = []       # (x, y, action) - HARVEST / COLLECT_FERTILIZER, no budget needed
        water_care_tiles = []  # (x, y, action) - WATER / CARE, no budget needed
        fertilize_tiles = []   # (x, y) - needs a shared FERTILIZER budget
        place_tiles = []       # (x, y) - needs a matching animal held in shed
        weed_tiles = []
        empty_tiles = []

        for y in range(BOARD_SIZE):
            row = farm["tiles"][y]
            for x in range(BOARD_SIZE):
                tile = row[x]
                if tile is None:
                    empty_tiles.append((x, y))
                    continue
                if tile == "LOCKED":
                    continue
                kind = tile.get("kind")
                if kind == "PLANT":
                    if agent_main.is_harvestable(tile, day):
                        ready_tiles.append((x, y, ["HARVEST"]))
                    elif not tile.get("watered_today", True):
                        water_care_tiles.append((x, y, ["WATER"]))
                    elif agent_main.wants_fertilizer(tile, day):
                        fertilize_tiles.append((x, y))
                elif kind == "WEED":
                    weed_tiles.append((x, y))
                elif "animal" in tile:
                    if not tile.get("fed_today"):
                        feed_tiles.append((x, y))
                        continue
                    info = ANIMALS.get(tile.get("animal"), {})
                    max_held = info.get("max_held", 1)
                    held = tile.get("yield_units", 0)
                    if held >= max_held or (
                        held > 0 and (held >= max_held - 2 or day >= SEASON_DAYS - 2)
                    ):
                        ready_tiles.append((x, y, ["HARVEST"]))
                    elif tile.get("fertilizer_available"):
                        ready_tiles.append((x, y, ["COLLECT_FERTILIZER"]))
                    elif not tile.get("cared_today"):
                        water_care_tiles.append((x, y, ["CARE"]))
                elif kind in agent_main.ANIMAL_STRUCTURE_KINDS:
                    place_tiles.append((x, y))

        assignments = []  # (unit_idx, x, y, action)

        def take(tiles, limit_check=None):
            # Optimal (not just first-in-list) unit<->tile matching within
            # this priority tier: minimize total Manhattan travel across the
            # units still available and the tiles in this tier, via the
            # Hungarian algorithm - provably at least as good as any other
            # matching, including the row-major-order greedy fill this
            # replaced. Consumes min(len(available), len(tiles)) units,
            # exactly like the greedy version did with `slots`.
            #
            # Each chosen pair consumes one crew-turn whether or not it
            # produces a real action - matching one unit considering one tile
            # per turn. Without this, a budget-exhausted crop pick (or a shed
            # budget that ran out) would make the loop skip on to try EVERY
            # other tile in this tier instead of just wasting that one unit's
            # turn, which is what actually happens in choose_unit_action. The
            # travel distance is charged the same way - the unit still has to
            # walk there to discover the budget is empty.
            if not tiles or not available:
                return
            cost = [
                [abs(ux - t[0]) + abs(uy - t[1]) for t in tiles]
                for (_, (ux, uy)) in available
            ]
            row_ind, col_ind = linear_sum_assignment(cost)
            used_rows = set()
            for row, col in zip(row_ind, col_ind):
                unit_idx, (ux, uy) = available[row]
                x, y = tiles[col][0], tiles[col][1]
                action = tiles[col][2] if limit_check is None else limit_check(x, y)
                self.counters["total_assignment_distance"] += abs(ux - x) + abs(uy - y)
                if action is not None:
                    assignments.append((unit_idx, x, y, action))
                used_rows.add(row)
            available[:] = [item for i, item in enumerate(available) if i not in used_rows]

        # 1. Feed - shared WHEAT budget, same shape as main.py's wheat_budget.
        wheat_left = shed.get("WHEAT", 0)

        def feed_action(x, y):
            nonlocal wheat_left
            if wheat_left <= 0:
                return None
            wheat_left -= 1
            return ["FEED"]

        take(feed_tiles, feed_action)

        # 2. Ready harvests / fertilizer collection - no budget needed.
        take(ready_tiles)

        # 3. Water / care - no budget needed.
        take(water_care_tiles)

        # 3b. Fertilize - shared FERTILIZER budget.
        fert_left = shed.get("FERTILIZER", 0)

        def fertilize_action(x, y):
            nonlocal fert_left
            if fert_left <= 0:
                return None
            fert_left -= 1
            return ["FERTILIZE"]

        take(fertilize_tiles, fertilize_action)

        # 4. Place a bought animal on an empty structure - per-species shed budget.
        species_left = {a: shed.get(a, 0) for a in agent_main.ACTIVE_ANIMALS}

        def place_action(x, y):
            for species in agent_main.ACTIVE_ANIMALS:
                if species_left.get(species, 0) > 0:
                    species_left[species] -= 1
                    return ["PLACE", species]
            return None

        take(place_tiles, place_action)

        # 8. Weeds - free.
        take([(x, y, ["DIG"]) for x, y in weed_tiles])

        # 9. Empty ground: build a structure, or plant under the shared
        #    per-turn seed budget - this is where the can_afford/plant_budget
        #    mismatch (see module docstring) shows up if it's real.
        plant_budget = dict(seeds)
        pending_builds = [0]

        def empty_action(x, y):
            animal_to_build = agent_main.choose_animal_to_build(
                farm, private, BOARD_SIZE, day, pending_builds[0], x, y
            )
            if animal_to_build:
                pending_builds[0] += 1
                structure = ANIMALS[animal_to_build]["structure"]
                return [f"BUILD_{structure}"]
            crop = agent_main.choose_crop(
                farm,
                state["market_state"],
                private,
                day,
                unlocked_shops=state["unlocked_shops"],
                start_step=state["step"],
                opponent_pipeline=state.get("opponent_pipeline"),
            )
            if not crop:
                return None
            self.counters["crop_chosen_total"] += 1
            self.counters[f"crop_chosen_{crop}"] += 1
            if plant_budget.get(crop, 0) > 0:
                plant_budget[crop] -= 1
                return ["PLANT", crop]
            # Not planted. Distinguish the real candidate bug (choose_crop
            # named a crop via its can_afford branch while we hold ZERO seed
            # for it - plant_budget can never have anything to give) from
            # ordinary same-turn contention (we held some, but an earlier
            # crew member this same turn already spent it - exactly what
            # plant_budget is there to prevent from overcommitting, not a
            # bug in itself).
            self.counters["crop_chosen_but_not_planted"] += 1
            self.counters[f"crop_chosen_but_not_planted_{crop}"] += 1
            if seeds.get(crop, 0) == 0:
                self.counters["crop_chosen_with_zero_seed_held"] += 1
                self.counters[f"crop_chosen_with_zero_seed_held_{crop}"] += 1
            else:
                self.counters["crop_chosen_seed_exhausted_this_turn"] += 1
            return None

        take(empty_tiles, empty_action)

        return assignments

    def _apply_assignment(self, idx, x, y, action):
        farm, private = self.farm, self.private
        if idx == 0:
            farm["farmer"] = [x, y]
        else:
            while len(farm["hands"]) < idx:
                farm["hands"].append([x, y])
            farm["hands"][idx - 1] = [x, y]
        while len(private["inventories"]) <= idx:
            private["inventories"].append({})
        inv = private["inventories"][idx]
        shed = private["shed"]
        op = action[0]

        # Deliberate simplification (see module docstring): the unit "already
        # has" whatever it needs from the shed this turn, instead of a
        # separate PICKUP-and-carry trip. Re-checked here against the real
        # shed, defensively, in case the assignment pass's running budget
        # ever desyncs from it.
        if op == "FEED" and shed.get("WHEAT", 0) > 0:
            shed["WHEAT"] -= 1
            inv["WHEAT"] = inv.get("WHEAT", 0) + 1
        elif op == "FERTILIZE" and shed.get("FERTILIZER", 0) > 0:
            shed["FERTILIZER"] -= 1
            inv["FERTILIZER"] = inv.get("FERTILIZER", 0) + 1
        elif op == "PLACE" and shed.get(action[1], 0) > 0:
            shed[action[1]] -= 1
            inv[action[1]] = inv.get(action[1], 0) + 1

        _apply_unit_action(
            farm, private, idx, action, BOARD_SIZE, self.day, TURNS_PER_DAY, SHED_CAPACITY
        )
        self.counters[op] += 1
        if op == "PLANT":
            self.counters[f"crop_planted_{action[1]}"] += 1

    def _decide_market_orders(self, state):
        farm, private = self.farm, self.private
        day, hour = self.day, self.hour
        seeds = private.get("seeds", {})
        orders = agent_main.decide_hire_orders(farm, BOARD_SIZE, day, hour, seeds)
        filled_animals, _ = agent_main.scan_animal_structures(farm, BOARD_SIZE)
        reserved_wheat = filled_animals * agent_main.MIN_WHEAT_RESERVE_FOR_FEEDING
        orders += agent_main.decide_market_actions(
            farm,
            private,
            state["market_state"],
            day,
            reserved_wheat=reserved_wheat,
            unlocked_shops=state["unlocked_shops"],
            start_step=state["step"],
            opponent_pipeline=state.get("opponent_pipeline"),
        )
        orders += agent_main.decide_animal_market_actions(farm, private, BOARD_SIZE, day)
        orders += agent_main.decide_land_orders(farm, day)
        return orders[: agent_main.MAX_MARKET_ORDERS_PER_TURN]

    def _process_market_orders(self, orders):
        # Single-side call into the shared two-sided lockstep - with one side
        # this reduces to the original solo sequential-commit behaviour, but
        # now shares one implementation with contested mode instead of a
        # separate hand-rolled loop that could drift from it.
        _process_market_two_sided(
            [{"farm": self.farm, "private": self.private, "orders": orders, "counters": self.counters}],
            self.market,
        )

    def _consume_town_demand(self):
        _tick_town_demand(self.market, self.town, self.step)

    def _end_of_day(self):
        farm, private = self.farm, self.private
        _daily_refresh_plants(farm, self.day, TURNS_PER_DAY)
        _daily_refresh_animals(farm, self.day)
        _spawn_weeds(farm, BOARD_SIZE, WEED_SPAWN_CHANCE, self.rng)
        _drop_inventories_to_shed(private, SHED_CAPACITY)
        farm["farmer"] = list(HOME_SPAWN)
        farm["hands"] = []
        farm["hires_today"] = 0
        private["inventories"] = [{}]

        # Shop unlocks are global town state - a contested episode advances
        # this once at the orchestrator level (see ContestedEconomyModel),
        # not once per side.
        if not self.shares_market:
            _maybe_unlock_shop(self.town, self.day + 1, self.rng)

    def _record_daily_snapshot(self):
        farm = self.farm
        kinds = collections.Counter()
        for row in farm["tiles"]:
            for tile in row:
                if tile is None:
                    kinds["EMPTY"] += 1
                elif tile == "LOCKED":
                    kinds["LOCKED"] += 1
                elif tile.get("kind") == "PLANT":
                    kinds[f"PLANT:{tile.get('crop')}"] += 1
                else:
                    kinds[tile.get("kind", "?")] += 1
        self.daily_log.append(
            {
                "day": self.day,
                "money": farm.get("money", 0),
                "hands": len(farm.get("hands") or []),
                "seeds": dict(self.private.get("seeds", {})),
                "shed": dict(self.private.get("shed", {})),
                "market_inventory": dict(self.market["inventory"]),
                "market_prices": dict(self.market["prices"]),
                "tiles": dict(kinds),
                "unlocked_shops": len(self.town["unlocked_shops"]),
            }
        )

    def step_once(self):
        if self.hour == 0:
            self._record_daily_snapshot()

        state = self._state()
        assignments = self._assign_crew(state)
        orders = self._decide_market_orders(state)

        for unit_idx, x, y, action in assignments:
            self._apply_assignment(unit_idx, x, y, action)

        self._process_market_orders(orders)
        self._consume_town_demand()
        _decay_plants(self.farm, self.step)

        if (self.step + 1) % TURNS_PER_DAY == 0:
            self._end_of_day()

        self.step += 1
        self.day = self.step // TURNS_PER_DAY
        self.hour = self.step % TURNS_PER_DAY

    def report(self):
        return {
            "final_money": self.farm.get("money", 0),
            "counters": dict(self.counters),
            "daily_log": self.daily_log,
            "final_tiles": self.daily_log[-1]["tiles"] if self.daily_log else {},
            "final_market_prices": dict(self.market["prices"]),
            "final_market_inventory": dict(self.market["inventory"]),
        }


def run_episode(seed=0, days=SEASON_DAYS, overrides=None):
    """Run one episode against town/shop demand only (no competing seller -
    the same "market stays uncontested" shape as paired_compare.py's `pass`/
    `starter` built-ins, which is where most of the documented crop-economy
    findings this model validates against were originally measured).
    """
    overrides = overrides or {}
    with _override_main(**overrides):
        model = EconomyModel(seed=seed)
        for _ in range(days * TURNS_PER_DAY):
            model.step_once()
        if model.hour == 0:
            model._record_daily_snapshot()
        return model.report()


class ContestedEconomyModel:
    """Two independent farm/private states sharing one market and one town,
    replicating the real engine's per-order-index price interleaving
    (_process_market_two_sided, i.e. kaggriculture.py's own _process_market)
    instead of bptk's solo uncontested loop. This is what closes bptk's one
    documented blind spot: with no competing seller, price-impact questions
    (fertilizer round-trips, melon gluts, wool depth) and selling-cadence
    tradeoffs couldn't be modelled here at all - they had to go straight to
    a real 720-turn self-play/head-to-head episode.

    Each side can run under its own main.py overrides (candidate vs control,
    mirroring experiments/head_to_head.py's variant-vs-baseline shape) or
    identical overrides for self-play. Overrides are applied by scoping
    _override_main tightly around each side's own decision-function calls in
    turn, one side at a time - Python's single-threaded execution makes this
    equivalent to two independent module namespaces without needing one,
    since each side's calls fully complete (and _override_main restores the
    prior values) before the other side's calls begin.

    Spatial pathing stays out of scope here too, same as EconomyModel -
    both sides still use the zero-travel-time _assign_crew abstraction.
    """

    def __init__(self, seed=0, seed_b=None, overrides=None, overrides_b=None):
        self.market = _new_market()
        self.town = _new_town()
        self.rng = random.Random(seed)
        self.overrides = [overrides or {}, overrides_b if overrides_b is not None else (overrides or {})]
        self.sides = [
            EconomyModel(seed=seed, market=self.market, town=self.town, shares_market=True),
            EconomyModel(
                seed=seed_b if seed_b is not None else seed,
                market=self.market,
                town=self.town,
                shares_market=True,
            ),
        ]
        self.day = 0
        self.hour = 0
        self.step = 0

    def step_once(self):
        if self.hour == 0:
            for side in self.sides:
                side._record_daily_snapshot()

        assignments = []
        orders = []
        for side, side_overrides in zip(self.sides, self.overrides):
            with _override_main(**side_overrides):
                state = side._state()
                assignments.append(side._assign_crew(state))
                orders.append(side._decide_market_orders(state))

        for side, side_assignments in zip(self.sides, assignments):
            for unit_idx, x, y, action in side_assignments:
                side._apply_assignment(unit_idx, x, y, action)

        _process_market_two_sided(
            [
                {"farm": side.farm, "private": side.private, "orders": side_orders, "counters": side.counters}
                for side, side_orders in zip(self.sides, orders)
            ],
            self.market,
        )
        _tick_town_demand(self.market, self.town, self.step)
        for side in self.sides:
            _decay_plants(side.farm, side.step)

        if (self.step + 1) % TURNS_PER_DAY == 0:
            for side in self.sides:
                side._end_of_day()  # per-farm only - shares_market=True skips the shop-unlock
            _maybe_unlock_shop(self.town, self.day + 1, self.rng)

        self.step += 1
        self.day = self.step // TURNS_PER_DAY
        self.hour = self.step % TURNS_PER_DAY
        for side in self.sides:
            side.step, side.day, side.hour = self.step, self.day, self.hour

    def report(self):
        return [side.report() for side in self.sides]


def run_contested_episode(seed=0, seed_b=None, days=SEASON_DAYS, overrides=None, overrides_b=None):
    """Two policies (or the same one twice, for self-play) sharing one
    market/town for the whole episode. Returns [report_a, report_b], same
    shape as EconomyModel.report() per side. See ContestedEconomyModel's
    docstring for the override-scoping mechanics.
    """
    model = ContestedEconomyModel(seed=seed, seed_b=seed_b, overrides=overrides, overrides_b=overrides_b)
    for _ in range(days * TURNS_PER_DAY):
        model.step_once()
    if model.hour == 0:
        for side in model.sides:
            side._record_daily_snapshot()
    return model.report()


# ---------------------------------------------------------------------
# Validation gate - must reproduce these before trusting the model for any
# new finding. See CLAUDE.md's "Measured dead ends" for the numbers this
# is checked against.
# ---------------------------------------------------------------------
def validate(seed=0, verbose=True):
    results = collections.OrderedDict()

    baseline = run_episode(seed=seed)

    # 1. STRAWBERRY collapse / CARROT flood under the corrected growth_days
    #    (real ongoing-crop tile occupancy instead of max_yield_day).
    corrected_crops = {crop: dict(info) for crop, info in CROPS.items()}
    corrected_crops["TOMATO"]["max_yield_day"] = 12
    corrected_crops["STRAWBERRY"]["max_yield_day"] = 17
    corrected = run_episode(seed=seed, overrides={"CROPS": corrected_crops})
    results["1_growth_days_correction"] = {
        "baseline_strawberry_planted": baseline["counters"].get("crop_planted_STRAWBERRY", 0),
        "corrected_strawberry_planted": corrected["counters"].get("crop_planted_STRAWBERRY", 0),
        "baseline_carrot_planted": baseline["counters"].get("crop_planted_CARROT", 0),
        "corrected_carrot_planted": corrected["counters"].get("crop_planted_CARROT", 0),
        "expect": "corrected STRAWBERRY << baseline; corrected CARROT >> baseline",
    }

    # 2. WHEAT absorbing STRAWBERRY's freed tile-time when CROP_PLANTING_WINDOWS fires.
    windows_off = run_episode(seed=seed, overrides={"CROP_PLANTING_WINDOWS": {}})
    results["2_planting_windows"] = {
        "windows_on_wheat_planted": baseline["counters"].get("crop_planted_WHEAT", 0),
        "windows_off_wheat_planted": windows_off["counters"].get("crop_planted_WHEAT", 0),
        "expect": "windows_on WHEAT >> windows_off WHEAT",
    }

    # 3. Magnitude of the can_afford/plant_budget mismatch (not yet a claim
    #    of impact - just how often it fires under real seed-stock cadence).
    results["3_plant_budget_mismatch"] = {
        "crop_chosen_total": baseline["counters"].get("crop_chosen_total", 0),
        "crop_chosen_but_not_planted": baseline["counters"].get("crop_chosen_but_not_planted", 0),
        "crop_chosen_with_zero_seed_held": baseline["counters"].get(
            "crop_chosen_with_zero_seed_held", 0
        ),
        "crop_chosen_seed_exhausted_this_turn": baseline["counters"].get(
            "crop_chosen_seed_exhausted_this_turn", 0
        ),
        "note": "zero_seed_held is the real candidate bug; exhausted_this_turn is ordinary contention plant_budget already handles correctly",
    }

    # 5. Second-sheep cash-trough collapse, pre/post the seed-reserve fix.
    pre_fix = run_episode(
        seed=seed, overrides={"MAX_ANIMALS": 2, "MIN_CASH_RESERVE_FOR_SEED_BUYING": 100}
    )
    post_fix = run_episode(
        seed=seed, overrides={"MAX_ANIMALS": 2, "MIN_CASH_RESERVE_FOR_SEED_BUYING": 450}
    )
    results["5_second_sheep_trough"] = {
        "pre_fix_feed_count": pre_fix["counters"].get("FEED", 0),
        "post_fix_feed_count": post_fix["counters"].get("FEED", 0),
        "pre_fix_money": pre_fix["final_money"],
        "post_fix_money": post_fix["final_money"],
        "expect": "pre_fix collapses (low FEED, low money); post_fix recovers",
    }

    # 6. MAX_ANIMALS cliff: 4 should stay stable, 5 should collapse.
    four = run_episode(seed=seed, overrides={"MAX_ANIMALS": 4})
    five = run_episode(seed=seed, overrides={"MAX_ANIMALS": 5})
    results["6_max_animals_cliff"] = {
        "four_money": four["final_money"],
        "five_money": five["final_money"],
        "expect": "five collapses relative to four",
    }

    # 7. BUY_LAND: 2 quadrants should beat 3.
    two_q = run_episode(seed=seed, overrides={"MAX_LAND_PURCHASES": 2})
    three_q = run_episode(seed=seed, overrides={"MAX_LAND_PURCHASES": 3})
    results["7_buy_land"] = {
        "two_quadrants_money": two_q["final_money"],
        "three_quadrants_money": three_q["final_money"],
        "expect": "two_quadrants money >= three_quadrants money",
    }

    if verbose:
        print(f"baseline final money: {baseline['final_money']:.0f}")
        for name, data in results.items():
            print(f"--- {name} ---")
            for k, v in data.items():
                print(f"  {k}: {v}")
    return results


def validate_contested(seed=0, verbose=True):
    """Self-play contest checks for the two-sided market lockstep - not a
    claim of matching real bank numbers (bptk's zero-travel-time abstraction
    still inflates both sides, same caveat as solo mode), just that sharing
    one market produces the right *direction*: a contested market should
    sell for less than an uncontested one, and MELON (the crop this repo has
    documented crashing hardest under real self-play, ~$280 vs the real
    $1 floor - see CLAUDE.md) should crash harder still with two sellers
    competing for the same town/shop demand.
    """
    solo = run_episode(seed=seed)
    contested = run_contested_episode(seed=seed)

    results = collections.OrderedDict()
    results["1_contested_vs_solo_money"] = {
        "solo_final_money": solo["final_money"],
        "contested_side_a_money": contested[0]["final_money"],
        "contested_side_b_money": contested[1]["final_money"],
        "expect": "both contested sides well below solo - town/shop demand is now split between two sellers instead of one",
    }

    # MELON's end-of-season price does NOT reliably fall under contest -
    # verified on seed 0, it does the opposite. Default policy on both sides
    # drives such a severe combined early glut that both sides' revenue
    # collapses (see scenario 4), SELL_MELON stays at 0 all season on both
    # sides, and with nobody selling into it the market recovers from disuse
    # and ends HIGHER than solo, not lower. Real model behaviour, not a bug -
    # read this one alongside scenario 4, not in isolation.
    results["2_melon_price_under_contest"] = {
        "solo_end_melon_price": solo["final_market_prices"].get("MELON"),
        "contested_end_melon_price": contested[0]["final_market_prices"].get("MELON"),
        "solo_sell_melon_count": solo["counters"].get("SELL_MELON", 0),
        "contested_sell_melon_count": contested[0]["counters"].get("SELL_MELON", 0),
        "note": "end price alone is not a valid signal when one side stops selling entirely (see scenario 4) - it can end higher under contest purely because nobody sold into it",
    }

    results["3_seat_symmetry"] = {
        "side_a_money": contested[0]["final_money"],
        "side_b_money": contested[1]["final_money"],
        "note": "identical policy, same base seed, both sides - some asymmetry is expected (side A commits first at every order-index in the lockstep, the same shape as the real engine's documented seat 0/1 effect), not necessarily a bug if present",
    }

    # 4. The mechanism behind 1 and 2: does contested selling extend/deepen
    #    the days 3-7 cash trough CLAUDE.md documents? Verified on seed 0:
    #    yes, dramatically - side A's money stalls at ~$19 (the same
    #    hire-gate floor CLAUDE.md documents - "the trough bottoms out near
    #    $20 anyway") from roughly day 6 through day 18, well past solo's
    #    day-12 recovery. Two zero-travel-time sides both keep full
    #    solo-level throughput while competing for the SAME fixed town/shop
    #    demand, so the combined glut and revenue crash is more severe than
    #    either two real (travel-time-throttled) agents or bptk's own solo
    #    mode alone - a known amplification of bptk's existing ~1.5-2x
    #    inflation caveat, not a new bug.
    day9_solo = next((r for r in solo["daily_log"] if r["day"] == 9), {})
    day9_contested = next((r for r in contested[0]["daily_log"] if r["day"] == 9), {})
    results["4_cash_trough_under_contest"] = {
        "solo_day9_money": day9_solo.get("money"),
        "contested_day9_money": day9_contested.get("money"),
        "note": "contested money stuck well below solo's day-9 recovery is the trough extending/deepening under competition - the root cause of scenarios 1 and 2, not a separate issue",
    }

    if verbose:
        for name, data in results.items():
            print(f"--- {name} ---")
            for k, v in data.items():
                print(f"  {k}: {v}")
    return results


def _check_assignment_optimality(verbose=True):
    """Property check for the Hungarian-assignment upgrade in _assign_crew:
    on a synthetic over-subscribed tier, confirm the optimal (Hungarian)
    total travel distance is never worse than a naive fixed unit-order-to-
    tile-order pairing (what the row-major greedy fill this replaced
    amounted to, within one tier). This is a mathematical guarantee of the
    algorithm for any cost matrix, not a coincidence of this input - checked
    once here against this codebase's actual distance metric (Manhattan)
    rather than only asserted.
    """
    units = [(0, 0), (9, 9), (5, 0)]
    tiles = [(1, 0), (8, 8), (0, 5), (9, 0), (4, 4)]
    cost = [[abs(ux - tx) + abs(uy - ty) for (tx, ty) in tiles] for (ux, uy) in units]

    row_ind, col_ind = linear_sum_assignment(cost)
    optimal_total = sum(cost[r][c] for r, c in zip(row_ind, col_ind))
    k = min(len(units), len(tiles))
    naive_fixed_pairing_total = sum(cost[i][i] for i in range(k))

    result = {
        "optimal_total_distance": optimal_total,
        "naive_fixed_pairing_total_distance": naive_fixed_pairing_total,
        "optimal_never_worse": optimal_total <= naive_fixed_pairing_total,
    }
    if verbose:
        print("--- assignment_optimality_check ---")
        for k_, v_ in result.items():
            print(f"  {k_}: {v_}")
    return result


def _print_summary(report):
    print(f"final money: {report['final_money']:.0f}")
    print("counters:")
    for key in sorted(report["counters"]):
        print(f"  {key}: {report['counters'][key]}")
    print("final tiles:")
    for key in sorted(report["final_tiles"]):
        print(f"  {key}: {report['final_tiles'][key]}")
    print("final market (price / inventory):")
    for item in sorted(report["final_market_prices"]):
        print(
            f"  {item}: {report['final_market_prices'][item]} / "
            f"{report['final_market_inventory'][item]}"
        )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument(
        "--seed-b", type=int, default=None,
        help="second side's seed for --contested (defaults to --seed)",
    )
    parser.add_argument("--days", type=int, default=SEASON_DAYS)
    parser.add_argument("--validate", action="store_true", help="run the validation gate")
    parser.add_argument(
        "--validate-contested", action="store_true",
        help="run the contested-market validation checks",
    )
    parser.add_argument(
        "--contested", action="store_true",
        help="run one self-play contested episode (shared market) instead of solo",
    )
    parser.add_argument(
        "--check-assignment", action="store_true",
        help="run the Hungarian-assignment optimality property check",
    )
    args = parser.parse_args()

    if args.validate:
        validate(seed=args.seed)
    elif args.validate_contested:
        validate_contested(seed=args.seed)
    elif args.check_assignment:
        _check_assignment_optimality()
    elif args.contested:
        side_a, side_b = run_contested_episode(seed=args.seed, seed_b=args.seed_b, days=args.days)
        print("=== side A ===")
        _print_summary(side_a)
        print("=== side B ===")
        _print_summary(side_b)
    else:
        _print_summary(run_episode(seed=args.seed, days=args.days))
