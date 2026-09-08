"""d0-d7 executed-$ vs v20, seed 0 (the $139 d6h00 leak)."""
import importlib.util
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "experiments"))
spec = importlib.util.spec_from_file_location(
    "trace_cashflow_v20", ROOT / "experiments" / "_trace_cashflow_v20.py"
)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
run_seed = mod.run_seed

rep = run_seed(0, us_seat=0)
print("seed0 d0-d7 category gaps (us-v20)")
for d in range(8):
    us = Counter(rep["by_day_us"].get(d, {}))
    v20 = Counter(rep["by_day_v20"].get(d, {}))
    cats = sorted(set(us) | set(v20), key=lambda c: abs(us[c] - v20[c]), reverse=True)
    print(f"--- d{d} ---")
    for c in cats:
        g = us[c] - v20[c]
        if abs(g) >= 1:
            print(f"  {c:<22} us={us[c]:7.0f} v20={v20[c]:7.0f} gap={g:+7.0f}")

print("--- h00 money ---")
for t in rep["turns"]:
    if t["hour"] == 0 and t["day"] <= 8:
        print(
            f"d{t['day']}h00 money us={t['money_us']:.0f} "
            f"v20={t['money_v20']:.0f} gap={t['money_us']-t['money_v20']:+.0f}"
        )
