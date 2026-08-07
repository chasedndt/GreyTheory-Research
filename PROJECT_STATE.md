# PROJECT STATE

## Project
GreyTheory AI

## Subtitle
Proof-First Security Research

## Definition
GreyTheory AI is a proof-first security research control plane. It converts authorisation into evidence — and refuses to move without either.

Canonical: `Docs/definition.md`. It outranks `README.md` and `Docs/architecture.md`.

## Current Phase
Roadmap Phase 3 - real programmes. Local-only posture. Authority, Judgement and the offline Signal Plane collectors are built.

## Locked Decisions
- Three ranked planes: **Authority** (root, fail-closed) → **Signal** (four lanes as pluggable collectors) → **Judgement** (operator loop). Lower planes cannot bypass higher ones.
- The Authority Plane is the root and the defensible layer; detection is commodity and replaceable. It governs the operator's own research — it is not a governance product for other people's systems.
- A lane observes and emits signals; it may not promote its own output past `contextual`.
- One finding entity, one lifecycle, spanning internal states and recorded external programme states.
- Every claim is tagged `observed` | `checked` | `inferred`. No silent promotion between them.
- Every artifact carries an authority reference. No reference, no vault entry.
- The system never marks a finding valid, accepted, rewarded, or disclosed — only programmes produce those states.
- Zero-income and zero-finding hours are recorded with equal fidelity.
- **Purpose: a bug bounty and authorised security research engine.** The Authority Plane governs the operator's own research. Governance offerings for other people's agents are derivative products, not this system.
- External intelligence (Scope Watch, roadmap Phase 5) is information-only and never reaches Plane 2.
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
Tracked in `Docs/open-questions.md`. O2 (ChaseOS reconciliation) and O3 (evidence location) are resolved. Remaining: ChaseOS audit tamper-evidence (O9), and raising the posture ceiling (roadmap Phase 6).

Deferred until the Signal Plane is built: exact tool stack per lane, crawl/recon architecture, AI-app test isolation.

## Built
The full path from authorisation to a validated report draft. `greytheory/` package, 317 tests, zero runtime dependencies, no network surface (CI-enforced).

Programme registry (versioning, source snapshots, drift detection), scope compiler (fails closed), execution gate (17 denial reasons + posture ceiling + kill switch), operator approvals (bound, expiring, single-use), hash-chained audit log, provenance triple, evidence vault (raw/redacted split, repo guard), validation gates B-F, report studio, triage and earnings ledger, finding lifecycle, operator dashboard, Signal Plane lane framework with three static offline collectors (Lanes 1, 2 and 4), CLI.

Architecture articulated in `Docs/system-overview.md`.

## Immediate Next Step
Phase 3 of `Docs/roadmap.md`: compile real programme rules and fix what breaks. Costs nothing, risks nothing, and tests the compiler against reality rather than fixtures we wrote. Phase 4 (advisory sourcing, vulnerability cards, curriculum, hypothesis engine) follows and is also offline. Phase 6 - raising the posture ceiling - is the operator decision that unlocks network collectors.

## Do Not Do Yet
- no exploit automation assumptions
- no giant monolithic agent
- no unsafe autonomous behavior
- no network collector inside greytheory/ - the runner refuses them
- no external network calls in the core package
- no duplicate approval/audit/graph system - ChaseOS owns these, GreyTheory adapts

## Source of Truth
Current repo docs are the source of truth for architecture decisions.
