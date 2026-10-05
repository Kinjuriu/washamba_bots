# Audit: can we construct a more useful opponent-supply forecast?

Audit only. No code changed in `main.py` or `pricing.py`. Nothing merged,
nothing submitted, no new selling policy implemented. This follows up on
`experiments/opponent_aware_sell_gate_report.md`, whose finding was:
the *specific* signal tested (`count_opponent_pipeline` — "does the
opponent currently have any standing tile of this crop") never had a
positive value at the 162 real decision points where our own gate needed
one, across every seed and opponent tested. That report's own
recommendation (section 9) was to check whether a wider-surface-area
signal would actually co-occur with our own gluts before building
anything new. This is that check.

Two new, disposable probe scripts back this audit — not proposed as
permanent tooling, kept for reproducibility:
`experiments/opponent_supply_probe.py` (correlation/variation) and
`experiments/opponent_supply_cooccurrence_probe.py` (the specific
co-occurrence question). Both run self-play (`main.py` vs `main.py`),
read only what a live agent's `obs` would contain, and print aggregate
statistics — no replay JSONs committed.

## 1–2. What's observable, what isn't

Read directly from the installed engine
(`kaggle_environments/envs/kaggriculture/kaggriculture.py`), specifically
`_new_farm`, `_new_plant`, `_new_animal`, `_daily_refresh_plants`,
`_daily_refresh_animals`, the `HARVEST` handler, and — the load-bearing
fact this whole audit turns on — `_initialize`/`update` wiring each
`state[i].observation.farms = obs0.farms` (`kaggriculture.py:271`,
`952`): **every player's observation gets the literal same `farms` list
object.** There is no redaction between "my farm" and "their farm" the
way there is for `private`. Verified by reading the assignment, not
inferred from behavior.

| variable | class | basis |
|---|---|---|
| opponent land (tiles, locked/owned) | **directly observable** | `obs["farms"][1-player]["tiles"]`, same shared object |
| opponent crops (which tile, which crop) | **directly observable** | tile dict, `kind`/`crop` |
| **crop maturity / accrued yield (`yield_units`)** | **directly observable, exact** | tile dict carries the live `yield_units` field the engine itself uses — `HARVEST` moves exactly this many units to inventory (`kaggriculture.py:446-462`) and zeroes it. Not an estimate; it's the actual counter. |
| watering compliance (`consecutive_unwatered`, `watered_today`), fertilizer (`fertilized_until_day`), planted day | **directly observable** | same tile dict |
| opponent inventory (shed contents) | **unavailable** | lives in `private["shed"]`, and `state[i].observation.private = privates[i]` — each player gets *only their own* `private` (`kaggriculture.py:269`). Opponent's is never assigned into our observation. Confirmed by reading the assignment, and matches `CLAUDE.md`'s standing note. |
| opponent per-farmer/hand inventory (harvested, not yet dropped to shed) | **unavailable** | same `private["inventories"]`, same per-player split |
| opponent seeds held | **unavailable** | `private["seeds"]`, same split |
| opponent cash | **directly observable** | `farm["money"]`, shared `farms` object |
| opponent animals (species, `yield_units`, `consecutive_unfed`, `fed_today`, `cared_today`, `pending_care_bonus`, `placed_day`) | **directly observable, exact** | animal tiles carry the same fields as plant tiles, same shared object |
| opponent labor (hand count, hand positions, `hires_today`) | **directly observable** | `farm["hands"]`, `farm["hires_today"]` |
| opponent's *chosen action this turn* (what they submitted) | **unavailable directly; inferable from before/after diffs** | `obs` has no action log (confirmed against the documented key set: `player, day, hour, step, farms, market, town, private, remainingOverageTime` — no `actions`/`log` field). What we get is the *result* one step later — a tile disappearing, money changing, a market inventory delta — which is a diff of already-public state, not a leak of anything private. |
| opponent selling actions specifically | **inferable, noisy** | market inventory rises on any SELL by either player and falls on town consumption (and rises again on our own or their `BUY_PRODUCT`/`BUY_SEED`). Isolating "how much of this delta was the opponent's SELL order" requires subtracting our own known contribution and a town-demand estimate (`pricing.py`'s `apply_town_demand`, already verified against the engine) from the observed net change — a real computation, not a single field read, and never product-attributable with certainty when both players trade the same product the same turn (see the concurrent-selling mechanic `pricing_engine_notes.md` already flagged). |
| market inventory / prices | **directly observable, exact, shared** | `obs["market"]` is the same object for both players (`state[i].observation.market = obs0.market`) |
| town demand / unlocked shops | **directly observable** (current unlocks); **future unlocks are stochastic and unavailable** | `obs["town"]["unlocked_shops"]` is a live snapshot; shop unlocks sample with replacement going forward, per `CLAUDE.md` |
| remaining season | **deterministically derivable** | `SEASON_DAYS - obs["day"]`, both constants/fields already read every turn |

**One caveat that matters for *building*, not for *observability*:**
turn-to-turn state (e.g., "how much did the opponent's shed grow between
last turn and this one," which requires remembering last turn's
observation) needs the agent to keep its own memory across calls within
an episode. `kaggle_environments/agent.py`'s `build_agent` loads the
module once and reuses the same callable for the whole episode locally
(`agent.py:143-152`, the `if agent is None:` / `nonlocal agent` pattern)
— so a module-level cache *would* persist turn-to-turn in this harness.
Whether the live Kaggle scoring process gives the same one-process-per-
episode guarantee is not verified here (out of scope for an audit that
touches no code) and should be checked before anything is built that
depends on it — the code's own comment flags this as an assumption, not
a guarantee ("assuming an agent is a global callable is not enough to
guarantee it is stateless").

## 3–4. Candidate signals, precisely defined

All of these read only fields established as directly observable above —
no candidate here uses opponent shed/inventory/seeds.

1. **`opponent_standing_yield[crop]`** — sum of `tile["yield_units"]`
   over the opponent's own `PLANT` tiles of that crop, right now. This is
   the smallest change from the existing (rejected) signal: swap
   `count_opponent_pipeline`'s `crop_info["max_yield"]` per tile (a flat
   ceiling assumed the instant *any* tile of that crop exists, regardless
   of how far along it is) for the tile's real, exact `yield_units` (what
   `HARVEST` would actually move to inventory this instant). Same data
   source, same loop shape, one field swapped.
2. **`opponent_standing_yield_animals[product]`** — same computation over
   animal tiles (`WOOL`/`MILK`/`EGG`).
3. **`opponent_projected_supply[crop, N]`** — (2) projected `N` turns
   forward using the engine's own accrual rule
   (`_daily_refresh_plants`/`_decay_plants`), anchored on the *observed*
   current `yield_units` rather than reconstructed from `planted_day`
   alone. `pricing_v1.estimate_own_harvest_units` already implements this
   accrual formula (validated against a live episode per its own
   docstring) but derives the day-0 value from `planted_day`, assuming
   perfect watering compliance the entire time; anchoring on the observed
   value instead is strictly more accurate whenever the opponent ever
   missed a watering day, and costs nothing extra to compute. Not
   measured separately in this audit (see recommendation) — flagged as
   the natural refinement of (1), not a new mechanism.
4. **Net-inventory-change residual** — `Δmarket_inventory[crop]` over a
   window minus our own known contribution minus `apply_town_demand`'s
   prediction, as a proxy for "how much the opponent (and us, on the
   buy-back side for WHEAT/FERTILIZER) actually moved this turn." Not
   computed in this audit; listed because it's the only candidate that
   reaches toward *actions* rather than *standing crop*, at the cost of
   being an inference rather than a read.

Signal (1) is what was actually measured below — it directly answers the
task's reframed question ("expected units entering the market soon"),
it's the cheapest to compute, and it's the direct upgrade of the
mechanism the previous experiment already implemented and instrumented,
which keeps this a controlled comparison rather than a fresh design.

## 5–6. Does it vary, and does it predict anything?

`experiments/opponent_supply_probe.py`, 6 self-play seeds (`main.py` vs
`main.py`, 720 turns each, 4,320 turn-observations per product). For
each product, fraction of turns with `opponent_standing_yield > 0`, then
Pearson correlation of that value against the price change and market-
inventory change over three forward horizons (24/48/96 turns = 1/2/4
days), plus a grouped mean comparison (`opponent_standing_yield == 0` vs
`> 0`):

| product | turns with signal > 0 | corr(signal, Δprice) at N=96 | corr(signal, Δinventory) at N=96 | mean Δprice, sig=0 vs sig>0 (N=96) |
|---|---|---|---|---|
| **MELON** | 83.2% | **-0.73** | **+0.78** | +4.5 vs **-15.0** |
| **STRAWBERRY** | 38.2% | **-0.56** | **+0.58** | +22.6 vs **-19.2** |
| **WOOL** | 30.3% | -0.22 | +0.29 | -3.8 vs **-22.8** |
| WHEAT | 24.6% | -0.13 | -0.37 | +3.4 vs +3.3 (no real difference) |
| CARROT | 6.6% (thin) | +0.42 (wrong sign) | -0.43 | +1.5 vs +6.7 |
| MILK | 41.3% | -0.05 | -0.28 | +21.8 vs +20.7 (no real difference) |
| TOMATO | 0% | — | — | never positive in 6 seeds |
| EGG | 0% | — | — | never positive in 6 seeds (no GOOSE in the current build) |

Full table with N=24/48 rows in the probe's stdout; not reproduced here
for brevity — every product's correlation strengthens monotonically as N
grows, which is itself a sanity check (a real supply-timing signal should
matter more the further out you look, up to the point the crop's own
cycle ends).

**Reading this against the engine's own price-decay shapes
(`CLAUDE.md`'s market table) is what makes it more than a coincidence:**
MELON (`sq`, steepest decay, 158 units to floor), STRAWBERRY (`linear`,
62 units to floor) and WOOL (`sq`) are exactly the three products where
the signal is strong — the ones whose price is *structurally* sensitive
to added supply. WHEAT (`log`, 2000+ units to floor) and CARROT
(`sqrt`, decent absorption) are exactly where it's weak or absent — their
price barely moves regardless of who's adding supply. This is the same
mechanism `pricing_engine_notes.md` and the melon/glut sections of
`CLAUDE.md` already document from a different angle; this audit adds
that the opponent-supply signal's *usefulness* is concentrated in
precisely the same products, for the same structural reason.

CARROT's positive (wrong-direction) correlation and MILK/WHEAT's null
result are flagged, not explained away — CARROT in particular runs on
only 6.6% of turns (284/4320) and deserves more data before trusting the
sign at all.

### The co-occurrence question, re-run with the corrected signal

The previous experiment's actual failure mode wasn't "no variation" — it
was "zero co-occurrence with our own real glut, at the 162 decision
points checked." `experiments/opponent_supply_cooccurrence_probe.py`
re-runs that specific question with `opponent_standing_yield` in place
of `count_opponent_pipeline`, using shed-quantity-above-10 as a glut
proxy, split at the *live* `LIQUIDATION_START_DAY` (verified as `19` in
current `main.py:523` — not the `10` an earlier `CLAUDE.md` section
describes as shipped; trust the code), since the gate this signal would
feed only matters before that day:

| product | glut turns, day<19 (gate active) | of those, opp signal > 0 | mean opponent yield during our glut |
|---|---|---|---|
| **MELON** | 14 | **14/14 (100%)** | 5.14 |
| STRAWBERRY | 0 | — | never accumulates >10 held before day 19 in these seeds |
| WOOL | 4 | 0/4 | 0.00 |

**MELON is a clean, complete reversal of the earlier finding at n=14.**
Every single time our own shed held more than 10 units of MELON before
liquidation, the opponent's tiles also showed positive standing yield of
MELON at that exact turn. This is not proof the two reports contradict
each other — the sampling isn't identical (this probe uses a coarse
shed>10 proxy over an aggregate of 6 seeds; the original report
conditioned per-turn on `should_sell` actually returning `False` for the
specific product, across 2 of its seeds) — but it is strong enough,
freshly measured evidence to say the presence/absence signal's failure
mode does *not* obviously generalize to the exact-yield signal, and this
should be re-checked with an apples-to-apples version of the original
diagnostic before concluding anything further either way. n=14 is small;
treat this as promising, not settled.

STRAWBERRY never built a pre-liquidation glut at all in these 6 seeds —
worth noting since STRAWBERRY's `first_yield_day = 10` (ongoing crop,
`_daily_refresh_plants` gates all accrual on this) means it has a real,
engine-enforced floor on when it can produce anything at all, which
compresses how much of the season is even available to glut before
`LIQUIDATION_START_DAY = 19` handles it anyway.

## 7. Leakage risks

- **Everything used above (tile `yield_units`, `planted_day`, animal
  fields, `farm["money"]`, `farm["hands"]`) comes from the same shared
  `obs["farms"]` object a live agent already receives every turn** — not
  from `env.steps` replay history, not from `state[1].observation`
  accessed out of band, and not from anything the opponent's own private
  namespace holds. Confirmed by reading the assignment in
  `kaggriculture.py`, not assumed.
- **Do not read the opponent's `private`** — a research harness that
  iterates `env.steps` for analysis (as this audit's probes do) has
  access to *both* players' full `Struct`, including
  `steps[t][1].observation.private`, which a live agent never sees. Both
  probe scripts here only ever read `step[0].observation` (the same
  object a real player-0 agent's `obs` argument would be) and only
  reach into `obs["farms"][1-player]`, never `obs["private"]` for the
  opponent — but this is an easy mistake to make in exactly this kind of
  research script, worth flagging explicitly for whoever builds on this.
- **The correlation analysis itself has a look-ahead structure by
  design** (feature at turn T, outcome at T+N) — appropriate for
  *validating* a signal offline, but a reminder that any future model
  trained this way must never let a *decision* at turn T see anything
  from T+N; nothing here does, since the whole point was measuring
  whether T predicts T+N, not building a decision.
- **Module-level cross-turn memory** (needed for the diff-based
  candidate signal, #4 above) is an unverified assumption about the live
  scoring environment's process model, not a leakage risk in the
  information-theoretic sense — but a silent-failure risk in this
  repo's usual sense (per `CLAUDE.md`'s "silent-failure gotchas"): if the
  assumption is wrong, the agent doesn't crash, it just quietly loses its
  memory every turn and the feature silently degrades to nothing. Verify
  before depending on it.

## 8. Recommendation for the next experiment

**Not "no predictive signal exists" — the opposite.** The reframing this
task asked for (standing-crop presence → exact accrued yield) already
shows real, engine-consistent, horizon-strengthening correlation for
MELON, STRAWBERRY and WOOL, and a co-occurrence rate for MELON (14/14 in
this sample) that directly contradicts the previous report's "zero of
162" on the crude signal. The earlier rejection was correctly a rejection
of *that specific implementation*, not of the underlying idea, exactly as
`opponent_aware_sell_gate_report.md`'s own section 9 anticipated.

Recommended next step, smallest first:

1. **Re-run the exact original diagnostic** (per-turn, per-product,
   conditioned on `should_sell(...) == False`, excluding liquidation
   turns, same seeds where possible) but swap `count_opponent_pipeline`
   for `opponent_standing_yield` (signal #1 above) as the only change.
   This directly tests whether the earlier zero-effect result reverses,
   using the same measurement the earlier report already trusted, rather
   than a new proxy (shed>10) introduced for this audit's convenience.
2. If that reverses cleanly for MELON, re-run
   `opponent_aware_sell_gate.py`'s full evaluation (self-play, head-to-
   head, `paired_compare.py` vs `starter`) with the signal swapped and
   nothing else changed, so the result is attributable to the one
   variable that moved.
3. **Do not widen scope beyond the swap in the same experiment** — no
   projected-forward version (#3), no cadence integration, no
   `LIQUIDATION_START_DAY`/`SELL_PRICE_THRESHOLDS` retuning alongside it.
   If the swap alone doesn't move the needle, the projected/cadence
   directions are the next things to try, in that order, each as its own
   measured change.
4. **Keep an eye on WOOL and STRAWBERRY's near-total lack of pre-
   liquidation co-occurrence in this sample** (0/4 and 0/0) — the signal
   may be real for those markets (both show strong unconditional
   correlation in section 5–6) without ever actually reaching the sell
   gate before liquidation takes over, the same disconnect the earlier
   report found for the old signal. If step 1 confirms this for those
   two products specifically, the more useful next experiment for them
   is probably cadence/pacing *within* the liquidation window (where
   `should_sell` is already bypassed but *how much* to sell each turn
   still matters), not a pre-liquidation gate — this is `pricing_engine_notes.md`'s
   already-proposed layer 2, not a new idea, and the reverted
   `experiment/sell-cadence` branch is prior art to read first per that
   doc's standing caution.

No implementation follows automatically from this audit.
