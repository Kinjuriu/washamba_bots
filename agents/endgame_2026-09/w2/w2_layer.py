

# ---------------------------------------------------------------------------
# Washamba Bots W2 layer (2026-09-23): premium selling by short-horizon planning.
# Wraps the v15stack entry above. From day 10, the tape's SELL orders for the
# products in W2_ITEMS are replaced by a plan: each turn, forecast the market
# inventory for the next W2_H turns (shop and town consumption from unlocked
# shops, opponent's visible ripe stock), assign every unit we hold or will soon
# hold to the turn where the engine's own price formula pays most, sell now only
# the units assigned to now, and put those sells first in the order queue.
# Guards: never sell less than the tape when cash is short or the tape's own
# purchases this turn need the money; clear shed space before night overflow;
# sell everything in the last turns.
# ---------------------------------------------------------------------------
import math as _w2m

W2_ON = True
W2_ITEMS = ("WOOL", "STRAWBERRY", "MILK")
W2_FROM_STEP = 240
W2_H = 48
W2_DISCOUNT = 0.997
W2_LAG = 3                  # turns before ripe stock on our tiles can be sold
W2_OPP_SPREAD = 24          # opponent's visible ripe stock assumed sold over this many turns
W2_CASH_GUARD = 1500
W2_SHED_LIMIT = 94
W2_FINAL_STEP = 704
_W2_PARAMS = {
    "WHEAT": (25, 400, "sqrt", 0.80, "log", 0.20), "CARROT": (35, 450, "hinge", 1.00, "sqrt", 0.70),
    "TOMATO": (60, 200, "hinge", 0.40, "sqrt", 0.60), "STRAWBERRY": (120, 100, "sqrt", 0.70, "linear", 1.60),
    "MELON": (250, 300, "log", 0.20, "sq", 3.60), "EGG": (50, 332, "hinge", 0.40, "log", 0.20),
    "MILK": (160, 122, "sqrt", 0.60, "linear", 1.60), "WOOL": (200, 105, "log", 0.20, "sq", 3.20),
    "FERTILIZER": (100, 200, "linear", 0.40, "linear", 0.40),
}
_W2_SHOPS = {
    "BAKERY": ("EGG", "WHEAT"), "PIZZA_SHOP": ("MILK", "TOMATO", "WHEAT"),
    "BRUNCH_SPOT": ("EGG", "WHEAT", "STRAWBERRY"), "YARN_STORE": ("WOOL",),
    "ICE_CREAM_SHOP": ("STRAWBERRY", "MILK", "WHEAT"), "PET_CAFE": ("CARROT",),
    "SMOOTHIE_SHOP": ("STRAWBERRY", "MILK"), "FARMERS_MARKET": ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY"),
}
_W2_SOURCE = {"WOOL": ("animal", "SHEEP"), "MILK": ("animal", "COW"), "EGG": ("animal", "GOOSE"),
              "STRAWBERRY": ("crop", "STRAWBERRY"), "TOMATO": ("crop", "TOMATO"), "MELON": ("crop", "MELON")}
_W2_REPORT = {"turns": 0, "replaced": 0, "guard_cash": 0, "guard_shed": 0, "final": 0, "errors": 0}


def _w2_shape(f, x, T):
    x = max(0.0, x)
    if f == "linear": return x
    if f == "sq": return x * x
    if f == "sqrt": return _w2m.sqrt(x)
    if f == "log": return _w2m.log(1.0 + x)
    if f == "hinge":
        u = x / T
        return u + 8.0 * max(0.0, u - 1.0) ** 2
    return x


def _w2_price(item, inv):
    base, T, bf, bt, af, at = _W2_PARAMS[item]
    if inv < 10000:
        p = base + bt * base / _w2_shape(bf, T, T) * _w2_shape(bf, 10000 - inv, T)
    else:
        p = base - at * base / _w2_shape(af, T, T) * _w2_shape(af, inv - 10000, T)
    return max(1, int(round(p)))


def _w2_g(o, k, d=None):
    try:
        v = o[k]
        return d if v is None else v
    except Exception:
        return getattr(o, k, d)


def _w2_drain(item, shops, step):
    d = 0
    if step % 4 == 0:
        for s in shops:
            prods = _W2_SHOPS.get(s, ())
            if item in prods:
                d += 2 if len(prods) == 1 else 1
    if step % 24 == 0 and item != "FERTILIZER":
        d += 1
    return d


def _w2_ripe(farm, item):
    kind, name = _W2_SOURCE.get(item, (None, None))
    n = 0
    for row in _w2_g(farm, "tiles", []) or []:
        for t in row:
            if not isinstance(t, dict):
                continue
            if kind == "animal" and t.get("animal") == name:
                n += int(t.get("yield_units") or 0)
            elif kind == "crop" and t.get("kind") == "PLANT" and t.get("crop") == name:
                n += int(t.get("yield_units") or 0)
    return n


def _w2_plan(item, inv0, shops, step, have, arrivals, opp_rate):
    """Greedy water-filling of our units over the next H turns; returns units to sell now.
    arrivals: list of earliest slots for units we will hold later (carried, ripe, future output).
    opp_rate: expected opponent units sold per turn (measured from market flow)."""
    H = max(1, min(W2_H, 720 - step))
    base = []
    inv = float(inv0)
    for k in range(H):
        base.append(inv)
        inv = inv - _w2_drain(item, shops, step + k) + opp_rate
    added = [0] * H
    now = 0
    units = [0] * have + sorted(a for a in arrivals if a < H)
    for u, lo in enumerate(units):
        best, best_k = -1.0, lo
        cum = 0
        for k in range(H):
            cum += added[k]
            if k < lo:
                continue
            v = _w2_price(item, base[k] + cum) * (W2_DISCOUNT ** k)
            if v > best:
                best, best_k = v, k
        added[best_k] += 1
        if best_k == 0 and u < have:
            now += 1
    return now


_W2_RATE = {"SHEEP": 4.0 / 72, "COW": 3.0 / 48, "GOOSE": 2.0 / 24}   # units per turn with daily care
_W2_STATE = {}


def _w2_own_rate(farm, item):
    kind, name = _W2_SOURCE.get(item, (None, None))
    if kind == "animal":
        n = 0
        for row in _w2_g(farm, "tiles", []) or []:
            for t in row:
                if isinstance(t, dict) and t.get("animal") == name:
                    n += 1
        return n * _W2_RATE.get(name, 0.0)
    if kind == "crop":
        n = 0
        for row in _w2_g(farm, "tiles", []) or []:
            for t in row:
                if isinstance(t, dict) and t.get("kind") == "PLANT" and t.get("crop") == name:
                    n += 1
        return n * (1.0 / 48)
    return 0.0


def _w2_wrap(parent):
    def agent(observation, configuration=None):
        action = parent(observation, configuration)
        if not W2_ON:
            return action
        try:
            step = int(_w2_g(observation, "step", 0) or 0)
            if step < W2_FROM_STEP or not isinstance(action, dict):
                return action
            _W2_REPORT["turns"] += 1
            me = int(_w2_g(observation, "player", 0) or 0)
            farms = _w2_g(observation, "farms", []) or []
            my, op = farms[me], farms[1 - me]
            priv = _w2_g(observation, "private", {}) or {}
            shed = dict(_w2_g(priv, "shed", {}) or {})
            invs = _w2_g(priv, "inventories", []) or []
            carried = {}
            for w in invs:
                for k, v in (w or {}).items():
                    carried[k] = carried.get(k, 0) + int(v or 0)
            market = _w2_g(observation, "market", {}) or {}
            minv = _w2_g(market, "inventory", {}) or {}
            shops = list(_w2_g(_w2_g(observation, "town", {}) or {}, "unlocked_shops", []) or [])
            money = float(_w2_g(my, "money", 0) or 0)
            orders = [list(o) for o in (action.get("market") or []) if isinstance(o, (list, tuple)) and o]
            tape_q = {}
            rest = []
            for o in orders:
                if o[0] == "SELL" and len(o) >= 3 and o[1] in W2_ITEMS:
                    tape_q[o[1]] = tape_q.get(o[1], 0) + int(o[2] or 0)
                else:
                    rest.append(o)
            buys = any(o[0] in ("BUY_SEED", "BUY_ANIMAL", "BUY_PRODUCT", "BUY_LAND", "HIRE") for o in rest)
            st = _W2_STATE.get(me)
            if st is None or step <= st.get("step", -1):
                st = {"step": -1, "inv": {}, "req": {}, "shed": {}, "opp": {it: [] for it in W2_ITEMS}}
                _W2_STATE[me] = st
            if st["step"] == step - 1:
                for it in W2_ITEMS:
                    total = float(minv.get(it, 10000)) - st["inv"].get(it, 10000) + _w2_drain(it, st.get("shops", shops), step - 1)
                    ours_exec = min(st["req"].get(it, 0), st["shed"].get(it, 0) + carried.get(it, 0))
                    st["opp"][it].append(max(0.0, total - ours_exec))
                    st["opp"][it] = st["opp"][it][-W2_H:]
            plan = {}
            for item in W2_ITEMS:
                have = max(int(shed.get(item, 0) or 0), tape_q.get(item, 0))
                if have <= 0:
                    continue
                if step >= W2_FINAL_STEP:
                    q = have; _W2_REPORT["final"] += 1
                else:
                    hist = st["opp"].get(item) or []
                    opp_rate = (sum(hist) / len(hist)) if len(hist) >= 12 else _w2_own_rate(op, item)
                    arrivals = [W2_LAG] * (carried.get(item, 0) + _w2_ripe(my, item))
                    r = _w2_own_rate(my, item)
                    if r > 0:
                        j = 1
                        while True:
                            a = W2_LAG + int(j / r)
                            if a >= W2_H or j > 200:
                                break
                            arrivals.append(a); j += 1
                    q = _w2_plan(item, float(minv.get(item, 10000)), shops, step, have, arrivals, opp_rate)
                    if q < tape_q.get(item, 0) and (money < W2_CASH_GUARD or buys):
                        q = tape_q.get(item, 0); _W2_REPORT["guard_cash"] += 1
                if q > 0:
                    plan[item] = q
            # night overflow guard: shed cap counts every item, not seeds
            hour = step % 24
            if hour >= 16:
                shed_total = sum(int(v or 0) for v in shed.values()) + sum(carried.values())
                after = shed_total - sum(plan.values())
                if after > W2_SHED_LIMIT:
                    need = after - W2_SHED_LIMIT
                    ranked = sorted(W2_ITEMS, key=lambda it: -_w2_price(it, float(minv.get(it, 10000))))
                    for it in ranked:
                        avail = max(int(shed.get(it, 0) or 0), tape_q.get(it, 0)) - plan.get(it, 0)
                        take = min(avail, need)
                        if take > 0:
                            plan[it] = plan.get(it, 0) + take; need -= take; _W2_REPORT["guard_shed"] += 1
                        if need <= 0:
                            break
            st["step"] = step; st["shops"] = shops
            st["inv"] = {it: float(minv.get(it, 10000)) for it in W2_ITEMS}
            st["req"] = dict(plan); st["shed"] = {it: int(shed.get(it, 0) or 0) for it in W2_ITEMS}
            ours = [["SELL", it, q] for it, q in sorted(plan.items(), key=lambda kv: -_w2_price(kv[0], float(minv.get(kv[0], 10000))))]
            merged = ours + rest
            while len(merged) > 10:
                idx = [i for i in range(len(ours), len(merged)) if merged[i][0] == "SELL"]
                if idx:
                    merged.pop(idx[-1])
                else:
                    merged.pop(len(ours) - 1); ours = ours[:-1]
            if ours or tape_q:
                _W2_REPORT["replaced"] += 1
            action = dict(action)
            action["market"] = merged
            return action
        except Exception:
            _W2_REPORT["errors"] += 1
            return action
    agent.telemetry = _W2_REPORT
    return agent


_W2_PARENT = v15_submission_entry
w2_agent = _w2_wrap(_W2_PARENT)
