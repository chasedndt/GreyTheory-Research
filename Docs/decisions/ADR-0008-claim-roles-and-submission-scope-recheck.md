# ADR-0008 — Claim roles for report-readiness, and a submission-time scope recheck

**Status:** Accepted · 2026-08-09
**Supersedes in part:** the `report_ready` guard introduced with the finding lifecycle.

## Context

Two gaps were identified in the external productisation review (§20 of the analysis that produced Milestones 1–13). Both were correct, and neither was closed by Milestones 1–6.

### 1. One checked claim satisfied `report_ready`

The guard read: *at least one `checked` claim*. That is satisfiable by proving almost nothing. A finding could reach report-ready having deterministically established only that a request returned HTTP 200 — true, checked, receipted, and completely silent on whether anything was wrong.

The guard counted evidence instead of asking what the evidence was *for*.

### 2. Nothing rechecked scope at submission

Every authority check happens before or during evidence collection. Evidence is gathered on Monday; the programme narrows its scope on Wednesday; the report goes out on Friday citing a contract that no longer grants what it did.

The registry already detects drift on re-registration and invalidates human review. Nothing connected that to the moment of submission.

## Decision

### Claim roles

A finding is report-ready when a claim answers each of seven roles, not when a count is met:

| Role | Question | Settled by |
|---|---|---|
| `behaviour` | What actually happened? | Validator receipt |
| `boundary` | Why should the actor not have been able to? | Validator receipt |
| `target` | Which controlled object was affected? | Validator receipt |
| `scope` | Under which contract was this produced? | Validator receipt |
| `evidence_integrity` | Do artifacts still hash to what was recorded? | Validator receipt |
| `reproduction` | Did it repeat from a clean state? | Human, with uncertainty |
| `impact` | What is the security consequence? | Human, with uncertainty |

A `RoleBinding` cannot be constructed unsoundly: a checked role rejects a non-`checked` claim, demands the receipt that promoted it, and refuses a receipt whose id does not match the claim's `check_ref`. A judgement role refuses to exist without a statement of what remains unknown.

One claim cannot answer two roles. That was the shortcut a count-based guard invited.

### Why `impact` is not machine-settled

Whether a proven behaviour *matters* is a judgement about the product, its users, and the programme's own view. A validator that could settle it would be manufacturing exactly the false certainty this project exists to prevent.

### Why `reproduction` is not machine-settled

This one is less obvious and was decided against the reviewer's suggested list.

Reproduction *is* checkable in principle — run it twice, compare. But the only way to obtain that receipt is to act on the target a second time. Making it a required checked role would push **every finding in the system** into doubling its interaction with the target, which contradicts invariant I4 (minimum impact): the proof should be the smallest one that establishes the issue.

Gate B in `validation.py` already treats reproducibility as *attested plus a supporting checked claim*. Two mechanisms disagreeing about the same question would be worse than either. So reproduction is a judgement role here, and Gate B remains its deterministic backstop.

### Submission-time scope recheck

Entering `submitted` now requires a `ScopeRecheck`: the finding's authority reference, the contract fingerprint currently in force, when it was checked, and the contract's status. A mismatch blocks — it is not a warning.

The recheck must belong to the finding whose transition it is authorising, so one finding's recheck cannot be reused to wave through another.

### Role validators

Four reusable validators settle the checked roles *from artifacts already held*: `OwnershipBoundaryValidator`, `SyntheticTargetValidator`, `ContractCurrencyValidator`, `EvidenceIntegrityValidator`. None performs any interaction. That constraint is what makes the stricter guard compatible with minimum-impact proof.

`EvidenceIntegrityValidator` treats an empty manifest as `invalid_input` rather than `supported`. "Nothing to check" must never read as "everything verified" — the same rule the dashboard follows for absent data.

## Consequences

**The vertical slice now proves five things instead of one.** It gained no new target interaction; the additional roles are re-derived from bytes the run already stored. Its test asserted `len(check_claims) == 1`, which encoded the old weak guarantee, and now asserts five plus complete role coverage.

**Existing findings cannot be promoted without bindings.** Any caller reaching `report_ready` must bind roles first. This is a deliberate breaking change; the alternative was a compatibility flag, and a guard with an off switch is not a guard.

**Reports should be generated from `Finding.matrix()`.** Prose drifts stronger than its evidence; a table with a `missing` row cannot. The matrix renders to markdown for embedding.

## Alternatives rejected

- **Keep the count, raise it to three.** Three trivial checked facts are no better than one. The problem was never the number.
- **Make every role machine-settled.** Would have forced a second target read into every finding, and would have had a validator adjudicating impact.
- **Warn instead of block on scope drift.** A warning at submission time is read by someone who has already decided to submit.
