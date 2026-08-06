# Module Breakdown

What exists, what each module is responsible for, and what it is deliberately *not* responsible for.

## Implemented — Plane 1 (Authority)

| Module | Responsibility | Explicitly not its job |
|---|---|---|
| [`greytheory/provenance.py`](../greytheory/provenance.py) | The observed/checked/inferred triple. Gates promotion on a falsifiable check. | Deciding whether a claim is *true* — only how it came to be believed. |
| [`greytheory/audit.py`](../greytheory/audit.py) | Append-only hash-chained JSONL. Detects edits, reorders and deletions. | Access control on the log file itself; that is the filesystem's job. |
| [`greytheory/authority/scope.py`](../greytheory/authority/scope.py) | `ScopeContract`, pattern matching, staleness, fingerprinting. | DNS resolution. A hostname is not an address and will not be resolved to match a CIDR. |
| [`greytheory/authority/compiler.py`](../greytheory/authority/compiler.py) | Programme source → contract. Fails closed on ambiguity. Hashes the source. | Fetching programme pages. Input arrives as a local record. |
| [`greytheory/authority/approvals.py`](../greytheory/authority/approvals.py) | Binding, expiry and single-use enforcement over whatever store is in play. | Storing approvals when a platform already owns them. Deciding *whether* to approve — that is the operator's. |
| [`greytheory/authority/gate.py`](../greytheory/authority/gate.py) | The single execution decision. Posture ceiling, approval threshold, kill switch, mandatory audit. | Performing the permitted action. It answers *may this happen*, nothing more. |
| [`greytheory/registry.py`](../greytheory/registry.py) | Versioned programme records, source snapshots, scope drift detection, the attention queue. | Fetching programme pages. Deciding a contract is trustworthy — that is the gate's. |
| [`greytheory/validation.py`](../greytheory/validation.py) | Gates B–F. Deterministic where possible, attested where not. | Submitting. Passing the gates makes a finding *eligible* for Gate G, nothing more. |
| [`greytheory/report.py`](../greytheory/report.py) | Report structure, placeholder detection, markdown rendering. | Writing the report. Structure is enforced; prose is not. |
| [`greytheory/evidence.py`](../greytheory/evidence.py) | Raw/redacted split, hashing, manifests, integrity, export gating, repository guard. | Redacting. Only the operator knows which bytes are sensitive; a regex that thinks it does is worse than nothing. |
| [`greytheory/findings.py`](../greytheory/findings.py) | One finding entity, one lifecycle, internal/external seam. | Assessing severity, or deciding a finding is valid. |
| [`greytheory/cli.py`](../greytheory/cli.py) | Operator surface: compile, review, check, audit-verify. | Anything that touches a network. |

### Dependency direction

```
cli ──▶ authority.gate ──▶ authority.scope
 │           │         └──▶ authority.approvals
 │           └──▶ audit
 ├──▶ registry ──▶ authority.compiler ──▶ authority.scope
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

Integrations read foreign **filesystem contracts**, never foreign Python packages. That keeps `greytheory` dependency-free and means an upstream refactor breaks a test here rather than the runtime.

## Designed, not built

| Module | Plane | Blocked on |
|---|---|---|
| Dashboard read model | 1/3 | Open question O10 — operator's panel specification |

## Aspirational

The four Signal Plane lanes, the curriculum and skill graph, the triage and earnings ledgers, the Grapevine adapter, and any dashboard surface. Architected in `README.md` and `Docs/architecture.md`; none are specified to build-ready detail.

## Constraints on every module

- **No network in the core.** Enforced in CI, not by convention. When lanes eventually need network access they will live in a separate package that can only act through a `Decision`.
- **No runtime dependencies** in `greytheory/`. Standard library only, so the trust surface of the thing that grants authority stays small.
- **Injected clocks.** Anything time-dependent takes a `clock` callable, so staleness and expiry are testable rather than flaky.
