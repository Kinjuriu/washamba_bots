import sys, json, gzip, math, random, csv, collections
sys.path.insert(0, "/home/claude/splice/experiments/splice")
import controller as C
from price_model import WB_PriceModel
from sell_engine import WB_SellEngine
KINDS = ["FEED", "CARE", "COLLECT", "HARVEST", "WATER", "FERT", "DIG", "PLANT", "BUILD"]
OP2K = {"FEED": "FEED", "CARE": "CARE", "COLLECT_FERTILIZER": "COLLECT", "HARVEST": "HARVEST", "WATER": "WATER",
        "FERTILIZE": "FERT", "DIG": "DIG", "PLANT": "PLANT", "BUILD_PASTURE": "BUILD", "BUILD_COOP": "BUILD"}
UNITOPS = ("PICKUP", "DROP", "PLACE")
MOVES = ("NORTH", "SOUTH", "EAST", "WEST")
CROPS = ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON"]
ANIMALS = ["GOOSE", "COW", "SHEEP"]
PROD = {"GOOSE": "EGG", "COW": "MILK", "SHEEP": "WOOL"}
NNEG = 15

def jfeats(kind, x, y, w, v, units):
    k = "BUILD" if kind.startswith("BUILD") else kind
    f = [1.0 if k == q else 0.0 for q in KINDS]
    t = v.farm["tiles"][y][x]; t = t if isinstance(t, dict) else {}
    ds = [abs(u[0] - x) + abs(u[1] - y) for u in units]
    f += [w / 100.0, v.day / 30.0, v.hour / 24.0, sum(d <= 3 for d in ds) / 5.0, len(units) / 15.0, max(0, v.hour - 13) / 10.0]
    crop = t.get("crop") if t.get("kind") == "PLANT" else None
    an = t.get("animal")
    f += [1.0 if crop == c else 0.0 for c in CROPS] + [1.0 if an == a else 0.0 for a in ANIMALS]
    age = (v.day - int(t["planted_day"])) if crop else 0
    f += [age / 10.0, int(t.get("yield_units", 0)) / 6.0, float(int(t.get("consecutive_unwatered", 0)) >= 1),
          float(bool(t.get("watered_today"))), float(int(t.get("fertilized_until_day", -1)) >= v.day),
          float(int(t.get("consecutive_unfed", 0)) >= 1), float(bool(t.get("fed_today"))),
          float(bool(t.get("cared_today"))), int(t.get("pending_care_bonus", 0)) / 5.0]
    item = crop or (PROD.get(an) if an else None)
    p = v.price(item) if item else 0.0
    f += [math.log1p(max(0.0, p)) / 6.0]
    return f

def run(path, seat, full_eval, seed=0, lo=144):
    rnd = random.Random(seed)
    d = json.load(gzip.open(path)); S = d["steps"]
    pm = WB_PriceModel(); ctrl = C.WB_Controller(pm, WB_SellEngine(pm))
    cov = collections.Counter(); groups = []
    # per unit index: list of (turn, op, pos) for work actions
    acts = {}
    for t in range(1, len(S)):
        a = S[t][seat]["action"] or {}; o = S[t - 1][seat]["observation"]; farm = o["farms"][seat]
        pos = [farm["farmer"]] + list(farm["hands"])
        ua = [a.get("farmer")] + list(a.get("hands") or [])
        acts[t] = [(u[0] if u else "PASS", tuple(pos[i]) if i < len(pos) and pos[i] else None) for i, u in enumerate(ua)]
    for t in range(max(lo, 1), len(S)):
        o = dict(S[t - 1][seat]["observation"]); o["step"] = t - 1; o["player"] = seat
        try:
            v = C._WB_View(o)
            if v.day != ctrl.plan_day or ctrl.plan is None:
                ctrl.plan_day = v.day
                try: ctrl.plan = ctrl._dawn(v)
                except Exception: ctrl.plan = ctrl._default_plan(v)
            tasks = ctrl._tasks(v)
        except Exception:
            cov["view_error"] += 1; continue
        units = v.units
        tset = {}
        for (key, kind, x, y, w, arg) in tasks:
            k = "BUILD" if kind.startswith("BUILD") else kind
            tset[(k, x, y)] = (kind, w)
        feats_cache = {}
        for i, (op, pos) in enumerate(acts.get(t, [])):
            if pos is None or op == "PASS": continue
            inv = v.invs[i] if i < len(v.invs) else {}
            if op in UNITOPS: cov["unitop:" + op] += 1; continue
            if op in OP2K:
                k = OP2K[op]; kind_label = "work"; tgt = (k, pos[0], pos[1])
            elif op in MOVES:
                # destination: this unit's next work action within 12 turns, same day
                tgt = None
                for t2 in range(t + 1, min(len(S), t + 13)):
                    if (t2 - 1) // 24 != (t - 1) // 24: break
                    L = acts.get(t2, [])
                    if i >= len(L): break
                    op2, pos2 = L[i]
                    if op2 in OP2K: tgt = (OP2K[op2], pos2[0], pos2[1]); break
                    if op2 in UNITOPS: break
                if tgt is None: cov["move:no_dest"] += 1; continue
                kind_label = "move"; k = tgt[0]
            else:
                cov["other:" + op] += 1; continue
            hit = tgt in tset
            cov["%s:%s:%s" % (kind_label, k, "hit" if hit else "miss")] += 1
            if not hit: continue
            # candidates this unit could take (executor's own feasibility filter)
            cands = []
            for (kk, x, y), (kind, w) in tset.items():
                if kk == "FEED" and inv.get("WHEAT", 0) <= 0 and (kk, x, y) != tgt: continue
                if kk == "FERT" and inv.get("FERTILIZER", 0) <= 0 and (kk, x, y) != tgt: continue
                cands.append((kk, x, y))
            ci = cands.index(tgt)
            if not full_eval:
                neg = [c for c in cands if c != tgt]
                neg = rnd.sample(neg, min(NNEG, len(neg)))
                cands = [tgt] + neg; ci = 0
            F = []; Dd = []; Wp = []
            for c in cands:
                if c not in feats_cache:
                    kind, w = tset[c]; feats_cache[c] = (jfeats(kind, c[1], c[2], w, v, units), w)
                f, w = feats_cache[c]
                F.append(f); Dd.append(abs(pos[0] - c[1]) + abs(pos[1] - c[2])); Wp.append(w)
            groups.append({"t": t, "src": kind_label, "ci": ci, "F": F, "d": Dd, "w": Wp})
    return cov, groups

if __name__ == "__main__":
    from multiprocessing import Pool
    man = list(csv.DictReader(open("nn_manifest.csv")))
    jobs = [(gi, m["file"], int(m["seat"])) for gi, m in enumerate(man)]
    if len(sys.argv) > 1: jobs = jobs[: int(sys.argv[1])]
    def job(a):
        gi, f, s = a
        try:
            cov, g = run(f, s, full_eval=(gi % 5 == 0))
            if gi % 5 == 0:   # held-out: keep a fifth of full groups to bound size
                g = g[::5]
            return gi, f, dict(cov), g
        except Exception as e:
            import traceback; return gi, f, repr(e) + traceback.format_exc()[-400:], []
    with Pool(2) as p, open("groups.jsonl", "w") as out:
        tot = collections.Counter()
        for gi, f, cov, g in p.imap_unordered(job, jobs):
            if isinstance(cov, str): print("ERR", f, cov, flush=True); continue
            tot.update(cov)
            out.write(json.dumps({"gi": gi, "ep": f, "cov": cov, "groups": g}) + "\n"); out.flush()
            print(gi, f, len(g), flush=True)
        json.dump(dict(tot), open("coverage.json", "w"), indent=1)
