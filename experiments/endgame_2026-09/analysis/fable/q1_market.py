import csv, json, collections, statistics as st

TOP6 = {"Boey","M & M & P & Q","DSM","Unknown Mother-Goose","DECEM","吃白饭的大肥鱼"}

# 1) exact trades: per-unit avg price by item, top6 vs others (78 fresh games)
agg = collections.defaultdict(lambda: collections.defaultdict(lambda: [0,0]))  # side -> item -> [units, rev]
for line in open('exact_trades_78games.jsonl'):
    r = json.loads(line)
    side = 'top6' if r['name'] in TOP6 else 'other'
    for item,(u,rev,bu,bc) in r['items'].items():
        agg[side][item][0]+=u; agg[side][item][1]+=rev
print("=== exact_trades: avg sale price per unit (units) ===")
for item in ["WOOL","MILK","STRAWBERRY","MELON","EGG","TOMATO","CARROT","WHEAT","FERTILIZER"]:
    row=[]
    for side in ('top6','other'):
        u,rev = agg[side][item]
        row.append(f"{side}: {rev/u if u else 0:.0f} ({u}u)")
    print(f"{item:11s} " + " | ".join(row))

# 2) sells.csv (old top5 corpus): premium slice sizes & prices
rows = list(csv.DictReader(open('sells.csv')))
for prod, base in [("WOOL",200),("MILK",160),("STRAWBERRY",120)]:
    pr = [r for r in rows if r['product']==prod]
    sizes = collections.Counter(int(r['requested']) for r in pr)
    prices = [int(r['price']) for r in pr]
    above = sum(1 for p in prices if p>=base)
    print(f"\n=== {prod} sells (top5 corpus, n={len(pr)}) ===")
    print("slice sizes:", sizes.most_common(6))
    print(f"price: median {st.median(prices):.0f}, mean {st.mean(prices):.0f}, >=base({base}): {above/len(prices)*100:.0f}%")
    # by day decile
    byday = collections.defaultdict(list)
    for r in pr: byday[int(r['day'])//5].append(int(r['price']))
    print("median price by 5-day bucket:", {f"d{k*5}-{k*5+4}": int(st.median(v)) for k,v in sorted(byday.items())})
