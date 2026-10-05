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
base = {101: [96073.0, 96073.0], 102: [104236.0, 104236.0], 103: [99960.0, 99960.0]}
for v in ("C1", "C2"):
    p = os.path.abspath(f"{v}/main.py")
    ok = all(play(p, W0, s, "0")[:2] == base[s] and play(W0, p, s, "0")[:2] == base[s] for s in base)
    print(v, "identity:", "PASS" if ok else "FAIL")
    for s in (101, 102):
        try: os.remove(f"{v}/smoke{s}.log")
        except OSError: pass
        r = play(p, W0, s, "1", os.path.abspath(f"{v}/smoke{s}.log"))
        print(v, f"smoke seed{s}:", r, "(base", base[s], ")")
