#!/bin/zsh
PY=~/Desktop/washamba_bots/.venv/bin/python
cd ~/KagricultureLocalData/experiments_r3
for v in B D4 D8; do
  $PY panel_faithful.py $v $v/main.py panel_$v.jsonl 7
done
echo ALL-PANELS-DONE
