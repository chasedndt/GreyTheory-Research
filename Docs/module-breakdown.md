# Module Breakdown

What exists, what each module is responsible for, and what it is deliberately *not* responsible for.

## Implemented — Plane 1 (Authority)

| Module | Responsibility | Explicitly not its job |
|---|---|---|
| [`greytheory/provenance.py`](../greytheory/provenance.py) | The observed/checked/inferred triple. Gates promotion on a falsifiable check. | Deciding whether a claim is *true* — only how it came to be believed. |
| [`greytheory/audit.py`](../greytheory/audit.py) | Append-only hash-chained JSONL. Detects edits, reorders and deletions. | Access control on the log file itself; that is the filesystem's job. |
| [`greytheory/authority/scope.py`](../greytheory/authority/scope.py) | `ScopeContract`, pattern matching, staleness, fingerprinting. | DNS resolution. A hostname is not an address and will not be resolved to match a CIDR. |
| [`greytheory/authority/compiler.py`](../greytheory/authority/compiler.py) | Programme source → contract. Fails closed on ambiguity. Hashes the source. | Fetching programme pages. Input arrives as a local record. |
| [`greytheory/authority/gate.py`](../greytheory/authority/gate.py) | The single execution decision. Posture ceiling, kill switch, mandatory audit. | Performing the permitted action. It answers *may this happen*, nothing more. |
| [`greytheory/findings.py`](../greytheory/findings.py) | One finding entity, one lifecycle, internal/external seam. | Assessing severity, or deciding a finding is valid. |
| [`greytheory/cli.py`](../greytheory/cli.py) | Operator surface: compile, review, check, audit-verify. | Anything that touches a network. |

### Dependency direction

```
cli ──▶ authority.gate ──▶ authority.scope
 │           │
 │           └──▶ audit
 ├──▶ authority.compiler ──▶ authority.scope
 └──▶ findings ──▶ provenance
```

Nothing in `authority/` imports `findings`. The gate does not know what a finding is, and does not need to.

## Designed, not built

| Module | Plane | Blocked on |
|---|---|---|
| Evidence vault | 3 | Open question O3 — where raw evidence lives |
| Validation gates A–F | 3 | Evidence vault |
| Report studio | 3 | Validation gates |
| Approval store | 1 | Open question O2 — whether ChaseOS already owns one |
| Programme registry | 1 | Nothing; next natural slice after the vault |

## Aspirational

The four Signal Plane lanes, the curriculum and skill graph, the triage and earnings ledgers, the Grapevine adapter, and any dashboard surface. Architected in `README.md` and `Docs/architecture.md`; none are specified to build-ready detail.

## Constraints on every module

- **No network in the core.** Enforced in CI, not by convention. When lanes eventually need network access they will live in a separate package that can only act through a `Decision`.
- **No runtime dependencies** in `greytheory/`. Standard library only, so the trust surface of the thing that grants authority stays small.
- **Injected clocks.** Anything time-dependent takes a `clock` callable, so staleness and expiry are testable rather than flaky.
