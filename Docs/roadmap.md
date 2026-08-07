# Roadmap

> **Purpose check.** GreyTheory is a bug bounty and authorised security research engine. Every phase below serves that. See [`definition.md` §1](definition.md#what-it-is-for-and-what-it-governs).

**Current phase:** 3 — surviving contact with real programmes.
**Posture:** local-only. The ceiling sits at `LOCAL_FIXTURE` and no collector performs network I/O.

---

## Done

### Phase 0 — Definition
Three ranked planes, six invariants, capability register. The repository's contradictions found and resolved: a README that authorised probing a policy prohibited, four docs that were 0-byte files linked as real, lane statuses that implied shipping code that did not exist.

### Phase 1 — Authority Plane
Scope compiler that fails closed. Execution gate with seventeen denial paths and one allow. Operator approvals — bound to one action on one target, expiring, single-use. Hash-chained audit log. The provenance triple.

### Phase 2 — Judgement Plane
Evidence vault with the raw/redacted split and a repository guard. Validation gates B–F, deterministic where possible and attested where not. Report studio. Programme registry with drift detection. Triage and earnings ledger that counts the hours which produced nothing. Operator dashboard.

### Phase 2.5 — Signal Plane, offline
Lane framework: collectors reach nothing except through a granted Decision, and cannot promote past `contextual`. Three static lanes — dependency manifests (1), local-tree exposure (2), agent and MCP configuration (4).

---

## Phase 3 — Real programmes *(current)*

Everything so far has been tested against fixtures I wrote, which means the compiler has only ever met ambiguities someone thought to invent. Real programme rules are worse: scope in prose rather than tables, exceptions in footnotes, platform defaults that contradict the programme page, "see our policy" pointing at a fourth document.

**This phase costs nothing and risks nothing.** Compiling a programme involves no contact with its target.

- [ ] Register three real public programmes from pasted or saved source.
- [ ] Record every case where the compiler blocked on something a human resolves in seconds — that list is the work.
- [ ] Extend the compiler for the patterns that actually appear: prose scope, tiered assets, per-asset authority levels, reward tables, temporary exclusions.
- [ ] Handle the platform-versus-programme rule conflict, where a platform default and a programme page disagree. Fail closed and say which is which.
- [ ] Keep the fail-closed bias. A compiler that gets smart enough to guess has stopped being useful.

**Done when** three real programmes compile to contracts the operator would actually rely on, and the blocked cases that remain are ones a human would also stop at.

## Phase 4 — Knowing the field

Feeding the engine what the niche actually knows. All offline.

- [x] **Advisory sourcing.** `greytheory/advisories.py` imports the OSV format that GitHub, PyPI, npm and Go publish, from files already on disk. Ecosystem-aware matching and correct pre-release ordering. `greytheory advisories <file-or-dir>`.
- [ ] **Vulnerability cards.** One per class: plain-English model, root cause, safe test pattern, what counts as evidence, the remediation, and the internal control it maps to. These feed the report studio and the curriculum both.
- [ ] **Curriculum and skill graph.** Learning units with a state machine — not-started, reading, micro-test, lab, transfer, mastered — where mastery expires into review. Mastery means explain, recognise, test, prove, remediate, transfer. Not "watched a video".
- [ ] **Hypothesis engine.** Ranked, scoped hypotheses instead of undirected clicking. Priority from impact potential, programme eligibility, specialism fit and test safety, divided by time cost, duplicate risk and ambiguity.
- [ ] **Postmortems that compound.** A session with no finding still produces a recorded lesson, and the lesson changes the next target score.

**Done when** a study session, a lab and a hunt session all produce artifacts the system can use later, and a duplicate changes the programme score rather than just disappointing someone.

## Phase 5 — Scope Watch

Noticing that a programme changed without being told. **Requires the posture ceiling raised**, since it fetches pages.

- [ ] Fetch registered programme sources on a schedule, through the gate like everything else.
- [ ] Diff against the stored snapshot; on change, invalidate the review and surface it in `needs_attention`.
- [ ] Collect published advisories and authorised write-ups.
- [ ] Information-only throughout. It may trigger a recompile; it may never *be* the scope.

The registry already does the hard half — detecting drift and invalidating review. This adds only the fetching.

## Phase 6 — Raising the posture ceiling

**The decision that changes the risk category, not just a config value.**

Today the worst case is a wrong answer in a report. Above `LOCAL_FIXTURE`, the worst case is an unauthorised request against infrastructure that is not ours — a legal event, not a bug. Gates and approvals make that hard; hard is not impossible, and guardrails only bind if the work routes through them.

Preconditions, all of them:

- [ ] At least one real programme compiled, reviewed and verified (Phase 3).
- [ ] Written authorisation identified, with the researcher account and any required identity headers configured.
- [ ] Network collectors living **outside** `greytheory/`, acting only through a granted `Decision`. The runner refuses them in-package by design and that stays.
- [ ] Rate limits enforced against the contract's declared limit, not a hopeful default.
- [ ] Kill switch tested under load, not just in a unit test.
- [ ] Evidence vault pointed at a real private root, verified to be outside every repository.

**Ceiling raised one level at a time.** `PASSIVE_HTTP` first — unauthenticated reads of in-scope hosts. `AUTHENTICATED` only after passive work has run clean for a sustained period. `INTRUSIVE` requires a per-instance approval and probably never becomes routine.

## Phase 7 — Network collectors

Only after Phase 6, in this order, chosen by proof model rather than by interest:

- [ ] **Subdomain takeover** (Lane 3). First because the proof is binary: a CNAME points at an unclaimed service or it does not. No judgement, no argument.
- [ ] **Exposure over live hosts** (Lane 2). Reuses the shape logic already built; adds reachability, which is the part a local tree could never tell us.
- [ ] **Authorization testing** (Lane 3). IDOR/BOLA across two controlled accounts. The primary specialism, and the hardest to automate honestly — a cross-account response difference is a fact, but only a human can say whether it matters.
- [ ] **Live AI-app testing** (Lane 4). Where the static config review becomes behavioural.

## Phase 8 — First submission

Not a build phase. The point of the system.

- [ ] A finding passes Gates A–F on its own merits.
- [ ] The operator can explain it without reference to any generated prose.
- [ ] Gate G — the decision to send — happens as an operator act.
- [ ] The triage outcome is recorded with programme evidence, whatever it is.
- [ ] The duplicate or rejection, if it comes, changes the target model.

**A rejected first submission that taught something is a success. A quota-driven submission that was accepted is not.**

## Phase 9 — Proof and public surface

Only from authorised material, and only after disclosure permission:

- [ ] Lab write-ups and owned-app findings.
- [ ] Sanitised methodology.
- [ ] ChaseInTech content drawn from real work.
- [ ] Internal ChaseOS hardening artifacts — the transfer already began: reading ChaseOS's approval layer surfaced that its run audits are editable, and the hash chain here is the fix (O9).

---

## Deliberately not on this roadmap

- **Autonomous submission.** Gate G is an operator act by construction.
- **Mass scanning.** The engine optimises for fewer, stronger reports.
- **Credential validation as a default.** Testing whether a found secret is live is `INTRUSIVE`, opt-in, per-instance.
- **Governing other people's agents.** Derivative products, separate scope, not this system.

## Open decisions

Tracked in [`open-questions.md`](open-questions.md). The two that gate everything: raising the posture ceiling (Phase 6), and whether Lane 3 or Lane 2 goes first once it is raised.
