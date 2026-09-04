# GreyTheory governed local claim lifecycle - 2026-08-25

## Repository truth

- Starting commit: `ef71d4536f1a03148d951d00f0b63aac256b3b20`.
- Worktree: `E:\ChaseOSBuilds\2026-08-24-greytheory-workbench-foundation\worktree`.
- Branch: `codex/2026-08-24-greytheory-workbench-foundation`.
- E: had 693.72 GiB free during final verification.
- Canonical ChaseOS remained read-only with 14,610 unrelated tracked changes.

## Repo-truth delta

The workbench could author and validate a private report but could not assemble
the seven required claim roles or persist a guarded internal lifecycle move.
The lower-level vertical slice proved those concepts, but the default local
application had no typed, revision-safe use case for them.

## Change

- Added exact two-account-fixture claim assembly that reads only existing
  private raw evidence, verifies integrity/authority/current scope, reruns five
  deterministic validators, and derives reproduction/impact roles from the
  configured operator's persisted attestations and explicit uncertainty.
- Added atomic finding-plus-report-matrix persistence with strict refusal of
  unrelated identity, lifecycle, or prose changes. Assembly invalidates the
  prior validation pass and creates no evidence or target interaction.
- Added next-state-only internal lifecycle progression. `report_ready` requires
  a current passing Gates B-F run and all seven sound role bindings; the
  handler cannot enter `submitted` or any programme-owned outcome.
- Added a digest-bound `finding.json` to private exports so claim-role bindings
  and validator receipts remain inspectable alongside the report and redacted
  evidence.

## Safety boundary

- The UI cannot author authority, claims, checked provenance, receipts,
  lifecycle destination, or artifact formats.
- Claim assembly is limited to the exact in-memory two-account fixture and a
  reviewed current programme contract; broader passive adapters remain absent.
- No network, model, worker, new fixture action, submission, programme outcome,
  posture change, deployment, push, merge, secret use, or canonical write.

## Verification

- Focused claim/lifecycle/export/application/domain/transport suite:
  `106 passed in 4.60s`.
- Final store/application/capability boundary subset: `14 passed in 2.69s`.
- Full repository suite with pytest artifacts on E:: `590 passed in 22.40s`.
- `python -m compileall -q greytheory greytheory_app greytheory_local` passed
  with `PYTHONPYCACHEPREFIX` rooted on E:; package discovery and
  `python -m greytheory_local.cli --help` passed.
- Relative Markdown links passed for all 13 changed/new documentation files;
  `git diff --check` passed.
- Acceptance proves seven unique roles, validator receipts, no evidence
  mutation, optimistic revisions, validation invalidation/rerun, one-state
  progression, retained current pass after state-only promotion, receipt-chain
  export, and refusal past `report_ready`.

## Remaining

- General/passive claim assembly needs its own validator/evidence adapter.
- Operator selection and implementation of visual direction 1, 2, or 3.
- Browser/accessibility/responsive and packaged Windows acceptance.
- Passive capture encryption, adapter conformance, worker controls, and Ubuntu
  VM acceptance remain separate; `PASSIVE_HTTP` is not enabled.
