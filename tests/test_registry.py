"""The programme registry: versions, drift, and what needs the operator."""

# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 ChaseInTech

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

import pytest

from greytheory.audit import AuditLog
from greytheory.authority.scope import ContractStatus
from greytheory.registry import ProgrammeRegistry, RegistryError, diff_contracts

NOW = datetime(2026, 8, 6, 12, 0, tzinfo=timezone.utc)

BASE = {
    "id": "acme",
    "verified_at": "2026-08-06T00:00:00+00:00",
    "max_authority": "LOCAL_FIXTURE",
    "in_scope": [{"type": "wildcard", "value": "*.acme.test"}],
    "out_of_scope": [{"type": "exact", "value": "legacy.acme.test"}],
    "prohibited_techniques": ["denial_of_service"],
}


@pytest.fixture
def registry(tmp_path):
    return ProgrammeRegistry(tmp_path / "contracts", clock=lambda: NOW)


def register(registry, **overrides):
    programme = {**BASE, **overrides}
    return registry.register(programme, raw_source=json.dumps(programme, sort_keys=True))


class TestRegistration:
    def test_first_registration_creates_version_one(self, registry):
        result = register(registry)
        assert result.is_new_programme
        assert result.version.version == 1
        assert result.diff is None
        assert result.requires_review

    def test_a_source_snapshot_is_required(self, registry):
        with pytest.raises(RegistryError, match="source snapshot is required"):
            registry.register(BASE, raw_source="   ")

    def test_the_snapshot_is_kept_verbatim(self, registry):
        raw = json.dumps(BASE, sort_keys=True)
        registry.register(BASE, raw_source=raw)
        assert registry.source("acme", 1) == raw

    def test_versions_accumulate_and_contracts_are_never_edited(self, registry):
        register(registry)
        register(registry, in_scope=[{"type": "wildcard", "value": "*.acme.test"},
                                    {"type": "wildcard", "value": "*.acme-api.test"}])
        versions = registry.versions("acme")
        assert [v.version for v in versions] == [1, 2]
        # v1 still says what it said.
        assert len(versions[0].contract.assets_in_scope) == 1
        assert len(versions[1].contract.assets_in_scope) == 2

    def test_rejects_unsafe_programme_ids(self, registry):
        with pytest.raises(RegistryError, match="safe identifier"):
            registry.register({**BASE, "id": "../escape"}, raw_source="x")


class TestReviewAndDrift:
    def test_review_promotes_to_verified(self, registry):
        register(registry)
        contract = registry.review("acme", reviewer="chase")
        assert contract.status is ContractStatus.VERIFIED
        assert registry.current_contract("acme").human_reviewed

    def test_changed_source_invalidates_the_review(self, registry):
        # The rule the whole module exists for.
        register(registry)
        registry.review("acme", reviewer="chase")

        result = register(registry, out_of_scope=[{"type": "wildcard", "value": "*.beta.acme.test"}])

        assert result.source_changed
        assert result.requires_review
        assert not result.version.contract.human_reviewed

    def test_identical_source_carries_the_review_forward(self, registry):
        # Re-reading text a person already read is friction with no safety value.
        register(registry)
        registry.review("acme", reviewer="chase")
        result = register(registry)

        assert not result.source_changed
        assert not result.requires_review
        assert result.version.contract.human_reviewed

    def test_identical_source_does_not_carry_review_onto_a_blocked_contract(self, tmp_path):
        registry = ProgrammeRegistry(tmp_path / "c", clock=lambda: NOW)
        registry.register(BASE, raw_source="fixed source")
        registry.review("acme", reviewer="chase")
        # Same source string, but the record now compiles blocked.
        result = registry.register({**BASE, "paused": True}, raw_source="fixed source")
        assert result.blocked
        assert not result.version.contract.human_reviewed

    def test_cannot_review_twice(self, registry):
        register(registry)
        registry.review("acme", reviewer="chase")
        with pytest.raises(RegistryError, match="already reviewed"):
            registry.review("acme", reviewer="chase")

    def test_cannot_review_an_unregistered_programme(self, registry):
        with pytest.raises(RegistryError, match="no programme"):
            registry.review("nobody", reviewer="chase")


class TestDiff:
    def test_detects_a_widened_scope(self, registry):
        register(registry)
        result = register(
            registry,
            in_scope=[
                {"type": "wildcard", "value": "*.acme.test"},
                {"type": "wildcard", "value": "*.acme-api.test"},
            ],
        )
        assert result.diff.changed
        assert not result.diff.is_narrowing
        assert "wildcard:*.acme-api.test" in result.diff.added_in_scope

    def test_a_removed_asset_is_narrowing(self, registry):
        # The direction that matters: work already done may have been against
        # an asset that is no longer authorised.
        register(registry)
        result = register(
            registry, in_scope=[{"type": "exact", "value": "app.acme.test"}]
        )
        assert result.diff.is_narrowing
        assert "wildcard:*.acme.test" in result.diff.removed_in_scope

    def test_a_new_exclusion_is_narrowing(self, registry):
        register(registry)
        result = register(
            registry,
            out_of_scope=[
                {"type": "exact", "value": "legacy.acme.test"},
                {"type": "wildcard", "value": "*.internal.acme.test"},
            ],
        )
        assert result.diff.is_narrowing

    def test_a_new_prohibition_is_narrowing(self, registry):
        register(registry)
        result = register(
            registry, prohibited_techniques=["denial_of_service", "automation"]
        )
        assert result.diff.is_narrowing
        assert "automation" in result.diff.added_prohibitions

    def test_reduced_authority_is_narrowing(self, registry):
        register(registry, max_authority="PASSIVE_HTTP", rate_limit_rps=2)
        result = register(registry, max_authority="LOCAL_FIXTURE")
        assert result.diff.is_narrowing
        assert result.diff.authority_change == ("PASSIVE_HTTP", "LOCAL_FIXTURE")

    def test_raised_authority_is_not_narrowing(self, registry):
        register(registry)
        result = register(registry, max_authority="PASSIVE_HTTP", rate_limit_rps=5)
        assert result.diff.changed
        assert not result.diff.is_narrowing

    def test_rate_limit_change_is_reported(self, registry):
        register(registry, max_authority="PASSIVE_HTTP", rate_limit_rps=10)
        result = register(registry, max_authority="PASSIVE_HTTP", rate_limit_rps=2)
        assert result.diff.rate_limit_change == (10, 2)

    def test_summary_is_human_readable(self, registry):
        register(registry)
        result = register(
            registry, in_scope=[{"type": "exact", "value": "app.acme.test"}]
        )
        assert any("no longer in scope" in line for line in result.diff.summary())

    def test_diff_between_arbitrary_versions(self, registry):
        register(registry)
        register(registry, prohibited_techniques=["denial_of_service", "automation"])
        register(registry, prohibited_techniques=["denial_of_service"])
        assert not registry.diff_versions("acme", 1, 3).changed
        assert registry.diff_versions("acme", 1, 2).changed

    def test_unknown_version(self, registry):
        register(registry)
        with pytest.raises(RegistryError, match="no version 9"):
            registry.diff_versions("acme", 1, 9)


class TestNeedsAttention:
    def test_a_blocked_programme_is_surfaced(self, registry):
        register(registry, in_scope=[])
        items = registry.needs_attention()
        assert [i.reason for i in items] == ["blocked"]

    def test_an_unreviewed_programme_is_surfaced(self, registry):
        register(registry)
        assert [i.reason for i in registry.needs_attention()] == ["awaiting_review"]

    def test_a_reviewed_fresh_programme_is_quiet(self, registry):
        register(registry)
        registry.review("acme", reviewer="chase")
        assert registry.needs_attention() == []

    def test_a_stale_programme_is_surfaced(self, tmp_path):
        registry = ProgrammeRegistry(tmp_path / "c", clock=lambda: NOW)
        register(registry)
        registry.review("acme", reviewer="chase")

        later = ProgrammeRegistry(
            tmp_path / "c", clock=lambda: NOW + timedelta(days=30)
        )
        items = later.needs_attention()
        assert [i.reason for i in items] == ["stale"]
        assert "re-read the programme" in items[0].detail

    def test_blocked_takes_priority_over_review(self, registry):
        # A blocked contract cannot be reviewed, so reporting both would send
        # the operator down a path that dead-ends.
        register(registry, in_scope=[])
        reasons = [i.reason for i in registry.needs_attention()]
        assert reasons == ["blocked"]

    def test_multiple_programmes_are_all_reported(self, registry):
        register(registry)
        register(registry, id="beta")
        assert len(registry.needs_attention()) == 2


class TestConfidentialGuard:
    def test_refuses_confidential_programmes_inside_a_repository(self, tmp_path):
        (tmp_path / ".git").mkdir()
        registry = ProgrammeRegistry(tmp_path / "contracts", clock=lambda: NOW)
        with pytest.raises(RegistryError, match="inside the git working tree"):
            registry.register(
                {**BASE, "confidential": True}, raw_source="private rules"
            )

    def test_public_programmes_are_fine_inside_a_repository(self, tmp_path):
        (tmp_path / ".git").mkdir()
        registry = ProgrammeRegistry(tmp_path / "contracts", clock=lambda: NOW)
        assert registry.register(BASE, raw_source="public rules").version.version == 1

    def test_confidential_can_be_forced(self, tmp_path):
        (tmp_path / ".git").mkdir()
        registry = ProgrammeRegistry(
            tmp_path / "contracts",
            allow_confidential_in_repository=True,
            clock=lambda: NOW,
        )
        assert registry.register(
            {**BASE, "confidential": True}, raw_source="private rules"
        )


class TestPersistenceAndAudit:
    def test_survives_reopening(self, tmp_path):
        first = ProgrammeRegistry(tmp_path / "c", clock=lambda: NOW)
        first.register(BASE, raw_source="rules")
        first.review("acme", reviewer="chase")

        second = ProgrammeRegistry(tmp_path / "c", clock=lambda: NOW)
        assert second.programmes() == ["acme"]
        assert second.current_contract("acme").human_reviewed

    def test_registration_and_review_are_audited(self, tmp_path):
        audit = AuditLog(tmp_path / "audit.jsonl")
        registry = ProgrammeRegistry(tmp_path / "c", audit=audit, clock=lambda: NOW)
        registry.register(BASE, raw_source="rules")
        registry.review("acme", reviewer="chase")

        actions = [r.action for r in audit.records()]
        assert actions == ["programme.register", "programme.review"]
        assert audit.records()[0].detail["programme_id"] == "acme"
        audit.verify()

    def test_the_diff_is_recorded_in_the_audit(self, tmp_path):
        audit = AuditLog(tmp_path / "audit.jsonl")
        registry = ProgrammeRegistry(tmp_path / "c", audit=audit, clock=lambda: NOW)
        registry.register(BASE, raw_source="v1")
        registry.register({**BASE, "in_scope": []}, raw_source="v2")

        detail = audit.records()[-1].detail
        assert detail["source_changed"] is True
        assert detail["diff"]["is_narrowing"] is True

    def test_unknown_programme_reads_as_empty(self, registry):
        assert registry.versions("nobody") == []
        assert registry.latest("nobody") is None
        assert registry.current_contract("nobody") is None


def test_diff_direction_decides_whether_it_is_narrowing(registry):
    # v2 is a strict superset of v1, so widening one way is narrowing the other.
    # A replacement (drop A, add B) is narrowing in *both* directions, which is
    # correct: something was removed either way.
    register(registry)
    register(
        registry,
        in_scope=[
            {"type": "wildcard", "value": "*.acme.test"},
            {"type": "wildcard", "value": "*.acme-api.test"},
        ],
    )
    versions = registry.versions("acme")
    widening = diff_contracts(versions[0].contract, versions[1].contract)
    narrowing = diff_contracts(versions[1].contract, versions[0].contract)

    assert widening.added_in_scope == narrowing.removed_in_scope
    assert not widening.is_narrowing
    assert narrowing.is_narrowing


def test_a_replacement_is_narrowing_in_both_directions(registry):
    register(registry)
    register(registry, in_scope=[{"type": "exact", "value": "app.acme.test"}])
    versions = registry.versions("acme")

    assert diff_contracts(versions[0].contract, versions[1].contract).is_narrowing
    assert diff_contracts(versions[1].contract, versions[0].contract).is_narrowing
