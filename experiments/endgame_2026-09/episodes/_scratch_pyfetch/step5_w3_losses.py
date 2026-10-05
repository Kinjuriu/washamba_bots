import sys, os, csv, json, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from resim_runner import run_resim
from day_margin import first_day_opponent_leads_by

ROOT = '/Users/stephanengugi/KagricultureLocalData'
OUT = sys.argv[1]  # washamba_0924b dir name
manifest = os.path.join(ROOT, OUT, 'manifest_classified.csv')
replays_dir = os.path.join(ROOT, OUT, 'replays')

rows = list(csv.DictReader(open(manifest)))
w3_losses = []
for r in rows:
    if 'W3' not in r['display']:
        continue
    if r['won'] != '0':
        continue
    try:
        rating = float(r['opponent_rating_snapshot']) if r['opponent_rating_snapshot'] else None
    except Exception:
        rating = None
    if rating is None or rating <= 2500:
        continue
    w3_losses.append(r)

print(f"W3 losses vs opponent rated >2500: {len(w3_losses)}")
for r in w3_losses:
    print(" ", r['episode_id'], r['opponent_name'], r['opponent_rating_snapshot'], r['player_bank'], r['opponent_bank'])

paths = []
meta = {}
for r in w3_losses:
    eid = r['episode_id']
    p = os.path.join(replays_dir, f'{eid}.json.gz')
    if os.path.exists(p):
        paths.append(p)
        meta[eid] = r

resim_out = run_resim(paths)
json.dump(resim_out, open(os.path.join(ROOT, OUT, 'w3_loss_resim.json'), 'w'), indent=2)

# aggregate revenue deltas by product across these losses (our seat only)
product_delta = collections.defaultdict(float)
product_us = collections.defaultdict(float)
product_opp = collections.defaultdict(float)
per_game = []
for rec in resim_out:
    if 'error' in rec:
        continue
    eid = rec['ep']
    m = meta.get(eid)
    if m is None:
        continue
    my_seat = int(m['player_seat'])
    if rec['seat'] != my_seat:
        continue  # only take our own seat's record (has full items dict for both us & counted opp buys, but we need opponent's SELL too -> other rec)
    per_game.append(rec)

# also grab the paired opponent-seat record to compute opponent revenue per product
by_ep_seat = {(rec['ep'], rec['seat']): rec for rec in resim_out if 'error' not in rec}
day_leads = {}
for r in w3_losses:
    eid = r['episode_id']
    my_seat = int(r['player_seat'])
    p = os.path.join(replays_dir, f'{eid}.json.gz')
    if not os.path.exists(p):
        continue
    day, margin = first_day_opponent_leads_by(p, my_seat, 3000)
    day_leads[eid] = dict(day=day, margin=margin, opponent=r['opponent_name'], opponent_rating=r['opponent_rating_snapshot'])

for r in w3_losses:
    eid = r['episode_id']
    my_seat = int(r['player_seat'])
    opp_seat = 1 - my_seat
    me = by_ep_seat.get((eid, my_seat))
    opp = by_ep_seat.get((eid, opp_seat))
    if not me or not opp:
        continue
    for item, (sc, srev, bc, bspend) in me['items'].items():
        product_us[item] += srev
    for item, (sc, srev, bc, bspend) in opp['items'].items():
        product_opp[item] += srev

for item in set(list(product_us.keys()) + list(product_opp.keys())):
    product_delta[item] = product_us.get(item, 0) - product_opp.get(item, 0)

ranked = sorted(product_delta.items(), key=lambda kv: kv[1])
print("Product revenue delta (W3 - opponent), most negative first, across these losses:")
for item, delta in ranked:
    print(f"  {item:12s} delta={delta:+.0f}  W3={product_us.get(item,0):.0f}  opp={product_opp.get(item,0):.0f}")

out = dict(
    n_losses=len(w3_losses),
    losses=[dict(episode_id=r['episode_id'], opponent=r['opponent_name'],
                 opponent_rating=r['opponent_rating_snapshot'],
                 our_bank=r['player_bank'], opp_bank=r['opponent_bank'],
                 day_opp_led_by_3000=day_leads.get(r['episode_id'])) for r in w3_losses],
    product_revenue_us=dict(product_us),
    product_revenue_opp=dict(product_opp),
    product_delta_ranked=ranked,
)
json.dump(out, open(os.path.join(ROOT, OUT, 'w3_loss_analysis.json'), 'w'), indent=2, default=str)
print("wrote w3_loss_analysis.json")
