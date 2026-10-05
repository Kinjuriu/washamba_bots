#!/bin/zsh
PY=~/Desktop/washamba_bots/.venv/bin/python
cd ~/KagricultureLocalData/experiments_r3
$PY identity_check_c.py > identity_c_rev3.txt 2>&1
if grep -q FAIL identity_c_rev3.txt; then echo "IDENTITY FAILED - STOP"; exit 1; fi
$PY ../harness/pool_harness.py \
  --agent w0=../submissions/w0_v15stack_control.py --agent C1=C1/main.py --agent C2=C2/main.py \
  --candidates C1 C2 --opponents w0 --seeds 2001-2030 --workers 7 --out mirror_C.jsonl > mirror_C_summary.txt 2>&1
$PY panel_faithful.py C1 C1/main.py panel_C1.jsonl 7
$PY panel_faithful.py C2 C2/main.py panel_C2.jsonl 7
echo C-ALL-DONE
