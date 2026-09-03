"""Whole-plan router from one harvested lineage: opening medoid (0-71), first-shop
medoid (72-143), exact key at 144 (only if consistent with the 72-143 segment),
sibling by first shop otherwise. Rim (LEAD_K) from router_fam_lead.
usage: make_whole.py <manifest.jsonl> <tapes_dir> <sub_id> <out.py> [K]"""
import json, sys, os, re, base64, zlib, collections
man, tdir, sub, out = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4]
K = int(sys.argv[5]) if len(sys.argv) > 5 else 6
src = open("C:/Users/HP/Spidey-Hub/washamba_bots/agents/router_fam_lead.py", encoding="utf-8").read()
rows = [json.loads(l) for l in open(man) if json.loads(l)["sub"] == sub and "__" in json.loads(l)["key"]]
def c(a): return json.dumps(a, sort_keys=True, separators=(",", ":"))
T = {r["episode"]: json.load(open(f"{tdir}/{r['episode']}_{r['seat']}.json")) for r in rows}
C = {e: [c(a) for a in t] for e, t in T.items()}
def ag(a, b, lo, hi): return sum(1 for i in range(lo, hi) if a[i] == b[i]) / (hi - lo)
eps = list(T)
op = max(eps, key=lambda e: sum(ag(C[e], C[o], 0, 72) for o in eps))
eps = [e for e in eps if ag(C[e], C[op], 0, 72) >= 0.95]
print("opening medoid", op, "compatible", len(eps), "of", len(T))
byfirst = collections.defaultdict(list)
for r in rows:
    if r["episode"] in eps: byfirst[r["key"].split("__")[0]].append(r)
tapes = {"open": T[op]}; FIRST = {}; KEYS = {}; SIB = {}
for f, rs in byfirst.items():
    es = [r["episode"] for r in rs]
    m = max(es, key=lambda e: sum(ag(C[e], C[o], 72, 144) for o in es))
    FIRST[f] = "W%d" % m; tapes["W%d" % m] = T[m]; SIB[f] = "W%d" % m
    for r in sorted(rs, key=lambda r: -r["reward"]):
        e = r["episode"]
        if ag(C[e], C[m], 72, 144) >= 0.95 and r["key"] not in KEYS:
            KEYS[r["key"]] = "W%d" % e; tapes["W%d" % e] = T[e]
print("first-shop tapes", FIRST); print("keys", len(KEYS), sorted(KEYS))
data = base64.b85encode(zlib.compress(json.dumps(tapes, separators=(",", ":")).encode(), 9)).decode()
src = re.sub(r"_TAPES_DATA = '[^']*'", lambda m: "_TAPES_DATA = %r" % data, src, count=1)
src = src.replace("LEAD_K = 6", "LEAD_K = %d" % K, 1)
which = '''
W_FIRST = %r
W_KEYS = %r
W_SIB = %r
def _which(step, shops):
    if step < 72 or not shops:
        return "open"
    first = str(shops[0])
    if step < 144 or len(shops) < 2:
        return W_FIRST.get(first, "open")
    key = "%%s__%%s" %% (shops[0], shops[1])
    return W_KEYS.get(key) or W_SIB.get(first, "open")
''' % (FIRST, KEYS, SIB)
i = src.index("def _which(step, shops):"); j = src.index("def agent(observation")
# keep the rim definitions that sit between _which and agent
mid = src[i:j]; k = mid.index("\nLEAD_K")
src = src[:i] + which + mid[k:] + src[j:]
open(out, "w", encoding="utf-8").write(src); print("wrote", out)
