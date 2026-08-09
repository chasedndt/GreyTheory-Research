"""Offline programme-source bundles.

One programme rarely has one source of authority. Platform defaults, the
programme policy, scope tables, attachments, and linked policies can all apply
at once. This module records the complete reviewed set without fetching any of
it: acquisition is an operator action, compilation is local and deterministic.

The bundle is deliberately fail-closed. A missing file, bad path, hash drift,
uncited authority field, invalid precedence list, or unresolved human decision
blocks the resulting contract. It never guesses which source should win.
"""

# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 ChaseInTech

from __future__ import annotations

import csv
import ipaddress
import io
import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path, PurePosixPath
from typing import Any

from greytheory.authority.compiler import compile_contract, source_hash
from greytheory.authority.scope import ContractStatus, ScopeContract

SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
PUBLIC_HTTPS_URL = re.compile(
    r"^https://(?P<authority>[^/?#\s]+)(?:[/?#][^\s]*)?$",
    re.IGNORECASE,
)
REQUIRED_FIELD_SOURCES = {
    "in_scope",
    "out_of_scope",
    "prohibited_techniques",
    "max_authority",
}


class BundleError(ValueError):
    """The bundle cannot be read safely enough to produce a contract."""


class SourceKind(str, Enum):
    PLATFORM_DEFAULT = "platform_default"
    PROGRAMME_POLICY = "programme_policy"
    SCOPE_TABLE = "scope_table"
    LINKED_POLICY = "linked_policy"
    ATTACHMENT = "attachment"


class CaptureMode(str, Enum):
    """How faithfully the saved text represents the public source."""

    STRUCTURED_EXPORT = "structured_export"
    VERBATIM = "verbatim"
    OPERATOR_EXTRACT = "operator_extract"


class ResolutionStatus(str, Enum):
    ACCEPTED = "accepted"
    PENDING = "pending"
    REJECTED = "rejected"


class DerivationKind(str, Enum):
    HACKERONE_SCOPE_CSV_V1 = "hackerone_scope_csv_v1"


def _parse_datetime(value: Any, *, label: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise BundleError(f"{label} must be an ISO-8601 timestamp")
    text = value.strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as exc:
        raise BundleError(f"{label} is not a valid ISO-8601 timestamp") from exc
    if parsed.tzinfo is None:
        raise BundleError(f"{label} must include a timezone")
    return parsed


def _safe_id(value: Any, *, label: str) -> str:
    text = str(value or "").strip()
    if not SAFE_ID.fullmatch(text):
        raise BundleError(f"{label} {value!r} is not a safe identifier")
    return text


def _safe_file(root: Path, value: Any, *, label: str) -> Path:
    text = str(value or "").strip()
    relative = PurePosixPath(text)
    if (
        not text
        or relative.is_absolute()
        or ".." in relative.parts
        or "\\" in text
        or ":" in text
    ):
        raise BundleError(f"{label} must be a safe relative POSIX path")

    root = root.resolve()
    path = (root / Path(*relative.parts)).resolve()
    if path != root and root not in path.parents:
        raise BundleError(f"{label} escapes the bundle directory")
    if not path.is_file():
        raise BundleError(f"{label} does not exist: {text}")
    return path


def _public_https_url(value: str) -> bool:
    """Validate provenance syntax without importing a network-capable module."""

    match = PUBLIC_HTTPS_URL.fullmatch(value)
    if match is None:
        return False
    authority = match.group("authority")
    # Provenance URLs identify public documents, never embedded credentials.
    if "@" in authority:
        return False

    if authority.startswith("["):
        closing = authority.find("]")
        if closing == -1:
            return False
        host = authority[1:closing]
        port = authority[closing + 1 :]
        if port and (not port.startswith(":") or not port[1:].isdigit()):
            return False
    else:
        if authority.count(":") > 1:
            return False
        host, separator, port = authority.partition(":")
        if separator and not port.isdigit():
            return False

    host = host.casefold().rstrip(".")
    if not host or host == "localhost" or host.endswith(".local"):
        return False
    try:
        return ipaddress.ip_address(host).is_global
    except ValueError:
        # A bare intranet label is not public provenance. Public DNS names have
        # at least one dot; syntax beyond that is preserved as source metadata.
        return "." in host


@dataclass(frozen=True)
class ProgrammeSource:
    id: str
    kind: SourceKind
    capture_mode: CaptureMode
    url: str
    retrieved_at: datetime
    path: str
    declared_hash: str
    content: str = field(repr=False)
    last_modified_at: datetime | None = None

    @property
    def actual_hash(self) -> str:
        return source_hash(self.content)

    @property
    def intact(self) -> bool:
        return self.declared_hash == self.actual_hash

    def metadata_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "kind": self.kind.value,
            "capture_mode": self.capture_mode.value,
            "url": self.url,
            "retrieved_at": self.retrieved_at.isoformat(),
            "last_modified_at": (
                self.last_modified_at.isoformat() if self.last_modified_at else None
            ),
            "path": self.path,
            "declared_hash": self.declared_hash,
            "actual_hash": self.actual_hash,
        }


@dataclass(frozen=True)
class HumanResolution:
    id: str
    issue: str
    decision: str
    source_ids: tuple[str, ...]
    status: ResolutionStatus
    decided_by: str = ""
    decided_at: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "issue": self.issue,
            "decision": self.decision,
            "source_ids": list(self.source_ids),
            "status": self.status.value,
            "decided_by": self.decided_by,
            "decided_at": self.decided_at.isoformat() if self.decided_at else None,
        }


@dataclass(frozen=True)
class SourceDerivation:
    id: str
    kind: DerivationKind
    source_id: str
    target_fields: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "kind": self.kind.value,
            "source_id": self.source_id,
            "target_fields": list(self.target_fields),
        }


def _programme_patterns(
    programme: dict[str, Any], field_name: str
) -> set[tuple[str, str]]:
    patterns: set[tuple[str, str]] = set()
    for entry in programme.get(field_name, []):
        if isinstance(entry, dict) and entry.get("type") and entry.get("value"):
            patterns.add(
                (str(entry["type"]).strip().lower(), str(entry["value"]).strip())
            )
    return patterns


def _format_patterns(patterns: set[tuple[str, str]]) -> str:
    values = [f"{pattern_type}:{value}" for pattern_type, value in sorted(patterns)]
    shown = ", ".join(values[:3])
    return shown + (f" and {len(values) - 3} more" if len(values) > 3 else "")


def _check_hackerone_scope_csv(
    source: ProgrammeSource,
    programme: dict[str, Any],
    *,
    derivation_id: str,
) -> list[str]:
    """Verify the normalised scope record against HackerOne's public CSV."""
    reader = csv.DictReader(io.StringIO(source.content))
    required = {"identifier", "asset_type", "eligible_for_submission"}
    missing_columns = required - set(reader.fieldnames or [])
    if missing_columns:
        return [
            f"derivation {derivation_id!r} source lacks columns: "
            f"{', '.join(sorted(missing_columns))}"
        ]

    type_map = {
        "URL": "exact",
        "SOURCE_CODE": "exact",
        "OTHER": "exact",
        "WILDCARD": "wildcard",
    }
    derived_in: set[tuple[str, str]] = set()
    derived_out: set[tuple[str, str]] = set()
    issues: list[str] = []
    for row_number, row in enumerate(reader, start=2):
        identifier = str(row.get("identifier") or "").strip()
        asset_type = str(row.get("asset_type") or "").strip().upper()
        eligibility = str(row.get("eligible_for_submission") or "").strip().lower()
        if not identifier:
            issues.append(
                f"derivation {derivation_id!r} row {row_number} has no identifier"
            )
            continue
        if asset_type not in type_map:
            issues.append(
                f"derivation {derivation_id!r} row {row_number} has unsupported "
                f"asset_type {asset_type!r}"
            )
            continue
        pattern = (type_map[asset_type], identifier)
        if eligibility == "true":
            derived_in.add(pattern)
        elif eligibility == "false":
            derived_out.add(pattern)
        else:
            issues.append(
                f"derivation {derivation_id!r} row {row_number} has non-boolean "
                "eligible_for_submission"
            )

    actual_in = _programme_patterns(programme, "in_scope")
    actual_out = _programme_patterns(programme, "out_of_scope")
    for label, expected, actual in (
        ("in_scope", derived_in, actual_in),
        ("out_of_scope", derived_out, actual_out),
    ):
        missing = expected - actual
        extra = actual - expected
        if missing:
            issues.append(
                f"derivation {derivation_id!r} record omits {label}: "
                f"{_format_patterns(missing)}"
            )
        if extra:
            issues.append(
                f"derivation {derivation_id!r} record adds uncited {label}: "
                f"{_format_patterns(extra)}"
            )
    return issues


@dataclass(frozen=True)
class ProgrammeSourceBundle:
    id: str
    programme_id: str
    retrieved_at: datetime
    sources: tuple[ProgrammeSource, ...]
    precedence: tuple[str, ...]
    programme: dict[str, Any]
    field_sources: dict[str, tuple[str, ...]]
    derivations: tuple[SourceDerivation, ...]
    human_resolutions: tuple[HumanResolution, ...]
    ambiguities: tuple[str, ...] = ()
    schema_version: int = 1

    @classmethod
    def load(cls, manifest_path: str | Path) -> ProgrammeSourceBundle:
        path = Path(manifest_path)
        if path.is_dir():
            path = path / "manifest.json"
        if not path.is_file():
            raise BundleError(f"bundle manifest does not exist: {path}")

        try:
            manifest = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise BundleError(f"could not read bundle manifest {path}: {exc}") from exc
        if not isinstance(manifest, dict):
            raise BundleError("bundle manifest must be a JSON object")
        if manifest.get("schema_version") != 1:
            raise BundleError("unsupported bundle schema_version; expected 1")

        root = path.parent
        bundle_id = _safe_id(manifest.get("id"), label="bundle id")
        programme_id = _safe_id(
            manifest.get("programme_id"), label="programme id"
        )
        retrieved_at = _parse_datetime(
            manifest.get("retrieved_at"), label="bundle retrieved_at"
        )

        record_path = _safe_file(
            root, manifest.get("programme_record"), label="programme_record"
        )
        try:
            programme = json.loads(record_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise BundleError(f"programme_record is not valid JSON: {exc}") from exc
        if not isinstance(programme, dict):
            raise BundleError("programme_record must contain a JSON object")

        raw_sources = manifest.get("sources")
        if not isinstance(raw_sources, list) or not raw_sources:
            raise BundleError("bundle must declare at least one source")

        sources: list[ProgrammeSource] = []
        seen_ids: set[str] = set()
        ambiguities: list[str] = []
        for index, raw_source in enumerate(raw_sources):
            if not isinstance(raw_source, dict):
                raise BundleError(f"sources[{index}] must be an object")
            source_id = _safe_id(raw_source.get("id"), label=f"sources[{index}].id")
            if source_id in seen_ids:
                raise BundleError(f"duplicate source id {source_id!r}")
            seen_ids.add(source_id)

            try:
                kind = SourceKind(raw_source.get("kind"))
                capture_mode = CaptureMode(raw_source.get("capture_mode"))
            except ValueError as exc:
                raise BundleError(
                    f"source {source_id!r} has an unknown kind or capture_mode"
                ) from exc

            url = str(raw_source.get("url") or "").strip()
            if not _public_https_url(url):
                raise BundleError(f"source {source_id!r} must use a public HTTPS URL")

            source_path_value = str(raw_source.get("path") or "")
            source_path = _safe_file(
                root, source_path_value, label=f"source {source_id!r} path"
            )
            try:
                content = source_path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError) as exc:
                raise BundleError(
                    f"source {source_id!r} could not be read as UTF-8: {exc}"
                ) from exc
            declared_hash = str(raw_source.get("sha256") or "").strip()
            source = ProgrammeSource(
                id=source_id,
                kind=kind,
                capture_mode=capture_mode,
                url=url,
                retrieved_at=_parse_datetime(
                    raw_source.get("retrieved_at"),
                    label=f"source {source_id!r} retrieved_at",
                ),
                last_modified_at=(
                    _parse_datetime(
                        raw_source["last_modified_at"],
                        label=f"source {source_id!r} last_modified_at",
                    )
                    if raw_source.get("last_modified_at")
                    else None
                ),
                path=source_path_value,
                declared_hash=declared_hash,
                content=content,
            )
            if not declared_hash.startswith("sha256:"):
                ambiguities.append(
                    f"source {source_id!r} has no valid declared sha256 hash"
                )
            elif not source.intact:
                ambiguities.append(
                    f"source {source_id!r} hash mismatch: declared "
                    f"{source.declared_hash}, actual {source.actual_hash}"
                )
            if source.retrieved_at > retrieved_at:
                ambiguities.append(
                    f"source {source_id!r} was retrieved after the bundle timestamp"
                )
            sources.append(source)

        precedence_raw = manifest.get("precedence")
        if not isinstance(precedence_raw, list):
            raise BundleError("precedence must be a high-to-low list of source ids")
        precedence = tuple(str(item) for item in precedence_raw)
        if len(precedence) != len(set(precedence)):
            ambiguities.append("precedence contains duplicate source ids")
        missing = seen_ids - set(precedence)
        unknown = set(precedence) - seen_ids
        if missing:
            ambiguities.append(
                f"precedence omits source ids: {', '.join(sorted(missing))}"
            )
        if unknown:
            ambiguities.append(
                f"precedence names unknown source ids: {', '.join(sorted(unknown))}"
            )

        raw_field_sources = manifest.get("field_sources")
        if not isinstance(raw_field_sources, dict):
            raise BundleError("field_sources must be an object")
        field_sources: dict[str, tuple[str, ...]] = {}
        for field_name, source_ids in raw_field_sources.items():
            if not isinstance(source_ids, list) or not source_ids:
                ambiguities.append(
                    f"field_sources.{field_name} must cite at least one source"
                )
                continue
            citations = tuple(str(item) for item in source_ids)
            field_sources[str(field_name)] = citations
            cited_unknown = set(citations) - seen_ids
            if cited_unknown:
                ambiguities.append(
                    f"field_sources.{field_name} cites unknown source ids: "
                    f"{', '.join(sorted(cited_unknown))}"
                )
        for field_name in sorted(REQUIRED_FIELD_SOURCES - set(field_sources)):
            ambiguities.append(f"authority field {field_name!r} has no source citation")

        raw_derivations = manifest.get("derivations", [])
        if not isinstance(raw_derivations, list):
            raise BundleError("derivations must be a list")
        derivations: list[SourceDerivation] = []
        derivation_ids: set[str] = set()
        sources_by_id = {source.id: source for source in sources}
        for index, raw_derivation in enumerate(raw_derivations):
            if not isinstance(raw_derivation, dict):
                raise BundleError(f"derivations[{index}] must be an object")
            derivation_id = _safe_id(
                raw_derivation.get("id"), label=f"derivations[{index}].id"
            )
            if derivation_id in derivation_ids:
                raise BundleError(f"duplicate derivation id {derivation_id!r}")
            derivation_ids.add(derivation_id)
            try:
                kind = DerivationKind(raw_derivation.get("kind"))
            except ValueError as exc:
                raise BundleError(
                    f"derivation {derivation_id!r} has unknown kind"
                ) from exc
            source_id = str(raw_derivation.get("source_id") or "").strip()
            if source_id not in sources_by_id:
                ambiguities.append(
                    f"derivation {derivation_id!r} cites unknown source {source_id!r}"
                )
            target_fields = tuple(
                str(item) for item in raw_derivation.get("target_fields", [])
            )
            if not target_fields:
                ambiguities.append(
                    f"derivation {derivation_id!r} declares no target_fields"
                )
            derivation = SourceDerivation(
                id=derivation_id,
                kind=kind,
                source_id=source_id,
                target_fields=target_fields,
            )
            derivations.append(derivation)
            if source_id in sources_by_id:
                if kind is DerivationKind.HACKERONE_SCOPE_CSV_V1:
                    if set(target_fields) != {"in_scope", "out_of_scope"}:
                        ambiguities.append(
                            f"derivation {derivation_id!r} must target in_scope and "
                            "out_of_scope"
                        )
                    ambiguities.extend(
                        _check_hackerone_scope_csv(
                            sources_by_id[source_id],
                            programme,
                            derivation_id=derivation_id,
                        )
                    )

        raw_resolutions = manifest.get("human_resolutions", [])
        if not isinstance(raw_resolutions, list):
            raise BundleError("human_resolutions must be a list")
        resolutions: list[HumanResolution] = []
        resolution_ids: set[str] = set()
        for index, raw_resolution in enumerate(raw_resolutions):
            if not isinstance(raw_resolution, dict):
                raise BundleError(f"human_resolutions[{index}] must be an object")
            resolution_id = _safe_id(
                raw_resolution.get("id"), label=f"human_resolutions[{index}].id"
            )
            if resolution_id in resolution_ids:
                raise BundleError(f"duplicate human resolution id {resolution_id!r}")
            resolution_ids.add(resolution_id)
            try:
                status = ResolutionStatus(raw_resolution.get("status"))
            except ValueError as exc:
                raise BundleError(
                    f"human resolution {resolution_id!r} has unknown status"
                ) from exc

            source_ids = tuple(
                str(item) for item in raw_resolution.get("source_ids", [])
            )
            cited_unknown = set(source_ids) - seen_ids
            if not source_ids:
                ambiguities.append(
                    f"human resolution {resolution_id!r} cites no sources"
                )
            elif cited_unknown:
                ambiguities.append(
                    f"human resolution {resolution_id!r} cites unknown sources: "
                    f"{', '.join(sorted(cited_unknown))}"
                )

            decided_at = (
                _parse_datetime(
                    raw_resolution["decided_at"],
                    label=f"human resolution {resolution_id!r} decided_at",
                )
                if raw_resolution.get("decided_at")
                else None
            )
            resolution = HumanResolution(
                id=resolution_id,
                issue=str(raw_resolution.get("issue") or "").strip(),
                decision=str(raw_resolution.get("decision") or "").strip(),
                source_ids=source_ids,
                status=status,
                decided_by=str(raw_resolution.get("decided_by") or "").strip(),
                decided_at=decided_at,
            )
            if not resolution.issue:
                ambiguities.append(
                    f"human resolution {resolution_id!r} has no issue statement"
                )
            if status is ResolutionStatus.ACCEPTED:
                if not resolution.decision:
                    ambiguities.append(
                        f"accepted human resolution {resolution_id!r} has no decision"
                    )
                if not resolution.decided_by or not resolution.decided_at:
                    ambiguities.append(
                        f"accepted human resolution {resolution_id!r} lacks "
                        "decided_by or decided_at"
                    )
            else:
                ambiguities.append(
                    f"human resolution {resolution_id!r} remains {status.value}"
                )
            resolutions.append(resolution)

        if str(programme.get("id") or "").strip() != programme_id:
            ambiguities.append(
                "programme_record id does not match manifest programme_id"
            )

        return cls(
            id=bundle_id,
            programme_id=programme_id,
            retrieved_at=retrieved_at,
            sources=tuple(sources),
            precedence=precedence,
            programme=programme,
            field_sources=field_sources,
            derivations=tuple(derivations),
            human_resolutions=tuple(resolutions),
            ambiguities=tuple(ambiguities),
        )

    @property
    def sources_by_id(self) -> dict[str, ProgrammeSource]:
        return {source.id: source for source in self.sources}

    def canonical_payload(self) -> dict[str, Any]:
        by_id = self.sources_by_id
        ordered_sources = [
            by_id[source_id]
            for source_id in self.precedence
            if source_id in by_id
        ]
        ordered_ids = {source.id for source in ordered_sources}
        ordered_sources.extend(
            sorted(
                (source for source in self.sources if source.id not in ordered_ids),
                key=lambda source: source.id,
            )
        )
        return {
            "schema_version": self.schema_version,
            "id": self.id,
            "programme_id": self.programme_id,
            "retrieved_at": self.retrieved_at.isoformat(),
            "precedence": list(self.precedence),
            "field_sources": {
                key: list(value) for key, value in sorted(self.field_sources.items())
            },
            "derivations": [derivation.to_dict() for derivation in self.derivations],
            "human_resolutions": [
                resolution.to_dict() for resolution in self.human_resolutions
            ],
            "programme": self.programme,
            "sources": [
                {
                    **source.metadata_dict(),
                    "content": source.content,
                }
                for source in ordered_sources
            ],
        }

    def canonical_snapshot(self) -> str:
        """The complete semantic source set a future review attaches to."""
        return json.dumps(
            self.canonical_payload(),
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
        ) + "\n"

    @property
    def bundle_hash(self) -> str:
        return source_hash(self.canonical_snapshot())


@dataclass
class BundleCompilationResult:
    bundle: ProgrammeSourceBundle
    contract: ScopeContract
    ambiguities: list[str]
    snapshot: str

    @property
    def blocked(self) -> bool:
        return self.contract.status is ContractStatus.BLOCKED


def compile_source_bundle(
    bundle: ProgrammeSourceBundle | str | Path,
    *,
    now: datetime | None = None,
) -> BundleCompilationResult:
    """Compile a saved bundle without performing network I/O."""
    if not isinstance(bundle, ProgrammeSourceBundle):
        bundle = ProgrammeSourceBundle.load(bundle)

    snapshot = bundle.canonical_snapshot()
    base = compile_contract(bundle.programme, raw_source=snapshot, now=now)
    ambiguities = [*bundle.ambiguities, *base.ambiguities]
    contract = base.contract
    contract.source_hashes = [
        bundle.sources_by_id[source_id].actual_hash
        for source_id in bundle.precedence
        if source_id in bundle.sources_by_id
    ] + [bundle.bundle_hash]
    contract.ambiguities = ambiguities
    if ambiguities:
        contract.status = ContractStatus.BLOCKED

    return BundleCompilationResult(
        bundle=bundle,
        contract=contract,
        ambiguities=ambiguities,
        snapshot=snapshot,
    )


__all__ = [
    "BundleCompilationResult",
    "BundleError",
    "CaptureMode",
    "DerivationKind",
    "HumanResolution",
    "ProgrammeSource",
    "ProgrammeSourceBundle",
    "ResolutionStatus",
    "SourceDerivation",
    "SourceKind",
    "compile_source_bundle",
]
