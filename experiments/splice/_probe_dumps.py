"""Tape dump schedules (Builder A): every premium SELL a tape family executes, with its route.

Runs each family against W3 (whose opening our splice plays through step 191), seats
alternating by seed, on up to 3 worker processes. Both seats are recorded. Per seat:
- route key: the first two unlocked shops at obs step 144, which is what the shared
  router keys on;
- the rival key the router reads at step 2: (rival money, WHEAT market inventory);
- the route the chassis actually used at steps 150 and 650, read from the agent's state;
- every executed SELL, from an instrumented _commit_unit, aggregated per (step, item).

Output: fam/dump_runs.jsonl, one line per game (gitignored).

Usage: .venv/Scripts/python.exe experiments/splice/_probe_dumps.py [first_seed] [n_seeds] [families]
"""
import json
import os
import sys
from multiprocessing import Pool

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
AGENTS = os.path.join(ROOT, "agents")
FAMILIES = {"W3": "w3_herdsafe2700.py", "W0": "w0_v15stack_control.py", "F2945": "washamba_base_v1.py"}
OPP = ("W3", "w3_herdsafe2700.py")
OUT = os.path.join(ROOT, "fam", "dump_runs.jsonl")

_CUR = {}
_LOG = []


def _instrument():
    import kaggle_environments.envs.kaggriculture.kaggriculture as K
    if getattr(K, "_wb_dump_probe", False):
        return
    o_pm, o_cu = K._process_market, K._commit_unit

    def pm(state, env):
        _CUR["farms"] = state[0].observation.farms
        _CUR["step"] = state[0].observation.get("step", 0)
        return o_pm(state, env)

    def cu(op, item, price, farm, private, market, shed_capacity=100):
        ok = o_cu(op, item, price, farm, private, market, shed_capacity)
        if ok and op == "SELL":
            _LOG.append((0 if farm is _CUR["farms"][0] else 1, _CUR["step"], item, price))
        return ok

    K._process_market, K._commit_unit = pm, cu
    K._wb_dump_probe = True


def _load(fname):
    ns = {}
    if AGENTS not in sys.path:
        sys.path.append(AGENTS)
    path = os.path.join(AGENTS, fname)
    exec(compile(open(path, encoding="utf-8").read(), path, "exec"), ns)
    return ns, [v for v in ns.values() if callable(v)][-1]


def job(args):
    fam, seed, seat = args
    from kaggle_environments import make
    _instrument()
    _LOG.clear()
    names = [None, None]
    names[seat], names[1 - seat] = fam, OPP[0]
    loaded = [None, None]
    loaded[seat] = _load(FAMILIES[fam])
    loaded[1 - seat] = _load(OPP[1])
    routes = [{}, {}]
    rkeys = [None, None]

    def wrap(i):
        ns, fn = loaded[i]

        def agent(obs, cfg=None):
            act = fn(obs, cfg)
            s = int(obs["step"])
            if s in (150, 650):
                routes[i][s] = ns["_IMPL"].chassis.players.get(i, {}).get("route")
            if s == 2:
                rv = obs["farms"][1 - i]
                rkeys[i] = (round(float(rv["money"]), 3), int(obs["market"]["inventory"]["WHEAT"]))
            return act
        return agent

    env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})
    env.run([wrap(0), wrap(1)])
    key = list(env.steps[144][0]["observation"]["town"]["unlocked_shops"][:2])
    shops = list(env.steps[-1][0]["observation"]["town"]["unlocked_shops"])
    sells = [{}, {}]
    for s, step, item, price in _LOG:
        cell = sells[s].setdefault(f"{step}:{item}", [0, 0])
        cell[0] += 1
        cell[1] += price
    return {"seed": seed, "families": names, "key": key, "shops": shops, "rkeys": rkeys,
            "routes": [[r.get(150), r.get(650)] for r in routes],
            "banks": [s.reward for s in env.steps[-1]], "statuses": [s.status for s in env.steps[-1]],
            "sells": sells}


ITEMS = ("MELON", "STRAWBERRY", "MILK", "WOOL", "TOMATO", "CARROT")   # EGG measured unpredictable (precision 0.34)
TABLE_FROM_STEP = 96           # day 4: covers the pre-handover dumps a W3 overlay can front-run
PREDICTOR = os.path.join(HERE, "dump_predictor.py")
BEGIN, END = "# ---- BEGIN GENERATED TABLES (_probe_dumps.py --table) ----", "# ---- END GENERATED TABLES ----"


def _seats(games):
    """(family, route at 150, seed, {(step, item): units}) per recorded seat."""
    out = []
    for g in games:
        for s in (0, 1):
            d = {}
            for k, (u, _r) in g["sells"][s].items():
                st, item = k.split(":")
                if item in ITEMS:
                    d[(int(st), item)] = u
            out.append((g["families"][s], g["routes"][s][0], g["seed"], d))
    return out


def build_table(seats, min_units, min_share=0.5, min_route_seats=2):
    """{family: {route | 'any': {item: ((step, median qty), ...)}}} from recorded seats. A route
    seen in fewer than min_route_seats seats gets no cell (the family's 'any' is used)."""
    groups = {}
    for fam, route, _seed, d in seats:
        groups.setdefault((fam, route), []).append(d)
        groups.setdefault((fam, "any"), []).append(d)
    table = {}
    for (fam, route), ds in groups.items():
        if route != "any" and len(ds) < min_route_seats:
            continue
        need = max(1, -(-len(ds) * min_share // 1)) if len(ds) > 1 else 1
        per = {}
        for item in ITEMS:
            hits = {}
            for d in ds:
                for (st, it), u in d.items():
                    if it == item and st >= TABLE_FROM_STEP and u >= min_units:
                        hits.setdefault(st, []).append(u)
            rows = []
            for st in sorted(hits):
                if len(hits[st]) >= need:
                    us = sorted(hits[st])
                    rows.append((st, us[len(us) // 2]))
            if rows:
                per[item] = tuple(rows)
        table.setdefault(fam, {})[route] = per
    return table


def key_route_map():
    ns, _ = _load(FAMILIES["W3"])            # the router and its tables are shared by all three
    router = ns["_router"]
    shops = sorted(ns["SHOPS"]) if "SHOPS" in ns else ["BAKERY", "BRUNCH_SPOT", "FARMERS_MARKET", "ICE_CREAM_SHOP",
                                                       "PET_CAFE", "PIZZA_SHOP", "SMOOTHIE_SHOP", "YARN_STORE"]
    out = {}
    for a in shops:
        for b in shops:
            obs = {"player": 0, "farms": [{"money": 0}, {"money": 0}],
                   "market": {"inventory": {"WHEAT": 0}}, "town": {"unlocked_shops": [a, b]}}
            out[(a, b)] = router(obs, 144, {})
    return out, dict(ns["_V93_ROUTE_BY_RIVAL"])


def evaluate(table, seats, min_units):
    """Precision / recall of the table's (step, item) dumps on held-out seats, per family."""
    stats = {}
    for fam, route, _seed, d in seats:
        rows = (table.get(fam, {}).get(route) or table.get(fam, {}).get("any") or {})
        pred = {(st, item) for item, rs in rows.items() for st, _q in rs}
        actual = {(st, it) for (st, it), u in d.items() if st >= TABLE_FROM_STEP and u >= min_units}
        s = stats.setdefault(fam, [0, 0, 0, 0])
        s[0] += len(pred & actual)
        s[1] += len(pred)
        s[2] += len(actual)
        near = {(st + k, it) for (st, it) in pred for k in (-1, 0, 1)}
        s[3] += len(actual & near)
    return {f: {"precision": round(a / p, 3) if p else None, "recall": round(a / r, 3) if r else None,
                "recall_within_1": round(n / r, 3) if r else None, "predicted": p, "actual": r}
            for f, (a, p, r, n) in stats.items()}


def write_table(min_units=4, holdout_from=916):
    games = [json.loads(line) for line in open(OUT, encoding="utf-8")]
    seats = _seats(games)
    train = [x for x in seats if x[2] < holdout_from]
    test = [x for x in seats if x[2] >= holdout_from]
    print("held-out check (table from seeds <", holdout_from, "):",
          json.dumps(evaluate(build_table(train, min_units), test, min_units)))
    table = build_table(seats, min_units)
    kr, rival = key_route_map()
    lines = [BEGIN,
             f"# {len(games)} games, {len(seats)} seats; dumps >= {min_units} units at the same step in >= half",
             "# of a route's seats (median units); 'any' pools all routes of a family.",
             f"WB_DP_KEY_ROUTE = {kr!r}",
             f"WB_DP_RIVAL_ROUTE = {rival!r}",
             "WB_DP_DUMPS = {"]
    for fam in sorted(table):
        lines.append(f"    {fam!r}: {{")
        for route in sorted(table[fam], key=str):
            lines.append(f"        {route!r}: {table[fam][route]!r},")
        lines.append("    },")
    lines += ["}", END]
    src = open(PREDICTOR, encoding="utf-8").read()
    block = "\n".join(lines)
    if BEGIN in src:
        src = src[:src.index(BEGIN)] + block + src[src.index(END) + len(END):]
    else:
        src = src.rstrip("\n") + "\n\n\n" + block + "\n"
    open(PREDICTOR, "w", encoding="utf-8").write(src)
    n_rows = sum(len(rs) for fam in table.values() for per in fam.values() for rs in per.values())
    print(f"wrote {n_rows} (step, qty) rows for {sum(len(f) for f in table.values())} (family, route) cells")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--table":
        write_table(int(sys.argv[2]) if len(sys.argv) > 2 else 4)
        sys.exit(0)
    first = int(sys.argv[1]) if len(sys.argv) > 1 else 900
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 30
    fams = sys.argv[3].split(",") if len(sys.argv) > 3 else list(FAMILIES)
    jobs = [(f, s, s % 2) for f in fams for s in range(first, first + n)]
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with Pool(3) as pool, open(OUT, "a", encoding="utf-8") as out:
        for k, res in enumerate(pool.imap_unordered(job, jobs)):
            out.write(json.dumps(res) + "\n")
            out.flush()
            print(f"[{k + 1}/{len(jobs)}] {res['families']} seed {res['seed']} key {res['key']} "
                  f"routes {res['routes']} banks {res['banks']}", flush=True)
