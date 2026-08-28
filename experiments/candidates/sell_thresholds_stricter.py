"""
Sell-threshold audit, candidate C: data-driven STRICTER thresholds - the
opposite direction from the historical halving, justified directly by
measured price data rather than by symmetry with candidate B.

CONTEXT: experiments/opponent_aware_sell_gate_exact_yield_report.md found
that pre-liquidation, `should_sell(MELON, ...)` is almost never False at
today's threshold (180) - only 17 of 866 checks across 12 self-play
seeds, all in a single day (18) right before LIQUIDATION_START_DAY (19).
STRAWBERRY, WHEAT, CARROT never produced a False check at all. That
result raised the question this candidate answers directly: is 180 (and
the other current thresholds) simply too low relative to where MELON's
price actually trades?

Measured directly (experiments/price_distribution probe, 6 self-play
seeds, `main.py` vs itself, pre-liquidation turns only - day < 19):

    product      min   p10   p25  median   p75   p90   max   base price
    MELON        171   206   212    260    268   271   272      250
    STRAWBERRY   120   132   147    182    214   234   263      120
    WOOL         116   141   189    199    215   234   243      200
    WHEAT         25    29    31     35     39    42    46       25
    CARROT        35    35    35     36     37    41    46       35

MELON's pre-liquidation MEDIAN spot price (260) is above its own base
price (250) - the market spends most of the season undersupplied, not
oversupplied, and the CURRENT threshold (180) sits below even the 10th
percentile (206) of observed prices. That is the actual reason
`should_sell` almost never says no: the bar is set so far under where
price actually trades that it is nearly unconditional. STRAWBERRY and
WHEAT show the identical pattern relative to their own thresholds.

This candidate raises each threshold to roughly its own measured 25th
percentile of pre-liquidation spot price (rounded) - a bar clearly above
where price spends most of its time, so `should_sell` is expected to say
no often enough to actually route decisions through the forward-looking
pricing backbone (estimate_future_price / recommend_sell_quantity's
price-path walk), without pinning the gate permanently closed the way
"raise it to the median" or higher would. Not chosen as an arbitrary
sweep value - it is the lowest round number that clears the OLD gate's
"nearly unconditional yes" failure mode while leaving real season-long
room for should_sell to still say yes on genuinely strong days (p75+ is
still comfortably above every new threshold here).

    WHEAT   20 -> 30     (p25 = 31)
    CARROT  25 -> 35     (p25 = 35)
    STRAWBERRY 90 -> 145 (p25 = 147)
    MELON   180 -> 210   (p25 = 212)
    WOOL    140 -> 190   (p25 = 189)

TOMATO, EGG and MILK are left at their current values (main.py's TOMATO
threshold and DEFAULT_SELL_THRESHOLD respectively) - no pre-liquidation
price series was measured for them (TOMATO is essentially never planted
by the current choose_crop scoring per CLAUDE.md's closed TOMATO-scoring
investigation; EGG is inert with no GOOSE in ACTIVE_ANIMALS; MILK's sell
gate was already recorded as a measured no-op at the current animal mix,
commit cc9645d) - changing a threshold with no measured price series
behind it would be an unjustified guess, which the task explicitly asked
this audit not to make.

ONE change from current `main.py`: SELL_PRICE_THRESHOLDS only. Everything
else - LIQUIDATION_START_DAY, MAX_HANDS_PER_DAY, SHED_FORCE_SELL_THRESHOLD,
MAX_ANIMALS, land, crop selection, pricing.py, opponent forecasting,
concurrent-selling mechanics - is untouched `main.py`.

Usage:
    .venv/Scripts/python.exe experiments/candidates/sell_thresholds_stricter.py
    .venv/Scripts/python.exe experiments/selfplay_agent.py experiments/candidates/sell_thresholds_stricter.py 6
    .venv/Scripts/python.exe experiments/head_to_head.py experiments/candidates/sell_thresholds_stricter.py main.py 6
    .venv/Scripts/python.exe experiments/paired_compare.py main.py experiments/candidates/sell_thresholds_stricter.py
"""
import os
import sys


def _find_repo_root():
    candidates = []
    if "__file__" in dir():
        this_dir = os.path.dirname(os.path.abspath(__file__))
        candidates.append(os.path.abspath(os.path.join(this_dir, "..", "..")))
    here = os.getcwd()
    for _ in range(4):
        candidates.append(here)
        here = os.path.dirname(here)
    for c in candidates:
        if os.path.isfile(os.path.join(c, "main.py")):
            return c
    return os.getcwd()


_ROOT = _find_repo_root()
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import main as base  # noqa: E402

# Built from the literal, hardcoded original values (not `dict(base.SELL_PRICE_THRESHOLDS)`
# at import time) deliberately: `base.SELL_PRICE_THRESHOLDS` is a mutable
# module global that experiments/candidates/sell_thresholds_historical_permissive.py
# (and any future threshold candidate) also monkeypatches at import time.
# Deriving from the live global would make TOMATO/EGG's "leave unchanged"
# values silently depend on which candidate module happened to import
# first in the current process - exactly the kind of import-order bug
# tests/test_sell_thresholds_candidates.py caught during development.
SELL_PRICE_THRESHOLDS_STRICTER = {
    "WHEAT": 30,
    "CARROT": 35,
    "TOMATO": 40,       # unchanged from current main.py - see module docstring
    "STRAWBERRY": 145,
    "MELON": 210,
    "EGG": 35,           # unchanged from current main.py - see module docstring
    "WOOL": 190,
}

base.SELL_PRICE_THRESHOLDS = SELL_PRICE_THRESHOLDS_STRICTER


def sell_thresholds_stricter(obs):
    return base.nikaangukia_meroni(obs)


def _self_test(seeds=(0, 1, 2)):
    from kaggle_environments import make

    for seed in seeds:
        env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})
        env.run([sell_thresholds_stricter, sell_thresholds_stricter])
        a, b = env.steps[-1]
        print(f"seed {seed}: seat0 {a.reward:>8.0f} [{a.status}]   seat1 {b.reward:>8.0f} [{b.status}]")


agent = sell_thresholds_stricter

if __name__ == "__main__":
    _self_test()
