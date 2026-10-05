# Concepts: Constants, Causal Links, Synergies

## What this is and how to use it

A structured, living reference for the game's mechanics — constants,
causal links, and resource synergies — separate from `CLAUDE.md`'s
narrative lesson log. **`CLAUDE.md` is the reasoning trail** (what was
tried, why, what the measurement showed). **This file is the lookup table**
extracted from it: the facts a new heuristic should be checked against
*before* it ships, not after it's measured false.

Every entry below cites how it was verified, following the same
"engine is the source of truth" priority order `CLAUDE.md` already
establishes: the installed `kaggle_environments` source first, then
instrumented tracing/replay observation, then the compiled competition
docs. Update this file the moment a new mechanic is discovered — that's
the entire point of keeping it. A discovery that cost hours of tracing or
a losing submission should never have to be paid for twice.

---

## 1. Constants (game mechanics)

| Category | Constant | Value | Verified via |
|---|---|---|---|
| Season | Total turns / days / turns per day | 720 / 30 / 24 | engine config |
| Board | Initial unlocked tiles | 25 (one quadrant) | engine |
| Board | Land expansion costs | $1k / $2k / $4k for the remaining quadrants | engine |
| Board | Shed capacity | 100 non-seed items; overflow silently discarded | engine, `CLAUDE.md` |
| Board | Shed-adjacent tiles | `(4,4)`, `(5,4)`, `(4,5)`, `(5,5)` | engine |
| Labor | Hire cost | `farmHandCostMult × fib(n)`, `n` resets to 0 every morning | engine, `CLAUDE.md` |
| Labor | Crew-sizing heuristic | `WORK_TILES_PER_HAND = 4` (measured optimal vs. 6) | `paired_compare.py`, `head_to_head.py` — +1,910, 16/16 |
| Market | Price floor | $1 | engine |
| Market | Starting inventory | 10,000 units, all products | engine |
| Market | Buyable-back products | Only `WHEAT` and `FERTILIZER` | engine |
| Market | Max orders/turn | 10 | engine config |
| Market decay shape | `MELON` | quadratic — 158 units to floor, $26,236 extractable, $166/unit | engine `MARKET_PARAMS`, `CLAUDE.md` |
| Market decay shape | `STRAWBERRY` | linear — 62 units to floor, $3,690 extractable, $60/unit | engine `MARKET_PARAMS`, `CLAUDE.md` |
| Market decay shape | `TOMATO` | sqrt — 529 units to floor, $11,069 extractable | engine `MARKET_PARAMS`, `CLAUDE.md` |
| Market decay shape | `CARROT` | sqrt — 842 units to floor, $10,646 extractable | engine `MARKET_PARAMS`, `CLAUDE.md` |
| Market decay shape | `WHEAT` / `EGG` | log — 2000+ units to floor, absorbs oversupply gradually | engine `MARKET_PARAMS`, `CLAUDE.md` |
| Crop lifecycle | One-shot crops (`WHEAT`, `CARROT`, `MELON`) | Tile frees on `HARVEST` | engine `kaggriculture.py:467-468` |
| Crop lifecycle | Ongoing crops (`TOMATO`, `STRAWBERRY`) | `HARVEST` does **not** clear the tile; it keeps producing at `interval`-spaced ticks past `max_yield_day`, then decays to `WEED` (needs `DIG`) after the last tick | instrumented trace + real episode replay, `CLAUDE.md` |
| Crop lifecycle | Real tile-occupancy, ongoing crops | `TOMATO` ≈ 12 days (not the formula's `max_yield_day=8`); `STRAWBERRY` ≈ 17 days (not `10`) | instrumented trace vs. `_daily_refresh_plants`/`_decay_plants`, `CLAUDE.md` |
| Planting mechanic | Oversubscribed seed demand | If a turn's total `PLANT` demand for a crop exceeds held seed stock, the engine drops **all** of that turn's requests for the crop, not just the excess | engine `kaggriculture.py:920-931`, `CLAUDE.md` |
| Animal mechanic | `CARE` bank | Accrues +1 only on days the animal was **both** fed and cared for; pays out **in full** on the animal's next production day only if also fed that day; resets to 0 on any day it doesn't pay out | engine, instrumented trace, `CLAUDE.md` |
| Animal mechanic | Escape / death thresholds | 2 consecutive unfed days → animal escapes, unrecoverable. 2 consecutive unwatered days → plant becomes a `WEED` (a fresh planting starts at `consecutive_unwatered=1`, so one missed day already kills it) | engine, `CLAUDE.md` |
| Animal economics | Modelled net/season by species | `GOOSE`: 26 events × 2 units = 52 units, $2,023 net. `COW`: 11 × 3 = 33 units, $3,704 net. `SHEEP`: 8 × 4 = 32 units, **$5,236 net** — calibrated against 52 measured egg units | `CLAUDE.md` — model predicted 52, measured 52 |
| Fertilizer | Yield bonus | 2× yield for 3 days, only on days the plant is also watered (multiplier on the watering baseline, not a substitute) | engine, `CLAUDE.md` |
| Fertilizer | Market shape | Linear both ways, target 0.40 → `price = 100 - 0.2 × excess`; every unit traded moves price $0.20 against the trader | engine `MARKET_PARAMS`, `CLAUDE.md` |
| Town demand | Town Center | 1 unit of each product consumed per day (baseline floor, post mid-season balance patch) | engine, `docs/kaggriculture_context.md` |
| Town demand | Shops | Fire every 4 steps vs. Town Center's 24; a single-product shop consumes at 2× rate; shops unlock with replacement | engine `SHOPS` |
| Town demand | MELON specifically | In **no shop** at all — its only sink is the Town Center's ~1/day (~30/season) | engine `SHOPS`, `CLAUDE.md` — this was the single largest measured fix, +3,358 |

---

## 2. Causal links (domain knowledge)

**Resource conversion chains**
```
Money → Seed → Planted Tile → (Time + Water) → Yield → Money
Money → Animal → Structure → (Time + Wheat) → Product → Money
Money → Land → Tiles → Capacity → Yield → Money   [only positive if Hands scale with it — see §3]
Money → Hands → Actions → Throughput → Yield → Money
```

**Failure modes (irreversible losses)**
```
Unwatered ×2 days → Weed → lost seed + lost tile time until DIG'd
Unfed ×2 days → Animal escapes → unrecoverable, lost structure investment
Shed overflow (>100 non-seed items) → silently discarded, no buffer
Late planting → crop can't mature before day 29 → lost seed + opportunity cost
Ongoing-crop tile left growing past its last tick, never DIG'd → tile stays dead the rest of the season
```

**Market dynamics**
```
Player sells → own inventory-side price term rises → price falls for that player
Town/shops consume → inventory falls → price recovers over time (a market recovers
    between sales — this is why spreading sells over time beats dumping, not a fixed quota)
Premium goods (base price > $100: strawberry, melon, milk, wool) crash toward the
    $1 floor fast on oversupply; staples (wheat, carrot, egg) absorb it gradually
In a thin market, your own order IS the price move — verified directly: a 573-unit
    fertilizer buy-the-dip/sell-the-recovery strategy bought at 97.8 and sold at
    97.0, moving the price against itself both directions (-1,486, 0/16 matches)
```

**Temporal / lifecycle constraints**
```
Melon planted after day ~18 → cannot mature → forbidden by the season-maturity gate
Strawberry planted after day ~12 → can't get all its yields → low ROI
Ongoing crops (tomato, strawberry) should be planted once per tile in an early-to-mid
    window and left alone — replanting them like a one-shot crop wastes the fact that
    one planting keeps paying out (see the replay-observed target shape, §4)
```

**Synergies & anti-synergies**
```
Animals + self-grown wheat feed source        → positive
Animals + no wheat source (buying feed)       → negative in isolation, but see §4:
                                                  top-ladder play buys wheat back
                                                  heavily as a standing supply line
                                                  once the animal count justifies it
Land expansion + crew that does NOT scale up  → negative (measured: BUY_LAND is a
                                                  loss against a fixed crew)
Land expansion + crew that DOES scale up      → unresolved locally, but this is the
                                                  universal pattern in every top-ladder
                                                  episode sampled — see §4 and
                                                  docs/ROADMAP.md Phase 2/3
Fertilizer + one-shot crops                   → strong positive (doubles bonus-window yield)
Fertilizer + ongoing crops                    → moderate positive (doubles scheduled yield)
Multiple animal structures + undersized crew  → heavy loss (measured: -16,634, 0/16
                                                  for sheep+cow); every structure costs
                                                  a tile and a share of upkeep capacity
                                                  that a small crew can't spare
Multiple animal structures + top-ladder-scale
    crew (10-14 hands)                        → the universal pattern on the real
                                                  ladder — every sample runs 2+ species;
                                                  this is the confound §Land above
                                                  shares, and the next thing to
                                                  re-test once crew size is derived
                                                  rather than fixed (ROADMAP Phase 3)
```

---

## 3. Evaluation discipline (process, not mechanics — kept here because it's just as load-bearing)

- **Paired comparison, not across-seed stdev.** The across-seed spread
  (~±2,000) mostly measures how much *seasons* differ from each other, not
  how much a change matters — both arms of a paired test see the same
  seeds, so that variance cancels. Two real, large wins (daily feeding,
  `WORK_TILES_PER_HAND`) were mislabeled "a wash" by testing against the
  wrong baseline.
- **Read the win count before the t-value.** Better on 12 of 12 seeds needs
  no statistics; better on 7 of 12 isn't rescued by a good t-value.
- **Only pair against `pass`/`starter`.** `random`'s own RNG isn't
  seed-controlled — the same seed doesn't reproduce its episode, so pairing
  against it is invalid.
- **Bundle coupled changes into one test.** If two resources only pay off
  jointly (land and crew size, crew size and multi-animal), testing them as
  independent on/off toggles will produce false-negative "dead ends" for
  both — see the Land/Animal anti-synergy entries above.
- **Self-play deflates optimistic numbers, and that's the point.** Built-in
  opponents (`pass`, `random`, `starter`) never sell, so the market stays
  pristine and our own sales never compete with a rival's — `selfplay_bench.py`
  is what predicts the ladder, not the built-in batch.

---

## 4. Empirically-observed target shape (replay-derived, 2026-08-17)

Pulled from six real top-ladder episodes via the host-maintained
[`kaggriculture-episodes-index`](https://www.kaggle.com/datasets/kaggle/kaggriculture-episodes-index)
dataset (episodes spanning Aug 1–16, 2026). See `docs/ROADMAP.md` §1-2
for the full table and sourcing detail. Headline facts, each independently
confirmed across all 6 episodes:

- Final money: $71,757 – $126,015 (our local ceiling: $31,132 self-play, ~$42k
  vs. built-ins)
- `BUY_LAND` exactly twice, always in the day 6–11 window, never again after
- Crew scales to 10-14 hands by day ~8, sustained through ~day 27
- Two-plus animal species always (COW + SHEEP, sometimes + GOOSE)
- MELON planted only days 0-7, then never again for the rest of the season
- STRAWBERRY planted only days 5-12 — once per tile, matching the ongoing-crop
  lifecycle fact in §1
- CARROT planted only days 21-25 — a late-game short-cycle filler
- TOMATO planted in **zero** of the 6 episodes — independently validates the
  closed TOMATO/STRAWBERRY investigation's conclusion in `CLAUDE.md`
- Selling ramps hard from day ~10 (15-48 orders/day) and stays high through
  day 29 — there is no observed day-22 "liquidation" discontinuity

**Independently corroborated, 2026-08-17 (`da8cdea` on `origin/main`,
`docs/REPLAY_ANALYSIS.md`):** two more contested-market episodes, sampled
independently of the six above (different dates — Aug 8 and Aug 16 — and
different teams), run the identical strategy down to the land-purchase
days (`BUY_LAND` days 6-7 and 11; COW x5-6 + SHEEP x3; crew held at 12-15
from day ~10). Four teams, two dates, one strategy — this is one dominant
shared approach (almost certainly a widely forked public notebook), not
independent convergence, which strengthens rather than weakens the case
for treating this shape as a real target: it's what a strong, reproducible
strategy looks like, not an artifact of one lucky sample.

This section should be refreshed whenever new replay evidence is pulled —
note the pull date next to any update so staleness is visible.
