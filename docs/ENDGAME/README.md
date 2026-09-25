# Endgame research, Sept 21-30, 2026

Start with the plan and its status log: `docs/superpowers/plans/2026-09-21-endgame.md`.
Every submission since Sept 21 is in `submissions_log.md`.

## Where things stand

- Today's top 10 are reactive agents, not fixed schedules. None of them can be copied (`copyability.md`).
- Strongest agent we hold: **W3** (`agents/w3_herdsafe2700.py`, public Herd-Safe Sale Window by Dmitrii Gluzdov). It beats V57 2-14 and reactive v7 0-16 (`crosscheck_2026-09-25.md`). No public agent descends from the top six.
- Eight overlays on the 2945 Farm were measured and rejected. The base already contains our rim, sells-first ordering and the turn-0 wheat trick.
- On the ladder the 2945 Farm converges at about 2,145, because most of its opponents are copies or forks of it (`ladder_diagnosis_56431632.md`).

## Read in this order

| doc | question it answers |
|---|---|
| `harness_gate.md` | Can we replay real ladder games locally? (Yes, 30/30 to the dollar.) |
| `public_inventory.md`, `public_panel.md` | What is public, and which public agent is strongest? |
| `copyability.md`, `dataset_harvest.md` | Can the top teams' schedules be harvested? (No.) |
| `day11_diagnosis.md`, `traces_2026-09-21.md` | Where does the 2945 Farm lose to 3,000+ teams? |
| `late_overlay_results.md`, `v2_results.md`, `v3_results.md`, `rim_results.md`, `dead_spend.md`, `fork_results.md` | The eight levers, and why each one was rejected |
| `ladder_diagnosis_56431632.md` | Why the base converged at 2,145 on the ladder |
| `crosscheck_2026-09-25.md` | How do our candidates fare against W3, W1 and W0, and can we adopt a top-six agent? (No.) |

## Rules the measurements taught

- The frozen-replay harness inflates any lever the opponent would respond to. Absolute self-play and head-to-head against the base settle those levers.
- If you stop selling into a market you have already flooded, whoever still sells there picks up that revenue.
- Only the latest two submissions are active, and a new one evicts the older. Check the active pair before anyone submits.
