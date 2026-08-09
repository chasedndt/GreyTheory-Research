# Documentation History - Local Two-Account Slice

- Date: 2026-08-09
- Runtime: Codex
- Type: implementation, verification, and documentation reconciliation
- Status: COMPLETE and VERIFIED locally

## Historical change

This pass moved GreyTheory from a persistence-only research domain at
Milestone 3 to its first complete end-to-end local research demonstration at
Milestone 4. It also replaced caller-asserted claim promotion with a
validator-issued receipt path and made claim/evidence provenance explicit in
reports.

The implementation uses only a deliberately vulnerable in-memory two-account
fixture. Acceptance review and attestations are explicitly labelled
`test_fixture`; no human judgement, live target, real finding, submission, or
programme outcome is claimed. Milestone 5 is now current, and the generated
IDOR/BOLA card update remains a proposal until that system exists.

## Surfaces affected

- Check receipt, local execution, fixture, and vertical-slice modules
- Provenance, report, validation, CLI, and static-collector boundary docs
- Milestone 4 fixtures and tests
- Canonical definition, state, domain, roadmap, threat, validation, diagrams,
  contributor guidance, and accepted ADR status
- Prepared ChaseInTech project/build-log copy on its own local branch

## Links

- [Build log](../../07_LOGS/Build-Logs/2026-08-09-ChaseOS-local-two-account-slice.md)
- [Daily note](../../07_LOGS/Daily/2026-08-09.md)
- [Agent activity](../../07_LOGS/Agent-Activity/2026-08-09-codex-local-two-account-slice.md)
- [Roadmap](../../Docs/roadmap.md)
- [Domain model](../../DOMAIN_MODEL.md)
