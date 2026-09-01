# Build log — GreyTheory Guided Mission Control

**Date:** 2026-09-01

**Branch:** `codex/2026-09-01-workbench-read-model-binding`

**Posture:** `LOCAL_FIXTURE`

## Repo-truth delta

Guided Mission Control is no longer an unselected design. The operator selected
Direction 1 and approved a hybrid composition using Direction 2's focused
lesson/skill map and Direction 3's case/evidence/competency views. The local
preview now completes one realistic learner journey. Installed Windows
acceptance, server-persisted graphical commands, governed model-backed coach
conversation, and Ubuntu service acceptance remain open.

## Changes

- rebuilt the application shell, navigation, typography, responsive grid, and
  safety footer;
- implemented Mission Control, Learn, Safe Lab, Cases, Evidence, Readiness, and
  Library views;
- retained the chronological Research Ledger as a working tab inside Cases;
- added an inspectable recommendation and explicit advisory-coach boundary;
- added `CASE-AGENT-AUTH-001` with deterministic positive and negative controls;
- added evidence-quality and six-dimensional competency representations;
- added automated authorization-case tests;
- replaced the README preview media and synchronized roadmap/state truth; and
- created central visual-QA evidence and a passing design comparison report.

## Verification

- `npm run test:ui` — 5 passed.
- `npm run test:sites` — 4 passed.
- `npm run build` — passed; 87 modules transformed and Sites outputs prepared.
- `python -m pytest tests/test_dashboard.py tests/test_learning_journey.py tests/test_workbench_app.py -q` — 62 passed.
- in-app browser — full learner journey passed; zero console errors.
- responsive browser checks — no horizontal overflow at 390, 768, 1024, or
  1440 CSS pixels.
- `workbench_ui/design-qa.md` — `final result: passed`.

## Untouched boundaries

No merge, deployment, publication, social post, live target activity, posture
change, Ubuntu restart, permission change, secret use, report submission, or
automatic mastery award occurred.

## Next safe action

Bind learner transitions to the existing application command contract, then run
full sequential-keyboard and clean-user Windows package acceptance before any
wider research-preview announcement.
