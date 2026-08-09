"""Typed records for a complete, authority-bound research session.

These records describe research.  They do not execute it.  The Authority
Plane remains the only component that can decide whether an action may occur,
and :class:`ActionRequest` only provides a bridge into that existing gate.

The records deliberately have no generic ``notes`` or credential-value fields.
Every free-text field has a research meaning, controlled identities carry only
credential references, and every record is bound to one workspace and contract
fingerprint.
"""

# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 ChaseInTech

from __future__ import annotations

import re
from dataclasses import dataclass, fields
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Mapping

from greytheory.authority.gate import AccessRequest, AuthorityLevel, Decision
from greytheory.authority.scope import ScopeClassification

SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,191}$")
SHA256 = re.compile(r"^[a-f0-9]{64}$")
SENSITIVE_METADATA = re.compile(
    r"(^|[-_.])(authorization|cookie|password|passwd|secret|token|api[-_]?key)"
    r"($|[-_.])",
    re.IGNORECASE,
)


class ResearchDomainError(ValueError):
    """Raised when a research record would violate a domain invariant."""


class WorkspaceStatus(str, Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"


class SessionStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    COMPLETED = "completed"
    ABORTED = "aborted"


class AssetKind(str, Enum):
    DOMAIN = "domain"
    URL = "url"
    API = "api"
    ENDPOINT = "endpoint"
    REPOSITORY = "repository"
    PACKAGE = "package"
    APPLICATION = "application"
    MOBILE_CLIENT = "mobile_client"
    LOCAL_FIXTURE = "local_fixture"
    IDENTITY_PROVIDER = "identity_provider"
    ROLE = "role"
    ACCOUNT = "account"
    RESOURCE_CLASS = "resource_class"
    INTEGRATION = "integration"
    STORAGE_SYSTEM = "storage_system"
    AGENT = "agent"
    TOOL = "tool"
    MCP_SERVER = "mcp_server"


class RelationshipKind(str, Enum):
    CALLS = "calls"
    TRUSTS = "trusts"
    OWNS = "owns"
    MAY_ACCESS = "may_access"
    INVOKES = "invokes"
    SENDS_DATA_TO = "sends_data_to"
    BUILDS = "builds"
    DEPLOYS_TO = "deploys_to"
    AUTHENTICATES_WITH = "authenticates_with"
    CONTAINS = "contains"


class HypothesisStatus(str, Enum):
    DRAFT = "draft"
    SCOPED = "scoped"
    PLANNED = "planned"
    TESTING = "testing"
    SUPPORTED = "supported"
    REFUTED = "refuted"
    INCONCLUSIVE = "inconclusive"
    CONVERTED_TO_FINDING = "converted_to_finding"
    CONVERTED_TO_LESSON = "converted_to_lesson"


class ExperimentStatus(str, Enum):
    DRAFT = "draft"
    READY = "ready"
    ACTIVE = "active"
    COMPLETED = "completed"
    STOPPED = "stopped"


HYPOTHESIS_TRANSITIONS: dict[HypothesisStatus, set[HypothesisStatus]] = {
    HypothesisStatus.DRAFT: {HypothesisStatus.SCOPED},
    HypothesisStatus.SCOPED: {
        HypothesisStatus.PLANNED,
        HypothesisStatus.REFUTED,
        HypothesisStatus.INCONCLUSIVE,
    },
    HypothesisStatus.PLANNED: {
        HypothesisStatus.TESTING,
        HypothesisStatus.REFUTED,
        HypothesisStatus.INCONCLUSIVE,
    },
    HypothesisStatus.TESTING: {
        HypothesisStatus.SUPPORTED,
        HypothesisStatus.REFUTED,
        HypothesisStatus.INCONCLUSIVE,
    },
    HypothesisStatus.SUPPORTED: {
        HypothesisStatus.CONVERTED_TO_FINDING,
        HypothesisStatus.CONVERTED_TO_LESSON,
    },
    HypothesisStatus.REFUTED: {HypothesisStatus.CONVERTED_TO_LESSON},
    HypothesisStatus.INCONCLUSIVE: {HypothesisStatus.CONVERTED_TO_LESSON},
    HypothesisStatus.CONVERTED_TO_FINDING: set(),
    HypothesisStatus.CONVERTED_TO_LESSON: set(),
}

EXPERIMENT_TRANSITIONS: dict[ExperimentStatus, set[ExperimentStatus]] = {
    ExperimentStatus.DRAFT: {ExperimentStatus.READY},
    ExperimentStatus.READY: {ExperimentStatus.ACTIVE, ExperimentStatus.STOPPED},
    ExperimentStatus.ACTIVE: {
        ExperimentStatus.COMPLETED,
        ExperimentStatus.STOPPED,
    },
    ExperimentStatus.COMPLETED: set(),
    ExperimentStatus.STOPPED: set(),
}


def _safe_id(value: str, label: str) -> str:
    text = str(value or "").strip()
    if not SAFE_ID.fullmatch(text):
        raise ResearchDomainError(f"{label} {value!r} is not a safe identifier")
    return text


def _required(value: str, label: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ResearchDomainError(f"{label} is required")
    return text


def _authority(value: str) -> str:
    text = _required(value, "authority reference")
    if not SHA256.fullmatch(text):
        raise ResearchDomainError(
            "authority reference must be a lowercase SHA-256 contract fingerprint"
        )
    return text


def _aware(value: datetime | None, label: str) -> datetime | None:
    if value is not None and value.tzinfo is None:
        raise ResearchDomainError(f"{label} must be timezone-aware")
    return value


def _parse_dt(value: Any) -> datetime | None:
    if value is None:
        return None
    parsed = value if isinstance(value, datetime) else datetime.fromisoformat(str(value))
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def _text_tuple(values: Any, label: str, *, allow_empty: bool = True) -> tuple[str, ...]:
    result = tuple(str(value).strip() for value in (values or ()))
    if any(not value for value in result):
        raise ResearchDomainError(f"{label} cannot contain empty values")
    if not allow_empty and not result:
        raise ResearchDomainError(f"{label} must contain at least one value")
    return result


def _encode(value: Any) -> Any:
    if isinstance(value, AuthorityLevel):
        return value.name
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, EffectBudget):
        return value.to_dict()
    if isinstance(value, tuple):
        return [_encode(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _encode(item) for key, item in value.items()}
    return value


class SerializableRecord:
    def to_dict(self) -> dict[str, Any]:
        return {item.name: _encode(getattr(self, item.name)) for item in fields(self)}


@dataclass(frozen=True)
class EffectBudget:
    """Named, non-negative effect limits or actual effect counts."""

    limits: tuple[tuple[str, int], ...] = ()

    def __post_init__(self) -> None:
        normalised: list[tuple[str, int]] = []
        seen: set[str] = set()
        for name, amount in self.limits:
            key = _safe_id(name, "effect name")
            if key in seen:
                raise ResearchDomainError(f"duplicate effect limit {key!r}")
            if isinstance(amount, bool) or int(amount) != amount or amount < 0:
                raise ResearchDomainError("effect limits must be non-negative integers")
            seen.add(key)
            normalised.append((key, int(amount)))
        object.__setattr__(self, "limits", tuple(sorted(normalised)))

    @classmethod
    def from_mapping(cls, values: Mapping[str, int] | None = None) -> EffectBudget:
        return cls(tuple((str(key), value) for key, value in (values or {}).items()))

    @classmethod
    def from_dict(cls, data: Mapping[str, Any] | None) -> EffectBudget:
        return cls.from_mapping((data or {}).get("limits", data or {}))

    def to_dict(self) -> dict[str, int]:
        return dict(self.limits)

    def value(self, effect: str) -> int:
        return dict(self.limits).get(effect, 0)

    def allows(self, actual: EffectBudget) -> bool:
        permitted = dict(self.limits)
        return all(amount <= permitted.get(name, 0) for name, amount in actual.limits)

    def plus(self, other: EffectBudget) -> EffectBudget:
        combined = dict(self.limits)
        for name, amount in other.limits:
            combined[name] = combined.get(name, 0) + amount
        return EffectBudget.from_mapping(combined)


@dataclass(frozen=True)
class ResearchWorkspace(SerializableRecord):
    id: str
    programme_id: str
    contract_id: str
    authority_ref: str
    title: str
    operating_posture: AuthorityLevel
    request_budget: int
    time_budget_minutes: int
    effect_budget: EffectBudget
    goals: tuple[str, ...]
    created_at: datetime
    unresolved_questions: tuple[str, ...] = ()
    status: WorkspaceStatus = WorkspaceStatus.ACTIVE

    def __post_init__(self) -> None:
        _safe_id(self.id, "workspace id")
        _safe_id(self.programme_id, "programme id")
        _safe_id(self.contract_id, "contract id")
        _authority(self.authority_ref)
        _required(self.title, "workspace title")
        if self.request_budget < 0 or self.time_budget_minutes < 0:
            raise ResearchDomainError("workspace budgets cannot be negative")
        _text_tuple(self.goals, "workspace goals", allow_empty=False)
        _text_tuple(self.unresolved_questions, "unresolved questions")
        _aware(self.created_at, "workspace creation time")

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> ResearchWorkspace:
        return cls(
            id=data["id"],
            programme_id=data["programme_id"],
            contract_id=data["contract_id"],
            authority_ref=data["authority_ref"],
            title=data["title"],
            operating_posture=AuthorityLevel.parse(data["operating_posture"]),
            request_budget=int(data["request_budget"]),
            time_budget_minutes=int(data["time_budget_minutes"]),
            effect_budget=EffectBudget.from_dict(data.get("effect_budget")),
            goals=_text_tuple(data.get("goals"), "workspace goals", allow_empty=False),
            created_at=_parse_dt(data["created_at"]),
            unresolved_questions=_text_tuple(
                data.get("unresolved_questions"), "unresolved questions"
            ),
            status=WorkspaceStatus(data.get("status", "active")),
        )


@dataclass(frozen=True)
class ResearchSession(SerializableRecord):
    id: str
    workspace_id: str
    authority_ref: str
    goal: str
    operating_posture: AuthorityLevel
    identity_ids: tuple[str, ...]
    request_budget: int
    time_budget_minutes: int
    effect_budget: EffectBudget
    created_at: datetime
    status: SessionStatus = SessionStatus.DRAFT
    started_at: datetime | None = None
    ended_at: datetime | None = None
    time_spent_minutes: int = 0
    checked_evidence_refs: tuple[str, ...] = ()
    outcome_summary: str = ""

    def __post_init__(self) -> None:
        _safe_id(self.id, "session id")
        _safe_id(self.workspace_id, "workspace id")
        _authority(self.authority_ref)
        _required(self.goal, "session goal")
        for identity_id in self.identity_ids:
            _safe_id(identity_id, "identity id")
        if self.request_budget < 0 or self.time_budget_minutes < 0:
            raise ResearchDomainError("session budgets cannot be negative")
        if self.time_spent_minutes < 0:
            raise ResearchDomainError("time spent cannot be negative")
        if self.time_spent_minutes > self.time_budget_minutes:
            raise ResearchDomainError("time spent exceeds the session time budget")
        _aware(self.created_at, "session creation time")
        _aware(self.started_at, "session start time")
        _aware(self.ended_at, "session end time")
        _text_tuple(self.checked_evidence_refs, "checked evidence references")
        if self.status is SessionStatus.DRAFT and self.started_at is not None:
            raise ResearchDomainError("a draft session cannot have a start time")
        if self.status is SessionStatus.ACTIVE and self.started_at is None:
            raise ResearchDomainError("an active session requires a start time")
        if self.status in {SessionStatus.COMPLETED, SessionStatus.ABORTED}:
            if self.started_at is None or self.ended_at is None:
                raise ResearchDomainError("a closed session requires start and end times")
            if self.ended_at < self.started_at:
                raise ResearchDomainError("session end time cannot precede its start")

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> ResearchSession:
        return cls(
            id=data["id"],
            workspace_id=data["workspace_id"],
            authority_ref=data["authority_ref"],
            goal=data["goal"],
            operating_posture=AuthorityLevel.parse(data["operating_posture"]),
            identity_ids=_text_tuple(data.get("identity_ids"), "identity ids"),
            request_budget=int(data["request_budget"]),
            time_budget_minutes=int(data["time_budget_minutes"]),
            effect_budget=EffectBudget.from_dict(data.get("effect_budget")),
            created_at=_parse_dt(data["created_at"]),
            status=SessionStatus(data.get("status", "draft")),
            started_at=_parse_dt(data.get("started_at")),
            ended_at=_parse_dt(data.get("ended_at")),
            time_spent_minutes=int(data.get("time_spent_minutes", 0)),
            checked_evidence_refs=_text_tuple(
                data.get("checked_evidence_refs"), "checked evidence references"
            ),
            outcome_summary=data.get("outcome_summary", ""),
        )


@dataclass(frozen=True)
class TargetAsset(SerializableRecord):
    id: str
    workspace_id: str
    authority_ref: str
    kind: AssetKind
    canonical_identifier: str
    scope_classification: ScopeClassification
    display_name: str
    discovered_from_id: str | None = None
    classification_evidence_ref: str = ""

    def __post_init__(self) -> None:
        _safe_id(self.id, "asset id")
        _safe_id(self.workspace_id, "workspace id")
        _authority(self.authority_ref)
        _required(self.canonical_identifier, "canonical asset identifier")
        _required(self.display_name, "asset display name")
        if self.discovered_from_id is not None:
            _safe_id(self.discovered_from_id, "discovery asset id")
        _required(self.classification_evidence_ref, "classification evidence reference")

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> TargetAsset:
        return cls(
            id=data["id"],
            workspace_id=data["workspace_id"],
            authority_ref=data["authority_ref"],
            kind=AssetKind(data["kind"]),
            canonical_identifier=data["canonical_identifier"],
            scope_classification=ScopeClassification(data["scope_classification"]),
            display_name=data["display_name"],
            discovered_from_id=data.get("discovered_from_id"),
            classification_evidence_ref=data.get("classification_evidence_ref", ""),
        )


@dataclass(frozen=True)
class AssetRelationship(SerializableRecord):
    id: str
    workspace_id: str
    authority_ref: str
    source_asset_id: str
    kind: RelationshipKind
    target_asset_id: str
    basis: str
    evidence_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _safe_id(self.id, "relationship id")
        _safe_id(self.workspace_id, "workspace id")
        _authority(self.authority_ref)
        _safe_id(self.source_asset_id, "source asset id")
        _safe_id(self.target_asset_id, "target asset id")
        if self.source_asset_id == self.target_asset_id:
            raise ResearchDomainError("an asset relationship cannot be self-referential")
        _required(self.basis, "relationship basis")
        _text_tuple(self.evidence_refs, "relationship evidence references")

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> AssetRelationship:
        return cls(
            id=data["id"],
            workspace_id=data["workspace_id"],
            authority_ref=data["authority_ref"],
            source_asset_id=data["source_asset_id"],
            kind=RelationshipKind(data["kind"]),
            target_asset_id=data["target_asset_id"],
            basis=data["basis"],
            evidence_refs=_text_tuple(data.get("evidence_refs"), "evidence references"),
        )


@dataclass(frozen=True)
class ResearchIdentity(SerializableRecord):
    id: str
    workspace_id: str
    programme_id: str
    authority_ref: str
    role: str
    ownership_attestation_ref: str
    credential_ref: str
    permitted_uses: tuple[str, ...]
    created_at: datetime
    expires_at: datetime | None = None
    required_researcher_marker: str = ""
    synthetic_object_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _safe_id(self.id, "identity id")
        _safe_id(self.workspace_id, "workspace id")
        _safe_id(self.programme_id, "programme id")
        _authority(self.authority_ref)
        _required(self.role, "identity role")
        _safe_id(self.ownership_attestation_ref, "ownership attestation reference")
        _safe_id(self.credential_ref, "credential reference")
        _text_tuple(self.permitted_uses, "permitted uses", allow_empty=False)
        for object_id in self.synthetic_object_ids:
            _safe_id(object_id, "synthetic object id")
        _aware(self.created_at, "identity creation time")
        _aware(self.expires_at, "identity expiry time")
        if self.expires_at is not None and self.expires_at <= self.created_at:
            raise ResearchDomainError("identity expiry must follow creation")

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> ResearchIdentity:
        return cls(
            id=data["id"],
            workspace_id=data["workspace_id"],
            programme_id=data["programme_id"],
            authority_ref=data["authority_ref"],
            role=data["role"],
            ownership_attestation_ref=data["ownership_attestation_ref"],
            credential_ref=data["credential_ref"],
            permitted_uses=_text_tuple(
                data.get("permitted_uses"), "permitted uses", allow_empty=False
            ),
            created_at=_parse_dt(data["created_at"]),
            expires_at=_parse_dt(data.get("expires_at")),
            required_researcher_marker=data.get("required_researcher_marker", ""),
            synthetic_object_ids=_text_tuple(
                data.get("synthetic_object_ids"), "synthetic object ids"
            ),
        )


@dataclass(frozen=True)
class Hypothesis(SerializableRecord):
    id: str
    workspace_id: str
    session_id: str
    authority_ref: str
    title: str
    preconditions: tuple[str, ...]
    actor_identity_id: str | None
    action: str
    target_asset_id: str
    consequence: str
    reasoning: str
    supporting_observation_refs: tuple[str, ...]
    assumptions: tuple[str, ...]
    required_authority: AuthorityLevel
    expected_safe_behaviour: str
    expected_vulnerable_behaviour: str
    falsifier: str
    evidence_needs: tuple[str, ...]
    stop_conditions: tuple[str, ...]
    estimated_request_cost: int
    estimated_time_minutes: int
    estimated_effects: EffectBudget
    duplicate_risk: str
    learning_value: str
    status: HypothesisStatus = HypothesisStatus.DRAFT
    result_summary: str = ""
    result_refs: tuple[str, ...] = ()
    finding_ref: str | None = None
    lesson_ref: str | None = None

    def __post_init__(self) -> None:
        _safe_id(self.id, "hypothesis id")
        _safe_id(self.workspace_id, "workspace id")
        _safe_id(self.session_id, "session id")
        _authority(self.authority_ref)
        _required(self.title, "hypothesis title")
        _text_tuple(self.preconditions, "hypothesis preconditions", allow_empty=False)
        if self.actor_identity_id is not None:
            _safe_id(self.actor_identity_id, "actor identity id")
        _required(self.action, "hypothesis action")
        _safe_id(self.target_asset_id, "hypothesis target asset id")
        _required(self.consequence, "hypothesis consequence")
        _required(self.reasoning, "hypothesis reasoning")
        _text_tuple(self.supporting_observation_refs, "supporting observation references")
        _text_tuple(self.assumptions, "hypothesis assumptions", allow_empty=False)
        _required(self.expected_safe_behaviour, "expected safe behaviour")
        _required(self.expected_vulnerable_behaviour, "expected vulnerable behaviour")
        _required(self.falsifier, "hypothesis falsifier")
        _text_tuple(self.evidence_needs, "evidence needs", allow_empty=False)
        _text_tuple(self.stop_conditions, "hypothesis stop conditions", allow_empty=False)
        if self.estimated_request_cost < 0 or self.estimated_time_minutes < 0:
            raise ResearchDomainError("hypothesis cost estimates cannot be negative")
        _required(self.duplicate_risk, "duplicate risk")
        _required(self.learning_value, "learning value")
        _text_tuple(self.result_refs, "hypothesis result references")
        if self.status is HypothesisStatus.CONVERTED_TO_FINDING and not self.finding_ref:
            raise ResearchDomainError("conversion to a finding requires a finding reference")
        if self.status is HypothesisStatus.CONVERTED_TO_LESSON and not self.lesson_ref:
            raise ResearchDomainError("conversion to a lesson requires a lesson reference")

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> Hypothesis:
        return cls(
            id=data["id"],
            workspace_id=data["workspace_id"],
            session_id=data["session_id"],
            authority_ref=data["authority_ref"],
            title=data["title"],
            preconditions=_text_tuple(
                data.get("preconditions"), "preconditions", allow_empty=False
            ),
            actor_identity_id=data.get("actor_identity_id"),
            action=data["action"],
            target_asset_id=data["target_asset_id"],
            consequence=data["consequence"],
            reasoning=data["reasoning"],
            supporting_observation_refs=_text_tuple(
                data.get("supporting_observation_refs"), "observation references"
            ),
            assumptions=_text_tuple(
                data.get("assumptions"), "assumptions", allow_empty=False
            ),
            required_authority=AuthorityLevel.parse(data["required_authority"]),
            expected_safe_behaviour=data["expected_safe_behaviour"],
            expected_vulnerable_behaviour=data["expected_vulnerable_behaviour"],
            falsifier=data["falsifier"],
            evidence_needs=_text_tuple(
                data.get("evidence_needs"), "evidence needs", allow_empty=False
            ),
            stop_conditions=_text_tuple(
                data.get("stop_conditions"), "stop conditions", allow_empty=False
            ),
            estimated_request_cost=int(data["estimated_request_cost"]),
            estimated_time_minutes=int(data["estimated_time_minutes"]),
            estimated_effects=EffectBudget.from_dict(data.get("estimated_effects")),
            duplicate_risk=data["duplicate_risk"],
            learning_value=data["learning_value"],
            status=HypothesisStatus(data.get("status", "draft")),
            result_summary=data.get("result_summary", ""),
            result_refs=_text_tuple(data.get("result_refs"), "result references"),
            finding_ref=data.get("finding_ref"),
            lesson_ref=data.get("lesson_ref"),
        )


@dataclass(frozen=True)
class ExperimentPlan(SerializableRecord):
    id: str
    workspace_id: str
    session_id: str
    hypothesis_id: str
    authority_ref: str
    ordered_actions: tuple[str, ...]
    positive_controls: tuple[str, ...]
    negative_controls: tuple[str, ...]
    expected_outcomes: tuple[str, ...]
    required_authority: AuthorityLevel
    effect_budget: EffectBudget
    rollback_steps: tuple[str, ...]
    stop_conditions: tuple[str, ...]
    evidence_plan: tuple[str, ...]
    status: ExperimentStatus = ExperimentStatus.DRAFT
    outcome_summary: str = ""
    result_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _safe_id(self.id, "experiment id")
        _safe_id(self.workspace_id, "workspace id")
        _safe_id(self.session_id, "session id")
        _safe_id(self.hypothesis_id, "hypothesis id")
        _authority(self.authority_ref)
        _text_tuple(self.ordered_actions, "ordered actions", allow_empty=False)
        _text_tuple(self.positive_controls, "positive controls", allow_empty=False)
        _text_tuple(self.negative_controls, "negative controls", allow_empty=False)
        _text_tuple(self.expected_outcomes, "expected outcomes", allow_empty=False)
        _text_tuple(self.rollback_steps, "rollback steps", allow_empty=False)
        _text_tuple(self.stop_conditions, "experiment stop conditions", allow_empty=False)
        _text_tuple(self.evidence_plan, "evidence plan", allow_empty=False)
        _text_tuple(self.result_refs, "experiment result references")

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> ExperimentPlan:
        return cls(
            id=data["id"],
            workspace_id=data["workspace_id"],
            session_id=data["session_id"],
            hypothesis_id=data["hypothesis_id"],
            authority_ref=data["authority_ref"],
            ordered_actions=_text_tuple(
                data.get("ordered_actions"), "ordered actions", allow_empty=False
            ),
            positive_controls=_text_tuple(
                data.get("positive_controls"), "positive controls", allow_empty=False
            ),
            negative_controls=_text_tuple(
                data.get("negative_controls"), "negative controls", allow_empty=False
            ),
            expected_outcomes=_text_tuple(
                data.get("expected_outcomes"), "expected outcomes", allow_empty=False
            ),
            required_authority=AuthorityLevel.parse(data["required_authority"]),
            effect_budget=EffectBudget.from_dict(data.get("effect_budget")),
            rollback_steps=_text_tuple(
                data.get("rollback_steps"), "rollback steps", allow_empty=False
            ),
            stop_conditions=_text_tuple(
                data.get("stop_conditions"), "stop conditions", allow_empty=False
            ),
            evidence_plan=_text_tuple(
                data.get("evidence_plan"), "evidence plan", allow_empty=False
            ),
            status=ExperimentStatus(data.get("status", "draft")),
            outcome_summary=data.get("outcome_summary", ""),
            result_refs=_text_tuple(data.get("result_refs"), "result references"),
        )


@dataclass(frozen=True)
class ActionRequest(SerializableRecord):
    id: str
    workspace_id: str
    session_id: str
    experiment_id: str
    authority_ref: str
    action_type: str
    exact_action: str
    target_asset_id: str
    identity_id: str | None
    required_authority: AuthorityLevel
    purpose: str
    technique: str | None
    max_requests: int
    expected_effects: EffectBudget
    stop_conditions: tuple[str, ...]
    created_at: datetime
    approval_ref: str | None = None

    def __post_init__(self) -> None:
        _safe_id(self.id, "action request id")
        _safe_id(self.workspace_id, "workspace id")
        _safe_id(self.session_id, "session id")
        _safe_id(self.experiment_id, "experiment id")
        _authority(self.authority_ref)
        _safe_id(self.action_type, "action type")
        _required(self.exact_action, "exact action")
        _safe_id(self.target_asset_id, "target asset id")
        if self.identity_id is not None:
            _safe_id(self.identity_id, "identity id")
        _required(self.purpose, "action purpose")
        if self.technique is not None:
            _required(self.technique, "technique")
        if self.max_requests < 0:
            raise ResearchDomainError("maximum request count cannot be negative")
        _text_tuple(self.stop_conditions, "action stop conditions", allow_empty=False)
        _aware(self.created_at, "action request creation time")
        if self.approval_ref is not None:
            _safe_id(self.approval_ref, "approval reference")

    def to_access_request(self, asset: TargetAsset, *, actor: str) -> AccessRequest:
        """Translate intent into the existing gate shape without executing it."""
        if asset.id != self.target_asset_id or asset.workspace_id != self.workspace_id:
            raise ResearchDomainError("target asset does not match the action request")
        if asset.authority_ref != self.authority_ref:
            raise ResearchDomainError("target asset authority does not match the request")
        return AccessRequest(
            asset=asset.canonical_identifier,
            authority_level=self.required_authority,
            actor=_required(actor, "action actor"),
            technique=self.technique,
            purpose=self.purpose,
            action_type=self.action_type,
            approval_id=self.approval_ref,
        )

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> ActionRequest:
        return cls(
            id=data["id"],
            workspace_id=data["workspace_id"],
            session_id=data["session_id"],
            experiment_id=data["experiment_id"],
            authority_ref=data["authority_ref"],
            action_type=data["action_type"],
            exact_action=data["exact_action"],
            target_asset_id=data["target_asset_id"],
            identity_id=data.get("identity_id"),
            required_authority=AuthorityLevel.parse(data["required_authority"]),
            purpose=data["purpose"],
            technique=data.get("technique"),
            max_requests=int(data["max_requests"]),
            expected_effects=EffectBudget.from_dict(data.get("expected_effects")),
            stop_conditions=_text_tuple(
                data.get("stop_conditions"), "stop conditions", allow_empty=False
            ),
            created_at=_parse_dt(data["created_at"]),
            approval_ref=data.get("approval_ref"),
        )


MetadataValue = str | int | float | bool | None


def metadata_items(values: Mapping[str, MetadataValue] | None = None) -> tuple[tuple[str, MetadataValue], ...]:
    result: list[tuple[str, MetadataValue]] = []
    for key, value in (values or {}).items():
        name = _safe_id(str(key), "response metadata key")
        if SENSITIVE_METADATA.search(name):
            raise ResearchDomainError(
                f"sensitive response metadata key {name!r} is not permitted"
            )
        if value is not None and not isinstance(value, (str, int, float, bool)):
            raise ResearchDomainError("response metadata values must be JSON scalars")
        result.append((name, value))
    return tuple(sorted(result))


@dataclass(frozen=True)
class ActionReceipt(SerializableRecord):
    id: str
    workspace_id: str
    session_id: str
    request_id: str
    authority_ref: str
    exact_action: str
    worker: str
    tool_version: str
    gate_decision_ref: str
    approval_ref: str | None
    target_asset_id: str
    target_canonical_identifier: str
    identity_id: str | None
    started_at: datetime
    ended_at: datetime
    request_count: int
    redirects: tuple[str, ...]
    resolved_addresses: tuple[str, ...]
    response_metadata: tuple[tuple[str, MetadataValue], ...]
    output_hashes: tuple[str, ...]
    errors: tuple[str, ...]
    effects: EffectBudget
    stop_condition_fired: str | None = None

    def __post_init__(self) -> None:
        _safe_id(self.id, "action receipt id")
        _safe_id(self.workspace_id, "workspace id")
        _safe_id(self.session_id, "session id")
        _safe_id(self.request_id, "action request id")
        _authority(self.authority_ref)
        _required(self.exact_action, "receipt exact action")
        _safe_id(self.worker, "worker id")
        _required(self.tool_version, "tool version")
        _safe_id(self.gate_decision_ref, "gate decision reference")
        if self.approval_ref is not None:
            _safe_id(self.approval_ref, "approval reference")
        _safe_id(self.target_asset_id, "target asset id")
        _required(self.target_canonical_identifier, "target canonical identifier")
        if self.identity_id is not None:
            _safe_id(self.identity_id, "identity id")
        _aware(self.started_at, "action start time")
        _aware(self.ended_at, "action end time")
        if self.ended_at < self.started_at:
            raise ResearchDomainError("action end time cannot precede its start")
        if self.request_count < 0:
            raise ResearchDomainError("receipt request count cannot be negative")
        _text_tuple(self.redirects, "redirects")
        _text_tuple(self.resolved_addresses, "resolved addresses")
        object.__setattr__(self, "response_metadata", metadata_items(dict(self.response_metadata)))
        for digest in self.output_hashes:
            if not SHA256.fullmatch(digest):
                raise ResearchDomainError("output hashes must be lowercase SHA-256 digests")
        _text_tuple(self.errors, "receipt errors")
        if self.stop_condition_fired is not None:
            _required(self.stop_condition_fired, "fired stop condition")

    @classmethod
    def from_execution(
        cls,
        *,
        id: str,
        request: ActionRequest,
        asset: TargetAsset,
        decision: Decision,
        worker: str,
        tool_version: str,
        started_at: datetime,
        ended_at: datetime,
        request_count: int,
        redirects: tuple[str, ...] = (),
        resolved_addresses: tuple[str, ...] = (),
        response_metadata: Mapping[str, MetadataValue] | None = None,
        output_hashes: tuple[str, ...] = (),
        errors: tuple[str, ...] = (),
        effects: EffectBudget = EffectBudget(),
        stop_condition_fired: str | None = None,
    ) -> ActionReceipt:
        if not decision.allowed:
            raise ResearchDomainError("a denied gate decision cannot produce an execution receipt")
        if decision.authority_ref != request.authority_ref:
            raise ResearchDomainError("gate decision authority does not match the request")
        if decision.audit_seq is None:
            raise ResearchDomainError("gate decision must have an audit sequence")
        if asset.id != request.target_asset_id:
            raise ResearchDomainError("receipt asset does not match the request")
        return cls(
            id=id,
            workspace_id=request.workspace_id,
            session_id=request.session_id,
            request_id=request.id,
            authority_ref=request.authority_ref,
            exact_action=request.exact_action,
            worker=worker,
            tool_version=tool_version,
            gate_decision_ref=f"audit:{decision.audit_seq}",
            approval_ref=request.approval_ref,
            target_asset_id=asset.id,
            target_canonical_identifier=asset.canonical_identifier,
            identity_id=request.identity_id,
            started_at=started_at,
            ended_at=ended_at,
            request_count=request_count,
            redirects=redirects,
            resolved_addresses=resolved_addresses,
            response_metadata=metadata_items(response_metadata),
            output_hashes=output_hashes,
            errors=errors,
            effects=effects,
            stop_condition_fired=stop_condition_fired,
        )

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> ActionReceipt:
        return cls(
            id=data["id"],
            workspace_id=data["workspace_id"],
            session_id=data["session_id"],
            request_id=data["request_id"],
            authority_ref=data["authority_ref"],
            exact_action=data["exact_action"],
            worker=data["worker"],
            tool_version=data["tool_version"],
            gate_decision_ref=data["gate_decision_ref"],
            approval_ref=data.get("approval_ref"),
            target_asset_id=data["target_asset_id"],
            target_canonical_identifier=data["target_canonical_identifier"],
            identity_id=data.get("identity_id"),
            started_at=_parse_dt(data["started_at"]),
            ended_at=_parse_dt(data["ended_at"]),
            request_count=int(data["request_count"]),
            redirects=_text_tuple(data.get("redirects"), "redirects"),
            resolved_addresses=_text_tuple(
                data.get("resolved_addresses"), "resolved addresses"
            ),
            response_metadata=metadata_items(dict(data.get("response_metadata", ()))),
            output_hashes=_text_tuple(data.get("output_hashes"), "output hashes"),
            errors=_text_tuple(data.get("errors"), "errors"),
            effects=EffectBudget.from_dict(data.get("effects")),
            stop_condition_fired=data.get("stop_condition_fired"),
        )


@dataclass(frozen=True)
class Lesson(SerializableRecord):
    id: str
    workspace_id: str
    session_id: str
    authority_ref: str
    summary: str
    what_was_tested: tuple[str, ...]
    prioritisation_reason: str
    observation_refs: tuple[str, ...]
    disproved: tuple[str, ...]
    incorrect_assumptions: tuple[str, ...]
    result_change_conditions: tuple[str, ...]
    target_score_change: str
    vulnerability_card_updates: tuple[str, ...]
    next_actions: tuple[str, ...]
    created_at: datetime
    hypothesis_id: str | None = None

    def __post_init__(self) -> None:
        _safe_id(self.id, "lesson id")
        _safe_id(self.workspace_id, "workspace id")
        _safe_id(self.session_id, "session id")
        _authority(self.authority_ref)
        _required(self.summary, "lesson summary")
        _text_tuple(self.what_was_tested, "what was tested", allow_empty=False)
        _required(self.prioritisation_reason, "prioritisation reason")
        _text_tuple(self.observation_refs, "lesson observation references")
        _text_tuple(self.disproved, "disproved theories")
        _text_tuple(self.incorrect_assumptions, "incorrect assumptions")
        _text_tuple(self.result_change_conditions, "result change conditions")
        _required(self.target_score_change, "target score change")
        _text_tuple(self.vulnerability_card_updates, "vulnerability card updates")
        _text_tuple(self.next_actions, "next actions", allow_empty=False)
        _aware(self.created_at, "lesson creation time")
        if self.hypothesis_id is not None:
            _safe_id(self.hypothesis_id, "hypothesis id")

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> Lesson:
        return cls(
            id=data["id"],
            workspace_id=data["workspace_id"],
            session_id=data["session_id"],
            authority_ref=data["authority_ref"],
            summary=data["summary"],
            what_was_tested=_text_tuple(
                data.get("what_was_tested"), "what was tested", allow_empty=False
            ),
            prioritisation_reason=data["prioritisation_reason"],
            observation_refs=_text_tuple(
                data.get("observation_refs"), "observation references"
            ),
            disproved=_text_tuple(data.get("disproved"), "disproved theories"),
            incorrect_assumptions=_text_tuple(
                data.get("incorrect_assumptions"), "incorrect assumptions"
            ),
            result_change_conditions=_text_tuple(
                data.get("result_change_conditions"), "result change conditions"
            ),
            target_score_change=data["target_score_change"],
            vulnerability_card_updates=_text_tuple(
                data.get("vulnerability_card_updates"), "card updates"
            ),
            next_actions=_text_tuple(
                data.get("next_actions"), "next actions", allow_empty=False
            ),
            created_at=_parse_dt(data["created_at"]),
            hypothesis_id=data.get("hypothesis_id"),
        )


__all__ = [
    "ActionReceipt",
    "ActionRequest",
    "AssetKind",
    "AssetRelationship",
    "EffectBudget",
    "ExperimentPlan",
    "ExperimentStatus",
    "EXPERIMENT_TRANSITIONS",
    "HYPOTHESIS_TRANSITIONS",
    "Hypothesis",
    "HypothesisStatus",
    "Lesson",
    "RelationshipKind",
    "ResearchDomainError",
    "ResearchIdentity",
    "ResearchSession",
    "ResearchWorkspace",
    "SessionStatus",
    "TargetAsset",
    "WorkspaceStatus",
    "metadata_items",
]
