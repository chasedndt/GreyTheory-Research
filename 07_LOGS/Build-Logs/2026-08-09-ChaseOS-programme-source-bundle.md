# Build Log - Programme Source Bundle

- Date: 2026-08-09
- Runtime: Codex
- Session descriptor: `programme-source-bundle`
- Phase / pass: Productisation Milestone 2, real-programme proof 1 of 3
- Branch: `codex/2026-08-09-programme-source-bundle`
- Base: `f17c4a2`
- Status: PARTIAL milestone; implementation VERIFIED locally; not pushed or deployed

## Task summary

Implement the first real public programme-source bundle without target contact: preserve the complete source set, prove source integrity and precedence, compile it offline into the existing authority contract, fail closed on unresolved human decisions or scope drift, and synchronize current product truth and the prepared ChaseInTech surface.

## Repo-truth baseline

- Milestone 1 was complete locally at `f17c4a2` with 347 passing tests.
- The registry accepted only a single raw source snapshot; it had no complete multi-source provenance object.
- Milestone 2 requires three real public programme proofs: HackerOne, Bugcrowd, and a direct vulnerability disclosure programme (VDP).
- The active posture was and remains `LOCAL_FIXTURE`; no live-target authority exists.

## Files read

- Current identity, state, roadmap, domain, system, module, open-question, and decision documentation
- Existing authority compiler, scope contract, programme registry, CLI, package exports, and tests
- Public GitLab programme policy and scope table on HackerOne
- Official HackerOne Core Ineligible Findings documentation
- Current GreyTheory fixture and governance conventions

## Files modified

- `greytheory/registry.py`
- `greytheory/cli.py`
- `greytheory/__init__.py`
- `greytheory/authority/__init__.py`
- `pyproject.toml`
- `README.md`, `PROJECT_STATE.md`, `PROJECT_DEFINITION.md`, `DOMAIN_MODEL.md`, and `CHANGELOG.md`
- `Docs/README.md`, `Docs/definition.md`, `Docs/roadmap.md`, `Docs/system-overview.md`, `Docs/module-breakdown.md`, `Docs/open-questions.md`, and `Docs/decisions/README.md`
- Linked build-log, documentation-history, daily, agent-activity, and index records

## Files created

- `greytheory/authority/sources.py`
- `tests/test_sources.py`
- `fixtures/programmes/public/hackerone-gitlab-2026-08-09/README.md`
- `fixtures/programmes/public/hackerone-gitlab-2026-08-09/manifest.json`
- `fixtures/programmes/public/hackerone-gitlab-2026-08-09/programme.json`
- `fixtures/programmes/public/hackerone-gitlab-2026-08-09/sources/gitlab-scope.csv`
- `fixtures/programmes/public/hackerone-gitlab-2026-08-09/sources/gitlab-programme-guidelines.md`
- `fixtures/programmes/public/hackerone-gitlab-2026-08-09/sources/hackerone-core-ineligible.md`
- `Docs/decisions/ADR-0005-offline-semantic-programme-source-bundles.md`
- This build log and linked session records

## Tests run

```powershell
python -m pytest -q tests/test_sources.py tests/test_registry.py tests/test_compiler.py
python -m pytest -q
python -m greytheory.cli --audit <temp>/audit.jsonl programme --registry <temp>/contracts register-bundle fixtures/programmes/public/hackerone-gitlab-2026-08-09
python -m greytheory.cli --audit <temp>/audit.jsonl audit-verify
```

The GitHub Actions no-network import expression was also reproduced locally against `greytheory/`.

ChaseInTech surface acceptance was run in its dedicated branch:

```powershell
npm run build
npm run test:e2e
```

## Test results

- Focused bundle/compiler/registry suite: 84 passed.
- Full GreyTheory suite: 376 passed in 26.05 seconds.
- Core no-network import check: PASS.
- Real bundle CLI smoke: PASS; `pending_review`, `LOCAL_FIXTURE`, 3 sources, 19 in-scope rows, and 25 out-of-scope rows.
- Audit verification: PASS; one intact registration record.
- ChaseInTech publication audit/build: PASS; 10 projects, 8 published logs, 2 drafts, 54 pages, and zero noncanonical links.
- ChaseInTech Chromium suite: 56 passed in 2.6 minutes against the exact final 376-test site tree.

## Verification evidence

- The saved `gitlab-scope.csv` is byte-for-byte equal to the official public HackerOne export captured on 2026-08-09.
- CSV SHA-256: `sha256:d61978dc7d199361ee52c4e06616fe3258d38b3b271497ac4ec688fc136003c3`.
- Compiled semantic bundle hash: `sha256:65391e64c8390be0aae126c9e450fc76fa669f1cbc3ca28236a8fe667febbf65`.
- Deterministic derivation tests prove the normalized contract cannot omit or invent a structured scope row.
- Registry tests prove the complete source snapshot is retained and review is invalidated when any semantic source input changes.

## Process and storage closeout

- System-drive free space before final build/test work: 15.74 GiB.
- System-drive free space after final build/test work: 14.43 GiB (6.07%), above the 10 GiB and 5% reporting thresholds.
- `python -m chaseos audit storage --apply --require-headroom` was attempted and could not run because the active Python environment has no `chaseos` module. No broad cleanup was substituted.
- The Playwright-owned Astro preview exited and port 4321 has zero listeners.
- A 27,255-byte CLI smoke directory remains at `C:/Users/chaseos/AppData/Local/Temp/greytheory-bundle-smoke-20260809-codex`; the execution layer rejected the exact bounded recursive cleanup command. No repository, package, cache, or ambiguous path was deleted.

## What changed

- `ProgrammeSourceBundle` now records source kind, capture mode, public provenance, retrieval/update timestamps, per-source hashes, explicit high-to-low precedence, field citations, deterministic derivations, and human conflict resolutions.
- Bundle compilation remains offline and fail-closed. Bad paths, hash drift, missing citations, ambiguous precedence, unresolved decisions, or structured scope mismatch block the contract.
- Registry storage now retains a complete canonical bundle snapshot and invalidates human review when the semantic bundle changes.
- The CLI can register a saved bundle with `programme register-bundle`.
- The first real proof packages GitLab's public HackerOne scope and bounded policy extracts.

## What did not change

- No network client was added to the GreyTheory package.
- No target host was contacted; only public policy/documentation sources were read.
- No human review was fabricated. The real bundle remains `PENDING_REVIEW`.
- No live-target, submission, disclosure, credential, or bounty authority was enabled.
- No branch was pushed, merged, or deployed.

## What remains unverified

- Human review of the GitLab bundle.
- A real Bugcrowd bundle and a real direct-VDP bundle.
- Whether the generic source model survives both remaining platforms without unjustified special cases.
- Production publication of the GreyTheory repository and prepared ChaseInTech copy.
- Milestones 3-13.

## Remaining open loops

- Capture and compile one public Bugcrowd programme using the same offline evidence rules.
- Record real precedence/conflict behavior rather than assuming HackerOne semantics generalize.
- Complete the direct-VDP proof before closing Milestone 2.

## Next recommended pass

Milestone 2, proof 2 of 3: add one saved public Bugcrowd programme bundle, extend only the source/derivation semantics its evidence requires, keep posture at `LOCAL_FIXTURE`, and retain pending human review.

## Links

- [Documentation history](../../99_ARCHIVE/Documentation-History/2026-08-09_programme-source-bundle.md)
- [Daily note](../Daily/2026-08-09.md)
- [Agent activity](../Agent-Activity/2026-08-09-codex-programme-source-bundle.md)
- [Roadmap](../../Docs/roadmap.md)
- [ADR-0005](../../Docs/decisions/ADR-0005-offline-semantic-programme-source-bundles.md)
