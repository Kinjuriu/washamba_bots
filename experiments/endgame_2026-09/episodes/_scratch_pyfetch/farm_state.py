import gzip, json, collections

def snapshot_at_days(path, my_seat, days=(6, 12, 18, 26)):
    d = json.load(gzip.open(path))
    st = d['steps']
    wanted = set(days)
    out = {}
    peak_hands_by_day = collections.defaultdict(int)
    for s in st:
        obs = s[my_seat]['observation'] if s[my_seat].get('observation') else None
        if obs is None:
            continue
        day = obs.get('day')
        if day is None:
            continue
        farm = obs['farms'][my_seat]
        nhands = len(farm.get('hands', []))
        if nhands > peak_hands_by_day[day]:
            peak_hands_by_day[day] = nhands
        if day in wanted and day not in out:
            tiles = farm['tiles']
            animals = collections.Counter()
            crops = collections.Counter()
            land = 0
            for row in tiles:
                for t in row:
                    if t is None:
                        land += 1
                    elif t == 'LOCKED':
                        continue
                    elif isinstance(t, dict):
                        land += 1
                        if t.get('kind') in ('PASTURE', 'COOP'):
                            animals[t.get('animal')] += 1
                        elif t.get('kind') == 'PLANT':
                            crops[t.get('crop')] += 1
            out[day] = dict(day=day, animals=dict(animals), land_tiles=land,
                             crop_tiles=dict(crops), cash=farm.get('money'))
    # fill peak hands into each snapshot (peak seen on that exact day)
    for day in out:
        out[day]['peak_hands_that_day'] = peak_hands_by_day.get(day, None)
    return out
