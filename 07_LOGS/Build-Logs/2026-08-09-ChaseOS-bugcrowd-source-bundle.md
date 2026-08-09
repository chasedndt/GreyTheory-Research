# Build Log - Bugcrowd Source Bundle

- Date: 2026-08-09
- Runtime: Codex
- Session descriptor: `bugcrowd-source-bundle`
- Phase / pass: Productisation Milestone 2, real-programme proof 2 of 3
- Branch: `codex/2026-08-09-bugcrowd-source-bundle`
- Base: `c4234e8`
- Status: VERIFIED locally; bundle intentionally `BLOCKED`; Milestone 2 PARTIAL; not pushed or deployed

## Task summary

Capture one public Bugcrowd programme without target contact, preserve its rendered target groups and governing policy extracts as offline evidence, extend deterministic source derivation only for the observed source shape, fail closed on genuine authority conflicts, and synchronize repository and prepared ChaseInTech truth.

## Repo-truth baseline

- The multi-source compiler and first HackerOne/GitLab proof were implemented at `c4234e8` with 376 passing tests.
- Milestone 2 still required one Bugcrowd proof and one independently hosted direct vulnerability disclosure programme (VDP) proof.
- Bugcrowd presents target groups in a JavaScript-rendered engagement brief rather than an official downloadable scope export on the selected public page.
- The active posture was and remains `LOCAL_FIXTURE`; no live-target authority exists.

## Files read

- Current identity, state, roadmap, domain, system, module, open-question, decision, and governance documentation
- Existing source-bundle compiler and tests
- Public YNAB Bugcrowd engagement brief and its two rendered target groups
- Bugcrowd Standard Disclosure Terms linked by the engagement brief
- Bugcrowd customer documentation for engagement scope and reward configuration
- Current ChaseInTech GreyTheory project/build-log data and regression tests

## Files modified

- `greytheory/authority/sources.py`
- `tests/test_sources.py`
- `README.md`, `PROJECT_STATE.md`, `PROJECT_DEFINITION.md`, `DOMAIN_MODEL.md`, and `CHANGELOG.md`
- `Docs/README.md`, `Docs/definition.md`, `Docs/roadmap.md`, `Docs/system-overview.md`, `Docs/module-breakdown.md`, `Docs/open-questions.md`, and `Docs/decisions/ADR-0005-offline-semantic-programme-source-bundles.md`
- Linked build-log, documentation-history, daily, agent-activity, and index records

## Files created

- `.gitattributes`
- `fixtures/programmes/public/bugcrowd-ynab-2026-08-09/README.md`
- `fixtures/programmes/public/bugcrowd-ynab-2026-08-09/manifest.json`
- `fixtures/programmes/public/bugcrowd-ynab-2026-08-09/programme.json`
- `fixtures/programmes/public/bugcrowd-ynab-2026-08-09/sources/ynab-target-groups.json`
- `fixtures/programmes/public/bugcrowd-ynab-2026-08-09/sources/ynab-programme-brief.md`
- `fixtures/programmes/public/bugcrowd-ynab-2026-08-09/sources/bugcrowd-standard-disclosure.md`
- This build log and linked session records

## Tests run

```powershell
python -m pytest -q tests/test_sources.py tests/test_registry.py tests/test_compiler.py
python -m pytest -q
```

Additional checks:

```powershell
# Parse the manifest, programme record, and target-group extract; recompute each SHA-256; compile the saved bundle.
python -

# Reproduce the CI network-import prohibition against greytheory/*.py.
Get-ChildItem greytheory -Recurse -File -Filter *.py | Select-String <CI-network-import-pattern>

git check-attr text eol -- fixtures/programmes/public/bugcrowd-ynab-2026-08-09/manifest.json fixtures/programmes/public/bugcrowd-ynab-2026-08-09/programme.json fixtures/programmes/public/bugcrowd-ynab-2026-08-09/sources/ynab-target-groups.json
```

ChaseInTech surface acceptance ran on its dedicated branch:

```powershell
npm run build
npx playwright test tests/smoke.spec.js --grep "GreyTheory public surface"
npm run test:e2e
```

## Test results

- Final focused source/compiler/registry suite: 94 passed in 10.96 seconds.
- Full GreyTheory suite: 386 passed in 39.51 seconds.
- Manifest/programme/target JSON parsing and all three saved-source hashes: PASS.
- Core no-network import check: PASS.
- Git attribute check: PASS; hashed public programme evidence is `text` with `eol=lf`.
- Direct bundle compile: expected `BLOCKED`, 3 in-scope rows, 5 out-of-scope rows, and exactly 2 pending human-resolution ambiguities.
- ChaseInTech production build: PASS; 10 projects, 8 published logs, 2 drafts, 54 pages, zero noncanonical links, and 3,168 indexed words.
- Focused GreyTheory Chromium regression: 1 passed in 38.1 seconds.
- Full ChaseInTech Chromium suite: 56 passed in 1.8 minutes.

## Verification evidence

- Live rendered target arrays were mechanically compared with the saved extract and matched exactly: 3 in-scope and 5 out-of-scope rows.
- The public brief contained both broad YNAB-owned-host language and later listed-target-only language, plus a production-API mention and a production-environment exclusion.
- Bugcrowd's linked platform terms state that programme-brief terms supersede platform defaults and that testing is limited to the listed Targets by default.
- Target-group SHA-256: `sha256:db1d0590b1f5fb5c4bc2c5000d57e8b4ff1afc2f7db57687cb9542351b2f0964`.
- Programme-brief SHA-256: `sha256:357d16587b79ecf806109bd3c245b4b72d0f35b020b16a395f2f9ecfd6eeb1dc`.
- Platform-default SHA-256: `sha256:799f15fa2c29b3429ec13d307b72cf798abe7b1f2457cf65ebc013385e940bf9`.
- Compiled semantic bundle hash: `sha256:0ad3eeb6982283853799c8c878d68d893427463e0d268b9e7f2d184c5f311167`.

## Process and storage closeout

- System-drive free space before this proof's final test/build work: 14.43 GiB.
- System-drive free space at final closeout: 14.27 GiB (6.00%), above the 10 GiB and 5% reporting thresholds.
- `python -m chaseos audit storage --apply --require-headroom` was attempted during closeout and could not run because the active Python environment has no `chaseos` module. No broad cleanup was substituted.
- The browser research tabs were closed, Playwright's preview process exited, and port 4321 has zero listeners.
- The prior pass's 27,255-byte bounded temporary CLI-smoke directory remains untouched after its exact cleanup was rejected; no source, package, cache, evidence, or ambiguous path was deleted.

## What changed

- Added `bugcrowd_target_groups_json_v1` validation for a schema-versioned operator extract of rendered Bugcrowd target groups.
- Scope-table derivations now require a `scope_table` source and exactly the `in_scope` and `out_of_scope` target fields.
- Missing, invented, duplicate, malformed, or cross-class target rows fail closed.
- Added a real public YNAB bundle with explicit precedence, citations, integrity hashes, and two pending human-resolution records.
- Added a narrow LF rule so byte-sensitive public evidence hashes remain reproducible across Windows and Linux checkouts.

## What did not change

- No official Bugcrowd export is claimed; every saved source is truthfully labelled `operator_extract`.
- No target host was visited; only public Bugcrowd programme, platform, and documentation pages were read.
- No AI or operator decision was invented. The YNAB bundle remains `BLOCKED`.
- No network client, live-target lane, disclosure, submission, credential, or bounty authority was enabled.
- No branch was pushed, merged, or deployed.

## What remains unverified

- Human resolution of the two YNAB authority conflicts.
- The independently hosted direct-VDP proof needed to complete Milestone 2.
- Production publication of the GreyTheory repository and prepared ChaseInTech copy.
- Milestones 3-13 and all live-target behavior.

## Remaining open loops

- Capture and compile one independently hosted direct-VDP public policy bundle.
- Keep the YNAB conflict decisions separate and human-owned.
- Do not advance beyond `LOCAL_FIXTURE` or imply testing authority from saved public evidence.

## Next recommended pass

Milestone 2, proof 3 of 3: select one suitable direct VDP, capture only its public policy evidence without target contact, reuse the existing semantics where they fit, and extend the model only for observed evidence.

## Links

- [Documentation history](../../99_ARCHIVE/Documentation-History/2026-08-09_bugcrowd-source-bundle.md)
- [Daily note](../Daily/2026-08-09.md)
- [Agent activity](../Agent-Activity/2026-08-09-codex-bugcrowd-source-bundle.md)
- [Roadmap](../../Docs/roadmap.md)
- [ADR-0005](../../Docs/decisions/ADR-0005-offline-semantic-programme-source-bundles.md)
