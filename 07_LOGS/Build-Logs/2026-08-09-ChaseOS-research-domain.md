# Build Log - GreyTheory Research Domain

- Date: 2026-08-09
- Runtime: Codex
- Session descriptor: `research-domain`
- Phase / pass: Milestone 3 structured research domain
- Branch: `codex/2026-08-09-research-domain`
- Base: `9b8e2d7`
- Status: COMPLETE and VERIFIED locally; not pushed or deployed

## Task summary

Implement the complete ten-object Milestone 3 research domain, prove one full local structured session without generic notes or network dependencies, reconcile canonical truth, and synchronize the prepared GreyTheory surface on ChaseInTech only after implementation evidence was green.

## Repo-truth baseline

- Milestones 1 and 2 were complete and the repository was clean at 397 tests.
- `DOMAIN_MODEL.md` specified the ten research records and invariants, but no `greytheory/research/` package or workspace/session persistence existed.
- The active posture was `LOCAL_FIXTURE`; all live-target, submission, disclosure, and programme-outcome claims remained prohibited.
- Package placement was an evidence-gated open question.

## Files read

- The supplied GreyTheory productisation plan and its Milestone 3 object, lifecycle, broker, and exit requirements
- `README.md`, `PROJECT_DEFINITION.md`, `PROJECT_STATE.md`, `DOMAIN_MODEL.md`, `DATA_POLICY.md`, `THREAT_MODEL.md`, `INTEGRATION_BOUNDARIES.md`
- `Docs/roadmap.md`, `Docs/open-questions.md`, `Docs/definition.md`, `Docs/module-breakdown.md`, `Docs/system-overview.md`, and relevant ADRs
- Existing authority, audit, registry, evidence, ledger, finding, signal, test, and package-export implementations
- Current build logs, documentation history, daily note, and indexes

## Files modified

- `greytheory/__init__.py`
- `README.md`
- `PROJECT_DEFINITION.md`
- `PROJECT_STATE.md`
- `DOMAIN_MODEL.md`
- `DATA_POLICY.md`
- `THREAT_MODEL.md`
- `INTEGRATION_BOUNDARIES.md`
- `Docs/roadmap.md`
- `Docs/open-questions.md`
- `Docs/definition.md`
- `Docs/module-breakdown.md`
- `Docs/system-overview.md`
- `Docs/decisions/ADR-0001-security-research-operating-system.md`
- Linked daily and index records

## Files created

- `greytheory/research/__init__.py`
- `greytheory/research/domain.py`
- `greytheory/research/store.py`
- `tests/test_research.py`
- This build log
- `99_ARCHIVE/Documentation-History/2026-08-09_research-domain.md`
- `07_LOGS/Agent-Activity/2026-08-09-codex-research-domain.md`

## Tests run

```powershell
python -m compileall -q greytheory
python -m pytest -q tests/test_research.py
python -m pytest -q
```

Paired prepared-site acceptance is recorded in `chaseintech-personal-site/07_LOGS/Build-Logs/2026-08-09-ChaseOS-greytheory-research-domain-sync.md`.

## Test results

- Package compilation: PASS.
- Focused research-domain suite: 14 passed in 4.50 seconds on the final code.
- Complete GreyTheory suite: 411 passed in 21.04 seconds on the final code.
- Diff whitespace check: PASS.

## Verification evidence

- One persisted and reopened local session exercises `ResearchWorkspace`, `ResearchSession`, `TargetAsset`, `AssetRelationship`, `ResearchIdentity`, `Hypothesis`, `ExperimentPlan`, `ActionRequest`, `ActionReceipt`, and `Lesson`.
- Every record is workspace- and contract-fingerprint-bound; workspace creation requires a current human-reviewed verified contract.
- Asset classification is recomputed from that contract, and graph relationships cannot mutate classification or inherit scope.
- Identity records contain ownership and credential references, not credential values; sensitive response-metadata keys are rejected.
- Hypothesis, experiment, session, and workspace transitions are explicit; plans have no execution method.
- Receipts require an allowed audited `gate.evaluate` record matching authority, canonical asset, requested authority, technique, purpose, action type, and approval reference.
- Request, time, and named effect budgets fail closed at action, session, and workspace boundaries.
- Workspace JSON is atomically replaced, integrity-digested, referentially validated, refused inside Git by default, and optionally written to the existing hash-chained audit.
- Completed sessions require checked evidence, a refuted/inconclusive hypothesis, or a reusable lesson.
- Static acceptance confirms the research package imports no network or process-execution modules.

## What changed

- Resolved the product/domain boundary at `greytheory/research/`, outside the authority package but dependency-free and subordinate to it.
- Implemented all ten Milestone 3 records, supporting enums/effect budgets, serialization, lifecycle rules, and the local `ResearchStore`.
- Marked Milestone 3 COMPLETE and Milestone 4 current only after the 14-test focused and 411-test full evidence passed.
- Updated data, threat, integration, package, public-copy, and roadmap truth to distinguish the verified structured domain from the still-unbuilt integrated vertical slice.

## What did not change

- Operating posture remains `LOCAL_FIXTURE`; no network, browser, target, credential validation, submission, disclosure, or programme contact was added.
- The Bugcrowd/YNAB bundle remains `BLOCKED` on two human-owned conflicts; HackerOne/GitLab and MCP Python SDK remain `PENDING_REVIEW`.
- The existing gate, evidence vault, validation, report studio, provenance, finding, and ledger contracts were not weakened or rewritten.
- No SQLite index, graphical workbench, model gateway, vulnerability-card system, or validator-issued `CheckReceipt` was added.
- No branch was pushed, merged, or deployed.

## What remains unverified

- Milestone 4's deliberately vulnerable two-account fixture and the end-to-end runner to observation/check to evidence to validation to report connection.
- Production publication of the GreyTheory source and the prepared ChaseInTech copy.
- Real programme research, findings, submissions, outcomes, and any posture above `LOCAL_FIXTURE`.

## Remaining open loops

- Build the Milestone 4 local fixture with two controlled identities and synthetic objects.
- Bind action tickets/receipts to the existing runner and add deterministic check receipts without caller-asserted proof.
- Keep the prepared site branch local until the GreyTheory source sequence is intentionally published and deployment is explicitly authorized.

## Process and storage closeout

- System-drive free space was 12.29 GiB (5.17%) at Milestone 3 preflight and 12.83 GiB (5.40%) at closeout, above both reporting thresholds but still close to the percentage boundary.
- `python -m chaseos audit storage --apply --require-headroom` was attempted and failed because the active Python environment has no `chaseos` module; no broad cleanup was substituted.
- The exact site build orphan from the first bounded build attempt was identified as PID 34672 by repository command line, stopped, and verified absent with no owned listener.
- Final browser teardown left port 4321 clear. Only the active Codex runtime and diagnostic shell referenced the repositories at closeout; no spawned server, browser, model worker, or helper remained.
- The final site `dist` is 21.89 MiB and the GreyTheory `.pytest_cache` is 0.04 MiB. Neither justified deleting current evidence or shared caches.

## Next recommended pass

Implement Milestone 4 as one deliberately vulnerable, fully local two-account authorisation slice. Preserve the gate as the authority root, issue validator-owned check receipts, and do not raise posture or contact any target.

## Links

- [Documentation history](../../99_ARCHIVE/Documentation-History/2026-08-09_research-domain.md)
- [Daily note](../Daily/2026-08-09.md)
- [Agent activity](../Agent-Activity/2026-08-09-codex-research-domain.md)
- [Roadmap](../../Docs/roadmap.md)
- [Domain model](../../DOMAIN_MODEL.md)
- [Prepared ChaseInTech sync](../../../chaseintech-personal-site/07_LOGS/Build-Logs/2026-08-09-ChaseOS-greytheory-research-domain-sync.md)
