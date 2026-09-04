# ChaseOS Reconciliation

Historical reconciliation from 2026-08-06: does ChaseOS already own an approval layer, audit log, or knowledge graph that GreyTheory can adapt to rather than duplicate?

**Answer: yes to all three.** Read on 2026-08-06 against `C:/Users/chaseos/Documents/Projects/chaseos-core`.

## Reconciliation table

| Capability | ChaseOS status | Location | GreyTheory decision |
|---|---|---|---|
| Approval request/response | **LIVE** | `runtime/operator_surface/approvals.py` — `ApprovalRequest`, `ApprovalResponse`, `ApprovalDenied`, `ApprovalTimeout` | **Adapt.** Optional ChaseOS provider; standalone local provider remains first-class. |
| Durable approval records | **LIVE** | `runtime/osril/approvals.py` — writes `<vault>/runtime/osril/approvals/<id>.response.json`, with duplicate-response rejection and pending-event matching | **Import.** Read via `ChaseOSApprovalStore`. |
| Immutable approval record type | **LIVE** | `runtime/operator_surface/contracts.py` — `ApprovalRecord` | **Import.** Field names mirrored. |
| Approval packets for subagents | **LIVE** | `runtime/subagents/approval_packet.py` | Not needed yet. |
| Run audit artifacts | **LIVE** | `runtime/operator_surface/audit.py` — `OperatorRunAudit` → `07_LOGS/Agent-Activity/*.json` | **Coexist.** See divergence below. |
| Knowledge graph | **LIVE** | `runtime/graph/` — builder, index, query, resolver, diff, topology, advisory, artifact | **Import when needed.** GreyTheory builds no graph. |
| Memory subsystem | **LIVE** | `runtime/memory/` | Not needed yet. |
| Permission matrix | **LIVE** (doc) | `kernel/PERMISSION_MATRIX.md`, `06_AGENTS/Permission-Matrix.md` | Align posture ceiling against it. |
| Approval governance docs | **LIVE** | `docs/governance/Approval-Center.md`, `templates/governance/Approval-{Request,Decision}-Template.md` | Reference, do not restate. |
| Scope contract compiler | **ABSENT** | — | **Build here.** Now live in GreyTheory. |
| Provenance triple | **ABSENT** | — | **Build here.** Now live in GreyTheory. |
| Tamper-evident audit | **ABSENT** | — | **Build here.** See below. |

`chaser-agent` was also checked: it contains no approval, audit or graph implementation of its own.

## What GreyTheory did as a result

In a ChaseOS-backed deployment, `greytheory/authority/approvals.py` reads ChaseOS OSRIL responses and adds three enforcement properties the decision record alone does not provide:

- **Binding** — an approval covers one `action_type` on one `target`. Approval to read is not approval to delete, and an approval against one asset does not carry to another. An unbound approval covers nothing.
- **Expiry** — 8-hour default window. Consent from last week is not consent now.
- **Single use** — a spent approval cannot be replayed. Enforced against the audit log rather than a second ledger, since the log already records every allow.

### Coupling choice

The ChaseOS store is read through its **filesystem contract**, not by importing `runtime.osril`. GreyTheory currently declares `ApprovalStore` as a `Protocol` and ships `ChaseOSApprovalStore` and `LocalApprovalStore`.

The accepted 2026-08-09 product boundary is an explicit `ApprovalProvider` protocol with exactly one active provider per deployment. The current stores remain LIVE until that migration. Approvals must never be mirrored between providers. See [`../INTEGRATION_BOUNDARIES.md`](../INTEGRATION_BOUNDARIES.md) and ADR-0003.

This keeps `greytheory` dependency-free and usable outside a ChaseOS vault, and means a ChaseOS refactor breaks a test here rather than the runtime. The cost is that the path and JSON field names are duplicated knowledge — `test_approvals.py::TestChaseOSStore` writes the format ChaseOS writes, so drift surfaces as a failing test.

## Divergence worth acting on

**ChaseOS run audits are not tamper-evident.** `runtime/operator_surface/audit.py` writes one JSON file per run to `07_LOGS/Agent-Activity/`. Any of those files can be edited, replaced or deleted afterwards with nothing detecting it.

GreyTheory's `audit.py` hash-chains every record, so an edit, reorder or deletion breaks `verify()`.

The two logs answer different questions — ChaseOS records *what a run did*, GreyTheory records *what was authorised* — so both should exist. But for a system whose entire premise is that authority can be proven after the fact, an editable log is a weak link. **Recommendation:** port the chaining approach into ChaseOS's audit writer. It is roughly 40 lines and needs no schema change; a `prev_hash` and `hash` field on the existing artifact would do it.

This is logged as an internal trust-engineering transfer, exactly the Mission B pattern the handover describes: an external research discipline (evidence integrity) becoming an internal control.

## Still open

- ~~O1 — Grapevine AI~~ **Cut.** No implementation was found and the source document admitted it had never seen one. Restated as Scope Watch in roadmap Milestone 8.
- ~~O3 — evidence storage location~~ **Resolved.** Standalone platform data root or optional `CHASEOS_VAULT_ROOT`, always outside repositories; see `evidence-policy.md`.
