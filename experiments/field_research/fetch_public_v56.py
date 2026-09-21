"""Fetch ahmedberatozer's public V56 notebook and decode its agent - WITHOUT executing it.

Same rule as experiments/route_v20.py: the decoded agent is a local sparring partner
and a submission candidate, it is gitignored and never committed from here.

    python experiments/field_research/fetch_public_v56.py

Writes experiments/field_research/public_agents/v56.py, verified byte-for-byte against
the SHA-256 the notebook itself publishes. The notebook states Apache-2.0 with upstream
notices retained inside the source; confirm the licence field on the notebook page
before submitting a derivative.
"""
import ast, base64, hashlib, json, os, urllib.request, zlib

VERSION_ID = 351622802  # kaggle.com/code/ahmedberatozer/kaggriculture-v56-smarter-seeds-and-fertilizer
URL = f"https://www.kaggle.com/kernels/scriptcontent/{VERSION_ID}/download"
SHA256 = "a1ad0fd1d174477ee2cbdd561a812bcb7029647ce34599e79d6b79e9057eff6c"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "public_agents", "v56.py")


def main():
    req = urllib.request.Request(URL, headers={"User-Agent": "Mozilla/5.0"})
    nb = json.load(urllib.request.urlopen(req, timeout=180))
    for cell in nb["cells"]:
        src = "".join(cell["source"])
        if cell["cell_type"] != "code" or "SOURCE_BLOB" not in src:
            continue
        for node in ast.walk(ast.parse(src)):  # parsed, never exec'd
            if (isinstance(node, ast.Call) and getattr(node.func, "attr", "") == "join"
                    and node.args and isinstance(node.args[0], (ast.Tuple, ast.List))):
                blob = "".join(e.value for e in node.args[0].elts if isinstance(e, ast.Constant))
                raw = zlib.decompress(base64.b85decode(blob))
                got = hashlib.sha256(raw).hexdigest()
                if got != SHA256:
                    raise SystemExit(f"SHA-256 mismatch: {got}")
                last = [n.name for n in ast.parse(raw).body if isinstance(n, ast.FunctionDef)][-1]
                os.makedirs(os.path.dirname(OUT), exist_ok=True)
                open(OUT, "wb").write(raw)
                print(f"wrote {OUT} ({len(raw):,} bytes), sha256 verified, entrypoint (last def): {last}")
                return
    raise SystemExit("payload not found - the notebook layout changed")


if __name__ == "__main__":
    main()
