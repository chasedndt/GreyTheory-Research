# PROJECT STATE

## Project
GreyTheory AI

## Subtitle
Proof-First Security Research

## Current Phase
Security Research Product Lane incubation — local-only / repo-docs / safe-demo proof

## Locked Decisions
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
- exact tool stack per lane
- validation evidence schema
- crawl/recon architecture
- graph/memory layer choice
- reporting format
- observability/logging design
- what human review gates are mandatory
- how AI-app testing will be isolated and validated safely

## Immediate Next Step
Generate and refine the core project documentation inside `/docs` before any code scaffolding begins.

## Do Not Do Yet
- no full repo scaffolding
- no exploit automation assumptions
- no giant monolithic agent
- no coding before documentation review
- no unsafe autonomous behavior

## Source of Truth
Current repo docs are the source of truth for architecture decisions.
