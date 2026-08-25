# GreyTheory bounded local-fixture action intent - 2026-08-25

## Repository truth

- Starting commit: `9b5466b8889b58a12696e63b3880f546e7dfb866`.
- Worktree: `E:\ChaseOSBuilds\2026-08-24-greytheory-workbench-foundation\worktree`.
- Branch: `codex/2026-08-24-greytheory-workbench-foundation`.
- Canonical ChaseOS remained read-only and its unrelated dirty state was
  untouched.

## Repo-truth delta

The workbench command contract could express an action request but the
application service refused it. The research store already enforced active
session/experiment/hypothesis state and request/effect budgets, so the missing
piece was a strict UI-intent adapter—not a second executor.

## Change

- Added a fresh, human-acknowledged `REQUEST_ACTION` handler limited to
  `LOCAL_FIXTURE` and `fixture.*` action types.
- Required the exact action to exist in the selected active server-held
  experiment and the target to match the in-scope hypothesis target.
- Derived workspace, session, hypothesis, target, authority fingerprint,
  identity, required authority, and stop conditions from persisted state.
- Persisted one bounded `ActionRequest` through the existing research store;
  request and effect ceilings remain store-enforced.
- Added idempotent replay, typed duplicate conflict, unplanned-action refusal,
  and network-shaped action-type refusal.

## Safety boundary

- Operating posture remains `LOCAL_FIXTURE`; every application result reports
  `executed: false`.
- The handler does not call the Gate, resolve approval, invoke a fixture,
  launch a process, contact a target, or create an action receipt.
- No posture change, deployment, push, merge, secret use, or canonical mutation
  occurred.

## Verification

- Focused application/research/transport/capability suite:
  `42 passed in 6.10s`.
- Full repository suite with pytest artifacts on E:: `583 passed in 22.77s`.
- Acceptance proves server-side derivation, active lifecycle and budget checks,
  idempotency, zero receipts, unplanned-action denial, and non-fixture denial.

## Remaining

- Persisted workbench report authoring and later research lifecycle handlers.
- Operator selection and implementation of the graphical shell.
- Browser, accessibility, 390-pixel, Windows package/ACL/clean-user acceptance.
- A future UI action remains intent only; execution still requires the separate
  Gate/executor path and is not added by this slice.
