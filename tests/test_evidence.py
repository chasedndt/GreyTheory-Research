"""The evidence vault: raw stays private, redacted travels, nothing leaks."""

# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 ChaseInTech

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from greytheory.audit import AuditLog
from greytheory.evidence import (
    EvidenceError,
    EvidenceVault,
    VaultLocationError,
    find_repository_root,
    resolve_root,
)

NOW = datetime(2026, 8, 6, 12, 0, tzinfo=timezone.utc)
AUTHORITY = "fingerprint_abc123"

RAW = b"GET /api/doc/9 HTTP/1.1\nCookie: session=SECRET_TOKEN_VALUE\n"
REDACTED = b"GET /api/doc/9 HTTP/1.1\nCookie: session=[REDACTED]\n"


@pytest.fixture
def vault(tmp_path):
    return EvidenceVault(tmp_path / "vault", clock=lambda: NOW)


def store(vault, **overrides):
    kwargs = dict(
        finding_id="finding_1",
        artifact_id="artifact_1",
        kind="http_request_response",
        data=RAW,
        authority_ref=AUTHORITY,
        extension=".http",
    )
    kwargs.update(overrides)
    return vault.store_raw(**kwargs)


class TestRootResolution:
    def test_explicit_root_wins(self, tmp_path):
        assert resolve_root(tmp_path / "here") == tmp_path / "here"

    def test_environment_override(self, tmp_path, monkeypatch):
        monkeypatch.setenv("GREYTHEORY_EVIDENCE_ROOT", str(tmp_path / "env"))
        assert resolve_root() == tmp_path / "env"

    def test_chaseos_vault_is_used_when_present(self, tmp_path, monkeypatch):
        monkeypatch.delenv("GREYTHEORY_EVIDENCE_ROOT", raising=False)
        monkeypatch.setenv("CHASEOS_VAULT_ROOT", str(tmp_path / "vault"))
        assert resolve_root() == tmp_path / "vault" / "07_LOGS" / "greytheory-evidence"

    def test_greytheory_override_beats_chaseos(self, tmp_path, monkeypatch):
        monkeypatch.setenv("GREYTHEORY_EVIDENCE_ROOT", str(tmp_path / "mine"))
        monkeypatch.setenv("CHASEOS_VAULT_ROOT", str(tmp_path / "vault"))
        assert resolve_root() == tmp_path / "mine"

    def test_standalone_default_needs_no_chaseos(self, monkeypatch):
        # GreyTheory is Apache-licensed and runs on its own. With nothing
        # configured it still resolves to a sane per-user location.
        monkeypatch.delenv("GREYTHEORY_EVIDENCE_ROOT", raising=False)
        monkeypatch.delenv("CHASEOS_VAULT_ROOT", raising=False)
        root = resolve_root()
        assert root.is_absolute()
        assert "greytheory" in str(root).lower()


class TestRepositoryGuard:
    def test_refuses_to_sit_inside_a_git_working_tree(self, tmp_path):
        (tmp_path / ".git").mkdir()
        with pytest.raises(VaultLocationError, match="inside the git working tree"):
            EvidenceVault(tmp_path / "evidence")

    def test_refuses_from_a_nested_directory_too(self, tmp_path):
        (tmp_path / ".git").mkdir()
        with pytest.raises(VaultLocationError):
            EvidenceVault(tmp_path / "a" / "b" / "c")

    def test_can_be_forced_for_throwaway_trees(self, tmp_path):
        (tmp_path / ".git").mkdir()
        assert EvidenceVault(tmp_path / "evidence", allow_in_repository=True)

    def test_find_repository_root(self, tmp_path):
        (tmp_path / ".git").mkdir()
        nested = tmp_path / "a" / "b"
        nested.mkdir(parents=True)
        assert find_repository_root(nested) == tmp_path
        assert find_repository_root(tmp_path.parent) is None


class TestStoringRaw:
    def test_stores_and_hashes(self, vault):
        artifact = store(vault)
        assert artifact.raw_bytes == len(RAW)
        assert artifact.raw_sha256
        assert artifact.contains_sensitive_data is True  # assumed until redacted
        assert not artifact.is_exportable

    def test_written_to_the_raw_tree_only(self, vault):
        store(vault)
        assert (vault.raw_dir / "finding_1" / "artifact_1.http").is_file()
        assert not (vault.redacted_dir / "finding_1" / "artifact_1.http").exists()

    def test_requires_an_authority_reference(self, vault):
        with pytest.raises(EvidenceError, match="authority reference"):
            store(vault, authority_ref="")

    def test_refuses_empty_payloads(self, vault):
        with pytest.raises(EvidenceError, match="empty artifact"):
            store(vault, data=b"")

    def test_raw_is_written_once(self, vault):
        # Overwriting would destroy the original silently.
        store(vault)
        with pytest.raises(EvidenceError, match="written once"):
            store(vault, data=b"different bytes")

    def test_rejects_unsafe_identifiers(self, vault):
        with pytest.raises(EvidenceError, match="safe identifier"):
            store(vault, finding_id="../../escape")
        with pytest.raises(EvidenceError, match="safe identifier"):
            store(vault, artifact_id="a/b")


class TestRedaction:
    def test_attaching_a_redacted_copy_makes_it_exportable(self, vault):
        store(vault)
        updated = vault.attach_redacted(
            finding_id="finding_1", artifact_id="artifact_1", data=REDACTED
        )
        assert updated.is_redacted
        assert updated.is_exportable
        assert updated.contains_sensitive_data is False

    def test_an_identical_copy_is_not_a_redaction(self, vault):
        # Copying the raw bytes across is the exact failure this catches.
        store(vault)
        with pytest.raises(EvidenceError, match="nothing was redacted"):
            vault.attach_redacted(
                finding_id="finding_1", artifact_id="artifact_1", data=RAW
            )

    def test_cannot_redact_twice(self, vault):
        store(vault)
        vault.attach_redacted(
            finding_id="finding_1", artifact_id="artifact_1", data=REDACTED
        )
        with pytest.raises(EvidenceError, match="already has a redacted"):
            vault.attach_redacted(
                finding_id="finding_1", artifact_id="artifact_1", data=b"other"
            )

    def test_unknown_artifact(self, vault):
        store(vault)
        with pytest.raises(EvidenceError, match="no artifact"):
            vault.attach_redacted(
                finding_id="finding_1", artifact_id="nope", data=REDACTED
            )

    def test_reading_redacted_before_it_exists_fails(self, vault):
        store(vault)
        with pytest.raises(EvidenceError, match="no redacted counterpart"):
            vault.read_redacted("finding_1", "artifact_1")

    def test_round_trip(self, vault):
        store(vault)
        vault.attach_redacted(
            finding_id="finding_1", artifact_id="artifact_1", data=REDACTED
        )
        assert vault.read_raw("finding_1", "artifact_1") == RAW
        assert vault.read_redacted("finding_1", "artifact_1") == REDACTED


class TestIntegrity:
    def test_a_clean_vault_verifies(self, vault):
        store(vault)
        vault.attach_redacted(
            finding_id="finding_1", artifact_id="artifact_1", data=REDACTED
        )
        assert vault.verify("finding_1") == []

    def test_modified_raw_evidence_is_detected(self, vault):
        store(vault)
        (vault.raw_dir / "finding_1" / "artifact_1.http").write_bytes(b"tampered")
        assert "has been modified" in " ".join(vault.verify("finding_1"))

    def test_missing_raw_evidence_is_detected(self, vault):
        store(vault)
        (vault.raw_dir / "finding_1" / "artifact_1.http").unlink()
        assert "is missing" in " ".join(vault.verify("finding_1"))

    def test_modified_redacted_evidence_is_detected(self, vault):
        store(vault)
        vault.attach_redacted(
            finding_id="finding_1", artifact_id="artifact_1", data=REDACTED
        )
        (vault.redacted_dir / "finding_1" / "artifact_1.http").write_bytes(b"tampered")
        assert "redacted artifact has been modified" in " ".join(vault.verify("finding_1"))


class TestExport:
    def test_export_lists_only_redacted_paths(self, vault):
        store(vault)
        vault.attach_redacted(
            finding_id="finding_1", artifact_id="artifact_1", data=REDACTED
        )
        package = vault.export_package("finding_1")

        assert len(package["artifacts"]) == 1
        entry = package["artifacts"][0]
        assert "redacted" in entry["path"]
        assert str(vault.raw_dir) not in entry["path"]
        assert entry["authority_ref"] == AUTHORITY

    def test_export_refuses_while_anything_is_unredacted(self, vault):
        # Partial export is how raw evidence escapes.
        store(vault)
        store(vault, artifact_id="artifact_2", data=b"second capture")
        vault.attach_redacted(
            finding_id="finding_1", artifact_id="artifact_1", data=REDACTED
        )
        with pytest.raises(EvidenceError, match="no redacted counterpart"):
            vault.export_package("finding_1")

    def test_export_refuses_when_integrity_fails(self, vault):
        store(vault)
        vault.attach_redacted(
            finding_id="finding_1", artifact_id="artifact_1", data=REDACTED
        )
        (vault.raw_dir / "finding_1" / "artifact_1.http").write_bytes(b"tampered")
        with pytest.raises(EvidenceError, match="integrity check failed"):
            vault.export_package("finding_1")

    def test_export_of_an_empty_finding_fails(self, vault):
        with pytest.raises(EvidenceError, match="no evidence held"):
            vault.export_package("finding_absent")


class TestManifestAndAudit:
    def test_manifest_persists_across_instances(self, tmp_path):
        first = EvidenceVault(tmp_path / "vault", clock=lambda: NOW)
        store(first)
        second = EvidenceVault(tmp_path / "vault", clock=lambda: NOW)
        assert len(second.manifest("finding_1").artifacts) == 1

    def test_writes_are_audited_with_their_authority(self, tmp_path):
        audit = AuditLog(tmp_path / "audit.jsonl")
        vault = EvidenceVault(tmp_path / "vault", audit=audit, clock=lambda: NOW)
        store(vault)
        vault.attach_redacted(
            finding_id="finding_1", artifact_id="artifact_1", data=REDACTED
        )

        actions = [r.action for r in audit.records()]
        assert actions == ["evidence.store_raw", "evidence.attach_redacted"]
        assert all(r.authority_ref == AUTHORITY for r in audit.records())
        audit.verify()

    def test_vault_works_without_an_audit_log(self, vault):
        assert store(vault)
