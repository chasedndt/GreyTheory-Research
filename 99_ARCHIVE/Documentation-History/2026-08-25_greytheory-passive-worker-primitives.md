# Documentation History - GreyTheory Passive Worker Primitives

- Date: 2026-08-25
- Runtime: Codex / Axiom-Codex
- Status: PARTIAL and VERIFIED with injected syscalls

## Historical change

The passive pilot now has concrete but unlaunched DNS and direct TLS mechanics.
Blocking absolute-name system resolution is isolated in one cancellable owned
child over capped JSON bytes. The TLS transport connects only to the selected
numeric address, uses explicit CA and hostname/SNI verification, disables key
logging, shares one deadline, bounds header reads, verifies the peer, and closes
on every path.

No repository test made a network call. The package has no launcher, service,
broker transport, default secret/CA, or posture route. Ubuntu host behavior,
egress, canary acceptance, and `PASSIVE_HTTP` remain unproven.

## Links

- [Build log](../../07_LOGS/Build-Logs/2026-08-25-greytheory-passive-worker-primitives.md)
- [Daily note](../../07_LOGS/Daily/2026-08-25.md)
- [Agent activity](../../07_LOGS/Agent-Activity/2026-08-25-codex-greytheory-passive-worker-primitives.md)
- [ADR-0015](../../Docs/decisions/ADR-0015-unlaunched-passive-worker-primitives.md)
