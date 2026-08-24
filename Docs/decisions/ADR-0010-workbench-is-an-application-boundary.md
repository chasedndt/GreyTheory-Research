# ADR-0010 - The workbench is an application boundary, not a new authority plane

**Status:** Accepted - 2026-08-24

**Relates to:** Product workbench track and Milestone 9.

## Context

GreyTheory has a substantial offline trust and research kernel, but its current
dashboard is a static text/JSON/HTML status export. A usable research operating
system needs navigation, active-workspace state, learning journeys, hypothesis
and evidence interaction, and explicit operator decisions.

Putting those behaviours directly into `greytheory/` would weaken two existing
properties: the core has no network code, and domain invariants do not depend on
a UI framework. Letting a browser or desktop shell call collectors directly
would also create a second execution route around the gate.

## Decision

The graphical workbench will be a separate application layer around the
existing core.

```text
operator
  -> workbench UI
  -> local application service
  -> GreyTheory use cases and read models
  -> Authority Gate
  -> LOCAL_FIXTURE executor now / governed worker later
```

- `greytheory/` remains the dependency-free, offline trust and domain kernel.
- The workbench consumes serialisable read models and submits typed intents to a
  local application service. It never invokes a collector, model provider,
  shell, browser, or worker directly.
- Every consequential intent is re-authorised at execution time. UI state,
  route state, and a previously displayed allow decision are never authority.
- The first workbench runs at `LOCAL_FIXTURE`, binds only to the local machine,
  and has no target-network capability.
- The Windows workstation is the initial operator host. A future
  `PASSIVE_HTTP` worker belongs in an isolated Ubuntu 24.04 environment and must
  return receipts and immutable captures through the broker boundary.
- The executable capability register supplies status labels to the dashboard
  and workbench. It describes shipped code, not current runtime health; missing
  data remains `UNKNOWN`.
- The selected visual direction may change layout and interaction details, but
  it may not change these authority, provenance, storage, or process boundaries.

## Consequences

The UI can evolve without importing network dependencies into the kernel. A
desktop package, local web shell, and a later remote viewer can share the same
application contract, although only the local operator shell is in current
scope.

The application service becomes a security boundary and therefore needs its own
contract tests: loopback binding, origin checks, request-size limits, no ambient
authority, deterministic error states, and a refusal path for every action. A
pretty screen is not an implementation of those controls.

The graphical workbench remains `PLANNED` until the selected visual direction
is implemented and its primary journeys work. This decision records the
boundary; it does not claim the application exists.

## Rejected alternatives

- **Put a web server in `greytheory/`.** Rejected because it introduces network
  machinery into the trust kernel and makes framework lifecycle part of domain
  correctness.
- **Let the UI run tools directly.** Rejected because it creates an execution
  route that can bypass gate, approval, and receipt enforcement.
- **Start with a VPS-hosted dashboard.** Rejected for the pilot because it adds
  authentication, exposure, telemetry, and raw-evidence risks before the local
  workflow is proven.
- **Treat the static HTML dashboard as the workbench.** Rejected because it has
  no navigation, active session, learning path, evidence drill-down, or typed
  action boundary.
