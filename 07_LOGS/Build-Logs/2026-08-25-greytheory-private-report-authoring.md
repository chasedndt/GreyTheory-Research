# GreyTheory persistent private report authoring - 2026-08-25

## Repository truth

- Starting commit: `1622d6d5d1690347c28b8e6bfbf0e15251a728be`.
- Worktree: `E:\ChaseOSBuilds\2026-08-24-greytheory-workbench-foundation\worktree`.
- Branch: `codex/2026-08-24-greytheory-workbench-foundation`.
- E: had 693.77 GiB free at start.
- Canonical ChaseOS remained read-only with 14,610 unrelated tracked changes.

## Repo-truth delta

The local runtime could export a configured server-held draft but did not own a
persistent report source. Reports therefore rendered `UNKNOWN` in the default
launcher, and a restart could not retain workbench-authored prose. Separately,
`Finding.from_dict` discarded persisted claim-role bindings and receipts.

## Change

- Added full `CheckReceipt`, `RoleBinding`, and `Finding` deserialisation so a
  report-ready claim matrix survives restart.
- Added an integrity-checked private `ReportStore` with Git-worktree refusal,
  atomic writes, audited create/save operations, and optimistic case revisions.
- Added informational report-case creation from a persisted testing/supported
  hypothesis. Programme, asset, target, authority, and initial lifecycle state
  are derived on the application side.
- Added full-draft revisioned saves. The UI can edit prose and select existing
  evidence identifiers but cannot supply authority, finding state, programme,
  asset, or claim-matrix state.
- Added measured draft revision/completeness/export-candidate fields to the
  report read model and wired the store into the default local runtime.
- Reused the same persisted store for private redacted export acceptance.

## Safety boundary

- New cases begin `informational`; authoring cannot promote claims or findings.
- Saving a draft never validates, exports, submits, contacts, executes, calls a
  model, invokes a worker, or changes posture.
- Operating posture remains `LOCAL_FIXTURE`; Canonical and unrelated worktrees
  were untouched.

## Verification

- Focused report-store/application/transport/claim-role suite:
  `60 passed in 6.06s`.
- Full repository suite with pytest artifacts on E:: `587 passed in 22.56s`.
- Acceptance covers restart persistence, envelope tamper detection, Git-root
  refusal, audit events, stale revision conflict, server-owned context,
  incomplete-draft status, full claim/receipt round trip, and export from the
  persisted store.

## Remaining

- Workbench validation, claim-role binding, and finding-lifecycle promotion.
- Operator selection and implementation of visual direction 1, 2, or 3.
- Browser/accessibility/responsive and packaged Windows acceptance.
- Passive worker controls and Ubuntu VM acceptance remain separate.
