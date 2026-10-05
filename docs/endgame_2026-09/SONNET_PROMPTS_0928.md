# Sonnet prompt, 28 September: fetch the demand-preserving sale timing agent (tetsutani)

Run in VS Code in ~/KagricultureLocalData. Read-only on Kaggle: do not submit anything.

```
Goal: get the public source of the "demand-preserving sale timing" layer attributed to
tetsutani (Apache-2.0), which Peter layered on W3 as w3_dp_saletiming.py (26-6 vs W3).
Peter has not shared his file, so we rebuild it from the public notebook.

1. Find the notebook(s). Use the Kaggle CLI, streaming results, few calls, back off 60 s
   on HTTP 429:
     kaggle kernels list --competition kaggriculture --search tetsutani --page-size 50
     kaggle kernels list --competition kaggriculture --search demand --page-size 50
     kaggle kernels list --competition kaggriculture --search "sale timing" --page-size 50
   Also check public_notebooks/ and agents/ here in case we already have it.
2. Pull every candidate (kaggle kernels pull <ref> -p public_notebooks/tetsutani/<slug> -m)
   and extract the agent code the way decode_route/earlier scans did. Keep the licence
   header and the notebook URL in a README.md in that folder.
3. Identify exactly what "demand-preserving" does: which products, the rule that decides
   the lot size and the turn to sell, and any constants. Write it up in 20-40 lines in
   public_notebooks/tetsutani/WHAT_IT_DOES.md (quote function names, not long code).
4. Build agents/dp/w3_dp_rebuild.py: submissions/w3_herdsafe2700.py plus that selling
   layer, as close to the public version as the code allows, entry point captured with
   [v for v in list(globals().values()) if callable(v)][-1] (W3's `agent` name is an
   inner layer). Check: self-play seed 0 finishes DONE/DONE, max turn under 500 ms.
5. Quick check with harness/pool_harness.py: w3_dp_rebuild vs w3_herdsafe2700, seeds
   9401-9410, both seats (20 games), 2 workers. Report W-L-T and mean margin.
   Peter reported 26-6 against W3 on his holdout; if we are far from that, say so.
Report in public_notebooks/tetsutani/REPORT.md. Do not upload anything.
```
