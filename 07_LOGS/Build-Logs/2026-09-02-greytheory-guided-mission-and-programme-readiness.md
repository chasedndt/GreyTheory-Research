# GreyTheory guided mission and programme readiness

## Repo-truth delta

The ready Agent Tool Authorization Case Pack is now an exact 30-minute guided
mission with selectable time-boxed stages and two scored practice scenarios per
topic. The Programmes journey now demonstrates the governed transition from a
saved public policy snapshot to a synthetic local case. The operating posture
remains `LOCAL_FIXTURE`; no source refresh, account connection, target request,
or posture change was added.

## Built

- Learn 8, Practise 10, Prove 5, Reflect 4, and Assess 3 minute mission stages.
- Topic-specific scenario questions with immediate reasoning feedback.
- A practice gate requiring both correct answers and three learner-owned
  explanations before the Safe Lab unlocks.
- A four-stage programme readiness explainer for saved HackerOne, Bugcrowd, and
  direct-policy bundles, including preserved YNAB ambiguity and an unavailable
  live-posture state.
- Responsive, keyboard-focusable controls using the accepted Guided Mission
  Control visual language.

## Verification

- `python -m pytest -q` - 682 passed in 107.04 seconds.
- `python -m pytest tests/test_case_pack_workbench.py tests/test_learning.py -q` - 12 passed.
- `npm test` - 22 UI and 4 Sites tests passed.
- `npm run build` - passed; the Sites bundle was prepared.
- In-app desktop interaction - selectable mission stages, two-answer practice
  gate, three-explanation threshold, and enabled Safe Lab CTA passed.
- In-app programme interaction - synthetic-case explanation, YNAB ambiguity,
  unavailable network, and dark live-posture states passed.
- Mobile geometry - 390-pixel Learn and Programmes views reported no document
  overflow; current viewport captures passed visual inspection.

## Visual QA

`E:\Visual QA\GreyTheory Visual QA\Current Reviews\2026-09-02-guided-mission-and-programme-readiness`

## Boundaries retained

No deployment, publication, external fetch, credential use, programme contact,
target interaction, posture change, Ubuntu acceptance, merge, or submission
occurred. Practice unlock does not award mastery.

## Next safe action

Finish whole-application first-entry keyboard traversal, then exercise the
accepted wheel through a separate Windows user and shortcut/install/recovery
path. After those product gates, connect the coach through the governed model
gateway and implement the two queued local Case Packs.
