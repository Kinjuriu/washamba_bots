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
abstraction, not an attempt to reproduce real per-episode turn counts.

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
    .venv/Scripts/python.exe bptk.py                  # one baseline episode
    .venv/Scripts/python.exe bptk.py --validate        # the validation gate
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
)

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


class EconomyModel:
    """One episode's worth of state, stepped one turn at a time."""

    def __init__(self, seed=0):
        self.rng = random.Random(seed)
        self.farm = _new_farm(BOARD_SIZE, STARTING_MONEY)
        self.private = _new_private()
        self.market = _new_market()
        self.town = _new_town()
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
        slots = self._crew_size()

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

        assignments = []

        def take(tiles, limit_check=None):
            # Each item consumes one crew-turn whether or not it produces a
            # real action - matching one unit considering one tile per turn.
            # Without this, a budget-exhausted crop pick (or a shed budget
            # that ran out) would make the loop skip on to try EVERY other
            # tile in this tier instead of just wasting that one unit's turn,
            # which is what actually happens in choose_unit_action.
            nonlocal slots
            for item in tiles:
                if slots <= 0:
                    return
                slots -= 1
                x, y = item[0], item[1]
                action = item[2] if limit_check is None else limit_check(x, y)
                if action is not None:
                    assignments.append((x, y, action))

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
        farm, private, market = self.farm, self.private, self.market

        atomic = [o for o in orders if isinstance(o, list) and o and o[0] in ("HIRE", "BUY_LAND")]
        unit_priced = [
            o for o in orders if isinstance(o, list) and o and o[0] not in ("HIRE", "BUY_LAND")
        ]

        for order in atomic:
            if order[0] == "HIRE":
                before = farm["money"]
                _do_hire(farm, private, BOARD_SIZE, FARM_HAND_COST_MULT)
                if farm["money"] < before:
                    self.counters["HIRE"] += 1
            elif order[0] == "BUY_LAND":
                before = len(farm["unlocked_quadrants"])
                _do_buy_land(farm, BOARD_SIZE)
                if len(farm["unlocked_quadrants"]) > before:
                    self.counters["BUY_LAND"] += 1

        for order in unit_priced:
            op = order[0]
            if len(order) < 3:
                continue
            item = order[1]
            try:
                remaining = int(order[2])
            except (TypeError, ValueError):
                continue
            while remaining > 0:
                if op == "SELL" and item in MARKET_PARAMS:
                    price = market_price(item, market["inventory"][item], market.get("params"))
                elif op == "BUY_PRODUCT" and item in ("WHEAT", "FERTILIZER"):
                    price = market_price(
                        item, market["inventory"][item] - 1, market.get("params")
                    )
                elif op == "BUY_SEED" and item in CROPS:
                    price = CROPS[item]["seed"]
                elif op == "BUY_ANIMAL" and item in ANIMALS:
                    price = ANIMALS[item]["cost"]
                else:
                    break
                if not _commit_unit(op, item, price, farm, private, market, SHED_CAPACITY):
                    break
                remaining -= 1
                self.counters[f"{op}_{item}"] += 1
        _refresh_prices(market)

    def _consume_town_demand(self):
        market = self.market
        step = self.step
        if step % SHOP_SELL_INTERVAL == 0:
            for shop_name in self.town["unlocked_shops"]:
                products = SHOPS[shop_name]
                multiplier = 2 if len(products) == 1 else 1
                for item in products:
                    market["inventory"][item] -= multiplier
        if step % CENTER_SELL_INTERVAL == 0:
            for item in TOWN_CENTER_PRODUCTS:
                market["inventory"][item] -= 1
        _refresh_prices(market)

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

        next_day = self.day + 1
        if next_day > 0 and next_day % SHOP_UNLOCK_INTERVAL == 0:
            if len(self.town["unlocked_shops"]) < MAX_SHOP_INSTANCES:
                self.town["unlocked_shops"].append(self.rng.choice(sorted(SHOPS)))

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

        for idx, (x, y, action) in enumerate(assignments):
            self._apply_assignment(idx, x, y, action)

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
    parser.add_argument("--days", type=int, default=SEASON_DAYS)
    parser.add_argument("--validate", action="store_true", help="run the validation gate")
    args = parser.parse_args()

    if args.validate:
        validate(seed=args.seed)
    else:
        _print_summary(run_episode(seed=args.seed, days=args.days))
