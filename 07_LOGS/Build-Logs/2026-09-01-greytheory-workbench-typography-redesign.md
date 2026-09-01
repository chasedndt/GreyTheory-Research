# GreyTheory workbench typography redesign

**Date:** 2026-09-01

**Posture:** `LOCAL_FIXTURE`

**Branch:** `codex/2026-09-01-workbench-read-model-binding`

## Repo-truth delta

The existing Research Preview is now a readable, responsive research instrument rather than a dense prototype shell. This is a presentation and usability improvement; it does not expand GreyTheory's execution authority.

## Changes

- Bundled Manrope and IBM Plex Mono, including their upstream licence notices.
- Rebuilt the display, body, metadata and control type scale.
- Improved the ledger, navigation, utility header, authority card, evidence inspector and dialog hierarchy.
- Corrected the 390-pixel hero, metadata and ledger-card reflow.
- Refreshed the repository README media and added a mobile preview asset.
- Produced before/after desktop evidence and current desktop/mobile QA captures.

## Verification

- `node node_modules\vite\bin\vite.js build --debug` - PASS; 4,572 modules transformed.
- `node scripts\prepare-sites-build.mjs` - PASS.
- `node --test tests\workbench-api.test.mjs` - PASS; 3 tests.
- `node --test tests\sites-worker.test.mjs` - PASS; 4 tests.
- In-app browser navigation sweep - PASS; all 13 destinations opened.
- Mobile evidence drawer - PASS.
- Desktop and 390-pixel visual comparison - PASS; no P0, P1 or P2 issue remains.

## Untouched boundaries

- No commands, target access, scanning, submission, disclosure, deployment or posture promotion was added.
- Ubuntu passive-worker acceptance remains a separate unverified track.
- The canonical vault and original C: checkout were not changed.

## Next safe action

Bind the Today and learning flows to their existing approved application handlers while keeping the preview read-only for research execution.

