"""One finding entity, one lifecycle.

The prior design carried two schemas — a scanner-shaped ``finding`` and a
research-shaped ``finding_candidate`` — for what is the same object at
different maturities. They are unified here (`Docs/definition.md` section 4).

The lifecycle has a hard seam in it. Everything up to ``report_ready`` is
*asserted* by GreyTheory. Everything from ``submitted`` onward is *recorded*
from the outside world, and cannot be entered without evidence that the outside
world actually said it — invariant I5, no self-award.
"""

# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 ChaseInTech

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from greytheory.provenance import Claim, Tag, partition


class Taxonomy(str, Enum):
    # Internal — asserted by this system
    INFORMATIONAL = "informational"
    CONTEXTUAL = "contextual"
    CANDIDATE = "candidate"
    VALIDATED = "validated"
    REPORT_READY = "report_ready"
    # External — recorded from a programme
    SUBMITTED = "submitted"
    TRIAGED = "triaged"
    VALID = "valid"
    DUPLICATE = "duplicate"
    INFORMATIVE = "informative"
    NOT_APPLICABLE = "not_applicable"
    OUT_OF_SCOPE = "out_of_scope"
    REWARDED = "rewarded"
    NO_REWARD = "no_reward"
    FIXED = "fixed"
    RETESTED = "retested"
    DISCLOSED = "disclosed"
    PRIVATE_CLOSED = "private_closed"


INTERNAL_STATES = {
    Taxonomy.INFORMATIONAL,
    Taxonomy.CONTEXTUAL,
    Taxonomy.CANDIDATE,
    Taxonomy.VALIDATED,
    Taxonomy.REPORT_READY,
}

EXTERNAL_STATES = set(Taxonomy) - INTERNAL_STATES

_ORDER = [
    Taxonomy.INFORMATIONAL,
    Taxonomy.CONTEXTUAL,
    Taxonomy.CANDIDATE,
    Taxonomy.VALIDATED,
    Taxonomy.REPORT_READY,
]

TRANSITIONS: dict[Taxonomy, set[Taxonomy]] = {
    Taxonomy.INFORMATIONAL: {Taxonomy.CONTEXTUAL},
    Taxonomy.CONTEXTUAL: {Taxonomy.CANDIDATE},
    Taxonomy.CANDIDATE: {Taxonomy.VALIDATED},
    Taxonomy.VALIDATED: {Taxonomy.REPORT_READY},
    Taxonomy.REPORT_READY: {Taxonomy.SUBMITTED},
    Taxonomy.SUBMITTED: {Taxonomy.TRIAGED},
    Taxonomy.TRIAGED: {
        Taxonomy.VALID,
        Taxonomy.DUPLICATE,
        Taxonomy.INFORMATIVE,
        Taxonomy.NOT_APPLICABLE,
        Taxonomy.OUT_OF_SCOPE,
    },
    Taxonomy.VALID: {Taxonomy.REWARDED, Taxonomy.NO_REWARD},
    Taxonomy.DUPLICATE: {Taxonomy.PRIVATE_CLOSED},
    Taxonomy.INFORMATIVE: {Taxonomy.PRIVATE_CLOSED},
    Taxonomy.NOT_APPLICABLE: {Taxonomy.PRIVATE_CLOSED},
    Taxonomy.OUT_OF_SCOPE: {Taxonomy.PRIVATE_CLOSED},
    Taxonomy.REWARDED: {Taxonomy.FIXED},
    Taxonomy.NO_REWARD: {Taxonomy.FIXED, Taxonomy.PRIVATE_CLOSED},
    Taxonomy.FIXED: {Taxonomy.RETESTED},
    Taxonomy.RETESTED: {Taxonomy.DISCLOSED, Taxonomy.PRIVATE_CLOSED},
    Taxonomy.DISCLOSED: set(),
    Taxonomy.PRIVATE_CLOSED: set(),
}


class TransitionError(Exception):
    """Raised when a lifecycle move is not permitted."""


@dataclass
class Finding:
    """A finding at whatever maturity it has actually reached."""

    id: str
    title: str
    lane: int
    """Signal Plane lane that produced the originating signal, 1-4."""

    target: str
    authority_ref: str
    """Invariant I2. The contract fingerprint this was produced under."""

    state: Taxonomy = Taxonomy.INFORMATIONAL
    claims: list[Claim] = field(default_factory=list)
    evidence_refs: list[str] = field(default_factory=list)
    history: list[dict[str, Any]] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.authority_ref:
            raise ValueError(
                "a finding without an authority reference cannot exist (I2)"
            )

    @property
    def is_external(self) -> bool:
        return self.state in EXTERNAL_STATES

    @property
    def proven_claims(self) -> list[Claim]:
        return [c for c in self.claims if c.is_proven]

    def provenance_summary(self) -> dict[str, int]:
        return {tag.value: len(items) for tag, items in partition(self.claims).items()}

    def advance(
        self,
        to: Taxonomy,
        *,
        actor: str,
        note: str = "",
        programme_evidence: str | None = None,
        operator_approval: str | None = None,
        now: datetime | None = None,
    ) -> None:
        """Move to a new state, or refuse.

        Args:
            to: Target state.
            actor: Who is making the move.
            programme_evidence: Reference to what the programme actually said.
                Required for every state past ``submitted`` (I5).
            operator_approval: Approval reference. Required to enter
                ``submitted``, which is an act, not an observation.

        Raises:
            TransitionError: If the move is not permitted, or the evidence
                required to justify it is absent.
        """
        if to not in TRANSITIONS.get(self.state, set()):
            raise TransitionError(
                f"{self.state.value} -> {to.value} is not a permitted transition"
            )

        if to is Taxonomy.SUBMITTED and not operator_approval:
            raise TransitionError(
                "submission is an operator act and requires an approval reference"
            )

        if to in EXTERNAL_STATES and to is not Taxonomy.SUBMITTED:
            if not programme_evidence:
                raise TransitionError(
                    f"{to.value} is a programme outcome; it can only be recorded "
                    "with evidence of what the programme said (I5 — the system "
                    "never awards itself a result)"
                )

        if to is Taxonomy.REPORT_READY and not self.proven_claims:
            raise TransitionError(
                "report_ready requires at least one 'checked' claim; inference "
                "alone is not a report"
            )

        previous = self.state
        self.state = to
        self.history.append(
            {
                "from": previous.value,
                "to": to.value,
                "actor": actor,
                "note": note,
                "programme_evidence": programme_evidence,
                "operator_approval": operator_approval,
                "at": (now or datetime.now(timezone.utc)).isoformat(),
            }
        )

    def demote(self, to: Taxonomy, *, actor: str, reason: str) -> None:
        """Walk an internal finding back down.

        Evidence weakens as often as it strengthens, and a system that can only
        promote will overstate everything it holds. Demotion is internal-only:
        a programme outcome is never un-said by us.
        """
        if self.state not in INTERNAL_STATES or to not in INTERNAL_STATES:
            raise TransitionError("demotion applies only within internal states")
        if _ORDER.index(to) >= _ORDER.index(self.state):
            raise TransitionError(f"{to.value} is not below {self.state.value}")
        previous = self.state
        self.state = to
        self.history.append(
            {
                "from": previous.value,
                "to": to.value,
                "actor": actor,
                "note": f"demoted: {reason}",
                "at": datetime.now(timezone.utc).isoformat(),
            }
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "lane": self.lane,
            "target": self.target,
            "authority_ref": self.authority_ref,
            "state": self.state.value,
            "claims": [c.to_dict() for c in self.claims],
            "evidence_refs": list(self.evidence_refs),
            "provenance": self.provenance_summary(),
            "history": list(self.history),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Finding:
        return cls(
            id=data["id"],
            title=data["title"],
            lane=data["lane"],
            target=data["target"],
            authority_ref=data["authority_ref"],
            state=Taxonomy(data.get("state", "informational")),
            claims=[Claim.from_dict(c) for c in data.get("claims", [])],
            evidence_refs=list(data.get("evidence_refs", [])),
            history=list(data.get("history", [])),
        )


__all__ = [
    "EXTERNAL_STATES",
    "Finding",
    "INTERNAL_STATES",
    "TRANSITIONS",
    "Tag",
    "Taxonomy",
    "TransitionError",
]
