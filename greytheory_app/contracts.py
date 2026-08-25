"""Versioned, transport-neutral contracts for the local workbench."""

# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 ChaseInTech

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Mapping

from greytheory.authority.gate import AuthorityLevel


WORKBENCH_SCHEMA_VERSION = "greytheory.workbench.v1"
SAFE_ID = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_.:-]{0,191}$")


class WorkbenchContractError(ValueError):
    """Raised when UI/application data could weaken a boundary."""


class ReadinessStatus(str, Enum):
    READY = "ready"
    ATTENTION = "attention"
    BLOCKED = "blocked"
    EMPTY = "empty"
    UNKNOWN = "unknown"


class CommandKind(str, Enum):
    SELECT_WORKSPACE = "select_workspace"
    START_LEARNING_JOURNEY = "start_learning_journey"
    ADVANCE_LEARNING_JOURNEY = "advance_learning_journey"
    ABANDON_LEARNING_JOURNEY = "abandon_learning_journey"
    CREATE_HYPOTHESIS = "create_hypothesis"
    REVIEW_HYPOTHESIS_SCOPE = "review_hypothesis_scope"
    PLAN_EXPERIMENT = "plan_experiment"
    REQUEST_ACTION = "request_action"
    RECORD_MASTERY_ASSESSMENT = "record_mastery_assessment"
    CREATE_REPORT_CASE = "create_report_case"
    SAVE_REPORT_DRAFT = "save_report_draft"
    RUN_REPORT_VALIDATION = "run_report_validation"
    ASSEMBLE_LOCAL_FIXTURE_CLAIMS = "assemble_local_fixture_claims"
    ADVANCE_REPORT_FINDING = "advance_report_finding"
    EXPORT_REPORT = "export_report"


class CommandDisposition(str, Enum):
    ACCEPTED = "accepted"
    REFUSED = "refused"
    CONFLICT = "conflict"
    INVALID = "invalid"


def _required(value: str, label: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise WorkbenchContractError(f"{label} is required")
    return text


def _safe_id(value: str, label: str) -> str:
    text = _required(value, label)
    if not SAFE_ID.fullmatch(text):
        raise WorkbenchContractError(f"{label} {value!r} is not a safe identifier")
    return text


@dataclass(frozen=True)
class WorkbenchMetric:
    label: str
    value: str
    status: ReadinessStatus
    detail: str = ""
    source: str = ""

    def __post_init__(self) -> None:
        _required(self.label, "metric label")
        _required(self.value, "metric value")

    def to_dict(self) -> dict[str, str]:
        return {
            "label": self.label,
            "value": self.value,
            "status": self.status.value,
            "detail": self.detail,
            "source": self.source,
        }


@dataclass(frozen=True)
class WorkbenchRecord:
    id: str
    title: str
    status: ReadinessStatus
    subtitle: str = ""
    detail: str = ""
    references: tuple[str, ...] = ()
    attributes: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        _safe_id(self.id, "record id")
        _required(self.title, "record title")
        keys = [key for key, _ in self.attributes]
        if any(not str(key).strip() for key in keys) or len(keys) != len(set(keys)):
            raise WorkbenchContractError("record attribute names must be unique")
        if any(not str(ref).strip() for ref in self.references):
            raise WorkbenchContractError("record references cannot be empty")

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "status": self.status.value,
            "subtitle": self.subtitle,
            "detail": self.detail,
            "references": list(self.references),
            "attributes": {key: value for key, value in self.attributes},
        }


@dataclass(frozen=True)
class WorkbenchSection:
    id: str
    title: str
    status: ReadinessStatus
    metrics: tuple[WorkbenchMetric, ...] = ()
    records: tuple[WorkbenchRecord, ...] = ()
    note: str = ""

    def __post_init__(self) -> None:
        _safe_id(self.id, "section id")
        _required(self.title, "section title")
        record_ids = [record.id for record in self.records]
        if len(record_ids) != len(set(record_ids)):
            raise WorkbenchContractError(f"section {self.id!r} has duplicate record ids")

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "status": self.status.value,
            "metrics": [metric.to_dict() for metric in self.metrics],
            "records": [record.to_dict() for record in self.records],
            "note": self.note,
        }


@dataclass(frozen=True)
class WorkbenchContext:
    workspace_id: str | None = None
    session_id: str | None = None
    hypothesis_id: str | None = None
    finding_id: str | None = None
    learning_journey_id: str | None = None

    def __post_init__(self) -> None:
        for label, value in (
            ("workspace id", self.workspace_id),
            ("session id", self.session_id),
            ("hypothesis id", self.hypothesis_id),
            ("finding id", self.finding_id),
            ("learning journey id", self.learning_journey_id),
        ):
            if value is not None:
                _safe_id(value, label)

    def to_dict(self) -> dict[str, str | None]:
        return {
            "workspace_id": self.workspace_id,
            "session_id": self.session_id,
            "hypothesis_id": self.hypothesis_id,
            "finding_id": self.finding_id,
            "learning_journey_id": self.learning_journey_id,
        }


@dataclass(frozen=True)
class NextAction:
    id: str
    title: str
    reason: str
    route: str
    requires_human: bool = False
    executable: bool = False

    def __post_init__(self) -> None:
        _safe_id(self.id, "next-action id")
        _required(self.title, "next-action title")
        _required(self.reason, "next-action reason")
        if not str(self.route).startswith("/"):
            raise WorkbenchContractError("next-action route must be application-local")
        if self.executable:
            raise WorkbenchContractError(
                "a displayed next action is navigation or intent, never execution authority"
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "reason": self.reason,
            "route": self.route,
            "requires_human": self.requires_human,
            "executable": False,
        }


@dataclass(frozen=True)
class WorkbenchSnapshot:
    generated_at: datetime
    posture: AuthorityLevel
    context: WorkbenchContext
    next_action: NextAction
    sections: tuple[WorkbenchSection, ...]
    source_errors: tuple[str, ...] = ()
    schema_version: str = WORKBENCH_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.generated_at.tzinfo is None:
            raise WorkbenchContractError("snapshot time must be timezone-aware")
        if self.schema_version != WORKBENCH_SCHEMA_VERSION:
            raise WorkbenchContractError("unsupported workbench schema version")
        if self.posture > AuthorityLevel.LOCAL_FIXTURE:
            raise WorkbenchContractError(
                "the current workbench contract cannot represent live-target posture"
            )
        section_ids = [section.id for section in self.sections]
        if len(section_ids) != len(set(section_ids)):
            raise WorkbenchContractError("workbench section ids must be unique")

    @property
    def live_target_available(self) -> bool:
        return False

    def section(self, section_id: str) -> WorkbenchSection:
        for section in self.sections:
            if section.id == section_id:
                return section
        raise KeyError(section_id)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "generated_at": self.generated_at.isoformat(),
            "posture": self.posture.name,
            "live_target_available": False,
            "context": self.context.to_dict(),
            "next_action": self.next_action.to_dict(),
            "sections": [section.to_dict() for section in self.sections],
            "source_errors": list(self.source_errors),
        }


CommandValue = str | int | bool | None | tuple[str, ...]


@dataclass(frozen=True)
class CommandField:
    name: str
    value: CommandValue

    def __post_init__(self) -> None:
        _safe_id(self.name, "command field name")
        if isinstance(self.value, tuple) and any(
            not isinstance(item, str) or not item.strip() for item in self.value
        ):
            raise WorkbenchContractError(
                "command tuple values must be non-empty strings"
            )

    def to_dict(self) -> dict[str, Any]:
        return {self.name: list(self.value) if isinstance(self.value, tuple) else self.value}

    @classmethod
    def from_pair(cls, name: str, value: Any) -> CommandField:
        if isinstance(value, list):
            if any(not isinstance(item, str) for item in value):
                raise WorkbenchContractError(
                    "command list values may contain only strings"
                )
            value = tuple(value)
        if not (
            value is None
            or isinstance(value, (str, int, bool, tuple))
        ):
            raise WorkbenchContractError(
                f"command field {name!r} has an unsupported value type"
            )
        return cls(str(name), value)


@dataclass(frozen=True)
class WorkbenchCommand:
    id: str
    kind: CommandKind
    operator_ref: str
    issued_at: datetime
    idempotency_key: str
    fields: tuple[CommandField, ...] = ()
    workspace_id: str | None = None
    expected_revision: int | None = None
    requested_authority: AuthorityLevel = AuthorityLevel.NONE
    human_acknowledged: bool = False
    schema_version: str = WORKBENCH_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _safe_id(self.id, "command id")
        _safe_id(self.operator_ref, "operator reference")
        _safe_id(self.idempotency_key, "idempotency key")
        if self.issued_at.tzinfo is None:
            raise WorkbenchContractError("command time must be timezone-aware")
        if self.schema_version != WORKBENCH_SCHEMA_VERSION:
            raise WorkbenchContractError("unsupported command schema version")
        if self.workspace_id is not None:
            _safe_id(self.workspace_id, "command workspace id")
        if self.expected_revision is not None and (
            isinstance(self.expected_revision, bool)
            or not isinstance(self.expected_revision, int)
            or self.expected_revision < 0
        ):
            raise WorkbenchContractError(
                "expected revision must be a non-negative integer"
            )
        if self.requested_authority > AuthorityLevel.LOCAL_FIXTURE:
            raise WorkbenchContractError(
                "the current workbench refuses authority above LOCAL_FIXTURE"
            )
        names = [field.name for field in self.fields]
        if len(names) != len(set(names)):
            raise WorkbenchContractError("command field names must be unique")
        if self.kind is CommandKind.REQUEST_ACTION:
            required = {
                "action_type",
                "exact_action",
                "target_asset_id",
                "purpose",
                "max_requests",
            }
            missing = required - set(names)
            if missing:
                raise WorkbenchContractError(
                    f"action request command is missing fields {sorted(missing)!r}"
                )
            if not self.human_acknowledged:
                raise WorkbenchContractError(
                    "an action request intent requires explicit human acknowledgement"
                )
            if self.workspace_id is None:
                raise WorkbenchContractError(
                    "an action request intent requires a workspace"
                )
            if self.expected_revision != 0:
                raise WorkbenchContractError(
                    "creating an action request intent requires expected revision zero"
                )
            if self.requested_authority is not AuthorityLevel.LOCAL_FIXTURE:
                raise WorkbenchContractError(
                    "the current action-intent handler is limited to LOCAL_FIXTURE"
                )
        if self.kind is CommandKind.CREATE_HYPOTHESIS and self.expected_revision != 0:
            raise WorkbenchContractError(
                "creating a hypothesis requires expected revision zero"
            )
        if self.kind in {
            CommandKind.REVIEW_HYPOTHESIS_SCOPE,
            CommandKind.PLAN_EXPERIMENT,
        }:
            if self.expected_revision is None:
                raise WorkbenchContractError(
                    f"{self.kind.value} requires the current hypothesis revision"
                )
            if self.requested_authority is not AuthorityLevel.NONE:
                raise WorkbenchContractError(
                    "review and planning commands carry no execution authority"
                )
        if (
            self.kind is CommandKind.REVIEW_HYPOTHESIS_SCOPE
            and not self.human_acknowledged
        ):
            raise WorkbenchContractError(
                "scope review requires explicit human acknowledgement"
            )
        if self.kind is CommandKind.RECORD_MASTERY_ASSESSMENT:
            if self.expected_revision != 0:
                raise WorkbenchContractError(
                    "recording a mastery assessment requires expected revision zero"
                )
            if self.requested_authority is not AuthorityLevel.NONE:
                raise WorkbenchContractError(
                    "a human mastery assessment carries no execution authority"
                )
            if not self.human_acknowledged:
                raise WorkbenchContractError(
                    "mastery assessment requires explicit human acknowledgement"
                )
        if self.kind is CommandKind.EXPORT_REPORT:
            if self.expected_revision != 0:
                raise WorkbenchContractError(
                    "exporting an immutable report requires expected revision zero"
                )
            if self.requested_authority is not AuthorityLevel.NONE:
                raise WorkbenchContractError(
                    "report export carries no execution authority"
                )
            if not self.human_acknowledged:
                raise WorkbenchContractError(
                    "report export requires explicit human acknowledgement"
                )
        if self.kind is CommandKind.CREATE_REPORT_CASE:
            if self.workspace_id is None:
                raise WorkbenchContractError(
                    "creating a report case requires a workspace"
                )
            if self.expected_revision != 0:
                raise WorkbenchContractError(
                    "creating a report case requires expected revision zero"
                )
            if self.requested_authority is not AuthorityLevel.NONE:
                raise WorkbenchContractError(
                    "report authoring carries no execution authority"
                )
        if self.kind is CommandKind.SAVE_REPORT_DRAFT:
            if self.expected_revision is None:
                raise WorkbenchContractError(
                    "saving a report draft requires its current revision"
                )
            if self.requested_authority is not AuthorityLevel.NONE:
                raise WorkbenchContractError(
                    "report authoring carries no execution authority"
                )
        if self.kind is CommandKind.RUN_REPORT_VALIDATION:
            if self.expected_revision is None:
                raise WorkbenchContractError(
                    "report validation requires the current report revision"
                )
            if self.requested_authority is not AuthorityLevel.NONE:
                raise WorkbenchContractError(
                    "report validation carries no execution authority"
                )
            if not self.human_acknowledged:
                raise WorkbenchContractError(
                    "report validation requires explicit human acknowledgement"
                )
        if self.kind in {
            CommandKind.ASSEMBLE_LOCAL_FIXTURE_CLAIMS,
            CommandKind.ADVANCE_REPORT_FINDING,
        }:
            if self.expected_revision is None:
                raise WorkbenchContractError(
                    f"{self.kind.value} requires the current report revision"
                )
            if self.requested_authority is not AuthorityLevel.NONE:
                raise WorkbenchContractError(
                    "report claim and lifecycle work carries no execution authority"
                )
            if not self.human_acknowledged:
                raise WorkbenchContractError(
                    "report claim and lifecycle work requires explicit human acknowledgement"
                )

    def field(self, name: str, default: CommandValue = None) -> CommandValue:
        for field in self.fields:
            if field.name == name:
                return field.value
        return default

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "id": self.id,
            "kind": self.kind.value,
            "operator_ref": self.operator_ref,
            "issued_at": self.issued_at.isoformat(),
            "idempotency_key": self.idempotency_key,
            "workspace_id": self.workspace_id,
            "expected_revision": self.expected_revision,
            "requested_authority": self.requested_authority.name,
            "human_acknowledged": self.human_acknowledged,
            "fields": {
                field.name: (
                    list(field.value)
                    if isinstance(field.value, tuple)
                    else field.value
                )
                for field in self.fields
            },
            "executable": False,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> WorkbenchCommand:
        expected = {
            "schema_version",
            "id",
            "kind",
            "operator_ref",
            "issued_at",
            "idempotency_key",
            "workspace_id",
            "expected_revision",
            "requested_authority",
            "human_acknowledged",
            "fields",
            "executable",
        }
        actual = set(data)
        if actual != expected:
            raise WorkbenchContractError(
                "workbench command keys do not match the versioned contract: "
                f"missing={sorted(expected - actual)!r}, "
                f"unexpected={sorted(actual - expected)!r}"
            )
        if data["executable"] is not False:
            raise WorkbenchContractError(
                "transport commands must explicitly declare executable false"
            )
        textual = (
            "schema_version",
            "id",
            "kind",
            "operator_ref",
            "issued_at",
            "idempotency_key",
            "requested_authority",
        )
        if any(not isinstance(data[name], str) for name in textual):
            raise WorkbenchContractError(
                "command identity, schema, kind, time, and authority must be text"
            )
        fields = data["fields"]
        if not isinstance(fields, Mapping) or any(
            not isinstance(name, str) for name in fields
        ):
            raise WorkbenchContractError("command fields must be an object")
        try:
            issued_at = datetime.fromisoformat(data["issued_at"])
            kind = CommandKind(data["kind"])
            authority = AuthorityLevel.parse(data["requested_authority"])
        except (TypeError, ValueError) as exc:
            raise WorkbenchContractError(
                "command kind, time, or authority is invalid"
            ) from exc
        workspace_id = data["workspace_id"]
        expected_revision = data["expected_revision"]
        human_acknowledged = data["human_acknowledged"]
        if workspace_id is not None and not isinstance(workspace_id, str):
            raise WorkbenchContractError("command workspace id must be text or null")
        if expected_revision is not None and not isinstance(expected_revision, int):
            raise WorkbenchContractError(
                "command expected revision must be an integer or null"
            )
        if not isinstance(human_acknowledged, bool):
            raise WorkbenchContractError(
                "command human acknowledgement must be a boolean"
            )
        return cls(
            id=data["id"],
            kind=kind,
            operator_ref=data["operator_ref"],
            issued_at=issued_at,
            idempotency_key=data["idempotency_key"],
            fields=tuple(
                CommandField.from_pair(name, value)
                for name, value in fields.items()
            ),
            workspace_id=workspace_id,
            expected_revision=expected_revision,
            requested_authority=authority,
            human_acknowledged=human_acknowledged,
            schema_version=data["schema_version"],
        )


@dataclass(frozen=True)
class CommandResult:
    command_id: str
    disposition: CommandDisposition
    code: str
    message: str
    record_refs: tuple[str, ...] = ()
    executed: bool = False

    def __post_init__(self) -> None:
        _safe_id(self.command_id, "result command id")
        _safe_id(self.code, "result code")
        _required(self.message, "result message")
        if self.executed:
            raise WorkbenchContractError(
                "application command results may record domain mutation, never tool execution"
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "command_id": self.command_id,
            "disposition": self.disposition.value,
            "code": self.code,
            "message": self.message,
            "record_refs": list(self.record_refs),
            "executed": False,
        }


__all__ = [
    "WORKBENCH_SCHEMA_VERSION",
    "CommandDisposition",
    "CommandField",
    "CommandKind",
    "CommandResult",
    "NextAction",
    "ReadinessStatus",
    "WorkbenchCommand",
    "WorkbenchContext",
    "WorkbenchContractError",
    "WorkbenchMetric",
    "WorkbenchRecord",
    "WorkbenchSection",
    "WorkbenchSnapshot",
]
