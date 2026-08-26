# ADR-0018: Keep broker authority outside the passive worker process

**Status:** Accepted

**Date:** 2026-08-26

## Context

GreyTheory already had a signed passive ticket, replay ledger, kill switch,
capture encryption, adapter contract, and OS-facing resolver/TLS primitives.
Simply constructing all of them inside one Ubuntu service would give the
lower-trust worker receipt-signing authority, replay state, kill-switch access,
and unnecessary visibility into the operator environment. It would also make a
compromised worker capable of resolving and connecting without the broker
checking the complete DNS answer between those phases.

## Decision

The first worker assembly is an owned spawned process with a fixed two-command
protocol:

1. the trusted parent verifies and reserves the one-use ticket, checks the
   default-engaged kill switch, and sends one canonical hostname plus the shared
   monotonic deadline;
2. the worker performs one cancellable absolute-name system resolution and
   returns a typed, capped JSON result;
3. the parent applies the broker's public-address policy to the complete answer
   and constructs one full-request-digest-bound exact-address request;
4. the worker accepts that request only when its hostname matches the first
   phase and its numeric address appeared in the worker's own answer;
5. the worker performs one direct TLS `HEAD`, returns one typed bounded header
   result, and exits; and
6. the parent parses the response, encrypts the capture to the operator-held
   recipient, seals the receipt, and completes replay state.

The worker child receives only its private process channel and an explicit CA
file path. It receives no ticket or receipt signing key, capture private key,
replay database, kill-switch authority, research store, credentials, or second
action. Its environment is reduced to fixed locale/no-bytecode keys. The parent
refuses the worker unless it reports Linux, non-root UID/GID, no foreign
supplementary group, zero effective and bounding capabilities, and
`NoNewPrivs=1`. Frames are canonical JSON capped at 196,608 bytes; they are not
pickle and their schemas and sequence are exact.

On Linux, the parent starts the worker through a clean multiprocessing fork
server preloaded only with the worker service module. It does not fork the
broker process and therefore cannot inherit broker keys or state. Once the
worker has scrubbed its environment and has no broker authority, it may fork
one cancellable resolver child; this avoids a second full application spawn
inside the signed 30-second action ceiling without weakening the parent/worker
boundary. Non-Linux fallback remains spawn-based and cannot satisfy the Linux
identity admission contract.

There is no CLI, scheduler, listener, service manager, programme route, default
CA, or posture switch. The included host harness is safe only inside its
ephemeral no-default-route namespace and does not enable `PASSIVE_HTTP`.

## Consequences

- A compromised worker cannot mint or sign a new action or receipt, release the
  kill switch, reset replay state, or read the private research store through
  the protocol.
- DNS and connection remain distinct phases, allowing the trusted broker to
  reject private, metadata, mixed, or otherwise invalid answers before TCP.
- A crash consumes rather than replays the ticket, and the parent terminates
  and reaps only the exact owned worker process on timeout or protocol failure.
- The implementation and unit contract do not prove Ubuntu host behavior.
  Recovered attempts fixed multiple wrapper/fixture/startup defects but shared
  WSL/Hermes startup instability prevented a complete JSON record, so
  successful real system DNS, full-path host acceptance, durable egress,
  hardened image,
  approved root-KEK provider, and VM/VPS acceptance remain open.
- `PASSIVE_HTTP` remains unavailable and operating posture remains
  `LOCAL_FIXTURE`.
