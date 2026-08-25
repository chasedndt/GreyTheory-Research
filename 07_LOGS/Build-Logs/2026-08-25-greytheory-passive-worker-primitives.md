# GreyTheory passive worker primitives - 2026-08-25

## Repository truth

- Starting commit: `753e7f28249b28add94505b3815964685656d909`.
- Worktree: `E:\ChaseOSBuilds\2026-08-24-greytheory-workbench-foundation\worktree`.
- Branch: `codex/2026-08-24-greytheory-workbench-foundation`.
- E: had 686.42 GiB free during final verification.
- Canonical ChaseOS remained read-only with seven unrelated working-tree
  changes preserved at final verification.

## Repo-truth delta

The passive broker and adapter contract could prove exact orchestration using
injected results, but no concrete code isolated blocking DNS, forced a numeric
socket connect, configured TLS independently of ambient proxy/CA/key-log state,
or enforced deadline and header limits at the socket boundary.

## Change

- Added `CancellableSystemResolver`: it validates the host, resolves the
  trailing-dot absolute name in one owned `spawn` child, returns no more than 64
  addresses over capped UTF-8 JSON bytes rather than pickle, and terminates/
  kills only that exact child at the total deadline.
- Added `DirectTlsHeadTransport`: it creates IPv4/IPv6 sockets for the selected
  numeric address, never invokes a URL/proxy/resolver API, and retains the host
  only for SNI, certificate hostname verification, and the fixed Host header.
- Required an explicit existing CA file, TLS 1.2+, `CERT_REQUIRED`, HTTP/1.1
  ALPN, disabled compression/renegotiation where supported, and disabled TLS
  key logging. Connect, handshake, write, and read consume one shared deadline.
- Added exact peer verification, signed-ceiling streaming reads, rejection of
  any observed body bytes, deterministic close, and specific timeout/capture
  exceptions mapped by the adapter into signed stops.
- Added the `passive-worker` optional dependency extra but no executable entry
  point, service, default secret/CA, ticket source, or posture route.

## Safety boundary

- Every test injects process, pipe, resolver, socket, TLS context/socket, and
  monotonic time. No real DNS query, connect, TLS handshake, or HTTP request ran.
- The package is unlaunched. There is no worker service/image, broker transport,
  worker identity, evidence path, scheduler, egress policy, canary, programme,
  VPS, or target action.
- Ubuntu cancellation, peer binding, CA/hostname behavior, streaming cleanup,
  service confinement, and egress are unverified until local VM acceptance.
- `PASSIVE_HTTP` remains unavailable; posture remains `LOCAL_FIXTURE`.
- No deployment, push, merge, secret use, target contact, canonical write, or
  posture change occurred.

## Verification

- Focused primitive/adapter/broker/encryption/capability suite:
  `75 passed in 14.65s`.
- Full repository suite with pytest temp and bytecode paths rooted on E::
  `643 passed in 153.38s`.
- `python -m compileall -q greytheory greytheory_app greytheory_local
  greytheory_broker greytheory_worker_contract greytheory_worker` passed with
  bytecode on E:.
- Tests cover absolute-name lookup, capped JSON child protocol, malformed/
  oversized child messages, normal and forced owned-child termination, spawn
  failure, finite deadlines, numeric IPv4/IPv6 connects, exact SNI/wire bytes,
  explicit CA/TLS settings, key-log disablement, peer/ALPN mismatch, timeout,
  overflow, unexpected body/incomplete headers, and close on every result.

## Remaining

- Select an approved local OS secret provider and backup/recovery process for
  the root KEK.
- Assemble an authenticated broker transport and unprivileged service in a
  dedicated local Ubuntu 24.04 VM with deny-by-default egress.
- Pass real host conformance, owned-canary, one-programme review, sustained
  clean operation, and explicit human posture approval before any target I/O.
- Operator selection and implementation of visual direction 1, 2, or 3.
