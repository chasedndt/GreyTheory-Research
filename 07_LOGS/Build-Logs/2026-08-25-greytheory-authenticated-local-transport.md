# GreyTheory authenticated local transport - 2026-08-25

## Repository truth

- Starting commit: `2f2bbc5f981708936a9987c96d4497af40fe6eac`.
- Worktree: `E:\ChaseOSBuilds\2026-08-24-greytheory-workbench-foundation\worktree`.
- Branch: `codex/2026-08-24-greytheory-workbench-foundation`.
- Canonical ChaseOS remained read-only and its unrelated dirty state was
  untouched.

## Repo-truth delta

GreyTheory had a transport-neutral workbench service but no supported local
launch path. A future browser shell would otherwise need to invent its own
store assembly, request parsing, authentication, origin policy, and command
limits.

## Change

- Added strict round-trip decoding for the versioned `WorkbenchCommand`
  contract, including exact keys/types and `executable: false`.
- Added `greytheory_local` private runtime assembly for programme, research,
  learning, evidence, approval, and audit stores outside every Git worktree.
- Added the `greytheory-workbench` / `python -m greytheory_local` launcher.
- Added numeric `127.0.0.1`-only binding, exact Host admission, in-memory bearer
  authentication, exact-origin POST admission, no CORS, 64-KiB body ceiling,
  five-second body timeout, no transfer encoding, and duplicate critical
  header/JSON-key refusal.
- Added no-store defensive JSON responses and a minimal non-private health
  route. The listener serves no files and imports no target client.
- Accepted ADR-0012 and reconciled capability, threat, roadmap, project,
  workbench, changelog, and governed-log truth.

## Safety boundary

- Operating posture remains `LOCAL_FIXTURE`; every application result remains
  non-executing.
- No target request, external bind, CORS permission, browser shell, model,
  process adapter, passive worker, credential persistence, posture change,
  deployment, push, or canonical mutation occurred.
- The printed token is process-local launch material, not a durable credential.

## Verification

- Focused transport/application/capability suite: `24 passed in 4.73s`.
- Full repository suite with pytest artifacts on E:: `580 passed in 24.86s`.
- Byte-compilation passed with cache output redirected to E:; setuptools
  discovery includes `greytheory_local`; launcher `--help` passed.
- All local links in the 16 changed or new Markdown files resolved and
  `git diff --check` passed.
- Acceptance covers private-root refusal, real-store assembly, every non-v1
  bind refusal, strict command round-trip, Host/token/origin denial, no CORS,
  snapshot read, successful non-executing command dispatch, oversized body,
  content type, duplicate Host, and duplicate JSON-key refusal.
- AST policy proves the local launch package has the standard-library server
  but no target HTTP client, subprocess, or browser adapter import.

## Remaining

- Selected graphical Today/Learn/Research shell and browser-level acceptance.
- Installed shortcut, current-user Windows ACL verification, clean-user launch,
  accessibility, responsive operation, packaging, and update lifecycle.
- Later action-intent, mastery-assessment, and report-export use cases.
- This decision does not authorize LAN, VPS, remote access, or `PASSIVE_HTTP`.
