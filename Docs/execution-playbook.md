# Execution playbook

The roadmap says *what*. This says *what happens next, in order*, so work
continues without re-asking the operator for direction already given.

Derived from `Docs/roadmap.md`, `Docs/learner-engagement-design.md`, and
ADR-0029. Updated as items complete.

## The only reasons to stop and ask

Everything else proceeds. These four are genuinely the operator's, and no agent
may decide them:

1. **Host changes** — enabling Hyper-V, creating a VM, changing Windows
   features or services. Prepare a review packet; do not apply.
2. **Granting a submission approval** and triggering a real send (ADR-0029
   tier 3). An agent may assemble and present; the operator approves and sends.
3. **Entering platform credentials** (ADR-0029 tier 2). Build the mechanism;
   the operator provisions the secret.
4. **Raising the execution posture** to `PASSIVE_HTTP` or beyond — the worker
   touching a programme's assets. The collector posture for public reads was
   already approved on 2026-09-08 and does not need re-asking.

Anything already approved is not re-litigated. Anything the roadmap already
sequences is not re-proposed.

## Queue

### 1. Lesson bodies — ~~21 remaining~~ **done 2026-09-08**

All 24 written, one file per lesson under `workbench_ui/src/lessons/` with a
registry in teaching order. Each carries concept, traditional lens, AI-native
lens, stepped worked example, what proof looks like, and three checks
(`recognise`, `decide`, `prove`) with progressive hints.

A regression test asserts every trajectory node resolves to a written lesson on
its own track, so a rename cannot silently break the link.

### 2. Programme-driven topic selection — **done 2026-09-08**

Selection reaches the UI through a `curriculum` read-model section built by
`greytheory_app/curriculum_section.py`, so the UI never parses programme
authority itself. Mission Control renders the ranked topics, each with the
reason and the in-scope assets that selected it, plus the programme's
prohibited techniques as study notes marked `is_target=false`.

Verified end to end against the three real saved programmes.

Ranking is **surface-diverse**: a rule carrying five cards would otherwise
crowd out a whole surface, so the strongest topic from each matched rule is
taken before remaining slots fill by score. Without this, a scope naming an API
lost object ownership to five browser cards.

### 3. Rotation limit — **done 2026-09-08**

`workbench_ui/src/rotation.js` with 9 tests. Two changes per day, configurable.
A spin is spent only when the topic actually changes, so a no-op costs nothing.
Solving a lesson's checks clears that topic and lifts its lock permanently; a
new day restores the allowance without erasing what was earned.

Being out of spins blocks **rotation, never study** — every topic stays
readable, and the message says how to lift the lock rather than only refusing.
State is browser-local because rotation is a motivational device, not evidence.

### 4. Tier 2 login surface — **done 2026-09-08**

Settings carries a **Connect a platform** panel. The operator picks a platform,
pastes their own token, chooses *Ask me again* (memory only) or *Stay signed
in* (encrypted at rest), marks it read-only, and can disconnect.

The credential travels over a dedicated `/api/v1/credentials` route that shares
every admission check with the command route but **dispatches separately**, so
a token never enters the command bus where it would be digested for idempotency
and retained. Tests prove the secret reaches neither the reply, the snapshot,
nor the audit.

At-rest protection is Windows DPAPI via
`greytheory_intelligence/credential_cipher.py`. Where no provider exists,
saving is **refused rather than silently downgraded** to plaintext.

### 5. Collector posture record — **done 2026-09-08**

Collector posture is a **separate axis** from execution posture, in
`greytheory_intelligence/posture.py`. `AuthorityLevel` is ordered by access to a
programme's assets; reading a public index is not that, so putting it on that
scale would make it look like progress toward `PASSIVE_HTTP`.

Recorded posture is `OPERATOR_ACCOUNT` — tiers 1 and 2 were both approved. The
item originally said `PUBLIC_INTELLIGENCE`, written before tier 2 was approved.
Execution posture is unchanged at `LOCAL_FIXTURE`.

`authorise()` enforces the recorded posture before any transport check, so the
code cannot run ahead of what the system says about itself.

**The first live outbound request has been made**:
`acceptance/run-public-directory-read.py` fetched `https://hackerone.com/security`,
HTTP 200, 9,913 bytes, digest
`0ba341758c1d1973a0535cccedf3bf22da2d7670303a708b0a67242f88a03d2c`. Evidence:
`E:\Projects\GreyTheorycceptance\public-directory-20260908-153456-19496\`.

### 6. Share card — **done 2026-09-08**

`workbench_ui/src/shareCard.js` generates an SVG in the browser, previewed live
in the progress panel and downloaded only on request. Personalisation: handle,
avatar, accent colour. Content: topic practised plus real participation figures.

The content rules are **enforced, not documented**. A card is refused if the
handle or topic would carry a certification or mastery claim, a finding,
exploit, breach or bounty reference, a CVE, a URL, a hostname, or an IP. The
refusal explains itself to the learner rather than failing silently. Ordinary
security vocabulary still passes, so the card stays useful.

35 tests, including a static check that the module has no network path.

### 7. Coach follow-ups and session recommendation — **done 2026-09-08**

`workbench_ui/src/coachGuidance.js`, 9 tests.

**On open with no history**: one recommended action that cites what produced it
— an in-flight journey, zero receipts, the thinnest track's coverage, or a cold
streak. The first matching rule wins, so the reason is the most specific true
thing. A test asserts every recommendation carries an action, a because, and a
named evidence source, because a nudge without a basis is an instruction.

**After a turn**: three follow-ups drawn from the lesson's own sections, so a
follow-up cannot lead a learner outside the curriculum. Each names the section
that answers it.

### 7a. Loopback transport flake — **fixed 2026-09-08**

It was a product defect, not a test artifact, and worth the correction.

Refusals happen before the request body is read — an unexpected Host, a missing
token, a wrong origin. Closing a socket that still holds unread inbound data
makes Windows send RST rather than FIN, so the caller's read failed with
`WinError 10053` **instead of receiving the reason it was refused**. A real
client would sometimes see a connection error in place of a clear 400 or 403.

`_error` now drains the body first, bounded in bytes and time. An oversized
declaration is deliberately **not** drained: waiting for bytes a caller may
never send is a denial-of-service shape, and refusing early is the whole point.

From ~1 failure in 4 runs to 0 in 12, and the suite runs roughly twice as fast.
Two regression tests pin both halves.

### 8. Milestone 9 engineering

The GreyTheory VHDX assembly and its host-change review packet. Build and
verify offline; stop at the packet.

### 9. Outbound handover

Keep `Docs/handovers/2026-09-07-claude-to-codex-return-handover.md` current so
an audit can start at any point.

## Standing rules

- Every change ships with tests. A feature without them is not done.
- Nothing claims mastery, authority, or a finding it cannot evidence.
- Files stay under ~300 lines; one responsibility each; content one unit per
  file plus a registry.
- Record what a later agent must not undo in `Docs/agent-activity.md`.
- Both suites green before moving on.
