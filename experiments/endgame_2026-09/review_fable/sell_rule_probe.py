"""Per premium sale event of the analysed seat: units, stock before, price before/after, hour, inter-event gap. Usage: sell_rule_probe.py out.jsonl SIDE files..."""
import gzip,json,sys,os
TOP=["Boey","M & M & P & Q","DSM","Unknown Mother-Goose","DECEM","吃白饭的大肥鱼"]
PREM=("WOOL","MILK","STRAWBERRY"); BASE={"STRAWBERRY":120,"MILK":160,"WOOL":200}
side=sys.argv[2]
with open(sys.argv[1],'a') as f:
    for path in sys.argv[3:]:
        d=json.load(gzip.open(path)); st=d['steps']; names=d['info']['TeamNames']
        for s in (0,1):
            if not ((side=="TOP" and names[s] in TOP) or names[s]==side): continue
            shed=[st[t][s]['observation']['private']['shed'] for t in range(len(st))]
            prices=[st[t][0]['observation']['market']['prices'] for t in range(len(st))]
            for p in PREM:
                last=None
                for t in range(1,len(st)):
                    n=shed[t-1].get(p,0)-shed[t].get(p,0)
                    if n>0:
                        f.write(json.dumps(dict(name=names[s],p=p,t=t,n=n,stock=shed[t-1].get(p,0),pb=prices[t-1][p]/BASE[p],pa=prices[t][p]/BASE[p],gap=(t-last) if last else None,day=t//24))+'\n')
                        last=t
