# GreyTheory AI — Complete Project Brief

> **Snapshot:** 2026-08-07 · 347 tests passing · 6,974 lines of Python · zero runtime dependencies
> **Repository:** `chasedndt/GreyTheory-Research` · Apache-2.0
> **Purpose of this file:** a single self-contained document that can be pasted into a fresh AI session to define the project completely, without that session having to guess at anything.

---

# 0. How to use this document

This is written to be handed to another AI (ChatGPT Pro, or anything else) so it can reason about the project properly. Everything needed is here — no external context required.

**Read §1 before anything else.** It corrects two framings that, if carried into a new session, will produce advice that contradicts the entire system.

Sections are ordered so they can be read straight through, or jumped into:

| Part | Contains |
|---|---|
| §1 | **Two framing corrections.** Read first. |
| §2 | Executive summary — the whole thing in one page |
| §3 | Glossary — every technical term used here |
| §4 | Definition: what it is, what it is not, what it governs |
| §5 | Architecture: three planes, six invariants |
| §6 | Every module: what it owns, what it refuses |
| §7 | The current truth: what works, what does not |
| §8 | How it actually works — walkthrough and CLI |
| §9 | The roadmap |
| §10 | Every design decision and why |
| §11 | Choices to avoid — design, operational, and linguistic |
| §12 | Open questions |
| §13 | A ready-made brief to paste into a new session |

---

# 1. Two framing corrections — read this first

## 1.1 This is not an autonomous system, and that is deliberate

It has been described as "an autonomous system that helps cybersecurity professionals get bug bounties". The second half is right. The first half is the opposite of what was built, and if a new session accepts it, everything it suggests afterwards will pull against the design.

**The system is semi-autonomous with mandatory human gates.** Specifically:

- It cannot submit a report. Submission requires an operator approval reference, enforced in code.
- It cannot decide a finding is valid. Only a programme can, and the system records that.
- It cannot grant itself authority. A compiled scope contract starts at `PENDING_REVIEW`; only a human promotes it to `VERIFIED`.
- It cannot test anything above its operating posture ceiling, currently `LOCAL_FIXTURE` — no network access at all.
- Three of five validation gates require a *recorded human statement*, not a model's opinion.

This is not timidity or an unfinished state. It is the thesis. An autonomous bug-bounty submitter is a well-understood failure mode: it generates plausible reports nobody can reproduce, burns platform reputation, and is banned. The economically valuable thing is **fewer, stronger, defensible reports**, and defensibility requires a human who understands the finding.

The right phrasing is: **an AI-assisted research engine that makes a human researcher faster, more systematic and more evidence-disciplined, without taking authority away from them.**

## 1.2 "In ways that are always possible" — nothing here is guaranteed

Bug bounty is duplicate-heavy, adversarial and variable. Most submissions are not paid. This system improves the *rate* and the *defensibility* of good findings; it cannot make finding them certain, and any advice built on the assumption that it can will be wrong.

The system is built so that the honest version of this is unavoidable: the earnings ledger divides income by *every* tracked hour including the unproductive ones, and refuses to forecast at all until there are 100 tracked hours, 20 sessions, 5 submissions and 5 closed outcomes behind it.

---

# 2. Executive summary

**GreyTheory AI is a proof-first bug bounty and authorised security research engine. It converts authorisation into evidence — and refuses to move without either.**

## The problem it solves

Security research produces three things that look alike and are constantly confused:

1. what a **tool observed**
2. what a **test proved**
3. what a **person or model believes follows**

Nearly every bad outcome in bug bounty is one of these being silently promoted to another. A scanner version-match becomes "a vulnerability". A single reproduction becomes "reproducible". A model's plausible reading becomes "impact". Add an LLM and it accelerates, because fluent prose makes inference *read* like proof.

GreyTheory's answer is not to keep the LLM out. It is to make the distinction **structural**, so an LLM can be used everywhere without its output ever being mistaken for evidence.

## The shape

Three ranked planes. Lower planes cannot bypass higher ones.

```
PLANE 1 — AUTHORITY   (root, fail-closed)   may this happen at all?
   │
   ├── PLANE 2 — SIGNAL     (pluggable collectors)  what did we observe?
   └── PLANE 3 — JUDGEMENT  (the operator loop)     what does it mean, is it sendable?
```

Authority sits at the root because it is the only plane whose failure is unrecoverable. A missed vulnerability is a lost opportunity. An unauthorised request is a legal event.

## The state, honestly

| | |
|---|---|
| **Works today** | The full path from a written authorisation to a validated report draft, offline. |
| **Does not exist** | Any network capability. The system currently detects nothing on a live target. |
| **Blocked on a decision** | Raising the operating posture ceiling — the operator's call, not a build step. |

---

# 3. Glossary

Terms used throughout, including ones that may be unfamiliar.

## Core system terms

**Authority Plane** — the root layer. Owns scope contracts, the execution gate, approvals, the audit log, the kill switch. Nothing runs except through it.

**Signal Plane** — the collectors ("lanes"). They observe and emit; they never conclude.

**Judgement Plane** — the operator's loop. Evidence, validation, reports, ledgers. Where the human sits.

**ScopeContract** — a programme's rules compiled into a machine-checkable object: in-scope assets, exclusions, prohibited techniques, granted authority level, rate limits, an expiry, and a hash of the source text it came from.

**Execution gate** — the single point where any action is permitted or refused. Seventeen distinct denial reasons, one allow path.

**Posture ceiling** — a system-wide cap on authority applied *on top of* whatever a contract grants. Currently `LOCAL_FIXTURE`. A contract legitimately granting `AUTHENTICATED` still cannot exercise it while the ceiling is lower.

**Provenance triple** — every claim is tagged `observed`, `checked`, or `inferred`. See §5.2.

**Authority reference** — a fingerprint of the contract an artifact was produced under. Every artifact carries one.

**Fail-closed** — absence, ambiguity, staleness and error all resolve to *denial*. The opposite (fail-open) is when an error accidentally permits something.

**Attestation** — a recorded human statement that something was done, naming what was done. Required by three validation gates that cannot be machine-decided.

**Kill switch** — a flag that makes the gate deny everything until explicitly released.

**Lane** — one collector. Lane 1 known-vulnerability, Lane 2 exposure, Lane 3 web, Lane 4 AI-app.

**RawSignal** — what a lane emits. Cannot be more than `contextual`.

**LaneContext** — the only thing a collector receives. Rooted at one directory; every read is checked against that root.

**Evidence vault** — content-addressed storage with a hard raw/redacted split. Raw never leaves.

**Scope Watch** — a roadmap component (Phase 5) that would fetch programme pages and detect changes. Not built.

## Security domain terms

**Bug bounty programme** — a company's public offer to pay researchers for security findings, with published rules defining what may be tested.

**VDP (Vulnerability Disclosure Programme)** — a lawful reporting path that usually does not pay.

**Scope** — the assets a programme permits testing against. Out-of-scope assets are prohibited.

**Safe harbour** — a programme's promise not to pursue legal action against researchers who follow the rules. It is not unlimited immunity, and it never overrides scope, local law, or third-party rights.

**Triage** — the programme's process for validating a submitted report.

**Duplicate** — a finding someone else already reported. Usually pays nothing. Typically the largest single category of unpaid work.

**IDOR / BOLA** — Insecure Direct Object Reference / Broken Object Level Authorization. Changing an identifier in a request to access another user's data. The highest-value common class, and hard to automate honestly.

**BFLA** — Broken Function Level Authorization. A lower-privileged role reaching a function it should not.

**SSRF** — Server-Side Request Forgery. Making the server issue requests on the attacker's behalf, often to internal services.

**Subdomain takeover** — a DNS record pointing at an unclaimed third-party service, which an attacker can then claim. Valuable because the proof is binary.

**Prompt injection** — untrusted content reaching an AI system's instruction context. *Indirect* prompt injection is when that content arrives via a tool (a fetched web page, an email) rather than from the user.

**Excessive agency** — an AI system able to take actions beyond what its task requires.

**CVE / GHSA / OSV** — vulnerability identifier schemes. OSV is the machine-readable format published by GitHub, PyPI, npm and Go; this project imports it.

**CVSS** — a numerical severity scoring framework. Recorded but never used to decide anything here.

**MCP (Model Context Protocol)** — a standard for connecting AI models to tools and data sources. Its configuration is one of the things Lane 4 inspects.

**KYC** — Know Your Customer. Identity verification platforms require before paying out.

## Engineering terms

**Hash chain** — each record commits to the hash of the previous one, so altering or removing any entry breaks verification from that point on. Makes tampering *detectable*, not impossible.

**Content-addressed** — stored and verified by the hash of the content itself.

**Idempotent** — doing it twice has the same effect as doing it once.

**Fingerprint** — a stable hash of an object's substantive content, so a change is visible even if the identifier is reused.

**Protocol / duck typing** — an interface defined by the methods something has rather than what it inherits from. Used so integrations can be swapped.

**Injected clock** — passing time in as a parameter rather than calling `now()` internally, so time-dependent behaviour is testable rather than flaky.

**Shannon entropy** — a measure of randomness in a string. Used as a *weak supporting* signal for secret detection.

**PEP 503 normalisation** — the Python packaging rule that `Example_Lib`, `example.lib` and `example-lib` are the same package.

---

# 4. Definition

## 4.1 The one-sentence version

> **GreyTheory AI is a proof-first security research control plane. It converts authorisation into evidence — and refuses to move without either.**

## 4.2 Long form

GreyTheory takes a written authorisation, compiles it into a machine-checkable scope contract, admits only the work that contract permits, records every action against it, and produces artifacts that carry their own proof.

Its output is not "findings". Its output is **evidence with provenance**, which becomes either a report or a lesson.

## 4.3 What it is

- A control plane that governs security research.
- A system where authority is a first-class runtime object, not a paragraph in a policy document.
- An engine that produces fewer, stronger, reproducible artifacts.
- A learning system: work that produces no finding still produces a recorded lesson.

## 4.4 What it is not

- **Not a scanner.** Scanners are a replaceable input.
- **Not autonomous.** See §1.1.
- **Not an exploitation engine.**
- **Not a system that decides what is legal, in scope, valid, or rewarded.** Humans and programmes decide those.
- **Not a source of income projections.** Economics are measured, never forecast from other people's numbers.
- **Not a governance product for other people's systems.** See below.

## 4.5 What it governs — the question that matters

The question *"a control plane governing what?"* has one answer: **it governs the operator's own research activity.**

What may be tested, under whose authorisation, at what authority level, with what evidence, and whether the result may leave.

The Authority Plane is not a general-purpose permission system that happens to be pointed at bug bounty. It is the part of a research engine that stops the research becoming an incident.

**This needs stating because the repository contained an ambiguity from the start.** An early planning document listed product surfaces — an "AI Agent Authority Audit", a "Runtime Safety Pack" — that would govern *someone else's* agents. Those are **derivative offerings**: things that could later be built from the same parts, sold separately, under their own scope.

| | Governs | Status |
|---|---|---|
| **GreyTheory** | The operator's own research | This system. Built. |
| Agent Authority Audit, Runtime Safety Pack | A client's agent deployment | Derivative products. Not built. Not this. |

The mechanisms here — expiring scope contracts, bound single-use approvals, tamper-evident audit, an evidence vault that gates export — are reusable. But *reusable* is an observation about code. **It is not a change of purpose, and must not become one.**

---

# 5. Architecture

## 5.1 The three planes

```
┌─────────────────────────────────────────────────────────────┐
│  PLANE 1 — AUTHORITY          (root; fail-closed)           │
│  ScopeContract compiler · programme registry ·              │
│  execution gate · approvals · append-only audit ·           │
│  posture ceiling · kill switch                              │
└──────────────────────────┬──────────────────────────────────┘
                           │ grants / denies
        ┌──────────────────┴──────────────────┐
        │                                     │
┌───────▼──────────────────┐   ┌──────────────▼───────────────┐
│  PLANE 2 — SIGNAL        │   │  PLANE 3 — JUDGEMENT         │
│  Lane 1 Known-Vuln       │   │  evidence vault ·            │
│  Lane 2 Exposure         │──▶│  validation gates B-F ·      │
│  Lane 3 Web Vuln         │   │  report studio ·             │
│  Lane 4 AI-App           │   │  triage + earnings ledger    │
│  (pluggable collectors)  │   │  dashboard                   │
└──────────────────────────┘   └──────────────┬───────────────┘
                                              │
                                        the operator
```

### Plane 1 — Authority (root)

Rules:

- **No contract, no execution.** Missing, stale, ambiguous or unverified all block.
- **Fail-closed.** Ambiguity resolves to `BLOCKED`, never "probably fine".
- **Out-of-scope beats in-scope** on every match.
- **Derived assets are not inherited.** An asset found *through* an in-scope asset is out of scope until it independently satisfies the contract.
- Every action below records an authority reference. An action with none is a defect.

Plane 1 requires no network access to build, test or demonstrate — which is why it was built first and why the system works today.

### Plane 2 — Signal (pluggable)

The four lanes, **demoted from "the system" to collectors**. A lane observes; it does not conclude.

- Lanes are replaceable. Swapping one scanner for another changes a plugin, not the system.
- A lane cannot promote its own output past `contextual`. Promotion is Plane 3's job, under Plane 1's authority.
- Lane 4 (AI-App) is the **differentiated** lane. It is the only one where agent-harness experience is an advantage rather than table stakes.

### Plane 3 — Judgement (the operator loop)

Where the human sits. This is what stops the system being a scanner with a chat interface: a finding cannot leave without a person having understood it well enough to attest to it.

The LLM operates across Plane 3 as reasoner, critic and drafter. It never executes, never concludes a binary question, and never holds authority.

## 5.2 The six invariants

These hold everywhere. A component that violates one is broken.

### I1 — The provenance triple

| Tag | Meaning | Produced by |
|---|---|---|
| `observed` | A tool saw this | Plane 2 |
| `checked` | A deterministic test ran and returned a binary result | Validators |
| `inferred` | A model or human believes this follows | LLM / operator |

An `inferred` claim may never be silently upgraded. **Promotion to `checked` requires a test that could have failed.**

In code: `promote_to_checked(check_ref, could_have_failed=True)`. That parameter looks unremarkable until you notice that a check which cannot fail proves nothing — and that this is the exact shape of every "the model reviewed it and agreed" workflow.

**This is the load-bearing invariant.** It is what makes an LLM safe to use at every step.

### I2 — Authority reference

Every artifact carries the id of the authority it was produced under. Artifacts without one cannot enter the evidence vault.

### I3 — Fail-closed

Absence of permission is denial. Staleness is denial. Ambiguity is denial.

### I4 — Minimum impact

The proof that establishes an issue is the smallest one that establishes it. Controlled accounts, synthetic data, stop on third-party data.

### I5 — No self-award

The system never marks a finding valid, accepted, rewarded, or disclosed. Only a programme produces those states; the system records them, and only with evidence of what the programme said.

### I6 — Zero income is data

Hours that produce nothing are recorded with the same fidelity as hours that produce a payout. A ledger that only counts wins is a broken ledger.

## 5.3 Authority levels

Ordered. Two independent caps apply to every request — what the **contract** grants, and what the **posture ceiling** allows. The lower wins.

| Level | Meaning |
|---|---|
| `NONE` | Nothing. Also what an unrecognised level parses to. |
| `LOCAL_FIXTURE` | Local files only. No network. **Current ceiling.** |
| `PASSIVE_HTTP` | Unauthenticated reads of in-scope hosts. |
| `AUTHENTICATED` | Requests using accounts the operator controls. |
| `INTRUSIVE` | Anything that could materially affect a target. Always human-approved per instance. |

## 5.4 The seventeen denial reasons

One allow path. That ratio is the design.

| Reason | Triggered when |
|---|---|
| `kill_switch_engaged` | The kill switch is on |
| `no_contract` | No contract supplied |
| `contract_blocked` | The contract has unresolved ambiguities |
| `contract_not_verified` | Compiled but not human-reviewed |
| `contract_stale` | Past the trust window (7 days default) |
| `technique_prohibited` | The contract forbids this technique |
| `asset_out_of_scope` | Matches an exclusion |
| `asset_unresolved` | Matches nothing — absence is denial |
| `derived_asset_not_inherited` | Found via an in-scope asset but not itself in scope |
| `authority_level_exceeded` | Above what the contract grants |
| `posture_ceiling_exceeded` | Above what the operating posture allows |
| `approval_required` | Above the approval threshold, none presented |
| `approval_not_found` | The referenced approval does not exist |
| `approval_denied` | The operator said no |
| `approval_not_binding` | Approval covers a different action or target |
| `approval_expired` | Older than the approval window (8h default) |
| `approval_already_consumed` | Single-use, already spent |

## 5.5 One finding, one lifecycle

```
informational → contextual → candidate → validated → report_ready
    ═══════════ the seam ═══════════
    → submitted → triaged
    → valid | duplicate | informative | not_applicable | out_of_scope
    → rewarded | no_reward
    → fixed → retested
    → disclosed | private_closed
```

Everything to `report_ready` is **asserted** by GreyTheory. Everything from `submitted` is **recorded** from outside.

Two guards on the seam:

- `report_ready` requires at least one `checked` claim. Inference alone is not a report.
- Every state past `submitted` requires `programme_evidence` — a reference to what the programme actually said.

Findings can also be **demoted** within the internal states. Evidence weakens as often as it strengthens, and a system that can only promote will overstate everything it holds. Programme outcomes are never un-said by us.

## 5.6 The validation gates

| Gate | Question | Kind |
|---|---|---|
| **A — Authority** | In scope, permitted, verified, fresh? | Deterministic (the gate) |
| **B — Reproducibility** | Reproduces from a clean session, server-side confirmed? | Attested + requires a `checked` claim |
| **C — Impact** | Which security property, by whom, against whom, at what scale? | Attested + requires a `checked` claim |
| **D — Evidence** | Complete, intact, redacted, minimal? | Deterministic |
| **E — Duplicate risk** | Prior research reviewed, residual risk stated honestly? | Attested |
| **F — Report quality** | Sections present, finished, severity reasoned? | Deterministic |
| **G — Submission** | Should this be sent at all? | **Operator only. Never automatable.** |

**Deterministic** gates re-derive their answer from artifacts every run. Gate D rehashes evidence off disk rather than trusting the manifest, so a modified file fails even though the manifest still agrees with itself.

**Attested** gates cannot be machine-decided, so they demand a recorded human statement. An attestation must name its author and say something substantive — a few words is a checkbox, not a statement.

**Three states, not two.** An attested gate with no attestation returns `NOT_ASSESSED`, not `FAIL`. "Nobody looked" and "someone looked and it did not hold" call for different actions. Both block.

**Gate E rejects claims of certainty about duplicates** — "definitely unique", "no chance of duplicate". It cannot be. A researcher who believes otherwise has stopped modelling the other researchers.

---

# 6. Every module

## Plane 1 — Authority

| Module | Lines | Owns | Explicitly refuses |
|---|---:|---|---|
| `provenance.py` | 127 | The observed/checked/inferred triple; promotion gated on a falsifiable check | Deciding whether a claim is *true* — only how it came to be believed |
| `audit.py` | 168 | Append-only hash-chained JSONL; detects edits, reorders, deletions | Access control on the file itself |
| `authority/scope.py` | 218 | `ScopeContract`, pattern matching (exact/wildcard/CIDR), staleness, fingerprinting | DNS resolution. A hostname is not an address |
| `authority/compiler.py` | 217 | Programme source → contract; fails closed; hashes the source | Fetching programme pages |
| `authority/approvals.py` | ~250 | Binding, expiry, single-use enforcement | Storing approvals when a platform already owns them |
| `authority/gate.py` | 422 | The single execution decision | Performing the action. It answers *may this happen* |
| `registry.py` | 497 | Versioned programmes, source snapshots, drift detection, attention queue | Deciding a contract is trustworthy |
| `advisories.py` | ~330 | OSV import, ecosystem-aware matching, version ordering | Fetching advisory data |

## Plane 2 — Signal

| Module | Lines | Owns | Explicitly refuses |
|---|---:|---|---|
| `signal/contract.py` | 236 | `LaneSpec`, `RawSignal`, the rooted `LaneContext` | Letting a collector conclude |
| `signal/runner.py` | 213 | The only path by which a collector executes | Running a lane that declares network I/O |
| `lanes/agent_config.py` | 332 | Lane 4 — static agent/MCP config review | Sending prompts or invoking a model |
| `lanes/exposure.py` | 320 | Lane 2 — credential shapes, VCS metadata, backups over a local tree | Recording a secret's value |
| `lanes/dependency_manifest.py` | 181 | Lane 1 — manifest versions vs advisories | Calling a version match a vulnerability |

## Plane 3 — Judgement

| Module | Lines | Owns | Explicitly refuses |
|---|---:|---|---|
| `evidence.py` | 509 | Raw/redacted split, hashing, manifests, export gating, repository guard | Redacting — only the operator knows which bytes are sensitive |
| `validation.py` | 430 | Gates B–F | Submitting |
| `report.py` | 216 | Report structure, placeholder detection, markdown rendering | Writing the report |
| `findings.py` | 256 | One finding entity, one lifecycle | Assessing severity, or deciding validity |
| `ledger.py` | 665 | Sessions, triage outcomes, payouts, expenses, honest metrics | Predicting what the next finding is worth |
| `dashboard.py` | 708 | Read model + text/HTML/JSON renderers | Inventing data. Absent stores report unknown |
| `cli.py` | 389 | Operator surface | Anything that touches a network |

**Total: 6,974 lines. Zero runtime dependencies. Standard library only.**

The trust surface of the thing that grants authority is kept deliberately small.

---

# 7. The current truth

## 7.1 Capability register

Public and internal descriptions must use these words.

### Live — exists and is used

| Component | Plane |
|---|---|
| Programme registry (versioning, source snapshots, drift detection) | 1 |
| ScopeContract compiler (fails closed) | 1 |
| Execution gate (17 denial reasons, posture ceiling, kill switch) | 1 |
| Operator approvals (bound, expiring, single-use) | 1 |
| Hash-chained audit log | 1 |
| Provenance triple | 1 |
| Advisory import (offline OSV) | 1/3 |
| Lane framework and runner | 2 |
| Lane 1 — dependency manifests (static) | 2 |
| Lane 2 — local-tree exposure (static) | 2 |
| Lane 4 — agent/MCP config (static) | 2 |
| Evidence vault (raw/redacted, repo guard, export gating) | 3 |
| Validation gates B–F | 3 |
| Report studio | 3 |
| Finding lifecycle | 3 |
| Triage and earnings ledger | 3 |
| Operator dashboard | 1/3 |
| CLI | — |

### Designed but not built

Scope Watch (Phase 5). Lane 3 web collectors. Live versions of Lanes 1, 2, 4.

### Aspirational — architected, not build-ready

Curriculum and skill graph. Hypothesis engine. Vulnerability cards.

## 7.2 Test inventory — 347 tests

| Area | Tests |
|---|---:|
| `test_validation.py` | 37 |
| `test_registry.py` | 36 |
| `test_evidence.py` | 32 |
| `test_advisories.py` | 29 |
| `test_signal.py` | 29 |
| `test_dashboard.py` | 28 |
| `test_ledger.py` | 27 |
| `test_exposure_lane.py` | 21 |
| `test_gate.py` | 21 |
| `test_compiler.py` | 19 |
| `test_approvals.py` | 19 |
| `test_scope.py` | 19 |
| `test_findings.py` | 13 |
| `test_provenance.py` | 8 |
| `test_audit.py` | 7 |

CI runs Linux + Windows across Python 3.11–3.13, plus two extra jobs:

- **Proof job** — fails the build if the deliberately-ambiguous programme fixture ever compiles clean.
- **`no-network-in-core`** — fails the build if any network import appears in `greytheory/`.

## 7.3 What it cannot do — stated plainly

- **It detects nothing on a live target.** The three implemented lanes read local files. There is no network capability at all.
- **It cannot submit.** By design.
- **It has never seen real programme rules.** Every contract compiled so far came from fixtures written in-house, which means the compiler has only met ambiguities someone thought to invent.
- **No curriculum, no hypothesis engine, no vulnerability cards.**
- **Scope Watch does not exist.** Nothing notices a programme edit until you re-register it.
- **No earnings data.** The ledger works; there is nothing in it.

## 7.4 Known gaps and findings

- **ChaseOS run audits are not tamper-evident.** While reconciling with the parent ChaseOS system, its approval layer was found to write per-run JSON files that can be edited, replaced or deleted afterwards with nothing detecting it. GreyTheory's hash chain is the fix; porting it across is proposed and undecided.
- **Two ambiguities in the original planning material** were resolved rather than propagated: a phantom integration (see §11.1) and a purpose drift (see §4.5).

---

# 8. How it actually works

## 8.1 The path, end to end

```
Programme rules (read by a human)
  → Programme record (local JSON)
  → Scope Compiler          fails closed on ambiguity; hashes the source
  → PENDING_REVIEW          a clean compile grants nothing
  → Human review            → VERIFIED
  → Execution gate          17 denial paths, 1 allow, every outcome audited
  → Approval                bound to one action + target, expiring, single-use
  → Collector (lane)        emits observations only, capped at contextual
  → Evidence Vault          raw private and write-once; redacted separate
  → Validation gates B-F    deterministic where possible, attested where not
  → Report Draft            structure enforced, prose not
  → Gate G                  the operator. Never automatable.
  → Programme               the only thing that can say "valid"
  → Ledgers and lessons     including the hours that produced nothing
```

Every arrow is a place the system can say no. That is the design, not a side effect.

## 8.2 CLI surface

```
greytheory compile <programme.json>          compile into a contract
greytheory review <contract.json>            human-review into VERIFIED
greytheory check <contract.json> --asset X   ask the gate a question
greytheory audit-verify                      verify the audit hash chain
greytheory advisories <file-or-dir>          import OSV advisory data offline
greytheory dashboard [--html out.html]       operator dashboard
greytheory programme register|review|status|diff
```

## 8.3 Worked example — the compiler failing closed

Given a deliberately broken programme record:

```
status:      BLOCKED

BLOCKED by 6 ambiguity/ies:
  - in_scope[2] could not be parsed: invalid CIDR 'not-a-cidr'
  - '*.mock-ambiguous.test' appears in both in-scope and out-of-scope
  - max_authority PASSIVE_HTTP permits target interaction but no rate limit is defined
  - notes contains unresolved marker 'unclear'
  - notes contains unresolved marker 'ask'
  - scope note on 'api.mock-ambiguous.test' contains unresolved marker 'tbd'
```

Given a clean one:

```
status:      PENDING_REVIEW

Compiled clean. Status is PENDING_REVIEW - it grants nothing until
a human reviews it.
```

Then the gate, before and after review:

```
DENY   app.mock-verified.test  [contract_not_verified]
ALLOW  app.mock-verified.test  [allowed]
DENY   x.blog.mock-verified.test  [asset_out_of_scope]
DENY   cdn.thirdparty.test  [derived_asset_not_inherited]
DENY   app.mock-verified.test  [authority_level_exceeded]
```

Every one of those decisions is in the hash-chained audit log.

## 8.4 Worked example — Lane 4 on a misconfigured agent

Seven signals on the deliberately vulnerable fixture, zero on the clean one:

```
[contextual] tool_without_approval_gate
    Tool 'delete_record' suggests a consequential action and has no approval requirement
[contextual] wildcard_tool_permission
    Tool 'delete_record' holds a wildcard permission
[contextual] tool_without_approval_gate
    Tool 'send_email' suggests a consequential action and has no approval requirement
[contextual] inline_secret_reference
    Configuration key 'api_key' appears to hold a literal secret
[contextual] unrestricted_egress
    Network egress at runtime.allowed_hosts is unrestricted
[contextual] plaintext_transport
    Server at connectors.crm is configured over plaintext HTTP
[contextual] untrusted_content_reaches_ungated_action
    Agent can fetch external content and hold ungated consequential tools in the same context
```

**The last one is the interesting one.** Neither half — a fetch-capable tool, an ungated consequential tool — is a finding alone. Together they are the *shape* of an indirect prompt-injection path. A per-key scanner never sees it.

## 8.5 Worked example — the honest hourly rate

48 tracked hours, one £400 payout:

```
hours tracked      : 48
gross              : 400 GBP
effective hourly   : 8.33 GBP/h   <- over ALL hours

forecast() refused:
not enough personal data to forecast honestly. Missing:
  - 52.0 more tracked hours (have 48.0 of 100)
  - 8 more sessions (have 12 of 20)
  - 4 more submissions (have 1 of 5)
  - 5 more closed triage outcomes (have 0 of 5)
Until then, plan on zero.
```

£8.33/hour, not "£400 for the session that found it". There is no parameter to change that.

---

# 9. Roadmap

**Current phase: 3.** Posture: local-only.

## Done

**Phase 0 — Definition.** Three planes, six invariants, capability register. Repository contradictions resolved.

**Phase 1 — Authority Plane.** Compiler, gate, approvals, audit, provenance.

**Phase 2 — Judgement Plane.** Evidence vault, validation gates, report studio, registry, ledger, dashboard.

**Phase 2.5 — Signal Plane, offline.** Lane framework plus three static lanes.

## Phase 3 — Real programmes *(current)*

Real programme rules are messier than any fixture: scope in prose rather than tables, exceptions in footnotes, platform defaults contradicting the programme page, "see our policy" pointing at a fourth document.

**Costs nothing, risks nothing** — compiling never contacts the target.

- Register three real public programmes from pasted or saved source.
- Record every case where the compiler blocked on something a human resolves in seconds. **That list is the work.**
- Extend for the patterns that actually appear: prose scope, tiered assets, per-asset authority, reward tables, temporary exclusions.
- Handle platform-versus-programme rule conflicts. Fail closed and say which is which.
- **Keep the fail-closed bias.** A compiler that gets smart enough to guess has stopped being useful.

## Phase 4 — Knowing the field

- ✅ **Advisory sourcing.** OSV import, ecosystem-aware, correct pre-release ordering.
- **Vulnerability cards.** One per class: plain-English model, root cause, safe test pattern, what counts as evidence, remediation, and the internal control it maps to.
- **Curriculum and skill graph.** Mastery expires into review. Mastery means explain, recognise, test, prove, remediate, transfer — not "watched a video".
- **Hypothesis engine.** Ranked, scoped hypotheses instead of undirected clicking.
- **Postmortems that compound.** A no-finding session still produces a lesson that changes the next target score.

## Phase 5 — Scope Watch

Fetch registered programme sources, diff against snapshot, invalidate review on change. **Requires the ceiling raised.** The registry already does the hard half.

## Phase 6 — Raising the posture ceiling

**The decision that changes the risk category, not a config value.**

Today the worst case is a wrong answer in a report. Above `LOCAL_FIXTURE`, the worst case is an unauthorised request against infrastructure that is not ours — a legal event.

Preconditions, all of them:

- At least one real programme compiled, reviewed, verified.
- Written authorisation identified; researcher account and identity headers configured.
- Network collectors living **outside** the core package, acting only through a granted Decision.
- Rate limits enforced against the contract's declared limit.
- Kill switch tested under load.
- Evidence vault pointed at a real private root outside every repository.

**One level at a time.** `PASSIVE_HTTP` first. `AUTHENTICATED` only after passive work runs clean for a sustained period. `INTRUSIVE` per-instance, probably never routine.

## Phase 7 — Network collectors

Ordered by proof model, not by interest:

1. **Subdomain takeover** — binary proof. No judgement, no argument.
2. **Exposure over live hosts** — adds reachability, the part a local tree could never tell us.
3. **Authorization testing (IDOR/BOLA)** — the primary specialism, hardest to automate honestly.
4. **Live AI-app testing** — where static config review becomes behavioural.

## Phase 8 — First submission

Not a build phase. The point of the system.

**A rejected first submission that taught something is a success. A quota-driven submission that was accepted is not.**

## Phase 9 — Proof and public surface

Only from authorised material, only after disclosure permission.

## Deliberately not on the roadmap

- Autonomous submission
- Mass scanning
- Credential validation as a default
- Governing other people's agents

---

# 10. Design decisions and why

| # | Decision | Rationale |
|---|---|---|
| D1 | Authority Plane is the root; lanes are plugins | Detection is commodity; authority, provenance and judgement are the defensible layer |
| D2 | One finding entity, one lifecycle | Two schemas described the same object; a translation layer would be pure defect surface |
| D3 | Provenance triple mandatory everywhere | Makes LLM use safe by construction rather than by convention |
| D4 | External intelligence is Plane 1/3 only, information-only | Prevents a feed becoming an unaudited authority source |
| D5 | Local-only until Plane 1 exists | Building guardrails after operating without them inverts the thesis |
| D6 | Python, local-first, tested | Fastest path to demonstrable proof with no network surface |
| D7 | Prior architecture doc superseded, retained | Historical design value |
| D8 | Approvals read from ChaseOS, never stored here | Two approval stores means neither is complete |
| D9 | Coupled through filesystem contracts, not Python imports | Keeps the package dependency-free; upstream refactors break a test, not the runtime |
| D10 | Approvals bound, expiring, single-use | A decision record says consent happened, not that it covers *this* act, *now*, *once* |
| D11 | Apache-2.0 | Patent grant and explicit contribution terms matter for security tooling |
| D12 | Standalone is first-class; integrations are adapters | Apache-licensed means people will run it without the parent system |
| D13 | Raw evidence lives outside every git working tree, enforced by a guard | A `.gitignore` is a convention; committed raw evidence is unrecoverable |
| D14 | Export is all-or-nothing and redacted-only | Partial export is how raw evidence escapes |
| D15 | Validation gates split deterministic / attested | Judgement cannot be machine-decided |
| D16 | Unattested gate is `NOT_ASSESSED`, not `FAIL` | "Nobody looked" and "it did not hold" call for different actions |
| D17 | Gate E rejects duplicate-certainty claims | Duplicate risk can be reduced and estimated, never eliminated |
| D18 | Changed programme source invalidates the human review | Review attaches to the text a person actually read |
| D19 | Narrowing scope changes called out separately | Work already done may have been against an asset no longer authorised |
| D20 | Effective hourly always divides by total tracked hours | Dividing by only productive hours is how bug bounty starts looking like good money |
| D21 | Forecasting refused below thresholds | A forecast from three data points has an interval wide enough to contain any belief |
| D22 | Mixed currencies never silently summed | A total that adds dollars to pounds is worse than no total |
| D23 | A lane may not promote past `contextual` | Once a collector can conclude, everything downstream is downstream of its optimism |
| D24 | Collectors reach nothing except through a granted Decision and a rooted context | A lane with a traversal bug fails loudly rather than widening its own scope |
| D25 | The runner refuses any lane declaring network I/O | Keeps the core offline by construction |
| D26 | Absent dashboard data reports UNKNOWN, never zero | "0 attempts" and "nothing recorded" look identical and mean opposite things |
| D27 | A collector records the shape of a secret, never its value | A lane that copies credentials into the evidence trail creates the problem it was looking for |
| D28 | Presence reported, never reachability | A key in a tree is present; whether it is served depends on things a directory cannot know |
| D29 | **Purpose is bug bounty and authorised research** | Corrects a drift: reusable mechanisms are an observation about code, not a change of purpose |
| D30 | Phantom integration cut, capability restated under our own name | Building an interface against an unseen system is how a guess hardens into a fact |

---

# 11. Choices to avoid

## 11.1 The phantom-dependency trap — a real example from this project

An early planning document specified an integration with a named system, "Grapevine AI", complete with input and output schemas, a permissions model and a graph structure.

**That document stated, in its own frontmatter, that the system's architecture "was not available in the source context used to create this file."** It was writing a contract for a system it had never seen. No implementation was ever found.

The same document warns, at its own §34.12, against "canonical contamination" — an AI guess hardening into a fact through repetition. It then did exactly that.

**The lesson, generalised:** if a specification names a dependency nobody can point at, the dependency does not exist. Delete the section. If the *capability* is genuinely wanted, restate it under your own name, in your own roadmap, sized to what you would actually build.

Here the capability was restated as **Scope Watch**, and it turned out half of it already existed offline.

## 11.2 Architectural choices to avoid

**Do not let a collector conclude.** A version match is not a vulnerability. A pattern match is not a leaked secret. Once detection can promote its own output, every downstream decision inherits its optimism. Cap collectors at `contextual` structurally, not by convention.

**Do not build a second store for something that already exists.** Two approval systems means an approval recorded in one is invisible to the other, and authority becomes unprovable. Adapt to what exists; ship a self-sufficient default beside it.

**Do not couple through imports when a filesystem contract will do.** An upstream refactor should break a test, not the runtime.

**Do not put security-relevant behaviour behind a boolean nobody checks.** `could_have_failed=True` is the most abusable parameter in this codebase and is documented as such.

**Do not fail open.** Never write a code path where an exception, a missing value or an unrecognised input results in permission. Unknown authority level parses to `NONE`, not to "probably fine".

**Do not let a compiler get smart enough to guess.** Ambiguity resolving to a confident answer is worse than ambiguity blocking.

**Do not store money as floats.** `Decimal` throughout.

**Do not call `now()` inside logic.** Inject the clock, or expiry and staleness become untestable.

**Do not make a dashboard fill empty panels with zeros.**

## 11.3 Operational and account choices to avoid

These are bug-bounty-specific and cost real money and reputation.

**Do not test before verifying scope on the day.** Programmes edit scope without announcing it. A contract verified last month is not evidence of anything — which is why contracts expire in seven days here.

**Do not treat a domain name as authorisation.** Nor a security.txt file, nor a company having a security page, nor a platform listing where the specific asset or technique is excluded.

**Do not use your primary personal accounts for testing.** Use accounts created for the purpose, with the email alias or identifying header the programme requires. Many programmes mandate a specific pattern so their SOC can distinguish research from an attack — skipping it is how researchers get reported as intruders.

**Do not test with an account you do not control both sides of.** Cross-account testing needs two accounts *you* own. Using a real user's data to prove IDOR converts a finding into a privacy incident.

**Do not scale automation before reading the automation policy.** Many programmes cap request rates or prohibit scanners entirely. Rate-limit violations get researchers banned faster than bad reports.

**Do not chase dozens of programmes shallowly.** One primary deep programme, one secondary, one lab lane. Depth beats breadth because duplicates cluster in the shallow surface everyone else also scanned.

**Do not validate a discovered secret.** Finding a credential-shaped string is one thing; testing whether it works is unauthorised access. This system records shape and length and never the value, deliberately.

**Do not retain third-party data.** If sensitive data is captured accidentally: stop, record exactly what was accessed, notify the programme promptly, delete the raw capture, keep the manifest entry noting the deletion.

**Do not submit to hit a quota.** Valid-report rate is the reputational metric that unlocks private programmes. A low-quality submission costs more than the zero it earns.

**Do not argue severity aggressively with triage.** Strong impact explanation outperforms dramatic language with every triager who matters.

**Do not publish before disclosure permission.** Not the finding, not the target name, not a screenshot, not "a client I can't name".

**Do not assume payout mechanics.** KYC requirements, supported countries, payout providers, thresholds, processing times and tax documentation vary per platform and must be checked before treating any of it as income.

## 11.4 Language to avoid

The project treats phrasing as a correctness issue, because imprecise language is how unsupportable claims enter reports.

| Never say | Say instead |
|---|---|
| "is vulnerable" (from a version match) | "matches advisory X's affected range" |
| "exposed" / "leaked" (from a local file) | "present in tree" — presence is not reachability |
| "duplicate risk eliminated" | "residual duplicate risk remains [assessment]" |
| "the model verified it" | Name the deterministic check that could have failed |
| "autonomous" | "semi-autonomous with mandatory human gates" |
| "guaranteed" / "always possible" | State the actual rate, or say it is unknown |
| Describing an aspirational component as working | Use the capability register's words |

---

# 12. Open questions

| # | Question | Why it matters |
|---|---|---|
| **Posture ceiling** | Raise above `LOCAL_FIXTURE`? | The decision that unlocks all network capability, and moves the worst case from "wrong report" to "legal event". Everything in Phases 5–8 waits on it. |
| **First real programme** | Which one? | Phase 3 cannot start without programme text. Costs nothing, risks nothing, and tests the compiler against reality rather than in-house fixtures. |
| **Specialism** | Web/API authorization first, or AI-app security first? | Authorization (IDOR/BOLA) is the highest-value common class. AI-app is where existing agent-harness experience is a genuine edge and where competition is thinnest. |
| **ChaseOS audit** | Port the hash chain across? | Its run audits are currently editable. ~40 lines, no schema change. |
| **Curriculum shape** | How should study actually be structured? | The system can enforce whatever structure is chosen, but the structure is a personal decision. |
| **Commercial** | Does the derivative governance product get built, and when? | It reuses the same parts but has separate scope. Not this system. |

---

# 13. Brief to paste into a new AI session

Copy everything below the line into a new conversation, together with this document.

---

**CONTEXT**

I am building GreyTheory AI, a proof-first bug bounty and authorised security research engine. The complete specification is in the document above. It is real, working code — 6,974 lines of Python, 347 passing tests, Apache-2.0, zero runtime dependencies.

**WHAT I WANT FROM YOU**

Help me deepen and pressure-test the design. Specifically:

1. Where is the architecture wrong or fragile?
2. What have I missed that a professional security researcher would consider obvious?
3. What should Phase 3 (compiling real programme rules) actually handle that I have not anticipated?
4. What is the strongest argument against the choices in §10, and is it right?

**CONSTRAINTS — do not violate these**

- **It is not autonomous and must not become autonomous.** Submission, disclosure, and the decision that a finding is real are human acts, enforced in code. Do not propose removing a human gate.
- **Fail-closed everywhere.** Absence, ambiguity, staleness and error resolve to denial. Do not propose a path where an error results in permission.
- **The provenance triple is not negotiable.** Every claim is `observed`, `checked` or `inferred`, and promotion to `checked` requires a test that could have failed. Do not propose treating model output as evidence.
- **The system never asserts a programme outcome.** It records what the programme said, with evidence.
- **Currently local-only.** No network capability exists and the runner refuses any collector declaring network I/O. Do not assume live scanning.
- **Do not invent dependencies.** If you propose integrating with a system, it must be one that demonstrably exists. This project already had to delete a phantom integration written against a system nobody had seen.
- **No income guarantees.** Bug bounty is duplicate-heavy and variable.

**HOW TO ANSWER**

Be concrete and technical. Prefer naming a specific failure mode over general advice. If you think a decision in §10 is wrong, say which number and why. If you do not know something, say so rather than filling the gap — that is the exact failure this project is designed against.

---

*End of brief. Snapshot 2026-08-07.*
