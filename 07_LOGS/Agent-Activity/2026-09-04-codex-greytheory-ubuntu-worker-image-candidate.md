# Codex activity - GreyTheory Ubuntu worker-image candidate

## Scope

Continue the active GreyTheory goal by implementing the next passive-pilot
image boundary without raising posture or contacting a target.

## Actions

- Reconciled the isolated E: worktree, branch, free space, active goal, and
  current canonical project/roadmap/threat-model truth.
- Added Canonical image and Ubuntu archive signature-chain verification for the
  exact base plus 18 locked runtime packages.
- Added deterministic two-build SquashFS construction and a non-activating
  clean-source manifest.
- Added strict read-only image admission, bounded writable mounts/devices,
  unprivileged process enforcement, mandatory exact egress, immutable-path
  checks, and composed full-worker evidence.
- Added focused algorithm/contract/composition tests and ran the complete suite.
- Corrected the stale workbench status and stack entry in the open-questions
  register without rewriting the historical architecture decision.
- Removed the discarded unsafe host `/dev` bind approach and preserved the
  operator's existing WSL processes when the temporary devtmpfs damage was
  discovered.

## Guardrails retained

`LOCAL_FIXTURE` remains the ceiling. Source implementation is not image
acceptance. No restart, WSL system install, target/programme contact, key
activation, VPS, launcher, scheduler, or posture transition occurred.

## Verification

20 focused tests and all 707 repository tests pass. Shell and PowerShell syntax
checks pass. All 18 packages match three Canonical-signed Ubuntu archive
indexes. The WSL runtime remains blocked before process creation, so no image
build/runtime record exists.

## Handoff

Obtain explicit permission to restart only the Ubuntu WSL distribution. Then
verify `/dev`, confirm no mounts under the exact scratch roots, run a clean
release build and image acceptance, and retain VM/reboot, broker transport,
key-provider/recovery, programme review, sustained operation, and human posture
as independent gates.
