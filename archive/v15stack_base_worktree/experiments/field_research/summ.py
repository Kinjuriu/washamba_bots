import json, sys, statistics as st
from fetch import episodes
US=16675684
def rows(sub):
    out=[]
    for ep in episodes(sub).get("episodes",[]):
        if ep.get("state")!="COMPLETED": continue
        m=[a for a in ep["agents"] if a.get("submissionId")==int(sub)]; o=[a for a in ep["agents"] if a.get("submissionId")!=int(sub)]
        if not m or not o or m[0].get("reward") is None or o[0].get("reward") is None: continue
        m,o=m[0],o[0]
        out.append(dict(ep=ep["id"],t=ep["endTime"],seat=m.get("index",0),mine=m["reward"],opp=o["reward"],r0=m.get("initialScore"),r1=m.get("updatedScore"),orat=o.get("initialScore"),oteam=o.get("teamId"),osub=o.get("submissionId")))
    return sorted(out,key=lambda r:r["t"])
def summ(sub,rs,label=""):
    if not rs: print(sub,"no rows"); return
    w=sum(r["mine"]>r["opp"] for r in rs); t=sum(r["mine"]==r["opp"] for r in rs)
    print(f"{sub} {label} n={len(rs)} W-L-T={w}-{len(rs)-w-t}-{t} ({100*w/len(rs):.0f}%) bank={st.mean(r['mine'] for r in rs):,.0f} opp={st.mean(r['opp'] for r in rs):,.0f} margin={st.mean(r['mine']-r['opp'] for r in rs):+,.0f} med={st.median(r['mine']-r['opp'] for r in rs):+,.0f} oppRating={st.mean(r['orat'] or 0 for r in rs):,.0f} {rs[0]['t'][:16]}..{rs[-1]['t'][:16]} rating={rs[-1]['r1']:.0f}")
if __name__=="__main__":
    for s in sys.argv[1:]:
        rs=rows(s); summ(s,rs,"all"); ss=[r for r in rs if (r["orat"] or 0)>=2000]; summ(s,ss,"opp>=2000")
        for seat in (0,1): summ(s,[r for r in ss if r["seat"]==seat],f"steady seat{seat}")
