# Public panel — sibling scan vs `public_farm2945` and `nf_trim`

Follow-up to `docs/ENDGAME/public_inventory.md` (T2). That inventory staged
`agents/public_farm2945.py` (thomastschinkel's "2945 Farm", claimed live 2,944.7) and
measured it 16-0 vs our `agents/router_yuan_nf_trim.py`, but never measured the five
sibling agents from the same EXP-167 lineage that were pulled alongside it, plus two
more yhay81 route generations. This closes that gap: every sibling gated and round-robined
against both `public_farm2945.py` and `router_yuan_nf_trim.py`, seeds 300-307, both seats
(16 games per pairing). Raw per-game results: `experiments/endgame/public_panel_results.jsonl`
— **untracked, not committed, but not actually covered by `.gitignore`** (verified via
`git check-ignore -v`; only single-file `agents/.pub_*.py` paths match the existing
`agents/.*.py` rule). See the gitignore-exposure note below.

Zero `NON-DONE/INERT` warnings across all 224 games in both background runs
(`grep -c NON-DONE` on both run logs returns 0) — no candidate silently no-opped.

## Candidates

Extracted verbatim from their notebooks (no code changes) to `agents/.pub_<name>.py`
(dot-prefixed). Two are multi-file submissions and live at `agents/.pub_<name>/main.py`
with their companion data files alongside — Kaggle's tar.gz-with-main.py-at-root format,
same as the competition allows for any submission.

**Gitignore exposure, not yet fixed:** `.gitignore`'s `agents/.*.py` rule only matches
flat files, so the 5 single-file candidates above are correctly gitignored, but the two
multi-file directories, `agents/.pub_yhay81_0908/` and `agents/.pub_yhay81_0909/`, are
**not** covered (confirmed via `git check-ignore -v`) and show as untracked in
`git status`. `agents/.pub_yhay81_0909/actions.json` alone is ~5.1 MB of third-party data.
Nothing here was committed, but `.gitignore` should gain an `agents/.pub_*/` rule (or
equivalent) before anyone runs a broad `git add -A` on this branch — that edit was left
to whichever agent owns the `.gitignore` change already in flight on this branch (it
shows `M` in git status).

| shortname | source kernel | author | pulled | format |
|---|---|---|---|---|
| `ahmedberatozer_v48` | `ahmedberatozer/kaggriculture-v48-clear-the-queue` | Ahmed Berat Özer | 2026-09-21 | single file, embedded `SOURCE_BYTES` blob, sha256-verified against the notebook's own `EXPECTED_MAIN_SHA256` |
| `aurax7_reactivev5` | `aurax7/kaggriculture-shop-router-reactive-v5` | Yaxon | 2026-09-21 | single file, `%%writefile main.py` cell |
| `flexonafft_multiroute` | `flexonafft/kaggriculture-multi-route-farming-agent` | Igor Zharov | 2026-09-21 | single file, embedded `SOURCE_BYTES` blob (V45), sha256-verified |
| `yhay81_0913` | `yhay81/shop-router-0913` | Yusuke Hayashi | 2026-09-21 | single file, `%%writefile main.py` self-contained base85/zlib tape loader |
| `yhay81_0911` | `yhay81/shop-router-0911-simple` | Yusuke Hayashi | 2026-09-21 | single file, same loader shape as 0913 |
| `yhay81_0908` | `yhay81/shop-router-0908` | Yusuke Hayashi | 2026-09-21 | multi-file: `main.py` + `observation.py` + `model.json` + `actions.json`, extracted from an embedded base64 `submission.tar.gz` |
| `yhay81_0909` | `yhay81/shop-router-0909` | Yusuke Hayashi | 2026-09-21 | multi-file: `main.py` + `actions.json` + `LICENSE.txt` (134 votes, most-voted of the yhay81 series) |

All 7 gated clean: `env.run([f, f])` on seed 0 → `['DONE', 'DONE']`, neither reward == 3000
(rewards ranged $67,078–$71,766 both seats, all 7 files).

**Note on `experiments/tapes/run_agents.py`'s summary print:** it labels each candidate
by `os.path.basename(path)`, so both multi-file candidates print as bare `main.py` in the
console summary and in the `cand` field of the jsonl — they are distinguishable only by
which block of 16 jsonl lines they fall in (candidate order in the invocation: v48, aurax7,
flexonafft, 0913, 0911, 0908, 0909 — 16 lines each, in that order). The table below already
resolves this; a future reader of the raw jsonl should not assume the `cand` field alone
disambiguates 0908 from 0909.

## Results

### vs `agents/router_yuan_nf_trim.py` (our current base)

| candidate | W–L (of 16) | mean Δ | worst Δ | min bank |
|---|---|---:|---:|---:|
| `ahmedberatozer_v48` | 16–0 | +16,984 | +1,418 | 64,645 |
| `flexonafft_multiroute` | 16–0 | +16,138 | +2,218 | 66,000 |
| `aurax7_reactivev5` | 16–0 | +14,230 | +2,150 | 66,006 |
| `yhay81_0909` | 16–0 | +11,112 | +3,977 | 63,627 |
| `yhay81_0908` | 15–1 | +7,550 | -6,917 | 62,111 |
| `yhay81_0913` | 13–3 | +11,077 | -4,764 | 67,106 |
| `yhay81_0911` | 12–4 | +9,504 | -4,113 | 65,486 |
| (for reference) `public_farm2945` | 16–0 | +15,982 | +5,395 | 64,263 |

Ordered by win count, not mean, per this scan's own rule. `ahmedberatozer_v48`,
`flexonafft_multiroute`, `aurax7_reactivev5`, `yhay81_0909` (all 16-0) and `yhay81_0908`
(15-1, one game from the group) are **within 2 games of each other — a five-way tie**;
mean order among them is not a tiebreaker. `yhay81_0913` (13-3) and `yhay81_0911` (12-4)
are clearly behind, each having lost outright multiple times.

### vs `agents/public_farm2945.py`

| candidate | W–L (of 16) | mean Δ | worst Δ | min bank |
|---|---|---:|---:|---:|
| `ahmedberatozer_v48` | 0–16 | -3,454 | -10,092 | 58,797 |
| `aurax7_reactivev5` | 0–16 | -6,025 | -9,862 | 57,786 |
| `yhay81_0909` | 0–16 | -8,725 | -15,677 | 55,840 |
| `flexonafft_multiroute` | 0–16 | -8,499 | -23,764 | 51,906 |
| `yhay81_0908` | 0–16 | -10,806 | -24,120 | 55,233 |
| `yhay81_0911` | 0–16 | -10,498 | -31,062 | 60,198 |
| `yhay81_0913` | 0–16 | -18,306 | -52,020 | 50,368 |

**Every sibling loses every game to `public_farm2945`, 0-16, on every seed.** This is the
same matrix read from the other side, per the task instructions — `run_agents.py`'s
`play(a,b)` / `play(b,a)` already covers `public_farm2945` vs each sibling in both seats
within the run above, so no separate farm2945-as-candidate run was needed.
`ahmedberatozer_v48` (its own direct upstream — v48 is credited by name in farm2945's
chassis table) is the closest of the seven, still a clean, decisive loss.

## Verdict

**`public_farm2945` (thomastschinkel's "2945 Farm", already staged and adopted) is the
strongest base of the eight agents measured here, and not by a small margin.** It beats
`router_yuan_nf_trim` 16-0 (+15,982 mean, from the prior inventory) and beats every one
of its own sibling/ancestor agents 16-0 as well, with a floor (min bank 64,263) that no
sibling's worst-case loss comes close to threatening. **No sibling beats `public_farm2945`
head-to-head** — the record is 0-112 across all seven candidates combined, on every one
of the 8 seeds, in both seats, with no split results. Among the siblings themselves,
`ahmedberatozer_v48` / `flexonafft_multiroute` / `aurax7_reactivev5` / `yhay81_0909` tie
for strongest-of-the-rest (each 16-0 vs `nf_trim`), but that distinction is moot for T6:
`public_farm2945` is already the adopted base and nothing here beats it, so the sibling
scan closes without producing a new candidate.

## farm2945's own stated weakness (verbatim, its notebook cell 24)

> v9/4 beats every public notebook, yet against seven of today's top-10 teams it went
> **0 – 36** on the ladder (September 15–17). I replayed 24 of those losses in the engine
> with an exact ledger (both players' real action streams) to see where the money went.
> **We lead until day 10**, because the melon race is ours, **and lose it all after day 11.**

The diagnosed mechanism (cell 26, verbatim):

> The biggest single hole is **tomatoes**. The farms that beat us buy about **9 tomato
> seeds from day ~12** and hold about 10 tomato tiles on day 20. We buy 1.6, and the first
> on day 18. They sell 71 tomatoes at $114 each. We sell 7, at $316, because nobody else
> is selling into that book.
>
> Every tomato program I built lost:
>
> * a tomato overlay on the route's wheat tiles from day 13: **0 gained / 85 lost**
> * a 20-tile tomato patch on new land: **0 / 56**, because the crews cannot water 20 more tiles
> * loosening the gate of the existing tomato project: **+4 / −11**
>
> The route tape is the constraint. Its workers are busy from dawn to dusk, so a tomato
> program needs a different *labour* plan, not just a different crop choice. The adaptive
> farms don't replay a tape. They plan the crew around the crops.

This is the mechanism the cash-aware repair layer (T5) and any later "beat the adaptive
top band" work (T6+) need to account for. The author's own diagnosis is a **fixed labour
schedule that cannot re-plan its crew around a different crop mix once the game state
diverges from the recorded tape** — every tomato fix he tried failed because it changed
the crop without changing the route's labour plan. Note what this does *not* say: the
author does not claim the second-half loss is cash-related, and his own "what did not
work" table (cell 27) never mentions a purchase failure — so this finding doesn't confirm
or rule out T5's separate, cash-specific hypothesis about silent `BUY_ANIMAL`/`BUY_LAND`
failures under contested cash. Treat the two as distinct, both-plausible failure modes on
a route-tape base (`nf_trim`, or any of the siblings above inherit the same tape-replay
structure), not one explaining the other.
