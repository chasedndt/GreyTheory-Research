# Vulnerability Coverage Matrix

**Detection coverage today: three static, offline collectors. Learning coverage:
twelve synthetic local fixtures.** A learning fixture is not a target collector,
real-session example, or vulnerability claim.

The implemented lanes read local files only. The card fixtures execute distinct
in-memory security-property simulations with synthetic data and no network,
browser, model, process, credential, or target. Every network-based class below
still needs an explicit posture decision above `LOCAL_FIXTURE`.

Read alongside the capability register in
[`definition.md`](definition.md#6-capability-register).

## Legend

| Status | Meaning |
|---|---|
| `NOT BUILT` | No current implementation |
| `DESIGNED` | Specified to build-ready detail |
| `STATIC` | Implemented local-file signal collector; no reachability claim |
| `LOCAL LAB` | Synthetic card fixture implemented and tested; no target detection |

Implemented collectors: `lane1_dependency_manifest`, `lane2_exposure`, and
`lane4_agent_config`. Implemented labs: one distinct fixture for each of the 12
Milestone 5 cards.

## Lane 1 — Known vulnerability

| Class | Status | Deterministic check it would need | Notes |
|---|---|---|---|
| Version-matched CVE | `STATIC` | Version string → CVE range match | `lane1_dependency_manifest`; match alone is `contextual`, never a vulnerability claim |
| Exposed known-vulnerable component | `NOT BUILT` | Fingerprint + reachable path confirmation | Requires network posture |
| Default credentials | `NOT BUILT` | Exact approved credential check | Requires `AUTHENTICATED`; human-approved per instance, never swept |
| Container / dependency CVE | `STATIC` | Manifest parse + advisory match | Ecosystem-aware matching over imported OSV data; reachability is separate |

## Lane 2 — Exposure

| Class | Status | Deterministic check it would need | Notes |
|---|---|---|---|
| Exposed `.env` / config | `STATIC` | Assignment shape + entropy, placeholders excluded | Local-tree presence, not reachability |
| Exposed VCS directory | `STATIC` | Directory presence in the granted tree | `.git`, `.svn`, `.hg`, and `.bzr` |
| Open object storage | `NOT BUILT` | Listing response parse | Derived assets need independent scope and network posture |
| Secrets in JavaScript bundles | `STATIC` | Known credential formats + entropy | Records shape and digest, never the value; live validation remains intrusive |
| Exposed backups / archives | `STATIC` | Suffix match | The file is never opened |
| Debug endpoints and stack traces | `NOT BUILT` | Response signature | Usually informational alone |

## Lane 3 — Web vulnerability

| Class | Status | Deterministic check it would need | Notes |
|---|---|---|---|
| Subdomain takeover | `NOT BUILT` | CNAME → unclaimed-service fingerprint | Intended first binary-proof network module |
| IDOR / BOLA | `LOCAL LAB` | Cross-account response + ownership oracle | Complete in-memory Milestone 4 slice and test-fixture-sourced card revision; no live collector |
| Broken function-level authorisation | `LOCAL LAB` | Role × function matrix difference | Synthetic two-role property fixture only |
| Business-logic authorisation | `LOCAL LAB` | State-machine invariant break | Synthetic reversible workflow fixture only |
| CSRF | `LOCAL LAB` | Intent-bound state-change comparison | Synthetic reversible state fixture only |
| Session-management weakness | `LOCAL LAB` | Before/after invalidation comparison | Opaque synthetic handles only |
| SSRF | `LOCAL LAB` | Controlled destination-policy result | Dictionary-backed fixture; no socket, DNS, redirect, or callback |
| Reflected / stored / DOM XSS | `LOCAL LAB` | Source/output-context control comparison | Three marker-only fixtures; no payload, browser, or target |
| SQL injection | `LOCAL LAB` | Query-structure comparison | Read-only synthetic query construction; no database target |
| Race conditions | `NOT BUILT` | Concurrent outcome divergence | No concurrency fixture or collector |
| NoSQL / command injection | `NOT BUILT` | Controlled differential or out-of-band result | No card in the first Milestone 5 set |

## Lane 4 — AI-app vulnerability

| Class | Status | Deterministic check it would need | Notes |
|---|---|---|---|
| Indirect prompt injection with consequence | `STATIC + LOCAL LAB` | Untrusted content → privileged action trace | Static risky-shape signal plus model-free instruction/data fixture; neither proves a live consequence |
| Tool-authorisation failure | `STATIC + LOCAL LAB` | Exact decision/action/target/effect binding | Static wildcard/ungated signal plus no-effect one-use-ticket fixture |
| Approval-gate bypass | `STATIC` | Consequential tool with no approval requirement | `lane4_agent_config`; no tool is invoked |
| Insecure MCP transport or permissions | `STATIC` | Plaintext scheme to a non-loopback host | Configuration signal only |
| Cross-tenant context leakage | `NOT BUILT` | Tenant A data in a tenant B response | Requires explicit AI asset and account authority |
| Memory poisoning | `NOT BUILT` | Persisted untrusted claim reaching privileged context | |
| Excessive agency | `NOT BUILT` | Action beyond declared scope | |
| Audit tampering | `NOT BUILT` as target test | Chain-verification failure | GreyTheory's own audit log is the local control reference |

## Deprioritised regardless of lane

Low-signal classes do not enter the future hypothesis queue unless a programme
explicitly rewards them and impact is demonstrable: missing security headers,
version disclosure, self-XSS, generic open redirect, absent rate limiting with
no consequence, CORS on non-sensitive endpoints, clickjacking without a
meaningful action, and scanner-only outdated-library reports.

## Build order

1. Deterministic, static, no network — **done**.
2. Agent and exposure local fixtures — **done**.
3. Local-tree exposure lane — **done**.
4. Twelve vulnerability-card property fixtures and skill graph — **done**.
5. Binary-proof network lane — subdomain takeover.
6. Live authorisation lanes — only against a separately authorised,
   controlled multi-account target.

Steps 5 onward require the posture ceiling to be raised above `LOCAL_FIXTURE`.
That is a separate operator decision, and the runner refuses any lane declaring
network I/O until collectors move outside the core package and every threat-model
precondition is tested.
