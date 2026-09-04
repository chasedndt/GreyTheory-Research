# GreyTheory authenticated worker-session foundation - build log

**Date:** 2026-09-04

**Agent:** Codex

**Branch:** `codex/2026-09-01-workbench-read-model-binding`

**Posture:** `LOCAL_FIXTURE`

## Repo-truth delta

Before this increment, the broker and worker had a private same-host process
pipe, but the future isolated local-VM boundary had no executable mutual
authentication, confidentiality, framing, or session-replay contract. The
repository described authenticated broker transport as entirely open.

This increment adds only the launch-dark protocol foundation. The carrier,
worker identity-key provisioning, durable replay across reboot, VM peer
binding, security review, and host acceptance remain open.

## Implementation

- Added a signed broker hello and transcript-bound worker response using
  separately pinned Ed25519 identities.
- Added fresh per-session X25519 agreement and transcript-salted
  HKDF-SHA-256 derivation of distinct directional keys.
- Added ChaCha20-Poly1305 encryption with authenticated session, transcript,
  direction, sequence, and message type.
- Enforced a maximum 30-second session, no pre-authentication command/zero-RTT
  path, strict duplicate-key-free canonical JSON, and the existing
  196,608-byte frame ceiling.
- Enforced only `resolve -> resolution -> head -> transport`; a typed worker
  error replaces one response and closes the session.
- Required an injected replay guard to consume each authenticated broker hello
  once. The included bounded in-memory guard is explicitly limited to
  network-free tests and a one-shot worker lifetime.
- Kept existing `ResolutionResult`, `DirectHeadRequest`, and
  `HeadTransportResult` records lossless across the encrypted channel.

## Standards review

The design was checked against the RFC Editor sources for Ed25519, X25519,
HKDF, ChaCha20-Poly1305, and TLS 1.3 early-data replay behavior. The transcript
includes both ephemeral public keys;
the maintained cryptography implementation refuses invalid key agreement; HKDF
uses an authenticated salt plus a versioned context; and each directional key
uses a role-prefixed counter nonce. The design intentionally sends no command
before the full signed exchange. Independent cryptographic review remains a
required acceptance gate.

## Verification

```text
python -m pytest tests/test_passive_broker_transport.py -q
6 passed

python -m pytest -q
714 passed

python -m compileall -q greytheory_worker_transport
exit 0

python -m pip wheel . --no-deps --no-build-isolation --wheel-dir <E artifact root>
greytheory-0.1.0-py3-none-any.whl, 347039 bytes
SHA-256 42b392fa7e328c6bf85457cbe8134a8e27e21b0a7354222a64b5a2c498f09dbd

python -m pip install --no-deps --target <isolated E root> <wheel>
isolated import: greytheory.broker-transport.v1
```

The static transport test also confirms the package imports no socket, SSL,
HTTP client, multiprocessing, subprocess, or asynchronous carrier module. The
wheel inventory contains both `greytheory_worker_transport` modules.

## Host boundary

No host feature, listener, network route, VM runtime, target, programme,
credential, or posture was changed. This Windows host currently has a running
hypervisor/compute substrate but no available Hyper-V PowerShell module/VMMS,
QEMU, VirtualBox, Multipass, Vagrant, Podman, or running Docker engine. Enabling
or installing a true local-VM carrier is a separate host mutation and was not
authorized by the operator's Ubuntu-only restart approval.

## Next safe action

After explicit host-runtime authority, bind the protocol to a local-only VM
carrier, provision distinct broker/worker transport identities outside the
image, add a durable replay store, and run cold-boot/reboot plus negative peer,
tamper, replay, oversized-frame, timeout, and cleanup acceptance. Do not enable
`PASSIVE_HTTP` or use a VPS as a shortcut.
