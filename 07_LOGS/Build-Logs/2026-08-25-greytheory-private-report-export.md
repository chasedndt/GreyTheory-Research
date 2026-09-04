# GreyTheory private redacted report export - 2026-08-25

## Repository truth

- Starting commit: `a4613283efc8be063a5628d7daab78bf2de31435`.
- Worktree: `E:\ChaseOSBuilds\2026-08-24-greytheory-workbench-foundation\worktree`.
- Branch: `codex/2026-08-24-greytheory-workbench-foundation`.
- Canonical ChaseOS remained read-only and its unrelated dirty state was
  untouched.

## Repo-truth delta

The core could render structured report drafts and the evidence vault could
identify an all-redacted export set, but the authenticated workbench command
still refused export. A UI could otherwise be tempted to supply its own draft,
filesystem destination, or incomplete evidence selection.

## Change

- Added a human-acknowledged `EXPORT_REPORT` handler over server-held findings
  and drafts.
- Required a report-ready finding, matching authority, passing Gate F report
  quality, a complete integrity-verified redacted evidence package, fresh
  operator intent, and an immutable safe export identifier.
- Added a private-root writer that atomically emits `report.md`, `report.json`,
  copied redacted evidence files, and a digest manifest.
- Bound the destination root, finding, draft, evidence selection, and operator
  identity on the application side; the UI supplies no prose or path.
- Recorded `submission_performed: false` in the manifest and audit.

## Safety boundary

- Operating posture remains `LOCAL_FIXTURE`; the command result reports
  `executed: false`.
- Export copies only evidence paths returned by the verified redacted-only
  vault package and rehashes each artifact during the copy.
- No submission, programme contact, disclosure, target request, model call,
  browser shell, posture change, deployment, push, merge, secret use, or
  canonical mutation occurred.

## Verification

- Final focused application/transport/capability/validation/evidence suite:
  `98 passed in 5.97s`.
- Full repository suite with pytest artifacts on E:: `582 passed in 22.08s`.
- Acceptance proves report/draft/evidence binding, copied redacted artifacts,
  absence of the raw secret marker, digest manifest, idempotent replay,
  immutable export conflict, audit record, and explicit no-submission state.

## Remaining

- Persisted finding/draft authoring and editing through later research use
  cases; the handler currently consumes a configured server-held report source.
- Dedicated non-executing action-intent handler.
- Operator-selected graphical shell, browser/accessibility acceptance, and
  Windows packaging.
- Any submission integration or `PASSIVE_HTTP` worker remains unavailable and
  separately human-governed.
