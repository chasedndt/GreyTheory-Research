# Project State

## Project

GreyTheory

## Category

Security Research Operating System

## Definition

GreyTheory is a standalone, local-first, human-governed security research operating system for bug bounty and authorised security testing. Its three-plane control plane is the trust kernel: it converts programme authority into enforceable boundaries and refuses to turn inference into proof.

Canonical identity and capability truth: [`PROJECT_DEFINITION.md`](PROJECT_DEFINITION.md).

## Current stage

- **Completed productisation milestones:** Milestone 1 — Canonical project foundation; Milestone 2 — Real programme compiler; Milestone 3 — structured research domain; Milestone 4 — first end-to-end local vertical slice; Milestone 5 — vulnerability cards and skill graph.
- **Current research milestone:** Milestone 6 — transparent hypothesis ranking and research queue.
- **Operating posture:** `LOCAL_FIXTURE`; no network collector or live-target interaction.
- **Verified baseline:** 430 repository tests passing, including 10 focused Milestone 5 and 8 Milestone 4 acceptance tests, on 2026-08-09.

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
- twelve versioned first-class vulnerability cards covering reflected/stored/DOM XSS, SQL injection, CSRF, SSRF, IDOR/BOLA, BFLA, session management, business-logic authorisation, indirect prompt injection, and tool-authorisation failure;
- one distinct synthetic, network-free local fixture per card, each executed through positive, vulnerable, and negative-control paths and producing a runner/fixture-digested receipt that explicitly proves no real vulnerability and awards no mastery;
- an acyclic card-prerequisite skill graph with separate `explain`, `recognise`, `test`, `prove`, `remediate`, and `transfer` dimensions;
- an integrity-checked private `MasteryStore` that refuses repository storage, requires explicit evidence and review dates, credits only human assessments, and keeps labelled test-fixture assessments non-crediting;
- offline CLI catalogue, fixture-verification, mastery-status, and evidence-bound assessment commands;
- the Milestone 4 BOLA proposal applied to `idor-bola` v1.0.0 as an explicitly `test_fixture`-sourced revision, without inventing a real session or human mastery record.

## What is not built

- human resolution of the two recorded YNAB policy conflicts;
- transparent hypothesis ranking and research-queue decision support;
- guided, assisted, assessment, and transfer training orchestration, adaptive review scheduling, and broader curriculum packs beyond the first 12 cards;
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
- Framework mappings classify a card; they never prove a vulnerability, impact, severity, or mastery.
- Synthetic fixture receipts prove only the shipped local scenario and its controls. They cannot become real-session evidence or mastery credit.
- Mastery is six separate evidence-bound human assessments; completing a lab or receiving model output awards nothing automatically.
- Every action and artifact carries authority. Asset discovery never widens scope.
- Programme outcomes are recorded from external evidence, never self-awarded.
- Raw evidence remains outside repositories; only redacted evidence is exportable.
- GreyTheory is standalone and Apache-2.0. ChaseOS is an optional integration and cannot bypass the gate.
- Core remains minimal and offline; future workers/models/UI may use pinned isolated dependencies outside the trust kernel.
- No external security activity occurs before the explicit posture milestone and all of its testable preconditions.

## Immediate next step

Build Milestone 6 as transparent decision support over existing hypotheses. Rank without executing or calling anything a vulnerability, explain every factor, and keep missing or ambiguous scope confidence fail-closed. The posture remains `LOCAL_FIXTURE`; the separate YNAB conflict-resolution gate remains human-owned.

## Do not build next

- mass scanning;
- a general-purpose autonomous browser or shell agent;
- automatic submission or disclosure;
- a ten-agent swarm;
- cloud raw-evidence storage;
- a custom proxy;
- a marketplace or enterprise collaboration surface;
- public claims of live research capability.
