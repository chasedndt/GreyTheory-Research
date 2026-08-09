# Project State

## Project

GreyTheory

## Category

Security Research Operating System

## Definition

GreyTheory is a standalone, local-first, human-governed security research operating system for bug bounty and authorised security testing. Its three-plane control plane is the trust kernel: it converts programme authority into enforceable boundaries and refuses to turn inference into proof.

Canonical identity and capability truth: [`PROJECT_DEFINITION.md`](PROJECT_DEFINITION.md).

## Current stage

- **Completed productisation milestone:** Milestone 1 — Canonical project foundation.
- **Current research milestone:** Milestone 2 — compile three real public programme source bundles without contacting targets.
- **Operating posture:** `LOCAL_FIXTURE`; no network collector or live-target interaction.
- **Verified baseline:** 347 tests passing at the 2026-08-09 foundation preflight.

## What is built

The complete offline path from supplied authorisation to a validated report draft:

- programme registry and single-source scope compiler;
- execution gate with seventeen denial reasons, posture ceiling, and kill switch;
- bound, expiring, single-use approvals;
- hash-chained audit and provenance triple;
- local-only lane runner with three static collectors (dependency, local-tree exposure, agent/MCP configuration);
- offline OSV advisory import;
- raw/redacted evidence vault, validation gates B-F, report studio, finding lifecycle, ledger, dashboard read model, and CLI.

## What is not built

- real `ProgrammeSourceBundle` ingestion and three-programme proof;
- research workspaces, sessions, typed assets/relationships, and controlled identities;
- hypothesis and experiment engine;
- action and validator-issued check receipts;
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
- A future `CheckReceipt` replaces caller-asserted falsifiability without weakening current callers during migration.
- Every action and artifact carries authority. Asset discovery never widens scope.
- Programme outcomes are recorded from external evidence, never self-awarded.
- Raw evidence remains outside repositories; only redacted evidence is exportable.
- GreyTheory is standalone and Apache-2.0. ChaseOS is an optional integration and cannot bypass the gate.
- Core remains minimal and offline; future workers/models/UI may use pinned isolated dependencies outside the trust kernel.
- No external security activity occurs before the explicit posture milestone and all of its testable preconditions.

## Immediate next step

Begin Milestone 2 with one saved public programme source bundle. Record compiler blocks and human resolutions; add only the policy shapes real sources prove are necessary. Do not contact a target.

## Do not build next

- mass scanning;
- a general-purpose autonomous browser or shell agent;
- automatic submission or disclosure;
- a ten-agent swarm;
- cloud raw-evidence storage;
- a custom proxy;
- a marketplace or enterprise collaboration surface;
- public claims of live research capability.
