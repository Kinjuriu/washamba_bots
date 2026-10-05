import csv, collections, statistics as st
TOP6 = {"Boey","M & M & P & Q","DSM","Unknown Mother-Goose","DECEM","吃白饭的大肥鱼"}
rows = list(csv.DictReader(open('pairs.csv')))
def side(r):
    n = r['name'].replace('OPP:','')
    return 'top6' if n in TOP6 else 'other'
groups = collections.defaultdict(list)
for r in rows: groups[side(r)].append(r)
print({k: len(v) for k,v in groups.items()})
def med(g, col):
    vals = [float(r[col]) for r in g if r[col] not in ('','None')]
    return st.median(vals) if vals else None
cols = ['first_WOOL','first_STRAWBERRY','first_MILK','first_EGG','first_MELON',
        'GOOSE_d12','COW_d12','SHEEP_d12','crop_TOMATO_d12','crop_CARROT_d12','crop_WHEAT_d12','crop_STRAWBERRY_d12','crop_MELON_d12',
        'hands_d12','sell_req','sell_req_d0_2','rev_prem','rev_total',
        'units_WOOL','rev_WOOL','units_EGG','units_TOMATO','units_CARROT']
print(f"{'col':24s} top6    other")
for c in cols:
    print(f"{c:24s} {med(groups['top6'],c)!s:7s} {med(groups['other'],c)!s}")
# avg wool price per side
for k,g in groups.items():
    u = sum(float(r['units_WOOL']) for r in g); rev = sum(float(r['rev_WOOL']) for r in g)
    ue = sum(float(r['units_EGG']) for r in g); reve = sum(float(r['rev_EGG']) for r in g)
    print(k, 'wool avg', round(rev/u,1), 'egg avg', round(reve/ue,1))
