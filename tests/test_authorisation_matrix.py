"""The role-object-action matrix: owned things only, controls for denials, review per family."""

from __future__ import annotations

import pytest

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

A, B, ADMIN = "identity-user-a", "identity-user-b", "identity-admin"
MANIFEST = {
    "fixture_id": "two-account-v1",
    "controlled_identities": [A, B, ADMIN],
    "objects": {"object-user-a": A, "object-user-b": B, "object-admin": ADMIN},
}
ROLES = {A: "user", B: "user", ADMIN: "admin"}
BUDGET = {f: 10 for f in TestFamily}


def _matrix(*cells):
    return Matrix("two-account-v1", ROLES, cells)


def _full():
    return _matrix(
        Cell(A, "object-user-a", "read", Expectation.ALLOW),
        Cell(B, "object-user-b", "read", Expectation.ALLOW),
        Cell(ADMIN, "object-admin", "read", Expectation.ALLOW),
        Cell(A, "object-user-b", "read", Expectation.DENY),
        Cell(A, "object-admin", "read", Expectation.DENY),
        Cell(ANONYMOUS, "object-user-a", "read", Expectation.DENY),
    )


def test_families_are_derived_from_ownership_and_roles():
    p = plan(_full(), MANIFEST, BUDGET)
    fam = {(i.cell.identity_id, i.cell.object_id): i.family for i in p.intents}

    assert fam[(A, "object-user-a")] is TestFamily.OWN
    assert fam[(A, "object-user-b")] is TestFamily.HORIZONTAL
    assert fam[(A, "object-admin")] is TestFamily.VERTICAL
    assert fam[(ANONYMOUS, "object-user-a")] is TestFamily.UNAUTHENTICATED


def test_every_denial_carries_its_owner_control_and_costs_two_requests():
    p = plan(_full(), MANIFEST, BUDGET)
    denial = next(i for i in p.intents if i.cell.identity_id == A and i.cell.object_id == "object-user-b")

    assert denial.control == Cell(B, "object-user-b", "read", Expectation.ALLOW)
    assert denial.request_cost == 2
    assert p.cost_by_family()[TestFamily.HORIZONTAL] == 2


def test_a_denial_without_an_owner_control_is_refused():
    m = _matrix(Cell(A, "object-user-b", "read", Expectation.DENY))
    with pytest.raises(MatrixError, match="proves nothing"):
        plan(m, MANIFEST, BUDGET)


def test_an_uncontrolled_identity_or_object_is_refused():
    with pytest.raises(MatrixError, match="not a controlled identity"):
        Matrix("two-account-v1", {"identity-stranger": "user"}, ()).validate(MANIFEST)
    m = _matrix(Cell(A, "object-elsewhere", "read", Expectation.DENY))
    with pytest.raises(MatrixError, match="not in the ownership record"):
        m.validate(MANIFEST)


def test_an_object_owned_by_an_uncontrolled_identity_is_refused():
    manifest = dict(MANIFEST, objects={**MANIFEST["objects"], "object-x": "identity-stranger"})
    m = _matrix(Cell(A, "object-x", "read", Expectation.DENY))
    with pytest.raises(MatrixError, match="uncontrolled identity"):
        m.validate(manifest)


def test_a_manifest_for_another_fixture_is_refused():
    with pytest.raises(MatrixError, match="different fixtures"):
        _full().validate(dict(MANIFEST, fixture_id="other"))


def test_duplicate_cells_are_refused():
    m = _matrix(Cell(A, "object-user-a", "read", Expectation.ALLOW), Cell(A, "object-user-a", "read", Expectation.DENY))
    with pytest.raises(MatrixError, match="duplicate"):
        m.validate(MANIFEST)


def test_over_budget_refuses_rather_than_trimming():
    with pytest.raises(MatrixError, match="reduce the matrix"):
        plan(_full(), MANIFEST, dict(BUDGET, **{TestFamily.HORIZONTAL: 1}))
    with pytest.raises(MatrixError, match="no request budget"):
        plan(_full(), MANIFEST, {TestFamily.OWN: 10})


def test_nothing_is_executable_until_every_family_is_reviewed():
    p = plan(_full(), MANIFEST, BUDGET)
    assert not p.executable

    for fam in (TestFamily.OWN, TestFamily.HORIZONTAL, TestFamily.VERTICAL):
        p = review_family(p, fam, "operator:chase")
    assert not p.executable, "unauthenticated family not yet reviewed"

    p = review_family(p, TestFamily.UNAUTHENTICATED, "operator:chase")
    assert p.executable
    assert all(i.reviewed_by == "operator:chase" for i in p.intents)


def test_a_review_must_name_the_reviewer_and_an_existing_family():
    p = plan(_full(), MANIFEST, BUDGET)
    with pytest.raises(MatrixError, match="name the reviewer"):
        review_family(p, TestFamily.OWN, " ")
    only_own = plan(_matrix(Cell(A, "object-user-a", "read", Expectation.ALLOW)), MANIFEST, BUDGET)
    with pytest.raises(MatrixError, match="no vertical intents"):
        review_family(only_own, TestFamily.VERTICAL, "operator:chase")
