
# ===================== FABLE R3 WRAPPER (appended to a copy of W0) =====================
# Mode/params are replaced per variant by build_variants.py.
import os as _f_os

_F_MODE = "__MODE__"          # "B" | "C" | "D" | "E"
_F_C_START_DAY = __C_START__  # C: first day extra-goose program may act
_F_D_LIMIT = __D_LIMIT__      # D: max substituted tiles per game
_F_ON = _f_os.environ.get("FABLE_ON", "1") == "1"
_F_LOG = _f_os.environ.get("FABLE_LOG", "")
_F_PARENT = v15_submission_entry

_F_TARGET_GEESE = 5
_F_CASH_RESERVE = 800.0

_F_MP = {  # market params copied from engine (kaggle-environments 1.32.7)
    "WHEAT":  dict(base=25, T=400, bf="sqrt", bt=0.80, af="log", at=0.20),
    "CARROT": dict(base=35, T=450, bf="hinge", bt=1.00, af="sqrt", at=0.70),
    "EGG":    dict(base=50, T=332, bf="hinge", bt=0.40, af="log", at=0.20),
}
def _f_shape(func, x, T):
    import math
    x = max(0.0, x)
    if func == "linear": return x
    if func == "sq": return x * x
    if func == "sqrt": return math.sqrt(x)
    if func == "log": return math.log(1.0 + x)
    if func == "hinge":
        u = x / T
        return u + 8.0 * max(0.0, u - 1.0) ** 2
    return x
def _f_price(item, inv):
    p = _F_MP[item]
    if inv < 10000:
        amp = p["bt"] * p["base"] / _f_shape(p["bf"], p["T"], p["T"])
        v = p["base"] + amp * _f_shape(p["bf"], 10000 - inv, p["T"])
    else:
        amp = p["at"] * p["base"] / _f_shape(p["af"], p["T"], p["T"])
        v = p["base"] - amp * _f_shape(p["af"], inv - 10000, p["T"])
    return max(1, int(round(v)))

def _f_log(msg):
    if _F_LOG:
        try:
            with open(_F_LOG, "a") as f: f.write(msg + "\n")
        except Exception: pass

def _f_get(o, k, d=None):
    try:
        if isinstance(o, dict): return o.get(k, d)
        return getattr(o, k, d)
    except Exception:
        return d

# ---------- B: replace duplicate CARE with a useful same-tile action ----------
def _f_care_dedup(obs, action):
    me = _f_get(obs, "player", 0)
    farm = _f_get(obs, "farms")[me]
    tiles = farm["tiles"]
    poss = [list(farm["farmer"])] + [list(p) for p in farm["hands"]]
    units = [action.get("farmer")] + list(action.get("hands") or [])
    priv = _f_get(obs, "private", {}) or {}
    invs = _f_get(priv, "inventories", []) or []
    cared = set()
    hands = None
    for i, u in enumerate(units):
        if not (isinstance(u, (list, tuple)) and u and u[0] == "CARE"):
            continue
        if i >= len(poss):
            continue
        x, y = poss[i][0], poss[i][1]
        t = tiles[y][x]
        isani = isinstance(t, dict) and ("animal" in t)
        if isani and not t.get("cared_today") and (x, y) not in cared:
            cared.add((x, y)); continue          # this CARE lands; keep it
        new = None
        if isani:
            if t.get("fertilizer_available"): new = ["COLLECT_FERTILIZER"]
            elif t.get("yield_units", 0) > 0: new = ["HARVEST"]
            elif not t.get("fed_today") and i < len(invs) and (invs[i] or {}).get("WHEAT", 0) > 0:
                new = ["FEED"]
        if new is None:
            continue
        _f_log("B swap t=%s unit=%d %s" % (_f_get(obs, "step"), i, new[0]))
        if i == 0:
            action["farmer"] = new
        else:
            if hands is None: hands = list(action.get("hands") or [])
            hands[i - 1] = new
    if hands is not None:
        action["hands"] = hands
    return action

# ---------- C: extra geese run by one extra hired hand (rev2) ----------
_F_CST = {}
def _f_reset_c(step):
    if step <= 1 or _F_CST.get("_step_seen", -1) > step:
        _F_CST.clear()
        _F_CST.update(plan=[], built=[], hand_idx=None, hire_day=-1,
                      expect_hands=None, bought=0, prev_geese={})
    _F_CST["_step_seen"] = step

def _f_step_toward(pos, tgt):
    x, y = pos; tx, ty = tgt
    if x < tx: return ["EAST"]
    if x > tx: return ["WEST"]
    if y < ty: return ["SOUTH"]
    if y > ty: return ["NORTH"]
    return None

def _f_extra_geese(obs, action):
    st = _F_CST
    step = _f_get(obs, "step", 0); _f_reset_c(step)
    day = _f_get(obs, "day", 0); hour = _f_get(obs, "hour", 0)
    me = _f_get(obs, "player", 0)
    farm = _f_get(obs, "farms")[me]
    tiles = farm["tiles"]; money = farm["money"]
    priv = _f_get(obs, "private", {}) or {}
    shed = dict(_f_get(priv, "shed", {}) or {})
    invs = _f_get(priv, "inventories", []) or []
    market = list(action.get("market") or [])
    hands_pos = [list(p) for p in farm["hands"]]
    if day < _F_C_START_DAY:
        return action
    SPAWN = (4, 4)

    def tile_at(c): return tiles[c[1]][c[0]]
    def total_geese():
        n = 0
        for row in tiles:
            for t in row:
                if isinstance(t, dict) and t.get("animal") == "GOOSE": n += 1
        return n

    # verify yesterday's hire capture
    if st.get("expect_hands") is not None:
        st["hand_idx"] = (st["expect_hands"] - 1) if len(hands_pos) == st["expect_hands"] else None
        st["expect_hands"] = None
        if st["hand_idx"] is None: _f_log("C capture FAILED d=%d" % day)
    if st.get("hire_day") != day:
        st["hand_idx"] = None if st.get("expect_hands") is None and st.get("hire_day") != day else st.get("hand_idx")

    # classify OUR structures only
    st["built"] = [c for c in st["built"] if isinstance(tile_at(c), dict)]
    managed = [c for c in st["built"] if tile_at(c).get("animal") == "GOOSE"]
    empty_built = [c for c in st["built"] if tile_at(c).get("kind") == "COOP" and "animal" not in tile_at(c)]
    # escape logging
    for c in st["built"]:
        was = st["prev_geese"].get(tuple(c), False)
        now = tile_at(c).get("animal") == "GOOSE"
        if was and not now: _f_log("C ESCAPE d=%d %s" % (day, str(c)))
        st["prev_geese"][tuple(c)] = now
    need = max(0, _F_TARGET_GEESE - total_geese() - shed.get("GOOSE", 0))
    # keep the build plan valid (tiles must still be empty AND ours-to-be)
    st["plan"] = [c for c in st["plan"] if tile_at(c) is None]
    want_coops = max(0, min(3, need + len(managed)) - len(st["built"]) - len(st["plan"]))
    if want_coops > 0 and need > 0 and (st["built"] or (need >= 2 and money >= 1500)):
        cands = []
        for yy in range(len(tiles)):
            for xx in range(len(tiles[yy])):
                if tiles[yy][xx] is None and (xx, yy) not in st["plan"]:
                    cands.append((abs(xx - SPAWN[0]) + abs(yy - SPAWN[1]), (xx, yy)))
        cands.sort()
        st["plan"].extend(c for _, c in cands[:want_coops])
    to_build = list(st["plan"])
    work = bool(to_build or shed.get("GOOSE", 0) > 0 or managed or (need > 0 and empty_built))

    def slots(): return 10 - len(market)
    if work and st.get("hire_day") != day and slots() > 0 and hour <= 6:
        n_before = len(hands_pos)
        tape_hires = sum(1 for o in market if isinstance(o, (list, tuple)) and o and o[0] == "HIRE")
        fib = [1, 1]
        while len(fib) < 30: fib.append(fib[-1] + fib[-2])
        cost = fib[min(29, farm.get("hires_today", 0) + tape_hires)]
        if money >= cost + _F_CASH_RESERVE:
            market.append(["HIRE"])
            st["hire_day"] = day
            st["expect_hands"] = n_before + tape_hires + 1
            st["hand_idx"] = None
    if (need > 0 and shed.get("GOOSE", 0) == 0 and empty_built and st["bought"] < 4
            and st.get("bought_day") != day and shed.get("WHEAT", 0) >= 2
            and slots() > 0 and money >= 1500 and sum(shed.values()) < 99):
        market.append(["BUY_ANIMAL", "GOOSE", 1]); st["bought"] += 1; st["bought_day"] = day
        _f_log("C buy goose d=%d" % day)
    if managed and shed.get("WHEAT", 0) < len(managed) + 2 and slots() > 0 and money >= 200 and sum(shed.values()) < 96:
        market.append(["BUY_PRODUCT", "WHEAT", 4])
    if shed.get("EGG", 0) >= 6 and slots() > 0:
        inv_egg = _f_get(obs, "market")["inventory"]["EGG"]
        if _f_price("EGG", inv_egg) >= 35:
            market.append(["SELL", "EGG", shed.get("EGG", 0) - 4])
    action["market"] = market

    h = st.get("hand_idx")
    if h is None or h >= len(hands_pos):
        return action
    pos = tuple(hands_pos[h])
    inv = (invs[h + 1] if h + 1 < len(invs) else {}) or {}
    act = None
    if inv.get("GOOSE", 0) > 0:
        tgt = tuple(empty_built[0]) if empty_built else None
        if tgt is None:
            act = ["PASS"]
        elif pos == tgt:
            act = ["PLACE", "GOOSE"]; _f_log("C place goose d=%d %s" % (day, str(tgt)))
        else:
            act = _f_step_toward(pos, tgt) or ["PASS"]
    elif shed.get("GOOSE", 0) > 0 and empty_built:
        act = ["PICKUP", "GOOSE", 1] if pos == SPAWN else (_f_step_toward(pos, SPAWN) or ["PICKUP", "GOOSE", 1])
    elif to_build and need > 0:
        tgt = tuple(to_build[0])
        if pos == tgt:
            act = ["BUILD_COOP"]
            st["built"].append(tgt); st["plan"] = [c for c in st["plan"] if tuple(c) != tgt]
            _f_log("C build coop d=%d %s" % (day, str(tgt)))
        else:
            act = _f_step_toward(pos, tgt) or ["PASS"]
    if act is None and managed:
        carrying = inv.get("WHEAT", 0)
        hungry = [c for c in managed if not tile_at(c).get("fed_today")]
        if hungry and carrying == 0 and shed.get("WHEAT", 0) > 0:
            act = ["PICKUP", "WHEAT", min(len(hungry), shed.get("WHEAT", 0))] if pos == SPAWN else _f_step_toward(pos, SPAWN)
        else:
            def task_at(c):
                t = tile_at(c)
                if not t.get("fed_today") and carrying > 0: return ["FEED"]
                if t.get("yield_units", 0) > 0: return ["HARVEST"]
                if t.get("fertilizer_available"): return ["COLLECT_FERTILIZER"]
                if not t.get("cared_today"): return ["CARE"]
                return None
            best = None
            for c in sorted(managed, key=lambda c: abs(c[0] - pos[0]) + abs(c[1] - pos[1])):
                if task_at(c) is not None: best = c; break
            if best is not None:
                act = task_at(best) if tuple(best) == pos else _f_step_toward(pos, best)
            else:
                act = ["PASS"]
    if act is None:
        act = ["PASS"]
    hands = list(action.get("hands") or [])
    while len(hands) <= h: hands.append(["PASS"])
    hands[h] = act
    action["hands"] = hands
    return action

# ---------- D: reactive wheat<->carrot substitution from day 10 ----------
_F_DST = {}
def _f_reset_d(step):
    if step <= 1 or _F_DST.get("_step_seen", -1) > step:
        _F_DST.clear(); _F_DST.update(subs=0, bought={"WHEAT": 0, "CARROT": 0})
    _F_DST["_step_seen"] = step

def _f_crop_value(obs, crop, me):
    farms = _f_get(obs, "farms"); farm = farms[me]
    market = _f_get(obs, "market"); town = _f_get(obs, "town", {}) or {}
    shops = _f_get(town, "unlocked_shops", []) or []
    per_tick = {"WHEAT": 0, "CARROT": 0}
    SHOPS = {"BAKERY": ["EGG", "WHEAT"], "PIZZA_SHOP": ["MILK", "TOMATO", "WHEAT"],
             "BRUNCH_SPOT": ["EGG", "WHEAT", "STRAWBERRY"], "YARN_STORE": ["WOOL"],
             "ICE_CREAM_SHOP": ["STRAWBERRY", "MILK", "WHEAT"], "PET_CAFE": ["CARROT"],
             "SMOOTHIE_SHOP": ["STRAWBERRY", "MILK"],
             "FARMERS_MARKET": ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY"]}
    for s in shops:
        prods = SHOPS.get(s, [])
        if crop in prods: per_tick[crop] += 2 if len(prods) == 1 else 1
    drain = 6 * per_tick[crop] + 1
    yld = 4.0 if crop == "WHEAT" else 3.0
    days = 5.0 if crop == "WHEAT" else 4.0
    seed = 10 if crop == "WHEAT" else 20
    pending = 0
    for row in farm["tiles"]:
        for t in row:
            if isinstance(t, dict) and t.get("crop") == crop:
                pending += 1
    inv_h = market["inventory"][crop] - drain * (days - 1) + pending * yld * 0.5
    price = _f_price(crop, inv_h)
    return (yld * price - seed) / days

def _f_crop_sub(obs, action):
    st = _F_DST
    step = _f_get(obs, "step", 0); _f_reset_d(step)
    day = _f_get(obs, "day", 0)
    me = _f_get(obs, "player", 0)
    farm = _f_get(obs, "farms")[me]
    priv = _f_get(obs, "private", {}) or {}
    seeds = dict(_f_get(priv, "seeds", {}) or {})
    money = farm["money"]
    market = list(action.get("market") or [])
    # keep a small reserve of both seeds from day 9
    if day >= 9 and st["subs"] < _F_D_LIMIT:
        for c, cost in (("CARROT", 20), ("WHEAT", 10)):
            if seeds.get(c, 0) < 2 and st["bought"][c] < 8 and len(market) < 10 and money >= 2 * cost + 600:
                market.append(["BUY_SEED", c, 2]); st["bought"][c] += 2
                money -= 2 * cost
    action["market"] = market
    if day < 10 or st["subs"] >= _F_D_LIMIT:
        return action
    units = [action.get("farmer")] + list(action.get("hands") or [])
    tape_plants = {"WHEAT": 0, "CARROT": 0}
    for u in units:
        if isinstance(u, (list, tuple)) and len(u) >= 2 and u[0] == "PLANT" and u[1] in tape_plants:
            tape_plants[u[1]] += 1
    vals = {c: _f_crop_value(obs, c, me) for c in ("WHEAT", "CARROT")}
    hands = None
    subs_this_turn = {"WHEAT": 0, "CARROT": 0}
    for i, u in enumerate(units):
        if st["subs"] >= _F_D_LIMIT: break
        if not (isinstance(u, (list, tuple)) and len(u) >= 2 and u[0] == "PLANT"): continue
        x = u[1]
        if x not in ("WHEAT", "CARROT"): continue
        alt = "CARROT" if x == "WHEAT" else "WHEAT"
        if vals[alt] <= 1.25 * vals[x]: continue
        need = tape_plants[alt] + subs_this_turn[alt] + 1
        if seeds.get(alt, 0) < need: continue
        new = ["PLANT", alt]
        subs_this_turn[alt] += 1; tape_plants[x] -= 1
        st["subs"] += 1
        _f_log("D sub t=%d %s->%s (v %.1f vs %.1f)" % (step, x, alt, vals[x], vals[alt]))
        if i == 0:
            action["farmer"] = new
        else:
            if hands is None: hands = list(action.get("hands") or [])
            hands[i - 1] = new
    if hands is not None:
        action["hands"] = hands
    return action

# ---------- entry ----------
def fable_agent(observation, configuration=None):
    action = _F_PARENT(observation, configuration)
    if not _F_ON:
        return action
    try:
        if not isinstance(action, dict):
            return action
        action = dict(action)
        if _F_MODE in ("B", "E"):
            action = _f_care_dedup(observation, action)
        if _F_MODE in ("C", "E"):
            action = _f_extra_geese(observation, action)
        if _F_MODE in ("D", "E"):
            action = _f_crop_sub(observation, action)
    except Exception as e:
        _f_log("WRAPPER ERROR %r" % (e,))
    return action
