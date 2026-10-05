"""Behavioural probe per analysed seat: stranded value at checkpoints, shed-to-sale lags, sale structure,
herd vs shops, land timing, opponent-responsiveness, price sensitivity, labour-action hashes.
Usage: policy_probe.py out.jsonl SIDE files...   SIDE in TOP | R712 | washamba_bots | ALL"""
import gzip,json,sys,os,collections,hashlib
TOP=["Boey","M & M & P & Q","DSM","Unknown Mother-Goose","DECEM","吃白饭的大肥鱼"]
R712=["Kaggledew Valley 🏆","Kaggledew Valley","Azat Akhtyamov","THIRD FARM CLUB","Arda Ceylan","mtmr_s1","TheEggman"]
PREM=("WOOL","MILK","STRAWBERRY","MELON")
BASE={"WHEAT":25,"CARROT":35,"TOMATO":60,"STRAWBERRY":120,"MELON":250,"EGG":50,"MILK":160,"WOOL":200,"FERTILIZER":100}
ANP={"SHEEP":"WOOL","COW":"MILK","GOOSE":"EGG"}
MILK_SHOPS=("PIZZA_SHOP","ICE_CREAM_SHOP","SMOOTHIE_SHOP"); EGG_SHOPS=("BAKERY","BRUNCH_SPOT")
side=sys.argv[2]
def want(name):
    if side=="ALL": return True
    if side=="TOP": return name in TOP
    if side=="R712": return name in R712
    return name==side
def probe(path):
    d=json.load(gzip.open(path)); st=d['steps']; names=d['info']['TeamNames']; out=[]
    for s in (0,1):
        if not want(names[s]): continue
        o=1-s; rec=dict(ep=os.path.basename(path).split('.')[0],seat=s,name=names[s],opp=names[o],bank=d['rewards'][s],opp_bank=d['rewards'][o])
        # series
        shed=[st[t][s]['observation']['private']['shed'] for t in range(len(st))]
        oshed=[st[t][o]['observation']['private']['shed'] for t in range(len(st))]
        prices=[st[t][0]['observation']['market']['prices'] for t in range(len(st))]
        farms=[st[t][0]['observation']['farms'][s] for t in range(len(st))]
        # checkpoints
        cps={}
        for day in (6,12,18,24,29):
            t=min(day*24,len(st)-1); pr=prices[t]; priv=st[t][s]['observation']['private']; f=farms[t]
            shedv=sum(v*pr.get(k,0) for k,v in priv['shed'].items() if k in pr)
            invv=sum(v*pr.get(k,0) for inv in priv['inventories'] for k,v in inv.items() if k in pr)
            tilev=0
            for row in f['tiles']:
                for tile in row:
                    if isinstance(tile,dict):
                        if 'animal' in tile: tilev+=tile.get('yield_units',0)*pr.get(ANP[tile['animal']],0)
                        elif tile.get('kind')=='PLANT': tilev+=tile.get('yield_units',0)*pr.get(tile['crop'],0)
            cps[day]=dict(cash=f['money'],shed=shedv,inv=invv,tile=tilev)
        rec['cps']=cps
        tl=st[-1][s]['observation']['private']; pr=prices[-1]
        rec['terminal_unsold']=sum(v*pr.get(k,0) for k,v in tl['shed'].items() if k in pr)+sum(v*pr.get(k,0) for inv in tl['inventories'] for k,v in inv.items() if k in pr)
        # shed-to-sale lag (FIFO) and sale events for premium items; opponent sale steps
        lags={}; sale_events={}; opp_sales={}
        for p in PREM:
            fifo=collections.deque(); L=[]; ev=[]
            for t in range(1,len(st)):
                dlt=shed[t].get(p,0)-shed[t-1].get(p,0)
                if dlt>0: fifo.append([t,dlt])
                elif dlt<0:
                    n=-dlt; stock=shed[t-1].get(p,0)
                    ev.append(dict(t=t,n=n,frac=n/stock if stock else 1.0,pb=prices[t-1].get(p,0)/BASE[p],h=t%4))
                    while n>0 and fifo:
                        if fifo[0][1]<=n: n-=fifo[0][1]; L.extend([t-fifo[0][0]]*fifo[0][1]); fifo.popleft()
                        else: fifo[0][1]-=n; L.extend([t-fifo[0][0]]*n); n=0
            lags[p]=L; sale_events[p]=ev
            opp_sales[p]=[t for t in range(1,len(st)) if oshed[t].get(p,0)<oshed[t-1].get(p,0)]
        rec['lags']={p:(sorted(L)[len(L)//2] if L else None, sum(1 for x in L if x<=6)/len(L) if L else None, sum(1 for x in L if x<=24)/len(L) if L else None, len(L)) for p,L in lags.items()}
        # sale structure + responsiveness + price sensitivity
        struct={}
        for p in PREM:
            ev=sale_events[p]; os_=set(opp_sales[p])
            if not ev: continue
            after=sum(1 for e in ev if any((e['t']-k) in os_ for k in (1,2)))
            before=sum(1 for e in ev if any((e['t']+k) in os_ for k in (1,2)))
            same=sum(1 for e in ev if e['t'] in os_)
            fracs=sorted(e['frac'] for e in ev)
            struct[p]=dict(n=len(ev),h2=sum(1 for e in ev if e['h']==2)/len(ev),frac_med=fracs[len(fracs)//2],full=sum(1 for e in ev if e['frac']>=0.99)/len(ev),
                           pb_med=sorted(e['pb'] for e in ev)[len(ev)//2],after_opp=after/len(ev),before_opp=before/len(ev),same_step=same/len(ev))
            # price sensitivity: steps with stock>=1, sold or not, by price bucket
            hi=[0,0]; lo=[0,0]
            for t in range(1,len(st)):
                stock=shed[t-1].get(p,0)
                if stock<1: continue
                sold=shed[t].get(p,0)<stock
                pb=prices[t-1].get(p,0)/BASE[p]
                b=hi if pb>=1.0 else (lo if pb<0.6 else None)
                if b is not None: b[0]+=1; b[1]+=sold
            struct[p]['p_sell_hi']=(hi[1]/hi[0] if hi[0] else None,hi[0]); struct[p]['p_sell_lo']=(lo[1]/lo[0] if lo[0] else None,lo[0])
        rec['struct']=struct
        # herd vs shops
        f12=farms[min(288,len(st)-1)]; shops9=st[min(216,len(st)-1)][0]['observation']['town']['unlocked_shops']
        herd=collections.Counter()
        for row in f12['tiles']:
            for tile in row:
                if isinstance(tile,dict) and 'animal' in tile: herd[tile['animal']]+=1
        rec['herd12']=dict(herd); rec['shops9']=dict(yarn=shops9.count('YARN_STORE'),milk=sum(shops9.count(x) for x in MILK_SHOPS),egg=sum(shops9.count(x) for x in EGG_SHOPS),straw=sum(shops9.count(x) for x in ('BRUNCH_SPOT','ICE_CREAM_SHOP','SMOOTHIE_SHOP','FARMERS_MARKET')))
        rec['shops_all']=st[-1][0]['observation']['town']['unlocked_shops']
        # land timing
        land=[]; q=1
        for t in range(1,len(st)):
            nq=len(farms[t]['unlocked_quadrants'])
            if nq>q: land.append(dict(day=t//24,hour=t%24,money_before=farms[t-1]['money'])); q=nq
        rec['land']=land
        # labour action hashes per step (farmer+hands), for cross-game agreement
        hs=[]
        for t in range(1,len(st)):
            a=st[t][s]['action'] or {}
            hs.append(hashlib.md5(json.dumps([a.get('farmer'),a.get('hands')],sort_keys=True).encode()).hexdigest()[:8])
        rec['labour_hash']=hs
        rec['first_shop']=shops9[0] if shops9 else None
        out.append(rec)
    return out
with open(sys.argv[1],'a') as f:
    for p in sys.argv[3:]:
        try:
            for r in probe(p): f.write(json.dumps(r)+'\n')
        except Exception as e: f.write(json.dumps(dict(ep=os.path.basename(p),error=repr(e)))+'\n')
        f.flush()
