import sys, time, json
from kaggle_environments import make
A = sys.argv[1]; seed = int(sys.argv[2])
t0 = time.time()
env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})
env.run([A, A])
print(json.dumps(dict(seed=seed, wall=round(time.time()-t0,1), rewards=[s.reward for s in env.steps[-1]], status=[s.status for s in env.steps[-1]], nsteps=len(env.steps))))
