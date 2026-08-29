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

# ---------------------------------------------------------------------
# Path C Core - reproduced from mydocs/PATH_C_CORE.md, research done in a
# separate environment. Nothing under this heading existed in bptk.py
# before this pass (verified: no PATH_C_* / run_path_c / path_c_overrides
# anywhere in this repo's history on any branch) - treat every number this
# produces as a first faithful-to-spec implementation, not a re-run of an
# already-verified result. See compare_path_c/compare_path_c_ladder below.
# ---------------------------------------------------------------------
PATH_C_EARLY_ANIMALS = 3
PATH_C_EARLY_DAY_LIMIT = 8
PATH_C_STRAW_CAP = 50
PATH_C_STRAW_WINDOW_END = 14
PATH_C_SCALE_MAX_ANIMALS = 10
PATH_C_SCALE_STRAW_DONE = 50
PATH_C_SCALE_DAY = 15
PATH_C_LEVEL2_CREW = True
PATH_C_L2_STRAW_TILES = 30
PATH_C_L2_MIN_ANIMALS = 6
PATH_C_HIRE_BUMP_CEILING = 10
PATH_C_HIRE_BUMP_MIN_DAY = 12
PATH_C_HIRE_BUMP_MIN_MONEY = 1500
PATH_C_MELON_PAUSE_DAY = 0  # core = off; the experimental melon-pause arm is not reproduced here
PATH_C_GATE_FERT_SELL = True
# Not in PATH_C_CORE.md's constants table - the doc's prose names "3" as the
# fertilize-elevation trigger ("After >=3 animals on tiles"); pulled out as
# its own named constant here rather than left as a bare literal.
PATH_C_FERT_ELEVATE_MIN_ANIMALS = 3
# Fix pass (mydocs/Path C System Dynamics Diagnosis.md), off by default so the
# broken core-C control stays byte-reproducible; ladder arms turn these on.
# PIN_WHEAT_VALVE: fix #1 - the STRAW pin only fires while shed+carried WHEAT
#   >= MIN_WHEAT_RESERVE_FOR_FEEDING * (owned_animals + 1); below that it falls
#   through to normal choose_crop, which can pick WHEAT on its own glut-aware
#   terms. Restores the pin's missing connector to the feed subsystem.
# SCALE_WHEAT_BUFFER: fix #2 - replaces the toothless "wheat_stock > 0" scale
#   check. None = the original broken check (control); a number N requires
#   stock >= MIN_WHEAT_RESERVE_FOR_FEEDING * N before the cap may jump to
#   scale_max; "owned" keys the same requirement to owned+1 instead of
#   scale_max - the F8 guard, since 2*10=20 may be unreachable while the valve
#   sawtooths around 2*(owned+1)=8 and the herd would stick at the beach-head.
PATH_C_PIN_WHEAT_VALVE = False
PATH_C_SCALE_WHEAT_BUFFER = None  # None | number | "owned"
# Composite arm (2026-08-26, user-designed sequence - never before run as ONE
# arm): phase-0 filler policy, force WHEAT plantings while day <= end_day and
# live WHEAT tiles are under `tiles`. Bounded twice over - by tile count and by
# day window - unlike the recorded F7 unbounded force-wheat flood (200+
# WHEAT plantings); it releases before STRAWBERRY's planting window opens, so
# filler phase and carpet phase never overlap. Default 0 = off, keeping every
# pre-existing arm byte-reproducible.
PATH_C_WHEAT_FRONTLOAD_TILES = 0
PATH_C_WHEAT_FRONTLOAD_END_DAY = 4


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

    def __init__(self, seed=0, market=None, town=None, shares_market=False, pin_strawberry=False,
                 trace_tiers=False, path_c=False, path_c_cfg=None):
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
        # Crew-attention priority experiment (straw-first, attempt 4 - see
        # CLAUDE.md / mydocs): while True and the current day falls inside
        # agent_main.CROP_PLANTING_WINDOWS["STRAWBERRY"], STRAWBERRY tiles in
        # the WATER/CARE tier of _assign_crew are matched to crew BEFORE any
        # other crop's tiles in that same tier, instead of one Hungarian
        # match across all of them together. Does not touch choose_crop or
        # which crop gets planted anywhere - only which already-planted
        # tile's watering/care a scarce crew reaches first.
        self.pin_strawberry = pin_strawberry
        # Diagnostic-only, additive, off by default: when True, `_assign_crew`
        # records which unit indices each priority tier (`take()` call)
        # consumed this turn - used to trace whether the pin_strawberry
        # water/care re-split changes which physical units are left over for
        # the tiers that come after it (fertilize/place/weed/empty) even when
        # STRAWBERRY's own tile count doesn't move. Never read by any
        # non-diagnostic code path.
        self.trace_tiers = trace_tiers
        self.tier_trace = []
        # PATH_C_CORE.md's two crew-attention-priority pieces (STRAW-elevated
        # FERTILIZE, and the Level-2 FEED->STRAW harvest->plant WATER->other
        # harvest->animal CARE reorder) have no main.py equivalent to
        # override, so they live directly in _assign_crew, gated on this
        # flag+cfg rather than through _override_main. Off by default -
        # existing pin_strawberry/plain-Path-A behavior is unchanged.
        self.path_c = path_c
        self.path_c_cfg = path_c_cfg or {}
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
                        # 4th element (crop) is extra, harmless to `take()`
                        # (it only ever reads index 0/1/2) - used by Path C's
                        # STRAW-harvest-first crew split below.
                        ready_tiles.append((x, y, ["HARVEST"], tile.get("crop")))
                    elif not tile.get("watered_today", True):
                        water_care_tiles.append((x, y, ["WATER"], tile.get("crop")))
                    elif agent_main.wants_fertilizer(tile, day):
                        fertilize_tiles.append((x, y, tile.get("crop")))
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
                        ready_tiles.append((x, y, ["HARVEST"], None))
                    elif tile.get("fertilizer_available"):
                        ready_tiles.append((x, y, ["COLLECT_FERTILIZER"], None))
                    elif not tile.get("cared_today"):
                        water_care_tiles.append((x, y, ["CARE"], None))
                elif kind in agent_main.ANIMAL_STRUCTURE_KINDS:
                    place_tiles.append((x, y))

        assignments = []  # (unit_idx, x, y, action)

        def take(tiles, limit_check=None, tier_name=None):
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
                if self.trace_tiers and tier_name is not None:
                    self.tier_trace.append({
                        "day": self.day, "hour": self.hour, "tier": tier_name,
                        "tiles": len(tiles), "available_before": len(available),
                        "used_units": [], "available_after": len(available),
                    })
                return
            cost = [
                [abs(ux - t[0]) + abs(uy - t[1]) for t in tiles]
                for (_, (ux, uy)) in available
            ]
            row_ind, col_ind = linear_sum_assignment(cost)
            used_rows = set()
            used_units = []
            available_before = len(available)
            for row, col in zip(row_ind, col_ind):
                unit_idx, (ux, uy) = available[row]
                x, y = tiles[col][0], tiles[col][1]
                action = tiles[col][2] if limit_check is None else limit_check(x, y)
                self.counters["total_assignment_distance"] += abs(ux - x) + abs(uy - y)
                if action is not None:
                    assignments.append((unit_idx, x, y, action))
                    used_units.append(unit_idx)
                used_rows.add(row)
            available[:] = [item for i, item in enumerate(available) if i not in used_rows]
            if self.trace_tiers and tier_name is not None:
                self.tier_trace.append({
                    "day": self.day, "hour": self.hour, "tier": tier_name,
                    "tiles": len(tiles), "available_before": available_before,
                    "used_units": used_units, "available_after": len(available),
                })

        # 1. Feed - shared WHEAT budget, same shape as main.py's wheat_budget.
        wheat_left = shed.get("WHEAT", 0)

        def feed_action(x, y):
            nonlocal wheat_left
            if wheat_left <= 0:
                return None
            wheat_left -= 1
            return ["FEED"]

        take(feed_tiles, feed_action, tier_name="FEED")

        # Path C Core (PATH_C_CORE.md, sections 3-4): once >=3 animals are
        # filled, elevate STRAWBERRY's own FERTILIZE tiles ahead of every
        # other crop's; once straw_tiles/animals both clear their L2
        # thresholds, reorder the whole crew ladder to
        # FEED -> STRAW harvest -> plant WATER -> other harvest -> animal
        # CARE. Both gated on self.path_c - Path A (path_c=False) and the
        # unrelated pin_strawberry experiment are unaffected below.
        path_c_cfg = self.path_c_cfg
        straw_tile_count = sum(
            1
            for row in farm["tiles"]
            for t in row
            if isinstance(t, dict) and t.get("kind") == "PLANT" and t.get("crop") == "STRAWBERRY"
        )
        filled_animals, _ = agent_main.scan_animal_structures(farm, BOARD_SIZE)
        level2_active = (
            self.path_c
            and path_c_cfg.get("level2_crew", True)
            and straw_tile_count >= path_c_cfg.get("l2_straw_tiles", 30)
            and filled_animals >= path_c_cfg.get("l2_min_animals", 6)
        )
        fert_elevate_active = (
            self.path_c
            and filled_animals >= path_c_cfg.get("fert_elevate_min_animals", 3)
        )

        if level2_active:
            self.counters["path_c_l2_active_turns"] += 1
            straw_ready = [
                (x, y, action) for (x, y, action, crop) in ready_tiles if crop == "STRAWBERRY"
            ]
            other_ready = [
                (x, y, action) for (x, y, action, crop) in ready_tiles if crop != "STRAWBERRY"
            ]
            plant_water = [
                (x, y, action) for (x, y, action, crop) in water_care_tiles if crop is not None
            ]
            animal_care = [
                (x, y, action) for (x, y, action, crop) in water_care_tiles if crop is None
            ]
            take(straw_ready, tier_name="STRAW_HARVEST")
            take(plant_water, tier_name="PLANT_WATER")
            take(other_ready, tier_name="OTHER_HARVEST")
            take(animal_care, tier_name="ANIMAL_CARE")
        else:
            # 2. Ready harvests / fertilizer collection - no budget needed.
            take(ready_tiles, tier_name="READY")

            # 3. Water / care - no budget needed. When pin_strawberry is on
            # and today falls inside STRAWBERRY's own planting window, split
            # this tier so STRAWBERRY tiles get matched to crew before any
            # other crop's tiles in the same tier (two Hungarian solves
            # instead of one) - the crew-priority experiment (see
            # __init__'s docstring). Outside the window, or with the flag
            # off, behavior is unchanged.
            straw_window = agent_main.CROP_PLANTING_WINDOWS.get("STRAWBERRY")
            pin_active = (
                self.pin_strawberry
                and straw_window is not None
                and straw_window[0] <= day <= straw_window[1]
            )
            if pin_active:
                strawberry_tiles = [
                    (x, y, action) for (x, y, action, crop) in water_care_tiles if crop == "STRAWBERRY"
                ]
                other_tiles = [
                    (x, y, action) for (x, y, action, crop) in water_care_tiles if crop != "STRAWBERRY"
                ]
                self.counters["pin_strawberry_tiles_prioritized"] += len(strawberry_tiles)
                take(strawberry_tiles, tier_name="WATER_CARE_STRAWBERRY")
                take(other_tiles, tier_name="WATER_CARE_OTHER")
            else:
                take(
                    [(x, y, action) for (x, y, action, crop) in water_care_tiles],
                    tier_name="WATER_CARE",
                )

        # 3b. Fertilize - shared FERTILIZER budget.
        fert_left = shed.get("FERTILIZER", 0)

        def fertilize_action(x, y):
            nonlocal fert_left
            if fert_left <= 0:
                return None
            fert_left -= 1
            return ["FERTILIZE"]

        if fert_elevate_active:
            straw_fert = [(x, y) for (x, y, crop) in fertilize_tiles if crop == "STRAWBERRY"]
            other_fert = [(x, y) for (x, y, crop) in fertilize_tiles if crop != "STRAWBERRY"]
            take(straw_fert, fertilize_action, tier_name="FERTILIZE_STRAW")
            take(other_fert, fertilize_action, tier_name="FERTILIZE_OTHER")
        else:
            take(fertilize_tiles, fertilize_action, tier_name="FERTILIZE")

        # 4. Place a bought animal on an empty structure - per-species shed budget.
        species_left = {a: shed.get(a, 0) for a in agent_main.ACTIVE_ANIMALS}

        def place_action(x, y):
            for species in agent_main.ACTIVE_ANIMALS:
                if species_left.get(species, 0) > 0:
                    species_left[species] -= 1
                    return ["PLACE", species]
            return None

        take(place_tiles, place_action, tier_name="PLACE")

        # 8. Weeds - free.
        take([(x, y, ["DIG"]) for x, y in weed_tiles], tier_name="WEED")

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

        take(empty_tiles, empty_action, tier_name="EMPTY")

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
        filled_before, _ = agent_main.scan_animal_structures(farm, BOARD_SIZE)
        _daily_refresh_animals(farm, self.day)
        filled_after, _ = agent_main.scan_animal_structures(farm, BOARD_SIZE)
        # Animals never leave voluntarily, so any drop across the nightly
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
        filled_animals, _ = agent_main.scan_animal_structures(farm, BOARD_SIZE)
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
                "animals": filled_animals,
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
            "tier_trace": self.tier_trace if self.trace_tiers else None,
        }


def run_episode(seed=0, days=SEASON_DAYS, overrides=None, pin_strawberry=False, trace_tiers=False,
                 path_c=False, path_c_cfg=None):
    """Run one episode against town/shop demand only (no competing seller -
    the same "market stays uncontested" shape as paired_compare.py's `pass`/
    `starter` built-ins, which is where most of the documented crop-economy
    findings this model validates against were originally measured).
    """
    overrides = overrides or {}
    with _override_main(**overrides):
        model = EconomyModel(
            seed=seed, pin_strawberry=pin_strawberry, trace_tiers=trace_tiers,
            path_c=path_c, path_c_cfg=path_c_cfg,
        )
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

    def __init__(self, seed=0, seed_b=None, overrides=None, overrides_b=None,
                 pin_strawberry=False, pin_strawberry_b=False):
        self.market = _new_market()
        self.town = _new_town()
        self.rng = random.Random(seed)
        self.overrides = [overrides or {}, overrides_b if overrides_b is not None else (overrides or {})]
        self.sides = [
            EconomyModel(
                seed=seed, market=self.market, town=self.town, shares_market=True,
                pin_strawberry=pin_strawberry,
            ),
            EconomyModel(
                seed=seed_b if seed_b is not None else seed,
                market=self.market,
                town=self.town,
                shares_market=True,
                pin_strawberry=pin_strawberry_b,
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


def run_contested_episode(seed=0, seed_b=None, days=SEASON_DAYS, overrides=None, overrides_b=None,
                           pin_strawberry=False, pin_strawberry_b=False):
    """Two policies (or the same one twice, for self-play) sharing one
    market/town for the whole episode. Returns [report_a, report_b], same
    shape as EconomyModel.report() per side. See ContestedEconomyModel's
    docstring for the override-scoping mechanics.
    """
    model = ContestedEconomyModel(
        seed=seed, seed_b=seed_b, overrides=overrides, overrides_b=overrides_b,
        pin_strawberry=pin_strawberry, pin_strawberry_b=pin_strawberry_b,
    )
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


def _straw_first_gate_open(
    farm, day, strawberry_min_tiles=None, min_day=None, cash_buffer_multiple=None
):
    """Shared gate logic for both straw-first overrides below - kept as one
    function so the animal-purchase gate and the sell-hold gate can never
    drift out of sync with each other.

    Each condition is independent; the gate opens as soon as ANY enabled
    one is true. min_day is a day floor so the pause can't outlive
    STRAWBERRY's own 5-12 planting window with nothing to show for it.
    cash_buffer_multiple is the v2 addition: open early once money clears
    cash_buffer_multiple x MIN_CASH_RESERVE_FOR_ANIMAL_BUYING, on the
    reasoning that v1's own displacement-check result showed STRAWBERRY is
    tile/window-capped, not cash-capped - so idle cash sitting past that
    buffer isn't doing anything for STRAWBERRY by staying unspent, and
    should go to the animal instead of waiting out a rigid day/tile gate.
    All conditions None means "never pauses" (falls through to Path A).
    """
    conditions = []
    if min_day is not None:
        conditions.append(day >= min_day)
    if strawberry_min_tiles is not None:
        straw_tiles = sum(
            1
            for row in farm["tiles"]
            for tile in row
            if tile and tile != "LOCKED"
            and tile.get("kind") == "PLANT"
            and tile.get("crop") == "STRAWBERRY"
        )
        conditions.append(straw_tiles >= strawberry_min_tiles)
    if cash_buffer_multiple is not None:
        money = farm.get("money", 0)
        conditions.append(
            money >= agent_main.MIN_CASH_RESERVE_FOR_ANIMAL_BUYING * cash_buffer_multiple
        )
    return any(conditions) if conditions else True


def _straw_seed_boost_overrides(straw_seed_stockpile=None):
    """Raise the seed-restock TARGET for STRAWBERRY only, without touching
    seed_restock_quantity's own cash-safety loop.

    Traced in straw_first_pause_session_notes.md ("take 3"): MAX_SEED_STOCKPILE
    (3) and SEED_REBUY_TRIGGER (0) are global, not per-crop, so at most 3
    STRAWBERRY plantings can land per restock cycle regardless of how many
    idle hands want to plant it during the narrow 8-day (days 5-12) window -
    a ceiling never tested against on its own, distinct from the window,
    growth_days, or animal-purchase-timing dead ends already closed in
    CLAUDE.md.

    Wraps agent_main.seed_restock_quantity: for calls where crop ==
    "STRAWBERRY", temporarily bump agent_main.MAX_SEED_STOCKPILE to
    straw_seed_stockpile for the duration of that one call only (restored in
    `finally`), then delegate to the real function unchanged - its
    affordability loop (SEED_SPEND_CAP_FRACTION, MIN_CASH_RESERVE_FOR_SEED_BUYING)
    still runs against the bigger target, so this only raises the ceiling on
    how many the loop is ALLOWED to buy when cash genuinely allows it; it
    never bypasses the checks that stopped the historical $80/turn
    seed-repurchase spiral (CLAUDE.md's three failed per-turn-budget
    variants). Non-STRAWBERRY crops are untouched.

    Returns {} (no override) if straw_seed_stockpile is None, matching the
    existing all-None-means-no-op convention.
    """
    if straw_seed_stockpile is None:
        return {}

    original_restock = agent_main.seed_restock_quantity

    def restock_wrapper(crop, farm, private):
        if crop != "STRAWBERRY":
            return original_restock(crop, farm, private)
        original_cap = agent_main.MAX_SEED_STOCKPILE
        try:
            agent_main.MAX_SEED_STOCKPILE = straw_seed_stockpile
            return original_restock(crop, farm, private)
        finally:
            agent_main.MAX_SEED_STOCKPILE = original_cap

    return {"seed_restock_quantity": restock_wrapper}


def _straw_first_overrides(
    strawberry_min_tiles=None,
    min_day=None,
    cash_buffer_multiple=None,
    hold_product=None,
    straw_seed_stockpile=None,
):
    """Build an overrides dict implementing the straw-first pause mechanism
    via function-object swaps through _override_main - no main.py changes.
    Three independent, optional levers, combinable:

    - The animal-purchase gate (strawberry_min_tiles / min_day /
      cash_buffer_multiple, via _straw_first_gate_open) replaces
      main.choose_animal_to_build; a refused tile falls through to the
      existing, unmodified choose_crop call exactly as it does today
      whenever choose_animal_to_build already returns None (e.g. under
      MAX_ANIMALS) - this deliberately never touches choose_crop's own
      price/glut-aware scoring, unlike the failed Test 1a/1b fill-priority
      wrappers in CLAUDE.md.
    - hold_product (e.g. "STRAWBERRY"): while the gate above is closed,
      strip that product's normal-price-threshold SELL order out of
      main.decide_market_actions's output instead of letting it sell -
      i.e. hold the harvest in the shed rather than sell continuously.
      Only while shed_total stays under SHED_FORCE_SELL_THRESHOLD, which
      is a total-shed-contents threshold, not per-product - that existing
      overflow safety valve is read live, never overridden, since losing
      product to silent shed overflow (kaggriculture.py's 100-item cap)
      is worse than an early sale. Once the gate opens, held stock sells
      down normally (still capped per-turn by MAX_SELL_PER_TURN) - a
      cash injection timed to when the delayed animal purchase needs it,
      not a season-wide urgency ramp like the two already-failed
      sell-cadence experiments in CLAUDE.md (a different mechanism: one
      narrow hold-and-release at a single transition, not continuous
      re-scoring of every sale all season).
    - straw_seed_stockpile: see _straw_seed_boost_overrides above - raises
      STRAWBERRY's own seed-restock ceiling, independent of the other two
      levers (can be used alone, with neither gate/hold set, to isolate its
      effect per the "take 3" plan's Step A).

    Passing all five as None returns an empty dict (pure Path A, no-op).
    """
    original_build = agent_main.choose_animal_to_build
    original_market = agent_main.decide_market_actions

    def gate_open(farm, day):
        return _straw_first_gate_open(
            farm, day,
            strawberry_min_tiles=strawberry_min_tiles,
            min_day=min_day,
            cash_buffer_multiple=cash_buffer_multiple,
        )

    overrides = {}

    if strawberry_min_tiles is not None or min_day is not None or cash_buffer_multiple is not None:

        def build_wrapper(farm, private, board_size, day, pending_builds=0, ux=None, uy=None):
            if not gate_open(farm, day):
                return None
            return original_build(farm, private, board_size, day, pending_builds, ux, uy)

        overrides["choose_animal_to_build"] = build_wrapper

    if hold_product is not None:

        def market_wrapper(
            farm, private, market_state, day, reserved_wheat=0, unlocked_shops=(),
            start_step=None, opponent_pipeline=None,
        ):
            actions = original_market(
                farm, private, market_state, day, reserved_wheat, unlocked_shops,
                start_step, opponent_pipeline,
            )
            if not gate_open(farm, day):
                shed_total = sum(private.get("shed", {}).values())
                if shed_total < agent_main.SHED_FORCE_SELL_THRESHOLD:
                    actions = [
                        a for a in actions
                        if not (a[0] == "SELL" and a[1] == hold_product)
                    ]
            return actions

        overrides["decide_market_actions"] = market_wrapper

    overrides.update(_straw_seed_boost_overrides(straw_seed_stockpile))

    return overrides


def run_straw_first_pause(
    seed=0,
    days=SEASON_DAYS,
    strawberry_min_tiles=20,
    min_day=12,
    cash_buffer_multiple=None,
    hold_product=None,
    straw_seed_stockpile=None,
):
    """One seed's Path A (baseline, unmodified main.py) vs the straw-first
    pause variant - same seed for both, so any delta is the gate's effect,
    not seed luck (same paired-comparison logic paired_compare.py uses on
    the real engine). Defaults reproduce the original v1 experiment (gate
    only, no cash escape valve, no holding); pass cash_buffer_multiple
    and/or hold_product="STRAWBERRY" for the v2 variant, and/or
    straw_seed_stockpile for the "take 3" seed-ceiling lever (see
    _straw_seed_boost_overrides) - all independently optional.
    """
    baseline = run_episode(seed=seed, days=days)
    overrides = _straw_first_overrides(
        strawberry_min_tiles=strawberry_min_tiles,
        min_day=min_day,
        cash_buffer_multiple=cash_buffer_multiple,
        hold_product=hold_product,
        straw_seed_stockpile=straw_seed_stockpile,
    )
    paused = run_episode(seed=seed, days=days, overrides=overrides)
    return {"baseline": baseline, "paused": paused}


def compare_straw_first_pause(
    seeds=range(12),
    days=SEASON_DAYS,
    strawberry_min_tiles=20,
    min_day=12,
    cash_buffer_multiple=None,
    hold_product=None,
    straw_seed_stockpile=None,
    verbose=True,
):
    """Batch paired comparison, win-count first per this repo's own
    standing rule (CLAUDE.md: "judge a change with a paired comparison,
    not against the across-seed stdev; read the win count before any
    t-value"). bptk-only signal - see module-level inflation caveat.
    """
    rows = []
    for seed in seeds:
        result = run_straw_first_pause(
            seed=seed,
            days=days,
            strawberry_min_tiles=strawberry_min_tiles,
            min_day=min_day,
            cash_buffer_multiple=cash_buffer_multiple,
            hold_product=hold_product,
            straw_seed_stockpile=straw_seed_stockpile,
        )
        base_money = result["baseline"]["final_money"]
        paused_money = result["paused"]["final_money"]
        base_counters = result["baseline"]["counters"]
        paused_counters = result["paused"]["counters"]
        # Every crop, not just STRAWBERRY - this is the displacement check.
        # CLAUDE.md documents four separate "freed tile-time" experiments
        # that all lost because the freed turns defaulted to cheap,
        # fast-cycling WHEAT instead of anything more valuable. If that's
        # happening here too, planted_WHEAT will rise under the pause while
        # planted_STRAWBERRY barely moves - visible directly in this dict
        # rather than discovered after the fact.
        all_crops = sorted(
            {
                key.replace("crop_planted_", "")
                for key in list(base_counters) + list(paused_counters)
                if key.startswith("crop_planted_")
            }
        )
        planted = {
            crop: {
                "baseline": base_counters.get(f"crop_planted_{crop}", 0),
                "paused": paused_counters.get(f"crop_planted_{crop}", 0),
            }
            for crop in all_crops
        }
        rows.append(
            {
                "seed": seed,
                "baseline_money": base_money,
                "paused_money": paused_money,
                "delta": paused_money - base_money,
                "planted": planted,
                "baseline_feed": base_counters.get("FEED", 0),
                "paused_feed": paused_counters.get("FEED", 0),
                "baseline_daily_log": result["baseline"]["daily_log"],
                "paused_daily_log": result["paused"]["daily_log"],
            }
        )
    deltas = [r["delta"] for r in rows]
    wins = sum(1 for d in deltas if d > 0)
    mean_delta = sum(deltas) / len(deltas) if deltas else 0.0
    # Displacement summary across the whole batch: for each crop, mean
    # (paused - baseline) planted count. A positive WHEAT number alongside
    # a near-zero STRAWBERRY number is the exact failure mode to watch for.
    displacement = {}
    for crop in sorted({c for r in rows for c in r["planted"]}):
        deltas_for_crop = [
            r["planted"][crop]["paused"] - r["planted"][crop]["baseline"]
            for r in rows
            if crop in r["planted"]
        ]
        displacement[crop] = sum(deltas_for_crop) / len(deltas_for_crop)
    if verbose:
        print(
            f"straw-first pause vs Path A baseline, {len(rows)} seeds "
            f"(strawberry_min_tiles={strawberry_min_tiles}, min_day={min_day})"
        )
        for r in rows:
            print(
                f"  seed {r['seed']:>2}: baseline={r['baseline_money']:.0f}  "
                f"paused={r['paused_money']:.0f}  delta={r['delta']:+.0f}"
            )
        print(f"mean delta: {mean_delta:+.0f}  wins: {wins}/{len(rows)}")
        print("mean planted-count delta by crop (paused - baseline):")
        for crop, d in displacement.items():
            print(f"  {crop}: {d:+.1f}")
    return {
        "rows": rows,
        "mean_delta": mean_delta,
        "wins": wins,
        "n": len(rows),
        "displacement": displacement,
    }


def _path_c_defaults():
    return {
        "early_animals": PATH_C_EARLY_ANIMALS,
        "early_day_limit": PATH_C_EARLY_DAY_LIMIT,
        "straw_cap": PATH_C_STRAW_CAP,
        "straw_window_end": PATH_C_STRAW_WINDOW_END,
        "scale_max": PATH_C_SCALE_MAX_ANIMALS,
        "scale_straw_done": PATH_C_SCALE_STRAW_DONE,
        "scale_day": PATH_C_SCALE_DAY,
        "level2_crew": PATH_C_LEVEL2_CREW,
        "l2_straw_tiles": PATH_C_L2_STRAW_TILES,
        "l2_min_animals": PATH_C_L2_MIN_ANIMALS,
        "hire_bump_ceiling": PATH_C_HIRE_BUMP_CEILING,
        "hire_bump_min_day": PATH_C_HIRE_BUMP_MIN_DAY,
        "hire_bump_min_money": PATH_C_HIRE_BUMP_MIN_MONEY,
        "melon_pause_day": PATH_C_MELON_PAUSE_DAY,
        "gate_fert_sell": PATH_C_GATE_FERT_SELL,
        "fert_elevate_min_animals": PATH_C_FERT_ELEVATE_MIN_ANIMALS,
        # Fix-pass keys (mydocs/Path C System Dynamics Diagnosis.md); defaults
        # off/None so run_path_c() with no overrides is still the broken core.
        "pin_wheat_valve": PATH_C_PIN_WHEAT_VALVE,
        "scale_wheat_buffer": PATH_C_SCALE_WHEAT_BUFFER,
    }


def _path_c_straw_tile_count(farm):
    return sum(
        1
        for row in farm["tiles"]
        for tile in row
        if isinstance(tile, dict) and tile.get("kind") == "PLANT" and tile.get("crop") == "STRAWBERRY"
    )


def _path_c_wheat_tile_count(farm):
    return sum(
        1
        for row in farm["tiles"]
        for tile in row
        if isinstance(tile, dict) and tile.get("kind") == "PLANT" and tile.get("crop") == "WHEAT"
    )


def _path_c_wheat_stock(private):
    shed_wheat = private.get("shed", {}).get("WHEAT", 0)
    carried = sum(
        (inv or {}).get("WHEAT", 0)
        for inv in (private.get("inventories") or [])
        if isinstance(inv, dict)
    )
    return shed_wheat + carried


def _path_c_wheat_buffer_met(private, owned, cfg):
    """The scale-unlock's wheat safety check. With `scale_wheat_buffer=None`
    this is PATH_C_CORE.md's original "wheat_stock > 0" - which the real-engine
    trace showed is nearly always true, i.e. toothless (mydocs/Path C System
    Dynamics Diagnosis.md, culprit #2). A number N instead requires stock >=
    MIN_WHEAT_RESERVE_FOR_FEEDING * N; "owned" keys it to owned+1 so growing
    the herd by one animal always leaves one reserve-worth of buffer behind.
    """
    req = cfg.get("scale_wheat_buffer")
    stock = _path_c_wheat_stock(private)
    if req is None:
        return stock > 0
    if req == "owned":
        req = owned + 1
    return stock >= agent_main.MIN_WHEAT_RESERVE_FOR_FEEDING * req


def _path_c_animal_cap(farm, private, day, cfg):
    """PATH_C_CORE.md's "Animal sequencing": up to `early_animals` while
    day <= early_day_limit; frozen at whatever's already owned (pause) until
    the STRAW carpet reaches `scale_straw_done` tiles or day reaches
    `scale_day`; then a ceiling of `scale_max` - unless the wheat-buffer gate
    (`_path_c_wheat_buffer_met`) fails, in which case the freeze holds.
    """
    owned = agent_main.count_owned_animals(farm, private, BOARD_SIZE)
    straw_tiles = _path_c_straw_tile_count(farm)
    scale_unlocked = straw_tiles >= cfg["scale_straw_done"] or day >= cfg["scale_day"]
    if scale_unlocked and _path_c_wheat_buffer_met(private, owned, cfg):
        return cfg["scale_max"]
    if day <= cfg["early_day_limit"]:
        return max(cfg["early_animals"], owned)
    return owned  # pause: freeze, no further buys/builds until scale unlocks


def _path_c_straw_pin_active(farm, private, day, cfg):
    """PATH_C_CORE.md's crop policy #1: "while in STRAW window and
    straw_tiles < 50, always prefer STRAWBERRY (inviolable)". The window's
    start day is read from main.py's own CROP_PLANTING_WINDOWS (its real
    STRAWBERRY start), extended through cfg['straw_window_end'] rather than
    CROP_PLANTING_WINDOWS's own (shorter) end - matching PATH_C_STRAW_WINDOW_END's
    documented role ("Pin active through" 14, vs. the base window's 12).

    Fix #1 (mydocs/Path C System Dynamics Diagnosis.md): with pin_wheat_valve,
    the pin additionally yields while shed+carried WHEAT is under
    MIN_WHEAT_RESERVE_FOR_FEEDING * (owned+1), letting choose_crop plant WHEAT
    on its own terms - the connector the original pin lacked (it starved the
    herd's only organic food source for the whole window).
    """
    window = agent_main.CROP_PLANTING_WINDOWS.get("STRAWBERRY")
    if window is None:
        return False
    window_start = window[0]
    if not (window_start <= day <= cfg["straw_window_end"]):
        return False
    if cfg.get("pin_wheat_valve"):
        owned = agent_main.count_owned_animals(farm, private, BOARD_SIZE)
        stock = _path_c_wheat_stock(private)
        if stock < agent_main.MIN_WHEAT_RESERVE_FOR_FEEDING * (owned + 1):
            return False
    return _path_c_straw_tile_count(farm) < cfg["straw_cap"]


def _path_c_any_straw_wants_fertilizer(farm, day):
    for row in farm["tiles"]:
        for tile in row:
            if (
                isinstance(tile, dict)
                and tile.get("kind") == "PLANT"
                and tile.get("crop") == "STRAWBERRY"
                and agent_main.wants_fertilizer(tile, day)
            ):
                return True
    return False


def path_c_overrides(**cfg_overrides):
    """Build the main.py function-object overrides for PATH_C_CORE.md's
    normative policy (see mydocs/PATH_C_CORE.md - research done in a
    separate environment; nothing under this name existed in bptk.py before
    this pass, so this is a first faithful-to-spec reproduction, not a
    re-run of an already-verified result).

    Four of the doc's six policy pieces are pure function-object swaps
    (same _override_main mechanism as _straw_first_overrides): animal
    sequencing (choose_animal_to_build / decide_animal_market_actions), the
    STRAWBERRY pin (choose_crop), the fertilizer-sell gate
    (decide_market_actions), and the day/cash hire bump (decide_hire_orders).
    The remaining two - elevating STRAWBERRY within the FERTILIZE crew tier,
    and the Level-2 crew reorder - are crew-attention-priority changes with
    no main.py equivalent to override, so they live directly in
    EconomyModel._assign_crew, gated on path_c_cfg (pass path_c=True,
    path_c_cfg=cfg to run_episode/EconomyModel alongside these overrides -
    run_path_c/compare_path_c do this automatically).

    Not reproduced: the "MELON under wheat encroachment" experimental arm
    (PATH_C_MELON_PAUSE_DAY defaults to 0 = off in core, per the doc) and
    the doc's vague, number-free "controlled STRAWBERRY/MELON sell caps"
    (main.py's existing MAX_SELL_PER_TURN defaults are left as-is).
    """
    cfg = _path_c_defaults()
    cfg.update(cfg_overrides)

    original_build = agent_main.choose_animal_to_build
    original_buy = agent_main.decide_animal_market_actions
    original_crop = agent_main.choose_crop
    original_hire = agent_main.decide_hire_orders
    original_market = agent_main.decide_market_actions

    def build_wrapper(farm, private, board_size, day, pending_builds=0, ux=None, uy=None):
        cap = _path_c_animal_cap(farm, private, day, cfg)
        original_cap = agent_main.MAX_ANIMALS
        try:
            agent_main.MAX_ANIMALS = cap
            return original_build(farm, private, board_size, day, pending_builds, ux, uy)
        finally:
            agent_main.MAX_ANIMALS = original_cap

    def buy_wrapper(farm, private, board_size, day):
        cap = _path_c_animal_cap(farm, private, day, cfg)
        original_cap = agent_main.MAX_ANIMALS
        try:
            agent_main.MAX_ANIMALS = cap
            return original_buy(farm, private, board_size, day)
        finally:
            agent_main.MAX_ANIMALS = original_cap

    def crop_wrapper(
        farm, market_state, private, day, unlocked_shops=(), start_step=None,
        opponent_pipeline=None, require_held_seed=False,
    ):
        if not require_held_seed and _path_c_straw_pin_active(farm, private, day, cfg):
            return "STRAWBERRY"
        return original_crop(
            farm, market_state, private, day, unlocked_shops, start_step,
            opponent_pipeline, require_held_seed,
        )

    def hire_wrapper(farm, board_size, day, hour, seeds=None):
        bump = (
            day >= cfg["hire_bump_min_day"]
            and farm.get("money", 0) >= cfg["hire_bump_min_money"]
        )
        original_ceiling = agent_main.MAX_HANDS_PER_DAY
        try:
            if bump:
                agent_main.MAX_HANDS_PER_DAY = cfg["hire_bump_ceiling"]
            return original_hire(farm, board_size, day, hour, seeds)
        finally:
            agent_main.MAX_HANDS_PER_DAY = original_ceiling

    def market_wrapper(
        farm, private, market_state, day, reserved_wheat=0, unlocked_shops=(),
        start_step=None, opponent_pipeline=None,
    ):
        actions = original_market(
            farm, private, market_state, day, reserved_wheat, unlocked_shops,
            start_step, opponent_pipeline,
        )
        if cfg["gate_fert_sell"] and _path_c_any_straw_wants_fertilizer(farm, day):
            actions = [a for a in actions if not (a[0] == "SELL" and a[1] == "FERTILIZER")]
        return actions

    return {
        "choose_animal_to_build": build_wrapper,
        "decide_animal_market_actions": buy_wrapper,
        "choose_crop": crop_wrapper,
        "decide_hire_orders": hire_wrapper,
        "decide_market_actions": market_wrapper,
    }


def run_path_c(seeds=range(12), days=SEASON_DAYS, **cfg_overrides):
    """One Path C candidate episode per seed. Mirrors mydocs/PATH_C_CORE.md's
    own "How to run" example (`cand = bptk.run_path_c(seeds=range(12),
    early_animals=3, straw_cap=50, scale_max=10)`) - compare against
    `[run_episode(seed=s) for s in seeds]` (Path A) yourself, or use
    compare_path_c for the paired version with win-count/mean printed.
    """
    cfg = _path_c_defaults()
    cfg.update(cfg_overrides)
    overrides = path_c_overrides(**cfg)
    return [
        run_episode(seed=seed, days=days, overrides=overrides, path_c=True, path_c_cfg=cfg)
        for seed in seeds
    ]


def _episode_mechanism_stats(result):
    """Mechanism-gate counters for the Path C fix pass (mydocs/Path C System
    Dynamics Diagnosis.md). Read these BEFORE any bank number: the diagnosis's
    claim is about the wheat/feed mechanism, so the fix is only credible if

    - ``escapes`` goes to ~0 (real engine showed 17-20 per 12 episodes),
    - shed WHEAT leaves the MIN_WHEAT_RESERVE_FOR_FEEDING=2 floor mid-season,
    - peak STRAW tiles shows whether the straw>=scale_straw_done unlock branch
      is reachable at all (it never fired in the traced seeds; peak was 49),
    - final filled animals stays above the beach-head of 3 (an F8-stuck herd -
      herd frozen at beach-head because a hard buffer never accumulates - is
      the fix failing in the opposite direction).
    """
    log = result.get("daily_log") or []
    shed = [d.get("shed", {}).get("WHEAT", 0) for d in log if 15 <= d["day"] <= 25]
    animals = [d.get("animals", 0) for d in log]
    return {
        "buy_product_wheat": result["counters"].get("BUY_PRODUCT_WHEAT", 0),
        "shed_wheat_d15_25_mean": (sum(shed) / len(shed)) if shed else None,
        "shed_wheat_d15_25_min": min(shed) if shed else None,
        "straw_tiles_peak": max(
            (d.get("tiles", {}).get("PLANT:STRAWBERRY", 0) for d in log), default=0
        ),
        "animals_final": animals[-1] if animals else 0,
        "animals_min_post_day15": min((a for a, d in zip(animals, log) if d["day"] >= 15), default=0)
        if log
        else 0,
    }


def compare_path_c(seeds=range(12), days=SEASON_DAYS, verbose=True, **cfg_overrides):
    """Paired Path C vs Path A comparison, same seed both sides, win-count
    first per this repo's own standing rule (CLAUDE.md). bptk-only signal -
    see module-level inflation caveat; PATH_C_CORE.md's own numbers were
    measured elsewhere and are not assumed to reproduce exactly here.
    """
    cfg = _path_c_defaults()
    cfg.update(cfg_overrides)
    overrides = path_c_overrides(**cfg)
    rows = []
    for seed in seeds:
        baseline = run_episode(seed=seed, days=days)
        candidate = run_episode(
            seed=seed, days=days, overrides=overrides, path_c=True, path_c_cfg=cfg
        )
        base_mech = _episode_mechanism_stats(baseline)
        cand_mech = _episode_mechanism_stats(candidate)
        base_money = baseline["final_money"]
        cand_money = candidate["final_money"]
        rows.append(
            {
                "seed": seed,
                "path_a_money": base_money,
                "path_c_money": cand_money,
                "delta": cand_money - base_money,
                "path_a_straw_planted": baseline["counters"].get("crop_planted_STRAWBERRY", 0),
                "path_c_straw_planted": candidate["counters"].get("crop_planted_STRAWBERRY", 0),
                "path_a_melon_planted": baseline["counters"].get("crop_planted_MELON", 0),
                "path_c_melon_planted": candidate["counters"].get("crop_planted_MELON", 0),
                "path_a_animals_bought": sum(
                    baseline["counters"].get(f"BUY_ANIMAL_{a}", 0) for a in agent_main.ACTIVE_ANIMALS
                ),
                "path_c_animals_bought": sum(
                    candidate["counters"].get(f"BUY_ANIMAL_{a}", 0) for a in agent_main.ACTIVE_ANIMALS
                ),
                "path_c_feed": candidate["counters"].get("FEED", 0),
                "path_c_l2_turns": candidate["counters"].get("path_c_l2_active_turns", 0),
                **{f"path_a_{k}": v for k, v in base_mech.items()},
                **{f"path_c_{k}": v for k, v in cand_mech.items()},
            }
        )
    deltas = [r["delta"] for r in rows]
    wins = sum(1 for d in deltas if d > 0)
    mean_delta = sum(deltas) / len(deltas) if deltas else 0.0
    if verbose:
        n = max(len(rows), 1)

        def _avg(key):
            vals = [r[key] for r in rows if r.get(key) is not None]
            return sum(vals) / len(vals) if vals else float("nan")

        print(f"Path C vs Path A, {len(rows)} seeds")
        for r in rows:
            print(
                f"  seed {r['seed']:>2}: path_a={r['path_a_money']:.0f}  "
                f"path_c={r['path_c_money']:.0f}  delta={r['delta']:+.0f}  "
                f"L2 turns={r['path_c_l2_turns']}  "
                f"animals A/C={r['path_a_animals_bought']}/{r['path_c_animals_bought']}  "
                f"escapes A/C={r['path_a_escapes']}/{r['path_c_escapes']}  "
                f"final animals A/C={r['path_a_animals_final']}/{r['path_c_animals_final']}"
            )
        print(f"mean delta: {mean_delta:+.0f}  wins: {wins}/{len(rows)}")
        print(
            "mechanism (mean over seeds; read before bank): "
            f"buy_product_wheat A/C={_avg('path_a_buy_product_wheat'):.1f}/"
            f"{_avg('path_c_buy_product_wheat'):.1f}  "
            f"shed_wheat d15-25 mean A/C={_avg('path_a_shed_wheat_d15_25_mean'):.1f}/"
            f"{_avg('path_c_shed_wheat_d15_25_mean'):.1f}  "
            f"min A/C={_avg('path_a_shed_wheat_d15_25_min'):.1f}/"
            f"{_avg('path_c_shed_wheat_d15_25_min'):.1f}  "
            f"straw peak(max) C={max(r['path_c_straw_tiles_peak'] for r in rows)}  "
            f"animals min post-d15 C={min(r['path_c_animals_min_post_day15'] for r in rows)}"
        )
    return {"rows": rows, "mean_delta": mean_delta, "wins": wins, "n": len(rows)}


def compare_path_c_ladder(seeds=range(6), days=SEASON_DAYS, verbose=True):
    """Clean ablation: Path A vs full Path C vs Path C with one lever
    disabled at a time, so a win or loss can be attributed to a specific
    policy piece rather than the whole bundle. No STRAW/MELON-encroach arms
    (those are PATH_C_CORE.md's own already-parked experiments, not part of
    core) - see that doc's "Explicitly parked / rejected" table.
    """
    seeds = list(seeds)
    arms = collections.OrderedDict()
    arms["path_a"] = None
    arms["path_c_full"] = _path_c_defaults()

    no_pin = _path_c_defaults()
    no_pin["straw_cap"] = 0  # tile count is never < 0: pin never activates
    arms["path_c_no_straw_pin"] = no_pin

    no_l2 = _path_c_defaults()
    no_l2["level2_crew"] = False
    arms["path_c_no_level2_crew"] = no_l2

    no_seq = _path_c_defaults()
    no_seq["early_animals"] = agent_main.MAX_ANIMALS
    no_seq["scale_max"] = agent_main.MAX_ANIMALS
    arms["path_c_no_animal_seq"] = no_seq

    no_hire = _path_c_defaults()
    no_hire["hire_bump_min_day"] = 10 ** 6  # never triggers
    arms["path_c_no_hire_bump"] = no_hire

    no_fert_gate = _path_c_defaults()
    no_fert_gate["gate_fert_sell"] = False
    arms["path_c_no_fert_gate"] = no_fert_gate

    # Fix-pass arms (mydocs/Path C System Dynamics Diagnosis.md). One factor at
    # a time from broken core, per the team agreement - except fixes #1+#2,
    # which are one subsystem (the pin's missing wheat connector) and only
    # make sense together: #2 alone gates scaling on a buffer nothing refills
    # (the F8 hard-freeze failure mode), #1 alone leaves the toothless ">0"
    # gate in place. Two #2 flavours because the diagnosis's max-keyed target
    # (MIN_WHEAT_RESERVE * scale_max = 20) may be unreachable while the valve
    # sawtooths around MIN_WHEAT_RESERVE * (owned+1) = 8 - the owned-keyed
    # flavour is the F8 guard. straw42 / no_l2 ride on the owned base; if the
    # max-keyed base ends up winning, re-run them via run_path_c(**overrides).
    fix1 = _path_c_defaults()
    fix1["pin_wheat_valve"] = True
    arms["path_c_fix1_valve"] = fix1

    fix12_max = dict(fix1)
    fix12_max["scale_wheat_buffer"] = PATH_C_SCALE_MAX_ANIMALS
    arms["path_c_fix12_buf_scalemax"] = fix12_max

    fix12_owned = dict(fix1)
    fix12_owned["scale_wheat_buffer"] = "owned"
    arms["path_c_fix12_buf_owned"] = fix12_owned

    fix123 = dict(fix12_owned)
    fix123["scale_straw_done"] = 42  # traced straw-tile peak was 49 vs threshold 50
    arms["path_c_fix123_straw42"] = fix123

    fix123_no_l2 = dict(fix123)
    fix123_no_l2["level2_crew"] = False  # fix #4 ablated separately, not bundled
    arms["path_c_fix123_no_l2"] = fix123_no_l2

    results = collections.OrderedDict()
    mechs = collections.OrderedDict()
    for name, cfg in arms.items():
        rows = []
        arm_mechs = []
        for seed in seeds:
            if cfg is None:
                report = run_episode(seed=seed, days=days)
            else:
                overrides = path_c_overrides(**cfg)
                report = run_episode(
                    seed=seed, days=days, overrides=overrides, path_c=True, path_c_cfg=cfg
                )
            rows.append(report["final_money"])
            arm_mechs.append(_episode_mechanism_stats(report))
        results[name] = rows
        mechs[name] = arm_mechs

    path_a_rows = results["path_a"]
    if verbose:

        def _arm_mech_line(name):
            m = mechs[name]
            n = max(len(m), 1)
            shed = [
                x["shed_wheat_d15_25_mean"] for x in m if x["shed_wheat_d15_25_mean"] is not None
            ]
            return (
                f"escapes={sum(x['escapes'] for x in m)}  "
                f"buy_wheat/ep={sum(x['buy_product_wheat'] for x in m) / n:.0f}  "
                f"shedW d15-25={sum(shed) / len(shed) if shed else float('nan'):.1f}  "
                f"final_animals={sum(x['animals_final'] for x in m) / n:.1f}  "
                f"F8-stuck seeds={sum(1 for x in m if x['animals_min_post_day15'] <= 3)}  "
                f"straw_peak(max)={max(x['straw_tiles_peak'] for x in m)}"
            )

        print(f"Path C ablation ladder, {len(seeds)} seeds")
        for name, rows in results.items():
            mean = sum(rows) / len(rows)
            if name == "path_a":
                print(f"  {name:<26} mean={mean:>9.0f}")
            else:
                wins = sum(1 for a, b in zip(rows, path_a_rows) if a > b)
                print(f"  {name:<26} mean={mean:>9.0f}  wins vs path_a: {wins}/{len(seeds)}")
            print(f"    {_arm_mech_line(name)}")
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
    parser.add_argument(
        "--straw-first", action="store_true",
        help="run the straw-first pause-animals experiment vs Path A baseline",
    )
    parser.add_argument("--straw-first-seeds", type=int, default=12)
    parser.add_argument("--straw-first-min-tiles", type=int, default=20)
    parser.add_argument("--straw-first-min-day", type=int, default=12)
    parser.add_argument(
        "--straw-first-cash-multiple", type=float, default=None,
        help="v2: also open the animal gate once money clears this many x "
        "MIN_CASH_RESERVE_FOR_ANIMAL_BUYING (default: disabled, pure v1)",
    )
    parser.add_argument(
        "--straw-first-hold-product", type=str, default=None,
        help="v2: hold this product's normal sell while the gate is closed, "
        "e.g. STRAWBERRY (default: disabled, pure v1)",
    )
    parser.add_argument(
        "--straw-first-seed-stockpile", type=int, default=None,
        help="take 3: raise STRAWBERRY's own seed-restock ceiling to this "
        "many held seeds (default: disabled, MAX_SEED_STOCKPILE=3 as-is). "
        "Can be combined with or used independently of the gate/hold levers "
        "above - see _straw_seed_boost_overrides.",
    )
    parser.add_argument(
        "--compare-path-c", action="store_true",
        help="Path C Core vs Path A, paired per seed (see compare_path_c / mydocs/PATH_C_CORE.md)",
    )
    parser.add_argument(
        "--ladder", action="store_true",
        help="Path C ablation ladder: Path A vs full Path C vs each lever disabled once (see compare_path_c_ladder)",
    )
    parser.add_argument("--path-c-seeds", type=int, default=12)
    args = parser.parse_args()

    if args.validate:
        validate(seed=args.seed)
    elif args.validate_contested:
        validate_contested(seed=args.seed)
    elif args.check_assignment:
        _check_assignment_optimality()
    elif args.straw_first:
        compare_straw_first_pause(
            seeds=range(args.straw_first_seeds),
            days=args.days,
            strawberry_min_tiles=args.straw_first_min_tiles,
            min_day=args.straw_first_min_day,
            cash_buffer_multiple=args.straw_first_cash_multiple,
            hold_product=args.straw_first_hold_product,
            straw_seed_stockpile=args.straw_first_seed_stockpile,
        )
    elif args.compare_path_c:
        compare_path_c(seeds=range(args.path_c_seeds), days=args.days)
    elif args.ladder:
        compare_path_c_ladder(seeds=range(args.path_c_seeds), days=args.days)
    elif args.contested:
        side_a, side_b = run_contested_episode(seed=args.seed, seed_b=args.seed_b, days=args.days)
        print("=== side A ===")
        _print_summary(side_a)
        print("=== side B ===")
        _print_summary(side_b)
    else:
        _print_summary(run_episode(seed=args.seed, days=args.days))
