"""Day-14 identical-board test. W3 plays both seats to HANDOVER; then the candidate
controller takes seat `seat`, the other seat keeps playing W3. Margin = candidate
final bank minus W3-continuing final bank in the same seat and seed."""
import sys, os, json, time, importlib.util, itertools
from multiprocessing import Pool
HERE = os.path.dirname(os.path.abspath(__file__))
SPLICE = os.environ.get("WA_DIR", os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE); sys.path.insert(0, SPLICE)
HANDOVER = int(os.environ.get("H_STEP", 336))
BASE = os.environ.get("H_BASE", os.path.join(HERE, "w3_herdsafe2700.py"))
_cnt = itertools.count()

def load_last_callable(path):
    spec = importlib.util.spec_from_file_location(f"_m{next(_cnt)}_{os.getpid()}", path)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return [v for v in vars(m).values() if callable(v)][-1]

def call(fn, obs, cfg):
    n = getattr(getattr(fn, "__code__", None), "co_argcount", 2)
    return fn(*([obs, cfg][:n]))

def make_ctrl(kind):
    import importlib
    import price_model, sell_engine, dump_predictor
    pm = price_model.WB_PriceModel(); dp = dump_predictor.WB_DumpPredictor(pm)
    se = sell_engine.WB_SellEngine(pm, predictor=dp)
    if kind == "peter":
        import controller
        for kv in filter(None, os.environ.get("H_SET", "").split(";")):
            k, val = kv.split("=", 1); setattr(controller, k, json.loads(val))
        c = controller.WB_Controller(pm, se)
    else:
        mod = importlib.import_module(kind)
        import controller
        for kv in filter(None, os.environ.get("H_SET", "").split(";")):
            k, val = kv.split("=", 1)
            setattr(mod if hasattr(mod, k) else controller, k, json.loads(val))
        c = mod.make(pm, se)
    return c, dp

def hybrid(kind):
    base = load_last_callable(BASE)
    ctrl, dp = make_ctrl(kind)
    st = {"ctrl": ctrl}
    def ag(obs, cfg=None):
        try: dp.observe(obs)
        except Exception: pass
        if obs["step"] < HANDOVER:
            return call(base, obs, cfg)
        return ctrl.act(obs)
    ag.state = st
    return ag

def play(job):
    seed, seat, kind = job
    from kaggle_environments import make
    t0 = time.time()
    a = [load_last_callable(BASE), load_last_callable(BASE)]
    if kind:
        a[seat] = hybrid(kind)
    env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed}, debug=False)
    env.run(a)
    last = env.steps[-1]
    traj = [int(env.steps[d*24][seat].observation.farms[seat]["money"]) for d in range(14, 30)]
    res = {"traj": traj, "seed": seed, "seat": seat, "kind": kind, "bank": [s.reward for s in last],
           "status": [s.status for s in last], "sec": round(time.time() - t0, 1)}
    if kind:
        c = a[seat].state["ctrl"]
        res["errors"] = getattr(c, "errors", 0); res["last_error"] = getattr(c, "last_error", None)
        if hasattr(c, "summary"): res["summary"] = c.summary()
    return res

def refs(seeds, seats):
    path = os.path.join(HERE, f"ref_{HANDOVER}_{os.path.basename(BASE)}.json")
    have = json.load(open(path)) if os.path.exists(path) else {}
    need = [(s, s % 2, None) for s in seeds if str(s) not in have or ("traj_%d_%d" % (s, s % 2)) not in have]
    if need:
        with Pool(2) as p:
            for r in p.imap_unordered(play, need):
                have[str(r["seed"])] = r["bank"]; have["traj_%d_%d" % (r["seed"], r["seat"])] = r["traj"]
        json.dump(have, open(path, "w"))
    return have

if __name__ == "__main__":
    kind = sys.argv[1]
    seeds = [int(x) for x in (sys.argv[2] if len(sys.argv) > 2 else "900,901,902,903,904,905,906,907").split(",")]
    jobs = [(s, s % 2, kind) for s in seeds]
    ref = refs(seeds, None)
    out = []
    with Pool(2) as p:
        for r in p.imap_unordered(play, jobs):
            rb = ref[str(r["seed"])][r["seat"]]
            r["margin"] = r["bank"][r["seat"]] - rb
            r["ref"] = rb
            rt = ref.get("traj_%d_%d" % (r["seed"], r["seat"]))
            if rt: r["dtraj"] = [a - b for a, b in zip(r["traj"], rt)]
            out.append(r)
            print(json.dumps({k: r.get(k) for k in ("seed", "seat", "margin", "errors")}), "d14..29 gap:", [round(x/1000,1) for x in r.get("dtraj", [])[::3]], flush=True)
            if r.get("last_error"): print("  ERR", r["last_error"][-300:], flush=True)
    ms = sorted(r["margin"] for r in out)
    print(f"{kind} {os.environ.get('H_SET','')} H={HANDOVER} n={len(ms)} mean {sum(ms)/len(ms):.0f} median {ms[len(ms)//2]:.0f}")
    with open(os.path.join(HERE, "h14_results.jsonl"), "a") as f:
        for r in out: f.write(json.dumps({k: v for k, v in r.items() if k != "last_error"}) + "\n")
