# GreyTheory owned-process worker assembly documentation history

**Date:** 2026-08-26

## Documentation delta

- Accepted ADR-0018 for retaining broker authority outside the worker process.
- Updated capability truth from separate unlaunched primitives to a dark,
  unit-verified two-phase owned-process assembly.
- Kept the passive worker `UNAVAILABLE` and the supporting capabilities
  `PARTIAL` because the current full Ubuntu harness has no passing host evidence.
- Documented the first host timeout, WSL control-path failure, refined overlay
  wrapper, untouched unrelated Hermes processes, and required rerun gate.
- Updated roadmap, project definition/state, threat model, integration boundary,
  system overview, workbench architecture, acceptance guide, tests, logs, and
  indexes.

## Truth boundary retained

`LOCAL_FIXTURE` remains the operating posture. No target, programme, VPS,
production secret, deployment, or `PASSIVE_HTTP` action was used or enabled.
