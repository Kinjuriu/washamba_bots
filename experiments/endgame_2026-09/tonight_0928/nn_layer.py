# ---- learned labour-job ranker: trained on 128 top-8 ladder replays to pick the job a strong
# agent's unit chose, against every other job the controller offered it that turn (softmax,
# distance penalty beta*log(d+1) learned jointly). Held-out 32 replays: top-1 on moves 0.376
# vs 0.251 for the hand-set weights, on own-tile work 0.933 vs 0.748.
import math as _nn_math
_NN_KINDS = ["FEED", "CARE", "COLLECT", "HARVEST", "WATER", "FERT", "DIG", "PLANT", "BUILD"]
_NN_CROPS = ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON"]
_NN_ANIMALS = ["GOOSE", "COW", "SHEEP"]
_NN_PROD = {"GOOSE": "EGG", "COW": "MILK", "SHEEP": "WOOL"}
NN_C = 3000.0
NN_ON = True


def _nn_feats(kind, x, y, w, v, units):
    k = "BUILD" if kind.startswith("BUILD") else kind
    f = [1.0 if k == q else 0.0 for q in _NN_KINDS]
    t = v.farm["tiles"][y][x]; t = t if isinstance(t, dict) else {}
    ds = [abs(u[0] - x) + abs(u[1] - y) for u in units]
    f += [w / 100.0, v.day / 30.0, v.hour / 24.0, sum(d <= 3 for d in ds) / 5.0, len(units) / 15.0, max(0, v.hour - 13) / 10.0]
    crop = t.get("crop") if t.get("kind") == "PLANT" else None
    an = t.get("animal")
    f += [1.0 if crop == c else 0.0 for c in _NN_CROPS] + [1.0 if an == a else 0.0 for a in _NN_ANIMALS]
    age = (v.day - int(t["planted_day"])) if crop else 0
    f += [age / 10.0, int(t.get("yield_units", 0)) / 6.0, float(int(t.get("consecutive_unwatered", 0)) >= 1),
          float(bool(t.get("watered_today"))), float(int(t.get("fertilized_until_day", -1)) >= v.day),
          float(int(t.get("consecutive_unfed", 0)) >= 1), float(bool(t.get("fed_today"))),
          float(bool(t.get("cared_today"))), int(t.get("pending_care_bonus", 0)) / 5.0]
    item = crop or (_NN_PROD.get(an) if an else None)
    p = v.price(item) if item else 0.0
    f += [_nn_math.log1p(max(0.0, p)) / 6.0]
    return f


def _nn_logit(f):
    W1, b1, W2, b2 = _NN_W["W1"], _NN_W["b1"], _NN_W["W2"], _NN_W["b2"]
    z = b2[0]
    nz = [(i, fi) for i, fi in enumerate(f) if fi]
    for j in range(len(b1)):
        a = b1[j]
        for i, fi in nz:
            a += fi * W1[i][j]
        if a > 0:
            z += a * W2[j][0]
    return z


def _nn_make_class(Base):
    class NNController(Base):
        def _tasks(self, v):
            T = Base._tasks(self, v)
            if not NN_ON:
                return T
            units = v.units
            out = []
            for (key, kind, x, y, w, arg) in T:
                if w >= 600.0:
                    out.append((key, kind, x, y, w, arg))
                    continue
                try:
                    z = _nn_logit(_nn_feats(kind, x, y, w, v, units))
                    w2 = NN_C * _nn_math.exp(max(-30.0, min(12.0, z)))
                except Exception:
                    w2 = w
                out.append((key, kind, x, y, w2, arg))
            return out
    return NNController
