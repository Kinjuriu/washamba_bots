"""Decode a public Kaggriculture notebook into a runnable agent file, for vetting.

Base adoption needs candidate routes as local agent files. Public notebooks pack
their agent one of two ways we have seen:
  verbatim - the agent is just the code cells (yhay81's router).
  packed   - the agent is a base85+zlib blob joined from string parts and
             decoded at import (boatlee's v20).
This pulls the kernel, tries verbatim then packed, writes the result to a
gitignored file under experiments/.decoded/, and self-plays it once to prove it
loads. It never execs the notebook's cells; for the packed case it pulls the
literal out as data and decodes that. If a notebook fits neither shape it stops
with a clear message so you can eyeball the cells and add a strategy here.

Usage, from the repo root (kaggle CLI must be authenticated):
    .venv/bin/python experiments/decode_route.py <kernel-slug> [out_name]
"""

import ast
import base64
import json
import os
import re
import subprocess
import sys
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))


def kaggle_exe():
    local = os.path.join(".venv", "Scripts", "kaggle.exe")
    return local if os.path.exists(local) else "kaggle"


def code_cells(slug):
    cache = os.path.join(HERE, ".kernel_cache", slug.replace("/", "__"))
    os.makedirs(cache, exist_ok=True)
    if not any(f.endswith(".ipynb") for f in os.listdir(cache)):
        subprocess.run([kaggle_exe(), "kernels", "pull", slug, "-p", cache],
                       check=True, capture_output=True, text=True)
    nb = next((f for f in os.listdir(cache) if f.endswith(".ipynb")), None)
    if not nb:
        raise SystemExit(f"no notebook for {slug}: check the slug and that kaggle is authenticated")
    cells = json.load(open(os.path.join(cache, nb), encoding="utf-8"))["cells"]
    return ["".join(c["source"]) for c in cells if c.get("cell_type") == "code"]


def has_agent(text):
    return "def agent" in text


def as_verbatim(cells):
    joined = "\n\n".join(cells)
    if not has_agent(joined):
        return None
    try:
        tree = ast.parse(joined)
    except SyntaxError:
        return None
    # Cut the source right after `agent`'s own last line, not merely at a cell
    # boundary, so nothing a notebook defines below it - demo/eval cells living
    # in the same or a later cell - can become the last callable in the module
    # and silently hijack the entrypoint (kaggle_environments/agent.py:64 picks
    # the last callable, not the one named `agent`).
    agent_defs = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "agent"]
    if not agent_defs:
        return None
    end_line = agent_defs[-1].end_lineno
    trimmed = "\n".join(joined.splitlines()[:end_line])
    return trimmed.encode("utf-8")


def as_packed(cells):
    for src in cells:
        m = re.search(r'join\(\((.*?)\n\s*\)\)', src, re.S)
        if not m:
            continue
        try:
            parts = ast.literal_eval("(" + m.group(1).rstrip().rstrip(",") + ",)")
            raw = zlib.decompress(base64.b85decode("".join(parts)))
        except Exception:
            continue
        if has_agent(raw.decode("utf-8", "replace")):
            return raw
    return None


def decode(slug, out_name=None):
    cells = code_cells(slug)
    for how, fn in (("verbatim", as_verbatim), ("packed", as_packed)):
        raw = fn(cells)
        if raw is not None:
            break
    else:
        raise SystemExit("notebook is neither verbatim-with-def-agent nor a decodable packed blob; "
                         "open the .ipynb under experiments/.kernel_cache and add a strategy here")
    name = out_name or slug.rstrip("/").split("/")[-1]
    outdir = os.path.join(HERE, ".decoded")
    os.makedirs(outdir, exist_ok=True)
    out = os.path.join(outdir, re.sub(r"[^A-Za-z0-9_.-]", "_", name) + ".py")
    with open(out, "wb") as fh:
        fh.write(raw)
    return out, how


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        raise SystemExit(2)
    out, how = decode(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
    print(f"decoded ({how}) {os.path.getsize(out)} bytes -> {out}")
    from kaggle_environments import make
    env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": 0})
    env.run([out, out])
    print("self-play:", [s.status for s in env.steps[-1]], [s.reward for s in env.steps[-1]])


if __name__ == "__main__":
    main()
