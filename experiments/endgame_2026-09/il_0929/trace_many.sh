#!/bin/zsh
cd /Users/stephanengugi/KagricultureLocalData
for s in 900 901 902 903 904 905 906 907 908 909 910 911 912 913 914 915; do
  ( .venv313/bin/python il_0929/trace_game.py il_0929/hA_drop.py tonight_0928/tetsu_step1009_full.py $s il_0929/tr_drop_$s.json > /dev/null 2>&1 ) &
  while [ $(jobs -r | wc -l) -ge 6 ]; do sleep 1; done
done
wait
echo TRACES_DONE > il_0929/trace_many.done
