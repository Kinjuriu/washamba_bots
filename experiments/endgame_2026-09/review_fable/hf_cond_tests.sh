#!/bin/bash
PY=~/Desktop/washamba_bots/.venv/bin/python
cd ~/KagricultureLocalData/review_fable
while pgrep -f "hf_tests.sh|hf_variants.sh" > /dev/null; do sleep 30; done
echo "cond start $(date)" >> hf_cond.log
$PY ../harness/pool_harness.py --agent cond=agents/w3_hf_cond.py --agent w3=../submissions/w3_herdsafe2700.py --agent w0=../submissions/w0_v15stack_control.py --agent hsv3=../agents/herdsafev3/main.py --agent v57=../agents/v57/main.py --candidates cond --opponents w3 w0 hsv3 v57 --seeds 9101-9110 --workers 4 --out hf_cond_pool.jsonl > hf_cond_pool.log 2>&1
echo "cond pool done $(date)" >> hf_cond.log
$PY r7to12panel.py cond agents/w3_hf_cond.py r7to12_panel_results.jsonl 4
echo "cond r712 done $(date)" >> hf_cond.log
