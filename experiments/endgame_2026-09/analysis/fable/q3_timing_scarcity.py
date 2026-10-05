"""Fable session, 23 Sep 2026. Measures behind FABLE_IDEAS.md:
- phase revenue medians from exact_trades_78games.jsonl (top6 vs all others)
- premium sell hour histogram from sells.csv (old top5 corpus)
- max/above-base price frequency per product from daily.csv
Run from analysis/: python3 fable/q3_timing_scarcity.py"""
import csv, json, collections, statistics as st
TOP6 = {"Boey","M & M & P & Q","DSM","Unknown Mother-Goose","DECEM","吃白饭的大肥鱼"}
agg = collections.defaultdict(lambda: collections.defaultdict(list))
for line in open('exact_trades_78games.jsonl'):
    r = json.loads(line)
    side = 'top6' if r['name'] in TOP6 else 'other'
    for k,v in r['phase'].items(): agg[side][k].append(v)
for side in ('top6','other'):
    print(side, {k: int(st.median(v)) for k,v in agg[side].items()}, 'n=',len(agg[side]['sell_d00']))
rows = [r for r in csv.DictReader(open('sells.csv')) if r['product'] in ('WOOL','MILK','STRAWBERRY')]
hours = collections.Counter(int(r['turn'])%24 for r in rows)
tick = sum(v for h,v in hours.items() if h%4==0); tot = sum(hours.values())
print(f"premium sells on shop-tick hours (h%4==0): {tick/tot*100:.0f}% (uniform=25%)")
print('hour histogram:', dict(sorted(hours.items())))
drows = list(csv.DictReader(open('daily.csv')))
for p,base in [('CARROT',35),('EGG',50),('TOMATO',60),('WHEAT',25),('WOOL',200),('MILK',160),('STRAWBERRY',120),('MELON',250),('FERTILIZER',100)]:
    vals = [int(float(r['price_'+p])) for r in drows if r.get('price_'+p)]
    print(f"{p:11s} base {base:3d} max {sorted(vals)[-1]:4d}  %days>base {sum(1 for v in vals if v>base)/len(vals)*100:4.0f}%")
