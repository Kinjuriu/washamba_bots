"""Per-game labour-scheduling feature extraction for the top-12 vs W3 scheduler study.

Streams one replay at a time (never holds more than one game's steps in memory).
Positions are read directly from the observation (farm['farmer'], farm['hands']) --
the engine stores them there already, so no manual movement simulation is needed.
Action at steps[t][seat]['action'] was decided from steps[t-1]'s observation and is
applied to reach steps[t]'s observation (this file's causal convention throughout).

Output per game: a single JSON-serialisable summary dict (not raw per-step logs),
so the corpus can be processed and aggregated without holding much in RAM.
"""
import gzip, json, collections, statistics

TURNS_PER_DAY = 24
BOARD_SIZE = 10
N_DAYS = 30

MOVE_OPS = {"NORTH", "SOUTH", "EAST", "WEST"}
ANIMAL_OPS = {"FEED", "CARE", "COLLECT_FERTILIZER"}
CROP_OPS = {"WATER", "PLANT", "FERTILIZE"}
# HARVEST is ambiguous (animal or crop tile) -- resolved by inspecting the tile.
REPLANT_CROPS = {"WHEAT", "CARROT"}  # non-ongoing: harvest clears the tile
ONGOING_CROPS = {"TOMATO", "STRAWBERRY", "MELON"}

PHASES = [("d0_7", 0, 7), ("d8_14", 8, 14), ("d15_22", 15, 22), ("d23_29", 23, 29)]


def phase_of(day):
    for name, lo, hi in PHASES:
        if lo <= day <= hi:
            return name
    return "d23_29"


def load_replay(path):
    with gzip.open(path, "rb") as f:
        return json.load(f)


def median_iqr(vals):
    vals = sorted(v for v in vals if v is not None)
    n = len(vals)
    if n == 0:
        return dict(median=None, q1=None, q3=None, n=0)
    med = statistics.median(vals)
    q1 = vals[max(0, n // 4)]
    q3 = vals[min(n - 1, (3 * n) // 4)]
    return dict(median=round(med, 3) if isinstance(med, float) else med, q1=q1, q3=q3, n=n)


def _tile_category(tile):
    if not isinstance(tile, dict):
        return None
    if "animal" in tile:
        return "animal"
    if tile.get("kind") == "PLANT":
        return "crop"
    return None


def _is_legal(op, action, tile, inv, seeds, day):
    """Approximate engine legality for the non-move ops we care about, given the
    tile/inventory state *before* the action (as the engine sees it)."""
    if op in ("PASS",) or op in MOVE_OPS:
        return True
    if op == "WATER":
        return isinstance(tile, dict) and tile.get("kind") == "PLANT" and not tile.get("watered_today")
    if op == "HARVEST":
        return isinstance(tile, dict) and tile.get("yield_units", 0) > 0
    if op == "PLANT":
        crop = action[1] if len(action) > 1 else None
        return tile is None and crop is not None and seeds.get(crop, 0) > 0
    if op == "FEED":
        return isinstance(tile, dict) and "animal" in tile and not tile.get("fed_today") and inv.get("WHEAT", 0) > 0
    if op == "CARE":
        return isinstance(tile, dict) and "animal" in tile and not tile.get("cared_today")
    if op == "FERTILIZE":
        return isinstance(tile, dict) and tile.get("kind") == "PLANT" and inv.get("FERTILIZER", 0) > 0
    if op == "COLLECT_FERTILIZER":
        return isinstance(tile, dict) and "animal" in tile and tile.get("fertilizer_available")
    if op == "PICKUP":
        return True  # shed-adjacency not re-derived here; spot-checked separately
    if op == "DROP":
        return True
    if op == "PLACE":
        return True
    return True  # DIG, BUILD_*, NOOP-ish: not central to this study


def check_legality_sample(d, seat, max_events=2000):
    """Validation helper: for every non-move unit action in the game, confirm it was
    legal given the tile/inventory the engine would have seen. Returns (n_checked, n_illegal, examples)."""
    st = d["steps"]
    n_checked = 0
    n_illegal = 0
    examples = []
    for t in range(1, len(st)):
        action = st[t][seat].get("action") or {}
        obs_prev = st[t - 1][seat]["observation"]
        farm_prev = obs_prev["farms"][seat]
        priv_prev = obs_prev["private"]
        seeds = priv_prev.get("seeds", {})
        units = [action.get("farmer", ["PASS"])] + list(action.get("hands", []) or [])
        for idx, a in enumerate(units):
            if not isinstance(a, list) or not a:
                continue
            op = a[0]
            if op in MOVE_OPS or op == "PASS":
                continue
            pos = farm_prev["farmer"] if idx == 0 else (
                farm_prev["hands"][idx - 1] if idx - 1 < len(farm_prev["hands"]) else None)
            if pos is None:
                continue
            x, y = pos
            tile = farm_prev["tiles"][y][x]
            inv = priv_prev["inventories"][idx] if idx < len(priv_prev["inventories"]) else {}
            day = obs_prev.get("step", t - 1) // TURNS_PER_DAY
            n_checked += 1
            if not _is_legal(op, a, tile, inv, seeds, day):
                n_illegal += 1
                if len(examples) < 10:
                    examples.append(dict(t=t, idx=idx, op=op, pos=pos, tile=tile))
            if n_checked >= max_events:
                return n_checked, n_illegal, examples
    return n_checked, n_illegal, examples


def analyze_game(d, seat, team_name=None):
    st = d["steps"]
    T = len(st)
    opp_seat = 1 - seat

    # ---- per-unit tracking state ----
    # unit key: 0 = farmer, k = hand slot (1-based), reset each day.
    day_hand_tiles = collections.defaultdict(lambda: collections.defaultdict(set))   # slot -> day -> {(x,y)}
    day_hand_cat = collections.defaultdict(lambda: collections.defaultdict(collections.Counter))  # slot->day->Counter(animal/crop/other)
    unit_visit_pos = {}      # idx -> current (x,y) at start of current visit
    unit_visit_start = {}    # idx -> step index the visit started
    unit_visit_actions = {}  # idx -> list of ops performed during current visit
    visit_action_counts = []       # actions per visit (all units, all visits)
    visit_combo_counter = collections.Counter()
    moves_between_visits = []
    day_hand_order_seq = collections.defaultdict(lambda: collections.defaultdict(list))  # slot->day-> [ops in order, deduped consecutive]

    hires_hourly = []       # hour of each HIRE market order
    hire_days = []          # day of each HIRE market order (parallel to hires_hourly)
    land_days = []          # day index when a new quadrant unlocked
    animals_by_day = {}
    planted_by_day = {}
    hands_final_by_day = {}

    feed_hours, care_hours, water_hours = [], [], []
    escapes = 0
    weed_events = 0
    consec_unfed_at_daystart = []  # pooled across animal-days

    replant_lags = []
    same_hand_same_visit = [0, 0]  # [yes, total opportunities]
    plantings_by_day_crop = collections.defaultdict(lambda: collections.defaultdict(int))
    # pending harvest-clears awaiting replant: (x,y) -> (step_harvested, idx, visit_key)
    pending_replant = {}

    pickup_events = []  # dict(item, qty, hour, day, slot)

    moves_count_by_day = collections.Counter()
    useful_count_by_day = collections.Counter()
    idle_count_by_day = collections.Counter()
    total_unit_turns_by_day = collections.Counter()
    hands_count_samples_by_day = collections.defaultdict(list)  # day -> [len(hands) at each hour]

    prev_day = -1
    prev_quadrants = 1

    for t in range(1, T):
        action = st[t][seat].get("action") or {}
        obs_prev = st[t - 1][seat]["observation"]
        obs_cur = st[t][seat]["observation"]
        farm_prev = obs_prev["farms"][seat]
        farm_cur = obs_cur["farms"][seat]
        priv_prev = obs_prev["private"]

        stepnum = obs_prev.get("step", t - 1)
        day = stepnum // TURNS_PER_DAY
        hour = stepnum % TURNS_PER_DAY

        if day != prev_day:
            # day boundary: flush nothing needed (defaultdicts handle it), just track resets
            prev_day = day

        n_quadrants = len(farm_cur.get("unlocked_quadrants", ["NW"]))
        if n_quadrants > prev_quadrants:
            land_days.append(day)
            prev_quadrants = n_quadrants

        n_hands_now = len(farm_prev.get("hands", []))
        hands_count_samples_by_day[day].append(1 + n_hands_now)

        # Real hires this step = growth in the hand count (not the raw count of ['HIRE']
        # tokens in the action -- agents often submit more HIRE orders than they can
        # afford in one turn, so counting tokens overcounts by including failed attempts).
        n_hands_cur = len(farm_cur.get("hands", []))
        real_hires = max(0, n_hands_cur - n_hands_now)
        for _ in range(real_hires):
            hires_hourly.append(hour)
            hire_days.append(day)

        units = [action.get("farmer", ["PASS"])] + list(action.get("hands", []) or [])
        for idx, a in enumerate(units):
            pos_prev = farm_prev["farmer"] if idx == 0 else (
                farm_prev["hands"][idx - 1] if idx - 1 < len(farm_prev["hands"]) else None)
            if pos_prev is None:
                continue
            total_unit_turns_by_day[day] += 1
            if not isinstance(a, list) or not a:
                op = "PASS"
            else:
                op = a[0]

            if op in MOVE_OPS:
                moves_count_by_day[day] += 1
                # visit bookkeeping: leaving current tile
                key = idx
                if key in unit_visit_pos:
                    acts = unit_visit_actions.get(key, [])
                    if acts:
                        visit_action_counts.append(len(acts))
                        combo = tuple(sorted(set(acts)))
                        if len(combo) > 1:
                            visit_combo_counter[combo] += 1
                    unit_visit_actions[key] = []
                unit_visit_pos[key] = None  # in transit
                continue

            if op == "PASS" or not isinstance(a, list) or not a:
                idle_count_by_day[day] += 1
                continue

            useful_count_by_day[day] += 1
            x, y = pos_prev
            tile = farm_prev["tiles"][y][x]
            slot = idx  # 0 = farmer, 1..k = hand slots

            key = idx
            if unit_visit_pos.get(key) != (x, y):
                # arrived at a new tile (or first action of the day)
                if key in unit_visit_pos and unit_visit_pos[key] is None:
                    moves_between_visits.append(1)  # at least one move happened (already counted above)
                unit_visit_pos[key] = (x, y)
                unit_visit_start[key] = t
                unit_visit_actions[key] = []
            unit_visit_actions.setdefault(key, []).append(op)

            day_hand_tiles[slot][day].add((x, y))
            seq = day_hand_order_seq[slot][day]
            if not seq or seq[-1] != op:
                seq.append(op)

            if op in ANIMAL_OPS or (op == "HARVEST" and _tile_category(tile) == "animal"):
                day_hand_cat[slot][day]["animal"] += 1
            elif op in CROP_OPS or (op == "HARVEST" and _tile_category(tile) == "crop"):
                day_hand_cat[slot][day]["crop"] += 1
            else:
                day_hand_cat[slot][day]["other"] += 1

            if op == "FEED":
                feed_hours.append(hour)
            elif op == "CARE":
                care_hours.append(hour)
            elif op == "WATER":
                water_hours.append(hour)
            elif op == "PICKUP" and len(a) >= 2:
                item = a[1]
                qty = int(a[2]) if len(a) >= 3 else 1
                pickup_events.append(dict(item=item, qty=qty, hour=hour, day=day, slot=slot))
            elif op == "PLANT" and len(a) >= 2:
                crop = a[1]
                plantings_by_day_crop[crop][day] += 1
                # replant check: was this tile pending a replant?
                pk = (x, y)
                if pk in pending_replant and crop in REPLANT_CROPS:
                    hstep, hidx, hkey = pending_replant.pop(pk)
                    replant_lags.append(t - hstep)
                    same_hand_same_visit[1] += 1
                    vstart = unit_visit_start.get(key)
                    if hidx == idx and vstart is not None and vstart <= hstep:
                        # same unit, and it never left this tile between harvest and plant
                        same_hand_same_visit[0] += 1
            elif op == "HARVEST":
                crop = tile.get("crop") if isinstance(tile, dict) else None
                if crop in REPLANT_CROPS and isinstance(tile, dict) and tile.get("yield_units", 0) > 0:
                    pending_replant[(x, y)] = (t, idx, key)

        # ---- animal escape / weed detection: compare tile grids prev->cur ----
        for row_prev, row_cur in zip(farm_prev["tiles"], farm_cur["tiles"]):
            for tp, tc in zip(row_prev, row_cur):
                if isinstance(tp, dict) and "animal" in tp:
                    if isinstance(tc, dict) and "animal" not in tc and tc.get("kind") == tp.get("kind"):
                        # structure remained, animal gone -> escape (only at day rollover)
                        if (t % TURNS_PER_DAY) == 0:
                            escapes += 1
                if isinstance(tp, dict) and tp.get("kind") == "PLANT":
                    if isinstance(tc, dict) and tc.get("kind") == "WEED":
                        weed_events += 1

        # start-of-day consecutive_unfed snapshot
        if hour == 0:
            for row in farm_prev["tiles"]:
                for tile in row:
                    if isinstance(tile, dict) and "animal" in tile:
                        consec_unfed_at_daystart.append(tile.get("consecutive_unfed", 0))

    # ---- close out any open visits at end of game ----
    for key, acts in unit_visit_actions.items():
        if acts:
            visit_action_counts.append(len(acts))
            combo = tuple(sorted(set(acts)))
            if len(combo) > 1:
                visit_combo_counter[combo] += 1

    # ---- animal / planted tile counts by day (sampled at hour 23 each day) ----
    for day in range(N_DAYS):
        t_end = min(day * TURNS_PER_DAY + TURNS_PER_DAY - 1, T - 1)
        if t_end < 0 or t_end >= T:
            continue
        farm = st[t_end][seat]["observation"]["farms"][seat]
        n_animals = 0
        n_planted = 0
        for row in farm["tiles"]:
            for tile in row:
                if isinstance(tile, dict):
                    if "animal" in tile:
                        n_animals += 1
                    elif tile.get("kind") == "PLANT":
                        n_planted += 1
        animals_by_day[day] = n_animals
        planted_by_day[day] = n_planted
        hands_final_by_day[day] = len(farm.get("hands", []))

    # ---- per-phase aggregates ----
    def phase_agg(per_day_dict, agg="mean"):
        out = {}
        for name, lo, hi in PHASES:
            vals = [per_day_dict[d] for d in range(lo, min(hi, N_DAYS - 1) + 1) if d in per_day_dict]
            if not vals:
                out[name] = None
                continue
            out[name] = round(statistics.mean(vals), 3) if agg == "mean" else statistics.median(vals)
        return out

    crew_by_phase = phase_agg({d: statistics.mean(v) for d, v in hands_count_samples_by_day.items()})
    hires_per_day_by_phase = {}
    for name, lo, hi in PHASES:
        n_hires_in_phase = sum(1 for dday in hire_days if lo <= dday <= hi)
        n_days_in_phase = hi - lo + 1
        hires_per_day_by_phase[name] = round(n_hires_in_phase / n_days_in_phase, 3)

    ratio_hands_animals_by_phase = {}
    ratio_hands_planted_by_phase = {}
    for name, lo, hi in PHASES:
        ha, hp = [], []
        for dday in range(lo, hi + 1):
            if dday in hands_final_by_day and dday in animals_by_day and animals_by_day[dday] > 0:
                ha.append(hands_final_by_day[dday] / animals_by_day[dday])
            if dday in hands_final_by_day and dday in planted_by_day and planted_by_day[dday] > 0:
                hp.append(hands_final_by_day[dday] / planted_by_day[dday])
        ratio_hands_animals_by_phase[name] = round(statistics.mean(ha), 3) if ha else None
        ratio_hands_planted_by_phase[name] = round(statistics.mean(hp), 3) if hp else None

    moves_per_useful_by_phase = {}
    idle_share_by_phase = {}
    for name, lo, hi in PHASES:
        mv = sum(moves_count_by_day.get(d, 0) for d in range(lo, hi + 1))
        us = sum(useful_count_by_day.get(d, 0) for d in range(lo, hi + 1))
        idl = sum(idle_count_by_day.get(d, 0) for d in range(lo, hi + 1))
        tot = sum(total_unit_turns_by_day.get(d, 0) for d in range(lo, hi + 1))
        moves_per_useful_by_phase[name] = round(mv / us, 3) if us else None
        idle_share_by_phase[name] = round(idl / tot, 3) if tot else None

    plantings_per_day_by_phase = {}
    for crop in REPLANT_CROPS | ONGOING_CROPS:
        by_phase = {}
        for name, lo, hi in PHASES:
            days = [plantings_by_day_crop[crop].get(d, 0) for d in range(lo, hi + 1)]
            by_phase[name] = round(statistics.mean(days), 3) if days else None
        plantings_per_day_by_phase[crop] = by_phase

    # zone stability: Jaccard between slot's tileset on consecutive days it appears
    jaccards = []
    zone_sizes = []
    specialization = []
    for slot, byday in day_hand_tiles.items():
        days_sorted = sorted(byday.keys())
        for dday in days_sorted:
            zone_sizes.append(len(byday[dday]))
            cat = day_hand_cat[slot][dday]
            tot = sum(cat.values())
            if tot > 0:
                specialization.append(max(cat.get("animal", 0), cat.get("crop", 0)) / tot)
        for i in range(len(days_sorted) - 1):
            d0, d1 = days_sorted[i], days_sorted[i + 1]
            if d1 - d0 != 1:
                continue
            a, b = byday[d0], byday[d1]
            union = a | b
            if union:
                jaccards.append(len(a & b) / len(union))

    # pickup pattern: fraction of hand-days with >1 pickup vs exactly 1
    pk_by_slot_day = collections.defaultdict(int)
    for e in pickup_events:
        pk_by_slot_day[(e["slot"], e["day"])] += 1
    repeated = sum(1 for v in pk_by_slot_day.values() if v > 1)
    single = sum(1 for v in pk_by_slot_day.values() if v == 1)

    return dict(
        episode_id=d.get("info", {}).get("EpisodeId"),
        team=team_name, seat=seat,
        crew_by_phase=crew_by_phase,
        hires_per_day_by_phase=hires_per_day_by_phase,
        hire_hours=hires_hourly,
        land_days=land_days,
        ratio_hands_animals_by_phase=ratio_hands_animals_by_phase,
        ratio_hands_planted_by_phase=ratio_hands_planted_by_phase,
        zone_jaccard_mean=round(statistics.mean(jaccards), 3) if jaccards else None,
        zone_size_mean=round(statistics.mean(zone_sizes), 3) if zone_sizes else None,
        specialization_mean=round(statistics.mean(specialization), 3) if specialization else None,
        visit_actions_median=statistics.median(visit_action_counts) if visit_action_counts else None,
        visit_combos={"+".join(k): v for k, v in visit_combo_counter.items()},
        moves_per_useful_by_phase=moves_per_useful_by_phase,
        idle_share_by_phase=idle_share_by_phase,
        feed_hours=feed_hours, care_hours=care_hours, water_hours=water_hours,
        escapes=escapes, weed_events=weed_events,
        consec_unfed_at_daystart=consec_unfed_at_daystart,
        replant_lags=replant_lags,
        replant_same_hand_same_visit=same_hand_same_visit,
        plantings_per_day_by_phase=plantings_per_day_by_phase,
        pickup_repeated_days=repeated, pickup_single_days=single,
        order_patterns=[tuple(seq) for byday in day_hand_order_seq.values() for seq in byday.values() if seq],
    )
