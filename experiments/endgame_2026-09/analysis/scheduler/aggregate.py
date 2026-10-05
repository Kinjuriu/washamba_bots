"""Aggregate per-game feature summaries (from run_extract.py) into per-team stats:
medians + IQR ACROSS GAMES for every scalar/per-phase measure, plus a few pooled
(event-level) distributions for hour-of-day and combo frequencies where a per-game
median would throw away most of the signal (noted explicitly where used).
"""
import sys, os, json, glob, statistics, collections

ROOT = '/Users/stephanengugi/KagricultureLocalData'
FEAT_DIR = os.path.join(ROOT, 'analysis/scheduler/features')
PHASES = ["d0_7", "d8_14", "d15_22", "d23_29"]

FAMILY = {
    "DECEM": "DSM", "M & M & P & Q": "DSM", "Unknown Mother-Goose": "DSM", "Azat Akhtyamov": "DSM",
    "Boey": "Boey",
    "Majkel1337": "other", "Vadim Vasilenko": "other", "Fourth Quadrant": "other",
    "Just A game on your lips": "other", "Anton Tikhonov": "other", "KawattaTaido": "other",
    "有辣条有权": "other", "W3": "W3",
}


def med_iqr(vals):
    vals = sorted(v for v in vals if v is not None)
    n = len(vals)
    if n == 0:
        return None
    med = statistics.median(vals)
    q1 = vals[n // 4]
    q3 = vals[min(n - 1, (3 * n) // 4)]
    return dict(median=round(med, 3) if isinstance(med, float) else med, q1=round(q1, 3) if isinstance(q1, float) else q1,
                q3=round(q3, 3) if isinstance(q3, float) else q3, n=n)


def by_phase_agg(games, key):
    out = {}
    for ph in PHASES:
        vals = [g[key].get(ph) for g in games if g.get(key)]
        out[ph] = med_iqr(vals)
    return out


def pooled_hour_stats(games, key):
    hours = []
    for g in games:
        hours.extend(g.get(key) or [])
    if not hours:
        return None
    c = collections.Counter(hours)
    n = len(hours)
    return dict(n=n, median=statistics.median(hours),
                frac_hour0=round(c.get(0, 0) / n, 3),
                frac_by6=round(sum(c[h] for h in range(0, 7) if h in c) / n, 3),
                top_hours=c.most_common(5))


def load_games(path):
    games = []
    for line in open(path):
        g = json.loads(line)
        if 'error' not in g:
            games.append(g)
    return games


def team_summary(team, games):
    n = len(games)
    summary = dict(team=team, family=FAMILY.get(team, 'other'), n_games=n)
    summary['crew_by_phase'] = by_phase_agg(games, 'crew_by_phase')
    summary['hires_per_day_by_phase'] = by_phase_agg(games, 'hires_per_day_by_phase')
    summary['ratio_hands_animals_by_phase'] = by_phase_agg(games, 'ratio_hands_animals_by_phase')
    summary['ratio_hands_planted_by_phase'] = by_phase_agg(games, 'ratio_hands_planted_by_phase')
    summary['hire_hour_pooled'] = pooled_hour_stats(games, 'hire_hours')
    summary['feed_hour_pooled'] = pooled_hour_stats(games, 'feed_hours')
    summary['care_hour_pooled'] = pooled_hour_stats(games, 'care_hours')
    summary['water_hour_pooled'] = pooled_hour_stats(games, 'water_hours')

    land0 = [g['land_days'][0] for g in games if g.get('land_days')]
    land1 = [g['land_days'][1] for g in games if g.get('land_days') and len(g['land_days']) > 1]
    land2 = [g['land_days'][2] for g in games if g.get('land_days') and len(g['land_days']) > 2]
    summary['land_day_1st'] = med_iqr(land0)
    summary['land_day_2nd'] = med_iqr(land1)
    summary['land_day_3rd'] = med_iqr(land2)

    summary['zone_jaccard'] = med_iqr([g.get('zone_jaccard_mean') for g in games])
    summary['zone_size'] = med_iqr([g.get('zone_size_mean') for g in games])
    summary['specialization'] = med_iqr([g.get('specialization_mean') for g in games])
    summary['visit_actions_median'] = med_iqr([g.get('visit_actions_median') for g in games])

    combo_pool = collections.Counter()
    for g in games:
        for k, v in (g.get('visit_combos') or {}).items():
            combo_pool[k] += v
    summary['visit_combos_top'] = combo_pool.most_common(6)

    summary['moves_per_useful_by_phase'] = by_phase_agg(games, 'moves_per_useful_by_phase')
    summary['idle_share_by_phase'] = by_phase_agg(games, 'idle_share_by_phase')

    summary['escapes'] = med_iqr([g.get('escapes') for g in games])
    summary['weed_events'] = med_iqr([g.get('weed_events') for g in games])

    cu = []
    for g in games:
        cu.extend(g.get('consec_unfed_at_daystart') or [])
    if cu:
        c = collections.Counter(cu)
        summary['consec_unfed_daystart'] = dict(n=len(cu), frac0=round(c.get(0, 0) / len(cu), 3),
                                                 frac1=round(c.get(1, 0) / len(cu), 3),
                                                 frac_ge2=round(sum(v for k, v in c.items() if k >= 2) / len(cu), 3))
    else:
        summary['consec_unfed_daystart'] = None

    lag_per_game_median = [statistics.median(g['replant_lags']) for g in games if g.get('replant_lags')]
    summary['replant_lag'] = med_iqr(lag_per_game_median)
    sh = [(g['replant_same_hand_same_visit'][0] / g['replant_same_hand_same_visit'][1])
          for g in games if g.get('replant_same_hand_same_visit') and g['replant_same_hand_same_visit'][1] > 0]
    summary['replant_same_hand_share'] = med_iqr(sh)

    plantings_by_crop = {}
    crops = set()
    for g in games:
        crops.update((g.get('plantings_per_day_by_phase') or {}).keys())
    for crop in crops:
        plantings_by_crop[crop] = {ph: med_iqr([g['plantings_per_day_by_phase'][crop].get(ph)
                                                 for g in games if g.get('plantings_per_day_by_phase', {}).get(crop)])
                                    for ph in PHASES}
    summary['plantings_per_day_by_phase'] = plantings_by_crop

    pk = [(g['pickup_repeated_days'] / (g['pickup_repeated_days'] + g['pickup_single_days']))
          for g in games if (g.get('pickup_repeated_days', 0) + g.get('pickup_single_days', 0)) > 0]
    summary['pickup_repeat_share'] = med_iqr(pk)

    pattern_pool = collections.Counter()
    for g in games:
        for p in (g.get('order_patterns') or []):
            if len(p) >= 2:  # single-action "patterns" aren't informative
                pattern_pool[tuple(p)] += 1
    summary['order_patterns_top'] = [(list(k), v) for k, v in pattern_pool.most_common(8)]

    return summary


def main():
    out = []
    for path in sorted(glob.glob(os.path.join(FEAT_DIR, '*.jsonl'))):
        games = load_games(path)
        if not games:
            continue
        team = games[0]['team']
        out.append(team_summary(team, games))
    json.dump(out, open(os.path.join(ROOT, 'analysis/scheduler/team_summaries.json'), 'w'), indent=2, default=str)
    for s in out:
        print(s['team'], s['family'], 'n=', s['n_games'])
    print("DONE aggregate.py")


if __name__ == '__main__':
    main()
