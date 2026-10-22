"""Bind a reviewed authorisation matrix plan to research-domain experiments.

One ``ExperimentPlan`` per test family. The matrix supplies what it knows -
ordered actions, positive controls (owner ALLOW cells), negative controls
(DENY cells), expected outcomes, and the family's request budget as the
effect budget. What it does not know it refuses to invent: rollback steps,
stop conditions and the evidence plan come from the caller, because "there is
nothing to roll back" is a judgement about the fixture that only the operator
who built it can make.

A plan that has not been reviewed in every family does not bind. The domain
record carries ``required_authority = AUTHENTICATED`` regardless of family:
the unauthenticated family still runs *against* owned accounts' objects inside
the authenticated lab, and the posture is about the lab, not the request.
"""

# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 ChaseInTech

from __future__ import annotations

from dataclasses import dataclass

from greytheory.authority.gate import AuthorityLevel
from greytheory.lab.authorisation_matrix import (
    Cell,
    Expectation,
    ExperimentIntent,
    MatrixError,
    Plan,
    TestFamily,
)
from greytheory.research.domain import EffectBudget, ExperimentPlan, ExperimentStatus

REQUEST_EFFECT = "requests"


@dataclass(frozen=True)
class BindingContext:
    workspace_id: str
    session_id: str
    hypothesis_id: str
    authority_ref: str
    """The verified ``ScopeContract.fingerprint()`` - a lowercase SHA-256. The
    domain refuses anything else, so an experiment can never be bound to a
    contract that was not compiled and reviewed."""
    rollback_steps: tuple[str, ...]
    stop_conditions: tuple[str, ...]
    evidence_plan: tuple[str, ...]
    required_authority: AuthorityLevel = AuthorityLevel.AUTHENTICATED
    """``AUTHENTICATED`` for a real programme lab. ``LOCAL_FIXTURE`` when the
    target is the synthetic two-account fixture, whose gate runs under that
    ceiling; the fixture is not a programme asset and must not be requested as
    one."""


def _describe(cell: Cell) -> str:
    return f"{cell.identity_id} {cell.action} {cell.object_id} -> expect {cell.expectation.value}"


def _outcome(intent: ExperimentIntent) -> str:
    c = intent.cell
    if c.expectation is Expectation.ALLOW:
        return f"{c.identity_id} is served {c.object_id} on {c.action} (owner control)"
    return (
        f"{c.identity_id} is refused {c.action} on {c.object_id} while its owner "
        f"{intent.control.identity_id} is served the same request"
    )


def bind(plan: Plan, ctx: BindingContext) -> dict[TestFamily, ExperimentPlan]:
    """Produce one domain experiment per family, or refuse."""

    if not plan.executable:
        unreviewed = sorted({i.family.value for i in plan.intents if not i.executable})
        raise MatrixError(f"plan is not fully reviewed; unreviewed families: {unreviewed}")

    out: dict[TestFamily, ExperimentPlan] = {}
    for family in TestFamily:
        intents = [i for i in plan.intents if i.family is family]
        if not intents:
            continue
        positives = [_describe(i.control) for i in intents if i.control is not None]
        positives += [_describe(i.cell) for i in intents if i.cell.expectation is Expectation.ALLOW]
        negatives = [_describe(i.cell) for i in intents if i.cell.expectation is Expectation.DENY]
        # The domain insists every experiment names both kinds of control. A
        # family made only of owner ALLOW cells has no negative; say so in
        # words rather than fabricate one.
        if not negatives:
            negatives = ["none: this family is the owner control set, exercised for comparison"]
        if not positives:
            raise MatrixError(f"family {family.value} has no positive control; the planner should have refused")

        budget = plan.budget.get(family)
        if budget is None:
            raise MatrixError(f"family {family.value} has no request budget")

        out[family] = ExperimentPlan(
            id=f"exp-matrix-{plan.fixture_id}-{family.value}",
            workspace_id=ctx.workspace_id,
            session_id=ctx.session_id,
            hypothesis_id=ctx.hypothesis_id,
            authority_ref=ctx.authority_ref,
            ordered_actions=tuple(_describe(i.cell) for i in intents),
            positive_controls=tuple(dict.fromkeys(positives)),
            negative_controls=tuple(dict.fromkeys(negatives)),
            expected_outcomes=tuple(_outcome(i) for i in intents),
            required_authority=ctx.required_authority,
            effect_budget=EffectBudget.from_mapping({REQUEST_EFFECT: budget}),
            rollback_steps=ctx.rollback_steps,
            stop_conditions=ctx.stop_conditions,
            evidence_plan=ctx.evidence_plan,
            status=ExperimentStatus.READY,
            outcome_summary=f"reviewed by {intents[0].reviewed_by}; family {family.value}",
        )
    return out
