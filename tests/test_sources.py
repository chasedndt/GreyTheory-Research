"""ProgrammeSourceBundle is multi-source authority, compiled offline."""

from __future__ import annotations

import json
import shutil
import socket
from datetime import datetime, timezone
from pathlib import Path

import pytest

import greytheory
from greytheory.audit import AuditLog
from greytheory.authority.compiler import source_hash
from greytheory.authority.scope import ContractStatus, ScopeClassification
from greytheory.authority.sources import (
    BundleError,
    CaptureMode,
    DerivationKind,
    ProgrammeSourceBundle,
    SourceKind,
    compile_source_bundle,
)
from greytheory.cli import main
from greytheory.registry import ProgrammeRegistry, RegistryError

REAL_BUNDLE = (
    Path(__file__).resolve().parent.parent
    / "fixtures"
    / "programmes"
    / "public"
    / "hackerone-gitlab-2026-08-09"
)
NOW = datetime(2026, 8, 9, 10, 30, tzinfo=timezone.utc)


def copy_bundle(tmp_path: Path) -> Path:
    target = tmp_path / "bundle"
    shutil.copytree(REAL_BUNDLE, target)
    return target


def read_manifest(bundle: Path) -> dict:
    return json.loads((bundle / "manifest.json").read_text(encoding="utf-8"))


def write_manifest(bundle: Path, manifest: dict) -> None:
    (bundle / "manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )


def update_source_hash(bundle: Path, source_id: str) -> None:
    manifest = read_manifest(bundle)
    source = next(item for item in manifest["sources"] if item["id"] == source_id)
    content = (bundle / source["path"]).read_text(encoding="utf-8")
    source["sha256"] = source_hash(content)
    write_manifest(bundle, manifest)


class TestRealPublicBundle:
    def test_bundle_api_is_exported_from_the_package_root(self):
        assert greytheory.ProgrammeSourceBundle is ProgrammeSourceBundle
        assert greytheory.compile_source_bundle is compile_source_bundle

    def test_loads_three_explicit_source_classes(self):
        bundle = ProgrammeSourceBundle.load(REAL_BUNDLE)

        assert bundle.id == "hackerone-gitlab-2026-08-09"
        assert bundle.precedence == (
            "gitlab-scope-csv",
            "gitlab-programme-guidelines",
            "hackerone-core-ineligible",
        )
        assert [source.kind for source in bundle.sources] == [
            SourceKind.SCOPE_TABLE,
            SourceKind.PROGRAMME_POLICY,
            SourceKind.PLATFORM_DEFAULT,
        ]
        assert [source.capture_mode for source in bundle.sources] == [
            CaptureMode.STRUCTURED_EXPORT,
            CaptureMode.OPERATOR_EXTRACT,
            CaptureMode.OPERATOR_EXTRACT,
        ]
        assert all(source.intact for source in bundle.sources)
        assert len(bundle.derivations) == 1
        assert bundle.derivations[0].kind is DerivationKind.HACKERONE_SCOPE_CSV_V1

    def test_compiles_clean_but_never_self_verifies(self):
        result = compile_source_bundle(REAL_BUNDLE, now=NOW)

        assert result.contract.status is ContractStatus.PENDING_REVIEW
        assert result.contract.human_reviewed is False
        assert result.contract.max_authority == "LOCAL_FIXTURE"
        assert result.ambiguities == []
        assert len(result.contract.assets_in_scope) == 19
        assert len(result.contract.assets_out_of_scope) == 25

    def test_records_each_source_hash_and_the_whole_bundle_hash(self):
        bundle = ProgrammeSourceBundle.load(REAL_BUNDLE)
        result = compile_source_bundle(bundle, now=NOW)

        expected_sources = [
            bundle.sources_by_id[source_id].actual_hash
            for source_id in bundle.precedence
        ]
        assert result.contract.source_hashes == [
            *expected_sources,
            bundle.bundle_hash,
        ]
        assert json.loads(result.snapshot)["programme"]["id"] == bundle.programme_id

    def test_explicit_exclusion_beats_the_broader_wildcard(self):
        contract = compile_source_bundle(REAL_BUNDLE, now=NOW).contract

        assert contract.classify("gitlab.com") is ScopeClassification.IN_SCOPE
        assert contract.classify("support.gitlab.com") is ScopeClassification.OUT_OF_SCOPE
        assert contract.classify("research.gitlab.net") is ScopeClassification.IN_SCOPE
        assert (
            contract.classify("api.runway.gitlab.net")
            is ScopeClassification.OUT_OF_SCOPE
        )

    def test_compilation_performs_no_network_io(self, monkeypatch):
        def forbidden(*_args, **_kwargs):
            raise AssertionError("programme bundle compilation attempted network I/O")

        monkeypatch.setattr(socket, "create_connection", forbidden)
        assert not compile_source_bundle(REAL_BUNDLE, now=NOW).blocked


class TestBundleIntegrity:
    def test_tampered_source_blocks_instead_of_trusting_the_manifest(self, tmp_path):
        bundle = copy_bundle(tmp_path)
        source = bundle / "sources" / "gitlab-programme-guidelines.md"
        source.write_text(
            source.read_text(encoding="utf-8") + "\nChanged after capture.\n",
            encoding="utf-8",
        )

        result = compile_source_bundle(bundle, now=NOW)

        assert result.blocked
        assert any("hash mismatch" in item for item in result.ambiguities)

    def test_a_recaptured_source_changes_the_bundle_hash(self, tmp_path):
        bundle = copy_bundle(tmp_path)
        before = ProgrammeSourceBundle.load(bundle).bundle_hash
        source = bundle / "sources" / "gitlab-programme-guidelines.md"
        source.write_text(
            source.read_text(encoding="utf-8") + "\nNew public-policy fact.\n",
            encoding="utf-8",
        )
        update_source_hash(bundle, "gitlab-programme-guidelines")

        after = ProgrammeSourceBundle.load(bundle)

        assert after.bundle_hash != before
        assert not compile_source_bundle(after, now=NOW).blocked

    def test_missing_or_unknown_precedence_blocks(self, tmp_path):
        bundle = copy_bundle(tmp_path)
        manifest = read_manifest(bundle)
        manifest["precedence"] = [
            "gitlab-scope-csv",
            "gitlab-scope-csv",
            "not-a-source",
        ]
        write_manifest(bundle, manifest)

        result = compile_source_bundle(bundle, now=NOW)

        assert result.blocked
        assert any("duplicate" in item for item in result.ambiguities)
        assert any("omits source ids" in item for item in result.ambiguities)
        assert any("unknown source ids" in item for item in result.ambiguities)

    def test_uncited_authority_field_blocks(self, tmp_path):
        bundle = copy_bundle(tmp_path)
        manifest = read_manifest(bundle)
        del manifest["field_sources"]["max_authority"]
        write_manifest(bundle, manifest)

        result = compile_source_bundle(bundle, now=NOW)

        assert result.blocked
        assert any("max_authority" in item for item in result.ambiguities)

    def test_programme_record_cannot_omit_a_structured_scope_row(self, tmp_path):
        bundle = copy_bundle(tmp_path)
        programme_path = bundle / "programme.json"
        programme = json.loads(programme_path.read_text(encoding="utf-8"))
        programme["in_scope"] = programme["in_scope"][1:]
        programme_path.write_text(
            json.dumps(programme, indent=2) + "\n", encoding="utf-8"
        )

        result = compile_source_bundle(bundle, now=NOW)

        assert result.blocked
        assert any("record omits in_scope" in item for item in result.ambiguities)

    def test_recaptured_scope_export_must_be_renormalised(self, tmp_path):
        bundle = copy_bundle(tmp_path)
        source = bundle / "sources" / "gitlab-scope.csv"
        source.write_text(
            source.read_text(encoding="utf-8")
            + "new.gitlab.example,URL,,true,true,,,,medium,,2026-08-09 10:30:00 UTC,2026-08-09 10:30:00 UTC\n",
            encoding="utf-8",
        )
        update_source_hash(bundle, "gitlab-scope-csv")

        result = compile_source_bundle(bundle, now=NOW)

        assert result.blocked
        assert any("record omits in_scope" in item for item in result.ambiguities)

    def test_unsafe_source_path_is_refused(self, tmp_path):
        bundle = copy_bundle(tmp_path)
        manifest = read_manifest(bundle)
        manifest["sources"][0]["path"] = "../outside.csv"
        write_manifest(bundle, manifest)

        with pytest.raises(BundleError, match="safe relative POSIX path"):
            ProgrammeSourceBundle.load(bundle)

    @pytest.mark.parametrize(
        "url",
        [
            "http://hackerone.com/teams/gitlab/assets/download_csv.csv",
            "https://user:password@hackerone.com/policy",
            "https://localhost/policy",
            "https://LOCALHOST:443/policy",
            "https://127.0.0.1:443/policy",
            "https://[::1]/policy",
            "https:///missing-host",
        ],
    )
    def test_source_provenance_requires_a_public_https_url(self, tmp_path, url):
        bundle = copy_bundle(tmp_path)
        manifest = read_manifest(bundle)
        manifest["sources"][0]["url"] = url
        write_manifest(bundle, manifest)

        with pytest.raises(BundleError, match="public HTTPS URL"):
            ProgrammeSourceBundle.load(bundle)

    def test_non_utf8_source_is_refused_as_a_bundle_error(self, tmp_path):
        bundle = copy_bundle(tmp_path)
        source = bundle / "sources" / "gitlab-programme-guidelines.md"
        source.write_bytes(b"\xff\xfe\x00")

        with pytest.raises(BundleError, match="could not be read as UTF-8"):
            ProgrammeSourceBundle.load(bundle)


class TestHumanConflictResolution:
    def test_pending_resolution_blocks(self, tmp_path):
        bundle = copy_bundle(tmp_path)
        manifest = read_manifest(bundle)
        manifest["human_resolutions"] = [
            {
                "id": "wildcard-exception",
                "issue": "A narrower exclusion sits inside a broad wildcard.",
                "decision": "Preserve the explicit exclusion.",
                "source_ids": ["gitlab-scope-csv"],
                "status": "pending"
            }
        ]
        write_manifest(bundle, manifest)

        result = compile_source_bundle(bundle, now=NOW)

        assert result.blocked
        assert any("remains pending" in item for item in result.ambiguities)

    def test_accepted_resolution_requires_human_identity_and_time(self, tmp_path):
        bundle = copy_bundle(tmp_path)
        manifest = read_manifest(bundle)
        manifest["human_resolutions"] = [
            {
                "id": "wildcard-exception",
                "issue": "A narrower exclusion sits inside a broad wildcard.",
                "decision": "Preserve the explicit exclusion.",
                "source_ids": ["gitlab-scope-csv"],
                "status": "accepted"
            }
        ]
        write_manifest(bundle, manifest)

        result = compile_source_bundle(bundle, now=NOW)

        assert result.blocked
        assert any("lacks decided_by or decided_at" in item for item in result.ambiguities)

    def test_complete_human_resolution_compiles(self, tmp_path):
        bundle = copy_bundle(tmp_path)
        manifest = read_manifest(bundle)
        manifest["human_resolutions"] = [
            {
                "id": "wildcard-exception",
                "issue": "A narrower exclusion sits inside a broad wildcard.",
                "decision": "Preserve both patterns; out-of-scope wins.",
                "source_ids": ["gitlab-scope-csv"],
                "status": "accepted",
                "decided_by": "fixture-reviewer",
                "decided_at": "2026-08-09T10:30:00Z"
            }
        ]
        write_manifest(bundle, manifest)

        assert not compile_source_bundle(bundle, now=NOW).blocked


class TestBundleRegistry:
    def test_registry_keeps_the_complete_bundle_snapshot(self, tmp_path):
        registry = ProgrammeRegistry(tmp_path / "contracts", clock=lambda: NOW)

        result = registry.register_bundle(REAL_BUNDLE)
        snapshot = json.loads(registry.source("hackerone-gitlab-public", 1))

        assert result.version.contract.status is ContractStatus.PENDING_REVIEW
        assert len(snapshot["sources"]) == 3
        assert all(source["content"] for source in snapshot["sources"])

    def test_any_source_change_invalidates_review(self, tmp_path):
        bundle = copy_bundle(tmp_path)
        registry = ProgrammeRegistry(tmp_path / "contracts", clock=lambda: NOW)
        registry.register_bundle(bundle)
        registry.review("hackerone-gitlab-public", reviewer="fixture-reviewer")

        unchanged = registry.register_bundle(bundle)
        assert unchanged.version.contract.human_reviewed
        assert not unchanged.source_changed

        source = bundle / "sources" / "hackerone-core-ineligible.md"
        source.write_text(
            source.read_text(encoding="utf-8") + "\nNew platform fact.\n",
            encoding="utf-8",
        )
        update_source_hash(bundle, "hackerone-core-ineligible")
        changed = registry.register_bundle(bundle)

        assert changed.source_changed
        assert changed.requires_review
        assert not changed.version.contract.human_reviewed

    def test_bundle_registration_is_audited(self, tmp_path):
        audit = AuditLog(tmp_path / "audit.jsonl")
        registry = ProgrammeRegistry(
            tmp_path / "contracts", audit=audit, clock=lambda: NOW
        )

        registry.register_bundle(REAL_BUNDLE)
        detail = audit.records()[-1].detail

        assert detail["source_kind"] == "bundle"
        assert detail["bundle_id"] == "hackerone-gitlab-2026-08-09"
        assert detail["source_count"] == 3
        audit.verify()

    def test_bundle_error_is_exposed_as_registry_refusal(self, tmp_path):
        with pytest.raises(RegistryError, match="invalid programme source bundle"):
            ProgrammeRegistry(tmp_path / "contracts").register_bundle(
                tmp_path / "missing"
            )


def test_cli_registers_the_bundle_offline(tmp_path, capsys):
    exit_code = main(
        [
            "--audit",
            str(tmp_path / "audit.jsonl"),
            "programme",
            "--registry",
            str(tmp_path / "contracts"),
            "register-bundle",
            str(REAL_BUNDLE),
        ]
    )

    assert exit_code == 0
    output = capsys.readouterr().out
    assert "hackerone-gitlab-public" in output
    assert "PENDING_REVIEW" in output
    assert "LOCAL_FIXTURE" in output
