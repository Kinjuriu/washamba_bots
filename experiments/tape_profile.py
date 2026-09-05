"""Diff an agent's season *timing* against the v20 tapes, day by day.

Why this exists: `mydocs/FACTS.md`'s counters are unit counts at named
moments (`d0 4/4`, `unlock >= 14`, `NW STRAW = 0`). Seven sessions passed
every one of them while the contested bank vs `agents/route_v20.py` fell
from ~51k to ~8k, because the rows had drifted 4-6 days later than the
tapes on every producing asset and no counter measured *when*.

This prints the tape profile (mean over `mydocs/tape_transcripts`), the
candidate's profile from a real contested episode, and the live opponent's
profile from the same episode, for the quantities that carry the season:
crew, herd, plantings by crop, sells by product, land days.

Usage:
    .venv/Scripts/python.exe experiments/tape_profile.py                    # tapes only
    .venv/Scripts/python.exe experiments/tape_profile.py experiments/_facts_v20.py
    .venv/Scripts/python.exe experiments/tape_profile.py main.py --seed 8
"""

from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TAPES_CSV = ROOT / "mydocs" / "tape_transcripts" / "all_tapes_turns.csv"
V20 = ROOT / "agents" / "route_v20.py"

DAYS = 30
CROPS = ("MELON", "WHEAT", "STRAWBERRY", "CARROT", "TOMATO")
PRODUCTS = ("MELON", "WHEAT", "STRAWBERRY", "CARROT", "WOOL", "MILK", "FERTILIZER")


def _blank():
    """Per-day profile of one season."""
    return {
        "hands": [0] * DAYS,
        "owned": [0] * DAYS,
        "plant": {c: [0] * DAYS for c in CROPS},
        "sell": {p: [0] * DAYS for p in PRODUCTS},
        "land": [],
        "bank": None,
    }


def _joined(tokens):
    """The engine submits each action/order as a token list: ["PLANT", "MELON"]."""
    if not tokens:
        return ""
    if isinstance(tokens, str):
        return tokens
    return " ".join(str(t) for t in tokens if t is not None)


def _tally(prof, day, n_hands, unit_actions, market_orders):
    prof["hands"][day] = max(prof["hands"][day], n_hands)
    for act in unit_actions:
        if act.startswith("PLANT "):
            crop = act.split()[1]
            if crop in prof["plant"]:
                prof["plant"][crop][day] += 1
    for order in market_orders:
        parts = order.split()
        if not parts:
            continue
        kind = parts[0]
        qty = int(parts[2]) if len(parts) > 2 and parts[2].lstrip("-").isdigit() else 1
        if kind == "SELL" and parts[1] in prof["sell"]:
            prof["sell"][parts[1]][day] += qty
        elif kind == "BUY_ANIMAL":
            prof["owned"][day] += qty
        elif kind == "BUY_LAND":
            prof["land"].append(day)


def _cumulate(prof):
    running = 0
    for d in range(DAYS):
        running += prof["owned"][d]
        prof["owned"][d] = running
    return prof


def tape_profile():
    """Mean per-day profile over every tape in `all_tapes_turns.csv`."""
    rows = list(csv.DictReader(TAPES_CSV.open(encoding="utf-8")))
    per_tape = defaultdict(_blank)
    for row in rows:
        tape = row["tape"]
        day = int(row["day"]) - 1  # transcript day N = engine day N-1
        if not 0 <= day < DAYS:
            continue
        hands = [a.strip() for a in row["hands_actions"].split(";") if a.strip()]
        units = [row["farmer_action"].strip()] + hands
        orders = [o.strip() for o in row["market_actions"].split(";") if o.strip()]
        _tally(per_tape[tape], day, len(hands), [u for u in units if u], orders)

    tapes = [_cumulate(p) for p in per_tape.values()]
    n = len(tapes)
    mean = _blank()
    for d in range(DAYS):
        mean["hands"][d] = sum(t["hands"][d] for t in tapes) / n
        mean["owned"][d] = sum(t["owned"][d] for t in tapes) / n
        for c in CROPS:
            mean["plant"][c][d] = sum(t["plant"][c][d] for t in tapes) / n
        for p in PRODUCTS:
            mean["sell"][p][d] = sum(t["sell"][p][d] for t in tapes) / n
    land = Counter(d for t in tapes for d in t["land"])
    mean["land"] = sorted(land)
    return mean, n


def episode_profiles(agent, opponent, seed):
    """Profiles for both seats of one contested episode (agent in seat 0)."""
    from kaggle_environments import make

    env = make(
        "kaggriculture",
        configuration={"episodeSteps": 720, "seed": seed},
        debug=False,
    )
    env.run([str(agent), str(opponent)])

    profs = [_blank(), _blank()]
    for step in env.steps:
        obs = step[0].observation
        day = int(obs["day"])
        if not 0 <= day < DAYS:
            continue
        for seat in (0, 1):
            action = step[seat].action or {}
            hands = [_joined(h) for h in (action.get("hands") or [])]
            hands = [h for h in hands if h]
            units = [_joined(action.get("farmer"))] + hands
            orders = [_joined(o) for o in (action.get("market") or [])]
            _tally(
                profs[seat], day, len(hands),
                [u for u in units if u], [o for o in orders if o],
            )

    final = env.steps[-1]
    for seat in (0, 1):
        _cumulate(profs[seat])
        profs[seat]["bank"] = final[seat].reward
    return profs


def _row(label, values, width=5, fmt="{:.0f}"):
    return label.ljust(14) + "".join(fmt.format(v).rjust(width) for v in values)


def print_series(title, tape, cand, opp, cand_label, opp_label):
    print(f"\n{title}")
    print("day".ljust(14) + "".join(str(d).rjust(5) for d in range(DAYS)))
    print(_row("tape mean", tape))
    if cand is not None:
        print(_row(cand_label, cand))
        print(_row(opp_label, opp))
        print(_row("cand - tape", [c - t for c, t in zip(cand, tape)]))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("agent", nargs="?", help="candidate agent path (omit for tapes only)")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--opponent", default=str(V20))
    args = ap.parse_args()

    tape, n_tapes = tape_profile()
    print(f"tape profile: mean over {n_tapes} tapes ({TAPES_CSV.name})")

    cand = opp = None
    if args.agent:
        agent_path = ROOT / args.agent if not Path(args.agent).is_absolute() else Path(args.agent)
        cand, opp = episode_profiles(agent_path, args.opponent, args.seed)
        print(
            f"contested episode: {args.agent} (seat 0) vs "
            f"{Path(args.opponent).name} (seat 1), seed {args.seed}"
        )
        print(f"  bank: candidate {cand['bank']:.0f}  opponent {opp['bank']:.0f}  "
              f"delta {cand['bank'] - opp['bank']:+.0f}")
        print(f"  land days: tape {tape['land']}  candidate {cand['land']}  "
              f"opponent {opp['land']}")

    lab_c, lab_o = "candidate", "opponent"
    print_series("crew (max hands acting in a turn)", tape["hands"],
                 cand and cand["hands"], opp and opp["hands"], lab_c, lab_o)
    print_series("herd owned (cumulative BUY_ANIMAL)", tape["owned"],
                 cand and cand["owned"], opp and opp["owned"], lab_c, lab_o)
    for crop in CROPS:
        if not any(tape["plant"][crop]) and not (cand and any(cand["plant"][crop])):
            continue
        print_series(f"PLANT {crop}", tape["plant"][crop],
                     cand and cand["plant"][crop], opp and opp["plant"][crop],
                     lab_c, lab_o)
    for product in PRODUCTS:
        if not any(tape["sell"][product]) and not (cand and any(cand["sell"][product])):
            continue
        print_series(f"SELL {product} (order qty)", tape["sell"][product],
                     cand and cand["sell"][product], opp and opp["sell"][product],
                     lab_c, lab_o)

    if cand is not None:
        print("\nfirst day each series falls behind the tape by more than a third:")
        series = [("crew", tape["hands"], cand["hands"]),
                  ("herd", tape["owned"], cand["owned"])]
        series += [(f"PLANT {c}", tape["plant"][c], cand["plant"][c]) for c in CROPS]
        for name, t, c in series:
            behind = next(
                (d for d in range(DAYS) if t[d] >= 3 and c[d] < t[d] * 2 / 3), None
            )
            print(f"  {name:<18} {'day ' + str(behind) if behind is not None else 'never'}")


if __name__ == "__main__":
    main()
