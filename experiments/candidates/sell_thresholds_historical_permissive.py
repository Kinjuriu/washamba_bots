"""
Sell-threshold audit, candidate B: the historical "halved" SELL_PRICE_THRESHOLDS
values, re-tested in isolation under TODAY's other settings.

CONTEXT (see experiments/sell_threshold_audit_report.md section 1 for the
full history): `SELL_PRICE_THRESHOLDS` was halved once, in commit 9c52c09
("experiment: land + crew + animals + early selling, as one change",
2026-08-18), bundled together with LIQUIDATION_START_DAY 19->10,
SHED_FORCE_SELL_THRESHOLD 70->40, MAX_HANDS_PER_DAY 8->15, and BUY_LAND.
Stated reason (commit message): "a 75-tile farm outproduces the old
gates" - the halving was meant to let a much bigger farm's higher
production clear the market before season end.

**That configuration is NOT current `main.py`.** Direct inspection
(`grep SELL_PRICE_THRESHOLDS main.py`, and `git blame` on every constant
9c52c09 touched) shows current `main.py` has LIQUIDATION_START_DAY=19,
SHED_FORCE_SELL_THRESHOLD=70, MAX_HANDS_PER_DAY=8, and
SELL_PRICE_THRESHOLDS at the ORIGINAL, pre-halving values - i.e. the
whole bundle except MAX_ANIMALS=4 and BUY_LAND itself was walked back at
some point after 2026-08-18, with no revert commit found. So "current
baseline" and "pre-halving" are the SAME configuration today - this
candidate exists to test the OTHER historical value set (the halved one)
in isolation, not to reproduce something already live.

ONE change from current `main.py`: SELL_PRICE_THRESHOLDS only. Everything
else - LIQUIDATION_START_DAY, MAX_HANDS_PER_DAY, SHED_FORCE_SELL_THRESHOLD,
MAX_ANIMALS, land, crop selection, pricing.py, opponent forecasting,
concurrent-selling mechanics - is untouched `main.py`, so any measured
difference is attributable to the threshold values alone, not the whole
9c52c09 bundle.

Usage:
    .venv/Scripts/python.exe experiments/candidates/sell_thresholds_historical_permissive.py
    .venv/Scripts/python.exe experiments/selfplay_agent.py experiments/candidates/sell_thresholds_historical_permissive.py 6
    .venv/Scripts/python.exe experiments/head_to_head.py experiments/candidates/sell_thresholds_historical_permissive.py main.py 6
    .venv/Scripts/python.exe experiments/paired_compare.py main.py experiments/candidates/sell_thresholds_historical_permissive.py
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

# The exact values commit 9c52c09 introduced on 2026-08-18, reproduced
# verbatim from `git show 9c52c09 -- main.py` rather than re-derived, so
# this candidate tests the historical value set precisely, not an
# approximation of it.
SELL_PRICE_THRESHOLDS_HISTORICAL_PERMISSIVE = {
    "WHEAT": 10,
    "CARROT": 12,
    "TOMATO": 20,
    "STRAWBERRY": 45,
    "MELON": 90,
    "EGG": 17,
    "WOOL": 70,
}

base.SELL_PRICE_THRESHOLDS = SELL_PRICE_THRESHOLDS_HISTORICAL_PERMISSIVE


def sell_thresholds_historical_permissive(obs):
    return base.nikaangukia_meroni(obs)


def _self_test(seeds=(0, 1, 2)):
    from kaggle_environments import make

    for seed in seeds:
        env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})
        env.run([sell_thresholds_historical_permissive, sell_thresholds_historical_permissive])
        a, b = env.steps[-1]
        print(f"seed {seed}: seat0 {a.reward:>8.0f} [{a.status}]   seat1 {b.reward:>8.0f} [{b.status}]")


agent = sell_thresholds_historical_permissive

if __name__ == "__main__":
    _self_test()
