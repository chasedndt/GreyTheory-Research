"""Approvals: bound, fresh, single-use — and read from ChaseOS, not stored here."""

# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 ChaseInTech

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

import pytest

from greytheory.audit import AuditLog
from greytheory.authority.approvals import (
    Approval,
    ChaseOSApprovalStore,
    LocalApprovalStore,
)
from greytheory.authority.gate import AccessRequest, AuthorityLevel, Gate, Reason
from greytheory.authority.scope import (
    AssetPattern,
    ContractStatus,
    PatternType,
    ScopeContract,
)

NOW = datetime(2026, 8, 6, 12, 0, tzinfo=timezone.utc)


@pytest.fixture
def audit(tmp_path):
    return AuditLog(tmp_path / "audit.jsonl")


@pytest.fixture
def store():
    return LocalApprovalStore()


@pytest.fixture
def gate(audit, store):
    # Posture raised so the approval layer is the thing under test.
    return Gate(
        audit,
        posture_ceiling=AuthorityLevel.INTRUSIVE,
        approvals=store,
        approval_required_above=AuthorityLevel.PASSIVE_HTTP,
        clock=lambda: NOW,
    )


def contract() -> ScopeContract:
    return ScopeContract(
        id="scope_test",
        programme_id="test",
        verified_at=NOW,
        status=ContractStatus.VERIFIED,
        assets_in_scope=[AssetPattern(PatternType.WILDCARD, "*.example.test")],
        max_authority="INTRUSIVE",
        human_reviewed=True,
    )


def request(**overrides) -> AccessRequest:
    base = dict(
        asset="app.example.test",
        authority_level=AuthorityLevel.AUTHENTICATED,
        actor="chase",
        action_type="read_object",
    )
    base.update(overrides)
    return AccessRequest(**base)


class TestApprovalRequirement:
    def test_below_the_threshold_no_approval_is_needed(self, gate):
        decision = gate.evaluate(
            contract(), request(authority_level=AuthorityLevel.PASSIVE_HTTP)
        )
        assert decision.allowed

    def test_above_the_threshold_an_approval_is_required(self, gate):
        decision = gate.evaluate(contract(), request())
        assert decision.reason is Reason.APPROVAL_REQUIRED

    def test_a_gate_with_no_store_cannot_grant_high_authority(self, audit):
        gate = Gate(
            audit,
            posture_ceiling=AuthorityLevel.INTRUSIVE,
            approvals=None,
            clock=lambda: NOW,
        )
        decision = gate.evaluate(contract(), request(approval_id="a1"))
        assert decision.reason is Reason.APPROVAL_REQUIRED

    def test_unknown_approval_id_denies(self, gate):
        decision = gate.evaluate(contract(), request(approval_id="nope"))
        assert decision.reason is Reason.APPROVAL_NOT_FOUND


class TestApprovalContent:
    def test_a_valid_bound_approval_allows(self, gate, store):
        store.grant(
            approval_id="a1",
            operator_id="chase",
            action_type="read_object",
            target="app.example.test",
            responded_at=NOW,
        )
        assert gate.evaluate(contract(), request(approval_id="a1")).allowed

    def test_a_denied_approval_denies(self, gate, store):
        store.deny(
            approval_id="a1",
            operator_id="chase",
            action_type="read_object",
            target="app.example.test",
            responded_at=NOW,
        )
        decision = gate.evaluate(contract(), request(approval_id="a1"))
        assert decision.reason is Reason.APPROVAL_DENIED

    def test_an_approval_for_another_target_does_not_carry(self, gate, store):
        store.grant(
            approval_id="a1",
            operator_id="chase",
            action_type="read_object",
            target="other.example.test",
            responded_at=NOW,
        )
        decision = gate.evaluate(contract(), request(approval_id="a1"))
        assert decision.reason is Reason.APPROVAL_NOT_BINDING

    def test_an_approval_for_another_action_does_not_carry(self, gate, store):
        # Approval to read is not approval to delete.
        store.grant(
            approval_id="a1",
            operator_id="chase",
            action_type="read_object",
            target="app.example.test",
            responded_at=NOW,
        )
        decision = gate.evaluate(
            contract(), request(approval_id="a1", action_type="delete_object")
        )
        assert decision.reason is Reason.APPROVAL_NOT_BINDING

    def test_an_unbound_approval_covers_nothing(self, gate, store):
        store.grant(
            approval_id="a1",
            operator_id="chase",
            action_type="",
            target="",
            responded_at=NOW,
        )
        decision = gate.evaluate(contract(), request(approval_id="a1"))
        assert decision.reason is Reason.APPROVAL_NOT_BINDING

    def test_a_stale_approval_denies(self, gate, store):
        store.grant(
            approval_id="a1",
            operator_id="chase",
            action_type="read_object",
            target="app.example.test",
            responded_at=NOW - timedelta(days=2),
        )
        decision = gate.evaluate(contract(), request(approval_id="a1"))
        assert decision.reason is Reason.APPROVAL_EXPIRED


class TestSingleUse:
    def test_an_approval_cannot_be_replayed(self, gate, store):
        store.grant(
            approval_id="a1",
            operator_id="chase",
            action_type="read_object",
            target="app.example.test",
            responded_at=NOW,
        )
        first = gate.evaluate(contract(), request(approval_id="a1"))
        second = gate.evaluate(contract(), request(approval_id="a1"))

        assert first.allowed
        assert second.reason is Reason.APPROVAL_ALREADY_CONSUMED

    def test_a_denied_attempt_does_not_burn_the_approval(self, gate, store):
        # Only allows consume. Otherwise a wrong-target attempt would silently
        # void a legitimate approval.
        store.grant(
            approval_id="a1",
            operator_id="chase",
            action_type="read_object",
            target="app.example.test",
            responded_at=NOW,
        )
        gate.evaluate(contract(), request(approval_id="a1", asset="out.of.scope"))
        assert gate.evaluate(contract(), request(approval_id="a1")).allowed


class TestAuditing:
    def test_the_approval_id_is_recorded_with_the_decision(self, gate, store, audit):
        store.grant(
            approval_id="a1",
            operator_id="chase",
            action_type="read_object",
            target="app.example.test",
            responded_at=NOW,
        )
        gate.evaluate(contract(), request(approval_id="a1"))
        assert audit.records()[-1].detail["request"]["approval_id"] == "a1"
        audit.verify()


class TestChaseOSStore:
    """Read across the filesystem contract that runtime/osril/approvals.py writes."""

    def write_response(self, vault, approval_id: str, **fields) -> None:
        directory = vault / "runtime" / "osril" / "approvals"
        directory.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema_version": 1,
            "approval_id": approval_id,
            "decision": "APPROVE",
            "operator_id": "chase",
            "operator_note": "",
            "responded_at": "2026-08-06T12:00:00Z",
            "action_type": "read_object",
            "target": "app.example.test",
        }
        payload.update(fields)
        (directory / f"{approval_id}.response.json").write_text(
            json.dumps(payload), encoding="utf-8"
        )

    def test_reads_an_osril_response(self, tmp_path):
        self.write_response(tmp_path, "a1")
        approval = ChaseOSApprovalStore(tmp_path).lookup("a1")

        assert isinstance(approval, Approval)
        assert approval.granted
        assert approval.operator_id == "chase"
        assert approval.source == "chaseos_osril"
        # ChaseOS writes a trailing 'Z'; it must parse as UTC.
        assert approval.responded_at == NOW

    def test_reads_a_denial(self, tmp_path):
        self.write_response(tmp_path, "a2", decision="DENY")
        assert ChaseOSApprovalStore(tmp_path).lookup("a2").granted is False

    def test_missing_response_returns_none(self, tmp_path):
        assert ChaseOSApprovalStore(tmp_path).lookup("absent") is None

    def test_malformed_response_returns_none_rather_than_raising(self, tmp_path):
        directory = tmp_path / "runtime" / "osril" / "approvals"
        directory.mkdir(parents=True)
        (directory / "bad.response.json").write_text("{not json", encoding="utf-8")
        assert ChaseOSApprovalStore(tmp_path).lookup("bad") is None

    def test_path_traversal_in_the_approval_id_is_rejected(self, tmp_path):
        # The id arrives from a request, so it is untrusted input.
        store = ChaseOSApprovalStore(tmp_path)
        assert store.lookup("../../../etc/passwd") is None
        assert store.lookup("a/b") is None
        assert store.lookup("") is None

    def test_end_to_end_through_the_gate(self, tmp_path, audit):
        self.write_response(tmp_path, "a1")
        gate = Gate(
            audit,
            posture_ceiling=AuthorityLevel.INTRUSIVE,
            approvals=ChaseOSApprovalStore(tmp_path),
            clock=lambda: NOW,
        )
        assert gate.evaluate(contract(), request(approval_id="a1")).allowed
