import gzip, json

def first_day_opponent_leads_by(path, my_seat, threshold=3000):
    """Read the ORIGINAL downloaded replay (not a re-sim) and find the first day
    (obs['day']) at which the opponent's money - my money > threshold, checked once
    per day using that day's last available step. Returns (day, margin) or (None, None)."""
    d = json.load(gzip.open(path))
    st = d['steps']
    opp_seat = 1 - my_seat
    best = None
    last_by_day = {}
    for s in st:
        obs = s[my_seat]['observation'] if s[my_seat].get('observation') else None
        if obs is None:
            continue
        day = obs.get('day')
        farms = obs.get('farms')
        if day is None or farms is None:
            continue
        my_money = farms[my_seat].get('money')
        opp_money = farms[opp_seat].get('money')
        if my_money is None or opp_money is None:
            continue
        last_by_day[day] = opp_money - my_money
    for day in sorted(last_by_day):
        margin = last_by_day[day]
        if margin > threshold:
            return day, margin
    return None, None
