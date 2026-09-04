# GreyTheory — Trust-Kernel Definition

> **Status:** canonical for the trust kernel. `PROJECT_DEFINITION.md` is canonical for product identity and overall capability truth.
> **Established:** 2026-08-06
> **Reframed:** 2026-08-09 — the control plane remains intact inside the Security Research Operating System category.
> **Supersedes:** the framing in `Docs/architecture.md` (retained as historical design reference only).

---

## 1. The definition

> **GreyTheory is a standalone, local-first, human-governed Security Research Operating System. Its proof-first control plane converts authorisation into evidence — and refuses to move without either.**

Long form:

GreyTheory takes written authorisation, compiles it into a machine-checkable scope contract, admits only work that contract permits, records every action against it, and produces artifacts that carry their own proof. The existing code is the constitutional and evidentiary kernel. Research workspaces, hypotheses, experiments, the governed learning catalogue, transparent hypothesis ranking, offline model gateway, dark worker foundations, and the Windows-first Guided Mission Control workbench now exist at their documented local/offline maturity; network collection, passive posture, and live-programme operation remain later gated layers.

### What it is

- A Security Research Operating System whose trust kernel governs security research.
- A system where authority is a first-class runtime object, not a paragraph in a policy file.
- An engine that produces fewer, stronger, reproducible artifacts.
- A learning system: work that produces no finding still produces a recorded lesson.

### What it is not

- Not a scanner. Scanners are a replaceable input.
- Not an autonomous exploitation or submission engine.
- Not a system that decides what is legal, in scope, valid, or rewarded. Those are decisions made by humans and by programmes.
- Not a source of income projections. Economics are measured, never forecast from other people's numbers.
- **Not a governance product for other people's systems.** See below.

### What it is for, and what it governs

**GreyTheory is a bug bounty and authorised security research operating system.** That is the purpose. It is not a secondary reading and it does not drift.

The question "a control plane governing *what*?" has one answer: **it governs the operator's own research activity.** What may be tested, under whose authorisation, at what authority level, with what evidence, and whether the result may leave. The Authority Plane is not a general-purpose permission system that happens to be pointed at bug bounty — it is the part of a research engine that stops the research becoming an incident.

This needs stating because the repository contained an ambiguity before any code was written. `product-boundary-map.md` lists product surfaces — an Agent Authority Audit, a Runtime Safety Pack — that would govern *someone else's* agents. Those are **derivative offerings**: things that could later be built from the same parts, sold separately, under their own scope. They are downstream of this system, not a description of it.

The distinction matters practically:

| | Governs | Status |
|---|---|---|
| **GreyTheory** | The operator's own research | This system. Built. |
| Agent Authority Audit, Runtime Safety Pack | A client's agent deployment | Derivative products. Not built, not specified, not this. |

The mechanisms here — expiring scope contracts, bound single-use approvals, tamper-evident audit, an evidence vault that gates export — are reusable, and that reusability is worth something later. But *reusable* is an observation about the code. It is not a change of purpose, and it must not be allowed to become one. A component being general-purpose is not a reason to redefine the system around it.

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

Plane 1 requires no network access to build, test, or demonstrate — which is why it was built first, and why it works today under a local-only posture.

Its mechanisms would also underpin the derivative products in `Docs/product-boundary-map.md`. That is a note about reuse, not about what this plane is for: here it governs the operator's own research, and nothing else.

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
- Lane 4 (AI-App) is the differentiated lane. It is the only one where agent-harness experience is an advantage rather than table stakes, and it maps directly onto the internal ChaseOS hardening work.

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

## 5. Scope Watch — external intelligence, when it is built

*Formerly specified as an integration with a system called "Grapevine AI". That name came from a planning document which admitted, in its own words, that the system's implementation "was not available in the source context used to create this file". No such implementation was found. Building an interface against a system nobody has seen is how a guess hardens into a fact, so the name is retired and the capability is restated here on our own terms. See roadmap Milestone 8.*

**Scope Watch** is a future component that watches programme sources for change. It is defined now so its boundary is fixed before anything is built against it.

| Permitted | Prohibited |
|---|---|
| Fetching programme pages the operator has registered | Any connection to Plane 2 |
| Detecting that source text has changed since the last snapshot | Launching or influencing tests |
| Collecting published advisories and authorised write-ups | Holding or using credentials |
| Flagging a contract as due for re-verification | Submitting, disclosing, or contacting anyone |
| Ranking opportunities for the operator's attention | Promoting anything to canonical without human review |

Every Scope Watch output is information-only and requires review before it changes anything. It may *trigger* a recompile; it may never *be* the scope.

Half of this already exists without any network access: the registry detects drift the moment a programme is re-registered, and invalidates the human review when the source text differs. What Scope Watch adds is only the fetching — noticing without being told. That is a small component under a clear name, not an integration with an unknown system.

---

## 6. Capability register

Public and internal descriptions must use these words. Nothing here is inflated.

| Component | Plane | Status |
|---|---|---|
| Scope and authority policy | 1 | **Live** (documented, and now enforced in code) |
| Disclosure / authority checklist | 1 | **Live** |
| `ScopeContract` compiler | 1 | **Live** — `greytheory/authority/compiler.py`, fails closed on ambiguity |
| Execution gate | 1 | **Live** — `greytheory/authority/gate.py`, 17 denial reasons + posture ceiling |
| Append-only audit log | 1 | **Live** — `greytheory/audit.py`, hash-chained, tamper-detecting |
| Kill switch | 1 | **Live** — `Gate.engage_kill_switch` |
| Provenance triple (I1) | 1 | **Live** — `greytheory/provenance.py` |
| Validator-issued check receipts | 1/3 | **Live (offline)** — `greytheory/checks.py`, exact-input hashes and single-use promotion |
| Finding schema + lifecycle | 1/3 | **Live** — `greytheory/findings.py`, I5 enforced at the internal/external seam |
| Operator CLI | 1 | **Live** — `greytheory/cli.py` |
| Operator approvals | 1 | **Live** — `greytheory/authority/approvals.py`, reads ChaseOS OSRIL; adds binding, expiry, single-use |
| Programme registry | 1 | **Live** — `greytheory/registry.py`, versioned contracts, source snapshots, scope drift detection |
| Programme source bundles | 1 | **Live (offline)** — `greytheory/authority/sources.py`; HackerOne/GitLab, blocked Bugcrowd/YNAB, and direct-policy/MCP Python SDK source shapes verified |
| Lane framework + runner | 2 | **Live** — `greytheory/signal/`, gate-mediated, network lanes refused |
| Lane 1 Known-Vuln | 2 | **Live (static)** — `lane1_dependency_manifest`, ecosystem-aware, over imported OSV data |
| Lane 2 Exposure | 2 | **Live (static)** — local-tree inspection; presence, never reachability |
| Advisory import | 3 | **Live** — `greytheory/advisories.py`, offline OSV ingestion |
| Lane 4 AI-App | 2 | **Live (static)** — `lane4_agent_config`, offline config review |
| Lane 3 Web and live versions of Lanes 1/2/4 | 2 | **Planned** — no network capability exists |
| Evidence vault | 3 | **Live** — `greytheory/evidence.py`, raw/redacted split, repo guard, export gating |
| Validation gates B–F | 3 | **Live** — `greytheory/validation.py`, deterministic where possible, attested where not |
| Dashboard | 1/3 | **Live** — `greytheory/dashboard.py`, absent data reports unknown, never zero |
| Report studio | 3 | **Live** — `greytheory/report.py`, structure enforced, claim/evidence matrix, markdown rendering |
| Research workspace/domain objects | 1/3 | **Live (offline)** — all ten Milestone 3 records plus integrity-checked `ResearchStore` |
| Hypothesis / experiment engine | 3 | **Live (offline)** — explicit lifecycles/budgets plus one complete two-account `LOCAL_FIXTURE` integration |
| Transparent research queue | 3 | **Live (offline)** — versioned nine-factor policy, explained ordinal scores, scope-review partition, integrity-bound private output, no execution authority |
| Vulnerability cards / skill graph | 3 | **Live (offline)** — 12 versioned cards, 12 synthetic fixtures, acyclic prerequisites, and six evidence-bound mastery dimensions |
| Training modes / adaptive curriculum | 3 | **Partial / live offline** — deterministic guidance, transparent adaptive review, explicit human assessment, bounded standard/assisted/transfer journeys, 24 interactive lessons, topic roadmaps, and two ready Case Packs exist; the session/role pack, broader curricula, and governed coach conversation remain open |
| Model gateway | cross-cutting | **Live offline** — governed roles, citations, budgets, provenance, adversarial evaluation, and deterministic local provider; no network provider configured |
| Standalone graphical workbench | 1/3 | **Partial / implemented preview** — Guided Mission Control, thirteen journeys, same-origin persisted learner commands, repeatable whole-application keyboard acceptance, a bundled wheel, and current-user shortcut/restart/upgrade/runtime-recovery acceptance pass; separate-account, screen-reader/platform AT, signing, and uninstall acceptance remain open |
| Passive broker / worker | cross-cutting | **Partial / dark local foundation** — Ubuntu 24.04.4 no-route/full-service, namespace-lifetime exact-egress, clean read-only WSL2 image-runtime, Windows CurrentUser DPAPI same-profile, and carrier-neutral authenticated-session candidate proofs pass; hardened local-VM/reboot acceptance, provisioned identity keys, durable replay, accepted carrier/VM binding, security review, approved recovery/ACLs, programme review, and posture approval remain open |
| Triage + earnings ledger | 3 | **Live** — `greytheory/ledger.py`, all hours counted, forecasting refused below thresholds |
| Scope Watch | 1/3 | **Partial** — offline captured-source comparison and invalidation are live; governed external collection is unavailable |

Definitions: **Live** = exists and passes current tests. **Partial** = a useful subset exists. **Designed** = specified, not built. **Planned** = sequenced but not implemented. **Historical** = retained context, not current truth.

---

## 7. Positioning

### GitHub repository description

> Local-first, human-governed Security Research Operating System. From scope to proof; every action authorised, every claim traceable.

### chasintech.com

> **GreyTheory** — a local-first Security Research Operating System built on one rule: nothing runs without authorisation, and nothing leaves without proof. Its offline trust kernel, structured research domain, complete in-memory two-account slice, governed 12-card learning catalogue, transparent unproven-hypothesis queue, and interactive Windows-first learning workbench are implemented as a research preview. Passive networking remains dark pending every host, recovery, programme, and human-approval gate.

### The line that does the work

> No scope, no test. No impact, no bounty. No evidence, no report. No permission, no disclosure.

Public copy must not imply live scanning capability, real-world findings, or income until the capability register says otherwise.

---

## 8. Operating posture (current)

- Local-only. No external scanning, live target interaction, credential validation, disclosure, or outreach — per `Docs/scope-policy.md`, which is authoritative.
- Lanes run against local fixtures only.
- The first live engagement happens only after the network-worker, source-bundle, data-policy, threat-model, and posture gates are implemented and operator-approved.
- Build substrate: local-first Python package with tests. No network dependency in the core.

---

## 9. Decision log

| # | Decision | Rationale |
|---|---|---|
| D1 | Authority Plane is the product; lanes are plugins | Detection is commodity; authority, provenance and judgement are the defensible layer, and the only one buildable with zero external interaction |
| D2 | One finding entity, one lifecycle | The two prior schemas described the same object; a translation layer would have been pure defect surface |
| D3 | Provenance triple is mandatory everywhere | Makes LLM use safe by construction rather than by convention |
| D4 | External intelligence is Plane 1/3 only, information-only | Prevents a feed from becoming an unaudited authority source. Applies to Scope Watch when built. |
| D5 | Local-only until Plane 1 exists | Building the guardrails after operating without them inverts the entire thesis |
| D6 | Python, local-first, tested | Fastest path to demonstrable proof with no network surface |
| D7 | `Docs/architecture.md` superseded, retained | Historical design value; removing it would lose the lane detail |
| D8 | Approval authority has one source per deployment | Local standalone and optional ChaseOS-backed providers must not mirror or compete. See ADR-0003. |
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
| D29 | **Purpose is bug bounty and authorised research. It governs the operator's own work.** | Corrects a drift: the Authority Plane's mechanisms are reusable, which is an observation about code, not a change of purpose. Governance products for other people's agents are derivative, downstream and separate. |
| D30 | Grapevine cut; the capability restated as Scope Watch | The name came from a planning document that admitted it had never seen the implementation. Building an interface against an unseen system is how a guess hardens into a fact. |
| D31 | **Security Research Operating System is the product category** | The control plane is the trust kernel, but not the complete researcher-facing product. ADR-0001. |
| D32 | Trust planes and product layers coexist | Planes define trust; layers define capability. No layer may weaken a plane. ADR-0002. |
| D33 | Exactly one approval provider is active | Standalone and ChaseOS-backed deployments share a protocol without mirroring authority. ADR-0003. |
| D34 | Checked promotion migrates to validator-issued receipts | Caller-declared falsifiability is too easy to misuse; migration must preserve current behaviour until callers move. ADR-0004. |
| D35 | A programme review attaches to one offline semantic source bundle | Platform defaults, programme policy, scope exports, precedence, field citations, and human resolutions are reviewed together; any substantive change invalidates review. ADR-0005. |
| D27 | A collector records the shape of a secret, never its value | A lane that copies credentials into the evidence trail creates the problem it was looking for, at scale, into a store that outlives the engagement. |
| D28 | Presence is reported, never reachability | A key in a tree is present; whether it is served depends on the web root, the branch and the build, none of which a directory knows. |
| D26 | Absent dashboard data reports UNKNOWN, never zero | "0 out-of-scope attempts" and "nothing is being recorded" look identical on a screen and mean opposite things. |
| D22 | Mixed currencies are never silently summed | A total that quietly adds dollars to pounds is worse than no total. |
| D19 | Narrowing scope changes are called out separately | A widened scope is an opportunity; a narrowed one means work already done may have been against an asset that is no longer authorised. |
