# Kaggriculture — Setup & First Task

*The repo now has its own real docs for setup, evaluation, and workflow — better maintained than a standalone summary could be. This file is deliberately thin: it points to the actual source, confirms what's current, and lays out what to work on first and why. Superseded material is removed as each freeze lands — those questions are answered in the repo itself.*

---

## 0. What actually changed

Everything below reflects the repo as of checkpoint **V2-sheep**, commit `93d6bed` (freeze commit `e9dd82b`, "docs: freeze checkpoint V2, correct stale claims, fix self-play sampling"), frozen 2026-08-16. **This supersedes V1-baseline** (`df69f97`, self-play 28,212) — read `docs/checkpoints/V2-sheep.md`, not the V1 file, for current numbers.

Since V1:

- **Sheep replaces goose.** `ACTIVE_ANIMALS` — the `CARE` bank pays out in full on the animal's next production day, and a longer production interval banks a bigger payout: sheep collect 4 units an event at 4× the price a goose does. `MAX_ANIMALS` stays at **1** — a second animal (even a different species, sheep+cow) is still a measured loss (-16,634, 0/16). COW alone was measured too: +606 vs sheep's +1,332 — sheep wins.
- **Denser crew.** `WORK_TILES_PER_HAND` 6 → 4. **This was previously recorded as a dead end and that record was wrong** — it had been judged against the across-seed stdev (the wrong test) on a much older agent. Re-measured head-to-head: **+1,910, 16/16 wins.** The farm was watering 19.2 tiles/day against 24 planted; hands were the correct lever.
- **Demand-aware `choose_crop`.** Reads `obs["town"]["unlocked_shops"]` live and divides the self-supply discount by market absorption *plus* demand still arriving, not just current inventory.
- **`FERTILIZE` mechanic shipped** (`wants_fertilizer`, `FERTILIZABLE_CROPS = ("TOMATO", "STRAWBERRY")`) — but only benefits **strawberry** in practice. `choose_crop` has no fertilizer-awareness in its scoring, so tomato still never wins the crop-selection ranking and is never planted (0 in V2's sold mix). **The tomato+fertilizer opportunity from V1's backlog is not done** — don't confuse "the mechanic exists" with "the opportunity is captured." See §3 Fix B.
- **`pricing.py`** (PR #11, Steff's forward-pricing research) landed as a **standalone module — not wired into `main.py`.** Research only.
- **`experiments/aggressive_opponent.py`** — new stress-test harness: an asymmetric, undercutting twin of `main.py` (monkey-patches only the aggressiveness constants) for probing whether real market competition pushes the agent into an idle-late-game pattern that `pass`/`random`/`starter` and symmetric self-play can't reveal.
- Self-play mean **35,583** (V2-sheep, 8 seeds) — up from V1's 28,212 combined `+12,698`.
- Test suite: **108 passing** (was 82) — added `tests/test_pricing.py`.
- A tooling bug fix: `selfplay_bench.py` used to pool both mirror-match players' banks into one sample set; since they're near-identical in a mirror match this **halved the apparent stdev**. Fixed 2026-08-16. Means are unaffected; V1/V2's recorded stdevs stay internally comparable to each other but not to anything measured fresh.
- Leaderboard at freeze: active submission **603.8** (rank 2,915/4,758), control **469.9** kept unchanged for comparison — the +134 gap is the first change visible above the ±120 rating drift noise.

---

## 1. Setup (from zero)

Follow `README.md`'s **Setup** section directly — it's current and specific, don't improvise around it:

```bash
uv venv --python 3.13.7 .venv
uv pip install --python .venv/Scripts/python.exe \
  "kaggle-environments>=1.32.6" kaggle \
  numpy pandas matplotlib seaborn jupyterlab ipykernel
```

(macOS: `.venv/bin/python` instead of `.venv/Scripts/python.exe` — and don't commit either path; the team is split across OSes and a hardcoded path silently breaks half the team.)

**On a genuinely fresh machine, `uv` itself may not exist either** — check `uv --version` first. If it's missing: `pip install uv` into whatever system Python is present, then run the two commands above; `uv` fetches its own pinned Python 3.13.7 build, so the system interpreter's version doesn't matter.

`kaggle-environments>=1.32.6` is a hard floor, not a suggestion — there was a mid-season balance patch (Town Center demand, shop sampling) that the official starter notebook's `>=1.32.2` pin predates. `requirements.txt` is a broad 190-package workspace freeze, not this agent's real dependency list — don't install it wholesale.

Get a Kaggle API token (kaggle.com/settings/api or `kaggle auth login`) — this step needs a human, it can't be scripted unattended.

**Run cold, before touching anything** (`README.md` → Running and testing):

```bash
.venv/Scripts/python.exe -m unittest discover -s tests   # expect 108 passing
.venv/Scripts/python.exe -c "
from kaggle_environments import make
env = make('kaggriculture', configuration={'episodeSteps': 720, 'seed': 0})
env.run(['main.py', 'main.py'])
print([s.status for s in env.steps[-1]])   # must be ['DONE', 'DONE']
"
```

If both pass, you're on a clean, working V2-sheep checkout. Don't run `selfplay_bench.py`/`seeded_batch.py` cold expecting to need them yet — the numbers are already recorded in `docs/checkpoints/V2-sheep.md`. Read that file instead of re-measuring it.

---

## 2. Read these two files before writing any code

- **`docs/checkpoints/V2-sheep.md`** — what the agent currently does, every metric that matters, and (critically) its own **Known limitations** and **What is not included** sections. This is closer to a prioritized backlog than a status report. (`V1-baseline.md` is now historical only — superseded, kept frozen for reference.)
- **`docs/CHECKPOINTS.md`** — the workflow (`OBSERVE → HYPOTHESIZE → FREEZE → CHANGE ONE → TEST → COMPARE → DIAGNOSE → DOCUMENT → SUBMIT → NEW CHECKPOINT`), and which harness to use for what. The harness choice isn't a style preference — using the wrong one has already produced a result that pointed the *opposite* direction from the truth (liquidation-timing example, `CHECKPOINTS.md` §"Choosing the comparison"). Also has the self-play stdev-pooling note above.

---

## 3. What to work on first, in order, and why

**Detailed spec for Fix A and Fix B lives in `mydocs/fix.md` — read that before touching code, this section only orders and motivates them.** Pulled from V2-sheep's own **Known limitations** / **What is not included**:

### Fix A. Per-turn seed budget (PLANT-rejection) — unchanged, still open
The engine drops *all* PLANT requests for a crop when a turn's demand exceeds held seed, and nothing tracks a shared per-turn budget across units — still costing **~43 unit-turns/season**, likely more now that `WORK_TILES_PER_HAND` dropped to 4 (denser crew = more units overcommitting the same seed stock). The fix (a mutable `seed_budget` dict shared across the farmer and hands, same pattern already used for `claimed`, `pending_builds`, `feed_claimed`) is fully scoped in `fix.md`. Use `paired_compare.py` against V2-baseline (`93d6bed`) — planting/movement change, not a selling one. **Do this first** — fix.md calls it out as more urgent under the denser crew, and Fix B builds on it being clean.

### Fix B. Tomato fertilizer bonus in `choose_crop`
**Not shipped — this is still open, despite `FERTILIZE` landing in V2.** `choose_crop`'s scoring has zero fertilizer-awareness, so tomato (the crop fertilizer pays off best on — 3 production ticks per 3-day cover) never outranks strawberry or melon and is never planted; V2's own sold mix confirms **0 tomato, every season**. Fix: a `FERTILIZER_BONUS_TOMATO` constant plus an `_has_fertilizer_access()` guard (checking `ACTIVE_ANIMALS` membership generically, not a hardcoded species) added to `choose_crop`'s `expected_yield` term. Full mechanism, scoring math, and risk notes in `fix.md`. Use `paired_compare.py` then confirm on `selfplay_bench.py` (new product entering a contested market) — key metric is **sold mix showing TOMATO > 0**.

### (Deferred — per fix.md's own scope, not blocked on A/B, can proceed in parallel)

- **Idle-crew routing.** `PASS` rose from 414 (V1) to 829 (V2) with the denser crew — the extra hands pay for themselves but idle roughly half the time. This is a **routing problem, not a headcount one**; the crew-size question itself is closed (4 tiles/hand is correct). A routing redesign, next priority after Fix B per fix.md.
- **Wire `pricing.py` into `main.py`.** Steff's forward-pricing research module is tested (`tests/test_pricing.py`, 24 tests) but isn't called from the agent at all. A research→engineering pass needing its own benchmark cycle.

### Melon oversupply — diagnose before touching again (not in fix.md, separate item)
Melon still finishes near the $1 floor (24 against a base of 250) and V2's demand-aware scoring **did not fix it** — melon volume barely moved (179 → 183 units), the gain came from carrot shifting into strawberry instead. The mechanism is unconfirmed. **Diagnose why demand-awareness didn't touch melon before trying another lever** — three separate throttle/diversification attempts have already failed badly (see dead ends below); don't repeat those specific ideas.

**Do not re-attempt, and don't let anyone else either — these are recorded dead ends in `CLAUDE.md`'s "measured dead ends" section:**
- ❌ `BUY_LAND` — tested twice (low and high capital), lost both times. Diagnosed mechanism: we under-water what we already own, so more acreage just spreads the same crew thinner. Revisit only alongside a genuine upkeep-capacity increase.
- ❌ More than one animal, any species combination — 2/3/4/6 geese all lost; sheep+cow lost worse (-16,634, 0/16) despite being two separate, non-competing markets.
- ❌ Melon throttling/diversification (`SELF_SUPPLY_EXPONENT` up, smaller sell slices) — three separate attempts, all lost badly. (This is *why* the melon item above says diagnose, not throttle-again.)
- ~~Denser crew~~ — **retracted, this is now a confirmed win** (+1,910, 16/16). If you see this called a dead end anywhere older than the V2 freeze, it's wrong — the original claim was a measurement error (judged against across-seed stdev instead of a paired/head-to-head test).

Each of these is exactly the kind of afternoon `CHECKPOINTS.md` warns is "only spent once if you document it" — they're already spent and documented. Don't spend them again, except the denser-crew correction, which is the second dead end this repo has had to retract for the same measurement mistake — worth remembering *why* it happened, not just that it did.

---

## 4. The thing none of the above fixes

V2-sheep's own limitations list still ends with: **no opponent modelling, no lookahead, no multi-turn planning.** That's the actual ceiling on patch-shaped work, not a bug. Fix A, Fix B, idle-crew routing, and melon diagnosis are all worth doing — they're cheap, measured, and close to the last remaining patches — but they're finishing the patch phase, not a path to the top quartile by themselves. Wiring in `pricing.py` is the one item on this list that could plausibly start pointing toward the harder problem, since it's forward-looking rather than reactive.

---

## 5. Before you submit anything

- **Announce in the team channel first.** 5/day, only the latest 2 stay active — a stray upload can silently evict a better agent with no undo.
- **Keep one submission slot as an unchanged control** while evaluating a new one — the only reason the team could tell a 20-point ladder gap was noise and not a real difference. (Currently: control at 469.9.)
- The **PR benchmark gate** in `CONTRIBUTING.md` is still marked **"proposed, not adopted"** — it binds the whole team and needs an explicit yes/no from everyone, not just whoever's currently working.

---

## 6. Watch out for (still current, from `CLAUDE.md`)

- `tiles[y][x]` is row-major; `farmer`/`hands` positions are `[x, y]` — axis flip is a classic silent bug.
- `agent = nikaangukia_meroni` must stay the **last line** of `main.py` — the framework picks the last callable in the module namespace, not one named `agent`. A helper defined below it silently hijacks the submission; the episode still reports `DONE`, every action is discarded, and the bank ends at exactly starting `$3,000`. Treat that exact number as a failure signal, not a strategy result.
- `random` doesn't reproduce on a fixed seed — only `pass`/`starter` do, and self-play doesn't have this problem at all.
- Shed caps at 100 non-seed items; overflow past that is silently discarded, not held.
- Farm hands vanish nightly and must be re-hired each morning.
- 1 second per-turn budget, 60-second overage bank for the whole episode — current agent uses none of it.
- **Never judge a delta against the across-seed stdev (~2,000)** — that measures how much *seasons* differ from each other, not how much your change did. Use the paired difference. This mistake has now caused **three** real results to be mislabeled (daily feeding, fertilizer, and denser crew) — it's not a one-off, treat it as a standing trap.
- **Test count is 108, not 82** — if a cold `unittest discover` reports fewer, the checkout is stale (pre-V2) or something didn't install.
- **Don't trust a freshly-measured self-play stdev against V1/V2's recorded figures** — the pooling-bug fix means anything measured now uses a different (correct) method than what's frozen in those two checkpoint docs. Means compare fine; stdevs don't.
