# Build Log - Direct VDP Source Bundle

- Date: 2026-08-09
- Runtime: Codex
- Session descriptor: `direct-vdp-source-bundle`
- Phase / pass: Productisation Milestone 2, real-programme proof 3 of 3
- Branch: `codex/2026-08-09-direct-vdp-source-bundle`
- Base: `75a617e`
- Status: VERIFIED locally; direct bundle `PENDING_REVIEW`; Milestone 2 implementation/evidence proof COMPLETE; not pushed or deployed

## Task summary

Complete the third programme-source proof using one independently maintained public security policy, preserve the exact immutable source, add derivation semantics only for its observed Markdown support table, prove compilation remains offline and fail-closed, and advance repository and prepared ChaseInTech truth to Milestone 3 without granting live authority.

## Repo-truth baseline

- Milestone 1 was complete and Milestone 2 had two of three source-shape proofs at `75a617e` with 386 passing tests.
- HackerOne/GitLab reached `PENDING_REVIEW`; Bugcrowd/YNAB correctly remained `BLOCKED` on two human-owned conflicts.
- The direct VDP or independently hosted policy proof was the sole missing Milestone 2 implementation item.
- The active posture was and remains `LOCAL_FIXTURE`; no network collector or live-target interaction exists.

## Files read

- Operator-supplied GreyTheory productisation plan and its Milestone 2 exit conditions
- Current canonical identity, state, domain, roadmap, system, module, open-question, decision, and governance documentation
- Existing programme-source compiler, registry, CLI, fixtures, and tests
- Official `modelcontextprotocol/python-sdk` public security policy and immutable GitHub commit metadata
- Current ChaseInTech GreyTheory project/build-log data and regression tests

## Files modified

- `greytheory/authority/sources.py`
- `tests/test_sources.py`
- `README.md`, `PROJECT_STATE.md`, `PROJECT_DEFINITION.md`, `DOMAIN_MODEL.md`, and `CHANGELOG.md`
- `Docs/README.md`, `Docs/definition.md`, `Docs/roadmap.md`, `Docs/system-overview.md`, `Docs/module-breakdown.md`, `Docs/open-questions.md`, and `Docs/decisions/ADR-0005-offline-semantic-programme-source-bundles.md`
- Linked build-log, documentation-history, daily, agent-activity, and index records

## Files created

- `fixtures/programmes/public/direct-mcp-python-sdk-2026-08-09/README.md`
- `fixtures/programmes/public/direct-mcp-python-sdk-2026-08-09/manifest.json`
- `fixtures/programmes/public/direct-mcp-python-sdk-2026-08-09/programme.json`
- `fixtures/programmes/public/direct-mcp-python-sdk-2026-08-09/sources/SECURITY.md`
- This build log and linked session records

## Tests run

```powershell
python -m pytest -q tests/test_sources.py
python -m pytest -q
```

Additional checks:

```powershell
# Fetch immutable raw SECURITY.md bytes and compare them to the fixture.
python -

# Parse the manifest, recompute the saved-source SHA-256, and compile the bundle.
python -

# Reproduce the CI network-import prohibition against greytheory/*.py.
Get-ChildItem greytheory -Recurse -File -Filter *.py | Select-String <CI-network-import-pattern>

git check-attr text eol -- fixtures/programmes/public/direct-mcp-python-sdk-2026-08-09/manifest.json fixtures/programmes/public/direct-mcp-python-sdk-2026-08-09/programme.json fixtures/programmes/public/direct-mcp-python-sdk-2026-08-09/sources/SECURITY.md
```

ChaseInTech acceptance ran on its dedicated branch:

```powershell
npm run build
npx playwright test tests/smoke.spec.js --grep "GreyTheory public surface"
npm run test:e2e
```

## Test results

- Final source-bundle suite: 50 passed in 8.35 seconds.
- Final full GreyTheory suite: 397 passed in 28.77 seconds.
- Immutable remote/local byte comparison: PASS, 1,691 bytes identical.
- Manifest parsing, source hash, and direct bundle compilation: PASS.
- Core no-network import check: PASS.
- Git attribute check: PASS; hashed public programme evidence is `text` with `eol=lf`.
- Direct bundle result: `PENDING_REVIEW`, 2 in-scope rows, 1 out-of-scope row, zero ambiguities.
- ChaseInTech build: PASS; 10 projects, 8 published logs, 2 drafts, 54 pages, zero noncanonical links, and 3,166 indexed words.
- Final focused GreyTheory Chromium regression: 1 passed in 25.8 seconds.
- Final full ChaseInTech Chromium suite: 56 passed in 1.8 minutes.

## Verification evidence

- Selected source: official `modelcontextprotocol/python-sdk` `SECURITY.md` at immutable commit `d82ed88eb558e80079c32b45a83a774cf1b3db7b`.
- Source commit timestamp: `2026-07-29T13:54:45Z`.
- Verbatim source SHA-256: `sha256:c0e53bd713720169a6ec499e1e4f1df21656eb8a1b260e67fda11ba3e4f90ad6`.
- Compiled semantic bundle hash: `sha256:338980d3fa655d6400854557e5ee472f5a73bc1cc2ba763f238ecc0f23ee169f`.
- The observed Markdown Version/Line/Support table derives exactly two security-supported lines and one explicitly unsupported class.
- Tests prove missing, added, malformed, unclassified, or wrongly typed policy/table evidence blocks instead of changing authority silently.
- Registry and CLI tests preserve the complete verbatim source and never self-award human review.

## Process and storage closeout

- System-drive free space at the start of this continuation: 14.27 GiB.
- System-drive free space at final closeout: 12.33 GiB (5.18%), above the 10 GiB and 5% reporting thresholds but close to the percentage threshold.
- `python -m chaseos audit storage --apply --require-headroom` was attempted and could not run because the active Python environment has no `chaseos` module. No broad cleanup was substituted.
- One bounded CLI-smoke command containing exact temporary-directory cleanup was rejected before execution; it created no directory and left no new residue.
- Playwright-owned preview processes exited and port 4321 has zero listeners.
- A bounded audit found only 21.89 MiB in the current site `dist`, 0.05 MiB in `.astro`, and 0.03 MiB in GreyTheory `.pytest_cache`. Recent matching temporary items were at most 3.25 MiB; the 0.685 GiB shared Playwright browser cache predates this session. These owned/session-visible items do not explain the wider concurrent free-space drop, so no shared cache, other session's 0.85 MiB Miniflare directory, or ambiguous path was deleted.

## What changed

- Added `markdown_supported_versions_v1` validation for the exact supported-version table observed in an independently maintained repository policy.
- Derivation source-kind and capture-mode validation now distinguishes structured platform exports, operator-extracted rendered tables, and immutable verbatim programme policies.
- Added an immutable, verbatim direct-policy fixture with exact source provenance, hash, field citations, one-source precedence, and no fabricated human resolution.
- Closed the three-source Milestone 2 implementation/evidence proof and advanced the roadmap to Milestone 3.

## What did not change

- The saved policy is not treated as target-testing permission; the normalized contract remains under `LOCAL_FIXTURE` and `PENDING_REVIEW`.
- No SDK, deployed MCP service, or other target was contacted. Only public GitHub repository, API, raw-content, and security-policy surfaces were read.
- The Bugcrowd/YNAB bundle remains blocked; its two policy decisions remain human-owned.
- No network import, live-target lane, disclosure, submission, credential, or bounty authority was enabled.
- No branch was pushed, merged, or deployed.

## What remains unverified

- Human review of the HackerOne/GitLab and direct-policy/MCP Python SDK bundles.
- Human resolution of the two YNAB policy conflicts.
- Milestone 3 research-domain implementation and every later milestone.
- Production publication of the GreyTheory repository and prepared ChaseInTech copy.
- All live-target behavior and security outcomes.

## Remaining open loops

- Implement Milestone 3's structured domain objects without weakening Authority Plane boundaries.
- Keep source acquisition manual and offline until the separate Scope Watch milestone.
- Do not raise posture or publish testing-capability claims from source-shape proof alone.

## Next recommended pass

Begin Milestone 3 with the authority-bound research-domain contracts: workspace, session, asset/relationship, controlled identity, hypothesis, experiment plan, action request/receipt, and lesson. Verify one complete local structured session before any UI work.

## Links

- [Documentation history](../../99_ARCHIVE/Documentation-History/2026-08-09_direct-vdp-source-bundle.md)
- [Daily note](../Daily/2026-08-09.md)
- [Agent activity](../Agent-Activity/2026-08-09-codex-direct-vdp-source-bundle.md)
- [Roadmap](../../Docs/roadmap.md)
- [ADR-0005](../../Docs/decisions/ADR-0005-offline-semantic-programme-source-bundles.md)
