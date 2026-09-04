# GreyTheory navigation scrollbar and keyboard - build log

**Date:** 2026-09-02

**Agent:** Codex

**Branch:** `codex/2026-09-01-workbench-read-model-binding`

**Posture:** `LOCAL_FIXTURE`

## Repo-truth delta

The drawer previously exposed bright native scrollbar chrome that did not match
Guided Mission Control. It now uses a visible thin rail, stable gutter, navy
track, muted-blue thumb, and amber active state. Desktop and 390-pixel states
retain the accepted structure and have no document-level horizontal overflow.

Runtime checks reconfirmed reverse and forward drawer focus wrapping, Escape
close, and trigger restoration. A visible-focusable inventory places the skip
link first, but the in-app harness cannot originate the first Tab from an
unfocused document body, so the whole-app first-entry gate remains open.

## Verification

```text
npm --prefix workbench_ui run test:ui
19 passed

npm --prefix workbench_ui run build
production build passed

Browser QA
390 x 844 closed/open: no horizontal overflow
drawer scrollbar: thin; stable gutter; rgb(58, 83, 107) on rgb(7, 19, 33)
drawer focus: Close -> Shift+Tab Settings -> Tab Close -> Escape Open navigation
1440 x 1000 desktop: no horizontal overflow; thirteen journeys visible
```

Evidence:
`E:\Visual QA\GreyTheory Visual QA\Current Reviews\2026-09-02-navigation-scrollbar-and-keyboard`.

The inspected evidence could not be added to Figma because the authenticated
Starter plan had reached its MCP call limit. The failed call was atomic; no
Figma nodes were created.

## Untouched boundaries

No target request, provider connector, credential, Ubuntu worker, VPS,
submission path, deployment, or posture transition was enabled. The dirty
primary GreyTheory and ChaseInTech workspaces remain untouched.

## Next safe action

Complete first-entry whole-app keyboard acceptance in a harness that can issue
the initial Tab, then run the accepted wheel through a separate Windows user,
shortcut or installer, persisted restart, upgrade, and recovery path.
