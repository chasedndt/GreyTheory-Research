# GreyTheory AI-Native Dashboard Direction

## Repo-truth delta

The thirteen-panel Research Ledger remains a useful local-fixture case view,
but it is no longer described as the accepted dashboard shell. A fresh visual
audit found desktop canvas overflow and 390-pixel clipping. The graphical
learner workbench, bounded coach, and learning visualisations remain designed,
not implemented.

## Work completed

- Captured Overview, Knowledge, and Ledger states at desktop and 390 pixels.
- Recorded the failure evidence under
  `E:\Visual QA\GreyTheory Visual QA\Current Reviews\2026-09-01-ai-native-dashboard-audit`.
- Produced three independent modern concepts: Guided Mission Control, Research
  Notebook + Skill Graph, and Adaptive Pathways + Case Canvas.
- Created and visually verified the editable Figma audit/direction board:
  <https://www.figma.com/design/1Agfk1l6iKvmNf8agWCqpB>.
- Added the learner-first information architecture, agent-security curriculum,
  recommendation contract, visualisation rules, responsive acceptance, and
  Windows-to-Ubuntu transition to the canonical repository documentation.

## Boundaries retained

- No production UI direction was selected on the operator's behalf.
- No browser command, target route, network collector, posture change, VPS
  deployment, publication, or live-target capability was added.
- The temporary Figma capture script was removed after capture; the application
  retains no external runtime dependency on Figma.
- `LOCAL_FIXTURE` remains the only workbench posture.

## Verification

- Current visual states were inspected from real browser screenshots.
- The Figma direction board was inspected through a rendered 1400 x 1514 image
  after fixing title and information-architecture wrapping.
- Documentation links and Mermaid fence counts were checked locally.
- `npm run test:ui`: 3 passed.
- `npm run test:sites`: 4 passed.
- `python -m pytest -q tests/test_dashboard.py tests/test_learning_journey.py tests/test_workbench_app.py`: 62 passed.
- `npm run build`: passed after stopping the task-owned preview that held the
  Windows Vite transform/cache path; the preview was restarted on port 4174.
- The restored page loaded with no browser console warnings/errors and no Figma
  capture script.

## Next safe action

The operator selects Direction 1, 2, or 3. The recommended foundation is
Direction 1, Guided Mission Control, with the focused learning note from
Direction 2 and case canvas from Direction 3 considered only after selection.
