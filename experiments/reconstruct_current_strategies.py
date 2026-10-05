#!/usr/bin/env python3
"""
Reconstruct the complete strategies used by the current top-five
Kaggriculture ladder leaders, from the replay corpus `pull_episodes.py`
downloaded to ~/KagricultureLocalData/episodes/.

This is RECONSTRUCTION, not a benchmark. Everything this script reports is
a descriptive observation of a fixed set of already-played ladder games -
win rates and bank figures here are ladder observations, not causal claims
and not a local benchmark. The live Kaggle ladder is the only competitive
benchmark; local execution (this script included) is for reconstruction,
debugging, and sanity-checking only.

REPLAY ALIGNMENT - verified against the installed engine, not assumed.
At replay row i, steps[i][seat]["observation"] and steps[i][seat]["action"]
are the SAME turn: the action a seat emitted in response to that
observation, stored at the same index. There is no "row 0 is a
placeholder" and no t -> t+1 shift. Verified two ways:
  1. A local env.run() episode: row 0's action is a real emitted action
     (not a placeholder), and observation.step == row index at every row.
  2. The repo's own existing replay tools (experiments/replay_shape.py,
     experiments/opening_trace.py) already read observation and action
     from the same `steps[i][player]` dict, with no offset.
`tests/test_reconstruct_current_strategies.py` proves this against a real
engine-produced episode, not a fabricated one.

Consequence for the five-window agreement split this script reports: the
requested "288-718" final window is one turn short of the real remainder
(a 720-step episode has valid turns 0..719 under this verified alignment).
This script uses 288-719 and documents that difference in the report
rather than silently truncating turn 719 to match an unverified premise.

Inputs (read-only - never written to):
    ~/KagricultureLocalData/episodes/manifest.csv
    ~/KagricultureLocalData/episodes/replays/<episode_id>.json.gz

Outputs, all OUTSIDE the repository:
    ~/KagricultureLocalData/episodes/reconstructed_strategies/
        target_trajectories.csv
        route_families.csv
        checkpoint_states.jsonl
        route_library.json.gz
        family_membership.csv
        strategy_reconstruction_report.md
        trajectory_action_streams.jsonl.gz   (extra - see report: full
            per-trajectory action tapes, required by "preserve the
            complete emitted action stream" but too large for a CSV cell
            and not itself one of the six named deliverables)

Run:
    python experiments/reconstruct_current_strategies.py
"""

import csv
import gzip
import hashlib
import json
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field, asdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from pull_episodes import validate_replay_structure  # noqa: E402

DATA_DIR = Path.home() / "KagricultureLocalData" / "episodes"
MANIFEST_PATH = DATA_DIR / "manifest.csv"
REPLAY_DIR = DATA_DIR / "replays"
LIBRARY_DIR = DATA_DIR / "reconstructed_strategies"

TURNS_PER_EPISODE = 720
CHECKPOINTS = (72, 144, 216, 288)
SUFFIX_POINTS = (144, 216, 288)
# (start, end_inclusive, label) - see the alignment note above for why the
# final window ends at 719, not the requested-but-unverified 718.
AGREEMENT_WINDOWS = [
    (0, 71, "turns_0_71"),
    (72, 143, "turns_72_143"),
    (144, 215, "turns_144_215"),
    (216, 287, "turns_216_287"),
    (288, TURNS_PER_EPISODE - 1, "turns_288_719"),
]
AGREEMENT_THRESHOLDS = (0.99, 0.95)

TILE_KIND_PLANT = "PLANT"
TILE_KIND_WEED = "WEED"
TILE_KIND_PASTURE = "PASTURE"


# ---------------------------------------------------------------------------
# Canonical hashing - stable regardless of dict key ordering.
# ---------------------------------------------------------------------------
def canonical_bytes(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"),
                       default=str).encode("utf-8")


def sha256_hex(data_bytes):
    return hashlib.sha256(data_bytes).hexdigest()


def turn_digest(action):
    """8-byte stable digest of one turn's action dict, used for fast
    per-turn equality comparison across trajectories."""
    return hashlib.blake2b(canonical_bytes(action), digest_size=8).digest()


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


# ---------------------------------------------------------------------------
# Manifest
# ---------------------------------------------------------------------------
def load_manifest(path=MANIFEST_PATH):
    with open(path, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    for r in rows:
        r["episode_id"] = int(r["episode_id"])
        r["player_seat"] = int(r["player_seat"]) if r["player_seat"] not in (None, "") else None
        r["player_submission"] = int(r["player_submission"])
        r["player_bank"] = float(r["player_bank"]) if r["player_bank"] not in (None, "") else None
        r["opponent_bank"] = float(r["opponent_bank"]) if r["opponent_bank"] not in (None, "") else None
    return rows


# ---------------------------------------------------------------------------
# Replay loading
# ---------------------------------------------------------------------------
def load_replay(gz_path):
    with gzip.open(gz_path, "rt", encoding="utf-8") as fh:
        data = json.load(fh)
    ok, reason = validate_replay_structure(data)
    if not ok:
        raise ValueError(f"{gz_path.name}: failed structural validation ({reason})")
    return data


def extract_action_stream(replay, seat):
    """Same-index alignment: steps[i][seat]['action'] is the action emitted
    in response to steps[i][seat]['observation'], both at row i."""
    steps = replay["steps"]
    return [ (row[seat].get("action") if seat < len(row) else None) or {}
             for row in steps ]


# ---------------------------------------------------------------------------
# Checkpoint state extraction
# ---------------------------------------------------------------------------
def _tile_summary(tiles):
    plant_by_crop = Counter()
    animal_by_species = Counter()
    weeds = 0
    empty_pasture = 0
    for row in tiles:
        for t in row:
            if not isinstance(t, dict):
                continue
            kind = t.get("kind")
            if kind == TILE_KIND_PLANT:
                plant_by_crop[t.get("crop")] += 1
            elif kind == TILE_KIND_WEED:
                weeds += 1
            elif kind == TILE_KIND_PASTURE:
                animal = t.get("animal")
                if animal:
                    animal_by_species[animal] += 1
                else:
                    empty_pasture += 1
    return dict(plant_by_crop), dict(animal_by_species), weeds, empty_pasture


def extract_checkpoint_state(replay, seat, turn, cumulative_actions):
    """Live strategic state at `turn`, from the target seat's own
    observation row (private shed/seeds/carried inventory are only visible
    from the observing player's own perspective, which this is)."""
    steps = replay["steps"]
    if turn >= len(steps) or seat >= len(steps[turn]):
        return {"turn": turn, "available": False}

    obs = steps[turn][seat].get("observation") or {}
    farms = obs.get("farms") or []
    farm = farms[seat] if seat < len(farms) else {}
    private = obs.get("private") or {}
    town = obs.get("town") or {}
    market = obs.get("market") or {}

    plant_by_crop, animal_by_species, weeds, empty_pasture = ({}, {}, None, None)
    tiles = farm.get("tiles")
    if tiles:
        plant_by_crop, animal_by_species, weeds, empty_pasture = _tile_summary(tiles)

    shops_so_far = []
    for t in range(turn + 1):
        if t >= len(steps) or seat >= len(steps[t]):
            break
        u = ((steps[t][seat].get("observation") or {}).get("town") or {}).get("unlocked_shops") or []
        for s in u:
            if s not in shops_so_far:
                shops_so_far.append(s)

    hires_requested_so_far = sum(
        1 for a in cumulative_actions[:turn + 1]
        for o in (a.get("market") or [])
        if o and o[0] == "HIRE"
    )

    return {
        "turn": turn,
        "available": True,
        "day": obs.get("day"),
        "hour": obs.get("hour"),
        "money": farm.get("money"),
        "unlocked_quadrants": sorted(farm.get("unlocked_quadrants") or []),
        "n_hands": len(farm.get("hands") or []),
        "hires_today": farm.get("hires_today"),
        "hires_requested_cumulative": hires_requested_so_far,
        "unlocked_shops_in_order": shops_so_far,
        "animals_by_species": animal_by_species,
        "planted_by_crop": plant_by_crop,
        "weeds": weeds,
        "empty_pastures": empty_pasture,
        "shed": private.get("shed") or {},
        "seeds_held": private.get("seeds") or {},
        "carried_inventories": private.get("inventories"),
        "market_prices": market.get("prices"),
        "market_inventory": market.get("inventory"),
    }


def checkpoint_compat_key(state):
    """Coarse, honest compatibility signature: two checkpoints are
    'compatible' iff this key matches. Deliberately coarse - exact money
    or exact tile-by-tile layout would make every pair 'incompatible' and
    say nothing useful about whether a suffix could plausibly graft onto
    a different prefix."""
    if not state.get("available"):
        return None
    return (
        tuple(state["unlocked_quadrants"]),
        tuple(sorted(state["animals_by_species"].items())),
        _bucket(state["n_hands"], (0, 2, 4, 6, 9, 12, 16)),
        _bucket(state["hires_requested_cumulative"], (0, 5, 15, 30, 60, 100)),
        tuple(state["unlocked_shops_in_order"]),
        _bucket(sum(state["planted_by_crop"].values()), (0, 5, 10, 20, 35, 50)),
    )


def _bucket(value, edges):
    if value is None:
        return None
    for e in edges:
        if value <= e:
            return f"<={e}"
    return f">{edges[-1]}"


# ---------------------------------------------------------------------------
# Action summaries (requested_*) and observed_landed_* state evidence
# ---------------------------------------------------------------------------
def summarize_actions(actions, replay, seat):
    land_turns = []
    animal_events = []  # (turn, species)
    planting_turns = defaultdict(list)  # crop -> [turn,...]
    market_first_turn = {}  # order_type/product key -> first turn
    order_counts = Counter()
    farmer_action_counts = Counter()

    for t, a in enumerate(actions):
        for unit_action in [a.get("farmer")] + list(a.get("hands") or []):
            if unit_action:
                farmer_action_counts[unit_action[0]] += 1
                if unit_action[0] == "PLANT" and len(unit_action) > 1:
                    planting_turns[unit_action[1]].append(t)
        for order in (a.get("market") or []):
            if not order:
                continue
            order_counts[order[0]] += 1
            key = order[0] if len(order) < 2 else f"{order[0]}:{order[1]}"
            market_first_turn.setdefault(key, t)
            if order[0] == "BUY_LAND":
                land_turns.append(t)
            if order[0] == "BUY_ANIMAL" and len(order) > 1:
                animal_events.append((t, order[1]))

    steps = replay["steps"]
    max_hands = 0
    for t in range(len(steps)):
        if seat < len(steps[t]):
            farms = (steps[t][seat].get("observation") or {}).get("farms") or []
            if seat < len(farms):
                max_hands = max(max_hands, len(farms[seat].get("hands") or []))

    return {
        "land_purchase_turns": land_turns,
        "animal_purchase_events": animal_events,
        "workforce_max_hands_observed": max_hands,
        "planting_turns_by_crop": dict(planting_turns),
        "market_order_first_turn": market_first_turn,
        "market_order_counts": dict(order_counts),
        "farmer_action_counts": dict(farmer_action_counts),
    }


def state_transition_evidence(actions, replay, seat):
    """Separate requested_* (what was emitted) from observed_landed_*
    (what state evidence supports actually happened). Uses per-product
    shed deltas between consecutive turns as evidence a SELL/BUY_PRODUCT
    landed. This is a LOWER BOUND, not a precise reconstruction: a
    same-turn HARVEST/CARE production event for the same product can mask
    a landed sell by refilling the shed in the same turn. Turns with such
    a same-turn confound are marked 'unknown' rather than guessed."""
    steps = replay["steps"]
    requested_sell = []   # (turn, product, qty)
    requested_buy_product = []
    observed_landed_sell = []
    observed_landed_buy_product = []
    unknown_sell = []
    unknown_buy_product = []

    harvest_products = set()  # products a HARVEST/CARE this turn could refill
    for t, a in enumerate(actions):
        turn_harvest_products = set()
        for unit_action in [a.get("farmer")] + list(a.get("hands") or []):
            if unit_action and unit_action[0] in ("HARVEST", "CARE"):
                turn_harvest_products.add("__any__")  # conservative: any harvest/care this turn confounds

        for order in (a.get("market") or []):
            if not order:
                continue
            if order[0] == "SELL" and len(order) >= 3:
                requested_sell.append((t, order[1], order[2]))
            elif order[0] == "BUY_PRODUCT" and len(order) >= 3:
                requested_buy_product.append((t, order[1], order[2]))

        if turn_harvest_products:
            harvest_products.add(t)

    def shed_at(turn, product):
        if turn >= len(steps) or seat >= len(steps[turn]):
            return None
        priv = (steps[turn][seat].get("observation") or {}).get("private") or {}
        shed = priv.get("shed") or {}
        return shed.get(product)

    for (t, product, qty) in requested_sell:
        before = shed_at(t, product)
        after = shed_at(t + 1, product)
        if t in harvest_products:
            unknown_sell.append((t, product, qty))
        elif before is None or after is None:
            unknown_sell.append((t, product, qty))
        elif after < before:
            observed_landed_sell.append((t, product, qty, before - after))
        else:
            unknown_sell.append((t, product, qty))

    for (t, product, qty) in requested_buy_product:
        before = shed_at(t, product)
        after = shed_at(t + 1, product)
        if before is None or after is None:
            unknown_buy_product.append((t, product, qty))
        elif after > before:
            observed_landed_buy_product.append((t, product, qty, after - before))
        else:
            unknown_buy_product.append((t, product, qty))

    return {
        "requested_sell": requested_sell,
        "requested_buy_product": requested_buy_product,
        "observed_landed_sell": observed_landed_sell,
        "observed_landed_buy_product": observed_landed_buy_product,
        "unknown_sell": unknown_sell,
        "unknown_buy_product": unknown_buy_product,
    }


# ---------------------------------------------------------------------------
# Trajectory
# ---------------------------------------------------------------------------
@dataclass
class Trajectory:
    trajectory_id: str
    episode_id: int
    target_team: str
    target_submission: int
    target_seat: int
    opponent_team: str
    opponent_submission: object
    opponent_seat: object
    seed: object
    end_time: str
    final_bank: float
    opponent_final_bank: float
    result: str
    final_margin: float
    n_turns: int
    replay_sha256: str
    action_stream_sha256: str
    prefix_hash: dict
    suffix_hash: dict
    shop_signature: tuple
    actions: list = field(repr=False)
    turn_digests: object = field(repr=False)
    action_summary: dict = field(repr=False)
    evidence: dict = field(repr=False)
    checkpoints: dict = field(repr=False)


def build_trajectory(manifest_row, replay, replay_sha256):
    seat = manifest_row["player_seat"]
    eid = manifest_row["episode_id"]
    actions = extract_action_stream(replay, seat)
    n_turns = len(actions)
    full_bytes = canonical_bytes(actions)
    action_stream_sha256 = sha256_hex(full_bytes)

    digests = [turn_digest(a) for a in actions]

    prefix_hash = {}
    for c in CHECKPOINTS:
        end = min(c, n_turns - 1)
        prefix_hash[c] = sha256_hex(b"".join(digests[:end + 1]))
    suffix_hash = {}
    for s in SUFFIX_POINTS:
        start = min(s, n_turns)
        suffix_hash[s] = sha256_hex(b"".join(digests[start:]))

    checkpoints = {c: extract_checkpoint_state(replay, seat, min(c, n_turns - 1), actions)
                   for c in CHECKPOINTS}

    shop_signature = tuple(checkpoints[max(CHECKPOINTS)].get("unlocked_shops_in_order", ()))

    info = replay.get("info") or {}
    rewards = replay.get("rewards") or [None, None]
    opp_seat = 1 - seat if seat in (0, 1) else None
    opponent_bank = rewards[opp_seat] if opp_seat is not None and opp_seat < len(rewards) else None
    my_bank = rewards[seat] if seat is not None and seat < len(rewards) else None

    if my_bank is None or opponent_bank is None:
        result = "unknown"
        margin = None
    elif my_bank > opponent_bank:
        result, margin = "win", my_bank - opponent_bank
    elif my_bank < opponent_bank:
        result, margin = "loss", my_bank - opponent_bank
    else:
        result, margin = "tie", 0.0

    action_summary = summarize_actions(actions, replay, seat)
    evidence = state_transition_evidence(actions, replay, seat)

    return Trajectory(
        trajectory_id=f"{eid}:{seat}",
        episode_id=eid,
        target_team=manifest_row["player"],
        target_submission=manifest_row["player_submission"],
        target_seat=seat,
        opponent_team=manifest_row.get("opponent_name"),
        opponent_submission=manifest_row.get("opponent_submission"),
        opponent_seat=manifest_row.get("opponent_seat"),
        seed=info.get("seed"),
        end_time=manifest_row.get("end_time"),
        final_bank=my_bank,
        opponent_final_bank=opponent_bank,
        result=result,
        final_margin=margin,
        n_turns=n_turns,
        replay_sha256=replay_sha256,
        action_stream_sha256=action_stream_sha256,
        prefix_hash=prefix_hash,
        suffix_hash=suffix_hash,
        shop_signature=shop_signature,
        actions=actions,
        turn_digests=digests,
        action_summary=action_summary,
        evidence=evidence,
        checkpoints=checkpoints,
    )


# ---------------------------------------------------------------------------
# Route-family discovery
# ---------------------------------------------------------------------------
class UnionFind:
    def __init__(self, items):
        self.parent = {i: i for i in items}

    def find(self, x):
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.parent[ra] = rb

    def groups(self):
        out = defaultdict(list)
        for x in self.parent:
            out[self.find(x)].append(x)
        return list(out.values())


def agreement_matrix(trajectories):
    n = len(trajectories)
    max_len = max(t.n_turns for t in trajectories)
    mat = np.full((n, max_len), -1, dtype=np.int64)
    for i, t in enumerate(trajectories):
        arr = np.frombuffer(b"".join(t.turn_digests), dtype=np.uint8).reshape(-1, 8)
        ints = arr.view(np.int64).reshape(-1)
        mat[i, :len(ints)] = ints
    return mat


def pairwise_full_agreement(mat):
    n = mat.shape[0]
    sim = np.zeros((n, n), dtype=np.float64)
    for i in range(n):
        valid_i = mat[i] != -1
        eq = (mat == mat[i]) & valid_i[None, :]
        both_valid = valid_i[None, :] & (mat != -1)
        denom = both_valid.sum(axis=1)
        num = (eq & both_valid).sum(axis=1)
        with np.errstate(invalid="ignore", divide="ignore"):
            sim[i] = np.where(denom > 0, num / denom, 0.0)
    return sim


def window_agreement(t_a, t_b, start, end):
    end = min(end, t_a.n_turns - 1, t_b.n_turns - 1)
    if end < start:
        return None
    da = t_a.turn_digests[start:end + 1]
    db = t_b.turn_digests[start:end + 1]
    n = len(da)
    matches = sum(1 for x, y in zip(da, db) if x == y)
    return matches / n if n else None


def discover_families(trajectories):
    families = {}  # family_type -> list of dict(family rows) + membership

    # 1. exact full-stream hash
    by_hash = defaultdict(list)
    for t in trajectories:
        by_hash[t.action_stream_sha256].append(t)
    families["exact_full_hash"] = list(by_hash.values())

    # 2. exact prefix hashes at each checkpoint
    for c in CHECKPOINTS:
        by_prefix = defaultdict(list)
        for t in trajectories:
            by_prefix[t.prefix_hash[c]].append(t)
        families[f"prefix_{c}"] = list(by_prefix.values())

    # 3. shop-unlock signature
    by_shop = defaultdict(list)
    for t in trajectories:
        by_shop[t.shop_signature].append(t)
    families["shop_signature"] = list(by_shop.values())

    # 4. approximate full-stream agreement thresholds via union-find
    ids = [t.trajectory_id for t in trajectories]
    mat = agreement_matrix(trajectories)
    sim = pairwise_full_agreement(mat)
    by_id = {t.trajectory_id: t for t in trajectories}

    for thresh in AGREEMENT_THRESHOLDS:
        uf = UnionFind(ids)
        n = len(ids)
        for i in range(n):
            for j in range(i + 1, n):
                if sim[i, j] >= thresh:
                    uf.union(ids[i], ids[j])
        grouped = uf.groups()
        key = f"agreement_{int(thresh * 100)}"
        families[key] = [[by_id[tid] for tid in group] for group in grouped]

    return families, sim, ids


def pick_medoid(group, sim, id_index):
    if len(group) == 1:
        return group[0]
    idxs = [id_index[t.trajectory_id] for t in group]
    best, best_score = None, -1
    for a in idxs:
        score = sum(sim[a, b] for b in idxs if b != a)
        if score > best_score:
            best_score, best = score, a
    inv = {v: k for k, v in id_index.items()}
    tid = inv[best]
    return next(t for t in group if t.trajectory_id == tid)


def first_divergence_turn(t_a, t_b):
    n = min(t_a.n_turns, t_b.n_turns)
    for i in range(n):
        if t_a.turn_digests[i] != t_b.turn_digests[i]:
            return i
    return n if t_a.n_turns != t_b.n_turns else None


# ---------------------------------------------------------------------------
# Output writers
# ---------------------------------------------------------------------------
def write_target_trajectories(trajectories, path):
    cols = ["trajectory_id", "episode_id", "target_team", "target_submission",
            "target_seat", "opponent_team", "opponent_submission", "opponent_seat",
            "seed", "end_time", "final_bank", "opponent_final_bank", "result",
            "final_margin", "n_turns", "replay_sha256", "action_stream_sha256",
            "prefix_hash_72", "prefix_hash_144", "prefix_hash_216", "prefix_hash_288",
            "suffix_hash_144", "suffix_hash_216", "suffix_hash_288",
            "shop_signature", "land_purchase_turns", "animal_purchase_events",
            "workforce_max_hands_observed", "planting_turns_by_crop",
            "market_order_first_turn", "market_order_counts",
            "requested_sell_count", "observed_landed_sell_count", "unknown_sell_count",
            "requested_buy_product_count", "observed_landed_buy_product_count",
            "unknown_buy_product_count"]
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        for t in trajectories:
            w.writerow({
                "trajectory_id": t.trajectory_id, "episode_id": t.episode_id,
                "target_team": t.target_team, "target_submission": t.target_submission,
                "target_seat": t.target_seat, "opponent_team": t.opponent_team,
                "opponent_submission": t.opponent_submission, "opponent_seat": t.opponent_seat,
                "seed": t.seed, "end_time": t.end_time, "final_bank": t.final_bank,
                "opponent_final_bank": t.opponent_final_bank, "result": t.result,
                "final_margin": t.final_margin, "n_turns": t.n_turns,
                "replay_sha256": t.replay_sha256, "action_stream_sha256": t.action_stream_sha256,
                "prefix_hash_72": t.prefix_hash[72], "prefix_hash_144": t.prefix_hash[144],
                "prefix_hash_216": t.prefix_hash[216], "prefix_hash_288": t.prefix_hash[288],
                "suffix_hash_144": t.suffix_hash[144], "suffix_hash_216": t.suffix_hash[216],
                "suffix_hash_288": t.suffix_hash[288],
                "shop_signature": json.dumps(list(t.shop_signature)),
                "land_purchase_turns": json.dumps(t.action_summary["land_purchase_turns"]),
                "animal_purchase_events": json.dumps(t.action_summary["animal_purchase_events"]),
                "workforce_max_hands_observed": t.action_summary["workforce_max_hands_observed"],
                "planting_turns_by_crop": json.dumps(t.action_summary["planting_turns_by_crop"]),
                "market_order_first_turn": json.dumps(t.action_summary["market_order_first_turn"]),
                "market_order_counts": json.dumps(t.action_summary["market_order_counts"]),
                "requested_sell_count": len(t.evidence["requested_sell"]),
                "observed_landed_sell_count": len(t.evidence["observed_landed_sell"]),
                "unknown_sell_count": len(t.evidence["unknown_sell"]),
                "requested_buy_product_count": len(t.evidence["requested_buy_product"]),
                "observed_landed_buy_product_count": len(t.evidence["observed_landed_buy_product"]),
                "unknown_buy_product_count": len(t.evidence["unknown_buy_product"]),
            })


def write_checkpoint_states(trajectories, path):
    with open(path, "w", encoding="utf-8") as fh:
        for t in trajectories:
            for c in CHECKPOINTS:
                rec = dict(t.checkpoints[c])
                rec["trajectory_id"] = t.trajectory_id
                rec["compat_key"] = checkpoint_compat_key(t.checkpoints[c])
                fh.write(json.dumps(rec, default=str) + "\n")


def write_family_rows(families, sim, ids, path):
    id_index = {tid: i for i, tid in enumerate(ids)}
    cols = ["family_id", "family_type", "n_trajectories", "target_submissions",
            "episode_count", "distinct_seeds", "distinct_opponents",
            "wins", "ties", "losses", "final_bank_min", "final_bank_mean",
            "final_bank_max", "representative_trajectory_id",
            "representative_episode_id", "shop_signature",
            "nearest_other_family_id", "nearest_other_family_agreement",
            "first_divergence_turn_from_nearest"]
    rows_out = []
    family_meta = {}  # (type, fam_idx) -> row dict, for cross-family nearest lookup

    for ftype, groups in families.items():
        reps = []
        for fam_idx, group in enumerate(groups):
            fam_id = f"{ftype}#{fam_idx}"
            rep = pick_medoid(group, sim, id_index) if ftype.startswith("agreement") else group[0]
            banks = [g.final_bank for g in group if g.final_bank is not None]
            row = {
                "family_id": fam_id,
                "family_type": ftype,
                "n_trajectories": len(group),
                "target_submissions": ";".join(sorted({str(g.target_submission) for g in group})),
                "episode_count": len({g.episode_id for g in group}),
                "distinct_seeds": len({g.seed for g in group}),
                "distinct_opponents": len({g.opponent_submission for g in group}),
                "wins": sum(1 for g in group if g.result == "win"),
                "ties": sum(1 for g in group if g.result == "tie"),
                "losses": sum(1 for g in group if g.result == "loss"),
                "final_bank_min": min(banks) if banks else None,
                "final_bank_mean": sum(banks) / len(banks) if banks else None,
                "final_bank_max": max(banks) if banks else None,
                "representative_trajectory_id": rep.trajectory_id,
                "representative_episode_id": rep.episode_id,
                "shop_signature": json.dumps(list(rep.shop_signature)),
            }
            reps.append((fam_id, rep, row, group))
        # nearest-other-family within this family_type only (comparing
        # across types, e.g. prefix_72 vs agreement_99, isn't meaningful)
        for fam_id, rep, row, group in reps:
            best_id, best_sim, best_div = None, -1.0, None
            for other_id, other_rep, _, _ in reps:
                if other_id == fam_id:
                    continue
                s = sim[id_index[rep.trajectory_id], id_index[other_rep.trajectory_id]]
                if s > best_sim:
                    best_sim, best_id = s, other_id
                    best_div = first_divergence_turn(rep, other_rep)
            row["nearest_other_family_id"] = best_id
            row["nearest_other_family_agreement"] = round(best_sim, 4) if best_id else None
            row["first_divergence_turn_from_nearest"] = best_div
            rows_out.append(row)

    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        w.writerows(rows_out)
    return rows_out


def write_family_membership(trajectories, families, path):
    membership = defaultdict(dict)
    for ftype, groups in families.items():
        for fam_idx, group in enumerate(groups):
            fam_id = f"{ftype}#{fam_idx}"
            for t in group:
                membership[t.trajectory_id][ftype] = fam_id

    ftypes = sorted(families.keys())
    cols = ["trajectory_id"] + ftypes
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        for t in trajectories:
            row = {"trajectory_id": t.trajectory_id}
            row.update(membership[t.trajectory_id])
            w.writerow(row)


def write_route_library(families, path):
    library = {}
    for ftype in ("exact_full_hash", "agreement_99", "agreement_95"):
        for fam_idx, group in enumerate(families[ftype]):
            fam_id = f"{ftype}#{fam_idx}"
            rep = group[0]
            library[fam_id] = {
                "family_id": fam_id,
                "family_type": ftype,
                "n_members": len(group),
                "source_episode_id": rep.episode_id,
                "source_submission_id": rep.target_submission,
                "source_seat": rep.target_seat,
                "seed": rep.seed,
                "shop_signature": list(rep.shop_signature),
                "checkpoint_compat_keys": {
                    str(c): checkpoint_compat_key(rep.checkpoints[c]) for c in CHECKPOINTS
                },
                "alignment_convention": "same-index: steps[i][seat]['action'] "
                                         "answers steps[i][seat]['observation'], both row i",
                "replay_sha256": rep.replay_sha256,
                "action_stream_sha256": rep.action_stream_sha256,
                "actions": rep.actions,
            }
    with gzip.open(path, "wt", encoding="utf-8") as fh:
        json.dump(library, fh)


def write_trajectory_action_streams(trajectories, path):
    with gzip.open(path, "wt", encoding="utf-8") as fh:
        for t in trajectories:
            fh.write(json.dumps({
                "trajectory_id": t.trajectory_id,
                "episode_id": t.episode_id,
                "target_submission": t.target_submission,
                "target_seat": t.target_seat,
                "replay_sha256": t.replay_sha256,
                "action_stream_sha256": t.action_stream_sha256,
                "actions": t.actions,
            }) + "\n")


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------
def largest_family(groups):
    return max(groups, key=len)


def no_op_signals(trajectories):
    """Neutral, evidence-only signals worth a human's attention - no claim
    about intent. Two kinds: (1) requested SELL/BUY_PRODUCT orders with no
    supporting shed-delta evidence either way ('unknown', not 'rejected'),
    and (2) long unbroken PASS runs by the farmer unit."""
    total_unknown_sell = sum(len(t.evidence["unknown_sell"]) for t in trajectories)
    total_unknown_buy = sum(len(t.evidence["unknown_buy_product"]) for t in trajectories)
    total_requested_sell = sum(len(t.evidence["requested_sell"]) for t in trajectories)
    total_requested_buy = sum(len(t.evidence["requested_buy_product"]) for t in trajectories)

    long_pass_runs = 0
    for t in trajectories:
        run = 0
        for a in t.actions:
            farmer = a.get("farmer")
            if farmer and farmer[0] == "PASS":
                run += 1
                if run == 10:
                    long_pass_runs += 1
            else:
                run = 0
    return {
        "total_requested_sell": total_requested_sell,
        "total_unknown_sell": total_unknown_sell,
        "total_requested_buy_product": total_requested_buy,
        "total_unknown_buy_product": total_unknown_buy,
        "trajectories_with_10plus_farmer_pass_run": long_pass_runs,
    }


def generate_report(trajectories, families, sim, ids, family_rows, skipped, out_path):
    id_index = {tid: i for i, tid in enumerate(ids)}
    n = len(trajectories)

    exact_groups = families["exact_full_hash"]
    agree99_groups = families["agreement_99"]
    agree95_groups = families["agreement_95"]
    prefix72_groups = families["prefix_72"]
    prefix144_groups = families["prefix_144"]

    top72 = largest_family(prefix72_groups) if prefix72_groups else []
    top144 = largest_family(prefix144_groups) if prefix144_groups else []

    lineage_verdict = (
        "one shared lineage" if len(agree95_groups) == 1 else
        "several related lineages" if len(agree95_groups) < n / 2 else
        "genuinely different strategies"
    )

    reusable = sorted(
        (r for r in family_rows if r["family_type"] == "agreement_99" and r["n_trajectories"] >= 3),
        key=lambda r: -r["n_trajectories"]
    )

    compat216 = Counter()
    compat288 = Counter()
    for t in trajectories:
        k216 = checkpoint_compat_key(t.checkpoints[216])
        k288 = checkpoint_compat_key(t.checkpoints[288])
        if k216:
            compat216[k216] += 1
        if k288:
            compat288[k288] += 1
    top_compat216 = compat216.most_common(5)
    top_compat288 = compat288.most_common(5)

    noop = no_op_signals(trajectories)

    lines = []
    lines.append("# Strategy reconstruction report - current top-five Kaggriculture leaders\n")
    lines.append(
        "These are descriptive observations of a fixed corpus of already-played "
        "ladder games. Win rates and bank figures below are ladder observations, "
        "not local benchmarks and not causal claims about which route is "
        "superior - the live Kaggle ladder is the only competitive benchmark.\n"
    )
    lines.append(
        "**Alignment note:** built on same-index replay alignment "
        "(`steps[i][seat]['action']` answers `steps[i][seat]['observation']`, "
        "both row i), verified directly against the installed engine and "
        "against this repo's own `replay_shape.py`/`opening_trace.py`. The "
        "originally-specified `experiments/current_meta_report.py` does not "
        "exist in this repo, and its claimed row-0-placeholder/`t+1` shift "
        "does not match the engine's actual output. See the accompanying chat "
        "message for the full discrepancy.\n"
    )

    lines.append(f"## Corpus\n")
    lines.append(f"- {n} target-player trajectories reconstructed from "
                 f"{len({t.episode_id for t in trajectories})} unique episodes.")
    if skipped:
        lines.append(f"- {len(skipped)} manifest rows skipped (replay missing/corrupt): "
                     + "; ".join(f"episode {e} ({why})" for e, why in skipped))
    else:
        lines.append("- 0 manifest rows skipped - every manifest row had a valid replay.")
    lines.append("")

    lines.append("## Route families\n")
    lines.append(f"- Exact complete-action-stream equality: **{len(exact_groups)}** distinct "
                 f"strategies among {n} trajectories.")
    lines.append(f"- >=99% full-episode action agreement (union-find over pairwise agreement): "
                 f"**{len(agree99_groups)}** families.")
    lines.append(f"- >=95% full-episode action agreement: **{len(agree95_groups)}** families.")
    lines.append(f"- Distinct turn-72 opening prefixes (exact): **{len(prefix72_groups)}**.")
    lines.append(f"- Distinct turn-144 route prefixes (exact): **{len(prefix144_groups)}**.")
    lines.append(f"- Distinct shop-unlock signatures: **{len(families['shop_signature'])}**.")
    lines.append(
        f"\n**Lineage read at 95% agreement:** {lineage_verdict} "
        f"({len(agree95_groups)} families over {n} trajectories; a family formed by "
        "transitive >=95%-agreement chaining, which can merge trajectories that "
        "individually differ more than 5% from each other - see route_families.csv "
        "for pairwise nearest-family agreement per family).\n"
    )

    lines.append("## Most common opening (through turn 72)\n")
    if top72:
        rep = top72[0]
        lines.append(f"- {len(top72)}/{n} trajectories share this exact prefix, "
                     f"from submissions: {sorted({t.target_submission for t in top72})}.")
        lines.append(f"- Representative: episode {rep.episode_id}, seat {rep.target_seat} "
                     f"(`{rep.trajectory_id}`).")
        lines.append(f"- Land-purchase turns (representative): {rep.action_summary['land_purchase_turns']}")
        lines.append(f"- Animal-purchase events (representative): {rep.action_summary['animal_purchase_events']}\n")
    else:
        lines.append("- No trajectories available.\n")

    lines.append("## Most common route (through turn 144)\n")
    if top144:
        rep = top144[0]
        lines.append(f"- {len(top144)}/{n} trajectories share this exact prefix, "
                     f"from submissions: {sorted({t.target_submission for t in top144})}.")
        lines.append(f"- Representative: episode {rep.episode_id}, seat {rep.target_seat} "
                     f"(`{rep.trajectory_id}`).\n")
    else:
        lines.append("- No trajectories available.\n")

    lines.append("## Major divergence points after turn 144\n")
    divergences = Counter()
    for r in family_rows:
        if r["family_type"] == "agreement_95" and r["first_divergence_turn_from_nearest"] is not None:
            t = r["first_divergence_turn_from_nearest"]
            if t >= 144:
                divergences[t] += 1
    if divergences:
        for turn, count in sorted(divergences.items())[:15]:
            lines.append(f"- turn {turn}: {count} family-pair(s) first diverge here")
    else:
        lines.append("- No post-144 divergence points recorded among agreement_95 families "
                     "(either too few families, or all divergences occur before turn 144).")
    lines.append("")

    lines.append("## Routes repeated enough to serve as new-agent source material\n")
    lines.append("(>=99% agreement families with >=3 members, i.e. observed more than twice)\n")
    if reusable:
        for r in reusable[:15]:
            lines.append(f"- `{r['family_id']}`: {r['n_trajectories']} trajectories, "
                         f"{r['distinct_seeds']} distinct seeds, {r['distinct_opponents']} distinct "
                         f"opponents, submissions {r['target_submissions']}, "
                         f"W/T/L {r['wins']}/{r['ties']}/{r['losses']}, "
                         f"bank range {r['final_bank_min']:.0f}-{r['final_bank_max']:.0f}, "
                         f"representative `{r['representative_trajectory_id']}`.")
    else:
        lines.append("- None found at the >=99% / >=3-member bar.")
    lines.append("")

    lines.append("## Checkpoint compatibility (turn 216 / turn 288)\n")
    lines.append(f"- Turn-216 compat-key groups (trajectories sharing quadrants/animals/hands-bucket/"
                 f"hires-bucket/shop-signature/planted-bucket): {len(compat216)} distinct groups.")
    for key, count in top_compat216:
        lines.append(f"  - {count} trajectories: quadrants={key[0]}, animals={key[1]}, "
                     f"hands{key[2]}, hires{key[3]}, shops={key[4]}, planted{key[5]}")
    lines.append(f"- Turn-288 compat-key groups: {len(compat288)} distinct groups.")
    for key, count in top_compat288:
        lines.append(f"  - {count} trajectories: quadrants={key[0]}, animals={key[1]}, "
                     f"hands{key[2]}, hires{key[3]}, shops={key[4]}, planted{key[5]}")
    lines.append(
        "\nTrajectories sharing a compat-key at turn 216 or 288 are the ones whose "
        "turn-216-to-end / turn-288-to-end suffixes are observably compatible with "
        "each other's prefixes under this coarse key - see checkpoint_states.jsonl "
        "for the full per-trajectory state.\n"
    )

    lines.append("## Apparent invalid/no-op/camouflage actions (described neutrally)\n")
    lines.append(
        f"- {noop['total_unknown_sell']}/{noop['total_requested_sell']} requested SELL orders "
        "have no shed-delta evidence either confirming or denying they landed (same-turn "
        "HARVEST/CARE, or absent before/after data) - `unknown`, not `rejected`."
    )
    lines.append(
        f"- {noop['total_unknown_buy_product']}/{noop['total_requested_buy_product']} requested "
        "BUY_PRODUCT orders are similarly unconfirmed."
    )
    lines.append(
        f"- {noop['trajectories_with_10plus_farmer_pass_run']} trajectories contain a farmer-unit "
        "run of 10+ consecutive PASS actions. No claim is made about why."
    )
    lines.append("")

    lines.append("## Artifacts\n")
    for p in sorted(LIBRARY_DIR.glob("*")):
        lines.append(f"- `{p}`")
    lines.append("")

    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))

    return {
        "n_trajectories": n,
        "n_exact_families": len(exact_groups),
        "n_agree99_families": len(agree99_groups),
        "n_agree95_families": len(agree95_groups),
        "lineage_verdict": lineage_verdict,
        "top72": top72,
        "top144": top144,
        "reusable": reusable,
        "skipped": skipped,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    LIBRARY_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Manifest: {MANIFEST_PATH}")
    manifest_rows = load_manifest()
    print(f"  {len(manifest_rows)} manifest rows")

    by_episode = defaultdict(list)
    for r in manifest_rows:
        by_episode[r["episode_id"]].append(r)
    print(f"  {len(by_episode)} unique episodes")

    trajectories = []
    skipped = []
    replay_sha_cache = {}

    for i, (eid, rows) in enumerate(sorted(by_episode.items()), 1):
        gz_path = REPLAY_DIR / f"{eid}.json.gz"
        if not gz_path.exists():
            skipped.append((eid, "replay file missing"))
            continue
        try:
            replay_sha = replay_sha_cache.get(eid) or sha256_file(gz_path)
            replay_sha_cache[eid] = replay_sha
            replay = load_replay(gz_path)
        except Exception as e:
            skipped.append((eid, str(e)))
            continue

        for row in rows:
            if row["player_seat"] is None:
                skipped.append((eid, f"no seat for {row['player']}"))
                continue
            try:
                traj = build_trajectory(row, replay, replay_sha)
            except Exception as e:
                skipped.append((eid, f"trajectory build failed for {row['player']}: {e}"))
                continue
            trajectories.append(traj)

        if i % 50 == 0 or i == len(by_episode):
            print(f"  processed {i}/{len(by_episode)} episodes, "
                 f"{len(trajectories)} trajectories so far")

    print(f"\nReconstructed {len(trajectories)} trajectories "
         f"({len(skipped)} manifest rows skipped).")

    print("Discovering route families ...")
    families, sim, ids = discover_families(trajectories)

    print("Writing artifacts ...")
    write_target_trajectories(trajectories, LIBRARY_DIR / "target_trajectories.csv")
    write_checkpoint_states(trajectories, LIBRARY_DIR / "checkpoint_states.jsonl")
    family_rows = write_family_rows(families, sim, ids, LIBRARY_DIR / "route_families.csv")
    write_family_membership(trajectories, families, LIBRARY_DIR / "family_membership.csv")
    write_route_library(families, LIBRARY_DIR / "route_library.json.gz")
    write_trajectory_action_streams(trajectories, LIBRARY_DIR / "trajectory_action_streams.jsonl.gz")

    summary = generate_report(trajectories, families, sim, ids, family_rows, skipped,
                              LIBRARY_DIR / "strategy_reconstruction_report.md")

    print(f"\nDone. {summary['n_trajectories']} trajectories, "
         f"{summary['n_exact_families']} exact families, "
         f"{summary['n_agree99_families']} >=99% families, "
         f"{summary['n_agree95_families']} >=95% families.")
    print(f"Report: {LIBRARY_DIR / 'strategy_reconstruction_report.md'}")


if __name__ == "__main__":
    main()
