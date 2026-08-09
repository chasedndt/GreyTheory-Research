# GreyTheory Domain Model

> **Status:** DESIGNED; implementation is PLANNED unless a type is explicitly marked LIVE or PARTIAL.
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

`ProgrammeSourceBundle` (PARTIAL: one of three real programme proofs), `ScopeContract`, gate decisions, approvals, observations (`RawSignal`), claims, evidence artifacts, findings, reports, programme outcomes, and ledger entries already exist in narrower forms. Their current implementations remain source truth until migrated deliberately.

## Next five domain objects

### `ResearchWorkspace`

One public programme or authorised engagement. Owns the verified contract reference, target model, controlled identities, sessions, hypotheses, evidence links, findings, reports, questions, and budgets. It stores references to credentials and evidence, never their raw bytes.

### `ResearchSession`

A bounded period of work with one workspace, contract fingerprint, posture, identity set, request/time/effect budget, declared goal, start/end state, and outcome. A completed session must produce checked evidence, a refuted/inconclusive hypothesis, or a reusable lesson.

### `TargetAsset`

A typed canonical asset rather than a free-form hostname. Initial kinds: domain, URL, API, repository, package, application, local fixture, identity provider, role, resource class, agent, tool, and MCP server. An asset carries a scope classification; graph discovery never grants it scope.

### `Hypothesis`

A falsifiable theory with preconditions, actor, action, target, consequence, reasoning, supporting observations, assumptions, required authority, expected safe/vulnerable behaviour, falsifier, evidence needs, stop conditions, estimated cost, duplicate risk, and learning value. It never silently becomes a finding.

### `ExperimentPlan`

The smallest safe procedure capable of supporting or refuting a hypothesis. Contains ordered actions, positive and negative controls, expected outcomes, authority/effect requirements, rollback, stop conditions, and evidence plan. Planning grants nothing.

## Following objects

- `ProgrammeSourceBundle` (**IMPLEMENTED / VERIFIED OFFLINE**): all saved policy sources, capture modes, hashes, retrieval times, precedence, field citations, and human conflict resolutions compiled as one authority input. HackerOne/GitLab proves a structured export, Bugcrowd/YNAB proves operator-extracted target groups and fail-closed human conflicts, and the MCP Python SDK proves an immutable verbatim policy with an embedded Markdown support table.
- `ResearchIdentity`: a controlled role/identity handle with ownership attestation and credential reference, not a credential container.
- `AssetRelationship`: a typed edge such as `calls`, `trusts`, `owns`, `may_access`, `invokes`, or `sends_data_to`.
- `ActionRequest`: a structured request for one exact action.
- `ActionReceipt`: what actually happened, bound to decision, worker, target, identity, budgets, outputs, and stop state.
- `CheckReceipt`: a validator-issued record of a falsifiable assertion and its result.
- `Lesson`: a reusable change to research behaviour, card, hypothesis pattern, or target score.

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

Use typed Python objects first. Add SQLite indexes when the object contracts stabilise. Continue using content-addressed files for evidence and source snapshots, and the append-only audit chain for authority-relevant events. A graph database is not required.

## Milestone 3 exit condition

A researcher can manage a complete local session through structured objects without relying on unstructured notes, and no new object can weaken the existing gate, evidence, or provenance rules.
