# Codex activity - GreyTheory authenticated worker-session foundation

## Scope

Continue the active GreyTheory goal on the passive-pilot transport lane while
the current Windows host lacks an authorized true-VM runtime.

## Actions

- Reconciled the clean pushed worktree and active goal after the accepted WSL2
  image-runtime milestone.
- Confirmed that the owned-process pipe is not the future isolated-VM broker
  transport and kept the distinction explicit.
- Reviewed the primary IETF sources for Ed25519, X25519, HKDF, and
  ChaCha20-Poly1305 constraints.
- Added a carrier-neutral mutual-authentication handshake, ephemeral
  directional session derivation, encrypted bounded framing, exact message
  order, expiry, transcript binding, replay guard, and terminal key clearing.
- Proved lossless compatibility with the existing worker contract records and
  negative behavior for tampering, wrong identity, replay, reflection,
  out-of-order messages, duplicate JSON keys, expiry, and oversize frames.
- Added ADR-0021 and reconciled capability truth without closing the transport
  or local-VM roadmap gates.

## Guardrails retained

The new package has no carrier, listener, process launcher, scheduler, service
manager, programme route, or posture switch. The fixture replay guard is not
durable. Transport identity-key provisioning, VM peer binding, independent
security review, and rebooted-host acceptance remain open. `PASSIVE_HTTP`
remains unavailable and neither GreyTheory nor its harness contacted an
external target, programme, or provider.

## Verification

Six focused transport tests and all 714 repository tests pass. Python bytecode
compilation passes. A no-dependency wheel build contains both new transport
modules. No UI changed, so the previously accepted 23 UI tests, 4 Sites tests,
production build, and rendered desktop/mobile QA remain the UI baseline rather
than being rerun as evidence for this backend-only increment.

## Handoff

The next host-bound step requires explicit authority to enable or install a
true VM runtime. Then implement the local VM carrier, external identity
provisioning, durable replay, cold-boot/reboot conformance, and negative
boundary tests. Do not substitute WSL2 or a VPS for that acceptance gate.
