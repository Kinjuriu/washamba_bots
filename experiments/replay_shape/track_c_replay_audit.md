# Track C — Replay Analysis → Executable Constraints (Issue #21)

Forensic audit only. **No strategy code written or modified. `main.py`
untouched.** Branch: `track-c/replay-audit`, off `main` (`4bf0155`). Not
merged, not submitted, no checkpoint created.

Issue #21's own framing, quoted because it's the right discipline for this
whole document: *"We're not trying to clone another team's agent. We're
trying to identify the underlying mechanism."* Issue #21 asks specifically
for necessary-vs-correlated-vs-timing. That's the spine of this report.

## Method

Every claim below is checked against a primary source, not restated on
trust. Primary sources, in order of how much weight they carry:

1. **`ROADMAP.md`** — 6 replay episodes, host-downloaded, spanning Aug 1,
   Aug 10, Aug 16 (×3), 8 distinct player pairings. This is the *origin* of
   Issue #21's headline numbers.
2. **`docs/REPLAY_ANALYSIS.md`** — an *independent* re-verification using 2
   **different** episodes (IDs `93459920` and `90849277`, Aug 16 and Aug 8,
   confirmed via `info.TeamNames` to be different teams than ROADMAP.md's
   sample). This is the only claim-checking that has actually happened
   inside this repo so far.
3. **`experiments/ladder_episodes.py`'s commit message** (`c431769`) — a
   *third*, independent data source: our own live ladder matches, read via
   Kaggle's episode API, not a downloaded replay. Confirms opponents
   banking up to **$114,678** directly, no replay file involved.
4. **Issue #19 / Track A**, closed 2026-08-18, and its evidence branch
   `experiment/land-and-crew` (commit `1d5be21`) — the first attempt to
   turn this evidence into code, bundling land+crew+crop-windows+
   liquidation-timing as ROADMAP.md itself insists it must be tested.
   **Result: not shippable.** This is load-bearing for section D below —
   several of Issue #21's own "target" values were already tried together
   and the bundle lost on the harness that matters (head-to-head).
5. **Issue #23 / Track D** — a live, not-yet-tested refinement hypothesis
   born directly from Track A's failure (land-for-pasture instead of
   land-for-crops). Cited for context, not verified here.
6. Current `main.py`, `pricing.py`, and `tests/` — to establish what's
   already implemented vs. what a "constraint" would need to add.

## Claim-by-claim audit

### 1. "~75 owned tiles"

- **Source**: ROADMAP.md (6 episodes, descriptive) + REPLAY_ANALYSIS.md
  (2 episodes, both independently confirm).
- **Evidence**: REPLAY_ANALYSIS.md's own numbers: tiles `25 → 50 → 75` and
  `25 → 75` — i.e. **two staged expansions to exactly 75**, not a single
  jump, not a range around 75. `1d5be21` reproduced this mechanically:
  `decide_land_orders` buying two quadrants gets to 75 exactly.
- **Category**: (1) directly observed fact, corroborated in 2/2
  independently-checked episodes on top of the original 6.
- **Confidence**: High that 75 is the number (not "~75" — it's the exact
  ceiling of buying both purchasable quadrants at the default board size).
  Not yet established whether 75 is *necessary* (see claim 8 below).
- **Executable constraint?** The *number* is safe to hardcode as a target
  (it's just "buy both available quadrants"). Whether to *pull the trigger*
  is not settled — see claim 9.

### 2. "13–15 crew"

- **Source**: REPLAY_ANALYSIS.md, directly measured: "crew held 12-13,
  days 8-29" (episode 1) / "15, days 12-29" (episode 2).
- **Evidence**: Two data points, `12–13` and `15` — a real range, n=2.
- **Category**: (2) range observed across multiple replays (thin — 2
  episodes, not a distribution).
- **Confidence**: Medium. Directionally solid (well above our ~6), but a
  2-point range shouldn't be read as a tight target band.
- **Distinct from a different number that's easy to conflate with this
  one**: REPLAY_ANALYSIS.md separately reports "`HIRE` orders 277 / 263" —
  that's **total hire orders issued over the whole 30-day season**
  (hands are re-hired every morning, per `CLAUDE.md`), not simultaneous
  crew size. Issue #21's own table keeps these distinct correctly ("Crew"
  vs. no separate HIRE-count row), but the user's prompt for this task
  listed "crew around 263–277" as if it were a crew-size figure — **it
  is not; it's the hire-order count**, and conflating the two would produce
  a wildly wrong target. Flagging this explicitly since Issue #21 asks not
  to trust headline numbers at face value.
- **Executable constraint?** `1d5be21` already tested a derived-crew
  formula (`hand_cap_for_farm = max(MAX_HANDS_PER_DAY, owned // 5)`) and
  reproduced "crew held at 13 from day 12 to 28" — mechanically matches.
  The formula itself is safe to implement; whether it should be *active*
  depends entirely on land (claim 9), since at 25 tiles it's a no-op by
  construction (confirmed in the commit message: "exactly 8 at 25 tiles,
  so it is a no-op until land fires").

### 3. "8–9 animals"

- **Source**: REPLAY_ANALYSIS.md: `COW ×6 SHEEP ×3` and `COW ×5 SHEEP ×3`
  → totals 9 and 8.
- **Evidence**: n=2, both episodes agree the total is 8–9, and both show
  cow outnumbering sheep 5–6:3 (i.e. "5-6 cows + ~3 sheep" is directly
  where this specific split comes from — confirmed, not inflated).
- **Category**: (2) range across 2 replays, real but thin.
- **Confidence**: Medium on the total (8–9), medium-low on the exact
  species split generalizing (n=2).
- **Executable constraint?** **Not yet, and there's a directly relevant
  measured caution against jumping here.** Our own species-diversity work
  (commit `ec38fc5`, shipped) swept animal counts on the *current* 25-tile
  farm and found the mean peaks at "2 sheep + 1 cow" (`MAX_ANIMALS=3`,
  +5,191 paired) — "3 sheep + 3 cow" (`MAX_ANIMALS=6`) was a **heavy loss
  on a single seed probe**. That's the same land/crew-upkeep confound
  ROADMAP.md §3b already names for `BUY_LAND`: more animals on a farm that
  can't feed/water them isn't free. Scaling toward 8–9 animals is coupled
  to claims 1 and 2, not an independent knob — this is exactly what Issue
  #21's question 2 ("what is merely correlated?") is asking about, and the
  honest answer is: **we don't know yet whether 8-9 animals is a
  consequence of 75 tiles / 13-15 crew, or an independently useful target.**

### 4. "First land purchase day 6-ish, second ~day 11"

- **Source**: REPLAY_ANALYSIS.md, directly measured: `BUY_LAND` days
  `[6, 11]` and `[7, 11]`.
- **Evidence**: n=2, tightly clustered (6 or 7, then 11 both times).
  ROADMAP.md's 6-episode summary independently states "exactly 2×, every
  episode, always day 6–11" — a *stronger*, higher-n claim than the
  2-episode spot check alone, and the two sources agree.
- **Category**: (1) directly observed fact, well corroborated (6 + 2
  episodes, consistent window).
- **Confidence**: High on the window (day 6–7, then ~day 11). This is one
  of the best-evidenced numbers in the whole hypothesis list.
- **Executable constraint?** The *day* is safe to hardcode as a target
  once/if land purchasing is implemented at all — `1d5be21` used days 6
  and 11 directly and reproduced the shape correctly. Still gated on
  whether to implement `BUY_LAND` at all (claim 9).

### 5. "Meaningful selling from ~day 10, no day-22 cliff"

- **Source**: ROADMAP.md primarily. **This is the weakest-verified claim
  in the whole list.**
- **Evidence**: ROADMAP.md's table states it as a conclusion from the
  6-episode sample but does not show the underlying per-day sell counts in
  the document. REPLAY_ANALYSIS.md's 2-episode check reports only
  **season totals** (`SELL orders 501` / `175`) and a single derived
  figure per episode ("first sell-heavy day: 10" for both, from
  `replay_shape.py`'s own logic, which flags a day as "sell-heavy" once it
  hits ≥10 orders) — it does **not** independently re-derive "15–48
  orders/day" or explicitly re-check for a day-22 discontinuity.
- **Category**: (1) for "starts ~day 10" (2/2 independently confirms this
  specific figure via `replay_shape.py`'s own computed first-sell-heavy-day
  output). (4) hypothesis, not independently re-verified, for the specific
  "15–48 orders/day" range and the "no day-22 cliff" claim — both rest on
  ROADMAP.md's original 6-episode read alone.
- **Confidence**: Medium-high that selling ramps starting ~day 10.
  Medium that there's no day-22 cliff (plausible, matches the "no explicit
  late-game phase" finding elsewhere, but not independently re-derived
  from the 2 spot-check episodes' raw step data). Low-medium on the
  specific 15–48 bound (a range from n=6 episodes without the per-day data
  shown, not a distribution the audit can independently characterize).
- **Executable constraint?** "Don't liquidate on a hard day cutoff, ramp
  instead" is safe to act on directionally (matches this repo's own
  independent finding that `LIQUIDATION_START_DAY=19` head-to-head beats
  `25` — a *different*, already-shipped piece of evidence for smooth vs.
  cliff behaviour, not the replay data, but pointing the same way). The
  literal 15–48 number should **not** be hardcoded as a target without
  first re-deriving it from a replay's raw per-day step data — that's a
  cheap, concrete follow-up (see section G).

### 6. Per-crop planting windows (MELON early, STRAWBERRY narrow, WHEAT continuous, CARROT late, TOMATO avoided)

- **Source**: Both ROADMAP.md (6 episodes) and REPLAY_ANALYSIS.md (2
  episodes, independently).
- **Evidence, reconciled precisely** (this one has real disagreement worth
  flagging):
  - **TOMATO never planted**: **8/8 episodes across both sources agree.**
    The single most robust finding in this entire audit.
  - **WHEAT continuous, days 0–27**: 8/8 agree on the window; unit counts
    vary (127 / 108 / and ROADMAP's 6-episode figure of 127 again) — the
    *window* is solid, the *volume* varies by game length/seed.
  - **STRAWBERRY narrow window**: ROADMAP says days 5–12. The 2
    verification episodes show `5–12` and `7–11` — **both inside**
    ROADMAP's window, good agreement.
  - **MELON early-only**: ROADMAP says "days 0–7 only, then stops." The 2
    verification episodes show `0–7` and **`0–11`** — one episode's melon
    window runs 4 days past ROADMAP's stated cutoff. This is a real,
    if minor, disagreement between the 6-episode summary and one of the
    2 spot-check episodes.
  - **CARROT late-filler, days 21–25**: ROADMAP states this as a
    consistent pattern. The 2 verification episodes show it in **only
    one of two** (`days 21-25` in episode 1, **`none` at all** in episode
    2). This is the largest disagreement found in the audit — CARROT's
    late-filler role is not universal even in the small verification
    sample.
- **Category**: TOMATO/WHEAT/STRAWBERRY = (1) directly observed,
  well-corroborated facts. MELON = (1) fact with a soft edge (window may
  extend to day 11, not always day 7). CARROT = (3) correlation at best —
  present in roughly half of directly-checked episodes, not a rule.
- **Confidence**: High (TOMATO, WHEAT, STRAWBERRY), Medium (MELON — window
  boundary uncertain), Low (CARROT — inconsistent even at n=2).
- **Executable constraint?** Safe now: **stop planting TOMATO** (already
  true of current agent — "rare," per ROADMAP, and this audit found no
  code path that plants it deliberately) — this is a no-regret,
  fully-verified constraint. MELON early-window and STRAWBERRY
  narrow-window are reasonable to prototype but should keep the window's
  right edge as a tunable, not hardcode day 7 given the day-11 exception.
  CARROT's day-21-25 rule should **not** be implemented as a hard
  constraint yet — the evidence doesn't support it as a rule rather than
  an occasional pattern.

### 7. "Large agents banking $90k–$100k"

- **Source**: The user's hypothesis list states this range. Checked
  against all three data sources.
- **Evidence**: REPLAY_ANALYSIS.md's two episodes: **$95,288 / $91,904**
  (inside the claimed range) and **$54,528 / $52,963** (well below it —
  roughly half). ROADMAP.md's 6-episode range is wider: "$71,757 –
  $126,015." `ladder_episodes.py`'s commit message adds a third,
  independent data point from live matches: an opponent observed banking
  **$114,678** (above the claimed range's ceiling).
- **Category**: (3) — this is better described as **"a wide observed
  range with the $90k-100k band sitting inside it, not defining it"**
  than as a verified fact. The specific "$90k-100k" framing in the
  hypothesis list is **not what the evidence shows** — the true observed
  range across all three sources spans roughly **$53k to $126k**, more
  than 2× wide.
- **Confidence**: High that top agents bank far more than us (~$50k vs.
  our current ladder average of ~$52,500, per `ladder_episodes.py`'s
  commit message — comparable floor, much higher ceiling). Low confidence
  in "$90k-100k" specifically as a representative target — it understates
  the real spread on both ends.
- **Executable constraint?** Not directly — this is an outcome metric, not
  a lever. Useful as a benchmark sanity check (are we closing the gap),
  not as something to implement toward directly.

### 8. Necessity vs. correlation (Issue #21's actual question)

This is the one Issue #21 explicitly asks for and it's the one this repo
already has the best answer to, because Track A tried it:

- **Land and crew are necessarily coupled, not independently optimal.**
  `1d5be21`'s ablation is the clearest evidence in this whole audit:
  self-play seed 0, main = 41,392; **+ land + crew alone = 15,727** (a
  collapse — "STRAWBERRY price 195 → 20," the crew waters the acreage but
  the market floods); + crop windows recovers to 32,834; + liquidation
  timing recovers further to 46,759. **None of the three components pay
  off alone; the bundle barely breaks even against main's baseline.**
  This directly answers Issue #21's question 2 ("do they have 13-15 crew
  because they own 75 tiles, rather than 13-15 being inherently
  optimal?") — the evidence says land and crew are a coupled pair, and
  neither one is independently "the target."
- **What's still unknown**: whether **selling throughput** (not land, not
  crew, not crop windows) is the actual remaining binding constraint.
  `1d5be21`'s own conclusion: "they fire 501 SELL orders to our 273... 
  Selling throughput, not acreage, looks like the next binding
  constraint." This is an unverified hypothesis, not yet tested in
  isolation on top of the land+crew+windows+liquidation bundle.

### 9. Should land/crew scaling become an executable constraint now?

- **Direct answer from the repo's own most recent, most rigorous test**:
  **no, not as currently formulated.** Issue #19 / Track A is **closed**
  with the bundle measured **not shippable**: head-to-head +161 mean,
  14/24 wins, **worst match −17,301**; self-play mean essentially
  unchanged (41,919 vs. 42,017) with **2.6× the variance** and the floor
  down from 33,269 to 24,276. Two of three harnesses reject it; the one
  that likes it (`paired_compare.py` vs. `starter`, +8,669, 11/12) is
  explicitly the harness that "never sells, so it cannot see market
  flooding at all" — the same structural blind spot `docs/CHECKPOINTS.md`
  already warns about for anything involving selling.
- **A real documentation gap found by this audit**: `CLAUDE.md` (lines
  138–142, 165) still states the *original*, now-superseded conclusion —
  "`BUY_LAND` is a loss, even when rich... the crew, not the acreage, is
  the ceiling" — as a settled dead end. That conclusion predates both
  `da8cdea` ("BUY_LAND and multi-animal are not dead ends" — overturns the
  *reason* for the old conclusion) and `1d5be21` (tests the corrected
  version and *still* finds it not shippable, for a **different** reason —
  selling throughput, not crew capacity). `CLAUDE.md` currently reflects
  neither of the two more recent, more informed conclusions. This should
  be corrected regardless of what Track C decides next, since it's the
  team's stated source of truth.

## A. VERIFIED FACTS

(Directly observed, corroborated across independent sources, not merely
asserted)

1. Winning replay agents plant **zero TOMATO** — 8/8 episodes across both
   independent evidence sets.
2. **WHEAT is planted continuously**, days 0–27, in every episode checked.
3. Land expansion happens in **exactly two purchases**, clustered at
   **day 6–7 and day 11**, reaching **75 tiles** — consistent across 6 + 2
   independently-sourced episodes.
4. **Selling starts ramping around day 10** — independently reconfirmed
   via `replay_shape.py`'s own "first sell-heavy day" computation on both
   spot-check episodes.
5. Land, crew, and market-flooding are **causally coupled** — adding land
   and crew alone (no crop-window or liquidation-timing change) *collapses*
   self-play performance (41,392 → 15,727 in one measured ablation) via a
   crashed STRAWBERRY market. This is a directly measured mechanism, not
   an inference.
6. **`BUY_LAND` is currently not implemented at all** in `main.py` (no
   `BUY_LAND` action is ever emitted); no land-related tests exist.

## B. STRONG CORRELATIONS

(Consistent pattern, but causal direction or generality not established)

1. **13–15 crew co-occurs with 75 tiles** in every episode checked — but
   Track A's own evidence shows this is a *coupled* pair, not two
   independently-optimal numbers picked in isolation.
2. **STRAWBERRY narrow mid-season window** (roughly day 5–12) — consistent
   across all checked episodes, and mechanistically explained (it's the
   shallowest premium market, floors fastest on oversupply).
3. **8–9 animals, split roughly 5–6 cow : 3 sheep** — consistent at n=2,
   but our own experimentation shows animal count is sensitive to the same
   land/crew upkeep confound that broke the land-alone test.
4. **MELON early-season planting** — both checked episodes plant it in the
   first ~11 days and never later, but the exact cutoff (day 7 vs. day 11)
   varies between them.

## C. UNVERIFIED HYPOTHESES

(Plausible, stated with confidence somewhere in the evidence chain, not
independently confirmed by this audit)

1. **"15–48 sell orders/day"** as a specific numeric range — traceable
   only to ROADMAP.md's 6-episode summary; not independently re-derived
   from either spot-check episode's raw per-day data.
2. **"No day-22 liquidation cliff"** — plausible and consistent with this
   repo's own separate finding that day-19 beats day-25 for our own agent,
   but not independently re-verified against the replay's own raw
   per-day sell data.
3. **CARROT as a reliable day-21-25 late filler** — present in only one of
   two independently-checked episodes; likely real but not yet a rule.
4. **Selling throughput (order count/frequency), not acreage, is the next
   binding constraint** — Track A's own stated conclusion, directly
   measured as a *gap* (273 vs. 501 orders) but not yet tested as a
   *fix* in combination with the land+crew+windows+liquidation bundle.
5. **Land-for-pasture (Track D / Issue #23) reverses Track A's failure** —
   a coherent, evidence-motivated hypothesis, entirely untested as of this
   audit.
6. **8-9 animals is independently valuable** rather than merely a
   consequence of having 75 tiles / a bigger crew to support them.

## D. EXECUTABLE CONSTRAINTS WE CAN SAFELY IMPLEMENT

(Low-risk, well-evidenced, or already validated by this repo's own
harnesses — safe to act on without further replay data)

1. **Continue not planting TOMATO.** Already true; no action needed, but
   safe to assert as a permanent constraint rather than an emergent
   accident of current thresholds — 8/8 replay agreement plus this repo's
   own earlier TOMATO/STRAWBERRY investigation independently concluded the
   same thing.
2. **Update `CLAUDE.md`'s stale `BUY_LAND` dead-end entry** to reflect
   `da8cdea` and `1d5be21`'s more recent, more specific conclusions. This
   is documentation, not strategy code, and closes a real gap between what
   the team's source-of-truth doc says and what's actually been measured
   most recently.
3. **The land-purchase timing window (day 6-7, then ~11) and the two-
   quadrant target (→75 tiles)**, *if and when* land is revisited — not
   because it's safe to ship now (it isn't, per Track A), but because
   *when this is retried* (Track D, or a throughput-augmented retry of
   Track A), the timing parameters themselves don't need re-deriving —
   they're the best-evidenced numbers in this entire audit.

## E. THINGS WE SHOULD NOT IMPLEMENT YET

1. **`BUY_LAND` for crops, in anything like its currently-tested form.**
   Directly measured NOT shippable (Issue #19/Track A, closed): worst
   head-to-head match −17,301, self-play variance 2.6×, floor down 9,000.
2. **Scaling `MAX_ANIMALS` toward 8–9.** Our own sweep already found
   "3 sheep + 3 cow" a heavy loss on the current farm — this is coupled to
   land/crew capacity exactly like Track A's failure, not an independent
   win waiting to happen.
3. **Hardcoding "15–48 sell orders/day" or a specific CARROT day-21-25
   rule** as literal targets — neither is independently verified strongly
   enough yet (see C1, C3).
4. **A single global day-gated phase machine for liquidation** — ROADMAP.md
   itself argues against this explicitly ("no day-22 cliff... per-crop
   timing windows layered on top of one early infrastructure window, not
   one global phase variable").

## F. MISSING DATA

1. **Raw per-day sell-order counts** from the 2 spot-check replay episodes
   — `replay_shape.py` currently only reports season totals and a single
   "first sell-heavy day" figure, not a full per-day series. This is the
   cheapest possible next step to firm up claim C1/C2 and is pure
   analysis tooling, no strategy risk.
2. **A larger replay sample.** All specific numeric ranges in this audit
   rest on 6 (ROADMAP.md) + 2 (REPLAY_ANALYSIS.md) episodes total — enough
   to establish direction confidently, not enough to treat any single
   number as a tight target.
3. **Whether Track A's bundle, retried with a throughput fix layered on
   top** (more sell orders/day, not just bigger per-order quantities —
   note this is a *different* lever than the pricing-cadence work on the
   separate `experiment/pricing-cadence-v1` branch, which increases
   *volume per order*, not order *frequency*), closes the gap. Untested.
4. **Whether Track D's land-for-pasture hypothesis holds up** — stated,
   motivated, not yet run.
5. **Opponent shed contents** — as with the pricing work, replay analysis
   can only see what opponents *plant/buy/sell*, never their held shed
   inventory; all "production" figures are a lower bound.

## G. RECOMMENDED NEXT EXPERIMENT

**Not** another land/crew retry in isolation — that's already been tried
and the mechanism (market flooding without matching sell throughput) is
identified, just not fixed. Two candidates, in order of cost:

1. **Cheapest, do first**: extend `experiments/replay_shape.py` to emit a
   full per-day sell-order-count series (not just season totals + first
   sell-heavy day) for the 2 episodes already available, to convert claim
   C1 ("15-48/day") and C2 ("no day-22 cliff") from *unverified hypothesis*
   to *directly checked fact or correction*. Pure analysis tooling, zero
   strategy risk, answers Issue #21's own question 3 (timing) with actual
   numbers instead of a restated range.
2. **Directly answers the open mechanism question**: re-run Track A's
   exact bundle (`1d5be21`, land + derived crew + crop windows +
   liquidation timing) with the throughput lever added — i.e., either
   raise `maxMarketOrdersPerTurn`-bounded order *frequency* (up to the
   engine's 10-orders-per-turn cap, currently likely under-used) or bundle
   in the pricing-cadence work's cap-boost finding from the parallel
   `experiment/pricing-cadence-v1` branch, which independently found that
   raising per-order sell *quantity* alone captures more value than a
   sophisticated forecast. These are two different, complementary
   throughput levers (frequency vs. quantity) that Track A never tested
   because it wasn't the hypothesis in scope at the time. This is the
   single most evidence-motivated next step in the whole roadmap — it's
   the *specific, identified* remaining gap between our bundle and the
   replay shape, not a guess.
