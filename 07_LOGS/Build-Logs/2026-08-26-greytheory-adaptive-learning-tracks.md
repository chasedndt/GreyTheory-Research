# GreyTheory transparent adaptive learning tracks

**Date:** 2026-08-26

**Branch:** `codex/2026-08-24-greytheory-workbench-foundation`

**Posture:** `LOCAL_FIXTURE`

## Repository-truth delta

Before this slice, GreyTheory had deterministic recommendations and persisted
five-stage journeys, but adaptive review, assisted learning, and transfer
orchestration were correctly documented as unbuilt.

After this slice, all three exist in the shared learning domain, CLI, private
persistence, workbench application commands, and snapshot read model. The
graphical Learn surface and broader curricula remain unbuilt.

## Changes

- Added the inspectable `adaptive-evidence-review-v1` policy using only earlier
  credited human history for the same card and dimension.
- Persisted policy reference and rationale on mastery assessments while keeping
  old records readable and explicit operator date overrides available.
- Added `standard`, `assisted`, and `transfer` journey tracks.
- Added visible assisted guidance and refused independent/transferable mastery
  claims from assisted journeys.
- Required transfer journeys to have independent test/prove foundations and a
  distinct local context cited in proof and final assessment.
- Added CLI and workbench application integration, including snapshot track
  truth and adaptive review receipts.
- Added ADR-0017 and reconciled capability, project, roadmap, architecture, and
  index truth.

## Untouched boundaries

- No graphical workbench, graphical Learn surface, Windows package, shortcut,
  or clean-user installation proof was created.
- No fixture, model, or journey awards mastery; final credit still requires a
  separately persisted human assessment.
- No target, network worker, VPS, deployment, external programme, or secret was
  contacted or changed.
- No canonical ChaseOS file was changed.
- `PASSIVE_HTTP` remains unavailable and posture remains `LOCAL_FIXTURE`.

## Verification

```text
python -m pytest -q tests\test_capabilities.py tests\test_learning.py tests\test_learning_journey.py tests\test_workbench_app.py
50 passed in 92.73s (0:01:32)
```

```text
python -m pytest -q
651 passed in 209.89s (0:03:29)
```

```text
git diff --check
PASS (line-ending conversion warnings only)
```

## Verification status

**VERIFIED for the offline adaptive-review and bounded learning-track
contracts.** This is not verification of a graphical UI, broader curriculum,
installed Windows application, passive worker, VPS, or live research.

## Remaining unknowns

- which of the three prepared visual directions the operator selects;
- keyboard, accessibility, desktop, and 390-pixel behavior of the future UI;
- packaging and clean-user Windows acceptance;
- broader curriculum packs beyond the current 12 cards.

## Next safe action

Select visual direction 1, 2, or 3, then bind its Today/Learn/Research journey
to the verified numeric-loopback snapshot and command contract. In parallel,
passive worker work may continue only in the isolated local Ubuntu acceptance
environment without enabling `PASSIVE_HTTP`.
