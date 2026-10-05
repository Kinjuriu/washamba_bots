"""Fail-closed shop observer and revealed-shop market overlay.

The parent policy always acts first. Future-shop inference is telemetry-only
unless the supplied seed domain is exhaustive and uniquely resolved. The live
policy modification uses only already revealed shops and public farm state.
"""

from __future__ import annotations

import copy
import math
from typing import Any, Callable

import shop_predictor as predictor


SHOPS = {
    "BAKERY": ("EGG", "WHEAT"),
    "PIZZA_SHOP": ("MILK", "TOMATO", "WHEAT"),
    "BRUNCH_SPOT": ("EGG", "WHEAT", "STRAWBERRY"),
    "YARN_STORE": ("WOOL",),
    "ICE_CREAM_SHOP": ("STRAWBERRY", "MILK", "WHEAT"),
    "PET_CAFE": ("CARROT",),
    "SMOOTHIE_SHOP": ("STRAWBERRY", "MILK"),
    "FARMERS_MARKET": ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY"),
}

MARKET_PARAMS = {
    "WHEAT": (25, 400, "sqrt", .80, "log", .20),
    "CARROT": (35, 450, "hinge", 1.00, "sqrt", .70),
    "TOMATO": (60, 200, "hinge", .40, "sqrt", .60),
    "STRAWBERRY": (120, 100, "sqrt", .70, "linear", 1.60),
    "MELON": (250, 300, "log", .20, "sq", 3.60),
    "EGG": (50, 332, "hinge", .40, "log", .20),
    "MILK": (160, 122, "sqrt", .60, "linear", 1.60),
    "WOOL": (200, 105, "log", .20, "sq", 3.20),
    "FERTILIZER": (100, 200, "linear", .40, "linear", .40),
}

PRODUCTS = tuple(MARKET_PARAMS)


def get(obj: Any, key: str, default: Any = None) -> Any:
    if isinstance(obj, dict):
        return obj.get(key, default)
    getter = getattr(obj, "get", None)
    if callable(getter):
        return getter(key, default)
    return getattr(obj, key, default)


def shape(kind: str, x: float, threshold: float) -> float:
    x = max(0.0, float(x))
    if kind == "linear":
        return x
    if kind == "sq":
        return x * x
    if kind == "sqrt":
        return math.sqrt(x)
    if kind == "log":
        return math.log1p(x)
    if kind == "hinge":
        u = x / threshold
        return u + 8.0 * max(0.0, u - 1.0) ** 2
    return x


def market_price(product: str, inventory: float) -> int:
    base, threshold, below_kind, below_target, above_kind, above_target = MARKET_PARAMS[product]
    if inventory < 10000:
        amplitude = below_target * base / shape(below_kind, threshold, threshold)
        value = base + amplitude * shape(below_kind, 10000 - inventory, threshold)
    else:
        amplitude = above_target * base / shape(above_kind, threshold, threshold)
        value = base - amplitude * shape(above_kind, inventory - 10000, threshold)
    return max(1, math.floor(value + .5))


def shop_demand(open_shops: list[str], product: str) -> int:
    total = 0
    for shop in open_shops:
        basket = SHOPS.get(shop, ())
        if product in basket:
            total += 2 if len(basket) == 1 else 1
    return total


def visible_tile_supply(farm: Any) -> tuple[dict[str, float], dict[str, int]]:
    supply = {product: 0.0 for product in PRODUCTS}
    footprint = {product: 0 for product in PRODUCTS}
    animal_products = {"GOOSE": "EGG", "COW": "MILK", "SHEEP": "WOOL"}
    for row in list(get(farm, "tiles", []) or []):
        for tile in row:
            if not isinstance(tile, dict):
                continue
            if tile.get("kind") == "PLANT" and tile.get("crop") in supply:
                product = str(tile["crop"])
                footprint[product] += 1
                supply[product] += max(0.0, float(tile.get("yield_units", 0) or 0))
            elif tile.get("animal") in animal_products:
                product = animal_products[str(tile["animal"])]
                footprint[product] += 1
                supply[product] += max(0.0, float(tile.get("yield_units", 0) or 0))
    return supply, footprint


def private_stock(observation: Any) -> tuple[dict[str, int], int]:
    private = get(observation, "private", {}) or {}
    shed = get(private, "shed", {}) or {}
    stock = {product: max(0, int(get(shed, product, 0) or 0)) for product in PRODUCTS}
    total = sum(stock.values())
    for inventory in list(get(private, "inventories", []) or []):
        for product in PRODUCTS:
            total += max(0, int(get(inventory, product, 0) or 0))
    return stock, total


def copy_action(action: Any) -> dict[str, Any]:
    action = copy.deepcopy(action if isinstance(action, dict) else {})
    return {
        "farmer": list(action.get("farmer") or ["PASS"]),
        "hands": [list(command or ["PASS"]) for command in list(action.get("hands") or [])],
        "market": [list(order) for order in list(action.get("market") or [])],
    }


def effective_sell(action: dict[str, Any], product: str, available: int) -> int:
    requested = sum(
        max(0, int(order[2]))
        for order in action.get("market", [])
        if len(order) >= 3 and order[0] == "SELL" and order[1] == product
    )
    return min(available, requested)


def replace_sell(action: dict[str, Any], product: str, quantity: int) -> None:
    market: list[list[Any]] = []
    insertion = None
    for order in action.get("market", []):
        if len(order) >= 3 and order[0] == "SELL" and order[1] == product:
            if insertion is None:
                insertion = len(market)
            continue
        market.append(order)
    if quantity > 0:
        market.insert(len(market) if insertion is None else insertion, ["SELL", product, int(quantity)])
    action["market"] = market[:10]


def empty_count(observation: Any) -> int:
    return sum(
        tile is None
        for farm in list(get(observation, "farms", []) or [])
        for row in list(get(farm, "tiles", []) or [])
        for tile in row
    )


class GodModeShopOverlay:
    """Observe hidden-seed evidence and apply only bounded, seed-blind sales changes."""

    def __init__(
        self,
        parent: Callable[[Any], dict[str, Any]],
        *,
        particle_count: int = 512,
        reserve_cap: int = 8,
        capacity_soft_limit: int = 88,
        minimum_price_gain: int = 3,
        minimum_own_gain: float = 10.0,
    ) -> None:
        self.parent = parent
        self.particle_count = max(128, int(particle_count))
        self.reserve_cap = max(0, int(reserve_cap))
        self.capacity_soft_limit = max(0, int(capacity_soft_limit))
        self.minimum_price_gain = max(0, int(minimum_price_gain))
        self.minimum_own_gain = float(minimum_own_gain)
        self.telemetry: list[dict[str, Any]] = []
        self.pending: dict[str, dict[str, int]] = {}
        self.last_step = -1
        self.previous_tiles = None
        self.previous_unit_positions = tuple()
        self.previous_day: int | None = None
        self.previous_hour: int | None = None
        self.shop_count = 0
        self._new_posterior()

    def _new_posterior(self) -> None:
        self.posterior = predictor.SeedPosterior(
            predictor.stratified_seed_particles(self.particle_count), exhaustive=False
        )

    def _reset(self) -> None:
        self.telemetry.clear()
        self.pending.clear()
        self.last_step = -1
        self.previous_tiles = None
        self.previous_unit_positions = tuple()
        self.previous_day = None
        self.previous_hour = None
        self.shop_count = 0
        self._new_posterior()

    def _observe(self, observation: Any, day: int, hour: int) -> None:
        if not (
            self.previous_tiles is not None
            and self.previous_day is not None
            and hour == 0
            and self.previous_hour == 23
            and day == self.previous_day + 1
        ):
            return
        evidence = predictor.extract_day_evidence(
            self.previous_tiles,
            self.previous_unit_positions,
            observation,
            end_day=self.previous_day,
            previous_shop_count=self.shop_count,
        )
        event = self.posterior.update(evidence)
        event.update(type="seed_posterior", observed_day=day)
        self.telemetry.append(event)

    def _settle(self, observation: Any, action: dict[str, Any], step: int) -> None:
        stock, _ = private_stock(observation)
        settled = []
        for product, debt in list(self.pending.items()):
            if step < int(debt["release_step"]):
                continue
            due = max(0, int(debt["quantity"]))
            available = max(0, int(stock.get(product, 0)))
            parent_sell = effective_sell(action, product, available)
            final_sell = min(available, max(parent_sell, due))
            replace_sell(action, product, final_sell)
            settled.append((product, due, final_sell))
            del self.pending[product]
        if settled:
            self.telemetry.append({"type": "settlement", "step": step, "products": settled})

    def _revealed_shop_overlay(
        self,
        observation: Any,
        action: dict[str, Any],
        step: int,
        day: int,
        hour: int,
        player: int,
    ) -> None:
        if day >= 29 or (day >= 28 and hour >= 12):
            return
        farms = list(get(observation, "farms", []) or [])
        if len(farms) < 2:
            return
        shops = list(get(get(observation, "town", {}) or {}, "unlocked_shops", []) or [])
        stock, total_stock = private_stock(observation)
        own_visible, own_footprint = visible_tile_supply(farms[player])
        _, rival_footprint = visible_tile_supply(farms[1 - player])
        market = get(observation, "market", {}) or {}
        inventories = get(market, "inventory", {}) or {}
        prices = get(market, "prices", {}) or {}
        changes = []
        for product in PRODUCTS:
            if product in self.pending:
                continue
            available = stock[product]
            parent_sell = effective_sell(action, product, available)
            demand = shop_demand(shops, product)
            footprint_edge = own_footprint[product] - rival_footprint[product]
            if parent_sell <= 0 or demand <= 0 or footprint_edge < 0:
                continue
            inventory = int(get(inventories, product, 10000) or 10000)
            current_price = int(get(prices, product, market_price(product, inventory)) or 0)
            projected_price = market_price(product, inventory - demand)
            price_gain = projected_price - current_price
            room = max(0, self.capacity_soft_limit - (total_stock - available))
            reserve = min(self.reserve_cap, parent_sell, demand, room)
            own_gain = reserve * max(0, price_gain)
            release_step = ((step // 4) + 1) * 4 + 1
            if (
                reserve <= 0
                or price_gain < self.minimum_price_gain
                or own_gain < self.minimum_own_gain
                or release_step >= 708
            ):
                continue
            replace_sell(action, product, parent_sell - reserve)
            self.pending[product] = {"quantity": reserve, "release_step": release_step}
            changes.append({
                "product": product,
                "reserved": reserve,
                "release_step": release_step,
                "current_price": current_price,
                "projected_price": projected_price,
                "own_footprint": own_footprint[product],
                "rival_footprint": rival_footprint[product],
                "visible_own_yield": round(own_visible[product], 2),
            })
        if changes:
            self.telemetry.append({
                "type": "revealed_shop_overlay",
                "step": step,
                "day": day,
                "hour": hour,
                "open_shops": shops,
                "changes": changes,
            })

    def _record_prediction(self, observation: Any, day: int) -> None:
        if (day + 1) % 3 != 0 or day + 1 > 24:
            return
        central = empty_count(observation)
        scenarios = []
        for delta in (-1, 0, 1):
            count = max(0, min(200, central + delta))
            result = self.posterior.distribution(day, count)
            scenarios.append({
                "empty_count": count,
                "status": result["status"],
                "predicted_shop": result["predicted_shop"],
                "top_probability": round(float(result["top_probability"]), 6),
                "entropy_bits": round(float(result["entropy_bits"]), 6),
                "candidate_count": int(result["candidate_count"]),
            })
        self.telemetry.append({
            "type": "next_shop_prediction",
            "made_at_day": day,
            "unlock_day": day + 1,
            "scenarios": scenarios,
            "acted": False,
            "reason": "sampled posterior is diagnostic, not a proven full-domain oracle",
        })

    def __call__(self, observation: Any, configuration: Any = None) -> dict[str, Any]:
        step = int(get(observation, "step", 0) or 0)
        day = int(get(observation, "day", step // 24) or 0)
        hour = int(get(observation, "hour", step % 24) or 0)
        player = int(get(observation, "player", 0) or 0)
        if step <= self.last_step:
            self._reset()
        self.last_step = step
        self._observe(observation, day, hour)
        self.shop_count = len(list(get(get(observation, "town", {}) or {}, "unlocked_shops", []) or []))

        action = copy_action(self.parent(observation, configuration))
        self._settle(observation, action, step)
        self._revealed_shop_overlay(observation, action, step, day, hour, player)
        if hour == 23:
            self._record_prediction(observation, day)

        self.previous_tiles = predictor.copy_tiles(observation)
        self.previous_unit_positions = predictor.unit_positions(observation)
        self.previous_day = day
        self.previous_hour = hour
        return action
