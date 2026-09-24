"""Add missing route keys to router_yuan_nf without touching any tape it already
holds. usage: augment.py <manifest.jsonl> <tapes_dir> <sub_id> <out.py>"""
import json, sys, os, re, io, base64, zlib, collections
man, tdir, sub, out = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4]
BASE = "C:/Users/HP/Spidey-Hub/washamba_bots/agents/router_yuan_nf.py"
src = io.open(BASE, encoding="utf-8").read()
tapes = json.loads(zlib.decompress(base64.b85decode(
    re.search(r"_TAPES_DATA = '([^']*)'", src).group(1))).decode())
FIRST = eval(re.search(r"^W_FIRST = (\{.*?\})$", src, re.M).group(1))
KEYS = eval(re.search(r"^W_KEYS = (\{.*?\})$", src, re.M).group(1))
SIB = eval(re.search(r"^W_SIB = (\{.*?\})$", src, re.M).group(1))
def c(a): return json.dumps(a, sort_keys=True, separators=(",", ":"))
C = {k: [c(a) for a in t] for k, t in tapes.items()}
def ag(a, b, lo, hi):
    n = min(len(a), len(b), hi)
    if n <= lo: return 0.0
    return sum(1 for i in range(lo, n) if a[i] == b[i]) / (n - lo)
rows = [json.loads(l) for l in open(man)]
rows = [r for r in rows if r["sub"] == sub and "__" in r.get("key", "")]
rows.sort(key=lambda r: -r["reward"])
print("manifest rows for sub:", len(rows), "| existing keys:", len(KEYS))
added, seen = [], set()
skip = collections.Counter()
for r in rows:
    key, first = r["key"], r["key"].split("__")[0]
    if key in KEYS or key in seen: skip["already"] += 1; continue
    if first not in FIRST: skip["no first-shop medoid"] += 1; continue
    p = f"{tdir}/{r['episode']}_{r['seat']}.json"
    if not os.path.exists(p): skip["tape missing"] += 1; continue
    t = json.load(open(p)); ct = [c(a) for a in t]
    a0 = ag(ct, C["open"], 0, 72)
    a1 = ag(ct, C[FIRST[first]], 72, 144)
    if a0 < 0.95: skip["opening <0.95"] += 1; continue
    if a1 < 0.95: skip["segment <0.95"] += 1; continue
    name = "W%d" % r["episode"]
    tapes[name] = t; KEYS[key] = name; seen.add(key)
    added.append((key, name, r["reward"], round(a0, 3), round(a1, 3)))
print("skipped:", dict(skip))
print("ADDED %d keys:" % len(added))
for a in added: print("  %-34s %-12s reward %7d  ag71 %.2f ag143 %.2f" % a)
print("keys now", len(KEYS), "of 64 possible")
data = base64.b85encode(zlib.compress(json.dumps(tapes, separators=(",", ":")).encode(), 9)).decode()
src = re.sub(r"_TAPES_DATA = '[^']*'", lambda m: "_TAPES_DATA = %r" % data, src, count=1)
src = re.sub(r"^W_KEYS = \{.*?\}$", lambda m: "W_KEYS = %r" % KEYS, src, count=1, flags=re.M)
io.open(out, "w", encoding="utf-8").write(src)
print("wrote", out, os.path.getsize(out), "bytes")
# sanity: the no-flip opening must survive untouched
chk = json.loads(zlib.decompress(base64.b85decode(
    re.search(r"_TAPES_DATA = '([^']*)'", io.open(out, encoding="utf-8").read()).group(1))).decode())
print("open[0]", chk["open"][0], "open[1]", chk["open"][1])
assert chk["open"] == tapes["open"], "opening tape changed!"
