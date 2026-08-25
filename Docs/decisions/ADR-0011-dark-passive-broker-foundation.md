# ADR-0011 - Build the passive broker dark before adding a network adapter

**Status:** Accepted - 2026-08-25

**Relates to:** Milestone 9 and ADR-0010.

## Context

Milestone 9 cannot begin safely with an HTTP client. The preconditions are the
admission and containment rules around the client: a current Gate decision,
canonical target, DNS result, request/rate/time/size limits, replay protection,
kill switch, evidence handling, and a receipt that can be verified after a
lower-trust worker returns it.

Putting those rules inside a future HTTP callback would make them difficult to
test independently and easy for another adapter to omit. Implementing a worker
first would also create target-network capability before the operator has
approved the posture transition.

## Decision

Create a separate `greytheory_broker` package with no network or process
adapter. The base trust kernel remains dependency-free; the broker uses the
optional `cryptography` extra for Ed25519 signatures. Its first policy is
`passive-head-v1`:

- exactly one unauthenticated `HEAD` to one canonical HTTPS URL;
- DNS hostname only, IDNA ASCII form, port 443, and no userinfo, query,
  fragment, path traversal, or ambiguous encoded delimiter;
- one request, zero followed redirects, at most 64 KiB of capture metadata,
  at most 30 seconds, and an explicit programme rate capped at 1 rps;
- every DNS answer must be non-empty and contain only globally routable
  addresses; mixed public/private answers deny the attempt;
- ticket issuance requires the exact hash-chain-verified `gate.evaluate`
  record, matching request, contract fingerprint/id, `PASSIVE_HTTP` posture
  ceiling, and an allow no more than 30 seconds old;
- tickets are Ed25519-signed, expire within five minutes, and are reserved once
  in a SQLite ledger before DNS; a worker receives the public verifier but not
  the broker private key, so it cannot mint tickets; a crash consumes rather
  than replays a ticket;
- the persistent kill switch fails engaged when absent, unreadable, or corrupt
  and requires an authorization reference to release;
- target material remains `UNTRUSTED` and `RAW_RESTRICTED`; a completed receipt
  requires both the capture digest and the encrypted-envelope digest; and
- completed and stopped receipts are Ed25519-signed by the worker and bound to
  the ticket digest; the broker needs only the worker public verification key.

The v1 policy denies every redirect rather than trying to infer whether a new
location inherits scope. A future policy may admit a redirect only after a new
broker-side Gate/scope/DNS decision and a new acceptance record.

## What this does not authorize or implement

- no DNS query, socket, HTTP request, browser action, subprocess, or worker;
- no capture encryption algorithm or key-distribution implementation;
- no key provisioning, rotation, hardware binding, or remote attestation;
- no Ubuntu image, service manager, VM, VPS, tunnel, or scheduler;
- no live programme, canary, sustained-operation evidence, or posture change.

The executable capability register therefore marks the broker foundation
`PARTIAL` and the passive HTTP worker `UNAVAILABLE`. `LOCAL_FIXTURE` remains the
only current operating posture.

## Consequences

A future adapter has a small state machine it must call before DNS, before a
connection, and before accepting evidence. Its conformance suite can mutate
tickets, DNS answers, timing, redirects, capture sizes, kill-switch state, and
receipts without any network traffic.

The receipt metadata proves that a worker reported compliance with the signed
limits; it is not proof that an untrusted or compromised host actually obeyed
them. The Ubuntu worker still needs isolation, OS-level egress constraints,
capture encryption, key management, independent broker verification, and
sustained canary acceptance before it can contact any target.
