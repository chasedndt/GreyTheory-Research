# GreyTheory Domain Model

> **Status:** IMPLEMENTED / VERIFIED OFFLINE for the Milestone 3 research objects and local store; later graph nodes retain their explicit status below.
>
> **Effective:** 2026-08-09

## Purpose

This model turns GreyTheory from a set of research controls into the structured environment in which a complete research session can happen. It does not grant authority. Every object that describes action or evidence remains subordinate to a verified contract and the Authority Plane.

## Canonical object graph

```text
Programme
└── ProgrammeSourceBundle
    └── ScopeContract
        └── ResearchWorkspace
            ├── ResearchIdentity
            ├── TargetAsset
            ├── AssetRelationship
            ├── ResearchSession
            │   ├── Hypothesis
            │   │   └── ExperimentPlan
            │   │       └── ActionRequest
            │   │           ├── GateDecision
            │   │           ├── ApprovalReference
            │   │           └── ActionReceipt
            │   ├── Observation
            │   ├── Claim
            │   │   └── CheckReceipt
            │   └── EvidenceArtifact
            └── Finding
                └── Report
                    └── SubmissionRecord
                        └── ProgrammeOutcome
                            ├── Retest
                            ├── Lesson
                            └── LedgerEntry
```

## Existing objects

`ProgrammeSourceBundle` (IMPLEMENTED: three source-shape proofs), `ScopeContract`, gate decisions, approvals, observations (`RawSignal`), claims, evidence artifacts, findings, reports, programme outcomes, and ledger entries already exist in narrower forms. Their current implementations remain source truth until migrated deliberately.

## Implemented research objects

### `ResearchWorkspace`

One public programme or authorised engagement. Owns the verified contract reference, posture, research goals, unresolved questions, and workspace-level request/time/effect budgets. The local `ResearchStore` owns its typed child records and stores references to credentials and evidence, never their raw bytes.

### `ResearchSession`

A bounded period of work with one workspace, contract fingerprint, posture, identity set, request/time/effect budget, declared goal, start/end state, and outcome. A completed session must produce checked evidence, a refuted/inconclusive hypothesis, or a reusable lesson.

### `TargetAsset`

A typed canonical asset rather than a free-form hostname. Initial kinds: domain, URL, API, repository, package, application, local fixture, identity provider, role, resource class, agent, tool, and MCP server. An asset carries a scope classification; graph discovery never grants it scope.

### `Hypothesis`

A falsifiable theory with preconditions, actor, action, target, consequence, reasoning, supporting observations, assumptions, required authority, expected safe/vulnerable behaviour, falsifier, evidence needs, stop conditions, estimated cost, duplicate risk, and learning value. It never silently becomes a finding.

### `ExperimentPlan`

The smallest safe procedure capable of supporting or refuting a hypothesis. Contains ordered actions, positive and negative controls, expected outcomes, authority/effect requirements, rollback, stop conditions, and evidence plan. Planning grants nothing; explicit lifecycle transitions are required before an action request can be recorded.

## Additional graph objects

- `ProgrammeSourceBundle` (**IMPLEMENTED / VERIFIED OFFLINE**): all saved policy sources, capture modes, hashes, retrieval times, precedence, field citations, and human conflict resolutions compiled as one authority input. HackerOne/GitLab proves a structured export, Bugcrowd/YNAB proves operator-extracted target groups and fail-closed human conflicts, and the MCP Python SDK proves an immutable verbatim policy with an embedded Markdown support table.
- `ResearchIdentity` (**IMPLEMENTED / VERIFIED OFFLINE**): a controlled role/identity handle with ownership attestation and credential reference, not a credential container.
- `AssetRelationship` (**IMPLEMENTED / VERIFIED OFFLINE**): a typed edge such as `calls`, `trusts`, `owns`, `may_access`, `invokes`, or `sends_data_to`; recording an edge cannot alter scope classification.
- `ActionRequest` (**IMPLEMENTED / VERIFIED OFFLINE**): a structured request for one exact action that can be translated into the existing gate shape but cannot execute itself.
- `ActionReceipt` (**IMPLEMENTED / VERIFIED OFFLINE**): what actually happened, bound to an allowed audited decision, worker, exact target/action/identity, budgets, outputs, and stop state.
- `CheckReceipt` (**PLANNED**): a validator-issued record of a falsifiable assertion and its result.
- `Lesson` (**IMPLEMENTED / VERIFIED OFFLINE**): a structured no-finding/postmortem record and reusable change to research behaviour, card, hypothesis pattern, or target score.

## Invariants

1. Every object is scoped to a workspace or is immutable reference data.
2. Every action and resulting artifact carries the current authority reference.
3. Asset discovery and graph edges never widen scope.
4. Identities use handles; secrets never enter ordinary domain records.
5. Hypotheses remain theories until checks and human judgement support promotion.
6. Plans cannot execute themselves.
7. Receipts describe actual execution, not intent.
8. Checked claims require validator evidence.
9. Programme outcomes are recorded from external evidence, never self-awarded.
10. A session that finds nothing still records time and a lesson or explicit inconclusive result.

## Initial storage direction

The ten objects live in `greytheory/research/domain.py`. `ResearchStore` persists one integrity-digested JSON snapshot per workspace with atomic replacement, repository-storage refusal by default, referential checks, and optional hash-chained audit writeback. Add SQLite indexes only when the object contracts and query patterns stabilise. Continue using content-addressed files for evidence and source snapshots. A graph database is not required.

## Milestone 3 exit condition

**VERIFIED 2026-08-09.** `tests/test_research.py` manages and reopens a complete local session through all ten objects, an allowed gate decision, bounded receipt, refuted hypothesis, and reusable lesson without a generic notes field or network dependency. The focused suite passes 14 tests; the complete repository suite passes 411 tests. Milestone 4 remains responsible for connecting these records to the runner, observations, deterministic checks, evidence vault, validation, and report studio through a deliberately vulnerable fixture.
