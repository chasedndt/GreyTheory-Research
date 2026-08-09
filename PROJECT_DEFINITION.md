# GreyTheory Project Definition

> **Status:** CANONICAL
>
> **Effective:** 2026-08-09
>
> **Current maturity:** Working offline trust kernel; research operating system partially productised; no live-target capability.

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

Every model output begins as `inferred`. Every executed action must be admitted by the deterministic Authority Plane. Every checked claim must eventually consume a validator-issued `CheckReceipt`; the current caller-supplied falsifiability Boolean is a known migration gap.

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
| 2 | Research Workspace | PLANNED |
| 3 | Target and Asset Graph | PLANNED |
| 4 | Knowledge and Skill System | PLANNED |
| 5 | Hypothesis and Experiment Engine | PLANNED |
| 6 | Execution and Tool Broker | PLANNED; local-only runner exists |
| 7 | Signal and Observation | PARTIAL; three static offline collectors |
| 8 | Evidence, Validation and Reporting | LIVE offline; claim-evidence matrix planned |
| 9 | Outcomes, Economics and Learning | PARTIAL; ledger live, learning loop planned |
| 10 | Workbench and Integrations | PARTIAL; CLI live, workbench planned |

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
- validation gates B-F, report studio, finding lifecycle, ledger, dashboard read model, and CLI.

### PARTIAL / NOT PROVEN AGAINST REAL OPERATION

- one real public HackerOne/GitLab source bundle compiles cleanly to `PENDING_REVIEW` from three saved sources and the official 44-row scope export;
- one real public Bugcrowd/YNAB source bundle derives all rendered target-group rows but compiles to `BLOCKED` because two policy conflicts remain explicitly human-owned;
- one real independently maintained `modelcontextprotocol/python-sdk` security policy compiles from an immutable verbatim source, deriving two supported release lines and one unsupported class exactly before reaching `PENDING_REVIEW`;
- Milestone 2's three-source implementation proof is complete; individual bundle review and conflict states remain authoritative and unchanged;
- approvals have local and ChaseOS stores, but the provider boundary needs one explicit protocol;
- deterministic claim promotion still accepts a caller-supplied falsifiability Boolean;
- the dashboard is a read model, not the planned standalone workbench.

### PLANNED / NOT BUILT

- research workspaces, sessions, typed assets, relationships, and controlled identities;
- hypotheses, experiment plans, action receipts, and lessons;
- validator-issued `CheckReceipt` promotion;
- vulnerability cards, curriculum, and skill graph;
- governed model gateway and evaluation harness;
- Scope Watch, network broker, network workers, and live collectors;
- standalone graphical workbench;
- live research proof and programme outcomes.

## Current stage

Milestones 1 and 2 are complete at their documented implementation/evidence exit conditions. Milestone 3 — the structured research domain — is current and culminates in a local two-account authorisation vertical slice in Milestone 4.

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
