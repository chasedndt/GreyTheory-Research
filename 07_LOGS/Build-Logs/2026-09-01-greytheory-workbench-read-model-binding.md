# GreyTheory workbench read-model binding

**Date:** 2026-09-01

**Posture:** `LOCAL_FIXTURE`

**Branch:** `codex/2026-09-01-workbench-read-model-binding`

## Repo-truth delta

The Research Ledger is now an Apache-2.0 research preview that can read an
authenticated server-owned snapshot from GreyTheory's exact numeric-loopback
transport. The browser still cannot issue commands or authorize research.

## Changes

- Added an explicit Apache-2.0 research-preview banner and connection state.
- Added a fail-closed, read-only browser client for `GET /api/v1/snapshot`.
- Kept the bearer token in memory and cleared it after connection.
- Added opt-in exact-origin CORS for the snapshot read only; cross-origin
  command requests remain refused.
- Added CLI support for the exact UI origin and mapped server records into the
  existing Overview, Hypotheses, Knowledge, Artifacts, Claims, Governance, and
  Workspaces panels.
- Reconciled README, project definition, roadmap, workbench architecture, and
  visual QA evidence.

## Verification

- `node --test tests/workbench-api.test.mjs` - PASS; 3 tests.
- `npm run test:sites` - PASS; 4 tests.
- `python -m pytest -q tests/test_local_workbench_transport.py tests/test_workbench_app.py` - PASS; 24 tests.
- `npm run build` - PASS.
- Browser connection against the live local Python service - PASS; the
  Overview provenance changed to `Authenticated local API`.
- Desktop and 390-pixel visual QA - PASS; no UI warnings or errors.
- GitHub Linux authority-plane proof - repaired to refresh only its reserved
  `.test` CI fixture at runtime, so the seven-day stale-contract guard remains
  enforced without making the workflow expire by calendar date.

## Untouched boundaries

- No browser command transport, live target, scan, submission, disclosure,
  deployment, or posture promotion was added.
- Ubuntu passive-worker acceptance remains separate and unverified here.
- The original C: checkout and unrelated work remained untouched.

## Next safe action

Add typed local-fixture commands behind explicit approvals, beginning with the
Today queue and learning/reflection flows; keep the passive Ubuntu worker as a
separate acceptance track.
