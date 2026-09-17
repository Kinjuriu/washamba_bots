"""Counter sweep for shape arms B1-B4, R1-R4 vs base on seeds 0 and 8."""
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PY = ROOT / ".venv" / "Scripts" / "python.exe"
LEFTOVER = ROOT / "experiments" / "_facts_leftover.py"

ARMS = [
    "experiments/_facts_v20.py",
    "experiments/_facts_v20_B1.py",
    "experiments/_facts_v20_B2.py",
    "experiments/_facts_v20_B3.py",
    "experiments/_facts_v20_B4.py",
    "experiments/_facts_v20_R1.py",
    "experiments/_facts_v20_R2.py",
    "experiments/_facts_v20_R3.py",
    "experiments/_facts_v20_R4.py",
]
SEEDS = (0, 8)


def parse_run(text):
    m = re.search(r"bank=(\d+)", text)
    bank = int(m.group(1)) if m else None
    ne = re.search(r"PLANT NE STRAW d7-11=(\d+)", text)
    sw = re.search(r"SW STRAW=(\d+)", text)
    unlock_landed = {}
    for line in text.splitlines():
        mm = re.search(r"^\s+d(\d+) req=\d+ landed=(\d+)", line)
        if mm:
            unlock_landed[int(mm.group(1))] = int(mm.group(2))
    d9 = unlock_landed.get(9, 0)
    d10 = unlock_landed.get(10, 0)
    d11 = unlock_landed.get(11, 0)
    deaths = re.search(r"night_deaths=(\d+) WATER_acts", text)
    return {
        "bank": bank,
        "ne_straw_d7_11": int(ne.group(1)) if ne else None,
        "sw_straw": int(sw.group(1)) if sw else None,
        "unlock_d9": d9,
        "unlock_d10": d10,
        "unlock_d11": d11,
        "night_deaths": int(deaths.group(1)) if deaths else None,
    }


def run_arm(agent, seed):
    proc = subprocess.run(
        [str(PY), str(LEFTOVER), agent, str(seed)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=120,
    )
    out = proc.stdout + proc.stderr
    if proc.returncode != 0:
        return {"error": out[-500:]}
    return parse_run(out)


def main():
    rows = []
    for arm in ARMS:
        label = Path(arm).stem.replace("_facts_v20", "base").replace("_facts_v20_", "")
        if label == "base":
            label = "BASE"
        for seed in SEEDS:
            print(f"running {label} seed={seed} ...", flush=True)
            stats = run_arm(arm, seed)
            stats["arm"] = label
            stats["seed"] = seed
            rows.append(stats)

    print("\n=== SHAPE ARM COUNTER TABLE ===")
    print(
        f"{'arm':<6} {'seed':>4} {'bank':>7} {'NE7-11':>6} {'SW':>4} "
        f"{'d9':>3} {'d10':>3} {'d11':>3} {'deaths':>6} {'pass':>4}"
    )
    for r in rows:
        if "error" in r:
            print(f"{r['arm']:<6} {r['seed']:4d} ERROR {r['error'][:60]}")
            continue
        unlock_ok = r["unlock_d9"] >= 15
        ne_ok = r["ne_straw_d7_11"] == 0
        deaths_ok = r["night_deaths"] == 0
        passed = unlock_ok and ne_ok and deaths_ok
        print(
            f"{r['arm']:<6} {r['seed']:4d} {r['bank'] or 0:7d} "
            f"{r['ne_straw_d7_11'] or -1:6d} {r['sw_straw'] or -1:4d} "
            f"{r['unlock_d9']:3d} {r['unlock_d10']:3d} {r['unlock_d11']:3d} "
            f"{r['night_deaths'] or -1:6d} {'Y' if passed else 'N':>4}"
        )


if __name__ == "__main__":
    main()
