# Validation Policy

What has to be true before a finding moves, and who is allowed to say so.

## The two-stage model

Validation happens twice, for different reasons.

**Stage 1 — deterministic.** A check that could have failed, ran, and did not. Machine-decidable, reproducible, no judgement involved. This is the only thing that can create a `checked` claim.

**Stage 2 — judgement.** Whether the proven facts amount to a security impact worth reporting. Human, assisted by a model critic that can flag gaps but cannot clear them.

A finding that passes stage 1 and fails stage 2 is a lesson. A finding that passes stage 2 without stage 1 is an opinion, and cannot reach `report_ready` — enforced in [`findings.py`](../greytheory/findings.py).

## Gates

Adapted from the handover's Gates A–G. A–B are partially implemented; C–G are designed.

| Gate | Question | Decided by | Status |
|---|---|---|---|
| **A — Authority** | Was the asset in scope, the technique permitted, and the contract verified and fresh at the time of testing? | `Gate.evaluate`, deterministic | Implemented |
| **B — Reproducibility** | Does it reproduce from a clean session, with no hidden precondition, confirmed server-side? | Deterministic replay | Designed |
| **C — Impact** | Which security property is violated, by whom, against whom, at what scale? | Operator, model critic | Designed |
| **D — Evidence** | Baseline and modified request/response, roles, redaction, minimal data? | Schema validator + operator | Designed |
| **E — Duplicate risk** | Public disclosures, changelogs and prior research reviewed? | Operator | Designed |
| **F — Report quality** | Title, steps, expected vs actual, impact, remediation, severity rationale all present and defensible? | Deterministic completeness check + model critic | Designed |
| **G — Submission** | Should this be sent at all? | Operator only. Never automatable. | By definition manual |

## What counts as a deterministic check

A check qualifies only if it has a reachable failure path. `promote_to_checked(..., could_have_failed=True)` is an assertion by the caller that this is so, and it is the single most abusable parameter in the codebase — a check that always passes is not evidence, and asserting otherwise is how model output launders itself into proof.

Qualifying:

- A response body, status or timing that differs measurably between two controlled accounts.
- A server-side state change observable through an independent request.
- A parsed value matching or failing a declared schema.
- A hash comparison.

Not qualifying:

- "The model reviewed it and agreed."
- A client-side observation with no server-side confirmation.
- A check whose assertion cannot fail given the inputs.
- Absence of evidence. Not finding a control is not proof there isn't one.

## Confidence and demotion

Findings can be walked back down. `Finding.demote()` exists because evidence weakens as often as it strengthens, and a system that can only promote will overstate everything it holds.

Demote when: reproduction fails on a clean session, the behaviour turns out to be intended, the precondition proves unrealistic, the affected asset leaves scope, or the impact narrative depends on a step that was never proven.

Demotion is internal-only. A programme outcome is never un-said by us.

## Severity

Recorded, never used to decide anything. Both CVSS and the programme's own framework are stored where available, and neither drives a gate. Severity is a claim about impact and is subject to the same provenance rules as any other claim: if the impact was not demonstrated, the severity is `inferred`.

Do not inflate severity to negotiate. A strong impact explanation outperforms dramatic language with every triager who matters.

## Where this is enforced today

| Rule | Enforcement |
|---|---|
| `report_ready` requires a `checked` claim | Code — `Finding.advance` |
| Programme outcomes require programme evidence | Code — `Finding.advance` |
| Submission requires an operator approval reference | Code — `Finding.advance` |
| Every finding carries an authority reference | Code — `Finding.__post_init__` |
| Gates B–F | Policy only, until the evidence vault exists |
