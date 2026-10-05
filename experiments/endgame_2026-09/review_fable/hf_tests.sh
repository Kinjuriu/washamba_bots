#!/bin/bash
PY=~/Desktop/washamba_bots/.venv/bin/python
cd ~/KagricultureLocalData/review_fable
A="--agent hf=agents/w3_hf.py --agent w3=../submissions/w3_herdsafe2700.py --agent hsv3=../agents/herdsafev3/main.py --agent k0013=../agents/k0013/main.py --agent fieldcraft=../agents/fieldcraft/main.py --agent farm2945=../agents/farm2945/main.py --agent v57=../agents/v57/main.py --agent w0=../submissions/w0_v15stack_control.py"
echo "start $(date)" >> hf_tests.log
$PY ../harness/pool_harness.py $A --candidates hf --opponents w3 hsv3 k0013 fieldcraft farm2945 v57 w0 --seeds 9101-9110 --workers 4 --out hf_pool.jsonl > hf_pool.log 2>&1
echo "pool done $(date)" >> hf_tests.log
$PY ../harness/pool_harness.py $A --candidates hf --opponents w3 --seeds 9111-9120 --workers 4 --out hf_pool.jsonl > hf_mirror2.log 2>&1
echo "mirror2 done $(date)" >> hf_tests.log
$PY ../harness/pool_harness.py $A --candidates w3 --opponents hsv3 k0013 fieldcraft farm2945 v57 w0 --seeds 9101-9110 --workers 4 --out w3_pool_ref.jsonl > w3_pool_ref.log 2>&1
echo "w3 ref done $(date)" >> hf_tests.log
$PY r7to12panel.py hf agents/w3_hf.py r7to12_panel_results.jsonl 4
echo "r712 panel done $(date)" >> hf_tests.log
$PY ../harness/top6panel.py w3 ../submissions/w3_herdsafe2700.py top6_panel_results_review.jsonl 4
echo "top6 panel w3 done $(date)" >> hf_tests.log
$PY ../harness/top6panel.py hf agents/w3_hf.py top6_panel_results_review.jsonl 4
echo "top6 panel hf done $(date)" >> hf_tests.log
