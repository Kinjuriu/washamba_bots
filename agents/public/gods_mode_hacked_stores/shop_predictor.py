"""Observation-only next-shop inference for Kaggriculture 1.32.7.

The module has no dependency on a particular economic policy.  It can be
wrapped around any agent.  It reconstructs the exact daily weed-draw stream
from the hour-23 and hour-0 observations, filters a seed posterior, and gives
a conditional distribution for the next shop for any proposed empty-cell
count.

Important: a distribution is not called an exact prediction unless the seed
domain is exhaustive and exactly one seed remains.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
import random
from typing import Any, Iterable, Sequence


SHOPS = tuple(
    sorted(
        (
            "BAKERY",
            "BRUNCH_SPOT",
            "FARMERS_MARKET",
            "ICE_CREAM_SHOP",
            "PET_CAFE",
            "PIZZA_SHOP",
            "SMOOTHIE_SHOP",
            "YARN_STORE",
        )
    )
)
SEED_LIMIT = 2**31
SEED_MULTIPLIER = 1_000_003


def get(obj: Any, key: str, default: Any = None) -> Any:
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def tile_kind(tile: Any) -> str | None:
    return tile.get("kind") if isinstance(tile, dict) else None


def copy_tiles(observation: Any) -> tuple[tuple[tuple[Any, ...], ...], ...]:
    farms = list(get(observation, "farms", []) or [])
    return tuple(
        tuple(tuple(dict(tile) if isinstance(tile, dict) else tile for tile in row) for row in get(farm, "tiles", []) or [])
        for farm in farms
    )


@dataclass(frozen=True)
class DayEvidence:
    """RNG evidence observed before any action of the new day.

    ``weed_outcomes`` is in the engine scan order: player, row, column.  True
    means that this RNG draw produced a new weed; False means the cell stayed
    empty.  Old weeds are occupied cells and therefore are not RNG draws.
    """

    end_day: int
    weed_outcomes: tuple[bool | None, ...]
    actual_shop: str | None
    old_weeds_excluded: int = 0
    ambiguous_old_weeds: int = 0


def unit_positions(observation: Any) -> tuple[frozenset[tuple[int, int]], ...]:
    positions = []
    for farm in list(get(observation, "farms", []) or []):
        values = [get(farm, "farmer", [])] + list(get(farm, "hands", []) or [])
        positions.append(
            frozenset(
                (int(value[0]), int(value[1]))
                for value in values
                if isinstance(value, (list, tuple)) and len(value) >= 2
            )
        )
    return tuple(positions)


def extract_day_evidence(
    previous_tiles: Sequence[Sequence[Sequence[Any]]],
    previous_unit_positions: Sequence[frozenset[tuple[int, int]]],
    observation: Any,
    end_day: int,
    previous_shop_count: int,
) -> DayEvidence:
    """Recover the daily RNG outcomes from consecutive hour-23/hour-0 frames.

    At hour 0, every pre-spawn empty cell is either still ``None`` (failed
    weed draw) or contains a new weed (successful draw).  A weed that was
    already present at hour 23 was occupied and was not tested, so it is
    excluded.  This is exact unless an old weed is removed on the final turn
    and the same cell immediately respawns as a weed; that rare transition is
    observationally ambiguous and is reported in telemetry.
    """

    current = copy_tiles(observation)
    outcomes: list[bool | None] = []
    old_weeds = 0
    ambiguous_old_weeds = 0
    for player in range(min(2, len(current))):
        for y, row in enumerate(current[player]):
            for x, tile in enumerate(row):
                if tile is None:
                    outcomes.append(False)
                    continue
                if tile_kind(tile) != "WEED":
                    continue
                previous = None
                if player < len(previous_tiles) and y < len(previous_tiles[player]) and x < len(previous_tiles[player][y]):
                    previous = previous_tiles[player][y][x]
                if previous is None:
                    positions = previous_unit_positions[player] if player < len(previous_unit_positions) else frozenset()
                    if (x, y) in positions:
                        # A crop planted on hour 23 starts with one missed
                        # watering and the immediate daily refresh turns it
                        # into WEED.  Public state cannot distinguish that
                        # deterministic path from a failed/no-op action plus
                        # a random weed on the same previously empty tile.
                        outcomes.append(None)
                        ambiguous_old_weeds += 1
                    else:
                        outcomes.append(True)
                    continue

                # A plant can turn into WEED through lifespan decay or missed
                # watering without any RNG draw.  Any other occupied tile is
                # likewise skipped by _spawn_weeds.  Only a unit already on
                # this tile could have removed it on hour 23 and allowed an
                # immediate random respawn; retain that alternative.
                positions = previous_unit_positions[player] if player < len(previous_unit_positions) else frozenset()
                removable = not (isinstance(previous, dict) and "animal" in previous)
                if removable and (x, y) in positions:
                    outcomes.append(None)
                    ambiguous_old_weeds += 1
                else:
                    old_weeds += 1

    shops = list(get(get(observation, "town", {}) or {}, "unlocked_shops", []) or [])
    actual_shop = shops[-1] if len(shops) > previous_shop_count else None
    return DayEvidence(
        end_day=int(end_day),
        weed_outcomes=tuple(outcomes),
        actual_shop=actual_shop,
        old_weeds_excluded=old_weeds,
        ambiguous_old_weeds=ambiguous_old_weeds,
    )


def rng_for(seed: int, end_day: int) -> random.Random:
    return random.Random((int(seed) * SEED_MULTIPLIER) ^ int(end_day))


def seed_matches(seed: int, evidence: DayEvidence, weed_chance: float) -> bool:
    ambiguous = sum(value is None for value in evidence.weed_outcomes)
    # Usually ambiguous == 0.  Enumerating the small set is safer than
    # silently deleting the real seed when an old weed is DIGged on hour 23
    # and immediately respawns.
    for mask in range(1 << ambiguous):
        rng = rng_for(seed, evidence.end_day)
        ambiguity_index = 0
        valid = True
        for observed in evidence.weed_outcomes:
            if observed is None:
                consume_as_respawn = bool(mask & (1 << ambiguity_index))
                ambiguity_index += 1
                if consume_as_respawn and not (rng.random() < weed_chance):
                    valid = False
                    break
                continue
            if (rng.random() < weed_chance) != observed:
                valid = False
                break
        if valid and evidence.actual_shop is not None and rng.choice(SHOPS) != evidence.actual_shop:
            valid = False
        if valid:
            return True
    return False


def shop_for(seed: int, end_day: int, empty_count: int, weed_chance: float = 0.005) -> str:
    """Return the exact shop for a known seed and pre-spawn empty count."""

    del weed_chance  # Draw count matters; the threshold does not change RNG advancement.
    rng = rng_for(seed, end_day)
    for _ in range(max(0, int(empty_count))):
        rng.random()
    return rng.choice(SHOPS)


def _entropy(probabilities: dict[str, float]) -> float:
    return -sum(p * math.log2(p) for p in probabilities.values() if p > 0.0)


class SeedPosterior:
    """A discrete posterior over seeds.

    If ``exhaustive`` is true, the caller guarantees that the real seed is in
    the supplied domain.  Otherwise the seeds are particles sampled from the
    31-bit prior, and predictions remain estimates rather than proofs.
    """

    def __init__(self, seeds: Iterable[int], *, exhaustive: bool = False, weed_chance: float = 0.005) -> None:
        unique = dict.fromkeys(int(seed) for seed in seeds if 0 <= int(seed) < SEED_LIMIT)
        self.seeds = list(unique)
        self.exhaustive = bool(exhaustive)
        self.weed_chance = float(weed_chance)
        self.evidence: list[DayEvidence] = []
        self.initial_count = len(self.seeds)

    def update(self, evidence: DayEvidence) -> dict[str, Any]:
        before = len(self.seeds)
        self.seeds = [seed for seed in self.seeds if seed_matches(seed, evidence, self.weed_chance)]
        self.evidence.append(evidence)
        return {
            "end_day": evidence.end_day,
            "empty_draws": len(evidence.weed_outcomes),
            "new_weeds": sum(value is True for value in evidence.weed_outcomes),
            "weed_success_indices": [index for index, value in enumerate(evidence.weed_outcomes) if value is True],
            "ambiguous_draw_indices": [index for index, value in enumerate(evidence.weed_outcomes) if value is None],
            "actual_shop": evidence.actual_shop,
            "old_weeds_excluded": evidence.old_weeds_excluded,
            "ambiguous_old_weeds": evidence.ambiguous_old_weeds,
            "candidates_before": before,
            "candidates_after": len(self.seeds),
            "domain_is_exhaustive": self.exhaustive,
            "true_seed_is_proven": self.exhaustive and len(self.seeds) == 1,
        }

    def distribution(self, end_day: int, empty_count: int) -> dict[str, Any]:
        counts = {shop: 0 for shop in SHOPS}
        for seed in self.seeds:
            counts[shop_for(seed, end_day, empty_count)] += 1
        n = len(self.seeds)
        probabilities = {shop: (counts[shop] / n if n else 0.0) for shop in SHOPS}
        ranked = sorted(SHOPS, key=lambda shop: (-probabilities[shop], shop))
        top = ranked[0] if n else None
        top_probability = probabilities[top] if top is not None else 0.0
        runner_up_probability = probabilities[ranked[1]] if n > 0 else 0.0
        exact = self.exhaustive and n == 1
        # A non-exhaustive particle posterior can estimate a conditional
        # distribution, but cannot prove the hidden seed.  Keep the label
        # explicit so downstream policies can fail closed.
        if exact:
            status = "exact"
        elif n >= 256:
            status = "posterior_estimate"
        else:
            status = "insufficient_support"
        return {
            "end_day": int(end_day),
            "unlock_day": int(end_day) + 1,
            "empty_count": int(empty_count),
            "candidate_count": n,
            "domain_is_exhaustive": self.exhaustive,
            "status": status,
            "predicted_shop": top,
            "top_probability": top_probability,
            "runner_up_probability": runner_up_probability,
            "margin_over_runner_up": top_probability - runner_up_probability,
            "entropy_bits": _entropy(probabilities),
            "counts": counts,
            "probabilities": probabilities,
        }


def stratified_seed_particles(count: int, salt: int = 0x5EED5EED) -> list[int]:
    """Spread deterministic particles across the complete 31-bit seed range."""

    count = max(1, int(count))
    # An odd multiplier permutes the 31-bit integers.  Taking its first values
    # avoids the misleading ``range(N)`` assumption used by the first proof.
    multiplier = 1_103_515_245
    offset = int(salt) & (SEED_LIMIT - 1)
    return [((offset + i * multiplier) & (SEED_LIMIT - 1)) for i in range(count)]
