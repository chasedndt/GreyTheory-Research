"""Private, atomic report export for the local GreyTheory workbench."""

# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 ChaseInTech

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import tempfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping

from greytheory.audit import AuditLog
from greytheory.evidence import find_repository_root
from greytheory.findings import Finding
from greytheory.report import ReportDraft


SAFE_ID = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_.:-]{0,191}$")


class ReportExportError(ValueError):
    """Raised when a report export would be unsafe or incomplete."""


class ReportExportConflict(ReportExportError):
    """Raised when an immutable export identifier already exists."""


@dataclass(frozen=True)
class ReportExportReceipt:
    export_id: str
    finding_id: str
    path: Path
    manifest_sha256: str
    artifact_count: int


def _encoded(data: Mapping[str, Any]) -> bytes:
    return (json.dumps(data, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class ReportExportWriter:
    """Write one immutable, redacted-only report package outside Git."""

    def __init__(self, root: Path, *, audit: AuditLog | None = None) -> None:
        self.root = Path(root).expanduser().resolve()
        repository = find_repository_root(self.root)
        if repository is not None:
            raise ReportExportError(
                f"report exports are refused inside the Git worktree at {repository}"
            )
        self.audit = audit

    def export(
        self,
        *,
        export_id: str,
        finding: Finding,
        draft: ReportDraft,
        evidence_package: Mapping[str, Any],
        operator_ref: str,
        exported_at: datetime,
    ) -> ReportExportReceipt:
        if not SAFE_ID.fullmatch(export_id):
            raise ReportExportError("report export id is not a safe identifier")
        if evidence_package.get("finding_id") != draft.finding_id:
            raise ReportExportError("evidence package belongs to a different finding")
        if finding.id != draft.finding_id:
            raise ReportExportError("finding and report draft identifiers do not match")
        if finding.authority_ref != draft.authority_ref:
            raise ReportExportError("finding and report draft authority do not match")
        artifacts = evidence_package.get("artifacts")
        if not isinstance(artifacts, list) or not artifacts:
            raise ReportExportError("report export requires verified redacted evidence")

        self.root.mkdir(parents=True, exist_ok=True)
        destination = self.root / export_id
        if destination.exists():
            raise ReportExportConflict(f"report export {export_id!r} already exists")
        temporary = Path(tempfile.mkdtemp(prefix="report-export-", dir=self.root))
        try:
            evidence_dir = temporary / "evidence"
            evidence_dir.mkdir()
            exported_artifacts: list[dict[str, Any]] = []
            for entry in artifacts:
                if not isinstance(entry, Mapping):
                    raise ReportExportError("evidence export entry is invalid")
                artifact_id = str(entry.get("id", ""))
                if not SAFE_ID.fullmatch(artifact_id):
                    raise ReportExportError("evidence artifact id is unsafe")
                source = Path(str(entry.get("path", ""))).resolve()
                expected = str(entry.get("sha256", ""))
                data = source.read_bytes()
                if not expected or _sha256(data) != expected:
                    raise ReportExportError(
                        f"redacted artifact {artifact_id!r} changed during export"
                    )
                suffix = source.suffix.lower()
                if not re.fullmatch(r"\.[a-z0-9]{1,16}", suffix):
                    suffix = ".bin"
                relative = Path("evidence") / f"{artifact_id}{suffix}"
                output = temporary / relative
                output.write_bytes(data)
                exported_artifacts.append(
                    {
                        "id": artifact_id,
                        "kind": str(entry.get("kind", "")),
                        "authority_ref": str(entry.get("authority_ref", "")),
                        "path": relative.as_posix(),
                        "sha256": expected,
                        "bytes": len(data),
                    }
                )

            report_markdown = draft.render().encode("utf-8")
            report_json = _encoded(draft.to_dict())
            finding_json = _encoded(finding.to_dict())
            (temporary / "report.md").write_bytes(report_markdown)
            (temporary / "report.json").write_bytes(report_json)
            (temporary / "finding.json").write_bytes(finding_json)
            manifest = {
                "schema_version": 1,
                "export_id": export_id,
                "finding_id": draft.finding_id,
                "authority_ref": draft.authority_ref,
                "exported_at": exported_at.isoformat(),
                "operator_ref": operator_ref,
                "submission_performed": False,
                "report": {
                    "markdown_path": "report.md",
                    "markdown_sha256": _sha256(report_markdown),
                    "json_path": "report.json",
                    "json_sha256": _sha256(report_json),
                },
                "finding": {
                    "json_path": "finding.json",
                    "json_sha256": _sha256(finding_json),
                },
                "artifacts": exported_artifacts,
            }
            manifest_bytes = _encoded(manifest)
            (temporary / "manifest.json").write_bytes(manifest_bytes)
            os.replace(temporary, destination)
        except Exception:
            shutil.rmtree(temporary, ignore_errors=True)
            raise

        receipt = ReportExportReceipt(
            export_id=export_id,
            finding_id=draft.finding_id,
            path=destination,
            manifest_sha256=_sha256(manifest_bytes),
            artifact_count=len(exported_artifacts),
        )
        if self.audit is not None:
            self.audit.append(
                actor=operator_ref,
                action="report.export",
                authority_ref=draft.authority_ref,
                detail={
                    "export_id": export_id,
                    "finding_id": draft.finding_id,
                    "manifest_sha256": receipt.manifest_sha256,
                    "artifact_count": receipt.artifact_count,
                    "submission_performed": False,
                },
            )
        return receipt


__all__ = [
    "ReportExportConflict",
    "ReportExportError",
    "ReportExportReceipt",
    "ReportExportWriter",
]
