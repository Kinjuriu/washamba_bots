"""A reference opponent that actually competes for the market.

Every local opponent we have is blind in the same way. `pass`, `random` and
`starter` never sell at all, so the order book stays pristine and any change
to what or when we sell looks free - that is why `starter` blessed BUY_LAND
(#19) when the contested harnesses would not. Self-play fixes the selling but
not the scale: both sides are the same 25-tile farm, so a change that only
pays off at a bigger scale cannot win there either.

This is the missing third case: an opponent that farms more ground, keeps more
animals, and sells heavily from day 10 with no end-of-season cliff - the shape
`docs/REPLAY_ANALYSIS.md` found across four teams and two dates.

It is deliberately NOT a rewrite. It imports main.py, overrides the tuning
constants that control aggression and scale, and wraps the agent to add the
land purchases main.py does not make. Everything else - the unit-action
ladder, crop scoring, animal care - is main.py's, unchanged. That keeps it
honest as a harness: when our agent beats this, it is beating a strategy
difference, not a different codebase.

Loading it does not affect main.py. kaggle_environments exec's an agent file
into an isolated namespace rather than importing it, so this module's `import
main` is a separate object from the `main.py` playing the other seat.

Measured over 6 seeds, against main.py and against main.py's own self-play:

                        main.py vs this   main.py self-play
    main.py bank              58,654            54,536
    opponent bank             65,835                 -
    opponent wins               6/6                  -
    SELL orders/episode           242                190
    end MELON price                94                138

It wins every seed, and the melon price is the tell: 94 against 138 means our
own sales are landing into a market this opponent has already worked over.
That is the property no built-in has and self-play only half has.

Note WOOL ends HIGHER against it (237 vs 148), which looks wrong for an
opponent running more animals. It is not - it sells from day 10 rather than
dumping at liquidation, so the town has the rest of the season to absorb it.
Spreading sales over time really does hold price up, which is the same
mechanism CLAUDE.md records under market decay shapes.

What this is NOT: a replay clone. It is main.py scaled up and made to sell,
not an independent strategy reconstructed from ladder episodes (#21). Our own
agent's blind spots are still in here, so treat it as a harder, market-crowding
sparring partner rather than as ground truth about how the top agents play.

Usage - anywhere a harness takes an agent path:

    .venv/Scripts/python.exe experiments/head_to_head.py main.py experiments/bigfarm_opponent.py
    .venv/Scripts/python.exe experiments/bigfarm_opponent.py     # self-test
"""

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__)) if "__file__" in dir() else os.getcwd()
_ROOT = os.path.dirname(_HERE) if os.path.basename(_HERE) == "experiments" else os.getcwd()
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import main as base  # noqa: E402  (import after the sys.path fix above)

# ---------------------------------------------------------------------
# Sell hard, and early. This is the property that matters most.
#
# The point of this opponent is a contested order book, not a high score.
# An opponent that banks less but floods the market is a better instrument
# than one that banks more politely, because flooding is exactly what our
# built-in opponents cannot do.
# ---------------------------------------------------------------------
LIQUIDATION_START_DAY = 10          # main.py: 19 - the replays show no late cliff
SELL_THRESHOLD_SCALE = 0.5          # accept half the price main.py holds out for
SHED_FORCE_SELL_THRESHOLD = 40      # main.py: 70 - clear the shed sooner

# ---------------------------------------------------------------------
# Scale: more ground, more crew to tend it, more animals on it.
# ---------------------------------------------------------------------
LAND_BUY_DAYS = [6, 11]             # two quadrants, 25 tiles -> 75
LAND_PRICES = [1000, 2000, 4000]    # engine kaggriculture.py:96-97
LAND_CASH_RESERVE = 450             # never re-open the days 3-7 trough
MAX_HANDS_PER_DAY = 15              # main.py: 8 - a 75-tile farm needs the crew
MAX_ANIMALS = 4                     # main.py: 3 - and 4 is a cliff edge, see below

# The animal count is the one number here that cannot be tuned by eye. Measured
# against main.py over seeds 0-2, everything else in this file held fixed:
#
#   animals | opponent bank | beats main.py
#   --------|---------------|--------------
#      2    |     48,345    |     1/3
#      3    |     50,796    |     2/3
#      4    |     65,640    |     3/3
#      5    |        356    |     0/3
#
# Five animals does not degrade, it collapses - the days 3-7 cash trough empties,
# there is no money for feed, and the whole herd starves and escapes. That is the
# same failure CLAUDE.md records for a second sheep before the seed reserve was
# retuned, and it is why an opponent built by simply setting MAX_ANIMALS to the
# replays' 8-9 banks $429 instead of competing.

base.LIQUIDATION_START_DAY = LIQUIDATION_START_DAY
base.SELL_PRICE_THRESHOLDS = {
    product: max(1, int(price * SELL_THRESHOLD_SCALE))
    for product, price in base.SELL_PRICE_THRESHOLDS.items()
}
base.DEFAULT_SELL_THRESHOLD = max(1, int(base.DEFAULT_SELL_THRESHOLD * SELL_THRESHOLD_SCALE))
base.SHED_FORCE_SELL_THRESHOLD = SHED_FORCE_SELL_THRESHOLD
base.MAX_HANDS_PER_DAY = MAX_HANDS_PER_DAY
base.MAX_ANIMALS = MAX_ANIMALS


def land_order(farm, day):
    """`["BUY_LAND"]` when the next quadrant is due and affordable, else nothing.

    main.py never buys land, so this cannot be done with a constant override.
    The day gates track when the money actually exists rather than an arbitrary
    schedule - peak bank is ~$350 on day 6, ~$1,379 on day 7 and ~$19,600 on
    day 11 - which is why the sampled replays buy on days 6-7 and 11.
    """
    bought = len(farm.get("unlocked_quadrants") or ["NW"]) - 1
    if bought >= len(LAND_BUY_DAYS) or day < LAND_BUY_DAYS[bought]:
        return None
    if base.remaining_season_days(day) < 8:
        return None  # no season left to grow anything on it
    if farm.get("money", 0) < LAND_PRICES[bought] + LAND_CASH_RESERVE:
        return None
    return ["BUY_LAND"]


def bigfarm_opponent(obs):
    actions = base.nikaangukia_meroni(obs)
    try:
        farm = obs["farms"][obs["player"]]
        order = land_order(farm, obs.get("day", 0))
        if order is not None:
            # Ahead of the rest: orders past the per-turn cap are dropped
            # silently by the engine, and a missed quadrant does not come back.
            market = [order] + [o for o in actions.get("market") or [] if o != order]
            actions["market"] = market[: base.MAX_MARKET_ORDERS_PER_TURN]
    except (KeyError, IndexError, TypeError):
        return actions  # never let the harness opponent crash an episode
    return actions


def _self_test(seeds=(0, 1, 2)):
    """Bank, crew and end-of-season market state against main.py."""
    from kaggle_environments import make

    for seed in seeds:
        env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})
        env.run(["main.py", bigfarm_opponent])
        ours, theirs = env.steps[-1][0], env.steps[-1][1]
        obs = env.steps[-1][1].observation
        farm = obs["farms"][1]
        tiles = sum(1 for row in farm["tiles"] for t in row if t != "LOCKED")
        prices = {
            p: round(v)
            for p, v in obs["market"]["prices"].items()
            if p in ("MELON", "WHEAT", "WOOL", "MILK")
        }
        print(
            f"seed {seed}: main.py {ours.reward:>7.0f} [{ours.status}]   "
            f"bigfarm {theirs.reward:>7.0f} [{theirs.status}]   "
            f"tiles {tiles}  end prices {prices}"
        )


agent = bigfarm_opponent

if __name__ == "__main__":
    _self_test()
