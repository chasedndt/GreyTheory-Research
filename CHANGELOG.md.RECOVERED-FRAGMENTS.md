# Recovered fragments: CHANGELOG.md

Original path: `E:\Projects\GreyTheory\2026-09-01-workbench-read-model-binding\worktree\CHANGELOG.md`. The whole file was never captured in a transcript, so these are the
recorded edits in time order: each shows the text that was replaced and the text that replaced it.
Append-style logs can usually be reassembled from the 'new text' blocks.

## 1.   (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
# Changelog

## 2026-09-15 - A sidebar control that was never a control, and a rail you can collapse
````

New text:

````
# Changelog

## 2026-09-16 - The teaching material existed; the teaching page was not using it

**Reported as "appalling", and the report was accurate.** The Learn page opened
with two scenario questions and four "confirm you can explain this" boxes behind
roughly a hundred words of summary. Questions before material is interrogation,
not teaching. Its wrong-answer feedback was a single generic sentence for every
question on every topic - "re-read the focused note" - pointing back at the same
hundred words that had not taught it.

**The cause was routing, not content.** Two parallel systems existed and never
met. `LEARNING_TOPICS` - a lede, four principle cards, a "roadmap" of four
titles with nothing behind them - was what the page rendered. The 28 written
lessons, each with three paragraphs of concept, a traditional lens, an
agent-era lens, a worked example and graded checks, were reachable only from
skill-trajectory nodes elsewhere. The two data sets did not even share keys:
topic `tool-authorization` against card `tool-authorization-failure`.

- **`curriculumPath`** joins what was already there: `SKILL_TRACKS` lists the
  tracks in the order a learner walks them, and every lesson carries a matching
  `trackId` in registry order, which *is* teaching order. Nothing new had to be
  invented - only connected.
- **The rule it enforces:** you are never asked about something you were not
  first taught. A lesson is reachable when everything before it in its track is
  done, and each track shows exactly one entry point rather than a grid of
  equal-looking tiles.
- **Reading ahead is never blocked.** "Comes later" is signposting, not a
  barrier: someone who wants to read on is learning, not cheating.
- Progress is a browser-local practice record. Corrupted or unavailable storage
  reads as *no* progress rather than inventing some - telling a learner they
  were taught something they were not is worse than losing a streak.

**A real ordering defect, found by printing the path rather than reasoning about
it.** `csrf` sat at position 2 in Web & API, ahead of `accessControl` - a
Foundation lesson before a Beginner one, asking someone to reason about forged
cross-site requests before being taught who is allowed to do what. Registry
order is teaching order, so it moved.

**The onboarding is an overlay, not a page.** Its steps span the whole product,
so anchoring it to Mission Control would lose your place the moment you went to
do what a step told you to. Every step is ticked because the underlying fact is
true - a contract recording a human review, a lesson whose checks were worked
through - so it cannot be clicked past, and it stays useful afterwards as a
status board. It refuses to collapse until connected: hiding the one step that
makes your work persist is not a choice worth offering.

**Four fabricated metrics removed.** Mission Control displayed "7 evidence
receipts", "2 reviews", "0 authority violations" and a "5 day" streak, all
hardcoded, on a dashboard whose entire argument is that claims must be sourced.
They now count things on this machine, and "authority violations" is gone
outright because nothing counts them.

**The accessibility contract was retargeted, not deleted.** Six assertions
guarded markup inside the removed page. Satisfying them by restoring that markup
would have reinstated the defect; deleting them would have dropped real
protections. The properties - a labelled region, grouped and announced
questions, a gated practice action, an honest no-mastery line - all survive in
`CurriculumView` and `LessonDialog`, so the assertions moved there. The
`disabled={!labReady}` gate moved too rather than being dropped: it also carries
the guided journey from its learn stage into practise.

**Motion, in one file, gated behind `prefers-reduced-motion: no-preference`.**
CSS rather than a library, because the app already neutralises animation for
reduced-motion users and a JS library would bypass that. Each animation answers
a question the interface was otherwise answering only in words: a reachable
page's light breathes, an opened card reveals, a completed lesson's tick lands.
Only a *live* light animates - a stale or failed one must not draw the eye as
though it were healthy.

Python 1339 passed / 4 skipped; UI 277 passed; build clean.

## 2026-09-15 - A sidebar control that was never a control, and a rail you can collapse
````

## 2.   (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
Python 1339 passed / 4 skipped; UI 277 passed; build clean.
````

New text:

````
**And then none of it ran.** With that suite green and the build clean, the app
did not start at all: `#root` held zero children and the page was blank. The
curriculum route passed `onOpenLesson={openLesson}` while nothing anywhere
declared `openLesson`, and a ReferenceError during render unmounts everything -
so one undeclared name took down the entire product.

Nothing in the pipeline could see it. An undeclared identifier is legal
JavaScript, so the bundler compiled it without complaint; and every UI test here
reads source files as text and matches regexes against them, so not one of them
evaluates a component. "277 passed, build clean" and "the app refuses to start"
were true simultaneously. This is the second time this class has shipped - the
note above `activePack` records the first, a const read before its initialiser -
and that fix left only a comment behind.

**So the suite now runs the app.** `tests/app-mounts.test.mjs` loads `App.jsx`
through Vite's own SSR pipeline - Vite is already a dependency, so no toolchain
is added - and calls `renderToString`, which evaluates every component body and
every hook initialiser. Both past failures fail this test. Each view module is
also evaluated on its own, because mounting the default view alone would let a
broken panel wait undetected until someone navigated to it, which is exactly how
the curriculum route shipped.

Two lessons from writing it, both kept in the file: it must load the project's
real vite config, because dropping `@vitejs/plugin-react` silently switches
esbuild to the classic JSX transform and every module then needs a `React`
binding it correctly does not import; and it had to be added to `test:ui` by
hand, that being an explicit file list rather than a glob - otherwise a new test
file sits in the repository never running, which is worse than no test because
it reads as coverage.

Python 1339 passed / 4 skipped; UI 279 passed; build clean - and this time the
app was loaded in a browser and observed to mount, connect, and render its
panels.
````

## 3.   (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
# Changelog

## 2026-09-16 - The teaching material existed; the teaching page was not using it
````

New text:

````
# Changelog

## 2026-09-16 - What the screenshots showed that every passing test could not

Visual QA with real pixels - headless Edge driven over the DevTools protocol,
walking the app the way a person would - found defects no test and no DOM check
had seen. None of them was about what the markup says; all of them were about
what a person can see and reach.

- **`.surface` carries no padding, and eight panels assumed it did.** It is a
  skin: background, border, radius, shadow. Older panels pad themselves
  (`.learner-loop`, `.study-plan`); the bounty board, programme roster,
  shortlist, directory lookup, bounty workspace, research, campaign and review
  panels did not, so the lower half of Mission Control ran flush against its own
  borders with nothing between sections. The curriculum page had the same fault.
  Each now pads and spaces itself in its own stylesheet, under a doubled
  selector so the result does not depend on which sheet the bundler emits first
  - which is also why the next-lesson card's amber edge had been silently losing
  to `.surface`'s border.
- **The worked example rendered one word per line.** A two-column grid with
  three children auto-placed the step's detail into the 24px number column.
  Pinned to column 2, it now renders 722px wide.
- **Lesson text was about 11px** - `.62-.68rem` on the one surface built for
  sustained reading. Body copy is now near 14.5px with a ~74ch measure,
  questions and options scale with it, and the dialog pads itself: it borrowed
  the coach modal's width, whose body padding is zero. The scenario and takeaway
  styles had never applied at all, because `.lesson__block p` outranked them.
- **The guide contradicted itself.** "Take me there" opened the curriculum and
  then sat on top of the "Begin here" button it was pointing at. Following a
  step now folds the guide first; measured with `elementFromPoint`, the button
  is the topmost element at its own centre. An open guide also light-dismisses
  on a press outside it, and folds when keyboard focus lands on a control it
  covers - WCAG 2.2 SC 2.4.11, Focus Not Obscured.
- **On a phone the guide covered most of the screen, and before connecting it
  could not be dismissed.** It now starts collapsed on narrow screens unless
  someone has chosen otherwise - which needed a third stored state, so "never
  chose" cannot overrule "chose to keep it open" - and it can be minimised
  before connecting, as an amber pill that still says nothing is being saved.
  Minimised, never hidden.
- **A programme's topics were raw identifiers.** "What this programme will ask
  of you" listed `csrf` and `dom-xss` while already looking up the lessons that
  explain them. It now leads with the lesson's title, keeps the identifier as a
  small traceable tag, and opens the lesson: the point where a real bounty hands
  you to the material that teaches it. Its styles moved out of the global sheet
  into `StudyPlan.css`, at a readable scale.
- Smaller: the track progress bar was invisible at zero and its count rendered
  past the page edge; "Open on HackerOne" was underlined inside a button; the
  phone navigation drawer showed a desktop-only rail toggle.

**One failure during QA was the harness, not the code.** Focusing a covered
control did not fold the guide - because Chromium dispatches focus events only
to a page that has focus, and a headless page does not (`document.hasFocus()`
was false). With focus emulated, the unchanged code passed. Confirming that
first avoided "fixing" something that worked.

UI 285 passed, Sites 4 passed, build clean. No Python changed; that suite stands
at 1339 passed / 4 skipped from earlier today. Visual QA: 22 captures at desktop
and phone width, zero page errors, no horizontal overflow.

## 2026-09-16 - The teaching material existed; the teaching page was not using it
````

## 4. 2026-09-11T21:16:27.312Z  (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
# Changelog

## 2026-09-11 - Host change refused by a corrupt component store; nothing altered
````

New text:

````
# Changelog

## 2026-09-11 - Milestone 10 begins: subdomain-takeover verification as claims

- Added `greytheory_collectors/subdomain_takeover.py`, the first binary-proof
  collector. It consumes observations - a CNAME chain and an optional HTTP
  body - and emits claims whose provenance says exactly how far the evidence
  goes: `observed` for a CNAME into a known provider (and for a dangling
  target), `inferred` for the provider's unclaimed-resource marker in the body.
- **It never emits `checked`.** Binary proof of a takeover is claiming the
  resource and serving a token, which is an action on the target; that needs
  the execution posture to allow it and an operator to do it, and the check
  reference then enters through the trust kernel. The assessment restates
  `proven: false` so a candidate cannot be read as a finding.
- Live probing is refused below `PASSIVE_HTTP` (`require_probe_posture`), and
  a test asserts the module carries no resolver or socket of its own: at
  `LOCAL_FIXTURE` there is nothing it could legitimately query, so it cannot.
- Five provider fingerprints (GitHub Pages, S3, Azure Websites, Heroku,
  Fastly), one file each under `takeover_fingerprints/` with a registry. Each
  names the human step that would turn `inferred` into `checked`. Suffix
  matching is exact (`notherokuapp.com` does not match `herokuapp.com`).
- 12 tests.

## 2026-09-11 - Host change refused by a corrupt component store; nothing altered
````

## 5. 2026-09-11T21:22:39.608Z  (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
- 12 tests.

## 2026-09-11 - Host change refused by a corrupt component store; nothing altered
````

New text:

````
- 12 tests.

## 2026-09-11 - Milestone 10, item 2: reachable exposure, scope first

- Added `greytheory_collectors/reachable_exposure.py`. An observation that a
  host answered on a port is only meaningful against a scope contract, so the
  collector asks `classify()` first and emits **nothing** - not a weaker claim,
  nothing - for a host that is not `IN_SCOPE`. A claim about an out-of-scope
  host would be a record of having looked where the programme said not to. A
  programme that prohibits port scanning makes the observation unusable too.
- `observed` for the answer (banner quoted, observer named in the source);
  `inferred` for five services rarely meant to face the internet (redis,
  mongodb, elasticsearch, rdp, smb). Never `checked`: proving an exposure
  matters means interacting with the service.
- An observation must name what observed it, or it is refused.
- Moved the shared probe gate to `greytheory_collectors/probe_posture.py` so
  both collectors refuse live probing below `PASSIVE_HTTP` through one rule,
  and neither carries network code - a test per collector asserts it.
- 19 collector tests; 1138 Python tests pass, 4 skip.

## 2026-09-11 - Host change refused by a corrupt component store; nothing altered
````

## 6. 2026-09-11T21:24:06.552Z  (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
- 19 collector tests; 1138 Python tests pass, 4 skip.

## 2026-09-11 - Host change refused
````

New text:

````
- 19 collector tests; 1138 Python tests pass, 4 skip.

## 2026-09-11 - Milestone 10, item 3: advisory correlation with nothing bundled

- Added `greytheory_collectors/advisory_correlation.py`. It correlates an
  observed product and version with advisories the operator or Scope Watch
  supplies. **No advisories ship with it** - a bundled one would be a claim
  about a real product nobody here verified, and a test asserts the source
  contains no `CVE-`.
- `observed` for the version seen; `inferred` for a version inside an
  advisory's `[affected_from, fixed_in)` range, with the supplier named in the
  claim's source. Never `checked`: confirming an advisory applies means
  exercising it. Banners lie and backports exist, so "affected" is not
  "exploitable here".
- Versions are dotted integers compared numerically (`2.10 > 2.9`). Anything
  richer - `2.4.1-beta` - is refused rather than guessed, and the refusal is
  recorded as an `observed` claim so a skipped advisory is visible.
- Scope first, as every collector: no claim for a host not `IN_SCOPE`.
  Unattributed observations and advisories are refused.
- 12 tests.

## 2026-09-11 - Host change refused
````

## 7. 2026-09-11T21:25:22.568Z  (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
- 12 tests.

## 2026-09-11 - Host change refused
````

New text:

````
- 12 tests.

## 2026-09-11 - Milestone 10, item 4: safe HTTP misconfiguration checks

- Added `greytheory_collectors/http_misconfiguration.py`: five small pure
  checks over one supplied response - HSTS, CSP (including `'unsafe-inline'`
  in `script-src`), CORS wildcard with credentials, version-bearing `Server` /
  `X-Powered-By`, and a directory index on a 200. "Safe" means the checks read
  an ordinary response and the module performs no request; a test asserts it.
- `observed` for what a header literally says or that it is absent;
  `inferred` for the risk that usually implies, because a missing header on
  one response is not a property of the site and a permissive value may be
  intentional for that endpoint. Never `checked`: demonstrating a
  misconfiguration is exploitable is an experiment, and experiments are
  planned, budgeted, and approved.
- HSTS is not expected over plain HTTP. Header names match case-insensitively.
- 11 tests.

**Milestone 10 as a whole:** all four collectors now exist as offline
evaluators over supplied observations, sharing one posture gate and one rule -
scope first, then `observed`/`inferred` only. What remains for the milestone is
the *gathering* side, which is exactly the part `LOCAL_FIXTURE` forbids, so
the milestone stops here until the execution posture is raised.

## 2026-09-11 - Host change refused
````

## 8. 2026-09-11T23:31:20.013Z  (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
# Changelog

## 2026-09-11 - Milestone 10 begins
````

New text:

````
# Changelog

## 2026-09-12 - The corruption is three Hyper-V components, not the store

- After the reboot, `DISM /CheckHealth` reports the store clean, and a full
  `RestoreHealth` (2 h 16 min, exit 0) changes nothing - yet enabling
  `Microsoft-Hyper-V` still fails with 0x80073712. CBS.log names why:
  `Microsoft-Hyper-V-Offline-Common-merged-Deployment-LanguagePack` (en-GB,
  10.0.26100.8875 and .9168) and
  `HyperV-UX-PowerShell-Module-HyperV-WOW64-Deployment` (10.0.26100.8972) are
  flagged `CorruptManifest` at staging time. CBS marks corruption only when a
  component is staged, so a store-wide check that never stages Hyper-V cannot
  see it. The lesson for the record: **"the store is healthy" and "this
  feature can be enabled" are different claims, checked by different code.**
- The repair wrapper's regex matched "No component store corruption detected"
  as needing repair. Fixed to match DISM's actual verdict phrases.
- Host still unchanged: item 1 fails before the registry key is reached, and
  the apply record `host-change-20260912-002843.json` says so.

## 2026-09-11 - Milestone 10 begins
````

## 9. 2026-09-11T23:40:34.449Z  (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
# Changelog

## 2026-09-12 - The corruption is three Hyper-V components, not the store
````

New text:

````
# Changelog

## 2026-09-12 - Milestone 11 groundwork: the role-object-action matrix

- Added `greytheory/lab/authorisation_matrix.py`. The matrix is the
  expectation written down before any request: which controlled identity
  should be able to do which action on which controlled object. Experiments
  derive from it, so a result is always compared against something that
  predates it.
- **Owned things only.** Every identity and object must appear in the
  ownership manifest the two-account fixture already produces; a cell naming
  anything else, or an object owned by an uncontrolled identity, is refused.
- **Every expected denial needs a paired control** - the owner's ALLOW cell
  for the same object and action - and costs two requests, not one. "The
  other user was denied" means nothing unless the owner was served; without
  the control a broken endpoint looks secure.
- Families are derived, not declared: own (control), horizontal (same role,
  other owner), vertical (lesser role), unauthenticated.
- **Budgets refuse rather than trim.** An over-budget family is an error that
  names the family and the shortfall; a planner that silently dropped cells
  would report coverage it did not have. A family with no declared budget is
  also an error.
- **Nothing is executable until every family is reviewed by a named human.**
  Review is recorded per family, so a reviewer sees the shape of what will be
  sent rather than approving one request at a time.
- 10 tests.

## 2026-09-12 - The corruption is three Hyper-V components, not the store
````

## 10. 2026-09-12T00:01:13.570Z  (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
- 10 tests.

## 2026-09-12 - The corruption is three Hyper-V components, not the store
````

New text:

````
- 10 tests.
- Added `greytheory/lab/matrix_binding.py`: a fully reviewed plan binds to one
  research-domain `ExperimentPlan` per family, `READY`, `AUTHENTICATED`, the
  family's request budget as its effect budget, owner ALLOW cells as positive
  controls and DENY cells as negative ones. What the matrix cannot know -
  rollback, stop conditions, evidence plan - must come from the caller; the
  binder refuses to invent them, and the owner-control family says in words
  that it has no negative rather than fabricating one. The domain's own rule
  that `authority_ref` must be a verified contract fingerprint is kept and
  documented, so an experiment can never be bound to an unreviewed contract.
  Records round-trip through the domain serialiser. 5 tests.

## 2026-09-12 - The corruption is three Hyper-V components, not the store
````

## 11. 2026-09-12T00:04:02.869Z  (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
  Records round-trip through the domain serialiser. 5 tests.

## 2026-09-12 - The corruption is three Hyper-V components, not the store
````

New text:

````
  Records round-trip through the domain serialiser. 5 tests.
- Added `greytheory/lab/action_emission.py`: one `ActionRequest` per intent
  and one per paired owner control, control first so a denial is never sent
  unpaired. Each is one question (`max_requests=1`, one request of effect),
  carries the family as its technique, and leaves `approval_ref` empty -
  family review happened in the matrix; approving each request is the gate's
  act, recorded when it happens. Target asset ids are supplied by the caller
  and an unmapped fixture object is refused rather than guessed. The emitted
  count reconciles exactly with the family budget. 7 tests.

## 2026-09-12 - The corruption is three Hyper-V components, not the store
````

## 12. 2026-09-12T00:12:33.054Z  (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
# Changelog

## 2026-09-12 - Milestone 11 groundwork: the role-object-action matrix
````

New text:

````
# Changelog

## 2026-09-12 - The cumulative update cannot install either; the store needs an in-place repair

- KB5124008 (26200.9445) downloaded and failed to install with 0x80240022;
  CBS.log shows the same 0x80073712 at staging. The missing manifests are not
  only Hyper-V's: `Microsoft-Windows-msmq-*` (.8972/.9168) and
  `microsoft-windows-client-desktop-required-deployment*` (en-GB, .8973) fail
  the same way. Intermediate cumulative-update versions were scavenged across
  the store, and Windows Update does not serve superseded builds, so neither
  `RestoreHealth` (which reported success) nor the newer LCU (which needs the
  scavenged versions to stage) can repair it. Chicken and egg.
- No reboot was taken; the host is unchanged. The remaining route is an
  in-place repair install (Settings > System > Recovery > "Fix problems using
  Windows Update"), which reinstalls the current build while keeping files,
  apps and settings. Operator decision, requested 2026-09-12.
- The lesson kept for the record: **DISM's "no corruption detected" is a
  statement about packages it was asked to stage, not about the store.**

## 2026-09-12 - Milestone 11 groundwork: the role-object-action matrix
````

## 13. 2026-09-14T11:12:18.084Z  (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
# Changelog

## 2026-09-12 - The cumulative update cannot install either
````

New text:

````
# Changelog

## 2026-09-14 - The campaign spine: where an engagement stands, in code

The product had every piece of a bug-bounty engagement - scope compilation,
programme-driven curriculum, lessons, collectors, experiment planning, report
drafting, submission transport - and nothing that said **where a campaign
actually is and what is stopping it moving**. That question was being answered
in conversation, which is the wrong place: the honest answer changes with
posture, evidence and approval, and a person should never have to ask an agent
whether they are allowed to proceed.

- Added `greytheory/campaign/`: seven ordered stages - programme, curriculum,
  study, plan, evidence, draft, submission - each reporting `satisfied`, the
  observation behind it, and the next action.
- **"Not permitted" is distinguished from "not done".** `blocked_by_governance`
  marks stages waiting on an operator decision - a posture change, a lifted
  kill switch, a bound approval - rather than on work. Confusing the two makes
  a person believe they are behind when they are waiting, and would let an
  agent present a governance gate as a to-do item.
- **Checked evidence about a programme's assets cannot be claimed below
  `PASSIVE_HTTP`**, and the stage says so with the reason, not a bare false.
  A test proves this holds *even when checked claims are supplied* - the
  posture forbids the assertion, not merely the gathering.
- **A later stage satisfied above an earlier gap is reported as premature**,
  not as progress. A finished report above missing evidence is the exact
  failure this product exists to prevent, so it is named rather than shown as
  a tidy green line.
- Nothing is gathered: every input is supplied and read. The record restates
  `submitted: false`.
- Run against the real GitLab programme it reports: programme and curriculum
  satisfied (19 in-scope assets, 8 topics selected), current stage **study**,
  and evidence blocked by governance naming the VM and the posture decision.
- 14 tests.

## 2026-09-12 - The cumulative update cannot install either
````

## 14. 2026-09-14T11:16:15.978Z  (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
- 14 tests.

## 2026-09-12 - The cumulative update cannot install either
````

New text:

````
- 14 tests.

### Unresolved: one transport failure, not reproduced

`test_an_oversized_declaration_is_refused_without_reading_its_body` failed once
inside a full-suite run, then passed 25 times in isolation, 3 times in file
context, and in a clean full suite of 1197. **Recorded without a verdict**,
because this is the module where a real defect was once written off as a flake.

Two explanations fit, and the evidence does not separate them:

- *Product.* The oversized branch deliberately does not drain the body, so
  unread bytes remain and closing the socket sends RST rather than FIN - the
  same shape as the 2026-09-08 defect, surviving in the branch exempted from
  its fix. A caller could then receive a connection error instead of its 413.
- *Harness.* The test's client timeout is 5 s. The failing run took 300 s
  against 195 s for the green one, so the machine was heavily loaded and the
  timeout may simply have expired.

The load difference is real and favours the second. Do not "fix" the test to
silence it: if it recurs, capture the exception type first - a timeout and a
`ConnectionAbortedError` point at different halves of this.

## 2026-09-12 - The cumulative update cannot install either
````

## 15. 2026-09-14T12:28:19.936Z  (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
# Changelog

## 2026-09-14 - The campaign spine: where an engagement stands, in code
````

New text:

````
# Changelog

## 2026-09-14 - The campaign reaches the read model, and a third gate appears

- Added `greytheory_app/campaign_section.py` and wired it into the snapshot, so
  "where is this campaign" is now a section the UI can render rather than a
  library call. One record per compiled programme: current stage, the reason,
  the next action, and a compact per-stage marker. Posture comes from
  `self.posture`; practised topics come from real `FixtureReceiptStore`
  receipts, not a hand-passed set.
- **The adapter is where the care went.** A `ScopeContract` always carries a
  `verified_at` datetime whether or not anyone reviewed it, so an adapter that
  trusted that field would report a DRAFT contract as verified. The trust
  signal is `status`, and `PENDING_REVIEW` says in its own docstring that it
  still blocks execution. A contract holding `ambiguities` - its own reasons it
  cannot be trusted - is not offered as verified either. Tested per status.

### A third gate, previously unnoticed

Every compiled programme - GitLab, YNAB, MCP SDK - carries
`max_authority: LOCAL_FIXTURE`. **Raising the host posture would still not
permit probing any of them.** The evidence stage now checks the programme's own
ceiling *before* the host posture, because the two have different remedies:
re-compile the contract from the published policy, versus raise the posture.
Sending someone to the wrong decision is worse than saying nothing.

An unparseable ceiling reads as the lowest authority, never the highest: an
unrecognised value is a reason to stop, not licence to continue.

This also caught four of the earlier campaign tests asserting the ceiling while
claiming to test the posture - they passed for the wrong reason. They now use a
programme whose contract permits more, and a new test records the real records'
cap explicitly so it cannot be forgotten again.

- 26 campaign tests; 1209 Python tests pass, 4 skip.

## 2026-09-14 - The campaign spine: where an engagement stands, in code
````

## 16. 2026-09-14T12:28:24.135Z  (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
The load difference is real and favours the second. Do not "fix" the test to
silence it: if it recurs, capture the exception type first - a timeout and a
`ConnectionAbortedError` point at different halves of this.
````

New text:

````
**Updated later the same day, against the load hypothesis.** A subsequent full
suite ran in 342 s - slower than the 300 s run that failed - and the test
passed. The slowest run yet being green weakens the timeout explanation rather
than supporting it, so neither hypothesis is favoured and the cause remains
genuinely unknown.

Do not "fix" the test to silence it: if it recurs, capture the exception type
first - a timeout and a `ConnectionAbortedError` point at different halves of
this, and one of them would mean a real defect in the refusal path.
````

## 17. 2026-09-14T18:15:44.766Z  (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
# Changelog

## 2026-09-14 - The campaign reaches the read model, and a third gate appears
````

New text:

````
# Changelog

## 2026-09-14 - The registry was empty, and the campaign was reporting a fixture

- Registered the three saved programme bundles into the live registry for the
  first time, through `register_bundle` against the real audit chain. Until
  now `%LOCALAPPDATA%\GreyTheory\workbench\programmes` held **nothing**: the
  compile -> review -> registry -> campaign chain had never been exercised end
  to end with real data.
- **A correction.** Earlier the same day I reported the GitLab campaign as
  "current stage: study". That was an assessment of the repo *fixture dict*
  passed in as a raw record, not of a compiled contract. Against the live
  registry all three campaigns report **stage: programme**, blocked, with the
  reason "has N in-scope assets but no human verification". The assessor and
  the section were correct; the claim about the current state was not.
- **`register_bundle` was the right path, and `register` would have been the
  wrong one.** The CLI's single-source route records the programme JSON's own
  text as `raw_source`, which would make our transcription "the text the rules
  came from" and discard the saved sources - GitLab's bundle carries the scope
  CSV, the programme guidelines, and HackerOne's core-ineligible list, plus the
  bundle's precedence and derivation metadata. Registering a record against our
  own restatement of it is the circular-proof shape this codebase keeps finding.
- Compiled state: GitLab and the MCP SDK are `pending_review` with no
  ambiguities; YNAB is `blocked` on two unresolved human resolutions
  (`owned-host-wildcard-vs-listed-targets` and
  `production-api-vs-production-exclusion`). Nothing is verified, nothing is
  reviewed, and every ceiling is `LOCAL_FIXTURE`.

## 2026-09-14 - The campaign reaches the read model, and a third gate appears
````

## 18. 2026-09-14T18:36:43.398Z  (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
# Changelog

## 2026-09-14 - The registry was empty, and the campaign was reporting a fixture
````

New text:

````
# Changelog

## 2026-09-14 - A rate limit is not enough to put traffic on someone else's systems

- Added `greytheory/authority/live_authority.py` and wired it into
  `compile_contract`. A record may no longer claim `PASSIVE_HTTP` or above on a
  rate limit alone. It must also declare **identity**, **egress** and
  **accepted terms**, each present because of a way real research goes wrong:
  - **identity** - a header and a user agent the target can recognise while
    the traffic is arriving. A user agent imitating a browser is refused:
    blending in is what an attacker does, and identification is the point.
  - **egress** - at least one *globally routable* address, and `fail_closed`
    must be true. A tunnel that drops back to the researcher's own connection
    defeats the entire arrangement, so accepting `false` was never an option.
  - **terms** - a named human who read the saved sources and says so in their
    own words. Mirrors `validation.Attestation`: a model may draft it but
    cannot be the one who accepts, and a few words is a checkbox.
- **Inert for every current record.** All three registered programmes cap at
  `LOCAL_FIXTURE`, and the check returns immediately for any ceiling at or
  below it.
- One existing test changed deliberately:
  `test_interactive_authority_with_a_rate_limit_compiles` asserted that a rate
  limit was sufficient. It is not, so the expectation was *moved* rather than
  deleted, and the reason recorded in the test itself.
- **A one-sided-test gap, found and closed.** Every compiler-level assertion
  added was a refusal, so a check wired to always fail would have passed the
  whole suite. Added the accept path - a complete declaration compiles clean to
  `PENDING_REVIEW`, still unverified - which is the single test that would
  catch that.
- Fixed a misleading refusal rather than a hole: a missing `accepted_at`
  defaulted to a naive `datetime.now()`, so it *was* refused, but for being
  timezone-naive instead of for being absent. The reason now says what is
  actually wrong.
- **`is_global` replaced five predicates**, and correctly rejects the RFC 5737
  and RFC 3849 documentation ranges. The first tests used `203.0.113.17` - the
  textbook example address - and the module was right to refuse it: a
  documentation address is by definition not where traffic comes from.
- 1237 Python tests pass, 4 skip.

## 2026-09-14 - The registry was empty, and the campaign was reporting a fixture
````

## 19. 2026-09-14T22:44:26.464Z  (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
# Changelog

## 2026-09-14 - A rate limit is not enough to put traffic on someone else's systems
````

New text:

````
# Changelog

## 2026-09-14 - The campaign becomes visible

- Added `workbench_ui/src/CampaignPanel.jsx` and its co-located
  `CampaignPanel.css`, plus a `campaignFromSnapshot` adapter, wired through
  Mission Control. The campaign section had been in the read model, tested, and
  rendered by nothing - unfinished work by this project's own standard.
- **Why a panel rather than more prose.** "Blocked" and "unfinished" read
  identically in a sentence and are not the same thing. The stage rail draws a
  stage awaiting an operator decision differently from one awaiting work, so
  the difference is visible at a glance. Each entry carries the *reason*, not
  just the position: a stage name without its cause is a progress bar, and a
  progress bar cannot say "waiting on you".
- Marker meaning is not carried by colour alone - each stage also renders
  screen-reader text naming its state.
- Self-contained component with no imports from `App.jsx`, since `Pill` and
  `ShieldCheck` live there and importing them back would be circular.

Two defects caught in my own work while wiring it:

- The component was rendered and its prop threaded, but **never imported**.
  The build would have failed; the node tests would not have caught it, because
  they never load `App.jsx` as a module.
- **`test:ui` is an explicit file list, not a glob.** A new
  `tests/campaign-api.test.mjs` would have silently never run - worse than no
  test, because it reads as coverage while asserting nothing. Adding it to the
  list took the UI suite from 146 to 153, which is the proof it now executes.

- 153 UI tests and 4 Sites tests pass; the production build passes.

## 2026-09-14 - A rate limit is not enough to put traffic on someone else's systems
````

## 20. 2026-09-14T23:18:08.889Z  (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
# Changelog

## 2026-09-14 - The campaign becomes visible
````

New text:

````
# Changelog

## 2026-09-15 - The app had not been mounting at all

- **Fixed a pre-existing temporal-dead-zone error that prevented the entire
  application from rendering.** `assessmentEvidence` referenced `activePack` in
  both its body and its `useMemo` dependency array, while `const activePack`
  was declared on the line *below* it. React evaluates that dependency array
  during render, so every load threw
  `ReferenceError: Cannot access 'activePack' before initialization` and `<App>`
  failed to mount. Fixed by declaring `activePack` above its first use; its own
  dependencies (`selectedPackId`, `journey`) already precede it, so this removes
  the dead zone rather than relocating it.
- **Not introduced by the campaign panel.** The defect sits in inherited
  uncommitted work (the `CoachPanel`/`CoachDialog` changes among 523 uncommitted
  insertions in `App.jsx`). The panel's own import chain is `CampaignPanel.jsx ->
  CampaignPanel.css` and nothing else.
- **Why nothing caught it.** The production build succeeds - bundlers do not
  resolve temporal dead zones. The 153 node tests never evaluate `App.jsx` as a
  module. The accessibility and layout contracts only run regexes against the
  file's *source text*. Nothing in the suite loads the page, so only opening it
  finds this class of defect.
- Verified live: connected to the local API, the campaign panel renders all
  three registered programmes with their stage rails, reasons and next actions.

**A debugging lesson worth keeping.** Four hypotheses were wrong before the
right one: an import cycle, a React version mismatch, a minification fault, and
finally my own new import. The minified stack pointed at byte offset 25:1610,
which lands inside React's scheduler - a red herring produced by reading a
mangled single-chunk bundle by column number. The dev server's *unminified*
build named the real variable on the first load. When a bundle blames vendor
code, check the unminified build before theorising about the bundler.

## 2026-09-14 - The campaign becomes visible
````

## 21. 2026-09-15T00:21:18.707Z  (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
# Changelog

## 2026-09-15 - The app had not been mounting at all
````

New text:

````
# Changelog

## 2026-09-15 - Review material: what you would be confirming, in the dashboard

- Added `greytheory_app/review_section.py` and `workbench_ui/src/ReviewPanel.jsx`
  so "review the compiled scope" is an act performed in the dashboard rather
  than an instruction to go and find files. Asking someone to confirm something
  without showing it to them produces a rubber stamp, which is the single
  outcome the review gate exists to prevent.
- **It shows both halves side by side**: what the compiler concluded - in
  scope, out of scope, prohibited techniques - beside the source documents it
  read. Reviewing is the comparison, so both must be present.
- **Sources come from the registry's own stored copy**, not from a working-tree
  file. The stored bundle retains each document's full content, so the reviewer
  sees the bytes that were actually compiled. This also avoids a
  file-serving route: a page served over http cannot open `file://` links, and
  widening the transport's admission rules to allow arbitrary reads would have
  been the wrong trade for a convenience.
- **`capture_mode` is surfaced deliberately.** `verbatim` is the publisher's own
  text; an `operator_extract` is a paraphrase someone made. Reviewing a
  paraphrase is not the same act as reviewing the source, and a reviewer who
  cannot see the difference is being misled by omission.
- **Hash agreement is a blocking state, not a decoration.** Each source declares
  a hash and the bundle records the one actually computed. If they disagree the
  stored content is not what was claimed, and reading it proves nothing - so the
  document renders blocked and the whole section reports blocked.
- Unresolved `human_resolutions` are surfaced, because they are exactly what a
  blocked contract waits on, and `mark_reviewed` refuses a blocked contract.
- Verified against the live server rather than a fixture: the `review` section
  reports 18 records - 7 source documents across 3 programmes, all hashes
  agreeing, 3 awaiting review - and both panels render in the running app.
- 10 new Python tests and 9 new UI tests. 1247 Python pass / 4 skip; 162 UI and
  4 Sites pass; the production build passes.

**Two notes for whoever runs this next.** A page reload drops the connection by
design - the session token lives only in React state and `connect()` clears it
after use - so both panels correctly disappear until you reconnect. And a
running server does not pick up a newly added section module; the API must be
restarted after adding one, which is why `review` was absent from the snapshot
until the process was replaced.

## 2026-09-15 - The app had not been mounting at all
````

## 22. 2026-09-15T00:32:05.196Z  (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
# Changelog

## 2026-09-15 - Review material: what you would be confirming, in the dashboard
````

New text:

````
# Changelog

## 2026-09-15 - The global footer, compacted

- Desktop footer height 70px -> 40px, measured in the running app at 1440px:
  padding `0 20px`, gap 14px, icons 23px -> 15px, and each item laid out on one
  line rather than stacked.
- **The four labels stay at every width.** `LOCAL_FIXTURE`, no live targets,
  human approval required, and the licence are governance statements, not
  decoration - so the compaction removed height, never facts. Only the
  explanatory sentences collapse.
- Those sentences remain in the DOM, clipped for screen readers rather than
  `display:none`, with the same wording repeated in each item's `title` so a
  pointer can still reach it. Verified clipped in the running app
  (`0x0`, `rect(0,0,0,0)`, not visible) - the clipping resolves against
  `.global-footer` rather than the `span` parent, which was worth checking
  rather than assuming.
- **Every `@media` block was left untouched on purpose.**
  `accessibility-contract.test.mjs` asserts that below 760px the footer is
  `position:static` and the workspace keeps `padding-bottom:0` - a real
  behaviour, since a fixed footer on a small screen obscures content. Only the
  desktop rule changed; 162 UI tests and 4 Sites tests still pass.

## 2026-09-15 - Review material: what you would be confirming, in the dashboard
````

## 23. 2026-09-15T01:13:01.792Z  (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
# Changelog

## 2026-09-15 - The global footer, compacted
````

New text:

````
# Changelog

## 2026-09-15 - All seven campaign stages reachable, and one bounty at a time

**The panel could only ever reach stage 3 of 7.** `assess_campaign` accepts
eight inputs; the read-model section supplied three. `chosen_card_id`,
`plan_reviewed_by`, `claims` and `draft` all fell to defaults, so plan,
evidence, draft and submission read "not yet done" permanently - not because
the work was undone, but because nothing fed them. The assessor was right; the
binding was half-built.

Now wired, from real stored state:

- **`chosen_card_id`** from the active learning journey. A `LearningJourney`
  carries no programme link, so this is passed through *unattributed* on
  purpose: `_study_stage` already refuses a topic the programme's own scope did
  not select, so one bounty can never be credited with study done for another.
  Inventing a programme association would have been the weaker fix.
- **`draft`** matched on `authority_ref` against the contract fingerprint. A
  draft written under an earlier compile correctly stops matching, because a
  report cites the contract it was produced under. **Not** matched on
  `ReportDraft.programme`, which is never populated anywhere - that join would
  have matched nothing while appearing to work.

Two inputs are **deliberately left unwired**, with the reason recorded in code:

- **`plan_reviewed_by`** - `ExperimentPlan` records a status but never who
  reviewed it. Deriving a reviewer from `status is READY` would assert that a
  person acted when nothing recorded that they did.
- **`claims`** - nothing in the service constructs a `SubmissionClaim`, and
  correctly so: a claim describes evidence gathered against a real target,
  which `LOCAL_FIXTURE` forbids.

Both stages therefore report honestly as unmet rather than being handed a value
that makes them look satisfied.

- Fixed a latent crash in the journey selection: `max(..., key=...)` fell back
  to `0` for a missing timestamp and would have compared `int` against
  `datetime`. My fakes used ints, so the tests would have passed while real
  journeys raised - a fixture agreeing with me rather than with reality.
- Added `BountyWorkspace`: one bounty selected at a time, with its stage rail
  and its review material together. Previously both panels listed every
  programme, so working a single bounty meant reading three stacked copies and
  holding the match in your head. Each child now receives exactly one
  programme, so the redundant second switcher disappears on its own.
- 1254 Python tests pass / 4 skip; 162 UI and 4 Sites tests pass; build passes.

## 2026-09-15 - The global footer, compacted
````

## 24. 2026-09-15T09:58:53.563Z  (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
- 1254 Python tests pass / 4 skip; 162 UI and 4 Sites tests pass; build passes.

## 2026-09-15 - The global footer, compacted
````

New text:

````
- **One selection now drives every panel.** `StudyPlan` was extracted from
  `App.jsx` into its own module so the workspace can render it for the selected
  bounty. It needed no restructuring: given a single-programme curriculum its
  own switcher does not draw, the same mechanism that already silenced
  `ReviewPanel`'s. Three panels, one selector.
- Removed the duplicate heading inside `CampaignPanel` when it renders a single
  entry - the tab above already names the bounty and its state, so repeating
  both said the same thing twice in one card.
- Deleted the orphaned `StudyPlan` definition left behind in `App.jsx` after the
  extraction. Nothing rendered it, and a second definition of the same component
  is the kind of thing that later gets "fixed" by importing the wrong one. The
  node tests could not have caught it: they never evaluate `App.jsx`.
- Verified live rather than by inference - three programme names appear exactly
  once, as tabs; no second selector anywhere on the page.
- 1254 Python tests pass / 4 skip; 162 UI and 4 Sites tests pass; build passes.

## 2026-09-15 - The global footer, compacted
````

## 25. 2026-09-15T10:23:21.478Z  (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
# Changelog

## 2026-09-15 - All seven campaign stages reachable, and one bounty at a time
````

New text:

````
# Changelog

## 2026-09-15 - The review gate can be performed, and refusals say why

**The gate had no door.** Review is the act that turns `PENDING_REVIEW` into
`VERIFIED`, and the workspace put the material in front of you - compiled scope
beside the sources it was drawn from - but offered no way to act on it. The only
review command the service dispatched was `REVIEW_HYPOTHESIS_SCOPE`, which
reviews a hypothesis, not a programme. The CLI was the sole route, so the
interface could show you what you would be confirming and then not let you
confirm it.

- **`REVIEW_PROGRAMME`** added end to end, following `RECORD_MASTERY_ASSESSMENT`
  as the precedent for a human governance act. It requires
  `requested_authority is NONE` - reviewing states that a person read a clean
  compile, which is a claim about having read something, not permission to act
  on it - and explicit `human_acknowledged`. Commands that are future-dated
  (>30s) or stale (>10min) are refused: an approval that lands long after the
  person meant it is not consent.
- **A model cannot be the reviewer.** The marker list is imported from
  `live_authority` rather than copied, so the two cannot drift apart.
- **The registry's own refusals now reach the operator verbatim** - "a blocked
  contract cannot be reviewed into verification; resolve its 2 ambiguity/ies and
  recompile" names the rule, the count and the next action. It is not replaced
  with anything vaguer.

**Per-programme review state.** The review section counted `awaiting` only as a
section-level metric, and a count cannot tell a reader whether *this* programme
is one of the ones still waiting. The interface therefore had no honest basis
for offering - or withholding - a review control. Each programme now emits one
`programme_state` record carrying `human_reviewed` and `contract_status`, rather
than smearing that fact across the three scope records. A contract with no
`status` reports `unknown` instead of taking the section down.

- **`reviewability()`** lives in its own module because it is a decision, not a
  shape. Kept out of the component deliberately: this project's UI tests are
  pure JS with no React harness, so logic buried in JSX is logic that cannot be
  tested here.
- **`RecordReview`** sits directly beneath the source documents, so the act of
  confirming and the thing being confirmed stay together. When the server would
  refuse, the control is disabled *beside the reason* rather than hidden - a
  control that silently disappears reads as a bug, and a gate that refuses
  without saying why teaches people to route around it.

**A refusal is no longer reported as a fault.** The transport threw "the local
API returned an unsupported command result" for any non-accepted disposition,
collapsing three unrelated situations - a malformed payload, a result claiming
execution, and a deliberate governance refusal - into one message that describes
a defect. Operators would go looking for a bug in the client instead of
resolving an ambiguity in the source material. A result claiming execution stays
a fault whatever its disposition; a non-accepted disposition now throws the
server's own words. The only existing test on that path covered the accepted
case, so the path every governance decision travels had no coverage at all.

Python 1272 passed / 4 skipped; UI 175 passed; build clean.

## 2026-09-15 - All seven campaign stages reachable, and one bounty at a time
````

## 26. 2026-09-15T11:05:09.552Z  (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
# Changelog

## 2026-09-15 - The review gate can be performed, and refusals say why
````

New text:

````
# Changelog

## 2026-09-15 - Hints exist, and the toggle that claimed to control them now does

**A preference that changed only its own caption.** Settings offered "Show
lesson hints" with two captions - "Context prompts are visible in guided
lessons" and "Hints are hidden for independent practice" - and consumed the
value nowhere. Nothing in the application read it. The control stated a fact
about the product that was not true, which is the same failure as a fabricated
metric: the interface asserting something the system does not back.

There were also no hints for it to govern. An audit of every affordance found
`title=` used twice (both duplicating an already-visible label), one
`role="tooltip"` carrying lesson metadata, one `aria-describedby` on a character
counter, and no help, question-mark, or "what to look for" control anywhere.

- **`HelpHint`** - a disclosure button with `aria-expanded`/`aria-controls`,
  deliberately not a hover tooltip, which would exclude keyboard and touch users
  and treats guidance as decoration rather than content. It is content-agnostic:
  it knows how to disclose, never what is being explained.
- **`helpPreference`** - browser-local for the reason rotation is: this is
  presentation, not evidence. Hiding a hint changes what you are shown, never
  what was observed or what any gate permits. Every degraded path - absent
  value, unavailable storage, a corrupted string - resolves to *showing* hints,
  because silently withholding teaching from a learner is the failure that
  matters. Only the exact string `false` hides them.
- **The Settings toggle now reads and writes that preference**, and announces
  the change so open hints react immediately.

**Wired into the study plan, sourced from the written lesson** rather than
restated in the panel - duplicated teaching copy means two versions of one
explanation, and the unmaintained one is what a learner would read.

**What this exposed:** only 4 of 24 lessons carry a `cardId`. Of the five topics
GitLab's scope selects, only `business-logic-authorization` has a lesson
written; `sql-injection`, `session-management`, `csrf` and `ssrf` have none. The
hint says so in plain words instead of rendering nothing, because a silent gap
reads as "this needs no explanation" when the truth is that nobody has written
it yet.

Two defects caught in review before they shipped: the panel held paragraphs and
lists inside a `span`, which is flow content inside phrasing content, so it now
returns a fragment; and `display:block` on the panel would have overridden the
`hidden` attribute and left every hint permanently open, so `[hidden]` is now
explicit.

Also removed a dead rule: `.global-footer small{display:none}` at the 1260px
breakpoint, which could only hide an element already clipped screen-reader-only
at every width - and in doing so removed it from the accessibility tree, the
opposite of what the rule above it exists for.

UI 181 passed; build clean.

## 2026-09-15 - The review gate can be performed, and refusals say why
````

## 27. 2026-09-15T11:36:57.834Z  (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
# Changelog

## 2026-09-15 - Hints exist, and the toggle that claimed to control them now does
````

New text:

````
# Changelog

## 2026-09-15 - Every topic a registered programme selects now has a lesson

Adding the "what to look for" hints exposed how thin the curriculum binding was:
only **4 of 24 lessons carried a `cardId`**, so roughly one topic in five had
any teaching behind it. A learner opening the study plan for GitLab found four
of its five selected topics silent.

**Two gaps needed no new writing at all.** `http-and-sessions` already *is* the
session-management lesson - its middle section is "Where sessions go wrong",
covering identifier storage, the cookie flags, rotation on privilege change, and
a worked example on whether logout truly ends a session. `input-handling`
already *is* the injection lesson, teaching the general shape (a value reaching
a context that reads it as structure) with a SQL boolean-pair probe as its
worked example and an ethics check about extraction. Both were linked to their
cards rather than duplicated, because a second copy of an explanation is the one
that goes unmaintained and is therefore the one a learner ends up reading.

**One lesson may claim only one card** - `BY_CARD` is a `Map`, so a duplicate
binding would silently let the later entry win - which is why the remaining
topics needed authoring rather than further re-pointing.

Four new lessons, each following the established shape (concept, the
traditional form, the agent-era form, one worked example, what proof looks
like, and three graded checks):

- **`csrf`** - the browser attaches credentials by destination, so the server
  knows *who* but not *whether they meant it*. Framed as the classic confused
  deputy, with the agent-era parallel drawn explicitly: prompt injection is the
  same failure with a different transport, and in both cases intent must be
  established outside the channel the untrusted content arrived on.
- **`ssrf`** - the same shape inverted: the server lends its network position to
  your intent. The worked example targets only a host the researcher controls,
  and stops at "the server made a request I controlled" rather than reaching
  toward internal infrastructure.
- **`reflected-xss`** - the injection shape with the browser as interpreter,
  where the harmed party is another user. The checks push against the habit of
  escalating to a credential-stealing payload: capability is already proven, and
  the payload adds no evidence while risking real people.
- **`dom-xss`** - the variant whose value never reaches the server. Its final
  proof step is the one usually omitted: showing no request carries the value,
  which is what tells a team that server-side encoding will not fix it.

Registry order follows teaching order rather than import order, so forgery sits
directly after sessions, and the two scripting lessons sit after input handling
as the concrete browser-context case of the shape it introduces.

Result: **11 card bindings, all distinct**, and every topic selected by both
registered programmes now resolves to written material. UI 181 passed; build
clean.

## 2026-09-15 - Hints exist, and the toggle that claimed to control them now does
````

## 28. 2026-09-15T15:40:39.763Z  (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
# Changelog

## 2026-09-15 - Every topic a registered programme selects now has a lesson
````

New text:

````
# Changelog

## 2026-09-15 - A shortlist you can curate, with an archive that gives things back

**The front door did not exist.** Nothing browsed, shortlisted, or set aside a
programme; the three in the registry were there because they had been compiled
from saved bundles by hand. There was no record anywhere of which ones the
operator was actually working.

**Why this is not built on `ResearchWorkspace`,** which is where it obviously
belonged. Two findings ruled it out:

- Creating a workspace requires a human-reviewed, **verified**, unexpired
  contract. None of the three programmes qualifies yet - so nothing could have
  been shortlisted, and shortlisting is the act that leads someone *to* review a
  programme. Requiring the outcome as a precondition of the intent would have
  made the front door unreachable.
- `archive_workspace` is **one-way**. Its commit path refuses every write to an
  archived record, including the write that would un-archive it, and no
  `unarchive` exists anywhere. Every mature product treats archiving as
  reversible removal with nothing deleted; a one-way door is a *deletion*
  feature wearing the wrong word.

So `greytheory/shortlist.py` is its own small store: reversible by
construction, usable before review, leaving the workspace machinery for
programmes that graduate into real research.

- **`restore` checks the transition, not the stored status.** That single choice
  is what prevents inheriting the bug above, and a test archives and restores
  three times in a row to keep it honest.
- **Status, outcome and authority are kept separate.** Where an entry sits is
  not why it was set aside, and neither is permission to touch anything. An
  active entry carrying an outcome is refused outright, and restoring clears the
  reason, because a reason for setting something aside cannot outlive the
  setting-aside.
- **Lifecycle is not smuggled into `ReadinessStatus`.** That vocabulary answers
  "is this ready"; an archived entry is neither ready nor blocked. Overloading it
  would make the field unreadable for both purposes.

Three commands - `SHORTLIST_PROGRAMME`, `ARCHIVE_PROGRAMME`,
`RESTORE_PROGRAMME` - all requiring `AuthorityLevel.NONE`. Deliberately **no**
acknowledgement ceremony: these are cheap and reversible, and a confirmation on
every one would train the operator to click through the confirmations that
matter. Archive and restore pin their write to the revision the panel was
showing, so a change made elsewhere is refused rather than overwritten.

**The panel follows the evidence rather than my instincts.** Two views of one
collection means a segmented control, not tabs - and buttons with `aria-current`
rather than a `tablist`, since the list is re-rendered in place and half-tabs
(tab roles with no panel and no arrow keys) are the common failure. Counts sit
on both segments. Archiving is not confirmed; the durable undo is Restore living
permanently in the archive rather than inside a message that times out, which
also avoids putting an interactive control in a timed region. Focus after a row
leaves goes to the list container, never the next row's own control, so a
repeated keypress cannot cascade through the list.

Four empty states, not one. The state that is usually forgotten is the active
list emptied *because everything is archived* - without a route onward from
there, archiving your last programme is a dead end.

Python 1307 passed / 4 skipped; UI 189 passed; build clean. Verified end to end
against the running application: the command round-trips from the browser
through wire parsing, the store, and back into the panel, with the snapshot
independently confirming the write.

## 2026-09-15 - Every topic a registered programme selects now has a lesson
````

## 29. 2026-09-15T18:03:27.702Z  (session 57a5656e-c55f-4c8c-b9ee-279c9147f7bd)

Replaced text:

````
# Changelog

## 2026-09-15 - A shortlist you can curate, with an archive that gives things back
````

New text:

````
# Changelog

## 2026-09-15 - A sidebar control that was never a control, and a rail you can collapse

**Reported as "the toggle doesn't work". It was worse than that.** The profile
row at the bottom of the sidebar - avatar, "Grey Researcher", and a `CaretDown`
chevron - was a plain `<div>`. No click handler, no button element, no keyboard
access, no `aria` anything. The chevron promised a disclosure that had never
been wired, so the control could not be broken: there was nothing there to
break. It is now a real button opening the same local progress record the top
bar avatar does.

Making it a button forced a second correction: its inner `<div>` would have been
flow content inside phrasing content, which is invalid. The avatar and identity
moved to `.sidebar-profile__avatar` and `.sidebar-profile__identity`, which also
makes those rules independent of child order rather than keyed on `>div`/`>span`.

**The collapsible rail already existed - bound to the wrong thing.** The 1030px
media block collapses the sidebar to 78px, hides the labels, and pulls
`.workspace` in to match. That is precisely the requested behaviour, triggered
by viewport width instead of by choice. Rather than write a second
implementation, the same rule set is now also keyed on
`.app-shell[data-rail="collapsed"]`, kept adjacent to the media block so the two
cannot drift apart unnoticed.

- Scoped inside `@media(min-width:761px)`. Without it,
  `.app-shell[data-rail="collapsed"] .workspace` (0,2,1) outranks the mobile
  block's `.workspace{margin-left:0}` (0,1,0) and would have left a 78px gutter
  on a phone. Verified at 375px: drawer off-canvas, margin 0, hamburger shown.
- Nav buttons keep `title={label}`, so a collapsed icon still says what it is on
  hover. That attribute is pinned by the accessibility contract and earns its
  keep here.
- The choice persists in browser storage, for the same reason the hint
  preference does: rail width changes what you are shown, never what is recorded
  or permitted.

Measured live rather than assumed: 238px/238px expanded, 78px/78px collapsed
with sidebar width and content margin agreeing - a rail that narrows while the
content stays put is the failure this was watched for. UI 195 passed; build
clean. `layout-contract.test.mjs` pins the mission picker and trajectory
tooltips only, so these rules were free to change.

## 2026-09-15 - A shortlist you can curate, with an archive that gives things back
````
