# ---- cell 0
# Kaggriculture V57 — Funding-Order Invariant

V57 keeps the complete qualified V56 policy and fixes a causal hole in its same-turn order-book optimizer. V56 could move HIRE, BUY_SEED, BUY_ANIMAL or BUY_LAND earlier than the parent slot, before the sale cash that funded it had arrived. V57 rejects those permutations while retaining the route, production policy, scorer and all prior gates.

Two prospective official-engine panels used both seats, reacting opponents, exact hashes and replay checks. Across 320 games, V57 improved 30 paired outcomes, tied 290 and regressed in none. V56 scored 98/42/20; V57 scored 102/42/16. Points rose from 0.6750 to 0.6875 and mean paired margin rose $9.89. This measured safety upgrade does not guarantee a particular live rating.

| Panel | V56 W/L/T | V57 W/L/T | Point gain | Mean margin gain | Better / equal / worse |
|---|---:|---:|---:|---:|---:|
| Pilot: 4 new worlds, 8 rivals | 40/16/8 | 42/16/6 | +0.015625 | +$11.56 | 14 / 50 / 0 |
| Confirmation: 6 new worlds, 8 rivals | 58/26/12 | 60/26/10 | +0.010417 | +$8.77 | 16 / 80 / 0 |

The refresh inspected 21 current non-Ahmed public Code versions. Harvest Ledger's new mixed-market ledger was correct but outcome-identical in 128 games; Best Agent Ranking was byte-identical to Shiiin9 already represented in V56; Dmitrii's update retained its Rescue control after its challenger failed. No zero-impact layer was added.

Apache-2.0 notices and attribution remain for Thomas Tschinkel, Yusuke Hayashi, destbreso, aurax7, Tetsutani, prvsiyan, Dmitrii Gluzdov, Seyit Kaan Gunes, Shiiin9 and busyaprime. haodou092's Harvest Ledger is recorded as evaluated research input.

Run the three code cells on CPU. No dataset attachment, Internet, GPU or training is required. The notebook writes `submission_competitive_v57.tar.gz` in `/kaggle/working`; it does not submit or publish anything.

Source SHA256: `2ee689fdc58f38b7bf6b80b8d3f48129d19b47201dbee51fdcbd977498a5106f`. Isolated maximum callback time: 20.100 ms.
