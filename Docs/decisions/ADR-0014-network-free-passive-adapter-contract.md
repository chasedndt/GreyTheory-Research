# ADR-0014 - Prove the passive adapter contract without adding network I/O

**Status:** Accepted - 2026-08-25

**Relates to:** Milestone 9, ADR-0011, and ADR-0013.

## Context

The dark broker now admits one signed action and can encrypt its capture, but
an HTTP implementation could still weaken the design by re-resolving a host,
honouring ambient proxies, following a redirect, reading a body, exceeding the
header or time ceiling, or returning metadata unrelated to the exact request.
Building a socket implementation and discovering those omissions together
would create target-network capability before its contract was independently
testable.

## Decision

Create a separate, network-free `greytheory_worker_contract` package. It
orchestrates injected resolver and transport protocols but imports no DNS,
socket, TLS, HTTP, proxy, browser, or process implementation.

The contract:

- accepts one typed complete DNS result for the exact canonical host and passes
  every returned address through the broker's global-address policy;
- chooses one canonical public numeric address and creates a direct request
  bound to it, while retaining the canonical host as the TLS server name and
  HTTP Host header;
- fixes method `HEAD`, port 443, proxy mode `disabled`, redirect mode
  `record_only`, identity encoding, connection close, capture ceiling, and one
  monotonic deadline;
- hashes the ticket, URL, host, request target, numeric address, TLS name,
  method, port, proxy/redirect modes, capture ceiling, deadline, and exact wire
  bytes into the request identity;
- accepts only typed transport evidence matching that full request, exact
  address, and TLS name, with no proxy, no followed redirects, no body bytes,
  a closed connection, and consistent monotonic timing;
- parses exactly one complete HTTP/1.0 or HTTP/1.1 header block, rejects
  folding, duplicate or absent Content-Type, multiple Location headers, body
  bytes, controls, more than 100 headers, redirects, and signed-size overflow;
- encrypts the exact header bytes to the ticket recipient and lets the broker
  derive and sign the completed receipt; and
- converts resolver, transport, clock, parsing, redirect, size, encryption,
  kill-switch, and deadline failures into a broker-signed stop receipt.

The URL policy also requires an ASCII IDNA host and percent-encoded ASCII path
so the signed canonical URL has one unambiguous HTTP request-target encoding.

## Consequences

The future Ubuntu implementation has a narrow interface and an executable
denial suite before it can open a socket. A transport cannot satisfy the
contract by returning a response from another IP, host, ticket, deadline, or
wire request. Capture plaintext remains `RAW_RESTRICTED` and is encrypted
before a completed receipt is accepted.

This is evidence about orchestration, not OS behavior. No actual DNS resolver,
socket, TLS handshake, certificate check, HTTP write/read, kernel cancellation,
egress control, service, worker image, broker transport, canary, VPS, or target
action exists. Those implementations require Ubuntu-host conformance and the
remaining Milestone 9 gates. `PASSIVE_HTTP` remains unavailable and posture
remains `LOCAL_FIXTURE`.
