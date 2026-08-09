# ADR-0003 — Exactly One Approval Provider

- Date: 2026-08-09
- Status: ACCEPTED; migration PLANNED

## Decision

Standalone and ChaseOS-backed deployments share one `ApprovalProvider` protocol. Exactly one provider is active, and approvals are never mirrored between stores.

## Consequences

The current `LocalApprovalStore` and `ChaseOSApprovalStore` remain live until the protocol migration. ChaseOS stays optional and cannot widen GreyTheory authority.

