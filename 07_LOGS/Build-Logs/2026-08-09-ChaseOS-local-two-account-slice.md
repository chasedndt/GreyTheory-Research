# Build Log - GreyTheory Local Two-Account Slice

- Date: 2026-08-09
- Runtime: Codex
- Session descriptor: `local-two-account-slice`
- Phase / pass: Milestone 4 first end-to-end local vertical slice
- Branch: `codex/2026-08-09-local-two-account-slice`
- Base: `67595ab`
- Status: COMPLETE and VERIFIED locally; not pushed or deployed

## Task summary

Connect the verified research domain to the Authority, Signal, and Judgement
planes through one deliberately vulnerable in-memory two-account authorization
fixture, replace caller-asserted claim promotion with validator-issued receipts,
prove the fail-closed exit conditions, and update prepared ChaseInTech copy only
after the evidence was green.

## Repo-truth baseline

- Milestones 1-3 were complete; the branch was clean at 411 tests.
- The ten research records were persistence-tested, but their acceptance test
  fabricated a response receipt and did not execute an action.
- `Claim.promote_to_checked` trusted a caller-supplied
  `could_have_failed=True` Boolean.
- Reports had an evidence index but no claim/provenance/evidence matrix.
- The integrated two-account fixture was PLANNED and the posture was
  `LOCAL_FIXTURE`.

## Files read

- Supplied GreyTheory productisation plan, especially Milestone 4 and
  `CheckReceipt` requirements
- `README.md`, `PROJECT_DEFINITION.md`, `PROJECT_STATE.md`, `DOMAIN_MODEL.md`,
  `THREAT_MODEL.md`, and `Docs/scope-policy.md`
- `Docs/roadmap.md`, `Docs/definition.md`, `Docs/system-overview.md`,
  `Docs/validation-policy.md`, `Docs/module-breakdown.md`, relevant ADRs, and
  the historical `Docs/full-brief.md`
- Existing compiler, gate, audit, provenance, research-domain/store, signal,
  evidence, finding, validation, report, CLI, and test contracts
- Current build logs, documentation history, daily note, and indexes

## Files modified

- `greytheory/cli.py`
- `greytheory/provenance.py`
- `greytheory/report.py`
- `greytheory/validation.py`
- `greytheory/signal/contract.py`
- `tests/test_provenance.py`
- `tests/test_validation.py`
- Canonical/project documentation and current architecture/validation/ADR docs
- Linked daily and index records

## Files created

- `greytheory/checks.py`
- `greytheory/execution.py`
- `greytheory/lab/__init__.py`
- `greytheory/lab/two_account.py`
- `greytheory/vertical_slice.py`
- `fixtures/lab/two-account-authorization/programme.json`
- `fixtures/lab/two-account-authorization/test-attestations.json`
- `tests/test_vertical_slice.py`
- This build log
- `99_ARCHIVE/Documentation-History/2026-08-09_local-two-account-slice.md`
- `07_LOGS/Agent-Activity/2026-08-09-codex-local-two-account-slice.md`

## Tests run

```powershell
python -m pytest tests/test_provenance.py tests/test_validation.py -q
python -m pytest tests/test_provenance.py tests/test_validation.py tests/test_vertical_slice.py -q
python -m pytest tests/test_vertical_slice.py -q
python -m greytheory.cli demo local-two-account --root <private-proof-root> --attestations fixtures/lab/two-account-authorization/test-attestations.json --json
python -m greytheory.cli --audit <private-proof-root>/audit.jsonl audit-verify
python -m pytest -q
git diff --check
```

Paired prepared-site acceptance is recorded in
`chaseintech-personal-site/07_LOGS/Build-Logs/2026-08-09-ChaseOS-greytheory-local-slice-sync.md`.

## Test results

- Focused provenance/report/validation seam: 47 passed.
- Focused Milestone 4 acceptance after the first integration: 8 passed.
- Focused acceptance after explicit attestation-input governance: 56 passed
  across vertical-slice, provenance, and validation tests.
- Final complete GreyTheory suite: 420 passed.
- Fresh CLI proof: COMPLETE at `LOCAL_FIXTURE`, `report_ready`, one executed
  action, one persisted action receipt, three evidence artifacts, no submission,
  and `attestation_kind=test_fixture`.
- Proof audit chain: PASS, 34 records intact.
- Diff whitespace check: PASS.

## Verification evidence

- Saved training rules compile cleanly to `PENDING_REVIEW`; execution remains
  blocked until an explicit review/attestation record is supplied.
- The acceptance record is labelled `test_fixture`, so it cannot be presented
  as a real human judgement.
- Two controlled identities, two account assets, two synthetic object assets,
  and explicit `OWNS` edges are stored under one contract fingerprint.
- The action request cannot execute itself. The local executor asks the Gate,
  issues a one-use action ticket only after an audited allow, and persists one
  `ActionReceipt` for the one in-memory read.
- A contract prohibiting the technique produces a denied gate record, no action
  receipt, and no evidence.
- `ValidatorRegistry` hashes exact response/ownership bytes and validator code;
  it refuses unregistered, refuted, forged/modified, mismatched, replayed, and
  undeclared-outcome receipts.
- The checked ownership assertion consumes the successful receipt once; its
  input hashes equal the evidence vault's raw hashes.
- Every represented report claim names provenance and evidence. Gates B-F pass,
  and the finding advances only to `report_ready`.
- The completed session stores checked evidence, a postmortem, and a proposed
  IDOR/BOLA card update. The proposal is not canonical Milestone 5 knowledge.
- Static analysis confirms the slice/executor/fixture modules import no network
  clients.

## What changed

- Implemented the complete Milestone 4 training flow from rules through report
  and lesson.
- Removed the caller-supplied `could_have_failed` promotion API and introduced
  registry-issued single-use `CheckReceipt` promotion.
- Added a claim/provenance/evidence matrix to report drafts and Gate F.
- Added explicit operator-statement input; the CLI no longer invents
  attestations from an operator name.
- Marked Milestone 4 COMPLETE and Milestone 5 current after final evidence.

## What did not change

- Operating posture remains `LOCAL_FIXTURE`.
- No socket, HTTP client, browser, credential validation, live target,
  programme contact, submission, disclosure, or outcome path was added.
- HackerOne/GitLab and MCP Python SDK remain `PENDING_REVIEW`; Bugcrowd/YNAB
  remains `BLOCKED` on two human-owned conflicts.
- No vulnerability-card system, model gateway, network broker/worker, Scope
  Watch, or graphical workbench was built.
- No branch was pushed, merged, or deployed.

## What remains unverified

- A real human-supplied attestation record; acceptance used an explicitly
  labelled test fixture.
- Persistent receipt issuance/consumption trust across separate processes.
- Migration of legacy static-collector checked-claim origins to persisted
  receipts.
- Production publication of source or prepared ChaseInTech copy.
- Any real programme research, finding, submission, outcome, or posture above
  `LOCAL_FIXTURE`.

## Remaining open loops

- Build Milestone 5 vulnerability-card and skill-graph contracts, beginning
  with the proposed IDOR/BOLA update.
- Keep the test-fixture attestation distinct from human evidence in every UI
  and export.
- Design persisted validator/receipt trust before any cross-process or network
  executor is considered.

## Process and storage closeout

- System-drive free space was 12.81 GiB (5.39%) at continuation preflight and
  13.21 GiB (5.56%) before governed-record writeback; final closeout was
  12.62 GiB (5.31%), above both reporting thresholds but still close to the
  percentage boundary.
- `python -m chaseos audit storage --apply --require-headroom` was attempted and
  unavailable because the active Python environment has no `chaseos` module;
  no broad or ambiguous cleanup was substituted.
- The current private proof is 0.05 MiB. The first automatically-attested proof
  was moved, intact and recoverable, to a clearly named `superseded-auto-attestation`
  directory before the explicit-input proof replaced it.
- The final prepared-site acceptance used owned preview root PID 23912 and
  descendants 24724, 20112, 33576, and 14900. The 56-test suite passed; all
  owned PIDs were stopped leaf-first and verified absent. A later port-4321
  listener was traced to unrelated `chaseintech-growth-ops` PID 32836 and left
  untouched.

## Next recommended pass

Implement the Milestone 5 vulnerability-card schema, evidence thresholds,
falsifiable templates, and six-dimensional mastery state. Consume the proposed
IDOR/BOLA update only after those contracts pass focused and full tests.

## Links

- [Documentation history](../../99_ARCHIVE/Documentation-History/2026-08-09_local-two-account-slice.md)
- [Daily note](../Daily/2026-08-09.md)
- [Agent activity](../Agent-Activity/2026-08-09-codex-local-two-account-slice.md)
- [Prepared site sync](../../../chaseintech-personal-site/07_LOGS/Build-Logs/2026-08-09-ChaseOS-greytheory-local-slice-sync.md)
