"""Download, cache and parse a Kaggle episode replay.

WHERE THE SEED LIVES. `resolve_episode_seed` (kaggle_environments/utils.py:199)
takes the seed from `env.info["seed"]`, else `configuration["seed"]`, else a
random 31-bit int - and then *scrubs it out of the configuration* so agents
cannot read it from the observation, storing it on `env.info["seed"]` "so it
persists into the replay". So in a downloaded replay:

    configuration.seed  ->  ALWAYS null   (scrubbed, by design)
    info.seed           ->  the real seed (e.g. 116495659)

Feeding that value back as `configuration={'seed': N}` on a fresh env is
equivalent, because `env.info["seed"]` is empty on a fresh env and the config
value is then promoted to it. The engine's only seeded RNG is
`random.Random((seed * 1_000_003) ^ day)` in `_end_of_day`
(kaggriculture.py:871) - weed spawns and shop unlocks - so seed + both action
streams fully determine an episode.

INDEX CONVENTION. `steps[i][seat]["action"]` is the action the agent returned
*from* `steps[i-1]`'s observation. `tape(seat)[k]` is therefore the action
taken at observation step k (= day*24 + hour), i.e. `steps[k+1][seat].action`.
The last entry (k = 719) is None: no action follows the final observation.
"""

from __future__ import annotations

import json
import os
import urllib.request
from dataclasses import dataclass, field

HERE = os.path.dirname(os.path.abspath(__file__))
REP_DIR = os.path.join(HERE, "rep")
EPISODE_URL = "https://www.kaggleusercontent.com/episodes/{eid}.json"
UA = {"User-Agent": "washamba-endgame/1.0"}

# Which agent file played which submission id. Used by ladder_replay to seat
# our recorded agent; keep in sync when new submissions enter the harness.
SUBMISSION_AGENT = {
    56202213: "agents/router_yuan_nf.py",
    56202203: "agents/router_yuan_nf_trim.py",
}
OUR_TEAM = "washamba_bots"

PASS_ACTION = {"farmer": ["PASS"], "hands": [], "market": []}


def download(episode_id: int, timeout: int = 180) -> str:
    """Return a path to the cached replay JSON, downloading it if needed."""
    os.makedirs(REP_DIR, exist_ok=True)
    path = os.path.join(REP_DIR, "%d.json" % int(episode_id))
    if os.path.exists(path) and os.path.getsize(path) > 1000:
        return path
    req = urllib.request.Request(EPISODE_URL.format(eid=int(episode_id)), headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as h:
        blob = h.read()
    tmp = path + ".part"
    with open(tmp, "wb") as f:
        f.write(blob)
    os.replace(tmp, path)
    return path


@dataclass
class Replay:
    episode_id: int
    seed: int
    seed_source: str
    steps: list
    agents: list  # [{seat, submissionId, reward, team, status}]
    statuses: list
    module_version: str = ""
    configuration: dict = field(default_factory=dict)

    def tape(self, seat: int) -> list:
        """720 actions; entry k is the action taken at observation step k."""
        out = [self.steps[i][seat].get("action") for i in range(1, len(self.steps))]
        out.append(None)  # nothing follows the final observation
        return out

    def our_seat(self) -> int:
        for a in self.agents:
            if a["team"] == OUR_TEAM:
                return a["seat"]
        raise KeyError("no %s seat in episode %s" % (OUR_TEAM, self.episode_id))

    def reward(self, seat: int):
        return self.agents[seat]["reward"]

    def observation(self, step: int, seat: int = 0) -> dict:
        return self.steps[step][seat].get("observation") or {}


def _unwrap(raw: dict) -> dict:
    """The host serves the replay bare; some dumps wrap it in a `replay` field
    that is itself either a JSON string or a dict."""
    rep = raw.get("replay")
    if isinstance(rep, str):
        return json.loads(rep)
    if isinstance(rep, dict):
        return rep
    return raw


def parse(path: str, listing_index: dict | None = None) -> Replay:
    with open(path, encoding="utf-8") as f:
        rep = _unwrap(json.load(f))
    info = rep.get("info") or {}
    cfg = rep.get("configuration") or {}

    seed, src = cfg.get("seed"), "configuration.seed"
    if seed is None:
        seed, src = info.get("seed"), "info.seed"
    if seed is None:
        raise ValueError("no seed in %s (checked configuration.seed, info.seed)" % path)

    steps = rep["steps"]
    teams = list(info.get("TeamNames") or [])
    statuses = list(rep.get("statuses") or [])
    rewards = rep.get("rewards") or [steps[-1][s].get("reward") for s in range(len(steps[-1]))]

    # The replay itself carries no submission ids - only info.TeamNames. Join
    # on info.EpisodeId against the cached ListEpisodes dumps to fill them in;
    # None when the episode is not in the cache.
    eid = int(info.get("EpisodeId") or 0)
    listing = (listing_index if listing_index is not None else load_episode_listing()).get(eid)
    subs = [None, None]
    if listing:
        subs[listing["seat"]] = listing["submission"]
        subs[1 - listing["seat"]] = listing["opp_submission"]

    agents = []
    for seat in range(len(steps[-1])):
        agents.append({
            "seat": seat,
            "submissionId": subs[seat] if seat < len(subs) else None,
            "reward": rewards[seat] if seat < len(rewards) else None,
            "team": teams[seat] if seat < len(teams) else "",
            "status": statuses[seat] if seat < len(statuses) else "",
        })
    return Replay(
        # top-level `id` is a run uuid, not the episode id - that is info.EpisodeId
        episode_id=eid,
        seed=int(seed),
        seed_source=src,
        steps=steps,
        agents=agents,
        statuses=statuses,
        module_version=str(rep.get("module_version") or ""),
        configuration=cfg,
    )


# ---------------------------------------------------------------- listings

def load_episode_listing(submission_ids=SUBMISSION_AGENT.keys()) -> dict:
    """{episode_id: row} from the cached ListEpisodes dumps.

    Seat comes from the ListEpisodes `index` field, which is *absent* for
    seat 0 (protobuf default), not zero. Reward-matching against the replay is
    the cross-check, not the primary source.
    """
    index = {}
    for sid in submission_ids:
        path = os.path.join(HERE, "episodes_%d.json" % int(sid))
        if not os.path.exists(path):
            continue
        for ep in json.load(open(path, encoding="utf-8")):
            if ep.get("state") != "COMPLETED":
                continue
            mine = [a for a in ep["agents"] if a.get("submissionId") == int(sid)]
            opp = [a for a in ep["agents"] if a.get("submissionId") != int(sid)]
            if not mine or not opp or mine[0].get("reward") is None:
                continue
            m, o = mine[0], opp[0]
            index[int(ep["id"])] = {
                "episode": int(ep["id"]),
                "submission": int(sid),
                "agent_file": SUBMISSION_AGENT[int(sid)],
                "seat": int(m.get("index", 0) or 0),
                "recorded": m["reward"],
                "opp_recorded": o.get("reward"),
                "opp_submission": o.get("submissionId"),
                "opp_rating": o.get("initialScore"),
                "end_time": ep["endTime"],
                "win": bool(m["reward"] > (o.get("reward") or 0)),
            }
    return index


# ---------------------------------------------------------- farm inspection

def structure_counts(obs: dict, player: int) -> dict:
    """{structures, filled} for a farm: PASTURE/COOP tiles and how many hold
    an animal (`"animal" in tile`, per kaggriculture.py:488)."""
    farms = obs.get("farms") or []
    if player >= len(farms):
        return {"structures": 0, "filled": 0}
    total = filled = 0
    for row in (farms[player].get("tiles") or []):
        for tile in row:
            if isinstance(tile, dict) and tile.get("kind") in ("PASTURE", "COOP"):
                total += 1
                if "animal" in tile:
                    filled += 1
    return {"structures": total, "filled": filled}


def money(obs: dict, player: int):
    farms = obs.get("farms") or []
    return farms[player].get("money") if player < len(farms) else None
