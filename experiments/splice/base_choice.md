# Base choice for the splice build

Which base to embed byte-verbatim in `agents/washamba_splice_v1.py` for days 0-7
(`experiments/splice/build.py`'s `--base`, default `agents/w3_herdsafe2700.py`).

## Method

Ran each candidate base in self-play and vs W3 (`agents/w3_herdsafe2700.py`), 4 seeds
(900-903), truncated at `episodeSteps=192` so the run stops right after producing the
observation the splice controller actually inherits (`obs["step"] == 191`, the last turn
before handover at step 192 / day 8 hour 0). For the base's own seat, recorded: money,
land quadrants owned, tiles planted by crop, animals placed by species, structures, shed
contents, seeds held, hands hired that day (`farm["hires_today"]`).

Script: `experiments/splice/_base_choice_measure.py` (supporting script, not a frozen
deliverable, kept so these numbers are reproducible). Raw output:
`experiments/splice/results/base_choice_snapshots.jsonl`.

Candidates: W3 (`agents/w3_herdsafe2700.py`), W0 (`agents/w0_v15stack_control.py`),
reactive v7 (`agents/washamba_reactive_v1.py`), and — added 2026-09-25 per the
coordinator, since it's a public opening 15 of the top 100 ladder teams start from
(BUY WHEAT 20 / SELL 15, no seed buy) — the 2945 Farm (`agents/washamba_base_v1.py`).

## Result: the physical farm is almost identical across all four bases; money alone is
## the wrong metric, and shed wheat changes the answer

**Footprint.** On 3 of the 4 seeds tested (901, 902, 903), W3, W0, reactive v7 and the
2945 Farm own the same quadrants, plant the same crops, buy and place the same animals
(`{COW: 8, SHEEP: 2}`, `{PASTURE: 13}`), and hire the same crew (`hires_today = 7`) —
this is the same opening tape, not a coincidence: all four are documented forks of the
same public "v15stack" / "2945 Farm" lineage (`docs/ENDGAME/public_inventory.md`), and
W3's own header confirms it inherits this days-0-7 opening before its own RACEPX/HERD
layers take over. **Seed 900 is the exception**: W3, W0 and the 2945 Farm all buy a
GOOSE and build a COOP (`{COW: 6, SHEEP: 2, GOOSE: 2}`, `{PASTURE: 11, COOP: 2}`), while
reactive v7 alone skips that and puts the same money into two extra cows instead
(`{COW: 8, SHEEP: 2}`, `{PASTURE: 13}`) — a real, seed-conditional divergence, not a
tie, and it costs reactive v7 money on that seed specifically (below).

**Money alone favors W0 — but money alone is the wrong comparison.** W3 consistently
carries **~3 more wheat in its shed** than the other three at handover (5/7/5/5 units vs
2/4/2/2, every seed) — a designed feed reserve, consistent with W3 layering a
"herd-safe" mechanism on top of the shared opening. Priced at that seed's own day-8
`market["prices"]["WHEAT"]` quote (~$31-33/unit, read directly from the handover
observation — an approximation of the actual `BUY_PRODUCT` cost, which quotes one unit
of inventory later and so is negligibly different at this market depth), that reserve is
worth **$155-231**, comparable to or larger than W0's raw cash lead over W3 ($86-92 on
3 of 4 seeds, $282 on seed 900). Money alone is silently discarding an asset roughly the
same size as the difference it's ranking on.

Money + shed wheat at that day-8 quote, self-play, by seed:

| base | 900 | 901 | 902 | 903 | mean |
|---|---|---|---|---|---|
| **W3** | **898** | **703** | **691** | **698** | **747.5** |
| W0 | 891 | 693 | 684 | 691 | 739.8 |
| FARM2945 | 809 | 610 | 608 | 609 | 659.0 |
| REACTIVE_V1 | 609 | 610 | 608 | 609 | 609.0 |

**W3 comes out ahead of W0 on every one of the 4 seeds** once wheat is counted — a
small, consistent $7-10 lead, the reverse of the money-only ranking. FARM2945 and
REACTIVE_V1 are indistinguishable from each other on 3 of 4 seeds (same footprint, same
money, same shed) and sit clearly below both W3 and W0 on all four — mainly because
neither carries W3's wheat reserve, and neither reaches W0's cash level either. The
vs-W3 mode (not tabulated) tracks each base's own self-play total within a few dollars
on every seed, confirming this isn't a self-play artifact.

It isn't only a valuation nicety: Builder B's own instrumentation found **three animals
already sitting at `consecutive_unfed == 1` at step 192** (they missed day 7's feed).
Wheat already in the shed can be spent on a `FEED` action on the controller's very first
turn; a cash lead has to clear a `BUY_PRODUCT` order first, which lands next turn — one
extra turn of exposure on animals that are already one missed feed from escaping. W3's
reserve is a small but direct match for exactly the situation the controller inherits.

## Recommendation

**W3 (`agents/w3_herdsafe2700.py`)** — the contract's existing default, confirmed rather
than overridden. It wins the properly-priced day-8 asset comparison (money + shed wheat)
on every seed tested, and its wheat reserve is immediately usable against the
already-unfed animals the controller inherits, where a cash-only lead is not. No change
needed to `experiments/splice/build.py`'s default.

*(Note on process: an earlier draft of this section ranked bases by money alone and
recommended W0, and additionally mis-stated the footprint as identical on all 4 seeds
and REACTIVE_V1/FARM2945 as consistently below W3 in raw money — both wrong, caught on
review against this file's own underlying data. Corrected here; the raw snapshots in
`experiments/splice/results/base_choice_snapshots.jsonl` are unchanged and support the
numbers above directly.)*

## Panel baseline

Reproduces Stephane's top-six panel baseline (`harness/top6panel.py`,
`harness/top6_panel.json`, `harness/faithful_eps.json`) for W0 and W3, without editing
any of those files. The 80-episode panel's replays are not in the repo (~31 MB each,
gitignored); `harness/top6panel.py` itself hardcodes a replay directory that doesn't
exist on this machine. `experiments/splice/_panel_baseline.py` (supporting script, not a
frozen deliverable) downloads the 38 `faithful_eps.json` episodes needed for the target
number from `https://www.kaggleusercontent.com/episodes/{id}.json` (no auth; verified
the live JSON shape matches exactly what `harness/tapeopp.py` expects --
`info.seed`/`info.TeamNames`/`rewards`/`steps`), gzip-wraps them into
`experiments/endgame/rep/{id}.json.gz` (already-gitignored convention, matching other
downloaded replays there), and calls `harness/tapeopp.py` UNCHANGED, once per episode
(subprocess, exactly as `top6panel.py` itself does) -- only the path is adapted, per the
task's instruction not to edit Stephane's files.

Target: **W0 wins 6 of 38 faithful episodes, median margin -21,744.**

**Reproduced exactly.** `experiments/splice/_panel_baseline.py agents/w0_v15stack_control.py 3`:

> `w0_v15stack_control.py: 6 wins of 38 faithful episodes (0 errors)`
> `median margin -21,744   mean -13,433   worst -38,209   best +88,468`

Then W3 on the identical panel, `experiments/splice/_panel_baseline.py agents/w3_herdsafe2700.py 3`:

> `w3_herdsafe2700.py: 5 wins of 38 faithful episodes (0 errors)`
> `median margin -23,409   mean -15,667   worst -38,098   best +88,321`

| base | wins / 38 | median margin | mean margin | worst | best |
|---|---|---|---|---|---|
| W0 | 6 | -21,744 | -13,433 | -38,209 | +88,468 |
| W3 | 5 | -23,409 | -15,667 | -38,098 | +88,321 |

W0 edges out W3 on this panel too (one more win, a smaller median and mean deficit), consistent
with — though not the same evidence as — the step-191 money result above. Both losing records
against the top-six's real, frozen tapes are exactly what `docs/ENDGAME/splice_build.md` already
expects ("the top six beat the tape family by about 21,000") and the reason the splice's reactive
controller is the only path left with prize-level upside; neither number here is an argument
against W0, since both bases lose this badly and the choice between them is about which one the
*controller* inherits at day 8, not about closing this gap by day 7.

Raw per-episode results: `experiments/splice/results/panel_w0_v15stack_control.jsonl`,
`experiments/splice/results/panel_w3_herdsafe2700.jsonl`.
