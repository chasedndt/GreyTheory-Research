# GreyTheory Integration Boundaries

> **Status:** CANONICAL boundary; provider/application contracts are implemented offline and network-worker deployment remains planned.
>
> **Effective:** 2026-08-26

## Standalone rule

GreyTheory must be complete without ChaseOS. Core research semantics, authority decisions, workspaces, hypotheses, evidence, findings, reports, outcomes, and local approvals belong to GreyTheory.

## ChaseOS relationship

ChaseOS may provide operator identity, approval presentation, scheduling, notifications, orchestration, task management, and knowledge-graph mirroring. It may request work, but it cannot bypass GreyTheory's gate or override an expired contract, out-of-scope asset, prohibited technique, posture ceiling, invalid identity, exhausted budget, or consumed approval.

## Approval provider direction

Exactly one approval provider is active in a deployment:

```python
class ApprovalProvider(Protocol):
    def request(self, action: ActionRequest) -> ApprovalReference: ...
    def resolve(self, reference: ApprovalReference) -> ApprovalRecord: ...
    def consume(self, reference: ApprovalReference, action: ActionRequest) -> None: ...
```

Planned implementations:

- `LocalApprovalProvider` — standalone default;
- `ChaseOSApprovalProvider` — optional personal integration;
- a future team provider.

Approvals are not mirrored between providers. GreyTheory records provider identity, reference, fingerprint, and consumption receipt.

## Package boundary

- `greytheory/`: minimal, dependency-light trust kernel and current offline capabilities.
- `greytheory/research/`: current structured local workspaces, sessions, assets, identity handles, hypotheses, experiments, action records, and lessons.
- `greytheory/learning/`: current versioned card catalogue, synthetic fixtures,
  skill graph, private evidence-bound mastery records, transparent adaptive
  review, and bounded standard/assisted/transfer journey orchestration.
- `greytheory/hypothesis/`: current deterministic nine-factor ranking policy,
  explicit estimate contracts, explainable queue engine, synthetic proof, and
  private queue writeback. It consumes governed records and grants no authority.
- `greytheory_worker/`: current dark lower-trust DNS/direct-TLS process boundary
  behind one-use tickets; its trusted parent retains broker authority and no
  launcher, scheduler, accepted image, or posture route exists.
- `greytheory/models/`: current governed roles, policies, citations, budgets,
  provenance, adversarial evaluations, and deterministic offline provider; any
  network provider remains future work.
- `greytheory_app/` and `greytheory_local/`: current UI-neutral application
  snapshots/commands, private runtime, and authenticated numeric-loopback API;
  the graphical workbench remains future work.
- future `packs/`: third-party or separately distributed research methods, fixtures, validators, and curriculum; the built-in 12-card catalogue currently ships inside `greytheory.learning`.

Zero dependencies remains a trust-surface choice for the core, not a prohibition on pinned, isolated dependencies in workers, models, or the workbench.

## Plugin contract

Every future adapter declares its ID/version, binary digest, input/output schemas, minimum authority, network/filesystem/credential needs, side effects, data classes, determinism, maximum rate, emitted evidence, and supported stop conditions. A ticket cannot be issued when a plugin's declared capability exceeds the requested envelope.
