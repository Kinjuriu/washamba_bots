"""Analyze a trace_*.jsonl file: sheep lifecycle, feed actions, wheat levels."""
import json
import sys


def load(path):
    with open(path) as f:
        return [json.loads(line) for line in f]


def main():
    path = sys.argv[1]
    recs = load(path)

    ever_present = False
    escape_step = None
    place_step = None
    for r in recs:
        if "sheep_present" not in r:
            continue
        if r["sheep_present"] and not ever_present:
            ever_present = True
            place_step = r["step"]
        if ever_present and not r["sheep_present"] and escape_step is None:
            escape_step = r["step"]
            break

    print(f"{path}")
    print(f"  sheep first seen present at step={place_step}")
    print(f"  sheep escaped at step={escape_step}")

    print("  --- turns with FEED action, or sheep unfed>=1, or day<=6 wheat state ---")
    for r in recs:
        if "units" not in r:
            continue
        feed_here = any(u["action"] and u["action"][0] == "FEED" for u in r["units"])
        unfed = r.get("sheep_consecutive_unfed")
        interesting = feed_here or (unfed is not None and unfed >= 1)
        if interesting:
            unit_summary = ", ".join(
                f"{u['role']}@{tuple(u['pos'])}:{u['action']}(w={u['wheat_carried']})"
                for u in r["units"]
            )
            print(
                f"  step={r['step']:4d} day={r['day']:2d} hr={r['hour']:2d} "
                f"shed_wheat={r['shed_wheat']} sheep@{r.get('sheep_pos')} "
                f"fed_today={r.get('sheep_fed_today')} unfed={unfed} present={r.get('sheep_present')} "
                f"mkt={r.get('market_orders')} | {unit_summary}"
            )


if __name__ == "__main__":
    main()
