"""Per-trajectory features for a corpus folder (manifest.csv + replays/). Both seats of every game.
Uses the verified convention: action at row t was chosen from observation at row t-1.
A SELL is 'feasible' if the pre-decision shed + worker inventories held >=1 unit; est_units=min(q, held);
revenue estimate = est_units * pre-decision quoted price (upper bound)."""
import gzip, json, csv, os, sys, collections
corpus = sys.argv[1]; out = sys.argv[2]
P = ['WHEAT','CARROT','TOMATO','STRAWBERRY','MELON','EGG','MILK','WOOL','FERTILIZER']
PREM = ['STRAWBERRY','MELON','MILK','WOOL','EGG','TOMATO']
rows = list(csv.DictReader(open(os.path.join(corpus,'manifest.csv'))))
names = {}
for r in rows:
    if r.get('category','competitive') != 'competitive' and r.get('type') == 'EPISODE_TYPE_VALIDATION': continue
    names[(r['episode_id'], int(r['player_seat']))] = r['player']
    names.setdefault((r['episode_id'], int(r['opponent_seat'])), 'OPP:' + r['opponent_name'])
eps = sorted({e for e, s in names})
f = open(out, 'w', newline=''); w = None
for ep in eps:
    path = os.path.join(corpus, 'replays', ep + '.json.gz')
    if not os.path.exists(path): continue
    d = json.load(gzip.open(path)); st = d['steps']; rw = d['rewards']
    for s in (0, 1):
        o = 1 - s
        rec = collections.OrderedDict(episode=ep, seat=s, name=names.get((ep, s), '?'), opp=names.get((ep, o), '?'),
                                      bank=rw[s], opp_bank=rw[o], result=('W' if rw[s] > rw[o] else 'L' if rw[s] < rw[o] else 'T'))
        c = collections.Counter(); first = {}; rev = collections.Counter(); units = collections.Counter()
        early_req = early_feas = 0; minmoney_3_7 = 1e9; herd = {}
        for t in range(1, 720):
            pre = st[t-1][s]['observation']; act = st[t][s].get('action') or {}
            shed = pre['private']['shed']; inv = collections.Counter()
            for x in pre['private'].get('inventories', []):
                for k, v in x.items(): inv[k] += v
            pr = pre['market']['prices']; day = t // 24
            if 3 <= day <= 7: minmoney_3_7 = min(minmoney_3_7, pre['farms'][s]['money'])
            for od in (act.get('market') or []):
                if not od: continue
                c['ord_' + od[0]] += 1
                if od[0] == 'SELL' and len(od) > 1:
                    q = od[2] if len(od) > 2 else 1; held = shed.get(od[1], 0) + inv.get(od[1], 0)
                    c['sell_req'] += 1
                    if day < 3: early_req += 1
                    if held > 0 and q > 0:
                        c['sell_feas'] += 1
                        if day < 3: early_feas += 1
                        e = min(q, held)
                        if od[1] in P:
                            rev[od[1]] += e * pr.get(od[1], 0); units[od[1]] += e; first.setdefault(od[1], t)
                    elif held == 0: c['sell_empty'] += 1
                    if q <= 0: c['sell_zero_qty'] += 1
            if t in (287, 431, 623):
                a = collections.Counter(); crops = collections.Counter(); land = 0
                for row in st[t][s]['observation']['farms'][s]['tiles']:
                    for tl in row:
                        if tl != 'LOCKED': land += 1
                        if isinstance(tl, dict):
                            if tl.get('animal'): a[tl['animal']] += 1
                            if tl.get('crop'): crops[tl['crop']] += 1
                for k in ('COW','SHEEP','GOOSE'): rec[f'{k}_d{t//24+1}'] = a[k]
                for k in ('STRAWBERRY','WHEAT','TOMATO','CARROT','MELON'): rec[f'crop_{k}_d{t//24+1}'] = crops[k]
                rec[f'land_d{t//24+1}'] = land; rec[f'hands_d{t//24+1}'] = st[t][s]['observation']['farms'][s].get('hires_today')
                rec[f'money_d{t//24+1}'] = st[t][s]['observation']['farms'][s]['money']
        rec['sell_req'] = c['sell_req']; rec['sell_feas'] = c['sell_feas']; rec['sell_empty'] = c['sell_empty']; rec['sell_zero_qty'] = c['sell_zero_qty']
        rec['sell_req_d0_2'] = early_req; rec['sell_feas_d0_2'] = early_feas
        for k in ('BUY_PRODUCT','BUY_SEED','BUY_ANIMAL','HIRE','BUY_LAND'): rec['ord_' + k] = c['ord_' + k]
        rec['min_money_d3_7'] = minmoney_3_7
        for p in P: rec['rev_' + p] = rev[p]; rec['units_' + p] = units[p]; rec['first_' + p] = first.get(p, -1)
        rec['rev_total'] = sum(rev.values()); rec['rev_prem'] = sum(rev[p] for p in PREM)
        if w is None:
            w = csv.DictWriter(f, fieldnames=list(rec.keys()), extrasaction='ignore', restval=''); w.writeheader()
        w.writerow(rec)
f.close(); print('done', out)
