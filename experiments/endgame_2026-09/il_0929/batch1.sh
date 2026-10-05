#!/bin/zsh
cd /Users/stephanengugi/KagricultureLocalData
P=.venv313/bin/python
B=tonight_0928/tetsu_step1009_full.py
$P il_0929/run_match.py il_0929/hA_drop.py $B 900-915 6 il_0929/m_hA_drop_vs_base.jsonl > il_0929/m_hA_drop_vs_base.txt 2>&1
$P il_0929/run_match.py il_0929/hA_cow.py $B 900-915 6 il_0929/m_hA_cow_vs_base.jsonl > il_0929/m_hA_cow_vs_base.txt 2>&1
echo BATCH1_DONE >> il_0929/m_hA_cow_vs_base.txt
