"""experiments/splice/gate.py <candidate.py> [--workers N] [--seeds dev|holdout]

The kill-criterion harness for the splice build (docs/ENDGAME/splice_build.md
"Gates"). Runs <candidate.py> against the five fixed opponents plus two
self-play buckets, on 16 seeds in BOTH seats (32 games per opponent), and
prints win/loss/draw counts, margin stats and the R2.3 executor envelope --
then a PASS/FAIL line per gate against the thresholds in splice_build.md.

Seeds: --seeds dev -> 900..915 (16). --seeds holdout -> 1000..1015 (16).
Use dev while iterating; holdout is the less-frequently-spent check before a
kill/ship decision (same reason paired_compare.py separates `pass`/`starter`
from a final read).

Opponents (fixed, not configurable -- these are the contract's five, and every
one of them must be present on disk -- see "Missing opponents" below):
    W3           agents/w3_herdsafe2700.py           (the kill criterion, >= 16/32)
    W1           agents/w1_v15stack_race44.py         (>= 20/32)
    W0           agents/w0_v15stack_control.py        (>= 20/32)
    REACTIVE_V1  agents/washamba_reactive_v1.py        (>= 20/32; committed to the repo)
    FARM2945     agents/washamba_base_v1.py           (>= 20/32; public "2945 Farm" --
                 added 2026-09-25, the 2945 Farm and v15stack forks make up about half
                 the field we must climb, field_families_2026-09-25.md)

Both seats: each of the 16 seeds is played twice against every opponent, once
with the candidate at seat 0 and once at seat 1 (CLAUDE.md: seats are not
symmetric -- identical code gives seat 0 a few hundred less -- so this
harness plays both and reports the pooled 32, same convention as
experiments/tapes/run_agents.py and CLAUDE.md's head_to_head.py guidance).

Missing opponents: this is a gate, not a survey -- a missing opponent file
fails the whole run loudly (clear message, non-zero exit) rather than
quietly shrinking the field, so a bad checkout or a stale path can never be
mistaken for "passed with 4 opponents instead of 5".

Also runs, on the same seed set:
    candidate self-play   -- absolute bank, both sides identical code, one
                              game per seed (a self-play game already reports
                              both seats at once, so this does not double)
    W3 self-play           -- reference point for the same gate; cached under
                              experiments/splice/results/ since it does not
                              depend on the candidate, and reused across runs.

Executor envelope (R2.3, splice_build.md "Gates"): aggregated across every
game the candidate actually played (five opponent buckets + its own
self-play), using ONLY turns whose deciding observation has
obs["step"] >= WB_HANDOVER_STEP (192) -- i.e. only turns the controller (not
the base agent) was responsible for. See _compute_envelope() for exactly how
each metric is derived from env.steps; the short version:
    idle share       = PASS turns / unit-turns (farmer + every hand)
    waters/day       = WATER actions / distinct days in the window
    care/animal-day  = distinct (day, animal-tile) with >=1 real CARE,
                        divided by the number of animal-tiles alive that day,
                        summed over days
    duplicate CARE   = CARE attempts beyond the first on the same
                        (day, animal-tile) -- the engine no-ops these
                        (kaggriculture.py: `if tile["cared_today"]: return`),
                        so this is a lower bound on wasted turns, not an
                        upper one: two units CAREing the same tile in the
                        SAME turn both look "first" from a pre-action
                        observation, and this still catches that case because
                        it groups by (day, tile), not by turn.
    escapes          = a tile that had "animal" in the previous observation
                        and, at the same (x, y) in the next one, is a bare
                        PASTURE/COOP with no "animal" key (kaggriculture.py
                        comment at the FEED handler: "Animal escapes;
                        structure remains" -- DIG cannot remove a placed
                        animal, so this transition is unambiguous)
    weeds at end     = WEED tiles in the final observation
    sold/price       = per product, units actually transacted that turn
                        (NOT the order's declared quantity -- see below),
                        valued at that item's `market["prices"]` quote from
                        the PRE-action observation (sell price is quoted
                        pre-sell).

                        The declared quantity in a SELL order is not the
                        transacted quantity: tape-family agents (every
                        opponent this harness uses) issue "sell everything"
                        liquidation orders that declare huge, often
                        round-number quantities (997, 1000 seen directly in
                        a real trace) regardless of what they actually hold;
                        the engine silently sells only what's held and
                        no-ops the rest. Trusting the declared number
                        inflated "opponent sold" by 7x+ in one measured case
                        (splice-b-controller, gate_splice_b0800 -- W3
                        FERTILIZER read ~1566/game against their own
                        ~335/game ground truth from an instrumented
                        _commit_unit log). Fixed by capping each declared
                        quantity against a real, verifiable bound instead of
                        trusting it: the candidate's own orders are capped
                        by the candidate's own visible pre-turn shed stock
                        (exact); the opponent's orders -- whose shed is
                        never visible (CLAUDE.md) -- are capped by that
                        turn's own market-inventory rise, net of whatever
                        the candidate is already verified to have sold of
                        that item the same turn (SELL is the only action
                        that can raise market inventory, so this is a real
                        physical upper bound from public data alone, not a
                        reconstruction of engine internals). Still a
                        diagnostic, not one of the pass/fail gates, but now
                        bounded rather than fabricated -- verified against
                        the same trace that exposed the bug: a declared
                        "SELL FERTILIZER 997" against an unmoved market
                        inventory now correctly counts as 0, not 997.

Output: a summary block per opponent/bucket to stdout, then a PASS/FAIL
verdict per gate, and one raw jsonl line per game under
experiments/splice/results/ (gitignored-by-convention scratch, matching
experiments/endgame/rep/ -- not committed).

Usage:
    .venv/Scripts/python.exe experiments/splice/gate.py agents/washamba_splice_v1.py
    .venv/Scripts/python.exe experiments/splice/gate.py experiments/splice/dev_agent.py --seeds holdout --workers 3
"""
import argparse
import itertools
import json
import os
import statistics
import sys
import time
from collections import Counter
from multiprocessing import Pool

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(os.path.dirname(THIS_DIR))
AGENTS_DIR = os.path.join(REPO_ROOT, "agents")
RESULTS_DIR = os.path.join(THIS_DIR, "results")

EPISODE_STEPS = 720
# Must match dev_agent.py's WB_HANDOVER_STEP and splice_build.md's "Shape".
# Duplicated rather than imported: importing dev_agent.py for one constant
# would also run its base-agent load and controller-construction side
# effects, coupling this harness to files it should be able to gate even
# when they are broken.
WB_HANDOVER_STEP = 192

SEED_SETS = {
    "dev": list(range(900, 916)),        # 900..915, 16 seeds
    "holdout": list(range(1000, 1016)),  # 1000..1015, 16 seeds
}

# (bucket name, agent file, minimum wins of 32 -- 16 seeds x both seats).
OPPONENTS = [
    ("W3", "w3_herdsafe2700.py", 16),
    ("W1", "w1_v15stack_race44.py", 20),
    ("W0", "w0_v15stack_control.py", 20),
    ("REACTIVE_V1", "washamba_reactive_v1.py", 20),
    ("FARM2945", "washamba_base_v1.py", 20),
]

ENVELOPE_GATES = {
    "idle_share": ("<=", 0.05),
    "waters_per_day": (">=", 40.0),
    "care_per_animal_day": (">=", 0.8),
    "care_duplicates": ("==", 0),
}

# --- exact opponent sell-revenue reconstruction (splice-b-controller's fix,
# 2026-09-25 -- see _compute_envelope's "sold/price" docs above for the bug
# this replaces). Every constant below is verified directly against the
# installed kaggriculture.py; gate.py is local-only and never ships, so
# depending on the engine's own fixed-cost tables (unlike price_model.py,
# which must stay engine-import-free because it does ship) is fine.
FARM_HAND_COST_MULT = 1  # engine default; _play_one never overrides farmHandCostMult
LAND_ORDER = ["NE", "SW", "SE"]
LAND_PRICES = [1000, 2000, 4000]
SEED_COST = {"WHEAT": 10, "CARROT": 20, "TOMATO": 50, "STRAWBERRY": 100, "MELON": 80}
ANIMAL_COST = {"GOOSE": 300, "COW": 400, "SHEEP": 500}


def _fib(n):
    """kaggriculture.py's _fib: indexed so _fib(0)=1, _fib(1)=1, _fib(2)=2..."""
    a, b = 1, 1
    for _ in range(n):
        a, b = b, a + b
    return a


_PRICE_MODEL = None


def _price_model():
    """price_model.py lives next to this file; imported the same bare way
    dev_agent.py does, reusing Builder A's already-tested, test-suite-checked
    market_price port instead of reimplementing the price curve here."""
    global _PRICE_MODEL
    if _PRICE_MODEL is None:
        if THIS_DIR not in sys.path:
            sys.path.insert(0, THIS_DIR)
        import price_model as _wb_price_model_mod
        _PRICE_MODEL = _wb_price_model_mod.WB_PriceModel()
    return _PRICE_MODEL


def _invert_sell_revenue(item, inventory, target_revenue):
    """The exact qty whose WB_PriceModel.sell_revenue(item, inventory, qty)
    equals target_revenue. Both sides are sums of integer per-unit prices
    (sell_revenue already matches the engine's own floor-price behavior --
    price_model.py: "at the floor the inventory stops moving: the rest pay
    $1 each"), so for a clean, single-seller curve-walk this is exact, not
    approximate. Returns None if nothing in a generous range matches --
    meaning the turn was not actually clean (e.g. a shed/order cap the money
    accounting didn't predict) -- the caller falls back to the lower-bound
    method for that turn instead of trusting a wrong exact-looking number."""
    if target_revenue < 0:
        return None
    if target_revenue == 0:
        return 0
    pm = _price_model()
    lo, hi = 0, 1
    while pm.sell_revenue(item, inventory, hi) < target_revenue and hi < 5000:
        hi *= 2
    hi = min(hi, 5000)
    if pm.sell_revenue(item, inventory, hi) < target_revenue:
        return None
    while lo < hi:
        mid = (lo + hi) // 2
        if pm.sell_revenue(item, inventory, mid) < target_revenue:
            lo = mid + 1
        else:
            hi = mid
    return lo if pm.sell_revenue(item, inventory, lo) == target_revenue else None


def _play_one(job):
    """Run one episode. Returns a small, jsonl-safe dict -- never env.steps
    itself. Top-level and picklable: multiprocessing on Windows uses
    'spawn', which re-imports this module in each worker and requires the
    target function be a plain module-level name (matches
    experiments/tapes/run_agents.py's own `def job(args):` convention)."""
    bucket, seed, seat0_path, seat1_path, cand_seat, want_envelope = job
    from kaggle_environments import make

    env = make("kaggriculture", configuration={"episodeSteps": EPISODE_STEPS, "seed": seed}, debug=False)
    env.run([seat0_path, seat1_path])
    final = env.steps[-1]
    cand_state, opp_state = final[cand_seat], final[1 - cand_seat]
    result = {
        "bucket": bucket,
        "seed": seed,
        "cand_seat": cand_seat,
        "cand_bank": cand_state.reward,
        "opp_bank": opp_state.reward,
        "cand_status": cand_state.status,
        "opp_status": opp_state.status,
    }
    if result["cand_bank"] is not None and result["opp_bank"] is not None:
        result["margin"] = result["cand_bank"] - result["opp_bank"]
    else:
        result["margin"] = None
    if want_envelope:
        result["envelope"] = _compute_envelope(env.steps, cand_seat)
    return result


def _compute_envelope(steps, seat):
    """See module docstring for the exact derivation of every field."""
    n = len(steps)
    opp_seat = 1 - seat
    unit_turns = 0
    pass_turns = 0
    water_actions = 0
    days_seen = set()
    animal_day_days_counted = set()
    animal_day_total = 0
    care_groups = Counter()  # (day, x, y) -> attempts while genuinely on an animal tile
    escapes = 0
    cand_sold_qty = Counter()
    cand_sold_value = Counter()
    opp_sold_qty = Counter()
    opp_sold_value = Counter()

    for i in range(1, n):
        prev_state = steps[i - 1][seat]
        curr_state = steps[i][seat]
        prev_obs = prev_state.observation
        curr_obs = curr_state.observation

        step_no = prev_obs.get("step", i - 1)
        if step_no < WB_HANDOVER_STEP:
            continue

        day = prev_obs.get("day")
        days_seen.add(day)

        farm = prev_obs["farms"][seat]
        tiles = farm["tiles"]

        if day not in animal_day_days_counted:
            animal_day_days_counted.add(day)
            animal_day_total += sum(1 for row in tiles for t in row if isinstance(t, dict) and "animal" in t)

        action = curr_state.get("action") or {}
        farmer_action = action.get("farmer") or []
        hand_actions = action.get("hands") or []
        positions = [farm["farmer"]] + list(farm["hands"])
        acts = [farmer_action] + list(hand_actions)

        # zip_longest, not zip: if the controller emits fewer hand actions
        # than hands actually exist (a real bug worth surfacing, not hiding),
        # plain zip() would silently drop those unit-turns from the
        # denominator entirely instead of counting them as idle. A missing
        # action is a PASS to the engine, so fillvalue=[] falls straight into
        # the existing "not act" -> pass_turns branch below.
        for pos, act in itertools.zip_longest(positions, acts, fillvalue=[]):
            if not isinstance(pos, (list, tuple)) or len(pos) != 2:
                # More actions than real units exist (shouldn't happen) --
                # nothing to attribute this one to.
                continue
            unit_turns += 1
            verb = act[0] if act else "PASS"
            if verb == "WATER":
                water_actions += 1
            elif verb == "CARE":
                x, y = pos
                tile = tiles[y][x]
                if isinstance(tile, dict) and "animal" in tile:
                    care_groups[(day, x, y)] += 1
                # A CARE issued while not standing on an animal tile is a
                # plain no-op, not a "duplicate" -- left out of this count.
            elif verb in ("PASS", "NONE") or not act:
                pass_turns += 1

        # Escapes: same (x, y) had an animal in the pre-action observation
        # and does not in the resulting one, structure intact.
        curr_tiles = curr_obs["farms"][seat]["tiles"]
        for y, row in enumerate(tiles):
            for x, t in enumerate(row):
                if isinstance(t, dict) and "animal" in t:
                    ct = curr_tiles[y][x]
                    if isinstance(ct, dict) and ct.get("kind") in ("PASTURE", "COOP") and "animal" not in ct:
                        escapes += 1

        # Sold qty/price. See this function's docstring header (and the
        # module docstring's "sold/price" section) for the full history:
        # the original bug trusted each order's DECLARED quantity, which
        # tape-family liquidation orders inflate arbitrarily; a first fix
        # bounded it by market-inventory movement, which splice-b-controller
        # then showed is a systematic UNDERcount (drain, BUY_PRODUCT netting
        # and floor-price sales all move money without moving inventory the
        # same way). This is their proposed fix: reconstruct the opponent's
        # exact sell revenue from their PUBLIC money delta net of every
        # other public, fixed-price spend category, then invert revenue to
        # quantity via price_model.py's own tested curve-walker.
        prices = prev_obs["market"].get("prices", {})
        prev_inv = prev_obs["market"].get("inventory", {})
        curr_inv = curr_obs["market"].get("inventory", {})
        shed = prev_obs["private"].get("shed", {})
        candidate_sold_this_turn = Counter()
        candidate_items_this_turn = set()

        for order in (action.get("market") or []):
            if order and order[0] == "SELL":
                item = order[1]
                candidate_items_this_turn.add(item)
                declared = order[2] if len(order) > 2 else 1
                # Candidate's own shed IS visible for our own seat -- exact,
                # not an approximation (unlike the opponent case below).
                qty = max(0, min(declared, shed.get(item, 0) - candidate_sold_this_turn[item]))
                if qty <= 0:
                    continue
                cand_sold_qty[item] += qty
                cand_sold_value[item] += _price_model().sell_revenue(item, prev_inv.get(item, 0), qty)
                candidate_sold_this_turn[item] += qty
            elif order and order[0] == "BUY_PRODUCT":
                candidate_items_this_turn.add(order[1])

        opp_action = steps[i][opp_seat].get("action") or {}
        opp_orders = opp_action.get("market") or []
        opp_sell_items = {o[1] for o in opp_orders if o and o[0] == "SELL"}
        opp_has_buy_product = any(o and o[0] == "BUY_PRODUCT" for o in opp_orders)

        # Exact known spend on every category besides SELL/BUY_PRODUCT, all
        # of which are public and fixed-price (HIRE: fib(hires_today), fully
        # public; BUY_LAND: LAND_PRICES indexed off the public
        # unlocked_quadrants count; BUY_SEED/BUY_ANIMAL: CROPS/ANIMALS'
        # fixed per-unit cost -- unlike SELL/BUY_PRODUCT these don't share a
        # market-moving curve with the other player, so a running-money
        # simulation of just the opponent's own orders determines exactly
        # which succeeded, kaggriculture.py's own all-or-nothing-per-unit
        # affordability check). Not modeled: BUY_ANIMAL/BUY_PRODUCT can also
        # silently fail on the opponent's OWN shed being full (never
        # visible) -- rare, and caught safely by _invert_sell_revenue
        # returning None (falls back) rather than emitting a wrong number.
        opp_farm_prev = prev_obs["farms"][opp_seat]
        opp_money_delta = curr_obs["farms"][opp_seat]["money"] - opp_farm_prev["money"]
        hires_before = opp_farm_prev.get("hires_today", 0)
        n_land_before = len(opp_farm_prev.get("unlocked_quadrants") or ["NW"]) - 1
        running_money = opp_farm_prev["money"]
        known_spend = 0.0
        hire_n = land_n = 0
        for order in opp_orders:
            if not order:
                continue
            op = order[0]
            if op == "HIRE":
                cost = FARM_HAND_COST_MULT * _fib(hires_before + hire_n)
                if running_money >= cost:
                    known_spend += cost
                    running_money -= cost
                    hire_n += 1
            elif op == "BUY_LAND":
                idx = n_land_before + land_n
                if 0 <= idx < len(LAND_PRICES) and running_money >= LAND_PRICES[idx]:
                    known_spend += LAND_PRICES[idx]
                    running_money -= LAND_PRICES[idx]
                    land_n += 1
            elif op in ("BUY_SEED", "BUY_ANIMAL"):
                item = order[1] if len(order) > 1 else None
                declared = order[2] if len(order) > 2 else 1
                unit_cost = (SEED_COST if op == "BUY_SEED" else ANIMAL_COST).get(item)
                if unit_cost:
                    filled = min(declared, int(running_money // unit_cost))
                    known_spend += filled * unit_cost
                    running_money -= filled * unit_cost

        # "Clean": exactly one item sold, no same-turn BUY_PRODUCT (a second,
        # unmodeled market-moving order for the same or another item), and
        # the candidate didn't ALSO trade that item this turn -- a shared
        # price curve between two sellers in the same slot can't be split
        # from money alone (price_model.sell_revenue's own docstring:
        # "with no competing same-slot seller").
        clean = (
            len(opp_sell_items) == 1
            and not opp_has_buy_product
            and not (opp_sell_items & candidate_items_this_turn)
        )
        exact_qty = None
        if clean:
            exact_item = next(iter(opp_sell_items))
            target_revenue = opp_money_delta + known_spend
            exact_qty = _invert_sell_revenue(exact_item, prev_inv.get(exact_item, 0), target_revenue)

        if clean and exact_qty is not None:
            if exact_qty > 0:
                opp_sold_qty[exact_item] += exact_qty
                opp_sold_value[exact_item] += target_revenue
        else:
            # Fallback for anything not clean: the same market-inventory
            # lower bound as before (still a real, if pessimistic, physical
            # bound -- SELL is the only action that raises market
            # inventory).
            opp_sold_this_turn = Counter()
            for order in opp_orders:
                if order and order[0] == "SELL":
                    item = order[1]
                    declared = order[2] if len(order) > 2 else 1
                    inv_rise = curr_inv.get(item, 0) - prev_inv.get(item, 0)
                    room = max(0, inv_rise - candidate_sold_this_turn.get(item, 0) - opp_sold_this_turn[item])
                    qty = max(0, min(declared, room))
                    if qty <= 0:
                        continue
                    opp_sold_this_turn[item] += qty
                    opp_sold_qty[item] += qty
                    opp_sold_value[item] += qty * prices.get(item, 0)

    final_tiles = steps[-1][seat].observation["farms"][seat]["tiles"]
    weeds_at_end = sum(1 for row in final_tiles for t in row if isinstance(t, dict) and t.get("kind") == "WEED")
    care_duplicates = sum(c - 1 for c in care_groups.values() if c > 1)

    return {
        "unit_turns": unit_turns,
        "pass_turns": pass_turns,
        "water_actions": water_actions,
        "days_in_window": len(days_seen),
        "animal_days": animal_day_total,
        "care_legit_events": len(care_groups),
        "care_duplicates": care_duplicates,
        "escapes": escapes,
        "weeds_at_end": weeds_at_end,
        "cand_sold_qty": dict(cand_sold_qty),
        "cand_sold_value": dict(cand_sold_value),
        "opp_sold_qty": dict(opp_sold_qty),
        "opp_sold_value": dict(opp_sold_value),
    }


def _sum_envelopes(envelopes):
    total = {
        "unit_turns": 0, "pass_turns": 0, "water_actions": 0, "days_in_window": 0,
        "animal_days": 0, "care_legit_events": 0, "care_duplicates": 0, "escapes": 0,
    }
    weeds = []
    cand_sold_qty = Counter()
    cand_sold_value = Counter()
    opp_sold_qty = Counter()
    opp_sold_value = Counter()
    for e in envelopes:
        for k in total:
            total[k] += e[k]
        weeds.append(e["weeds_at_end"])
        cand_sold_qty.update(e["cand_sold_qty"])
        cand_sold_value.update(Counter(e["cand_sold_value"]))
        opp_sold_qty.update(e["opp_sold_qty"])
        opp_sold_value.update(Counter(e["opp_sold_value"]))
    total["weeds_at_end_mean"] = statistics.mean(weeds) if weeds else 0.0
    total["weeds_at_end_max"] = max(weeds) if weeds else 0
    total["cand_sold_qty"] = dict(cand_sold_qty)
    total["opp_sold_qty"] = dict(opp_sold_qty)
    total["cand_avg_price"] = {
        p: round(cand_sold_value[p] / cand_sold_qty[p], 1) for p in cand_sold_qty if cand_sold_qty[p]
    }
    total["opp_avg_price"] = {
        p: round(opp_sold_value[p] / opp_sold_qty[p], 1) for p in opp_sold_qty if opp_sold_qty[p]
    }
    return total


def _jsonl_path(candidate_path, seed_set_name):
    os.makedirs(RESULTS_DIR, exist_ok=True)
    base = os.path.splitext(os.path.basename(candidate_path))[0]
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    return os.path.join(RESULTS_DIR, f"gate_{base}_{seed_set_name}_{stamp}.jsonl")


def _w3_reference_path(seed_set_name):
    os.makedirs(RESULTS_DIR, exist_ok=True)
    return os.path.join(RESULTS_DIR, f"w3_selfplay_reference_{seed_set_name}.jsonl")


def _load_w3_reference(seed_set_name, seeds):
    path = _w3_reference_path(seed_set_name)
    if not os.path.exists(path):
        return None
    rows = []
    try:
        with open(path) as f:
            for line in f:
                line = line.strip()
                if line:
                    rows.append(json.loads(line))
    except (OSError, json.JSONDecodeError):
        return None
    have_seeds = {r["seed"] for r in rows}
    if have_seeds != set(seeds):
        return None
    return rows


def _cache_w3_reference(seed_set_name, rows):
    with open(_w3_reference_path(seed_set_name), "w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")


def _fmt_margin_stats(games):
    margins = [g["margin"] for g in games if g["margin"] is not None]
    cand_banks = [g["cand_bank"] for g in games if g["cand_bank"] is not None]
    wins = sum(1 for m in margins if m > 0)
    losses = sum(1 for m in margins if m < 0)
    draws = sum(1 for m in margins if m == 0)
    return {
        "n": len(games),
        "wins": wins, "losses": losses, "draws": draws,
        "mean_margin": statistics.mean(margins) if margins else float("nan"),
        "median_margin": statistics.median(margins) if margins else float("nan"),
        "worst_margin": min(margins) if margins else float("nan"),
        "min_bank": min(cand_banks) if cand_banks else float("nan"),
    }


def _flag(games, label):
    flags = []
    for g in games:
        if g["cand_bank"] == 3000 or g["cand_status"] != "DONE":
            flags.append(f"{label} seed={g['seed']} cand_seat={g['cand_seat']}: "
                         f"cand bank={g['cand_bank']} status={g['cand_status']}")
        if g["opp_bank"] == 3000 or g["opp_status"] != "DONE":
            flags.append(f"{label} seed={g['seed']} cand_seat={g['cand_seat']}: "
                         f"opp bank={g['opp_bank']} status={g['opp_status']}")
    return flags


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("candidate", help="path to the candidate agent .py file")
    ap.add_argument("--workers", type=int, default=3, help="max worker processes (default 3 -- CPU is shared)")
    ap.add_argument("--seeds", choices=["dev", "holdout"], default="dev")
    args = ap.parse_args()

    candidate_path = os.path.abspath(args.candidate)
    if not os.path.exists(candidate_path):
        sys.exit(f"gate.py: candidate not found: {candidate_path}")
    if args.workers > 3:
        print(f"gate.py: --workers {args.workers} > 3 -- CPU is shared with two other builders; "
              f"proceeding anyway since it was explicit, but 3 is the agreed ceiling.")

    seeds = SEED_SETS[args.seeds]
    w3_path = os.path.join(AGENTS_DIR, "w3_herdsafe2700.py")

    print(f"gate.py: {os.path.relpath(candidate_path, REPO_ROOT)}  seeds={args.seeds} ({seeds[0]}-{seeds[-1]})  "
          f"workers={args.workers}\n")

    # This is a gate, not a survey: every opponent must be on disk, or the
    # whole run fails loudly rather than quietly passing on a smaller field
    # (splice_build.md: "A missing opponent file must fail the gate loudly,
    # never skip it silently").
    missing = [(name, os.path.join(AGENTS_DIR, filename)) for name, filename, _ in OPPONENTS
               if not os.path.exists(os.path.join(AGENTS_DIR, filename))]
    if missing:
        lines = "\n".join(f"  {name}: {path}" for name, path in missing)
        sys.exit(f"gate.py: FAILED -- missing opponent file(s), refusing to run a partial gate:\n{lines}")

    # Build every job for the whole run up front and submit it to ONE pool.
    # Earlier version opened a fresh Pool per bucket (6 of them); on Windows
    # each Pool spawns brand-new worker processes ('spawn', not 'fork'), and
    # each of those pays kaggle_environments' own import cost again -- six
    # times the fixed overhead for no benefit. One pool, one batch of
    # multiprocessing spawn overhead, however many buckets are in play.
    jobs = []
    for name, filename, min_wins in OPPONENTS:
        opp_path = os.path.join(AGENTS_DIR, filename)
        for seed in seeds:
            for cand_seat in (0, 1):
                seat_paths = [None, None]
                seat_paths[cand_seat] = candidate_path
                seat_paths[1 - cand_seat] = opp_path
                jobs.append((name, seed, seat_paths[0], seat_paths[1], cand_seat, True))

    jobs += [("SELFPLAY", seed, candidate_path, candidate_path, 0, True) for seed in seeds]

    w3_cached = _load_w3_reference(args.seeds, seeds)
    if w3_cached is not None:
        print(f"(using cached W3 self-play reference: {_w3_reference_path(args.seeds)})\n")
    else:
        jobs += [("W3_SELFPLAY_REF", seed, w3_path, w3_path, 0, False) for seed in seeds]

    with Pool(args.workers) as pool:
        results = pool.map(_play_one, jobs)

    by_bucket = {}
    for r in results:
        by_bucket.setdefault(r["bucket"], []).append(r)

    all_flags = []
    all_games = []  # every game the candidate actually played, for the jsonl dump
    candidate_envelopes = []

    # --- opponent buckets (every one of OPPONENTS: missing files already exited above) ---
    for name, _filename, min_wins in OPPONENTS:
        games = by_bucket[name]
        all_games.extend(games)
        candidate_envelopes.extend(g["envelope"] for g in games)
        stats = _fmt_margin_stats(games)
        flags = _flag(games, name)
        all_flags.extend(flags)
        verdict = "PASS" if stats["wins"] >= min_wins else "FAIL"
        print(f"[{name}] {stats['wins']}-{stats['losses']}-{stats['draws']} of {stats['n']}  "
              f"(need >= {min_wins}/32 -> {verdict})")
        print(f"        mean margin {stats['mean_margin']:+,.0f}   median {stats['median_margin']:+,.0f}   "
              f"worst {stats['worst_margin']:+,.0f}   min bank {stats['min_bank']:,.0f}")
        if flags:
            print(f"        FLAGGED: {len(flags)} game(s) with reward==3000 or non-DONE status")
            for line in flags:
                print(f"          {line}")
        print()

    # --- candidate self-play (absolute bank) ---
    self_games = by_bucket["SELFPLAY"]
    all_games.extend(self_games)
    candidate_envelopes.extend(g["envelope"] for g in self_games)
    self_banks = [g["cand_bank"] for g in self_games] + [g["opp_bank"] for g in self_games]
    self_flags = _flag(self_games, "SELFPLAY")
    all_flags.extend(self_flags)
    print(f"[SELFPLAY] candidate vs itself, {len(self_games)} seeds, both sides pooled ({len(self_banks)} values)")
    print(f"           mean {statistics.mean(self_banks):,.0f}   median {statistics.median(self_banks):,.0f}   "
          f"min {min(self_banks):,.0f}   max {max(self_banks):,.0f}")
    if self_flags:
        print(f"           FLAGGED: {len(self_flags)}")
        for line in self_flags:
            print(f"             {line}")
    print()

    # --- W3 self-play reference (cached; independent of the candidate) ---
    if w3_cached is not None:
        w3_rows = w3_cached
    else:
        w3_rows = by_bucket["W3_SELFPLAY_REF"]
        _cache_w3_reference(args.seeds, w3_rows)
    w3_banks = [r["cand_bank"] for r in w3_rows] + [r["opp_bank"] for r in w3_rows]
    print(f"[W3_SELFPLAY_REF] {len(w3_rows)} seeds, both sides pooled ({len(w3_banks)} values)")
    print(f"                  mean {statistics.mean(w3_banks):,.0f}   median {statistics.median(w3_banks):,.0f}   "
          f"min {min(w3_banks):,.0f}   max {max(w3_banks):,.0f}")
    selfplay_verdict = "PASS" if statistics.mean(self_banks) >= statistics.mean(w3_banks) else "FAIL"
    print(f"                  candidate self-play mean {statistics.mean(self_banks):,.0f} "
          f"{'>=' if selfplay_verdict == 'PASS' else '<'} W3 self-play mean {statistics.mean(w3_banks):,.0f} "
          f"-> {selfplay_verdict}")
    print()

    # --- executor envelope (R2.3), aggregated across every game the candidate played ---
    agg = _sum_envelopes(candidate_envelopes)
    idle_share = agg["pass_turns"] / agg["unit_turns"] if agg["unit_turns"] else float("nan")
    waters_per_day = agg["water_actions"] / agg["days_in_window"] if agg["days_in_window"] else float("nan")
    care_per_animal_day = agg["care_legit_events"] / agg["animal_days"] if agg["animal_days"] else float("nan")
    envelope_values = {
        "idle_share": idle_share,
        "waters_per_day": waters_per_day,
        "care_per_animal_day": care_per_animal_day,
        "care_duplicates": agg["care_duplicates"],
    }
    print(f"[EXECUTOR ENVELOPE] steps >= {WB_HANDOVER_STEP} only, aggregated over "
          f"{len(candidate_envelopes)} games ({agg['unit_turns']:,} unit-turns, {agg['days_in_window']} "
          f"candidate-days summed across games)")
    print(f"        idle share            {idle_share:.1%}   (gate: <= 5%)")
    print(f"        waters/day            {waters_per_day:.1f}   (gate: >= 40)")
    print(f"        care/animal-day       {care_per_animal_day:.2f}   (gate: >= 0.8)")
    print(f"        duplicate CARE        {agg['care_duplicates']}   (gate: == 0)")
    print(f"        animal escapes        {agg['escapes']}")
    print(f"        weeds at end          mean {agg['weeds_at_end_mean']:.1f}   max {agg['weeds_at_end_max']}")
    print(f"        candidate sold (qty)  {agg['cand_sold_qty']}")
    print(f"        candidate avg price   {agg['cand_avg_price']}")
    print(f"        opponent sold (qty)   {agg['opp_sold_qty']}")
    print(f"        opponent avg price    {agg['opp_avg_price']}")
    for key, (op, threshold) in ENVELOPE_GATES.items():
        val = envelope_values[key]
        ok = (val <= threshold) if op == "<=" else (val >= threshold) if op == ">=" else (val == threshold)
        print(f"        gate {key:22} {'PASS' if ok else 'FAIL'}  ({val:.3g} {op} {threshold})")
    print()

    if all_flags:
        print(f"TOTAL FLAGGED GAMES: {len(all_flags)} (reward==3000 or non-DONE status -- see per-bucket detail above)")
    else:
        print("No flagged games (no reward==3000, no non-DONE status).")

    out_path = _jsonl_path(candidate_path, args.seeds)
    with open(out_path, "a") as f:
        for g in all_games:
            f.write(json.dumps(g) + "\n")
    print(f"\nraw results written to {os.path.relpath(out_path, REPO_ROOT)} ({len(all_games)} games)")


if __name__ == "__main__":
    main()
