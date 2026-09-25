"""Supporting script for experiments/splice/base_choice.md -- not one of the
frozen deliverables, kept only so that file's numbers are reproducible.

Runs W3, W0 and reactive v1 (v7) each in self-play and vs W3, 4 seeds each,
truncated at episodeSteps=192 so the run stops right after producing the
observation the splice controller would inherit (obs["step"] == 191, the
last turn before handover at step 192 / day 8 hour 0). Records, for the
base's own seat: money, land quadrants owned, tiles planted by crop, animals
placed by species, structures, shed contents, seeds held, hands hired that
day (farm["hires_today"]).

Usage:
    .venv/Scripts/python.exe experiments/splice/_base_choice_measure.py
"""
import json
import os
from multiprocessing import Pool

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(os.path.dirname(THIS_DIR))
AGENTS_DIR = os.path.join(REPO_ROOT, "agents")
RESULTS_DIR = os.path.join(THIS_DIR, "results")

BASES = [
    ("W3", "w3_herdsafe2700.py"),
    ("W0", "w0_v15stack_control.py"),
    ("REACTIVE_V1", "washamba_reactive_v1.py"),
    # Added 2026-09-25 per coordinator: public "2945 Farm" opening (BUY WHEAT 20 / SELL
    # 15, no seed buy) -- 15 of the top 100 ladder teams start from it.
    ("FARM2945", "washamba_base_v1.py"),
]
W3_PATH = os.path.join(AGENTS_DIR, "w3_herdsafe2700.py")
SEEDS = [900, 901, 902, 903]  # low end of gate.py's dev range, for consistency
HANDOVER_STEP = 192


def _snapshot(farm, private):
    tiles = farm["tiles"]
    crop_counts, animal_counts, structures = {}, {}, {}
    for row in tiles:
        for t in row:
            if not isinstance(t, dict):
                continue
            kind = t.get("kind")
            if kind == "PLANT":
                crop_counts[t["crop"]] = crop_counts.get(t["crop"], 0) + 1
            elif "animal" in t:
                animal_counts[t["animal"]] = animal_counts.get(t["animal"], 0) + 1
                structures[kind] = structures.get(kind, 0) + 1
            elif kind in ("PASTURE", "COOP"):
                structures[kind] = structures.get(kind, 0) + 1
    shed = {k: v for k, v in (private.get("shed") or {}).items() if v}
    seeds = {k: v for k, v in (private.get("seeds") or {}).items() if v}
    return {
        "money": farm["money"],
        "quadrants": farm.get("unlocked_quadrants"),
        "hires_today": farm.get("hires_today"),
        "crops": crop_counts,
        "animals": animal_counts,
        "structures": structures,
        "shed": shed,
        "seeds": seeds,
    }


def _job(args):
    label, mode, seat0_path, seat1_path, cand_seat, seed = args
    from kaggle_environments import make
    env = make("kaggriculture", configuration={"episodeSteps": HANDOVER_STEP, "seed": seed}, debug=False)
    env.run([seat0_path, seat1_path])
    final = env.steps[-1]
    obs = final[cand_seat].observation
    snap = _snapshot(obs["farms"][cand_seat], obs["private"])
    wheat_buy_price = obs["market"]["prices"].get("WHEAT")
    return {
        "base": label, "mode": mode, "seed": seed,
        "step": obs.get("step"), "status": final[cand_seat].status,
        "wheat_buy_price": wheat_buy_price,
        **snap,
    }


def main():
    jobs = []
    for label, filename in BASES:
        path = os.path.join(AGENTS_DIR, filename)
        if not os.path.exists(path):
            print(f"SKIP {label}: {path} not found on this machine")
            continue
        for seed in SEEDS:
            jobs.append((label, "selfplay", path, path, 0, seed))
            if label != "W3":  # vs-W3 is identical to self-play for W3's own row
                jobs.append((label, "vs_w3", path, W3_PATH, 0, seed))

    with Pool(3) as pool:
        rows = pool.map(_job, jobs)

    os.makedirs(RESULTS_DIR, exist_ok=True)
    out_path = os.path.join(RESULTS_DIR, "base_choice_snapshots.jsonl")
    with open(out_path, "w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")

    for r in rows:
        print(f"{r['base']:12} {r['mode']:9} seed={r['seed']} step={r['step']} status={r['status']} "
              f"money={r['money']:.0f} quadrants={r['quadrants']} hires_today={r['hires_today']} "
              f"crops={r['crops']} animals={r['animals']} structures={r['structures']} "
              f"shed={r['shed']} seeds={r['seeds']}")
    print(f"\nwritten to {out_path}")


if __name__ == "__main__":
    main()
