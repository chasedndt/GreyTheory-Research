# Documentation History - GreyTheory Workbench Foundation

- Date: 2026-08-24
- Runtime: Codex / Axiom-Codex
- Type: capability reconciliation, architecture, implementation, and verification
- Status: FOUNDATION IN PROGRESS and VERIFIED locally

## Historical change

This pass closed a truth gap between GreyTheory's implemented offline kernel and
its operator-facing dashboard. The dashboard had become stale after the model,
learning, signal, and Scope Watch milestones and still described those
capabilities as absent. A typed executable register now supplies current status
to surfaces and explicitly distinguishes offline shipped code from unavailable
network capability and unmeasured runtime state.

The pass also fixed the architectural place of the future workbench. It will be
a Windows-first local application layer around the offline core, not a new
authority plane or a direct tool runner. A later passive worker belongs in an
isolated Ubuntu 24.04 environment behind a separately verified broker. No
interactive workbench, broker, worker, or posture elevation is claimed here.

The same pass implemented the direction-independent learning workflow behind
the future Learn screen: deterministic prerequisite and review planning,
ordered Learn/Practise/Prove/Reflect/Assess stages, stage evidence, reflection,
private integrity-checked storage, optimistic revisions, and CLI operation.
The journey cannot run a fixture or award mastery, and completion requires an
already persisted matching human assessment.

## Surfaces affected

- Capability register, package exports, dashboard read model, and tests
- Learning planner, journey state, private store, CLI, and acceptance tests
- Canonical project definition/state, README capability summary, and roadmap
- Workbench architecture, ADR index, documentation map, and changelog
- Build log, daily note, agent activity, documentation history, and indexes

## Links

- [Build log](../../07_LOGS/Build-Logs/2026-08-24-greytheory-workbench-foundation.md)
- [Daily note](../../07_LOGS/Daily/2026-08-24.md)
- [Agent activity](../../07_LOGS/Agent-Activity/2026-08-24-codex-greytheory-workbench-foundation.md)
- [Workbench architecture](../../Docs/workbench-architecture.md)
- [ADR-0010](../../Docs/decisions/ADR-0010-workbench-is-an-application-boundary.md)
