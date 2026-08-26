# Codex activity - GreyTheory owned-process passive worker assembly

**Date:** 2026-08-26

**Agent:** Codex / Axiom-Codex

**Posture:** `LOCAL_FIXTURE`

## Repo-truth delta

The full passive path moved from separate contracts/primitives to a dark,
unit-verified owned-process assembly. It did not move to host-accepted or
available because the full Ubuntu run produced no evidence.

## Work performed

- Added exact two-phase worker IPC and strict typed serialization.
- Kept all broker authority and private key material in the trusted parent.
- Added worker environment, UID/GID, capability, supplementary-group, and
  no-new-privileges admission checks.
- Added process lifecycle, privileged-worker refusal, assembly, capability, and
  static no-route harness tests.
- Added the unprivileged Ubuntu full-service harness and ADR-0018.
- Recorded the WSL timeout honestly and left unrelated Hermes state untouched.

## Do not undo

- Do not combine resolve and connect inside the lower-trust worker without the
  parent broker rechecking the complete DNS answer.
- Do not pass signing keys, replay/kill-switch state, capture private keys, the
  research store, credentials, or ambient environment into the worker.
- Do not call the refined harness host-accepted until its JSON evidence exists.
- Keep `PASSIVE_HTTP` unavailable.

## Verification

See `07_LOGS/Build-Logs/2026-08-26-greytheory-owned-process-worker-assembly.md`.
