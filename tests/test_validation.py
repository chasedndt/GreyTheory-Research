"""Validation gates B-F, and the end-to-end path they complete."""

# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 ChaseInTech

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from greytheory.audit import AuditLog
from greytheory.evidence import EvidenceVault
from greytheory.findings import Finding, Taxonomy
from greytheory.provenance import Claim, Tag
from greytheory.report import ReportDraft
from greytheory.validation import (
    Attestation,
    GateId,
    GateKind,
    GateStatus,
    gate_b_reproducibility,
    gate_c_impact,
    gate_d_evidence,
    gate_e_duplicate_risk,
    gate_f_report_quality,
    validate,
)

NOW = datetime(2026, 8, 6, 12, 0, tzinfo=timezone.utc)
AUTHORITY = "fingerprint_abc123"

RAW = b"GET /api/doc/9\nCookie: session=SECRET\n"
REDACTED = b"GET /api/doc/9\nCookie: session=[REDACTED]\n"


@pytest.fixture
def vault(tmp_path):
    return EvidenceVault(tmp_path / "vault", clock=lambda: NOW)


@pytest.fixture
def finding():
    item = Finding(
        id="finding_1",
        title="BOLA in document sharing",
        lane=3,
        target="app.example.test",
        authority_ref=AUTHORITY,
    )
    item.claims.append(
        Claim("account B read account A's document", Tag.CHECKED, "validator", "check_1")
    )
    return item


def stocked(vault, finding, *, redact=True):
    vault.store_raw(
        finding_id=finding.id,
        artifact_id="artifact_1",
        kind="http_request_response",
        data=RAW,
        authority_ref=AUTHORITY,
        extension=".http",
    )
    if redact:
        vault.attach_redacted(
            finding_id=finding.id, artifact_id="artifact_1", data=REDACTED
        )
    return vault


def good_draft(**overrides) -> ReportDraft:
    base = dict(
        finding_id="finding_1",
        authority_ref=AUTHORITY,
        title="BOLA in document sharing allows cross-tenant document read",
        programme="Mock Programme",
        asset="app.example.test",
        summary="A standard user can read another tenant's document by changing "
        "the object identifier on the read endpoint.",
        affected_feature="Team document sharing",
        preconditions=["Two accounts in separate tenants"],
        steps=[
            "As account A, create a synthetic document and note its identifier.",
            "As account B, issue the read request with account A's identifier.",
            "Observe the document body in the response.",
        ],
        expected_result="The server should deny the read; B does not own the object.",
        actual_result="The server returns the document body with HTTP 200.",
        security_impact="Cross-tenant confidentiality breach on any document whose "
        "identifier is known or guessable.",
        evidence_index=["artifact_1"],
        data_minimisation_statement="All testing used researcher-controlled accounts "
        "and synthetic documents.",
        severity_proposed="High",
        severity_framework="CVSS 3.1",
        severity_rationale="Cross-tenant read of arbitrary documents with no user "
        "interaction, limited by identifier discoverability.",
        remediation="Enforce object-level authorisation server-side on the read path.",
        unresolved_uncertainty=["Whether identifiers are enumerable at scale"],
    )
    base.update(overrides)
    return ReportDraft(**base)


def attest(gate: GateId, statement: str) -> Attestation:
    return Attestation(
        gate=gate, actor="chase", statement=statement, attested_at=NOW
    )


REPRO = attest(
    GateId.B_REPRODUCIBILITY,
    "Reproduced twice from a clean browser session with no prior cookies.",
)
IMPACT = attest(
    GateId.C_IMPACT,
    "Confidentiality of another tenant's documents is exposed to any authenticated user.",
)
DUPES = attest(
    GateId.E_DUPLICATE_RISK,
    "Reviewed the programme's public disclosures and recent changelog entries; "
    "residual duplicate risk remains moderate.",
)
ALL_ATTESTATIONS = [REPRO, IMPACT, DUPES]


class TestAttestation:
    def test_must_name_who_made_it(self):
        with pytest.raises(ValueError, match="who made it"):
            Attestation(GateId.C_IMPACT, "", "a" * 40, NOW)

    def test_must_actually_say_something(self):
        # A checkbox is not an attestation.
        with pytest.raises(ValueError, match="checkbox"):
            Attestation(GateId.C_IMPACT, "chase", "done", NOW)


class TestGateB:
    def test_no_attestation_is_not_assessed_rather_than_failed(self, finding):
        result = gate_b_reproducibility(finding, [])
        assert result.status is GateStatus.NOT_ASSESSED
        assert result.kind is GateKind.ATTESTED

    def test_passes_with_attestation_and_a_checked_claim(self, finding):
        assert gate_b_reproducibility(finding, [REPRO]).passed

    def test_fails_when_nothing_was_deterministically_verified(self, finding):
        finding.claims = [Claim("looked broken", Tag.INFERRED, "model")]
        result = gate_b_reproducibility(finding, [REPRO])
        assert result.status is GateStatus.FAIL
        assert "checked" in " ".join(result.reasons)

    def test_warns_when_a_clean_session_is_not_mentioned(self, finding):
        vague = attest(
            GateId.B_REPRODUCIBILITY, "I ran it again and it happened once more."
        )
        result = gate_b_reproducibility(finding, [vague])
        assert result.passed
        assert "clean session" in " ".join(result.warnings)


class TestGateC:
    def test_no_attestation_is_not_assessed(self, finding):
        assert gate_c_impact(finding, []).status is GateStatus.NOT_ASSESSED

    def test_passes_with_attestation_and_proof(self, finding):
        assert gate_c_impact(finding, [IMPACT]).passed

    def test_fails_when_impact_rests_on_inference_alone(self, finding):
        finding.claims = [Claim("probably exploitable", Tag.INFERRED, "model")]
        result = gate_c_impact(finding, [IMPACT])
        assert result.status is GateStatus.FAIL

    def test_warns_when_no_security_property_is_named(self, finding):
        vague = attest(GateId.C_IMPACT, "This is quite bad for the business overall.")
        result = gate_c_impact(finding, [vague])
        assert result.passed
        assert "security property" in " ".join(result.warnings)


class TestGateD:
    def test_passes_on_complete_verified_redacted_evidence(self, vault, finding):
        stocked(vault, finding)
        result = gate_d_evidence(finding, vault)
        assert result.passed
        assert result.kind is GateKind.DETERMINISTIC

    def test_fails_with_no_evidence(self, vault, finding):
        result = gate_d_evidence(finding, vault)
        assert result.status is GateStatus.FAIL
        assert "no evidence held" in " ".join(result.reasons)

    def test_fails_when_evidence_is_unredacted(self, vault, finding):
        stocked(vault, finding, redact=False)
        result = gate_d_evidence(finding, vault)
        assert "no redacted counterpart" in " ".join(result.reasons)

    def test_rehashes_from_disk_rather_than_trusting_the_manifest(self, vault, finding):
        stocked(vault, finding)
        (vault.raw_dir / "finding_1" / "artifact_1.http").write_bytes(b"tampered")
        result = gate_d_evidence(finding, vault)
        assert result.status is GateStatus.FAIL
        assert "has been modified" in " ".join(result.reasons)

    def test_warns_when_evidence_came_from_a_different_contract(self, vault, finding):
        vault.store_raw(
            finding_id=finding.id,
            artifact_id="artifact_1",
            kind="note",
            data=RAW,
            authority_ref="a_different_contract_fingerprint",
            extension=".http",
        )
        vault.attach_redacted(
            finding_id=finding.id, artifact_id="artifact_1", data=REDACTED
        )
        result = gate_d_evidence(finding, vault)
        assert result.passed
        assert "different contract" in " ".join(result.warnings)

    def test_warns_when_a_redacted_copy_is_still_marked_sensitive(self, vault, finding):
        vault.store_raw(
            finding_id=finding.id,
            artifact_id="artifact_1",
            kind="note",
            data=RAW,
            authority_ref=AUTHORITY,
        )
        vault.attach_redacted(
            finding_id=finding.id,
            artifact_id="artifact_1",
            data=REDACTED,
            contains_sensitive_data=True,
        )
        assert "still marked as containing" in " ".join(
            gate_d_evidence(finding, vault).warnings
        )


class TestGateE:
    def test_no_attestation_is_not_assessed(self):
        assert gate_e_duplicate_risk([]).status is GateStatus.NOT_ASSESSED

    def test_passes_on_an_honest_statement(self):
        assert gate_e_duplicate_risk([DUPES]).passed

    @pytest.mark.parametrize(
        "claim",
        [
            "I checked the disclosures, this is definitely unique.",
            "Reviewed changelogs; there is no chance of duplicate here.",
            "Searched write-ups. Duplicate risk eliminated entirely.",
        ],
    )
    def test_rejects_claims_of_certainty(self, claim):
        # Duplicate risk can be reduced and estimated. Never eliminated.
        result = gate_e_duplicate_risk([attest(GateId.E_DUPLICATE_RISK, claim)])
        assert result.status is GateStatus.FAIL
        assert "certainty that does not exist" in " ".join(result.reasons)

    def test_warns_when_sources_are_not_named(self):
        vague = attest(
            GateId.E_DUPLICATE_RISK, "I had a good look around for a while beforehand."
        )
        result = gate_e_duplicate_risk([vague])
        assert result.passed
        assert "what was reviewed" in " ".join(result.warnings)


class TestGateF:
    def test_passes_on_a_complete_draft(self):
        assert gate_f_report_quality(good_draft()).passed

    def test_fails_on_missing_sections(self):
        result = gate_f_report_quality(good_draft(security_impact="", remediation=""))
        assert result.status is GateStatus.FAIL
        assert "security_impact" in " ".join(result.reasons)

    def test_fails_on_unfinished_placeholders(self):
        result = gate_f_report_quality(good_draft(remediation="TODO: work this out"))
        assert "unfinished placeholder" in " ".join(result.reasons)

    def test_fails_on_a_single_step_repro(self):
        result = gate_f_report_quality(good_draft(steps=["Send the request."]))
        assert "fewer than two" in " ".join(result.reasons)

    def test_fails_when_severity_has_no_rationale(self):
        result = gate_f_report_quality(good_draft(severity_rationale="  "))
        assert "number someone hoped for" in " ".join(result.reasons)

    def test_fails_without_an_authority_reference(self):
        result = gate_f_report_quality(good_draft(authority_ref=""))
        assert "authority reference" in " ".join(result.reasons)

    def test_warns_on_unqualified_absolutes(self):
        result = gate_f_report_quality(
            good_draft(security_impact="Any attacker can instantly read all users' data.")
        )
        assert result.passed
        assert "absolute claim" in " ".join(result.warnings)

    def test_warns_when_no_uncertainty_is_recorded(self):
        result = gate_f_report_quality(good_draft(unresolved_uncertainty=[]))
        assert result.passed
        assert "uncertainty" in " ".join(result.warnings)


class TestValidate:
    def test_a_complete_finding_is_submission_ready(self, vault, finding):
        stocked(vault, finding)
        report = validate(
            finding,
            vault=vault,
            draft=good_draft(),
            attestations=ALL_ATTESTATIONS,
            now=NOW,
        )
        assert report.submission_ready
        assert report.blocking == []

    def test_one_missing_attestation_blocks_everything(self, vault, finding):
        stocked(vault, finding)
        report = validate(
            finding, vault=vault, draft=good_draft(), attestations=[REPRO, IMPACT]
        )
        assert not report.submission_ready
        assert [r.gate for r in report.blocking] == [GateId.E_DUPLICATE_RISK]

    def test_no_attestations_at_all_leaves_three_gates_unassessed(self, vault, finding):
        stocked(vault, finding)
        report = validate(finding, vault=vault, draft=good_draft())
        unassessed = [
            r.gate for r in report.results if r.status is GateStatus.NOT_ASSESSED
        ]
        assert unassessed == [
            GateId.B_REPRODUCIBILITY,
            GateId.C_IMPACT,
            GateId.E_DUPLICATE_RISK,
        ]
        assert not report.submission_ready

    def test_the_run_is_audited(self, tmp_path, vault, finding):
        audit = AuditLog(tmp_path / "audit.jsonl")
        stocked(vault, finding)
        validate(
            finding,
            vault=vault,
            draft=good_draft(),
            attestations=ALL_ATTESTATIONS,
            audit=audit,
        )
        record = audit.records()[-1]
        assert record.action == "validation.run"
        assert record.authority_ref == AUTHORITY
        assert record.detail["submission_ready"] is True
        audit.verify()

    def test_validation_does_not_advance_the_finding(self, vault, finding):
        # Passing the gates makes a finding *eligible* for Gate G. It does not
        # move it, and it certainly does not submit it.
        stocked(vault, finding)
        validate(
            finding, vault=vault, draft=good_draft(), attestations=ALL_ATTESTATIONS
        )
        assert finding.state is Taxonomy.INFORMATIONAL


class TestReportRendering:
    def test_renders_every_required_heading(self):
        rendered = good_draft().render()
        for heading in (
            "## Programme and asset",
            "## Summary",
            "## Steps to reproduce",
            "## Expected result",
            "## Actual result",
            "## Security impact",
            "## Evidence",
            "## Data-minimisation statement",
            "## Severity assessment",
            "## Suggested remediation",
            "## Remaining uncertainty",
        ):
            assert heading in rendered

    def test_numbers_the_steps(self):
        rendered = good_draft().render()
        assert "1. As account A" in rendered
        assert "3. Observe" in rendered

    def test_cites_the_authority_reference(self):
        assert AUTHORITY in good_draft().render()

    def test_round_trips_through_dict(self):
        draft = good_draft()
        assert ReportDraft.from_dict(draft.to_dict()).render() == draft.render()
