"""Private persisted report cases and optimistic draft revisions."""

from __future__ import annotations

import json
from datetime import datetime, timezone

import pytest

from greytheory.audit import AuditLog
from greytheory.findings import Finding
from greytheory.report import ReportDraft
from greytheory.report_store import (
    ReportRevisionConflict,
    ReportStore,
    ReportStoreError,
)
from greytheory.validation import (
    Attestation,
    GateId,
    GateKind,
    GateResult,
    GateStatus,
    ValidationReport,
)


NOW = datetime(2026, 8, 25, 1, 0, tzinfo=timezone.utc)
AUTHORITY = "a" * 64


def finding() -> Finding:
    return Finding(
        id="finding-report-store",
        title="Local fixture report case",
        lane=4,
        target="fixture://report-store",
        authority_ref=AUTHORITY,
    )


def draft(*, summary: str = "") -> ReportDraft:
    return ReportDraft(
        finding_id="finding-report-store",
        authority_ref=AUTHORITY,
        title="Local fixture report case",
        summary=summary,
    )


def test_report_store_is_private_atomic_reopenable_and_revision_safe(tmp_path):
    audit = AuditLog(tmp_path / "audit" / "audit.jsonl", clock=lambda: NOW)
    root = tmp_path / "reports"
    store = ReportStore(root, audit=audit, clock=lambda: NOW)

    created = store.create(finding(), draft(), actor="operator-local")
    reopened = ReportStore(root, audit=audit, clock=lambda: NOW)
    saved = reopened.save_draft(
        draft(summary="A bounded operator-authored draft."),
        expected_revision=0,
        actor="operator-local",
    )

    assert created.revision == 0
    assert saved.revision == 1
    assert reopened.get(created.id).draft.summary == (
        "A bounded operator-authored draft."
    )
    reopened.verify()
    assert [record.action for record in audit.records()][-2:] == [
        "report.case.create",
        "report.draft.save",
    ]
    with pytest.raises(ReportRevisionConflict, match="expected 0, current 1"):
        reopened.save_draft(
            draft(summary="stale overwrite"),
            expected_revision=0,
            actor="operator-local",
        )


def test_report_store_detects_tampering_and_refuses_repository_storage(tmp_path):
    store = ReportStore(tmp_path / "reports", clock=lambda: NOW)
    store.create(finding(), draft(), actor="operator-local")
    envelope = json.loads(store.path.read_text(encoding="utf-8"))
    envelope["payload"]["cases"][0]["draft"]["title"] = "tampered"
    store.path.write_text(json.dumps(envelope), encoding="utf-8")

    with pytest.raises(ReportStoreError, match="integrity check failed"):
        store.verify()

    repository = tmp_path / "repository"
    (repository / ".git").mkdir(parents=True)
    with pytest.raises(ReportStoreError, match="Git worktree"):
        ReportStore(repository / "private-reports")


def test_report_case_refuses_mismatched_finding_and_authority(tmp_path):
    store = ReportStore(tmp_path / "reports", clock=lambda: NOW)
    with pytest.raises(ReportStoreError, match="different finding"):
        store.create(
            finding(),
            ReportDraft(finding_id="another-finding", authority_ref=AUTHORITY),
            actor="operator-local",
        )
    with pytest.raises(ReportStoreError, match="authority"):
        store.create(
            finding(),
            ReportDraft(
                finding_id="finding-report-store", authority_ref="b" * 64
            ),
            actor="operator-local",
        )


def test_report_validation_is_complete_revisioned_and_reopenable(tmp_path):
    store = ReportStore(tmp_path / "reports", clock=lambda: NOW)
    store.create(finding(), draft(), actor="operator-local")
    attestations = tuple(
        Attestation(
            gate,
            "operator-local",
            "The operator completed this bounded check against stored evidence.",
            NOW,
            ["evidence-1"],
        )
        for gate in (
            GateId.B_REPRODUCIBILITY,
            GateId.C_IMPACT,
            GateId.E_DUPLICATE_RISK,
        )
    )
    report = ValidationReport(
        finding_id="finding-report-store",
        results=[
            GateResult(
                gate,
                GateStatus.PASS,
                GateKind.ATTESTED
                if gate in {
                    GateId.B_REPRODUCIBILITY,
                    GateId.C_IMPACT,
                    GateId.E_DUPLICATE_RISK,
                }
                else GateKind.DETERMINISTIC,
            )
            for gate in GateId
        ],
        checked_at=NOW,
    )

    saved = store.record_validation(
        "finding-report-store",
        attestations=attestations,
        report=report,
        expected_revision=0,
        actor="operator-local",
    )
    reopened = ReportStore(tmp_path / "reports", clock=lambda: NOW).get(
        "finding-report-store"
    )

    assert saved.revision == 1
    assert reopened.current_validation is not None
    assert reopened.current_validation.attestations == attestations
    assert reopened.current_validation.report == report
    assert len(reopened.validations) == 1
    with pytest.raises(ReportRevisionConflict, match="expected 0, current 1"):
        store.record_validation(
            "finding-report-store",
            attestations=attestations,
            report=report,
            expected_revision=0,
            actor="operator-local",
        )
    with pytest.raises(ReportStoreError, match="one attestation for each"):
        store.record_validation(
            "finding-report-store",
            attestations=attestations[:-1],
            report=report,
            expected_revision=1,
            actor="operator-local",
        )
    edited = store.save_draft(
        draft(summary="An edit invalidates the current validation."),
        expected_revision=1,
        actor="operator-local",
    )
    assert edited.current_validation is None
    assert len(edited.validations) == 1
