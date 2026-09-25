"""Cadence probe: which obs["step"] phase (mod 4) sells on the post-drain inventory?

Builder A, splice build. Three checks on the real engine (kaggle-environments 1.32.7):

A. Drain timing, undoctored. A pass-vs-pass episode never trades, so every change in
   market inventory is town consumption. Each change is attributed to the interpreter
   call that produced it (row t's inventory is the result of the call that processed the
   actions decided at obs step t-1), and compared with WB_PriceModel.drain_per_step for
   that call's step and the shop list the agents saw.

B. Realized price by phase. Seat 0 sells 1 unit of each premium product (WOOL, MILK,
   STRAWBERRY) every step once a shop that consumes that product is unlocked; seat 1
   passes. The only doctoring: seat 0's shed starts with 600 of each product (no farm
   could produce that; the market, consumption and step counter are the engine's own).
   Realized prices are read from an instrumented _commit_unit, which also records the
   interpreter's step counter.

C. Index convention. Seat 0's farmer action encodes obs["step"] % 4 as a direction, so
   env.steps[i][0]["action"] can be matched to the observation it was decided from.

Usage:  .venv/Scripts/python.exe experiments/splice/_probe_cadence.py [seed]
"""
import collections
import os
import statistics as st
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import kaggle_environments.envs.kaggriculture.kaggriculture as K  # noqa: E402
from kaggle_environments import make  # noqa: E402

from price_model import WB_PriceModel  # noqa: E402

PREMIUM = ("WOOL", "MILK", "STRAWBERRY")
DIRS = ["NORTH", "EAST", "SOUTH", "WEST"]
PM = WB_PriceModel()

_CUR = {}
_LOG = []
_orig_pm = K._process_market
_orig_cu = K._commit_unit


def _pm(state, env):
    _CUR["farms"] = state[0].observation.farms
    _CUR["step"] = state[0].observation.get("step", 0)
    return _orig_pm(state, env)


def _cu(op, item, price, farm, private, market, shed_capacity=100):
    inv_before = market["inventory"][item]
    ok = _orig_cu(op, item, price, farm, private, market, shed_capacity)
    if ok:
        seat = 0 if farm is _CUR["farms"][0] else 1
        _LOG.append((seat, _CUR["step"], op, item, price, inv_before))
    return ok


def _install():
    K._process_market = _pm
    K._commit_unit = _cu


def _agent_obs(env, i):
    return env._Environment__get_shared_state(i).observation


def run(seed, seller):
    """Drive the episode by hand (env.run would reset the doctored shed)."""
    env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})
    env.reset(2)
    if seller:
        for item in PREMIUM:
            env.state[0].observation.private["shed"][item] = 600
    decided = {}
    while not env.done:
        o0, o1 = _agent_obs(env, 0), _agent_obs(env, 1)
        s = int(o0["step"])
        market = []
        if seller:
            shops = list(o0["town"]["unlocked_shops"])
            for item in PREMIUM:
                if any(item in K.SHOPS[n] for n in shops) and o0["private"]["shed"].get(item, 0) > 0:
                    market.append(["SELL", item, 1])
        a0 = {"farmer": [DIRS[s % 4]], "hands": [], "market": market}
        a1 = {"farmer": ["PASS"], "hands": [], "market": []}
        decided[s] = a0
        env.step([a0, a1])
    return env, decided


def check_drain(seed):
    env, _ = run(seed, seller=False)
    steps = env.steps
    by_phase = collections.Counter()
    exact = mismatch = 0
    for t in range(1, len(steps)):
        prev, cur = steps[t - 1][0]["observation"], steps[t][0]["observation"]
        s = int(prev["step"])                       # the call that produced row t
        assert int(cur["step"]) == t and s == t - 1
        shops = list(prev["town"]["unlocked_shops"])
        for item in K.PRODUCTS:
            d = prev["market"]["inventory"][item] - cur["market"]["inventory"][item]
            if d:
                by_phase[s % 4] += d
            if d == PM.drain_per_step(item, shops, s):
                exact += 1
            else:
                mismatch += 1
    shops_final = list(steps[-1][0]["observation"]["town"]["unlocked_shops"])
    return by_phase, exact, mismatch, shops_final


def check_prices(seed):
    _LOG.clear()
    env, decided = run(seed, seller=True)
    steps = env.steps
    # C. index convention
    conv_ok = sum(steps[i][0]["action"]["farmer"] == decided[i - 1]["farmer"] for i in range(1, len(steps)))
    conv_same_row = sum(steps[i][0]["action"]["farmer"] == decided.get(i, {}).get("farmer")
                        for i in range(1, len(steps) - 1))
    # B. realized prices vs the inventory each deciding observation showed
    obs_inv = {int(steps[i][0]["observation"]["step"]): steps[i][0]["observation"]["market"]["inventory"]
               for i in range(len(steps))}
    per_item = {}
    for item in PREMIUM:
        sales = [(s, price, inv) for (seat, s, op, it, price, inv) in _LOG if seat == 0 and op == "SELL" and it == item]
        # Each sale is quoted on exactly the inventory the deciding observation showed.
        same_as_obs = sum(PM.quote(item, obs_inv[s][item]) == price for s, price, _ in sales)
        # Group into drain cycles: the 4 calls after a tick are obs steps 4k+1..4k+4, and
        # the tick itself lands at the end of the call for 4k+4. Only complete cycles with
        # no $1 sale carry a price signal (a floor-only filter would bias the phases).
        cyc = collections.defaultdict(dict)
        for s, price, _ in sales:
            cyc[(s - 1) // 4][s % 4] = price
        full = [c for c in cyc.values() if len(c) == 4 and min(c.values()) > 1]
        by_phase = collections.defaultdict(list)
        for c in full:
            for ph, p in c.items():
                by_phase[ph].append(p)
        strict_best = collections.Counter()
        weak_best = collections.Counter()
        for c in full:
            top = max(c.values())
            winners = [ph for ph, p in c.items() if p == top]
            for ph in winners:
                weak_best[ph] += 1
            if len(winners) == 1:
                strict_best[winners[0]] += 1
        per_item[item] = {
            "sales": len(sales),
            "first_sale_step": sales[0][0] if sales else None,
            "mean_by_phase": {ph: round(st.mean(v), 2) for ph, v in sorted(by_phase.items())},
            "quote_matches_deciding_obs": f"{same_as_obs}/{len(sales)}",
            "cycles": len(full),
            "strict_best_phase": dict(strict_best),
            "weak_best_phase": dict(weak_best),
        }
    return conv_ok, conv_same_row, len(steps) - 1, per_item


def find_yarn_seed(start, stop):
    """First seed whose shop draws include YARN_STORE, so WOOL gets a drain cycle too."""
    for seed in range(start, stop):
        env, _ = run(seed, seller=False)
        if "YARN_STORE" in env.steps[-1][0]["observation"]["town"]["unlocked_shops"]:
            return seed
    return None


if __name__ == "__main__":
    seed = int(sys.argv[1]) if len(sys.argv) > 1 else 900
    _install()
    by_phase, exact, mismatch, shops = check_drain(seed)
    print(f"seed {seed}; shops unlocked by the end: {shops}")
    print("A. consumption units by (step of the producing call) % 4:", dict(sorted(by_phase.items())))
    print(f"   drain_per_step exact on {exact} of {exact + mismatch} product-calls (mismatches {mismatch})")
    conv_ok, conv_same, n, per_item = check_prices(seed)
    print(f"C. steps[i].action == action decided from obs step i-1: {conv_ok}/{n}; "
          f"== action decided from obs step i: {conv_same}/{n - 1}")
    print("B. seat 0 sells 1 unit/step; phase = obs['step'] % 4 of the deciding observation")
    for item, r in per_item.items():
        print(f"   {item:10} {r}")
    if not per_item["WOOL"]["sales"]:
        ys = find_yarn_seed(seed + 1, seed + 40)
        if ys is not None:
            _, _, _, per_item = check_prices(ys)
            print(f"   WOOL (seed {ys}, first seed after {seed} with a YARN_STORE) {per_item['WOOL']}")
