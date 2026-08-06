# GreyTheory AI — Canonical Definition

> **Status:** canonical. This document outranks `README.md` and `Docs/architecture.md` where they conflict.
> **Established:** 2026-08-06
> **Supersedes:** the framing in `Docs/architecture.md` (retained as historical design reference only).

---

## 1. The definition

> **GreyTheory AI is a proof-first security research control plane. It converts authorisation into evidence — and refuses to move without either.**

Long form:

GreyTheory AI takes a written authorisation, compiles it into a machine-checkable scope contract, admits only the work that contract permits, records every action against it, and produces artifacts that carry their own proof. Its output is not "findings". Its output is **evidence with provenance**, which becomes either a report or a lesson.

### What it is

- A control plane that governs security research.
- A system where authority is a first-class runtime object, not a paragraph in a policy file.
- An engine that produces fewer, stronger, reproducible artifacts.
- A learning system: work that produces no finding still produces a recorded lesson.

### What it is not

- Not a scanner. Scanners are a replaceable input.
- Not an autonomous exploitation engine.
- Not a system that decides what is legal, in scope, valid, or rewarded. Those are decisions made by humans and by programmes.
- Not a source of income projections. Economics are measured, never forecast from other people's numbers.

---

## 2. Structure: three planes

The system has three planes. They are ranked. Lower planes cannot bypass higher ones.

```
┌─────────────────────────────────────────────────────────────┐
│  PLANE 1 — AUTHORITY          (root; fail-closed)           │
│  ScopeContract compiler · authorisation records ·           │
│  approval gates · append-only audit · stop conditions ·     │
│  kill switch                                                │
└──────────────────────────┬──────────────────────────────────┘
                           │ grants / denies
        ┌──────────────────┴──────────────────┐
        │                                     │
┌───────▼──────────────────┐   ┌──────────────▼───────────────┐
│  PLANE 2 — SIGNAL        │   │  PLANE 3 — JUDGEMENT         │
│  Lane 1 Known-Vuln       │   │  curriculum · hypothesis     │
│  Lane 2 Exposure         │──▶│  queue · hunt sessions ·     │
│  Lane 3 Web Vuln         │   │  evidence vault · validation │
│  Lane 4 AI-App           │   │  gates · report studio ·     │
│  (pluggable collectors)  │   │  triage + earnings ledger    │
└──────────────────────────┘   └──────────────┬───────────────┘
                                              │
                                        the operator
```

### Plane 1 — Authority (root)

Owns: authorisation records, the `ScopeContract` compiler, approval gates, the append-only audit log, rate and volume budgets, stop conditions, and the kill switch.

Rules:

- **No contract, no execution.** A missing, stale, ambiguous, or unverified contract blocks everything below it.
- **Fail-closed.** Ambiguity resolves to `BLOCKED`, never to "probably fine".
- **Out-of-scope beats in-scope** on every match.
- **Derived assets are not inherited.** An asset discovered *through* an in-scope asset is out of scope until independently satisfied.
- Every action below records an authority reference. An action with no authority reference is a defect, not a warning.

Plane 1 requires no network access to build, test, or demonstrate. It is also the commercial surface — the Agent Authority Audit, the Disclosure Kit and the Runtime Safety Pack in `Docs/product-boundary-map.md` are all Plane 1 artifacts.

### Plane 2 — Signal (pluggable)

The four lanes, **demoted from "the system" to collectors**. A lane observes; it does not conclude.

A lane is defined by a plugin contract, not by its tooling:

```yaml
lane_contract:
  id: "lane_2_exposure"
  requires_authority: "PASSIVE_HTTP"   # NONE | LOCAL_FIXTURE | PASSIVE_HTTP | AUTHENTICATED | INTRUSIVE
  emits: "RawSignal"
  may_conclude: false
  network: true
  deterministic_check_required: true
```

Consequences of this framing:

- Lanes are replaceable. Swapping `nuclei` for something else changes a plugin, not the system.
- A lane cannot promote its own output past `contextual` in the taxonomy. Promotion is Plane 3's job, under Plane 1's authority.
- Lane 4 (AI-App) is the differentiated lane. It is the only one where agent-harness and governance experience is an advantage rather than table stakes, and it maps directly onto the internal ChaseOS hardening work.

### Plane 3 — Judgement (the operator loop)

Owns: curriculum and skill tracking, the hypothesis queue, hunt session records, the evidence vault, the validation gates, the report studio, triage outcomes, and the earnings ledger.

This is where the human sits. Plane 3 is what distinguishes GreyTheory from a scanner with a chat interface: it is the part that requires the operator to *understand* the finding before it can leave the system.

The LLM operates across Plane 3 as reasoner, critic and drafter. It never executes, never concludes a binary question, and never holds authority.

---

## 3. Invariants

These hold everywhere. A component that violates one is broken.

### I1 — The provenance triple

Every claim in every artifact is tagged as exactly one of:

| Tag | Meaning | Produced by |
|---|---|---|
| `observed` | A tool saw this, verbatim or summarised | Plane 2 |
| `checked` | A deterministic test ran and returned a binary result | Plane 2 / Plane 3 validators |
| `inferred` | A model or human believes this follows | LLM / operator |

An `inferred` claim may never be silently upgraded. Promotion to `checked` requires a test that could have failed.

This single rule is what makes an LLM safe to use at every step of the system.

### I2 — Authority reference

Every artifact carries the id of the authority under which it was produced. Artifacts without one cannot enter the evidence vault.

### I3 — Fail-closed

Absence of permission is denial. Staleness is denial. Ambiguity is denial.

### I4 — Minimum impact

The proof that establishes an issue is the smallest one that establishes it. Controlled accounts, synthetic data, stop on third-party data.

### I5 — No self-award

The system never marks a finding valid, accepted, rewarded, or disclosed. Only a programme produces those states; the system records them.

### I6 — Zero income is data

Hours that produce nothing are recorded with the same fidelity as hours that produce a payout. A ledger that only counts wins is a broken ledger.

---

## 4. One finding, one lifecycle

`README.md`'s `finding` schema and the handover's `finding_candidate` are **the same entity at different maturities**. There is one object and one state machine.

```
informational → contextual → candidate → validated → report_ready
    → submitted → triaged
    → valid | duplicate | informative | not_applicable | out_of_scope
    → rewarded | no_reward
    → fixed → retested
    → disclosed | private_closed
```

Everything up to `report_ready` is internal and asserted by GreyTheory. Everything from `submitted` onward is external and only ever *recorded* by GreyTheory (see I5).

Gate conditions between `candidate` and `report_ready` are the handover's Gates A–F: authority, reproducibility, impact, evidence, duplicate risk, report quality. Gate G — the decision to submit — is the operator's and is not automatable.

---

## 5. Grapevine AI boundary

Grapevine AI attaches to **Plane 1 and Plane 3 only**.

| Permitted | Prohibited |
|---|---|
| Programme discovery and change detection | Any connection to Plane 2 |
| Vulnerability-class and technology trend signal | Launching or influencing tests |
| Source and write-up collection | Holding or using credentials |
| Freshness monitoring on scope sources | Submitting, disclosing, or contacting anyone |
| Ranking opportunities | Promoting a signal to canonical without human review |

Every Grapevine output is `authority_status: INFORMATION_ONLY` and `canonical_promotion: REQUIRES_REVIEW`. A Grapevine signal may *trigger* a scope recompile; it may never *be* the scope.

**Unreconciled:** the real Grapevine AI implementation has not been inspected from this repo. This section is an interface contract, not a description of existing behaviour. Reconciliation is tracked in `Docs/open-questions.md`.

---

## 6. Capability register

Public and internal descriptions must use these words. Nothing here is inflated.

| Component | Plane | Status |
|---|---|---|
| Scope and authority policy | 1 | **Live** (documented, and now enforced in code) |
| Disclosure / authority checklist | 1 | **Live** |
| `ScopeContract` compiler | 1 | **Live** — `greytheory/authority/compiler.py`, fails closed on ambiguity |
| Execution gate | 1 | **Live** — `greytheory/authority/gate.py`, 11 denial reasons + posture ceiling |
| Append-only audit log | 1 | **Live** — `greytheory/audit.py`, hash-chained, tamper-detecting |
| Kill switch | 1 | **Live** — `Gate.engage_kill_switch` |
| Provenance triple (I1) | 1 | **Live** — `greytheory/provenance.py` |
| Finding schema + lifecycle | 1/3 | **Live** — `greytheory/findings.py`, I5 enforced at the internal/external seam |
| Operator CLI | 1 | **Live** — `greytheory/cli.py` |
| Operator approvals | 1 | **Live** — `greytheory/authority/approvals.py`, reads ChaseOS OSRIL; adds binding, expiry, single-use |
| Programme registry | 1 | **Live** — `greytheory/registry.py`, versioned contracts, source snapshots, scope drift detection |
| Lane framework + runner | 2 | **Live** — `greytheory/signal/`, gate-mediated, network lanes refused |
| Lane 1 Known-Vuln | 2 | **Live (static)** — `lane1_dependency_manifest`, offline manifest vs advisories |
| Lane 4 AI-App | 2 | **Live (static)** — `lane4_agent_config`, offline config review |
| Lane 4 AI-App | 2 | **Aspirational** — architected only |
| Evidence vault | 3 | **Live** — `greytheory/evidence.py`, raw/redacted split, repo guard, export gating |
| Validation gates B–F | 3 | **Live** — `greytheory/validation.py`, deterministic where possible, attested where not |
| Dashboard | 1/3 | **Live** — `greytheory/dashboard.py`, absent data reports unknown, never zero |
| Report studio | 3 | **Live** — `greytheory/report.py`, structure enforced, markdown rendering |
| Curriculum / skill graph | 3 | **Aspirational** |
| Triage + earnings ledger | 3 | **Live** — `greytheory/ledger.py`, all hours counted, forecasting refused below thresholds |
| Grapevine adapter | 1/3 | **Unreconciled** — interface defined, implementation not inspected |

Definitions: **Live** = exists and is used. **Designed** = specified to build-ready detail, not built. **Aspirational** = intended, not specified to build-ready detail. **Unreconciled** = depends on a system not yet inspected.

---

## 7. Positioning

### GitHub repository description

> Proof-first security research control plane. Converts authorisation into evidence — authority, scope and provenance as runtime objects, not policy prose.

### chasintech.com

> **GreyTheory AI** — a security research control plane built on a single rule: nothing runs without authorisation, and nothing leaves without proof. Scope becomes a machine-checked contract. Every claim is tagged as observed, checked, or inferred. The AI reasons and critiques; deterministic tools prove; the human decides.

### The line that does the work

> No scope, no test. No impact, no bounty. No evidence, no report. No permission, no disclosure.

Public copy must not imply live scanning capability, real-world findings, or income until the capability register says otherwise.

---

## 8. Operating posture (current)

- Local-only. No external scanning, live target interaction, credential validation, disclosure, or outreach — per `Docs/scope-policy.md`, which is authoritative.
- Lanes run against local fixtures only.
- The first live engagement happens only after Plane 1 can actually gate it.
- Build substrate: local-first Python package with tests. No network dependency in the core.

---

## 9. Decision log

| # | Decision | Rationale |
|---|---|---|
| D1 | Authority Plane is the product; lanes are plugins | Detection is commodity; authority, provenance and judgement are the defensible layer, and the only one buildable with zero external interaction |
| D2 | One finding entity, one lifecycle | The two prior schemas described the same object; a translation layer would have been pure defect surface |
| D3 | Provenance triple is mandatory everywhere | Makes LLM use safe by construction rather than by convention |
| D4 | Grapevine is Plane 1/3 only, information-only | Prevents an intelligence feed from becoming an unaudited authority source |
| D5 | Local-only until Plane 1 exists | Building the guardrails after operating without them inverts the entire thesis |
| D6 | Python, local-first, tested | Fastest path to demonstrable proof with no network surface |
| D7 | `Docs/architecture.md` superseded, retained | Historical design value; removing it would lose the lane detail |
| D8 | Approvals are read from ChaseOS, never stored here | ChaseOS already owns the approval layer (`chaseos-reconciliation.md`); two approval stores would mean neither is complete |
| D9 | ChaseOS is coupled through its filesystem contract, not Python imports | Keeps `greytheory` dependency-free and standalone-usable; a ChaseOS refactor then breaks a test rather than the runtime |
| D10 | Approvals are bound, expiring and single-use | A decision record alone says consent happened, not that it covers *this* act, *now*, *once* |
| D11 | Apache-2.0 | Patent grant and explicit contribution terms matter more than MIT's brevity for security tooling |
| D12 | **Standalone is first-class; ChaseOS is an adapter** | Apache-2.0 means people will run this without ChaseOS. Zero runtime dependencies, no required external system. Every integration point ships a self-sufficient default alongside it. |
| D13 | Raw evidence lives outside every git working tree, enforced by a guard | A `.gitignore` entry is a convention; committed-and-pushed raw evidence is unrecoverable. This needed to be a wall. |
| D14 | Export is all-or-nothing and redacted-only | Partial export is how raw evidence escapes — the operator fills the gap by hand from the wrong directory. |
| D15 | Validation gates split deterministic / attested | Judgement cannot be machine-decided, so it demands a named human statement rather than a model's opinion dressed as a check. |
| D16 | An unattested gate is `NOT_ASSESSED`, not `FAIL` | "Nobody looked" and "someone looked and it did not hold" call for different actions. Both block. |
| D17 | Gate E rejects claims of duplicate certainty | Duplicate risk can be reduced and estimated, never eliminated. Believing otherwise costs more than the duplicate. |
| D18 | Changed programme source invalidates the human review | Review attaches to the text a person actually read, not to the programme in the abstract. This is the structural defence against scope amnesia. |
| D20 | Effective hourly rate always divides by total tracked hours | There is no parameter to change it. Dividing by only the productive hours is how bug bounty starts looking like a good hourly rate. |
| D21 | Forecasting is refused below 100h / 20 sessions / 5 submissions / 5 closed outcomes | A forecast from three data points has a confidence interval wide enough to contain any belief you brought to it. |
| D23 | A lane may not promote past `contextual` | `RawSignal` has no field for a higher level. Once a collector can conclude, everything downstream is downstream of its optimism. |
| D24 | Collectors reach nothing except through a granted Decision and a rooted `LaneContext` | Enforcement, not convention: a lane with a traversal bug fails loudly rather than quietly widening its own scope. |
| D25 | The runner refuses any lane declaring network I/O | Keeps the core offline by construction; a collector wanting otherwise must move out of the package rather than argue. |
| D26 | Absent dashboard data reports UNKNOWN, never zero | "0 out-of-scope attempts" and "nothing is being recorded" look identical on a screen and mean opposite things. |
| D22 | Mixed currencies are never silently summed | A total that quietly adds dollars to pounds is worse than no total. |
| D19 | Narrowing scope changes are called out separately | A widened scope is an opportunity; a narrowed one means work already done may have been against an asset that is no longer authorised. |
