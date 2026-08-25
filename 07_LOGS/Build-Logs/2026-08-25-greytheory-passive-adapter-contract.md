# GreyTheory passive adapter contract - 2026-08-25

## Repository truth

- Starting commit: `9f0b6c704b129876d7b42a7c6d1811ce9b374d0b`.
- Worktree: `E:\ChaseOSBuilds\2026-08-24-greytheory-workbench-foundation\worktree`.
- Branch: `codex/2026-08-24-greytheory-workbench-foundation`.
- E: had 686.45 GiB free during final verification.
- Canonical ChaseOS remained read-only and reported no working-tree changes at
  final verification.

## Repo-truth delta

The dark broker could admit, encrypt, and receipt one passive action, but no
typed boundary forced a future resolver and transport to prove exact numeric
address use, matching TLS name, no proxy/redirect/body behavior, one bounded
header block, or a total monotonic deadline before their evidence was accepted.

## Change

- Added the network-free `greytheory_worker_contract` package with injected
  resolver and transport protocols; it imports no DNS, socket, TLS, HTTP,
  proxy-capable client, browser, subprocess, or worker implementation.
- Added a full direct-request digest over ticket, canonical URL/host/path,
  selected public numeric address, TLS name, method, port, proxy/redirect modes,
  capture ceiling, deadline, and exact wire bytes.
- Required matching typed transport evidence, no proxy, no followed redirect,
  zero body bytes, closed connection, consistent monotonic timing, and one
  strict HTTP/1.x header block with explicit single Content-Type.
- Encrypted the exact header bytes and derived broker completion metadata from
  that envelope. Resolver, transport, parsing, redirect, size, clock,
  encryption, kill-switch, and deadline failures seal signed stop receipts.
- Tightened the canonical URL policy to ASCII IDNA host plus percent-encoded
  ASCII path so the signed URL has one wire request-target representation.

## Safety boundary

- Tests use injected deterministic doubles only. No DNS query, socket, TLS
  handshake, certificate validation, HTTP call, proxy lookup, process, worker,
  canary, programme, or target action exists.
- This proves contract orchestration, not OS cancellation, egress control,
  no-re-resolution behavior, kernel limits, service isolation, or host
  acceptance.
- `PASSIVE_HTTP` remains unavailable and the posture remains `LOCAL_FIXTURE`.
- No deployment, push, merge, secret use, target contact, canonical write, or
  posture change occurred.

## Verification

- Focused adapter/broker/encryption/capability suite: `53 passed in 9.43s`.
- Full repository suite with pytest temp and bytecode paths rooted on E::
  `621 passed in 67.91s`.
- `python -m compileall -q greytheory greytheory_app greytheory_local
  greytheory_broker greytheory_worker_contract` passed with bytecode on E:.
- Tests prove exact request/address/TLS binding, request-digest sensitivity,
  public-only complete DNS admission, one transport call, direct fixed wire
  request, encrypted raw headers, and signed denial paths for every boundary
  listed above.
- Relative Markdown links passed for all 16 changed/new documentation files;
  `git diff --check` passed.

## Remaining

- Implement an OS-cancellable complete-answer resolver and direct numeric TLS
  transport behind the contract, with streaming enforcement and no
  re-resolution, inside the isolated Ubuntu worker only.
- Select and accept an OS secret provider for the root KEK, build the local
  Ubuntu image/service/broker transport, pass owned-canary and sustained clean
  operation, then require explicit human posture approval.
- Operator selection and implementation of visual direction 1, 2, or 3.
