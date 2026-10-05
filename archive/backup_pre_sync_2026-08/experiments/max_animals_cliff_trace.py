"""Causal trace for the MAX_ANIMALS 4->5 cliff.

Wraps the agent's own top-level callable (no internal monkeypatching of
main.py's decision functions - this only observes what the unmodified
agent actually returns each turn) to log every action taken, and samples
a rich state snapshot every turn. Built for two configurations
(MAX_ANIMALS=4 baseline, MAX_ANIMALS=5) run against the SAME opponent on
the SAME seed, so the first turn the two trajectories diverge is directly
visible.

RESEARCH ONLY. Does not modify main.py, pricing.py, or any opponent file.

    .venv/Scripts/python.exe experiments/max_animals_cliff_trace.py <opponent_path_or_'starter'> [seed]
"""
import sys
import importlib.util

from kaggle_environments import make

try:
    from kaggle_environments.envs.kaggriculture.kaggriculture import MARKET_PARAMS
except ImportError:
    MARKET_PARAMS = {}

ANIMAL_PRODUCTS = {"SHEEP": "WOOL", "COW": "MILK", "GOOSE": "EGG"}


def _load_main_module(max_animals):
    """A fresh, independent copy of main.py per call - so the 4-animal and
    5-animal configurations never share module state, even within one
    process."""
    spec = importlib.util.spec_from_file_location(f"main_ma{max_animals}", "main.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.MAX_ANIMALS = max_animals
    return module


class Tracer:
    def __init__(self, max_animals):
        self.module = _load_main_module(max_animals)
        self.log = []  # one entry per turn: {step, day, hour, action, snapshot}
        self._orig_agent = self.module.nikaangukia_meroni

    def make_agent_fn(self):
        # A plain closure, not a bound method: kaggle_environments' Agent.act
        # inspects __code__.co_argcount to decide how many positional args
        # to pass, and a bound method's co_argcount still counts `self`,
        # causing an extra-argument TypeError when the framework calls it
        # with (observation, configuration).
        def agent_fn(obs):
            action = self._orig_agent(obs)
            self._record(obs, action)
            return action
        return agent_fn

    def _record(self, obs, action):
        farm = self.module.get_player_farm(obs) or {}
        private = obs.get("private") or {}
        shed = dict(private.get("shed") or {})
        market = obs.get("market") or {}

        animal_species_counts = {}
        for row in farm.get("tiles") or []:
            for tile in row:
                if isinstance(tile, dict) and "animal" in tile:
                    sp = tile["animal"]
                    animal_species_counts[sp] = animal_species_counts.get(sp, 0) + 1

        self.log.append({
            "step": obs.get("step", 0),
            "day": obs.get("day", 0),
            "hour": obs.get("hour", 0),
            "money": farm.get("money", 0),
            "hands": len(farm.get("hands") or []),
            "hires_today": farm.get("hires_today", 0),
            "land": sum(1 for row in farm.get("tiles") or [] for t in row if t != "LOCKED"),
            "animal_species_counts": dict(animal_species_counts),
            "shed": shed,
            "wheat_reserve_needed": self.module.MIN_WHEAT_RESERVE_FOR_FEEDING,
            "action_market": list(action.get("market") or []),
            "action_farmer": action.get("farmer"),
            "market_prices": {k: v for k, v in (market.get("prices") or {}).items() if k in ("WOOL", "MILK", "EGG", "WHEAT")},
            "market_inventory": {k: v for k, v in (market.get("inventory") or {}).items() if k in ("WOOL", "MILK", "EGG", "WHEAT")},
        })


def run(opponent_path, seed):
    results = {}
    for max_animals in (4, 5):
        tracer = Tracer(max_animals)
        agent_fn = tracer.make_agent_fn()
        env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed}, debug=False)
        if opponent_path == "starter":
            env.run([agent_fn, "starter"])
        else:
            env.run([agent_fn, opponent_path])
        final_reward = env.steps[-1][0].reward
        results[max_animals] = {"log": tracer.log, "final_reward": final_reward, "status": env.steps[-1][0].status}
    return results


def summarize(results):
    log4 = results[4]["log"]
    log5 = results[5]["log"]
    print(f"final reward: MAX_ANIMALS=4 -> {results[4]['final_reward']:.0f} [{results[4]['status']}], "
          f"MAX_ANIMALS=5 -> {results[5]['final_reward']:.0f} [{results[5]['status']}]")

    # Index by (day) taking the LAST entry of that day (end-of-day state,
    # after that day's decisions had a chance to land) for a compact table.
    def by_day(log):
        out = {}
        for entry in log:
            out[entry["day"]] = entry  # overwritten each turn -> ends on last turn of the day
        return out

    d4 = by_day(log4)
    d5 = by_day(log5)
    all_days = sorted(set(d4) | set(d5))

    print(f"\n{'day':>3} | {'money(4/5)':>16} | {'animals(4/5)':>22} | {'hands(4/5)':>10} | "
          f"{'WOOL_shed(4/5)':>16} | {'MILK_shed(4/5)':>16}")
    for day in all_days:
        e4, e5 = d4.get(day), d5.get(day)
        if not e4 or not e5:
            continue
        m4, m5 = e4["money"], e5["money"]
        a4 = e4["animal_species_counts"]
        a5 = e5["animal_species_counts"]
        h4, h5 = e4["hands"], e5["hands"]
        w4 = e4["shed"].get("WOOL", 0)
        w5 = e5["shed"].get("WOOL", 0)
        mi4 = e4["shed"].get("MILK", 0)
        mi5 = e5["shed"].get("MILK", 0)
        print(f"{day:3d} | {m4:7.0f}/{m5:<7.0f} | {str(a4):>10}/{str(a5):<10} | {h4:3d}/{h5:<3d}      | "
              f"{w4:6.0f}/{w5:<6.0f}        | {mi4:6.0f}/{mi5:<6.0f}")

    # Actions involving animals - buy/build/feed/care - first divergence.
    print("\n--- animal-related market actions, MAX_ANIMALS=4 (first 20) ---")
    count = 0
    for entry in log4:
        for order in entry["action_market"]:
            if order and (order[0] == "BUY_ANIMAL" or (len(order) > 1 and order[1] in ("SHEEP", "COW", "GOOSE"))):
                print(f"  day={entry['day']:2d} hour={entry['hour']:2d} money={entry['money']:7.0f} order={order}")
                count += 1
                if count >= 20:
                    break
        if count >= 20:
            break

    print("\n--- animal-related market actions, MAX_ANIMALS=5 (first 20) ---")
    count = 0
    for entry in log5:
        for order in entry["action_market"]:
            if order and (order[0] == "BUY_ANIMAL" or (len(order) > 1 and order[1] in ("SHEEP", "COW", "GOOSE"))):
                print(f"  day={entry['day']:2d} hour={entry['hour']:2d} money={entry['money']:7.0f} order={order}")
                count += 1
                if count >= 20:
                    break
        if count >= 20:
            break

    # Cash trough: minimum money in the first 15 days.
    def trough(log):
        early = [e for e in log if e["day"] <= 15]
        if not early:
            return None
        m = min(early, key=lambda e: e["money"])
        return m["day"], m["hour"], m["money"]

    t4, t5 = trough(log4), trough(log5)
    print(f"\ncash trough (day<=15): MAX_ANIMALS=4 -> day={t4[0]} hour={t4[1]} money={t4[2]:.0f}   "
          f"MAX_ANIMALS=5 -> day={t5[0]} hour={t5[1]} money={t5[2]:.0f}")

    # WOOL/MILK sell events and realized prices.
    def sell_events(log, product):
        events = []
        for entry in log:
            for order in entry["action_market"]:
                if order and order[0] == "SELL" and len(order) > 1 and order[1] == product:
                    price = entry["market_prices"].get(product)
                    events.append((entry["day"], order[2] if len(order) > 2 else None, price))
        return events

    for product in ("WOOL", "MILK"):
        s4 = sell_events(log4, product)
        s5 = sell_events(log5, product)
        print(f"\n{product} sell events: MAX_ANIMALS=4 -> {len(s4)} events, total units "
              f"{sum(e[1] or 0 for e in s4)}")
        print(f"{product} sell events: MAX_ANIMALS=5 -> {len(s5)} events, total units "
              f"{sum(e[1] or 0 for e in s5)}")
        if s5:
            print(f"  MAX_ANIMALS=5 sample: {s5[:8]}")

    # HIRE counts and total spend (cumulative).
    def hire_stats(log):
        total_hires = sum(1 for e in log for o in e["action_market"] if o and o[0] == "HIRE")
        return total_hires

    print(f"\ntotal HIRE orders: MAX_ANIMALS=4 -> {hire_stats(log4)}   MAX_ANIMALS=5 -> {hire_stats(log5)}")

    # Feed / escape-relevant: track when an owned animal tile disappears
    # unexpectedly (escape) by watching animal_species_counts drop while
    # money/hands don't indicate a sale (animals aren't sellable directly).
    def species_drops(log):
        drops = []
        prev = {}
        for entry in log:
            cur = entry["animal_species_counts"]
            for sp, n in prev.items():
                if cur.get(sp, 0) < n:
                    drops.append((entry["day"], entry["hour"], sp, n, cur.get(sp, 0)))
            prev = cur
        return drops

    print(f"\nanimal-count DROPS (possible escapes), MAX_ANIMALS=4: {species_drops(log4)}")
    print(f"animal-count DROPS (possible escapes), MAX_ANIMALS=5: {species_drops(log5)}")


if __name__ == "__main__":
    opponent_path = sys.argv[1] if len(sys.argv) > 1 else "starter"
    seed = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    results = run(opponent_path, seed)
    summarize(results)
