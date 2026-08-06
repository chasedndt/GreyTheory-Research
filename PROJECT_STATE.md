# PROJECT STATE

## Project
GreyTheory AI

## Subtitle
Proof-First Security Research

## Definition
GreyTheory AI is a proof-first security research control plane. It converts authorisation into evidence — and refuses to move without either.

Canonical: `Docs/definition.md`. It outranks `README.md` and `Docs/architecture.md`.

## Current Phase
Security Research Product Lane incubation — local-only. Authority Plane (Plane 1) is the active build target.

## Locked Decisions
- Three ranked planes: **Authority** (root, fail-closed) → **Signal** (four lanes as pluggable collectors) → **Judgement** (operator loop). Lower planes cannot bypass higher ones.
- The Authority Plane is the product. Detection is commodity and replaceable.
- A lane observes and emits signals; it may not promote its own output past `contextual`.
- One finding entity, one lifecycle, spanning internal states and recorded external programme states.
- Every claim is tagged `observed` | `checked` | `inferred`. No silent promotion between them.
- Every artifact carries an authority reference. No reference, no vault entry.
- The system never marks a finding valid, accepted, rewarded, or disclosed — only programmes produce those states.
- Zero-income and zero-finding hours are recorded with equal fidelity.
- Grapevine AI attaches to Planes 1 and 3 only, information-only, never to Plane 2.
- **GreyTheory is standalone and Apache-2.0.** Zero runtime dependencies; fully functional with no ChaseOS present. ChaseOS is an optional adapter, never a requirement, and every integration point ships a self-sufficient default beside it.
- Raw evidence never enters a git working tree — enforced by a guard, not a `.gitignore` entry.
- Only redacted evidence may be exported, and export is all-or-nothing.
- Build substrate: local-first Python package with tests, no network in the core.
- Public copy may not describe an Aspirational component as working. Capability register in `Docs/definition.md` §6 governs all claims.
- GreyTheory AI × ChaseOS is a Business + GTM incubation lane, not yet a standalone business.
- The lane exists to build proof in agent systems, cybersecurity, and agentic-system defense.
- No external scanning, unauthorized testing, live target interaction, exploit publication, disclosure/outreach, credential validation, or public claims without explicit operator approval.
- Modular four-lane design remains the long-term architecture.
- LLM is planner/triager/reasoner, not the raw exploit engine.
- Deterministic validation is required before a finding is treated as real.
- System must support both learning value and practical bug bounty usefulness, but current work stays local/repo/demo-only.
- Prefer proof-first workflows over maximum autonomy.
- Prioritize low false positives and reproducible evidence.
- SSRF is deferred from V1 unless tightly controlled.

## Core Lanes
1. Known-Vuln Lane
2. Exposure Lane
3. Web Vuln Lane
4. AI-App Lane

## V1 Direction
Prioritize:
- known-vuln lane
- exposure lane
- core web vuln lane

AI-app lane should be designed from the start but may be partially phased depending on implementation complexity.

## Open Decisions
Tracked in `Docs/open-questions.md`. Blocking: Grapevine AI reconciliation (O1), ChaseOS approval/audit/graph reconciliation (O2), evidence storage location (O3).

Deferred until Plane 1 exists: exact tool stack per lane, crawl/recon architecture, graph/memory layer, reporting format, AI-app test isolation.

## Built
Authority Plane V0 — `greytheory/` package, 87 tests, zero runtime dependencies, no network surface (CI-enforced).
Scope compiler (fails closed), execution gate (11 denial reasons + posture ceiling + kill switch), hash-chained audit log, provenance triple, finding lifecycle, operator CLI. Proof fixtures for both a clean and a deliberately blocked programme.

## Immediate Next Step
O2 and O3 both answered. Evidence vault is live.

Next: validation gates B–F (reproducibility, impact, evidence completeness, duplicate risk, report quality) over the vault, then the report studio. Dashboard read model waits on the operator's panel specification (O10).

## Do Not Do Yet
- no exploit automation assumptions
- no giant monolithic agent
- no unsafe autonomous behavior
- no lane implementation before the Authority Plane can gate it
- no external network calls in the core package
- no duplicate approval/audit/graph system until O2 is answered

## Source of Truth
Current repo docs are the source of truth for architecture decisions.
