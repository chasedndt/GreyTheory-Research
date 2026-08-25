# GreyTheory Ubuntu primitive host acceptance documentation history

**Date:** 2026-08-25

## Documentation delta

- Recorded ADR-0016 for offline Ubuntu primitive acceptance in an ephemeral
  loopback-only, no-default-route network namespace.
- Updated canonical repository capability truth to distinguish injected tests,
  bounded WSL2 host proof, and missing full worker/VM/VPS acceptance.
- Split Milestone 9 so completed primitive host mechanics no longer imply that
  the full resolver/adapter/capture/receipt worker path is assembled.
- Updated the threat model, workbench architecture, roadmap, project definition,
  project state, README, and executable capability register.

## Truth boundary retained

`LOCAL_FIXTURE` remains the operating posture. The repository still has no
enabled passive action, successful real DNS acceptance, unprivileged worker
image, broker transport, OS-bound KEK, authorised canary, or VPS proof.
