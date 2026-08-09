"""First-class vulnerability-card and mastery contracts.

Cards are immutable reference knowledge.  Mastery is operator-specific state
and is therefore represented separately as evidence-bound assessments.  A lab
completion, model suggestion, framework mapping, or card membership never
awards mastery by itself.
"""

# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 ChaseInTech

from __future__ import annotations

import re
from dataclasses import dataclass, fields
from datetime import date, datetime
from enum import Enum, IntEnum
from string import Formatter
from typing import Any, Mapping


SAFE_ID = re.compile(r"^[a-z0-9][a-z0-9_.:-]{0,191}$")
ALLOWED_PROVENANCE = frozenset({"observed", "checked", "inferred", "attested"})


class LearningError(ValueError):
    """Raised when learning data would weaken a Milestone 5 invariant."""


class MasteryDimension(str, Enum):
    EXPLAIN = "explain"
    RECOGNISE = "recognise"
    TEST = "test"
    PROVE = "prove"
    REMEDIATE = "remediate"
    TRANSFER = "transfer"


class MasteryLevel(IntEnum):
    NOT_ASSESSED = 0
    INTRODUCTORY = 1
    ASSISTED = 2
    INDEPENDENT = 3
    TRANSFERABLE = 4

    @classmethod
    def parse(cls, value: MasteryLevel | str | int) -> MasteryLevel:
        if isinstance(value, cls):
            return value
        if isinstance(value, str):
            normalised = value.strip().upper().replace("-", "_")
            try:
                return cls[normalised]
            except KeyError as exc:
                raise LearningError(f"unknown mastery level {value!r}") from exc
        try:
            return cls(int(value))
        except (TypeError, ValueError) as exc:
            raise LearningError(f"unknown mastery level {value!r}") from exc


class AssessorKind(str, Enum):
    HUMAN = "human"
    TEST_FIXTURE = "test_fixture"


def _safe_id(value: str, label: str) -> str:
    text = str(value or "").strip()
    if not SAFE_ID.fullmatch(text):
        raise LearningError(f"{label} {value!r} is not a safe identifier")
    return text


def _required(value: str, label: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise LearningError(f"{label} is required")
    return text


def _text_tuple(
    values: Any, label: str, *, allow_empty: bool = False
) -> tuple[str, ...]:
    result = tuple(str(value).strip() for value in (values or ()))
    if any(not value for value in result):
        raise LearningError(f"{label} cannot contain empty values")
    if not allow_empty and not result:
        raise LearningError(f"{label} must contain at least one value")
    if len(result) != len(set(result)):
        raise LearningError(f"{label} cannot contain duplicates")
    return result


def _aware(value: datetime, label: str) -> datetime:
    if value.tzinfo is None:
        raise LearningError(f"{label} must be timezone-aware")
    return value


def _encode(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.name.lower() if isinstance(value, IntEnum) else value.value
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, tuple):
        return [_encode(item) for item in value]
    if hasattr(value, "to_dict"):
        return value.to_dict()
    return value


class SerializableRecord:
    def to_dict(self) -> dict[str, Any]:
        return {item.name: _encode(getattr(self, item.name)) for item in fields(self)}


@dataclass(frozen=True)
class FrameworkReference(SerializableRecord):
    framework: str
    reference: str
    url: str

    def __post_init__(self) -> None:
        _required(self.framework, "framework")
        _required(self.reference, "framework reference")
        if not str(self.url).startswith("https://"):
            raise LearningError("framework reference URL must use HTTPS")

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> FrameworkReference:
        return cls(
            framework=data["framework"],
            reference=data["reference"],
            url=data["url"],
        )


@dataclass(frozen=True)
class HypothesisTemplate(SerializableRecord):
    id: str
    statement: str
    variables: tuple[str, ...]
    preconditions: tuple[str, ...]
    expected_safe_behaviour: str
    expected_vulnerable_behaviour: str
    falsifier: str
    stop_conditions: tuple[str, ...]

    def __post_init__(self) -> None:
        _safe_id(self.id, "hypothesis template id")
        _required(self.statement, "hypothesis statement")
        variables = _text_tuple(self.variables, "hypothesis variables")
        for variable in variables:
            _safe_id(variable, "hypothesis variable")
        placeholders = {
            field_name
            for _, field_name, _, _ in Formatter().parse(self.statement)
            if field_name is not None
        }
        if placeholders != set(variables):
            raise LearningError(
                f"hypothesis template {self.id!r} placeholders must exactly match variables"
            )
        _text_tuple(self.preconditions, "hypothesis preconditions")
        _required(self.expected_safe_behaviour, "expected safe behaviour")
        _required(self.expected_vulnerable_behaviour, "expected vulnerable behaviour")
        _required(self.falsifier, "hypothesis falsifier")
        _text_tuple(self.stop_conditions, "hypothesis stop conditions")

    def instantiate(self, values: Mapping[str, str]) -> str:
        if set(values) != set(self.variables):
            raise LearningError(
                f"hypothesis values must exactly match {sorted(self.variables)!r}"
            )
        clean = {name: _required(value, f"hypothesis value {name}") for name, value in values.items()}
        return self.statement.format(**clean)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> HypothesisTemplate:
        return cls(
            id=data["id"],
            statement=data["statement"],
            variables=_text_tuple(data.get("variables"), "hypothesis variables"),
            preconditions=_text_tuple(data.get("preconditions"), "hypothesis preconditions"),
            expected_safe_behaviour=data["expected_safe_behaviour"],
            expected_vulnerable_behaviour=data["expected_vulnerable_behaviour"],
            falsifier=data["falsifier"],
            stop_conditions=_text_tuple(data.get("stop_conditions"), "hypothesis stop conditions"),
        )


@dataclass(frozen=True)
class EvidenceRequirement(SerializableRecord):
    role: str
    description: str
    accepted_provenance: tuple[str, ...]
    check_required: bool = False
    human_attestation_required: bool = False

    def __post_init__(self) -> None:
        _safe_id(self.role, "evidence role")
        _required(self.description, "evidence description")
        provenance = _text_tuple(self.accepted_provenance, "accepted provenance")
        unknown = set(provenance) - ALLOWED_PROVENANCE
        if unknown:
            raise LearningError(f"unknown evidence provenance: {sorted(unknown)!r}")
        if self.check_required and "checked" not in provenance:
            raise LearningError("check-required evidence must accept checked provenance")
        if self.human_attestation_required and "attested" not in provenance:
            raise LearningError("human-attested evidence must accept attested provenance")

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> EvidenceRequirement:
        return cls(
            role=data["role"],
            description=data["description"],
            accepted_provenance=_text_tuple(
                data.get("accepted_provenance"), "accepted provenance"
            ),
            check_required=data.get("check_required") is True,
            human_attestation_required=data.get("human_attestation_required") is True,
        )


@dataclass(frozen=True)
class LocalFixtureReference(SerializableRecord):
    id: str
    relative_path: str

    def __post_init__(self) -> None:
        _safe_id(self.id, "local fixture id")
        path = str(self.relative_path or "").replace("\\", "/")
        if not path or path.startswith("/") or ".." in path.split("/"):
            raise LearningError("local fixture path must stay inside the catalogue data root")
        if not path.endswith(".json"):
            raise LearningError("local fixture path must name a JSON manifest")

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> LocalFixtureReference:
        return cls(id=data["id"], relative_path=data["relative_path"])


@dataclass(frozen=True)
class CardRevision(SerializableRecord):
    version: str
    date: date
    summary: str
    source_kind: str
    source_refs: tuple[str, ...]

    def __post_init__(self) -> None:
        _required(self.version, "card revision version")
        _required(self.summary, "card revision summary")
        if self.source_kind not in {"curated_reference", "test_fixture", "human_review"}:
            raise LearningError(f"unsupported card revision source {self.source_kind!r}")
        _text_tuple(self.source_refs, "card revision source references")

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> CardRevision:
        return cls(
            version=data["version"],
            date=date.fromisoformat(data["date"]),
            summary=data["summary"],
            source_kind=data["source_kind"],
            source_refs=_text_tuple(data.get("source_refs"), "card revision source references"),
        )


@dataclass(frozen=True)
class CardUpdateProposal(SerializableRecord):
    """Evidence-bound proposal; it cannot mutate the canonical catalogue."""

    id: str
    card_id: str
    status: str
    change: str
    checked_claim_ref: str
    evidence_refs: tuple[str, ...]
    source_kind: str = "test_fixture"

    def __post_init__(self) -> None:
        _safe_id(self.id, "card update proposal id")
        _safe_id(self.card_id, "card update proposal card id")
        if self.status != "proposed":
            raise LearningError("card updates enter the learning system as proposals")
        _required(self.change, "card update change")
        _safe_id(self.checked_claim_ref, "checked claim reference")
        _text_tuple(self.evidence_refs, "card update evidence references")
        if self.source_kind not in {"test_fixture", "human_review"}:
            raise LearningError("card update source must be explicit")

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> CardUpdateProposal:
        return cls(
            id=data["id"],
            card_id=data["card_id"],
            status=data["status"],
            change=data["change"],
            checked_claim_ref=data["checked_claim_ref"],
            evidence_refs=_text_tuple(
                data.get("evidence_refs"), "card update evidence references"
            ),
            source_kind=data.get("source_kind", "test_fixture"),
        )


@dataclass(frozen=True)
class VulnerabilityCard(SerializableRecord):
    id: str
    version: str
    name: str
    aliases: tuple[str, ...]
    framework_references: tuple[FrameworkReference, ...]
    mental_model: str
    security_property: str
    root_causes: tuple[str, ...]
    application_shapes: tuple[str, ...]
    prerequisite_card_ids: tuple[str, ...]
    prerequisite_skills: tuple[str, ...]
    signals: tuple[str, ...]
    hypothesis_templates: tuple[HypothesisTemplate, ...]
    safe_test_pattern: str
    positive_controls: tuple[str, ...]
    negative_controls: tuple[str, ...]
    falsifiers: tuple[str, ...]
    minimum_evidence: tuple[EvidenceRequirement, ...]
    common_false_positives: tuple[str, ...]
    impact_boundaries: tuple[str, ...]
    minimum_impact_rules: tuple[str, ...]
    remediation: tuple[str, ...]
    programme_policy_considerations: tuple[str, ...]
    local_fixture: LocalFixtureReference
    completed_lab_refs: tuple[str, ...]
    real_session_refs: tuple[str, ...]
    mastery_dimensions: tuple[MasteryDimension, ...]
    review_date: date
    lessons: tuple[str, ...]
    revisions: tuple[CardRevision, ...]

    def __post_init__(self) -> None:
        _safe_id(self.id, "vulnerability card id")
        _required(self.version, "vulnerability card version")
        _required(self.name, "vulnerability card name")
        _text_tuple(self.aliases, "card aliases", allow_empty=True)
        if not self.framework_references:
            raise LearningError("a card requires at least one framework reference")
        _required(self.mental_model, "card mental model")
        _required(self.security_property, "card security property")
        for label, values in (
            ("root causes", self.root_causes),
            ("application shapes", self.application_shapes),
            ("prerequisite skills", self.prerequisite_skills),
            ("signals", self.signals),
            ("positive controls", self.positive_controls),
            ("negative controls", self.negative_controls),
            ("falsifiers", self.falsifiers),
            ("common false positives", self.common_false_positives),
            ("impact boundaries", self.impact_boundaries),
            ("minimum-impact rules", self.minimum_impact_rules),
            ("remediation", self.remediation),
            ("programme-policy considerations", self.programme_policy_considerations),
        ):
            _text_tuple(values, label)
        for prerequisite in self.prerequisite_card_ids:
            _safe_id(prerequisite, "prerequisite card id")
        if self.id in self.prerequisite_card_ids:
            raise LearningError("a card cannot be its own prerequisite")
        if not self.hypothesis_templates:
            raise LearningError("a card requires a falsifiable hypothesis template")
        _required(self.safe_test_pattern, "safe test pattern")
        roles = {item.role for item in self.minimum_evidence}
        required_roles = {"behaviour", "boundary", "control", "reproduction", "impact"}
        if not required_roles.issubset(roles):
            raise LearningError(
                f"card minimum evidence is missing roles {sorted(required_roles - roles)!r}"
            )
        expected_dimensions = tuple(MasteryDimension)
        if tuple(self.mastery_dimensions) != expected_dimensions:
            raise LearningError("cards must expose all six mastery dimensions in canonical order")
        if not self.revisions:
            raise LearningError("a card requires revision provenance")

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> VulnerabilityCard:
        return cls(
            id=data["id"],
            version=data["version"],
            name=data["name"],
            aliases=_text_tuple(data.get("aliases"), "card aliases", allow_empty=True),
            framework_references=tuple(
                FrameworkReference.from_dict(item)
                for item in data.get("framework_references", ())
            ),
            mental_model=data["mental_model"],
            security_property=data["security_property"],
            root_causes=_text_tuple(data.get("root_causes"), "root causes"),
            application_shapes=_text_tuple(
                data.get("application_shapes"), "application shapes"
            ),
            prerequisite_card_ids=_text_tuple(
                data.get("prerequisite_card_ids"),
                "prerequisite card ids",
                allow_empty=True,
            ),
            prerequisite_skills=_text_tuple(
                data.get("prerequisite_skills"), "prerequisite skills"
            ),
            signals=_text_tuple(data.get("signals"), "signals"),
            hypothesis_templates=tuple(
                HypothesisTemplate.from_dict(item)
                for item in data.get("hypothesis_templates", ())
            ),
            safe_test_pattern=data["safe_test_pattern"],
            positive_controls=_text_tuple(data.get("positive_controls"), "positive controls"),
            negative_controls=_text_tuple(data.get("negative_controls"), "negative controls"),
            falsifiers=_text_tuple(data.get("falsifiers"), "falsifiers"),
            minimum_evidence=tuple(
                EvidenceRequirement.from_dict(item)
                for item in data.get("minimum_evidence", ())
            ),
            common_false_positives=_text_tuple(
                data.get("common_false_positives"), "common false positives"
            ),
            impact_boundaries=_text_tuple(
                data.get("impact_boundaries"), "impact boundaries"
            ),
            minimum_impact_rules=_text_tuple(
                data.get("minimum_impact_rules"), "minimum-impact rules"
            ),
            remediation=_text_tuple(data.get("remediation"), "remediation"),
            programme_policy_considerations=_text_tuple(
                data.get("programme_policy_considerations"),
                "programme-policy considerations",
            ),
            local_fixture=LocalFixtureReference.from_dict(data["local_fixture"]),
            completed_lab_refs=_text_tuple(
                data.get("completed_lab_refs"), "completed lab refs", allow_empty=True
            ),
            real_session_refs=_text_tuple(
                data.get("real_session_refs"), "real session refs", allow_empty=True
            ),
            mastery_dimensions=tuple(
                MasteryDimension(item) for item in data.get("mastery_dimensions", ())
            ),
            review_date=date.fromisoformat(data["review_date"]),
            lessons=_text_tuple(data.get("lessons"), "card lessons", allow_empty=True),
            revisions=tuple(
                CardRevision.from_dict(item) for item in data.get("revisions", ())
            ),
        )


@dataclass(frozen=True)
class MasteryAssessment(SerializableRecord):
    id: str
    card_id: str
    dimension: MasteryDimension
    level: MasteryLevel
    assessor: str
    assessor_kind: AssessorKind
    evidence_refs: tuple[str, ...]
    rationale: str
    assessed_at: datetime
    review_due: date

    def __post_init__(self) -> None:
        _safe_id(self.id, "mastery assessment id")
        _safe_id(self.card_id, "mastery card id")
        if self.level is MasteryLevel.NOT_ASSESSED:
            raise LearningError("not-assessed is derived state, not a recordable assessment")
        _required(self.assessor, "mastery assessor")
        if self.assessor_kind is AssessorKind.HUMAN and re.search(
            r"\b(model|agent|assistant|llm|ai)\b", self.assessor, re.IGNORECASE
        ):
            raise LearningError("a model or agent cannot be recorded as a human assessor")
        _text_tuple(self.evidence_refs, "mastery evidence references")
        _required(self.rationale, "mastery assessment rationale")
        _aware(self.assessed_at, "mastery assessment time")
        if self.review_due < self.assessed_at.date():
            raise LearningError("mastery review date cannot precede assessment")

    @property
    def credits_mastery(self) -> bool:
        return self.assessor_kind is AssessorKind.HUMAN

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> MasteryAssessment:
        assessed_at = datetime.fromisoformat(data["assessed_at"])
        return cls(
            id=data["id"],
            card_id=data["card_id"],
            dimension=MasteryDimension(data["dimension"]),
            level=MasteryLevel.parse(data["level"]),
            assessor=data["assessor"],
            assessor_kind=AssessorKind(data["assessor_kind"]),
            evidence_refs=_text_tuple(data.get("evidence_refs"), "mastery evidence references"),
            rationale=data["rationale"],
            assessed_at=assessed_at,
            review_due=date.fromisoformat(data["review_due"]),
        )


@dataclass(frozen=True)
class MasteryState(SerializableRecord):
    card_id: str
    dimension: MasteryDimension
    level: MasteryLevel
    assessment_id: str | None = None
    review_due: date | None = None


__all__ = [
    "AssessorKind",
    "CardRevision",
    "CardUpdateProposal",
    "EvidenceRequirement",
    "FrameworkReference",
    "HypothesisTemplate",
    "LearningError",
    "LocalFixtureReference",
    "MasteryAssessment",
    "MasteryDimension",
    "MasteryLevel",
    "MasteryState",
    "VulnerabilityCard",
]
