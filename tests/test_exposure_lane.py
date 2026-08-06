"""Lane 2: shape is recorded, values never are, presence is not exposure.

Credential-shaped strings are assembled at runtime from fragments rather than
written as literals. Two reasons: a literal in a committed test file is exactly
the thing this lane exists to find, and secret-scanning push protection would
be right to object to it.
"""

# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 ChaseInTech

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from greytheory.audit import AuditLog
from greytheory.authority.gate import Gate
from greytheory.authority.scope import (
    AssetPattern,
    ContractStatus,
    PatternType,
    ScopeContract,
)
from greytheory.signal import SignalLevel, run_lane
from greytheory.signal.lanes.exposure import (
    ExposureLane,
    fingerprint,
    shannon_entropy,
)

NOW = datetime(2026, 8, 7, 9, 0, tzinfo=timezone.utc)

# Assembled from fragments on purpose - see the module docstring.
AWS_KEY = "AKI" + "A" + "Q" * 16
GITHUB_TOKEN = "gh" + "p_" + "A" * 36
STRIPE_KEY = "sk_" + "test_" + "0" * 24
PEM_HEADER = "-----BEGIN " + "RSA PRIVATE KEY-----"
HIGH_ENTROPY = "aZ9x" + "Kq3Lm7Rv2Tn8Wb4Yd6Pf1Sg5Hj0Ck"


@pytest.fixture
def gate(tmp_path):
    return Gate(AuditLog(tmp_path / "audit.jsonl"), clock=lambda: NOW)


def contract() -> ScopeContract:
    return ScopeContract(
        id="s",
        programme_id="lab",
        verified_at=NOW,
        status=ContractStatus.VERIFIED,
        assets_in_scope=[AssetPattern(PatternType.EXACT, "tree")],
        human_reviewed=True,
    )


def run(gate, root: Path):
    return run_lane(
        ExposureLane(),
        targets={"tree": root},
        gate=gate,
        contract=contract(),
        actor="chase",
        clock=lambda: NOW,
    )


@pytest.fixture
def tree(tmp_path):
    root = tmp_path / "tree"
    (root / "src").mkdir(parents=True)
    (root / ".git").mkdir()
    (root / ".git" / "HEAD").write_text("ref: refs/heads/main", encoding="utf-8")
    (root / ".env").write_text(
        f"DATABASE_PASSWORD={HIGH_ENTROPY}\nDEBUG=true\n", encoding="utf-8"
    )
    (root / "src" / "config.js").write_text(
        f"const awsKey = '{AWS_KEY}';\nconst token = '{GITHUB_TOKEN}';\n",
        encoding="utf-8",
    )
    (root / "src" / "app.js").write_text("console.log('hi')", encoding="utf-8")
    (root / "src" / "app.js.map").write_text('{"version":3}', encoding="utf-8")
    (root / "database.sql.bak").write_text("-- dump", encoding="utf-8")
    return root


@pytest.fixture
def clean_tree(tmp_path):
    root = tmp_path / "clean"
    (root / "src").mkdir(parents=True)
    (root / ".env.example").write_text(
        "DATABASE_PASSWORD=${DB_PASSWORD}\nAPI_KEY=your-api-key-here\n",
        encoding="utf-8",
    )
    (root / "src" / "app.js").write_text("console.log('hi')", encoding="utf-8")
    return root


class TestHelpers:
    def test_entropy_separates_random_from_repetitive(self):
        assert shannon_entropy("aaaaaaaaaa") < 1.0
        assert shannon_entropy(HIGH_ENTROPY) > 4.0

    def test_entropy_of_empty_is_zero(self):
        assert shannon_entropy("") == 0.0

    def test_fingerprint_is_stable_and_short(self):
        assert fingerprint("abc") == fingerprint("abc")
        assert len(fingerprint("abc")) == 12
        assert fingerprint("abc") != fingerprint("abd")


class TestCleanTree:
    def test_a_clean_tree_produces_nothing(self, gate, clean_tree):
        assert run(gate, clean_tree).signals == []

    def test_env_references_are_not_secrets(self, gate, clean_tree):
        # ${DB_PASSWORD} and your-api-key-here are placeholders, not findings.
        assert run(gate, clean_tree).signals == []


class TestDetection:
    def test_detects_vcs_metadata(self, gate, tree):
        kinds = {s.kind for s in run(gate, tree).signals}
        assert "vcs_metadata_present" in kinds

    def test_detects_known_credential_formats(self, gate, tree):
        signals = [
            s for s in run(gate, tree).signals if s.kind == "credential_format_match"
        ]
        formats = {s.detail["format"] for s in signals}
        assert {"aws_access_key_id", "github_token"} <= formats

    def test_detects_backup_artifacts(self, gate, tree):
        signals = [
            s for s in run(gate, tree).signals if s.kind == "backup_or_dump_present"
        ]
        assert any("database.sql.bak" in s.detail["file"] for s in signals)

    def test_detects_a_source_map_beside_its_bundle(self, gate, tree):
        kinds = {s.kind for s in run(gate, tree).signals}
        assert "source_map_present" in kinds

    def test_detects_a_high_entropy_assignment(self, gate, tree):
        signals = [
            s for s in run(gate, tree).signals if s.kind == "high_entropy_assignment"
        ]
        assert signals
        assert signals[0].detail["entropy"] > 4.0

    def test_detects_a_private_key_block(self, gate, tmp_path):
        root = tmp_path / "keys"
        root.mkdir()
        (root / "id_rsa.txt").write_text(PEM_HEADER + "\n", encoding="utf-8")
        formats = {
            s.detail.get("format")
            for s in run(gate, root).signals
            if s.kind == "credential_format_match"
        }
        assert "private_key_block" in formats


class TestValuesAreNeverRecorded:
    def test_no_signal_contains_the_matched_value(self, gate, tree):
        # The single most important property of this lane. A collector that
        # copies credentials into the evidence trail has created the problem.
        blob = str([s.to_dict() for s in run(gate, tree).signals])
        for secret in (AWS_KEY, GITHUB_TOKEN, HIGH_ENTROPY):
            assert secret not in blob

    def test_shape_is_recorded_instead(self, gate, tree):
        signals = [
            s for s in run(gate, tree).signals if s.kind == "credential_format_match"
        ]
        detail = signals[0].detail
        assert detail["length"] > 0
        assert len(detail["fingerprint"]) == 12

    def test_the_fingerprint_deduplicates_without_exposing(self, gate, tmp_path):
        root = tmp_path / "dup"
        root.mkdir()
        (root / "a.js").write_text(f"k='{AWS_KEY}'; k2='{AWS_KEY}';", encoding="utf-8")
        signals = [
            s for s in run(gate, root).signals if s.kind == "credential_format_match"
        ]
        assert len(signals) == 1  # same value, same file, reported once


class TestHonestFraming:
    def test_titles_say_present_not_exposed(self, gate, tree):
        # A key in a tree is present. Whether it is reachable depends on what
        # the web root serves, which a directory cannot know.
        for signal in run(gate, tree).signals:
            assert "exposed" not in signal.title.lower()
            assert "leaked" not in signal.title.lower()

    def test_every_signal_names_what_remains_unknown(self, gate, tree):
        for signal in run(gate, tree).signals:
            observed_claims = [c for c in signal.claims if not c.is_proven]
            assert observed_claims, f"{signal.kind} makes no statement of uncertainty"

    def test_entropy_signals_admit_they_are_weak(self, gate, tree):
        signal = next(
            s for s in run(gate, tree).signals if s.kind == "high_entropy_assignment"
        )
        text = " ".join(c.text for c in signal.claims)
        assert "weak evidence" in text

    def test_everything_stays_at_contextual(self, gate, tree):
        assert all(s.level is SignalLevel.CONTEXTUAL for s in run(gate, tree).signals)


class TestBoundaries:
    def test_oversized_files_are_skipped(self, gate, tmp_path, monkeypatch):
        import greytheory.signal.lanes.exposure as module

        monkeypatch.setattr(module, "MAX_FILE_BYTES", 10)
        root = tmp_path / "big"
        root.mkdir()
        (root / "big.js").write_text(f"k='{AWS_KEY}'", encoding="utf-8")
        assert not [
            s for s in run(gate, root).signals if s.kind == "credential_format_match"
        ]

    def test_binary_files_are_not_scanned_for_credentials(self, gate, tmp_path):
        root = tmp_path / "bin"
        root.mkdir()
        (root / "image.png").write_bytes(b"\x89PNG\r\n" + AWS_KEY.encode())
        assert not [
            s for s in run(gate, root).signals if s.kind == "credential_format_match"
        ]

    def test_the_lane_cannot_read_outside_its_granted_root(self, gate, tmp_path):
        outside = tmp_path / "outside"
        outside.mkdir()
        (outside / "secret.env").write_text(f"KEY={AWS_KEY}", encoding="utf-8")
        inside = tmp_path / "inside"
        inside.mkdir()

        blob = str([s.to_dict() for s in run(gate, inside).signals])
        assert AWS_KEY not in blob
        assert "secret.env" not in blob
