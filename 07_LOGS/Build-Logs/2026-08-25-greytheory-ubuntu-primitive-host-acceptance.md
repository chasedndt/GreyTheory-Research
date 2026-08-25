# GreyTheory Ubuntu primitive host acceptance

**Date:** 2026-08-25

**Branch:** `codex/2026-08-24-greytheory-workbench-foundation`

**Posture:** `LOCAL_FIXTURE`

## Repository-truth delta

Before this slice, the production resolver and direct-TLS classes were verified
only with injected process/socket/TLS doubles. The repository correctly left all
Ubuntu behavior unproven.

After this slice, Ubuntu 24.04.4 WSL2 has repeatable offline proof for the
production numeric direct-TLS transport and the production resolver parent's
spawn/deadline/termination path. The full adapter and worker remain unassembled.

## Changes

- Added `acceptance/ubuntu_worker_host.py` and a Windows-to-WSL PowerShell wrapper.
- Added a public test-only certificate/key for `greytheory-canary.invalid`.
- Created an ephemeral `unshare -Urn` namespace with only loopback, no default
  route, and a synthetic `8.8.8.8/32` loopback address.
- Exercised `DirectTlsHeadTransport` against the owned port-443 TLS canary with
  `getaddrinfo` replaced by a hard failure.
- Proved explicit CA and hostname verification, mismatch refusal, two-write
  header streaming, zero body, no proxy/redirect, and deterministic close.
- Proved a deliberately blocked real spawned resolver child is terminated and
  reaped at the deadline.
- Added static harness/fixture/wrapper contract tests and ADR-0016.
- Reconciled capability, roadmap, project-state, architecture, threat-model, and
  index truth.

## Untouched boundaries

- No external DNS, socket, HTTP, TLS, or target contact occurred.
- No worker service, scheduler, broker transport, or live adapter was assembled.
- No root KEK or production credential was created or read.
- No canonical ChaseOS file was changed.
- No posture, programme review, VM/VPS, deployment, push, merge, or submission
  action occurred.

## Verification

```text
& .\acceptance\run-ubuntu-worker-host.ps1
PASS - Ubuntu 24.04.4 LTS; interfaces=[lo]; default_route=false
PASS - numeric 8.8.8.8; resolver_calls=0; hostname mismatch refused
PASS - 78 header bytes; 2 server writes; body=0; connection closed
PASS - spawned resolver child exit=-15; alive=false; elapsed=0.202442 s
```

```text
python -m pytest -q tests/test_ubuntu_worker_host_acceptance.py tests/test_passive_worker_primitives.py tests/test_capabilities.py
31 passed in 3.78s
```

```text
python -m pytest -q
646 passed in 136.35s
```

```text
python -m compileall -q acceptance greytheory_worker greytheory
PASS
```

## Verification status

**VERIFIED for the bounded local Ubuntu primitive acceptance contract.** This is
not proof of successful real system DNS, the full adapter, an unprivileged worker
image, durable egress enforcement, a VPS, or `PASSIVE_HTTP` readiness.

## Remaining unknowns

- successful real system-resolver behavior in the final worker environment;
- full resolver-to-adapter-to-encrypted-receipt assembly;
- unprivileged Ubuntu image and persistent OS egress enforcement;
- approved OS secret-provider binding and recovery for the root KEK;
- broker authentication/transport, worker identity, authorised canary, sustained
  operation, and operator posture approval.

## Next safe action

Build the unprivileged local Ubuntu worker image and assemble the full adapter
against an owned, no-route acceptance canary. Keep Windows as the local operator
control plane and do not use a VPS until the identical local worker image and
broker boundaries pass.
