# GreyTheory Case Pack and persisted learner foundation

## Repo-truth delta

Guided Mission Control is no longer only a browser-session walkthrough. The
local application now owns a bounded, revision-safe Learn -> Practise -> Prove
-> Reflect command path and immutable synthetic fixture receipts. The operating
posture remains `LOCAL_FIXTURE` and no live-programme adapter is enabled.

## Built

- Three versioned Case Packs: Agent Tool Authorization is ready locally; API
  Object Ownership and Session/Role Transition are queued.
- A dark live-programme compatibility contract with complete authority fields
  and five mandatory activation gates.
- An integrity-checked private `FixtureReceiptStore` outside Git.
- A practise-stage `run_learning_fixture` command requiring the current
  revision, exact `LOCAL_FIXTURE` authority, and human acknowledgement.
- Optional bounded same-origin UI serving from `greytheory-workbench`.
- Same-origin UI command wiring, restored persisted journey state, focus-safe
  modal behavior, skip navigation, live status messaging, and working Demo
  Suite, Case Pack library, and transition-gate panels.

## Verification

- `python -m pytest -q tests/test_case_pack_workbench.py tests/test_local_workbench_transport.py` — 10 passed.
- `npm run test:ui` — 10 passed.
- `npm run test:sites` — 4 passed.
- `npm run build` — passed; Sites bundle prepared.
- `python -m pytest` — 670 passed in 261.52 seconds.
- Browser visual acceptance is pending because the selected in-app browser
  refused the numeric-loopback URL under its URL policy after the preview
  restart. No alternate browser or bypass was used.

## Boundaries retained

- No target, external request, credential, provider, programme connection,
  posture change, deployment, publication, merge, or push.
- Fixture receipts prove only the synthetic scenario and award no mastery.
- Separate preview origins remain read-only; commands require exact same origin.
- A VPS is not a substitute for Windows, Ubuntu, egress/key, programme-review,
  and human-posture acceptance.

## Next safe action

Visually verify and sequential-keyboard test the same-origin persisted flow,
then package it and run clean-user Windows acceptance.
