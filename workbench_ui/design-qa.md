# Guided Mission Control design QA

## Whole-application keyboard acceptance - 2026-09-04

The current desktop and 390-pixel shell has been inspected across all thirteen
panels and exercised from the browser's first Tab stop.

- Desktop now hides the mobile-only menu trigger while preserving the complete
  sidebar and themed scroll rail.
- The skip link is visibly focused first and transfers focus to the named main
  workspace.
- Every navigation destination is reachable from first entry and exposes the
  expected focus ring without clipping or layout drift.
- Case canvas/ledger tabs respond to ArrowLeft, ArrowRight, Home, and End with
  matching selection, focus, and labelled panel state.
- The connection modal and mobile drawer retain/restore focus; the closed
  drawer is inert and selecting Learn hands focus to the Learn workspace.
- The local Review packet preview is legible and keeps export, contact, review,
  and approval explicitly absent.

Evidence root:
`E:\Visual QA\GreyTheory Visual QA\Current Reviews\2026-09-04-whole-app-keyboard`.

Machine record:
`E:\Projects\GreyTheory\acceptance\workbench-keyboard-20260904-160220-20968\acceptance.json`.

**final result: browser keyboard and current rendered-state pass; platform
screen-reader/assistive-technology checks remain open**

## Navigation scrollbar and keyboard follow-up - 2026-09-02

The mobile navigation rail now uses the accepted Guided Mission Control navy,
muted-blue, and amber vocabulary instead of bright native scrollbar chrome.
The scrollbar remains visible, gains a stable gutter, and does not cover labels
or change the drawer's information architecture.

- 390-pixel closed and open states have no horizontal document overflow.
- The scrollable drawer reports a thin scrollbar, navy track, muted-blue thumb,
  and stable gutter at runtime.
- Reverse wrapping from Close reaches Settings; forward wrapping returns to
  Close; Escape closes the drawer and restores Open navigation.
- Desktop retains all thirteen navigation journeys and the accepted
  mission-first hierarchy.
- Runtime inspection found the skip link first in the visible focusable DOM
  order.
- The in-app browser still cannot synthesize the first Tab from an unfocused
  document body, so first-entry keyboard acceptance remains open.

Evidence root:
`E:\Visual QA\GreyTheory Visual QA\Current Reviews\2026-09-02-navigation-scrollbar-and-keyboard`.

Accepted captures: `01-mobile-closed.png`,
`02-mobile-navigation-open.png`, and `03-desktop-navigation.png`.

Figma board update was attempted only after the screenshots were inspected, but
the authenticated Starter plan had reached its MCP call limit. No Figma nodes
were created or changed in this pass.

**final result: scrollbar polish and bounded keyboard behavior passed; whole-app first-entry remains open**

## Keyboard and packaged-workbench follow-up - 2026-09-02

The in-app browser exposed unnamed icon-only navigation at the 1024-pixel
compact breakpoint and an off-screen mobile drawer that remained interactive
while closed. Both P1 accessibility defects are fixed.

- All thirteen compact navigation buttons retain explicit accessible names.
- The closed 390-pixel drawer is inert and `aria-hidden`; opening it focuses the
  Close control and exposes a labelled modal navigation drawer.
- Shift+Tab from the first control wraps to Settings, Tab from Settings wraps to
  Close, Escape closes the drawer and restores Open navigation, and selecting
  Learn closes the drawer and focuses the named Learn workspace.
- The connection dialog separately passed reverse/forward focus wrapping and
  Escape restoration to the safety control.
- The production build was bundled into a wheel and accepted from an empty
  Windows install prefix. This is functional acceptance, not new promotional
  media and not separate-user installer proof.

Evidence root:
`E:\Visual QA\GreyTheory Visual QA\Current Reviews\2026-09-02-keyboard-and-windows-package`.

Accepted interaction capture: `02-mobile-navigation-open.png`.

**final result: P1 defects fixed; focused keyboard and isolated-package checks passed**

## Release-media refresh - 2026-09-02

The current Mission Control, skill trajectory, topic-owned learning path,
beginner-to-transfer roadmap, and public-intelligence screen were recaptured in
the in-app browser and inspected at original resolution. Accepted evidence is
under `E:\Visual QA\GreyTheory Visual QA\Current Reviews\2026-09-02-release-media-refresh`.

- All five captures show the intended local preview state without blank,
  loading, error, or document-level horizontal-overflow failure.
- Prompt-injection selection replaces the complete topic body and checkpoint.
- Trajectory preview state remains visibly distinct from earned mastery.
- Intelligence sources remain contract-only; no request was sent.
- The browser error console was empty.
- Sequential keyboard, clean-user Windows, Ubuntu service and live-programme
  acceptance remain open and are not implied by the media.

final result: passed

**Source visual truth:** `E:\Visual QA\GreyTheory Visual QA\Current Reviews\2026-09-01-ai-native-dashboard-audit\06-direction-1-guided-mission-control.png`

**Implementation evidence:** `E:\Visual QA\GreyTheory Visual QA\Current Reviews\2026-09-01-guided-mission-control-implementation\01-mission-control-desktop.png`

**Comparison:** source 1487 x 1058 pixels; implementation 1440 x 1024 pixels at a 1440 x 1024 CSS viewport and device pixel ratio 1. The 47-pixel width difference does not change the desktop breakpoint or major-region composition. State: initial Mission Control with `LOCAL_FIXTURE`, no live targets, and advisory coach visible.

## Findings

No actionable P0, P1, or P2 differences remain.

- Typography: locally bundled Manrope and IBM Plex Mono reproduce the source's clear display/body/technical hierarchy without clipped headings at desktop or 390 pixels.
- Spacing and layout: the shell retains the source's left navigation, mission-first center, bounded coach, learner loop, trajectory, and fixed safety footer. The implemented mission is intentionally Agent Tool Authorization rather than the mock's IDOR example.
- Colors and tokens: navy surfaces, low-contrast rules, amber action state, green evidence state, blue next state, and violet judgment state remain semantically consistent.
- Image and icon quality: the supplied GreyTheory mark and Phosphor icon family are used throughout. No placeholder image, emoji, handcrafted SVG, or decorative CSS illustration replaces a source asset.
- Copy and content: recommendations explain why they appear, the coach states its limit, the environment is explicit, and practice is not described as mastery.
- Responsiveness: document overflow is absent at 390, 768, 1024, and 1440 CSS pixels. Mobile uses a working navigation drawer and puts the current lesson first.
- Interaction: navigation, recommendation, lesson checklist, authority review, theory, paired simulation, receipt, reflection, evidence selection, library filtering, and readiness assessment were exercised in the in-app browser. Console error count: zero.

## Comparison history

1. P2: at 390 pixels the topic carousel initially showed the introductory card instead of the selected current topic and exposed a native scrollbar. Fixed by ordering the selected card first at the mobile breakpoint and hiding only the scrollbar chrome; post-fix capture: `08-learn-mobile.png`.
2. P2: the desktop brand and release badge repeated “Research Preview.” Fixed by reserving the label for the release badge; post-fix capture: `01-mission-control-desktop.png`.

## Focused evidence

- Desktop lesson: `02-learn-desktop.png`
- Paired controls: `03-safe-lab-controls-desktop.png`
- Allow/deny decision: `04-safe-lab-evidence-desktop.png`
- Evidence receipt: `05-evidence-desktop.png`
- Human readiness check: `06-readiness-desktop.png`
- Mobile Mission Control: `07-mission-control-mobile.png`
- Mobile focused lesson: `08-learn-mobile.png`
- Retained Research Ledger: `09-research-ledger-desktop.png`

Full-view comparison was sufficient for the shell; focused captures were used for typography, controls, evidence, and assessment states. Full sequential-keyboard traversal and installed clean-user Windows acceptance remain product acceptance work, not a visual mismatch in this comparison.

**Follow-up polish:** preserve the current density while adding the server-persisted learner command path; do not turn the home screen into a record table.

**final result: passed**

## 2026-09-02 learning-path interaction follow-up

The live in-app audit reproduced two functional P2 issues: Skill Trajectory
used passive marks with no lesson detail, and changing topics updated only the
Focused Note heading while leaving the authorization body in place. Both are
fixed.

- All 24 trajectory nodes are keyboard-focusable buttons with accessible lesson
  names, hover/focus detail, selection, and honest preview fill.
- `View learning path` now sits in a padded footer below a selected-lesson
  summary instead of touching the trajectory grid.
- Prompt Injection, Tool Authorization, and MCP Abuse now change the entire
  lesson body, principles, lenses, checkpoints, roadmap, and official sources.
- Navigation now exposes all thirteen journeys, including Programmes,
  Hypotheses, Intelligence, Reports, and Settings.
- Public-intelligence and bug-bounty panels expose truthful connection state;
  no network request or account connection was made.
- Browser geometry at the default viewport and 390 CSS pixels reported no
  document overflow; the mobile drawer opened, exposed all thirteen panels,
  navigated to Learn, and closed after selection.

Evidence root:
`E:\Visual QA\GreyTheory Visual QA\Current Reviews\2026-09-02-learning-path-interactions`.
The current in-app browser capture path rasterised at device-pixel ratio 2 into
a CSS-pixel-sized bitmap, so the saved full-page PNGs are useful state evidence
but are not approved promotional media. Use the earlier DPR-1 campaign captures
until a new DPR-1 media pass is recorded.

**final result: functional pass; promotional recapture required**
# Guided mission and programme readiness - 2026-09-02

The accepted Guided Mission Control design now includes an exact 30-minute
stage selector, topic-specific practice questions, an honest lab unlock gate,
and an offline programme-to-local-case readiness explainer. Desktop interaction
and 390-pixel geometry passed. The tall full-page mobile capture remains subject
to the in-app capture duplication defect, so the two current viewport captures
are the visual acceptance source.

Evidence:
`E:\Visual QA\GreyTheory Visual QA\Current Reviews\2026-09-02-guided-mission-and-programme-readiness`.

**Final result: guided mission and programme readiness interaction passed;
live programme and Ubuntu worker acceptance remain open.**
