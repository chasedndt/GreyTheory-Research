# Safe Local Demo / Proof Plan

> Goal: produce postable, defensive proof without touching live targets.

## Demo 1 — Agent Authority Boundary Toy App

**Purpose:** show how an agent should refuse or route high-authority actions.

Local fixture examples:

- `send_customer_email` mocked action
- `publish_blog_post` mocked action
- `scan_external_target` mocked action
- `read_local_repo_docs` allowed action

Proof output:

- policy decision table
- audit JSONL sample
- safe/blocked action transcript
- README screenshot or terminal output

## Demo 2 — Prompt-Injection Guardrail Fixture

**Purpose:** show how external text is treated as untrusted data, not instructions.

Local fixture examples:

- malicious README snippet
- fake support ticket containing tool-use instructions
- docs page asking the agent to reveal secrets

Proof output:

- red-team prompt fixture
- expected defensive response
- policy explanation
- mitigation checklist

## Demo 3 — Security Report Evidence Schema

**Purpose:** demonstrate evidence-backed findings without real targets.

Local fixture examples:

- intentionally vulnerable local config file
- fake dependency manifest with known-version metadata
- mock finding JSONL

Proof output:

- finding taxonomy example
- deterministic check result
- human review gate state
- report draft clearly marked fictional/local-only

## Verification standard

Every demo must include:

- no external network target
- no real credentials
- no real customer or third-party data
- explicit local-only banner
- reproducible command or screenshot
- public-safe summary
- approval checklist for anything beyond local proof
