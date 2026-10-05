import json, collections
def load(p): return json.load(open(p))
def unit_acts(a): return json.dumps([a.get("farmer"),a.get("hands")],sort_keys=True) if isinstance(a,dict) else "X"
def agree(d,s0,s1,lo,hi):
    n=0
    for i in range(lo,min(hi,len(d["steps"]))):
        if unit_acts(d["steps"][i][s0]["action"])==unit_acts(d["steps"][i][s1]["action"]): n+=1
    return n/(hi-lo)
def sells(d,seat):
    out=collections.defaultdict(list)  # product -> [(step,qty)]
    for i,s in enumerate(d["steps"]):
        a=s[seat]["action"]
        if not isinstance(a,dict): continue
        for o in a.get("market") or []:
            if o and o[0]=="SELL": out[o[1]].append((i,o[2]))
    return out
def profile(d,seat):
    c=collections.Counter()
    for i,s in enumerate(d["steps"]):
        a=s[seat]["action"]
        if not isinstance(a,dict): continue
        for o in a.get("market") or []:
            if not o: continue
            if o[0] in("SELL","BUY_SEED","BUY_PRODUCT","BUY_ANIMAL"): c[f"{o[0]}_{o[1]}"]+=o[2] if len(o)>2 else 1
            else: c[o[0]]+=1
        for u in [a.get("farmer")]+list(a.get("hands") or []):
            if u: c["u_"+u[0]+("_"+str(u[1]) if u[0]=="PLANT" and len(u)>1 else "")]+=1
    return c
def lead(d,me,opp):
    """mean step lead of opp SELL orders vs ours for premium products, matched by cumulative qty"""
    sm,so=sells(d,me),sells(d,opp); diffs=[]
    for prod in sm:
        if prod in("WHEAT","FERTILIZER") or prod not in so: continue
        def cum(l):
            out=[];t=0
            for st,q in l:
                for _ in range(q): out.append(st)
            return out
        a,b=cum(sm[prod]),cum(so[prod])
        diffs+= [x-y for x,y in zip(a,b) if x>=144]  # positive => opp sold that unit earlier
    return diffs
