# Documentation Map

Where to start, and which document wins when two disagree.

## Authority order

1. **[`definition.md`](definition.md)** — canonical. Outranks everything else, including the root README.
2. **[`scope-policy.md`](scope-policy.md)** — the operating posture. Outranks any capability description.
3. Everything else.
4. **[`architecture.md`](architecture.md)** — superseded. Historical reference for lane-level detection detail only.

## Start here

| If you want to… | Read |
|---|---|
| Understand the whole system | [`system-overview.md`](system-overview.md) |
| Understand what GreyTheory is | [`definition.md`](definition.md) |
| See it rather than read it | [`diagrams.md`](diagrams.md) |
| Know what actually works today | [`definition.md` §6](definition.md#6-capability-register) |
| Know what it is allowed to do right now | [`scope-policy.md`](scope-policy.md) |

## By subject

### Definition and structure
- [`system-overview.md`](system-overview.md) — the whole architecture, and why each part is shaped as it is
- [`definition.md`](definition.md) — three planes, six invariants, capability register, decision log
- [`diagrams.md`](diagrams.md) — architecture, gate flow, compilation, lifecycle, provenance, authority levels, approvals, evidence
- [`module-breakdown.md`](module-breakdown.md) — what each module owns and refuses to own
- [`data-flow.md`](data-flow.md) — how authorisation becomes a defensible artifact

### Governance
- [`scope-policy.md`](scope-policy.md) — hard boundary and the authority checklist
- [`disclosure-authority-checklist.md`](disclosure-authority-checklist.md) — before any action leaves local work
- [`evidence-policy.md`](evidence-policy.md) — where evidence lives, what may leave, retention
- [`validation-policy.md`](validation-policy.md) — gates, what counts as a deterministic check, demotion

### Planning and state
- [`open-questions.md`](open-questions.md) — resolved, blocking, and non-blocking unknowns
- [`roadmap.md`](roadmap.md) — phases and graduation criteria
- [`vuln-coverage-matrix.md`](vuln-coverage-matrix.md) — intended Signal Plane surface. Current coverage: none
- [`safe-local-demo-proof-plan.md`](safe-local-demo-proof-plan.md) — local demos with no external target

### Integration and product
- [`chaseos-reconciliation.md`](chaseos-reconciliation.md) — what ChaseOS already owns, and what GreyTheory therefore does not build
- [`product-boundary-map.md`](product-boundary-map.md) — allowed now vs blocked until approval
- [`discord-lane-map.md`](discord-lane-map.md) — internal workspace wiring

## Repository root

- [`README.md`](../README.md) — landing page, quickstart, capability status
- [`SECURITY.md`](../SECURITY.md) — reporting a vulnerability in GreyTheory itself
- [`CONTRIBUTING.md`](../CONTRIBUTING.md) — setup and the non-negotiables
- [`CHANGELOG.md`](../CHANGELOG.md)
- [`LICENSE`](../LICENSE) / [`NOTICE`](../NOTICE) — Apache-2.0

## Writing rules for these docs

- Never describe an Aspirational component as working. The capability register governs every claim.
- Separate observation, proof and inference — the same rule the code enforces on claims.
- If a rule exists to prevent a specific mistake, name the mistake.
