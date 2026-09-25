"""Where does a candidate fall short of the top six, day by day? (Builder A, splice build)

Plays ONE episode (single process): the candidate vs an opponent (default: W3, seed 900),
measures the candidate seat with the same instrumented engine used to build the targets
(experiments/splice/daymetrics.py), and prints it next to the top-six median and IQR from
experiments/splice/top6_targets.json:

  1. metrics furthest outside the top-six band (IQR), with the days they are outside it;
  2. day-by-day panels: value (top-six median), marked < or > when outside the IQR;
  3. season revenue, units and average price per product for both seats vs the top six.

Usage: .venv/Scripts/python.exe experiments/splice/compare.py <candidate.py>
           [--seed 900] [--opponent agents/w3_herdsafe2700.py] [--seat 0]
           [--split all|vs_tape|vs_other|vs_top6] [--top 15]
"""
import argparse
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

import daymetrics as DM  # noqa: E402
from kaggle_environments import make  # noqa: E402

DEFAULT_OPP = os.path.join(ROOT, "agents", "w3_herdsafe2700.py")
TARGETS = os.path.join(HERE, "top6_targets.json")

PANELS = [
    ("Assets at dawn", ["money_dawn", "tiles_owned", "hires", "animals_COW", "animals_SHEEP",
                        "animals_GOOSE", "structures_empty", "tiles_planted"]),
    ("Crops at dawn (tiles)", ["planted_WHEAT", "planted_CARROT", "planted_TOMATO",
                               "planted_STRAWBERRY", "planted_MELON", "tiles_empty", "weeds"]),
    ("Daily flows", ["revenue_total", "harvest_MILK", "harvest_WOOL", "harvest_EGG", "water",
                     "fert_collect", "fert_apply", "feed_per_animal", "care_per_animal", "idle_frac"]),
]
SHORT = {"money_dawn": "money", "tiles_owned": "tiles", "animals_COW": "cow", "animals_SHEEP": "sheep",
         "animals_GOOSE": "goose", "structures_empty": "emptyS", "tiles_planted": "planted",
         "planted_WHEAT": "wheat", "planted_CARROT": "carrot", "planted_TOMATO": "tomato",
         "planted_STRAWBERRY": "strawb", "planted_MELON": "melon", "tiles_empty": "empty",
         "revenue_total": "revenue", "harvest_MILK": "h_milk", "harvest_WOOL": "h_wool",
         "harvest_EGG": "h_egg", "fert_collect": "f_coll", "fert_apply": "f_appl",
         "feed_per_animal": "feed/an", "care_per_animal": "care/an", "idle_frac": "idle"}


def fmt(v):
    if v is None:
        return "-"
    if isinstance(v, float) and abs(v) < 10 and v != int(v):
        return f"{v:.2f}"
    if abs(v) >= 10000:
        return f"{v / 1000:.0f}k"
    if abs(v) >= 1000:
        return f"{v / 1000:.1f}k"
    return f"{v:.0f}"


def distance(metric, v, p25, p50, p75):
    """How far v sits outside [p25, p75], in units of the IQR (floored per metric)."""
    if v is None or p25 is None:
        return 0.0
    s = max(p75 - p25, DM.scale_floor(metric))
    if v > p75:
        return (v - p75) / s
    if v < p25:
        return -(p25 - v) / s
    return 0.0


def play(candidate, opponent, seed, seat):
    DM.install()
    DM.REC.reset()
    agents = [candidate, opponent] if seat == 0 else [opponent, candidate]
    env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})
    t = time.time()
    env.run(agents)
    statuses = [s.status for s in env.steps[-1]]
    banks = [s.reward for s in env.steps[-1]]
    return env, statuses, banks, time.time() - t


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("candidate")
    ap.add_argument("--seed", type=int, default=900)
    ap.add_argument("--opponent", default=DEFAULT_OPP)
    ap.add_argument("--seat", type=int, default=0, choices=(0, 1))
    ap.add_argument("--split", default="all")
    ap.add_argument("--top", type=int, default=15)
    a = ap.parse_args()

    with open(TARGETS, encoding="utf-8") as f:
        targets = json.load(f)
    split = targets["splits"].get(a.split)
    if split is None:
        sys.exit(f"split {a.split!r} not in {list(targets['splits'])}")
    band = split["per_day"]
    n_games = targets["meta"]["n_games"][a.split]

    env, statuses, banks, secs = play(os.path.abspath(a.candidate), os.path.abspath(a.opponent), a.seed, a.seat)
    me, opp = a.seat, 1 - a.seat
    mine = DM.per_day(env.steps, me)
    theirs = DM.per_day(env.steps, opp)
    print(f"{os.path.basename(a.candidate)} (seat {me}) vs {os.path.basename(a.opponent)}, seed {a.seed}: "
          f"banks {banks[me]:,.0f} vs {banks[opp]:,.0f}, statuses {statuses}, {secs:.0f}s")
    season = split["season"]
    print(f"top-six band: split '{a.split}', {n_games} games; top-six bank median "
          f"{season['bank']['p50']:,.0f} [{season['bank']['p25']:,.0f}-{season['bank']['p75']:,.0f}]")

    # 1. furthest outside the band
    rows = []
    for m, series in mine.items():
        if m not in band:
            continue
        b = band[m]
        dists = []
        for d, v in enumerate(series):
            if b["n"][d] < 5 or v is None:
                continue
            z = distance(m, v, b["p25"][d], b["p50"][d], b["p75"][d])
            if z:
                dists.append((abs(z), z, d, v))
        if not dists:
            continue
        worst = max(dists)
        days_out = sorted(d for _, _, d, _ in dists)
        rows.append((worst[0], m, worst, days_out))
    rows.sort(reverse=True)
    print(f"\n1. Furthest outside the top-six IQR (worst day shown; distance in IQRs, floored)")
    print(f"   {'metric':22} {'day':>3} {'cand':>8} {'top6 p25 / p50 / p75':>24} {'dist':>6}  days outside")
    for _, m, (_, z, d, v), days_out in rows[:a.top]:
        b = band[m]
        span = f"{fmt(b['p25'][d])} / {fmt(b['p50'][d])} / {fmt(b['p75'][d])}"
        runs = _runs(days_out)
        print(f"   {m:22} {d:3d} {fmt(v):>8} {span:>24} {z:+6.1f}  {runs}")

    # 2. panels
    for title, metrics in PANELS:
        print(f"\n2. {title}: candidate (top-six median); < / > = below / above the top-six IQR")
        head = "   day " + "".join(f"{SHORT.get(m, m):>15}" for m in metrics)
        print(head)
        for d in range(len(mine["money_dawn"])):
            cells = []
            for m in metrics:
                v = mine[m][d]
                b = band[m]
                p50 = b["p50"][d]
                mark = ""
                if v is not None and b["p25"][d] is not None and b["n"][d] >= 5:
                    if v < b["p25"][d]:
                        mark = "<"
                    elif v > b["p75"][d]:
                        mark = ">"
                cells.append(f"{fmt(v)}{mark} ({fmt(p50)})")
            print(f"   {d:3d} " + "".join(f"{c:>15}" for c in cells))

    # 3. season revenue by product
    print(f"\n3. Season revenue by product (units x avg price): candidate, opponent, top-six median")
    print(f"   {'product':11} {'candidate':>22} {'opponent':>22} {'top6 median rev':>16} {'top6 units':>11} {'top6 avg':>9}")
    tot = [0, 0]
    for p in DM.PRODUCTS:
        cu, cr = sum(mine["sold_" + p]), sum(mine["revenue_" + p])
        ou, orr = sum(theirs["sold_" + p]), sum(theirs["revenue_" + p])
        tot[0] += cr
        tot[1] += orr
        t = season["revenue_" + p]["p50"]
        tu = season["units_" + p]["p50"]
        tp = season["avg_price_" + p]
        c = f"{cr:>9,.0f} ({cu}x{cr / cu:.0f})" if cu else f"{0:>9,}"
        o = f"{orr:>9,.0f} ({ou}x{orr / ou:.0f})" if ou else f"{0:>9,}"
        print(f"   {p:11} {c:>22} {o:>22} {t:>16,.0f} {tu:>11.0f} {tp if tp is None else round(tp):>9}")
    print(f"   {'total':11} {tot[0]:>22,.0f} {tot[1]:>22,.0f}")


def _runs(days):
    if not days:
        return ""
    out, start, prev = [], days[0], days[0]
    for d in days[1:]:
        if d == prev + 1:
            prev = d
            continue
        out.append(f"{start}" if start == prev else f"{start}-{prev}")
        start = prev = d
    out.append(f"{start}" if start == prev else f"{start}-{prev}")
    return ",".join(out)


if __name__ == "__main__":
    main()
