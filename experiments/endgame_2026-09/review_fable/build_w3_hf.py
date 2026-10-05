"""Build W3 + harvest-triggered front-running (market-only overlay). Usage: build_w3_hf.py ON|OFF out.py"""
import sys
base=open('/Users/stephanengugi/KagricultureLocalData/submissions/w3_herdsafe2700.py',encoding='utf-8').read()
flag=sys.argv[1].upper()=='ON'
overlay = r'''

# ==== review_fable (2026-09-26): harvest-triggered front-running, market orders only ====
# The opponent's farm is public, including yield counters on its animals and plants. A counter that
# drops to zero is a harvest; the opponent's sale of that product follows within a few steps (measured:
# median 2-5 steps, 60-78% within 6 steps, for tape families and for the top six alike). When we hold
# that product beyond what W3 already sells this turn, sell up to the harvested quantity now, at slot 0,
# so our units take the price tier the opponent's lot is about to take. Unit actions are never touched;
# W3's own orders are never removed or reordered. HF_ON = False makes every action W3's own.
_HF_BASE = [v for v in list(globals().values()) if callable(v)][-1]
import math as _hf_math
HF_ON = __HF_FLAG__
HF_ANIMAL_PRODUCT = {"SHEEP": "WOOL", "COW": "MILK"}
HF_PLANTS = ("STRAWBERRY", "MELON")
HF_ITEMS = ("WOOL", "MILK", "STRAWBERRY", "MELON")
HF_K = 6                 # steps a detected harvest stays pending
HF_MIN_STEP = 24
HF_MIN_PRICE_FRAC = 0.35 # do not front-run into a floored book
HF_MAX_ORDERS = 10
_HF_MP = {
    "WHEAT": (25, 400, "sqrt", 0.80, "log", 0.20), "CARROT": (35, 450, "hinge", 1.00, "sqrt", 0.70),
    "TOMATO": (60, 200, "hinge", 0.40, "sqrt", 0.60), "STRAWBERRY": (120, 100, "sqrt", 0.70, "linear", 1.60),
    "MELON": (250, 300, "log", 0.20, "sq", 3.60), "EGG": (50, 332, "hinge", 0.40, "log", 0.20),
    "MILK": (160, 122, "sqrt", 0.60, "linear", 1.60), "WOOL": (200, 105, "log", 0.20, "sq", 3.20),
    "FERTILIZER": (100, 200, "linear", 0.40, "linear", 0.40)}
def _hf_shape(func, x, T):
    x = max(0.0, x)
    if func == "linear": return x
    if func == "sq": return x * x
    if func == "sqrt": return _hf_math.sqrt(x)
    if func == "log": return _hf_math.log(1.0 + x)
    if func == "hinge":
        u = x / T
        return u + 8.0 * max(0.0, u - 1.0) ** 2
    return x
def _hf_price(item, inv):
    base, T, bf, bt, af, at = _HF_MP[item]
    if inv < 10000:
        return max(1, int(round(base + bt * base / _hf_shape(bf, T, T) * _hf_shape(bf, 10000 - inv, T))))
    return max(1, int(round(base - at * base / _hf_shape(af, T, T) * _hf_shape(af, inv - 10000, T))))
_HF_STATE = {}
_HF_REPORT = dict(fires=0, units=0)
def _hf_visible(farm):
    out = {}
    for y, row in enumerate(farm["tiles"]):
        for x, tile in enumerate(row):
            if isinstance(tile, dict):
                if "animal" in tile and tile["animal"] in HF_ANIMAL_PRODUCT:
                    out[(x, y)] = (HF_ANIMAL_PRODUCT[tile["animal"]], int(tile.get("yield_units", 0)))
                elif tile.get("kind") == "PLANT" and tile.get("crop") in HF_PLANTS:
                    out[(x, y)] = (tile["crop"], int(tile.get("yield_units", 0)))
    return out
def _hf_apply(obs, action):
    player = int(obs["player"]); step = int(obs["step"])
    st = _HF_STATE.get(player)
    if st is None or step <= st["step"]:
        st = _HF_STATE[player] = {"step": -1, "prev": None, "pending": {}}
        if step == 0:
            _HF_REPORT.update(fires=0, units=0)
    st["step"] = step
    farm = obs["farms"][1 - player]
    cur = _hf_visible(farm)
    prev = st["prev"]
    if prev is not None:
        for key, (p, yv) in prev.items():
            if yv <= 0: continue
            now = cur.get(key)
            if now is not None and now[0] == p and now[1] == 0:
                st["pending"][p] = st["pending"].get(p, 0) + yv
            elif now is None and p == "MELON":
                tile = farm["tiles"][key[1]][key[0]]
                if tile is None:
                    st["pending"][p] = st["pending"].get(p, 0) + yv
        st["pending_step"] = {p: step for p in st["pending"]} if "pending_step" not in st else st["pending_step"]
    st["prev"] = cur
    # expire pending
    ps = st.setdefault("pending_step", {})
    for p in list(st["pending"]):
        ps.setdefault(p, step)
        if step - ps[p] > HF_K or st["pending"][p] <= 0:
            st["pending"].pop(p, None); ps.pop(p, None)
        elif p in st["pending"] and ps[p] < step and prev is not None and any(k in cur and cur[k][1] == 0 and prev.get(k, (None, 0))[1] > 0 and cur[k][0] == p for k in prev):
            ps[p] = step
    if step < HF_MIN_STEP or not st["pending"]:
        return action
    market = [list(o) for o in (action.get("market") or [])]
    if len(market) >= HF_MAX_ORDERS:
        return action
    shed = obs["private"]["shed"]
    inv = obs["market"]["inventory"]
    changed = False
    for p in HF_ITEMS:
        pend = st["pending"].get(p, 0)
        if pend <= 0: continue
        own = sum(int(o[2]) for o in market if len(o) >= 3 and o[0] == "SELL" and o[1] == p)
        spare = int(shed.get(p, 0)) - own
        if spare <= 0: continue
        if _hf_price(p, inv[p]) < HF_MIN_PRICE_FRAC * _HF_MP[p][0]: continue
        q = min(spare, pend)
        if q <= 0 or len(market) >= HF_MAX_ORDERS: continue
        market.insert(0, ["SELL", p, q])
        st["pending"][p] = pend - q
        _HF_REPORT["fires"] += 1; _HF_REPORT["units"] += q
        changed = True
    if not changed:
        return action
    result = dict(action); result["market"] = market[:HF_MAX_ORDERS]
    return result
def w3_hf_agent(observation, configuration=None):
    action = _HF_BASE(observation, configuration)
    if not HF_ON:
        return action
    try:
        return _hf_apply(observation, action)
    except Exception:
        return action
w3_hf_agent.telemetry = _HF_REPORT
'''.replace("__HF_FLAG__", "True" if flag else "False")
open(sys.argv[2],'w',encoding='utf-8').write(base+overlay)
print("wrote",sys.argv[2],len(base+overlay))
