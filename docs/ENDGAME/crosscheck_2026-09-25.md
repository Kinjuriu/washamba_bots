# Cross-check against the team's v15stack agents, and the top-six opening check (Sept 24-25)

Two questions left open after the Sept 24 frontier screen, both answered locally.
Harness: `experiments/tapes/run_agents.py`, seeds 300-307, both seats (16 games per row).
Raw rows: `experiments/endgame/reactive_vs_stephane.jsonl`.

## 1. How do V57 and reactive v7 fare against Stephane's agents?

| candidate | vs W3 (herd-safe 2700) | vs W1 (v15stack race44) | vs W0 (v15stack) |
|---|---|---|---|
| V57 (`agents/washamba_base_v3.py`) | **2-14**, -1,224 | - | - |
| reactive v7 (`agents/washamba_reactive_v1.py`) | **0-16**, -4,763 | **16-0**, +9,926 | **16-0**, +9,950 |

- **The frontier screen's V57 recommendation is withdrawn.** W3 beats V57 2-14 here and 9-3 in Stephane's
  panel (`docs/SUBMISSIONS_2026-09-24.md`). V57 was submitted on Sept 24 (56514502) and has since been retired.
- **W3 is the strongest agent we hold.** Nothing we have tested beats it.
- **Reactive v7 beats the whole v15stack family by about 10,000 a game** (W0, W1, V56, V57), which fills the
  2,000-2,500 band, and loses to W3's and the 2945 Farm's style. It is the only candidate with a different
  matchup profile from W3, so it is the natural hedge for the second slot.

## 2. Does any public agent descend from the top six?

The top six share an opening no public agent was known to use (turn 1: buy 1 cow and 5 wheat; turn 2: sell
1 wheat, 4 hires, 1 cow, 3 sheep). `experiments/endgame/opening_check.py` printed the first two turns of all
20 public agents we hold plus W0/W1/W3.

**No sampled opening matches.** Every one of them hires 5 and buys 2 cows and 2 sheep on turn 2; they
differ only in the turn-1 wheat trade.

Scope, stated plainly: the survey ran each agent in seat 0 only, on seed 0 only, against `pass`, and read
two turns. A reactive agent, or a derivative that changed its opening, could still descend from the
top-six family without showing that opening here. So this is evidence against adopting any of these
agents as a top-six substitute, not proof that none descends from that family. Real-ladder records
support the same conclusion independently: every public family loses to the top-six opening family
(`field_families_2026-09-25.md`).

## What this means for the final pair

- Anchor: **W3**.
- Second slot: **W1** (current) or **reactive v7** (hedge against the v15stack band). Agree it with Stephane.
- Upload order if swapping: reactive v7 first (evicts the older W3), then W3 (evicts W1). The keeper goes last.
- The pair must be settled by Sept 29 so it converges before the Oct 1-15 episodes that set the final ranking.
- Honest ceiling: W3's lineage settles around 2,450-2,700. The top-10 line is ~2,930. No prize path is open.
