# Module Breakdown

What exists, what each module is responsible for, and what it is deliberately *not* responsible for.

## Implemented — Plane 1 (Authority) and Plane 3 (Judgement)

| Module | Responsibility | Explicitly not its job |
|---|---|---|
| [`greytheory/provenance.py`](../greytheory/provenance.py) | The observed/checked/inferred triple. Gates promotion on a falsifiable check. | Deciding whether a claim is *true* — only how it came to be believed. |
| [`greytheory/audit.py`](../greytheory/audit.py) | Append-only hash-chained JSONL. Detects edits, reorders and deletions. | Access control on the log file itself; that is the filesystem's job. |
| [`greytheory/authority/scope.py`](../greytheory/authority/scope.py) | `ScopeContract`, pattern matching, staleness, fingerprinting. | DNS resolution. A hostname is not an address and will not be resolved to match a CIDR. |
| [`greytheory/authority/compiler.py`](../greytheory/authority/compiler.py) | Programme source → contract. Fails closed on ambiguity. Hashes the source. | Fetching programme pages. Input arrives as a local record. |
| [`greytheory/authority/sources.py`](../greytheory/authority/sources.py) | Saved `ProgrammeSourceBundle` loading, integrity, capture modes, precedence, field citations, human resolutions, semantic snapshots, and offline compilation. | Fetching sources, interpreting prose, or granting review. |
| [`greytheory/authority/approvals.py`](../greytheory/authority/approvals.py) | Binding, expiry and single-use enforcement over whatever store is in play. | Storing approvals when a platform already owns them. Deciding *whether* to approve — that is the operator's. |
| [`greytheory/authority/gate.py`](../greytheory/authority/gate.py) | The single execution decision. Posture ceiling, approval threshold, kill switch, mandatory audit. | Performing the permitted action. It answers *may this happen*, nothing more. |
| [`greytheory/registry.py`](../greytheory/registry.py) | Versioned programme records, source snapshots, scope drift detection, the attention queue. | Fetching programme pages. Deciding a contract is trustworthy — that is the gate's. |
| [`greytheory/validation.py`](../greytheory/validation.py) | Gates B–F. Deterministic where possible, attested where not. | Submitting. Passing the gates makes a finding *eligible* for Gate G, nothing more. |
| [`greytheory/report.py`](../greytheory/report.py) | Report structure, placeholder detection, markdown rendering. | Writing the report. Structure is enforced; prose is not. |
| [`greytheory/evidence.py`](../greytheory/evidence.py) | Raw/redacted split, hashing, manifests, integrity, export gating, repository guard. | Redacting. Only the operator knows which bytes are sensitive; a regex that thinks it does is worse than nothing. |
| [`greytheory/ledger.py`](../greytheory/ledger.py) | Sessions, triage outcomes, payouts, expenses, and honest metrics. Refuses to forecast below thresholds. | Deciding what a finding was worth, or predicting what the next one will be. |
| [`greytheory/advisories.py`](../greytheory/advisories.py) | OSV import, ecosystem-aware matching, version ordering. | Fetching advisory data. Input is files already on disk. |
| [`greytheory/findings.py`](../greytheory/findings.py) | One finding entity, one lifecycle, internal/external seam. | Assessing severity, or deciding a finding is valid. |
| [`greytheory/dashboard.py`](../greytheory/dashboard.py) | Read model over every store, plus text/HTML/JSON renderers. | Inventing data. Absent stores report unknown, never zero. |
| [`greytheory/cli.py`](../greytheory/cli.py) | Operator surface: compile, review, check, audit-verify, programme, dashboard. | Anything that touches a network. |

## Implemented — Plane 2 (Signal)

| Module | Responsibility | Explicitly not its job |
|---|---|---|
| [`signal/contract.py`](../greytheory/signal/contract.py) | What a lane is: `LaneSpec`, `RawSignal`, the rooted `LaneContext`. | Letting a collector conclude. There is no field above `contextual`. |
| [`signal/runner.py`](../greytheory/signal/runner.py) | The only path by which a collector executes. Gate-mediated, authority-stamped, denials recorded. | Running a lane that declares network I/O. |
| [`signal/lanes/agent_config.py`](../greytheory/signal/lanes/agent_config.py) | Lane 4. Static agent/MCP config review. | Sending prompts or invoking a model. |
| [`signal/lanes/dependency_manifest.py`](../greytheory/signal/lanes/dependency_manifest.py) | Lane 1. Manifest versions vs a local advisory set. | Calling a version match a vulnerability. |
| [`signal/lanes/exposure.py`](../greytheory/signal/lanes/exposure.py) | Lane 2. Credential shapes, VCS metadata, backups and source maps over a local tree. | Recording a secret's value, or claiming presence means reachability. |

### Dependency direction

```
cli ──▶ authority.gate ──▶ authority.scope
 │           │         └──▶ authority.approvals
 │           └──▶ audit
 ├──▶ registry ──▶ authority.sources ──▶ authority.compiler ──▶ authority.scope
 │        └──▶ evidence (repository guard only)
 ├──▶ evidence ──▶ audit
 └──▶ validation ──▶ evidence, findings, report
              └──▶ findings ──▶ provenance
```

Nothing in `authority/` imports `findings` or `evidence`. The gate does not know what a finding is, and does not need to.

### Integration points

Each one ships a self-sufficient default beside it, so nothing external is ever required:

| Point | Standalone default | Optional integration |
|---|---|---|
| Approvals | `LocalApprovalStore` | `ChaseOSApprovalStore` reading OSRIL records |
| Evidence root | Platform user-data directory | `CHASEOS_VAULT_ROOT` → `<vault>/07_LOGS/greytheory-evidence` |
| Ledger root | Platform user-data directory | `CHASEOS_VAULT_ROOT` → `<vault>/07_LOGS/greytheory-ledger` |

Integrations read foreign **filesystem contracts**, never foreign Python packages. That keeps `greytheory` dependency-free and means an upstream refactor breaks a test here rather than the runtime.

## Designed, not built

| Module / package | Layer | Blocked on |
|---|---|---|
| Research workspace and session domain | 2 | Milestone 3 implementation |
| Typed target/asset graph | 3 | Domain object contracts |
| Hypothesis and experiment engine | 5 | Workspace/session domain |
| Validator-issued `CheckReceipt` | 8 | Safe migration of current promotion callers |
| Vulnerability cards and skill graph | 4 | Domain and local-fixture contracts |
| Model gateway | cross-cutting | Research objects and evaluation harness |
| Scope Watch | 1/3 | Network worker and Milestone 8 posture gate |
| Lane 3 and live collectors | 7 | Broker/worker controls and later posture milestones |
| Standalone graphical workbench | 10 | Stable structured domain and query layer |

## Constraints on every module

- **No network in the core.** Enforced in CI, not by convention. When lanes eventually need network access they will live in a separate package that can only act through a `Decision`.
- **No runtime dependencies** in `greytheory/`. Standard library only, so the trust surface of the thing that grants authority stays small.
- **Injected clocks.** Anything time-dependent takes a `clock` callable, so staleness and expiry are testable rather than flaky.
