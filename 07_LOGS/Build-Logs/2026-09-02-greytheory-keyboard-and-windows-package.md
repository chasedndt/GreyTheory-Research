# GreyTheory keyboard and Windows package — build log

**Date:** 2026-09-02

**Agent:** Codex

**Branch:** `codex/2026-09-01-workbench-read-model-binding`

**Posture:** `LOCAL_FIXTURE`

## Repo-truth delta

Before this increment, the selected dashboard passed responsive visual and
same-origin persistence checks, but compact navigation hid every visible label
without an accessible replacement, the closed mobile drawer remained in the
interaction tree, and the Python wheel did not contain a launchable UI. The
first isolated install also proved that Case Pack resources were missing from
the wheel.

After this increment:

- all thirteen compact navigation controls have accessible names;
- the closed mobile drawer is inert and hidden from assistive technology;
- mobile drawer and connection-dialog focus entry, wrapping, Escape close, and
  focus restoration are browser-verified;
- route selection closes the drawer and focuses the selected workspace;
- the wheel contains the production UI, cards, labs, and all three Case Packs;
- installed launch defaults to the bundled same-origin UI, with `--no-ui` as an
  explicit API-only escape hatch; and
- an empty-prefix Windows install passed launcher, UI, health, authenticated
  snapshot, exact-process cleanup, and a non-echoed ephemeral environment-token
  check.

## Verification

```text
python -m pytest -q
682 passed in 165.16s

npm --prefix workbench_ui run test
18 UI tests passed; 4 Sites tests passed

npm --prefix workbench_ui run build
production build passed

python -m pytest tests/test_packaged_ui.py tests/test_local_workbench_transport.py -q
11 passed in 7.51s

acceptance/run-windows-packaged-workbench.ps1 -PackageWheel <accepted wheel>
accepted=true; host=Windows; posture=LOCAL_FIXTURE; live_target_available=false;
loopback_host=127.0.0.1; ui_status=200; snapshot_authenticated=true
```

Accepted record:
`E:\Projects\GreyTheory\acceptance\windows-package-20260902-172716-21344\acceptance.json`.

Accepted wheel SHA-256:
`fc053bd1840f9302e17e5fe3913e23db3771008a3ee52a7d4d0cabe0352e8474`.

Browser evidence:
`E:\Visual QA\GreyTheory Visual QA\Current Reviews\2026-09-02-keyboard-and-windows-package\02-mobile-navigation-open.png`.

## Untouched boundaries

- No target-network client, provider fetcher, programme connector, model-backed
  coach, credential, VPS, submission path, or posture transition was enabled.
- The Ubuntu full worker-service acceptance remains unsuccessful and was not
  retried in this increment.
- The dirty primary GreyTheory and ChaseInTech workspaces were not changed.
- No release was published and the existing pull request was not merged.

## Remaining unknowns and next safe action

The in-app browser could verify the drawer/modal boundaries and route handoff,
but it could not synthesize the first Tab from an unfocused browser body, so a
complete first-entry and whole-application keyboard sweep remains open. The
wheel has not yet been installed under a separate Windows user, exposed through
an installed shortcut or signed installer, restarted with persisted learner
state, upgraded, or recovered. Those checks are the next Windows pilot gate.
