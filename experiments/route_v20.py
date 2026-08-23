"""Fetch boatlee's V20 multi-route notebook and decode it as a local opponent.

Same rules as `meta_opponent.py`: this is a HARNESS, not an entry. The code is
downloaded on demand, written to a gitignored path, and never committed here.
Nothing in the repo is derived from it. **Submitting anything based on it is a
separate decision gated on the notebook's licence**, which Kaggle renders only
in the page's JavaScript - the API cannot see it, so a human has to read it.

Why it exists: we ran a v16-derived route to a ladder plateau around 1,700
while forks of v20 sit near 2,364 (see docs/ROUTE_GENERATIONS.md). Measured
head to head, v20 beats our best agent by +8,855 over 24 matches. The route
generation, not the parameters on it, is the biggest lever we have found.

The notebook ships its agent as a base85+zlib blob with a SHA-256 it checks
itself. We decode it here **without executing the notebook's code** and verify
against that same checksum.

    python experiments/route_v20.py            # fetch + decode + self-test
    python experiments/head_to_head.py experiments/.v20_agent.py main.py 12
"""

import ast
import base64
import hashlib
import json
import os
import re
import subprocess
import sys
import zlib

KERNEL = "boatlee/v20-adaptive-r1-multi-route-agent"
HERE = os.path.dirname(os.path.abspath(__file__))
AGENT_PATH = os.path.join(HERE, ".v20_agent.py")
CACHE_DIR = os.path.join(HERE, ".v20_kernel")


def _kaggle_exe():
    local = os.path.join(".venv", "Scripts", "kaggle.exe")
    return local if os.path.exists(local) else "kaggle"


def _notebook_path():
    os.makedirs(CACHE_DIR, exist_ok=True)
    hits = [f for f in os.listdir(CACHE_DIR) if f.endswith(".ipynb")]
    if not hits:
        subprocess.run([_kaggle_exe(), "kernels", "pull", KERNEL, "-p", CACHE_DIR],
                       check=True, capture_output=True, text=True)
        hits = [f for f in os.listdir(CACHE_DIR) if f.endswith(".ipynb")]
    if not hits:
        raise SystemExit(f"no notebook downloaded for {KERNEL}")
    return os.path.join(CACHE_DIR, hits[0])


def decode(force=False):
    """Download, decode and checksum the agent. Returns the path."""
    if os.path.exists(AGENT_PATH) and not force:
        return AGENT_PATH
    cells = json.load(open(_notebook_path(), encoding="utf-8"))["cells"]
    for cell in cells:
        if cell.get("cell_type") != "code":
            continue
        src = "".join(cell["source"])
        if "_PACKED_SOURCE" not in src:
            continue
        # Pull the literal out and evaluate it as data. Never exec the cell:
        # it is someone else's code and we only want the payload.
        match = re.search(r'_PACKED_SOURCE = "".join\(\((.*?)\n\)\)', src, re.S)
        if not match:
            raise SystemExit("payload literal not found - notebook format changed")
        parts = ast.literal_eval("(" + match.group(1).rstrip().rstrip(",") + ",)")
        raw = zlib.decompress(base64.b85decode("".join(parts)))
        want = re.search(r"EXPECTED_SOURCE_SHA256 = '([0-9a-f]+)'", src)
        if want and hashlib.sha256(raw).hexdigest() != want.group(1):
            raise SystemExit("checksum mismatch - refusing to write")
        with open(AGENT_PATH, "wb") as fh:
            fh.write(raw)
        return AGENT_PATH
    raise SystemExit("no payload cell found in the notebook")


def main():
    path = decode(force="--force" in sys.argv)
    print(f"decoded {os.path.getsize(path)} bytes to {path}")
    from kaggle_environments import make
    env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": 0})
    env.run([path, path])
    print("self-play:", [s.status for s in env.steps[-1]],
          [s.reward for s in env.steps[-1]])


if __name__ == "__main__":
    main()
