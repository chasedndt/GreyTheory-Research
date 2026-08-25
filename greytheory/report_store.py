"""Integrity-checked private persistence for findings and report drafts."""

# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 ChaseInTech

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping

from greytheory.audit import AuditLog
from greytheory.evidence import find_repository_root
from greytheory.findings import Finding
from greytheory.report import ReportDraft
from greytheory.validation import Attestation, GateId, ValidationReport


SCHEMA_VERSION = 1


class ReportStoreError(ValueError):
    """Raised when private report state is unsafe, corrupt, or stale."""


class ReportRevisionConflict(ReportStoreError):
    """Raised when an edit targets an obsolete report-case revision."""


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _canonical(data: Mapping[str, Any]) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _digest(data: Mapping[str, Any]) -> str:
    return hashlib.sha256(_canonical(data).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class ReportValidation:
    """One immutable validation run bound to the case revision it checked."""

    base_revision: int
    attestations: tuple[Attestation, ...]
    report: ValidationReport

    def __post_init__(self) -> None:
        if isinstance(self.base_revision, bool) or self.base_revision < 0:
            raise ReportStoreError("validation base revision must be non-negative")
        gates = [item.gate for item in self.attestations]
        if len(gates) != len(set(gates)):
            raise ReportStoreError("validation attestations contain duplicate gates")
        if set(gates) != {
            GateId.B_REPRODUCIBILITY,
            GateId.C_IMPACT,
            GateId.E_DUPLICATE_RISK,
        }:
            raise ReportStoreError(
                "validation requires one attestation for each of Gates B, C, and E"
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "base_revision": self.base_revision,
            "attestations": [item.to_dict() for item in self.attestations],
            "report": self.report.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> ReportValidation:
        return cls(
            base_revision=int(data["base_revision"]),
            attestations=tuple(
                Attestation.from_dict(dict(item))
                for item in data.get("attestations", [])
            ),
            report=ValidationReport.from_dict(dict(data["report"])),
        )


@dataclass(frozen=True)
class ReportCase:
    """One finding and its operator-authored draft at one private revision."""

    finding: Finding
    draft: ReportDraft
    revision: int
    updated_at: datetime
    validations: tuple[ReportValidation, ...] = ()

    def __post_init__(self) -> None:
        if self.finding.id != self.draft.finding_id:
            raise ReportStoreError("report draft belongs to a different finding")
        if self.finding.authority_ref != self.draft.authority_ref:
            raise ReportStoreError("report draft authority does not match its finding")
        if isinstance(self.revision, bool) or self.revision < 0:
            raise ReportStoreError("report case revision must be non-negative")
        if self.updated_at.tzinfo is None:
            raise ReportStoreError("report case update time must be timezone-aware")
        if any(
            item.report.finding_id != self.finding.id for item in self.validations
        ):
            raise ReportStoreError("validation history belongs to another finding")
        base_revisions = [item.base_revision for item in self.validations]
        if base_revisions != sorted(set(base_revisions)):
            raise ReportStoreError("validation history revisions must increase")
        if any(base_revision >= self.revision for base_revision in base_revisions):
            raise ReportStoreError("validation history references an invalid revision")

    @property
    def id(self) -> str:
        return self.finding.id

    @property
    def current_validation(self) -> ReportValidation | None:
        """Return the latest run only when no later case edit invalidated it."""
        if not self.validations:
            return None
        latest = self.validations[-1]
        return latest if latest.base_revision + 1 == self.revision else None

    def to_dict(self) -> dict[str, Any]:
        return {
            "finding": self.finding.to_dict(),
            "draft": self.draft.to_dict(),
            "revision": self.revision,
            "updated_at": self.updated_at.isoformat(),
            "validations": [item.to_dict() for item in self.validations],
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> ReportCase:
        return cls(
            finding=Finding.from_dict(dict(data["finding"])),
            draft=ReportDraft.from_dict(dict(data["draft"])),
            revision=int(data["revision"]),
            updated_at=datetime.fromisoformat(str(data["updated_at"])),
            validations=tuple(
                ReportValidation.from_dict(dict(item))
                for item in data.get("validations", [])
            ),
        )


class ReportStore:
    """Atomic private report cases with optimistic draft revisions."""

    def __init__(
        self,
        root: str | os.PathLike[str],
        *,
        allow_in_repository: bool = False,
        audit: AuditLog | None = None,
        clock: Callable[[], datetime] = _utcnow,
    ) -> None:
        self.root = Path(root).expanduser().resolve()
        if not allow_in_repository and find_repository_root(self.root) is not None:
            raise ReportStoreError("report state is refused inside a Git worktree")
        self.path = self.root / "cases.json"
        self.audit = audit
        self.clock = clock

    def cases(self) -> tuple[ReportCase, ...]:
        cases = tuple(
            ReportCase.from_dict(item)
            for item in self._load_payload().get("cases", [])
        )
        ids = [case.id for case in cases]
        if len(ids) != len(set(ids)):
            raise ReportStoreError("report state contains duplicate case identifiers")
        return cases

    def get(self, finding_id: str) -> ReportCase:
        for case in self.cases():
            if case.id == finding_id:
                return case
        raise ReportStoreError(f"unknown report case {finding_id!r}")

    def create(
        self, finding: Finding, draft: ReportDraft, *, actor: str
    ) -> ReportCase:
        current = {case.id: case for case in self.cases()}
        if finding.id in current:
            raise ReportStoreError(f"report case {finding.id!r} already exists")
        case = ReportCase(finding, draft, 0, self.clock())
        current[case.id] = case
        self._write(current)
        self._audit("report.case.create", case, actor)
        return case

    def save_draft(
        self,
        draft: ReportDraft,
        *,
        expected_revision: int,
        actor: str,
    ) -> ReportCase:
        current = {case.id: case for case in self.cases()}
        try:
            existing = current[draft.finding_id]
        except KeyError as exc:
            raise ReportStoreError(
                f"unknown report case {draft.finding_id!r}"
            ) from exc
        if existing.revision != expected_revision:
            raise ReportRevisionConflict(
                f"report revision conflict: expected {expected_revision}, "
                f"current {existing.revision}"
            )
        updated = ReportCase(
            existing.finding,
            draft,
            existing.revision + 1,
            self.clock(),
            existing.validations,
        )
        current[updated.id] = updated
        self._write(current)
        self._audit("report.draft.save", updated, actor)
        return updated

    def save_finding(
        self,
        finding: Finding,
        *,
        expected_revision: int,
        actor: str,
    ) -> ReportCase:
        existing = self.get(finding.id)
        if existing.revision != expected_revision:
            raise ReportRevisionConflict(
                f"report revision conflict: expected {expected_revision}, "
                f"current {existing.revision}"
            )
        current = {case.id: case for case in self.cases()}
        updated = ReportCase(
            finding,
            existing.draft,
            existing.revision + 1,
            self.clock(),
            existing.validations,
        )
        current[updated.id] = updated
        self._write(current)
        self._audit("report.finding.save", updated, actor)
        return updated

    def record_validation(
        self,
        finding_id: str,
        *,
        attestations: tuple[Attestation, ...],
        report: ValidationReport,
        expected_revision: int,
        actor: str,
    ) -> ReportCase:
        existing = self.get(finding_id)
        if existing.revision != expected_revision:
            raise ReportRevisionConflict(
                f"report revision conflict: expected {expected_revision}, "
                f"current {existing.revision}"
            )
        if report.finding_id != finding_id:
            raise ReportStoreError("validation report belongs to another finding")
        validation = ReportValidation(expected_revision, attestations, report)
        current = {case.id: case for case in self.cases()}
        updated = ReportCase(
            existing.finding,
            existing.draft,
            existing.revision + 1,
            self.clock(),
            (*existing.validations, validation),
        )
        current[updated.id] = updated
        self._write(current)
        self._audit("report.validation.record", updated, actor)
        return updated

    def verify(self) -> None:
        self._load_payload()
        self.cases()

    def _load_payload(self) -> dict[str, Any]:
        if not self.path.exists():
            return {"schema_version": SCHEMA_VERSION, "cases": []}
        try:
            envelope = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ReportStoreError(f"cannot load report state: {exc}") from exc
        if not isinstance(envelope, dict) or set(envelope) != {"payload", "digest"}:
            raise ReportStoreError("report state has an invalid envelope")
        payload = envelope["payload"]
        if not isinstance(payload, dict) or _digest(payload) != envelope["digest"]:
            raise ReportStoreError("report state integrity check failed")
        if payload.get("schema_version") != SCHEMA_VERSION:
            raise ReportStoreError("unsupported report-state schema")
        if set(payload) != {"schema_version", "cases"}:
            raise ReportStoreError("report state payload has unexpected fields")
        if not isinstance(payload.get("cases"), list):
            raise ReportStoreError("report cases must be a list")
        return payload

    def _write(self, cases: Mapping[str, ReportCase]) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema_version": SCHEMA_VERSION,
            "cases": [cases[key].to_dict() for key in sorted(cases)],
        }
        envelope = {"payload": payload, "digest": _digest(payload)}
        encoded = json.dumps(envelope, indent=2, sort_keys=True) + "\n"
        handle, name = tempfile.mkstemp(
            prefix="report-cases-", suffix=".tmp", dir=self.root
        )
        temporary = Path(name)
        try:
            with os.fdopen(handle, "w", encoding="utf-8", newline="\n") as stream:
                stream.write(encoded)
                stream.flush()
                os.fsync(stream.fileno())
            temporary.replace(self.path)
        except Exception:
            temporary.unlink(missing_ok=True)
            raise

    def _audit(self, action: str, case: ReportCase, actor: str) -> None:
        if self.audit is not None:
            self.audit.append(
                actor=actor,
                action=action,
                authority_ref=case.finding.authority_ref,
                detail={
                    "finding_id": case.id,
                    "revision": case.revision,
                    "finding_state": case.finding.state.value,
                },
            )


__all__ = [
    "ReportCase",
    "ReportRevisionConflict",
    "ReportStore",
    "ReportStoreError",
]
