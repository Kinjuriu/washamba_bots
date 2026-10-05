#!/usr/bin/env python3
"""Merges raw/*.json.gz replays INTO replays.parquet (zstd), batch by batch.

Carries over every row already in episodes/replays.parquet whose id is not in
raw/, then appends the raw files. Never shrinks the corpus: raw/ holds only the
current crawl's downloads, the parquet holds history. Kaggle decompresses
uploaded .gz, hence parquet (~240x on JSON text). Batched to cap memory.
"""
import glob, gzip, os, shutil
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

HERE = Path(__file__).parent
WORK = HERE / "replays.parquet"
STAGE = HERE.parent / "episodes_dataset" / "replays.parquet"
TMP = HERE / "replays_new.parquet"
BATCH = 20
SCHEMA = pa.schema([("episode_id", pa.int64()), ("replay_json", pa.string())])

files = sorted(glob.glob(str(HERE / "raw" / "*.json.gz")))
raw_ids = {int(os.path.basename(f).split(".")[0]) for f in files}
writer = pq.ParquetWriter(TMP, SCHEMA, compression="zstd", compression_level=10)
carried = 0
try:
    if WORK.exists():
        for batch in pq.ParquetFile(WORK).iter_batches(batch_size=BATCH):
            tbl = batch.to_pydict()
            keep_i = [i for i, e in enumerate(tbl["episode_id"]) if e not in raw_ids]
            if keep_i:
                writer.write_table(pa.table(
                    {"episode_id": [tbl["episode_id"][i] for i in keep_i],
                     "replay_json": [tbl["replay_json"][i] for i in keep_i]}, schema=SCHEMA))
                carried += len(keep_i)
    for start in range(0, len(files), BATCH):
        ids, blobs = [], []
        for f in files[start:start + BATCH]:
            ids.append(int(os.path.basename(f).split(".")[0]))
            blobs.append(gzip.decompress(open(f, "rb").read()).decode())
        writer.write_table(pa.table({"episode_id": ids, "replay_json": blobs}, schema=SCHEMA))
finally:
    writer.close()
TMP.replace(WORK)
shutil.copy(WORK, STAGE)
total = pq.ParquetFile(WORK).metadata.num_rows
print(f"replays.parquet: {carried} carried + {len(files)} from raw = {total} rows, "
      f"{WORK.stat().st_size/1e6:.1f} MB")
