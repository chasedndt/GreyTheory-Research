# Changelog

Notable changes to GreyTheory AI. Format loosely follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versions are not yet published anywhere.

## [Unreleased]

### Added - private redacted report export

- Added a human-acknowledged workbench report-export handler over server-held findings and drafts. It requires `report_ready`, re-runs Gate F quality checks, verifies that cited evidence exists in the complete redacted-only evidence package, and remains non-executing.
- Added an immutable private export writer that atomically emits Markdown, structured JSON, copied redacted artifacts, and a digest manifest outside Git. It accepts no UI path or draft content, audits `submission_performed: false`, and performs no submission, contact, disclosure, or network action.

### Added - human-governed mastery assessment handler

- Added the workbench application handler for one explicit evidence-bound human mastery assessment. It requires a fresh human-acknowledged command, derives the assessor from the configured local operator, accepts no UI-supplied assessor identity, persists to the private integrity-checked mastery store, and remains non-executing.
- Added exact field admission, duplicate-record conflict handling, operator binding, command freshness checks, and idempotent replay. Fixture completion, model output, and journey progression still cannot award mastery.

### Added - authenticated local workbench launch boundary

- Added `greytheory_local` and the `greytheory-workbench` launcher. The runtime assembles real private stores outside Git and exposes versioned snapshots/commands only on numeric `127.0.0.1`; it contains no target client, file server, model, worker, subprocess, CORS surface, or posture-changing route.
- Added exact Host validation, an in-memory high-entropy bearer token, exact-origin POST admission, no-store defensive responses, a 64-KiB body ceiling, read timeout, duplicate-header/JSON-key refusal, strict command decoding, and no CORS permission. ADR-0012 records why a local browser boundary still requires authentication.

### Added - governed research-planning application handlers

- Added workbench handlers for create-only unproven hypotheses, explicit human scope review, and atomic experiment planning. Authority and workspace fingerprints are derived from persisted state, every changed hypothesis carries an optimistic revision, and stale UI commands conflict rather than overwrite newer decisions.
- Added store-level scope-review and planning transactions so a failed plan cannot leave an orphan experiment or partially advance a hypothesis. These commands mutate only private offline research records and always report `executed: false`; action intent remains refused, while report export was implemented by the later entry above.

### Added - dark passive broker foundation

- Added the separate `greytheory_broker` package and optional `passive-broker` crypto dependency. Its `passive-head-v1` policy binds one short-lived Ed25519 ticket to the exact hash-chain-verified Gate audit record, canonical HTTPS target, programme rate, authority fingerprint, and one unauthenticated `HEAD` request. Workers receive only the public ticket-verification key and cannot mint broker tickets.
- Added public-address-only DNS-answer validation, zero-redirect policy, default-engaged digest-protected kill switch, atomic SQLite exact-once ticket reservation, strict time/rate/capture limits, and signed completed/stopped receipt metadata requiring capture and encrypted-envelope digests.
- Kept the broker dark: no DNS query, HTTP client, socket, subprocess, capture encryption implementation, provisioned key, worker image, target action, or posture change exists. ADR-0011 records the remaining boundary.

### Added - workbench foundation and executable capability truth

- Added `greytheory_app`, a separate transport-neutral application layer with a versioned workbench snapshot across programmes, research, hypotheses, learning, evidence, reports, approvals, audit readiness, and executable capability truth.
- Added idempotent, optimistic-revision learning command handlers and explicit non-executing typed refusals for commands whose dedicated use cases are not implemented. The contract structurally rejects posture above `LOCAL_FIXTURE` and never represents a UI action as execution authority.
- Added `greytheory.capabilities`, a typed register shared by the dashboard and future workbench. It separates shipped-code status from runtime health and explicitly keeps Lane 3, external Scope Watch collection, and `PASSIVE_HTTP` unavailable.
- Corrected the dashboard's stale claim that no Signal Plane lane or learning graph existed. It now reports the three static offline lanes, the live learning core, offline model gateway, offline Scope Watch, and the still-unbuilt graphical workbench and network worker.
- Accepted ADR-0010: the graphical workbench is a separate local application layer around the offline core, never a direct collector or execution path.
- Added the workbench architecture covering Windows-first launch, private local storage, required Today/Learn/Research/Evidence journeys, typed command boundaries, UX truth rules, and the future isolated Ubuntu worker boundary.
- Added deterministic guided-learning planning with prerequisite routing, due-review priority, explicit review intervals, and explainable recommendations.
- Added ordered Learn/Practise/Prove/Reflect/Assess journeys, stage-specific evidence requirements, abandonment, serialisation, and integrity-checked private persistence with optimistic revisions.
- Added `learning plan`, `journey-start`, `journey-status`, `journey-advance`, and `journey-abandon` CLI commands. Journey completion requires an already persisted matching human assessment and never awards mastery itself.

### Changed — portfolio security hardening

- `ScopeWatch` now accepts only the exact rooted `LocalSourceFetcher`. The former `allow_network_fetcher=True` switch was a Boolean authority bypass: any caller could inject code that performed network I/O without a durable posture decision or broker receipt. Future external collection must be separately governed, capture bytes outside the core, and hand local evidence inward.
- Historical local demonstration fixtures now bind their stores and CLI runs to their fixture timestamps. This restores reproducibility without weakening stale-contract rejection for real contracts.
- GitHub Actions dependencies are pinned to exact upstream commits while retaining version comments for maintainers.

### Added — model gateway and Scope Watch (Milestones 7 and 8)

- `greytheory.models` -- the only route by which a model is ever called. Nothing in it touches a network: `ModelProvider` is a protocol and the core ships one deterministic local stub, so a real provider is supplied from outside. Classification is enforced at assembly rather than at send, so no window exists in which an unclassified string is appended to a checked prompt. A remote provider can never be approved for `RAW_RESTRICTED`. Nine role contracts each carry a ceiling below the provider's. A response citing context that was never supplied is refused, not flagged -- an unresolvable citation is an invented source. Every output enters as `inferred`, with no code path to `checked`. Prompts are audited by digest, never by content. An exhausted budget refuses.
- Evaluation harness: eight adversarial cases covering fabricated citations, missing citations, raw-capture leakage, role ceilings, impact overstatement, stated uncertainty, and indirect prompt injection in both compliant and non-compliant forms. Two are negative fixtures asserting the detector fires, so a clean run distinguishes a working harness from a well-behaved model.
- `greytheory.scopewatch` -- re-reads recorded programme sources and reports what moved. A source that could not be read is `UNREACHABLE`, never `UNCHANGED`: a source nobody could check has not been shown to be the same. It needs attention but does not by itself invalidate review, because "could not read it" is not "it changed". Changed and removed sources do invalidate it. A source without a comparable hash is skipped rather than guessed at.
- **The network fetcher is deliberately absent.** `SourceFetcher` remains an integration-shape protocol, but the core `ScopeWatch` accepts only the exact `LocalSourceFetcher`; arbitrary implementations and subclasses are refused. Fetching a programme page is still a request to somebody's server. ADR-0009.

### Changed — trust-kernel hardening

- **`report_ready` now requires a claim in each of seven roles**, not a count of checked claims. The old guard was satisfiable by proving a request returned 200 -- true, checked, receipted, and silent on whether anything was wrong. Five roles are settled by validator receipts derived from artifacts already held; `impact` and `reproduction` are judgement roles requiring a stated uncertainty. One claim cannot answer two roles -- the shortcut a count invited. ADR-0008.
- **Submission now requires a `ScopeRecheck`.** Evidence gathered Monday, scope narrowed Wednesday, report sent Friday: nothing earlier in the lifecycle would notice. A mismatch blocks rather than warns, and a recheck cannot authorise a finding it does not belong to.
- The Milestone 4 vertical slice now proves five things instead of one, with no additional fixture interaction.

### Added — claim roles

- `greytheory.claims` -- seven claim roles, `RoleBinding`, and the claim-evidence matrix that reports should be generated from. A binding cannot be constructed unsoundly: checked roles reject non-checked claims, demand the receipt that promoted them, and refuse a receipt whose id does not match the claim.
- `greytheory.validators` -- four reusable validators settling the checked roles offline: ownership boundary, synthetic target, contract currency and evidence integrity. None performs any interaction, which is what keeps the stricter guard compatible with minimum-impact proof. An empty evidence manifest is `invalid_input`, never `supported`.
- `Docs/agent-activity.md` -- why each session deviated from the roadmap, and what the next agent should not undo.

### Added — transparent hypothesis ranking

- Added a deterministic nine-factor research-queue engine over existing,
  contract-bound hypotheses and the 12-card catalogue.
- Added the versioned `conservative-local` policy with exact weights,
  direction-aware basis-point contributions, stable ordering, and fail-closed
  scope partitioning.
- Added provenance, rationale, uncertainty, derivation, and observed inputs for
  every factor. Four factors are system-derived; five require an explicit
  `operator` or `test_fixture` estimate. Model scoring remains refused.
- Added integrity-checked private queue output and CLI `hypothesis verify` and
  `hypothesis rank` commands. Every item remains `unproven`, decision-support
  only, and carries no execution authority.
- Added a three-theory synthetic proof with nine explanations per item and zero
  action requests, receipts, model calls, network actions, or external targets.

### Added — vulnerability cards and skill graph

- Added exactly 12 versioned first-class vulnerability cards with framework
  classifications, falsifiable hypothesis templates, explicit controls,
  minimum-evidence roles, impact boundaries, safe-test rules, remediation,
  policy constraints, review dates, and revision provenance.
- Added 12 distinct synthetic, network-free property fixtures. Their
  fixture/runner-digested receipts prove both controls and the deliberately
  vulnerable local path while explicitly proving no real vulnerability and
  awarding no mastery.
- Added an acyclic card-prerequisite graph and independent `explain`,
  `recognise`, `test`, `prove`, `remediate`, and `transfer` dimensions.
- Added an integrity-checked private mastery store. Only explicit,
  evidence-bound human assessments credit mastery; labelled test-fixture
  assessments remain visible but non-crediting.
- Applied the Milestone 4 BOLA proposal to `idor-bola` v1.0.0 with explicit
  `test_fixture` revision provenance and no real-session or human-mastery claim.
- Added offline CLI commands for catalogue inspection, fixture verification,
  mastery status, and explicit assessments.

### Added — direct-policy programme-source proof

- Added an independently maintained `modelcontextprotocol/python-sdk` bundle from the immutable public `SECURITY.md` at commit `d82ed88e`, captured byte-for-byte as a verbatim programme-policy source.
- Added `markdown_supported_versions_v1` derivation validation. The observed Version/Line/Support table must derive exactly two supported release lines and one unsupported class; malformed tables, unclassified support semantics, duplicates, or record drift fail closed.
- Made each observed derivation enforce its source kind and capture mode: HackerOne requires a structured scope export, Bugcrowd an operator-extracted scope table, and the direct policy a verbatim programme-policy source.
- Completed Milestone 2's three-source implementation proof without target contact. The direct bundle reaches `PENDING_REVIEW` under `LOCAL_FIXTURE`; existing HackerOne and Bugcrowd review/block states remain unchanged.

### Added — Bugcrowd programme-source proof

- Added a public Bugcrowd/YNAB bundle with an operator-structured extract of two rendered target groups, a bounded programme-policy extract, and Bugcrowd's linked platform-default extract.
- Added `bugcrowd_target_groups_json_v1` derivation validation. The 3 in-scope and 5 out-of-scope target rows must match the normalized record exactly; malformed groups, duplicates, cross-group conflicts, or record drift fail closed.
- Preserved two real policy conflicts as pending human resolutions. The bundle intentionally compiles to `BLOCKED` under `LOCAL_FIXTURE`; broad owned-host and production-API wording never become executable scope.
- Added LF-only Git attributes for hashed public programme evidence so source hashes remain reproducible across Windows and Linux checkouts.

### Added — first real programme-source bundle

- `greytheory.authority.sources` implements offline `ProgrammeSourceBundle` loading and compilation with explicit source kinds/capture modes, safe local paths, public provenance URLs, retrieval/update times, per-source hashes, high-to-low precedence, per-field citations, structured-export derivation checks, human-resolution gates, and a semantic whole-bundle snapshot/hash.
- `ProgrammeRegistry.register_bundle()` stores the complete bundle snapshot, audits its identity/hash/source count, carries review only across identical bundles, and invalidates review when any source or governing metadata changes.
- CLI command `greytheory programme register-bundle` registers a saved bundle without network I/O.
- First real proof: a 2026-08-09 HackerOne/GitLab bundle containing the official 44-row public scope CSV plus bounded programme and platform-policy extracts. It compiles to `PENDING_REVIEW` under `LOCAL_FIXTURE`; it is not human-reviewed and grants no live-target authority.

### Added — Security Research Operating System foundation

- Canonical product identity, research-domain model, bounded-autonomy model, threat model, data policy, integration boundaries, and four architecture decision records.
- Thirteen-milestone roadmap from real programme source bundles through the first operator-submitted research outcome.

### Changed — product framing and truth surfaces

- GreyTheory is now framed as a standalone, local-first, human-governed Security Research Operating System; the existing three-plane control plane remains its trust kernel.
- README, project state, documentation map, system overview, capability register, public positioning, and historical handover labels now distinguish the verified offline kernel from designed product layers.
- Corrected stale capability claims: the gate has seventeen denial reasons, Lane 2 is live offline, the dashboard read model exists, and no live-target lane exists.

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
- `greytheory.advisories` — offline import of the OSV advisory format that GitHub, PyPI, npm and Go publish, from a file or a directory tree. Ecosystem-aware matching, because `requests` on PyPI and `requests` on npm are different packages and a name-only match reports the wrong one with total confidence. Correct version ordering: `2.0.0-rc1` sorts before `2.0.0`, and getting that backwards reports a release candidate as patched. PEP 503 name normalisation. Records with no usable version range are skipped rather than guessed at, since unknown bounds would match every version. CLI: `greytheory advisories <file-or-dir>`.
- `signal.lanes.dependency_manifest` — Lane 1. Manifest versions against a local advisory file. Titles say "matches advisory", never "is vulnerable".
- `fixtures/lab/` — a deliberately misconfigured agent fixture and a clean one, so the lane's claims are testable in both directions.
- `greytheory.dashboard` — read model plus text, HTML and JSON renderers. Absent data reports UNKNOWN, never zero: "0 out-of-scope attempts" and "nothing is being recorded" must not look the same. The HTML is self-contained -- no scripts, no external resources. One next action, never six.
- `greytheory.ledger` — triage and earnings. Sessions of every kind, triage outcomes keeping the platform's own wording alongside the canonical one, payouts and expenses in `Decimal`. Effective hourly rate always divides by total tracked hours; `forecast()` raises below 100h / 20 sessions / 5 submissions / 5 closed outcomes and names what is missing; mixed currencies are excluded and reported, never summed. Months with no payout stay in the distribution. Refuses to sit inside a git working tree.
- `greytheory.registry` — the programme registry. Versioned contracts, verbatim source snapshots, scope diffing, and an attention queue (blocked / awaiting review / stale). Changed source invalidates the human review; identical source carries it forward. Narrowing changes — removed assets, new exclusions, new prohibitions, reduced authority — are called out separately from widening ones. Refuses to store a programme marked `confidential` inside a git working tree.
- `greytheory.cli` — `programme register | review | status | diff`.
- `greytheory.validation` — gates B–F. Deterministic gates (evidence, report quality) re-derive from artifacts every run; attested gates (reproducibility, impact, duplicate risk) require a recorded human statement. An unattested gate is `NOT_ASSESSED`, not `FAIL`. Gate E rejects claims that duplicate risk is eliminated.
- `greytheory.report` — report drafts with enforced structure, placeholder detection, absolute-claim warnings, and markdown rendering.
- `greytheory.evidence` — the evidence vault. Raw/redacted split, SHA-256 on both, write-once raw, manifests per finding, integrity verification, and redacted-only all-or-nothing export. Refuses to initialise inside a git working tree.

### Added — brand

- `assets/` — mark, mono mark, app icon, wordmark, favicon, GitHub social preview and README banner, plus `render.py` so the raster files are drawn from the same geometry as the SVGs and cannot drift. The mark is the gate: three paths approach, two stop, one passes. Amber is authority and appears nowhere else in the mark.

### Added — licensing

- Apache-2.0. `LICENSE`, `NOTICE`, PEP 639 metadata, SPDX headers on all source files.

### Added — documentation

- `Docs/definition.md` — canonical definition. Three planes, six invariants, capability register, decision log.
- `Docs/system-overview.md` — the whole architecture in one document, written at the point the path runs end to end.
- `Docs/full-brief.md` — a complete self-contained project brief for handing to another AI or person: definition, glossary, architecture, every module, the current truth, worked examples, roadmap, all thirty decisions, choices to avoid (architectural, operational and linguistic), open questions, and a ready-made prompt with constraints that prevent a fresh session drifting the design.
- `Docs/evidence-policy.md` — answers O3. Root resolution order, the repository guard, the rules the vault enforces, and retention.
- `Docs/chaseos-reconciliation.md` — answers O2. ChaseOS owns approvals, audit and graph; GreyTheory imports rather than duplicates. Records one divergence worth acting on: ChaseOS run audits are not tamper-evident.
- `Docs/diagrams.md` — ten diagrams: architecture, gate flow, compilation, finding lifecycle, provenance, authority levels, approvals, approval sources, evidence, evidence root resolution, validation gates, and the whole path.
- `Docs/README.md` — documentation map, including the authority order between documents.
- `SECURITY.md`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, issue and pull request templates, this changelog, CI workflow.

### Changed

- **Cut Grapevine AI.** The name came from a planning document which stated its implementation "was not available in the source context used to create this file", and no implementation was found. Building an interface against a system nobody has seen is how a guess hardens into a fact. The useful capability -- noticing that a programme's source changed -- is restated as **Scope Watch** under our own name in `roadmap.md` Phase 5. Half of it already exists offline: the registry detects drift and invalidates the human review on re-registration.
- **Purpose restated explicitly.** GreyTheory is a bug bounty and authorised security research engine; the Authority Plane governs the operator's own research. The Authority Plane's mechanisms are reusable, but that is an observation about the code, not a change of purpose -- governance offerings for other people's agents are derivative products with separate scope. `definition.md` §1 now says so, so it cannot drift again.
- `Docs/roadmap.md` rewritten. The prior version predated all code. Nine phases through real-programme handling, advisory sourcing, curriculum, Scope Watch, the posture-ceiling decision, network collectors and first submission -- plus what is deliberately not on it.

- **Reframed the system.** GreyTheory is a control plane whose root is authority; the four lanes are pluggable signal collectors, not the product.
- `README.md` — added a capability register distinguishing live from designed from aspirational, and corrected the design constraint that authorised automatic HTTP probing while `Docs/scope-policy.md` prohibited all external interaction.
- Lane status labels changed from "Planned V1 implementation" to "Designed, not built", which is what was true.
- `Docs/architecture.md` — marked superseded, retained for its lane-level detection detail.
- `PROJECT_STATE.md` — locked decisions rewritten around the three-plane model.
- `Docs/open-questions.md` — was an empty file linked as if real; now tracks blocking and non-blocking unknowns.

### Known gaps

- ChaseOS run audits are not tamper-evident; porting the hash chain across is proposed but not decided (O9).
- Lane 3 (web) is not implemented, and no collector performs network I/O. The three implemented lanes read local files only; anything touching a target needs the operating posture ceiling raised above `LOCAL_FIXTURE`, which is an explicit operator decision.
- The curriculum and skill graph are not built.
