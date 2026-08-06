"""The compiler must fail closed, and must never hand out authority by itself.

The two fixture tests at the bottom are the proof artifacts the build slice
requires: one programme that compiles clean, one that is blocked.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from greytheory.authority.compiler import compile_contract, mark_reviewed, source_hash
from greytheory.authority.scope import ContractStatus

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures" / "programmes"
NOW = datetime(2026, 8, 6, tzinfo=timezone.utc)

CLEAN = {
    "id": "clean",
    "verified_at": "2026-08-06T00:00:00+00:00",
    "max_authority": "LOCAL_FIXTURE",
    "in_scope": [{"type": "wildcard", "value": "*.example.test"}],
    "out_of_scope": [{"type": "exact", "value": "legacy.example.test"}],
}


def compile_clean(**overrides):
    programme = {**CLEAN, **overrides}
    return compile_contract(programme, raw_source=json.dumps(programme), now=NOW)


class TestCleanCompile:
    def test_a_clean_programme_is_pending_review_not_verified(self):
        # The compiler never grants authority. A human has to look first.
        result = compile_clean()
        assert result.contract.status is ContractStatus.PENDING_REVIEW
        assert result.contract.human_reviewed is False
        assert result.ambiguities == []

    def test_source_hash_is_recorded(self):
        result = compile_clean()
        assert result.contract.source_hashes[0].startswith("sha256:")

    def test_source_hash_changes_when_the_programme_text_changes(self):
        assert source_hash("original rules") != source_hash("original rules ")


class TestAmbiguityDetection:
    def test_no_in_scope_assets_blocks(self):
        result = compile_clean(in_scope=[])
        assert result.blocked
        assert any("grants nothing" in a for a in result.ambiguities)

    def test_unparseable_pattern_blocks_rather_than_being_skipped(self):
        result = compile_clean(
            in_scope=[
                {"type": "wildcard", "value": "*.example.test"},
                {"type": "cidr", "value": "not-a-cidr"},
            ]
        )
        assert result.blocked
        assert any("could not be parsed" in a for a in result.ambiguities)

    def test_asset_in_both_lists_blocks(self):
        result = compile_clean(
            out_of_scope=[{"type": "wildcard", "value": "*.example.test"}]
        )
        assert result.blocked
        assert any("both in-scope and out-of-scope" in a for a in result.ambiguities)

    def test_interactive_authority_without_a_rate_limit_blocks(self):
        result = compile_clean(max_authority="PASSIVE_HTTP")
        assert result.blocked
        assert any("no rate limit" in a for a in result.ambiguities)

    def test_interactive_authority_with_a_rate_limit_compiles(self):
        result = compile_clean(max_authority="PASSIVE_HTTP", rate_limit_rps=2)
        assert not result.blocked

    def test_unknown_authority_downgrades_to_none_and_blocks(self):
        result = compile_clean(max_authority="SUPERUSER")
        assert result.blocked
        assert result.contract.max_authority == "NONE"

    def test_unresolved_markers_in_notes_block(self):
        result = compile_clean(notes="rate limit is TBD, ask the programme")
        assert result.blocked
        assert any("unresolved marker" in a for a in result.ambiguities)

    def test_unresolved_marker_in_a_scope_note_blocks(self):
        result = compile_clean(
            in_scope=[
                {
                    "type": "wildcard",
                    "value": "*.example.test",
                    "note": "unclear whether v3 counts",
                }
            ]
        )
        assert result.blocked

    def test_paused_programme_blocks(self):
        assert compile_clean(paused=True).blocked

    def test_missing_verified_at_blocks(self):
        programme = {k: v for k, v in CLEAN.items() if k != "verified_at"}
        result = compile_contract(programme, raw_source="x", now=NOW)
        assert result.blocked
        assert any("verified_at" in a for a in result.ambiguities)

    def test_missing_raw_source_is_itself_an_ambiguity(self):
        result = compile_contract(CLEAN, now=NOW)
        assert result.blocked
        assert any("no raw programme source" in a for a in result.ambiguities)

    def test_missing_id_blocks(self):
        programme = {k: v for k, v in CLEAN.items() if k != "id"}
        result = compile_contract(programme, raw_source="x", now=NOW)
        assert result.blocked


class TestHumanReview:
    def test_review_promotes_a_clean_contract_to_verified(self):
        contract = compile_clean().contract
        mark_reviewed(contract, reviewer="chase")
        assert contract.status is ContractStatus.VERIFIED
        assert contract.human_reviewed is True
        assert "chase" in contract.notes

    def test_review_cannot_rescue_a_blocked_contract(self):
        # Review confirms a clean compile was read. It does not resolve
        # ambiguity — that requires fixing the source and recompiling.
        contract = compile_clean(in_scope=[]).contract
        with pytest.raises(ValueError, match="cannot be reviewed into verification"):
            mark_reviewed(contract, reviewer="chase")


class TestShippedFixtures:
    def test_verified_fixture_compiles_clean(self):
        raw = (FIXTURES / "mock-verified.json").read_text(encoding="utf-8")
        result = compile_contract(json.loads(raw), raw_source=raw, now=NOW)

        assert result.ambiguities == []
        assert result.contract.status is ContractStatus.PENDING_REVIEW

        mark_reviewed(result.contract, reviewer="test")
        assert result.contract.status is ContractStatus.VERIFIED

    def test_ambiguous_fixture_is_blocked_with_every_expected_defect(self):
        raw = (FIXTURES / "mock-ambiguous.json").read_text(encoding="utf-8")
        programme = json.loads(raw)
        result = compile_contract(programme, raw_source=raw, now=NOW)

        assert result.blocked
        assert result.contract.status is ContractStatus.BLOCKED

        joined = " | ".join(result.ambiguities).lower()
        assert "could not be parsed" in joined       # unparseable CIDR
        assert "both in-scope and out-of-scope" in joined
        assert "no rate limit" in joined
        assert "unresolved marker" in joined
        # One ambiguity per declared defect, at minimum.
        assert len(result.ambiguities) >= len(programme["_expected_ambiguities"])
