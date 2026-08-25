# Documentation History - GreyTheory Authenticated Local Transport

- Date: 2026-08-25
- Runtime: Codex / Axiom-Codex
- Status: PARTIAL and VERIFIED locally

## Historical change

The Windows-first workbench gained a real launch boundary without gaining a
graphical shell or target access. `greytheory_local` assembles private stores
outside Git and carries versioned application snapshots/commands over a strict,
authenticated numeric-loopback JSON endpoint.

ADR-0012 treats local web access as a security boundary: exact Host, an
in-memory token, exact-origin writes, no CORS, bounded bodies, and unambiguous
JSON/framing are mandatory. The result is a foundation for the selected shell,
not a claim that the dashboard is finished or installable.

## Links

- [Build log](../../07_LOGS/Build-Logs/2026-08-25-greytheory-authenticated-local-transport.md)
- [Daily note](../../07_LOGS/Daily/2026-08-25.md)
- [Agent activity](../../07_LOGS/Agent-Activity/2026-08-25-codex-greytheory-authenticated-local-transport.md)
- [ADR-0012](../../Docs/decisions/ADR-0012-authenticated-numeric-loopback-workbench.md)
- [Workbench architecture](../../Docs/workbench-architecture.md)
