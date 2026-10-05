"""Phase A, steps 2-3: resolve the live top-12 leaderboard, pull each team's active
submissions, list their completed public episodes, and build a stratified 30-per-team
manifest. Read-only. Writes manifest.csv BEFORE any replay download happens.
"""
import sys, os, csv, json, time, random
from collections import defaultdict
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fetch_lib import client, list_submission_episodes, list_team_public_submissions
from kagglesdk.competitions.types.competition_api_service import ApiGetLeaderboardRequest

ROOT = '/Users/stephanengugi/KagricultureLocalData'
TS = time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())
OUT = os.path.join(ROOT, 'episodes', f'{TS}_top12_strat')
os.makedirs(OUT, exist_ok=True)
random.seed(20260927)  # reproducible stratified sampling for this run

c = client()

# ---------- 1. Full live leaderboard (paginated) ----------
print("Paging live leaderboard for kaggriculture...", flush=True)
snapshot_time = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
rows = []
page_token = None
while True:
    req = ApiGetLeaderboardRequest()
    req.competition_name = 'kaggriculture'
    req.page_size = 200
    if page_token:
        req.page_token = page_token
    resp = c.competitions.competition_api_client.get_leaderboard(req)
    for s in resp.submissions:
        rows.append(dict(team_id=s.team_id, team_name=s.team_name, score=float(s.score),
                          submission_date=str(s.submission_date)))
    page_token = resp.next_page_token
    if not page_token:
        break
    time.sleep(0.2)
print(f"  {len(rows)} teams on leaderboard, snapshot {snapshot_time}", flush=True)

# assign rank by return order (API returns descending by score)
for i, r in enumerate(rows):
    r['rank'] = i + 1
rating_by_team = {r['team_id']: r['score'] for r in rows}

leaderboard_csv = os.path.join(OUT, 'leaderboard_full_snapshot.csv')
with open(leaderboard_csv, 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=['rank', 'team_id', 'team_name', 'score', 'submission_date'])
    w.writeheader()
    for r in rows:
        w.writerow(r)
print(f"  wrote {leaderboard_csv}", flush=True)

top12 = rows[:12]
json.dump(dict(snapshot_time_utc=snapshot_time, top12=top12),
          open(os.path.join(OUT, 'leaderboard_snapshot.json'), 'w'), indent=2)

def band(score):
    if score is None:
        return 'unknown'
    if score < 2500:
        return '<2500'
    if score < 2800:
        return '2500-2800'
    return '>2800'

def window_key(end_time_str):
    # end_time like '2026-09-24 19:31:02.123000' -> floor to 6h UTC bucket
    dt = datetime.fromisoformat(end_time_str.replace('Z', ''))
    bucket_hour = (dt.hour // 6) * 6
    return dt.strftime('%Y-%m-%d') + f'T{bucket_hour:02d}'

# ---------- 2. Per-team: active submissions, episode pools ----------
team_meta = []
all_manifest_rows = []

for t in top12:
    tid, tname, trank = t['team_id'], t['team_name'], t['rank']
    print(f"Rank {trank} {tname} (team {tid})...", flush=True)
    subs = list_team_public_submissions(c, tid)
    for s in subs:
        try:
            s['public_score'] = float(s['public_score'])
        except (TypeError, ValueError):
            s['public_score'] = None
    subs_sorted = sorted(subs, key=lambda s: (s['public_score'] is None, -(s['public_score'] or 0)))

    # completed non-validation episode counts per active submission
    sub_info = []
    for s in subs_sorted:
        eps = list_submission_episodes(c, s['id'])
        completed = [e for e in eps if e['type'] != 'EPISODE_TYPE_VALIDATION' and e['state'] == 'COMPLETED']
        sub_info.append(dict(submission_id=s['id'], date_submitted=s['date_submitted'],
                              public_score=s['public_score'], total_episodes=len(eps),
                              completed_episodes=completed))
        time.sleep(0.1)

    # choose primary: highest-rated submission, unless it has <30 completed episodes and
    # another active submission has >=30
    primary = sub_info[0]
    for cand in sub_info[1:]:
        if primary['completed_episodes'].__len__() < 30 and len(cand['completed_episodes']) >= 30:
            primary = cand
            break

    completed = primary['completed_episodes']
    sid = primary['submission_id']

    candidates = []
    for e in completed:
        me = next((a for a in e['agents'] if a['submission_id'] == sid), None)
        opp = next((a for a in e['agents'] if a['submission_id'] != sid), None)
        if me is None or opp is None:
            continue
        opp_rating = rating_by_team.get(opp['team_id'])
        candidates.append(dict(
            episode_id=e['episode_id'], end_time=e['end_time'], state=e['state'], type=e['type'],
            seat=me['index'], my_bank=me['reward'],
            opp_name=opp['team_name'], opp_team=opp['team_id'], opp_submission=opp['submission_id'],
            opp_seat=opp['index'], opp_bank=opp['reward'],
            won=(1 if (me['reward'] is not None and opp['reward'] is not None and me['reward'] > opp['reward'])
                 else (0.5 if me['reward'] == opp['reward'] else 0)),
            opp_rating=opp_rating, band=band(opp_rating), window=window_key(e['end_time']),
        ))

    # ---------- stratified sample of 30: seat x band cells, 5 each, neighbour fill ----------
    bands_order = ['<2500', '2500-2800', '>2800']
    neighbours = {'<2500': ['2500-2800', '>2800'], '2500-2800': ['<2500', '>2800'],
                  '>2800': ['2500-2800', '<2500']}
    cells = {(seat, b): [c for c in candidates if c['seat'] == seat and c['band'] == b]
             for seat in (0, 1) for b in bands_order}
    unknowns = {seat: [c for c in candidates if c['seat'] == seat and c['band'] == 'unknown']
                for seat in (0, 1)}

    quota = {(seat, b): 5 for seat in (0, 1) for b in bands_order}
    pools = {k: list(v) for k, v in cells.items()}

    # top up short cells from neighbouring bands (same seat), then from unknown-rating pool (same seat)
    for seat in (0, 1):
        for b in bands_order:
            need = quota[(seat, b)] - len(pools[(seat, b)])
            if need <= 0:
                continue
            for nb in neighbours[b]:
                if need <= 0:
                    break
                avail = [c for c in cells[(seat, nb)] if c not in pools[(seat, b)]]
                # only borrow surplus beyond that neighbour's own quota
                surplus = avail[quota[(seat, nb)]:] if len(avail) > quota[(seat, nb)] else []
                take = surplus[:need]
                pools[(seat, b)].extend(take)
                need -= len(take)
            if need > 0 and unknowns[seat]:
                take = unknowns[seat][:need]
                pools[(seat, b)].extend(take)
                unknowns[seat] = unknowns[seat][len(take):]
                need -= len(take)
            # last resort: relax seat balance, borrow from the same band, opposite seat
            if need > 0:
                other = 1 - seat
                avail = [c for c in cells[(other, b)] if c not in pools[(seat, b)] and c not in pools[(other, b)]]
                surplus = avail[quota[(other, b)]:] if len(avail) > quota[(other, b)] else avail
                take = surplus[:need]
                pools[(seat, b)].extend(take)
                need -= len(take)

    # final pick per cell honouring the 10-per-6h-window cap, spread not recency
    window_counts = defaultdict(int)
    selected = []
    for key in [(seat, b) for seat in (0, 1) for b in bands_order]:
        pool = pools[key]
        random.shuffle(pool)
        target = quota[key]
        picked_here = []
        remaining = list(pool)
        while len(picked_here) < target and remaining:
            eligible = [c for c in remaining if window_counts[c['window']] < 10]
            source = eligible if eligible else remaining  # relax cap only if no alternative at all
            source.sort(key=lambda c: window_counts[c['window']])
            best_w = source[0]['window']
            tied = [c for c in source if c['window'] == best_w]
            pick = random.choice(tied)
            picked_here.append(pick)
            remaining.remove(pick)
            window_counts[pick['window']] += 1
        selected.extend(picked_here)
        pools[key] = picked_here  # record what was actually used for the report

    for c_ in selected:
        c_['team_rank'] = trank
        c_['team_name'] = tname
        c_['team_id'] = tid
        c_['player_submission'] = sid
        c_['stratum'] = f"seat{c_['seat']}_{c_['band']}"
    all_manifest_rows.extend(selected)

    team_meta.append(dict(
        rank=trank, name=tname, team_id=tid, rating=t['score'],
        primary_submission=sid, primary_public_score=primary['public_score'],
        all_active_submissions=[dict(id=s['submission_id'], date_submitted=s['date_submitted'],
                                      public_score=s['public_score'],
                                      completed_episodes=len(s['completed_episodes'])) for s in sub_info],
        completed_episodes_available=len(completed),
        episodes_sampled=len(selected),
        cell_counts={f"seat{seat}_{b}": len(pools[(seat, b)]) for seat in (0, 1) for b in bands_order},
    ))
    print(f"  sampled {len(selected)}/30 from {len(completed)} completed episodes "
          f"(submission {sid}, rating {primary['public_score']})", flush=True)

# ---------- 3. Write manifest.csv BEFORE downloading ----------
cols = ['team_rank', 'team_name', 'team_id', 'player_submission', 'episode_id', 'end_time', 'state',
        'type', 'seat', 'my_bank', 'opp_name', 'opp_team', 'opp_submission', 'opp_seat', 'opp_bank',
        'won', 'opp_rating', 'band', 'window', 'stratum']
manifest_path = os.path.join(OUT, 'manifest.csv')
with open(manifest_path, 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=cols)
    w.writeheader()
    for row in all_manifest_rows:
        w.writerow({k: row.get(k) for k in cols})
print(f"Wrote manifest: {manifest_path} ({len(all_manifest_rows)} rows)", flush=True)

json.dump(team_meta, open(os.path.join(OUT, 'team_meta.json'), 'w'), indent=2)
print(f"OUT={OUT}")
print("DONE resolve_top12.py")
