# GreyTheory passive broker foundation - 2026-08-25

## Repository truth

- Starting commit: `91d3ba2f6167d0280c75c08b7a74afb3e2fbc0f1`.
- Worktree: `E:\ChaseOSBuilds\2026-08-24-greytheory-workbench-foundation\worktree`.
- Branch: `codex/2026-08-24-greytheory-workbench-foundation`.
- Agent Bus readiness was green with zero open tasks.
- Canonical ChaseOS remained read-only; its unrelated dirty state was untouched.

## Repo-truth delta

Before this pass, Milestone 9 named broker, DNS, redirect, rate, kill-switch,
receipt, and data controls but supplied no separate broker protocol. The only
executable path was the in-memory `LOCAL_FIXTURE` action. `PASSIVE_HTTP` and the
worker were correctly unavailable.

## Change

- Added the separate `greytheory_broker` package with no network/process
  adapter; the optional broker extra uses Ed25519 from `cryptography` while the
  base trust kernel retains zero dependencies.
- Defined `passive-head-v1`: one exact unauthenticated canonical HTTPS `HEAD`,
  one request, zero redirects, public DNS answers only, 30-second and 64-KiB
  ceilings, and an explicit programme rate capped at 1 rps.
- Bound ticket issuance to the latest fresh hash-chain-verified Gate audit
  allow, exact request, contract id/fingerprint, and exact `PASSIVE_HTTP`
  posture ceiling.
- Added asymmetric Ed25519 tickets/receipts, default-engaged digest-protected kill switch,
  SQLite exact-once reservation, atomic same-host rate enforcement, and signed
  completed/stopped receipts.
- Required `UNTRUSTED` / `RAW_RESTRICTED` data labels and both capture and
  encrypted-envelope digests before a receipt can be completed.
- Added the programme rate to `ScopeContract.fingerprint()` so changing a
  substantive request ceiling invalidates prior authority.
- Accepted ADR-0011 and reconciled capability, roadmap, threat-model, project,
  workbench, changelog, and governed-log truth.

## Safety boundary

- Operating posture remains `LOCAL_FIXTURE`.
- `passive_broker_foundation` is `PARTIAL`; `passive_http_worker` remains
  `UNAVAILABLE`.
- No DNS lookup, HTTP request, socket, subprocess, browser, target, external
  model, credential, capture encryption, provisioned key, VM/VPS worker,
  deployment, publication, push, or canonical mutation occurred.
- The test suite raises a synthetic Gate posture only inside offline fixtures;
  it contacts no host and does not alter runtime posture.

## Verification

- Broker file: 15 conformance tests passed as part of the focused suite.
- Integrated broker/scope/capability/registry/Gate/approval suite:
  `118 passed in 4.52s`.
- Full repository suite with pytest artifacts on E:: `571 passed in 24.50s`.
- Byte-compilation of `greytheory`, `greytheory_app`, and `greytheory_broker`
  passed with the Python cache redirected to E:.
- Setuptools discovery included `greytheory_broker`; all local links in the 17
  changed Markdown files resolved; `git diff --check HEAD` passed.
- Tests cover canonical URL/IDNA, private/metadata/mixed DNS refusal, audit
  tampering/freshness, contract status, ticket tampering/expiry, default and
  corrupt kill switch, replay, cross-ticket host rate, encrypted-capture
  receipt round-trip/tampering, Ed25519 public/private key separation, redirect,
  size, timeout, runtime storage guard, and the absence of network/process
  adapter imports.

## Remaining

- Capture encryption and key provisioning/rotation.
- Actual DNS/HTTP adapter with connect-to-validated-address, proxy disablement,
  streaming limits, cancellation, and conformance hooks.
- Broker transport/authentication and an unprivileged Ubuntu 24.04 worker image.
- Local VM acceptance, owned canary, one reviewed programme, sustained clean
  operation, and explicit operator posture approval.
- Graphical workbench selection and implementation remain a separate open lane.
