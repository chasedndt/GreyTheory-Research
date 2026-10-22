"""Collector posture: what public reading is permitted, on its own axis.

:class:`~greytheory.authority.gate.AuthorityLevel` is the **execution** posture.
It is ordered by how much access to a programme's assets is permitted, and the
gate uses it to decide whether an action may touch a target.

Reading a bug bounty platform's public programme index is not access to a
target. Placing it on that ordered scale would make it look like a step toward
`PASSIVE_HTTP`, so that raising it for a directory read would imply progress
toward touching assets. It is a different kind of activity, so it gets a
different axis.

The invariant this module exists to hold:

    Raising the collector posture never raises the execution posture.

They are checked independently, recorded independently, and approved
independently. ADR-0029 approved `PUBLIC_INTELLIGENCE`; the execution posture
remains exactly where it was.
"""

# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 ChaseInTech

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum


class CollectorPosture(IntEnum):
    """Ordered. What may be read from sources that are not targets."""

    NONE = 0
    """No outbound reading of any kind."""

    PUBLIC_INTELLIGENCE = 1
    """Unauthenticated reads of public advisory and programme-directory sources
    from established authorities. No credential, no account state, no target."""

    OPERATOR_ACCOUNT = 2
    """Authenticated reads of the operator's own platform account state."""


#: What ADR-0029 approved on 2026-09-08. The operator approved tier 1 (public
#: directories) and tier 2 (their own account state), so the collector posture
#: covers both. Tier 3 is outbound *writing*, which is not a collector posture
#: at all: it is gated per action by a payload-bound operator approval.
APPROVED_COLLECTOR_POSTURE = CollectorPosture.OPERATOR_ACCOUNT

#: The execution posture is unchanged by anything in this module.
UNCHANGED_EXECUTION_POSTURE = "LOCAL_FIXTURE"


class CollectorPostureError(RuntimeError):
    """Raised when an activity exceeds the recorded collector posture."""


@dataclass(frozen=True)
class CollectorPostureRecord:
    """What the system says about its own outbound reading."""

    collector_posture: str
    execution_posture: str
    approved_by: str
    approved_on: str
    decision_reference: str
    #: Restated on every record, because the whole point of a separate axis is
    #: that a reader can see these did not move together.
    raises_execution_posture: bool = False
    target_interaction_permitted: bool = False
    submission_permitted: bool = False

    def to_dict(self) -> dict[str, object]:
        return {
            "schema": "greytheory.collector-posture/1",
            "collector_posture": self.collector_posture,
            "execution_posture": self.execution_posture,
            "approved_by": self.approved_by,
            "approved_on": self.approved_on,
            "decision_reference": self.decision_reference,
            "raises_execution_posture": self.raises_execution_posture,
            "target_interaction_permitted": self.target_interaction_permitted,
            "submission_permitted": self.submission_permitted,
        }


def current_record() -> CollectorPostureRecord:
    """The recorded posture this build operates under."""

    return CollectorPostureRecord(
        collector_posture=APPROVED_COLLECTOR_POSTURE.name,
        execution_posture=UNCHANGED_EXECUTION_POSTURE,
        approved_by="operator",
        approved_on="2026-09-08",
        decision_reference="ADR-0029",
    )


def require_collector_posture(
    needed: CollectorPosture,
    *,
    current: CollectorPosture = APPROVED_COLLECTOR_POSTURE,
) -> None:
    """Refuse an activity the recorded collector posture does not cover."""

    if needed > current:
        raise CollectorPostureError(
            f"{needed.name} exceeds the recorded collector posture {current.name}"
        )
