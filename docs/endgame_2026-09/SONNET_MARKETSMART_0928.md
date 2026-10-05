# Sonnet task, 28 September evening: pull tetsutani's "Market-Smart Farming" agent

Run in VS Code in ~/KagricultureLocalData. Read-only on Kaggle: do not submit anything.
Few calls, back off 60 s on HTTP 429, stream files.

```
1. kaggle kernels pull tetsutani/market-smart-farming-kaggriculture -p public_notebooks/tetsutani/market_smart -m
   Note the kernel's last run time and version from kernel-metadata.json and the notebook header.
2. Extract the submitted agent the same way as public_notebooks/tetsutani/extract_archive.py did for
   the demand-preserving notebook (embedded base85/base64 tar, hash-checked). Save it as
   public_notebooks/tetsutani/market_smart/main.py with LICENSE/NOTICE beside it.
   If the agent is plain code cells instead of an archive, concatenate the cells that define the
   agent into main.py and say so.
3. Check: self-play seed 0 finishes DONE/DONE; print the name of the last callable in the module
   and the max turn duration from env.logs.
4. Write public_notebooks/tetsutani/market_smart/NOTE.md (10-20 lines): version/date, what the
   header says it adds over Step1009 (demand-preserving notebook), sha256 of main.py.
Do not run tournaments; Claude will test it in the cloud. Tell Stephane when main.py is saved.
```
