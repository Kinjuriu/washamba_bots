"""Cross-team opening clade map: one 0-71 tape per team's CURRENT submission,
pairwise agreement matrix, to see whether teams converged on a shared
public opening (e.g. the "2945 Farm" / Thomas Tschinkel hybrid)."""
import sys, json, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import copyability as cp

idx = json.load(open("experiments/endgame/episode_agents_index.json"))

# (label, submissionId, episode_id) - one current-sub episode per team
SOURCES = {
    "OUR_nf_trim": (None, None),  # special-cased below via our_opening.json
    "DSM": (56401245, 111578349),
    "Majkel1337": (56407295, 111579475),
    "VadimVasilenko": (56396983, 111577253),
    "THIRD_FARM_CLUB_cur": (56372014, 111048227),
    "SpaTaro_cur": (56384319, 111372877),
    "ymg_aq_cur": (56393666, 111343131),
    "UnknownMotherGoose_cur": (56417993, 111571696),
    "OrbitalTerraformer": (56212726, 111577258),
    "OtterVibe_cur": (56328447, 110853710),
    "ThomasTschinkel_2945Farm": (56269928, 109856068),
}

tapes = {}
our_opening = json.load(open("experiments/endgame/our_opening.json"))
tapes["OUR_nf_trim"] = [json.dumps(a, sort_keys=True, separators=(",", ":")) for a in our_opening][:72]

for label, (sub, eid) in SOURCES.items():
    if label == "OUR_nf_trim":
        continue
    meta = idx.get(str(eid))
    rep = cp.load_replay(eid)
    steps = rep["steps"]
    if meta is None:
        print(label, "no ListEpisodes record for", eid, "- using TeamNames fallback")
        seat = None
    else:
        agents = meta["agents"]
        mine = [a for a in agents if a.get("submissionId") == sub]
        m = mine[0] if mine else None
        seat = None
        if m and m.get("reward") is not None:
            for s in (0, 1):
                fr = steps[-1][s].get("reward")
                if fr is not None and abs(fr - m["reward"]) < 2:
                    seat = s
                    break
    if seat is None:
        print(label, eid, "SEAT UNRESOLVED - skipping")
        continue
    tape = cp.extract_tape(rep, seat)[:72]
    tapes[label] = tape
    print(label, "sub", sub, "ep", eid, "seat", seat, "len", len(tape))

labels = list(tapes.keys())
print("\n=== pairwise 0-71 agreement matrix ===")
print("%30s" % "", *["%10s" % l[:10] for l in labels])
mat = {}
for a in labels:
    row = []
    for b in labels:
        ag = cp.agreement(tapes[a], tapes[b], 0, 72)
        row.append(ag)
    mat[a] = row
    print("%30s" % a, *["%10.2f" % v if v is not None else "%10s" % "NA" for v in row])

json.dump({"labels": labels, "matrix": mat}, open("experiments/endgame/clade_matrix.json", "w"), indent=1)
print("\nWROTE experiments/endgame/clade_matrix.json")
