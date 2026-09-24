"""Run T4 copyability analysis over the downloaded panel_plan.json replays.

For each team: load up to 15 of its most recent locally-known episodes,
verify seat via the ListEpisodes agent record (reward match, cross-checked
against info.TeamNames), extract the canonical tape, compute shop keys at
72/144, pairwise agreement within same-key episode groups over the four
windows, and the 0-71 opening agreement against our own
router_yuan_nf_trim opening tape.

clade.py (referenced by experiments/tapes/harvest_lineage.py) is not present
in this checkout, so canon()/norm_action() are reimplemented here, matching
the inline `c()` helper in experiments/tapes/make_whole.py.
"""
import json
import os

from copyability import S, REP, PANEL, load_replay, extract_tape, agreement, key72, key144

os.makedirs(PANEL, exist_ok=True)

plan = json.load(open(os.path.join(S, "panel_plan.json")))
ep_agents = json.load(open(os.path.join(S, "episode_agents_index.json")))
our_opening = json.load(open(os.path.join(S, "our_opening.json")))
our_opening_c = [json.dumps(a, sort_keys=True, separators=(",", ":")) for a in our_opening]

LATEST_SUB = {  # today's actual latest submission id per team, from the crawl
    "DSM": 56401245, "Majkel1337": 56407295, "VadimVasilenko": 56396983,
    "THIRD_FARM_CLUB": 56372014, "UnknownMotherGoose": 56417993,
    "SpaTaro": 56384319, "ymg_aq": 56393666, "OrbitalTerraformer": 56212726,
    "KawattaTaido": None, "OtterVibe": 56328447,
    "ThomasTschinkel_2945Farm": 56269928,
}

index = {}
results = {}

for label, d in plan.items():
    if not d:
        results[label] = {"error": "no episodes reachable within budget"}
        continue
    sub = d["sub"]
    is_latest = (sub == LATEST_SUB.get(label))
    rows = []
    for eid, endtime in d["episodes"]:
        p = os.path.join(REP, f"{eid}.json")
        meta = ep_agents.get(str(eid)) or ep_agents.get(eid)
        if not os.path.exists(p) or os.path.getsize(p) < 1000:
            rows.append({"episode": eid, "error": "not downloaded"})
            continue
        if meta is None:
            rows.append({"episode": eid, "error": "no ListEpisodes agent record"})
            continue
        agents = meta["agents"]
        mine = [a for a in agents if a.get("submissionId") == sub]
        opp = [a for a in agents if a.get("submissionId") != sub]
        if not mine or not opp:
            rows.append({"episode": eid, "error": "sub not in agent record"})
            continue
        m, o = mine[0], opp[0]
        try:
            rep = load_replay(eid)
        except Exception as e:
            rows.append({"episode": eid, "error": f"load fail {e}"})
            continue
        steps = rep["steps"]
        if len(steps) < 720:
            rows.append({"episode": eid, "error": f"short replay len={len(steps)} (crash/timeout, not a full tape)"})
            continue
        final_rewards = [steps[-1][s].get("reward") for s in (0, 1)]
        # seat = index whose final reward matches the ListEpisodes record for `sub`
        seat = None
        if m.get("reward") is not None:
            for s in (0, 1):
                if final_rewards[s] is not None and abs(final_rewards[s] - m["reward"]) < 2:
                    seat = s
                    break
        if seat is None:
            rows.append({"episode": eid, "error": f"seat unresolved, rewards={final_rewards} vs record={m.get('reward')}"})
            continue
        opp_seat = 1 - seat
        tape = extract_tape(rep, seat)
        opp_tape = extract_tape(rep, opp_seat)
        k72v = key72(rep)
        k144v = key144(rep)
        cfg_seed = (rep.get("configuration") or {}).get("seed")
        info_seed = (rep.get("info") or {}).get("seed")
        seed = cfg_seed if cfg_seed is not None else info_seed
        seed_src = "configuration.seed" if cfg_seed is not None else "info.seed"
        ag_open = agreement(tape, our_opening_c, 0, 72)
        row = {
            "episode": eid, "seat": seat, "endTime": endtime,
            "key72": k72v, "key144": k144v, "seed": seed, "seed_src": seed_src,
            "reward": m.get("reward"), "opp_sub": o.get("submissionId"),
            "opp_team": o.get("teamId"), "opp_rating": o.get("updatedScore"),
            "opp_reward": o.get("reward"),
            "ag_open_vs_ours": ag_open,
        }
        rows.append(row)
        out_path = os.path.join(PANEL, f"{eid}_{seat}.json")
        json.dump(tape, open(out_path, "w"))
        opp_path = os.path.join(PANEL, f"{eid}_{opp_seat}.json")
        json.dump(opp_tape, open(opp_path, "w"))

        def upsert(fname, entry):
            # Two top teams can meet each other's episode: never let a
            # write from the *other* team's loop (is_top_team=False, i.e.
            # this team seen only as someone else's opponent) clobber an
            # entry already established as that team's own (is_top_team=True).
            existing = index.get(fname)
            if existing and existing.get("is_top_team") and not entry.get("is_top_team"):
                return
            if existing:
                existing.update({k: v for k, v in entry.items() if v is not None})
            else:
                index[fname] = entry

        upsert(os.path.basename(out_path), {
            "seed": seed, "seed_src": seed_src, "team": label, "sub": sub,
            "rating": m.get("updatedScore"), "reward": m.get("reward"),
            "opp_sub": o.get("submissionId"), "opp_team_id": o.get("teamId"),
            "opp_rating": o.get("updatedScore"), "opp_reward": o.get("reward"),
            "key72": k72v, "key144": k144v, "is_top_team": True,
        })
        upsert(os.path.basename(opp_path), {
            "seed": seed, "seed_src": seed_src, "team_id": o.get("teamId"),
            "sub": o.get("submissionId"), "rating": o.get("updatedScore"),
            "reward": o.get("reward"), "opp_team": label, "opp_sub": sub,
            "opp_rating": m.get("updatedScore"), "opp_reward": m.get("reward"),
            "key72": k72v, "key144": k144v, "is_top_team": False,
        })

    valid = [r for r in rows if "error" not in r]
    pairs = []
    for i in range(len(valid)):
        for j in range(i + 1, len(valid)):
            a, b = valid[i], valid[j]
            ta = json.load(open(os.path.join(PANEL, f"{a['episode']}_{a['seat']}.json")))
            tb = json.load(open(os.path.join(PANEL, f"{b['episode']}_{b['seat']}.json")))
            same72 = a["key72"] == b["key72"] and a["key72"] != ""
            same144 = a["key144"] == b["key144"] and a["key144"] != ""
            pair = {
                "eps": (a["episode"], b["episode"]),
                "same_key72": same72, "same_key144": same144,
                "key72_a": a["key72"], "key72_b": b["key72"],
                "key144_a": a["key144"], "key144_b": b["key144"],
                "ag_0_71": agreement(ta, tb, 0, 72),
            }
            pair["ag_72_143"] = agreement(ta, tb, 72, 144)
            if same144:
                pair["ag_144_400"] = agreement(ta, tb, 144, 400)
                pair["ag_400_718"] = agreement(ta, tb, 400, 719)
                a144, a718 = pair["ag_144_400"], pair["ag_400_718"]
                pair["hybrid_shape"] = bool(a144 is not None and a718 is not None and a144 >= 0.9 and a718 <= 0.5)
            pairs.append(pair)

    def mean(xs):
        xs = [x for x in xs if x is not None]
        return sum(xs) / len(xs) if xs else None

    same72_pairs = [p for p in pairs if p["same_key72"]]
    diff72_pairs = [p for p in pairs if not p["same_key72"]]
    same144_pairs = [p for p in pairs if p["same_key144"]]
    own_open_ag = mean(p["ag_0_71"] for p in pairs)  # own-tape internal opening consistency

    results[label] = {
        "sub_used": sub, "is_latest_sub": is_latest,
        "latest_sub_known": LATEST_SUB.get(label),
        "n_subs_seen": d.get("n_subs_seen"),
        "rows": rows, "pairs": pairs,
        "n_valid": len(valid), "n_errors": len(rows) - len(valid),
        "own_opening_pairwise_agreement": own_open_ag,
        "same_key72_ag_72_143_mean": mean(p["ag_72_143"] for p in same72_pairs),
        "diff_key72_ag_72_143_mean": mean(p["ag_72_143"] for p in diff72_pairs),
        "n_same_key72_pairs": len(same72_pairs), "n_diff_key72_pairs": len(diff72_pairs),
        "n_same_key144_pairs": len(same144_pairs),
        "same_key144_ag_144_400_mean": mean(p.get("ag_144_400") for p in same144_pairs),
        "same_key144_ag_400_718_mean": mean(p.get("ag_400_718") for p in same144_pairs),
        "any_hybrid_shape": any(p.get("hybrid_shape") for p in same144_pairs),
    }
    print(f"=== {label} (sub {sub}, is_latest={is_latest}) valid={len(valid)}/{len(rows)} ===")
    print(f"   own-opening pairwise ag: {own_open_ag}")
    print(f"   same-key72 ag(72-143) mean: {results[label]['same_key72_ag_72_143_mean']} (n={len(same72_pairs)})"
          f"  vs diff-key72: {results[label]['diff_key72_ag_72_143_mean']} (n={len(diff72_pairs)})")
    print(f"   same-key144 pairs: {len(same144_pairs)} / {len(pairs)} total pairs")
    for p in same144_pairs:
        print("   ", p["eps"], "ag144-400=", p.get("ag_144_400"), "ag400-718=", p.get("ag_400_718"), "hybrid=", p.get("hybrid_shape"))

json.dump(results, open(os.path.join(S, "copyability_results.json"), "w"), indent=1)
json.dump(index, open(os.path.join(PANEL, "index.json"), "w"), indent=1)
print("\nWROTE", os.path.join(S, "copyability_results.json"))
print("WROTE", os.path.join(PANEL, "index.json"), "entries:", len(index))
