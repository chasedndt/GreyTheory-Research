# Vulnerability Coverage Matrix

**Coverage today: none.** No lane is implemented. This matrix is the intended Signal Plane surface and the order it will be built in — it is a plan, not a capability claim.

Read alongside the capability register in [`definition.md`](definition.md#6-capability-register).

## Legend

| Mark | Meaning |
|---|---|
| ⬛ | Not built |
| ◐ | Designed to build-ready detail |
| ✅ | Implemented and tested |

Nothing is currently anything other than ⬛.

## Lane 1 — Known vulnerability

| Class | Status | Deterministic check it would need | Notes |
|---|---|---|---|
| Version-matched CVE | ⬛ | Version string → CVE range match | Match alone is `contextual` at best; reachability is a separate proof |
| Exposed known-vulnerable component | ⬛ | Fingerprint + reachable path confirmation | |
| Default credentials | ⬛ | — | Requires `AUTHENTICATED`. Human-approved per instance, never swept |
| Container / dependency CVE | ⬛ | Manifest parse + advisory match | Static; no target interaction needed |

## Lane 2 — Exposure

| Class | Status | Deterministic check it would need | Notes |
|---|---|---|---|
| Exposed `.env` / config | ⬛ | Content-shape match, not just status code | 200 with an HTML error page is not an exposure |
| Exposed `.git` directory | ⬛ | Index header signature | |
| Open object storage | ⬛ | Listing response parse | Derived asset — needs independent scope |
| Secrets in JavaScript bundles | ⬛ | Entropy + format match | Validation of a live secret is `INTRUSIVE`, opt-in, never automatic |
| Exposed backups / archives | ⬛ | Magic-byte check | |
| Debug endpoints, stack traces | ⬛ | Response signature | Usually `informational` alone |

## Lane 3 — Web vulnerability

| Class | Status | Deterministic check it would need | Notes |
|---|---|---|---|
| Subdomain takeover | ⬛ | CNAME → unclaimed-service fingerprint | Binary proof model; intended first Lane 3 module |
| IDOR / BOLA | ⬛ | Cross-account response comparison | The primary specialism. Needs two controlled accounts |
| Broken function-level authorization | ⬛ | Role × endpoint matrix diff | |
| Business logic / workflow abuse | ⬛ | State-machine invariant break | Hardest to automate, highest value |
| Race conditions | ⬛ | Concurrent-request outcome divergence | |
| SSRF | ⬛ | Owned callback receipt | Deferred; tightly controlled only |
| XSS (reflected / stored / DOM) | ⬛ | Sink execution confirmation | Commodity class, high duplicate pressure |
| SQL / NoSQL / command injection | ⬛ | Differential response or out-of-band signal | |

## Lane 4 — AI-app vulnerability

The differentiated lane, and the one where agent-harness work is an advantage rather than table stakes.

| Class | Status | Deterministic check it would need | Notes |
|---|---|---|---|
| Indirect prompt injection with consequence | ⬛ | Untrusted content → privileged action trace | A jailbreak with no consequence is not a vulnerability |
| Tool authorization bypass | ⬛ | Tool invoked outside its permission set | |
| Approval-gate bypass | ⬛ | Gated action executed without an approval record | Directly transferable to ChaseOS |
| Cross-tenant context leakage | ⬛ | Tenant A data in a tenant B response | |
| Memory poisoning | ⬛ | Persisted untrusted claim reaching a privileged prompt | |
| Insecure MCP transport or permissions | ⬛ | Config + transport inspection | Static |
| Excessive agency | ⬛ | Action taken beyond declared scope | |
| Audit tampering | ⬛ | Chain verification failure | GreyTheory's own audit log is the reference implementation |

## Deprioritised regardless of lane

Low-signal classes that will not enter the hypothesis queue unless a programme explicitly rewards them and impact is demonstrable: missing security headers, version disclosure, self-XSS, generic open redirect, absent rate limiting with no consequence, CORS on non-sensitive endpoints, clickjacking without a meaningful action, and scanner-only outdated-library reports.

## Build order

1. Deterministic, static, no network — dependency/manifest CVE matching, MCP config inspection.
2. Local fixture lanes — a deliberately vulnerable local app exercising Lane 4 classes.
3. Binary-proof network lane — subdomain takeover.
4. Authorization lanes — IDOR/BOLA against a controlled multi-account target.

Steps 3 onward require the posture ceiling to be raised above `LOCAL_FIXTURE`, which is a separate, explicit decision.
