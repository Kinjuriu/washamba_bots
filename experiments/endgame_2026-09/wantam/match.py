import sys, json
from multiprocessing import Pool
from kaggle_environments import make
A, B = sys.argv[1], sys.argv[2]
seeds = [int(s) for s in sys.argv[3].split(",")]
def play(a):
    seed, seat = a
    env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})
    ag = [A, B] if seat == 0 else [B, A]
    env.run(ag)
    r = [s.reward for s in env.steps[-1]]; st = [s.status for s in env.steps[-1]]
    return seed, seat, r[seat], r[1 - seat], st
if __name__ == "__main__":
    jobs = [(s, t) for s in seeds for t in (0, 1)]
    with Pool(int(sys.argv[4]) if len(sys.argv) > 4 else 2) as p:
        res = p.map(play, jobs)
    w = l = t = 0; tot = 0
    for seed, seat, a, b, st in res:
        m = a - b; tot += m
        w += m > 0; l += m < 0; t += m == 0
        print(seed, seat, a, b, int(m), st)
    print("W-L-T %d-%d-%d mean margin %.0f n=%d" % (w, l, t, tot / len(res), len(res)))
    json.dump(res, open("match_%s_%s.json" % (A.split("/")[-1][:-3], B.split("/")[-1][:-3]), "w"))
