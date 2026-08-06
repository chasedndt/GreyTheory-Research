# Vulnerability Coverage Matrix

**Coverage today: three static, offline collectors.** Everything else is a plan, not a capability claim.

The implemented lanes read local files only. Nothing here touches a target: every network-based class below needs the operating posture ceiling raised above `LOCAL_FIXTURE`, which is an explicit operator decision.

Read alongside the capability register in [`definition.md`](definition.md#6-capability-register).

## Legend

| Mark | Meaning |
|---|---|
| ⬛ | Not built |
| ◐ | Designed to build-ready detail |
| ✅ | Implemented and tested |

Implemented: `lane1_dependency_manifest`, `lane2_exposure`, `lane4_agent_config`. All static and offline.

## Lane 1 — Known vulnerability

| Class | Status | Deterministic check it would need | Notes |
|---|---|---|---|
| Version-matched CVE | ⬛ | Version string → CVE range match | Match alone is `contextual` at best; reachability is a separate proof |
| Exposed known-vulnerable component | ⬛ | Fingerprint + reachable path confirmation | |
| Default credentials | ⬛ | — | Requires `AUTHENTICATED`. Human-approved per instance, never swept |
| Container / dependency CVE | ✅ | Manifest parse + advisory match | `lane1_dependency_manifest`. Emits *version matches*, never vulnerability claims |

## Lane 2 — Exposure

| Class | Status | Deterministic check it would need | Notes |
|---|---|---|---|
| Exposed `.env` / config | ✅ | Assignment shape + entropy, placeholders excluded | `lane2_exposure`, over a local tree. Reports *presence*, not reachability |
| Exposed `.git` directory | ✅ | Directory presence in the granted tree | `lane2_exposure`. Also .svn, .hg, .bzr |
| Open object storage | ⬛ | Listing response parse | Derived asset — needs independent scope, and network |
| Secrets in JavaScript bundles | ✅ | Known credential formats + entropy | `lane2_exposure`. Records shape and a digest, never the value. Validation of a live secret remains `INTRUSIVE`, opt-in, never automatic |
| Exposed backups / archives | ✅ | Suffix match; the file is never opened | `lane2_exposure` |
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
| Indirect prompt injection with consequence | ✅ | Untrusted content → privileged action trace | `lane4_agent_config` detects the *shape* statically: fetch-capable tools plus ungated consequential tools in one context |
| Tool authorization bypass | ✅ | Wildcard permissions in config | `lane4_agent_config`, statically |
| Approval-gate bypass | ✅ | Consequential tool with no approval requirement | `lane4_agent_config`. Directly transferable to ChaseOS |
| Cross-tenant context leakage | ⬛ | Tenant A data in a tenant B response | |
| Memory poisoning | ⬛ | Persisted untrusted claim reaching a privileged prompt | |
| Insecure MCP transport or permissions | ✅ | Plaintext scheme to a non-loopback host | `lane4_agent_config` |
| Excessive agency | ⬛ | Action taken beyond declared scope | |
| Audit tampering | ⬛ | Chain verification failure | GreyTheory's own audit log is the reference implementation |

## Deprioritised regardless of lane

Low-signal classes that will not enter the hypothesis queue unless a programme explicitly rewards them and impact is demonstrable: missing security headers, version disclosure, self-XSS, generic open redirect, absent rate limiting with no consequence, CORS on non-sensitive endpoints, clickjacking without a meaningful action, and scanner-only outdated-library reports.

## Build order

1. ~~Deterministic, static, no network~~ — **done.** `lane1_dependency_manifest`, `lane4_agent_config`.
2. ~~Local fixture lanes~~ — **done.** `fixtures/lab/vulnerable-agent` and `clean-agent`.
3. ~~Secrets and exposure over local trees~~ — **done.** `lane2_exposure`.
4. Binary-proof network lane — subdomain takeover.
5. Authorization lanes — IDOR/BOLA against a controlled multi-account target.

Steps 4 onward require the posture ceiling to be raised above `LOCAL_FIXTURE`. That is a separate, explicit operator decision, and the runner refuses any lane declaring network I/O until collectors move outside the core package.
