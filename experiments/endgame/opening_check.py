"""Print each local agent's turn-1 and turn-2 market orders, to spot agent families.

The top six on the ladder share one opening (turn 1: BUY_ANIMAL COW 1 + BUY_PRODUCT
WHEAT 5; turn 2: SELL WHEAT 1, 4 hires, 1 cow, 3 sheep - docs/research/TOP6_FINDINGS_2026-09-23.md).
Every public tape-family agent opens with 5 hires, 2 cows, 2 sheep on turn 2. Running this
over the public agents we hold is how we checked whether any of them descends from the top
family (none did, 2026-09-25 - see docs/ENDGAME/crosscheck_2026-09-25.md).

The team's own agents (W0, W1, W3) and the 2945 Farm are read from their tracked paths.
Public agents under agents/.pub_*.py are gitignored local copies; recreate them with
`kaggle kernels pull` of the refs in docs/ENDGAME/frontier_screen_2026-09-24.md.

Scope: one seat (0), one seed (0), against `pass`, first two turns only. A match rules an agent
in; a mismatch only says this sampled opening differs.

    python experiments/endgame/opening_check.py
"""
import glob

from kaggle_environments import make

TRACKED = ["agents/washamba_base_v1.py", "agents/w0_v15stack_control.py",
           "agents/w1_v15stack_race44.py", "agents/w3_herdsafe2700.py"]
files = sorted(glob.glob("agents/.pub_*.py")) + TRACKED


def market(action):
    return [o[:3] for o in (action.get("market") or [])]


for f in files:
    try:
        env = make("kaggriculture", configuration={"episodeSteps": 4, "seed": 0})
        env.run([f, "pass"])
        t1, t2 = (env.steps[i][0].get("action") or {} for i in (1, 2))
        print(f"{f.split('/')[-1][:32]:32s} t1={market(t1)}  t2={market(t2)}")
    except Exception as e:  # a missing local copy should not stop the survey
        print(f, "ERR", str(e)[:80])
