# Documentation History - GreyTheory Passive Capture Encryption

- Date: 2026-08-25
- Runtime: Codex / Axiom-Codex
- Status: PARTIAL and VERIFIED offline

## Historical change

The dark passive broker now has a real confidentiality boundary before any
network worker exists. Captures are encrypted to an operator recipient and
authenticated against the signed ticket. Operator private keys are wrapped
under an external root KEK and can be provisioned, rotated, or revoked with an
authority reference while preserving decryption of retained immutable
evidence.

This does not enable `PASSIVE_HTTP`. OS secret-provider binding, DNS/HTTP
conformance, worker transport/isolation, canary acceptance, and explicit human
posture approval remain unimplemented.

## Links

- [Build log](../../07_LOGS/Build-Logs/2026-08-25-greytheory-passive-capture-encryption.md)
- [Daily note](../../07_LOGS/Daily/2026-08-25.md)
- [Agent activity](../../07_LOGS/Agent-Activity/2026-08-25-codex-greytheory-passive-capture-encryption.md)
- [ADR-0013](../../Docs/decisions/ADR-0013-passive-capture-encryption-and-key-lifecycle.md)
