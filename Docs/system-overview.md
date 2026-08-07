# System Overview

The whole architecture in one document, written at the point where the path runs end to end: authorisation in, evidence out, with a human gate at every consequential step.

For the canonical definition read [`definition.md`](definition.md). This explains how the parts actually fit together and *why they are shaped the way they are*.

---

## 1. The one-sentence version

> GreyTheory converts authorisation into evidence. Every step between is designed so that the failure mode is refusal, not permission.

## 2. The problem it solves

Security research produces three things that are easy to confuse and expensive to mix up:

- things a tool **observed**,
- things a test **proved**,
- things a person or a model **believes follows**.

Almost every bad outcome in bug bounty traces to one of these being silently promoted to another. A scanner match becomes "a vulnerability". A model's plausible reading becomes "impact". A single reproduction becomes "reproducible". A researcher's hope becomes "critical".

Add an LLM and the confusion accelerates, because fluent prose makes inference *read* like proof.

GreyTheory's answer is not to keep the LLM out. It is to make the distinction structural, so an LLM can be used everywhere without its output ever being mistaken for evidence.

## 3. Shape: three ranked planes

```
AUTHORITY  (root, fail-closed)  — may this happen at all?
   │
   ├── SIGNAL     (pluggable collectors) — what did we observe?
   └── JUDGEMENT  (the operator loop)    — what does it mean, and is it sendable?
```

Authority is the root because it is the only plane whose failure is unrecoverable. A missed vulnerability is a lost opportunity; an unauthorised request is a legal and reputational event. So the plane that can cause the worse failure sits above the ones that can cause the lesser.

**Signal is deliberately demoted.** The four lanes — known-vuln, exposure, web, AI-app — are collectors, not the product. Anyone can run a scanner. What is defensible is the authority, provenance and judgement wrapped around it. A lane observes and emits; it may not promote its own output past `contextual`.

**Judgement is where the human sits.** This is what stops the system being a scanner with a chat interface: a finding cannot leave without a person having understood it well enough to attest to it.

## 4. The six invariants

Everything else is an implementation detail. These are not.

| | Invariant | What it prevents |
|---|---|---|
| I1 | Every claim is `observed`, `checked` or `inferred`, and promotion to `checked` requires a falsifiable test | Inference laundering itself into proof |
| I2 | Every artifact carries the authority it was produced under | Evidence that cannot be traced to a permission |
| I3 | Absence, ambiguity, staleness and error all resolve to denial | Fail-open under exactly the conditions where care lapses |
| I4 | Proof is the smallest one that establishes the issue | Data greed dressed up as thoroughness |
| I5 | The system records programme outcomes; it never asserts them | A tool congratulating itself on a finding nobody accepted |
| I6 | Zero-yield hours are recorded at the same fidelity as payouts | A ledger that only counts wins, and the false hourly rate that follows |

I1 is the load-bearing one. `promote_to_checked(check_ref, could_have_failed=True)` looks unremarkable until you notice that a check which cannot fail proves nothing — and that this is the exact shape of every "the model reviewed it and agreed" workflow.

## 5. The path, end to end

```
Programme rules (read by a human)
  → Scope Compiler        fails closed on ambiguity; hashes the source
  → PENDING_REVIEW        a clean compile grants nothing
  → Human review          → VERIFIED
  → Gate                  17 denial paths, 1 allow, every outcome audited
  → Approval              bound to one action + target, expiring, single-use
  → Collector             emits observations only
  → Evidence Vault        raw private and write-once; redacted separate
  → Gates B-F             deterministic where possible, attested where not
  → Report Draft          structure enforced, prose not
  → Gate G                the operator. Never automatable.
  → Programme             the only thing that can say "valid"
  → Ledgers and lessons   including the hours that produced nothing
```

Every arrow is a place the system can say no. That is the design, not a side effect of it.

## 6. Why each component looks the way it does

### Scope Compiler — suspicious, not clever

It does not try to parse programme prose intelligently. It looks for reasons to refuse: unparseable rules, assets in both scope lists, interactive authority with no rate limit, `TBD`/`unclear`/`ask` markers, paused programmes, missing timestamps. Any one blocks the contract.

A clean compile produces `PENDING_REVIEW`, never `VERIFIED`. **The compiler cannot grant authority — only a human can.** And review cannot rescue a blocked contract; that requires fixing the source and recompiling. Review confirms a clean compile was read. It does not resolve ambiguity.

The source hash means a later re-read proves whether the rules changed, without storing the page.

### The Gate — seventeen ways to say no

One allow path, seventeen denials. That ratio is the design.

Two caps apply independently: what the **contract** grants, and what the current **operating posture** allows. The posture ceiling means the local-only stance is enforced in code rather than remembered — a contract legitimately granting `AUTHENTICATED` still cannot exercise it while the ceiling sits at `LOCAL_FIXTURE`.

Scope is not inherited. An asset discovered *through* an in-scope host is denied with a reason that names what it was discovered through, because that is the question the operator is about to ask.

Every decision is audited *before* it returns. An allow that was not audited is indistinguishable from one that never happened, so auditing is not the caller's responsibility.

### Approvals — bound, expiring, single-use

A decision record says consent happened. It does not say it covers *this act*, *now*, *once*. So:

- **Bound** — approval to read `a.example.test` is not approval to delete it, nor to touch `b.example.test`. An unbound approval covers nothing.
- **Expiring** — eight hours. A working session, not a week.
- **Single-use** — enforced against the audit log rather than a second ledger, because the log already records every allow and so already knows what has been spent. Only allows consume: a wrong-target typo does not silently void a legitimate approval.

### Evidence — a wall, not a convention

Raw and redacted are separate artifacts. Raw is write-once. Only redacted can be exported, and export is all-or-nothing — a partial package is how raw evidence escapes, because the operator fills the gap by hand from the wrong directory.

The vault **refuses to initialise inside a git working tree**. A `.gitignore` entry can be defeated by a `git add -f` or a tired evening, and raw evidence once pushed survives in the reflog, in forks, in caches. Unrecoverable failures get walls.

A redacted copy byte-identical to the raw capture is rejected as "nothing was redacted" — the single most likely mistake, and one that silently defeats the entire split.

The vault does not redact. Only the operator knows which bytes are sensitive, and a regex that thinks it does is worse than nothing: it produces confident, incomplete redaction.

### Validation — deterministic where possible, attested where not

Gates D and F re-derive their answers from artifacts every run. Gate D rehashes evidence off disk rather than trusting the manifest, so a modified file fails even though the manifest still agrees with itself.

Gates B, C and E cannot be machine-decided, so they demand a recorded human statement. An attested gate with no attestation returns `NOT_ASSESSED` rather than `FAIL` — nobody looked is a different state from someone looked and it did not hold.

Gate E rejects claims of certainty about duplicates. Duplicate risk can be reduced and estimated, never eliminated.

### Findings — one entity, one lifecycle

The scanner-shaped `finding` and the research-shaped `finding_candidate` were the same object at different maturities. Unified, with a hard seam: everything to `report_ready` is asserted by GreyTheory, everything from `submitted` is recorded from outside and requires evidence of what the programme said.

Findings can be **demoted**. Evidence weakens as often as it strengthens, and a system that can only promote will overstate everything it holds.

## 7. Standalone by construction

Apache-2.0, zero runtime dependencies, standard library only. The thing that grants authority should have a small trust surface.

No network code in the core, enforced in CI rather than by convention. When lanes eventually need network access they will live in a separate package that can only act through a `Decision`.

Integrations read foreign **filesystem contracts**, never foreign Python packages, and every integration point ships a self-sufficient default beside it:

| Point | Standalone default | Optional integration |
|---|---|---|
| Approvals | `LocalApprovalStore` | `ChaseOSApprovalStore` (OSRIL records) |
| Evidence root | Platform user-data directory | `CHASEOS_VAULT_ROOT` |

So an upstream refactor breaks a test here, not the runtime.

## 8. Where the LLM sits

It reasons across the Judgement Plane: summarising programmes, reading JavaScript, generating hypotheses, drafting reports, criticising findings, writing postmortems.

It never executes, never decides a binary question, never holds authority, and never produces a `checked` claim. It can help draft an attestation; it cannot be the attester, because an attestation is a claim about what a person did.

This is why the provenance triple is worth its cost. With it, an LLM can touch every part of the system safely. Without it, every LLM output is a potential false proof.

## 9. What does not exist

Stated plainly, because the failure mode of an architecture document is implying completeness:

- **No lane is implemented.** The system currently detects nothing. What works is the part that decides whether anything may run.
- **No submission path.** By design. Submitting, contacting triage, and disclosing are operator acts.
- **No programme registry, curriculum, skill graph, earnings ledger, or dashboard.**
- **Scope Watch does not exist.** Nothing notices a programme edit until you re-register it.
- **The posture ceiling is `LOCAL_FIXTURE`.** No external interaction is permitted at all right now.

The capability register in [`definition.md`](definition.md#6-capability-register) governs every public claim.

## 10. What the shape is for

Two missions, and the architecture serves both with the same parts.

**External:** authorised research that produces fewer, stronger, reproducible reports.

**Internal:** every control here is a transferable pattern — resource-level authorisation, approval binding and single-use consumption, tamper-evident audit, untrusted-content isolation, evidence minimisation. The one already earned back: reading ChaseOS's approval layer surfaced that its run audits are editable, and the hash chain built here is the fix.

That is the compounding loop. External research sharpens the internal controls; the internal architecture becomes the specialism that makes the external research distinctive.
