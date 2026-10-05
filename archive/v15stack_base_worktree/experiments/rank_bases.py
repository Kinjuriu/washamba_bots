"""Base-vetting pipeline: round-robin rank a set of agent files.

The winning lever here has been adopting the strongest public base route, not
tuning on one. This ranks any set of agents against each other under a contested
market, so a new base is judged in an hour of local play instead of a noisy
ladder submission (a single submission starts at rating 600 and swings 1000+ on
early-game RNG; local head-to-head over many seeds, both seats, is the stable
signal).

Scoring matches the ladder: win, loss, or TIE, margin ignored. Two tape
replayers on the same route bank exactly the same money in a mirror, which is a
tie, not a loss, so ties count as ties and the rank is a Bradley-Terry style
score, (wins + 0.5*ties) / matches. Reads head_to_head.play so a match is scored
the same way in both tools.

To vet a new public route:
  1. Decode it:  decode_route.py <kernel-slug>
  2. Rank it:    rank_bases.py 12 agents/router_yhay.py experiments/.decoded/<name>.py
  3. A candidate that clearly out-scores router_yhay (more wins than losses, not
     just ties) is worth a submission slot; otherwise discard it, no slot spent.

Read the RANK table first. The self-control line must sit near 50% score and near
zero margin (a pure tape replayer shows ~all ties there, which is correct); if it
doesn't, the harness is lying.

Usage, from the repo root:
    .venv/bin/python experiments/rank_bases.py [seeds] [agentA.py agentB.py ...]
"""

import itertools
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from head_to_head import play  # one seat-swapped episode, scored identically

AGENTS = [
    "agents/router_yhay.py",   # current base
    "agents/route_v20.py",     # previous base, kept as a reference opponent
]


def pair_record(a, b, seeds):
    """Both seats. Returns (a_wins, a_losses, ties, matches, a_mean_margin)."""
    diffs = []
    w = l = t = 0
    for seed in range(seeds):
        a0, b1 = play(a, b, seed)   # a in seat 0
        b0, a1 = play(b, a, seed)   # a in seat 1
        for ab, bb in ((a0, b1), (a1, b0)):
            diffs.append(ab - bb)
            if ab > bb: w += 1
            elif ab < bb: l += 1
            else: t += 1
    return w, l, t, len(diffs), sum(diffs) / len(diffs)


def name(p):
    return os.path.basename(p)


def main():
    args = sys.argv[1:]
    seeds = int(args.pop(0)) if args and args[0].isdigit() else 8
    agents = [a for a in (args or AGENTS) if os.path.exists(a)]
    if len(agents) < 2:
        print("need at least two existing agent files (checked: %s)" % (args or AGENTS))
        raise SystemExit(2)

    score = {a: 0.0 for a in agents}
    played = {a: 0 for a in agents}
    margin = {a: 0.0 for a in agents}

    print(f"round-robin over {len(agents)} agents, {seeds} seeds x 2 seats per pair")
    print("(W-L-T from the first agent's side; ties count as half)\n")
    for a, b in itertools.combinations(agents, 2):
        w, l, t, m, mean = pair_record(a, b, seeds)
        score[a] += w + 0.5 * t;   score[b] += l + 0.5 * t
        played[a] += m;            played[b] += m
        margin[a] += mean * m;     margin[b] += -mean * m
        print(f"  {name(a):<24} vs {name(b):<24}  {w}-{l}-{t} (of {m})  mean {mean:+9.0f}")

    order = sorted(agents, key=lambda a: (score[a] / played[a], margin[a] / played[a]), reverse=True)
    print("\nRANK  (score = (wins + half-ties) / matches, then mean margin)")
    for i, a in enumerate(order, 1):
        print(f"  {i}. {name(a):<26} {score[a]/played[a]:6.1%}   {margin[a]/played[a]:+9.0f}   ({played[a]} matches)")

    print("\nself-control (each agent vs a copy of itself; score ~50%, margin ~0)")
    ctrl = max(2, seeds // 2)
    for a in agents:
        w, l, t, m, mean = pair_record(a, a, ctrl)
        s = (w + 0.5 * t) / m
        ok = abs(mean) < 1500 and 0.35 <= s <= 0.65
        print(f"  {name(a):<26} {s:6.1%}  W-L-T {w}-{l}-{t}  mean {mean:+9.0f}{'' if ok else '   <-- CHECK'}")


if __name__ == "__main__":
    main()
