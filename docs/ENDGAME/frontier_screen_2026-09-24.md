# Frontier screen, 2026-09-24

Scope: 6 named public notebooks (7 refs, since two bullets each covered two
kernels) plus a `kernels list --sort-by dateRun` scan (pages 1-3) for anything
run since Sept 21 whose title/markdown claims a ladder score >= 2,800. Page 3
is entirely pre-Sept-21 (nothing added from it). Four title-claim additions
found: `statma/kaggriculture-thomas-2944-candidate` (2944), `dmitriigluzdov/
kaggriculture-7-turn-rescue-historical-lb-2800` (2800+), `haideptry/the-2965-
master-hybrid-engine` (2965), `hakdevelopment/kaggriculture-2887-score-
fieldcraft-agent` (2887). 11 kernels pulled total.

All pulled notebooks (`experiments/endgame/kernels/`) and extracted agents
(`agents/.pub_*.py`) are gitignored and untracked. **Note:**
`experiments/endgame/frontier_screen.jsonl` (this scan's raw per-game output)
is **not** covered by `.gitignore` (verified via `git check-ignore -v`) —
left as-is per instructions not to touch `.gitignore` or commit anything.

No file was modified, committed, or submitted. No dataset was downloaded via
Kaggle datasets; two candidates that required external input datasets are
marked excluded below rather than fetched.

## Extraction notes

- `ahmedberatozer_v48`, `aurax7_reactivev5`, `flexonafft_multiroute`,
  `yhay81_0911`, `yhay81_0913` already existed as `.pub_*.py` from a prior
  scan — not touched.
- `prvsiyan/...frontier-the-soil-remembers-rain` and `prvsiyan/...frontier-
  the-moon-counts-melons` decode to **byte-identical** agent source
  (sha256 `178ae0f7...`, both b85+lzma payloads with a matching
  `ORIGINAL_CANDIDATE_SHA` check in-notebook). Screened once as `frontier_soil`;
  `frontier_moon` is a duplicate, not re-screened.
- `prvsiyan/kaggriculture-floor-aware-market-ledger-20260923` and `prvsiyan/
  kaggriculture-hybrid-state-ledger-20260922` are **not submission notebooks**
  — manual inspection of every cell in both found no `main.py`/agent payload,
  only a reusable accounting library and (in the ledger notebook) an
  illustrative `def agent_skeleton(...)` stub. Excluded, not gated.
- `statma/kaggriculture-thomas-2944-candidate` requires two external Kaggle
  **input datasets** (`submission.tar.gz` files matched by sha256, read from
  `/kaggle/input`) that are not attached to the pulled kernel and were not
  fetched, per the no-dataset-download rule. Excluded, un-extractable under
  the ground rules.
- `hakdevelopment/kaggriculture-2887-score-fieldcraft-agent` is genuinely
  **multi-file**: `main.py` execs a second ~500 KB compressed data/logic file
  (`mirror_plan.py`, an obfuscated route table) at runtime; not trivial, so
  per instructions it's noted and skipped rather than reconstructed.
- All other candidates extracted cleanly (writefile cell, or a
  base85/base64 + zlib/lzma/gzip blob, decoded via AST — never executed).
  Where the notebook itself publishes a self-check hash
  (`EXPECTED_*SHA256`/`ORIGINAL_CANDIDATE_SHA`), it matched the decoded bytes
  (`v57`, `pop_robust`, `frontier_soil`/`frontier_moon`, `rescue_2800`).
  `metav4_v13` and `hybrid_2965` publish no such hash to check against; their
  decoded sha256 is recorded but unverifiable against an author-stated value.
- `dmitriigluzdov/kaggriculture-7-turn-rescue-historical-lb-2800` embeds a
  self-contained gzip'd tar (no external dataset needed); extracted `main.py`
  from it directly (`opening_liquidity_agent`, sha256 matches the notebook's
  own `EVALUATION_MANIFEST.candidate_source_sha256`).
- Oddity, noted not chased further: `pop_robust` and `rescue_2800` produce
  **byte-for-byte identical per-seed results** against V56 on all 8 seeds
  despite different source bytes — both are thin variations on the same
  "public state router" tape lineage and evidently never diverge in action
  on these seeds.
- Licence: all extracted candidates state **Apache-2.0** with upstream
  attribution notices retained in the source header/NOTICE text (checked in
  both the extracted `.py` and the source `.ipynb`); `kernel-metadata.json`'s
  own `license` field is `null` for every kernel (Kaggle's kernel-pull API
  doesn't surface the notebook-page licence badge — not a red flag, just not
  present there).

## Gate (self-play seed 0, `timeout 180`, plus a replay-based max-ms/turn pass)

All 7 screenable candidates: `['DONE','DONE']`, neither reward `== 3000`, max
per-turn time well under the 1,000 ms budget.

## Screen: vs `agents/washamba_base_v2.py` (V56), seeds 300-307, both seats (16 games)

| ref | author | date | licence | claimed score | gate | max ms/turn | vs V56 (W-L, mean, worst) | verdict |
|---|---|---|---|---|---|---:|---|---|
| `ahmedberatozer/kaggriculture-v57-funding-order-invariant` | Ahmed Berat Özer | 2026-09-22 | Apache-2.0 | not stated | pass | 105 | **16-0, +113, worst +46** | Strongest overall — see below |
| `aurax7/kaggriculture-shop-router-reactive-v7` | Yaxon | 2026-09-17 | Apache-2.0 | not stated | pass | 57 | **16-0, +10,312, worst +3,054** | Huge margin but a trap — loses to `base_v1` |
| `prvsiyan/...frontier-the-soil-remembers-rain` (= `...frontier-the-moon-counts-melons`, byte-identical) | prvsiyan | 2026-09-22 | Apache-2.0 | not a self-claim (cites a "2,879.7 public notebook" as an external reference) | pass | 265 | 14-2, +950, worst -993 | Real win, not top-2 by win count |
| `thomastschinkel/the-metav4-farm-submission-v13` | Thomas Tschinkel | 2026-09-20 | Apache-2.0 | "scored 2944" (markdown) | pass | 87 | 1-15, -504, worst -2,224 | Loses outright — reject |
| `nihilisticneuralnet/kaggriculture-population-robust-economy` | parthenos | 2026-09-23 | Apache-2.0 | not stated | pass | 186 | 8-8, +139, worst -516 | Coin flip — reject |
| `dmitriigluzdov/kaggriculture-7-turn-rescue-historical-lb-2800` | Dmitrii Gluzdov | 2026-09-22 | Apache-2.0 | "LB 2800+" (title) | pass | 112 | 8-8, +139, worst -516 (identical per-seed to `pop_robust`, see note) | Coin flip — reject |
| `haideptry/the-2965-master-hybrid-engine` | haideptry | 2026-09-23 | Apache-2.0 | "2965" (title) | pass | 157 | 6-10, +37, worst -536 | Losing record — reject |
| `statma/kaggriculture-thomas-2944-candidate` | statma | 2026-09-23 | Apache-2.0 | "2944" (title) | **not extractable** (needs external Kaggle input datasets) | — | — | Excluded |
| `prvsiyan/kaggriculture-floor-aware-market-ledger-20260923` | prvsiyan | 2026-09-23 | Apache-2.0 | n/a | **not a submission** (research notebook, no agent) | — | — | Excluded |
| `prvsiyan/kaggriculture-hybrid-state-ledger-20260922` | prvsiyan | 2026-09-22 | Apache-2.0 | n/a | **not a submission** (tutorial stub, no real policy) | — | — | Excluded |
| `hakdevelopment/kaggriculture-2887-score-fieldcraft-agent` | Hak | 2026-09-21 | Apache-2.0 | "2887" (title) | **multi-file, not trivial** | — | — | Excluded |

## Top 2 by win count vs each other and vs `agents/washamba_base_v1.py` (2945 Farm), same seeds

Top 2 by win count are `v57` and `reactive_v7` (both 16-0 vs V56 — `frontier_soil`'s 14-2 doesn't clear that bar per the read-win-count-first rule, despite a higher mean than v57).

| matchup | W-L (of 16) | mean | worst |
|---|---|---:|---:|
| `v57` vs `washamba_base_v1.py` (2945 Farm) | **16-0** | +1,991 | +1,022 |
| `reactive_v7` vs `washamba_base_v1.py` (2945 Farm) | **0-16** | -3,897 | -9,824 |
| `reactive_v7` vs `v57` | 16-0 | +10,297 | +3,049 |

## Recommendation

The three-way result is a genuine cycle, not a clean ranking: `base_v1` (2945 Farm) beats `reactive_v7` 16-0 (+3,897 read the other way), `reactive_v7` beats both V56 and `v57` 16-0 (+10,312 / +10,297), and `v57` beats both V56 and `base_v1` 16-0 (+113 / +1,991). Nobody measured here is undefeated.

**`ahmedberatozer/kaggriculture-v57-funding-order-invariant` is still the right pick, on a dominance argument rather than an undefeated one.** Swapping V56 -> `v57` gives up nothing and gains a little: `v57` matches or beats V56 in every matchup measured (16-0 directly vs V56 at +113 mean/worst +46, and 16-0 vs `base_v1` at +1,991, where V56 itself has not been shown to win), and its one loss — 0-16 vs `reactive_v7`, -10,297 — is the *same* loss V56 already takes (0-16 vs `reactive_v7`, -10,312, from the earlier V56-vs-siblings scan). So this is a strict improvement over the current base, not a step change: **be plain that the direct V56 margin (+113 mean) sits below this repo's own ~1,000-bank ladder-visibility floor (CLAUDE.md, "a change worth less than ~1,000 bank is invisible here") — the ladder will not register that edge on its own.** The measurable, ladder-relevant part of the case is the base_v1 result (+1,991, clearly above the floor) plus the no-regression property against `reactive_v7`.

`aurax7/kaggriculture-shop-router-reactive-v7` posts by far the largest single margin measured (+10,312 mean vs V56) and would look like the obvious pick on a V56-only comparison — but it collapses 0-16 against the 2945 Farm, which `docs/ENDGAME/README.md` identifies as a common ladder opponent shape (many top teams are forks of it). Losing cleanly to the most common opponent type is a worse failure mode for a Bradley-Terry tournament than a thin win margin, so it is not recommended as the primary submission. Everything else screened is a coin flip or an outright loss against V56 and does not clear the bar. Licence is Apache-2.0 across every screened candidate, with upstream attribution notices retained in the file headers, matching how V56 itself was staged — no legal blocker to submitting `v57`.
