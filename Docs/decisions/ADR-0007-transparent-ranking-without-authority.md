# ADR-0007 — Transparent Ranking Without Authority

- Date: 2026-08-09
- Status: ACCEPTED; IMPLEMENTED / VERIFIED OFFLINE 2026-08-09

## Context

Milestone 6 requires a useful research queue before GreyTheory has a model
gateway or any wider execution posture. A single unexplained score would hide
subjective judgement, encourage false precision, and risk being mistaken for
validity, severity, probability, or permission to test.

## Decision

GreyTheory ranks only existing, structured, unproven `Hypothesis` records. The
versioned `conservative-local` policy scores nine ordinal factors from 0 to 4:
scope confidence, evidence already present, likelihood, potential impact, test
cost, side-effect risk, duplicate risk, skill value, and target-specific
novelty. Levels are ranking inputs, not probabilities, severity ratings, or
proof.

Four factors are derived from governed records:

- scope confidence from the bound contract, review/staleness state, and current
  versus stored target classification;
- evidence already present from a capped inventory of declared references,
  explicitly not their quality;
- test cost from declared request/time estimates relative to the session budget;
- side-effect risk from the policy's named effect map, with unknown effects
  conservatively assigned level 4.

Likelihood, potential impact, duplicate risk, skill value, and target-specific
novelty require an explicit `operator` or `test_fixture` assessment. Every one
must include provenance, rationale, and uncertainty. `model` is not an accepted
source because the model gateway and evaluation harness do not exist yet.

Every factor records raw and direction-adjusted levels, weight, basis-point
contribution, rationale, provenance, uncertainties, derivation, and observed
inputs. Contributions sum exactly to the item score. Scope-supported items are
partitioned ahead of `scope_review_required` items regardless of numeric score.
Stable hypothesis-ID ordering breaks ties.

The queue is integrity-digested, written outside Git by default, and states
`decision_support_only`, `unproven`, and `execution_authority=none`. Ranking
cannot transition a hypothesis, call the Gate, create an action request, create
a receipt, invoke a model, or perform network/process/browser activity.

## Consequences

- An operator can inspect and challenge every point in the ranking.
- A high score changes queue order only; it does not support a claim or permit
  an experiment.
- Missing or stale scope evidence moves an item to scope review instead of
  being offset by impact or likelihood estimates.
- Target-specific queue artifacts remain private while the reusable policy and
  schema remain versioned reference code.
- Milestone 7 may evaluate model-proposed inputs, but model output must remain
  `inferred` and cannot bypass these provenance or uncertainty requirements.
