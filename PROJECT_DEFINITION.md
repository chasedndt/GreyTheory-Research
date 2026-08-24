# GreyTheory Project Definition

> **Status:** CANONICAL
>
> **Effective:** 2026-08-25
>
> **Current maturity:** Working offline trust and research kernel with governed learning, transparent hypothesis ranking, model gateway, offline Scope Watch, and a workbench foundation; no live-target capability.

## Identity

**GreyTheory is a standalone, local-first, human-governed security research operating system for bug bounty and authorised security testing.** It compiles programme rules into enforceable research boundaries, uses bounded AI roles to turn observations into falsifiable hypotheses and controlled experiments, and turns every research session into provenance-backed evidence, a defensible report, or a reusable lesson.

- Product line: **From scope to proof.**
- Technical line: **Every action authorised. Every claim traceable.**
- Brand line: **Research under authority. Evidence by construction.**
- Primary user: an independent security learner and researcher.
- Primary specialisation: web/API authorisation and business-logic testing.
- Differentiated specialisation: agentic-AI application security.

The three-plane control plane remains the constitutional and evidentiary kernel. The product category now names the complete environment being built around that kernel: a **Security Research Operating System**.

## Core promise

Convert programme authority into controlled research, and controlled research into proof or reusable knowledge.

```text
Authorise
→ Model
→ Hypothesise
→ Plan
→ Gate
→ Execute
→ Observe
→ Check
→ Prove
→ Report
→ Learn
```

## Operating model

GreyTheory is:

- local-first and standalone;
- bounded-agentic and human-governed;
- fail-closed on missing, stale, ambiguous, or conflicting authority;
- structured around falsifiable hypotheses and minimum-impact experiments;
- explicit about the difference between observation, deterministic proof, and inference;
- useful whether a session produces a finding, a refutation, or a reusable lesson.

GreyTheory is not:

- an autonomous submitter;
- a mass scanner;
- a validity or legal decision-maker;
- a system that infers new scope from discovered assets;
- a cloud store for raw evidence;
- a client-agent governance product inside the core;
- a source of payout guarantees.

## Authority and AI boundaries

AI may organise programme material, map assets, propose and rank hypotheses, prepare experiments, critique claims, curate supported evidence, draft reports, tutor, and extract postmortem lessons.

AI may not verify a contract, expand scope, reinterpret a denial, execute directly, create an approval, promote its own output to `checked`, decide validity or impact, submit, contact a programme, disclose, or access third-party data to strengthen a proof.

Every model output begins as `inferred`. Every executed action must be admitted by the deterministic Authority Plane. Promoting existing model or human output to `checked` must consume a successful, matching `CheckReceipt` issued by a registered deterministic validator; callers cannot assert their own falsifiability. Legacy static-collector origins remain an explicit migration boundary rather than a route for model promotion.

## Architecture

### Trust planes

1. **Authority** — may this happen?
2. **Signal** — what did a collector observe?
3. **Judgement** — what does the evidence mean, and is it sendable?

Lower planes cannot bypass higher ones. Signal collectors remain capped at `contextual`.

### Product layers

| Layer | Capability | Status |
|---|---|---|
| 0 | Trust Kernel | LIVE |
| 1 | Programme and Authority Intelligence | PARTIAL |
| 2 | Research Workspace | LIVE offline; structured store and sessions verified |
| 3 | Target and Asset Graph | LIVE offline; typed assets/edges, scope-neutral discovery |
| 4 | Knowledge and Skill System | LIVE offline for 12 cards, synthetic fixtures, skill graph, evidence-bound mastery, deterministic guided/review planning, and persisted staged journeys; adaptive and specialised modes remain partial |
| 5 | Hypothesis and Experiment Engine | LIVE offline; explicit lifecycles/budgets plus explained nine-factor ranking and private research queue |
| 6 | Execution and Tool Broker | LIVE for one bounded in-memory `LOCAL_FIXTURE` action; network broker/workers not built |
| 7 | Signal and Observation | PARTIAL; three static offline collectors |
| 8 | Evidence, Validation and Reporting | LIVE offline; validator receipts and claim-evidence matrix verified in the local slice |
| 9 | Outcomes, Economics and Learning | PARTIAL; ledger, lessons, card revisions, and mastery records live; adaptive learning loop planned |
| 10 | Workbench and Integrations | PARTIAL; CLI, static read model, executable capability register, application architecture, versioned snapshots, and bounded learning handlers live; transport and interactive workbench planned |

Planes define trust boundaries. Layers define the capabilities a researcher uses. A layer may never weaken a plane.

## Current capability truth

### LIVE / VERIFIED BY THE CURRENT TEST SUITE

- programme registry plus single-source and multi-source bundle compilation;
- offline `ProgrammeSourceBundle` integrity, source capture modes, retrieval metadata, field citations, structured-export/operator-extract derivation checks, precedence, and human-resolution gates;
- fail-closed execution gate with seventeen denial reasons, posture ceiling, and kill switch;
- bound, expiring, single-use approval enforcement;
- hash-chained audit log;
- `observed` / `checked` / `inferred` provenance;
- local-only collector framework;
- static dependency, local-tree exposure, and agent/MCP configuration collectors;
- offline OSV import;
- evidence vault with raw/redacted separation and repository guard;
- validation gates B-F, report studio, finding lifecycle, ledger, dashboard read model, and CLI;
- authority-bound workspaces, sessions, typed assets/relationships, controlled identity handles, hypotheses, experiment plans, action requests/receipts, and structured lessons;
- a private local research store with atomic integrity-digested snapshots, referential validation, explicit lifecycle/budget rules, and optional audit writeback.
- one complete deliberately vulnerable two-account `LOCAL_FIXTURE` slice from saved rules through a `report_ready` finding, postmortem, and proposed card update;
- registry-issued, single-use `CheckReceipt` promotion with exact input hashes, validator/version, possible and actual outcomes, runner digest, time, and authority reference;
- report claim matrices that bind every represented assertion to provenance and evidence references.
- twelve built-in versioned vulnerability cards, each with a falsifiable hypothesis template, explicit minimum-evidence roles, policy/minimum-impact boundaries, and a distinct synthetic local fixture;
- a network-free fixture runner whose receipts bind the fixture and runner digests, prove both controls plus the deliberately vulnerable case, and explicitly award neither real-vulnerability status nor mastery;
- an acyclic prerequisite graph and six-dimensional mastery model (`explain`, `recognise`, `test`, `prove`, `remediate`, `transfer`) backed by an integrity-checked private store;
- explicit mastery governance: only evidence-bound human assessments credit mastery; labelled test-fixture assessments remain visible but non-crediting;
- deterministic guided-learning recommendations with prerequisite routing, due-review priority, explicit review intervals, Learn/Practise/Prove/Reflect/Assess stage requirements, integrity-checked private journey persistence, optimistic revisions, and a CLI workflow; journey completion never awards mastery;
- the Milestone 4 `card-update-local-bola-v1` proposal applied to canonical `idor-bola` v1.0.0 with `test_fixture` revision provenance and no real-session claim.
- a versioned conservative nine-factor ranking policy, deterministic engine, and integrity-checked private research queue that explains every score, partitions uncertain scope, labels every item `unproven`, and carries no execution authority;
- a governed offline model gateway with role/data ceilings, citation checks, budget enforcement, inferred provenance, and an eight-case adversarial evaluation harness;
- offline Scope Watch comparison and review invalidation through the exact rooted `LocalSourceFetcher`, with no network fetcher escape hatch;
- an executable capability register shared by dashboard and future workbench surfaces, including explicit `UNAVAILABLE` boundaries for Lane 3, governed external collection, and `PASSIVE_HTTP`.
- a transport-neutral workbench application service with versioned fail-closed snapshots across the existing stores, stable next-action/context records, idempotent revision-bound learning handlers, and structural refusal of posture above `LOCAL_FIXTURE` or any claim of execution.

### PARTIAL / NOT PROVEN AGAINST REAL OPERATION

- one real public HackerOne/GitLab source bundle compiles cleanly to `PENDING_REVIEW` from three saved sources and the official 44-row scope export;
- one real public Bugcrowd/YNAB source bundle derives all rendered target-group rows but compiles to `BLOCKED` because two policy conflicts remain explicitly human-owned;
- one real independently maintained `modelcontextprotocol/python-sdk` security policy compiles from an immutable verbatim source, deriving two supported release lines and one unsupported class exactly before reaching `PENDING_REVIEW`;
- Milestone 2's three-source implementation proof is complete; individual bundle review and conflict states remain authoritative and unchanged;
- approvals have local and ChaseOS stores, but the provider boundary needs one explicit protocol;
- promotion of existing observed/inferred claims uses registry-issued receipts, while legacy static collectors still originate their own deterministic `checked` claims pending persisted receipt artifacts;
- the dashboard remains a static export, not the planned standalone workbench; the separate application service can now assemble UI-neutral snapshots and operate bounded learning journeys, but no transport or interactive shell exists and research/action/report handlers remain refused;
- the local executor supports only the deliberately vulnerable in-memory fixture; it is not a network broker or live collector.
- the knowledge/skill layer now has a deterministic guided/review journey and explicit human-assessment completion, but not adaptive scheduling, assisted or transfer-specific journeys, broader curriculum packs, or the graphical Learn surface.

### PLANNED / NOT BUILT

- adaptive review scheduling, assisted and transfer-specific orchestration, and broader curriculum packs;
- governed external Scope Watch collector, network broker, network workers, and live collectors;
- standalone graphical workbench;
- live research proof and programme outcomes.

## Current stage

Milestones 1 through 7 are complete and Milestone 8 is complete for its offline portion at their documented implementation/evidence exit conditions. Milestone 9 remains the next research milestone and is gated on the posture decision and broker controls. In parallel, the product workbench foundation is in progress under `LOCAL_FIXTURE`: architecture, executable capability truth, UI-neutral application snapshots, and bounded learning handlers exist, while transport and the interactive shell await visual selection and implementation. The ranking queue remains decision support only: its ordinal scores are not probability, severity, proof, vulnerability status, or authority to execute. The Milestone 4 IDOR/BOLA proposal is represented by `idor-bola` v1.0.0 as a test-fixture-sourced revision; it does not claim a real session or human mastery.

The operating posture remains `LOCAL_FIXTURE`. No external scanning or live-target interaction is authorised or implemented.

## Standalone and ChaseOS relationship

GreyTheory must be complete without ChaseOS. ChaseOS may provide operator identity, approval presentation, scheduling, notifications, orchestration, task management, and graph mirroring. It cannot bypass GreyTheory's gate or widen GreyTheory authority.

## Source hierarchy

1. `PROJECT_DEFINITION.md` — project identity, boundaries, capability truth.
2. `Docs/scope-policy.md` — current operating authority; it wins on what may happen now.
3. `DOMAIN_MODEL.md`, `AUTONOMY_MODEL.md`, `DATA_POLICY.md`, `THREAT_MODEL.md`, and `INTEGRATION_BOUNDARIES.md` — canonical designed state for their subjects.
4. `Docs/roadmap.md` — implementation order and exit conditions.
5. `Docs/definition.md` — detailed trust-kernel definition and decision history.
6. Other current documentation.
7. `Docs/full-brief.md` and `Docs/architecture.md` — historical snapshots where marked.
