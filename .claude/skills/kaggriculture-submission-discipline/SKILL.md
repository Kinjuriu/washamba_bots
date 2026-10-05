---
name: kaggriculture-submission-discipline
description: >
  Read this before evaluating a candidate agent offline or submitting one to the
  Kaggriculture ladder. It encodes how we decide what is worth a submission slot,
  how we read the ladder without fooling ourselves, and the one strategic lever
  (variance when behind) that this competition's scoring rewards. Trigger on any
  task about gating, evaluating, comparing, or submitting an agent.
---

# Kaggriculture submission discipline

Grounded in destbreso's community notebooks (six-checks, measure-your-agent,
know-your-noise, compare-two-agents) and our own results. Sanity-checked, not
swallowed whole: the gates and the noise algebra are trusted; the promotion
measures are treated as filters, because the author states their instrument is
not validated for telling apart two close strong agents, which is our exact case.

## What the offline gate is for

The gate is a reject filter, not a promotion oracle. In our rating band the
effective opponent count is single digits, and the margin between two strong
farms is a tenth of the noise, so the gate can reliably catch a candidate that is
clearly worse and cannot certify one that is slightly better. A pass means "not
obviously worse, worth a ladder slot", never "proven better". The ladder, with a
control running beside the candidate, is the judge.

## Submission protocol

- Five slots. Keep one as a frozen control (the current best base, unchanged),
  live continuously. The other four are candidates.
- Submit as soon as a candidate clears the gate filter. Do not hoard a candidate
  on your machine; an unsubmitted agent earns zero episodes and teaches nothing.
- Read a submission at about its 60th episode, its rating peak, not on day one.
- Never compare a rating today against a rating last week. A byte-identical agent
  drifts down by roughly 3 points per episode as the field is replaced; one of
  ours fell 182 points untouched. Read the candidate against the control's
  trajectory at the same episode count, never day over day.

## Pre-register, then hold out

- Decide the candidate before you run the full evaluation. Do not batch many
  post-hoc variants and keep the winner; that is selection, and it cost the
  community 20 rating points of pure noise on the same games.
- Keep an untouched held-out set of opponent behaviours that you never look at or
  tune against during development. Run the final candidate against it once, at the
  end, for the honest score. Split by whole opponent behaviour, never by seed.

## The six checks before a slot (stop on the first failure)

1. Same game: are you on the engine the recordings were made on? Prove it by
   replaying a recorded game and asserting the bank comes back to the dollar.
   Never trust the version string; it can report success while the wrong engine
   is loaded.
2. Off means off: with your change disabled, the agent is byte-identical to
   before, every turn. "0 differences over N turns" is a gate; "looks fine" is not.
3. It survives: finishes a full season, emits a well-formed action every turn,
   stays inside the turn budget. Invalid actions are silent no-ops, so a broken
   agent can quietly do nothing and just lose.
4. Who you tested against: count distinct opponent behaviours, not rows. Forty
   recorded opponents in our band are often single digits of real strategies.
   Quote the effective count.
5. Same games, not more games: compare candidate and control on the same seed,
   seat and recorded opponent, subtract first, then total. This cancels the
   seed, shop, weed and pairing noise that is most of a bank.
6. The number you picked is not the number you get: if you kept the best of
   several settings, its score is inflated by selection. Pre-register instead.

## The variance lever (design candidates around this)

Probability of beating an opponent is Phi(mu/sigma): mean bank margin over its
spread.

- Behind against an opponent (mu < 0): a higher-variance line wins more often.
- Ahead (mu > 0): tighten variance to lock the lead.

Rating is win/tie/loss with margin ignored, so a loss by a dollar and a loss by
100k score the same. The downside of variance is therefore free: when behind,
widening the spread converts some narrow losses into wins and costs nothing on
the losses that remain. The selector should rank continuations by Phi(mu/sigma)
per detected opponent, not by mean margin.

Caveats: Phi assumes the per-opponent margin is roughly normal, which holds only
inside a tight behaviour cluster; cross-check it against the raw paired win rate,
and treat sigma as directional until the ladder confirms it, since our band gives
too few games to estimate it tightly.

## Optional: a pre-submit hook

A shell hook that runs the gate and refuses the submit on a THIN sample or a
behaviour regression would enforce all of the above automatically. Wire it to
whatever command performs the Kaggle submission once that step is scripted.
