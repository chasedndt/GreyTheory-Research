"""Emit one ``ActionRequest`` per matrix intent, and one per paired control.

A bound experiment says what a family will do; an action request is the unit
the authority gate actually decides on. Emitting them from the plan rather
than by hand means every request traces to a reviewed cell, and the count
sent can be reconciled against the family budget exactly.

Deliberate limits:

* ``approval_ref`` is left ``None``. Review of the *family* happened in the
  matrix; approval of each *request* is the gate's act, recorded when it
  happens, not presumed here.
* ``max_requests`` is 1 per request. A cell is one question; retries are a
  new request with a new id, or they are not made.
* Target asset ids come from the caller's mapping of fixture objects to
  domain ``TargetAsset`` ids. An unmapped object is refused, because a request
  with a guessed target is the exact thing the gate exists to stop.
"""

# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 ChaseInTech

from __future__ import annotations

from datetime import datetime

from greytheory.authority.gate import AuthorityLevel
from greytheory.lab.authorisation_matrix import ANONYMOUS, Cell, MatrixError, Plan, TestFamily
from greytheory.lab.matrix_binding import REQUEST_EFFECT, BindingContext
from greytheory.research.domain import ActionRequest, EffectBudget, ExperimentPlan


def _request(
    *, n: int, cell: Cell, family: TestFamily, role: str, ctx: BindingContext,
    experiment: ExperimentPlan, asset_id: str, created_at: datetime,
) -> ActionRequest:
    return ActionRequest(
        id=f"act-{experiment.id}-{n:03d}",
        workspace_id=ctx.workspace_id,
        session_id=ctx.session_id,
        experiment_id=experiment.id,
        authority_ref=ctx.authority_ref,
        action_type=cell.action,
        exact_action=f"{cell.identity_id} {cell.action} {cell.object_id} ({role})",
        target_asset_id=asset_id,
        identity_id=None if cell.identity_id == ANONYMOUS else cell.identity_id,
        required_authority=ctx.required_authority,
        purpose=f"{family.value} authorisation check; expect {cell.expectation.value}",
        technique=family.value,
        max_requests=1,
        expected_effects=EffectBudget.from_mapping({REQUEST_EFFECT: 1}),
        stop_conditions=ctx.stop_conditions,
        created_at=created_at,
        approval_ref=None,
    )


def emit(
    plan: Plan,
    experiments: dict[TestFamily, ExperimentPlan],
    ctx: BindingContext,
    *,
    asset_ids: dict[str, str],
    created_at: datetime,
) -> dict[TestFamily, tuple[ActionRequest, ...]]:
    """Requests per family, controls first so a denial is never sent unpaired."""

    if not plan.executable:
        raise MatrixError("plan is not fully reviewed; no requests are emitted")

    out: dict[TestFamily, tuple[ActionRequest, ...]] = {}
    for family, experiment in experiments.items():
        reqs: list[ActionRequest] = []
        n = 0
        for intent in (i for i in plan.intents if i.family is family):
            for cell, role in ((intent.control, "control"), (intent.cell, "probe")):
                if cell is None:
                    continue
                asset = asset_ids.get(cell.object_id)
                if asset is None:
                    raise MatrixError(
                        f"no TargetAsset mapped for fixture object {cell.object_id!r}; "
                        "refusing to guess a target"
                    )
                n += 1
                reqs.append(_request(
                    n=n, cell=cell, family=family, role=role, ctx=ctx,
                    experiment=experiment, asset_id=asset, created_at=created_at,
                ))
        budget = experiment.effect_budget.value(REQUEST_EFFECT)
        if len(reqs) > budget:
            raise MatrixError(
                f"family {family.value} would send {len(reqs)} requests against a budget of {budget}"
            )
        out[family] = tuple(reqs)
    return out
