# GreyTheory Roadmap

> **Category:** Security Research Operating System
>
> **Current research milestone:** 9 - Passive execution pilot (gated on the posture decision)
>
> **Last completed:** 8 — Scope Watch, offline portion
>
> **Current product workstream:** Workbench and guided-learning foundation under `LOCAL_FIXTURE`
>
> **Posture:** `LOCAL_FIXTURE`; no network I/O or live-target interaction.

The existing Authority, Signal, and Judgement planes remain the trust architecture. This roadmap adds the product and research layers required to make that kernel a complete day-to-day research environment.

## Existing verified baseline

- Authority Plane, offline Signal framework with three static collectors, and Judgement Plane are implemented.
- Offline OSV advisory import is implemented.
- 708 repository tests pass on 2026-09-04. The unchanged UI baseline remains 23 UI tests, 4 Sites tests, the production UI build, and fresh desktop/390-pixel capability-truth QA. The full Ubuntu 24.04.4 no-route service harness passes, and a namespace-lifetime nftables candidate adds default-drop input/forward/output, one exact synthetic address/port, counted bypass denials, mutation refusal after capability drop, and the same encrypted full-service completion. A signed-input image build/runtime candidate has 21 focused static/provenance tests, linked Windows-worktree normalization, lock-bound pre-dependency install groups, an owned minimal build-time `/dev` while retaining a `nodev` ext4 root, a bounded root-manifest reproducibility diagnostic that removes `ldconfig`'s filesystem-specific auxiliary cache, and a clean two-build-identical release artifact; runtime acceptance has not passed. A Windows CurrentUser DPAPI root-KEK candidate passes same-profile restart/protected-copy recovery, tamper refusal, capture decryption, and audit checks. These are still local host proofs; posture remains unchanged and provider approval, ACL hardening, independent recovery, accepted hardened-image binding, programme, and human approval gates remain open.
- Three saved source shapes compile offline without guessed authority: HackerOne/GitLab and direct-policy/MCP Python SDK reach `PENDING_REVIEW`; Bugcrowd/YNAB correctly reaches `BLOCKED` on two unresolved human policy decisions.
- No network capability or live research outcome exists.

## Milestone 1 — Canonical project foundation *(COMPLETE 2026-08-09)*

- [x] Define GreyTheory as a local-first, human-governed Security Research Operating System.
- [x] Preserve the three-plane control plane as the trust kernel.
- [x] Define the research domain, autonomy boundary, data policy, threat model, and integration boundary.
- [x] Record productisation ADRs.
- [x] Reconcile every current public/internal description and remove stale pre-implementation claims.

**Exit:** nobody can confuse LIVE, PARTIAL, DESIGNED, PLANNED, or HISTORICAL capability, or describe GreyTheory as an autonomous submitter.

## Milestone 2 — Real programme compiler *(COMPLETE 2026-08-09)*

Register saved public sources for:

- [x] one HackerOne programme — GitLab, captured 2026-08-09;
- [x] one Bugcrowd programme — YNAB, captured 2026-08-09; target groups derive exactly and policy conflicts block;
- [x] one direct VDP or independently hosted policy — `modelcontextprotocol/python-sdk` `SECURITY.md` at immutable commit `d82ed88e`, captured 2026-08-09.

Implement `ProgrammeSourceBundle` from observed needs: platform defaults, programme rules, scope tables, attachments/linked policies, retrieval times, source hashes, precedence, and human conflict resolutions.

Implemented from the first bundle:

- [x] source kind and capture-mode truth (`structured_export`, `verbatim`, or `operator_extract`);
- [x] safe local paths, public HTTPS provenance, retrieval/source-update times, and per-source integrity hashes;
- [x] high-to-low precedence and per-authority-field source citations;
- [x] executable derivation check proving the 44 HackerOne CSV rows match the 19/25 normalised scope record;
- [x] executable derivation check proving the 3/5 Bugcrowd target-group rows match the normalised scope record;
- [x] executable derivation check proving the direct policy's Markdown table matches the 2/1 supported-version record;
- [x] accepted/pending/rejected human-resolution records, with unresolved or unattributed decisions blocking compilation;
- [x] whole-bundle semantic snapshot/hash and registry review invalidation when any source or governing metadata changes;
- [x] offline CLI registration and audit evidence;
- [x] prove operator-extracted Bugcrowd target groups and real policy conflicts without granting guessed scope;
- [x] prove the schema against a direct-policy source shape without inventing platform precedence.

**No target contact.** Compilation is offline.

**Exit:** all three compile without guessed authority; conflicts are explicit; verification records the entire reviewed bundle; any source change invalidates review; ambiguity never grants permission.

## Milestone 3 — Research domain *(COMPLETE 2026-08-09)*

- [x] Implement `ResearchWorkspace`, `ResearchSession`, `TargetAsset`, `AssetRelationship`, `ResearchIdentity`, `Hypothesis`, `ExperimentPlan`, `ActionRequest`, `ActionReceipt`, and `Lesson`.
- [x] Bind every record to one workspace and contract fingerprint; keep identities reference-only and graph edges scope-neutral.
- [x] Persist complete local workspaces atomically with integrity and referential checks plus optional hash-chained audit events.
- [x] Enforce explicit hypothesis/experiment/session lifecycles and request/time/effect budgets.
- [x] Prove all ten records in one complete persisted local session without unstructured notes or network/process execution.

**Exit:** one full local session can be managed through structured objects without unstructured notes.

## Milestone 4 — First end-to-end local vertical slice *(COMPLETE 2026-08-09)*

Use a deliberately vulnerable local two-account authorisation fixture:

```text
training programme rules
→ verified LOCAL_FIXTURE contract
→ workspace and two controlled identities
→ asset/ownership model
→ IDOR/BOLA hypothesis and experiment
→ gate decision and local action receipt
→ observation and deterministic check
→ evidence and impact attestation
→ report, postmortem, and vulnerability-card update
```

**Exit:** no action without a decision; every action and report claim has a receipt/provenance link; a session produces checked evidence or a reusable lesson.

Verified with one deliberately vulnerable, in-memory two-account fixture. The
allowed path executes exactly one read and persists exactly one action receipt;
the prohibited-technique path executes no action and produces neither receipt
nor evidence. A registered ownership validator issues the only promotable
`CheckReceipt`, report claims carry provenance/evidence links, all Gates B-F
pass, and the session produces checked evidence plus a postmortem. The card
update entered Milestone 5 as a proposal and is now recorded only as a labelled
`test_fixture` revision of the IDOR/BOLA card, not as a real-session claim.

## Milestone 5 — Vulnerability cards and skill graph *(COMPLETE 2026-08-09)*

Build the first 12 cards: reflected/stored/DOM XSS, SQL injection, CSRF, SSRF, IDOR/BOLA, BFLA, session management, business-logic authorisation, indirect prompt injection, and tool-authorisation failure.

**Exit:** each has a local fixture, falsifiable hypothesis template, minimum evidence, and six-dimensional mastery tracking: explain, recognise, test, prove, remediate, transfer.

Verified with exactly 12 versioned built-in cards and 12 distinct synthetic,
network-free fixture mechanisms. Each fixture exercises positive, deliberately
vulnerable, and negative-control paths and issues a fixture/runner-digested
receipt that explicitly proves no real vulnerability and awards no mastery.
The acyclic skill graph exposes all 72 card/dimension states. The private,
integrity-checked mastery store credits only explicit evidence-bound human
assessments; test-fixture assessments remain visible but non-crediting. The
Milestone 4 BOLA proposal maps to exactly one `idor-bola` v1.0.0 revision with
`test_fixture` provenance. Focused acceptance originally passed 10 tests and
the then-current full suite passed 430. Transparent adaptive review plus bounded
assisted and transfer tracks were added later under the workbench workstream.
Three versioned Case Packs and the graphical Learn surface now exist, but only
the first Case Pack is ready locally and installed product acceptance remains
PARTIAL.

## Milestone 6 — Hypothesis engine *(COMPLETE 2026-08-09)*

Rank theories using transparent scope confidence, existing evidence, likelihood, impact, cost, side-effect risk, duplicate risk, skill value, and target-specific novelty.

**Exit:** it produces an explained research queue without calling any item a vulnerability or executing it.

Verified with a versioned conservative policy covering the exact nine factors,
four system-derived inputs and five explicit provenance-rich assessments. Every
ordinal score contribution is explained and integrity checked; ambiguous scope
is partitioned for review rather than offset by another factor. The synthetic
proof ranks three unproven local theories while producing zero action requests,
receipts, network calls, model calls, or external targets. The focused suite
passes 13 tests and the complete repository passes 443.

## Trust-kernel hardening *(unscheduled, 2026-08-09)*

Two gaps from the productisation review, closed ahead of Milestone 7 because
both sit in the trust kernel that every later milestone assumes is correct:
claim roles for report-readiness, and a submission-time scope recheck. See
[ADR-0008](decisions/ADR-0008-claim-roles-and-submission-scope-recheck.md) and
[the agent activity log](agent-activity.md).

Still open from that review: `ApprovalProvider` (ADR-0003 exists, the code does
not), signed audit checkpoints, evidence tombstones, taint labels for
target-controlled content, and a plugin conformance suite.

## Milestone 7 — Model gateway and evaluation harness *(COMPLETE 2026-08-09)*

Add provider/version records, data-class policy, prompt/context assembly, structured output, inference provenance, citations, cost accounting, injection defences, and evaluation fixtures.

**Exit:** evaluations measure unsupported promotion, scope errors, fabricated evidence, unsafe tool requests, prompt injection, uncertainty, and report completeness. Every output remains `inferred`.

Verified with `greytheory.models`. No provider in the core performs network
I/O: `ModelProvider` is a protocol and the only shipped implementation is a
deterministic local stub, so a real provider is supplied from outside.

Classification is enforced at *assembly* rather than at send, so no window
exists in which an unclassified string can be appended to a checked prompt. A
remote provider cannot be approved for `RAW_RESTRICTED` at all, and each of the
nine roles carries its own ceiling below the provider's -- the tutor role sees
public material only, whatever the provider allows.

A response citing context that was never supplied is refused rather than
flagged: a citation that does not resolve is an invented source. Every output
enters as `inferred` with no code path to `checked`. Prompts are audited by
digest, never by content. An exhausted budget refuses.

The 8-case evaluation suite covers fabricated citations, missing citations, raw
capture leakage, role ceilings, impact overstatement, stated uncertainty, and
indirect prompt injection in both compliant and non-compliant forms. Two cases
are negative fixtures asserting that the detector fires, so a clean run
distinguishes a working harness from a well-behaved model.

## Milestone 8 — Scope Watch *(COMPLETE offline 2026-08-09; network fetcher deferred)*

Make saved public programme-source fetching the first network-enabled component. It informs Authority/Judgement only and never grants scope.

**Exit:** changes are diffed, narrowing changes highlighted, and affected contracts invalidated without interpreting source text as permission.

Verified with `greytheory.scopewatch`. All comparison, invalidation and
reporting logic is implemented and tested offline.

**What is deliberately not built: the network fetcher.** The core ships only
`LocalSourceFetcher`, and `ScopeWatch` accepts that exact rooted implementation
only. An arbitrary object cannot self-declare `network = False`, and there is
no Boolean escape hatch. Fetching a programme page is still a request to
somebody's server and belongs above `LOCAL_FIXTURE`. A future governed collector
must run outside the trust kernel and materialise immutable local evidence for
Scope Watch; it does not get injected directly into the core.

A source that could not be re-read is `UNREACHABLE`, never `UNCHANGED` -- a
source nobody could check has not been shown to be the same. It needs attention
but does not by itself invalidate review, because "could not read it" is not
"it changed" and conflating them would make every network blip look like drift.
A changed or removed source does invalidate review. A source recorded without a
comparable hash is skipped rather than guessed at, since watching something
uncomparable would report every run as changed.

## Product workstream - AI-native workbench and guided learning *(INTERACTIVE PREVIEW VERIFIED 2026-09-01)*

This workstream runs under `LOCAL_FIXTURE` and does not depend on raising the
research posture. The executable capability register and the application,
process, storage, learning, and future-worker boundary are now implemented.
The operator selected Direction 1, Guided Mission Control, as the shell and
approved borrowing Direction 2's focused lesson/skill map plus Direction 3's
case canvas/evidence/competency views. The interactive preview removes the
earlier document-level overflow and completes one deterministic local
Learn -> Practise -> Prove -> Reflect -> Assess case. The earlier Research
Ledger remains a first-class Research case view. The learner-facing contract is
defined in
[`ai-native-learning-workbench.md`](ai-native-learning-workbench.md).

- [x] Audit the existing desktop and 390-pixel static dashboard.
- [x] Produce three grounded workbench directions for operator selection.
- [x] Establish one executable capability register for dashboard and workbench truth.
- [x] Accept the workbench-as-application-boundary decision in ADR-0010.
- [x] Define required Today, Learn, Programmes, Research, Evidence, Reports, and Readiness journeys.
- [x] Implement deterministic prerequisite/review planning, staged private journeys, reflection, explicit persisted-human-assessment completion, and CLI operation.
- [x] Capture the current desktop and 390-pixel implementation in the central GreyTheory visual-QA registry.
- [x] Audit the learner journey, typography, hierarchy, responsiveness, and agent-security learning needs.
- [x] Produce three modern dashboard concepts plus an editable Figma audit/direction board.
- [x] Select Direction 1, Guided Mission Control, with focused-learning and case/evidence borrowings from Directions 2 and 3.
- [x] Build the versioned, transport-neutral application snapshot and bounded learning command contract.
- [x] Add create-only hypothesis, human scope-review, and atomic experiment-planning application handlers with optimistic revisions.
- [x] Build authenticated numeric-loopback transport, private runtime assembly, and the Windows-first local launch command.
- [x] Add a fresh, operator-bound, evidence-required human mastery-assessment application handler without automatic mastery or execution.
- [x] Add immutable private report export from server-held drafts and verified redacted evidence, with no submission path.
- [x] Add server-derived `LOCAL_FIXTURE` action intent from an active experiment without Gate evaluation, approval, receipt, or execution.
- [x] Persist complete private finding/draft cases and add revision-safe informational case creation and draft editing with server-owned authority state.
- [x] Persist fresh human-bound Gates B-F validation history without claim or finding promotion.
- [x] Assemble all seven claim roles for the exact two-account fixture from stored evidence and persisted operator attestations without another target action.
- [x] Advance exactly one internal finding state, require a current Gates B-F pass for `report_ready`, and refuse submission/programme outcomes.
- [x] Build the earlier Research Ledger direction as a local-fixture-only baseline; retain its ledger as a first-class Research case view.
- [x] Complete all thirteen visible prototype navigation panels with search, filters, inspection, responsive context, and explicit write boundaries.
- [x] Bind matching panels to authenticated server-owned snapshots through an explicit read-only numeric-loopback UI origin; retain exemplar labels where no server section exists and keep cross-origin commands disabled.
- [x] Build the selected learner-first graphical shell and remove document-level overflow at 390, 768, 1024, and 1440 pixels.
- [x] Implement Today, Learn, Practise, Research, Prove, Readiness, and Library preview journeys with realistic local-fixture data.
- [x] Add an inspectable recommendation explanation, six-stage learner loop, prerequisite/skill trajectory, agent-security track, case canvas, and evidence-quality visualisations.
- [x] Make every trajectory node focusable/selectable with honest completed,
  current, previewed, and future states plus lesson details that do not award
  mastery.
- [x] Give every current agent-security topic distinct focused notes,
  principles, traditional/AI lenses, self-checks, official learning sources,
  and a four-stage beginner-to-transfer roadmap.
- [x] Turn the ready local Case Pack into an exact 30-minute guided mission with
  selectable timed stages, two scored scenario checks per topic, and an
  explain-it-yourself threshold that unlocks practice without awarding mastery.
- [x] Restore the complete thirteen-panel navigation with working Programmes,
  Hypotheses, Intelligence, Reports, and Settings journeys.
- [x] Add a network-free public-intelligence contract for OSV, CISA KEV, FIRST
  EPSS, NVD, and GitHub Advisories; authenticated bug-bounty connectors remain
  dark and no fetcher is enabled.
- [x] Add an interactive programme-to-local-case readiness view for the saved
  HackerOne, Bugcrowd, and direct-policy bundles; ambiguity, network access, and
  live target activity remain blocked.
- [ ] Connect the bounded AI coach to the governed model gateway; its advisory-only presentation and explicit no-execution/no-mastery boundary are implemented.
- [x] Add transparent adaptive scheduling plus bounded assisted and transfer-specific learning modes beyond the deterministic foundation.
- [x] Define versioned Case Pack contracts for guided, assisted, and independent transfer runs; ship Agent Tool Authorization as the first ready local pack and queue API ownership plus session/role transition packs.
- [x] Persist immutable synthetic fixture receipts and bind the graphical Learn -> Practise -> Prove -> Reflect path to same-origin, revision-safe application commands.
- [x] Serve the built learner UI from the numeric-loopback application under a self-only content policy while keeping separate preview origins read-only.
- [x] Add a working three-story Demo Suite and expose the future live-programme adapter as dark, disabled, and gated by Windows, Ubuntu, egress/key, programme-review, and human-posture acceptance.
- [ ] Complete accessibility acceptance; responsive geometry, reload persistence,
  route focus, compact navigation names, inert closed mobile navigation, and
  mobile-drawer/modal focus containment and restoration pass. The themed
  navigation scrollbar and runtime focusable-order inventory now pass too,
  while a complete first-entry and whole-application keyboard sweep remains open.
- [x] Build a reproducible wheel that bundles the learner UI and all learning
  resources, then accept it from an empty Windows install prefix through its
  console launcher, numeric-loopback UI, health endpoint, and authenticated
  snapshot without enabling live targets.
- [x] Add and accept a current-user installer with a Start Menu-shaped shortcut,
  real same-origin learner persistence, application restart, same-wheel
  upgrade, and replaceable-runtime recovery. The evidence explicitly records
  that it is not a separate-account or signed-installer acceptance.
- [ ] Repeat the install/shortcut lifecycle from a genuinely separate Windows
  account and complete release signing/uninstall acceptance.

**Exit:** an operator can install and launch GreyTheory locally, resume a
bounded session, complete a guided learning-to-proof journey, inspect authority
and evidence, and export a report draft without any target-network capability.

Current next product gate: finish first-entry and whole-application keyboard
traversal, then repeat the accepted shortcut/install/recovery lifecycle from a
genuinely separate Windows account. See [`live-programme-transition.md`](live-programme-transition.md)
for the later five-gate transition; no VPS or programme connection is part of
this product gate.

## Milestone 9 — Passive execution pilot

Raise only to `PASSIVE_HTTP`, for one verified programme and one tightly controlled action type, after every precondition in `THREAT_MODEL.md` is implemented and tested.

Offline broker foundation completed without enabling the posture:

- [x] Define `passive-head-v1`: one canonical unauthenticated HTTPS `HEAD`, one
  request, zero redirects, explicit programme rate, 30-second and 64-KiB ceilings.
- [x] Bind short-lived signed tickets to the exact verified Gate audit record,
  request, contract fingerprint, target, and `PASSIVE_HTTP` ceiling.
- [x] Add public-address-only DNS-answer policy, default-engaged persistent kill
  switch, SQLite exact-once reservation, and signed completed/stopped receipts.
- [x] Require target data to remain `UNTRUSTED` / `RAW_RESTRICTED` and require
  capture plus encrypted-envelope digests for a completed receipt.
- [x] Implement ticket-bound X25519/HKDF/ChaCha20-Poly1305 capture encryption
  and authorised external-KEK-wrapped recipient provision, rotation,
  revocation, and retained-evidence decryption outside Git.
- [x] Implement the network-free resolver/direct-transport conformance contract:
  full request digest, exact validated address/TLS name, no proxy or followed
  redirect, zero body, closed connection, strict bounded header parsing,
  monotonic deadline, encryption, and signed stop paths.
- [x] Implement unlaunched actual primitives behind the contract: an owned-child
  cancellable absolute-name system resolver with capped JSON IPC and a direct
  numeric-address TLS 1.2+ `HEAD` transport with explicit CA trust, hostname
  verification, disabled key logging, total deadlines, bounded header reads,
  and deterministic close. Verification injects every syscall and performs no
  network I/O.
- [x] Prove the production direct-TLS primitive and spawned-child cancellation
  path on Ubuntu 24.04 WSL2 inside an ephemeral loopback-only namespace with no
  default route: no re-resolution, explicit CA/hostname enforcement, mismatch
  refusal, two-write header streaming, zero body, and deterministic cleanup.
  This contacts no external system and does not assemble or enable a worker.
- [x] Assemble the dark two-phase owned-process worker path in source: one
  resolution, broker recheck, one exact direct request, encrypted capture,
  signed receipt, exact-once replay completion, environment scrubbing, and
  strict non-root/zero-capability/no-new-privileges identity evidence. Unit and
  static acceptance tests pass; no launcher or posture route exists.
- [x] Run the implemented full-service harness to completion and prove
  successful real system DNS, broker recheck, unprivileged process behavior,
  encrypted evidence return, signed receipt, and cleanup on the isolated Ubuntu
  host. On 2026-09-04 the remaining Windows checkout defect was fixed by
  enforcing LF for shell entrypoints; Ubuntu 24.04.4 then emitted a complete
  durable JSON record while retaining `LOCAL_FIXTURE`, no route, and no external
  or programme contact.
- [x] Implement and host-test a candidate Windows CurrentUser DPAPI root-KEK
  provider without wiring it to posture: strict protected records, audited
  provision/lease operations, same-profile restart and protected-copy recovery,
  tamper refusal, capture decryption, and lease-buffer zeroing pass. This does
  not close the key gate.
- [x] Prove a namespace-lifetime OS egress candidate on Ubuntu 24.04.4 WSL2:
  hash-locked nftables userspace reconstructed under an owned temporary root,
  default-drop input/forward/output, one exact synthetic address/port,
  counted wrong-port/decoy-address/IPv6 denials, denied unprivileged route and
  firewall mutation, and successful full encrypted worker completion. No
  external packet, programme, posture raise, or WSL system install is involved.
- [ ] Prove durable egress enforcement in the hardened local image. Signed
  base/archive staging, a clean two-build-identical read-only SquashFS artifact,
  and strict runtime-admission code now exist; image runtime acceptance has not
  passed.
- [ ] Bind the external root KEK to an approved OS secret provider and prove
  hardened application-data ACLs plus independent cross-profile/bare-machine
  backup/recovery and host acceptance; no root KEK is stored by the repository.
- [ ] Accept and harden the unprivileged Ubuntu 24.04 worker image and broker
  transport; the image candidate is source-implemented, while runtime and
  transport acceptance remain open.
- [ ] Pass VM conformance, owned-canary, one-programme review, sustained clean
  operation, and explicit human posture approval.

**Exit:** rate, DNS, redirects, kill switch, data policy, receipts, and sustained clean operation are verified.

## Milestone 10 — Binary-proof collectors

Order: subdomain-takeover verification, reachable exposure, technology/advisory correlation, safe HTTP misconfiguration checks.

## Milestone 11 — Controlled authenticated authorisation testing

Two owned accounts, ownership records, role-object-action matrix, synthetic data, per-experiment plans, request budgets, and human review per test family.

## Milestone 12 — Live agentic-AI assessment

Test explicitly authorised AI assets through the full input → context → decision → tool → approval → execution → side-effect → audit chain.

## Milestone 13 — First submission

An operator-only act after Gates A-G. The result may be acceptance, duplicate, rejection, or another outcome; the success criterion is an authorised, reproducible, defensible process that produces evidence or learning.

## Deliberately excluded

- autonomous submission, disclosure, or programme contact;
- mass scanning and quota-driven reporting;
- credential validation by default;
- cloud-hosted raw evidence;
- client-agent governance inside GreyTheory Core;
- payout guarantees.

## North-star metric

**Research Yield:** the percentage of sessions that end in checked evidence or a reusable lesson while authority violations remain zero.
