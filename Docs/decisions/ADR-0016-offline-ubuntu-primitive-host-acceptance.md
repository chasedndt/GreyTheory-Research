# ADR-0016: Accept Ubuntu primitives in an offline network namespace

**Status:** Accepted

**Date:** 2026-08-25

## Context

The passive resolver and direct-TLS primitives had deterministic syscall-injected
coverage, but those tests could not prove Linux process cancellation, real TLS
hostname verification, socket streaming, or cleanup. Contacting a public host to
obtain that proof would cross the current `LOCAL_FIXTURE` posture, and a loopback
address cannot satisfy the production `DirectHeadRequest` public-address rule.

The operator workstation already provides Ubuntu 24.04 through WSL2. Host proof
must be reproducible there without treating WSL as the final worker image or
granting it target authority.

## Decision

GreyTheory accepts primitive-layer Ubuntu behavior through an ephemeral Linux
user and network namespace created with `unshare -Urn`:

1. the namespace exposes only loopback and has no default route;
2. `8.8.8.8/32` is assigned to loopback only inside the namespace, allowing the
   unchanged production public-address contract to be exercised without any
   packet leaving the namespace;
3. a repository-owned TLS canary binds that synthetic address on port 443 with
   a public test-only CA/key for `greytheory-canary.invalid`;
4. the production `DirectTlsHeadTransport` must connect numerically while a
   patched `getaddrinfo` fails if any re-resolution is attempted;
5. the canary splits one bounded response header across two writes, and the
   transport must return the exact header block, zero body bytes, no proxy or
   redirect, and a closed connection;
6. a second handshake with a mismatched hostname must fail;
7. the production resolver parent is exercised with a real spawned child that
   deliberately blocks, proving deadline termination and reaping without a DNS
   query; and
8. the harness emits JSON stating that external contact, worker assembly, and
   `PASSIVE_HTTP` enablement are false.

The PowerShell wrapper and Python harness live under `acceptance/`. The synthetic
address is not a target and must never be used outside the no-route namespace.

## Consequences

- Linux process, socket, and TLS behavior is now stronger than injected-test
  evidence alone.
- The proof is local, repeatable, and makes no external request.
- The test certificate private key is intentionally public fixture material and
  has no authority or production use.
- Effective UID 0 inside the mapped user namespace is not proof of a hardened
  unprivileged worker image.
- The replacement blocking child proves the production resolver parent's spawn,
  cancellation, and cleanup path; it does not prove successful real system DNS.
- The full adapter, encrypted capture, broker transport, worker identity, OS-bound
  root KEK, durable egress policy, VM/VPS image, authorised canary, sustained
  operation, and posture approval remain unbuilt or unaccepted.
- `PASSIVE_HTTP` remains unavailable.
