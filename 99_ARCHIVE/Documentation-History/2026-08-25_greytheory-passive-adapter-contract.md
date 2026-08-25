# Documentation History - GreyTheory Passive Adapter Contract

- Date: 2026-08-25
- Runtime: Codex / Axiom-Codex
- Status: PARTIAL and VERIFIED without network I/O

## Historical change

The passive pilot now has an executable adapter orchestration contract before
any socket implementation exists. Injected resolver and direct-transport
evidence must bind the exact host, numeric address, TLS name, full request,
deadline, close/no-body/no-proxy/no-follow behavior, and one bounded header
block. The exact bytes are encrypted and completion or denial is sealed through
the passive broker.

This is not a worker or network implementation. DNS/TLS/HTTP primitives,
OS-level cancellation and egress proof, Ubuntu isolation, broker transport,
canary acceptance, and explicit posture approval remain unimplemented.

## Links

- [Build log](../../07_LOGS/Build-Logs/2026-08-25-greytheory-passive-adapter-contract.md)
- [Daily note](../../07_LOGS/Daily/2026-08-25.md)
- [Agent activity](../../07_LOGS/Agent-Activity/2026-08-25-codex-greytheory-passive-adapter-contract.md)
- [ADR-0014](../../Docs/decisions/ADR-0014-network-free-passive-adapter-contract.md)
