# forward_pricing/

Deliberately empty. `forward_pricing_experiment.py` and
`forward_pricing_experiment_report.md` stay at `experiments/` root, not
here.

Why: `main.py` (line ~1661) contains a comment pointing to
`experiments/forward_pricing_experiment.py's report` for context on the
forward-pricing mechanism it inlines from `pricing.py`. `main.py` cannot
be modified — that is a hard constraint for this repo — so that pointer
can never be corrected if the file moves. Leaving the file at its
original path is the only way to keep the pointer in `main.py` accurate.

Status: this specific report's own decision was **NEEDS MORE DATA
(leaning ACCEPT)** — an earlier iteration of forward-pricing research,
not itself merged. The forward-pricing logic actually shipped in
`main.py`/`pricing.py` today was integrated via later work, not this
file directly; this file is preserved as the historical record of the
original experiment, not as the source of what's in production now.

This folder exists so the intended top-level layout is visible even
though nothing lives here today.
