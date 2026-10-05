import json, numpy as np, sys
H = int(sys.argv[1]) if len(sys.argv) > 1 else 16
SRC = sys.argv[2] if len(sys.argv) > 2 else "work,move"
srcs = SRC.split(",")
import pickle
Z = np.load("train.npz"); X = Z["X"]; O = Z["O"]; WK = Z["work"]
if srcs == ["work"]: X = X[WK]; O = O[WK]
if srcs == ["move"]: X = X[~WK]; O = O[~WK]
ev = [g for gi, g in pickle.load(open("eval.pkl", "rb"))]
D = X.shape[2]
print("train groups", len(X), "eval groups", len(ev), flush=True)
rng = np.random.default_rng(0)
P = {"W1": rng.normal(0, np.sqrt(2 / D), (D, H)).astype(np.float32), "b1": np.zeros(H, np.float32),
     "W2": rng.normal(0, np.sqrt(1 / H), (H, 1)).astype(np.float32), "b2": np.zeros(1, np.float32), "beta": np.ones(1, np.float32)}
Mo = {k: np.zeros_like(v) for k, v in P.items()}; Ve = {k: np.zeros_like(v) for k, v in P.items()}
def g_(x):
    h = np.maximum(0, x @ P["W1"] + P["b1"]); return h, (h @ P["W2"])[..., 0] + P["b2"][0]
def top1(groups, scorer):
    ok = 0
    for g in groups:
        s = scorer(g); ok += int(np.argmax(s) == g["ci"])
    return ok / max(1, len(groups))
def model_s(g):
    F = np.array(g["F"], np.float32); _, z = g_(F); return z - P["beta"][0] * np.log1p(np.array(g["d"], np.float32))
def peter_s(g): return np.array(g["w"]) / (np.array(g["d"]) + 1.0) + 1e-9 * np.random.rand(len(g["w"]))
def near_s(g): return -np.array(g["d"], float) + 1e-3 * np.random.rand(len(g["d"]))
lr = 3e-3; step = 0
for ep in range(int(sys.argv[3]) if len(sys.argv) > 3 else 4):
    idx = rng.permutation(len(X))
    for b in range(0, len(idx), 512):
        j = idx[b:b + 512]; x = X[j].astype(np.float32); o = O[j].astype(np.float32)
        h, z = g_(x); lg = z + P["beta"][0] * np.maximum(o, -50) + np.where(o < -50, -1e4, 0); lg -= lg.max(1, keepdims=True); p = np.exp(lg); p /= p.sum(1, keepdims=True)
        gz = p.copy(); gz[:, 0] -= 1; gz /= len(j)
        gW2 = np.einsum("nkh,nk->h", h, gz)[:, None]; gb2 = np.array([gz.sum()], np.float32)
        dh = gz[..., None] * P["W2"][:, 0][None, None, :] * (h > 0)
        gW1 = np.einsum("nkd,nkh->dh", x, dh); gb1 = dh.sum((0, 1)); gbeta = np.array([(gz * np.maximum(o, -50)).sum()], np.float32)
        step += 1
        for k, gk in (("W1", gW1), ("b1", gb1), ("W2", gW2), ("b2", gb2), ("beta", gbeta)):
            Mo[k] = 0.9 * Mo[k] + 0.1 * gk; Ve[k] = 0.999 * Ve[k] + 0.001 * gk * gk
            P[k] -= lr * (Mo[k] / (1 - 0.9 ** step)) / (np.sqrt(Ve[k] / (1 - 0.999 ** step)) + 1e-8)
    for s in ("work", "move"):
        e = [g for g in ev if g["src"] == s]
        print("epoch %d %s held-out top-1: model %.3f  peter %.3f  nearest %.3f  (n=%d, mean cands %.0f)" % (
            ep, s, top1(e, model_s), top1(e, peter_s), top1(e, near_s), len(e), np.mean([len(g["F"]) for g in e])), flush=True)
    print("beta", P["beta"][0], flush=True)
json.dump({k: v.tolist() for k, v in P.items()}, open("wts2_h%d_%s.json" % (H, SRC.replace(",", "")), "w"))
