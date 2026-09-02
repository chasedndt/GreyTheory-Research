# Prototype Instructions

Run the local server yourself and open the preview in the browser available to this environment. Do not give the user server-start instructions when you can run it.

Before making substantial visual changes, use the Product Design plugin's `get-context` skill when the visual source is unclear or no longer matches the current goal. When the user gives durable prototype-specific design feedback, preferences, or decisions, record them in `AGENTS.md`.

When implementing from a selected generated mock, treat that image as the source of truth for layout, component anatomy, density, spacing, color, typography, visible content, and hierarchy.

Build app UI in `src/`. Keep `.openai/hosting.json`, `worker/index.js`, `scripts/prepare-sites-build.mjs`, and `tests/sites-worker.test.mjs` intact so the same local prototype can be handed to Sites. Before a Sites handoff, run `npm run build` and `npm run test:sites`; the build must leave `dist/client/index.html`, `dist/server/index.js`, and `dist/.openai/hosting.json`.

## Durable design decision

On 2026-08-31 the operator selected visual direction 1, **Research Ledger**.
Preserve its dense chronological evidence ledger, persistent governance context,
right-side evidence inspector, navy/amber visual language, and explicit
`LOCAL_FIXTURE`/unproven/no-live-target wording unless the operator changes the
direction. The prototype must never imply authority or target execution.

On 2026-09-01 the operator changed the direction: the Research Ledger remains a
first-class case view, but it is no longer the accepted dashboard shell. The
next shell must be modern, learner-first, responsive, and designed for an
AI-native security researcher and bug-bounty learner. It must surface a guided
learning loop, explain recommendations, include agent-security pathways and
useful evidence/skill visualisations, keep AI advisory and human-governed, and
pass desktop plus 390-pixel visual QA without horizontal clipping.

The operator selected direction 1, **Guided Mission Control**, as the production
shell. Use its calm mission-first hierarchy and learner loop, while incorporating
direction 2's focused lesson and skill map plus direction 3's case canvas,
evidence-quality, and competency views. The first complete teaching case is the
LOCAL_FIXTURE-only Agent Tool Authorization Boundary scenario. It must teach
traditional access control and ethical research alongside AI-native risks such
as indirect prompt injection, excessive agency, consent, context isolation, and
tool authorization. Guided completion is practice, not mastery; AI remains
advisory and human assessment remains explicit.

On 2026-09-02 the operator accepted the current shell and asked for a complete,
interactive learning-path pass. Skill-trajectory nodes must be focusable and
selectable, hover/focus must explain each lesson, and previewed nodes must never
masquerade as earned mastery. Every topic must own distinct notes, principles,
traditional/AI lenses, checkpoints, and a beginner-to-transfer roadmap. Keep all
thirteen product panels represented in navigation. Public intelligence belongs
in read-only, source-preserving contracts; authenticated bug-bounty connectors
remain dark until credentials, account authority, and the external-worker gate
are separately accepted.

The 2026-09-02 release-media pass is the current visual source for repository
and ChaseInTech presentation. Same-origin browser acceptance proves an assigned
lesson persists across reload, and route navigation must continue to focus the
selected workspace while respecting reduced-motion preferences. Do not mark the
whole accessibility gate complete until sequential-keyboard and clean-user
Windows package acceptance have separately passed.
