# GreyTheory Roadmap

> **Category:** Security Research Operating System
>
> **Current milestone:** 9 — Passive execution pilot (blocked on the posture decision)
>
> **Last completed:** 8 — Scope Watch, offline portion
>
> **Posture:** `LOCAL_FIXTURE`; no network I/O or live-target interaction.

The existing Authority, Signal, and Judgement planes remain the trust architecture. This roadmap adds the product and research layers required to make that kernel a complete day-to-day research environment.

## Existing verified baseline

- Authority Plane, offline Signal framework with three static collectors, and Judgement Plane are implemented.
- Offline OSV advisory import is implemented.
- 443 repository tests pass, including 13 focused Milestone 6, 10 focused Milestone 5, and 8 focused Milestone 4 acceptance tests.
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
`test_fixture` provenance. Focused acceptance passes 10 tests; the full suite
passes 430. Broader training-mode orchestration and adaptive curriculum remain
PARTIAL and are not part of this exit claim.

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

## Milestone 9 — Passive execution pilot

Raise only to `PASSIVE_HTTP`, for one verified programme and one tightly controlled action type, after every precondition in `THREAT_MODEL.md` is implemented and tested.

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
