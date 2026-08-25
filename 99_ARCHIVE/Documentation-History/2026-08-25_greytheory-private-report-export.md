# Documentation History - GreyTheory Private Redacted Report Export

- Date: 2026-08-25
- Runtime: Codex / Axiom-Codex
- Status: PARTIAL and VERIFIED locally

## Historical change

The workbench application gained a private report-export path without gaining
a submission path. It exports only a server-held report-ready finding/draft and
the evidence vault's complete integrity-checked redacted package. The operator
acknowledges a fresh immutable export identifier; the UI cannot supply report
prose, an evidence subset, or a filesystem path.

The atomic package contains Markdown, structured JSON, copied redacted evidence,
and a digest manifest that records `submission_performed: false`. Report
authoring persistence and the graphical journey remain separate open work.

## Links

- [Build log](../../07_LOGS/Build-Logs/2026-08-25-greytheory-private-report-export.md)
- [Daily note](../../07_LOGS/Daily/2026-08-25.md)
- [Agent activity](../../07_LOGS/Agent-Activity/2026-08-25-codex-greytheory-private-report-export.md)
- [Workbench architecture](../../Docs/workbench-architecture.md)
