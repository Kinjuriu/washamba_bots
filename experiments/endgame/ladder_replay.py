"""Replay our real ladder episodes locally, to the dollar.

WHY THIS EXISTS. The only harness we own with real, selling opponents is the
live ladder, and it is slow (~20 episodes per submission in the first two
hours, then a trickle) and noisy (two byte-identical submissions read 86
rating points apart). But our ladder episodes are *public replays*, the engine
is deterministic given `env.info["seed"]` and both action streams, and a
recorded opponent is a fixed tape. So: put the opponent's recorded tape in its
recorded seat on the recorded seed, put our real agent file in ours, and the
episode reproduces exactly. That turns ~500 real contested games into a
deterministic local test set.

    python experiments/endgame/ladder_replay.py gate          # the 30-episode gate
    python experiments/endgame/ladder_replay.py index         # write harness_index.json
    python experiments/endgame/ladder_replay.py run <cand.py> # candidate vs the harness

READ THE FLIPS, NOT THE MEAN. `run()` freezes the opponent's tape. The moment
our candidate diverges, the recorded opponent is playing a schedule it would
not have played against the new us - it cannot respond to our prices, our
sells, our land. Mean bank delta here is therefore an UPPER BOUND on a real
gain. The trustworthy signal is direction: which recorded losses flip to wins,
and - the hard gate - whether any recorded win flips to a loss.
"""

from __future__ import annotations

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from experiments.endgame import make_tape_agent, replay_tools  # noqa: E402

INDEX_PATH = os.path.join(HERE, "harness_index.json")
DAY_PROBES = (6, 12)


def _episode_rows():
    return replay_tools.load_episode_listing()


def _opponent_agent_path(rep: replay_tools.Replay, opp_seat: int) -> str:
    out = os.path.join(replay_tools.REP_DIR, "opp_%d_%d.py" % (rep.episode_id, opp_seat))
    if os.path.exists(out):
        return out
    header = (
        "Opponent tape harvested from ladder episode %d, seat %d (seed %d,\n"
        "recorded bank %s). Generated for the replay harness; never submitted."
        % (rep.episode_id, opp_seat, rep.seed, rep.reward(opp_seat))
    )
    make_tape_agent.write(rep.tape(opp_seat), out, header)
    return out


def _play(seed: int, files: list):
    from kaggle_environments import make

    env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": int(seed)})
    env.run(files)
    last = env.steps[-1]
    rewards = [s["reward"] for s in last]
    statuses = [s["status"] for s in last]
    return env, rewards, statuses


def _local_tape(env, seat: int) -> list:
    out = [env.steps[i][seat].get("action") for i in range(1, len(env.steps))]
    out.append(None)
    return out


def _first_divergence(a: list, b: list):
    n = min(len(a), len(b))
    for i in range(n):
        if make_tape_agent.normalise(a[i]) != make_tape_agent.normalise(b[i]):
            return i
    return None


def reproduce(episode_id: int, rows=None, verbose: bool = False) -> dict:
    """Replay one recorded episode with our recorded agent file in our seat.

    Returns recorded vs replayed bank for BOTH seats plus `ok` (both within $1).
    """
    rows = rows if rows is not None else _episode_rows()
    row = rows.get(int(episode_id))
    if row is None:
        raise KeyError("episode %s not in the cached ListEpisodes dumps" % episode_id)

    rep = replay_tools.parse(replay_tools.download(episode_id))
    seat = row["seat"]
    # Cross-check the ListEpisodes `index` against the replay's own rewards and
    # team names: a silently wrong seat reproduces nothing and looks like a
    # seed bug.
    by_reward = [s for s in range(len(rep.agents))
                 if abs((rep.reward(s) or 0) - row["recorded"]) < 1.0]
    seat_checks = {
        "listing_index": seat,
        "by_reward": by_reward,
        "by_team": [a["seat"] for a in rep.agents if a["team"] == replay_tools.OUR_TEAM],
    }
    opp_seat = 1 - seat

    files = [None, None]
    files[seat] = os.path.join(ROOT, row["agent_file"])
    files[opp_seat] = _opponent_agent_path(rep, opp_seat)

    env, rewards, statuses = _play(rep.seed, files)

    ours_rec, ours_new = row["recorded"], rewards[seat]
    opp_rec, opp_new = rep.reward(opp_seat), rewards[opp_seat]
    d_ours = abs((ours_new or 0) - (ours_rec or 0))
    d_opp = abs((opp_new or 0) - (opp_rec or 0))

    out = {
        "episode": int(episode_id),
        "seed": rep.seed,
        "seed_source": rep.seed_source,
        "seat": seat,
        "seat_checks": seat_checks,
        "agent_file": row["agent_file"],
        "recorded_bank": ours_rec,
        "replayed_bank": ours_new,
        "opp_recorded_bank": opp_rec,
        "opp_replayed_bank": opp_new,
        "delta": (ours_new or 0) - (ours_rec or 0),
        "opp_delta": (opp_new or 0) - (opp_rec or 0),
        "statuses": statuses,
        "recorded_statuses": rep.statuses,
        "ok": d_ours <= 1.0 and d_opp <= 1.0,
        "win": row["win"],
        "module_version": rep.module_version,
    }
    if not out["ok"]:
        # Localise: an index bug diverges at step 0-1, a seed bug at a day
        # boundary, a seat bug everywhere, an encoding bug at one order type.
        out["first_action_divergence"] = _first_divergence(
            _local_tape(env, seat), rep.tape(seat))
        out["first_opp_divergence"] = _first_divergence(
            _local_tape(env, opp_seat), rep.tape(opp_seat))
    if 3000 in (ours_new, opp_new):
        out["flag_3000"] = True
    if verbose:
        print(json.dumps({k: v for k, v in out.items() if k != "seat_checks"}), flush=True)
    return out


def run(candidate_path: str, episode_ids, rows=None) -> list:
    """Replace our agent with `candidate_path` in our recorded seat.

    Upper bound, not a prediction - see the module docstring. Per episode:
    recorded/candidate bank, the frozen opponent's bank, whether the result
    flipped, and the first step at which the candidate's actions diverge from
    ours (0 differences means the candidate is a literal no-op on that seed).
    """
    rows = rows if rows is not None else _episode_rows()
    out = []
    for eid in episode_ids:
        row = rows[int(eid)]
        rep = replay_tools.parse(replay_tools.download(eid))
        seat, opp_seat = row["seat"], 1 - row["seat"]
        files = [None, None]
        files[seat] = os.path.abspath(candidate_path)
        files[opp_seat] = _opponent_agent_path(rep, opp_seat)
        env, rewards, statuses = _play(rep.seed, files)

        cand, opp = rewards[seat], rewards[opp_seat]
        won_before = row["win"]
        won_after = (cand or 0) > (opp or 0)
        out.append({
            "episode": int(eid),
            "seat": seat,
            "seed": rep.seed,
            "recorded": row["recorded"],
            "candidate_bank": cand,
            "opp_bank": opp,
            "opp_recorded": rep.reward(opp_seat),
            "delta": (cand or 0) - (row["recorded"] or 0),
            "won_before": won_before,
            "won_after": won_after,
            "flipped": ("loss->win" if (won_after and not won_before)
                        else "win->loss" if (won_before and not won_after) else ""),
            "first_divergence": _first_divergence(_local_tape(env, seat), rep.tape(seat)),
            "statuses": statuses,
            "flag_3000": 3000 in (cand, opp),
        })
        print(json.dumps(out[-1]), flush=True)
    return out


def summarise_run(results: list) -> dict:
    flips_up = [r for r in results if r["flipped"] == "loss->win"]
    flips_down = [r for r in results if r["flipped"] == "win->loss"]
    diverged = [r for r in results if r["first_divergence"] is not None]
    n = len(results) or 1
    return {
        "episodes": len(results),
        "loss_to_win": len(flips_up),
        "win_to_loss": len(flips_down),
        "mean_delta": sum(r["delta"] for r in results) / n,
        "diverged_at_all": len(diverged),
        "diverged_episodes": [(r["episode"], r["first_divergence"]) for r in diverged],
    }


# ------------------------------------------------------------- harness index

def build_index(episode_ids, rows=None, path: str = INDEX_PATH) -> list:
    """Recorded facts the repair task (T5) needs, from the recorded observations
    of our seat: bank, seat, seed, win/loss, and how many PASTURE/COOP
    structures exist and how many hold an animal at day 6, day 12 and end.

    Day d is probed at `steps[d*24]` - the first observation of day d, i.e.
    AFTER night d-1's `_end_of_day`, which is where an unfed animal escapes.
    """
    rows = rows if rows is not None else _episode_rows()
    out = []
    for eid in episode_ids:
        row = rows[int(eid)]
        rep = replay_tools.parse(replay_tools.download(eid))
        seat = row["seat"]
        rec = dict(row)
        rec["seed"] = rep.seed
        rec["seed_source"] = rep.seed_source
        rec["recorded_statuses"] = rep.statuses
        for d in DAY_PROBES:
            i = min(d * 24, len(rep.steps) - 1)
            obs = rep.observation(i, 0)
            rec["day%d" % d] = replay_tools.structure_counts(obs, seat)
            rec["day%d" % d]["money"] = replay_tools.money(obs, seat)
        obs = rep.observation(len(rep.steps) - 1, 0)
        rec["end"] = replay_tools.structure_counts(obs, seat)
        rec["end"]["money"] = replay_tools.money(obs, seat)
        rec["empty_structure_at_end"] = rec["end"]["structures"] - rec["end"]["filled"]
        out.append(rec)
    out.sort(key=lambda r: r["end_time"])
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1)
    return out


def pick_harness(n: int = 30, rows=None) -> list:
    """The n most recent completed episodes across both submissions, balanced
    as near 50/50 wins/losses as the tail allows."""
    rows = rows if rows is not None else _episode_rows()
    ordered = sorted(rows.values(), key=lambda r: r["end_time"], reverse=True)
    half = n // 2
    wins = [r["episode"] for r in ordered if r["win"]][:half]
    losses = [r["episode"] for r in ordered if not r["win"]][:n - half]
    picked = wins + losses
    if len(picked) < n:
        for r in ordered:
            if r["episode"] not in picked:
                picked.append(r["episode"])
            if len(picked) >= n:
                break
    order = {r["episode"]: i for i, r in enumerate(ordered)}
    return sorted(picked[:n], key=lambda e: order[e])


def _main(argv):
    cmd = argv[1] if len(argv) > 1 else "gate"
    rows = _episode_rows()
    if cmd == "gate":
        n = int(argv[2]) if len(argv) > 2 else 30
        ids = pick_harness(n, rows)
        res = [reproduce(e, rows, verbose=True) for e in ids]
        ok = sum(1 for r in res if r["ok"])
        print("\nGATE %d/%d within $1 on both seats" % (ok, len(res)))
        with open(os.path.join(HERE, "gate_results.json"), "w") as f:
            json.dump(res, f, indent=1)
    elif cmd == "index":
        ids = [r["episode"] for r in json.load(open(os.path.join(HERE, "gate_results.json")))] \
            if os.path.exists(os.path.join(HERE, "gate_results.json")) else pick_harness(30, rows)
        rec = build_index(ids, rows)
        print("wrote %s (%d episodes)" % (INDEX_PATH, len(rec)))
    elif cmd == "run":
        cand = argv[2]
        ids = [int(x) for x in argv[3:]] or pick_harness(30, rows)
        res = run(cand, ids, rows)
        print(json.dumps(summarise_run(res), indent=1))
    else:
        raise SystemExit(__doc__)


if __name__ == "__main__":
    _main(sys.argv)
