"""Gate 1: with FABLE_ON=0 each variant must produce banks identical to W0,
same seeds, same opponent (W0), both seats. Also one FABLE_ON=1 smoke game each."""
import json, os, subprocess, sys
PY = sys.executable
GAME = r"""
import sys, json, os
os.environ['FABLE_ON'] = sys.argv[4]
if len(sys.argv) > 5: os.environ['FABLE_LOG'] = sys.argv[5]
from kaggle_environments import make
env = make('kaggriculture', configuration={'seed': int(sys.argv[3])}, debug=False)
env.run([sys.argv[1], sys.argv[2]])
last = env.steps[-1]
print(json.dumps([last[0].reward, last[1].reward, last[0].status, last[1].status]))
"""
W0 = os.path.abspath("../submissions/w0_v15stack_control.py")
def play(pa, pb, seed, on, log=""):
    args = [PY, "-c", GAME, pa, pb, str(seed), on] + ([log] if log else [])
    r = subprocess.run(args, capture_output=True, text=True, timeout=900)
    return json.loads(r.stdout.strip().splitlines()[-1])
seeds = [101, 102, 103]
base = {s: play(W0, W0, s, "0") for s in seeds}
print("w0 vs w0 baselines:", {s: base[s][:2] for s in seeds})
for v in ("B", "C1", "C2", "D4", "D8"):
    p = os.path.abspath(f"{v}/main.py")
    ok = True
    for s in seeds:
        r0 = play(p, W0, s, "0")
        r1 = play(W0, p, s, "0")
        if r0[:2] != base[s][:2] or r1[:2] != base[s][:2] or "DONE" not in (r0[2], r0[3]):
            ok = False; print(v, "IDENTITY FAIL", s, r0[:2], r1[:2], "base", base[s][:2])
    print(v, "identity:", "PASS" if ok else "FAIL")
    r = play(p, W0, 101, "1", os.path.abspath(f"{v}/smoke.log"))
    print(v, "smoke on=1 seed101:", r)
