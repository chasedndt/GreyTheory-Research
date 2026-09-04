# ADR-0021: Authenticate the isolated worker session before choosing a carrier

**Status:** Accepted as a protocol foundation; carrier and host acceptance open

**Date:** 2026-09-04

## Context

The existing owned-process worker uses a private process pipe and already
enforces the exact `resolve -> resolution -> head -> transport` exchange. That
is sufficient for the current same-host fixture, but it is not an authenticated
broker transport for a separately booted local VM. Choosing a socket or VM
carrier first would leave mutual identity, confidentiality, replay, ordering,
and framing behavior to an eventual deployment script.

The channel must not move broker authority into the worker. In particular, the
worker must never receive the ticket/receipt signing keys, capture private key,
replay ledger, kill-switch authority, research store, credentials, or a second
action.

## Decision

Implement `greytheory_worker_transport` as a carrier-neutral, launch-dark
protocol foundation:

1. The broker and worker identities are separately pinned Ed25519 keys. Each
   side signs its exact canonical hello; the worker hello binds the broker
   hello digest, session identifier, both identity-key identifiers, broker
   nonce, expiry, and fresh worker ephemeral key.
2. Each side creates a fresh X25519 ephemeral key. The complete signed
   transcript is the HKDF-SHA-256 salt and the versioned protocol name is the
   derivation context. Two different 256-bit directional keys result.
3. No command is available before both signed hellos are authenticated. This
   explicitly excludes a zero-round-trip-data path.
4. Every application frame is ChaCha20-Poly1305 encrypted and authenticated.
   Session id, transcript digest, direction, sequence, and message type are
   authenticated as associated data. A role-specific prefix plus a 64-bit
   sequence supplies a unique 96-bit nonce for each directional key.
5. The only valid sequence is `resolve(1) -> resolution(1) -> head(2) ->
   transport(2)`. A typed error may replace either worker response and closes
   the session. Final frames erase the session key buffers on a best-effort
   basis.
6. Handshake lifetime is at most 30 seconds. Frames and handshakes are strict,
   duplicate-key-free canonical JSON capped at 196,608 bytes.
7. Worker acceptance requires an injected replay guard to atomically consume
   the broker-hello digest. The included bounded in-memory guard is only for
   tests and a one-shot process; a reboot-conformant carrier must provide a
   durable implementation.

The implementation uses maintained `cryptography` primitives rather than
implementing curve or AEAD arithmetic. Its construction follows the relevant
IETF constraints: X25519 public keys are included in the authenticated
transcript and invalid shared secrets fail closed; HKDF uses an authenticated
transcript salt and versioned context; and ChaCha20-Poly1305 nonces are unique
per directional key. See [RFC 7748](https://www.rfc-editor.org/rfc/rfc7748),
[RFC 5869](https://www.rfc-editor.org/rfc/rfc5869),
[RFC 8032](https://www.rfc-editor.org/rfc/rfc8032), and
[RFC 8439](https://www.rfc-editor.org/rfc/rfc8439). The refusal to carry a
command before mutual authentication also follows the conservative lesson from
[TLS 1.3's early-data replay analysis](https://www.rfc-editor.org/rfc/rfc8446).

## Consequences

- Broker/worker identity, forward-secret session derivation, encrypted framing,
  direction, ordering, expiry, and replay behavior are now executable and
  network-free rather than deferred prose.
- Existing `ResolutionResult`, `DirectHeadRequest`, and `HeadTransportResult`
  records round-trip through the authenticated channel in tests.
- No socket, listener, VM, Hyper-V socket, AF_VSOCK binding, process launcher,
  scheduler, service manager, key provisioning, or target route is added.
- The in-memory replay guard is not reboot evidence. Worker identity-key
  provisioning, durable replay state, carrier binding, peer/VM identity
  admission, cryptographic review, negative host tests, and reboot conformance
  remain open.
- This is not accepted authenticated broker transport and does not complete the
  Milestone 9 transport gate. `PASSIVE_HTTP` remains unavailable and posture
  remains `LOCAL_FIXTURE`.
