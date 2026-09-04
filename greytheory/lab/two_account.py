"""A deliberately vulnerable, in-memory two-account authorisation fixture."""

# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 ChaseInTech

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any


class ExecutionDenied(PermissionError):
    """Raised when code tries to bypass the gate-bound local executor."""


@dataclass(frozen=True)
class FixtureAction:
    token: str
    request_id: str
    gate_decision_ref: str
    action_type: str
    identity_id: str
    target_identifier: str


@dataclass(frozen=True)
class FixtureResponse:
    status_code: int
    body: bytes


def _canonical(value: Any) -> bytes:
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        + "\n"
    ).encode("utf-8")


class TwoAccountFixture:
    """Two controlled identities and objects, with an intentional BOLA flaw.

    The fixture has no sockets, URLs, credentials, or external state. Its only
    action method requires an opaque capability and one-use ticket held by the
    local execution broker. Calling the public convenience path always fails.
    """

    fixture_id = "two-account-authorization-v1"

    def __init__(self, *, vulnerable: bool = True) -> None:
        self.vulnerable = vulnerable
        self.identities = ("identity-user-a", "identity-user-b")
        self.objects = {
            "fixture://two-account/objects/object-user-a": {
                "id": "object-user-a",
                "owner_identity_id": "identity-user-a",
                "content": "synthetic note owned by controlled user A",
            },
            "fixture://two-account/objects/object-user-b": {
                "id": "object-user-b",
                "owner_identity_id": "identity-user-b",
                "content": "synthetic note owned by controlled user B",
            },
        }
        self._capability = object()
        self._consumed_tokens: set[str] = set()
        self.action_log: list[dict[str, str | int]] = []

    @property
    def action_count(self) -> int:
        return len(self.action_log)

    def ownership_manifest(self) -> bytes:
        return _canonical(
            {
                "fixture_id": self.fixture_id,
                "controlled_identities": list(self.identities),
                "objects": {
                    value["id"]: value["owner_identity_id"]
                    for value in self.objects.values()
                },
            }
        )

    def read_object(self, identity_id: str, target_identifier: str) -> FixtureResponse:
        del identity_id, target_identifier
        raise ExecutionDenied(
            "fixture actions require a one-use ticket from an allowed gate decision"
        )

    def _execute(self, action: FixtureAction, *, capability: object) -> FixtureResponse:
        if capability is not self._capability:
            raise ExecutionDenied("fixture execution capability is invalid")
        if action.token in self._consumed_tokens:
            raise ExecutionDenied("fixture action ticket was already consumed")
        if not action.gate_decision_ref.startswith("audit:"):
            raise ExecutionDenied("fixture action has no audited gate decision")
        if action.action_type != "read_object":
            raise ExecutionDenied(f"fixture action {action.action_type!r} is unsupported")
        if action.identity_id not in self.identities:
            raise ExecutionDenied("fixture identity is not one of the controlled accounts")
        try:
            target = self.objects[action.target_identifier]
        except KeyError as exc:
            raise ExecutionDenied("fixture target is not a controlled object") from exc

        self._consumed_tokens.add(action.token)
        owner = str(target["owner_identity_id"])
        allowed = self.vulnerable or owner == action.identity_id
        status_code = 200 if allowed else 403
        body = _canonical(
            {
                "fixture_id": self.fixture_id,
                "requester_identity_id": action.identity_id,
                "status_code": status_code,
                "object": target if allowed else None,
                "denial_reason": None if allowed else "object_owner_mismatch",
            }
        )
        self.action_log.append(
            {
                "request_id": action.request_id,
                "gate_decision_ref": action.gate_decision_ref,
                "identity_id": action.identity_id,
                "target_identifier": action.target_identifier,
                "status_code": status_code,
            }
        )
        return FixtureResponse(status_code=status_code, body=body)


class OwnershipValidator:
    """Re-derive whether a controlled cross-owner read was returned."""

    validator_id = "local.two_account.cross_owner_read"
    version = "1.0.0"
    exact_assertion = (
        "Controlled identity identity-user-a read controlled object object-user-b "
        "owned by identity-user-b."
    )
    possible_outcomes = ("supported", "refuted", "invalid_input")

    def validate(self, inputs: tuple[bytes, ...]) -> str:
        if len(inputs) != 2:
            return "invalid_input"
        try:
            response = json.loads(inputs[0])
            manifest = json.loads(inputs[1])
            returned = response.get("object")
            requester = response["requester_identity_id"]
            object_id = returned["id"] if returned else "object-user-b"
            recorded_owner = manifest["objects"][object_id]
        except (KeyError, TypeError, ValueError, json.JSONDecodeError):
            return "invalid_input"
        if (
            response.get("fixture_id") != manifest.get("fixture_id")
            or requester not in manifest.get("controlled_identities", [])
            or recorded_owner not in manifest.get("controlled_identities", [])
        ):
            return "invalid_input"
        if (
            response.get("status_code") == 200
            and returned is not None
            and returned.get("owner_identity_id") == recorded_owner
            and requester == "identity-user-a"
            and object_id == "object-user-b"
            and recorded_owner == "identity-user-b"
        ):
            return "supported"
        return "refuted"


__all__ = [
    "ExecutionDenied",
    "FixtureAction",
    "FixtureResponse",
    "OwnershipValidator",
    "TwoAccountFixture",
]
