import importlib.util, sys
REPO = r"C:\Users\user\OneDrive\Desktop\BFG\Collabs\washamba_bots"
sys.path.insert(0, REPO)
from kaggle_environments import make

def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def main():
    main_path, label, seed, max_day = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
    mod = load_module(main_path, f"seedtrace_{label}_{seed}")
    log = []
    def traced(obs):
        action = mod.nikaangukia_meroni(obs)
        try:
            state = mod.extract_state(obs)
            farm = state["farm"]
            if farm and state["day"] <= max_day:
                seeds = dict(state["private"].get("seeds", {}))
                farmer_act = action.get("farmer")
                hand_acts = action.get("hands") or []
                n_plant_melon = sum(1 for a in [farmer_act]+hand_acts if a and a[0]=="PLANT" and len(a)>1 and a[1]=="MELON")
                n_pass = sum(1 for a in [farmer_act]+hand_acts if a and a[0]=="PASS")
                log.append({"step": state["step"], "day": state["day"], "hour": state["hour"],
                            "money": farm.get("money"), "melon_seed": seeds.get("MELON",0),
                            "mkt": action.get("market"), "n_plant_melon": n_plant_melon, "n_pass": n_pass,
                            "n_units": 1+len(hand_acts)})
        except Exception as e:
            log.append({"err": repr(e)})
        return action
    env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed}, debug=False)
    env.run([traced, "starter"])
    for rec in log:
        print(rec)

if __name__ == "__main__":
    main()
