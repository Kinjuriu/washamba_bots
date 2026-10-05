"""The measurement instrument: four gates, four measures, one verdict.

    .venv/bin/python research/instrument.py --agent agents/v7.12_synth/main.py
    .venv/bin/python research/instrument.py --agent A/main.py --baseline B/main.py
    .venv/bin/python research/instrument.py --gates-only        # cheap, no games

WHY ONE ENTRY POINT. This project built fifteen ways to score a candidate and used
a different subset each time, which is how a retracted instrument stayed in use for
a week (`docs/MEASUREMENT.md`). This is the standard, repeatable run: the same gates
in the same order, every time, with the same report at the end.

THE ORDER IS NOT COSMETIC. Each gate can invalidate everything after it, so a
failure stops the run rather than being noted and worked around.

  GATE 0  ENGINE      Does the harness still reproduce recorded banks to the
                      dollar? A behavioural fixture, not a version string: the
                      same seed pays one public reference agent 28,370 on engine
                      1.32.3 and 9,002 on 1.32.6, and `importlib.metadata` can
                      report a pin that `import` did not actually take.
  GATE 1  PARITY      With the new behaviour off, is the candidate bit-identical
                      to its parent? Prints the turn count, because "parity OK" is
                      a wish and "4,314 turns, 0 differences" is a gate.
  GATE 2  SAFETY      Will it survive a season at all: stdlib-only, inside the
                      per-turn budget, no crash. A ladder crash is silent.
  GATE 3  POPULATION  Is the evaluation pool admissible, by coverage of the
                      current field and by how many distinct plans it holds, never
                      by its age.

  MEASURE A  PAIRED    The candidate and the baseline on the SAME seed, seat and
                       recorded opponent. This is common random numbers, so the
                       paired difference is precise and the absolute level is not.
  MEASURE B  OBJECTIVE Pr[win] = Phi(mu/sigma), which `research/objective_calibration.py`
                       measured to calibrate at a mean absolute error of 0.068 with
                       14 of 14 opponents inside their interval. So the objective
                       is a signal-to-noise ratio, not a mean.
  MEASURE C  SPLIT     Screen and confirm on disjoint halves, and the screen-to-
                       confirm drop printed rather than available on request.
                       Selecting the best of N and quoting its own score is
                       inflated by 24 to 27 points here.
  MEASURE D  RANKING   Bradley-Terry strength from the pairwise records, because
                       two agents on a rating-paired ladder meet DIFFERENT
                       opponents and their raw win rates compare nothing. GATED by
                       a transitivity check: a scalar rating is lossless only if
                       the game is transitive, so the cycle rate is measured first
                       and the scalar is refused when it is high.

WHAT IT STILL CANNOT DO, stated in the report every run. Every opponent here is a
recording and cannot react, and the population turns over in about a week. This is
the right instrument for *did this break the route, and does it move the margin
against the field we actually met*, and the wrong one for *will this rate higher*.

References for each piece are in `docs/REFERENCES.md` and `docs/MEASUREMENT.md` §9.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import math
import statistics
import subprocess
import sys
import zlib
from collections import Counter
from itertools import combinations
from math import comb, erf, sqrt
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / ".venv/lib/python3.14/site-packages"))
sys.path.insert(0, str(ROOT / "research"))

try:
    from exact_replay import full_observation, one_game  # noqa: E402
except Exception:                                        # pragma: no cover
    # IMPORTABLE WITHOUT THE ENGINE, ON PURPOSE. Only four things in this file
    # replay a game: gate_engine, gate_parity, gate_safety and play(). Everything
    # else is arithmetic on results somebody else produced, and that half is what
    # a reader with the published dataset and their own numbers can use. A
    # module-level import of the engine made the whole file unusable to them.
    full_observation = one_game = None


def _needs_engine(what):
    raise RuntimeError(
        f"{what} replays a recorded game, so it needs the Kaggriculture engine "
        f"and research/exact_replay.py, which are not importable here. The "
        f"sample audit, the power functions and the population and symmetry "
        f"gates do not, and work on any table of results you already have.")

POOL = ROOT / "sparring/recent_pool.json.zz"
OUT = ROOT / "results/data/instrument.json"
PASS = {"farmer": ["PASS"], "hands": [], "market": []}


# --------------------------------------------------------------------------- util
def load(path):
    spec = importlib.util.spec_from_file_location("m", str(path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    h = z * sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return ((c - h) / d, (c + h) / d)


def sign_test(up, down):
    n = up + down
    if n == 0:
        return 1.0
    k = max(up, down)
    return min(1.0, 2 * sum(comb(n, j) for j in range(k, n + 1)) / 2 ** n)


def phi(x):
    return 0.5 * (1.0 + erf(x / sqrt(2.0)))



# ---------------------------------------------------------------- sample audit
# EVERY sub-instrument declares the sample it needs. This exists because a measure
# taken on the wrong sample has no validity, no power, and does not transfer
# between two days of experimentation, and because the only way a project stops
# measuring differently in different experiments is if the instrument refuses.
#
# ADDING A MEASURE MEANS ADDING A ROW HERE. A sub-instrument with no declared
# sample requirement is not admitted (see `audit_samples`).
SPEC = {
    "ENGINE": {
        "needs": "recorded games carrying the bank the ladder actually recorded",
        "min_n": 6,
        "why": "fewer cannot separate a moved engine from one unlucky replay",
    },
    "PARITY": {
        "needs": "WHOLE episodes at BOTH seats, not sampled turns",
        "min_n": 2 * 720 * 3,
        "why": "a divergence can first appear at any turn, and seat 1 sees a "
               "trimmed observation that seat 0 does not",
    },
    "SAFETY": {
        "needs": "several seeds and several opponent kinds, including an idle one",
        "min_n": 12,
        "why": "a crash is usually a state the agent reaches rarely",
    },
    "POPULATION": {
        "needs": "EFFECTIVE n, distinct plans, seat balance, and the share of "
                 "games the baseline had already won",
        "min_n": 5,
        "why": "a win rate over near-duplicates is one game repeated, and a pool "
               "of games we already won cannot falsify a claim about being behind",
    },
    "SYMMETRY": {
        "needs": "games at BOTH seats, from episodes whose seat assignment we "
                 "did not choose",
        "min_n": 8,
        "why": "this is the control, and a control that cannot fire is worse "
               "than none because it reads as a pass. Eight games a side is the "
               "floor at which a two-sample test can reject anything at all; "
               "below it the honest report is 'not tested'",
    },
    "PAIRED": {
        "needs": "the SAME seed, seat and recorded opponent for both agents",
        "min_n": 200,
        "why": (
            "common random numbers only pays if the pairing is exact, and the "
            "count is DERIVED rather than chosen. Work backwards from the "
            "smallest effect worth acting on: this project measures the "
            "winner's curse at 20 points of win rate and the screen-to-confirm "
            "drop at 8, so a candidate that screens at 65 % confirms near 57 % "
            "and anything we would act on lives between 57 % and 60 %. Exact "
            "power of a two-sided sign test at 5 %: detecting a true 60 % takes "
            "199 games, 57.5 % takes 352, 55 % takes 786. At the 40 this "
            "project used for a week, POWER AGAINST A REAL 60 % IS 21 %, so "
            "four times in five a genuinely better agent came back as 'no "
            "difference'. The 40 was never chosen; it is the argparse default "
            "of the script that built the first pool. Cost is not the "
            "constraint: a replayed game takes 1.13 s, so 200 paired games is "
            "under eight minutes for both agents"
        ),
    },
    "OBJECTIVE": {
        "needs": "enough games per opponent for mu and sigma to mean anything",
        "min_n": 20,
        "why": "sigma from a handful of games is mostly its own error",
    },
    "SPLIT": {
        "needs": "two DISJOINT halves, seat-stratified, and ideally separated in "
                 "TIME as well as in seat",
        "min_n": 10,
        "why": "a seat split controls selection; only a time split controls the "
               "axis this competition moves along, so only a time split makes a "
               "result transferable to another day",
    },
    "RANKING": {
        "needs": "enough orientable TRIPLES to estimate the cycle rate",
        "min_n": 20,
        "why": "a scalar rating is lossless only where the game is transitive, "
               "and zero cycles in nine triples is an absence of evidence",
    },
    "FORECAST": {
        "needs": "rating TRAJECTORIES from the whole population, indexed by each "
                 "submission's own episode number, plus a subject reading taken "
                 "past convergence",
        "min_n": 200,
        "why": "the band is a quantile band, so its p10 and p90 edges each rest "
               "on a tenth of the trajectories; below about two hundred the edge "
               "of the band is three submissions wearing a percentile. The first "
               "version of this measure was fitted on FIVE trajectories, all of "
               "them our own, and was refused for that reason. And a reading "
               "taken before convergence forecasts the settling rather than the "
               "agent, so the episode count is reported beside it",
    },
}


def sign_power(n, p, alpha=0.05):
    """Exact power of the two-sided paired sign test against a true win rate p.

    Under the null the number of wins is Binomial(n, 1/2); the test rejects
    outside the central 1-alpha region, so the power is the mass a Binomial(n, p)
    puts outside that same region. Exact, no normal approximation, which matters
    because the counts here are small enough for the approximation to flatter the
    design by several points.

    HOW TO CHOOSE n WITH THIS, which is the reverse of how it is usually done.
    Do not pick a sample size and then ask what it can see. Pick the smallest
    effect you would act on, then read off the n that gives it 80 % power, then
    check the cost. For this project the smallest effect worth acting on is
    around 57-60 %, because the winner's curse is measured at 20 points and the
    screen-to-confirm drop at 8, so a candidate screening at 65 % confirms near
    57 %. That lands n between 199 and 352.
    """
    if n < 1:
        return 0.0
    # Binomial tails in log space. A first version summed math.comb terms and
    # raised OverflowError past a few hundred games, which is inside the range
    # this function exists to explore.
    def log_pmf(k, q):
        return (math.lgamma(n + 1) - math.lgamma(k + 1) - math.lgamma(n - k + 1)
                + k * math.log(q) + (n - k) * math.log1p(-q))

    def cdf(k, q):
        if k < 0:
            return 0.0
        k = min(int(k), n)
        return sum(math.exp(log_pmf(i, q)) for i in range(0, k + 1))

    lo, hi = -1, n + 1
    for k in range(0, n + 1):
        if cdf(k, 0.5) > alpha / 2:
            lo = k - 1
            break
    for k in range(n, -1, -1):
        if 1 - cdf(k - 1, 0.5) > alpha / 2:
            hi = k + 1
            break
    return float(cdf(lo, p) + (1 - cdf(hi - 1, p)))


def n_for_effect(p, target=0.80, alpha=0.05, cap=2000):
    """The games needed to give a true win rate p the stated power."""
    for n in range(10, cap):
        if sign_power(n, p, alpha) >= target:
            return n
    return None


def min_detectable_p(n, alpha=0.05, power=0.80):
    """The smallest true win probability this many paired games can distinguish
    from a coin, at the stated power. Reported so 'not shown' can be read as
    'not enough games' rather than as 'no effect'."""
    if n < 2:
        return None
    crit = None
    for k in range(n, n // 2, -1):
        if sign_test(k, n - k) <= alpha:
            crit = k
        else:
            break
    if crit is None:
        return None
    for i in range(500, 1000):
        p = i / 1000.0
        # P(at least crit successes) under Binomial(n, p)
        s = sum(comb(n, j) * p ** j * (1 - p) ** (n - j) for j in range(crit, n + 1))
        if s >= power:
            return p
    return None


def measure_forecast(submission, horizon=300, band=250.0, min_episodes=40):
    """Where a live rating is likely to travel, delegated to `ladder_forecast.py`.

    WHY THE WRAPPER EXISTS AT ALL, since it adds no statistics of its own. The
    project directive is that a way of measuring we decide to keep has to be
    reachable from the instrument and audited by it. This measure was added on
    its own, ran on whatever the day supplied, and was therefore exactly the
    dispersal the directive forbids. Calling it from here is what puts its sample
    in front of `audit_samples` like every other sub-instrument's.

    Returns None when the subject has no reading yet, which is a real answer.
    """
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import ladder_forecast as lf

    paths = lf.corpus(min_episodes)
    st = lf.population_stats(paths)

    # the subject's current position: the population corpus first, our own
    # sampled series second, because a submission published today is in neither
    # the public dataset nor anybody's corpus yet
    now = None
    own = paths.get(str(submission))
    if own:
        n = max(own)                      # a path is {episode: rating}
        now = (int(n), float(own[n]))
    else:
        f = ROOT / "results/data/rating_series.jsonl"
        pts = []
        if f.exists():
            for line in f.read_text().splitlines():
                r = json.loads(line)
                if str(r.get("id")) == str(submission) and r.get("episodes"):
                    pts.append((int(r["episodes"]), float(r["score"])))
        if pts:
            now = max(pts)
    if not now:
        return None

    lb = lf.leaderboard(False)
    out = lf.forecast(now[0], now[1], paths, horizon, lb, band=band)
    out.update({"n_paths": st["n_paths"], "now_episodes": now[0],
                "now_score": now[1], "submission": str(submission),
                "source": "corpus" if own else "our own sampled series"})
    return out


def audit_samples(gates, pool, ia=None, ib=None, triples=None, fc=None):
    """Is each sub-instrument's sample adequate for what it is being asked?"""
    pop = next((g for g in gates if g["name"] == "POPULATION"), {})
    eff = pop.get("effective") or 0
    rows = []

    def add(name, have, ok, note=""):
        s = SPEC[name]
        rows.append({"measure": name, "have": have, "need": s["min_n"],
                     "ok": bool(ok), "needs": s["needs"], "why": s["why"],
                     "note": note})

    for g in gates:
        if g["name"] == "ENGINE":
            add("ENGINE", g.get("checked", 0), g.get("checked", 0) >= 6)
        elif g["name"] == "PARITY":
            add("PARITY", g.get("checked", 0), g.get("checked", 0) >= SPEC["PARITY"]["min_n"])
        elif g["name"] == "SAFETY":
            add("SAFETY", "preflight", g.get("pass") is not None)
        elif g["name"] == "POPULATION":
            cov = pop.get("goodturing_coverage")
            note = (f"nominal {pop.get('nominal')}, "
                    f"{pop.get('already_won')} already won")
            if cov is not None:
                note += (f", covers {100 * cov:.0f} % of the field it was drawn "
                         f"from, at least {pop.get('unseen_at_least', 0):.0f} "
                         f"behaviours unseen")
            add("POPULATION", eff, eff >= 5, note)
        elif g["name"] == "SYMMETRY":
            m = min(g.get("seat0", 0), g.get("seat1", 0))
            add("SYMMETRY", m, m >= SPEC["SYMMETRY"]["min_n"],
                f"seats {g.get('seat0')}/{g.get('seat1')}"
                + (f", p = {g['p']:.3f}" if g.get("p") is not None
                   else ", NOT TESTED, which is not a pass"))

    n = len(pool)
    mdp = min_detectable_p(n)
    # Power against the effects this project would actually act on, because a
    # "smallest detectable effect" is easy to read as a formality and a "21 %
    # chance of noticing" is not.
    try:
        p60 = sign_power(n, 0.60)
        p575 = sign_power(n, 0.575)
        pw = (f"power against a real 60 %: {100*p60:.0f} %, "
              f"against 57.5 %: {100*p575:.0f} %")
    except Exception:
        pw = ""
    add("PAIRED", n, n >= SPEC["PAIRED"]["min_n"],
        (f"smallest detectable win rate at 80 % power: {100*mdp:.0f} %. {pw}"
         if mdp else f"underpowered at any effect. {pw}"))
    # The effective sample, not the nominal one, is what carries the power.
    add("OBJECTIVE", eff, eff >= 5,
        "sigma is estimated across opponents, so EFFECTIVE n carries it")
    if ia is not None and ib is not None:
        disjoint = not (set(ia) & set(ib))
        span = None
        try:
            t = [str(pool[i].get("episode_id", "")) for i in range(n)]
            span = "time-separable" if len(set(t)) == n else "no time key"
        except Exception:
            pass
        add("SPLIT", min(len(ia), len(ib)),
            disjoint and min(len(ia), len(ib)) >= 10,
            f"disjoint={disjoint}, {span}")
    if triples is not None:
        add("RANKING", triples, triples >= SPEC["RANKING"]["min_n"],
            "below this the transitivity check cannot fire")
    if fc is not None:
        np_ = fc.get("n_paths", 0)
        ep = fc.get("now_episodes", 0)
        rows_ = fc.get("band") or []
        thin_h = [r["episode"] for r in rows_ if r["peers"] < 20]
        add("FORECAST", np_,
            np_ >= SPEC["FORECAST"]["min_n"] and ep >= 40,
            f"reading at episode {ep} from {fc.get('source')}; "
            f"{fc.get('peers', 0)} peers near it; quote rating_convergence.py "
            f"before reading it as settled"
            + (f"; horizons past episode {min(thin_h)} rest on under 20 peers "
               f"and are a range, not a quantile" if thin_h else ""))
    return rows


# ------------------------------------------------------------------------- gates
def gate_engine(pool, n=6, tol=1.0):
    """GATE 0. A behavioural fixture beats a version string.

    Replays the agent that RECORDED these games and checks the banks come back.
    If the engine under us has moved, this is where it shows, before any number
    downstream is produced on a game that is not the recorded one.
    """
    if one_game is None:
        _needs_engine("gate_engine")
    ok = 0
    checked = pool[:n]
    src = ROOT / "agents/v7.3_lazarus/main.py"
    fn = load(src).agent
    errs = []
    for m in checked:
        ours, _t, _s = one_game(fn, m["script"], m["seed"], m["our_seat"])
        d = abs(ours - m["our_bank"])
        ok += d <= tol
        errs.append(d)
    return {"name": "ENGINE", "checked": len(checked), "reproduced": ok,
            "median_error": statistics.median(errs) if errs else None,
            "pass": ok == len(checked),
            "why": "the harness reproduces the recorded banks to the dollar"}


def gate_parity(child, parent, pool, flag="SELLER", n_games=3):
    """GATE 1. The control must be bit-identical, and the check must be non-trivial.

    The flag is SET here rather than assumed. This function used to rely on the
    module default, which held until an agent was packaged for the ladder with its
    new behaviour on; at that moment the gate would have compared the parent
    against a copy of itself and passed forever.
    """
    if one_game is None:
        _needs_engine("gate_parity")
    from kaggle_environments import make
    if not hasattr(child, flag):
        return {"name": "PARITY", "pass": None, "checked": 0, "diffs": 0,
                "why": f"no `{flag}` on the candidate: nothing to switch off"}
    old = getattr(child, flag)
    setattr(child, flag, 0)
    checked = diffs = 0
    first = None
    for m in pool[:n_games]:
        for seat in (0, 1):
            env = make("kaggriculture",
                       configuration={"episodeSteps": 720, "seed": int(m["seed"])})
            env.reset(2)
            step = 0
            while not env.done:
                obs = full_observation(env, seat)
                a, b = parent.agent(dict(obs)), child.agent(dict(obs))
                checked += 1
                if json.dumps(a, sort_keys=True) != json.dumps(b, sort_keys=True):
                    diffs += 1
                    first = first or step
                k = step + 1
                o = m["script"][k] if k < len(m["script"]) else None
                acts = [None, None]
                acts[seat] = a
                acts[1 - seat] = o if isinstance(o, dict) else dict(PASS)
                env.step(acts)
                step += 1
    setattr(child, flag, old)
    return {"name": "PARITY", "checked": checked, "diffs": diffs,
            "first_diff_turn": first, "pass": diffs == 0,
            "why": "with the new behaviour off the candidate emits its parent's action"}


def gate_safety(agent_path):
    """GATE 2. Will it survive a season at all. Delegates to the preflight."""
    proc = subprocess.run(
        [str(ROOT / ".venv/bin/python"), str(ROOT / "research/preflight_robustness.py"),
         "--agent", str(agent_path)],
        capture_output=True, text=True, cwd=str(ROOT))
    out = proc.stdout
    return {"name": "SAFETY", "pass": "SAFE TO SUBMIT" in out,
            "tail": out.strip().splitlines()[-3:] if out else [],
            "why": "no crash, well-formed action every turn, inside the time budget"}


def gate_population(pool_path, pool):
    """GATE 3. Is the evaluation population admissible, and how big is it really?

    Nominal n is not effective n: a pool sampled from a clustered field has an
    effective size governed by the number of clusters, not the number of draws
    (the design effect, Kish 1965). Reported here so silence cannot read as
    independence.
    """
    # Two OPTIONAL extras, and the import belongs inside the guard with them.
    # `pool_guard` lives beside this file in the repository, so an unguarded
    # import at the top of the function passed every local test and then failed
    # the moment somebody ran the module anywhere else. The effective-n
    # computation below needs nothing but the pool.
    rep = div = None
    try:
        import pool_guard
        rep = pool_guard.representativeness(pool)
        div = pool_guard.diversity(pool)
    except Exception:
        pass

    # Effective n from the opponents' own action streams, clustered at 90 %.
    def canon(a):
        return json.dumps(a, sort_keys=True, separators=(",", ":"), default=str)
    S = [[canon(x) for x in m["script"]] for m in pool]
    n = len(S)
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    for i, j in combinations(range(n), 2):
        k = min(720, len(S[i]), len(S[j]))
        if k > 1 and sum(S[i][t] == S[j][t] for t in range(1, k)) / (k - 1) >= 0.90:
            a, b = find(i), find(j)
            if a != b:
                parent[a] = b
    eff = len({find(i) for i in range(n)})
    won = sum(1 for m in pool if m.get("we_won"))
    seats = sum(1 for m in pool if m["our_seat"] == 0)

    # HOW MUCH OF THE FIELD IS THIS, not just how much of the pool. Effective n
    # answers "how many independent tests do I have"; it says nothing about
    # whether they are the tests that matter. The frequency spectrum of the
    # clusters answers the second question with two classical estimators.
    #
    #   Good-Turing coverage   C = 1 - f1/n      (Good 1953)
    #     the share of the sampled field's probability mass this pool represents.
    #     f1 is the number of behaviours seen EXACTLY ONCE, and the intuition is
    #     that singletons measure the rate at which new behaviour is still
    #     arriving: if half your pool is behaviours you saw once, the next
    #     opponent you add is about as likely to be new as not.
    #
    #   Chao1   S >= S_obs + f1^2 / (2 f2)       (Chao 1984)
    #     a LOWER bound on how many behaviours exist in the field you drew from.
    #     Far above S_obs means the pool has not seen the field, which is a
    #     different failure from the pool being small and is not fixed by
    #     replaying the same opponents more times.
    #
    # Measured on 4,000 recorded matchups: 638 behaviours observed, 448 of them
    # singletons, Chao1 at least 1,862. So a pool drawn from this field is
    # nowhere near saturation, and a coverage figure is the honest way to say so.
    sizes = Counter(find(i) for i in range(n))
    spec = Counter(sizes.values())
    f1, f2 = spec.get(1, 0), spec.get(2, 0)
    coverage_gt = 1.0 - f1 / n if n else None
    chao1 = eff + (f1 * f1 / (2.0 * f2) if f2 else f1 * (f1 - 1) / 2.0)

    return {"name": "POPULATION", "nominal": n, "effective": eff,
            "coverage": rep[0] if rep else None,
            "plans": div[0] if div else None,
            "singletons": f1, "doubletons": f2,
            "goodturing_coverage": coverage_gt,
            "chao1": float(chao1), "unseen_at_least": float(chao1 - eff),
            "already_won": won, "seat0": seats,
            "pass": eff >= 5,
            "why": "enough distinct behaviours that a win rate is not one game repeated"}


def gate_symmetry(pool):
    """GATE 5. A CONTROL: does this pool behave the way a symmetric game must?

    Every other gate asks whether the CANDIDATE is sound. This one asks whether
    the DATA is, and it is the only gate here that can fail without the agent
    being touched.

    The derivation is exact rather than empirical. `docs/GAME_THEORY.md`
    establishes that Kaggriculture is symmetric: both seats have the same action
    set, the same endowment and the same payoff rule, and the only asymmetry
    anyone has found is that seat 1's trimmed observation omits `step`. If the
    seats are exchangeable then the recorded margin, taken across episodes whose
    seat assignment we did not choose, must have the same distribution from
    either side. Not approximately. So a seat-dependent fault anywhere in the
    chain, in the recording, the replay, the extraction, or an agent that reads
    `obs["step"]` and silently gets nothing at seat 1, shows up here and is
    invisible to every other check in this file.

    `docs/INSTRUMENTS.md` argues that the only defence found against the largest
    failure family, a quantity that is true and adjacent to the one you need, is
    to carry a control that says what the number looks like when nothing is
    happening. This is that control.

    Measured on 2,000 independent episodes: mean margin -$291 with a 95 %
    interval of [-1,508, 915], and Kolmogorov-Smirnov against the mirrored
    distribution at p = 0.998.
    """
    def margins(seat):
        return [float(m["our_bank"]) - float(m["their_bank"])
                for m in pool
                if m.get("our_seat") == seat
                and m.get("our_bank") is not None
                and m.get("their_bank") is not None]

    a, b = margins(0), margins(1)
    out = {"name": "SYMMETRY", "seat0": len(a), "seat1": len(b)}
    if min(len(a), len(b)) < 8:
        out.update({"pass": None, "p": None,
                    "why": "too few games at one seat to test it, which is not "
                           "the same as passing"})
        return out
    try:
        from scipy import stats
        p = float(stats.ks_2samp(a, b).pvalue)
        method = "Kolmogorov-Smirnov, two sample"
    except Exception:
        # Mann-Whitney by hand, so the gate does not need scipy to exist
        import statistics as S
        allv = sorted(a + b)
        ra = sum(allv.index(v) + 1 for v in a)
        na, nb = len(a), len(b)
        u = ra - na * (na + 1) / 2
        mu, sd = na * nb / 2, (na * nb * (na + nb + 1) / 12) ** 0.5
        z = (u - mu) / sd if sd else 0.0
        p = float(2 * (1 - 0.5 * (1 + __import__("math").erf(abs(z) / 2 ** 0.5))))
        method = "Mann-Whitney, normal approximation"
    out.update({"pass": p > 0.01, "p": p, "method": method,
                "why": "the game is symmetric, so the recorded margin must look "
                       "the same from either seat; if it does not, the fault is "
                       "in the data rather than in the agent"})
    return out


# ---------------------------------------------------------------------- measures
def play(agent_fn, matchups):
    if one_game is None:
        _needs_engine("play()")
    return [one_game(agent_fn, m["script"], m["seed"], m["our_seat"])[:2]
            for m in matchups]


def measure_paired(cand, base, opponents=None):
    """MEASURE A + B. The paired difference, and the objective where it applies.

    WHICH SIGMA, AND WHY IT IS NOT THE OBVIOUS ONE. `Pr[win] = Phi(mu/sigma)`
    calibrates well, but it is defined on the margin against ONE opponent across
    seeds. The standard deviation of `margin` here is a different quantity: this
    pool holds one game per matchup, so that list has one entry per OPPONENT and
    its spread is the variation between opponents, not within a pairing. Feeding
    it to Phi charges the candidate for the variance of who it was drawn against,
    which `docs/INSTRUMENTS.md` calls the first failure family, a number that is
    true and adjacent to the one you need.

    AND THE LINK IS WRONG FOR THE POOLED QUANTITY ANYWAY. Phi assumes normality.
    Measured on 2,000 independent recorded episodes, a single bank IS normal
    (Kolmogorov-Smirnov p = 0.225 on 4,000 banks, against 1.4e-93 for the
    lognormal), but the POOLED margin is not: excess kurtosis +10.6, the normal
    rejected at 1e-50, best fitted by a t with about 1.4 degrees of freedom.
    Three explanations were tested and all three refuted, mixing over rating
    bands, catastrophic games, and clone-against-clone pairings, so the tails are
    a property of the margin rather than an artefact of pooling.

    SO: Phi(mu/sigma) is reported only where the pool actually replicates a
    pairing, and the field win rate is reported with a Wilson interval, which
    assumes nothing. `research/distributions.py` is the derivation.
    """
    margin = [a - b for a, b in cand]
    bmargin = [a - b for a, b in base]
    paired = [x - y for x, y in zip(margin, bmargin)]
    up = sum(1 for x in paired if x > 0)
    dn = sum(1 for x in paired if x < 0)
    mu = statistics.mean(margin)
    sd = statistics.pstdev(margin) if len(margin) > 1 else 0.0
    k = sum(1 for x in margin if x > 0)
    lo, hi = wilson(k, len(margin))

    # Does this pool replicate any pairing? Without replication there is no
    # within-pairing sigma to estimate and the objective is simply not available.
    per_opp, reps = {}, 0
    if opponents and len(opponents) == len(margin):
        for name, m in zip(opponents, margin):
            per_opp.setdefault(str(name), []).append(m)
        reps = sum(1 for v in per_opp.values() if len(v) >= 5)

    out = {
        "n": len(margin), "wins": k, "win_rate": k / len(margin),
        "wilson": [lo, hi],
        "median_margin": statistics.median(margin), "mean_margin": mu,
        "sigma_pooled": sd,
        "mu_over_sigma_pooled": mu / sd if sd > 0 else float("inf"),
        "opponents_with_replication": reps,
        "our_bank": statistics.median([a for a, _ in cand]),
        "their_bank": statistics.median([b for _, b in cand]),
        "paired_median": statistics.median(paired),
        "paired_better": up, "paired_worse": dn,
        "paired_p": sign_test(up, dn),
    }
    if reps:
        zs = [statistics.mean(v) / statistics.pstdev(v)
              for v in per_opp.values()
              if len(v) >= 5 and statistics.pstdev(v) > 0]
        out["mu_over_sigma_within"] = statistics.median(zs) if zs else None
        out["predicted_win_rate"] = (phi(out["mu_over_sigma_within"])
                                     if zs else None)
        out["objective_note"] = (f"within-pairing, from {reps} opponents with at "
                                 f"least 5 games each")
    else:
        out["mu_over_sigma_within"] = None
        out["predicted_win_rate"] = None
        out["objective_note"] = (
            "NOT AVAILABLE: this pool plays each opponent once, so there is no "
            "within-pairing sigma to estimate. The pooled figure is the spread "
            "BETWEEN opponents and Phi of it is not a win probability. Use the "
            "observed win rate and its Wilson interval instead")
    return out


def split_indices(pool, by="seat"):
    """MEASURE C. Two disjoint halves.

    `seat` stratifies by seat, which controls selection. `time` splits older from
    newer, which is the strict-future holdout: it controls the axis this
    competition actually moves along, and a seat split does not.
    """
    if by == "time":
        order = sorted(range(len(pool)),
                       key=lambda i: str(pool[i].get("episode_id", "")))
        h = len(order) // 2
        return sorted(order[:h]), sorted(order[h:])
    s0 = [i for i, m in enumerate(pool) if m["our_seat"] == 0]
    s1 = [i for i, m in enumerate(pool) if m["our_seat"] == 1]
    a = sorted(s0[::2] + s1[::2])
    return a, sorted(set(range(len(pool))) - set(a))


def cycle_rate(win):
    """Is the game transitive? Count 3-cycles among the triples we can orient.

    A scalar rating is lossless only where the game is transitive (Balduzzi et al.,
    Re-evaluating evaluation, NeurIPS 2018). `win[i][j]` is the share of games i
    beat j; a triple is a cycle when i>j, j>k and k>i.
    """
    ids = sorted(win)
    trips = cycles = 0
    for a, b, c in combinations(ids, 3):
        try:
            ab, bc, ca = win[a][b], win[b][c], win[c][a]
            ba, cb, ac = win[b][a], win[c][b], win[a][c]
        except KeyError:
            continue
        if min(ab + ba, bc + cb, ca + ac) == 0:
            continue
        trips += 1
        f = lambda x, y: 1 if x > y else (-1 if x < y else 0)   # noqa: E731
        s = f(ab, ba) + f(bc, cb) + f(ca, ac)
        if abs(s) == 3:
            cycles += 1
    return {"triples": trips, "cycles": cycles,
            "rate": cycles / trips if trips else None}


def bradley_terry(win, iters=300, tol=1e-9):
    """MEASURE D. One strength per player from UNBALANCED pairwise records.

    The minorisation-maximisation iteration (Hunter 2004), which is the standard
    fit for Bradley & Terry (1952). This is the piece that lets two agents who met
    DIFFERENT opponents be compared at all, which a raw win rate cannot do: on this
    ladder our own two live submissions met zero opponents in common.
    """
    ids = sorted(win)
    p = {i: 1.0 for i in ids}
    n = {i: {j: win[i].get(j, 0) + win[j].get(i, 0) for j in ids if j != i}
         for i in ids}
    w = {i: sum(win[i].get(j, 0) for j in ids if j != i) for i in ids}
    for _ in range(iters):
        new = {}
        for i in ids:
            den = sum(n[i][j] / (p[i] + p[j]) for j in ids if j != i and n[i][j])
            new[i] = (w[i] / den) if den > 0 and w[i] > 0 else p[i]
        s = sum(new.values()) / len(new)
        new = {k: v / s for k, v in new.items()}
        if max(abs(new[k] - p[k]) for k in ids) < tol:
            p = new
            break
        p = new
    # On the ladder's own scale, for readability only.
    return {i: {"strength": p[i], "elo": 400 * math.log10(max(p[i], 1e-12))}
            for i in ids}


# ------------------------------------------------------------------------ report
def verdict(gates, a, thin=None):
    failed = [g["name"] for g in gates if g.get("pass") is False]
    if failed == ["SYMMETRY"]:
        # The one gate whose failure does not accuse the agent. Saying "STOP,
        # your candidate is broken" here would send someone to debug code that
        # is fine, which is worse than no control at all.
        return "STOP, DATA", (
            "the symmetry control failed. The game is symmetric, so the recorded "
            "margin must look the same from either seat, and here it does not. "
            "That points at the pool, the recording or the extraction, NOT at "
            "the candidate. Fix the data before reading anything below it")
    if failed:
        return "STOP", f"gate {', '.join(failed)} failed; nothing downstream means anything"
    if a is None:
        return "GATES ONLY", "no games played"
    if a["paired_p"] < 0.05 and a["paired_median"] > 0:
        return "BETTER", "paired sign test rejects at 5 % in the candidate's favour"
    if a["paired_p"] < 0.05 and a["paired_median"] < 0:
        return "WORSE", "paired sign test rejects at 5 % against the candidate"
    if thin:
        return "NOT SHOWN", (f"the paired test does not resolve, and the sample is "
                             f"thin for {', '.join(thin)}: read this as not enough "
                             f"evidence rather than as no effect")
    return "NOT SHOWN", "the paired test does not resolve; more games or a real change"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--agent", required=True)
    ap.add_argument("--baseline", default="agents/v7.10_abdelrazik/main.py")
    ap.add_argument("--pool", default=str(POOL))
    ap.add_argument("--flag", default="SELLER")
    ap.add_argument("--split", default="seat", choices=["seat", "time"])
    ap.add_argument("--forecast", default=None, metavar="SUBMISSION",
                    help="also report where this live submission's rating is "
                         "likely to travel, audited on the same terms")
    ap.add_argument("--gates-only", action="store_true")
    ap.add_argument("--skip-engine", action="store_true")
    ap.add_argument("--out", default=str(OUT))
    args = ap.parse_args()

    pool = json.loads(zlib.decompress(Path(args.pool).read_bytes()))
    cand_mod, base_mod = load(ROOT / args.agent), load(ROOT / args.baseline)

    print(f"CANDIDATE  {args.agent}")
    print(f"BASELINE   {args.baseline}")
    print(f"POOL       {Path(args.pool).name}, {len(pool)} matchups\n")

    gates = []
    if not args.skip_engine:
        gates.append(gate_engine(pool))
    gates.append(gate_parity(cand_mod, base_mod, pool, args.flag))
    gates.append(gate_safety(ROOT / args.agent))
    gates.append(gate_population(args.pool, pool))
    gates.append(gate_symmetry(pool))

    print("GATES")
    for g in gates:
        mark = {True: "pass", False: "FAIL", None: "n/a "}[g.get("pass")]
        detail = ""
        if g["name"] == "ENGINE":
            detail = f"{g['reproduced']}/{g['checked']} banks reproduced, median error ${g['median_error']:,.0f}"
        elif g["name"] == "PARITY":
            detail = f"{g['checked']:,} turns, {g['diffs']} differences"
        elif g["name"] == "SAFETY":
            detail = g["tail"][-1][:60] if g["tail"] else ""
        elif g["name"] == "POPULATION":
            detail = (f"nominal {g['nominal']}, EFFECTIVE {g['effective']}, "
                      f"{g['already_won']} already won, seats {g['seat0']}/"
                      f"{g['nominal'] - g['seat0']}")
        print(f"  {mark}  {g['name']:<12}{detail}")
        print(f"        {g['why']}")

    res = {"agent": args.agent, "baseline": args.baseline, "pool": args.pool,
           "gates": gates}
    a = None
    ia = ib = None
    if not args.gates_only and all(g.get("pass") is not False for g in gates):
        ia, ib = split_indices(pool, args.split)
        print(f"\nMEASURES, split by {args.split}: screen {len(ia)}, confirm {len(ib)}")
        cand_all = play(cand_mod.agent, pool)
        base_all = play(base_mod.agent, pool)
        opp = [str(m.get("opponent")) for m in pool]
        a = measure_paired(cand_all, base_all, opp)
        scr = measure_paired([cand_all[i] for i in ia], [base_all[i] for i in ia],
                             [opp[i] for i in ia])
        cnf = measure_paired([cand_all[i] for i in ib], [base_all[i] for i in ib],
                             [opp[i] for i in ib])
        bse = measure_paired(base_all, base_all, opp)
        res.update({"all": a, "screen": scr, "confirm": cnf, "baseline_all": bse})

        # The pooled mu/sigma is printed as an EFFECT SIZE and never as Phi of
        # itself: the pooled margin has excess kurtosis near +10, so a normal
        # link on it is not a win probability. The Wilson interval on the
        # observed win rate is the distribution-free answer and is the one to
        # read. See measure_paired's docstring and research/distributions.py.
        print(f"\n{'':<12}{'wins':>9}{'win rate':>11}{'95 % Wilson':>16}"
              f"{'median':>11}{'effect':>10}{'vs base':>11}{'p':>9}")
        for nm, d in (("baseline", bse), ("candidate", a),
                      ("  screen", scr), ("  CONFIRM", cnf)):
            lo_, hi_ = 100 * d["wilson"][0], 100 * d["wilson"][1]
            print(f"{nm:<12}{str(d['wins'])+'/'+str(d['n']):>9}"
                  f"{100*d['win_rate']:>10.1f}%"
                  f"{f'[{lo_:.0f},{hi_:.0f}]':>16}"
                  f"{d['median_margin']:>+11,.0f}"
                  f"{d['mu_over_sigma_pooled']:>+10.2f}"
                  f"{d['paired_median']:>+11,.0f}{d['paired_p']:>9.4f}")
        if a.get("predicted_win_rate") is not None:
            print(f"\n  Phi(mu/sigma) within a pairing: "
                  f"{100*a['predicted_win_rate']:.0f} %  ({a['objective_note']})")
        else:
            print(f"\n  Phi(mu/sigma): {a['objective_note']}.")
        drop = scr["win_rate"] - cnf["win_rate"]
        print(f"\n  screen-to-confirm drop: {100*drop:+.1f} points "
              f"(the winner's curse, measured rather than assumed)")

        # MEASURE D: ranking, gated by transitivity.
        win = {"candidate": {}, "baseline": {}}
        cw = sum(1 for (x, y) in cand_all if x > y)
        bw = sum(1 for (x, y) in base_all if x > y)
        win["candidate"]["field"] = cw
        win["baseline"]["field"] = bw
        win["field"] = {"candidate": len(cand_all) - cw, "baseline": len(base_all) - bw}
        cyc = cycle_rate(win)
        bt = bradley_terry(win)
        res["transitivity"], res["bradley_terry"] = cyc, bt
        print(f"\n  transitivity check: {cyc['cycles']} cycles in {cyc['triples']} "
              f"orientable triples")
        if cyc["triples"] < 20:
            print("    TOO FEW TRIPLES TO CONCLUDE. A scalar rating is lossless only")
            print("    where the game is transitive (Balduzzi et al. 2018), and with a")
            print("    two-agent record there is nothing to orient. The Bradley-Terry")
            print("    strengths below are reported and MUST NOT be read as a ranking")
            print("    until the cycle rate is measured on a real set of agents.")
        for k, v in sorted(bt.items(), key=lambda kv: -kv[1]["strength"]):
            print(f"    {k:<12} strength {v['strength']:.3f}   {v['elo']:+.0f} elo-scale")

    # SAMPLE AUDIT. A measure taken on the wrong sample has no validity and no
    # power, and does not transfer to another day of experimentation. Printed
    # every run, before the verdict, so an inadequate sample cannot be quietly
    # inherited from one experiment into the next.
    trips = (res.get("transitivity") or {}).get("triples")
    fc = None
    if args.forecast:
        try:
            fc = measure_forecast(args.forecast)
        except Exception as e:
            print(f"\nFORECAST unavailable: {type(e).__name__}: {e}")
        if fc:
            res["forecast"] = fc
            print(f"\nFORECAST for {args.forecast}, from {fc['n_paths']:,} "
                  f"population trajectories, {fc['peers']:,} of them near this "
                  f"one at this episode")
            print(f"  now: {fc['now_score']:.1f} at episode {fc['now_episodes']}"
                  f" ({fc['source']})")
            if fc.get("too_few"):
                print("  too few peers to give a band, which is an answer: no "
                      "submission like this one has been seen here before.")
            # A percentile band narrows to its own extremes as the peers thin
            # out, and it does that silently: the far end of a horizon is often
            # a handful of submissions with p10 and p90 sitting on the minimum
            # and the maximum. Marked rather than trimmed, because the row is
            # still the best available answer, just not a quantile.
            for r in fc.get("band", []):
                mark = "  <- {} peers, read as a range".format(r["peers"]) \
                    if r["peers"] < 20 else ""
                print(f"  episode {r['episode']:>5}   p10 {r['p10']:>7.0f}   "
                      f"p50 {r['p50']:>7.0f}   p90 {r['p90']:>7.0f}   "
                      f"rank {r['rank_p90']}-{r['rank_p10']}{mark}")
        else:
            print(f"\nFORECAST: {args.forecast} has no reading yet, so there is "
                  f"nothing to forecast from.")
    audit = audit_samples(gates, pool, ia, ib, trips, fc)
    res["sample_audit"] = audit
    print(f"\nSAMPLE AUDIT, what each sub-instrument needs and what it got")
    print(f"  {'measure':<12}{'have':>10}{'need':>7}  status  what the sample must be")
    for r in audit:
        mark = "ok  " if r["ok"] else "THIN"
        print(f"  {r['measure']:<12}{str(r['have']):>10}{str(r['need']):>7}  {mark}    {r['needs'][:58]}")
        if r["note"]:
            print(f"  {'':<32}          {r['note']}")
        if not r["ok"]:
            print(f"  {'':<32}          WHY IT MATTERS: {r['why'][:70]}")
    thin = [r["measure"] for r in audit if not r["ok"]]
    if thin:
        print(f"\n  UNDERPOWERED: {', '.join(thin)}. Read those rows as 'not enough")
        print("  evidence', never as 'no effect', and do not carry them to another day.")

    v, why = verdict(gates, a, thin)
    res["verdict"], res["verdict_why"] = v, why
    print(f"\nVERDICT: {v}\n  {why}")
    print("\n  AND WHAT THIS CANNOT TELL YOU, every run: every opponent here is a")
    print("  recording and cannot react, and the field turns over in about a week.")
    print("  Right for 'did this break the route'; wrong for 'will this rate higher'.")

    Path(args.out).write_text(json.dumps(res, indent=1, default=float))
    print(f"\nwrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
