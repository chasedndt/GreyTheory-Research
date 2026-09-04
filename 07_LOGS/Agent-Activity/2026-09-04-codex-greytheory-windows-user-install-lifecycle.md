# Codex activity — GreyTheory Windows current-user install lifecycle

## Scope

Resume the existing GreyTheory goal by turning the packaged workbench into a
recoverable current-user application path before the Ubuntu worker phase.

## Actions

- Added a non-admin Windows installer with separate runtime and private-data
  roots, an integrity-linked install manifest, and a Start Menu-shaped shortcut.
- Kept browser launch outside the trusted Python package after its import guard
  correctly rejected an initial in-package browser helper.
- Added a health-gated launcher and a bounded acceptance harness with exact
  launcher/workbench child ownership.
- Ran a real same-origin learning command, then verified the saved journey after
  restart, same-wheel upgrade, and runtime replacement/recovery.
- Updated capability truth, roadmap, launch-transition documentation, changelog,
  build log, daily record, and indexes.

## Guardrails retained

`LOCAL_FIXTURE` remains the ceiling. The acceptance uses isolated E: roots and
explicitly records that a separate user and signed installer were not accepted.
No live target, external programme, model provider, Ubuntu worker, VPS,
submission, publication, or posture change was activated.

## Handoff

The existing Ubuntu full-service no-route harness subsequently passed in the
same goal continuation. Independently, complete one operator-observed initial-
Tab sweep and repeat the installer lifecycle from a genuinely separate Windows
account before closing the Windows host gate.
