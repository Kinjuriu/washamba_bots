#!/bin/bash
PY=~/Desktop/washamba_bots/.venv/bin/python
cd ~/KagricultureLocalData/review_fable
while pgrep -f hf_tests.sh > /dev/null; do sleep 30; done
echo "variants start $(date)" >> hf_variants.log
A="--agent w3=../submissions/w3_herdsafe2700.py --agent v57=../agents/v57/main.py --agent w0=../submissions/w0_v15stack_control.py --agent hsv3=../agents/herdsafev3/main.py --agent min3=agents/w3_hf_min3.py --agent nomelon=agents/w3_hf_nomelon.py --agent early=agents/w3_hf_early.py"
$PY ../harness/pool_harness.py $A --candidates min3 nomelon early --opponents w3 v57 w0 hsv3 --seeds 9101-9110 --workers 4 --out hf_variants.jsonl > hf_variants_run.log 2>&1
echo "variants done $(date)" >> hf_variants.log
