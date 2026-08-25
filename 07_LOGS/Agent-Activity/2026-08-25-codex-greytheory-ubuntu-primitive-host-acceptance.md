# Codex activity - GreyTheory Ubuntu primitive host acceptance

**Date:** 2026-08-25

**Agent:** Codex / Axiom-Codex

**Posture:** `LOCAL_FIXTURE`

## Repo-truth delta

Ubuntu behavior moved from entirely unverified to a bounded, repeatable WSL2
primitive proof. The capability remains `PARTIAL`; no worker exists.

## Work performed

- Reconciled the clean isolated worktree, stale canonical GreyTheory placeholder,
  E: storage, and operator host shape.
- Confirmed the installed WSL distribution is Ubuntu 24.04.4 on WSL2 with Python
  3.12.
- Added and ran a no-default-route, loopback-only namespace acceptance harness.
- Proved real numeric TLS/CA/hostname/streaming/cleanup behavior and real spawned
  child cancellation without a DNS query or target contact.
- Added ADR, capability, test, roadmap, threat-model, and log truth.

## Do not undo

- Do not run the synthetic `8.8.8.8` canary outside `unshare -Urn`; its safety
  depends on the absence of a default route and its local loopback assignment.
- Do not describe the blocking replacement child as successful system-DNS proof.
- Do not describe WSL2 primitive acceptance as an unprivileged image, VPS, full
  worker, or posture approval.
- Keep the fixture private key labelled test-only and never reuse it.
- Keep `PASSIVE_HTTP` unavailable.

## Verification

See `07_LOGS/Build-Logs/2026-08-25-greytheory-ubuntu-primitive-host-acceptance.md`.
