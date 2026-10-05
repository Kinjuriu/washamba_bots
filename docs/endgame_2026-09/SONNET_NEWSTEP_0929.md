# Sonnet task, 29 September evening: is there a tetsutani step newer than Step1009?

Run in VS Code in ~/KagricultureLocalData. Read-only on Kaggle: do not submit anything.
Few calls, back off 60 s on HTTP 429.

```
1. kaggle kernels list --user tetsutani --sort-by dateRun --page-size 20
   and  kaggle kernels list --competition kaggriculture --search tetsutani --sort-by dateRun --page-size 20
   Report every tetsutani kernel with its last run date.
2. Pull the current version of tetsutani/demand-preserving-turn-sale-timing into
   public_notebooks/tetsutani/latest_0929/ (kaggle kernels pull ... -p <dir> -m).
   Read the notebook's hero heading (the "StepNNNN" title in the first markdown cells) and
   kernel-metadata.json. If the step is still Step1009, write NOTE.md saying so and stop.
3. If the step is newer than 1009 (or another tetsutani kernel run after 27 Sep 12:00 UTC contains
   an agent archive), decode the archive exactly as public_notebooks/tetsutani/extract_archive.py
   does. If auto mode blocks tar extraction, do NOT add a permission rule: just tell Stephane the
   .ipynb path; Claude will extract it in the cloud.
4. Write public_notebooks/tetsutani/latest_0929/NOTE.md: step number, run date, archive sha256,
   main.py sha256 if extracted. Tell Stephane when done.
```
