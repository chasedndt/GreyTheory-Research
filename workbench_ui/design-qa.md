# GreyTheory Research Ledger design QA

## Evidence

- Source visual truth: `Docs/assets/research-ledger-overview.png`
- Implementation: `http://127.0.0.1:4174/`
- Desktop implementation: `E:\Visual QA\GreyTheory Visual QA\Current Reviews\2026-09-01-workbench-read-model-binding\greytheory-research-preview-overview-desktop.png`
- Mobile implementation: `E:\Visual QA\GreyTheory Visual QA\Current Reviews\2026-09-01-workbench-read-model-binding\greytheory-research-preview-mobile.png`
- Authenticated state: `E:\Visual QA\GreyTheory Visual QA\Current Reviews\2026-09-01-workbench-read-model-binding\greytheory-authenticated-overview-desktop.png`
- Combined comparison: `E:\Visual QA\GreyTheory Visual QA\Current Reviews\2026-09-01-workbench-read-model-binding\design-comparison-source-left-implementation-right.png`
- Source pixels: 1488 x 1058 JPEG, 1x reference capture.
- Implementation pixels: 1425 x 990 PNG at a requested 1440 x 1000 CSS viewport; browser content measured 1425 x 990, device scale 1.
- Mobile pixels: 375 x 812 PNG at a requested 390 x 844 CSS viewport; browser content measured 375 x 812, device scale 1.
- State compared: Overview, disconnected prototype exemplar. The new 40-pixel licence/research-preview banner is an intentional addition.

## Findings

- No actionable P0, P1 or P2 mismatch remains.
- Fonts and typography: the system sans and monospace hierarchy, weights, wrapping, and compact labels remain faithful. The licence banner uses the existing compact monospace language.
- Spacing and layout rhythm: the three-column ledger shell, navigation density, panel rows and evidence inspector remain aligned. The intentional banner reduces visible vertical content slightly but preserves scrolling and all persistent controls.
- Colors and visual tokens: navy surfaces, amber authority emphasis, green verification and muted secondary copy match the selected Research Ledger direction. The Apache-2.0 banner uses the existing amber boundary color rather than adding a competing palette.
- Image quality and asset fidelity: the repository-owned GreyTheory mark remains sharp and correctly scaled. No visible asset was replaced with CSS art or a placeholder.
- Copy and content: `Open source research preview`, `Apache-2.0`, `LOCAL_FIXTURE`, and `no live targets` are simultaneously visible. Prototype exemplar and authenticated local API sources are separately labelled.

## Interaction and responsive evidence

- Desktop and 390-pixel layouts rendered without hidden persistent controls or horizontal overflow.
- The connection dialog opened, accepted the numeric-loopback URL and in-memory session token, and changed the banner to `Local read model connected`.
- The authenticated Overview panel identified its source as `Authenticated local API` and displayed server-owned metrics.
- Cross-origin command submission remains absent from the browser UI and refused by transport tests.
- Navigation, dialogs, local searches, filters and inspectors remain available.
- Browser console warnings/errors: none.

## Comparison history

1. The first evidence pair used different visible panels and was rejected as an invalid comparison.
2. The implementation was recaptured on Overview at the same desktop state. The normalized side-by-side comparison found only the intentional licence banner and explicit source label additions.

## Follow-up polish

- P3: revisit the banner density when the installed application shell replaces the browser preview.
- P3: add a dedicated empty-state illustration only after the wider UI art direction is reviewed.

final result: passed
