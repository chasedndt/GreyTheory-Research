# GreyTheory API Object Ownership Case Pack - build log

**Date:** 2026-09-04

**Agent:** Codex

**Branch:** `codex/2026-09-01-workbench-read-model-binding`

**Posture:** `LOCAL_FIXTURE`

## Repo-truth delta

Before this increment, Case Pack 02 existed only as queued metadata. The
graphical workbench had one complete local learning mission and could not teach
or persist the API object-authorization loop as a distinct case.

This increment makes API Object Ownership the second ready local mission. It
does not activate a programme connector, HTTP client, target route, posture
change, mastery award, export, or submission path.

## Implementation

- Added an exact 50-minute mission: Learn 12, Practise 18, Prove 8, Reflect 6,
  and Assess 6 minutes.
- Added focused actor-object-action instruction, traditional and AI-assisted
  lenses, two scored checks, four learner explanations, a four-lesson roadmap,
  and primary OWASP/PortSwigger reading links.
- Added own-object allow, deliberately vulnerable cross-owner teaching, and
  server-enforced denial controls. The deterministic simulator emits
  `ALLOW_OWN_OBJECT`, `DEMONSTRATE_MISSING_OWNERSHIP_CHECK`, and
  `DENY_CROSS_OWNER` while declaring no external action.
- Bound Mission Control, Learn, Safe Lab, Cases/Ledger, Hypotheses, Evidence,
  Reports, Readiness, Demo Suite, and Library to the selected Case Pack.
- Added server-persisted end-to-end acceptance and refusal of queued packs.
- Kept the live-programme adapter structurally dark.

## Visual QA

Source and implementation were compared at matching 1265 x 712 and 390 x 844
viewports. Two P2 presentation issues were corrected: truncated desktop
selector labels and a mobile selector that hid ready missions behind a
horizontal introduction state. Final desktop/mobile comparison, learning,
lab-result, assessment, focus-return, console, and overflow checks pass.

Evidence:
`E:\Visual QA\GreyTheory Visual QA\Current Reviews\2026-09-04-api-object-ownership-case-pack`.

Repository media:

- `Docs/assets/api-object-ownership-mission-current.png`
- `Docs/assets/api-object-ownership-learning-current.png`
- `Docs/assets/api-object-ownership-lab-current.png`

## Verification

```text
python -m pytest tests/test_case_pack_workbench.py -q
4 passed

python -m pytest -q
716 passed

npm test
26 UI tests passed; 4 Sites tests passed

npm run build
90 modules transformed; production client and Sites artifacts emitted

scripts/build-windows-package.ps1
bundled UI, Case Pack 02, CSS, and JavaScript present in wheel
wheel SHA-256 a403fc4e831c19ba37888bbe188869d28a03c8cb9fe00c8159a8128ace3bfbda

acceptance/run-windows-packaged-workbench.ps1 -PackageWheel <wheel>
accepted=true; host=Windows; posture=LOCAL_FIXTURE; live_target_available=false;
ui_status=200; ui_bundled=true; snapshot_authenticated=true
```

Accepted package record:
`E:\Projects\GreyTheory\acceptance\windows-package-20260904-150820-27308\acceptance.json`.

## Untouched boundaries

- No programme account, credential, policy review, external intelligence
  fetcher, or target was contacted.
- Completing the journey or assessment does not award mastery automatically.
- Session and Role Transitions remains queued.
- The passive worker, VM carrier, key/recovery approval, programme review,
  human posture decision, VPS, and `PASSIVE_HTTP` remain separate open gates.

## Next safe action

Complete the whole-application first-entry keyboard sweep, then promote Session
and Role Transitions using the same content, persistence, fixture, reporting,
responsive QA, and no-mastering/no-network acceptance standard. The governed
coach connection remains a separate model-gateway boundary.
