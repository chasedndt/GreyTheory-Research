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
- After explicit approval, restarted only Ubuntu, verified regenerated devices
  and returning supervised user services, and proved the retained scratch roots
  were unmounted and not loop-device backing.
- Reproduced and fixed Linux Git's handling of the linked Windows worktree
  pointer before any image construction was accepted.
- Replaced alphabetical package unpacking with complete lock-bound install
  groups after `dpkg` correctly refused an unmet Python pre-dependency.
- Kept the ext4 build root `nodev` while giving package scripts an exact,
  owned temporary `/dev` tmpfs after the clean retry proved device access was
  otherwise denied. No host-device bind was reintroduced.
- Added bounded canonical root-manifest diagnostics after the byte-identity
  gate isolated `ldconfig`'s optional filesystem-specific auxiliary cache; the
  hardening pass now removes that cache without removing `/etc/ld.so.cache`.

## Guardrails retained

`LOCAL_FIXTURE` remains the ceiling. Source implementation is not image
acceptance. The operator-approved Ubuntu restart did not install a WSL system
package or enable target/programme contact, key activation, VPS, launcher,
scheduler, or a posture transition.

## Verification

21 focused tests and all 708 repository tests pass. Shell and PowerShell syntax
checks pass. All 18 packages match three Canonical-signed Ubuntu archive
indexes. Ubuntu process creation and device state are restored. A dirty-tree
development build now passes two-build byte identity, but no clean release
image or image-runtime acceptance record exists yet.

## Handoff

Commit the linked-worktree compatibility fix, run a clean release build and
image acceptance, and retain VM/reboot, broker transport, key-provider/recovery,
programme review, sustained operation, and human posture as independent gates.
