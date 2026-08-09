"""Deterministic, synthetic vulnerability-card training fixtures.

These fixtures demonstrate security properties without payloads, sockets,
credentials, browsers, or external targets.  A receipt proves only that the
shipped synthetic scenario and both controls behaved as declared; it is never
evidence that a real application is vulnerable and never grants mastery.
"""

# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 ChaseInTech

from __future__ import annotations

import hashlib
import html
import inspect
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Mapping

from greytheory.learning.domain import LearningError


class FixtureMechanism(str, Enum):
    REFLECTED_OUTPUT_ENCODING = "reflected_output_encoding"
    STORED_OUTPUT_ENCODING = "stored_output_encoding"
    DOM_SINK_CONTROL = "dom_sink_control"
    QUERY_PARAMETERIZATION = "query_parameterization"
    REQUEST_INTENT_BINDING = "request_intent_binding"
    DESTINATION_ALLOWLIST = "destination_allowlist"
    OBJECT_OWNERSHIP = "object_ownership"
    FUNCTION_ROLE_AUTHORIZATION = "function_role_authorization"
    SESSION_INVALIDATION = "session_invalidation"
    WORKFLOW_AUTHORIZATION = "workflow_authorization"
    INSTRUCTION_DATA_SEPARATION = "instruction_data_separation"
    TOOL_TICKET_BINDING = "tool_ticket_binding"


class FixtureCaseRole(str, Enum):
    POSITIVE_CONTROL = "positive_control"
    VULNERABLE_PROBE = "vulnerable_probe"
    NEGATIVE_CONTROL = "negative_control"


@dataclass(frozen=True)
class FixtureCase:
    id: str
    role: FixtureCaseRole
    expected_property_held: bool

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> FixtureCase:
        return cls(
            id=str(data["id"]),
            role=FixtureCaseRole(data["role"]),
            expected_property_held=data.get("expected_property_held") is True,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "role": self.role.value,
            "expected_property_held": self.expected_property_held,
        }


@dataclass(frozen=True)
class LocalTrainingFixture:
    schema_version: int
    id: str
    card_id: str
    title: str
    description: str
    mechanism: FixtureMechanism
    synthetic_only: bool
    network_required: bool
    cases: tuple[FixtureCase, ...]

    def __post_init__(self) -> None:
        if self.schema_version != 1:
            raise LearningError("unsupported training-fixture schema")
        if not self.id or not self.card_id or not self.title or not self.description:
            raise LearningError("training fixture identity and description are required")
        if not self.synthetic_only or self.network_required:
            raise LearningError("Milestone 5 fixtures must be synthetic and network-free")
        roles = tuple(item.role for item in self.cases)
        if len(self.cases) != 3 or set(roles) != set(FixtureCaseRole):
            raise LearningError("fixture requires exactly one case for each control role")
        for item in self.cases:
            expected = item.role is not FixtureCaseRole.VULNERABLE_PROBE
            if item.expected_property_held is not expected:
                raise LearningError(
                    f"fixture case {item.id!r} has an unsafe expected property result"
                )

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> LocalTrainingFixture:
        return cls(
            schema_version=int(data["schema_version"]),
            id=data["id"],
            card_id=data["card_id"],
            title=data["title"],
            description=data["description"],
            mechanism=FixtureMechanism(data["mechanism"]),
            synthetic_only=data.get("synthetic_only") is True,
            network_required=data.get("network_required") is True,
            cases=tuple(FixtureCase.from_dict(item) for item in data.get("cases", ())),
        )

    @classmethod
    def load(cls, path: Path) -> LocalTrainingFixture:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise LearningError(f"cannot load training fixture {path}: {exc}") from exc
        if not isinstance(data, dict):
            raise LearningError("training fixture root must be an object")
        return cls.from_dict(data)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "id": self.id,
            "card_id": self.card_id,
            "title": self.title,
            "description": self.description,
            "mechanism": self.mechanism.value,
            "synthetic_only": self.synthetic_only,
            "network_required": self.network_required,
            "cases": [item.to_dict() for item in self.cases],
        }

    def digest(self) -> str:
        encoded = json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class FixtureCaseResult:
    case_id: str
    role: FixtureCaseRole
    property_held: bool
    controlled_effect_observed: bool
    observation: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "role": self.role.value,
            "property_held": self.property_held,
            "controlled_effect_observed": self.controlled_effect_observed,
            "observation": self.observation,
        }


@dataclass(frozen=True)
class FixtureRunReceipt:
    id: str
    fixture_id: str
    card_id: str
    fixture_digest: str
    runner_id: str
    runner_version: str
    runner_digest: str
    executed_at: datetime
    case_results: tuple[FixtureCaseResult, ...]
    controls_passed: bool
    vulnerable_case_demonstrated: bool
    scope: str = "synthetic_training_only"
    proves_real_vulnerability: bool = False
    credits_mastery: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "fixture_id": self.fixture_id,
            "card_id": self.card_id,
            "fixture_digest": self.fixture_digest,
            "runner_id": self.runner_id,
            "runner_version": self.runner_version,
            "runner_digest": self.runner_digest,
            "executed_at": self.executed_at.isoformat(),
            "case_results": [item.to_dict() for item in self.case_results],
            "controls_passed": self.controls_passed,
            "vulnerable_case_demonstrated": self.vulnerable_case_demonstrated,
            "scope": self.scope,
            "proves_real_vulnerability": self.proves_real_vulnerability,
            "credits_mastery": self.credits_mastery,
        }


_DESCRIPTIONS: dict[FixtureMechanism, tuple[str, str, str]] = {
    FixtureMechanism.REFLECTED_OUTPUT_ENCODING: (
        "Trusted marker rendered as intended.",
        "Untrusted reflected marker crossed into an executable output context.",
        "Context-aware encoding kept the untrusted marker inert.",
    ),
    FixtureMechanism.STORED_OUTPUT_ENCODING: (
        "Trusted stored content rendered as intended.",
        "Stored untrusted marker crossed into another synthetic viewer's executable context.",
        "Encoding at render time kept stored untrusted content inert.",
    ),
    FixtureMechanism.DOM_SINK_CONTROL: (
        "Trusted DOM content reached the intended sink.",
        "Untrusted location data reached an executable DOM sink.",
        "A text-only sink kept untrusted location data inert.",
    ),
    FixtureMechanism.QUERY_PARAMETERIZATION: (
        "A valid synthetic lookup returned its named row.",
        "Untrusted query structure changed the synthetic result set.",
        "Parameter binding preserved the intended query structure.",
    ),
    FixtureMechanism.REQUEST_INTENT_BINDING: (
        "A same-context state change with an intent token was accepted.",
        "A cross-context state change without intent proof was accepted.",
        "The missing intent proof caused the synthetic state change to be denied.",
    ),
    FixtureMechanism.DESTINATION_ALLOWLIST: (
        "An allowlisted synthetic public destination was retrieved.",
        "A controlled internal-only destination was retrieved from untrusted input.",
        "Destination policy denied the controlled internal-only destination.",
    ),
    FixtureMechanism.OBJECT_OWNERSHIP: (
        "A controlled identity read its own synthetic object.",
        "A controlled identity read the other controlled identity's synthetic object.",
        "The ownership check denied the cross-owner read with no data returned.",
    ),
    FixtureMechanism.FUNCTION_ROLE_AUTHORIZATION: (
        "A privileged synthetic role invoked its permitted function.",
        "A basic synthetic role invoked a privileged function.",
        "The role check denied the privileged function to the basic role.",
    ),
    FixtureMechanism.SESSION_INVALIDATION: (
        "A current synthetic session token was accepted before logout.",
        "The prior synthetic token remained accepted after logout or rotation.",
        "The prior token was rejected after logout or rotation.",
    ),
    FixtureMechanism.WORKFLOW_AUTHORIZATION: (
        "A permitted synthetic workflow transition completed.",
        "A controlled actor bypassed a required workflow state or approval.",
        "The invalid transition was denied without changing state.",
    ),
    FixtureMechanism.INSTRUCTION_DATA_SEPARATION: (
        "A trusted local instruction selected the intended simulated action.",
        "Untrusted retrieved text changed a simulated tool decision.",
        "Untrusted retrieved text remained labelled data and caused no action.",
    ),
    FixtureMechanism.TOOL_TICKET_BINDING: (
        "A simulated tool action with an exact one-use ticket completed.",
        "A simulated tool action without a matching ticket completed.",
        "The missing or mismatched ticket caused the action to be denied.",
    ),
}


class TrainingFixtureRunner:
    runner_id = "greytheory.synthetic-learning-fixture"
    runner_version = "1.0.0"

    def __init__(self, *, clock: Callable[[], datetime] | None = None) -> None:
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    @classmethod
    def digest(cls) -> str:
        descriptions = json.dumps(
            {item.value: _DESCRIPTIONS[item] for item in FixtureMechanism},
            sort_keys=True,
            separators=(",", ":"),
        )
        material = inspect.getsource(cls) + "\n" + descriptions
        return hashlib.sha256(material.encode("utf-8")).hexdigest()

    def run(self, fixture: LocalTrainingFixture) -> FixtureRunReceipt:
        descriptions = _DESCRIPTIONS[fixture.mechanism]
        by_role = {item.role: item for item in fixture.cases}
        results = tuple(
            self._run_case(fixture.mechanism, by_role[role], descriptions[index])
            for index, role in enumerate(
                (
                    FixtureCaseRole.POSITIVE_CONTROL,
                    FixtureCaseRole.VULNERABLE_PROBE,
                    FixtureCaseRole.NEGATIVE_CONTROL,
                )
            )
        )
        controls_passed = all(
            item.property_held
            for item in results
            if item.role is not FixtureCaseRole.VULNERABLE_PROBE
        )
        vulnerable = any(
            not item.property_held and item.controlled_effect_observed
            for item in results
            if item.role is FixtureCaseRole.VULNERABLE_PROBE
        )
        if any(
            item.property_held != by_role[item.role].expected_property_held
            for item in results
        ):
            raise LearningError("fixture result disagrees with its declared oracle")
        executed_at = self._clock()
        if executed_at.tzinfo is None:
            raise LearningError("fixture runner clock must be timezone-aware")
        digest = fixture.digest()
        receipt_seed = f"{fixture.id}:{digest}:{executed_at.isoformat()}"
        receipt_id = "fixture-run-" + hashlib.sha256(receipt_seed.encode()).hexdigest()[:20]
        return FixtureRunReceipt(
            id=receipt_id,
            fixture_id=fixture.id,
            card_id=fixture.card_id,
            fixture_digest=digest,
            runner_id=self.runner_id,
            runner_version=self.runner_version,
            runner_digest=self.digest(),
            executed_at=executed_at,
            case_results=results,
            controls_passed=controls_passed,
            vulnerable_case_demonstrated=vulnerable,
        )

    @classmethod
    def _run_case(
        cls,
        mechanism: FixtureMechanism,
        case: FixtureCase,
        observation: str,
    ) -> FixtureCaseResult:
        property_held, controlled_effect = cls._simulate(mechanism, case.role)
        return FixtureCaseResult(
            case_id=case.id,
            role=case.role,
            property_held=property_held,
            controlled_effect_observed=controlled_effect,
            observation=observation,
        )

    @staticmethod
    def _simulate(
        mechanism: FixtureMechanism, role: FixtureCaseRole
    ) -> tuple[bool, bool]:
        """Exercise one distinct local boundary and return property/effect state."""

        vulnerable = role is FixtureCaseRole.VULNERABLE_PROBE
        if mechanism is FixtureMechanism.REFLECTED_OUTPUT_ENCODING:
            marker = "<UNTRUSTED-MARKER>"
            rendered = marker if vulnerable else html.escape(marker)
            raw_marker_crossed = marker in rendered
            return not raw_marker_crossed, raw_marker_crossed

        if mechanism is FixtureMechanism.STORED_OUTPUT_ENCODING:
            store = {"message": "<STORED-UNTRUSTED-MARKER>"}
            rendered = store["message"] if vulnerable else html.escape(store["message"])
            raw_marker_crossed = store["message"] in rendered
            return not raw_marker_crossed, raw_marker_crossed

        if mechanism is FixtureMechanism.DOM_SINK_CONTROL:
            sink = "innerHTML" if vulnerable else "textContent"
            executable_sink_reached = sink == "innerHTML"
            return not executable_sink_reached, executable_sink_reached

        if mechanism is FixtureMechanism.QUERY_PARAMETERIZATION:
            untrusted = "UNTRUSTED_QUERY_STRUCTURE"
            query = (
                f"SELECT synthetic_row WHERE name = {untrusted}"
                if vulnerable
                else "SELECT synthetic_row WHERE name = ?"
            )
            structure_changed = untrusted in query
            return not structure_changed, structure_changed

        if mechanism is FixtureMechanism.REQUEST_INTENT_BINDING:
            intent_present = role is FixtureCaseRole.POSITIVE_CONTROL
            state_changed = intent_present or vulnerable
            unauthorized_change = state_changed and not intent_present
            return not unauthorized_change, unauthorized_change

        if mechanism is FixtureMechanism.DESTINATION_ALLOWLIST:
            destination = "synthetic:internal" if role is not FixtureCaseRole.POSITIVE_CONTROL else "synthetic:public"
            allowed = destination == "synthetic:public" or vulnerable
            internal_retrieved = destination == "synthetic:internal" and allowed
            return not internal_retrieved, internal_retrieved

        if mechanism is FixtureMechanism.OBJECT_OWNERSHIP:
            actor = "identity-a"
            owner = "identity-b" if role is not FixtureCaseRole.POSITIVE_CONTROL else actor
            authorized = actor == owner
            object_returned = authorized or vulnerable
            cross_owner_read = object_returned and actor != owner
            return not cross_owner_read, cross_owner_read

        if mechanism is FixtureMechanism.FUNCTION_ROLE_AUTHORIZATION:
            role_name = "basic" if role is not FixtureCaseRole.POSITIVE_CONTROL else "privileged"
            permitted = role_name == "privileged"
            function_executed = permitted or vulnerable
            unauthorized_function = function_executed and not permitted
            return not unauthorized_function, unauthorized_function

        if mechanism is FixtureMechanism.SESSION_INVALIDATION:
            before_logout = role is FixtureCaseRole.POSITIVE_CONTROL
            token_valid = before_logout or vulnerable
            stale_token_accepted = not before_logout and token_valid
            return not stale_token_accepted, stale_token_accepted

        if mechanism is FixtureMechanism.WORKFLOW_AUTHORIZATION:
            precondition_met = role is FixtureCaseRole.POSITIVE_CONTROL
            transition_applied = precondition_met or vulnerable
            invalid_transition = transition_applied and not precondition_met
            return not invalid_transition, invalid_transition

        if mechanism is FixtureMechanism.INSTRUCTION_DATA_SEPARATION:
            trusted_instruction = role is FixtureCaseRole.POSITIVE_CONTROL
            untrusted_text_adopted = vulnerable and not trusted_instruction
            simulated_action_selected = trusted_instruction or untrusted_text_adopted
            unauthorized_selection = simulated_action_selected and not trusted_instruction
            return not unauthorized_selection, unauthorized_selection

        if mechanism is FixtureMechanism.TOOL_TICKET_BINDING:
            matching_ticket = role is FixtureCaseRole.POSITIVE_CONTROL
            effect_executed = matching_ticket or vulnerable
            unauthorized_effect = effect_executed and not matching_ticket
            return not unauthorized_effect, unauthorized_effect

        raise LearningError(f"unsupported fixture mechanism {mechanism.value!r}")


__all__ = [
    "FixtureCase",
    "FixtureCaseResult",
    "FixtureCaseRole",
    "FixtureMechanism",
    "FixtureRunReceipt",
    "LocalTrainingFixture",
    "TrainingFixtureRunner",
]
