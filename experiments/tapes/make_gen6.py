"""Build gen-6 router: router_fam_lead + harvested lineage per-key tapes.
usage: make_gen6.py <out.py> [K]"""
import json, sys, os, re, base64, zlib
S = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
out = sys.argv[1]; K = int(sys.argv[2]) if len(sys.argv) > 2 else 6
src = open("C:/Users/HP/Spidey-Hub/washamba_bots/agents/router_fam_lead.py", encoding="utf-8").read()
tapes = json.loads(zlib.decompress(base64.b85decode(re.search(r"_TAPES_DATA = '([^']*)'", src).group(1))).decode())
rows = [json.loads(l) for l in open(S + "/yarn2/manifest.jsonl")]
COMPAT_72 = (55956879, 55958920)   # subs whose opening is our fam opening (ag71 1.00)
ok = [r for r in rows if r["ag71"] >= 0.95 and "__" in r["key"] and (r["ag143"] >= 0.95 or (r["first"] == "YARN_STORE" and r["sub"] in COMPAT_72))]
best = {}
for r in sorted(ok, key=lambda r: -r["reward"]):
    best.setdefault(r["key"], r)
LIN, sib = {}, {}
for key, r in best.items():
    name = "L%d" % r["episode"]
    tapes[name] = json.load(open(f"{S}/yarn2/tapes/{r['episode']}_{r['seat']}.json"))
    LIN[key] = name
for key, name in sorted(LIN.items(), key=lambda kv: -best[kv[0]]["reward"]):
    a, b = key.split("__")
    if b != "YARN_STORE" or a == "YARN_STORE":
        sib.setdefault(a, name)
# yarn-first: one tape must carry steps 72-143 (second shop unknown at 72). Pick the
# medoid over 72-143 among the yarn-first tapes; keep only exact keys that agree
# >= 0.95 with it over 72-143, the rest fall back to the medoid tape at 144.
import json as _j
def _c(a): return _j.dumps(a, sort_keys=True, separators=(",", ":"))
yf = {k: [_c(a) for a in tapes[v][72:144]] for k, v in LIN.items() if k.startswith("YARN_STORE__")}
def _ag(a, b): return sum(x == y for x, y in zip(a, b)) / len(a)
yf72 = None
if yf:
    med = max(yf, key=lambda k: sum(_ag(yf[k], yf[o]) for o in yf))
    yf72 = LIN[med]
    for k in list(yf):
        if _ag(yf[k], yf[med]) < 0.95:
            print("drop yarn-first key (72-143 mismatch with medoid %s): %s %.2f" % (med, k, _ag(yf[k], yf[med])))
            del LIN[k]
    sib["YARN_STORE"] = yf72
data = base64.b85encode(zlib.compress(json.dumps(tapes, separators=(",", ":")).encode(), 9)).decode()
src = re.sub(r"_TAPES_DATA = '[^']*'", lambda m: "_TAPES_DATA = %r" % data, src, count=1)
src = src.replace("HANDOVER_AT_72 = True", "HANDOVER_AT_72 = %s\nLIN_KEYS = %r\nLIN_SIB = %r\nYF72 = %r" % (yf72 is None, LIN, sib, yf72), 1)
src = src.replace("LEAD_K = 6", "LEAD_K = %d" % K, 1)
old72 = '        if HANDOVER_AT_72 and first == "YARN_STORE":\n'
assert old72 in src
src = src.replace(old72, '        if YF72 and first == "YARN_STORE":\n            return YF72\n' + old72, 1)
old = '    key = "%s__%s" % (shops[0], shops[1])\n'
assert old in src
src = src.replace(old, old + '    if key in LIN_KEYS:\n        return LIN_KEYS[key]\n    if (str(shops[1]) != "YARN_STORE" or first == "YARN_STORE") and first in LIN_SIB:\n        return LIN_SIB[first]\n', 1)
open(out, "w", encoding="utf-8").write(src)
print("wrote", out, "keys", sorted(LIN), "sib", sib, "YF72", yf72)
