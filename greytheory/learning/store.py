"""Integrity-checked local storage for evidence-bound mastery assessments."""

# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 ChaseInTech

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any, Iterable, Mapping

from greytheory.audit import AuditLog
from greytheory.learning.catalogue import VulnerabilityCatalogue
from greytheory.learning.domain import LearningError, MasteryAssessment


class LearningStoreError(LearningError):
    """Raised when mastery state is invalid, stale, or unsafe to persist."""


def resolve_learning_root(explicit: Path | None = None) -> Path:
    if explicit is not None:
        return Path(explicit).expanduser().resolve()
    if configured := os.environ.get("GREYTHEORY_LEARNING_ROOT"):
        return Path(configured).expanduser().resolve()
    if local_app_data := os.environ.get("LOCALAPPDATA"):
        return Path(local_app_data) / "GreyTheory" / "learning"
    return Path.home() / ".local" / "share" / "greytheory" / "learning"


def _inside_git_worktree(path: Path) -> bool:
    candidate = path.resolve()
    return any((parent / ".git").exists() for parent in (candidate, *candidate.parents))


def _digest(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


class MasteryStore:
    """Append-only assessment records; the latest human record is current state."""

    def __init__(
        self,
        root: Path | None,
        *,
        catalogue: VulnerabilityCatalogue,
        allow_in_repository: bool = False,
        audit: AuditLog | None = None,
    ) -> None:
        self.root = resolve_learning_root(root)
        if not allow_in_repository and _inside_git_worktree(self.root):
            raise LearningStoreError(
                "mastery state is personal runtime data and is refused inside a git working tree"
            )
        self.catalogue = catalogue
        self.audit = audit
        self.path = self.root / "mastery.json"

    def assessments(self) -> tuple[MasteryAssessment, ...]:
        return tuple(
            MasteryAssessment.from_dict(item)
            for item in self._load_payload().get("assessments", ())
        )

    def record(self, assessment: MasteryAssessment) -> MasteryAssessment:
        self.catalogue.card(assessment.card_id)
        current = list(self.assessments())
        if any(item.id == assessment.id for item in current):
            raise LearningStoreError(f"duplicate mastery assessment {assessment.id!r}")
        current.append(assessment)
        current.sort(key=lambda item: (item.assessed_at, item.id))
        self._write(current)
        if self.audit is not None:
            self.audit.append(
                actor=assessment.assessor,
                action="learning.mastery.record",
                detail={
                    "assessment_id": assessment.id,
                    "card_id": assessment.card_id,
                    "dimension": assessment.dimension.value,
                    "level": assessment.level.name.lower(),
                    "assessor_kind": assessment.assessor_kind.value,
                    "credits_mastery": assessment.credits_mastery,
                    "evidence_refs": list(assessment.evidence_refs),
                    "catalogue_digest": self.catalogue.digest(),
                },
            )
        return assessment

    def verify(self) -> None:
        self._load_payload()
        assessments = self.assessments()
        self.catalogue.graph.mastery_states(assessments, include_non_crediting=True)

    def _load_payload(self) -> dict[str, Any]:
        if not self.path.exists():
            return {
                "schema_version": 1,
                "catalogue_digest": self.catalogue.digest(),
                "assessments": [],
            }
        try:
            wrapper = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise LearningStoreError(f"cannot load mastery state: {exc}") from exc
        if not isinstance(wrapper, dict) or set(wrapper) != {"payload", "digest"}:
            raise LearningStoreError("mastery state has an invalid envelope")
        payload = wrapper["payload"]
        if not isinstance(payload, dict) or _digest(payload) != wrapper["digest"]:
            raise LearningStoreError("mastery state integrity check failed")
        if payload.get("schema_version") != 1:
            raise LearningStoreError("unsupported mastery-state schema")
        if payload.get("catalogue_digest") != self.catalogue.digest():
            raise LearningStoreError(
                "mastery state belongs to a different card catalogue revision"
            )
        if not isinstance(payload.get("assessments"), list):
            raise LearningStoreError("mastery assessments must be a list")
        return payload

    def _write(self, assessments: Iterable[MasteryAssessment]) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema_version": 1,
            "catalogue_digest": self.catalogue.digest(),
            "assessments": [item.to_dict() for item in assessments],
        }
        wrapper = {"payload": payload, "digest": _digest(payload)}
        encoded = json.dumps(wrapper, indent=2, sort_keys=True) + "\n"
        handle, temp_name = tempfile.mkstemp(
            prefix="mastery-", suffix=".tmp", dir=self.root
        )
        temp_path = Path(temp_name)
        try:
            with os.fdopen(handle, "w", encoding="utf-8", newline="\n") as stream:
                stream.write(encoded)
                stream.flush()
                os.fsync(stream.fileno())
            temp_path.replace(self.path)
        except Exception:
            temp_path.unlink(missing_ok=True)
            raise


__all__ = ["LearningStoreError", "MasteryStore", "resolve_learning_root"]
