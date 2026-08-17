"""One-off: trace WHEAT market price + inventory + money + orders for a seed."""
import importlib.util
import sys

REPO = r"C:\Users\user\OneDrive\Desktop\BFG\Collabs\washamba_bots"
sys.path.insert(0, REPO)
from kaggle_environments import make  # noqa: E402


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main():
    main_path, label, seed, max_day = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
    mod = load_module(main_path, f"pricetrace_{label}_{seed}")
    log = []

    def traced(obs):
        action = mod.nikaangukia_meroni(obs)
        try:
            state = mod.extract_state(obs)
            farm = state["farm"]
            if farm and state["day"] <= max_day:
                ms = state["market_state"]
                log.append({
                    "step": state["step"], "day": state["day"], "hour": state["hour"],
                    "money": farm.get("money"),
                    "wheat_price": ms["prices"].get("WHEAT"),
                    "wheat_inv": ms["inventory"].get("WHEAT"),
                    "seeds": dict(state["private"].get("seeds", {})),
                    "mkt": action.get("market"),
                })
        except Exception as e:
            log.append({"err": repr(e)})
        return action

    env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed}, debug=False)
    env.run([traced, "starter"])
    for rec in log:
        print(rec)


if __name__ == "__main__":
    main()
