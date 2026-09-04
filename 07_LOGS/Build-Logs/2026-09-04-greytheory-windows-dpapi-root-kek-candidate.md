# GreyTheory Windows DPAPI root-KEK candidate — build log

**Date:** 2026-09-04

**Agent:** Codex

**Branch:** `codex/2026-09-01-workbench-read-model-binding`

**Posture:** `LOCAL_FIXTURE`

## Repo-truth delta

Before this increment, passive captures used an authorised external-KEK-wrapped
recipient lifecycle, but the external root KEK had no concrete OS provider.
The Ubuntu 24.04.4 no-route worker-service proof passed, while key-provider and
recovery acceptance remained a placeholder gate.

This increment adds an operator-side Windows CurrentUser DPAPI candidate. It is
deliberately not wired to the workbench launcher, Ubuntu worker, or posture.

## Implemented candidate

- Generates one random 32-byte root KEK and refuses replacement.
- Protects a strict versioned payload with CurrentUser DPAPI,
  `CRYPTPROTECT_UI_FORBIDDEN`, fixed purpose entropy, and a fixed description.
- Refuses provider records in Git, caps reads at 64 KiB, and publishes the
  first record without replacing a concurrently created destination.
- Audits provision and lease operations against explicit actor/authority
  references.
- Opens the existing capture-key store through a short-lived mutable lease and
  overwrites that owned buffer on close.
- Keeps the root KEK and recipient private keys out of the Ubuntu worker.

## Accepted candidate proof

The final Windows host record is:

`E:\Projects\GreyTheory\acceptance\windows-dpapi-root-kek-20260904-095757-20740\acceptance.json`

```text
provider_id=windows-dpapi-current-user-v1
provider_scope=current_user
posture=LOCAL_FIXTURE
passive_http_enabled=false
external_network_contact=false
worker_exercised=false
root_kek_plaintext_persisted=false
root_kek_lease_zeroed=true
restart_recovery_same_profile=true
protected_backup_recovery_same_profile=true
tampered_record_refused=true
capture_recipient_private_key_wrapped=true
capture_round_trip_verified=true
audit_chain_verified=true
provider_approved_for_posture=false
acl_hardening_accepted=false
cross_profile_recovery_accepted=false
independent_disaster_recovery_accepted=false
```

The retained provider record inherited these observed ACL entries:

```text
Owner: ZeusOS\chaseos
Administrators: FullControl
SYSTEM: FullControl
Authenticated Users: Modify, Synchronize
Users: ReadAndExecute, Synchronize
```

DPAPI prevents those identities from recovering the root plaintext, but this
ACL is not accepted for operational application data and permits tampering or
deletion. The candidate therefore does not close the key-provider gate.

## Capability-truth repair and rendered QA

The executable register and dashboard now describe Guided Mission Control as
`PARTIAL`, not planned. Current-user lifecycle, thirteen journeys, 24 lessons,
one ready Case Pack, and same-origin commands are visible without hiding the
open keyboard, separate-account, signing, uninstall, curriculum, coach, or
external-intelligence gaps.

Fresh accepted rendered evidence is under:

`E:\Visual QA\GreyTheory Visual QA\Current Reviews\2026-09-04-dpapi-capability-truth`

Desktop Programmes/Settings and 390-pixel Settings states have no horizontal
overflow, display the candidate/open-gate distinction, and emit zero accepted
console errors. The first capture found a missing favicon; the existing
GreyTheory mark is now declared and the clean rerun passed.

## Verification

```text
python -m pytest -q tests/test_windows_dpapi_root_kek.py tests/test_passive_capture_encryption.py tests/test_capabilities.py
18 passed in 0.67s

python -m pytest -q
694 passed in 21.93s

npm --prefix workbench_ui run test
22 UI tests passed; 4 Sites tests passed

npm --prefix workbench_ui run build
production build passed

acceptance/run-windows-dpapi-root-kek.ps1
candidate invariants passed; durable JSON retained
```

## Untouched boundaries

- No external target, programme endpoint, provider, account credential, VPS,
  durable route, or passive action was contacted or enabled.
- No root KEK or recipient private key entered the worker.
- `greytheory_local` remains free of browser, subprocess, and target-client
  imports.
- The source checkout and unrelated user changes remain untouched.

## Remaining gates

The candidate still needs explicit operator selection, hardened Windows
application-data ACLs, an approved profile/system backup procedure, and
recovery independent of the same account/profile. Durable egress, hardened
Ubuntu image, broker transport authentication, one unambiguous programme,
sustained operation, and explicit human posture approval remain separate gates.

The next safe passive milestone is durable egress enforcement in a reproducible
local Ubuntu image. It must not be treated as permission to contact a target.
