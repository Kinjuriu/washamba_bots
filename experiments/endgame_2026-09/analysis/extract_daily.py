"""Extract per-day and per-sell tables from the top-five replay corpus.
Target seat = the top-five player in each manifest row. Landed sells are ESTIMATES:
units = min(requested, shed + worker inventories at the start of the turn); price = quoted price at that turn."""
import gzip, json, csv, os, sys, collections
BASE = os.path.expanduser('~/mnt/KagricultureLocalData/episodes')
OUT = os.path.expanduser('~/mnt/KagricultureLocalData/analysis')
PRODUCTS = ['WHEAT','CARROT','TOMATO','STRAWBERRY','MELON','EGG','MILK','WOOL','FERTILIZER']
rows = list(csv.DictReader(open(f'{BASE}/manifest.csv')))
daily_f = open(f'{OUT}/daily.csv','w',newline=''); sells_f = open(f'{OUT}/sells.csv','w',newline='')
dw = sells_w = None
cache = {}
def farm_counts(farm):
    crops = collections.Counter(); animals = collections.Counter(); ready = collections.Counter()
    for row in farm['tiles']:
        for t in row:
            if not isinstance(t, dict): continue
            if t.get('kind') == 'PLANT' and t.get('crop'):
                crops[t['crop']] += 1; ready[t['crop']] += t.get('yield_units', 0) or 0
            elif t.get('animal'):
                animals[t['animal']] += 1
                prod = {'COW':'MILK','SHEEP':'WOOL','GOOSE':'EGG'}[t['animal']]
                ready[prod] += t.get('yield_units', 0) or 0
    return crops, animals, ready
for i, r in enumerate(rows):
    ep = r['episode_id']; s = int(r['player_seat']); o = 1 - s
    path = f'{BASE}/replays/{ep}.json.gz'
    if not os.path.exists(path): continue
    d = json.load(gzip.open(path)); st = d['steps']
    traj = f'{ep}:{s}'
    day_sell = collections.defaultdict(lambda: collections.Counter()); opp_day_sell = collections.defaultdict(lambda: collections.Counter())
    day_orders = collections.defaultdict(lambda: collections.Counter())
    for t in range(720):
        ob = st[t][s]['observation']; act = st[t][s].get('action') or {}
        oact = st[t][o].get('action') or {}
        day = t // 24
        shed = ob['private']['shed']; inv = collections.Counter()
        for w in ob['private'].get('inventories', []):
            for k, v in w.items(): inv[k] += v
        prices = ob['market']['prices']
        for od in (act.get('market') or []):
            if not od: continue
            typ = od[0]; day_orders[day][typ] += 1
            if typ == 'BUY_SEED' and len(od) > 1: day_orders[day]['SEED_'+od[1]] += od[2] if len(od) > 2 else 1
            if typ == 'BUY_ANIMAL' and len(od) > 1: day_orders[day]['ANIMAL_'+od[1]] += od[2] if len(od) > 2 else 1
            if typ == 'SELL' and len(od) > 1 and od[1] in PRODUCTS:
                q = od[2] if len(od) > 2 else 1
                est = min(q, shed.get(od[1], 0) + inv.get(od[1], 0))
                day_sell[day][od[1]] += est
                if est > 0:
                    rec = dict(traj=traj, player=r['player'], won=r['won'], turn=t, day=day, product=od[1], requested=q, est_units=est, price=prices.get(od[1]), shops='|'.join(ob['town']['unlocked_shops']))
                    if sells_w is None: sells_w = csv.DictWriter(sells_f, fieldnames=list(rec)); sells_w.writeheader()
                    sells_w.writerow(rec)
        for od in (oact.get('market') or []):
            if od and od[0] == 'SELL' and len(od) > 1 and od[1] in PRODUCTS:
                opp_day_sell[day][od[1]] += od[2] if len(od) > 2 else 1   # opponent: requested only
        if t % 24 == 23 or t == 719:
            me = ob['farms'][s]; op = ob['farms'][o]
            c, a, rd = farm_counts(me); oc, oa, ord_ = farm_counts(op)
            rec = dict(traj=traj, player=r['player'], won=r['won'], seat=s, day=day, money=me['money'], opp_money=op['money'],
                       hands=me.get('hires_today'), opp_hands=op.get('hires_today'), quads=len(me['unlocked_quadrants']), opp_quads=len(op['unlocked_quadrants']),
                       shops='|'.join(ob['town']['unlocked_shops']), shed_total=sum(v for k, v in shed.items()))
            for p in ['WHEAT','CARROT','TOMATO','STRAWBERRY','MELON']: rec['crop_'+p] = c[p]; rec['oppcrop_'+p] = oc[p]
            for an in ['COW','SHEEP','GOOSE']: rec['ani_'+an] = a[an]; rec['oppani_'+an] = oa[an]
            for p in PRODUCTS: rec['sold_'+p] = day_sell[day][p]; rec['oppreq_'+p] = opp_day_sell[day][p]; rec['price_'+p] = prices.get(p); rec['shed_'+p] = shed.get(p, 0)
            for k in ['HIRE','BUY_LAND','BUY_PRODUCT','SEED_WHEAT','SEED_CARROT','SEED_TOMATO','SEED_STRAWBERRY','SEED_MELON','ANIMAL_COW','ANIMAL_SHEEP','ANIMAL_GOOSE']: rec['ord_'+k] = day_orders[day][k]
            if dw is None: dw = csv.DictWriter(daily_f, fieldnames=list(rec)); dw.writeheader()
            dw.writerow(rec)
    if i % 20 == 0: print(i, traj, flush=True)
daily_f.close(); sells_f.close(); print('done')
