# Documentation History - GreyTheory Local-Fixture Action Intent

- Date: 2026-08-25
- Runtime: Codex / Axiom-Codex
- Status: PARTIAL and VERIFIED locally

## Historical change

The workbench application gained its final previously refused typed command: a
bounded `LOCAL_FIXTURE` action intent. The UI can name a configured active
experiment and propose its exact planned fixture action, purpose, and bounded
effects. The service derives all authority-bearing context from persisted state
and records only an `ActionRequest`.

This is not an execution path. It creates no approval, Gate decision, action
receipt, fixture invocation, process, or network request. The graphical review
and decision/receipt presentation remain unbuilt.

## Links

- [Build log](../../07_LOGS/Build-Logs/2026-08-25-greytheory-local-action-intent.md)
- [Daily note](../../07_LOGS/Daily/2026-08-25.md)
- [Agent activity](../../07_LOGS/Agent-Activity/2026-08-25-codex-greytheory-local-action-intent.md)
- [Workbench architecture](../../Docs/workbench-architecture.md)
