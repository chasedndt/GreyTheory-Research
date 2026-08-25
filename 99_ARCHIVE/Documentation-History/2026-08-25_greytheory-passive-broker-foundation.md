# Documentation History - GreyTheory Passive Broker Foundation

- Date: 2026-08-25
- Runtime: Codex / Axiom-Codex
- Status: PARTIAL and VERIFIED offline

## Historical change

Milestone 9 gained its first executable boundary without gaining network
capability. `greytheory_broker` now defines and tests the narrow protocol that a
future lower-trust worker must obey. The authority source remains the existing
Gate and its hash-chained audit record; the broker adds expiring one-use intent,
target/address/budget policy, persistent stop/replay controls, and a verifiable
return receipt.

The pass also corrected a trust-kernel omission: programme request rate is now
part of the scope-contract fingerprint. A rate change therefore invalidates
authority instead of preserving the old fingerprint.

No worker or network adapter exists. The package's value is that future I/O
cannot be introduced without crossing a visible conformance boundary.

## Links

- [Build log](../../07_LOGS/Build-Logs/2026-08-25-greytheory-passive-broker-foundation.md)
- [Daily note](../../07_LOGS/Daily/2026-08-25.md)
- [Agent activity](../../07_LOGS/Agent-Activity/2026-08-25-codex-greytheory-passive-broker-foundation.md)
- [ADR-0011](../../Docs/decisions/ADR-0011-dark-passive-broker-foundation.md)
- [Threat model](../../THREAT_MODEL.md)
