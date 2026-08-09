# Validation Policy

What has to be true before a finding moves, and who is allowed to say so.

## The two-stage model

Validation happens twice, for different reasons.

**Stage 1 — deterministic.** A check that could have failed, ran, and did not. Machine-decidable, reproducible, no judgement involved. This is the only thing that can create a `checked` claim.

**Stage 2 — judgement.** Whether the proven facts amount to a security impact worth reporting. Human, assisted by a model critic that can flag gaps but cannot clear them.

A finding that passes stage 1 and fails stage 2 is a lesson. A finding that passes stage 2 without stage 1 is an opinion, and cannot reach `report_ready` — enforced in [`findings.py`](../greytheory/findings.py).

## Gates

Adapted from the handover's Gates A–G. Gate A and Gates B–F are implemented offline; Gate G remains operator-only by definition.

| Gate | Question | Kind | Status |
|---|---|---|---|
| **A — Authority** | Was the asset in scope, the technique permitted, the contract verified and fresh? | Deterministic | Implemented — `authority/gate.py` |
| **B — Reproducibility** | Does it reproduce from a clean session, with no hidden precondition, confirmed server-side? | Attested + requires a `checked` claim | Implemented — `validation.py` |
| **C — Impact** | Which security property is violated, by whom, against whom, at what scale? | Attested + requires a `checked` claim | Implemented — `validation.py` |
| **D — Evidence** | Complete, intact, redacted, minimal? | Deterministic | Implemented — `validation.py` |
| **E — Duplicate risk** | Prior research reviewed, and residual risk stated honestly? | Attested | Implemented — `validation.py` |
| **F — Report quality** | Sections present, finished, and internally consistent? | Deterministic | Implemented — `validation.py` |
| **G — Submission** | Should this be sent at all? | Operator only. Never automatable. | By definition manual |

### Deterministic vs attested

**Deterministic** gates re-derive their answer from artifacts on every run. Gate D rehashes evidence off disk rather than trusting the manifest; Gate F re-reads the draft. Nobody can assert their way past them.

**Attested** gates cannot be machine-decided. Whether an impact is real, or whether prior research was checked, is a judgement — so they require a recorded human statement naming what was actually done. An attestation must name its author and say something substantive; a few words is a checkbox, not a statement.

An LLM can help *draft* an attestation. It cannot *be* the attester, because the attestation is a claim about what a person did.

### Three states, not two

An attested gate with no attestation returns `NOT_ASSESSED`, not `FAIL`. The distinction is real: failure means someone looked and it did not hold; not-assessed means nobody looked. Both block submission, but they call for different actions.

### The certainty rule

Gate E **rejects** an attestation claiming duplicate risk is eliminated — "definitely unique", "no chance of duplicate", "duplicate risk eliminated". It cannot be. A researcher who believes otherwise has stopped modelling the other researchers, and that belief costs more than the duplicate would have.

### Warnings

Gates emit warnings that do not block: a reproduction attestation that never mentions a clean session, an impact attestation that names no security property, a redacted artifact still flagged sensitive, evidence produced under a different contract than the finding, an absolute claim like "all users" or "instantly", or a report with no remaining uncertainty recorded. Each is sometimes legitimate. Seeing it flagged is what makes it deliberate.

## What counts as a deterministic check

A check qualifies only if it has a reachable failure path. A registered
validator must declare at least two possible outcomes and run on exact byte
artifacts. `ValidatorRegistry` issues a `CheckReceipt` containing the input
hashes, assertion, possible and actual outcomes, validator/version, runner
digest, time, and authority reference. Only a successful, matching, unused
receipt issued by that registry can promote a claim; the caller-supplied
falsifiability Boolean no longer exists.

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

## Learning-fixture receipts are not finding proof

Milestone 5 `FixtureRunReceipt` records prove only that one shipped synthetic
scenario exercised its positive, deliberately vulnerable, and negative-control
paths under the declared fixture and runner digests. They do not satisfy a
finding's `CheckReceipt` requirement, prove a real application vulnerable, or
credit mastery. Framework mappings are classifications and carry the same
non-proof status.

Mastery uses a separate record: an explicit assessment of one card and one of
six dimensions with named evidence, rationale, assessor, time, and review date.
Only a human assessment credits mastery. A labelled `test_fixture` assessment
may exercise storage and display paths, but the credited state remains
`not_assessed`.

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
| Gates B–F | Code — `validation.validate` |
| Evidence integrity at validation time | Code — Gate D rehashes from disk |
| Severity requires rationale | Code — Gate F |
| No claim of duplicate certainty | Code — Gate E |

Passing every gate does **not** submit anything, and does not advance the finding. It means the finding is *eligible* for the operator's Gate G decision.
