#!/usr/bin/env python3
"""
atlas_switchboard - a state-aware Kaggriculture agent that routes between
several reconstructed top-five macro-strategy families, using the same
executor as corrected Atlas (agents/atlas_profile.py).

WHERE IT COMES FROM
--------------------
experiments/build_switchboard_profiles.py reused Atlas's own extraction/
clustering pipeline (experiments/build_atlas_profile.py) - same manifest,
same replay corpus, same macro features, same clustering - and kept every
cluster whose submission-purity clears >= 0.7 (dominated by one real
top-five submission, not a blend of different agents' policies), the same
bar Atlas's own family had to clear. On the current corpus that is THREE
families:

  family 4 (DEFAULT): n=54, win_rate=0.76, submission 56401905
      ("Unknown Mother-Goose") - identical to corrected Atlas's family.
  family 3: n=29, win_rate=0.72, submission 56416487 ("ymg_aq").
  family 1: n=60, win_rate=0.72, submission 56407295 ("Majkel1337").

Every family's schedule carries the SAME workforce correction as Atlas:
daily crew target is the state-based median crew size (len(farm["hands"])
at a safe mid-day hour), not the interpolated-through-midnight-zero value
- see agents/atlas_profile.py's WORKFORCE CORRECTION note for the full
story of why that matters.

ROUTING
-------
Built from ALL 300 trajectories (wins AND losses, ties worth half a win -
never fit from winners alone), with Beta(1,1) (Laplace) smoothing on each
context/family cell's win rate, and a support floor of >= 8 DISTINCT
EPISODES per cell (not trajectory count - two rows can share one episode
when two target players faced each other, and that must not double-count
as support). A candidate family is only adopted over the default when its
smoothed win rate clears the default's by >= 0.10 in that exact context.
These are observational routing hypotheses read off historical outcomes,
not a claim that switching *causes* the win, and not an offline ladder
rating.

Re-evaluated at three decision points - 72, 144, 216 - each with a 4-tier
back-off, most to least specific:

  1. revealed shops + seat + coarse opponent farm descriptors
  2. revealed shops + seat
  3. revealed shops
  4. default family (corrected Atlas's own)

"Revealed shops" is every shop unlocked so far, in first-seen order
(cumulative, growing across the three decision points - never a future
shop). "Coarse opponent descriptors" are bucketed land/crop-count/animal-
count/workforce read from obs["farms"][opponent] - public state, visible
to both players (see kaggle_environments' own I/O contract) - NEVER the
opponent's shed, seeds, or carried inventory, which isn't in our
observation at all and is never used. Opponent workforce specifically
uses the SAME fix as our own crew count: hands observed at a non-midnight
hour only, tracked across the episode so far; a context where we've only
ever seen the opponent at hour 0 reads "unknown," never "0" - the same
nightly-reset artifact this whole repair is about, applied symmetrically
to what we can see of them.

On the current corpus, exactly ONE tier at ONE decision point ever clears
the bar: at step 72, "revealed shops" alone (tier 3) routes to family 1
when the first shop is YARN_STORE (Beta-smoothed win rate 0.846 vs the
default's 0.727, n=11 distinct episodes). Every seat-added and opponent-
descriptor-added tier, at all three decision points, and every other
shops-only context, came back with zero qualifying cells - reported
honestly rather than manufactured: splitting 300 trajectories across
seat and four opponent buckets on top of a shop signature fragments the
data far below the 8-episode floor almost everywhere. Verified against
experiments/build_switchboard_routing_v2.py's own printed per-tier counts
(28-111 contexts touched per tier, 0 of them non-default outside the one
exception above).

The chosen family FREEZES permanently at the first turn >= 216 (never
reconsidered again, even if new information arrives later - matching the
instruction not to keep second-guessing once a season is nearly a third
over). Before switching away from the default at ANY decision point, a
compatibility check must pass: the candidate's targets must not ask for
LESS land, FEWER animals, or FEWER hands than are already committed (all
three are effectively irreversible commitments once made), and the
candidate's crop plan must still contain at least one crop that can
mature before the season ends. A candidate that fails this check is
rejected and the default family is used instead for that decision - the
same "sparse or incompatible falls back to corrected Atlas" rule,
extended from "we don't trust this data" to "this specific commitment
isn't physically reachable from where we already are."

No raw coordinate tape is copied anywhere in this file; every target is a
state-derived macro quantity the executor below pursues through the real
legality/movement machinery, exactly as in Atlas.

Standard library only - zero imports at all. CROPS/ANIMALS/MARKET_PARAMS/
PRICE_FLOOR are inlined directly from the engine's own tables, the same
as agents/atlas_profile.py, so this file has no runtime dependency on the
kaggle_environments package being present, on any path, under any version.
"""

# Inlined directly from the engine's own tables - see agents/atlas_profile.py
# for the identical block and its provenance note.
PRICE_FLOOR = 1
CROPS = {
    "WHEAT":      {"seed": 10,  "first_yield_day": 2,  "max_yield_day": 4,  "interval": 0, "max_yield": 6, "ongoing": False},
    "CARROT":     {"seed": 20,  "first_yield_day": 2,  "max_yield_day": 3,  "interval": 0, "max_yield": 4, "ongoing": False},
    "TOMATO":     {"seed": 50,  "first_yield_day": 8,  "max_yield_day": 8,  "interval": 1, "max_yield": 4, "ongoing": True},
    "STRAWBERRY": {"seed": 100, "first_yield_day": 10, "max_yield_day": 10, "interval": 2, "max_yield": 4, "ongoing": True},
    "MELON":      {"seed": 80,  "first_yield_day": 10, "max_yield_day": 12, "interval": 0, "max_yield": 6, "ongoing": False},
}
ANIMALS = {
    "GOOSE": {"cost": 300, "structure": "COOP",    "first_yield_day": 4, "interval": 1, "max_held": 4, "product": "EGG"},
    "COW":   {"cost": 400, "structure": "PASTURE", "first_yield_day": 8, "interval": 2, "max_held": 6, "product": "MILK"},
    "SHEEP": {"cost": 500, "structure": "PASTURE", "first_yield_day": 6, "interval": 3, "max_held": 6, "product": "WOOL"},
}
MARKET_PARAMS = {
    "WHEAT": {"base": 25}, "CARROT": {"base": 35}, "TOMATO": {"base": 60},
    "STRAWBERRY": {"base": 120}, "MELON": {"base": 250}, "EGG": {"base": 50},
    "MILK": {"base": 160}, "WOOL": {"base": 200}, "FERTILIZER": {"base": 100},
}

# ---------------------------------------------------------------------
# Season / board mechanics (engine facts, not strategy)
# ---------------------------------------------------------------------
SEASON_DAYS = 30
TURNS_PER_DAY = 24
PLANTABLE_CROPS = ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON"]
FERTILIZABLE_CROPS = ("TOMATO", "STRAWBERRY")
LAND_ORDER = ["NE", "SW", "SE"]
LAND_PRICES = [1000, 2000, 4000]
MAX_MARKET_ORDERS_PER_TURN = 10
FARM_HAND_COST_MULT = 1
ANIMAL_STRUCTURE_KINDS = {info["structure"] for info in ANIMALS.values() if info.get("structure")}

CASH_RESERVE_FLOOR = 15
MAX_SELL_PER_TURN_GENERIC = 15
HIRE_BEFORE_HOUR = 6
MAX_HIRES_PER_TURN_GENERIC = 12
LIQUIDATION_START_DAY = 27
SEED_BATCH_CAP = 5
ANIMAL_CASH_RESERVE_FLOOR = 60

DECISION_TURNS = [72, 144, 216]
ROUTE_FREEZE_TURN = 216


def _hire_cost(n_already_today):
    a, b = 1, 1
    for _ in range(n_already_today):
        a, b = b, a + b
    return FARM_HAND_COST_MULT * a


# =======================================================================
# FAMILIES - three reconstructed macro profiles. Each entry's
# "schedule"/"daily_crew" is exactly the shape Atlas embeds for its one
# family - see agents/atlas_profile.py's module docstring for the full
# extraction methodology (same pipeline, same corrections).
# =======================================================================
DEFAULT_FAMILY = 4

FAMILIES = {
    4: {  # submission 56401905, n=54, win_rate=0.76 - identical to Atlas's family
        "daily_crew": [4, 4, 6, 5, 5, 5, 8, 8, 8, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11,
                       11, 11, 11, 11, 11, 11, 11, 11, 11, 11],
        "schedule": [
            {"turn": 0,   "usable_land": 25,
             "planted_by_crop": {"WHEAT": 0, "CARROT": 0, "TOMATO": 0, "STRAWBERRY": 0, "MELON": 0},
             "animals_by_species": {"COW": 0, "GOOSE": 0, "SHEEP": 0},
             "shed_by_product": {"WHEAT": 0, "CARROT": 0, "TOMATO": 0, "STRAWBERRY": 0, "MELON": 0,
                                  "EGG": 0, "MILK": 0, "WOOL": 0, "FERTILIZER": 0}},
            {"turn": 72,  "usable_land": 25,
             "planted_by_crop": {"WHEAT": 7, "CARROT": 0, "TOMATO": 0, "STRAWBERRY": 3, "MELON": 10},
             "animals_by_species": {"COW": 2, "GOOSE": 0, "SHEEP": 3},
             "shed_by_product": {"WHEAT": 6, "CARROT": 0, "TOMATO": 0, "STRAWBERRY": 0, "MELON": 0,
                                  "EGG": 0, "MILK": 0, "WOOL": 0, "FERTILIZER": 0}},
            {"turn": 144, "usable_land": 25,
             "planted_by_crop": {"WHEAT": 0, "CARROT": 0, "TOMATO": 0, "STRAWBERRY": 10, "MELON": 10},
             "animals_by_species": {"COW": 2, "GOOSE": 0, "SHEEP": 3},
             "shed_by_product": {"WHEAT": 8, "CARROT": 0, "TOMATO": 0, "STRAWBERRY": 0, "MELON": 0,
                                  "EGG": 0, "MILK": 0, "WOOL": 0, "FERTILIZER": 1}},
            {"turn": 216, "usable_land": 75,
             "planted_by_crop": {"WHEAT": 10, "CARROT": 0, "TOMATO": 0, "STRAWBERRY": 16, "MELON": 12},
             "animals_by_species": {"COW": 7, "GOOSE": 1, "SHEEP": 3},
             "shed_by_product": {"WHEAT": 18, "CARROT": 0, "TOMATO": 0, "STRAWBERRY": 0, "MELON": 0,
                                  "EGG": 0, "MILK": 0, "WOOL": 0, "FERTILIZER": 7}},
            {"turn": 288, "usable_land": 75,
             "planted_by_crop": {"WHEAT": 29, "CARROT": 0, "TOMATO": 1, "STRAWBERRY": 18, "MELON": 2},
             "animals_by_species": {"COW": 8, "GOOSE": 3, "SHEEP": 3},
             "shed_by_product": {"WHEAT": 51, "CARROT": 0, "TOMATO": 0, "STRAWBERRY": 0, "MELON": 6,
                                  "EGG": 0, "MILK": 0, "WOOL": 0, "FERTILIZER": 10}},
            {"turn": 360, "usable_land": 75,
             "planted_by_crop": {"WHEAT": 21, "CARROT": 0, "TOMATO": 2, "STRAWBERRY": 26, "MELON": 2},
             "animals_by_species": {"COW": 8, "GOOSE": 3, "SHEEP": 3},
             "shed_by_product": {"WHEAT": 47, "CARROT": 0, "TOMATO": 0, "STRAWBERRY": 9, "MELON": 0,
                                  "EGG": 4, "MILK": 1, "WOOL": 4, "FERTILIZER": 12}},
            {"turn": 432, "usable_land": 75,
             "planted_by_crop": {"WHEAT": 19, "CARROT": 0, "TOMATO": 4, "STRAWBERRY": 26, "MELON": 0},
             "animals_by_species": {"COW": 8, "GOOSE": 3, "SHEEP": 5},
             "shed_by_product": {"WHEAT": 41, "CARROT": 0, "TOMATO": 0, "STRAWBERRY": 14, "MELON": 0,
                                  "EGG": 4, "MILK": 0, "WOOL": 7, "FERTILIZER": 10}},
            {"turn": 504, "usable_land": 75,
             "planted_by_crop": {"WHEAT": 25, "CARROT": 1, "TOMATO": 6, "STRAWBERRY": 18, "MELON": 0},
             "animals_by_species": {"COW": 8, "GOOSE": 3, "SHEEP": 5},
             "shed_by_product": {"WHEAT": 42, "CARROT": 0, "TOMATO": 4, "STRAWBERRY": 8, "MELON": 0,
                                  "EGG": 4, "MILK": 7, "WOOL": 5, "FERTILIZER": 9}},
            {"turn": 576, "usable_land": 75,
             "planted_by_crop": {"WHEAT": 28, "CARROT": 12, "TOMATO": 4, "STRAWBERRY": 14, "MELON": 0},
             "animals_by_species": {"COW": 8, "GOOSE": 3, "SHEEP": 6},
             "shed_by_product": {"WHEAT": 43, "CARROT": 0, "TOMATO": 4, "STRAWBERRY": 12, "MELON": 0,
                                  "EGG": 4, "MILK": 2, "WOOL": 6, "FERTILIZER": 8}},
            {"turn": 648, "usable_land": 75,
             "planted_by_crop": {"WHEAT": 29, "CARROT": 16, "TOMATO": 3, "STRAWBERRY": 8, "MELON": 0},
             "animals_by_species": {"COW": 8, "GOOSE": 3, "SHEEP": 6},
             "shed_by_product": {"WHEAT": 39, "CARROT": 17, "TOMATO": 6, "STRAWBERRY": 10, "MELON": 0,
                                  "EGG": 0, "MILK": 5, "WOOL": 5, "FERTILIZER": 5}},
            {"turn": 696, "usable_land": 75,
             "planted_by_crop": {"WHEAT": 17, "CARROT": 6, "TOMATO": 1, "STRAWBERRY": 8, "MELON": 0},
             "animals_by_species": {"COW": 7, "GOOSE": 3, "SHEEP": 1},
             "shed_by_product": {"WHEAT": 33, "CARROT": 11, "TOMATO": 4, "STRAWBERRY": 4, "MELON": 0,
                                  "EGG": 2, "MILK": 5, "WOOL": 5, "FERTILIZER": 2}},
        ],
    },
    3: {  # submission 56416487 ("ymg_aq"), n=29, win_rate=0.72
        "daily_crew": [4, 3, 6, 6, 6, 6, 8, 9, 8, 10, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11,
                       11, 11, 11, 11, 11, 11, 11, 11, 10, 10],
        "schedule": [
            {"turn": 0,   "usable_land": 25,
             "planted_by_crop": {"WHEAT": 0, "CARROT": 0, "TOMATO": 0, "STRAWBERRY": 0, "MELON": 0},
             "animals_by_species": {"COW": 0, "GOOSE": 0, "SHEEP": 0},
             "shed_by_product": {"WHEAT": 0, "CARROT": 0, "TOMATO": 0, "STRAWBERRY": 0, "MELON": 0,
                                  "EGG": 0, "MILK": 0, "WOOL": 0, "FERTILIZER": 0}},
            {"turn": 72,  "usable_land": 25,
             "planted_by_crop": {"WHEAT": 5, "CARROT": 0, "TOMATO": 0, "STRAWBERRY": 2, "MELON": 12},
             "animals_by_species": {"COW": 2, "GOOSE": 0, "SHEEP": 3},
             "shed_by_product": {"WHEAT": 8, "CARROT": 0, "TOMATO": 0, "STRAWBERRY": 0, "MELON": 0,
                                  "EGG": 0, "MILK": 0, "WOOL": 0, "FERTILIZER": 0}},
            {"turn": 144, "usable_land": 25,
             "planted_by_crop": {"WHEAT": 0, "CARROT": 0, "TOMATO": 0, "STRAWBERRY": 8, "MELON": 12},
             "animals_by_species": {"COW": 2, "GOOSE": 0, "SHEEP": 3},
             "shed_by_product": {"WHEAT": 0, "CARROT": 0, "TOMATO": 0, "STRAWBERRY": 0, "MELON": 0,
                                  "EGG": 0, "MILK": 0, "WOOL": 0, "FERTILIZER": 0}},
            {"turn": 216, "usable_land": 50,
             "planted_by_crop": {"WHEAT": 4, "CARROT": 0, "TOMATO": 1, "STRAWBERRY": 21, "MELON": 12},
             "animals_by_species": {"COW": 5, "GOOSE": 0, "SHEEP": 3},
             "shed_by_product": {"WHEAT": 0, "CARROT": 0, "TOMATO": 0, "STRAWBERRY": 0, "MELON": 0,
                                  "EGG": 0, "MILK": 6, "WOOL": 0, "FERTILIZER": 2}},
            {"turn": 288, "usable_land": 75,
             "planted_by_crop": {"WHEAT": 27, "CARROT": 0, "TOMATO": 1, "STRAWBERRY": 23, "MELON": 2},
             "animals_by_species": {"COW": 8, "GOOSE": 1, "SHEEP": 10},
             "shed_by_product": {"WHEAT": 1, "CARROT": 0, "TOMATO": 0, "STRAWBERRY": 0, "MELON": 6,
                                  "EGG": 0, "MILK": 0, "WOOL": 6, "FERTILIZER": 11}},
            {"turn": 360, "usable_land": 75,
             "planted_by_crop": {"WHEAT": 18, "CARROT": 5, "TOMATO": 3, "STRAWBERRY": 25, "MELON": 0},
             "animals_by_species": {"COW": 9, "GOOSE": 1, "SHEEP": 10},
             "shed_by_product": {"WHEAT": 40, "CARROT": 0, "TOMATO": 0, "STRAWBERRY": 9, "MELON": 8,
                                  "EGG": 0, "MILK": 5, "WOOL": 0, "FERTILIZER": 16}},
            {"turn": 432, "usable_land": 75,
             "planted_by_crop": {"WHEAT": 12, "CARROT": 4, "TOMATO": 5, "STRAWBERRY": 27, "MELON": 0},
             "animals_by_species": {"COW": 10, "GOOSE": 2, "SHEEP": 10},
             "shed_by_product": {"WHEAT": 41, "CARROT": 1, "TOMATO": 1, "STRAWBERRY": 15, "MELON": 4,
                                  "EGG": 3, "MILK": 0, "WOOL": 0, "FERTILIZER": 19}},
            {"turn": 504, "usable_land": 75,
             "planted_by_crop": {"WHEAT": 16, "CARROT": 6, "TOMATO": 7, "STRAWBERRY": 17, "MELON": 0},
             "animals_by_species": {"COW": 10, "GOOSE": 2, "SHEEP": 10},
             "shed_by_product": {"WHEAT": 29, "CARROT": 0, "TOMATO": 2, "STRAWBERRY": 15, "MELON": 1,
                                  "EGG": 0, "MILK": 3, "WOOL": 3, "FERTILIZER": 17}},
            {"turn": 576, "usable_land": 75,
             "planted_by_crop": {"WHEAT": 24, "CARROT": 12, "TOMATO": 6, "STRAWBERRY": 6, "MELON": 0},
             "animals_by_species": {"COW": 9, "GOOSE": 2, "SHEEP": 10},
             "shed_by_product": {"WHEAT": 31, "CARROT": 4, "TOMATO": 3, "STRAWBERRY": 10, "MELON": 1,
                                  "EGG": 1, "MILK": 4, "WOOL": 3, "FERTILIZER": 18}},
            {"turn": 648, "usable_land": 75,
             "planted_by_crop": {"WHEAT": 24, "CARROT": 14, "TOMATO": 4, "STRAWBERRY": 2, "MELON": 0},
             "animals_by_species": {"COW": 9, "GOOSE": 2, "SHEEP": 9},
             "shed_by_product": {"WHEAT": 32, "CARROT": 12, "TOMATO": 7, "STRAWBERRY": 4, "MELON": 1,
                                  "EGG": 2, "MILK": 3, "WOOL": 3, "FERTILIZER": 16}},
            {"turn": 696, "usable_land": 75,
             "planted_by_crop": {"WHEAT": 17, "CARROT": 6, "TOMATO": 4, "STRAWBERRY": 2, "MELON": 0},
             "animals_by_species": {"COW": 8, "GOOSE": 2, "SHEEP": 5},
             "shed_by_product": {"WHEAT": 26, "CARROT": 13, "TOMATO": 6, "STRAWBERRY": 0, "MELON": 1,
                                  "EGG": 0, "MILK": 5, "WOOL": 6, "FERTILIZER": 5}},
        ],
    },
    1: {  # submission 56407295 ("Majkel1337"), n=60, win_rate=0.72
        "daily_crew": [5, 5, 4, 6, 6, 6, 8, 8, 10, 10, 10, 12, 11, 11, 11, 11, 11, 12, 12, 12,
                       12, 11, 12, 12, 11, 12, 12, 11, 10, 10],
        "schedule": [
            {"turn": 0,   "usable_land": 25,
             "planted_by_crop": {"WHEAT": 0, "CARROT": 0, "TOMATO": 0, "STRAWBERRY": 0, "MELON": 0},
             "animals_by_species": {"COW": 0, "GOOSE": 0, "SHEEP": 0},
             "shed_by_product": {"WHEAT": 0, "CARROT": 0, "TOMATO": 0, "STRAWBERRY": 0, "MELON": 0,
                                  "EGG": 0, "MILK": 0, "WOOL": 0, "FERTILIZER": 0}},
            {"turn": 72,  "usable_land": 25,
             "planted_by_crop": {"WHEAT": 6, "CARROT": 0, "TOMATO": 0, "STRAWBERRY": 0, "MELON": 13},
             "animals_by_species": {"COW": 3, "GOOSE": 0, "SHEEP": 3},
             "shed_by_product": {"WHEAT": 0, "CARROT": 0, "TOMATO": 0, "STRAWBERRY": 0, "MELON": 0,
                                  "EGG": 0, "MILK": 0, "WOOL": 0, "FERTILIZER": 0}},
            {"turn": 144, "usable_land": 25,
             "planted_by_crop": {"WHEAT": 2, "CARROT": 0, "TOMATO": 0, "STRAWBERRY": 3, "MELON": 13},
             "animals_by_species": {"COW": 4, "GOOSE": 0, "SHEEP": 3},
             "shed_by_product": {"WHEAT": 13, "CARROT": 0, "TOMATO": 0, "STRAWBERRY": 0, "MELON": 0,
                                  "EGG": 0, "MILK": 0, "WOOL": 0, "FERTILIZER": 0}},
            {"turn": 216, "usable_land": 75,
             "planted_by_crop": {"WHEAT": 14, "CARROT": 0, "TOMATO": 0, "STRAWBERRY": 24, "MELON": 13},
             "animals_by_species": {"COW": 7, "GOOSE": 0, "SHEEP": 3},
             "shed_by_product": {"WHEAT": 10, "CARROT": 0, "TOMATO": 0, "STRAWBERRY": 0, "MELON": 0,
                                  "EGG": 0, "MILK": 0, "WOOL": 0, "FERTILIZER": 4}},
            {"turn": 288, "usable_land": 75,
             "planted_by_crop": {"WHEAT": 23, "CARROT": 0, "TOMATO": 0, "STRAWBERRY": 28, "MELON": 6},
             "animals_by_species": {"COW": 7, "GOOSE": 2, "SHEEP": 3},
             "shed_by_product": {"WHEAT": 59, "CARROT": 0, "TOMATO": 0, "STRAWBERRY": 0, "MELON": 6,
                                  "EGG": 0, "MILK": 7, "WOOL": 2, "FERTILIZER": 16}},
            {"turn": 360, "usable_land": 75,
             "planted_by_crop": {"WHEAT": 22, "CARROT": 0, "TOMATO": 2, "STRAWBERRY": 29, "MELON": 0},
             "animals_by_species": {"COW": 7, "GOOSE": 2, "SHEEP": 3},
             "shed_by_product": {"WHEAT": 42, "CARROT": 0, "TOMATO": 0, "STRAWBERRY": 6, "MELON": 0,
                                  "EGG": 2, "MILK": 8, "WOOL": 11, "FERTILIZER": 12}},
            {"turn": 432, "usable_land": 75,
             "planted_by_crop": {"WHEAT": 14, "CARROT": 0, "TOMATO": 9, "STRAWBERRY": 29, "MELON": 0},
             "animals_by_species": {"COW": 7, "GOOSE": 2, "SHEEP": 3},
             "shed_by_product": {"WHEAT": 44, "CARROT": 0, "TOMATO": 0, "STRAWBERRY": 7, "MELON": 0,
                                  "EGG": 4, "MILK": 9, "WOOL": 12, "FERTILIZER": 8}},
            {"turn": 504, "usable_land": 75,
             "planted_by_crop": {"WHEAT": 17, "CARROT": 0, "TOMATO": 10, "STRAWBERRY": 25, "MELON": 0},
             "animals_by_species": {"COW": 7, "GOOSE": 2, "SHEEP": 3},
             "shed_by_product": {"WHEAT": 20, "CARROT": 0, "TOMATO": 0, "STRAWBERRY": 21, "MELON": 0,
                                  "EGG": 0, "MILK": 15, "WOOL": 12, "FERTILIZER": 7}},
            {"turn": 576, "usable_land": 75,
             "planted_by_crop": {"WHEAT": 30, "CARROT": 8, "TOMATO": 9, "STRAWBERRY": 9, "MELON": 0},
             "animals_by_species": {"COW": 7, "GOOSE": 2, "SHEEP": 3},
             "shed_by_product": {"WHEAT": 20, "CARROT": 0, "TOMATO": 2, "STRAWBERRY": 46, "MELON": 0,
                                  "EGG": 2, "MILK": 8, "WOOL": 5, "FERTILIZER": 2}},
            {"turn": 648, "usable_land": 75,
             "planted_by_crop": {"WHEAT": 26, "CARROT": 20, "TOMATO": 7, "STRAWBERRY": 3, "MELON": 0},
             "animals_by_species": {"COW": 7, "GOOSE": 2, "SHEEP": 3},
             "shed_by_product": {"WHEAT": 24, "CARROT": 7, "TOMATO": 13, "STRAWBERRY": 36, "MELON": 0,
                                  "EGG": 0, "MILK": 8, "WOOL": 0, "FERTILIZER": 1}},
            {"turn": 696, "usable_land": 75,
             "planted_by_crop": {"WHEAT": 14, "CARROT": 12, "TOMATO": 4, "STRAWBERRY": 2, "MELON": 0},
             "animals_by_species": {"COW": 6, "GOOSE": 2, "SHEEP": 0},
             "shed_by_product": {"WHEAT": 15, "CARROT": 15, "TOMATO": 8, "STRAWBERRY": 23, "MELON": 0,
                                  "EGG": 0, "MILK": 12, "WOOL": 6, "FERTILIZER": 1}},
        ],
    },
}

# Routing tables. Sparse by design - a missing key means "no context-
# specific signal cleared the support/margin bar," which resolves to
# DEFAULT_FAMILY, exactly as an explicit fallback would.
# ROUTING_TABLES[decision_turn]["shops" | "shops_seat" | "shops_seat_opp"]
# -> {key: family_label}. Sparse by design: a missing key means "no tier
# at this decision point cleared the >=8-distinct-episode support bar
# with a >=0.10 Beta(1,1)-smoothed win-rate margin over the default,"
# which resolves to the default family - see module docstring and
# experiments/build_switchboard_routing_v2.py for the full methodology
# and what each tier actually found on the current corpus.
ROUTING_TABLES = {
    72: {
        "shops": {("YARN_STORE",): 1},
        "shops_seat": {},
        "shops_seat_opp": {},
    },
    144: {"shops": {}, "shops_seat": {}, "shops_seat_opp": {}},
    216: {"shops": {}, "shops_seat": {}, "shops_seat_opp": {}},
}


def _lerp(a, b, frac):
    return a + (b - a) * frac


def _lerp_dict(a, b, frac, keys):
    return {k: _lerp(a.get(k, 0), b.get(k, 0), frac) for k in keys}


def profile_target_at(turn, family):
    """Linearly interpolate `family`'s schedule to any turn 0-719 - same
    interpolation as Atlas, just against whichever family is active."""
    sched = family["schedule"]
    if turn <= sched[0]["turn"]:
        return sched[0]
    if turn >= sched[-1]["turn"]:
        return sched[-1]
    for i in range(len(sched) - 1):
        lo, hi = sched[i], sched[i + 1]
        if lo["turn"] <= turn <= hi["turn"]:
            span = hi["turn"] - lo["turn"]
            frac = (turn - lo["turn"]) / span if span else 0.0
            return {
                "turn": turn,
                "usable_land": _lerp(lo["usable_land"], hi["usable_land"], frac),
                "planted_by_crop": _lerp_dict(lo["planted_by_crop"], hi["planted_by_crop"], frac, PLANTABLE_CROPS),
                "animals_by_species": _lerp_dict(lo["animals_by_species"], hi["animals_by_species"], frac, ANIMALS.keys()),
                "shed_by_product": _lerp_dict(lo["shed_by_product"], hi["shed_by_product"], frac, MARKET_PARAMS.keys()),
            }
    return sched[-1]


def daily_crew_target(family, day):
    crew = family["daily_crew"]
    return crew[min(max(day, 0), len(crew) - 1)]


# ---------------------------------------------------------------------
# Observation readers, movement, tile targeting - legality/execution
# machinery, identical to agents/atlas_profile.py (this repo's proven
# executor). None of this decides WHAT to build/plant/sell, only HOW to
# legally do it once a profile-driven decision names a target.
# ---------------------------------------------------------------------
def get_player_farm(obs):
    farms = obs.get("farms")
    player = obs.get("player")
    if not isinstance(farms, list) or not isinstance(player, int):
        return None
    if player < 0 or player >= len(farms):
        return None
    return farms[player]


def get_tile_at(farm, x, y):
    tiles = farm.get("tiles") if farm else None
    if not tiles or y < 0 or y >= len(tiles):
        return None
    row = tiles[y]
    if x < 0 or x >= len(row):
        return None
    return row[x]


def get_current_tile(farm):
    farmer_pos = farm.get("farmer") if farm else None
    if not farmer_pos or len(farmer_pos) != 2:
        return None
    return get_tile_at(farm, farmer_pos[0], farmer_pos[1])


def shed_access_tiles(board_size):
    half = board_size // 2
    return [(half - 1, half - 1), (half, half - 1), (half - 1, half), (half, half)]


def is_shed_adjacent(x, y, board_size):
    return (x, y) in shed_access_tiles(board_size)


def step_toward(fx, fy, tx, ty):
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
    if tile.get("yield_units", 0) <= 0:
        return False
    crop_info = CROPS.get(tile.get("crop"))
    if not crop_info:
        return False
    first_yield_day = crop_info.get("first_yield_day", 0)
    return day - tile.get("planted_day", day) >= first_yield_day


def remaining_season_days(day):
    return (SEASON_DAYS - 1) - day


def has_plantable_seed(seeds, day):
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
            elif (isinstance(tile, dict) and tile.get("kind") in ANIMAL_STRUCTURE_KINDS
                  and "animal" not in tile and task == "empty_structure"):
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
    if target_a is None:
        return target_b
    if target_b is None:
        return target_a
    dist_a = abs(target_a[0] - fx) + abs(target_a[1] - fy)
    dist_b = abs(target_b[0] - fx) + abs(target_b[1] - fy)
    return target_a if dist_a <= dist_b else target_b


def wants_fertilizer(tile, day):
    """Only ongoing crops (TOMATO/STRAWBERRY) ever benefit - engine fact,
    not a preference - and only inside the window where the 3-day cover
    still catches a production tick."""
    if not (isinstance(tile, dict) and tile.get("kind") == "PLANT"):
        return False
    crop = tile.get("crop")
    if crop not in FERTILIZABLE_CROPS:
        return False
    if tile.get("fertilized_until_day", -1) >= day:
        return False
    crop_info = CROPS.get(crop) or {}
    first_yield_day = crop_info.get("first_yield_day")
    if first_yield_day is None:
        return False
    interval = crop_info.get("interval") or 1
    max_yield = crop_info.get("max_yield") or 1
    last_tick_age = first_yield_day - 1 + interval * (max_yield - 1)
    age = day - tile.get("planted_day", day)
    return (first_yield_day - 3) <= age <= last_tick_age


def find_fertilizer_target(farm, board_size, ux, uy, day, exclude=None):
    exclude = exclude or set()
    tiles = farm.get("tiles") or []
    best_target, best_distance = None, None
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
    tiles = shed_access_tiles(board_size)
    return min(tiles, key=lambda t: abs(t[0] - fx) + abs(t[1] - fy))


def get_market_state(obs):
    market = obs.get("market") or {}
    return {"prices": market.get("prices") or {}, "inventory": market.get("inventory") or {}}


def extract_state(obs):
    obs = obs or {}
    farm = get_player_farm(obs)
    private = obs.get("private") or {}
    tiles = farm.get("tiles") if farm else None
    day = obs.get("day", 0)
    hour = obs.get("hour", 0)
    return {
        "farm": farm,
        "private": private,
        "market_state": get_market_state(obs),
        "board_size": len(tiles) if tiles else 0,
        "day": day,
        "hour": hour,
        "turn": obs.get("step", day * TURNS_PER_DAY + hour),
    }


def unit_inventory(private, unit_idx):
    inventories = private.get("inventories") or []
    if 0 <= unit_idx < len(inventories) and isinstance(inventories[unit_idx], dict):
        return inventories[unit_idx]
    return {}


def carried_animal(inv):
    for animal in ANIMALS:
        if inv.get(animal, 0) > 0:
            return animal
    return None


def scan_animal_structures(farm, board_size):
    tiles = farm.get("tiles") or []
    filled = unfilled = 0
    for y in range(board_size):
        row = tiles[y] if y < len(tiles) else []
        for tile in row:
            if isinstance(tile, dict) and tile.get("kind") in ANIMAL_STRUCTURE_KINDS:
                if "animal" in tile:
                    filled += 1
                else:
                    unfilled += 1
    return filled, unfilled


_animal_pace_tracker = {"day": None, "count": 0}


def _animal_commitments_today(day):
    """How many new animal commitments (BUILD or BUY) we've already started
    today, in this process - see agents/atlas_profile.py's identical
    tracker for the full reasoning (one farmer, finite daily capacity)."""
    if _animal_pace_tracker["day"] != day:
        _animal_pace_tracker["day"] = day
        _animal_pace_tracker["count"] = 0
    return _animal_pace_tracker["count"]


def _record_animal_commitment(day):
    _animal_commitments_today(day)
    _animal_pace_tracker["count"] += 1


def farm_has_unaddressed_neglect(farm, board_size):
    tiles = farm.get("tiles") or []
    for y in range(board_size):
        row = tiles[y] if y < len(tiles) else []
        for tile in row:
            if not isinstance(tile, dict):
                continue
            if tile.get("kind") == "WEED":
                return True
            if tile.get("kind") in ANIMAL_STRUCTURE_KINDS and "animal" in tile:
                if not tile.get("fed_today") or not tile.get("cared_today"):
                    return True
    return False


def species_owned_counts(farm, private, board_size):
    counts = {a: 0 for a in ANIMALS}
    shed = private.get("shed", {})
    for a in ANIMALS:
        counts[a] += shed.get(a, 0)
    for inv in private.get("inventories") or []:
        if isinstance(inv, dict):
            for a in ANIMALS:
                counts[a] += inv.get(a, 0)
    tiles = farm.get("tiles") or []
    for y in range(board_size):
        row = tiles[y] if y < len(tiles) else []
        for tile in row:
            if isinstance(tile, dict) and tile.get("kind") in ANIMAL_STRUCTURE_KINDS:
                species = tile.get("animal")
                if species in counts:
                    counts[species] += 1
    return counts


def tile_quadrant(x, y, board_size):
    half = board_size // 2
    return ("N" if y < half else "S") + ("W" if x < half else "E")


def current_planted_by_crop(farm):
    counts = {c: 0 for c in PLANTABLE_CROPS}
    for row in farm.get("tiles") or []:
        for t in row:
            if isinstance(t, dict) and t.get("kind") == "PLANT":
                crop = t.get("crop")
                if crop in counts:
                    counts[crop] += 1
    return counts


# ---------------------------------------------------------------------
# Market mechanics mirror (price formula + price-path-aware sell pacing).
# ---------------------------------------------------------------------
def market_price(item, inventory):
    params = MARKET_PARAMS.get(item) or {}
    base = params.get("base", 50)
    return max(PRICE_FLOOR, int(round(base)))


def recommend_sell_quantity(item, current_inventory, available_quantity, min_acceptable_price, max_per_turn=None):
    """Simplified, monotone-decreasing model of the engine's real per-unit
    price walk - see agents/atlas_profile.py's identical function for the
    full reasoning."""
    available_quantity = int(round(available_quantity))
    if max_per_turn is not None:
        max_per_turn = int(round(max_per_turn))
    if available_quantity <= 0 or min_acceptable_price <= 0:
        return 0
    cap = available_quantity
    if max_per_turn is not None:
        cap = min(cap, max_per_turn)
    price = market_price(item, current_inventory)
    count = 0
    for _ in range(cap):
        if price < min_acceptable_price:
            break
        count += 1
        price = max(PRICE_FLOOR, int(price * 0.985))
    return count


# ---------------------------------------------------------------------
# Routing: which family is "active" this turn.
# ---------------------------------------------------------------------
_shops_seen_order = []
_frozen = {"decided": False, "family_label": None}


def _update_shops_seen(obs):
    town = obs.get("town") or {}
    for s in town.get("unlocked_shops") or []:
        if s not in _shops_seen_order:
            _shops_seen_order.append(s)


def _bucket(value, edges, labels):
    for e, lab in zip(edges, labels[:-1]):
        if value <= e:
            return lab
    return labels[-1]


def _land_bucket(tiles):
    return _bucket(tiles, [25, 50, 75], ["<=25", "<=50", "<=75", ">75"])


def _crop_count_bucket(n):
    return _bucket(n, [0, 9, 24], ["0", "1-9", "10-24", "25+"])


def _animal_count_bucket(n):
    return _bucket(n, [0, 3, 7], ["0", "1-3", "4-7", "8+"])


def _workforce_bucket(n):
    if n is None:
        return "unknown"
    return _bucket(n, [0, 4, 8], ["0", "1-4", "5-8", "9+"])


# Opponent workforce OBSERVED SO FAR (public - obs["farms"][opponent] is
# visible; only obs["private"] is ours alone). Tracked the same way our
# own shop history is: across turns in this process, never assumed from a
# midnight snapshot - hands=0 at hour 0 is the nightly reset artifact for
# the opponent too, not evidence they run no crew (see module docstring).
_opponent_max_hands_seen = {"value": None}


def _update_opponent_workforce_seen(obs, seat):
    if obs.get("hour") == 0:
        return  # the one guaranteed-empty moment - not evidence, skip it
    farms = obs.get("farms") or []
    opp_seat = 1 - seat
    if opp_seat >= len(farms) or not farms[opp_seat]:
        return
    h = len(farms[opp_seat].get("hands") or [])
    if _opponent_max_hands_seen["value"] is None or h > _opponent_max_hands_seen["value"]:
        _opponent_max_hands_seen["value"] = h


def _opponent_descriptor(obs, seat, board_size):
    """Coarse public descriptor of the opponent's farm right now - land,
    crop count, animal count (all from obs["farms"][opponent], visible),
    and workforce observed so far (tracked above, "unknown" rather than 0
    if we've only ever seen them at hour 0). Never their shed, seeds, or
    carried inventory - those aren't in our observation at all."""
    farms = obs.get("farms") or []
    opp_seat = 1 - seat
    if opp_seat >= len(farms) or not farms[opp_seat]:
        return None
    opp_farm = farms[opp_seat]
    unlocked = opp_farm.get("unlocked_quadrants") or ["NW"]
    tiles_per_quadrant = (board_size * board_size) // 4 if board_size else 25
    land = len(unlocked) * tiles_per_quadrant
    crops = animals = 0
    for row in opp_farm.get("tiles") or []:
        for t in row:
            if not isinstance(t, dict):
                continue
            if t.get("kind") == "PLANT":
                crops += 1
            elif "animal" in t:
                animals += 1
    return (_land_bucket(land), _crop_count_bucket(crops), _animal_count_bucket(animals),
            _workforce_bucket(_opponent_max_hands_seen["value"]))


def _lookup_routing_table(table, key_len):
    if len(_shops_seen_order) < key_len:
        return None
    return table.get(tuple(_shops_seen_order[:key_len]))


def _decide_family_at(decision_turn, seat, obs, board_size):
    """4-tier back-off at one decision turn: shops+seat+opponent ->
    shops+seat -> shops -> default. Returns a family label or None (=
    stay on whatever was already active / default)."""
    tables = ROUTING_TABLES.get(decision_turn)
    if not tables or len(_shops_seen_order) == 0:
        return None
    shops = tuple(_shops_seen_order)

    opp = _opponent_descriptor(obs, seat, board_size)
    if opp is not None:
        key = (shops, seat) + opp
        lab = tables["shops_seat_opp"].get(key)
        if lab is not None:
            return lab

    key = (shops, seat)
    lab = tables["shops_seat"].get(key)
    if lab is not None:
        return lab

    lab = tables["shops"].get(shops)
    if lab is not None:
        return lab
    return None


def family_switch_compatible(farm, private, board_size, day, turn, candidate_family):
    """Before switching away from the default family, verify the
    candidate's targets are actually reachable from where we already are
    - not just statistically favored. Land and built structures are
    irreversible commitments (no sell-land, no un-build), so a candidate
    that wants LESS of either than we already have is not a switch, it's
    a contradiction. A candidate whose entire crop plan has already aged
    out of maturing before season end is equally not reachable."""
    target = profile_target_at(turn, candidate_family)
    tiles_per_quadrant = (board_size * board_size) // 4 if board_size else 25
    unlocked = farm.get("unlocked_quadrants") or ["NW"]
    current_land = len(unlocked) * tiles_per_quadrant
    if target["usable_land"] < current_land:
        return False

    owned_animals_total = sum(species_owned_counts(farm, private, board_size).values())
    if sum(target["animals_by_species"].values()) < owned_animals_total:
        return False

    crop_targets = target["planted_by_crop"]
    if sum(crop_targets.values()) > 0:
        remaining_days = remaining_season_days(day)
        any_maturing = any(
            crop_targets.get(c, 0) > 0 and (CROPS.get(c) or {}).get("first_yield_day", 999) <= remaining_days
            for c in PLANTABLE_CROPS
        )
        if not any_maturing:
            return False

    # Labour capacity: a candidate asking for FEWER hands than we already
    # have hired today would strand crew we've already paid for - the
    # same "irreversible commitment" logic as land/animals (hands are
    # cheap and daily-renewable, but the crew already on payroll today is
    # a sunk, already-realized commitment for today).
    current_hands = len(farm.get("hands") or [])
    if daily_crew_target(candidate_family, day) < current_hands:
        return False

    return True


def resolve_active_family(farm, private, board_size, day, turn, obs, seat):
    """Which family's schedule the executor should pursue this turn.
    Reconsidered at each of DECISION_TURNS (72/144/216, back off through
    shops+seat+opponent -> shops+seat -> shops -> default at each one),
    then frozen permanently at the first turn >= ROUTE_FREEZE_TURN (216) -
    see module docstring for why (don't keep second-guessing once the
    season is a third over). A candidate is only ever adopted if
    family_switch_compatible passes; otherwise the default family is used
    for that decision, exactly as "sparse or incompatible falls back to
    corrected Atlas" specifies."""
    if _frozen["decided"]:
        return FAMILIES[_frozen["family_label"]]

    active_decision_turn = None
    for t in DECISION_TURNS:
        if turn >= t:
            active_decision_turn = t

    if active_decision_turn is None:
        return FAMILIES[DEFAULT_FAMILY]

    label = _decide_family_at(active_decision_turn, seat, obs, board_size)
    if label is None:
        label = DEFAULT_FAMILY
    if label != DEFAULT_FAMILY:
        candidate = FAMILIES.get(label, FAMILIES[DEFAULT_FAMILY])
        if not family_switch_compatible(farm, private, board_size, day, turn, candidate):
            label = DEFAULT_FAMILY

    if turn >= ROUTE_FREEZE_TURN:
        _frozen["decided"] = True
        _frozen["family_label"] = label

    return FAMILIES[label]


# ---------------------------------------------------------------------
# PROFILE-DRIVEN POLICY - identical in shape to agents/atlas_profile.py's,
# except every function takes the currently-active `family` explicitly
# instead of reading one module-level schedule.
# ---------------------------------------------------------------------
def decide_land_orders_switchboard(farm, board_size, turn, family):
    target = profile_target_at(turn, family)
    target_tiles = target["usable_land"]
    tiles_per_quadrant = (board_size * board_size) // 4 if board_size else 25
    unlocked = farm.get("unlocked_quadrants") or ["NW"]
    current_tiles = len(unlocked) * tiles_per_quadrant
    if current_tiles >= target_tiles:
        return []
    n_extra = len(unlocked) - 1
    if n_extra < 0 or n_extra >= len(LAND_ORDER):
        return []
    cost = LAND_PRICES[n_extra]
    money = farm.get("money", 0)
    if money - cost < CASH_RESERVE_FLOOR:
        return []
    return [["BUY_LAND"]]


def decide_hire_orders_switchboard(farm, day, hour, family):
    if hour >= HIRE_BEFORE_HOUR:
        return []
    target = daily_crew_target(family, day)
    hands_field = farm.get("hands")
    if hands_field is None:
        return []  # missing hands field (malformed obs) - unknown, not zero
    current = len(hands_field)
    if current >= target:
        return []
    money = farm.get("money", 0)
    hires_today = farm.get("hires_today", 0)
    shortfall = min(target - current, MAX_HIRES_PER_TURN_GENERIC)
    orders = []
    remaining_money = money
    for i in range(shortfall):
        cost = _hire_cost(hires_today + i)
        if remaining_money - cost < CASH_RESERVE_FLOOR:
            break
        remaining_money -= cost
        orders.append(["HIRE"])
    return orders


def choose_animal_to_build_switchboard(farm, private, board_size, day, turn, family, pending_builds=0, ux=None, uy=None):
    filled, unfilled = scan_animal_structures(farm, board_size)
    if unfilled > 0 or pending_builds > 0:
        return None
    targets = profile_target_at(turn, family)["animals_by_species"]
    total_target = sum(targets.values())
    if total_target <= 0 or filled >= total_target:
        return None
    if filled > 0 and farm_has_unaddressed_neglect(farm, board_size):
        return None
    if _animal_commitments_today(day) >= 1:
        return None
    owned = species_owned_counts(farm, private, board_size)
    money = farm.get("money", 0)
    remaining_days = remaining_season_days(day)
    best_species, best_deficit = None, 0
    for species, info in ANIMALS.items():
        cost = info.get("cost")
        first_yield_day = info.get("first_yield_day")
        if cost is None or first_yield_day is None or first_yield_day > remaining_days:
            continue
        if money < cost or money - cost < ANIMAL_CASH_RESERVE_FLOOR:
            continue
        deficit = targets.get(species, 0) - owned.get(species, 0)
        if deficit > best_deficit:
            best_deficit = deficit
            best_species = species
    return best_species


def decide_animal_market_actions_switchboard(farm, private, board_size, day, turn, family):
    actions = []
    targets = profile_target_at(turn, family)["animals_by_species"]
    total_target = sum(targets.values())
    filled_now, _ = scan_animal_structures(farm, board_size)
    blocked = (
        (filled_now > 0 and farm_has_unaddressed_neglect(farm, board_size))
        or _animal_commitments_today(day) >= 1
    )
    if total_target > 0 and not blocked:
        owned = species_owned_counts(farm, private, board_size)
        if sum(owned.values()) < total_target:
            money = farm.get("money", 0)
            remaining_days = remaining_season_days(day)
            best_species, best_deficit = None, 0
            for species, info in ANIMALS.items():
                cost = info.get("cost")
                first_yield_day = info.get("first_yield_day")
                if cost is None or first_yield_day is None or first_yield_day > remaining_days:
                    continue
                if cost > money or money - cost < ANIMAL_CASH_RESERVE_FLOOR:
                    continue
                deficit = targets.get(species, 0) - owned.get(species, 0)
                if deficit > best_deficit:
                    best_deficit = deficit
                    best_species = species
            if best_species:
                actions.append(["BUY_ANIMAL", best_species, 1])
                _record_animal_commitment(day)

    filled, _ = scan_animal_structures(farm, board_size)
    if filled > 0 and farm.get("money", 0) > 0:
        shed_wheat = private.get("shed", {}).get("WHEAT", 0)
        carried_wheat = sum(
            inv.get("WHEAT", 0) for inv in (private.get("inventories") or []) if isinstance(inv, dict)
        )
        if shed_wheat + carried_wheat < 2:
            actions.append(["BUY_PRODUCT", "WHEAT", 1])
    return actions


def choose_crop_switchboard(farm, private, day, turn, family, require_held_seed=False):
    money = farm.get("money", 0)
    seeds = private.get("seeds", {})
    remaining_days = remaining_season_days(day)
    targets = profile_target_at(turn, family)["planted_by_crop"]
    current = current_planted_by_crop(farm)

    best_crop, best_deficit = None, 0
    for crop in PLANTABLE_CROPS:
        info = CROPS.get(crop)
        if not info:
            continue
        first_yield_day = info.get("first_yield_day")
        if first_yield_day is not None and first_yield_day > remaining_days:
            continue
        have_seed = seeds.get(crop, 0) > 0
        if require_held_seed:
            if not have_seed:
                continue
        else:
            can_afford = money >= (info.get("seed") or 0)
            if not have_seed and not can_afford:
                continue
        deficit = targets.get(crop, 0) - current.get(crop, 0)
        if deficit > best_deficit:
            best_deficit = deficit
            best_crop = crop
    return best_crop


def seed_restock_quantity_switchboard(crop, farm, private, deficit):
    seeds = private.get("seeds", {})
    if seeds.get(crop, 0) > 0:
        return 0
    info = CROPS.get(crop)
    if not info:
        return 0
    seed_cost = info.get("seed")
    if not seed_cost:
        return 0
    money = farm.get("money", 0)
    wanted = max(1, min(int(round(deficit)), SEED_BATCH_CAP))
    quantity = 0
    while quantity < wanted:
        if seed_cost > money:
            break
        remaining_after = money - seed_cost
        if remaining_after < CASH_RESERVE_FLOOR:
            break
        money = remaining_after
        quantity += 1
    return quantity


def decide_market_actions_switchboard(farm, private, market_state, day, turn, family, reserved_wheat=0):
    actions = []
    shed = private.get("shed", {})
    inventory = market_state.get("inventory", {})
    liquidating = day >= LIQUIDATION_START_DAY
    full_target = profile_target_at(turn, family)
    targets = full_target["shed_by_product"]

    for product in MARKET_PARAMS:
        if product == "FERTILIZER" and not liquidating:
            continue
        quantity = shed.get(product, 0)
        if quantity <= 0:
            continue
        sell_quantity = quantity
        if product == "WHEAT":
            sell_quantity = max(0, quantity - reserved_wheat)
        if sell_quantity <= 0:
            continue

        target = 0 if liquidating else targets.get(product, 0)
        excess = sell_quantity - target
        if excess <= 0:
            continue

        base_price = (MARKET_PARAMS.get(product) or {}).get("base", 50)
        min_price = PRICE_FLOOR if liquidating else max(PRICE_FLOOR, int(base_price * 0.15))
        amount = recommend_sell_quantity(
            product, inventory.get(product, 10000), excess,
            min_acceptable_price=min_price, max_per_turn=MAX_SELL_PER_TURN_GENERIC,
        )
        if amount > 0:
            actions.append(["SELL", product, amount])

    preferred_crop = choose_crop_switchboard(farm, private, day, turn, family)
    if preferred_crop:
        crop_deficit = (full_target["planted_by_crop"].get(preferred_crop, 0)
                        - current_planted_by_crop(farm).get(preferred_crop, 0))
        qty = seed_restock_quantity_switchboard(preferred_crop, farm, private, crop_deficit)
        if qty > 0:
            actions.append(["BUY_SEED", preferred_crop, qty])

    held_fert = shed.get("FERTILIZER", 0) + sum(
        (inv or {}).get("FERTILIZER", 0) for inv in (private.get("inventories") or [])
        if isinstance(inv, dict)
    )
    if day <= SEASON_DAYS - 6 and held_fert < 6:
        wanted = sum(1 for row in (farm.get("tiles") or []) for tile in row if wants_fertilizer(tile, day))
        fert_price = market_state.get("prices", {}).get("FERTILIZER", 0)
        if wanted > held_fert and fert_price and farm.get("money", 0) - fert_price >= CASH_RESERVE_FLOOR:
            actions.append(["BUY_PRODUCT", "FERTILIZER", 1])

    return actions


# ---------------------------------------------------------------------
# Per-unit executor - identical priority ladder to agents/atlas_profile.py,
# with the WHAT-to-build/plant calls taking the active family explicitly.
# ---------------------------------------------------------------------
def choose_unit_action(state, ux, uy, unit_idx, family, claimed=None, pending_builds=None,
                        feed_claimed=None, plant_budget=None, wheat_budget=None):
    claimed = claimed if claimed is not None else set()
    pending_builds = pending_builds if pending_builds is not None else [0]
    feed_claimed = feed_claimed if feed_claimed is not None else set()

    farm = state["farm"]
    if not farm:
        return ["PASS"]

    board_size = state["board_size"]
    day = state["day"]
    turn = state["turn"]
    private = state["private"]
    seeds = private.get("seeds", {})
    plant_budget = plant_budget if plant_budget is not None else dict(seeds)
    wheat_budget = (wheat_budget if wheat_budget is not None
                    else {"WHEAT": private.get("shed", {}).get("WHEAT", 0)})
    inv = unit_inventory(private, unit_idx)
    tile = get_tile_at(farm, ux, uy)

    if (ux, uy) in claimed:
        tile = "TAKEN"

    is_animal_tile = isinstance(tile, dict) and "animal" in tile

    def act_here(action):
        claimed.add((ux, uy))
        return action

    def walk_to(target):
        direction = step_toward(ux, uy, target[0], target[1])
        if not direction:
            return None
        claimed.add((target[0], target[1]))
        return [direction]

    # 1. Feed before anything else - a missed feed is a permanent loss.
    if is_animal_tile and not tile.get("fed_today"):
        if inv.get("WHEAT", 0) > 0:
            feed_claimed.add((ux, uy))
            return act_here(["FEED"])

    # 2. Harvest.
    if isinstance(tile, dict) and tile.get("kind") == "PLANT" and is_harvestable(tile, day):
        return act_here(["HARVEST"])
    if is_animal_tile:
        animal = ANIMALS.get(tile.get("animal"), {})
        max_held = animal.get("max_held", 1)
        held = tile.get("yield_units", 0)
        if held >= max_held:
            return act_here(["HARVEST"])
        if tile.get("fertilizer_available"):
            return act_here(["COLLECT_FERTILIZER"])
        if held > 0 and (held >= max_held - 2 or day >= SEASON_DAYS - 2):
            return act_here(["HARVEST"])

    # 3. Water / care.
    if isinstance(tile, dict) and tile.get("kind") == "PLANT" and not tile.get("watered_today", True):
        return act_here(["WATER"])
    if is_animal_tile and not tile.get("cared_today"):
        return act_here(["CARE"])

    # 3b. Fertilize what we're standing on.
    if inv.get("FERTILIZER", 0) > 0 and wants_fertilizer(tile, day):
        return act_here(["FERTILIZE"])

    # 4. Place a carried animal.
    animal_in_hand = carried_animal(inv)
    if animal_in_hand and isinstance(tile, dict) and "animal" not in tile:
        structure = ANIMALS.get(animal_in_hand, {}).get("structure")
        if structure and tile.get("kind") == structure:
            return act_here(["PLACE", animal_in_hand])

    # 5. Shed errands.
    if is_shed_adjacent(ux, uy, board_size):
        shed = private.get("shed", {})
        if animal_in_hand is None:
            _, unfilled = scan_animal_structures(farm, board_size)
            if unfilled > 0:
                for animal in ANIMALS:
                    if shed.get(animal, 0) > 0:
                        return act_here(["PICKUP", animal, 1])
        available_wheat = wheat_budget.get("WHEAT", 0)
        if inv.get("WHEAT", 0) <= 0 and available_wheat > 0:
            if find_nearest_target(farm, board_size, ux, uy, "feed", day, exclude=claimed):
                batch = min(available_wheat, 3)
                wheat_budget["WHEAT"] = available_wheat - batch
                return act_here(["PICKUP", "WHEAT", batch])

    # 6. Urgent work elsewhere.
    feed_target = find_nearest_target(farm, board_size, ux, uy, "feed", day, exclude=set())
    if feed_target in feed_claimed:
        feed_target = None
    if feed_target:
        if inv.get("WHEAT", 0) <= 0:
            if wheat_budget.get("WHEAT", 0) > 0:
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

    # 7. Carrying an animal - find it a home.
    if animal_in_hand:
        structure_target = find_nearest_target(farm, board_size, ux, uy, "empty_structure", day, exclude=claimed)
        if structure_target:
            moved = walk_to(structure_target)
            if moved:
                return moved

    # 8. Dig a weed underfoot.
    if isinstance(tile, dict) and tile.get("kind") == "WEED":
        return act_here(["DIG"])

    # 9. Build or plant on empty ground - profile-driven, active family.
    if tile is None:
        animal_to_build = choose_animal_to_build_switchboard(
            farm, private, board_size, day, turn, family, pending_builds[0], ux, uy
        )
        if animal_to_build:
            pending_builds[0] += 1
            _record_animal_commitment(day)
            structure = ANIMALS[animal_to_build]["structure"]
            return act_here([f"BUILD_{structure}"])
        crop = choose_crop_switchboard(farm, private, day, turn, family)
        if crop and plant_budget.get(crop, 0) <= 0:
            crop = choose_crop_switchboard(farm, private, day, turn, family, require_held_seed=True)
        if crop and plant_budget.get(crop, 0) > 0:
            plant_budget[crop] -= 1
            return act_here(["PLANT", crop])

    # 10. Fertilizer logistics.
    shed_fertilizer = (private.get("shed") or {}).get("FERTILIZER", 0)
    if inv.get("FERTILIZER", 0) > 0:
        fertilize_target = find_fertilizer_target(farm, board_size, ux, uy, day, exclude=claimed)
        if fertilize_target:
            moved = walk_to(fertilize_target)
            if moved:
                return moved
    elif shed_fertilizer > 0 and find_fertilizer_target(farm, board_size, ux, uy, day, exclude=claimed):
        if is_shed_adjacent(ux, uy, board_size):
            return act_here(["PICKUP", "FERTILIZER", min(shed_fertilizer, 3)])
        moved = walk_to(nearest_shed_tile(ux, uy, board_size))
        if moved:
            return moved

    # 11. Reclaim a weed elsewhere.
    weed_target = find_nearest_target(farm, board_size, ux, uy, "weed", day, exclude=claimed)
    if weed_target:
        moved = walk_to(weed_target)
        if moved:
            return moved

    # 12. Walk toward the closest useful tile.
    fallback_target = find_nearest_target(farm, board_size, ux, uy, "any", day, seeds, exclude=claimed)
    if fallback_target and fallback_target != (ux, uy):
        moved = walk_to(fallback_target)
        if moved:
            return moved

    # 13. Nothing to do.
    return ["PASS"]


def choose_farmer_action(state, family, claimed=None, pending_builds=None, feed_claimed=None,
                          plant_budget=None, wheat_budget=None):
    farm = state.get("farm")
    if not farm:
        return ["PASS"]
    farmer_pos = farm.get("farmer")
    if not farmer_pos or len(farmer_pos) != 2:
        return ["PASS"]
    return choose_unit_action(state, farmer_pos[0], farmer_pos[1], 0, family, claimed, pending_builds,
                               feed_claimed, plant_budget, wheat_budget)


# ---------------------------------------------------------------------
# Agent entry point
# ---------------------------------------------------------------------
def switchboard(observation, configuration=None):
    """Always returns a well-formed action dict, even for a missing or
    malformed observation - any unexpected shape falls back to a safe
    PASS/empty response instead of crashing (a crash forfeits the match)."""
    try:
        obs = observation or {}
        seat = obs.get("player", 0)
        _update_shops_seen(obs)
        _update_opponent_workforce_seen(obs, seat)
        state = extract_state(obs)
        farm = state["farm"]
        if not farm:
            return {"farmer": ["PASS"], "hands": [], "market": []}

        board_size = state["board_size"]
        day = state["day"]
        hour = state["hour"]
        turn = state["turn"]
        private = state["private"]
        seeds = private.get("seeds", {})

        family = resolve_active_family(farm, private, board_size, day, turn, obs, seat)

        claimed = set()
        pending_builds = [0]
        feed_claimed = set()
        plant_budget = dict(seeds)
        wheat_budget = {"WHEAT": private.get("shed", {}).get("WHEAT", 0)}

        farmer_action = choose_farmer_action(
            state, family, claimed, pending_builds, feed_claimed, plant_budget, wheat_budget
        )
        hands_actions = [
            choose_unit_action(
                state, hand[0], hand[1], idx + 1, family, claimed, pending_builds, feed_claimed,
                plant_budget, wheat_budget,
            )
            for idx, hand in enumerate(farm.get("hands") or [])
            if isinstance(hand, (list, tuple)) and len(hand) == 2
        ]

        market = decide_hire_orders_switchboard(farm, day, hour, family)
        filled_animals, _ = scan_animal_structures(farm, board_size)
        reserved_wheat = filled_animals * 2
        market += decide_market_actions_switchboard(
            farm, private, state["market_state"], day, turn, family, reserved_wheat=reserved_wheat
        )
        market += decide_animal_market_actions_switchboard(farm, private, board_size, day, turn, family)
        market += decide_land_orders_switchboard(farm, board_size, turn, family)

        return {
            "farmer": farmer_action if isinstance(farmer_action, list) else ["PASS"],
            "hands": hands_actions,
            "market": market[:MAX_MARKET_ORDERS_PER_TURN],
        }
    except Exception:
        return {"farmer": ["PASS"], "hands": [], "market": []}


# The framework picks the LAST callable in this module's namespace, not a
# function literally named `agent` - keep this binding last.
agent = switchboard
