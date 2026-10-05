"""Run harness/resim_trades.py on a list of replay paths, parse the JSON-lines output,
and return per-(episode,seat) records. Usage: python resim_runner.py out.json path1 path2 ...
"""
import sys, os, json, subprocess

HARNESS = '/Users/stephanengugi/KagricultureLocalData/harness'
PY = '/Users/stephanengugi/Desktop/washamba_bots/.venv/bin/python3'

def run_resim(paths, timeout_per=60):
    out = []
    # call individually so one bad replay doesn't kill the batch
    for p in paths:
        try:
            r = subprocess.run([PY, 'resim_trades.py', p], cwd=HARNESS,
                                capture_output=True, text=True, timeout=timeout_per)
            for line in r.stdout.strip().splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    out.append(json.loads(line))
                except Exception:
                    pass
            if r.returncode != 0 and not out:
                out.append(dict(path=p, error=r.stderr[-500:]))
        except Exception as ex:
            out.append(dict(path=p, error=str(ex)))
    return out

if __name__ == '__main__':
    out_path = sys.argv[1]
    paths = sys.argv[2:]
    res = run_resim(paths)
    json.dump(res, open(out_path, 'w'), indent=2)
    print(f"wrote {len(res)} records to {out_path}")
