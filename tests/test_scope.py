"""Scope matching. Out-of-scope wins; no match is denial, not a maybe."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from greytheory.authority.scope import (
    AssetPattern,
    ContractStatus,
    PatternError,
    PatternType,
    ScopeClassification,
    ScopeContract,
)

NOW = datetime(2026, 8, 6, tzinfo=timezone.utc)


def contract(**overrides) -> ScopeContract:
    base = dict(
        id="scope_test",
        programme_id="test",
        verified_at=NOW,
        status=ContractStatus.VERIFIED,
        assets_in_scope=[AssetPattern(PatternType.WILDCARD, "*.example.test")],
        assets_out_of_scope=[AssetPattern(PatternType.WILDCARD, "*.blog.example.test")],
        human_reviewed=True,
    )
    base.update(overrides)
    return ScopeContract(**base)


class TestPatternMatching:
    def test_wildcard_matches_any_depth(self):
        pattern = AssetPattern(PatternType.WILDCARD, "*.example.test")
        assert pattern.matches("app.example.test")
        assert pattern.matches("a.b.c.example.test")

    def test_wildcard_does_not_match_the_apex(self):
        # The apex must be listed explicitly. Assuming otherwise is how
        # out-of-scope roots get probed.
        pattern = AssetPattern(PatternType.WILDCARD, "*.example.test")
        assert not pattern.matches("example.test")

    def test_wildcard_does_not_match_a_lookalike_suffix(self):
        pattern = AssetPattern(PatternType.WILDCARD, "*.example.test")
        assert not pattern.matches("notexample.test")
        assert not pattern.matches("app.example.test.evil.test")

    def test_matching_is_case_insensitive(self):
        pattern = AssetPattern(PatternType.WILDCARD, "*.Example.Test")
        assert pattern.matches("APP.example.test")

    def test_exact_matches_only_itself(self):
        pattern = AssetPattern(PatternType.EXACT, "api.example.test")
        assert pattern.matches("api.example.test")
        assert not pattern.matches("v2.api.example.test")

    def test_cidr_matches_addresses_in_range(self):
        pattern = AssetPattern(PatternType.CIDR, "192.0.2.0/24")
        assert pattern.matches("192.0.2.55")
        assert not pattern.matches("198.51.100.1")

    def test_cidr_does_not_match_hostnames(self):
        # Resolution is not the scope layer's job; a name is not an address.
        pattern = AssetPattern(PatternType.CIDR, "192.0.2.0/24")
        assert not pattern.matches("app.example.test")

    def test_invalid_patterns_raise_rather_than_silently_never_match(self):
        with pytest.raises(PatternError):
            AssetPattern(PatternType.CIDR, "not-a-cidr")
        with pytest.raises(PatternError):
            AssetPattern(PatternType.WILDCARD, "example.test")
        with pytest.raises(PatternError):
            AssetPattern(PatternType.EXACT, "   ")


class TestClassification:
    def test_in_scope_asset(self):
        assert contract().classify("app.example.test") is ScopeClassification.IN_SCOPE

    def test_out_of_scope_beats_in_scope_on_overlap(self):
        # 'x.blog.example.test' matches both patterns. Denial wins.
        assert (
            contract().classify("x.blog.example.test")
            is ScopeClassification.OUT_OF_SCOPE
        )

    def test_unmatched_asset_is_unresolved_not_permitted(self):
        assert contract().classify("other.test") is ScopeClassification.UNRESOLVED


class TestStaleness:
    def test_fresh_contract_is_not_stale(self):
        assert not contract().is_stale(
            now=NOW + timedelta(days=3), max_age=timedelta(days=7)
        )

    def test_contract_past_the_window_is_stale(self):
        assert contract().is_stale(
            now=NOW + timedelta(days=8), max_age=timedelta(days=7)
        )


class TestFingerprint:
    def test_fingerprint_is_stable_for_identical_content(self):
        assert contract().fingerprint() == contract().fingerprint()

    def test_fingerprint_changes_when_scope_changes(self):
        widened = contract(
            assets_in_scope=[
                AssetPattern(PatternType.WILDCARD, "*.example.test"),
                AssetPattern(PatternType.WILDCARD, "*.other.test"),
            ]
        )
        assert widened.fingerprint() != contract().fingerprint()

    def test_fingerprint_changes_when_granted_authority_changes(self):
        assert contract(max_authority="INTRUSIVE").fingerprint() != contract().fingerprint()

    def test_fingerprint_changes_when_rate_limit_changes(self):
        assert contract(rate_limit_rps=1).fingerprint() != contract(
            rate_limit_rps=2
        ).fingerprint()


class TestProhibitions:
    def test_prohibited_technique_is_matched_case_insensitively(self):
        c = contract(prohibited_techniques=["Denial_Of_Service"])
        assert c.prohibits("denial_of_service")
        assert not c.prohibits("passive_read")

    def test_no_technique_is_not_a_prohibition(self):
        assert not contract(prohibited_techniques=["dos"]).prohibits(None)


def test_round_trips_through_dict():
    original = contract(prohibited_techniques=["dos"], rate_limit_rps=2)
    restored = ScopeContract.from_dict(original.to_dict())
    assert restored.fingerprint() == original.fingerprint()
    assert restored.status is original.status
    assert restored.human_reviewed is True
