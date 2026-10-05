import sys, collections
from kaggle_environments import make
A=sys.argv[1]; seed=int(sys.argv[2])
env=make("kaggriculture",configuration={"episodeSteps":720,"seed":seed}); env.run([A,A])
for day in (6,10,14,18,22,26,29):
    st=env.steps[day*24][0].observation; farm=st["farms"][0]
    c=collections.Counter()
    for row in farm["tiles"]:
        for t in row:
            if t=="LOCKED": c["LOCKED"]+=1
            elif t is None: c["EMPTY"]+=1
            elif t.get("kind")=="PLANT": c["P_"+t["crop"]]+=1
            elif "animal" in t: c["A_"+t["animal"]]+=1
            else: c[t.get("kind","?")]+=1
    print("day",day,"money",farm["money"],dict(sorted(c.items())))
