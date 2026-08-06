"""The evidence vault — raw stays private, redacted is what travels.

Resolves open question O3: where evidence lives.

Raw evidence is the most dangerous data this system touches. It can contain
session tokens, third-party personal data, internal identifiers and secrets,
and it is produced at exactly the moment attention is on something else. So the
vault is built around one rule that cannot be waived by being busy:

**Raw evidence never enters a repository working tree.** The vault refuses to
initialise inside one unless explicitly forced, because a `.gitignore` entry is
a convention and this needs to be a wall.

Two artifacts exist for every piece of evidence: the raw capture, written once
and never modified, and a redacted counterpart produced deliberately. Only the
redacted copy can be exported. A finding whose evidence has no redacted
counterpart cannot produce an export package at all.

Root resolution, in order:

1. an explicit ``root`` argument;
2. ``GREYTHEORY_EVIDENCE_ROOT``;
3. ``CHASEOS_VAULT_ROOT`` → ``<vault>/07_LOGS/greytheory-evidence`` (integration);
4. the platform user-data directory — ``%LOCALAPPDATA%/GreyTheory/evidence`` on
   Windows, ``$XDG_DATA_HOME/greytheory/evidence`` or
   ``~/.local/share/greytheory/evidence`` elsewhere.

Step 4 is the standalone default and is deliberately outside any project
directory. Step 3 exists so a ChaseOS operator gets one vault rather than two,
but GreyTheory does not require it.
"""

# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 ChaseInTech

from __future__ import annotations

import hashlib
import json
import os
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from greytheory.audit import AuditLog

SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
"""Ids become path segments, so they are validated rather than trusted."""


class EvidenceError(Exception):
    """Raised when an evidence operation would be unsafe or unsound."""


class VaultLocationError(EvidenceError):
    """Raised when the resolved vault root is not a safe place for raw evidence."""


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _validate_id(value: str, *, label: str) -> str:
    text = str(value or "").strip()
    if not SAFE_ID.fullmatch(text):
        raise EvidenceError(
            f"{label} {value!r} is not a safe identifier; expected "
            "alphanumerics, dot, dash or underscore"
        )
    return text


def _platform_data_dir() -> Path:
    if os.name == "nt":
        base = os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA")
        if base:
            return Path(base) / "GreyTheory" / "evidence"
        return Path.home() / "AppData" / "Local" / "GreyTheory" / "evidence"
    xdg = os.environ.get("XDG_DATA_HOME")
    base = Path(xdg) if xdg else Path.home() / ".local" / "share"
    return base / "greytheory" / "evidence"


def resolve_root(explicit: str | os.PathLike[str] | None = None) -> Path:
    """Resolve the evidence root without creating anything."""
    if explicit is not None:
        return Path(explicit).expanduser()

    override = os.environ.get("GREYTHEORY_EVIDENCE_ROOT")
    if override:
        return Path(override).expanduser()

    chaseos_vault = os.environ.get("CHASEOS_VAULT_ROOT")
    if chaseos_vault:
        return Path(chaseos_vault).expanduser() / "07_LOGS" / "greytheory-evidence"

    return _platform_data_dir()


def find_repository_root(path: Path) -> Path | None:
    """Return the nearest ancestor containing a ``.git`` entry, if any."""
    candidate = path if path.is_dir() else path.parent
    for directory in [candidate, *candidate.parents]:
        if (directory / ".git").exists():
            return directory
    return None


@dataclass(frozen=True)
class EvidenceArtifact:
    """One captured artifact, with the hashes that prove it has not changed."""

    id: str
    finding_id: str
    kind: str
    """e.g. ``http_request_response``, ``screenshot``, ``note``."""

    created_at: datetime
    authority_ref: str
    """Invariant I2. Evidence produced under no authority does not enter."""

    raw_sha256: str
    raw_bytes: int
    extension: str = ".bin"
    redacted_sha256: str | None = None
    redacted_bytes: int | None = None
    contains_sensitive_data: bool = True
    """Assumed true until a redacted counterpart says otherwise."""

    source_account: str = ""
    notes: str = ""

    @property
    def is_redacted(self) -> bool:
        return self.redacted_sha256 is not None

    @property
    def is_exportable(self) -> bool:
        """Only a redacted artifact may leave the vault."""
        return self.is_redacted

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "finding_id": self.finding_id,
            "kind": self.kind,
            "created_at": self.created_at.isoformat(),
            "authority_ref": self.authority_ref,
            "raw_sha256": self.raw_sha256,
            "raw_bytes": self.raw_bytes,
            "extension": self.extension,
            "redacted_sha256": self.redacted_sha256,
            "redacted_bytes": self.redacted_bytes,
            "contains_sensitive_data": self.contains_sensitive_data,
            "source_account": self.source_account,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> EvidenceArtifact:
        created_at = datetime.fromisoformat(data["created_at"])
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)
        return cls(
            id=data["id"],
            finding_id=data["finding_id"],
            kind=data["kind"],
            created_at=created_at,
            authority_ref=data["authority_ref"],
            raw_sha256=data["raw_sha256"],
            raw_bytes=data["raw_bytes"],
            extension=data.get("extension", ".bin"),
            redacted_sha256=data.get("redacted_sha256"),
            redacted_bytes=data.get("redacted_bytes"),
            contains_sensitive_data=data.get("contains_sensitive_data", True),
            source_account=data.get("source_account", ""),
            notes=data.get("notes", ""),
        )


@dataclass
class Manifest:
    """Everything held for one finding."""

    finding_id: str
    artifacts: list[EvidenceArtifact] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "finding_id": self.finding_id,
            "artifacts": [a.to_dict() for a in self.artifacts],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Manifest:
        return cls(
            finding_id=data["finding_id"],
            artifacts=[EvidenceArtifact.from_dict(a) for a in data.get("artifacts", [])],
        )


class EvidenceVault:
    """Content-addressed evidence storage with a hard raw/redacted split.

    Args:
        root: Explicit root. Omit to use the resolution order in the module
            docstring.
        audit: Audit log. Every write is recorded.
        allow_in_repository: Permit a root inside a git working tree. Off by
            default, and it should stay off — the guard exists because raw
            evidence being committed is unrecoverable once pushed.
        clock: Injected for testability.
    """

    def __init__(
        self,
        root: str | os.PathLike[str] | None = None,
        *,
        audit: AuditLog | None = None,
        allow_in_repository: bool = False,
        clock: Callable[[], datetime] = _utcnow,
    ):
        self.root = resolve_root(root).resolve()
        self._clock = clock
        self._audit = audit

        if not allow_in_repository:
            repository = find_repository_root(self.root)
            if repository is not None:
                raise VaultLocationError(
                    f"refusing to place the evidence vault at {self.root} — it is "
                    f"inside the git working tree at {repository}. Raw evidence "
                    "must not live in a repository. Set GREYTHEORY_EVIDENCE_ROOT "
                    "to a path outside it, or pass allow_in_repository=True if "
                    "this is a throwaway test tree."
                )

        for directory in (self.raw_dir, self.redacted_dir, self.manifest_dir):
            directory.mkdir(parents=True, exist_ok=True)

    @property
    def raw_dir(self) -> Path:
        return self.root / "raw"

    @property
    def redacted_dir(self) -> Path:
        return self.root / "redacted"

    @property
    def manifest_dir(self) -> Path:
        return self.root / "manifests"

    def _manifest_path(self, finding_id: str) -> Path:
        return self.manifest_dir / f"{_validate_id(finding_id, label='finding id')}.json"

    def _raw_path(self, artifact: EvidenceArtifact) -> Path:
        return self.raw_dir / artifact.finding_id / f"{artifact.id}{artifact.extension}"

    def _redacted_path(self, artifact: EvidenceArtifact) -> Path:
        return (
            self.redacted_dir / artifact.finding_id / f"{artifact.id}{artifact.extension}"
        )

    def _record(self, action: str, artifact: EvidenceArtifact, **extra: Any) -> None:
        if self._audit is None:
            return
        self._audit.append(
            actor="evidence_vault",
            action=action,
            authority_ref=artifact.authority_ref,
            detail={
                "artifact_id": artifact.id,
                "finding_id": artifact.finding_id,
                "kind": artifact.kind,
                **extra,
            },
        )

    def store_raw(
        self,
        *,
        finding_id: str,
        artifact_id: str,
        kind: str,
        data: bytes,
        authority_ref: str,
        extension: str = ".bin",
        source_account: str = "",
        notes: str = "",
    ) -> EvidenceArtifact:
        """Write a raw capture. Once. It is never modified afterwards.

        Raises:
            EvidenceError: If the authority reference is missing, the payload is
                empty, or an artifact with this id already exists. Overwriting
                raw evidence would silently destroy the original, so it is an
                error rather than an update.
        """
        finding_id = _validate_id(finding_id, label="finding id")
        artifact_id = _validate_id(artifact_id, label="artifact id")
        if not authority_ref:
            raise EvidenceError(
                "evidence requires an authority reference (I2); evidence produced "
                "under no authority does not enter the vault"
            )
        if not data:
            raise EvidenceError("refusing to store an empty artifact")

        manifest = self.manifest(finding_id)
        if any(a.id == artifact_id for a in manifest.artifacts):
            raise EvidenceError(
                f"artifact {artifact_id!r} already exists for finding "
                f"{finding_id!r}; raw evidence is written once"
            )

        artifact = EvidenceArtifact(
            id=artifact_id,
            finding_id=finding_id,
            kind=kind,
            created_at=self._clock(),
            authority_ref=authority_ref,
            raw_sha256=hashlib.sha256(data).hexdigest(),
            raw_bytes=len(data),
            extension=extension,
            source_account=source_account,
            notes=notes,
        )

        path = self._raw_path(artifact)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

        manifest.artifacts.append(artifact)
        self._write_manifest(manifest)
        self._record("evidence.store_raw", artifact, sha256=artifact.raw_sha256)
        return artifact

    def attach_redacted(
        self,
        *,
        finding_id: str,
        artifact_id: str,
        data: bytes,
        contains_sensitive_data: bool = False,
    ) -> EvidenceArtifact:
        """Attach the redacted counterpart that may actually be shared.

        Redaction is a deliberate act, not a transformation this module can
        perform — only the operator knows which bytes are sensitive. What the
        vault enforces is that the act happened, and that the result differs
        from the raw capture. An identical copy means nothing was redacted, and
        is refused rather than quietly accepted.
        """
        manifest = self.manifest(finding_id)
        for index, artifact in enumerate(manifest.artifacts):
            if artifact.id != artifact_id:
                continue
            if artifact.is_redacted:
                raise EvidenceError(
                    f"artifact {artifact_id!r} already has a redacted counterpart"
                )
            if not data:
                raise EvidenceError("refusing to store an empty redacted artifact")

            digest = hashlib.sha256(data).hexdigest()
            if digest == artifact.raw_sha256:
                raise EvidenceError(
                    "the redacted copy is byte-identical to the raw capture, so "
                    "nothing was redacted; if the raw capture genuinely contains "
                    "nothing sensitive, say so explicitly rather than copying it"
                )

            updated = EvidenceArtifact(
                **{
                    **artifact.to_dict(),
                    "created_at": artifact.created_at,
                    "redacted_sha256": digest,
                    "redacted_bytes": len(data),
                    "contains_sensitive_data": contains_sensitive_data,
                }
            )
            path = self._redacted_path(updated)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)

            manifest.artifacts[index] = updated
            self._write_manifest(manifest)
            self._record("evidence.attach_redacted", updated, sha256=digest)
            return updated

        raise EvidenceError(
            f"no artifact {artifact_id!r} for finding {finding_id!r}"
        )

    def read_redacted(self, finding_id: str, artifact_id: str) -> bytes:
        artifact = self.get(finding_id, artifact_id)
        if not artifact.is_redacted:
            raise EvidenceError(
                f"artifact {artifact_id!r} has no redacted counterpart"
            )
        return self._redacted_path(artifact).read_bytes()

    def read_raw(self, finding_id: str, artifact_id: str) -> bytes:
        """Read a raw capture.

        Separate from :meth:`read_redacted` on purpose: reaching for raw
        evidence should be a visibly different act in the calling code.
        """
        return self._raw_path(self.get(finding_id, artifact_id)).read_bytes()

    def get(self, finding_id: str, artifact_id: str) -> EvidenceArtifact:
        for artifact in self.manifest(finding_id).artifacts:
            if artifact.id == artifact_id:
                return artifact
        raise EvidenceError(f"no artifact {artifact_id!r} for finding {finding_id!r}")

    def manifest(self, finding_id: str) -> Manifest:
        path = self._manifest_path(finding_id)
        if not path.is_file():
            return Manifest(finding_id=finding_id)
        return Manifest.from_dict(json.loads(path.read_text(encoding="utf-8")))

    def _write_manifest(self, manifest: Manifest) -> None:
        self._manifest_path(manifest.finding_id).write_text(
            json.dumps(manifest.to_dict(), indent=2), encoding="utf-8"
        )

    def verify(self, finding_id: str) -> list[str]:
        """Rehash everything on disk and report any mismatch.

        Returns:
            A list of problems. Empty means every artifact still hashes to what
            the manifest recorded when it was written.
        """
        problems: list[str] = []
        for artifact in self.manifest(finding_id).artifacts:
            raw_path = self._raw_path(artifact)
            if not raw_path.is_file():
                problems.append(f"{artifact.id}: raw artifact is missing")
            elif hashlib.sha256(raw_path.read_bytes()).hexdigest() != artifact.raw_sha256:
                problems.append(f"{artifact.id}: raw artifact has been modified")

            if artifact.is_redacted:
                redacted_path = self._redacted_path(artifact)
                if not redacted_path.is_file():
                    problems.append(f"{artifact.id}: redacted artifact is missing")
                elif (
                    hashlib.sha256(redacted_path.read_bytes()).hexdigest()
                    != artifact.redacted_sha256
                ):
                    problems.append(f"{artifact.id}: redacted artifact has been modified")
        return problems

    def export_package(self, finding_id: str) -> dict[str, Any]:
        """Assemble what may leave the vault. Redacted only.

        Raises:
            EvidenceError: If any artifact lacks a redacted counterpart. A
                partial export is how raw evidence escapes — so an incomplete
                finding exports nothing rather than most of itself.
        """
        manifest = self.manifest(finding_id)
        if not manifest.artifacts:
            raise EvidenceError(f"no evidence held for finding {finding_id!r}")

        unredacted = [a.id for a in manifest.artifacts if not a.is_exportable]
        if unredacted:
            raise EvidenceError(
                f"cannot export {finding_id!r}: {len(unredacted)} artifact(s) have "
                f"no redacted counterpart ({', '.join(unredacted)})"
            )

        problems = self.verify(finding_id)
        if problems:
            raise EvidenceError(
                f"cannot export {finding_id!r}: integrity check failed — "
                + "; ".join(problems)
            )

        return {
            "finding_id": finding_id,
            "exported_at": self._clock().isoformat(),
            "artifacts": [
                {
                    "id": a.id,
                    "kind": a.kind,
                    "authority_ref": a.authority_ref,
                    "sha256": a.redacted_sha256,
                    "bytes": a.redacted_bytes,
                    "path": str(self._redacted_path(a)),
                    "contains_sensitive_data": a.contains_sensitive_data,
                    "source_account": a.source_account,
                }
                for a in manifest.artifacts
            ],
        }


__all__ = [
    "EvidenceArtifact",
    "EvidenceError",
    "EvidenceVault",
    "Manifest",
    "VaultLocationError",
    "find_repository_root",
    "resolve_root",
]
