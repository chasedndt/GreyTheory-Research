# Changelog

Notable changes to GreyTheory AI. Format loosely follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versions are not yet published anywhere.

## [Unreleased]

### Added — Authority Plane V0 (first code in the repository)

- `greytheory.provenance` — the observed/checked/inferred triple, with promotion gated on a falsifiable check.
- `greytheory.audit` — append-only, hash-chained JSONL audit log with tamper detection.
- `greytheory.authority.scope` — `ScopeContract`, asset pattern matching (exact / wildcard / CIDR), staleness, content fingerprinting.
- `greytheory.authority.compiler` — programme source → contract, failing closed on ambiguity; source hashing; human review as a required promotion step.
- `greytheory.authority.gate` — the single execution gate. Eleven denial reasons, a posture ceiling independent of contract grants, and a kill switch.
- `greytheory.findings` — one finding entity, one lifecycle, with the internal/external seam enforcing invariant I5.
- `greytheory.cli` — `compile`, `review`, `check`, `audit-verify`.
- Fixtures: one programme that compiles clean, one that is deliberately blocked.
- 87 tests. CI across Linux/Windows on Python 3.11–3.13, plus an end-to-end proof job and a check that no network import ever enters the core package.

- `greytheory.authority.approvals` — operator approvals **read from ChaseOS**, never stored here. `ChaseOSApprovalStore` reads OSRIL responses; `LocalApprovalStore` covers standalone use. Adds binding (one action, one target), expiry (8h default), and single-use enforcement via the audit log.
- Gate integration: six new denial reasons for approvals, and an `approval_required_above` threshold independent of both the contract grant and the posture ceiling.

- `greytheory.signal` — Plane 2. `LaneSpec`/`RawSignal`/`LaneContext` define what a collector is and is forbidden to be: a signal has no field above `contextual`, and every read goes through a root-bounded context built from a granted Decision. The runner is the only path by which a lane executes -- it refuses any lane declaring network I/O, overwrites any authority reference a lane sets with what the gate actually granted, and records skipped targets rather than swallowing them.
- `signal.lanes.agent_config` — Lane 4, the differentiated one. Static agent/MCP config review: ungated consequential tools, wildcard permissions, literal secrets (length recorded, value never), unrestricted egress, plaintext transport to non-loopback hosts, and the composite fetch-plus-ungated-action shape that no per-key scanner sees. Sends no prompts, invokes no model.
- `signal.lanes.exposure` — Lane 2, over a local tree. Known credential formats, high-entropy assignments (placeholders and env references excluded), VCS metadata, backups and source maps. Records format, length and a short digest; never the value. Titles say "present in tree", never "exposed" — presence is not reachability, and a directory cannot know what a web root serves. Files above 2 MiB and non-text suffixes are skipped.
- `signal.lanes.dependency_manifest` — Lane 1. Manifest versions against a local advisory file. Titles say "matches advisory", never "is vulnerable".
- `fixtures/lab/` — a deliberately misconfigured agent fixture and a clean one, so the lane's claims are testable in both directions.
- `greytheory.dashboard` — read model plus text, HTML and JSON renderers. Absent data reports UNKNOWN, never zero: "0 out-of-scope attempts" and "nothing is being recorded" must not look the same. The HTML is self-contained -- no scripts, no external resources. One next action, never six.
- `greytheory.ledger` — triage and earnings. Sessions of every kind, triage outcomes keeping the platform's own wording alongside the canonical one, payouts and expenses in `Decimal`. Effective hourly rate always divides by total tracked hours; `forecast()` raises below 100h / 20 sessions / 5 submissions / 5 closed outcomes and names what is missing; mixed currencies are excluded and reported, never summed. Months with no payout stay in the distribution. Refuses to sit inside a git working tree.
- `greytheory.registry` — the programme registry. Versioned contracts, verbatim source snapshots, scope diffing, and an attention queue (blocked / awaiting review / stale). Changed source invalidates the human review; identical source carries it forward. Narrowing changes — removed assets, new exclusions, new prohibitions, reduced authority — are called out separately from widening ones. Refuses to store a programme marked `confidential` inside a git working tree.
- `greytheory.cli` — `programme register | review | status | diff`.
- `greytheory.validation` — gates B–F. Deterministic gates (evidence, report quality) re-derive from artifacts every run; attested gates (reproducibility, impact, duplicate risk) require a recorded human statement. An unattested gate is `NOT_ASSESSED`, not `FAIL`. Gate E rejects claims that duplicate risk is eliminated.
- `greytheory.report` — report drafts with enforced structure, placeholder detection, absolute-claim warnings, and markdown rendering.
- `greytheory.evidence` — the evidence vault. Raw/redacted split, SHA-256 on both, write-once raw, manifests per finding, integrity verification, and redacted-only all-or-nothing export. Refuses to initialise inside a git working tree.

### Added — licensing

- Apache-2.0. `LICENSE`, `NOTICE`, PEP 639 metadata, SPDX headers on all source files.

### Added — documentation

- `Docs/definition.md` — canonical definition. Three planes, six invariants, capability register, decision log.
- `Docs/system-overview.md` — the whole architecture in one document, written at the point the path runs end to end.
- `Docs/evidence-policy.md` — answers O3. Root resolution order, the repository guard, the rules the vault enforces, and retention.
- `Docs/chaseos-reconciliation.md` — answers O2. ChaseOS owns approvals, audit and graph; GreyTheory imports rather than duplicates. Records one divergence worth acting on: ChaseOS run audits are not tamper-evident.
- `Docs/diagrams.md` — ten diagrams: architecture, gate flow, compilation, finding lifecycle, provenance, authority levels, approvals, approval sources, evidence, evidence root resolution, validation gates, and the whole path.
- `Docs/README.md` — documentation map, including the authority order between documents.
- `SECURITY.md`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, issue and pull request templates, this changelog, CI workflow.

### Changed

- **Reframed the system.** GreyTheory is a control plane whose root is authority; the four lanes are pluggable signal collectors, not the product.
- `README.md` — added a capability register distinguishing live from designed from aspirational, and corrected the design constraint that authorised automatic HTTP probing while `Docs/scope-policy.md` prohibited all external interaction.
- Lane status labels changed from "Planned V1 implementation" to "Designed, not built", which is what was true.
- `Docs/architecture.md` — marked superseded, retained for its lane-level detection detail.
- `PROJECT_STATE.md` — locked decisions rewritten around the three-plane model.
- `Docs/open-questions.md` — was an empty file linked as if real; now tracks blocking and non-blocking unknowns.

### Known gaps

- Grapevine AI integration is an interface contract only; the real implementation has not been inspected (open question O1). No `grapevine` directory was found under `Documents/Projects`.
- ChaseOS run audits are not tamper-evident; porting the hash chain across is proposed but not decided (O9).
- Lane 3 (web) is not implemented, and no collector performs network I/O. The three implemented lanes read local files only; anything touching a target needs the operating posture ceiling raised above `LOCAL_FIXTURE`, which is an explicit operator decision.
- The curriculum and skill graph are not built.
