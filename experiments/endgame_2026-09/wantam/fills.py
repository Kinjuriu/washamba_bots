"""Exact per-player sales ledger by monkeypatching the engine's per-unit commit."""
import kaggle_environments.envs.kaggriculture.kaggriculture as K
from collections import defaultdict
LEDGER = []
_orig = K._commit_unit
_STEP = {"s": 0}
_orig_pm = K._process_market
def _pm(state, env):
    _STEP["s"] = state[0].observation.get("step", 0) if hasattr(state[0].observation, "get") else 0
    _STEP["farms"] = [id(f) for f in state[0].observation.farms]
    return _orig_pm(state, env)
def _cu(op, item, price, farm, private, market, shed_capacity=100):
    before = farm["money"]
    r = _orig(op, item, price, farm, private, market, shed_capacity)
    seat = _STEP.get("farms", []).index(id(farm)) if id(farm) in _STEP.get("farms", []) else -1
    if farm["money"] != before:
        LEDGER.append((_STEP["s"], seat, op, item, farm["money"] - before))
    return r
K._commit_unit = _cu
K._process_market = _pm

def by_product(seat, start=336, end=720):
    out = defaultdict(lambda: [0, 0.0])
    for s, st, op, item, dm in LEDGER:
        if st == seat and start <= s < end:
            k = ("S:" if dm > 0 else "B:") + item
            out[k][0] += 1; out[k][1] += dm
    return {k: (v[0], int(v[1])) for k, v in sorted(out.items())}
