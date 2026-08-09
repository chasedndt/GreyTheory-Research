# GreyTheory Autonomy Model

> **Status:** CANONICAL boundary; higher levels remain PLANNED.
>
> **Effective:** 2026-08-09

## Principle

GreyTheory supports bounded autonomy inside a human-authorised research envelope. Autonomy changes who prepares or performs an already-permitted step. It never changes who grants authority, decides validity, submits, contacts a programme, or discloses.

## Autonomy ladder

| Level | Description | Status |
|---|---|---|
| A0 — Record only | Human performs work; GreyTheory records it | LIVE |
| A1 — Copilot | AI explains, organises, critiques, drafts, and tutors | DESIGNED; model gateway not built |
| A2 — Local autonomous analysis | Approved local collectors and validators operate on fixtures/files | PARTIAL |
| A3 — Bounded passive research | Approved unauthenticated reads in a strict envelope | PLANNED |
| A4 — Bounded authenticated research | Controlled-account workflows under reviewed plans | PLANNED |
| A5 — Per-experiment intrusive work | Individually approved constrained action | EXCEPTIONAL / PLANNED |
| Outside the ladder | Scope verification, validity, submission, contact, disclosure | ALWAYS HUMAN |

The current operating ceiling is `LOCAL_FIXTURE`, regardless of any contract's nominal authority.

## Effective authority

An action is permitted only by the intersection of:

```text
global posture ceiling
∩ deployment policy
∩ verified programme contract
∩ workspace policy
∩ session budget
∩ plugin capability manifest
∩ identity permissions
∩ action-specific approval
```

No component may expand another. A denial is final for that request.

## AI roles

One orchestrator may initially assume explicit roles: Policy Analyst, Cartographer, Hypothesis Analyst, Experiment Planner, Sceptical Critic, Evidence Curator, Report Drafter, Tutor, and Postmortem Analyst. Splitting roles into processes is justified only by privilege separation or scale.

The Executor is deterministic infrastructure, not an AI role.

## Research envelope

Every autonomous run must eventually receive an integrity-protected envelope containing the contract fingerprint, workspace/session IDs, canonical targets, allowed actions, identity handles, data classes, request/time/cost budgets, redirect and DNS policy, side-effect limits, stop conditions, expiry, approval reference, and single-use nonce.

## Non-negotiable refusals

A model cannot:

- grant or verify authority;
- interpret missing authority optimistically;
- use arbitrary shell, browser, or HTTP access;
- see raw credentials where a handle is sufficient;
- create or consume an approval on its own behalf;
- promote inference to proof;
- submit, disclose, or communicate externally.
