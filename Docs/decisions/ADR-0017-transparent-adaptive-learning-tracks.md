# ADR-0017: Keep adaptive learning transparent and assistance bounded

**Status:** Accepted

**Date:** 2026-08-26

## Context

GreyTheory already persisted evidence-bound human mastery and deterministic
five-stage learning journeys. It did not adapt review timing to demonstrated
retention, distinguish assisted work from independent work, or require a new
context before awarding transfer evidence. Adding those features through hidden
model scoring would weaken the project's central rule: a model may help the
operator reason, but it cannot create proof or award mastery.

## Decision

GreyTheory adopts an inspectable learning policy with three bounded tracks:

1. `adaptive-evidence-review-v1` considers only earlier credited human
   assessments for the same card and mastery dimension;
2. first assessment uses the existing level base interval; one retained or
   improved assessment extends it by 50 percent; two or more consecutive
   retained or improved assessments double it, capped at 180 days; regression
   halves the base interval, with a three-day floor;
3. test-fixture assessments remain visible but never influence adaptation;
4. every generated schedule records its policy reference, interval,
   adjustment, history count, and plain-language rationale; an operator may
   still set a date explicitly, which is persisted as `operator-set-v1`;
5. `standard` journeys retain the existing unassisted contract;
6. `assisted` journeys expose explicit guidance, but their final human
   assessment cannot claim `independent` or `transferable` mastery; and
7. `transfer` journeys require operator selection, independent `test` and
   `prove` foundations, the transfer dimension, and a distinct local context
   reference cited by both proof evidence and the persisted human assessment.

The CLI and transport-neutral application service use the same domain policy.
Journey completion still requires a separately persisted human assessment and
never executes a fixture, contacts a target, promotes a claim, or changes
research posture.

## Consequences

- Review timing can respond to retained or regressed evidence without hidden
  scoring or model authority.
- Assisted work remains useful while being structurally prevented from
  masquerading as independent performance.
- Transfer means applying an invariant in a distinct context, not replaying the
  original fixture receipt.
- Old stored assessments and journeys remain readable through default policy
  and `standard` track fields.
- The broader curriculum, graphical Learn surface, visual workbench, and any
  automatic mastery decision remain outside this decision and unbuilt.
- `LOCAL_FIXTURE` remains the operating posture.
