"""Build the diagnostic overlay agents/.wb_w3_sells.py (gitignored; not a ship candidate).

= agents/w3_herdsafe2700.py verbatim, then price_model.py and sell_engine.py, then a
wrapper that, from step 192 only, removes W3's premium SELL orders (WOOL, MILK,
STRAWBERRY) and puts WB_SellEngine's orders in front of the rest of W3's market list.
Everything else W3 emits is untouched; `sellable` is W3's own projected shed (shed after
this turn's unit actions, the same projection W3's sell layers use).

Usage:  .venv/Scripts/python.exe experiments/splice/_probe_w3_sells.py [name] [attr=value ...]
        e.g. `_probe_w3_sells.py .wb_w3_sells_alt.py "healthy_phases=(0,1,2,3)" "contested_dumps=True"`
        builds the mirror-tuned alternative (engine attributes overridden on the instance).
Then:   timeout 2400 .venv/Scripts/python.exe experiments/splice/_run_agents_small.py \
            agents/.wb_w3_sells.py 900 908 agents/w3_herdsafe2700.py fam/wb_w3_sells.jsonl
"""
import ast
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
BASE = os.path.join(ROOT, "agents", "w3_herdsafe2700.py")
OUT = os.path.join(ROOT, "agents", ".wb_w3_sells.py")
STRIP = "from price_model import"

OVERLAY = '''

# ---- Builder A diagnostic overlay (not a ship candidate) --------------------------
_WB_BASE = [v for v in list(globals().values()) if callable(v)][-1]   # W3's real entrypoint
{price_model}
{sell_engine}
_WB_OV_PM = WB_PriceModel()
_WB_OV_SE = WB_SellEngine(_WB_OV_PM)
{overrides}
_WB_OV_PREMIUM = ("WOOL", "MILK", "STRAWBERRY")
_WB_OV_FROM = 192
_WB_OV_REPORT = {{"turns": 0, "orders": 0, "errors": 0}}


def _wb_overlay_agent(observation, configuration=None):
    action = _WB_BASE(observation, configuration)
    if int(observation["step"]) < _WB_OV_FROM or not isinstance(action, dict):
        return action
    try:
        rest = [o for o in (action.get("market") or [])
                if not (isinstance(o, list) and len(o) >= 2 and o[0] == "SELL" and o[1] in _WB_OV_PREMIUM)]
        try:
            shed = projected_shed(action, FarmView(observation))
        except Exception:
            shed = observation["private"]["shed"]
        sellable = {{p: int(shed.get(p, 0)) for p in _WB_OV_PREMIUM}}
        mine = _WB_OV_SE.orders(observation, sellable, 10 - len(rest))
        _WB_OV_REPORT["turns"] += 1
        _WB_OV_REPORT["orders"] += len(mine)
        action = dict(action)
        action["market"] = mine + rest
    except Exception:
        _WB_OV_REPORT["errors"] += 1
    return action
'''


def main(argv):
    out = os.path.join(ROOT, "agents", argv[0]) if argv else OUT
    overrides = []
    for kv in argv[1:]:
        key, value = kv.split("=", 1)
        overrides.append(f"_WB_OV_SE.{key} = {ast.literal_eval(value)!r}")
    base = open(BASE, encoding="utf-8").read()
    pm = open(os.path.join(HERE, "price_model.py"), encoding="utf-8").read()
    se = open(os.path.join(HERE, "sell_engine.py"), encoding="utf-8").read()
    se = "\n".join(line for line in se.splitlines() if not line.startswith(STRIP))
    text = base.rstrip("\n") + "\n" + OVERLAY.format(price_model=pm, sell_engine=se,
                                                      overrides="\n".join(overrides))
    with open(out, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"wrote {out} ({len(text):,} bytes) overrides={overrides}")


if __name__ == "__main__":
    main(sys.argv[1:])
