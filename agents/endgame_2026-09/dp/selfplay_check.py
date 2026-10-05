"""Self-play seed-0 sanity check: must finish DONE/DONE, every per-turn agent call under
500 ms. Loads two INDEPENDENT module instances (importlib, fresh namespace each), not one
function reused for both seats -- a stateful controller (WantamController's self.plan_day/
self.starve/etc.) shared across both seats in a single self-play game corrupts state, since
neither seat's board matches the other's plan. Stateless tape agents don't care either way."""
import sys, time, json, importlib.util, itertools
from kaggle_environments import make

path = sys.argv[1] if len(sys.argv) > 1 else 'agents/dp/w3_dp_rebuild.py'
_cnt = itertools.count()


def load_fresh(path):
    spec = importlib.util.spec_from_file_location(f"_sp{next(_cnt)}", path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return [v for v in vars(m).values() if callable(v)][-1]


turn_times = []


def make_timed():
    real_agent = load_fresh(path)

    def timed_agent(observation, configuration=None):
        t0 = time.time()
        result = real_agent(observation, configuration)
        turn_times.append(time.time() - t0)
        return result
    return timed_agent


env = make('kaggriculture', configuration={'seed': 0}, debug=False)
t0 = time.time()
env.run([make_timed(), make_timed()])
total = time.time() - t0

r = [s.reward for s in env.steps[-1]]
st = [s.status for s in env.steps[-1]]
max_turn_ms = max(turn_times) * 1000 if turn_times else 0
print(json.dumps(dict(
    seed=0, status=st, reward=r, n_turns_timed=len(turn_times),
    max_turn_ms=round(max_turn_ms, 1), mean_turn_ms=round(1000 * sum(turn_times) / len(turn_times), 2) if turn_times else 0,
    total_secs=round(total, 1), verdict=('PASS' if st == ['DONE', 'DONE'] and max_turn_ms < 500 else 'FAIL'),
)))
