# GreyTheory Research Preview design QA

## Evidence

- Live implementation: `http://127.0.0.1:4174/`
- Baseline desktop: `E:\Visual QA\GreyTheory Visual QA\Current Reviews\2026-09-01-workbench-typography-redesign\01-current-desktop.png`
- Redesigned desktop: `E:\Visual QA\GreyTheory Visual QA\Current Reviews\2026-09-01-workbench-typography-redesign\03-redesigned-desktop.png`
- Redesigned mobile: `E:\Visual QA\GreyTheory Visual QA\Current Reviews\2026-09-01-workbench-typography-redesign\04-redesigned-mobile.png`
- Same-viewport comparison: `E:\Visual QA\GreyTheory Visual QA\Current Reviews\2026-09-01-workbench-typography-redesign\05-before-after-desktop.png`
- Repository preview media: `Docs/assets/research-ledger-overview.png` and `Docs/assets/research-ledger-mobile.png`
- Desktop viewport: 1440 x 1000 CSS pixels.
- Mobile viewport: 390 x 844 CSS pixels; document width 375 pixels with no horizontal overflow.

## Findings and corrections

- Typography: replaced the inconsistent system-only stack with locally bundled Manrope and IBM Plex Mono. Display, body, metadata and control styles now have distinct weights, tracking and line heights.
- Hierarchy: strengthened the product header, case title, entry titles and evidence headings while reserving monospace for provenance, identifiers and timestamps.
- Density: increased ledger row rhythm, authority-card padding, touch targets and inspector spacing without changing the approved three-column research-ledger direction.
- Secondary surfaces: raised inspector body size and contrast so the evidence roles and provenance remain readable supporting material.
- Mobile: restored a full-width hero, stable two-column metadata grid, deliberate ledger cards and a readable authority surface. The licence banner no longer competes with the primary title.
- Portability: fonts are repository-owned build assets, so Windows, Ubuntu and VPS-hosted builds do not depend on a third-party font request.

## Interaction and responsive evidence

- All 13 navigation destinations were opened in the in-app browser: Overview, Hypotheses, Experiments, Receipts, Claims, Reflections, Knowledge, Artifacts, Templates, Governance, Workspaces, Settings and Ledger.
- The mobile evidence drawer opened and exposed the complete claim-evidence role model and provenance panel.
- The ledger remained the selected local-fixture state after the navigation sweep.
- Persistent controls remained available and the mobile document produced no horizontal overflow.
- No browser command transport, live target or posture promotion was introduced.

## Automated verification

- Vite production bundle: PASS; 4,572 modules transformed and all three local font files emitted.
- Sites build preparation: PASS.
- Workbench API tests: PASS; 3/3.
- Sites worker tests: PASS; 4/4.

## Residual polish

- P3: the floating mobile evidence control can become a bottom navigation affordance in the later full application-shell redesign.
- P3: the utility header can be simplified further when workspace and researcher identity become server-owned product states.

final result: passed
