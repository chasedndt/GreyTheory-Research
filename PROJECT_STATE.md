# Project State

## Project

GreyTheory

## Category

Security Research Operating System

## Definition

GreyTheory is a standalone, local-first, human-governed security research operating system for bug bounty and authorised security testing. Its three-plane control plane is the trust kernel: it converts programme authority into enforceable boundaries and refuses to turn inference into proof.

Canonical identity and capability truth: [`PROJECT_DEFINITION.md`](PROJECT_DEFINITION.md).

## Current stage

- **Completed productisation milestones:** Milestone 1 — Canonical project foundation; Milestone 2 — Real programme compiler; Milestone 3 — structured research domain; Milestone 4 — first end-to-end local vertical slice.
- **Current research milestone:** Milestone 5 — vulnerability cards and skill graph.
- **Operating posture:** `LOCAL_FIXTURE`; no network collector or live-target interaction.
- **Verified baseline:** 420 repository tests passing, including 8 focused Milestone 4 acceptance tests, on 2026-08-09.

## What is built

The complete offline path from supplied authorisation to a validated report draft:

- programme registry plus single-source and multi-source bundle compilation;
- public-source provenance with capture modes, retrieval times, per-source hashes, field citations, structured-export/operator-extract derivation checks, precedence, and human-resolution gates;
- one real saved HackerOne/GitLab bundle containing the official 44-row scope export plus bounded programme/platform policy extracts;
- one real saved Bugcrowd/YNAB bundle whose 3/5 target-group rows derive exactly and whose two prose conflicts correctly block pending human decisions;
- one real saved direct-policy bundle for `modelcontextprotocol/python-sdk`; its immutable verbatim `SECURITY.md` derives the exact 2/1 supported-version split and reaches `PENDING_REVIEW`;
- execution gate with seventeen denial reasons, posture ceiling, and kill switch;
- bound, expiring, single-use approvals;
- hash-chained audit and provenance triple;
- local-only lane runner with three static collectors (dependency, local-tree exposure, agent/MCP configuration);
- offline OSV advisory import;
- raw/redacted evidence vault, validation gates B-F, report studio, finding lifecycle, ledger, dashboard read model, and CLI;
- all ten Milestone 3 research records: workspace, session, typed asset/relationship, controlled identity, hypothesis, experiment plan, action request/receipt, and lesson;
- integrity-checked, atomically persisted local research workspaces with referential validation, repository-storage refusal, explicit lifecycles, contract-bound scope classification, request/time/effect budgets, and optional audit writeback;
- one complete structured-session acceptance proof covering all ten records, gate binding, persistence/reopen, a refuted hypothesis, and a reusable lesson.
- one complete deliberately vulnerable local two-account slice connecting saved training rules, an explicit labelled test-fixture review/attestation record, ownership graph, hypothesis/experiment, gate-bound action execution, observation, validator-issued `CheckReceipt`, raw/redacted evidence, claim-provenance report, postmortem, and proposed vulnerability-card update;
- a one-use check-receipt registry that hashes exact input artifacts and validator code and refuses forged, modified, refuted, mismatched, or already-consumed receipts;
- a CLI demonstration that stops at `report_ready`, records one action receipt for one executed local action, and exposes no submission or network path.

## What is not built

- human resolution of the two recorded YNAB policy conflicts;
- vulnerability cards, curriculum, and skill graph;
- governed model gateway;
- standalone graphical workbench;
- Scope Watch, network broker/workers, and live collectors;
- live research evidence, submissions, or programme outcomes.

## Locked decisions

- GreyTheory is a Security Research Operating System; the control plane is its trust kernel.
- Three ranked planes remain: Authority → Signal → Judgement. Lower planes cannot bypass higher ones.
- Product layers add researcher-facing capability around the planes and may never weaken them.
- GreyTheory governs the operator's own authorised research. Client-agent governance is a derivative product.
- AI reasons, plans, critiques, curates, drafts, and tutors. It does not hold authority, execute directly, create proof, submit, contact, or disclose.
- Every claim is `observed`, `checked`, or `inferred`; no silent promotion.
- An existing observed or inferred claim is promoted to `checked` only by consuming a successful, matching `CheckReceipt` issued by the registry; caller-asserted falsifiability has been removed.
- Legacy static collectors still originate deterministic `checked` claims directly; migrating those origins to persisted receipts is a separate open loop and no model output may use that helper.
- Every action and artifact carries authority. Asset discovery never widens scope.
- Programme outcomes are recorded from external evidence, never self-awarded.
- Raw evidence remains outside repositories; only redacted evidence is exportable.
- GreyTheory is standalone and Apache-2.0. ChaseOS is an optional integration and cannot bypass the gate.
- Core remains minimal and offline; future workers/models/UI may use pinned isolated dependencies outside the trust kernel.
- No external security activity occurs before the explicit posture milestone and all of its testable preconditions.

## Immediate next step

Build Milestone 5's first vulnerability-card contracts and skill graph, starting with the IDOR/BOLA card update proposed by the verified local slice. Keep that proposal non-canonical until the card schema, evidence rules, and six-dimensional mastery tracking are implemented and tested. The posture remains `LOCAL_FIXTURE`; the separate YNAB conflict-resolution gate remains human-owned.

## Do not build next

- mass scanning;
- a general-purpose autonomous browser or shell agent;
- automatic submission or disclosure;
- a ten-agent swarm;
- cloud raw-evidence storage;
- a custom proxy;
- a marketplace or enterprise collaboration surface;
- public claims of live research capability.
