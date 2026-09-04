# Codex activity - GreyTheory Ubuntu service harness hardening

**Date:** 2026-08-26

**Agent:** Codex / Axiom-Codex

**Posture:** `LOCAL_FIXTURE`

## Repo-truth delta

The full Ubuntu harness is materially safer and more diagnosable, but it is not
host-accepted because no complete JSON evidence exists.

## Work performed

- Corrected the PowerShell-to-Bash boundary and moved namespace setup into a
  checked-in Linux script.
- Isolated WSL's generated hosts mount and added the absolute dotted canary name.
- Preserved the real worker exception during canary cleanup.
- Replaced authority-risky or slow process startup choices with a clean Linux
  fork server plus one resolver fork inside the scrubbed worker.
- Bounded the Windows wrapper and its exact owned WSL process cleanup.
- Reconciled current truth and verified 92 focused plus 665 repository tests.

## Do not undo

- Do not fork the broker process or pass broker authority into the worker.
- Do not remove the trailing-dot canary alias; production resolution is
  deliberately absolute to prevent search-suffix expansion.
- Do not append directly to WSL's generated `/etc/hosts` mount.
- Do not claim host acceptance without the complete JSON record.
- Do not restart the shared WSL distro/service or stop Hermes state implicitly.

## Verification

See `07_LOGS/Build-Logs/2026-08-26-greytheory-ubuntu-service-harness-hardening.md`.
