# GreyTheory Domain Model

> **Status:** IMPLEMENTED / VERIFIED OFFLINE through the Milestone 6 transparent-ranking layer; later graph nodes retain their explicit status below.
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
            │   │   ├── HypothesisRankingInput
            │   │   ├── RankedHypothesis
            │   │   │   └── ResearchQueue
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

The learning graph is reference knowledge plus private operator state, not a
child of one programme workspace:

```text
VulnerabilityCatalogue
├── VulnerabilityCard
│   ├── HypothesisTemplate
│   ├── EvidenceRequirement
│   ├── LocalTrainingFixture
│   └── CardRevision
└── SkillGraph
    ├── prerequisite edges
    └── MasteryAssessment × six independent dimensions
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

### `HypothesisRankingInput`, `RankingPolicy`, and `ResearchQueue`

`HypothesisRankingInput` records the five judgement factors that cannot be
derived safely—likelihood, potential impact, duplicate risk, skill value, and
target-specific novelty—with ordinal levels, rationale, provenance, uncertainty,
and an explicit operator or test-fixture source. `RankingPolicy` versions all
nine factor directions, weights, and conservative effect-risk mappings.
`ResearchQueue` binds policy, catalogue, workspace, and verified-contract
digests; explains every contribution; partitions scope-review items; and
self-verifies its integrity. It contains unproven theories and no executable
request.

## Additional graph objects

- `ProgrammeSourceBundle` (**IMPLEMENTED / VERIFIED OFFLINE**): all saved policy sources, capture modes, hashes, retrieval times, precedence, field citations, and human conflict resolutions compiled as one authority input. HackerOne/GitLab proves a structured export, Bugcrowd/YNAB proves operator-extracted target groups and fail-closed human conflicts, and the MCP Python SDK proves an immutable verbatim policy with an embedded Markdown support table.
- `ResearchIdentity` (**IMPLEMENTED / VERIFIED OFFLINE**): a controlled role/identity handle with ownership attestation and credential reference, not a credential container.
- `AssetRelationship` (**IMPLEMENTED / VERIFIED OFFLINE**): a typed edge such as `calls`, `trusts`, `owns`, `may_access`, `invokes`, or `sends_data_to`; recording an edge cannot alter scope classification.
- `ActionRequest` (**IMPLEMENTED / VERIFIED OFFLINE**): a structured request for one exact action that can be translated into the existing gate shape but cannot execute itself.
- `ActionReceipt` (**IMPLEMENTED / VERIFIED OFFLINE**): what actually happened, bound to an allowed audited decision, worker, exact target/action/identity, budgets, outputs, and stop state.
- `CheckReceipt` (**IMPLEMENTED / VERIFIED OFFLINE**): a registry-issued, single-use record of validator/version, exact input artifact hashes, assertion, possible and actual outcomes, issue time, validator runner digest, and authority reference. Only a successful matching receipt can promote its assertion to `checked`.
- `Lesson` (**IMPLEMENTED / VERIFIED OFFLINE**): a structured no-finding/postmortem record and reusable change to research behaviour, card, hypothesis pattern, or target score.
- `VulnerabilityCard` (**IMPLEMENTED / VERIFIED OFFLINE**): versioned reference knowledge with framework classifications, mental/security models, root causes, signals, falsifiable templates, both controls, minimum evidence, false-positive/impact boundaries, minimum-impact rules, remediation, programme-policy constraints, one local fixture, review date, lessons, and revision provenance.
- `LocalTrainingFixture` / `FixtureRunReceipt` (**IMPLEMENTED / VERIFIED OFFLINE**): distinct synthetic boundary simulations for all 12 cards. Receipts bind fixture and runner digests and prove only the shipped local scenario; they are explicitly not real-vulnerability evidence and do not credit mastery.
- `SkillGraph` / `MasteryAssessment` (**IMPLEMENTED / VERIFIED OFFLINE**): acyclic card prerequisites and separately measured `explain`, `recognise`, `test`, `prove`, `remediate`, and `transfer` state. Only explicit evidence-bound human assessments credit mastery; test-fixture records are non-crediting.
- `HypothesisRankingInput` / `RankingPolicy` / `ResearchQueue` (**IMPLEMENTED / VERIFIED OFFLINE**): exact nine-factor ordinal decision support over existing hypotheses. Four factors are derived from trusted scope/workspace records, five require explicit provenance-rich assessment, and every score contribution is explained. The queue grants no execution or finding authority.

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
11. Framework mappings classify knowledge and never prove validity, impact, severity, or mastery.
12. Completing or verifying a fixture does not award mastery.
13. Personal mastery state stays outside repositories by default and is integrity-bound to one catalogue revision.
14. A ranking score changes queue order only; it is never probability, severity, proof, a vulnerability label, or authority.
15. Scope uncertainty is fail-closed into a separate review partition, never compensated for by other high scores.
16. Ranking cannot create actions, receipts, checked claims, findings, model calls, or lifecycle promotions.

## Initial storage direction

The ten research objects live in `greytheory/research/domain.py`. `ResearchStore` persists one integrity-digested JSON snapshot per workspace with atomic replacement, repository-storage refusal by default, referential checks, and optional hash-chained audit writeback. Versioned learning reference data ships under `greytheory/learning/data/`; `MasteryStore` persists personal assessment records outside Git with an integrity envelope and catalogue digest. Ranking contracts and the engine live under `greytheory/hypothesis/`; queue artifacts are integrity-digested, atomically written to private storage, and refused inside Git. Add SQLite indexes only when the object contracts and query patterns stabilise. Continue using content-addressed files for evidence and source snapshots. A graph database is not required.

## Milestone 3 exit condition

**VERIFIED 2026-08-09.** `tests/test_research.py` manages and reopens a complete local session through all ten objects, an allowed gate decision, bounded receipt, refuted hypothesis, and reusable lesson without a generic notes field or network dependency.

## Milestone 4 exit condition

**VERIFIED 2026-08-09.** `tests/test_vertical_slice.py` and the `greytheory demo local-two-account` command connect saved training rules and an explicit review/attestation record to a `LOCAL_FIXTURE` contract, workspace, two controlled identities, explicit ownership edges, BOLA hypothesis/experiment, audited gate allow, exactly one in-memory action and action receipt, observation, validator-issued check receipt, raw/redacted evidence, a provenance-linked `report_ready` draft, postmortem, and proposed vulnerability-card update. Acceptance uses statements labelled `test_fixture`, not a claim that a human made those judgements. The denial proof produces no receipt or evidence, forged/refuted receipts cannot promote claims, and the slice imports no network clients. The focused suite passes 8 tests; the repository passed 420 at the Milestone 4 exit and now passes 430 after Milestone 5. The proposal is now represented by a labelled test-fixture revision of the IDOR/BOLA card. No submission occurs and the posture does not change.

## Milestone 5 exit condition

**VERIFIED 2026-08-09.** `tests/test_learning.py` loads exactly 12 versioned cards, validates their falsifiable templates and minimum-evidence roles, executes one distinct positive/vulnerable/negative-control local fixture per card, verifies an acyclic prerequisite graph, and tracks all 72 card/dimension states. Human evidence updates only the selected dimension; fixture completion and labelled test-fixture assessments award no mastery. The BOLA proposal resolves to exactly one `test_fixture`-sourced canonical revision. The focused Milestone 5 suite passes 10 tests and the complete repository passes 430. No model, network, process, credential, target, or submission path is present.

## Milestone 6 exit condition

**VERIFIED 2026-08-09.** `tests/test_hypothesis_engine.py` proves the exact nine-factor policy, direction and weight semantics, stable deterministic ordering, all-factor explanation arithmetic, queue integrity, contract/workspace binding, explicit assessment provenance, conservative scope partitioning, and refusal of caller-scored derived factors or model-sourced assessments. The synthetic proof ranks three unproven local theories and records zero execution requests, receipts, network calls, model calls, or external targets. The focused suite passes 13 tests and the complete repository passes 443. No item is called a vulnerability and no score grants authority.
