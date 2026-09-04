# GreyTheory Case Pack 02 design QA

Date: 2026-09-04

## Comparison target

- Preserved source visual truth: `E:/Visual QA/GreyTheory Visual QA/Current Reviews/2026-09-04-api-object-ownership-case-pack/00-source-guided-mission-control-20260902.png`
- Desktop source: 1265 x 712 pixels, 1265 x 712 CSS pixels, device scale factor 1
- Desktop implementation: `E:/Visual QA/GreyTheory Visual QA/Current Reviews/2026-09-04-api-object-ownership-case-pack/10-mission-agent-desktop-final.png`
- Desktop comparison: `E:/Visual QA/GreyTheory Visual QA/Current Reviews/2026-09-04-api-object-ownership-case-pack/11-source-implementation-comparison-final.png`
- Mobile source: `E:/Visual QA/GreyTheory Visual QA/Current Reviews/2026-09-02-guided-mission-and-programme-readiness/06-learn-mobile-viewport.png`
- Mobile implementation: `E:/Visual QA/GreyTheory Visual QA/Current Reviews/2026-09-04-api-object-ownership-case-pack/07-learn-object-mobile.png`
- Mobile comparison: `E:/Visual QA/GreyTheory Visual QA/Current Reviews/2026-09-04-api-object-ownership-case-pack/12-mobile-learning-comparison-final.png`
- Mobile source and implementation: 390 x 844 pixels, 390 x 844 CSS pixels, device scale factor 1
- State: dark theme, preview mode, `LOCAL_FIXTURE`, no live targets
- Repository release media: `Docs/assets/api-object-ownership-mission-current.png`, `Docs/assets/api-object-ownership-learning-current.png`, and `Docs/assets/api-object-ownership-lab-current.png`

## Findings

- No actionable P0, P1, or P2 differences remain.
- The selectable mission strip intentionally adds one new row above the accepted mission card. It preserves the shell's navy/amber palette, typography, panel geometry, learner-first hierarchy, advisory coach, and explicit authority boundary.
- Case Pack 02 keeps the same visual grammar across Learn, Safe Lab, Cases, Evidence, Reports, and Readiness. Its additional third control remains legible without widening the page.

## Required fidelity surfaces

- Fonts and typography: the bundled Manrope and IBM Plex Mono families, weights, line heights, uppercase eyebrows, and information hierarchy match the accepted shell. Long object-authorization copy wraps without clipping at desktop and 390 pixels.
- Spacing and layout rhythm: shell rails, panel gaps, radii, borders, sticky context, and card density remain consistent. The new selector is compact on desktop and becomes a two-column mission grid on mobile.
- Colors and visual tokens: existing navy, amber, green, blue, muted foreground, and semantic state tokens are reused. No new off-palette color was introduced.
- Image quality and asset fidelity: the supplied GreyTheory mark remains unchanged and sharp. Standard interface icons continue to use the existing Phosphor icon package; no placeholder or handcrafted image substitute was added.
- Copy and content: every visible Case Pack 02 surface distinguishes a synthetic teaching failure from a live vulnerability, separates identifier shape from authorization evidence, and retains human review and no-live-target language.

## Full-view comparison evidence

- Desktop source and implementation were combined into `11-source-implementation-comparison-final.png` at the same 1265 x 712 viewport. The only material composition change is the intentional mission selector; the accepted shell proportions and visual hierarchy remain coherent.
- Mobile source and implementation were combined into `12-mobile-learning-comparison-final.png` at the same 390 x 844 viewport. The longer Case Pack 02 heading and 50-minute route remain readable without document-level horizontal overflow.

## Focused region evidence

- `03-learn-object-ownership-desktop.png`: complete 50-minute route, four learning topics, focused note, traditional/AI lenses, practice checks, lesson roadmap, and official sources.
- `04-lab-object-results-desktop.png`: own-object allow, deliberately vulnerable cross-owner teaching path, and safe cross-owner denial, each with a visible decision and `external action: none`.
- `08-object-assessment-desktop.png`: object-authorization competency view and independent evidence-bound reasoning check.
- `06-mission-object-mobile-final.png`: all three mission choices visible, Case Pack 02 selected, and no document-level horizontal clipping.

## Interaction and browser checks

- Selected Case Pack 02 and confirmed every relevant panel followed it.
- Started the preview mission; answered both scenario checks correctly; confirmed three learner explanations; and verified that Safe Lab unlocked.
- Advanced through authority, theory, and the three-control simulation; inspected all deterministic decisions.
- Opened Cases and its Research Ledger, Hypotheses, Evidence, Reports and its Limitations section, and Readiness; completed the correct independent assessment response.
- Opened the 390-pixel navigation drawer, verified focus moved to Close navigation, closed it with Escape, and verified focus returned to Open navigation.
- Browser console warnings/errors: none.
- Document-level horizontal overflow at 1265 and 390 pixels: none.

## Comparison history

1. Initial mobile capture showed the mission-selector introduction consuming the first horizontal snap position and hiding the ready choices. Severity: P2. Fix: replaced the mobile rail with a two-column grid and a full-width queued row. Post-fix evidence: `06-mission-object-mobile-final.png`; all choices are visible and selector scroll width equals client width.
2. Initial desktop capture truncated the three compact selector labels. Severity: P2. Fix: shortened selector-only labels while retaining full Case Pack titles in the mission card and every destination panel. Post-fix evidence: `10-mission-agent-desktop-final.png`; all three labels fit at 1265 pixels.

## Follow-up polish

- P3: replace the static session greeting and demonstration counts with authenticated local learner state when that read model exists.

## Implementation checklist

- [x] Preserve the selected Guided Mission Control shell.
- [x] Keep both ready missions discoverable and the queued mission disabled.
- [x] Bind lesson, lab, evidence, report, and assessment copy to the selected pack.
- [x] Pass desktop and 390-pixel rendered checks.
- [x] Keep live-target posture unavailable.

final result: passed
