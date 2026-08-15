# Kaggriculture — Competition Context Doc

*Compiled Aug 15, 2026 from the competition Overview, Rules, and README pages on Kaggle.*

---

## 1. Competition Snapshot

| | |
|---|---|
| **Title** | Kaggriculture |
| **Host / Sponsor** | Kaggle (competition sponsored by Google LLC) |
| **Type** | Featured Simulation Competition (agent-vs-agent, not a static test set) |
| **Task** | Build an autonomous agent that manages a virtual farm and competes head-to-head against other agents |
| **Total Prizes** | $50,000 — 10 places × $5,000 each (1st through 10th, each ranked, no ties for prize purposes) |
| **Entrants so far** | ~12,700 entrants / ~4,600 teams / ~8,600 submissions (as of research date) |
| **Winner license** | CC-BY 4.0 (open) |
| **Data license** | Apache 2.0 |
| **Leaderboard type** | No private leaderboard — this is a simulation comp, ranking comes from live episodes and a final Bradley-Terry tournament |

### Timeline

| Date (11:59 PM UTC) | Milestone |
|---|---|
| **July 29, 2026** | Competition start |
| **Sept 23, 2026** | Entry deadline (must accept rules by this date) |
| **Sept 23, 2026** | Team merger deadline |
| **Sept 30, 2026** | Final submission deadline |
| **Oct 1 – ~Oct 15, 2026** | "Cooldown" — games keep running until leaderboard converges; then it's final |

You (Billy) have already accepted the competition rules, so you're entered as of this writing (Aug 15, 2026) — that gives roughly 5.5 weeks until the entry/merge deadline and 6.5 weeks until final submission.

### Matchmaking & Rating (Bradley-Terry)

- Each submission gets a **skill rating**; matchmaking pairs you with similarly-rated opponents.
- Only your **latest 2 submissions** are tracked/matched and count toward final evaluation — older submissions stop playing.
- Rating only cares about **win / loss / tie** — margin of victory (coin difference) does **not** affect rating at all. A 1-coin win counts the same as a landslide.
- Rating deltas scale with the **rating gap** between opponents: beating a higher-rated opponent (an upset) moves your rating more than beating a similarly- or lower-rated one.
- Every upload runs a **validation episode** (agent vs. a copy of itself) before it enters the matchmaking pool; failures are marked `Error` with downloadable logs.
- **Oct 1 – ~Oct 15, 2026:** games keep running post-deadline "until the leaderboard has reached convergence," then a single final Bradley-Terry tournament on those episodes sets the final leaderboard — explicitly to average out "hot streaks" rather than let a lucky late run decide placement.
- **Caveat (unresolved as of Aug 2026):** multiple competitors report large, persistent rating gaps (1000+ points) between byte-identical agents, attributed to early-game RNG (e.g. one side getting an early weed) compounding through the rating-gap-scaled update rule. No host fix or explanation beyond "update to the latest env version" as of this writing. Practical implication: don't read early rating swings as a signal your strategy is bad, and consider resubmitting periodically rather than trusting one submission's rating trajectory.

---

## 2. Rules Summary (the parts that actually matter day-to-day)

- **Team size:** max 5 people. Mergers allowed via the Team leader before the merge deadline, as long as combined submission count stays under the allowed cap.
- **Submission limits:** max 5 submissions/day; only your **latest 2** submissions stay "active" (played in matchmaking) and are what's used for final leaderboard evaluation. You can select up to 2 Final Submissions for judging.
- **Submission format:** a `main.py` at the root exposing an agent function, OR a `tar.gz` bundling multiple files with `main.py` at the root. Max size **100 MiB**.
- **Compute given to your agent per episode:** 8 GiB HDD, 6.5 GiB RAM, 1.6 vCPUs.
- **No ingress/egress:** during an episode your agent cannot call out to the internet or leak information externally — it only gets what's in `obs`.
- **External data/tools:** allowed if "reasonably accessible to all" participants at minimal/no cost. No excessively expensive proprietary data or licenses.
- **Code sharing:** private sharing of competition code outside your team is **not allowed** (that's a violation). Public sharing is fine, but only via the competition's Kaggle forum/notebooks, and it's automatically open-licensed if you do.
- **Eligibility:** 18+ (or age of majority), registered Kaggle account, one account per person, standard export-control/sanctioned-country exclusions apply.
- **Winner obligations:** if you place, you must publish a detailed methodology writeup (architecture, approach, how to reproduce) and license your winning submission's code under CC-BY 4.0 (or equivalent open license) — this applies to all 10 prize places, not just 1st.
- **Ties:** earliest submission wins the tiebreak (not really relevant here since Hackathon-style final ranking gives everyone a unique rank).

---

## 3. Game Mechanics — Full Reference

### 3.1 Premise

Two players, each with their own farm, compete over a **30-day season = 720 turns** (24 turns/day). Each turn: one action for your farmer (and any hired hands) + up to 10 market order actions. Winner = most money in the bank at turn 720. Ties are possible.

### 3.2 Object Types (crops & animals)

| Type | Yield Type | Seed/Purchase Cost | Base Market Price | Time to First Yield | Time to Max Yield | Subsequent Yields | Max Yield | Action Cost | Yield/tile/day |
|---|---|---|---|---|---|---|---|---|---|
| Wheat | One-time | 10 | 25 | 2 days | 4 days | none | 6 (4 unfertilized) | 1 | 0.80 |
| Carrot | One-time | 20 | 35 | 2 days | 3 days | none | 4 (3 unfertilized) | 1 | 0.75 |
| Tomato | Ongoing | 50 | 60 | 8 days | 11 days | every day ×4 | 4 | 1 | 0.33 |
| Strawberry | Ongoing | 100 | 120 | 10 days | 16 days | every other day ×4 | 4 | 1 | 0.24 |
| Melon | One-time | 80 | 250 | 10 days | 10 days | none | 6 | 1 | 0.55 |
| Goose/Egg | Ongoing | 300 | 50 | 4 days | NA | every day, indefinitely | 4 held | 1 (+1 to build coop) | 1.00 |
| Cow/Milk | Ongoing | 400 | 160 | 8 days | NA | every 2 days, indefinitely | 6 held | 1 (+1 to build pasture) | 0.50 |
| Sheep/Wool | Ongoing | 500 | 200 | 6 days | NA | every 3 days, indefinitely | 6 held | 1 (+1 to build pasture) | 0.33 |
| Fertilizer | — | 100 | — | — | — | — | — | 1 | — |

**Important nuances:**
- "Yield/tile/day" = total units harvested ÷ days occupied, assuming daily watering and harvest at peak. For animals it's the steady-state rate (1/interval).
- "Max Yield" for animals = `max_held`, the cap on **unharvested** product sitting on the tile — not a lifetime total.
- Melon's bonus window is ages 6–12, but base 1 + 1/watered day hits the cap of 6 at age 10 (fertilized: cap at age 8) — so days 11–12 add nothing unfertilized.
- Wheat/Carrot only reach their *listed* max (6 / 4) **with fertilizer**; watering alone caps at 4 / 3.
- Tomato & Strawberry are "ongoing" but capped at 4 scheduled yields (tomato: ages 8–11; strawberry: ages 10,12,14,16), after which the plant decays into a weed.

### 3.3 Watering / Feeding Rules

- All plants need watering **daily**; animals need feeding **daily** (feed = wheat).
- Miss **2 consecutive days**: plants → become a WEED (must DIG to reclaim tile); animals → escape (**unrecoverable**).
- A freshly planted seed starts with `consecutive_unwatered = 1` (the planting day itself counts as day 1 missed) — so an unwatered plant on day 0 becomes a weed that same night. **No grace period for new plantings.**
- A freshly placed animal starts `consecutive_unfed = 0` — it *does* survive its first day unfed.
- Watering **one-time** crops during their bonus window increases yield. This does **not** apply to ongoing crops/animals (see harvest yields below).

### 3.4 Harvest Yields

- **One-time crops** (wheat, carrot, melon): starting at `ceil(max_yield_day / 2)`, each watered day in the bonus window adds **+1** unit to total harvestable yield; **fertilized** days add **+2** instead.
- **Ongoing crops** (tomato, strawberry): base yield is 1 per scheduled production tick. If fertilized **and** watered that same day, yield doubles to 2.
- Once a plant hits max lifespan, remaining yield decays by 1 every other turn until it hits 0 → becomes a weed.
  - One-time crops: max lifespan = 1 day after `max_yield_day`.
  - Ongoing crops: decay starts 1 day after cumulative production count hits `max_yield` (regardless of whether you've harvested it yet).

### 3.5 Fertilizer

- `FERTILIZE` action doubles the per-day yield bonus for the **next 3 days**, but only applies on days the plant is also watered (watering is the baseline requirement — fertilizer is a multiplier on top).
- Fertilizer is purchased (100/unit) or collected from animals via `COLLECT_FERTILIZER` (1 unit/day per surviving animal, doesn't stack if uncollected).

### 3.6 Animal Care

- `CARE` (once/day, no-op if already done today) banks a bonus:
  - End of day: if animal was **both** fed AND cared for → `pending_care_bonus += 1`. Unfed days don't bank anything (feeding is the baseline requirement).
  - On the animal's **next scheduled production day**: if fed, the *entire* banked bonus is added to that yield (on top of the base 1) and the bank resets to 0. If unfed on the production day, base 1 still produced but bonus is lost (bank resets to 0 anyway).
  - Effectively capped by the animal's `max_held` yield cap.

### 3.7 Actions

**Farmer / Farm Hand actions** (one per unit per turn; multiple units *can* occupy the same tile):

- **Movement:** `NORTH / SOUTH / EAST / WEST` — moves off-board are no-ops. Locked tiles are *passable* (you can walk across/onto them) but tile actions (PLANT, WATER, BUILD_*, etc.) no-op there. Exception: shed actions (PICKUP/DROP/PLACE-into-shed) work from any shed-adjacent tile even if that tile is locked.
- **Shed:**
  - `PICKUP <item> [n]` — move up to n of an item from shed → active unit's inventory (default 1). Seeds are a separate slot and never picked up this way — `PLANT` consumes seeds directly.
  - `DROP` — dump entire inventory into shed (must be orthogonally adjacent); overflow past `shedCapacity` is discarded.
- **Plants:** `PLANT`, `WATER` (no-op if already watered today), `HARVEST`, `FERTILIZE` (see 3.5).
  - If you try to plant more seeds of a kind in one turn than you have, **none** get planted.
- **Animals:** `PLACE <item> [n]` (drop inventory onto a matching structure — GOOSE→coop, SHEEP/COW→pasture — or into the shed if standing shed-adjacent), `FEED`, `HARVEST`, `COLLECT_FERTILIZER`, `CARE`.
- **Terrain:** `BUILD_COOP`, `BUILD_PASTURE` (on an unoccupied tile), `DIG` (remove a plant/weed/empty coop-pasture; no-op if an animal occupies the structure).
- **Other:** `PASS` (default no-op).

**Market actions** (up to `maxMarketOrdersPerTurn` = 10/turn, ordered list, extras silently dropped):

- `BUY_SEED <CROP> <n>`
- `BUY_ANIMAL <ANIMAL> <n>`
- `BUY_PRODUCT <WHEAT|FERTILIZER> <n>` — **only these two** products can be bought back from the market.
- `SELL <ITEM> <n>` — any product (including collected fertilizer) can be sold, unrestricted.
- `HIRE` — hire a farm hand for the day. Cost = `farmHandCostMult × fib(n)` where n = hires already made *today* (fib: 1,1,2,3,5,8,13,21,… resets each day). Hands spawn shed-adjacent (NWSE preference order, or least-occupied tile) and disappear at end of day (drop inventory to shed first) — **must be re-hired daily**.
- `BUY_LAND` — unlock a neighboring 5×5 quadrant. Cost escalates: $1k → $2k → $4k.

### 3.8 Map / Farm

- Farm = `boardSize × boardSize` grid (default **10×10**), split into four 5×5 quadrants. You start owning just NW (25% of squares); buy the rest via `BUY_LAND`.
- Weeds can spontaneously spawn on empty unlocked tiles (`weedSpawnChance`, default 0.005/tile/day).
- **Shed** sits at board center, is *not* a tile (never appears in the `tiles` array). "Shed-adjacent" = one of the 4 center tiles: `(half-1,half-1), (half,half-1), (half-1,half), (half,half)` where `half = boardSize//2` — at default size that's `(4,4), (5,4), (4,5), (5,5)`, one per quadrant. Only NW's shed-adjacent tile starts unlocked; the shed itself is always reachable regardless of quadrant lock state.
- **Shed capacity:** 100 non-seed items. Overflow at any point (PLACE mid-day, end-of-day auto-drop) is simply discarded — no overflow buffer.
- You can see your opponent's **farm** state but not their **shed** contents.

### 3.9 Town Buildings (demand side of the economy)

- New shop unlocks every `townShopUnlockInterval` days (default 3), drawn **uniformly at random with replacement** from the shop table — duplicates possible, stops after 8 total instances unlocked.
- Each unlocked shop instance consumes 1 of every product it demands every `townShopSellInterval` turns (default 4 turns = once/day-equivalent per shop... actually 4 turns out of 24, so 6×/day). Single-product shops consume 2× that product.
- **Town center** additionally consumes 1 of every product (excluding fertilizer) every `townCenterSellInterval` turns (default 24 = once/day), flat for the whole season.

| Shop Type | Demands |
|---|---|
| Bakery | eggs, wheat |
| Pizza Shop | milk, tomatoes, wheat |
| Brunch Spot | eggs, wheat, strawberries |
| Yarn Store | wool (2×, single-product) |
| Ice Cream Shop | strawberries, milk, wheat |
| Pet Cafe | carrots (2×, single-product) |
| Smoothie Shop | strawberries, milk |
| Farmers Market | wheat, carrots, tomatoes, strawberries |

- **Demand-spike pricing** (patch requires `kaggle-environments >= 1.32.7`): tomato, carrot, and egg prices spike significantly above their normal §3.10 curve when shop demand for them is high but there's no production feeding the market — unmet demand pushes price up beyond the standard scarcity formula. Host-quantified at a zero-production baseline: triggers in ~50% of games for tomato, ~26% for carrot, ~22% for egg. Host has stated this "should be the last [balance] change, excepting game-breaking bugs."

### 3.10 Market Pricing Mechanics

- Every resource starts with market inventory `I0 = 10,000` units (deliberately far above realistic production, so it basically never runs dry).
- Sell price is quoted at **pre-sell** inventory; buy price is quoted at **post-buy** inventory → an immediate buy then sell of the same item nets exactly $0 if nothing else changed.
- Sell/buy orders across both players are processed **one unit at a time, concurrently**, so simultaneous large orders from both players shift price against each other as they go.
- Price floor is $1 — units still transact at the floor but no longer add to market inventory (keeps the floor "responsive").
- Only **WHEAT** and **FERTILIZER** can be bought back (`BUY_PRODUCT`); everything else is sell-only to the market.

**Price formula:**

```
price(inv) = base + sign · amp · f(|inv − I0|)
sign = +1 if inv < I0 (scarce → price up), −1 if inv > I0 (glut → price down)
amp = target · base / f(T)          # derived, not stored
f ∈ {linear, sq, sqrt, log (ln(1+x)), log10, hinge}
```

`hinge(u) = u + 8·max(0, u−1)²` where `u = x/T` — linear below T, steep quadratic above T.

`T` = production capacity of one 5×5 field over a 24-day calibration window at optimal watering, no fertilizer (animal totals pre-discounted 30% for feed overhead + 1 day setup). Price is floored at $1 and rounded to nearest dollar.

| Resource | Base | I0 | T | Below func | Below target | Above func | Above target | P(I0−T) | P(I0+T) | P(I0+2T) |
|---|---|---|---|---|---|---|---|---|---|---|
| Wheat | 25 | 10,000 | 400 | sqrt | 0.80 | log | 0.20 | $45 | $20 | $19 |
| Carrot | 35 | 10,000 | 450 | hinge | 1.00 | sqrt | 0.70 | $70 | $10 | $1 |
| Tomato | 60 | 10,000 | 200 | hinge | 0.40 | sqrt | 0.60 | $84 | $24 | $9 |
| Strawberry | 120 | 10,000 | 100 | sqrt | 0.70 | linear | 1.60 | $204 | $1 | $1 |
| Melon | 250 | 10,000 | 300 | log | 0.20 | sq | 3.60 | $300 | $1 | $1 |
| Egg | 50 | 10,000 | 332 | hinge | 0.40 | log | 0.20 | $70 | $40 | $39 |
| Milk | 160 | 10,000 | 122 | sqrt | 0.60 | linear | 1.60 | $256 | $1 | $1 |
| Wool | 200 | 10,000 | 105 | log | 0.20 | sq | 3.20 | $240 | $1 | $1 |
| Fertilizer | 100 | 10,000 | 200 | linear | 0.40 | linear | 0.40 | $140 | $60 | $20 |

**Strategic read:** wheat panics on scarcity but absorbs gluts well (safe staple). Carrot/tomato/egg use `hinge` on the scarcity side — stable near base under normal demand, spike hard only once you overbuy past T. Premium goods (base > $100: strawberry, melon, milk, wool) crash to the $1 floor fast on even modest oversupply — **timing and bundling sales matters a lot more for these**; don't dump large batches at once.

`MARKET_PARAMS` in `kaggriculture.py` holds these defaults; per-resource overrides can be passed via `env.configuration["marketParams"]` at episode creation without touching code.

### 3.11 Turn Processing Order (per turn)

1. Action validation
2. Player actions recorded (simultaneous)
3. Market actions processed (queued, in order, per player)
4. Town buy actions (shops/town center reduce inventory)
5. Observations updated
6. **Day refresh** (if applicable): plant/animal condition updates, fed/watered flags reset to false
7. **Market refresh**: prices updated based on prior turn's sells
8. **Income update**: bank balances updated from buys/sells
9. **Farm update**: harvested plants cleared, inventory items consumed/sold, new plants/animals added, etc.

### 3.12 Observation Format

```jsonc
{
  "player": 0 | 1,
  "day": int,          // 0-indexed
  "hour": int,         // 0-indexed turn within day
  "farms": [farm, farm],   // public, both players
  "market": {
    "inventory": {"WHEAT": int, "CARROT": int, ...},
    "prices": {"WHEAT": int, "CARROT": int, ...}
  },
  "town": {
    "unlocked_shops": ["BAKERY", "BAKERY", ...]   // may repeat
  },
  "private": {   // this player only
    "shed": {"WHEAT": int, "GOOSE": int, "FERTILIZER": int, ...},
    "seeds": {"WHEAT": int, "CARROT": int, ...},
    "inventories": [farmer_inv, hand_inv, ...]   // [0] = main farmer
  }
}
```

`farm` dict (public):
```jsonc
{
  "money": float,
  "tiles": [[tile, ...], ...],   // tiles[y][x]
  "farmer": [x, y],
  "hands": [[x, y], ...],
  "unlocked_quadrants": ["NW", ...],   // subset of {"NW","NE","SW","SE"}
  "hires_today": int
}
```

`tile` is one of: `None` (empty unlocked), `"LOCKED"`, a plant dict, a weed dict `{"kind":"WEED"}`, or an animal structure dict:

```jsonc
// plant
{
  "kind": "PLANT", "crop": "WHEAT"|"CARROT"|"TOMATO"|"STRAWBERRY"|"MELON",
  "planted_day": int, "watered_today": bool, "consecutive_unwatered": int,
  "yield_units": int, "max_lifespan_step": int, "fertilized_until_day": int
}

// coop / pasture
{
  "kind": "COOP"|"PASTURE", "animal": "GOOSE"|"COW"|"SHEEP"|None,
  "placed_day": int, "yield_units": int, "fed_today": bool,
  "consecutive_unfed": int, "cared_today": bool,
  "fertilizer_available": bool, "pending_care_bonus": int
}
```

### 3.13 Configurable Parameters (defaults)

| Parameter | Default | Meaning |
|---|---|---|
| `episodeSteps` | 720 | Total turns (24 × 30) |
| `boardSize` | 10 | Farm width/height in tiles |
| `startingMoney` | 3000 | Starting coins |
| `maxMarketOrdersPerTurn` | 10 | Market orders/turn cap |
| `turnsPerDay` | 24 | Turns per in-game day |
| `shedCapacity` | 100 | Max non-seed shed items |
| `weedSpawnChance` | 0.005 | Per-tile weed spawn chance/day |
| `townShopUnlockInterval` | 3 | Days between shop unlocks |
| `townShopSellInterval` | 4 | Turns between shop consumption ticks |
| `townCenterSellInterval` | 24 | Turns between town-center consumption ticks |
| `seed` | null | Optional deterministic episode seed (stripped from agent observations after read) |

---

## 4. Technical Workflow

### 4.1 Local setup

```bash
pip install -U kaggle-environments
pip install kaggle   # CLI
```

Kaggle API token: generate at kaggle.com/settings/api, save to `~/.kaggle/access_token` (or use `kaggle auth login` / `KAGGLE_API_TOKEN` env var).

**Pin the version.** Recent balance patches (town-center demand, shop sampling, tomato/carrot/egg demand-spike pricing — see §3.9) require `kaggle-environments >= 1.32.7`. Check with `pip show kaggle-environments` before trusting local test results against the current live ruleset.

### 4.2 Testing an agent locally

```python
from kaggle_environments import make

env = make("kaggriculture", configuration={"episodeSteps": 720}, debug=True)
env.run([agent, "random"])          # or env.run(["main.py", "random"])

final = env.steps[-1]
for i, s in enumerate(final):
    print(f"Player {i}: reward={s.reward}, status={s.status}")

env.render(mode="ipython", width=1200, height=800)   # notebook viz

import json
with open("replay.json", "w") as f:
    json.dump(env.toJSON(), f)   # replay for the visualizer
```

Built-in opponents to test against: `"pass"`, `"random"`, `"starter"` (deterministic baseline).

### 4.3 CLI workflow

```bash
kaggle competitions list -s "kaggriculture"
kaggle competitions pages kaggriculture --content
kaggle competitions list --group entered           # confirm you've joined
kaggle competitions download kaggriculture -p kaggriculture-data

# Submit (single file)
kaggle competitions submit kaggriculture -f main.py -m "Wheat loop v1"

# Submit (multi-file, tar.gz with main.py at root)
tar -czf submission.tar.gz main.py helper.py model_weights.pkl
kaggle competitions submit kaggriculture -f submission.tar.gz -m "Multi-file agent v1"

# Monitor
kaggle competitions submissions kaggriculture
kaggle competitions episodes <SUBMISSION_ID>
kaggle competitions replay <EPISODE_ID> -p ./replays
kaggle competitions logs <EPISODE_ID> 0 -p ./logs
kaggle competitions leaderboard kaggriculture -s
```

Each upload triggers a **validation episode** (agent vs. a copy of itself) — if it errors, the submission is marked `Error` and you can pull logs to debug.

### 4.4 Reference starter agent (wheat loop)

```python
def agent(obs):
    player = obs["player"]
    me = obs["farms"][player]
    private = obs["private"]
    fx, fy = me["farmer"]
    tile = me["tiles"][fy][fx]

    market = []

    if private["seeds"].get("WHEAT", 0) == 0 and me["money"] >= 10:
        market.append(["BUY_SEED", "WHEAT", 1])

    wheat_in_shed = private["shed"].get("WHEAT", 0)
    if wheat_in_shed > 0:
        market.append(["SELL", "WHEAT", wheat_in_shed])

    if tile is None and private["seeds"].get("WHEAT", 0) > 0:
        return {"farmer": ["PLANT", "WHEAT"], "hands": [], "market": market}

    if isinstance(tile, dict) and tile.get("kind") == "PLANT":
        crop_age = obs["day"] - tile["planted_day"]
        if crop_age >= 2:
            return {"farmer": ["HARVEST"], "hands": [], "market": market}
        if not tile["watered_today"]:
            return {"farmer": ["WATER"], "hands": [], "market": market}

    return {"farmer": ["PASS"], "hands": [], "market": market}
```

This is intentionally minimal (single tile, single farmer, no fertilizer/animals/hands/land) — a working floor to build on top of, not a competitive baseline.

### 4.5 Community & Host Resources

- **[`kaggriculture-episodes-index`](https://www.kaggle.com/datasets/kaggle/kaggriculture-episodes-index)** — host-maintained dataset of daily replay dumps (up to 20 GB/day) from the top-rated episodes each day. Useful for imitation learning, RL bootstrapping, or studying what strong agents are doing without playing hundreds of games yourself.
- The pinned **"Kaggriculture: Getting Started"** notebook on the Code tab is the only host-official code beyond the README/AGENTS.md quick-start — it doesn't add a separate environment wrapper or replay viewer beyond what ships in `kaggle-environments`.
- Community tooling exists (unofficial, unverified) for faster local iteration — a batched CUDA env reimplementation and a Rust port validated against thousands of leaderboard games. Worth searching for if raw local-simulation throughput becomes a bottleneck later.

---

## 5. Open Strategy Questions (worth thinking through before coding)

- **Crop/animal ROI ranking** — money per tile per day varies a lot by resource and by how much you sell into a given market state. Wheat's high yield/tile/day and forgiving price curve make it a safe backbone; melon/strawberry/wool are high-value but punish overselling badly.
- **Selling cadence** — since price is quoted pre-sell and moves per-unit, dumping a large harvest in one `SELL` order tanks your own price mid-order. Spreading sells over time (or across turns) preserves value for premium goods especially.
- **Labor scaling** — hiring cost resets daily and grows fast (Fibonacci) within a day, so there's a real question of how many hands is worth it vs. spreading actions across a smaller number of days.
- **Land expansion timing** — $1k/$2k/$4k for more tiles is a big capital outlay early; when does the marginal tile pay for itself given the 30-day season?
- **Animals vs. crops** — animals need continuous feeding (wheat) but yield indefinitely and don't decay into weeds the way crops eventually do; there's a wheat-production-for-feed subsystem question here (grow your own feed vs. buy it).
- **Fertilizer allocation** — since it doubles bonus-window yield for 3 days (only on watered days), the ROI is highest on high-value, well-tended plants — worth modeling explicitly rather than fertilizing everything.
- **Town demand as a tailwind** — shops unlock randomly over the season and create a floor under demand for whatever they buy; watching `unlocked_shops` in the observation could inform which resource to lean into as the season progresses.
- **Optimize for win probability, not margin** — the Bradley-Terry rating only sees win/loss/tie (see §1 Matchmaking & Rating), so a narrow win is worth exactly as much as a blowout. Once you're safely ahead late in a game, further risk to widen the margin has zero rating upside — the correct move is to protect the win, not maximize final coin count within that episode.
- **Endgame turn-720 uncertainty** — there's an open, unresolved report (as of Aug 2026) that the very last turn of the season may not actually execute in the engine. Until confirmed, don't design a strategy that depends on a specific action landing on turn 720 exactly (e.g. a final liquidation sell) — front-load the endgame cash-out by a turn or two as a hedge.
- **Unverified per-step compute limit** — an unconfirmed competitor report describes a ~1-second-per-step soft time limit with an overage "bank," similar to other Kaggle sim competitions. Not host-confirmed and not in the official docs, but worth profiling your agent's per-step wall time locally, especially before adding anything heavier than simple heuristics (search, ML inference, etc.).

---

*Source: Kaggle competition pages — Overview (`/competitions/kaggriculture/overview`), Rules (`/competitions/kaggriculture/rules`), and the community "Kaggriculture: Getting Started" notebook README, all retrieved Aug 15, 2026.*

*Follow-up pass (same day): Discussion tab review covering host balance-change threads ([735311](https://www.kaggle.com/competitions/kaggriculture/discussion/735311), [733431](https://www.kaggle.com/competitions/kaggriculture/discussion/733431), [731587](https://www.kaggle.com/competitions/kaggriculture/discussion/731587)), the doc-vs-engine discrepancy thread ([732450](https://www.kaggle.com/competitions/kaggriculture/discussion/732450)), the rules Q&A thread ([731953](https://www.kaggle.com/competitions/kaggriculture/discussion/731953)), and open rating-path-dependency reports ([734000](https://www.kaggle.com/competitions/kaggriculture/discussion/734000), [734074](https://www.kaggle.com/competitions/kaggriculture/discussion/734074)).*
