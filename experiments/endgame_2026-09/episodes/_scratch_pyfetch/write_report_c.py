import sys, os, json, csv

ROOT = '/Users/stephanengugi/KagricultureLocalData'
OUT = sys.argv[1]  # e.g. episodes/20260924T161358Z_washamba_0924b
d = os.path.join(ROOT, OUT)

sub_counts = json.load(open(os.path.join(d, 'sub_episode_counts.json')))
summary = json.load(open(os.path.join(d, 'summary_by_submission.json')))
w3_loss = None
w3_loss_path = os.path.join(d, 'w3_loss_analysis.json')
if os.path.exists(w3_loss_path):
    w3_loss = json.load(open(w3_loss_path))

download_results = json.load(open(os.path.join(d, 'download_results.json')))
log_results = json.load(open(os.path.join(d, 'log_download_results.json')))

def fmt_band_table(by_band):
    order = ['<2000', '2000-2500', '2500-2800', '>2800', 'unknown']
    lines = ["| Band | W | T | L |", "|---|---|---|---|"]
    for b in order:
        if b in by_band:
            w, t, l = by_band[b]
            lines.append(f"| {b} | {w} | {t} | {l} |")
    return "\n".join(lines)

def fmt_family_table(by_fam):
    lines = ["| Family | W | T | L |", "|---|---|---|---|"]
    for fam, (w, t, l) in sorted(by_fam.items()):
        lines.append(f"| {fam} | {w} | {t} | {l} |")
    return "\n".join(lines)

md = []
md.append("# Our current games and the 2,900 band (W3 / W1 re-upload)\n")
md.append(f"Generated from `{OUT}`. Read-only research; nothing submitted, no git actions taken.\n")

md.append("## 1. Submission IDs resolved\n")
md.append("| Submission | File | Submission ID | Non-validation completed episodes (API) |")
md.append("|---|---|---|---|")
label_map = {
    'w1_v15stack_race44.py (W1 re-upload)': ('w1_v15stack_race44.py', 56521297),
    'w3_herdsafe2700.py (W3, main.py)': ('main.py (w3_herdsafe2700.py)', 56518334),
    'w0_v15stack_control.py (W0, retired)': ('w0_v15stack_control.py', 56487592),
    'w1_v15stack_race44.py (W1, first upload)': ('w1_v15stack_race44.py (first upload)', 56491123),
}
for disp, meta in sub_counts.items():
    fname, sid = label_map.get(disp, (disp, meta['sid']))
    md.append(f"| {disp} | {fname} | {sid} | {meta['non_val_completed']} |")
md.append("")
md.append("**measured**: IDs resolved from `kaggle competitions submissions kaggriculture -v`, matched by "
           "upload date (24 Sep 2026) and description text. W1 re-upload = 56521297 (uploaded 12:34, "
           "\"Re-uploaded to pair with W3\"); W3 = 56518334 (uploaded 09:55, fileName `main.py`, description "
           "names it `w3_herdsafe2700`). W0 (56487592) and W1 first upload (56491123) were supplied by the task.\n")

md.append("## 2. Download summary\n")
n_replays_dl = sum(1 for v in download_results.values() if v.startswith('downloaded'))
n_replays_cache = sum(1 for v in download_results.values() if v.startswith('copied'))
n_replays_err = sum(1 for v in download_results.values() if v.startswith('error'))
n_logs_dl = sum(1 for v in log_results.values() if v.startswith('downloaded'))
n_logs_cache = sum(1 for v in log_results.values() if v.startswith('copied'))
n_logs_err = sum(1 for v in log_results.values() if v.startswith('error'))
md.append(f"- Replays: {n_replays_dl} freshly downloaded, {n_replays_cache} reused from the existing "
          f"`20260923T161855Z_washamba_vs_top6` / top6 caches (same episode_id, byte-identical file), "
          f"{n_replays_err} still failing after retries (out of {len(download_results)} distinct episodes). "
          f"**measured**")
md.append(f"- Our own agent logs: {n_logs_dl} freshly downloaded, {n_logs_cache} reused from cache, "
          f"{n_logs_err} still failing (out of {len(log_results)}). Opponent logs were never requested "
          f"(known 403, not retried). **measured**\n")

md.append("## 3. Ranks 7-12 report\n")
md.append("See the companion report for that deliverable (built in the same run) — path given in the "
           "final summary to the user.\n")

md.append("## 4. W-L-T, bands, families, tape near-ties\n")
for disp, s in summary.items():
    md.append(f"### {disp}\n")
    md.append(f"- Record: **{s['wins']}-{s['losses']}-{s['ties']}** (n={s['n']}). **measured**\n")
    md.append("**By opponent rating band** (opponent's current leaderboard rating, snapshot "
               "2026-09-24T16:13:50Z — NOT the opponent's rating at the time of that specific episode; "
               "see note below). **measured, with that caveat**\n")
    md.append(fmt_band_table(s['by_band']))
    md.append("")
    md.append("**By opponent family** (opening-fingerprint classification, this session). **measured**\n")
    md.append(fmt_family_table(s['by_family']))
    md.append("")
    if s['tape_n']:
        md.append(f"Against tape-family opponents (n={s['tape_n']}): {s['tape_near_ties_lt500']} games "
                   f"with |margin| < 500; median margin overall {s['tape_median_margin']:+.0f}. **measured**\n")
    else:
        md.append("No tape-family opponents encountered in this sample. **measured**\n")

md.append("## 5. W3 losses vs opponents rated above 2,500\n")
if w3_loss:
    md.append(f"n = {w3_loss['n_losses']} such losses. **measured**\n")
    md.append("| Episode | Opponent | Opp. rating | Our bank | Opp. bank | Day opp. led by >3,000 |")
    md.append("|---|---|---|---|---|---|")
    for L in w3_loss['losses']:
        dl = L['day_opp_led_by_3000'] or {}
        day = dl.get('day')
        md.append(f"| {L['episode_id']} | {L['opponent']} | {L['opponent_rating']} | {L['our_bank']} | "
                   f"{L['opp_bank']} | {day if day is not None else 'never'} |")
    md.append("")
    md.append("**Three products where W3 lost the most revenue** (sum of SELL revenue across these losses, "
               "W3 minus opponent; most negative = biggest deficit). **measured via `resim_trades.py`**\n")
    top3 = w3_loss['product_delta_ranked'][:3]
    md.append("| Product | Revenue delta (W3 - opp) | W3 revenue | Opp revenue |")
    md.append("|---|---|---|---|")
    for item, delta in top3:
        md.append(f"| {item} | {delta:+.0f} | {w3_loss['product_revenue_us'].get(item,0):.0f} | "
                   f"{w3_loss['product_revenue_opp'].get(item,0):.0f} |")
else:
    md.append("(not yet computed)")

open(os.path.join(d, '_section_draft.md'), 'w').write("\n".join(md))
print("wrote _section_draft.md")
