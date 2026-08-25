# GreyTheory governed research-planning handlers - 2026-08-25

## Repository truth

- Starting commit: `e4a74dea4c35ce18d200e86120288b1ec968b865`.
- Worktree: `E:\ChaseOSBuilds\2026-08-24-greytheory-workbench-foundation\worktree`.
- Branch: `codex/2026-08-24-greytheory-workbench-foundation`.
- Canonical ChaseOS remained read-only and its unrelated dirty state was
  untouched.

## Repo-truth delta

The application contract could show complete research state but refused every
research command. A graphical shell therefore could not drive even the safe,
pre-execution hypothesis-to-plan journey. Research records also lacked an
optimistic revision suitable for stale UI detection.

## Change

- Added non-negative revisions to hypothesis and experiment records with
  backward-compatible loading of revision-zero state.
- Added a create-only hypothesis handler that derives its authority reference
  from the persisted workspace and records only an `unproven` draft.
- Added explicit, human-acknowledged scope review against an already in-scope
  stored target. It records a review basis but grants no authority.
- Added atomic experiment planning: the experiment is added and the hypothesis
  moves from `scoped` to `planned` in one integrity-checked store write.
- Added typed stale-revision conflict handling at both service and store race
  boundaries, idempotency, and snapshot revision exposure.
- Reconciled capability, roadmap, project, workbench, changelog, and governed
  log truth.

## Safety boundary

- Operating posture remains `LOCAL_FIXTURE`.
- Every accepted result remains `executed: false`.
- No fixture, Gate action, model, process, network, target, report export,
  mastery award, posture change, deployment, push, or canonical mutation
  occurred.
- Action-intent, mastery-assessment, and report-export handlers remain refused.

## Verification

- Focused application/research/capability suite: `33 passed in 5.01s`.
- Full repository suite with pytest artifacts on E:: `574 passed in 23.88s`.
- Byte-compilation passed with Python cache output redirected to E:; setuptools
  discovery includes both `greytheory_app` and `greytheory_broker`.
- All local links in the 10 changed Markdown files resolved and
  `git diff --check` passed.
- Tests cover create-only conflicts, explicit human acknowledgement, derived
  authority, stale UI revisions, store-side revision races, failed-plan
  atomicity, successful scope-to-plan state, and the continuing non-execution
  contract.

## Remaining

- Loopback-only transport, request limits, origin/session protection, and a
  Windows local launch command.
- Operator selection and implementation of one of the three visual concepts.
- Action-intent, explicit mastery-assessment, and report-export use cases.
- Accessibility, 390-pixel acceptance, packaging, and clean-user launch proof.
- Every passive-worker, VM/VPS, canary, and posture gate remains separate.
