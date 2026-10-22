"""ActionRequest emission: one per intent and control, traceable, budget-exact."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from greytheory.authority.gate import AuthorityLevel
from greytheory.lab.action_emission import emit
from greytheory.lab.authorisation_matrix import MatrixError, TestFamily
from greytheory.lab.matrix_binding import bind
from greytheory.research.domain import ActionRequest
from tests.test_matrix_binding import CTX, _plan, _reviewed

ASSETS = {"object-user-a": "asset-obj-a", "object-user-b": "asset-obj-b"}
NOW = datetime(2026, 9, 12, 1, 0, tzinfo=timezone.utc)


def _emit(plan=None):
    p = plan or _reviewed()
    return emit(p, bind(p, CTX), CTX, asset_ids=ASSETS, created_at=NOW)


def test_a_denial_emits_its_control_first_then_the_probe():
    reqs = _emit()[TestFamily.HORIZONTAL]

    assert len(reqs) == 2
    assert reqs[0].identity_id == "identity-user-b" and "(control)" in reqs[0].exact_action
    assert reqs[1].identity_id == "identity-user-a" and "(probe)" in reqs[1].exact_action
    assert reqs[1].target_asset_id == "asset-obj-b"


def test_anonymous_probes_carry_no_identity():
    reqs = _emit()[TestFamily.UNAUTHENTICATED]
    probe = next(r for r in reqs if "(probe)" in r.exact_action)
    assert probe.identity_id is None


def test_every_request_is_one_question_with_no_presumed_approval():
    for family, reqs in _emit().items():
        for r in reqs:
            assert r.max_requests == 1
            assert r.expected_effects.value("requests") == 1
            assert r.approval_ref is None
            assert r.required_authority is AuthorityLevel.AUTHENTICATED
            assert r.technique == family.value


def test_requests_reconcile_exactly_with_the_experiment_budget():
    p = _reviewed()
    exps = bind(p, CTX)
    reqs = emit(p, exps, CTX, asset_ids=ASSETS, created_at=NOW)
    for family, rs in reqs.items():
        assert len(rs) == p.cost_by_family()[family]
        assert len(rs) <= exps[family].effect_budget.value("requests")


def test_an_unmapped_object_is_refused_rather_than_guessed():
    with pytest.raises(MatrixError, match="refusing to guess"):
        emit(_reviewed(), bind(_reviewed(), CTX), CTX, asset_ids={"object-user-a": "asset-obj-a"}, created_at=NOW)


def test_an_unreviewed_plan_emits_nothing():
    with pytest.raises(MatrixError, match="no requests are emitted"):
        emit(_plan(), {}, CTX, asset_ids=ASSETS, created_at=NOW)


def test_requests_round_trip_through_the_domain_serialiser():
    for reqs in _emit().values():
        for r in reqs:
            assert ActionRequest.from_dict(r.to_dict()) == r
