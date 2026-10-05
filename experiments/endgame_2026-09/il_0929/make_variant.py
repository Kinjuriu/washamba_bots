"""Build a Step1009 variant: full base file + appended demand-keyed herd overlay.
Usage: make_variant.py out.py MODE MIN_STEP [COW_SHOPS_MIN]
MODE: drop  -> remove SHEEP purchases when no YARN_STORE is unlocked
      cow   -> convert them to COW purchases
      smart -> convert to COW if milk-shop instances >= COW_SHOPS_MIN else drop"""
import sys, shutil
out, mode, min_step = sys.argv[1], sys.argv[2], int(sys.argv[3])
cow_min = int(sys.argv[4]) if len(sys.argv) > 4 else 2
shutil.copyfile("tonight_0928/tetsu_step1009_full.py", out)
layer = f'''

# ---- Washamba Bots (29 Sep 2026, il_0929): demand-keyed late herd overlay ----
# Step1009 buys a baseline of 6 sheep in every world (2 at step 1, 4 more around steps 196-266).
# Without a YARN_STORE the wool market absorbs only about 60 units above I0 before the $1 floor;
# in traced no-yarn mirrors 321 of the last 376 steps sat at the floor and 64 of 130 wool units
# sold for $1. This layer rewrites the late SHEEP purchases while no yarn store is unlocked.
_WB_HERD_PARENT = [_wb_v for _wb_v in list(globals().values()) if callable(_wb_v)][-1]
_WB_HERD_MODE = {mode!r}
_WB_HERD_MIN_STEP = {min_step}
_WB_HERD_COW_SHOPS_MIN = {cow_min}
_WB_MILK_SHOPS = ('PIZZA_SHOP', 'ICE_CREAM_SHOP', 'SMOOTHIE_SHOP')
_WB_HERD_STATS = {{'rewritten': 0, 'dropped': 0}}

def washamba_demand_herd_agent(observation, configuration=None):
    action = _WB_HERD_PARENT(observation, configuration)
    try:
        step = int(observation.get('step', 0) or 0)
        shops = list((observation.get('town') or {{}}).get('unlocked_shops') or [])
        if step >= _WB_HERD_MIN_STEP and 'YARN_STORE' not in shops and isinstance(action, dict):
            market = action.get('market') or []
            if any(isinstance(o, list) and len(o) >= 3 and o[0] == 'BUY_ANIMAL' and o[1] == 'SHEEP' for o in market):
                milk_shops = sum(1 for s in shops if s in _WB_MILK_SHOPS)
                to_cow = _WB_HERD_MODE == 'cow' or (_WB_HERD_MODE == 'smart' and milk_shops >= _WB_HERD_COW_SHOPS_MIN)
                new = []
                for o in market:
                    if isinstance(o, list) and len(o) >= 3 and o[0] == 'BUY_ANIMAL' and o[1] == 'SHEEP':
                        if to_cow:
                            new.append(['BUY_ANIMAL', 'COW', o[2]]); _WB_HERD_STATS['rewritten'] += 1
                        else:
                            _WB_HERD_STATS['dropped'] += 1
                        continue
                    new.append(o)
                action['market'] = new
    except Exception:
        pass
    return action

agent = washamba_demand_herd_agent
'''
open(out, "a").write(layer)
print("wrote", out, mode, min_step, cow_min)
