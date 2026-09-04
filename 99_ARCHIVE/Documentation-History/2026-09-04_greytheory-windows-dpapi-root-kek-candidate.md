# Documentation history — GreyTheory Windows DPAPI root-KEK candidate

On 2026-09-04 repository truth changed from no concrete root-key provider to a
host-tested but unapproved Windows CurrentUser DPAPI candidate. Same-profile
restart/protected-copy recovery, tamper refusal, capture decryption, lease
zeroing, plaintext-tree scanning, and audit validation pass. The key-provider
activation gate remains open because inherited ACL hardening, independent
recovery, backup policy, and operator approval have not passed.

The same truth-sync corrected the executable graphical-workbench state from
planned to partial and added fresh desktop/390-pixel rendered evidence. A
missing favicon discovered in the first capture was fixed using the existing
GreyTheory mark; the accepted rerun has no console errors or horizontal
overflow.

Updated canonical/current surfaces include `README.md`, `PROJECT_STATE.md`,
`PROJECT_DEFINITION.md`, `DATA_POLICY.md`, `THREAT_MODEL.md`, `CHANGELOG.md`,
`Docs/definition.md`, `Docs/roadmap.md`, `Docs/system-overview.md`,
`Docs/workbench-architecture.md`, `Docs/live-programme-transition.md`,
`Docs/README.md`, ADR-0018, proposed ADR-0019, `acceptance/README.md`, the
executable capability register/dashboard, and UI capability copy. Indexed
build/activity/daily documentation was synchronized.

No document describes the candidate as an approved key provider, independent
recovery, durable egress, hardened image, programme authority, VPS acceptance,
live-target proof, or posture transition.
