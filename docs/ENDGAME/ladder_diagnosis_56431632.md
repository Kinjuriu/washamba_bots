# Ladder diagnosis — submission 56431632 (`agents/washamba_base_v1.py`)

**Date 2026-09-21, evening.** Submission `56431632` = `agents/washamba_base_v1.py`,
which is `agents/public_farm2945.py` with a two-line header comment changed and
**nothing else** (`diff` from line 3 on is empty; sha256 `bef1717e…` vs `b50ccd3c…`,
the difference being the header). Submitted 13:35 local, read here at **n = 83**.

Budget honoured: **exactly one `ListEpisodes` call** (logged in
`experiments/endgame/listepisodes_calls.log`), 83 completed replays downloaded at
≤ 6 threads into `experiments/endgame/rep/`, no dataset download, no retry.
No agent file, `main.py`, test or commit was touched. **Nothing was built** — see §6.

---

## 0. Answers up front

| question | answer |
|---|---|
| **Absorbed, or was 2,944.7 inflated?** | **Absorbed, decisively.** 59 of the 63 post-burst games (94%) are against agents running *this same base*. Six of them are byte-perfect copies that finish on **identical banks to the dollar**. All 63 post-burst opponents hold submission ids **above** `56269928` (the base's own public submission). |
| **Are we being front-run by our own copies?** | **No.** Median first-`SELL` step difference is **0** on every premium product, in both classes, and median market-list index difference is **0**. Engine-exact realised prices differ by **$0.1–1.6 per unit (<1%)** on identical unit counts. |
| **Is the adaptive horizon responding?** | **It measures, and then never fires.** In 5 traced mirror losses the observed rival lead climbs −12 → 16–25 and the RACE layer logs 97–149 rival sales, but `min(48, max(40, lead+12))` needs `lead ≥ 28`. The horizon is **40 on all 719 steps of all 5 episodes.** Every copy in the field is pinned at a fixed 40. |
| **Where is the deficit?** | **Not in mirrors** (21-14-6, we are *ahead*). It is the **near-copy** class, 4-14, and it decomposes to **CARROT units grown, not price or timing**. |
| **Has matchmaking settled?** | **Settled.** Opponent-rating sd collapsed 350 → ~45 at game 21 and has been flat since; our score has sat in a 2,125–2,236 band for 63 consecutive episodes with no trend. Equilibrium ≈ **2,145**. |
| **Ship the lead overlay?** | **No — the build condition is not met.** The losses are mirror/near-copy dominated but they are *not* front-running. §6. |

---

## 1. Method

`experiments/ladder_episodes.fetch_episodes(56431632)` → 84 rows, 84 `COMPLETED`,
83 with both rewards and an opponent (one self-match row dropped). Sorted by
`endTime`; **the first 20 are the burst** and are reported separately throughout.

**Seat** comes from the replay's own `info.TeamNames` index of `washamba_bots`, never
from the listing's `index` field — that field is *absent* for seat 0 (protobuf default),
which is why the early listing rows read `seat: null`.

**Agreement is split into labour and market, and this split is load-bearing.** The base's
market list reacts to the rival on every step (`_r36_reserve`'s horizon is read from the
observed lead, `_v224_sales_first` reorders, and ~20 opportunistic sell layers fire), so
two byte-identical copies in one game routinely show labour agreement `1.00` and market
agreement `0.86`. Classifying on the full canonical action would have mislabelled most of
the field as `near-copy`. So:

* **labour tape** = `canon([action.farmer, action.hands])` per step — the classifier.
* **market tape** = `canon(action.market)` per step — reported separately; it *is* the
  front-running question.

Classes, per the brief, on labour agreement over the combined window **0–143**:
`mirror ≥ 0.90`, `near-copy 0.60–0.90`, `different < 0.60`. Windows 0–71 / 72–143 /
144–400 / 400–718 are reported individually in `experiments/endgame/agreement_56431632.json`.

**Wins, losses and draws are counted separately.** Six post-burst games end on *exactly*
equal banks. A `ours > theirs` win test scores those as losses; the brief's "26-37" is
that test. The honest record is **26-31-6**.

Artefacts (all gitignored or scratch; none committed):
`experiments/endgame/episodes_56431632.json`, `agreement_56431632.json`,
`classified_56431632.json`, `firstsell_56431632.json`, `realised_56431632.json`,
`horizon_56431632.json`.

---

## 2. The class split

### Post-burst, games 21–83 (n = 63)

| class | n | W-L-D | points | mean margin | our bank | opp rating |
|---|---:|---|---:|---:|---:|---:|
| **mirror** | **41** | 21-14-6 | **59%** | **+1,556** | 102,315 | 2,165 |
| **near-copy** | **18** | 4-14-0 | **22%** | **−607** | 96,655 | 2,170 |
| `different` | 4 | 1-3-0 | 25% | +851 | 98,684 | 2,172 |
| **ALL** | **63** | **26-31-6** | **46%** | +893 | 100,467 | 2,167 |

### Games 1–20 (the burst) (n = 20)

| class | n | W-L-D | points | mean margin | opp rating |
|---|---:|---|---:|---:|---:|
| mirror | 10 | 9-1-0 | 90% | +4,489 | 1,826 |
| near-copy | 2 | 1-1-0 | 50% | +32 | 1,948 |
| `different` | 8 | 8-0-0 | 100% | **+40,804** | **908** |

The burst's 18-2 is the `different` column: eight games against a **908-rated** field we
beat by an average of **$40,804**. That is the ladder's entry cooldown, not a result.

### What the copies actually look like

57 distinct opponent submissions from 57 distinct teams in 63 post-burst games — this is
not one team spamming, it is the field. Their step-0 market order, which is the base's
signature Özer wheat round trip:

| n games | opponent's step-0 market |
|---:|---|
| 24 | `[["BUY_PRODUCT","WHEAT",7],["SELL","WHEAT",2]]` |
| 16 | `[["BUY_PRODUCT","WHEAT",20],["SELL","WHEAT",15]]` ← **ours, verbatim** |
| 11 | `[["BUY_PRODUCT","WHEAT",20],["SELL","WHEAT",15],["BUY_SEED","WHEAT",1]]` |
| 4 | `[["BUY_PRODUCT","WHEAT",5],["BUY_SEED","WHEAT",1]]` |
| 3 | `[["BUY_PRODUCT","WHEAT",5]]` |
| 2 | `[["BUY_PRODUCT","WHEAT",5],["BUY_PRODUCT","WHEAT",10],["SELL","WHEAT",15]]` |
| 1 each | `WHEAT 30/30`, `WHEAT 5+10/2`, and one genuinely unrelated 7×`HIRE` + `BUY_ANIMAL COW` opener |

**62 of 63 post-burst opponents open on the base's step-0 wheat move** — 55 as the full
round trip, 7 as the buy leg only (`WHEAT 5`, with or without a `BUY_SEED`). Of the 41
mirrors, 32 still agree with us at ≥ 0.95 over steps 144–400 and **12 agree at exactly
1.00 all the way to step 718.**

The labour-agreement numbers are the evidence here. The "every post-burst opponent
submitted after `56269928`" fact is corroboration only — it is trivially true of anything
active this week and carries no weight on its own.

Six games are perfect: identical labour *and* market tape, all four windows at 1.00, and
identical final banks — `111658982` (74,196 each), `111662480` (104,025), `111665990`
(124,621), `111674777` (108,559), `111676006` (117,672), `111711083` (134,903).

### The mirrors are not the problem — the forks are

Splitting post-burst mirrors by whether the opponent's opening matches ours exactly:

| | n | W-L-D | points | mean margin |
|---|---:|---|---:|---:|
| same opening (`WHEAT 20/15`) | 15 | 3-6-6 | 40% | −234 |
| different opening size | 26 | 18-8-0 | **69%** | **+2,589** |

Against the 22-game `WHEAT 7/2` cluster we are **16-6, +2,779**. Against our own opening
we draw six of fifteen and net −234.

**Read the step-0 order as a version fingerprint, not as the lever.** A +2,779 season
delta cannot come from a step-0 trade of 15 wheat at ~$30, which can move perhaps $100
either way; and `rim_results.md` §7 already measured resizing *our* opening upward at
**0-32**. The `WHEAT 7/2` cluster also carries market agreement of 0.86–0.93 against the
exact copies' 1.00, i.e. it is an **older or differently-tuned build** of the same base,
and its opening size is simply the cheapest way to tell it apart. Nothing in this table
says "change the opening". What it does say is the expected thing: identical code against
identical code is a coin flip (3-6-6), and the mirrors we beat are the ones running a
different *build*.

The deficit sits in `near-copy`, and within it in one fork:

| fork (post-burst) | n | W-L | mean margin |
|---|---:|---|---:|
| `WHEAT 20/15` **+ `BUY_SEED WHEAT 1`** | 11 | **2-9** | **−896** |
| `WHEAT 5` + `BUY_SEED WHEAT 1` | 4 | 1-3 | +960 |
| other near-copies | 3 | 1-2 | −1,637 |

---

## 3. Front-running: no

### 3.1 Who opens each book first

First `SELL` of each premium product, our step minus theirs. Positive = we are later.

| class | product | n | median Δstep | mean Δstep | median Δ list-index |
|---|---|---:|---:|---:|---:|
| mirror | MELON | 41 | **0** | −0.1 | **0** |
| mirror | STRAWBERRY | 41 | **0** | +0.7 | **0** |
| mirror | WOOL | 41 | **0** | +0.2 | **0** |
| mirror | MILK | 41 | **0** | −0.1 | **0** |
| mirror | EGG | 31 | **0** | +54.2 | **0** |
| mirror | TOMATO | 20 | **0** | 0.0 | **0** |
| mirror | CARROT | 41 | **−3** | −18.0 | **0** |
| near-copy | MELON | 18 | **0** | 0.0 | **0** |
| near-copy | STRAWBERRY | 18 | **0** | 0.0 | **0** |
| near-copy | WOOL | 18 | **0** | 0.0 | **0** |
| near-copy | MILK | 18 | **0** | 0.0 | **0** |
| near-copy | EGG | 17 | **0** | 0.0 | **0** |
| near-copy | TOMATO | 5 | **0** | 0.0 | **0** |
| near-copy | CARROT | 18 | **0** | +14.8 | **0** |

**Every median is zero, on both axes.** We and the copies open each book on the same turn
and at the same market-list index. The non-zero means are a handful of episodes where one
side skips a product for a long stretch (EGG), not a systematic lead. On CARROT we are, if
anything, three steps *early* against mirrors.

The market-list index matters because `_process_market` walks both queues position by
position (`for i in range(max_len)`), so index 0 prices before index 3 within a step.
Median Δ index 0 means neither side has a within-step advantage either.

### 3.2 Realised price, engine-exact

Both recorded tapes were re-seated on `info.seed` with `_commit_unit` instrumented, so
every committed unit is logged with its seat and the price it cleared at.
**All 59 mirror + near-copy episodes reproduce both recorded banks to the dollar.**

Near-copies we lost (n = 14):

| product | our rev | their rev | Δ rev | our units | their units | Δ avg $/unit |
|---|---:|---:|---:|---:|---:|---:|
| MELON | 14,213 | 14,312 | −99 | 72 | 72 | −1.37 |
| STRAWBERRY | 29,395 | 29,798 | −403 | 246 | 246 | −1.57 |
| WOOL | 14,702 | 14,860 | −158 | 137 | 137 | −1.10 |
| MILK | 16,562 | 16,658 | −96 | 192 | 192 | −0.50 |
| EGG | 5,379 | 5,360 | +20 | 106 | 106 | −0.09 |
| **CARROT** | 7,785 | **8,776** | **−992** | 137 | **152** | −0.92 |
| WHEAT | 14,846 | 14,188 | **+658** | 399 | 378 | −0.27 |
| FERTILIZER | 15,281 | 15,390 | −109 | 337 | 337 | −0.36 |
| **TOTAL** | | | **−1,180** | | | (actual margin −1,270) |

Unit counts are **identical** on every premium product. Our realised average price is
lower by **$0.1–1.6 a unit — under 1% on a $198 melon**, which is what a symmetric race
between two identical agents produces, and it appears only in the games we lost (in the
games we won the same table has the opposite sign). It is the *consequence* of losing the
coin flip, not its cause.

The single largest line is **CARROT: they sell 152 units to our 137.** That is production,
not timing. The same decomposition on the dominant 11-game fork:

| product | Δ rev | our units | their units |
|---|---:|---:|---:|
| **CARROT** | **−772** | 128.8 | **140.0** |
| WHEAT | **+460** | 408.6 | 394.2 |
| MELON / STRAWBERRY / WOOL / MILK / EGG / FERT | −63 / −199 / −105 / −26 / +15 / −174 | identical | identical |
| **TOTAL** | **−864** | | (actual margin −896) |

**86% of the −896 is CARROT units grown.** We out-sell them on WHEAT by 14 units and lose
11 units of a crop worth three times as much. The `BUY_SEED WHEAT 1` at step 0 is this
fork's *fingerprint*, not a mechanism — one wheat seed does not move eleven carrots; it
identifies the build whose crop mix differs. Nothing in the gap is a sell-timing or
sell-price effect.

**It is also not unsold stock.** Checked directly, because "they sold 152 and we sold 137"
is equally consistent with 15 carrots stranded in our shed at turn 720: on all 14
near-copy losses **both sheds are completely empty by step 710** (`private.shed` sums to
0 for both seats, CARROT included — traced step by step on `111661624`: ours 97 items at
step 600, 9 at 700, 0 at 710). Both sides liquidate everything. The difference is units
produced, not units left behind, so the follow-up pointer is planting, not liquidation.

---

## 4. The adaptive horizon measures correctly and then never fires

`agents/public_farm2945.py` l.3853–3869 sets, on every step:

```python
horizon = min(V9_RACE_MAX, max(V9_RACE_DEFAULT, st["lead"] + V9_RACE_MARGIN))
        = min(48,          max(40,              lead + 12))
```

with `st["lead"]` initialised to `-V9_RACE_MARGIN` = **−12** and raised monotonically by
`_v9_race_update` whenever a detected rival sale lands ahead of the tape's own next
planned sale of that item.

Traced by importing the base as a module, wrapping its `agent` to log
`_V9_RACE[player]["lead"]` and `_V9_ITEM_HZ[player]["MELON"]` per step, and seating it
live against the opponent's recorded tape on `info.seed`. The file on disk is untouched.
**All five reproduce both recorded banks to the dollar**, so the trace is the real one.

| episode | margin | lead: start → max | rival sales seen | leads logged | horizon min/max | steps above 40 |
|---|---:|---|---:|---:|---|---:|
| `111701305` | −2,922 | −12 → **16** | 97 | 31 | 40 / 40 | **0 / 719** |
| `111695274` | −1,431 | −12 → **21** | 149 | 43 | 40 / 40 | **0 / 719** |
| `111679497` | −1,180 | −12 → **22** | 106 | 23 | 40 / 40 | **0 / 719** |
| `111712209` | −932 | −12 → **25** | 133 | 29 | 40 / 40 | **0 / 719** |
| `111707622` | −613 | −12 → **21** | 130 | 26 | 40 / 40 | **0 / 719** |

**The detector works. The controller it feeds is dead.** The lead has to reach **28** for
`lead + 12` to clear the `max(40, …)` floor. The largest lead observed in a real contested
episode is **25**, and it is not reached until step ~160 at the earliest (first bump at
steps 162–167 in all five). So the horizon is a **constant 40 for the entire season, in
every episode measured.**

### This retracts `rim_results.md` §10

That file's headline conclusion — *"every `farm2945` copy in the frozen field carries the
answer to a fixed-K rim already compiled in: lead them by K and they lead you by K + 12,
up to the clamp"* — **is false in live play.** The adaptive band cannot answer anything,
because it never leaves its floor. Every copy on the ladder is running a **fixed K = 40**.

The measurement it was inferred from is still correct; the inference from it was not. The
retraction rests only on the five traces above — lead maxes at 25 against a threshold of
28, and the horizon reads 40 on 719 of 719 steps in 5 of 5 episodes. Nothing here explains
*why* rim §4's sweep came out monotone in K; the plain reading ("the rival sits at a fixed
40, so K < 40 prices after it and K > 40 barely ahead of it") fits without any adaptive
response at all, and no trace was run on that sweep. Do not cite a mechanism for it.

**This does not licence shipping a K override.** `rim_results.md` §4/§5 already measured
the only value that could matter: **K = 96 reads 21-11, mean +100**, against an
identical-code noise floor of **±1,131 on a single seat-result**, and self-play +64. That
result stands; what changes is only the stated *reason* it cannot be improved by
re-sampling.

---

## 5. The four `different` opponents

Only 4 of 63 post-burst games, and only 3 losses — Talvenn `111665477` (−602) and
Michael Timbs `111704191` (−1,353) / `111706492` (−1,690). Day-by-day, against Timbs
(`experiments/endgame/rep/`, both `farms[].money` and `structure_counts`):

| day | ours | theirs | gap | our structures | theirs |
|---:|---:|---:|---:|---|---|
| 6 | 801 | 274 | **+527** | 6/6 | 6/6 |
| 10 | 3,982 | 2,981 | **+1,001** | 13/13 | 13/13 |
| 14 | 22,936 | 20,910 | **+2,026** | 17/18 | 17/18 |
| 18 | 49,166 | 49,470 | −304 | 17/17 | 17/17 |
| 22 | 65,617 | 67,557 | **−1,940** | 17/17 | 17/17 |
| 24 | 66,452 | 69,251 | **−2,799** | 17/17 | 17/17 |
| 28 | 71,626 | 73,687 | −2,061 | 17/17 | 17/17 |

**These are not different farms.** Structure counts move 4/6 → 6/6 → 10/13 → 13/13 →
17/18 → 17/17 on *exactly* the same days as ours, in all three episodes — this is the same
base lineage with a permuted `hands` assignment, which is why the labour-tape classifier
puts it at 0.06 agreement while the farm is identical. Talvenn's trace is the same, within
±$400 all season.

The gap is flat-to-positive through day 16 and opens only from **day 18–22**. It is a
late-game selling difference on an identical farm, the same days-14-to-20 window
`day11_diagnosis.md` already names — and at −600 to −1,700 it is inside this repo's
measured ladder noise. With n = 3 there is nothing here to act on.

---

## 6. Matchmaking, and the rating

| games | opponent rating | sd | our score after | mean margin | W-L-D | % mirror |
|---|---:|---:|---:|---:|---|---:|
| 1–10 | **1,019** | 350 | 1,629 | +34,836 | 10-0-0 | 20% |
| 11–20 | 1,923 | 178 | 2,159 | +2,303 | 8-2-0 | 80% |
| 21–30 | 2,214 | **33** | 2,153 | −122 | 3-5-2 | 70% |
| 31–40 | 2,173 | 66 | 2,191 | +958 | 5-3-2 | 60% |
| 41–50 | 2,184 | 40 | 2,180 | +1,546 | 4-5-1 | 80% |
| 51–60 | 2,156 | 35 | 2,140 | +642 | 3-7-0 | 30% |
| 61–70 | 2,151 | 52 | 2,154 | +1,133 | 6-4-0 | 80% |
| 71–80 | 2,126 | 44 | 2,140 | +1,467 | 4-6-0 | 60% |
| 81–83 | 2,150 | 53 | 2,141 | +9 | 1-1-1 | 100% |

**Matchmaking has settled, it is not still walking us up.** The opponent-rating standard
deviation collapses from 350 in the burst to ~40–50 from game 21 and stays there; the mean
drifts *down* 48 points across the post-burst half (2,191 → 2,143), not up. Our own score
has oscillated inside **2,125–2,236 for 63 consecutive episodes** with no trend — it read
2,199 at game 21 and 2,141 at game 83.

This is convergence at **≈ 2,145**, which is the answer to the headline question.

### Why a 2,944.7 claim and a 2,145 equilibrium are both true

The base was worth 2,944.7 **when it was the only agent playing it**. It is now the
field's default: 59 of 63 settled-phase games are against it or a fork of it, and six of
those finish on identical banks to the dollar.

A rating is bought by beating people. Against your own code you cannot — a mirror is a
coin flip by construction, and we measure it at exactly that (21-14-6, 59 points of 100,
with six literal draws). When two thirds of your opposition is you, the whole copy-cluster
is forced onto one shared rating, and that rating is the cluster's own mean. The claim was
not inflated; it was **arbitraged away by publication**. The notebook was published
2026-09-19 and every one of our 63 settled-phase opponents submitted after the base's own
`56269928`.

The corollary that matters for T9: **a second copy of the base gains nothing structural.**
Two copies still draw with two thirds of the field. What a second slot buys is only what
`submissions_log.md` already prices — a second noisy draw from the same distribution.

---

## 7. Build decision: not built

The brief's condition was *"if and only if the losses are dominated by mirrors/near-copies
**front-running us**, build `agents/washamba_base_v1_lead.py`."*

Half of that is true and the operative half is not:

* Losses **are** mirror/near-copy dominated — 28 of the 31 post-burst losses (90%).
* They are **not** front-running. Median first-`SELL` step difference is **0** and median
  market-list index difference is **0** on all seven premium products in both classes
  (§3.1); realised prices differ by **under 1% on identical unit counts** (§3.2); and the
  one class with a real deficit loses **86% of it to CARROT units grown** (§3.2).

So no candidate was built, no agent file was created or edited, and no measurement suite
was run. Building the horizon override would have been building against a mechanism that
the data says is not operating — and its numbers are already on record in
`rim_results.md` §4/§5 (mirror 21-11 / +100, self-play +64, both inside a ±1,131 noise
floor).

**What the evidence does support, none of which is a sell-timing knob:**

1. **The deficit is one fork's crop mix** (the 11-game `+BUY_SEED WHEAT 1` build, 2-9,
   −896, 86% of it CARROT). It out-grows us by ~11 CARROT units and we out-grow it by ~14
   WHEAT, with both sheds empty at season end so nothing is stranded. This is the *only*
   measured, repeatable, class-specific loss in 83 games and it is fully reproducible
   offline (all 59 episodes replay to the dollar). It is a planting question, not a market
   one — and note that four earlier crop-mix levers on this base were rejected, so a fifth
   needs a real mechanism before it needs a build.
2. **Every copy on the ladder runs a fixed sell horizon of 40** (§4). `rim_results.md`
   §10's "the copies carry the adaptive answer" is retracted. A K override is still not
   worth a slot on the numbers already measured, but the *reason* recorded in that file was
   wrong and anyone re-reading it should read this section first.
3. **Two copies of the base is not a hedge against a copied field.** §6.

---

## Reproduce

```bash
# One ListEpisodes call, already spent; the dump is cached.
.venv/Scripts/python.exe -c "import json;from experiments import ladder_episodes as le;\
json.dump(le.fetch_episodes(56431632),open('experiments/endgame/episodes_56431632.json','w'))"

# Replays (83, ~600 s at 6 threads) -> experiments/endgame/rep/
# Agreement + classes  -> agreement_56431632.json, classified_56431632.json
# First-sell timing    -> firstsell_56431632.json
# Engine-exact prices  -> realised_56431632.json   (59/59 reproduce both banks to $0)
# Horizon trace        -> horizon_56431632.json    (5/5 reproduce both banks to $0)
```
