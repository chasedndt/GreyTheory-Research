"""Role-object-action matrix for controlled authorisation testing (Milestone 11).

The matrix is the *expectation*, written down before any request is made:
which controlled identity should be able to perform which action on which
controlled object. Experiments derive from it, not the other way round, so a
result is always compared against something that predates it.

Three rules keep it honest:

* **Every identity and object must appear in the ownership manifest** - the
  record of what the operator actually controls. A cell naming anything else
  is refused, because a test against an uncontrolled account or object is a
  test against someone else's data.
* **Every expected denial needs a paired control** - an ``ALLOW`` cell for the
  same object by its owner. "The other user was denied" means nothing unless
  the owner was served; without the control, a broken endpoint looks secure.
* **Nothing executes without a human reviewing the family.** Planning
  produces intents. Each carries a request cost and a review flag, and the
  review is recorded per test family, never per intent, so a reviewer sees the
  shape of what will be sent rather than approving one request at a time.
"""

# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 ChaseInTech

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field, replace
from enum import Enum

ANONYMOUS = "anonymous"


class Expectation(str, Enum):
    ALLOW = "allow"
    DENY = "deny"


class TestFamily(str, Enum):
    __test__ = False  # the name starts with "Test"; pytest must not collect it

    OWN = "own"
    """Control: the owner acting on their own object. Expected to succeed."""
    HORIZONTAL = "horizontal"
    """Same role, another owner's object."""
    VERTICAL = "vertical"
    """A lesser role attempting a more privileged action or object."""
    UNAUTHENTICATED = "unauthenticated"


class MatrixError(ValueError):
    """Raised when a matrix or a plan would test something it should not."""


@dataclass(frozen=True)
class Cell:
    identity_id: str
    object_id: str
    action: str
    expectation: Expectation


@dataclass(frozen=True)
class Matrix:
    fixture_id: str
    roles: dict[str, str]
    """identity_id -> role name. ``anonymous`` needs no entry."""
    cells: tuple[Cell, ...]

    def validate(self, manifest: dict) -> None:
        """Refuse anything the ownership manifest does not vouch for."""

        if manifest.get("fixture_id") != self.fixture_id:
            raise MatrixError("matrix and ownership manifest describe different fixtures")
        controlled = set(manifest.get("controlled_identities", ()))
        objects = manifest.get("objects", {})
        for ident in self.roles:
            if ident not in controlled:
                raise MatrixError(f"identity {ident!r} is not a controlled identity")
        seen = Counter((c.identity_id, c.object_id, c.action) for c in self.cells)
        dup = [k for k, n in seen.items() if n > 1]
        if dup:
            raise MatrixError(f"duplicate cells: {dup}")
        for c in self.cells:
            if c.identity_id != ANONYMOUS and c.identity_id not in self.roles:
                raise MatrixError(f"cell names identity {c.identity_id!r} with no role")
            if c.object_id not in objects:
                raise MatrixError(f"cell names object {c.object_id!r} not in the ownership record")
            if objects[c.object_id] not in controlled:
                raise MatrixError(f"object {c.object_id!r} is owned by an uncontrolled identity")

    def family_of(self, cell: Cell, manifest: dict) -> TestFamily:
        if cell.identity_id == ANONYMOUS:
            return TestFamily.UNAUTHENTICATED
        owner = manifest["objects"][cell.object_id]
        if cell.expectation is Expectation.ALLOW and owner == cell.identity_id:
            return TestFamily.OWN
        if self.roles.get(owner) == self.roles.get(cell.identity_id):
            return TestFamily.HORIZONTAL
        return TestFamily.VERTICAL


@dataclass(frozen=True)
class ExperimentIntent:
    cell: Cell
    family: TestFamily
    control: Cell | None
    """The paired ALLOW cell that gives a denial its meaning. None for OWN."""
    request_cost: int = 1
    human_review_required: bool = True
    reviewed_by: str | None = None

    @property
    def executable(self) -> bool:
        return not self.human_review_required or self.reviewed_by is not None


@dataclass(frozen=True)
class Plan:
    fixture_id: str
    intents: tuple[ExperimentIntent, ...]
    budget: dict[TestFamily, int] = field(default_factory=dict)

    def cost_by_family(self) -> dict[TestFamily, int]:
        out: Counter = Counter()
        for i in self.intents:
            out[i.family] += i.request_cost
        return dict(out)

    @property
    def executable(self) -> bool:
        return bool(self.intents) and all(i.executable for i in self.intents)


def plan(matrix: Matrix, manifest: dict, budget: dict[TestFamily, int]) -> Plan:
    """Derive intents from the matrix. Refuses rather than trims."""

    matrix.validate(manifest)
    controls = {
        (c.object_id, c.action): c
        for c in matrix.cells
        if c.expectation is Expectation.ALLOW
        and manifest["objects"][c.object_id] == c.identity_id
    }
    intents: list[ExperimentIntent] = []
    for c in matrix.cells:
        fam = matrix.family_of(c, manifest)
        control = None
        if c.expectation is Expectation.DENY:
            control = controls.get((c.object_id, c.action))
            if control is None:
                raise MatrixError(
                    f"deny cell {c.identity_id}/{c.object_id}/{c.action} has no owner ALLOW "
                    "control; a denial without a served owner proves nothing"
                )
        # A denial costs its own request plus the control's, so the budget
        # reflects what will actually be sent.
        cost = 1 if control is None else 2
        intents.append(ExperimentIntent(c, fam, control, request_cost=cost))

    p = Plan(matrix.fixture_id, tuple(intents), dict(budget))
    for fam, cost in p.cost_by_family().items():
        allowed = budget.get(fam)
        if allowed is None:
            raise MatrixError(f"no request budget declared for family {fam.value}")
        if cost > allowed:
            raise MatrixError(
                f"family {fam.value} needs {cost} requests, budget is {allowed}; "
                "reduce the matrix rather than letting the planner drop cells silently"
            )
    return p


def review_family(p: Plan, family: TestFamily, reviewer: str) -> Plan:
    """Record a human review for one family. Returns a new plan."""

    if not reviewer.strip():
        raise MatrixError("a review must name the reviewer")
    if not any(i.family is family for i in p.intents):
        raise MatrixError(f"plan has no {family.value} intents to review")
    return replace(
        p,
        intents=tuple(
            replace(i, reviewed_by=reviewer) if i.family is family else i for i in p.intents
        ),
    )
