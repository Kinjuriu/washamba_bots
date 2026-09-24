"""Starvation harness for agents/router_yuan_nf_trim.py's open-loop BUY_ANIMAL
orders (see agents/router_yuan_nf_trim_ar.py's header for the diagnosed bug).

Goal: find a local opponent under which the *baseline* nf_trim's recorded
BUY_ANIMAL orders reproducibly land with insufficient cash (money at the
buy step below the order's total cost), and pasture fill at day 4/6/10
drops below the ~13/13 seen against passive/tape opponents.

Usage:
    .venv/Scripts/python.exe experiments/animal_buy_starvation_harness.py <agent_path> <opponent> [seeds]

<opponent> is anything kaggle_environments' env.run() accepts: a builtin name
("pass", "starter"), a file path, or (when called from Python) a callable.
"""

import sys
from pathlib import Path

from kaggle_environments import make

ANIMAL_COST = {"GOOSE": 300, "COW": 400, "SHEEP": 500}
FILL_DAYS = (4, 6, 10)


def _order_value(o, prices):
    """Rough dollar size of one market order, using the turn's quoted prices
    as an estimate (real settlement drifts price per unit within the order;
    this is a projection, not an exact replay). Returns (delta_money, item,
    qty) where delta_money is signed (+ for SELL, - for a buy)."""
    if not o or len(o) < 2:
        return 0.0, None, 0
    op = o[0]
    item = o[1] if len(o) > 1 else None
    try:
        qty = int(o[2]) if len(o) > 2 else 0
    except (TypeError, ValueError):
        qty = 0
    price = float(prices.get(item, 50) or 50) if item else 0.0
    if op == "SELL":
        return price * qty, item, qty
    if op in ("BUY_PRODUCT", "BUY_SEED"):
        return -price * qty, item, qty
    if op == "BUY_ANIMAL":
        return -ANIMAL_COST.get(item, 500) * qty, item, qty
    return 0.0, item, qty


def project_buy_animal_outcomes(observation, action, player):
    """Sequentially settle a turn's own market order list (same-turn SELLs
    fund a later BUY_ANIMAL) using the turn's quoted prices as an estimate.
    Returns a list of dicts for every BUY_ANIMAL order in the turn, each
    with the *projected* money available when that order is reached and
    whether the projection says it would succeed."""
    market = list(action.get("market") or [])
    if not market:
        return []
    p = observation.get("player", player)
    money = float(observation["farms"][p].get("money", 0) or 0)
    prices = dict((observation.get("market") or {}).get("prices", {}) or {})

    out = []
    for o in market:
        if not o:
            continue
        if o[0] == "BUY_ANIMAL":
            item = o[1]
            qty = int(o[2]) if len(o) > 2 else 0
            cost = ANIMAL_COST.get(item, 500) * qty
            out.append({"item": item, "qty": qty, "cost": cost,
                        "money_at_order": money, "ok": money >= cost})
        delta, _, _ = _order_value(o, prices)
        money += delta
    return out


def count_pasture_fill(farm):
    total = filled = 0
    for row in farm.get("tiles") or []:
        for t in (row or []):
            if isinstance(t, dict) and t.get("kind") in ("PASTURE", "COOP"):
                total += 1
                if t.get("animal"):
                    filled += 1
    return filled, total


def run_episode(agent_path, opponent, seed):
    env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed}, debug=True)
    env.run([agent_path, opponent])
    return env


def analyze(env, player=0):
    steps = env.steps
    buy_events = []
    for i in range(0, len(steps) - 1):
        act = steps[i][player].get("action") or {}
        obs = steps[i][player]["observation"]
        for ev in project_buy_animal_outcomes(obs, act, player):
            buy_events.append({
                "step": i, "day": obs.get("day"), "hour": obs.get("hour"),
                "item": ev["item"], "qty": ev["qty"], "cost": ev["cost"],
                "money": ev["money_at_order"], "ok": ev["ok"],
            })

    fills = {}
    for day in FILL_DAYS:
        step = min(day * 24, len(steps) - 1)
        obs = steps[step][player]["observation"]
        p = obs.get("player", player)
        fills[day] = count_pasture_fill(obs["farms"][p])

    final = steps[-1][player]
    return {
        "bank": final.reward,
        "status": final.status,
        "buy_events": buy_events,
        "fills": fills,
    }


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        raise SystemExit(2)
    agent_path, opponent = sys.argv[1], sys.argv[2]
    n_seeds = int(sys.argv[3]) if len(sys.argv) > 3 else 6

    for seed in range(n_seeds):
        env = run_episode(agent_path, opponent, seed)
        res = analyze(env)
        fails = [e for e in res["buy_events"] if not e["ok"]]
        fill_str = " ".join(f"d{d}={f}/{t}" for d, (f, t) in res["fills"].items())
        print(f"seed={seed} bank={res['bank']:.0f} status={res['status']} fills[{fill_str}] "
              f"buy_events={len(res['buy_events'])} FAILS={len(fails)}")
        for e in fails:
            print(f"    FAIL step={e['step']} d{e['day']}h{e['hour']} {e['item']}x{e['qty']} "
                  f"cost={e['cost']} money={e['money']:.0f}")


if __name__ == "__main__":
    main()
