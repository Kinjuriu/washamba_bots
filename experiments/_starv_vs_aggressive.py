"""One-off: run animal_buy_starvation_harness's analysis with the aggressive
opponent (experiments/aggressive_opponent.py's aggressive_maxxer) as the rival,
since that opponent is a Python callable and can't be named on argv like a
file path. Kept as a thin, disposable driver rather than folding a callable
special-case into the harness CLI.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

import aggressive_opponent  # noqa: E402
from animal_buy_starvation_harness import run_episode, analyze  # noqa: E402

n_seeds = int(sys.argv[1]) if len(sys.argv) > 1 else 6

for seed in range(n_seeds):
    env = run_episode("agents/router_yuan_nf_trim.py", aggressive_opponent.aggressive_maxxer, seed)
    res = analyze(env)
    fails = [e for e in res["buy_events"] if not e["ok"]]
    fill_str = " ".join(f"d{d}={f}/{t}" for d, (f, t) in res["fills"].items())
    print(f"seed={seed} bank={res['bank']:.0f} status={res['status']} fills[{fill_str}] "
          f"buy_events={len(res['buy_events'])} FAILS={len(fails)}")
    for e in fails:
        print(f"    FAIL step={e['step']} d{e['day']}h{e['hour']} {e['item']}x{e['qty']} "
              f"cost={e['cost']} money={e['money']:.0f}")
