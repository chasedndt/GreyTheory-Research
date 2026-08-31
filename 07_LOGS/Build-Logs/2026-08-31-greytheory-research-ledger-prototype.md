# GreyTheory Research Ledger prototype

**Date:** 2026-08-31

**Posture:** `LOCAL_FIXTURE`

**Branch:** `codex/2026-08-31-greytheory-research-ledger-ui`

## Repo-truth delta

Visual direction 1 is no longer only a mock: it is a responsive interactive
React prototype with browser evidence. It is not yet bound to GreyTheory's
authenticated numeric-loopback API, installed as a desktop application, or
authorised for any live target.

## Changes

- Added `workbench_ui/`, a Product Design prototype preserving the selected
  Research Ledger's chronological evidence model and three-column desktop shell.
- Implemented minimum-evidence, receipt, reflection, navigation, and evidence
  drawer interactions using realistic synthetic `LOCAL_FIXTURE` data.
- Added responsive desktop and 390-pixel behavior, repository brand media,
  Phosphor icons, and explicit no-live-target language.
- Reconciled README, project definition, workbench architecture, and roadmap
  without promoting the installed workbench or Ubuntu service.

## Verification

- `npm run build` - PASS; 4,570 modules transformed and Sites output prepared.
- `npm run test:sites` - PASS; 4 tests.
- `python -m pytest -q tests/test_workbench_app.py tests/test_local_workbench_transport.py tests/test_capabilities.py` - PASS; 30 tests.
- In-app browser at desktop and 390-pixel viewports - PASS; no horizontal
  overflow, no warning/error logs, and all five primary interactions verified.
- Product Design comparison - PASS; see `workbench_ui/design-qa.md` and the
  project-specific Visual QA review.

## Untouched boundaries

- No core, broker, worker, permission, target, or posture behavior changed.
- No deployment, publication, push, merge, signing, secret use, or live network
  research occurred.
- The canonical ChaseOS vault path exposed for this run did not contain the
  expected canonical documents or indexes, so no vault writeback was invented.

## Next safe action

Bind the verified Research Ledger shell to read-only authenticated application
snapshots first, then add typed local-fixture commands behind the existing
application boundary. Keep Windows as the pilot host; Ubuntu service acceptance
remains a separate blocked infrastructure proof.
