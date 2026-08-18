"""Instrumentation + structural validation for
experiments/replay_shape_agent.py (Track C, Issue #21).

`trace_episode()` runs one real episode and records, once per day, every
metric the task asked for: cash, land count, crew count, animal count by
species, planted tiles, harvested units (cumulative), shed inventory by
product, sell orders that day, units sold that day, revenue that day, and
cumulative bank. `trace_both()` does the same for BOTH seats from a single
episode - used by experiments/replay_shape_matchup.py to compare our own
agent against this one without running the game twice.

Two passes, kept deliberately separate rather than merged into one clever
loop, to avoid a subtle timing bug: `env.steps[i].action` is the action
CHOSEN FROM `env.steps[i-1].observation`, not `env.steps[i].observation`
(verified directly against a real SELL order's effect on shed quantity -
see experiments/pricing_cadence_v1_2_mechanism_audit_report.md, where this
was first found). State snapshots (cash/tiles/crew/animals/shed) don't
need that pairing at all - they're read straight off each day's own
observation. Only per-day action tallies (sell orders, harvests) do.

Both seats' PUBLIC farm state (tiles, money, hands) is visible from either
seat's own observation - only the shed/inventory PRIVATE state requires
reading that seat's own `obs["private"]` (CLAUDE.md: "opponent's shed is
never visible"). So a two-sided trace still only needs one `env.run()` -
`extract_trajectory(steps, seat)` just reads `farms[seat]` off whichever
seat's observation, and `steps[i][seat]` for that seat's own actions/private.
"""
import sys

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from kaggle_environments import make  # noqa: E402

TURNS_PER_DAY = 24

# Base prices (MARKET_PARAMS in the engine) for the products this agent
# actually trades - used by validate_market_pressure to tell "the market
# got contested" apart from "nobody sold enough to move it".
BASE_PRICES = {"WHEAT": 25, "STRAWBERRY": 120, "MELON": 250, "MILK": 160, "WOOL": 200}


def _owned_tiles(farm):
    return sum(1 for row in farm["tiles"] for t in row if t != "LOCKED")


def _planted_tiles(farm):
    return sum(1 for row in farm["tiles"] for t in row if isinstance(t, dict) and t.get("kind") == "PLANT")


def _placed_animals(farm):
    counts = {}
    for row in farm["tiles"]:
        for t in row:
            if isinstance(t, dict) and "animal" in t:
                counts[t["animal"]] = counts.get(t["animal"], 0) + 1
    return counts


def run_episode(agent_a_path, agent_b_path, seed, episode_steps=720):
    """Runs one real episode, agent_a in seat 0 / agent_b in seat 1.
    Returns the raw `env.steps` for extract_trajectory()/trace_*() to read -
    factored out so a two-sided trace only pays for one `env.run()`."""
    env = make("kaggriculture", configuration={"episodeSteps": episode_steps, "seed": seed}, debug=False)
    env.run([agent_a_path, agent_b_path])
    return env.steps


def extract_trajectory(steps, seat):
    """Per-day instrumentation record for one seat (0 or 1) out of an
    already-run episode's `steps`."""
    n = len(steps)

    # Pass 1: per-day action tallies. steps[i][seat].action was chosen from
    # steps[i-1][seat].observation, so it belongs to that observation's day.
    per_day_sells = {}
    per_day_units = {}
    per_day_revenue = {}
    per_day_harvests = {}
    prior_obs = steps[0][seat].observation
    for i in range(1, n):
        action = steps[i][seat].get("action") or {}
        prior_obs = steps[i - 1][seat].observation
        day = prior_obs.get("day", 0)
        for order in action.get("market") or []:
            if order and order[0] == "SELL" and len(order) >= 3:
                per_day_sells[day] = per_day_sells.get(day, 0) + 1
                per_day_units[day] = per_day_units.get(day, 0) + order[2]
                price = prior_obs["market"]["prices"].get(order[1], 0)
                per_day_revenue[day] = per_day_revenue.get(day, 0.0) + order[2] * price
        for a in [action.get("farmer") or []] + list(action.get("hands") or []):
            if a and a[0] == "HARVEST":
                per_day_harvests[day] = per_day_harvests.get(day, 0) + 1

    # Pass 2: end-of-day state snapshots, read directly off each day's own
    # last available observation (hour 23, or the final step if the
    # episode is shorter).
    last_day = prior_obs.get("day", 0) if n > 1 else 0
    days = []
    cum_harvested = 0
    for day in range(last_day + 1):
        idx = min(day * TURNS_PER_DAY + (TURNS_PER_DAY - 1), n - 1)
        obs = steps[idx][seat].observation
        farm = obs["farms"][seat]
        private = obs["private"]
        cum_harvested += per_day_harvests.get(day, 0)
        days.append({
            "day": day,
            "cash": farm["money"],
            "land_tiles": _owned_tiles(farm),
            "crew": len(farm.get("hands") or []),
            "animals_placed": _placed_animals(farm),
            "planted_tiles": _planted_tiles(farm),
            "harvested_cumulative": cum_harvested,
            "shed_inventory": dict(private.get("shed") or {}),
            "sell_orders_today": per_day_sells.get(day, 0),
            "units_sold_today": per_day_units.get(day, 0),
            "revenue_today": per_day_revenue.get(day, 0.0),
            "cumulative_bank": farm["money"],
            "market_prices": {p: obs["market"]["prices"].get(p, 0) for p in BASE_PRICES},
        })
    # Final reward is the authoritative end-of-season bank (matches what
    # the engine actually scores; the last snapshot's "money" should
    # already agree, but read the reward directly rather than assume it).
    days[-1]["cumulative_bank"] = steps[-1][seat].reward
    return days


def trace_episode(agent_path, opponent_path, seed, episode_steps=720):
    """Runs one real episode (agent_path in seat 0). Returns a list of
    per-day dicts - the instrumentation record the task asked for."""
    steps = run_episode(agent_path, opponent_path, seed, episode_steps)
    return extract_trajectory(steps, 0)


def trace_both(agent_a_path, agent_b_path, seed, episode_steps=720):
    """One episode, both trajectories - agent_a's (seat 0) and agent_b's
    (seat 1), so a head-to-head comparison never has to run the game twice
    or worry about the two traces coming from different episodes."""
    steps = run_episode(agent_a_path, agent_b_path, seed, episode_steps)
    return extract_trajectory(steps, 0), extract_trajectory(steps, 1)


# =======================================================================
# Validation - one function per target, spec-referenced, HARD vs SOFT.
# Each returns (passed_or_in_range: bool, detail: str).
# =======================================================================

def validate_farm_scale(days):
    """HARD - spec §1: reach 75 tiles via land purchases."""
    final_tiles = days[-1]["land_tiles"]
    passed = final_tiles >= 75
    return passed, f"final land_tiles={final_tiles} (target: exactly 75, HARD)"


def validate_crew_scale(days):
    """SOFT - spec §2: 12-15 crew, sustained."""
    late_season = [d["crew"] for d in days if d["day"] >= 20]
    peak = max((d["crew"] for d in days), default=0)
    in_range = bool(late_season) and 12 <= max(late_season) <= 15
    return in_range, f"peak crew={peak}, days>=20 max={max(late_season) if late_season else 0} (target: 12-15, SOFT)"


def validate_animal_survival(days):
    """HARD (behavioural) - spec §3: animals bought must not be
    permanently stranded (unplaced) or lost. Checks "no stranding", not
    "reached 8-9" (that's SOFT - see validate_animal_scale)."""
    final = days[-1]
    stranded = sum(v for k, v in final["shed_inventory"].items() if k in ("COW", "SHEEP"))
    passed = stranded == 0
    return passed, f"final shed-stranded animals={stranded} (target: 0, HARD behavioural)"


def validate_animal_scale(days):
    """SOFT - spec §3: 8-9 total, ~5-6 cow : 3 sheep."""
    final_placed = days[-1]["animals_placed"]
    total = sum(final_placed.values())
    in_range = 8 <= total <= 9
    return in_range, f"placed={final_placed} total={total} (target: 8-9, ~5-6 cow:3 sheep, SOFT)"


def validate_selling_throughput(days):
    """SOFT - spec §6: meaningful selling from ~day 10, sustained (no
    cliff). Checks the shape, not an exact orders/day count (flagged in
    the audit as the weakest-evidenced number)."""
    pre10 = [d["sell_orders_today"] for d in days if d["day"] < 10]
    post10 = [d["sell_orders_today"] for d in days if 10 <= d["day"] < 29]
    late = [d["sell_orders_today"] for d in days if d["day"] >= 22]
    pre_mean = sum(pre10) / max(1, len(pre10))
    post_mean = sum(post10) / max(1, len(post10))
    no_cliff = bool(late) and max(late) > 0
    return (post_mean > pre_mean) and no_cliff, (
        f"mean orders/day pre-10={pre_mean:.1f}, day10-28={post_mean:.1f}, "
        f"day>=22 max={max(late) if late else 0} (target: ramps from ~day10, no cliff, SOFT)"
    )


def validate_final_bank(days):
    """SOFT, and explicitly the corrected range from the spec, not the
    input hypothesis's $90k-100k - see replay_shape_spec.md §7/§8."""
    final = days[-1]["cumulative_bank"]
    in_evidenced_range = 53_000 <= final <= 126_000
    in_narrow_claim = 90_000 <= final <= 100_000
    return in_evidenced_range, (
        f"final bank=${final:,.0f} - evidenced range $53k-$126k: "
        f"{'in range' if in_evidenced_range else ('BELOW range' if final < 53_000 else 'above range')}; "
        f"input hypothesis $90k-100k: {'met' if in_narrow_claim else 'not met'}"
    )


def validate_market_pressure(days):
    """SOFT, self-play only - spec's "contested order book" idea (see
    head_to_head.py's own docstring: built-in opponents never sell, so the
    market stays pristine and nothing about selling is actually tested
    against them). Checks that at least one premium product this agent
    trades (base price > $100: STRAWBERRY/MELON/MILK/WOOL) finished the
    season well below its base price - the documented self-play signature
    ("MELON finishes around $280 against a built-in and near the $1 floor
    in self-play", CLAUDE.md) - rather than just asserting units were sold."""
    final_prices = days[-1]["market_prices"]
    premium = {p: b for p, b in BASE_PRICES.items() if b > 100}
    crashed = {p: final_prices[p] for p, base in premium.items() if final_prices.get(p, base) < base * 0.5}
    passed = bool(crashed)
    detail = (
        f"final premium prices={ {p: final_prices[p] for p in premium} }, "
        f"crashed (<50% of base)={crashed or 'none'} (target: at least one, SOFT)"
    )
    return passed, detail


def validate_no_feed_collapse(days):
    """HARD (behavioural) - spec's "don't let the feed bill starve the
    herd" idea. An animal escape is permanent and shows up as the placed
    count dropping below its own season peak and never recovering - a
    distinct signal from validate_animal_survival (shed-stranding) and
    validate_animal_scale (final count only), both of which are blind to a
    mid-season escape that later gets backfilled by a fresh purchase."""
    totals = [sum(d["animals_placed"].values()) for d in days]
    peak = max(totals, default=0)
    final = totals[-1] if totals else 0
    passed = final >= peak
    return passed, f"peak placed={peak}, final placed={final} (target: final >= peak, i.e. no net escape, HARD behavioural)"


def run_validation_report(days):
    """One combined pass. Returns a dict of {check_name: (passed, detail)}."""
    return {
        "farm_scale (HARD)": validate_farm_scale(days),
        "crew_scale (SOFT)": validate_crew_scale(days),
        "animal_survival (HARD behavioural)": validate_animal_survival(days),
        "animal_scale (SOFT)": validate_animal_scale(days),
        "no_feed_collapse (HARD behavioural)": validate_no_feed_collapse(days),
        "selling_throughput (SOFT)": validate_selling_throughput(days),
        "market_pressure (SOFT, self-play only)": validate_market_pressure(days),
        "final_bank (SOFT, corrected range)": validate_final_bank(days),
    }


if __name__ == "__main__":
    seed = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    agent_path = __file__.rsplit("/", 1)[0] + "/replay_shape_agent.py"
    days = trace_episode(agent_path, "pass", seed)
    print(f"final bank: ${days[-1]['cumulative_bank']:,.0f}")
    for name, (passed, detail) in run_validation_report(days).items():
        print(f"  [{'PASS' if passed else 'MISS'}] {name}: {detail}")
