# ADR-0020: Accept namespace-lifetime exact egress before image binding

**Status:** Accepted

**Date:** 2026-09-04

## Context

The full Ubuntu worker service passed in a namespace with no default route, but
that proved only total network absence. A passive pilot eventually needs one
explicitly authorised destination while the operating system, independently of
the Python application, refuses every other destination and port.

The current Ubuntu 24.04.4 WSL2 distribution has no installed nftables binary
and exposes Landlock ABI 3, which predates network-port controls. Installing
packages globally would mutate the shared development distribution and would
not make the acceptance input reproducible.

## Decision

GreyTheory accepts a narrower egress candidate in a fresh user, mount, and
network namespace:

1. exact Ubuntu Noble nftables packages and dependencies are downloaded to the
   governed E: tool cache and verified against repository-held SHA-256 values;
2. each run reconstructs nftables userspace from those packages into its owned
   temporary root, without installing anything in the WSL distribution;
3. nftables input, forward, and output chains default to drop;
4. only loopback TCP to the owned synthetic `8.8.8.8:443` canary is accepted;
5. a wrong port, a separately routed decoy address, and IPv6 loopback are
   refused and accounted for by the named output-denial counter;
6. after the process is mapped to UID/GID 65534 with zero capabilities and
   no-new-privileges, attempts to add a route or flush the ruleset are refused;
7. the complete two-phase worker path must still return encrypted capture,
   signed receipt, completed replay state, and terminal cleanup; and
8. retained JSON states that the hardened image, programme authority,
   `PASSIVE_HTTP`, VPS use, and external contact are false.

The public-looking fixture and decoy addresses exist only as loopback addresses
inside the isolated namespace. They are not contacted externally.

## Consequences

- OS policy, rather than the application request validator alone, now proves
  exact address/port denial for the lifetime of the owned namespace.
- The decoy route distinguishes nftables enforcement from the earlier proof
  that merely lacked any route.
- The host distribution remains unchanged; the dependency cache is isolated
  under E: and the executed tool is reconstructed from hash-locked packages.
- This is not durable image acceptance. A reproducible read-only Ubuntu worker
  image still has to make policy application and admission unavoidable, then
  pass reboot/VM conformance and negative bypass tests.
- It grants no target authority, programme permission, key-provider approval,
  VPS suitability, or posture transition. `LOCAL_FIXTURE` remains mandatory.
