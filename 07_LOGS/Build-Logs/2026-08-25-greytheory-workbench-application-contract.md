# GreyTheory workbench application contract - 2026-08-25

## Repository truth

- Worktree: `E:\ChaseOSBuilds\2026-08-24-greytheory-workbench-foundation\worktree`.
- Branch: `codex/2026-08-24-greytheory-workbench-foundation`.
- Starting commit: `b98ba5ebd435ade046be0dbc1c64c9aac1a1a6ea`.
- The canonical ChaseOS vault was read only; its unrelated dirty state was not changed.

## Repo-truth delta

The architecture and guided-learning state machine existed, but the planned UI
had no application boundary it could call. The static dashboard remained a
separate export. There was no versioned assembly of programmes, learning,
research, hypotheses, evidence, reports, approvals, audit readiness, and
capability truth, and no typed workbench command result.

## Change

- Added `greytheory_app`, separate from the offline trust kernel.
- Added a versioned UI-neutral snapshot with stable sections, context, runtime
  readiness, source errors, and one non-executable next action.
- Missing sources are `UNKNOWN`, configured empty stores are `EMPTY`, and
  corrupt sources fail closed as `BLOCKED`.
- Added typed commands and results with idempotency, expected revisions, human
  acknowledgement, and structural `LOCAL_FIXTURE` ceilings.
- Implemented only bounded learning start/advance/abandon handlers. Research,
  action, assessment, and report command shapes explicitly refuse until their
  dedicated application use cases exist.
- Reconciled the capability register, project truth, roadmap, architecture,
  changelog, and governed logs.

## Safety boundary

- Posture remains `LOCAL_FIXTURE`; snapshot `live_target_available` is always false.
- No server, UI framework, process broker, network broker, worker, collector,
  external model, target, credential, or submission path was added or used.
- An application command result can record a domain mutation but is structurally
  unable to claim that tool execution occurred.
- No deployment, publication, push, merge, spending, secret use, or canonical
  ChaseOS mutation occurred.

## Verification

- Focused capability/application suite: `16 passed in 4.38s`.
- Full repository suite with pytest artifacts on the E: build volume:
  `555 passed in 18.05s`.
- The real local two-account slice assembled into research, hypothesis,
  evidence, report, and context records with zero source errors.
- A digest-tampered research workspace rendered `BLOCKED`, produced an integrity
  source error, and selected the repair action rather than presenting zero data.
- An exact, unexpired approval binding rendered ready while retaining the
  explicit requirement for a fresh gate decision at execution time.
- AST dependency guard confirmed that `greytheory_app` imports no socket,
  process, or network-client module.

## Remaining

- Operator selection of workbench visual direction 1, 2, or 3.
- Local-only transport and graphical application shell.
- Dedicated research, action-intent, human-assessment, and report-export handlers.
- Browser, keyboard, accessibility, desktop/390-pixel, packaging, and clean-user acceptance.
- General local fixture broker and every Milestone 9 passive-worker gate.
