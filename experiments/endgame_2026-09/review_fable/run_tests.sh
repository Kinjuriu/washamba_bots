#!/bin/bash
# Review test driver: waits for the corpus re-simulation, then runs the targeted checks. <= ~230 games.
PY=~/Desktop/washamba_bots/.venv/bin/python
cd ~/KagricultureLocalData/review_fable
while pgrep -f summarize_replays.py > /dev/null; do sleep 30; done
echo "corpus done $(date)" >> run_tests.log
# 1. opening fingerprints + early money, 4 workers
rm -f fp_chunk_* fingerprints_*.jsonl
split -l 358 all_replays.txt fp_chunk_
for c in fp_chunk_a?; do $PY fingerprints.py fingerprints_$c.jsonl $(cat $c) & done; wait
echo "fingerprints done $(date)" >> run_tests.log
# 2. ranks 7-12 replay panel: W3 then W3+frontrun (60 games each), 3 workers
$PY r7to12panel.py w3 ../submissions/w3_herdsafe2700.py r7to12_panel_results.jsonl 3
echo "panel w3 done $(date)" >> run_tests.log
$PY r7to12panel.py frontrun w3_frontrun_pr63.py r7to12_panel_results.jsonl 3
echo "panel frontrun done $(date)" >> run_tests.log
# 3. frontrun vs opponents outside its gate pool, fresh seeds, both seats (100 games), 4 workers
$PY ../harness/pool_harness.py --agent fr=w3_frontrun_pr63.py --agent w3=../submissions/w3_herdsafe2700.py \
  --agent hsv3=../agents/herdsafev3/main.py --agent k0013=../agents/k0013/main.py --agent fieldcraft=../agents/fieldcraft/main.py \
  --agent farm2945=../agents/farm2945/main.py --candidates fr --opponents w3 hsv3 k0013 fieldcraft farm2945 \
  --seeds 9001-9010 --workers 4 --out frontrun_pool.jsonl > frontrun_pool.log 2>&1
echo "frontrun pool done $(date)" >> run_tests.log
