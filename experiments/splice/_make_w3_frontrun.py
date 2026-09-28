"""Generate agents/w3_frontrun.py: W3 byte-verbatim + a market-only front-running overlay.

Builder A. The overlay:
- captures W3's entry point as the LAST callable right after the base text (what Kaggle
  runs; W3's `agent` name is an older inner layer);
- feeds WB_DumpPredictor every observation from step 0;
- calls W3 and returns its unit actions untouched;
- when a tape family is identified and predicts a dump of P within K steps, and our
  projected shed holds P that W3's own orders this turn are not already selling, ADDS
  SELL orders for P at the front of the market list. They are sized to the units whose
  quote now beats the price right after the dump, net of the drain in between. It never
  removes or reorders a W3 order, never exceeds 10 market orders, and never sells WHEAT
  or FERTILIZER.
WB_FRONTRUN_ON = False gives W3's own actions, byte for byte.

Usage: .venv/Scripts/python.exe experiments/splice/_make_w3_frontrun.py [K] [output]
       (default K 12, output agents/w3_frontrun.py)
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
BASE = os.path.join(ROOT, "agents", "w3_herdsafe2700.py")
STRIP = re.compile(r"^\s*(from|import)\s+(price_model|sell_engine|controller|dump_predictor)\b")

OVERLAY_HEAD = '''

# ==== w3_frontrun overlay (Builder A, experiments/splice/_make_w3_frontrun.py) ========
# Everything above is agents/w3_herdsafe2700.py, byte-verbatim. Its entry point is taken
# here as the LAST callable - before this overlay defines any - because W3's `agent`
# name is an older inner layer, not what Kaggle runs.
_WB_BASE = [v for v in list(globals().values()) if callable(v)][-1]
WB_FRONTRUN_ON = True       # False: every action is W3's own, byte for byte
WB_FRONTRUN_K = __K__         # steps ahead to look for a predicted tape dump
WB_FRONTRUN_ITEMS = ("MELON", "STRAWBERRY", "MILK", "WOOL", "TOMATO", "CARROT")   # never WHEAT/FERTILIZER
WB_FRONTRUN_MIN_QTY = 4     # ignore predicted dumps smaller than this
WB_FRONTRUN_MIN_DROP = 0.03 # ...or that would lower the price by less than 3%
WB_FRONTRUN_DEBUG = False   # tests: record (W3 market, final market) per turn
'''

OVERLAY_TAIL = '''

_WB_FR_PM = WB_PriceModel()
_WB_FR = {}                 # seat -> WB_DumpPredictor (reset at step 0)
_WB_FR_REPORT = {"turns": 0, "added_orders": 0, "added_units": 0, "errors": 0}
_WB_FR_LOG = []             # WB_FRONTRUN_DEBUG only: (step, W3's market, final market)


def _wb_fr_qty(dp, obs, item, n, inv, shops, step):
    """Units of `item` to sell now ahead of the predicted dump: those whose quote now is at
    least the price right after the dump (net of the drain before it); 0 if none is due."""
    dumps = [(s, q) for s, q in (dp.upcoming(obs, item, WB_FRONTRUN_K) or ()) if q > 0]
    total = sum(q for _, q in dumps)
    if total < WB_FRONTRUN_MIN_QTY:
        return 0
    first = min(s for s, _ in dumps)
    if step % 4 == 0 and first - step > 1:
        return 0                                    # one step later is post-drain and still first
    pm = _WB_FR_PM
    quote_now = pm.quote(item, inv)
    if quote_now <= 1:
        return 0
    drain = sum(pm.drain_per_step(item, shops, s) for s in range(step, first))
    post = pm.quote(item, pm.inventory_after_sells(item, inv - drain, total))
    if post >= quote_now * (1.0 - WB_FRONTRUN_MIN_DROP):
        return 0
    return pm.units_at_or_above(item, inv, post, n)


def _wb_fr_stock(action, obs):
    """W3's own projected shed (after this turn's unit actions, before the market)."""
    try:
        return projected_shed(action, FarmView(obs))
    except Exception:
        return dict(obs["private"]["shed"])


def w3_frontrun_agent(observation, configuration=None):
    action = _WB_BASE(observation, configuration)
    if not WB_FRONTRUN_ON:
        return action
    try:
        seat, step = int(observation["player"]), int(observation["step"])
        dp = _WB_FR.get(seat)
        if dp is None or step == 0:
            dp = _WB_FR[seat] = WB_DumpPredictor(_WB_FR_PM)
            if step == 0:
                _WB_FR_REPORT.update(turns=0, added_orders=0, added_units=0, errors=0)
        dp.observe(observation)
        _WB_FR_REPORT["turns"] += 1
        if not isinstance(action, dict):
            return action
        market = list(action.get("market") or [])
        if len(market) >= 10 or dp.active_family() not in WB_DP_TAPE_FAMILIES:
            return action
        stock = _wb_fr_stock(action, observation)
        own = {}
        for o in market:
            if isinstance(o, list) and len(o) >= 3 and o[0] == "SELL":
                try:
                    own[o[1]] = own.get(o[1], 0) + max(0, int(o[2]))
                except (TypeError, ValueError):
                    pass
        inv = observation["market"]["inventory"]
        shops = list(observation["town"]["unlocked_shops"] or [])
        adds = []
        for item in WB_FRONTRUN_ITEMS:
            n = int(stock.get(item, 0)) - own.get(item, 0)
            if n > 0:
                q = _wb_fr_qty(dp, observation, item, n, inv[item], shops, step)
                if q > 0:
                    adds.append([_WB_FR_PM.quote(item, inv[item]), item, q])
        if not adds:
            return action
        adds.sort(key=lambda r: -r[0])              # dearest first, in slot 0
        adds = [["SELL", item, q] for _p, item, q in adds][:10 - len(market)]
        out = dict(action)
        out["market"] = adds + market                # W3's orders follow, untouched and in order
        _WB_FR_REPORT["added_orders"] += len(adds)
        _WB_FR_REPORT["added_units"] += sum(o[2] for o in adds)
        if WB_FRONTRUN_DEBUG:
            _WB_FR_LOG.append((step, market, out["market"]))
        return out
    except Exception:
        _WB_FR_REPORT["errors"] += 1
        return action


w3_frontrun_agent.telemetry = _WB_FR_REPORT
# `w3_frontrun_agent` must stay the LAST callable defined in this file.
'''


def body(name):
    src = open(os.path.join(HERE, name), encoding="utf-8").read()
    return "\n".join(line for line in src.splitlines() if not STRIP.match(line)) + "\n"


def build(k=12, out=None):
    out = out or os.path.join(ROOT, "agents", "w3_frontrun.py")
    base = open(BASE, "rb").read()
    overlay = (OVERLAY_HEAD.replace("__K__", str(int(k))) + body("price_model.py") + "\n"
               + body("dump_predictor.py") + OVERLAY_TAIL)
    with open(out, "wb") as f:
        f.write(base + overlay.encode("utf-8"))
    return out


if __name__ == "__main__":
    k = int(sys.argv[1]) if len(sys.argv) > 1 else 12
    out = sys.argv[2] if len(sys.argv) > 2 else None
    print("wrote", build(k, out), "K =", k)
