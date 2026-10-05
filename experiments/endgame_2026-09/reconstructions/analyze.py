"""Offline reconstruction pipeline: cluster a leader's winning games by
turn-72 opening, pick the medoid per cluster, extract a macro route.

Read-only against ~/KagricultureLocalData/episodes. Writes JSON macro-plan
files into ~/KagricultureLocalData/reconstructions/ (LOCAL_WORKDIR) only.
"""
import csv, gzip, json, os, statistics
from collections import Counter, defaultdict

EPISODES_DIR = os.path.expanduser("~/KagricultureLocalData/episodes")
REPLAYS_DIR = os.path.join(EPISODES_DIR, "replays")
MANIFEST = os.path.join(EPISODES_DIR, "manifest.csv")
OUT_DIR = os.path.expanduser("~/KagricultureLocalData/reconstructions")


def load_manifest_wins(player):
    with open(MANIFEST) as f:
        rows = list(csv.DictReader(f))
    return [r for r in rows if r["player"] == player and r["won"] == "1"]


def load_replay(episode_id):
    path = os.path.join(REPLAYS_DIR, f"{episode_id}.json.gz")
    with gzip.open(path) as f:
        return json.load(f)


def opening_key(steps, seat, at_step=72):
    shops = steps[at_step][seat]["observation"]["town"].get("unlocked_shops") or []
    shops = shops[:2]
    if not shops:
        return "NONE"
    return "__".join(shops)


def action_signature(action):
    """Coordinate-discarded per-turn signature for distance/medoid purposes."""
    def collapse(a):
        if not a:
            return "PASS"
        head = a[0]
        if head in ("NORTH", "SOUTH", "EAST", "WEST"):
            return "MOVE"
        if head == "PLANT":
            return f"PLANT:{a[1]}" if len(a) > 1 else "PLANT"
        if head == "PLACE":
            return f"PLACE:{a[1]}" if len(a) > 1 else "PLACE"
        if head == "PICKUP":
            return f"PICKUP:{a[1]}" if len(a) > 1 else "PICKUP"
        return head
    farmer = collapse(action.get("farmer"))
    hands = tuple(sorted(collapse(h) for h in (action.get("hands") or [])))
    market = tuple(sorted(
        (o[0], o[1]) if o and len(o) > 1 else (o[0],) if o else ()
        for o in (action.get("market") or [])
    ))
    return (farmer, hands, market)


def game_signature_sequence(steps, seat):
    return [action_signature(steps[t][seat]["action"]) for t in range(len(steps))]


def hamming_distance(seq_a, seq_b):
    n = min(len(seq_a), len(seq_b))
    return sum(1 for i in range(n) if seq_a[i] != seq_b[i]) / n


def find_medoid(games, window=None):
    """games: list of (episode_id, seat, steps). Returns index of medoid.

    `window` restricts the distance computation to steps[:window] - used
    for the shared OPENING medoid, since every DSM win looks similar before
    its shop-branch point regardless of which opening it eventually drew;
    comparing full 720-step sequences there would just measure the
    (irrelevant, for this purpose) late-game divergence instead.
    """
    def sig(steps, seat):
        full = game_signature_sequence(steps, seat)
        return full[:window] if window else full
    sigs = [sig(steps, seat) for _, seat, steps in games]
    n = len(sigs)
    if n == 1:
        return 0
    dist = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            d = hamming_distance(sigs[i], sigs[j])
            dist[i][j] = dist[j][i] = d
    totals = [sum(row) for row in dist]
    return min(range(n), key=lambda i: totals[i])


def extract_macro_plan(steps, seat, opp_seat):
    """Turn-indexed macro schedule, coordinates discarded."""
    plan = {
        "land_days": [],
        "crew_by_day": {},
        "animal_events": [],     # [(day, species)]
        "plant_events": [],      # [(day, crop)]
        "sell_events": [],       # [(turn, product, qty)]
        "buy_events": [],        # [(turn, kind, product, qty)]  kind: BUY_SEED/BUY_PRODUCT
    }
    n = len(steps)
    for t in range(n):
        obs = steps[t][seat]["observation"]
        act = steps[t][seat]["action"] or {}
        day = obs.get("day", t // 24)
        hour = obs.get("hour", t % 24)
        farm = obs["farms"][seat]

        if hour == 23:
            hands = farm.get("hands") or []
            plan["crew_by_day"][day] = len(hands) + 1  # +1 farmer

        market = act.get("market") or []
        for o in market:
            if not o:
                continue
            if o[0] == "BUY_LAND":
                plan["land_days"].append(day)
            elif o[0] == "BUY_ANIMAL" and len(o) > 1:
                plan["animal_events"].append((day, o[1]))
            elif o[0] == "SELL" and len(o) > 2:
                plan["sell_events"].append((t, o[1], int(o[2])))
            elif o[0] in ("BUY_SEED", "BUY_PRODUCT") and len(o) > 2:
                plan["buy_events"].append((t, o[0], o[1], int(o[2])))

        for a in [act.get("farmer")] + list(act.get("hands") or []):
            if a and a[0] == "PLANT" and len(a) > 1:
                plan["plant_events"].append((day, a[1]))

    # Precompute a day-indexed crop histogram (most-planted crop per day,
    # descending) so the runtime agent doesn't have to scan plant_events
    # itself - it just looks up crop_by_day[str(day)].
    by_day = defaultdict(Counter)
    for day, crop in plan["plant_events"]:
        by_day[day][crop] += 1
    plan["crop_by_day"] = {
        str(day): [[c, n] for c, n in counter.most_common()]
        for day, counter in by_day.items()
    }

    # Cumulative per-species herd TARGET by day, not a purchase-order queue -
    # a runtime agent compares its own current owned count against this and
    # buys toward the deficit, which stays correct even mid-route-switch
    # (an ordered pointer would double-buy or under-buy once two different
    # medoids' event sequences get spliced at the opening/shop-key handover).
    running = Counter()
    target_by_day = {}
    for day, species in sorted(plan["animal_events"]):
        running[species] += 1
        target_by_day[day] = dict(running)
    plan["animal_target_by_day"] = {str(d): t for d, t in target_by_day.items()}

    return plan


def summarize_and_save(player_name, out_name, at_step=72, min_cluster=1):
    wins = load_manifest_wins(player_name)
    print(f"\n=== {player_name}: {len(wins)} winning games ===", flush=True)
    clusters = defaultdict(list)
    seeds_by_episode = {}
    for i, row in enumerate(wins, 1):
        ep_id = row["episode_id"]
        seat = int(row["player_seat"])
        data = load_replay(ep_id)
        steps = data["steps"]
        seeds_by_episode[ep_id] = data["info"]["seed"]
        key = opening_key(steps, seat, at_step=at_step)
        clusters[key].append((ep_id, seat, steps))
        print(f"  loaded {i}/{len(wins)} ep={ep_id} key={key}", flush=True)

    counts = Counter({k: len(v) for k, v in clusters.items()})
    print("opening cluster sizes:", counts.most_common())

    routes = {}

    # Shared OPENING route: medoid over ALL wins, distance computed only on
    # the pre-branch window (steps 0-71) - every DSM win plays similarly
    # before its shop is known, so this is real shared content, not a blend
    # across different families. Used for turns before any shop unlocks.
    all_games = [g for games in clusters.values() for g in games]
    opening_idx = find_medoid(all_games, window=at_step)
    ep_id, seat, steps = all_games[opening_idx]
    plan = extract_macro_plan(steps, seat, 1 - seat)
    routes["OPENING"] = {
        "medoid_episode_id": ep_id, "medoid_seat": seat,
        "cluster_size": len(all_games), "seed": seeds_by_episode[ep_id], "plan": plan,
    }
    print(f"  key='OPENING' n={len(all_games)} medoid_episode={ep_id} seed={seeds_by_episode[ep_id]}", flush=True)

    for key, games in clusters.items():
        if len(games) < min_cluster:
            continue
        medoid_idx = find_medoid(games)
        ep_id, seat, steps = games[medoid_idx]
        opp_seat = 1 - seat
        plan = extract_macro_plan(steps, seat, opp_seat)
        seed = seeds_by_episode[ep_id]
        routes[key] = {
            "medoid_episode_id": ep_id,
            "medoid_seat": seat,
            "cluster_size": len(games),
            "seed": seed,
            "plan": plan,
        }
        print(f"  key={key!r} n={len(games)} medoid_episode={ep_id} seed={seed}", flush=True)

    out_path = os.path.join(OUT_DIR, out_name)
    with open(out_path, "w") as f:
        json.dump(routes, f, indent=2)
    print(f"wrote {out_path}")
    return routes


if __name__ == "__main__":
    summarize_and_save("DSM", "dsm_routes.json", at_step=72)
    summarize_and_save("Unknown Mother-Goose", "goose_routes.json", at_step=72)
