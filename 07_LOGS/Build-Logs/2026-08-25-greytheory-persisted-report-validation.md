# GreyTheory persisted human-bound report validation - 2026-08-25

## Repository truth

- Starting commit: `50e9823168cc004abe906f54928f1d8173069975`.
- Worktree: `E:\ChaseOSBuilds\2026-08-24-greytheory-workbench-foundation\worktree`.
- Branch: `codex/2026-08-24-greytheory-workbench-foundation`.
- E: had 693.75 GiB free at start.
- Canonical ChaseOS remained read-only with 14,610 unrelated tracked changes.

## Repo-truth delta

Private report cases and drafts survived restart, but the workbench had no
bounded command for rerunning and persisting validation. Gate B-F results were
therefore available only through lower-level code, not as revisioned operator
state visible to the local workbench.

## Change

- Added `RUN_REPORT_VALIDATION`, requiring explicit human acknowledgement, a
  fresh command timestamp, the current report revision, and no authority.
- Derived the attester from the configured local operator and accepted only
  evidence identifiers already bound to the finding or its private manifest.
- Reran deterministic Gates D/F and human-attested Gates B/C/E against the
  persisted finding, draft, and verified private evidence.
- Persisted each immutable validation run with its checked case revision,
  attestations, and gate results inside the integrity-checked report store and
  exposed `not_run`, `blocked`, or `passed` through the report read model.
- A later draft or finding edit preserves history but invalidates the current
  validation status until the operator explicitly reruns the gates.
- Added complete validation deserialisation and fail-closed invariants for
  timezone awareness, finding binding, unique/full B-F results, and the exact
  B/C/E attestation set.

## Safety boundary

- Passing validation records eligibility evidence for the operator's separate
  Gate G decision. It does not bind missing claim roles or promote a finding.
- Validation does not export, submit, contact a target, execute, call a model,
  invoke a worker, or change posture.
- Operating posture remains `LOCAL_FIXTURE`; Canonical and unrelated worktrees
  were untouched.

## Verification

- Focused persistence/application/validation/transport/capability suite:
  `59 passed in 2.26s`.
- Full repository suite with pytest artifacts on E:: `588 passed in 22.28s`.
- `python -m compileall -q greytheory greytheory_app greytheory_local` passed
  with `PYTHONPYCACHEPREFIX` rooted on E:; package discovery and
  `python -m greytheory_local.cli --help` passed.
- Relative Markdown links passed for all 13 changed/new documentation files;
  `git diff --check` passed.
- Acceptance covers explicit human acknowledgement, fresh timestamps,
  server-derived attester identity, known evidence references, persisted
  round trips, full gate-set invariants, optimistic conflicts, later-edit
  invalidation, read-model status, unchanged lifecycle, and separate export.

## Remaining

- Workbench claim-role binding and governed finding-lifecycle transitions.
- Operator selection and implementation of visual direction 1, 2, or 3.
- Browser/accessibility/responsive and packaged Windows acceptance.
- Passive capture encryption, worker controls, and Ubuntu VM acceptance remain
  separate; `PASSIVE_HTTP` is not enabled.
