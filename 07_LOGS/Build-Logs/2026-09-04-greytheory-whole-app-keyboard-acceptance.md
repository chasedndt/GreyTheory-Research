# GreyTheory whole-application keyboard acceptance - build log

**Date:** 2026-09-04

**Agent:** Codex

**Branch:** `codex/2026-09-01-workbench-read-model-binding`

**Posture:** `LOCAL_FIXTURE`

## Repo-truth delta

The workbench previously had focused route, modal, and mobile-drawer checks but
no accepted browser run beginning with Tab from the unfocused document body.
The Cases control also declared ARIA tabs without implementing arrow movement,
the mobile menu trigger leaked onto desktop through CSS cascade order, and two
visible actions were non-functional placeholders.

This increment accepts the browser keyboard gate. It does not claim platform
screen-reader output, external target authority, export, human approval, or a
completed Windows release.

## Implementation

- Added an owned-preview Playwright harness and PowerShell wrapper with an
  ephemeral numeric-loopback origin, machine-readable evidence, current-run
  screenshots, and exact owned-process cleanup.
- Implemented roving Cases tabs with ArrowLeft, ArrowRight, Home, End,
  `aria-controls`, labelled tab panels, and focus-visible selection.
- Hid the mobile navigation trigger at desktop specificity and restored it only
  below the 760-pixel breakpoint.
- Made Evidence export truly disabled, labelled the learner-profile control,
  announced assessment results, and implemented a local-only review packet
  checklist after a correct independent check.

## Visual QA

All thirteen panel captures plus first-entry, skip-link, workspace-focus,
Cases-tab, modal, Readiness-packet, mobile-entry, drawer, and mobile-Learn states
were inspected. No clipping, horizontal overflow, broken hierarchy, incorrect
font, unintended desktop hamburger, or false capability state was observed.

Evidence:
`E:\Visual QA\GreyTheory Visual QA\Current Reviews\2026-09-04-whole-app-keyboard`.

## Verification

```text
acceptance/run-workbench-keyboard.ps1
accepted=true; 13 routes; first Tab=Skip to workspace; cases arrow/Home/End=true;
modal/mobile focus=true; positive_tabindex=0; console_errors=0; targetContacted=false

npm run test:ui
29 passed

npm run test:sites
4 passed

npm run build
90 modules transformed; production client and Sites artifacts emitted

python -m pytest -q
716 passed
```

Accepted record:
`E:\Projects\GreyTheory\acceptance\workbench-keyboard-20260904-160220-20968\acceptance.json`.

## Untouched boundaries

- No target, programme account, connector, or external intelligence service was
  contacted.
- The packet is a checklist preview, not an export, review, approval, mastery
  award, or submission.
- Separate-account Windows, signing, uninstall, platform assistive technology,
  governed coach, Session and Role Transitions, VM/reboot, and live posture
  gates remain open.

## Next safe action

Promote Session and Role Transitions using the accepted Case Pack contract and
repeat this browser gate against its complete local journey.
