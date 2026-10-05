"""Opening fingerprints + early money for both seats of each replay (review_fable).
Usage: python fingerprints.py out.jsonl files..."""
import gzip,json,sys,os
def fp(path):
    d=json.load(gzip.open(path)); st=d['steps']; out=[]
    for s in (0,1):
        a1=(st[1][s]['action'] or {}).get('market',[]); a2=(st[2][s]['action'] or {}).get('market',[])
        money=[st[t][0]['observation']['farms'][s]['money'] for t in (1,2,3)]
        # loose families
        r2=[tuple(o) for o in a2 if isinstance(o,list)]
        fam='other'
        if ('BUY_ANIMAL','COW',2) in r2 and ('BUY_ANIMAL','SHEEP',2) in r2: fam='tape'
        if a1[:2]==[['BUY_ANIMAL','COW',1],['BUY_PRODUCT','WHEAT',5]]: fam='DSM'
        if a1[:1]==[['BUY_PRODUCT','WHEAT',3]] and a1[1:6]==[['HIRE']]*5: fam='Boey'
        out.append(dict(ep=os.path.basename(path).split('.')[0],seat=s,name=d['info']['TeamNames'][s],fam=fam,t1=a1,t2=a2,money123=money,bank=d['rewards'][s],opp_bank=d['rewards'][1-s]))
    return out
if __name__=='__main__':
    with open(sys.argv[1],'a') as f:
        for p in sys.argv[2:]:
            try:
                for r in fp(p): f.write(json.dumps(r)+'\n')
            except Exception as e: f.write(json.dumps(dict(ep=os.path.basename(p),error=repr(e)))+'\n')
            f.flush()
