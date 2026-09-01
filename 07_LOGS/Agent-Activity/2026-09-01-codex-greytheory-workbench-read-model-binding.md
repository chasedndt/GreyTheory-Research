# Codex activity - GreyTheory workbench read-model binding

**Date:** 2026-09-01

**Agent:** Codex / Axiom-Codex

**Posture:** `LOCAL_FIXTURE`

## Repo-truth delta

The selected Research Ledger now reads authenticated local application state
without granting the browser execution authority.

## Work performed

- Created an isolated E: worktree and project-specific Visual QA review.
- Implemented the Apache-2.0 research-preview banner and read-only API client.
- Added exact-origin snapshot CORS and CLI configuration.
- Browser-tested disconnected, dialog, authenticated, desktop, and mobile states.
- Updated capability-facing documentation, tests, logs, and history.

## Do not undo

- Do not persist or log the bearer token in browser storage.
- Do not generalize the allowed UI origin or expose cross-origin commands.
- Do not present fixture or ranked-hypothesis data as proof, probability, or a finding.
- Do not claim Ubuntu host acceptance or live research capability from this work.

## Verification

See `07_LOGS/Build-Logs/2026-09-01-greytheory-workbench-read-model-binding.md`.
