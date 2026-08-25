"""Claim roles and the claim-evidence matrix.

The previous guard on ``report_ready`` was "at least one checked claim". That
is satisfiable by proving almost nothing. A finding could reach report-ready
having deterministically established only that a request returned 200 — true,
checked, and completely silent on whether anything was wrong.

A defensible report answers seven distinct questions, and a report is only as
strong as its *weakest* required answer. So the guard asks for a claim in each
role rather than a count:

======================  ====================================================
Role                    The question it answers
======================  ====================================================
``behaviour``           What actually happened?
``boundary``            Why should the actor not have been able to do it?
``target``              Which controlled object or asset was affected?
``reproduction``        Did it repeat from a clean state?
``impact``              What is the security consequence?
``scope``               Under which contract was this produced?
``evidence_integrity``  Do the artifacts still hash to what was recorded?
======================  ====================================================

Five of those are machine-decidable from artifacts already held and must carry
a ``checked`` claim backed by a validator-issued receipt. **Impact and
reproduction are deliberately not among them** — see :data:`JUDGEMENT_ROLES`
for why each is excluded. Both must still be present, attributed, and state
what remains uncertain.

The matrix built here is what a report should be generated *from*. Free-form
prose drifts stronger than its evidence; a table cannot.
"""

# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 ChaseInTech

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Iterable

from greytheory.checks import CheckReceipt
from greytheory.provenance import Claim, Tag


class ClaimRole(str, Enum):
    BEHAVIOUR = "behaviour"
    BOUNDARY = "boundary"
    TARGET = "target"
    REPRODUCTION = "reproduction"
    IMPACT = "impact"
    SCOPE = "scope"
    EVIDENCE_INTEGRITY = "evidence_integrity"


REQUIRED_ROLES: tuple[ClaimRole, ...] = tuple(ClaimRole)
"""Every role must be answered before a finding is report-ready."""

MUST_BE_CHECKED: frozenset[ClaimRole] = frozenset(
    {
        ClaimRole.BEHAVIOUR,
        ClaimRole.BOUNDARY,
        ClaimRole.TARGET,
        ClaimRole.SCOPE,
        ClaimRole.EVIDENCE_INTEGRITY,
    }
)
"""Roles a deterministic validator can settle from artifacts already held."""

JUDGEMENT_ROLES: frozenset[ClaimRole] = frozenset(
    {ClaimRole.IMPACT, ClaimRole.REPRODUCTION}
)
"""Roles that require a human position, stated with its uncertainty.

``impact`` because whether a proven behaviour *matters* is a judgement about
the product, its users and the programme's own view.

``reproduction`` for a less obvious reason. It is checkable in principle, but
only by performing the action a second time — so requiring a receipt would
push every finding to double its interaction with the target, against
invariant I4 (minimum impact). Gate B in :mod:`greytheory.validation` already
treats reproducibility as attested-plus-evidence, and the two must agree.
"""


class ClaimRoleError(Exception):
    """Raised when a role binding is unsound."""


@dataclass(frozen=True)
class RoleBinding:
    """One claim, bound to the question it answers.

    A binding is not an assertion that the claim is true — the claim's own
    provenance says that. It records which of the seven questions this claim
    is being offered as the answer to, so a missing answer is visible instead
    of being hidden behind a pile of claims about something else.
    """

    role: ClaimRole
    claim: Claim
    receipt: CheckReceipt | None = None
    """The validator receipt backing a ``checked`` claim. Required for the
    roles in :data:`MUST_BE_CHECKED`."""

    uncertainty: str = ""
    """What remains unknown. Required for judgement roles — an impact claim
    with nothing unresolved is almost always an impact claim nobody
    interrogated."""

    def __post_init__(self) -> None:
        if self.role in MUST_BE_CHECKED:
            if self.claim.tag is not Tag.CHECKED:
                raise ClaimRoleError(
                    f"role {self.role.value!r} must be answered by a 'checked' "
                    f"claim; this one is {self.claim.tag.value!r}"
                )
            if self.receipt is None:
                raise ClaimRoleError(
                    f"role {self.role.value!r} requires the validator receipt "
                    "that promoted its claim"
                )
            if not self.receipt.successful:
                raise ClaimRoleError(
                    f"role {self.role.value!r} cites a receipt whose outcome was "
                    f"{self.receipt.actual_outcome!r}, not 'supported'"
                )
            if self.receipt.id != self.claim.check_ref:
                raise ClaimRoleError(
                    f"role {self.role.value!r} cites receipt "
                    f"{self.receipt.id!r} but its claim references "
                    f"{self.claim.check_ref!r}"
                )
        if self.role in JUDGEMENT_ROLES and not self.uncertainty.strip():
            raise ClaimRoleError(
                f"role {self.role.value!r} is a judgement and must state what "
                "remains uncertain; an impact claim with nothing unresolved is "
                "usually one nobody interrogated"
            )

    @property
    def is_proven(self) -> bool:
        return self.claim.is_proven

    def to_dict(self) -> dict[str, Any]:
        return {
            "role": self.role.value,
            "claim": self.claim.to_dict(),
            "receipt": self.receipt.to_dict() if self.receipt else None,
            "uncertainty": self.uncertainty,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RoleBinding:
        receipt = data.get("receipt")
        return cls(
            role=ClaimRole(data["role"]),
            claim=Claim.from_dict(data["claim"]),
            receipt=CheckReceipt.from_dict(receipt) if receipt is not None else None,
            uncertainty=str(data.get("uncertainty", "")),
        )


@dataclass
class MatrixRow:
    role: ClaimRole
    text: str
    provenance: str
    check: str
    status: str
    uncertainty: str = ""

    def to_dict(self) -> dict[str, str]:
        return {
            "role": self.role.value,
            "claim": self.text,
            "provenance": self.provenance,
            "check": self.check,
            "status": self.status,
            "uncertainty": self.uncertainty,
        }


@dataclass
class ClaimEvidenceMatrix:
    """What is supported, what is asserted, and what is missing.

    Generate reports from this. A sentence can imply more than it proves; a row
    that says ``unsupported`` cannot.
    """

    rows: list[MatrixRow] = field(default_factory=list)
    missing: list[ClaimRole] = field(default_factory=list)

    @property
    def complete(self) -> bool:
        return not self.missing

    @property
    def supported(self) -> list[MatrixRow]:
        return [r for r in self.rows if r.status == "supported"]

    @property
    def asserted(self) -> list[MatrixRow]:
        """Rows resting on judgement rather than a deterministic check."""
        return [r for r in self.rows if r.status == "asserted"]

    def render(self) -> str:
        """Markdown, for inclusion in a report."""
        lines = [
            "| Role | Claim | Provenance | Check | Status | Remaining uncertainty |",
            "|---|---|---|---|---|---|",
        ]
        for row in self.rows:
            lines.append(
                f"| {row.role.value} | {row.text} | {row.provenance} | "
                f"{row.check} | {row.status} | {row.uncertainty or '-'} |"
            )
        for role in self.missing:
            lines.append(f"| {role.value} | — | — | — | **missing** | — |")
        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        return {
            "complete": self.complete,
            "rows": [r.to_dict() for r in self.rows],
            "missing": [r.value for r in self.missing],
        }


def build_matrix(bindings: Iterable[RoleBinding]) -> ClaimEvidenceMatrix:
    """Assemble the matrix, naming every role nobody answered."""
    by_role: dict[ClaimRole, RoleBinding] = {}
    for binding in bindings:
        by_role[binding.role] = binding

    rows: list[MatrixRow] = []
    for role in REQUIRED_ROLES:
        binding = by_role.get(role)
        if binding is None:
            continue
        rows.append(
            MatrixRow(
                role=role,
                text=binding.claim.text,
                provenance=binding.claim.tag.value,
                check=binding.receipt.validator_id if binding.receipt else "—",
                status="supported" if binding.is_proven else "asserted",
                uncertainty=binding.uncertainty,
            )
        )

    missing = [role for role in REQUIRED_ROLES if role not in by_role]
    return ClaimEvidenceMatrix(rows=rows, missing=missing)


def readiness_problems(bindings: Iterable[RoleBinding]) -> list[str]:
    """Why this set of bindings is not report-ready. Empty means it is."""
    bindings = list(bindings)
    by_role = {b.role: b for b in bindings}
    problems: list[str] = []

    for role in REQUIRED_ROLES:
        if role not in by_role:
            problems.append(f"no claim answers the {role.value!r} role")

    # A binding cannot be constructed unsoundly, so anything present is already
    # well formed. What remains is checking nobody bound the same claim to two
    # roles to satisfy the count — the exact shortcut the old guard invited.
    seen: dict[str, ClaimRole] = {}
    for binding in bindings:
        key = binding.claim.text.strip().lower()
        if key in seen and seen[key] is not binding.role:
            problems.append(
                f"the same claim answers both {seen[key].value!r} and "
                f"{binding.role.value!r}; one claim cannot be two different "
                "kinds of evidence"
            )
        seen[key] = binding.role

    return problems


__all__ = [
    "ClaimEvidenceMatrix",
    "ClaimRole",
    "ClaimRoleError",
    "JUDGEMENT_ROLES",
    "MUST_BE_CHECKED",
    "MatrixRow",
    "REQUIRED_ROLES",
    "RoleBinding",
    "build_matrix",
    "readiness_problems",
]
