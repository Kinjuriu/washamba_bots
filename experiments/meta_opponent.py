"""Fetch the public top-meta notebook and expose it as a local sparring partner.

We have failed three times to build an opponent stronger than ourselves:
`bigfarm_opponent.py` was neutralised the moment its settings shipped in #29,
`replay_shape_agent` banks 705-18,280 against our ~67,000, and the opening-book
reconstruction in #32 collapsed. Meanwhile a published notebook beats every
agent we have by 3-5x (see docs/PUBLIC_META.md).

Using it as a HARNESS is a different question from submitting anything based on
it - no competition entry is derived from it here, it never touches main.py, and
its code is never committed to this repo. It is downloaded on demand and written
to a gitignored path.

    python experiments/meta_opponent.py            # fetch + self-test
    python experiments/head_to_head.py main.py experiments/.meta_agent.py

If the notebook is ever taken down this stops working, which is the correct
failure mode: we do not want a silent copy of someone else's agent sitting in
the tree.
"""

import json
import os
import subprocess
import sys

KERNEL = "boatlee/v16-rc5-high-score-8c-4s-premium-market-lead"
HERE = os.path.dirname(os.path.abspath(__file__))
AGENT_PATH = os.path.join(HERE, ".meta_agent.py")


def _kaggle_exe():
    local = os.path.join(".venv", "Scripts", "kaggle.exe")
    return local if os.path.exists(local) else "kaggle"


def fetch(force=False):
    """Download the notebook and extract its agent cell. Returns the path."""
    if os.path.exists(AGENT_PATH) and not force:
        return AGENT_PATH

    dest = os.path.join(HERE, ".meta_kernel")
    os.makedirs(dest, exist_ok=True)
    subprocess.run(
        [_kaggle_exe(), "kernels", "pull", KERNEL, "-p", dest],
        check=True, capture_output=True, text=True,
    )
    nb_files = [f for f in os.listdir(dest) if f.endswith(".ipynb")]
    if not nb_files:
        raise SystemExit(f"no notebook found in {dest}")
    nb = json.load(open(os.path.join(dest, nb_files[0]), encoding="utf-8"))

    # The submission lives in the cell that writes main.py.
    for cell in nb["cells"]:
        if cell["cell_type"] != "code":
            continue
        src = "".join(cell["source"])
        if src.lstrip().startswith("%%writefile main.py"):
            body = src.replace("%%writefile main.py", "", 1).lstrip("\n")
            with open(AGENT_PATH, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(body)
            return AGENT_PATH
    raise SystemExit("no '%%writefile main.py' cell in the notebook")


def self_test(seeds=(0, 1, 2), ours="main.py"):
    from kaggle_environments import make

    path = fetch()
    print(f"opponent: {path}")
    for seed in seeds:
        env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})
        env.run([ours, path])
        left, right = env.steps[-1]
        print(f"  seed {seed}: {ours} {left.reward:>8.0f} [{left.status}]   "
              f"meta {right.reward:>8.0f} [{right.status}]")


if __name__ == "__main__":
    self_test(ours=sys.argv[1] if len(sys.argv) > 1 else "main.py")
