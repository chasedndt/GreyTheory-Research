"""The gate. Every denial path, and the audit trail each one leaves."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from greytheory.audit import AuditLog
from greytheory.authority.gate import AccessRequest, AuthorityLevel, Gate, Reason
from greytheory.authority.scope import (
    AssetPattern,
    ContractStatus,
    PatternType,
    ScopeContract,
)

NOW = datetime(2026, 8, 6, tzinfo=timezone.utc)


@pytest.fixture
def audit(tmp_path):
    return AuditLog(tmp_path / "audit.jsonl")


@pytest.fixture
def gate(audit):
    return Gate(audit, clock=lambda: NOW)


def verified_contract(**overrides) -> ScopeContract:
    base = dict(
        id="scope_test",
        programme_id="test",
        verified_at=NOW,
        status=ContractStatus.VERIFIED,
        assets_in_scope=[AssetPattern(PatternType.WILDCARD, "*.example.test")],
        assets_out_of_scope=[AssetPattern(PatternType.WILDCARD, "*.blog.example.test")],
        max_authority="LOCAL_FIXTURE",
        human_reviewed=True,
    )
    base.update(overrides)
    return ScopeContract(**base)


def request(**overrides) -> AccessRequest:
    base = dict(
        asset="app.example.test",
        authority_level=AuthorityLevel.LOCAL_FIXTURE,
        actor="chase",
    )
    base.update(overrides)
    return AccessRequest(**base)


class TestAllow:
    def test_in_scope_asset_within_authority_is_allowed(self, gate):
        decision = gate.evaluate(verified_contract(), request())
        assert decision.allowed
        assert decision.reason is Reason.ALLOWED
        assert bool(decision) is True

    def test_an_allow_carries_the_authority_reference(self, gate):
        contract = verified_contract()
        decision = gate.evaluate(contract, request())
        # Invariant I2 — artifacts produced under this allow must cite it.
        assert decision.authority_ref == contract.fingerprint()


class TestDenials:
    def test_no_contract_denies(self, gate):
        decision = gate.evaluate(None, request())
        assert not decision
        assert decision.reason is Reason.NO_CONTRACT

    def test_blocked_contract_denies_and_names_the_ambiguities(self, gate):
        contract = verified_contract(
            status=ContractStatus.BLOCKED, ambiguities=["scope unclear"]
        )
        decision = gate.evaluate(contract, request())
        assert decision.reason is Reason.CONTRACT_BLOCKED
        assert "scope unclear" in decision.detail

    def test_unreviewed_contract_denies(self, gate):
        # A clean compile is not authority until a human has read it.
        contract = verified_contract(
            status=ContractStatus.PENDING_REVIEW, human_reviewed=False
        )
        decision = gate.evaluate(contract, request())
        assert decision.reason is Reason.CONTRACT_NOT_VERIFIED

    def test_verified_status_without_the_review_flag_still_denies(self, gate):
        contract = verified_contract(human_reviewed=False)
        assert gate.evaluate(contract, request()).reason is Reason.CONTRACT_NOT_VERIFIED

    def test_stale_contract_denies(self, audit):
        gate = Gate(audit, clock=lambda: NOW + timedelta(days=30))
        decision = gate.evaluate(verified_contract(), request())
        assert decision.reason is Reason.CONTRACT_STALE

    def test_out_of_scope_asset_denies(self, gate):
        decision = gate.evaluate(
            verified_contract(), request(asset="x.blog.example.test")
        )
        assert decision.reason is Reason.ASSET_OUT_OF_SCOPE

    def test_unmatched_asset_denies(self, gate):
        decision = gate.evaluate(verified_contract(), request(asset="other.test"))
        assert decision.reason is Reason.ASSET_UNRESOLVED

    def test_derived_asset_does_not_inherit_scope(self, gate):
        # Discovered *through* an in-scope host, but not itself in scope.
        decision = gate.evaluate(
            verified_contract(),
            request(asset="cdn.thirdparty.test", derived_from="app.example.test"),
        )
        assert decision.reason is Reason.DERIVED_ASSET_NOT_INHERITED
        assert "not inherited" in decision.detail or "scope is not inherited" in decision.detail

    def test_prohibited_technique_denies_even_on_an_in_scope_asset(self, gate):
        contract = verified_contract(prohibited_techniques=["denial_of_service"])
        decision = gate.evaluate(contract, request(technique="denial_of_service"))
        assert decision.reason is Reason.TECHNIQUE_PROHIBITED

    def test_request_above_granted_authority_denies(self, audit):
        gate = Gate(
            audit, posture_ceiling=AuthorityLevel.INTRUSIVE, clock=lambda: NOW
        )
        decision = gate.evaluate(
            verified_contract(max_authority="LOCAL_FIXTURE"),
            request(authority_level=AuthorityLevel.AUTHENTICATED),
        )
        assert decision.reason is Reason.AUTHORITY_LEVEL_EXCEEDED

    def test_posture_ceiling_caps_even_a_generous_contract(self, gate):
        # The contract legitimately grants AUTHENTICATED. The current local-only
        # posture still refuses it. This is D5 enforced in code.
        decision = gate.evaluate(
            verified_contract(max_authority="AUTHENTICATED"),
            request(authority_level=AuthorityLevel.AUTHENTICATED),
        )
        assert decision.reason is Reason.POSTURE_CEILING_EXCEEDED

    def test_raise_if_denied(self, gate):
        decision = gate.evaluate(None, request())
        with pytest.raises(PermissionError, match="no_contract"):
            decision.raise_if_denied()


class TestKillSwitch:
    def test_engaged_kill_switch_denies_everything(self, gate):
        gate.engage_kill_switch(actor="chase", reason="incident")
        decision = gate.evaluate(verified_contract(), request())
        assert decision.reason is Reason.KILL_SWITCH_ENGAGED

    def test_release_restores_normal_evaluation(self, gate):
        gate.engage_kill_switch(actor="chase", reason="incident")
        gate.release_kill_switch(actor="chase", reason="resolved")
        assert gate.evaluate(verified_contract(), request()).allowed


class TestAuditing:
    def test_allows_and_denials_are_both_recorded(self, gate, audit):
        gate.evaluate(verified_contract(), request())
        gate.evaluate(verified_contract(), request(asset="other.test"))

        records = [r for r in audit.records() if r.action == "gate.evaluate"]
        assert len(records) == 2
        assert records[0].detail["allowed"] is True
        assert records[1].detail["allowed"] is False
        audit.verify()

    def test_the_decision_points_back_at_its_audit_record(self, gate, audit):
        decision = gate.evaluate(verified_contract(), request())
        record = audit.records()[decision.audit_seq]
        assert record.detail["reason"] == decision.reason.value

    def test_denied_requests_are_recorded_with_their_full_detail(self, gate, audit):
        gate.evaluate(
            verified_contract(),
            request(asset="secret.internal.test", purpose="curiosity"),
        )
        record = audit.records()[-1]
        assert record.detail["request"]["asset"] == "secret.internal.test"
        assert record.detail["request"]["purpose"] == "curiosity"


class TestAuthorityLevel:
    def test_levels_are_ordered(self):
        assert AuthorityLevel.NONE < AuthorityLevel.LOCAL_FIXTURE
        assert AuthorityLevel.PASSIVE_HTTP < AuthorityLevel.AUTHENTICATED
        assert AuthorityLevel.AUTHENTICATED < AuthorityLevel.INTRUSIVE

    def test_unknown_level_parses_to_none(self):
        # I3 — an unrecognised authority name grants nothing.
        assert AuthorityLevel.parse("SUPERUSER") is AuthorityLevel.NONE
        assert AuthorityLevel.parse("passive_http") is AuthorityLevel.PASSIVE_HTTP
