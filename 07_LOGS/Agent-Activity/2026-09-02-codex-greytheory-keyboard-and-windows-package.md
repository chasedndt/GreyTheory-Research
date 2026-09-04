# Codex activity — GreyTheory keyboard and Windows package

## Scope

Continue the existing local-first learner-pilot goal by closing the next
verified keyboard and packaging defects without enabling live research.

## Actions

- Audited compact and mobile navigation in the in-app browser.
- Added accessible navigation names, mobile drawer inert state, focus
  containment, Escape handling, and focus restoration.
- Browser-tested mobile forward/reverse wrapping, drawer dismissal, Learn route
  focus, and modal forward/reverse wrapping and dismissal.
- Added packaged-UI discovery, bundled package data, a Windows wheel builder,
  and an isolated installed-workbench acceptance harness.
- Used failed isolated runs as evidence: corrected a PowerShell selector,
  replaced slow full-venv bootstrap with an empty prefix, added missing Case
  Pack package data, then moved the token out of redirected stdout into a
  temporary child-process environment value restored after shutdown.
- Restored the repository's editable development install after a diagnostic
  prefix command caused pip to remove it.
- Ran targeted and full regressions and synchronized canonical documentation.

## Guardrails retained

`LOCAL_FIXTURE` remains the ceiling. No external HTTP, account connector,
credential, worker, Ubuntu service, VPS, submission, publication, or posture
decision was activated.

## Handoff

Complete first-entry/whole-application keyboard traversal and a separate-user
shortcut or signed-installer persistence/recovery run before treating the
Windows workbench gate as complete.
