"""Trace d9 land afford: pre-turn money, post-sell estimate, BUY_LAND emit. Throwaway."""
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from kaggle_environments import make

AGENT = ROOT / (sys.argv[1] if len(sys.argv) > 1 else "_facts_v20.py")
SEEDS = [int(s) for s in sys.argv[2:]] or [0, 8]

spec = importlib.util.spec_from_file_location("facts_v20", AGENT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

NEED = mod.LAND_PRICES[1] + mod.MIN_CASH_RESERVE_FOR_LAND_BUYING


def run(seed):
    env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed}, debug=False)
    env.run([str(AGENT), "starter"])
    prev = None
    for step in env.steps:
        obs = step[0].observation
        src = prev if prev is not None else obs
        day = src.get("day", 0)
        hour = src.get("hour", 0)
        if day != 9:
            prev = obs
            continue
        farm = (src.get("farms") or [{}])[0]
        priv = obs.get("private") or {}
        board_size = len(farm.get("tiles") or []) or 10
        owned = mod.count_owned_animals(farm, priv, board_size)
        market_state = src.get("market") or obs.get("market") or {}
        market = (step[0].get("action") or {}).get("market") or []
        land_i = next((i for i, o in enumerate(market) if o and o[0] == "BUY_LAND"), None)
        post = mod._estimated_post_sell_cash(
            farm, priv, market_state,
            day, reserved_wheat=owned * mod.MIN_WHEAT_RESERVE_FOR_FEEDING,
            unlocked_shops=(src.get("town") or {}).get("unlocked_shops") or (),
            sell_fert_for_buy=True, board_size=board_size,
        )
        post_pess = mod._estimated_post_sell_cash(
            farm, priv, market_state,
            day, reserved_wheat=owned * mod.MIN_WHEAT_RESERVE_FOR_FEEDING,
            unlocked_shops=(src.get("town") or {}).get("unlocked_shops") or (),
            sell_fert_for_buy=False, board_size=board_size,
        )
        can = mod.can_afford_pending_second_land_after_sells(
            farm, priv, market_state,
            day, reserved_wheat=owned * mod.MIN_WHEAT_RESERVE_FOR_FEEDING,
            unlocked_shops=(src.get("town") or {}).get("unlocked_shops") or (),
            board_size=board_size,
        )
        emit = mod.decide_land_orders(farm, day)
        print(
            f"  d9h{hour:02d} pre={farm.get('money', 0):5.0f} "
            f"post_opt={post:5.0f} post_pess={post_pess:5.0f} need={NEED} "
            f"can_after_sells={can} land_emit={bool(emit)} "
            f"market_land_i={land_i} unlocked={farm.get('unlocked_quadrants')}"
        )
        prev = obs


def main():
    for seed in SEEDS:
        print(f"\n=== seed {seed} ({AGENT.name}) ===")
        run(seed)


if __name__ == "__main__":
    main()
