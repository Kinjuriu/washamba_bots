"""Thin re-export so h14.py/gates.py (which call `mod.make(pm, se)`) can reach
WantamScoreExec, the Step 2 value-aware scoring executor."""
from wantam import make_score as make
