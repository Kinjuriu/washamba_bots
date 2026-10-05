# Behavioural policy inference: what decision rules generated the top teams' play?
Fable 5.1, 26 September 2026. Data: exact replays of the 23-24 September corpora (top-six seats n=407, ranks 7-12 seats n=402, W3 ladder seats n=84). Scripts: `policy_probe.py`, `aggregate_probe.py`, `sell_rule_probe.py`, `harvest_lag.py`. Raw output: `probe_report.txt`. Everything here is MEASURED unless marked inference. Different algorithms can produce the same behaviour, so each section states the smallest mechanism consistent with the evidence and which families the evidence rules out.

## 1. Method
Seven probes per seat, read from the replay observations (both players' private state is in the replay):
1. Labour-action agreement across a team's own games, by window (0-71, 72-143, 144-400, 400-718), split by whether the two games share the first shop. A tape scores about 1.0; a shop-keyed router scores high on same-shop pairs and low on different-shop pairs; a state-reactive controller scores near 0 in both.
2. Land purchase timing: step and cash just before. Zero dispersion in step means a schedule; dispersion in step with a tight cash band means a cash trigger.
3. Herd at day 12 conditioned on shops unlocked by day 9.
4. Sale events for wool, milk, strawberry: units per event, fraction of shed stock sold, hour mod 4, price/base before and after, gap between events, lot size by stock level, lot size by price level.
5. Shed-to-sale lag (FIFO), and whether sales sit within 2 steps of the opponent's sale of the same product (after, before, same step).
6. Stranded value at days 6/12/18/24/29: cash vs value in shed, hands and on tiles; terminal unsold.
7. Lag from a visible harvest on the opponent's public tiles to that opponent's sale.

## 2. Findings that hold for the whole top twelve

**Openings are scripted, the rest is not.** Agreement 0-71 ranges 0.11 (Boey) to 0.91 (THIRD FARM CLUB); from step 144 it is 0.01-0.11 for every team, and same-first-shop pairs agree no more than different-shop pairs (e.g. DSM 0.10 vs 0.07, DECEM 0.05 vs 0.05). W3 for contrast: 1.00 / 1.00 / 0.78 (same shop) vs 0.61 / 0.41. Rules out: pure tapes and shop-keyed tape routers for anything after about step 150. THIRD FARM CLUB is the one hybrid: fixed opening (0.91), a shop-keyed segment 72-143 (0.39 same-shop vs 0.09 different), reactive after.

**Land is bought on a clock, not on cash.** DSM family (DSM, Unknown Mother-Goose, DECEM, mtmr_s1, Arda Ceylan, TheEggman): purchase 1 at step 150 (quartiles 150-150) with cash 1,900-2,100; purchase 2 at step 220 (220-222) with cash 2,000-2,700; purchase 3 at step 254-255 with cash 4,200-5,600. M & M & P & Q and Azat Akhtyamov: 132 then 199. Boey and THIRD FARM CLUB: 146 then 199-202, and Boey buys with $37 in hand, so it sells down to the price first. W3: step 151, then step 266 with $18,133 idle, then (18 of 84 games) step 434. Inference: W3's second quadrant is two days later than every top team's while it sits on more cash than any of them.

**Herd size is a function of the shops.** Mean animals at day 12 when the shop type is absent vs present by day 9:

| team | sheep, no yarn store / yarn store | cows, no milk shop / milk shop | geese, no egg shop / egg shop |
|---|---|---|---|
| DSM | 3.0 / 11.2 | 6.0 / 10.5 | 4.3 / 8.4 |
| Unknown Mother-Goose | 3.0 / 11.5 | 5.0 / 9.9 | 3.1 / 6.2 |
| DECEM | 3.0 / 11.8 | 5.3 / 9.4 | 5.0 / 7.8 |
| M & M & P & Q | 4.3 / 12.4 | 5.2 / 9.4 | 0.3 / 0.7 |
| Boey | 2.9 / 11.3 | 3.9 / 8.5 | 5.2 / 7.7 |
| 吃白饭的大肥鱼 | 3.5 / 11.7 | 7.7 / 9.9 | 3.6 / 6.6 |
| THIRD FARM CLUB | 3.8 / 10.2 | 4.5 / 7.6 | 5.5 / 6.0 |
| W3 (ladder) | 5.7 / 10.6 | 5.9 / 7.9 | 1.7 / 3.5 |

Six teams with the same thresholds (3 sheep base, 11-12 with a yarn store; 5-6 cows base, 9-10 with milk shops) is a shared rule table, not six independent optimisers. Inference: the DSM family is one codebase. W3 has the same shape with smaller numbers; its herd layer swaps species rather than adding animals.

**Selling is drain-metered, not raced.** Top-six sale events (n=9,231):

| product | units per lot (median, IQR) | fraction of stock per lot | lots at the post-drain hour | gap between lots (mode) | fraction sold when price >= base / < 0.5 base |
|---|---|---|---|---|---|
| wool | 2 (1-3) | 0.30 | 73% | 4 steps (1,192 of 2,405) | 0.67 / 0.25 |
| milk | 2 (2-3) | 0.67 | 85% | 4 steps (1,161 of 2,974) | 1.00 / 0.50 |
| strawberry | 4 (2-6) | 0.45 | 68% | 4 steps (666 of 2,512) | 0.65 / 0.25 |

Lot size does not grow with stock (wool: median 2 units whether the shed holds 3 or 23) and only mildly with the drain: wool lots stay at 2 with zero, one or two yarn stores (4 with four); milk lots go 2, 2, 3, 3, 4 as milk shops go 1 to 5; strawberry lots stay 4-6 at any shop count. So the smallest mechanism is a fixed small lot per post-drain tick, not an exact drain match. One yarn store drains 2 wool per tick; milk shops drain 1 each; strawberry shops 1 each. So the lot is approximately the drain: they sell what the town just consumed, every tick, and step up when the price is above base. Shed-to-sale lag (FIFO): wool median 14 steps, strawberry 10, milk 6; melon 1 (dumped on harvest). Their lots are within 2 steps of an opponent's lot only 3-8% of the time, and on the same step 13-23%.

W3 (n=1,721 events): sells 100% of shed stock per event (median fraction 1.00 at every price level), lot grows with stock (3, 6, 12, 15), gap mostly 13+ steps (it sells when the shed fills), 47-50% at the post-drain hour, and 57-62% of its lots land on the same step as the opponent's lot. Median shed-to-sale lag 2 steps.

**Nobody reacts to the opponent's sales**, including W3 in effect: W3's same-step share is synchronization with a same-lineage opponent, not a response. The top six's timing is driven by their own harvests and the drain clock.

**Stranded value.** Cash / value in shed+hands+tiles / stranded share:

| | day 6 | day 12 | day 18 | day 24 | day 29 | terminal unsold |
|---|---|---|---|---|---|---|
| top six | 0.8k / 6.7k / 90% | 11.8k / 11.3k / 53% | 43.9k / 15.3k / 26% | 73.2k / 11.6k / 14% | 98.7k / 6.8k / 6% | $2 |
| ranks 7-12 | 0.8k / 6.0k / 88% | 7.6k / 11.8k / 59% | 39.3k / 16.8k / 30% | 69.1k / 12.5k / 15% | 94.4k / 8.0k / 8% | $0 |
| W3 | 0.8k / 6.7k / 89% | 15.0k / 6.5k / 30% | 41.2k / 11.9k / 24% | 68.2k / 10.9k / 14% | 90.2k / 7.8k / 8% | $0 |

W3 converts faster and more completely than the top. Its stranded value is not in inventory; it is idle cash at days 9-12 and under-built capacity (16 animals at day 10 vs 19; second quadrant two days late).

## 3. Smallest plausible mechanism per family

**DSM family (DSM, Unknown Mother-Goose, DECEM, M & M & P & Q, Azat, mtmr_s1, Arda Ceylan, TheEggman).** A fixed opening script to about step 150 including land at 150/220/254; a herd table keyed to shop counts; a task scheduler that re-plans every turn from state (routes unique per game); a sell rule of "each post-drain tick, sell a fixed lot about equal to the drain, more when price is above base, dump melon at harvest"; no opponent model. Inference: hand-written rules, because the thresholds are crisp, identical across teams, and periodic at 4 steps. Ruled out: tape, router, opponent-racing, price-threshold-only selling (milk sells equally at low prices). Not distinguishable from actions alone: whether the scheduler is greedy, an assignment solver, or learned.

**Boey (and THIRD FARM CLUB as a partial fork).** Opening agreement 0.11-0.14 from step 0, so randomised or opponent-conditioned from the first turn; land bought the moment cash allows (step 146 with $37); 7 geese; 3,300 wheat bought and sold per game at the same average price, which earns nothing and looks like noise injection against copiers. Selling otherwise like the DSM family. THIRD FARM CLUB keeps a deterministic opening and a shop-keyed segment to 143 (a small router), then reacts. Inference: Boey is either an optimiser with no churn penalty or a rule agent with deliberate obfuscation; either way copying its order stream copies noise.

**吃白饭的大肥鱼.** Own opening script through step 143 (agreement 0.86 in 72-143, the longest script at the top), then reactive; 11.7 sheep with a yarn store; the strongest milk book (124 per unit).

**W3 / tape lineage.** Route tape keyed by shops (agreement 0.78 same-shop vs 0.61 in 144-400), market-reactive layers on top (agreement falls to 0.41 late because the reserve and race layers move sells), full-stock dumps within 2 steps of harvest, land on the tape's clock two days late, herd swaps instead of herd growth.

## 4. What this says about the metrics you proposed
- Inventory-to-cash lag, liquidation lag, terminal unsold, shed overflow: all measured, none is W3's problem. W3 is the fastest converter on the ladder and leaves nothing unsold; overflow is 5 units a game for everyone.
- Realisation rate: this is where the price part of the gap lives. Top six realise 144 per strawberry and 139 per wool against W3's 117 and 122 (about +20% and +14%), by metering lots to the drain instead of dumping the shed.
- Stranded value curve: useful, but the sign is the opposite of the hypothesis. W3's stranded asset at day 12 is 15k of cash and 25 locked tiles, not inventory.
- Late production: yes. Second quadrant at step 266 vs 199-222; three fewer animals at day 10; zero tomato.

## 5. Implications for building
1. Copyable as rules, not tapes: the herd table (section 2), land at steps 150/220/254, and the sell rule (lot = drain per tick, more when price >= base, hold otherwise). None of these needs the opponent.
2. The hard part is the per-turn labour scheduler that keeps 19-22 animals fed and cared, 30+ tiles watered and replanted daily, on 12 hands. PR 61 lost 15k from an identical day-14 board on exactly this.
3. In a band of tape copies, the metered rule loses the mirror to a dumper (the W2 result, 1-19), because the dumper takes the price first. Against reactive opponents the dumper loses (W3 3 of 31 on the ranks-7-12 panel). So the sell rule has to be conditional on the opponent's family, which is readable from public state in the first two days (hires, structures, land timing).
