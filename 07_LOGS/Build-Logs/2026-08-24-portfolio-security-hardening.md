# GreyTheory portfolio security hardening — 2026-08-24

## Repository truth

- Clean immutable base: `dd1f92a8097fd6156171d69e152885f058510046`.
- Isolated worktree: `E:\ChaseOSBuilds\2026-08-24-greytheory-offline-boundary\worktree`.
- Branch: `codex/2026-08-24-greytheory-offline-boundary`.
- Canonical checkout was clean and remained untouched.

## Change

`ScopeWatch` no longer accepts caller-provided executable fetchers or a Boolean network override. It accepts only the exact rooted `LocalSourceFetcher`. Future network collection remains absent and must be implemented as a separately governed capture process that hands immutable local evidence to the core.

Historical synthetic fixture runners were bound to their fixture timestamps. This fixes two date-dependent clean-checkout test failures while preserving real stale-contract rejection.

All `actions/checkout` and `actions/setup-python` uses in `.github/workflows/ci.yml` were changed from mutable major tags to exact upstream commit hashes.

## Safety boundary

No target, programme, provider, model, browser, socket, credential, payment or external security system was contacted. No live posture was enabled. `PASSIVE_HTTP` remains dark.

## Verification

- Baseline full suite: 523 passed, 2 date-dependent fixture failures.
- Hardened targeted suite: 21 passed.
- Hardened full suite: 526 passed.
- `python -m compileall -q greytheory`: exit 0.
- `git diff --check`: exit 0.
- Workflow provenance check: every external `uses:` reference is a 40-character commit hash.
