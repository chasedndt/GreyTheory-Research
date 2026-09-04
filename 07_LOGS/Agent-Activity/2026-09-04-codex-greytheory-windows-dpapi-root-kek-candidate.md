# Codex activity — GreyTheory Windows DPAPI root-KEK candidate

## Scope

Continue the passive-pilot roadmap after Ubuntu no-route service acceptance by
replacing the root-key-provider placeholder with a bounded Windows candidate,
without enabling `PASSIVE_HTTP`.

## Actions

- Implemented a CurrentUser DPAPI adapter and root-KEK provider in the
  operator-side broker package.
- Added strict size/schema/provider checks, exclusive first publication,
  audit binding, short-lived zeroing leases, and capture-key-store integration.
- Added platform-independent denial tests plus a real Windows DPAPI host test.
- Added a bounded acceptance wrapper and durable candidate record proving
  same-profile restart/protected-copy recovery, tamper refusal, capture
  decryption, plaintext-tree scanning, lease zeroing, and audit integrity.
- Inspected the real inherited ACL and retained `acl_hardening_accepted=false`,
  `independent_disaster_recovery_accepted=false`, and
  `provider_approved_for_posture=false`.
- Corrected stale executable/dashboard copy that still called the implemented
  graphical workbench planned.
- Ran fresh desktop and 390-pixel visual QA, fixed the missing favicon with the
  existing brand mark, and retained a zero-console-error evidence set.
- Synchronized architecture, threat, data, roadmap, transition, capability,
  changelog, build, daily, activity, and documentation-history truth.

## Guardrails retained

The provider is not wired to a launcher or posture. Same-profile recovery is
not disaster recovery. DPAPI protection does not make the inherited filesystem
ACL acceptable. The Ubuntu worker receives no root KEK or private decryption
key. No target, programme, provider, VPS, or external network was used.

## Handoff

Keep the key-provider roadmap checkbox open until the operator accepts a
provider, hardened application-data ACLs, and independent recovery. The next
safe passive engineering slice is reproducible local-Ubuntu image and durable
egress enforcement, still against an owned fixture and under `LOCAL_FIXTURE`.
