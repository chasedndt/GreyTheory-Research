"""Transparent decision-support contracts for hypothesis prioritisation.

The objects in this module describe estimates and queue order only.  They do
not classify research outcomes, grant authority, or request execution.
"""

# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 ChaseInTech

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Mapping


SAFE_ID = re.compile(r"^[a-z0-9][a-z0-9._-]{0,127}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")


class HypothesisRankingError(ValueError):
    """Raised when a ranking input or output would be ambiguous or unsafe."""


def _required(value: Any, label: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise HypothesisRankingError(f"{label} is required")
    return text


def _safe_id(value: Any, label: str) -> str:
    text = _required(value, label)
    if not SAFE_ID.fullmatch(text):
        raise HypothesisRankingError(f"{label} is not a safe identifier")
    return text


def _texts(values: Any, label: str, *, allow_empty: bool = True) -> tuple[str, ...]:
    result = tuple(_required(value, label) for value in (values or ()))
    if not allow_empty and not result:
        raise HypothesisRankingError(f"{label} must contain at least one value")
    if len(result) != len(set(result)):
        raise HypothesisRankingError(f"{label} cannot contain duplicates")
    return result


def _parse_time(value: Any) -> datetime:
    parsed = value if isinstance(value, datetime) else datetime.fromisoformat(str(value))
    if parsed.tzinfo is None:
        raise HypothesisRankingError("ranking timestamps must be timezone-aware")
    return parsed


def _canonical(value: Mapping[str, Any]) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


class RankingFactor(str, Enum):
    SCOPE_CONFIDENCE = "scope_confidence"
    EVIDENCE_ALREADY_PRESENT = "evidence_already_present"
    LIKELIHOOD = "likelihood"
    POTENTIAL_IMPACT = "potential_impact"
    TEST_COST = "test_cost"
    SIDE_EFFECT_RISK = "side_effect_risk"
    DUPLICATE_RISK = "duplicate_risk"
    SKILL_VALUE = "skill_value"
    TARGET_SPECIFIC_NOVELTY = "target_specific_novelty"


class FactorDirection(str, Enum):
    HIGHER_IS_BETTER = "higher_is_better"
    LOWER_IS_BETTER = "lower_is_better"


class AssessmentSource(str, Enum):
    OPERATOR = "operator"
    TEST_FIXTURE = "test_fixture"


class QueuePartition(str, Enum):
    PLANNING_CANDIDATE = "planning_candidate"
    SCOPE_REVIEW_REQUIRED = "scope_review_required"


SYSTEM_DERIVED_FACTORS = frozenset(
    {
        RankingFactor.SCOPE_CONFIDENCE,
        RankingFactor.EVIDENCE_ALREADY_PRESENT,
        RankingFactor.TEST_COST,
        RankingFactor.SIDE_EFFECT_RISK,
    }
)
ASSESSED_FACTORS = frozenset(set(RankingFactor) - SYSTEM_DERIVED_FACTORS)


@dataclass(frozen=True)
class FactorWeight:
    factor: RankingFactor
    weight_percent: int
    direction: FactorDirection

    def __post_init__(self) -> None:
        if isinstance(self.weight_percent, bool) or not 1 <= self.weight_percent <= 100:
            raise HypothesisRankingError("factor weights must be integers from 1 to 100")

    def to_dict(self) -> dict[str, Any]:
        return {
            "factor": self.factor.value,
            "weight_percent": self.weight_percent,
            "direction": self.direction.value,
        }


@dataclass(frozen=True)
class RankingPolicy:
    id: str
    version: str
    weights: tuple[FactorWeight, ...]
    effect_risk_levels: tuple[tuple[str, int], ...]
    unknown_effect_risk_level: int = 4

    def __post_init__(self) -> None:
        _safe_id(self.id, "ranking policy id")
        _required(self.version, "ranking policy version")
        factors = tuple(item.factor for item in self.weights)
        if len(factors) != len(set(factors)):
            raise HypothesisRankingError("ranking policy factors must be unique")
        if set(factors) != set(RankingFactor):
            raise HypothesisRankingError("ranking policy must define all nine factors")
        if sum(item.weight_percent for item in self.weights) != 100:
            raise HypothesisRankingError("ranking policy weights must total 100 percent")
        seen: set[str] = set()
        normalised: list[tuple[str, int]] = []
        for name, level in self.effect_risk_levels:
            effect = _safe_id(name, "effect risk name")
            if effect in seen:
                raise HypothesisRankingError("effect risk names must be unique")
            if isinstance(level, bool) or not 0 <= level <= 4:
                raise HypothesisRankingError("effect risk levels must be integers from 0 to 4")
            seen.add(effect)
            normalised.append((effect, int(level)))
        if isinstance(self.unknown_effect_risk_level, bool) or not 0 <= self.unknown_effect_risk_level <= 4:
            raise HypothesisRankingError("unknown effect risk level must be from 0 to 4")
        object.__setattr__(self, "effect_risk_levels", tuple(sorted(normalised)))

    def weight(self, factor: RankingFactor) -> FactorWeight:
        return next(item for item in self.weights if item.factor is factor)

    def effect_level(self, name: str) -> tuple[int, bool]:
        levels = dict(self.effect_risk_levels)
        return (levels[name], True) if name in levels else (self.unknown_effect_risk_level, False)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "version": self.version,
            "weights": [item.to_dict() for item in self.weights],
            "effect_risk_levels": dict(self.effect_risk_levels),
            "unknown_effect_risk_level": self.unknown_effect_risk_level,
        }

    def digest(self) -> str:
        return hashlib.sha256(_canonical(self.to_dict()).encode("utf-8")).hexdigest()


def conservative_local_policy() -> RankingPolicy:
    """The inspectable default policy for the local-only research queue."""

    return RankingPolicy(
        id="conservative-local",
        version="1.0.0",
        weights=(
            FactorWeight(RankingFactor.SCOPE_CONFIDENCE, 20, FactorDirection.HIGHER_IS_BETTER),
            FactorWeight(
                RankingFactor.EVIDENCE_ALREADY_PRESENT,
                15,
                FactorDirection.HIGHER_IS_BETTER,
            ),
            FactorWeight(RankingFactor.LIKELIHOOD, 10, FactorDirection.HIGHER_IS_BETTER),
            FactorWeight(
                RankingFactor.POTENTIAL_IMPACT, 10, FactorDirection.HIGHER_IS_BETTER
            ),
            FactorWeight(RankingFactor.TEST_COST, 10, FactorDirection.LOWER_IS_BETTER),
            FactorWeight(
                RankingFactor.SIDE_EFFECT_RISK, 15, FactorDirection.LOWER_IS_BETTER
            ),
            FactorWeight(RankingFactor.DUPLICATE_RISK, 10, FactorDirection.LOWER_IS_BETTER),
            FactorWeight(RankingFactor.SKILL_VALUE, 5, FactorDirection.HIGHER_IS_BETTER),
            FactorWeight(
                RankingFactor.TARGET_SPECIFIC_NOVELTY,
                5,
                FactorDirection.HIGHER_IS_BETTER,
            ),
        ),
        effect_risk_levels=(("reads", 1), ("mutations", 4)),
        unknown_effect_risk_level=4,
    )


@dataclass(frozen=True)
class FactorAssessment:
    factor: RankingFactor
    level: int
    rationale: str
    provenance_refs: tuple[str, ...]
    uncertainties: tuple[str, ...]
    source: AssessmentSource

    def __post_init__(self) -> None:
        if self.factor not in ASSESSED_FACTORS:
            raise HypothesisRankingError(
                f"{self.factor.value} is system-derived and cannot be self-assessed"
            )
        if isinstance(self.level, bool) or not 0 <= self.level <= 4:
            raise HypothesisRankingError("factor levels must be integers from 0 to 4")
        _required(self.rationale, "factor rationale")
        _texts(self.provenance_refs, "factor provenance references", allow_empty=False)
        _texts(self.uncertainties, "factor uncertainties", allow_empty=False)

    def to_dict(self) -> dict[str, Any]:
        return {
            "factor": self.factor.value,
            "level": self.level,
            "rationale": self.rationale,
            "provenance_refs": list(self.provenance_refs),
            "uncertainties": list(self.uncertainties),
            "source": self.source.value,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> FactorAssessment:
        try:
            source = AssessmentSource(data["source"])
        except ValueError as exc:
            raise HypothesisRankingError(
                "factor source must be operator or test_fixture; model scoring is not built"
            ) from exc
        return cls(
            factor=RankingFactor(data["factor"]),
            level=data["level"],
            rationale=data["rationale"],
            provenance_refs=_texts(
                data.get("provenance_refs"),
                "factor provenance references",
                allow_empty=False,
            ),
            uncertainties=_texts(
                data.get("uncertainties"), "factor uncertainties", allow_empty=False
            ),
            source=source,
        )


@dataclass(frozen=True)
class HypothesisRankingInput:
    id: str
    hypothesis_id: str
    card_id: str
    actor: str
    source_ref: str
    assessments: tuple[FactorAssessment, ...]

    def __post_init__(self) -> None:
        _safe_id(self.id, "ranking input id")
        _safe_id(self.hypothesis_id, "hypothesis id")
        _safe_id(self.card_id, "card id")
        _required(self.actor, "ranking input actor")
        _required(self.source_ref, "ranking input source reference")
        factors = tuple(item.factor for item in self.assessments)
        if len(factors) != len(set(factors)):
            raise HypothesisRankingError("assessed ranking factors must be unique")
        if set(factors) != set(ASSESSED_FACTORS):
            missing = sorted(item.value for item in ASSESSED_FACTORS - set(factors))
            extra = sorted(item.value for item in set(factors) - ASSESSED_FACTORS)
            raise HypothesisRankingError(
                f"ranking input must assess exactly five factors; missing={missing}, extra={extra}"
            )

    def assessment(self, factor: RankingFactor) -> FactorAssessment:
        return next(item for item in self.assessments if item.factor is factor)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "hypothesis_id": self.hypothesis_id,
            "card_id": self.card_id,
            "actor": self.actor,
            "source_ref": self.source_ref,
            "assessments": [item.to_dict() for item in self.assessments],
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> HypothesisRankingInput:
        return cls(
            id=data["id"],
            hypothesis_id=data["hypothesis_id"],
            card_id=data["card_id"],
            actor=data["actor"],
            source_ref=data["source_ref"],
            assessments=tuple(
                FactorAssessment.from_dict(item) for item in data.get("assessments", ())
            ),
        )


@dataclass(frozen=True)
class FactorExplanation:
    factor: RankingFactor
    raw_level: int
    oriented_level: int
    direction: FactorDirection
    weight_percent: int
    contribution_bps: int
    rationale: str
    provenance_refs: tuple[str, ...]
    uncertainties: tuple[str, ...]
    derivation: str
    observed_inputs: tuple[str, ...]

    def __post_init__(self) -> None:
        for value, label in (
            (self.raw_level, "raw factor level"),
            (self.oriented_level, "oriented factor level"),
        ):
            if isinstance(value, bool) or not 0 <= value <= 4:
                raise HypothesisRankingError(f"{label} must be an integer from 0 to 4")
        if isinstance(self.weight_percent, bool) or not 1 <= self.weight_percent <= 100:
            raise HypothesisRankingError("factor explanation weight must be from 1 to 100")
        expected_oriented = (
            self.raw_level
            if self.direction is FactorDirection.HIGHER_IS_BETTER
            else 4 - self.raw_level
        )
        if self.oriented_level != expected_oriented:
            raise HypothesisRankingError("oriented factor level does not match its direction")
        if self.contribution_bps != self.oriented_level * self.weight_percent * 25:
            raise HypothesisRankingError("factor contribution does not match level and weight")
        _required(self.rationale, "factor explanation rationale")
        _texts(self.provenance_refs, "factor explanation provenance references")
        _texts(self.uncertainties, "factor explanation uncertainties", allow_empty=False)
        _required(self.derivation, "factor explanation derivation")
        _texts(self.observed_inputs, "factor observed inputs", allow_empty=False)

    def to_dict(self) -> dict[str, Any]:
        return {
            "factor": self.factor.value,
            "raw_level": self.raw_level,
            "oriented_level": self.oriented_level,
            "direction": self.direction.value,
            "weight_percent": self.weight_percent,
            "contribution_bps": self.contribution_bps,
            "rationale": self.rationale,
            "provenance_refs": list(self.provenance_refs),
            "uncertainties": list(self.uncertainties),
            "derivation": self.derivation,
            "observed_inputs": list(self.observed_inputs),
        }


@dataclass(frozen=True)
class RankedHypothesis:
    rank: int
    hypothesis_id: str
    card_id: str
    source_title: str
    source_status: str
    proposed_action: str
    target_asset_id: str
    potential_consequence: str
    reasoning: str
    expected_safe_behaviour: str
    expected_counter_behaviour: str
    falsifier: str
    minimum_evidence: tuple[str, ...]
    queue_partition: QueuePartition
    score_bps: int
    item_type: str
    claim_state: str
    decision_support_only: bool
    execution_authority: str
    factors: tuple[FactorExplanation, ...]
    assumptions: tuple[str, ...]
    stop_conditions: tuple[str, ...]

    def __post_init__(self) -> None:
        if isinstance(self.rank, bool) or self.rank < 0:
            raise HypothesisRankingError("queue rank must be a non-negative integer")
        _safe_id(self.hypothesis_id, "ranked hypothesis id")
        _safe_id(self.card_id, "ranked card id")
        _required(self.source_title, "ranked hypothesis source title")
        _required(self.source_status, "ranked hypothesis source status")
        _required(self.proposed_action, "ranked hypothesis proposed action")
        _safe_id(self.target_asset_id, "ranked hypothesis target asset id")
        _required(self.potential_consequence, "ranked hypothesis potential consequence")
        _required(self.reasoning, "ranked hypothesis reasoning")
        _required(self.expected_safe_behaviour, "ranked hypothesis expected safe behaviour")
        _required(
            self.expected_counter_behaviour,
            "ranked hypothesis expected counter behaviour",
        )
        _required(self.falsifier, "ranked hypothesis falsifier")
        _texts(self.minimum_evidence, "ranked hypothesis minimum evidence", allow_empty=False)
        if not 0 <= self.score_bps <= 10_000:
            raise HypothesisRankingError("ranked score must be between 0 and 10000 bps")
        if self.item_type != "research_hypothesis" or self.claim_state != "unproven":
            raise HypothesisRankingError("ranked items must remain unproven research hypotheses")
        if not self.decision_support_only or self.execution_authority != "none":
            raise HypothesisRankingError("ranked items cannot grant execution authority")
        factors = tuple(item.factor for item in self.factors)
        if factors != tuple(RankingFactor):
            raise HypothesisRankingError("ranked items must explain all nine factors in order")
        if sum(item.contribution_bps for item in self.factors) != self.score_bps:
            raise HypothesisRankingError("ranked score does not equal factor contributions")
        _texts(self.assumptions, "ranked hypothesis assumptions", allow_empty=False)
        _texts(self.stop_conditions, "ranked hypothesis stop conditions", allow_empty=False)

    def to_dict(self) -> dict[str, Any]:
        return {
            "rank": self.rank,
            "hypothesis_id": self.hypothesis_id,
            "card_id": self.card_id,
            "source_title": self.source_title,
            "source_status": self.source_status,
            "theory": {
                "proposed_action": self.proposed_action,
                "target_asset_id": self.target_asset_id,
                "potential_consequence": self.potential_consequence,
                "reasoning": self.reasoning,
                "expected_safe_behaviour": self.expected_safe_behaviour,
                "expected_counter_behaviour": self.expected_counter_behaviour,
                "falsifier": self.falsifier,
                "minimum_evidence": list(self.minimum_evidence),
            },
            "queue_partition": self.queue_partition.value,
            "score_bps": self.score_bps,
            "score_out_of_bps": 10_000,
            "item_type": self.item_type,
            "claim_state": self.claim_state,
            "decision_support_only": self.decision_support_only,
            "execution_authority": self.execution_authority,
            "factors": [item.to_dict() for item in self.factors],
            "assumptions": list(self.assumptions),
            "stop_conditions": list(self.stop_conditions),
        }


@dataclass(frozen=True)
class ResearchQueue:
    id: str
    schema_version: int
    generated_at: datetime
    workspace_id: str
    programme_id: str
    contract_fingerprint: str
    operating_posture: str
    catalogue_digest: str
    policy: RankingPolicy
    items: tuple[RankedHypothesis, ...]
    queue_digest: str
    decision_support_only: bool = True
    execution_requests_created: int = 0
    action_receipts_created: int = 0
    claim_state: str = "unproven_hypotheses"

    def __post_init__(self) -> None:
        _safe_id(self.id, "research queue id")
        if self.schema_version != 1:
            raise HypothesisRankingError("unsupported research queue schema")
        if self.generated_at.tzinfo is None:
            raise HypothesisRankingError("research queue time must be timezone-aware")
        _safe_id(self.workspace_id, "workspace id")
        _safe_id(self.programme_id, "programme id")
        if not SHA256.fullmatch(self.contract_fingerprint):
            raise HypothesisRankingError("queue contract fingerprint must be SHA-256")
        if not SHA256.fullmatch(self.catalogue_digest):
            raise HypothesisRankingError("queue catalogue digest must be SHA-256")
        if not SHA256.fullmatch(self.queue_digest):
            raise HypothesisRankingError("queue digest must be SHA-256")
        if not self.decision_support_only:
            raise HypothesisRankingError("a research queue must remain decision support only")
        if self.execution_requests_created or self.action_receipts_created:
            raise HypothesisRankingError("ranking cannot create execution records")
        if self.claim_state != "unproven_hypotheses":
            raise HypothesisRankingError("a research queue contains only unproven hypotheses")
        if tuple(item.rank for item in self.items) != tuple(range(1, len(self.items) + 1)):
            raise HypothesisRankingError("research queue ranks must be contiguous from one")
        hypothesis_ids = tuple(item.hypothesis_id for item in self.items)
        if len(hypothesis_ids) != len(set(hypothesis_ids)):
            raise HypothesisRankingError("a research queue cannot repeat a hypothesis")
        for item in self.items:
            for explanation in item.factors:
                weight = self.policy.weight(explanation.factor)
                if (
                    explanation.weight_percent != weight.weight_percent
                    or explanation.direction is not weight.direction
                ):
                    raise HypothesisRankingError(
                        "factor explanation does not match the queue policy"
                    )
        if self.queue_digest != self.calculated_digest():
            raise HypothesisRankingError("research queue failed its integrity check")

    def digest_material(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "generated_at": self.generated_at.astimezone(timezone.utc).isoformat(),
            "workspace_id": self.workspace_id,
            "programme_id": self.programme_id,
            "contract_fingerprint": self.contract_fingerprint,
            "operating_posture": self.operating_posture,
            "catalogue_digest": self.catalogue_digest,
            "policy": {**self.policy.to_dict(), "digest": self.policy.digest()},
            "items": [item.to_dict() for item in self.items],
            "decision_support_only": self.decision_support_only,
            "execution_requests_created": self.execution_requests_created,
            "action_receipts_created": self.action_receipts_created,
            "claim_state": self.claim_state,
        }

    def calculated_digest(self) -> str:
        return hashlib.sha256(
            _canonical(self.digest_material()).encode("utf-8")
        ).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "schema_version": self.schema_version,
            "generated_at": self.generated_at.astimezone(timezone.utc).isoformat(),
            "workspace_id": self.workspace_id,
            "programme_id": self.programme_id,
            "contract_fingerprint": self.contract_fingerprint,
            "operating_posture": self.operating_posture,
            "catalogue_digest": self.catalogue_digest,
            "policy": {**self.policy.to_dict(), "digest": self.policy.digest()},
            "item_count": len(self.items),
            "items": [item.to_dict() for item in self.items],
            "queue_digest": self.queue_digest,
            "decision_support_only": self.decision_support_only,
            "execution_requests_created": self.execution_requests_created,
            "action_receipts_created": self.action_receipts_created,
            "claim_state": self.claim_state,
        }


def parse_ranking_inputs(data: Any) -> tuple[HypothesisRankingInput, ...]:
    values = data.get("ranking_inputs", ()) if isinstance(data, Mapping) else data
    if not isinstance(values, list):
        raise HypothesisRankingError("ranking input JSON must be a list or ranking_inputs object")
    result = tuple(HypothesisRankingInput.from_dict(item) for item in values)
    if not result:
        raise HypothesisRankingError("at least one ranking input is required")
    ids = [item.id for item in result]
    hypothesis_ids = [item.hypothesis_id for item in result]
    if len(ids) != len(set(ids)):
        raise HypothesisRankingError("ranking input ids must be unique")
    if len(hypothesis_ids) != len(set(hypothesis_ids)):
        raise HypothesisRankingError("each hypothesis may appear only once")
    return result
