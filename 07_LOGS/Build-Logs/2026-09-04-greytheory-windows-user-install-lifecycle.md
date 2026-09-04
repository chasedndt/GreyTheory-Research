# GreyTheory Windows current-user install lifecycle — build log

**Date:** 2026-09-04

**Agent:** Codex

**Branch:** `codex/2026-09-01-workbench-read-model-binding`

**Posture:** `LOCAL_FIXTURE`

## Repo-truth delta

Before this increment, GreyTheory had a reproducible wheel and an accepted
empty-prefix launcher/UI check, but no user-mode installer, Start Menu-shaped
shortcut, or evidence that private learner state survived restart, upgrade, or
application-runtime recovery.

After this increment:

- `scripts/install-windows-user.ps1` builds or accepts a wheel, creates a
  current-user virtual environment, keeps private data in a separate root,
  writes a capability-truth manifest, and creates a shortcut;
- the generated Windows launcher opens the browser only after `/healthz`
  reports `LOCAL_FIXTURE` and `live_target_available=false`;
- browser-opening convenience stays outside `greytheory_local`, whose
  no-browser/no-target-client import guard continues to pass;
- `acceptance/run-windows-user-install.ps1` sends a real bounded learning
  command and proves its journey survives restart, same-wheel upgrade, and
  replaceable-runtime recovery; and
- the acceptance records `separate_user_accepted=false` and
  `signed_installer=false`, so it does not close the broader Windows host gate.

## Verification

```text
PowerShell parser: installer and lifecycle harness passed

python -m pytest -q tests/test_packaged_ui.py tests/test_local_workbench_transport.py
11 passed in 12.29s

python -m pytest -q
686 passed in 19.94s

acceptance/run-windows-user-install.ps1 -PackageWheel <accepted wheel>
accepted=true; host=Windows; account_scope=current_user_isolated_paths;
posture=LOCAL_FIXTURE; live_target_available=false;
shortcut_created=true; shortcut_target_launch_checked=true;
persisted_journey_restart=true; persisted_journey_upgrade=true;
persisted_journey_recovery=true; separate_user_accepted=false;
signed_installer=false
```

Accepted record:
`E:\Projects\GreyTheory\acceptance\windows-user-install-20260904-092039-9220\acceptance.json`.

Accepted wheel SHA-256:
`cf573bf9ba23d65794a923b3d9fdbe3181a755cb9ca40ec33946b1a421d64b02`.

The earlier interrupted run retained evidence through the fresh persisted
command and ended when its observation session was interrupted at restart. It
was not counted as acceptance. The final complete record above is authoritative.

## Untouched boundaries

- No real Start Menu, normal user-data root, secondary account, administrator
  permission, credential, signing key, uninstall registration, deployment, or
  publication was used.
- No target-network client, external programme connector, model provider,
  Ubuntu worker, VPS, submission path, or posture transition was enabled.
- The dirty primary GreyTheory checkout and unrelated workspaces were not
  changed.

## Remaining unknowns and next safe action

The in-app browser still cannot synthesize the initial Tab from an unfocused
document body, so the first-entry whole-application keyboard sweep remains
open. A genuinely separate Windows-account install and later release
signing/uninstall acceptance also remain open. The bounded Ubuntu full-service
no-route harness subsequently passed in the same goal continuation; see
`2026-09-04-greytheory-ubuntu-full-service-acceptance.md`. That pass did not
enable `PASSIVE_HTTP`.
