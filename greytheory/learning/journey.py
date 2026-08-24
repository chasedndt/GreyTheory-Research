"""Deterministic guided-learning plans and journey state.

This module orchestrates the existing catalogue and mastery records. It does
not run a fixture, record mastery, call a model, or perform I/O. The workbench
and CLI can therefore explain every recommendation before the operator acts.
"""

# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 ChaseInTech

from __future__ import annotations

import re
from dataclasses import dataclass, replace
from datetime import date, datetime, timedelta
from enum import Enum
from typing import Any, Iterable, Mapping

from greytheory.learning.catalogue import VulnerabilityCatalogue
from greytheory.learning.domain import (
    AssessorKind,
    LearningError,
    MasteryAssessment,
    MasteryDimension,
    MasteryLevel,
    MasteryState,
    VulnerabilityCard,
)


SAFE_ID = re.compile(r"^[a-z0-9][a-z0-9_.:-]{0,191}$")


class LearningMode(str, Enum):
    GUIDED = "guided"
    REVIEW = "review"
    PREREQUISITE = "prerequisite"
    FOCUSED = "focused"
    MAINTENANCE = "maintenance"


class LearningStage(str, Enum):
    LEARN = "learn"
    PRACTISE = "practise"
    PROVE = "prove"
    REFLECT = "reflect"
    ASSESS = "assess"
    COMPLETE = "complete"


class JourneyStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


@dataclass(frozen=True)
class StageBrief:
    stage: LearningStage
    title: str
    objective: str
    required_output: str

    def to_dict(self) -> dict[str, str]:
        return {
            "stage": self.stage.value,
            "title": self.title,
            "objective": self.objective,
            "required_output": self.required_output,
        }


@dataclass(frozen=True)
class LearningRecommendation:
    card_id: str
    card_name: str
    dimension: MasteryDimension
    current_level: MasteryLevel
    mode: LearningMode
    reason: str
    prerequisite_gaps: tuple[str, ...]
    review_due: date | None
    stages: tuple[StageBrief, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "card_id": self.card_id,
            "card_name": self.card_name,
            "dimension": self.dimension.value,
            "current_level": self.current_level.name.lower(),
            "mode": self.mode.value,
            "reason": self.reason,
            "prerequisite_gaps": list(self.prerequisite_gaps),
            "review_due": self.review_due.isoformat() if self.review_due else None,
            "stages": [stage.to_dict() for stage in self.stages],
            "mastery_credit_rule": "explicit evidence-bound human assessment only",
            "operating_posture": "LOCAL_FIXTURE",
        }


class ReviewPolicy:
    """Small, inspectable default intervals; never hidden adaptive scoring."""

    INTERVAL_DAYS = {
        MasteryLevel.INTRODUCTORY: 7,
        MasteryLevel.ASSISTED: 14,
        MasteryLevel.INDEPENDENT: 30,
        MasteryLevel.TRANSFERABLE: 90,
    }

    def review_due(self, assessed_on: date, level: MasteryLevel) -> date:
        if level is MasteryLevel.NOT_ASSESSED:
            raise LearningError("not-assessed has no review interval")
        return assessed_on + timedelta(days=self.INTERVAL_DAYS[level])

    def to_dict(self) -> dict[str, int]:
        return {
            level.name.lower(): days for level, days in self.INTERVAL_DAYS.items()
        }


class GuidedLearningPlanner:
    """Choose one explainable next card/dimension without changing state."""

    def __init__(self, catalogue: VulnerabilityCatalogue) -> None:
        self.catalogue = catalogue
        self._card_order = {
            card_id: index for index, card_id in enumerate(catalogue.graph.order)
        }
        self._dimension_order = {
            dimension: index for index, dimension in enumerate(MasteryDimension)
        }

    def recommend(
        self,
        assessments: Iterable[MasteryAssessment],
        *,
        today: date,
        preferred_card_id: str | None = None,
        preferred_dimension: MasteryDimension | None = None,
    ) -> LearningRecommendation:
        recorded = tuple(assessments)
        states = self.catalogue.graph.mastery_states(recorded)
        by_key = {(state.card_id, state.dimension): state for state in states}

        if preferred_card_id is not None:
            self.catalogue.card(preferred_card_id)
            gaps = self.catalogue.graph.prerequisite_gaps(
                preferred_card_id, recorded
            )
            if gaps:
                card_id = min(gaps, key=self._card_order.__getitem__)
                state = by_key[(card_id, MasteryDimension.TEST)]
                return self._build(
                    state,
                    LearningMode.PREREQUISITE,
                    f"{preferred_card_id} requires independent test evidence for {card_id}",
                    self.catalogue.graph.prerequisite_gaps(card_id, recorded),
                )
            dimension = preferred_dimension or self._weakest_dimension(
                preferred_card_id, by_key
            )
            state = by_key[(preferred_card_id, dimension)]
            return self._build(
                state,
                LearningMode.FOCUSED,
                "operator-selected card and mastery dimension",
                (),
            )

        due = [
            state
            for state in states
            if state.assessment_id is not None
            and state.review_due is not None
            and state.review_due <= today
        ]
        if due:
            state = min(
                due,
                key=lambda item: (
                    item.review_due,
                    self._card_order[item.card_id],
                    self._dimension_order[item.dimension],
                ),
            )
            return self._build(
                state,
                LearningMode.REVIEW,
                f"evidence-bound mastery review was due {state.review_due.isoformat()}",
                self.catalogue.graph.prerequisite_gaps(state.card_id, recorded),
            )

        candidates = [
            state
            for state in states
            if state.level < MasteryLevel.TRANSFERABLE
            and not self.catalogue.graph.prerequisite_gaps(state.card_id, recorded)
        ]
        if candidates:
            state = min(
                candidates,
                key=lambda item: (
                    self._card_order[item.card_id],
                    item.level,
                    self._dimension_order[item.dimension],
                ),
            )
            return self._build(
                state,
                LearningMode.GUIDED,
                "earliest prerequisite-ready mastery gap in the canonical skill graph",
                (),
            )

        assessed = [state for state in states if state.review_due is not None]
        if not assessed:
            raise LearningError("no eligible learning recommendation exists")
        state = min(
            assessed,
            key=lambda item: (
                item.review_due,
                self._card_order[item.card_id],
                self._dimension_order[item.dimension],
            ),
        )
        return self._build(
            state,
            LearningMode.MAINTENANCE,
            f"all eligible dimensions are transferable; next review is {state.review_due.isoformat()}",
            (),
        )

    def _weakest_dimension(
        self,
        card_id: str,
        states: Mapping[tuple[str, MasteryDimension], MasteryState],
    ) -> MasteryDimension:
        return min(
            MasteryDimension,
            key=lambda dimension: (
                states[(card_id, dimension)].level,
                self._dimension_order[dimension],
            ),
        )

    def _build(
        self,
        state: MasteryState,
        mode: LearningMode,
        reason: str,
        gaps: tuple[str, ...],
    ) -> LearningRecommendation:
        card = self.catalogue.card(state.card_id)
        return LearningRecommendation(
            card_id=card.id,
            card_name=card.name,
            dimension=state.dimension,
            current_level=state.level,
            mode=mode,
            reason=reason,
            prerequisite_gaps=gaps,
            review_due=state.review_due,
            stages=_stage_briefs(card, state.dimension),
        )


def _stage_briefs(
    card: VulnerabilityCard, dimension: MasteryDimension
) -> tuple[StageBrief, ...]:
    evidence_roles = ", ".join(item.role for item in card.minimum_evidence)
    return (
        StageBrief(
            LearningStage.LEARN,
            "Learn",
            f"Explain the security property for {card.name}: {card.security_property}",
            f"A concise explanation in your own words for the {dimension.value} dimension.",
        ),
        StageBrief(
            LearningStage.PRACTISE,
            "Practise",
            card.safe_test_pattern,
            f"A receipt from the synthetic fixture {card.local_fixture.id}; it proves no real vulnerability.",
        ),
        StageBrief(
            LearningStage.PROVE,
            "Prove",
            f"Separate observation, deterministic proof, and judgement using: {evidence_roles}.",
            "Evidence references sufficient for an operator to assess this dimension.",
        ),
        StageBrief(
            LearningStage.REFLECT,
            "Reflect",
            "Record what changed in your understanding, what could be a false positive, and what you would do differently.",
            "A written reflection linked to the journey.",
        ),
        StageBrief(
            LearningStage.ASSESS,
            "Assess",
            "Make an explicit human judgement against the evidence; do not infer mastery from completion.",
            "A separately persisted evidence-bound human MasteryAssessment.",
        ),
    )


@dataclass(frozen=True)
class LearningCheckpoint:
    stage: LearningStage
    completed_at: datetime
    evidence_refs: tuple[str, ...] = ()
    note: str = ""

    def __post_init__(self) -> None:
        if self.stage is LearningStage.COMPLETE:
            raise LearningError("complete is a journey status, not a checkpoint")
        if self.completed_at.tzinfo is None:
            raise LearningError("checkpoint time must be timezone-aware")
        if any(not str(item).strip() for item in self.evidence_refs):
            raise LearningError("checkpoint evidence references cannot be empty")

    def to_dict(self) -> dict[str, Any]:
        return {
            "stage": self.stage.value,
            "completed_at": self.completed_at.isoformat(),
            "evidence_refs": list(self.evidence_refs),
            "note": self.note,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> LearningCheckpoint:
        return cls(
            stage=LearningStage(data["stage"]),
            completed_at=datetime.fromisoformat(data["completed_at"]),
            evidence_refs=tuple(data.get("evidence_refs", ())),
            note=str(data.get("note", "")),
        )


@dataclass(frozen=True)
class LearningJourney:
    id: str
    card_id: str
    dimension: MasteryDimension
    mode: LearningMode
    objective: str
    status: JourneyStatus
    current_stage: LearningStage
    started_at: datetime
    updated_at: datetime
    revision: int = 0
    checkpoints: tuple[LearningCheckpoint, ...] = ()

    def __post_init__(self) -> None:
        if not SAFE_ID.fullmatch(str(self.id or "")):
            raise LearningError(f"journey id {self.id!r} is not a safe identifier")
        if not SAFE_ID.fullmatch(str(self.card_id or "")):
            raise LearningError(f"journey card id {self.card_id!r} is not a safe identifier")
        if not str(self.objective or "").strip():
            raise LearningError("journey objective is required")
        if self.started_at.tzinfo is None or self.updated_at.tzinfo is None:
            raise LearningError("journey times must be timezone-aware")
        if self.updated_at < self.started_at:
            raise LearningError("journey update cannot precede its start")
        if self.revision < 0:
            raise LearningError("journey revision cannot be negative")
        if self.revision != len(self.checkpoints):
            raise LearningError("journey revision must equal its checkpoint count")
        previous_time = self.started_at
        for checkpoint in self.checkpoints:
            if checkpoint.completed_at < previous_time:
                raise LearningError("journey checkpoints must be time ordered")
            if checkpoint.completed_at > self.updated_at:
                raise LearningError("journey checkpoint cannot follow the update time")
            previous_time = checkpoint.completed_at
        ordered = (
            LearningStage.LEARN,
            LearningStage.PRACTISE,
            LearningStage.PROVE,
            LearningStage.REFLECT,
            LearningStage.ASSESS,
        )
        if self.status is JourneyStatus.COMPLETED and self.current_stage is not LearningStage.COMPLETE:
            raise LearningError("a completed journey must be at the complete stage")
        if self.status is JourneyStatus.ACTIVE and self.current_stage is LearningStage.COMPLETE:
            raise LearningError("an active journey cannot be complete")
        if self.status is JourneyStatus.COMPLETED:
            if tuple(item.stage for item in self.checkpoints) != ordered:
                raise LearningError("a completed journey requires every stage in order")
        elif self.status is JourneyStatus.ACTIVE:
            completed = tuple(item.stage for item in self.checkpoints)
            if completed != ordered[: len(completed)] or len(completed) >= len(ordered):
                raise LearningError("active journey checkpoints are out of order")
            if self.current_stage is not ordered[len(completed)]:
                raise LearningError("active journey stage does not follow its checkpoints")
        elif self.status is JourneyStatus.ABANDONED:
            if not self.checkpoints or not self.checkpoints[-1].note.startswith("abandoned: "):
                raise LearningError("an abandoned journey requires a final reason checkpoint")
            completed = tuple(item.stage for item in self.checkpoints[:-1])
            if completed != ordered[: len(completed)]:
                raise LearningError("abandoned journey checkpoints are out of order")
            if self.current_stage is not ordered[len(completed)]:
                raise LearningError("abandoned journey stage does not match its final checkpoint")

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "card_id": self.card_id,
            "dimension": self.dimension.value,
            "mode": self.mode.value,
            "objective": self.objective,
            "status": self.status.value,
            "current_stage": self.current_stage.value,
            "started_at": self.started_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "revision": self.revision,
            "checkpoints": [item.to_dict() for item in self.checkpoints],
            "awards_mastery": False,
            "operating_posture": "LOCAL_FIXTURE",
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> LearningJourney:
        return cls(
            id=data["id"],
            card_id=data["card_id"],
            dimension=MasteryDimension(data["dimension"]),
            mode=LearningMode(data["mode"]),
            objective=data["objective"],
            status=JourneyStatus(data["status"]),
            current_stage=LearningStage(data["current_stage"]),
            started_at=datetime.fromisoformat(data["started_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            revision=int(data.get("revision", 0)),
            checkpoints=tuple(
                LearningCheckpoint.from_dict(item)
                for item in data.get("checkpoints", ())
            ),
        )


def start_learning_journey(
    recommendation: LearningRecommendation,
    *,
    journey_id: str,
    now: datetime,
    objective: str | None = None,
) -> LearningJourney:
    if now.tzinfo is None:
        raise LearningError("journey start time must be timezone-aware")
    return LearningJourney(
        id=journey_id,
        card_id=recommendation.card_id,
        dimension=recommendation.dimension,
        mode=recommendation.mode,
        objective=(objective or recommendation.stages[0].objective),
        status=JourneyStatus.ACTIVE,
        current_stage=LearningStage.LEARN,
        started_at=now,
        updated_at=now,
    )


_NEXT_STAGE = {
    LearningStage.LEARN: LearningStage.PRACTISE,
    LearningStage.PRACTISE: LearningStage.PROVE,
    LearningStage.PROVE: LearningStage.REFLECT,
    LearningStage.REFLECT: LearningStage.ASSESS,
    LearningStage.ASSESS: LearningStage.COMPLETE,
}


def advance_learning_journey(
    journey: LearningJourney,
    *,
    at: datetime,
    fixture_receipt_ref: str | None = None,
    evidence_refs: Iterable[str] = (),
    reflection: str | None = None,
    assessment: MasteryAssessment | None = None,
    recorded_assessment_ids: Iterable[str] = (),
) -> LearningJourney:
    """Advance exactly one stage without creating evidence or mastery."""

    if journey.status is not JourneyStatus.ACTIVE:
        raise LearningError("only an active learning journey can advance")
    if at.tzinfo is None:
        raise LearningError("journey checkpoint time must be timezone-aware")
    if at < journey.updated_at:
        raise LearningError("journey checkpoint cannot move backwards in time")

    refs = tuple(str(item).strip() for item in evidence_refs)
    if any(not item for item in refs):
        raise LearningError("journey evidence references cannot be empty")
    note = str(reflection or "").strip()
    stage = journey.current_stage

    if stage is LearningStage.PRACTISE:
        receipt = str(fixture_receipt_ref or "").strip()
        if not receipt:
            raise LearningError("practise requires a synthetic fixture receipt reference")
        refs = (receipt, *refs)
    elif stage is LearningStage.PROVE and not refs:
        raise LearningError("prove requires at least one evidence reference")
    elif stage is LearningStage.REFLECT and not note:
        raise LearningError("reflect requires the operator's written reflection")
    elif stage is LearningStage.ASSESS:
        if assessment is None:
            raise LearningError("assess requires an explicit mastery assessment")
        if assessment.assessor_kind is not AssessorKind.HUMAN or not assessment.credits_mastery:
            raise LearningError("journey completion requires a human mastery assessment")
        if (assessment.card_id, assessment.dimension) != (
            journey.card_id,
            journey.dimension,
        ):
            raise LearningError("mastery assessment does not match the journey")
        if assessment.id not in set(recorded_assessment_ids):
            raise LearningError("mastery assessment must already be persisted")
        refs = (f"mastery-assessment:{assessment.id}", *refs)

    checkpoint = LearningCheckpoint(
        stage=stage,
        completed_at=at,
        evidence_refs=refs,
        note=note,
    )
    next_stage = _NEXT_STAGE[stage]
    return replace(
        journey,
        status=(
            JourneyStatus.COMPLETED
            if next_stage is LearningStage.COMPLETE
            else JourneyStatus.ACTIVE
        ),
        current_stage=next_stage,
        updated_at=at,
        revision=journey.revision + 1,
        checkpoints=(*journey.checkpoints, checkpoint),
    )


def abandon_learning_journey(
    journey: LearningJourney, *, at: datetime, reason: str
) -> LearningJourney:
    if journey.status is not JourneyStatus.ACTIVE:
        raise LearningError("only an active learning journey can be abandoned")
    if at.tzinfo is None or at < journey.updated_at:
        raise LearningError("journey abandonment time must be aware and monotonic")
    note = str(reason or "").strip()
    if not note:
        raise LearningError("journey abandonment requires a reason")
    checkpoint = LearningCheckpoint(
        stage=journey.current_stage,
        completed_at=at,
        note=f"abandoned: {note}",
    )
    return replace(
        journey,
        status=JourneyStatus.ABANDONED,
        updated_at=at,
        revision=journey.revision + 1,
        checkpoints=(*journey.checkpoints, checkpoint),
    )


__all__ = [
    "GuidedLearningPlanner",
    "JourneyStatus",
    "LearningCheckpoint",
    "LearningJourney",
    "LearningMode",
    "LearningRecommendation",
    "LearningStage",
    "ReviewPolicy",
    "StageBrief",
    "abandon_learning_journey",
    "advance_learning_journey",
    "start_learning_journey",
]
