"""Binding a reviewed matrix plan to ExperimentPlan records."""

from __future__ import annotations

import pytest

from greytheory.authority.gate import AuthorityLevel
from greytheory.lab.authorisation_matrix import (
    ANONYMOUS,
    Cell,
    Expectation,
    Matrix,
    MatrixError,
    TestFamily,
    plan,
    review_family,
)
from greytheory.lab.matrix_binding import BindingContext, bind
from greytheory.research.domain import ExperimentStatus, ResearchDomainError

A, B = "identity-user-a", "identity-user-b"
MANIFEST = {
    "fixture_id": "two-account-v1",
    "controlled_identities": [A, B],
    "objects": {"object-user-a": A, "object-user-b": B},
}
CTX = BindingContext(
    workspace_id="ws-lab", session_id="sess-1", hypothesis_id="hyp-bola-1",
    # The domain requires a verified contract fingerprint, not a label.
    authority_ref="c" * 64,
    rollback_steps=("fixture is in-memory; discard it",),
    stop_conditions=("any 5xx", "any response naming an identity outside the manifest"),
    evidence_plan=("record request and response bytes per intent",),
)


def _plan():
    m = Matrix("two-account-v1", {A: "user", B: "user"}, (
        Cell(A, "object-user-a", "read", Expectation.ALLOW),
        Cell(B, "object-user-b", "read", Expectation.ALLOW),
        Cell(A, "object-user-b", "read", Expectation.DENY),
        Cell(ANONYMOUS, "object-user-a", "read", Expectation.DENY),
    ))
    return plan(m, MANIFEST, {f: 8 for f in TestFamily})


def _reviewed():
    p = _plan()
    for f in (TestFamily.OWN, TestFamily.HORIZONTAL, TestFamily.UNAUTHENTICATED):
        p = review_family(p, f, "operator:chase")
    return p


def test_an_unreviewed_plan_does_not_bind():
    with pytest.raises(MatrixError, match="unreviewed families"):
        bind(_plan(), CTX)


def test_one_ready_experiment_per_family_with_controls_split():
    exps = bind(_reviewed(), CTX)

    assert set(exps) == {TestFamily.OWN, TestFamily.HORIZONTAL, TestFamily.UNAUTHENTICATED}
    h = exps[TestFamily.HORIZONTAL]
    assert h.status is ExperimentStatus.READY
    assert h.required_authority is AuthorityLevel.AUTHENTICATED
    assert any("identity-user-b read object-user-b -> expect allow" in c for c in h.positive_controls)
    assert any("identity-user-a read object-user-b -> expect deny" in c for c in h.negative_controls)
    assert "while its owner identity-user-b is served" in h.expected_outcomes[0]
    assert h.effect_budget.value("requests") == 8
    assert "operator:chase" in h.outcome_summary


def test_the_owner_control_family_states_it_has_no_negative_rather_than_inventing_one():
    own = bind(_reviewed(), CTX)[TestFamily.OWN]
    assert own.negative_controls == ("none: this family is the owner control set, exercised for comparison",)


def test_rollback_and_stop_conditions_come_from_the_caller_and_are_required():
    bad = BindingContext(**{**CTX.__dict__, "rollback_steps": ()})
    with pytest.raises(ResearchDomainError):
        bind(_reviewed(), bad)


def test_experiments_round_trip_through_the_domain_serialiser():
    from greytheory.research.domain import ExperimentPlan

    for exp in bind(_reviewed(), CTX).values():
        assert ExperimentPlan.from_dict(exp.to_dict()) == exp
