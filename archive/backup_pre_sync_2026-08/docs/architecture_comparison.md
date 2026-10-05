# Architecture comparison: `main.py` vs. the route-based meta lineage

Research only. `main.py` and `pricing.py` are untouched (`git diff --stat -- main.py
pricing.py` is empty throughout this audit). Nothing merged, nothing submitted.
Peter's files were read via `git show <branch>:<path>` from fetched-but-not-checked-out
remote branches (`origin/agent/moon-md-lead`, `origin/agent/route-v20`) — never
modified.

**A provenance flag up front, because it changes how to read everything below.**
`route_moon_md.py`, `route_moon_tuned.py`, and `route_moon_md_r5.py` are not
Peter's original strategy design. Their own header comments state plainly that
they are a third-party public Kaggle notebook, decoded and lightly parameter-tuned.
`route_v20.py` is a second, different public notebook, submitted completely
unmodified. Section 5 audits this in full. The short version: two named,
attributed, Apache-2.0-licensed notebooks, verified by a teammate reading the
Kaggle page directly (the same gate this repo already used once before, for the
already-shipped `agents/meta_lead3.py`) — plus a separate, real concern this
audit surfaces that licensing does not resolve: the decoded route hardcodes
counters against several *named, identifiable* competitors. See section 5's
closing recommendation before building anything that resembles it.

## 1. Our current architecture (`main.py`)

```
                              obs (raw observation)
                                    |
                              extract_state(obs)
              (farm, private, market_state, day/hour/step,
               opponent_pipeline, unlocked_shops - rebuilt
               FROM SCRATCH every single turn, no memory kept)
                                    |
        +---------------+----------+-----------+------------------+
        |               |          |           |                  |
  choose_farmer_    choose_unit_  decide_    decide_market_    decide_animal_
  action (farmer)   action x N    hire_      actions           market_actions
                     (hired hands) orders    (SELL/BUY_SEED/    + decide_land_
                                              FERTILIZER)         orders
        |               |          |           |                  |
        +-------+-------+          +-----------+------------------+
                |                              |
         {"farmer": [...],           market = hire + sell/buy + animal + land
          "hands": [[...]...]}       orders, truncated to MAX_MARKET_ORDERS_PER_TURN
                |______________________________|
                              |
                    {"farmer", "hands", "market"}  ->  one turn's action
```

**Per-unit decision ladder** (`choose_unit_action`, run independently for the
farmer and every hand, with a shared per-turn claim-set/plant-budget/wheat-budget
so units don't collide): harvest -> water urgent plants -> reclaim a weed
underfoot via `DIG` -> feed/care a hungry animal -> move toward the nearest
urgent tile -> place a carried animal -> plant on empty ground -> deliver
fertilizer -> walk -> pass. Fixed priority order, identical every turn, for
every unit.

**Strategic modules, and what actually decides each one:**

| module | what decides it | forward-looking? | opponent-aware? |
|---|---|---|---|
| **Crop selection** | `choose_crop`: score = `future_price * expected_yield / growth_days`, `future_price` from `estimate_future_price` (own + opponent standing-crop supply, town demand over the crop's own growth window), season-maturity gate | yes, but only for *this one decision* | yes — the **only** place `count_opponent_pipeline` reaches |
| **Land expansion** | `decide_land_orders`: fixed two-quadrant `BUY_LAND` schedule, days 6 and 11 | no | no |
| **Animal purchasing** | `choose_animal_to_build`: care-bank arithmetic picks species, `MAX_ANIMALS=4` hard cap | no | no |
| **Crew/labor** | `decide_hire_orders`/`max_hands_ceiling`: crew size derived from unlocked-tile + animal-structure count, hired every morning before `HIRE_BEFORE_HOUR` | no | no |
| **Market/selling** | `should_sell`: `spot_price >= SELL_PRICE_THRESHOLDS[product]`, flat constant, no forecast at all | **no** | **no** |
| **Liquidation** | `LIQUIDATION_START_DAY=19`, hard day-cliff: sell everything regardless of price | no | no |
| **Opponent awareness** | `count_opponent_pipeline(obs)` reads the opponent's public standing crop **once**, feeds it into `choose_crop`'s forecast only | - | one signal, one destination |
| **State tracking** | none — `extract_state(obs)` is rebuilt from the raw `obs` every turn; no module-level memory, no history buffer, no "what did the opponent do last turn" | - | - |
| **Action sequencing** | fixed per-unit priority ladder + fixed market-order priority (hire, then sell/buy/fertilizer, then animal orders, then land orders), truncated at 10 | - | - |

**Implicit assumption about the opponent, stated plainly because it is the
whole story of section 4:** `main.py` treats the opponent as an
undifferentiated, non-adversarial market participant whose only relevant
footprint is *how much standing crop they currently show*, feeding one price
forecast. It never reads opponent money, hand count, past actions, or
build shape. It never asks "does this look like a mirror of me" or "does this
look like a known opponent archetype." Every decision is a pure, memoryless
function of the current turn's own-farm-plus-market state. This was verified,
not assumed — four separate pricing experiments this session (`opponent_supply_forecast_audit.md`,
`opponent_aware_sell_gate_exact_yield_report.md`, `sell_threshold_audit_report.md`,
`forward_sell_policy_v1_1_report.md`) each independently confirmed the sell
decision has zero opponent-awareness and zero cross-turn memory.

## 2. Peter's agents (`route_moon_md.py`, `route_moon_tuned.py`, `route_moon_md_r5.py`, `route_v20.py`)

All four share **one architecture**, inherited from decoding public Kaggle
notebooks (see section 5). They are not four different designs — they are one
design, with `route_v20.py` at an earlier point in its own version lineage
(smaller, no crop-diversification overlays) and the three `route_moon_*` files
at a later point (larger, from a different base notebook, with several
crop-pivot overlays layered on), differing from *each other* only by a small
number of individually-disclosed constant changes. Read in full by four
parallel research passes over the actual decoded source (not the summary
docs) — every claim below is grounded in quoted code, function names, and
line numbers from that reading.

### Shared architecture

**1. State representation.** Real, persistent, cross-turn memory: module-level
dicts keyed by seat (`0`/`1`), mutated in place across the ~700 calls to
`agent()` within an episode, reset when `step == 0`. Includes a preemption
debt ledger (`_SHIFT_STATE`), an online opponent-market-inference learner
(`_RACE_STATE` — evidence scores, decayed with `_ADAPT_DECAY=0.999`, that
estimate how many steps ahead the opponent's premium sells tend to land),
weed-repair trackers, and one latch-flag dict per opponent-archetype detector.
`main.py` has none of this category at all.

**2. Route selection.** Five complete, pre-recorded ~700-step action
schedules (`_ACTIONS_10C4S_3Q`, `_ACTIONS_8C6S_3Q`, `_ACTIONS_6C8S_3Q`,
`_ACTIONS_6C12S_4Q_FIRST_YARN`, `_ACTIONS_6C12S_4Q_SECOND_YARN` — names encode
cow/sheep/quadrant counts, up to 18 animals on 4 quadrants), stored as
base85+zlib-compressed JSON, decoded at import time. `_kawa_route_label(obs)`
picks one purely from which shop unlocks first among `obs["town"]["unlocked_shops"]`
(a `YARN_STORE`-first vs. -second vs. -third vs. a milk-shop signal). A second
gate, `_kawa_use_legacy_layout`, fingerprints the *opponent's* exact early
tile counts (`{"WHEAT":5,"MELON":5,"COW":1,"SHEEP":4,"PASTURE":0}` and
`money<=12`) and swaps in a parallel "legacy" version of the chosen route if
matched.

**3. Opponent modeling.** Two channels, both reading `obs["farms"][1-seat]`
every turn:
- **Direct fingerprinting**: `_public_signature`/`_clone_distance` build a
  weighted-L1 similarity score (hand count, quadrant count, per-crop/animal
  tile counts) between the two farms — explicit mirror/clone detection.
  `_v17_is_r5_family` (`sheep>=4, cows<=3`) and `_v17_is_md_family`
  (`quadrants>=2 and cows>=4 and sheep<=2`, or `cows>=9`) fingerprint two
  named opponent archetypes and latch permanently once matched.
- **Indirect inference**: `_observe_opponent_market` watches market-inventory
  deltas turn to turn, subtracts known town demand and its own sells, and
  attributes the residual to the opponent — an online estimate of *when* the
  opponent tends to sell, not just *what* they're growing.

**4. Lookahead.** No game-tree search anywhere. Three lookup-based
mechanisms instead: (a) reading its **own** pre-baked schedule N steps
ahead (`_planned_premium`); (b) reading a **separately embedded, pre-recorded
opponent-sell table** N steps ahead (`_V17_R5_MARKETS`, `_V17_MD_MARKETS` —
literal recorded market orders for the two named archetypes); (c) closed-form
NPV projections summing town-demand drain over the remaining season for
crop-pivot decisions.

**5. Replay/history usage.** Foundational, not incidental. Module docstring,
quoted verbatim: *"BL-MDgogo-10C4S-R0: public-replay consensus route with
generic execution guards. This is a behavioral reconstruction from twelve
public traces, not either team's hidden source policy."* Comments name
specific competitors by first name (*"Ryo's public route begins relaying
carrots after its fifth shop... Subramanya's largest public carrot cohort..."*)
and reference a *"Legacy/public Wufang layout"* with hardcoded tile-coordinate
whitelists tied to that named layout.

**6. Adaptive behavior.** Fixed at import: all five route tables, both
opponent-sell tables, every threshold/fraction constant. Adaptive at
runtime, but almost entirely as **one-shot latches, not continuous
adaptation**: route choice, legacy-layout swap, and both archetype detectors
each decide once at a specific step window and never revisit. The one
genuinely continuous learner is the market-inference evidence/horizon
estimator feeding preemption.

**7. Market/selling strategy — the signature mechanism.** `_preempt_shift` +
`_repay_shift`: for `_PREMIUM = ("STRAWBERRY","MELON","MILK","WOOL")`, pull a
sell that's scheduled for a **future** step forward to the current step,
then cancel that same volume at the original step next turn — **volume-neutral,
timing-only**. Gated by `_clone_distance(obs) <= 6` (unconditional against
near-mirrors) or accumulated statistical evidence (against everyone else),
inside step window `[120, 680)`, capped at `_PREEMPT_MAX_BATCH` units. The
route's own comment states the mechanism's purpose directly: *"In a mirror
the alternative to selling into a crashed market is not selling later at a
better price — it is selling one step later at the same crashed price, after
your clone got there first. Being first into a bad market beats being second
into it."* Separately, `_v17_r5_counter`/`_v17_md_counter` inject sells
matching the **opponent's own predicted schedule** (from the embedded
archetype tables) once that opponent's archetype is latched — a second,
independent front-running mechanism, opponent-specific rather than
mirror-specific.

**8-10. Crop/animal/labor strategy.** All baked into the chosen route by
name (6-18 animals, 3-4 quadrants — far larger scale than `main.py`'s 4
animals / up to 3 quadrants). Layered on top: several NPV-gated crop-pivot
overlays (wheat→carrot, strawberry→tomato via two separate mechanisms,
cow/sheep→goose), each keyed to a specific step, shop-mix, and/or opponent
visible-supply signal, several using hardcoded tile-coordinate whitelists
tied to specific named public layouts. Labor is mostly baked into the route;
one small dynamic hire-reconciler exists only for a late-game tomato overlay.

**11. Action scheduling.** A strict linear guard/overlay pipeline (11 stages
in `route_v20.py`, 18 in the `route_moon_*` files), each function taking and
patching the whole action dict in a fixed order — weed repair, feed/room
guards, repay, sell-slot ranking, preemption, both archetype counters, crop
pivots, capacity guards, terminal liquidation, hand alignment — wrapped in a
bare `try/except` that falls back to all-`PASS` on any error.

**12. Preemption.** Covered in full at point 7.

**13. Liquidation/endgame.** Three to four overlapping, escalating layers:
a daily end-of-day shed-overflow guard, a late-hour (`step>=648, hour>=21`)
evacuation, a step-716 top-up sell, a step-718 full liquidation, and (from
`step>=708`) a **complete pipeline replacement** — the scripted route is
abandoned entirely in favor of a live greedy controller that harvests and
sells everything reachable.

**14. Meta-strategy.** The clearest single differentiator from `main.py`:
multiple independent, irreversible regime-switch latches (which route,
whether to swap to the legacy layout, whether to counter a sheep-heavy or
cow-heavy opponent) that permanently change what the rest of the game looks
like, each triggered by reading the opponent's public state once and never
revisiting the decision.

### Mechanical improvement vs. architectural improvement vs. parameter tuning — across the four files

This is the answer to the task's explicit request to distinguish these three
categories, and the finding is sharper than "some of each": **none of the
four files differ from each other architecturally.** Every difference between
them is a **named, individually disclosed constant**, per the Apache 2.0
attribution requirement each file's own header honors:

| file | disclosed changes from the decoded notebook | category |
|---|---|---|
| `route_v20.py` | none — submitted byte-identical, deliberately, "to establish where this route lands for us before we change anything on top of it" | reference baseline |
| `route_moon_tuned.py` | `_ADAPT_MIN_EVIDENCE` 2.0→1.0, `_PREEMPT_MAX_BATCH` 12→24 | **parameter tuning** — header states explicitly "no logic is altered," both are single constants |
| `route_moon_md.py` | the same two, **plus** `_v17_md_counter` lookahead `step+1`→`step+6` | **parameter tuning**, but the third change touches a more consequential mechanism — its own header distinguishes this: *"`_v17_md_counter` is not general market timing — it front-runs a PRE-BAKED MODEL OF ONE OPPONENT ARCHETYPE"* |
| `route_moon_md_r5.py` | the same three, **plus** `_v17_r5_counter` lookahead `step+3`→`step+6` | **parameter tuning**, explicitly labeled by its own author as *"an unmeasured bet"* — the sheep-heavy trigger never fires in their own self-play harness, so this one is untested extrapolation, not a measured result |

No file adds a new mechanism, a new data source, or a new decision axis over
another. The **architectural** gap is not *between* these four files — it is
entirely between this whole lineage, as a single unit, and `main.py`.

## 3. Comparison table

| Capability | Our `main.py` | `route_moon_md` | `route_moon_tuned` | `route_moon_md_r5` | `route_v20` |
|---|---|---|---|---|---|
| **State memory** | none — rebuilt from `obs` every turn | module-global, persists across the episode | same | same | same |
| **Opponent model** | one signal (standing-crop count) into crop choice only | direct fingerprinting (archetype + clone-distance) *and* statistical inference from market deltas | same | same | same, minus the crop-pivot overlays' opponent-supply reads |
| **Lookahead** | one-turn price forecast for crop choice; sell decision has none | table lookups (own schedule, recorded opponent schedule) + closed-form NPV; no game-tree search | same | same | same, narrower item scope (no crop-pivot NPV) |
| **Crop planning** | live scoring (`future_price*yield/growth_days`), replanned every turn | fixed per-route, with NPV-gated pivot overlays on top | same, +2 fewer aggressive pivots (per header ablations) | same as `route_moon_md` | fixed per-route, **no pivot overlays** |
| **Market planning** | flat per-product price threshold, no timing logic | clone/evidence-gated preemption + archetype-specific counter-selling + impact-ranked order batching | same, batch cap 24 vs 12 stock | same as `route_moon_md` | same core preemption, no rival-flush overlay |
| **Land planning** | fixed 2-quadrant schedule, days 6 & 11 | baked into route choice (3-4 quadrants) | same | same | same |
| **Animal planning** | care-bank species pick, hard cap of 4 | baked into route choice (6-18 animals) | same | same | same |
| **Labor planning** | crew size derived from tile/animal count, hired every morning | mostly baked into route; small dynamic reconciler for one overlay | same | same | fully baked into route, no reconciler |
| **Action scheduling** | fixed per-unit priority ladder + fixed market-order priority | 11-18-stage linear guard/overlay pipeline patching one base action | same, 18 stages | same, 18 stages | same, 11 stages (no crop-pivot stages) |
| **Adaptive routing** | none | route/layout/archetype choices, each a one-shot latch on `obs` signals | same | same | same |
| **Replay/history use** | none | foundational — the whole route + 2 opponent-sell tables are reconstructed replay data | same | same | same |
| **Endgame strategy** | one hard day-cliff (`LIQUIDATION_START_DAY=19`) | 3-4 escalating layers, culminating in a full pipeline replacement at `step>=708` | same | same | same |

### What architectural capabilities does Peter's lineage have that we fundamentally lack?

Four, in order of how directly each one maps to a measurable gap:

1. **Cross-turn memory.** `main.py` cannot learn anything about this specific
   opponent over the course of a game, because it never keeps any. Every
   opponent-adaptive mechanism on the other side depends on this existing at
   all.
2. **Opponent-state representation and similarity detection.** We read the
   opponent's public farm for exactly one purpose (standing-crop count for a
   price forecast). We never build a "how similar is this opponent to me"
   or "which known archetype does this opponent match" signal, even though
   the same public data (tiles, money, hands, quadrants) is available to us
   right now, unchanged, from the same `obs`.
3. **Adaptive routing / regime switching.** We commit to one fixed economic
   shape (2 quadrants, 4 animals, one crop-scoring formula) every game,
   regardless of what the town's shop unlocks or the opponent's build imply.
   The other lineage commits to one of several shapes *early*, based on a
   cheap, observable signal.
4. **A mirror-aware selling tactic.** In a field where a large share of
   matches are between near-identical builds (see section 4), a mechanism
   that specifically wins the tie-break in that situation is worth having;
   we have nothing that even detects the situation, let alone exploits it.

**What we already have that this lineage does not, worth stating precisely so
Step 6 doesn't undervalue it:** a live, continuously-recomputed, per-turn
forecast-driven crop-selection formula (vs. a fixed, pre-recorded plan), and
this session's own validated `pricing_v1.py` forecasting machinery
(`estimate_future_price`, `compare_immediate_vs_delayed_selling`,
`estimate_own_pipeline`) — none of which is wired into `main.py`'s sell
decision yet, but which is a **more principled** foundation for a genuine
forward-looking sell timer than a pre-recorded opponent-sell table copied
from twelve public replays. Section 6 builds on this rather than discarding
it.

## 4. Why ~61k local self-play but only 598.2 on Kaggle

Traced from actual code and this session's own already-measured evidence —
not speculation. Every step below cites a specific source.

**1. Self-play cannot see any opponent at all, let alone a stronger one.**
`main.py` has zero opponent-adaptive code (section 1). In self-play, both
seats run byte-identical, memoryless code with no cross-turn state. The
61,303 local mean measures "how well does this economy run with no
adversarial pressure and no scale reference point" — a categorically
different question from ladder performance, where the field is neither a
clone nor passive.

**2. The dominant ladder population is not a diverse field of independent
designs — it is heavily forks of two public notebooks.** `docs/route-generation-gap`
(fetched this session, `origin/docs/route-generation-gap`) reads the actual
leaderboard: `raykkretzschmar` (rank 40, 2,658), `boatlee` — the v20 author
himself — (rank 106, 2,501), `bruceqdu` (108, 2,494), `kunaldesale2408` (186,
2,391), `flexonafft` — *"a fork, not an original"* — (213, 2,364) are all
v20-era. `denizeryilmaz` (673, 1,964), `kaitofukami` (814, 1,891),
`web3cainiao` (1,054, 1,770) are v16-era. **Everything at 2,300+ is v20-era;
everything v16-era is under 2,000** — the same document's own words. This
repo's own submitted v16-derived agent (`agents/meta_lead3.py`, submission
`55650592`) plateaued at **1,687.5, rank 1,223 of 5,940**, and that document's
own conclusion after a full day tuning it further: *"it did not matter,
because the route itself is the constraint... check whether the ceiling you
are optimising under is the ceiling of your approach or the ceiling of your
starting point."*

**3. `main.py` is not a fork of either lineage, and sits below both tiers'
floors.** 598.2 is below even the v16 tier's ~1,687-1,964 range, not just
below the v20 tier's ~2,300-2,658. This is consistent with, not contradicted
by, everything measured about `main.py`'s own economy: `docs/PUBLIC_META.md`
(already committed on `main`, from an earlier session) measured the v16
reference agent beating "our main" (the land-expanded build) by **3-5x
locally** — 53,884 vs 148,321, 29,602 vs 123,856, 29,450 vs 83,451 on three
seeds — using nothing but a **12-animal, 3-quadrant** herd-first economy
against our 4-animal ceiling. That gap was measured *before* today's new
information; it already predicted a large real-world shortfall, entirely
from acreage/herd scale alone, with no preemption or mirror-awareness
involved at all.

**4. The scale gap and the meta-fork density compound, and neither is
visible locally.** Every local harness used across this session's four
pricing experiments — self-play, head-to-head vs. `main.py`, paired vs.
`pass`/`starter` — either mirrors `main.py` against itself or plays a
built-in that never sells. None of them include an opponent that (a) runs a
meaningfully larger economy, (b) detects and exploits mirror matches, or (c)
represents the actual density of near-identical forks the real ladder
contains. **`CLAUDE.md`'s own long-standing finding — "we are mid-field, not
half-size... the top of the field is roughly double" — undersells the size
of the gap for exactly this reason: that finding was itself derived from the
same limited local/ladder-burst evidence, before this session's discovery of
the route-generation tiering.**

**5. Caveat on 598.2 specifically, stated because this repo has been burned
by exactly this before.** `CLAUDE.md` documents that this competition's
Bradley-Terry-style rating is unreliable below roughly 10 episodes
(*"identical code... can agree to within 3 points and disagree by 86 an
episode later"*), and 598.2 sits close to the ~600 seed default new
submissions start at. This alone would not explain a gap this size — every
independently-derived number this session found (the 3-5x local measurement,
the 1,687-2,658 tier structure, the architectural absence of any
opponent-adaptive machinery) points the same direction and is not subject to
the same noise floor — but **treat 598.2 itself as directionally correct,
not as a precise, converged number**, until it's re-read at a real episode
count.

**Conclusion:** the discrepancy is not a bug, a mismeasurement, or evidence
that local self-play is worthless — it is exactly what section 3's
capability gap predicts. `main.py` was tuned exclusively against itself and
against opponents that don't compete, for an entire project's worth of
experiments (see the four pricing reports from earlier today, all judged on
exactly these harnesses), and the one capability shown to matter most on the
real ladder — running the field's shared large-scale economy, or defending
against/exploiting the fact that most matches are near-mirrors — was never
in scope for any of that tuning, because none of the harnesses could
represent it.

## 5. V20 / route-moon provenance and license audit

**What is independently verifiable, and what is not — stated precisely,
because this determines everything else.**

| notebook | title | author | URL | license claim | how verified |
|---|---|---|---|---|---|
| feeds `route_moon_md.py`, `route_moon_tuned.py`, `route_moon_md_r5.py` | "Kaggriculture Frontier | The Moon Counts Melons" | `prvsiyan` | `kaggle.com/code/prvsiyan/kaggriculture-frontier-the-moon-counts-melons` | Apache License 2.0 | "licence verified on the notebook page, 2026-08-23" — a **human** reading the page, per the file's own header |
| feeds `route_v20.py` | "V20-Adaptive-R1 | Multi-Route Agent" | `boatlee` | `kaggle.com/code/boatlee/v20-adaptive-r1-multi-route-agent` | Apache License 2.0 | same, "2026-08-23" |
| feeds `agents/meta_lead3.py` (**already submitted**, `55650592`) | "v16-rc5-high-score-8c-4s-premium-market-lead" | `boatlee` | `kaggle.com/code/boatlee/v16-rc5-high-score-8c-4s-premium-market-lead` | Apache License 2.0 | same gate, already cleared and already shipped |

**A correction to the task's own framing, found while auditing, not
assumed:** the task named "salemali7" as the notebook to trace. That name
does not appear anywhere in the actual `route_v20.py` source — it is a
cross-reference inside a *different* doc (`docs/V20_ANATOMY.md`, on
`origin/agent/route-v20`) noting that a `salemali7` notebook independently
"decodes to a source with the same opening docstring," i.e. a claimed
sibling/duplicate in the same lineage, not the file's actual source. The
code-verified attribution for every file this audit read is `boatlee`
(v20/v16) and `prvsiyan` (moon-counts-melons). Treat the `salemali7`
reference as unverified hearsay inside a working doc, not as this lineage's
real provenance.

**Independent re-verification attempted this session, and its result.** I
tried to confirm the notebooks and their licenses via `WebSearch` and
`WebFetch` before finding the team's own prior audit. Both hit the exact
same wall the team already documented: Kaggle's Code tab is JavaScript-rendered,
so an automated fetch returns an empty shell with no notebook listing,
author, or license field — `WebFetch` on the competition's code-tab URL
returned literally nothing but a page title. This matches `docs/PUBLIC_META.md`'s
original note about the v16 notebook (*"the page is JS-rendered, so it could
not be confirmed programmatically"*) and `docs/route-generation-gap`'s
identical note about v20 (*"Kaggle renders it only in the page's JavaScript...
A human has to open the page and read the licence field"*). **I cannot
independently confirm the license from this environment; the only
verification on record is the human read attested in each file's header,
dated 2026-08-23.** That is a real verification, done the same way the
team's one already-shipped derivative (`meta_lead3.py`) was cleared — but it
is a human attestation, not something this audit (or any automated process)
can re-derive. If that attestation is trusted, the license question is
resolved for these three specific notebooks. If it needs re-confirming
before anything ships, a human opening those three URLs directly is the
only way to do it.

**The acquisition method itself, once misread by me, now resolved.**
`docs/V20_ANATOMY.md`'s phrase *"decoded source... gitignored, never
committed"* initially read, out of context, like it might describe
reverse-engineering a hidden competitor's private code. Reading the actual
decode harness and the files' own headers corrects this: the payload is
**base85+zlib-encoded inside the notebook's own public page** (a common,
if adversarial, Kaggle Simulations practice to slow down casual copying
while the notebook stays technically public), decoded **without executing**
the notebook's code, and verified byte-for-byte against a SHA-256 **the
notebook itself publishes**. `docs/route-generation-gap` states the intent
directly: *"Using it as a local opponent is fine regardless — measuring is
not distributing... Submitting a derivative is gated on that licence."*
`agents/README.md` states it even more plainly: *"Everything here is public,
Apache-2.0-licensed third-party work plus a stated change of ours. Nothing
private and nothing another competitor shared with us."* This is
ordinary — if hardcore — public-notebook culture, not misappropriation.

**What licensing does not resolve, and is a separate concern this audit is
raising on its own initiative.** The decoded route hardcodes three distinct
opponent-fingerprint mechanisms (`_kawa_use_legacy_layout`,
`_v17_is_r5_family`/`_v17_r5_counter`, `_v17_is_md_family`/`_v17_md_counter`),
plus a rival-triggered flush (`_v79_rival_strawberry_flush`) gated on an
exact shop-sequence match, plus comments naming specific competitors by name
(*"Ryo's public route... Subramanya's largest public carrot cohort..."*) and
a *"Legacy/public Wufang layout"* whose exact tile coordinates are hardcoded
into the route. Every ingredient here is individually ordinary — public
replays are visible to any competitor, and studying an opponent's revealed
play pattern from a public match is not different in kind from a human
player noticing "my opponent always opens the same way." But shipping a
submission that carries **hardcoded, named-competitor-specific counter-logic**
is a different question from whether the *notebook* is properly licensed,
and it's one this audit cannot resolve on technical grounds — it is a
fair-play/competition-norms judgment call, not a licensing one.
**Recommendation: do not replicate this specific mechanism (hardcoded
fingerprints keyed to identifiable competitors' known builds) in anything we
design in section 6, independent of how the licensing question resolves.**
The *general* idea — "detect how similar the opponent's build looks to a
known shape, and adjust" — is fine and is exactly what candidate B/D below
build, using our own original similarity computation against **generic
archetypes we define**, not fingerprints matched to a specific named
competitor's exact tile counts.

**Whether Peter's implementation "appears derived from" the notebooks: yes,
explicitly and by design**, not by inference — every one of the three
`route_moon_*` files states this in its own header as the whole point of the
file (decode, verify, disclose the deltas). This is the opposite of hidden
derivation.

**Bottom line for section 6:** per the task's own fallback rule — *"If the
license cannot be verified, treat the code as reference-only and do not copy
implementation details into our submission"* — and given verification here
rests on a human attestation this audit cannot independently reproduce, that
fallback is the safe default. None of the candidates below copy code from
these files. They build originally, informed by the architectural *concepts*
audited in sections 2-3.

## 6. Candidate architecture experiments

Per instruction: no candidate is implemented in this pass. `main.py` and
`pricing.py` remain untouched. This section specifies exactly what each
candidate would change, why, and how it would be judged, so a future session
can implement and test without re-deriving the design.

**A — Current production architecture.** No code change; `main.py`
unmodified. Included in every evaluation as the control every other
candidate is measured against, on both local harnesses and (once submitted)
the ladder.

**B — Opponent-aware state layer.**
*Exact code change:* add one new function to `main.py`, e.g.
`extract_opponent_state(obs)`, reading `obs["farms"][1-player]` for tile
counts by crop/animal type, hand count, unlocked-quadrant count, and money —
all fields already legally visible in `obs`, none copied from any decoded
file. Store the result in `extract_state`'s returned dict as a new key. **Do
not consume it anywhere yet.**
*Hypothesis:* representing opponent state is a necessary but not sufficient
foundation for any opponent-adaptive behavior, and can be added with zero
behavioral risk.
*Expected mechanism:* none — this candidate is explicitly inert.
*What it tests:* that the extraction is correct and cheap (no wrong-field
bugs, no turn-timeout risk) before anything downstream depends on it.
*What would falsify it:* any measurable difference at all from candidate A
on local self-play. Since nothing reads the new state, any difference is a
bug in the extraction, not evidence about the underlying idea. **No Kaggle
submission needed for this candidate** — local self-play equality is the
only test, and it should be exact, not "close."

**C — Route/shape lookahead layer.**
*Exact code change:* a small dispatcher, computed once early in the game
from `obs["town"]["unlocked_shops"]` (the same *kind* of signal
`_kawa_route_label` uses, not its table), that picks between 2-3 originally-defined
economic *shapes* — e.g. "balanced" (current `main.py` defaults) vs.
"animal-heavy" (raise `MAX_ANIMALS`, bias `choose_animal_to_build` earlier,
buy the third quadrant sooner) vs. "crop-heavy" (skip the third quadrant,
raise `WORK_TILES_PER_HAND` density instead) — each shape expressed as a
different set of *our own existing* constants, not a pre-recorded action
table.
*Hypothesis:* `main.py`'s single fixed shape may be leaving scale-driven
value on the table the way `docs/PUBLIC_META.md` already measured for a
12-animal reference economy (3-5x locally) — committing to a bigger shape
early, when a cheap signal suggests the game supports it, could close part
of that gap without copying any specific route.
*Expected mechanism:* more animals/land bought earlier, if the crew-scaling
work already validated this season (`MAX_HANDS_PER_DAY`, `WORK_TILES_PER_HAND`)
holds at a larger scale too.
*What it tests:* whether *shape* (how much of the farm goes where) is a
comparably large lever to the *tactics* `main.py`'s existing tuning already
covers.
*What would falsify it:* no measurable change across several self-play
seeds and a head-to-head vs. unmodified `main.py`, or a measurable loss
(mirroring the earlier `BUY_LAND`/crew-density dead ends already recorded in
`CLAUDE.md`, which found scale changes are only safe when crew and animals
scale together — this candidate needs to re-check that precondition at the
new, larger scale, not assume it still holds).

**D — Adaptive routing / mirror-aware sell timing.**
*Exact code change:* wire candidate B's opponent state into one existing,
already-tuned decision — an *original* similarity computation (e.g. a
simple weighted difference of tile/hand/quadrant counts, defined from
scratch, not `_clone_distance`'s exact formula) that, when the opponent's
build looks very close to our own, biases this session's own
`pricing_v1.py` forward-looking sell machinery (`estimate_sell_or_hold_decision`
/ `estimate_multi_day_sell_or_hold_decision`, already built and tested, never
wired into `main.py`) toward selling sooner rather than waiting.
*Hypothesis:* the *mechanism* behind Peter's preemption — "in a near-mirror
match, being first into a shared, crashing market beats being second" — is
portable even without copying the implementation, and self-play is exactly
the harness that should show it, since self-play is a mirror match by
definition (clone-distance 0 on every single turn).
*Expected mechanism:* in self-play specifically, whichever side's sell logic
reacts to the mirror condition first should show a measurable, consistent
edge over the unmodified twin.
*What it tests:* whether the *mirror-match tie-break* idea has real teeth
for this specific economy, independent of the rest of the route-based
lineage's scale/opponent-archetype machinery.
*What would falsify it:* no measurable, consistent edge in self-play (the
sharpest possible test, since it's *always* a mirror) — if the idea doesn't
show up there, it is not going to show up against a genuinely different
opponent either.

**E — Hybrid.**
*Exact code change:* combine only the pieces of B/C/D that individually
cleared their own falsification bar, on top of the deterministic pricing
backbone already validated this session (`pricing_v1.py`'s forecasting
functions, current `LIQUIDATION_START_DAY`/`SELL_PRICE_THRESHOLDS` —
unchanged, per this session's own sell-threshold audit finding that neither
direction of retuning those constants helped).
*Hypothesis:* the individual pieces compose without interference.
*Expected mechanism:* whatever combination of C's shape and D's timing
survived individually.
*What it tests:* composition risk specifically — two individually-neutral-
or-positive changes can still interact badly (shared cash/crew constraints,
per this project's own repeated "cash trough" lessons).
*What would falsify it:* E performing worse than the better of its
surviving components alone.

### Evaluation protocol (leaderboard is ground truth, per this task's instruction)

1. **B**: local self-play only, exact-equality bar. No submission.
2. **C** and **D**: each gets local validation first (unit tests for any new
   function, several self-play seeds, one head-to-head vs. `main.py`) purely
   to confirm the code *works* and produces the intended behavioral
   difference — not to judge it. Once each is confirmed to behave as
   designed, **each gets exactly one Kaggle submission**, evaluated against
   the current live submission's rating once both have enough episodes to be
   above the noise floor (`CLAUDE.md`'s own established ~10-episode minimum
   before any rating is trusted at all).
3. Do not submit C and D on the same day unless the 5-submission daily
   budget comfortably allows re-reading both later — each is one meaningful
   architectural hypothesis, not a sweep, so combining them in one submission
   would conflate two different questions.
4. **E** is submitted only if at least one of C/D shows a real ladder
   improvement, combining only the surviving piece(s).
5. Keep/reject each candidate primarily on its **ladder** result. A candidate
   that scores lower locally but higher on the ladder is not rejected for
   that reason; the reverse is not accepted for that reason either — per
   this task's explicit instruction, and per section 4's own finding that
   local self-play cannot see the specific gap these candidates are trying
   to close.

## Recommendation

**Build B first, then D, before C.** B is free (no behavioral risk, no
submission cost) and is a hard prerequisite for D. D is the cheapest way to
test the single most directly-transferable idea this audit found — the
mirror-match tie-break — because self-play, the one harness this whole
project has leaned on all along, is *exactly* the right instrument to detect
it (every self-play turn is a mirror). C (shape/scale) is very likely real
value, given `docs/PUBLIC_META.md`'s already-measured 3-5x gap from scale
alone, but it's a bigger, riskier change that revisits ground this project's
own `CLAUDE.md` already flags as having failed twice before when crew/animal
scaling weren't moved together — it deserves its own careful re-validation,
not a rushed first submission.

This is a plan review, not an implementation. Waiting for sign-off before
touching `main.py`, per instruction.
