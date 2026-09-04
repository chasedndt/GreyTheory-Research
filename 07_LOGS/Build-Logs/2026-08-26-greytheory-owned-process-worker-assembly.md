# GreyTheory owned-process passive worker assembly

**Date:** 2026-08-26

**Branch:** `codex/2026-08-24-greytheory-workbench-foundation`

**Posture:** `LOCAL_FIXTURE`

## Repository-truth delta

Before this slice, GreyTheory had a network-free adapter contract and real
resolver/direct-TLS primitives, but no process boundary assembled them. The
repository correctly described the full worker as unassembled.

After this slice, source and unit tests contain a dark two-phase owned-process
assembly: resolve once, return the complete answer for trusted broker recheck,
then perform one exact direct request and exit. The full Ubuntu service has not
passed host acceptance, so the capability remains `PARTIAL` and
`PASSIVE_HTTP` remains unavailable.

## Changes

- Added strict JSON serialization for resolution, direct-request, and transport
  records; frames reject extra fields, wrong JSON types, malformed base64, and
  payloads above 196,608 bytes.
- Added an owned spawned worker service that permits exactly one resolution
  followed by one request bound to the same host and an address from its own
  complete answer.
- Kept ticket/receipt signing keys, replay state, kill-switch authority, capture
  private keys, and research data in the trusted parent assembly.
- Scrubbed the child environment and required Linux non-root UID/GID, no foreign
  supplementary group, zero effective/bounding capabilities, and
  no-new-privileges before accepting worker evidence.
- Added deterministic process termination/reaping and exact two-frame client
  tests, including privileged identity refusal before accepting a result.
- Added a full no-route Ubuntu harness and wrapper using UID/GID 65534, an
  ephemeral `/etc` overlay, an owned TLS canary, dropped capabilities, and no
  default route.
- Accepted ADR-0018 and reconciled capability, threat-model, roadmap, project,
  integration, architecture, and acceptance truth.

## Untouched boundaries

- No launcher, scheduler, listener, service manager, programme route, or
  workbench command can invoke the worker.
- No production/root KEK, credential, programme source, VPS, or target was read
  or contacted.
- The worker child receives no private signing/decryption key or research store.
- No canonical ChaseOS file was changed.
- No push, merge, deployment, posture change, or `PASSIVE_HTTP` action occurred.

## Verification

```text
python -m pytest -q tests\test_passive_broker_foundation.py tests\test_passive_capture_encryption.py tests\test_passive_adapter_contract.py tests\test_passive_worker_primitives.py tests\test_passive_worker_service.py tests\test_ubuntu_worker_host_acceptance.py tests\test_capabilities.py
91 passed in 38.15s
```

```text
python -m pytest -q
664 passed in 202.57s (0:03:22)
```

```text
python -m compileall -q acceptance greytheory_worker greytheory_worker_contract
PASS
```

```text
git diff --check
PASS (line-ending conversion warnings only)
```

## Ubuntu host acceptance attempt

The first full-service wrapper attempt exceeded its 120-second outer ceiling
without emitting JSON evidence. Afterwards, even local WSL control commands
such as `wsl -d Ubuntu -- echo` timed out. Exact task-owned Windows-side WSL
clients were stopped; unrelated Hermes WSL processes were not touched.

The wrapper was then refined to use an ephemeral overlay of `/etc` rather than
binding WSL's generated `/etc/hosts` special file. The current refined wrapper
could not be run because the Ubuntu control path remained unavailable. No host
pass is claimed.

## Verification status

**VERIFIED for source assembly, serialization, broker/worker separation,
identity policy, process lifecycle, and local unit/static contracts.**

**UNVERIFIED for the current full Ubuntu service harness.** Earlier accepted
Ubuntu evidence still proves only primitive numeric TLS and spawned-child
cancellation. It does not prove real system-resolution through the assembled
service, encrypted full-path return, or hardened worker behavior.

## Remaining unknowns

- successful execution of the refined no-route Ubuntu full-service harness;
- durable OS egress enforcement and hardened repeatable Ubuntu image;
- approved OS secret-provider binding, backup, and recovery for the root KEK;
- broker transport beyond the owned spawned-process channel;
- authorised canary/programme review, sustained clean operation, and explicit
  human posture approval;
- selected graphical workbench direction and Windows installed acceptance.

## Next safe action

Wait for Ubuntu to recover or obtain explicit operator authority to terminate
and restart that distribution, because unrelated Hermes processes also use it.
Then rerun `acceptance/run-ubuntu-worker-service.ps1` and require complete JSON
evidence before advancing host truth. Do not use a VPS or enable
`PASSIVE_HTTP`.
