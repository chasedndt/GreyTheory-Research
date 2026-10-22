# GreyTheory: Claude to Codex / GPT-6 Astra return handover — 2026-09-08

Prepared 2026-09-08. Author: Claude. Owner: ChaseInTech.

Second and much larger day of work. The
[2026-09-07 handover](2026-09-07-claude-to-codex-return-handover.md) covers the
VHDX determinism session and remains accurate for that day; where the two
disagree, this one is later.

Worktree, branch, and HEAD unchanged. Nothing committed or pushed.
At writing: **61 modified tracked files, 132 untracked entries, 1,033 tests
collected.**

## A. What changed

### A1. Curriculum — all 24 lessons written

`workbench_ui/src/lessons/`, one file per lesson plus a registry in teaching
order. Each carries concept, a traditional lens, an AI-native lens, a stepped
worked example, what proof would look like, and three checks (`recognise`,
`decide`, `prove`) with progressive hints.

A regression test asserts every one of the 24 trajectory nodes resolves to a
written lesson **on its own track**, so renaming either side cannot silently
break the link.

### A2. Programme-driven curriculum selection — the moat

`greytheory/learning/programme_curriculum.py` maps compiled programme scope to
catalogue cards through six hand-authored, reviewable rules. It reaches the UI
through a `curriculum` read-model section
(`greytheory_app/curriculum_section.py`), so the UI never parses programme
authority itself.

Two decisions worth probing:

1. **Identity evidence is tracked separately from asset evidence.** The MCP SDK
   programme names an agent surface in its title while listing only version rows
   as assets, so ignoring identity would miss the material that matters most.
   Identity evidence never enters `matched_assets`, so it cannot widen scope,
   and a test enforces that. Only rules describing what a programme *is*
   (`api`, `agent-sdk`) are identity-eligible.
2. **Ranking is surface-diverse.** A rule carrying five cards outscored one
   carrying two purely on card count, so the real YNAB scope produced five
   browser cards and dropped object ownership despite naming an API host.
   `_diverse()` takes the strongest topic per matched rule before filling by
   score. Verified live: YNAB now surfaces `bfla` at rank 5.

### A3. Platform integration — ADR-0029

The operator approved all three tiers on 2026-09-08. **Read ADR-0029 before
auditing any of this**; it records the approval and the limits that survive it.

- **Tier 1** — `directory_fetcher.py`. HTTPS only, GET only, declared origin,
  **redirects refused**, response ceiling, content-type check, no credential.
- **Tier 2** — `platform_credentials.py` (session or encrypted-at-rest,
  Git-worktree refusal, zeroing leases, overwrite-before-unlink),
  `credential_cipher.py` (DPAPI, entropy bound per platform), `account_reader.py`
  (token in an `Authorization` header and nowhere else).
- **Tier 3** — `submission.py`. Payload-digest-bound authorisation, so editing
  one character invalidates approval. Kill switch engaged by default, one
  approval sends once, every claim must be `checked` and receipt-backed.
- Shared `authorisation.py` so both read tiers apply identical transport rules.

**The credentials route deliberately bypasses the command bus.**
`/api/v1/credentials` shares every admission check with `/api/v1/commands` but
dispatches before a `WorkbenchCommand` is built, because the bus digests whole
commands for idempotency and retains them in memory.

### A4. Collector posture — a separate axis

`greytheory_intelligence/posture.py`. `AuthorityLevel` is ordered by access to a
programme's assets; reading a public index is not that. Putting
`PUBLIC_INTELLIGENCE` on that enum would have made approving a directory read
look like progress toward `PASSIVE_HTTP`.

Recorded collector posture: `OPERATOR_ACCOUNT`. **Execution posture unchanged at
`LOCAL_FIXTURE`.** Every record restates that they did not move together.

### A5. The first live outbound request

`acceptance/run-public-directory-read.py` fetched
`https://hackerone.com/security` — HTTP 200, 9,913 bytes, body digest
`0ba341758c1d1973a0535cccedf3bf22da2d7670303a708b0a67242f88a03d2c`.

Evidence:
`E:\Projects\GreyTheory\acceptance\public-directory-20260908-153456-19496\`.
The record states `credential_sent=false`, `redirect_followed=false`,
`target_interaction=false`, `asset_touched=false`, `submission_performed=false`,
`grants_authority=false`. Retrieved content is `PUBLIC` and `UNTRUSTED`.

### A6. Engagement surfaces

Local participation tracking (`achievements.js`), practice ranks (`titles.js`),
share card (`shareCard.js`), topic rotation (`rotation.js`), coach follow-ups
and session recommendation (`coachGuidance.js`).

The rule holding all of it together: **a rank never travels without its
criterion**, and a recommendation always cites the state that produced it. The
share card enforces its content rules in code, refusing handles or topics that
carry certification claims, findings, CVEs, URLs, hostnames, or IPs — a guard
that caught one of our own rank blurbs during development.

### A7. A "flake" that was a real defect

`tests/test_local_workbench_transport.py` had failed roughly 1 run in 4 with
`WinError 10053`. It was recorded as a harness race. **It was not.**

Refusals are written before the request body is read. Closing a socket holding
unread inbound data makes Windows send RST rather than FIN, so a caller could
receive a connection error **instead of the reason it was refused** — a 400
`host_refused` or 403 `origin_refused` lost to a reset.

`_error` now drains first, bounded in bytes and by a one-second timeout. An
oversized declaration is deliberately **not** drained: waiting for bytes a
caller may never send is a denial-of-service shape. From ~1-in-4 failures to
0 in 12, and the suite runs about twice as fast.

A first attempt drained unconditionally and made it 8-in-8. Worth knowing before
anyone simplifies the bounds away.

## B. Milestone 9 — where it actually stands

### B1. Built and tested offline

- `acceptance/vhdx_assembly_spec.py` — turns the VM contract's prose into
  checks. 17 tests covering a resigned boot component, a writable partition
  surviving reboot, a network interface, a substituted payload, a missing kernel
  feature, and a reusable worker contract.
- `acceptance/assemble-greytheory-vhdx.sh` — copies signed components byte for
  byte, never rebuilds one, refuses an output root outside the governed E:
  artifact tree. Syntax checked, zero CR bytes.
- `Docs/host-change-review-packet.md` — five host changes, the exact registry
  key, rollback for each, and the Hermes impact stated plainly.

### B2. Not done, and honestly so

- **The assembly script has never been executed.** It was written at the end of
  the session and WSL failed before it could run. Its syntax is checked; its
  behaviour is not. **Treat it as unproven code.**
- No VHDX assembled, converted, normalised, or validated end to end.
- No VM exists. No boot attempted. None of the eight negative tests in the
  review packet has been run.
- Milestones 10 through 13 untouched.

### B3. WSL state at session end

`wsl.exe` fails with `Wsl/Service/E_UNEXPECTED` on every new command.
`wsl --list` reports Ubuntu **Running** and `vmmemWSL` is alive, so the distro
and the Hermes processes inside it are probably still up — what is broken is
starting new commands.

None of the lingering `wsl.exe` processes belong to this session: four are
Docker Desktop's, two are Hermes cron pollers. But this session was by far the
heaviest user of `wsl.exe` and a contribution cannot be ruled out.

`wsl --shutdown` would likely clear it, and would stop Hermes inside the distro.
Left to the operator rather than decided by an agent.

## C. Operational mistakes made this session

Recorded because an auditor should know what was done badly, not only what was
built.

1. **A broad `Stop-Process -Name python`** to free a port. The incoming handover
   explicitly warns against this. It restarted Hermes on Windows; WSL processes
   were unaffected. The correct form resolves the PID holding the port:
   `(Get-NetTCPConnection -LocalPort <port> -State Listen).OwningProcess`.
2. **A flake dismissed rather than investigated** (A7) — a real defect for most
   of the day because it was annotated instead of read.
3. **A stale assumption carried in the playbook** — item 5 said raise the
   collector posture to `PUBLIC_INTELLIGENCE`, written before tier 2 was
   approved. The posture gate refusing tier 2 is what surfaced it.

## D. Review questions for Astra

1. Is collector posture genuinely separable from execution posture, or does
   `OPERATOR_ACCOUNT` create a path toward target interaction I have missed?
2. Does the credentials route's bypass of the command bus lose any admission
   check that route provides?
3. Is DPAPI same-profile protection adequate for platform tokens, given its ACL
   hardening and cross-profile recovery remain open gates?
4. Does payload-digest binding actually prevent an edited submission, including
   whitespace-only and unicode-normalisation edits?
5. Is surface-diverse ranking defensible, or does it under-weight a genuinely
   dominant surface?
6. Review `assemble-greytheory-vhdx.sh` as **unrun code**: partition sizing,
   loop-device cleanup on every failure path, the `blkid` discovery of donor
   partitions, and whether `dd` onto a partition can silently truncate.
7. Does draining a refused request body introduce any new denial-of-service
   surface at the bounds chosen?
8. Confirm no engagement surface — ranks, share card, rotation — can be read as
   a competence claim.

## E. Suggested order for the next session

1. Recover WSL (operator decision), then **run** the assembly script and
   validate its output against the specification.
2. Convert, normalise, and two-build the resulting VHDX.
3. Present the host-change review packet for a decision.
4. Only with approval, create the VM and run the eight negative tests.
