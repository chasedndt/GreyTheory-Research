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

## Panel completion increment

The same branch now resolves every visible navigation entry to a functional
local-fixture prototype panel. Overview, Hypotheses, Experiments, Receipts,
Claims, Reflections, Knowledge, Artifacts, Templates, Governance, Workspaces,
and Settings support search, status filtering, empty-state recovery, record
inspection, responsive context, and an explicit non-persisting action boundary.
The original Ledger flows remain intact.

Additional verification:

- live browser matrix across all twelve non-Ledger panels - PASS for identity,
  search, empty-state recovery, inspection, and action-boundary dialog;
- Ledger evidence, receipt, and reflection regression - PASS;
- Governance at 390 x 844 plus mobile navigation/context drawer - PASS;
- desktop/mobile horizontal overflow and browser warning/error checks - PASS;
- refreshed `npm run build` - PASS; 4,571 modules transformed;
- `npm run test:sites` - PASS; 4 tests;
- targeted GreyTheory application/transport/capability suite - PASS; 30 tests.

The README now carries a curated synthetic Overview screenshot copied from the
project-specific Visual QA review. No raw evidence or private workspace data was
placed in Git.
