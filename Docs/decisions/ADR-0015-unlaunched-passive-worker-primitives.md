# ADR-0015 - Implement passive worker primitives without launching them

**Status:** Accepted - 2026-08-25

**Relates to:** Milestone 9, ADR-0011, ADR-0013, and ADR-0014.

## Context

ADR-0014 proves the passive orchestration contract with injected resolver and
transport results, but an Ubuntu worker still needs concrete OS mechanics. A
normal URL client is unsuitable: it may consult proxy environment variables,
re-resolve the hostname after broker validation, follow redirects, negotiate a
different protocol, read an unbounded response, or expose TLS keys through an
ambient key-log setting. Blocking system DNS also needs real cancellation at
the shared ticket deadline.

Adding these primitives must not silently create a runnable worker or imply
that Windows, Ubuntu, a VM, or a VPS has accepted them.

## Decision

Create an unlaunched `greytheory_worker` package with two primitives:

1. `CancellableSystemResolver` validates the canonical hostname, appends a
   trailing dot to suppress resolver search-suffix expansion, and calls the
   blocking system resolver in one specifically owned `spawn` child. The child
   returns at most 64 addresses through capped UTF-8 JSON bytes, not pickle.
   At the total deadline the parent terminates, joins, and if necessary kills
   only that exact child object.
2. `DirectTlsHeadTransport` creates an IPv4 or IPv6 stream socket directly for
   the contract's numeric address. The canonical hostname appears only as TLS
   SNI/hostname verification and the fixed HTTP Host header; no URL library,
   proxy API, or second resolver is used.

The TLS transport requires an explicit existing CA bundle, `CERT_REQUIRED`,
hostname checking, TLS 1.2 or newer, HTTP/1.1-only ALPN, disabled compression
and renegotiation where supported, and an explicitly disabled TLS key-log
filename. Connect, handshake, write, and every read use the remaining shared
monotonic deadline. It verifies the peer address, sends the contract-owned
`HEAD`, captures no more than the signed header ceiling, rejects any bytes
after the first header block, and closes the owned socket on every path.

The adapter maps primitive timeout and streaming-ceiling exceptions to signed
stop receipts. The package has no CLI, service manager, scheduler, ticket
source, broker transport, posture switch, evidence path, or default CA/secret.

## Consequences

The implementation no longer depends on a future developer choosing safe DNS,
proxy, TLS, deadline, and read behavior from scratch. The resolver process is
individually attributable and cancellable; the TLS path cannot re-resolve the
broker-selected address through a URL client.

All repository verification replaces process, pipe, socket, TLS context, TLS
socket, and monotonic time with deterministic doubles. No DNS query or network
connection is made, so this is not Ubuntu or network acceptance. A dedicated
local Ubuntu 24.04 VM must still prove actual cancellation, CA/hostname checks,
numeric peer binding, streaming ceilings, cleanup, egress policy, service
identity, broker transport, encrypted evidence return, and an owned canary.
`PASSIVE_HTTP` remains unavailable and posture remains `LOCAL_FIXTURE`.
