# Design QA - Research Ledger

**Comparison target**

- Source visual truth: `E:\Visual QA\GreyTheory Visual QA\Current Reviews\2026-08-31-research-ledger-workbench\reference\research-ledger-selected.png`
- Implementation: `E:\Visual QA\GreyTheory Visual QA\Current Reviews\2026-08-31-research-ledger-workbench\screenshots\implementation-desktop-pass-2.png`
- Combined comparison: `E:\Visual QA\GreyTheory Visual QA\Current Reviews\2026-08-31-research-ledger-workbench\screenshots\comparison-desktop-pass-2.png`
- Responsive evidence: `E:\Visual QA\GreyTheory Visual QA\Current Reviews\2026-08-31-research-ledger-workbench\screenshots\implementation-mobile-390.png`
- Source pixels: 1487 x 1058.
- Desktop CSS viewport: 1488 x 1058 at device density 1; browser content capture: 1473 x 1047.
- Mobile CSS viewport: 390 x 844 at device density 1; browser content capture: 375 x 812.
- Normalization: the source and pass-2 desktop capture were placed in one comparison canvas and scaled proportionally to the same 700-pixel content height. No device frame or browser chrome was included.
- State: dark `LOCAL_FIXTURE` research ledger, selected IDOR/BOLA hypothesis, evidence inspector open, claim unproven.

**Findings**

- No actionable P0, P1, or P2 differences remain.
- Fonts and typography: the system sans stack, restrained weights, compact labels, and ledger hierarchy closely reproduce the source; no material wrapping or truncation drift remains.
- Spacing and layout rhythm: the three-column shell, top utility bar, dense ledger rows, inspector, and action rail preserve the source hierarchy and density. Desktop and 390-pixel layouts have no horizontal overflow.
- Colors and visual tokens: deep navy surfaces, low-contrast separators, grey text hierarchy, amber actions, and green/amber semantic states match the selected direction.
- Image quality and asset fidelity: the repository's supplied GreyTheory raster mark is used cleanly; interface icons use Phosphor rather than handmade SVG, CSS art, emoji, or text glyphs.
- Copy and content: visible authority, evidence, receipt, claim, provenance, local-only, unproven, and no-live-target wording matches the source intent and repository truth.

**Focused region comparison**

No separate crop was required: the original-resolution combined comparison keeps the header, brand mark, six ledger rows, statuses, evidence roles, provenance, and action controls readable together. Those dense regions were also inspected in the pass-2 original capture.

**Comparison history**

1. Pass 1 found one P2 desktop-header defect: the mobile navigation control remained visible at desktop width and forced utility controls into an implicit second row. The external SVG mark also rendered only its amber gate because `currentColor` does not inherit through an image document.
2. Fix: raised the desktop hide selector to `.icon-button.mobile-menu`, restored it only below 760 pixels, and replaced the external-currentColor mark with the supplied GreyTheory raster mark.
3. Pass 2 evidence: `comparison-desktop-pass-2.png`. Header tracks, mark, utilities, ledger, inspector, and action rail align with the selected direction. No actionable P0/P1/P2 issue remains.

**Primary interactions tested**

- Minimum-evidence review dialog opens and closes.
- Check-receipt dialog opens and closes.
- Reflection form accepts text, saves, marks the claim, and retains the note in the browser session.
- Mobile navigation drawer opens and closes.
- Mobile evidence inspector opens and closes.
- Desktop and mobile document widths remain within the viewport.
- Browser warning/error log: empty.

**Open Questions**

- API binding and persisted domain data are intentionally outside this visual prototype; the repository continues to classify the installed workbench as partial.

**Implementation Checklist**

- [x] Match selected desktop visual direction.
- [x] Use real repository brand asset and an icon library.
- [x] Make core ledger actions interactive.
- [x] Verify desktop and 390-pixel responsive behavior.
- [x] Verify browser console health.
- [x] Preserve `LOCAL_FIXTURE` and no-live-target boundaries.

**Follow-up Polish**

- None required for visual handoff. API-backed loading, empty/error states, keyboard automation, and installed-shell packaging belong to the next integration milestone.

final result: passed
