"""What a public programme directory returned, kept for later.

A directory read is the front door to registering a programme: the bytes a
platform publishes about it are the source material a bundle is compiled from.
A read that vanished when the page refreshed would be a demonstration rather
than a step, so what came back is written down.

Three things this module holds to.

**Reading grants nothing.** Every record restates it. Retrieving what a platform
publishes about a programme is not permission to touch that programme, and a
stored lookup must never be mistaken for a scope contract.

**The bytes are kept beside their hash.** The body is written under its own
SHA-256, so the record and the material cannot drift apart, and a later compile
can prove it used what was actually retrieved.

**Untrusted stays untrusted.** The content came off the public internet. It is
`PUBLIC` and `UNTRUSTED`, and nothing here upgrades that by having saved it.
"""

# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 ChaseInTech

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

from greytheory.audit import AuditLog

SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,191}$")
SCHEMA_VERSION = 1


class DirectoryLookupError(ValueError):
    """Raised when a stored lookup would be invalid or unsafe to persist."""


def resolve_lookup_root(explicit: Path | None = None) -> Path:
    if explicit is not None:
        return Path(explicit).expanduser().resolve()
    if configured := os.environ.get("GREYTHEORY_LOOKUP_ROOT"):
        return Path(configured).expanduser().resolve()
    if local_app_data := os.environ.get("LOCALAPPDATA"):
        return Path(local_app_data) / "GreyTheory" / "directory"
    return Path.home() / ".local" / "share" / "greytheory" / "directory"


def _inside_git_worktree(path: Path) -> bool:
    candidate = path.resolve()
    return any((parent / ".git").exists() for parent in (candidate, *candidate.parents))


def _digest(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _parse_dt(value: Any) -> datetime:
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError) as exc:
        raise DirectoryLookupError("lookup timestamp is not valid") from exc
    return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=timezone.utc)


@dataclass(frozen=True)
class DirectoryLookup:
    """One recorded public read of what a platform publishes about a programme."""

    identifier: str
    provider_id: str
    url: str
    status: int
    content_type: str
    body_sha256: str
    body_bytes: int
    retrieved_at: datetime
    #: Restated on every record. Reading a public page is not permission.
    grants_authority: bool = False
    data_class: str = "PUBLIC"
    trust: str = "UNTRUSTED"

    def __post_init__(self) -> None:
        if not SAFE_ID.fullmatch(str(self.identifier or "")):
            raise DirectoryLookupError(
                f"lookup identifier {self.identifier!r} is not a safe identifier"
            )
        if ":" not in self.identifier:
            raise DirectoryLookupError("a lookup identifier is platform:handle")
        if not self.url.startswith("https://"):
            raise DirectoryLookupError("a stored lookup must record an HTTPS url")
        if not re.fullmatch(r"[a-f0-9]{64}", str(self.body_sha256 or "")):
            raise DirectoryLookupError("a lookup records a lowercase SHA-256 body hash")
        if self.body_bytes < 0:
            raise DirectoryLookupError("body size cannot be negative")
        if self.retrieved_at.tzinfo is None:
            raise DirectoryLookupError("lookup time must be timezone-aware")
        # These are the properties that make the read defensible; a record that
        # claimed otherwise would misdescribe what was actually done.
        if self.grants_authority:
            raise DirectoryLookupError("a directory read never grants authority")
        if self.data_class != "PUBLIC" or self.trust != "UNTRUSTED":
            raise DirectoryLookupError(
                "directory content is public and untrusted; saving it changes neither"
            )

    @property
    def platform(self) -> str:
        return self.identifier.split(":", 1)[0]

    @property
    def handle(self) -> str:
        return self.identifier.split(":", 1)[1]

    def to_dict(self) -> dict[str, Any]:
        return {
            "identifier": self.identifier,
            "provider_id": self.provider_id,
            "url": self.url,
            "status": self.status,
            "content_type": self.content_type,
            "body_sha256": self.body_sha256,
            "body_bytes": self.body_bytes,
            "retrieved_at": self.retrieved_at.isoformat(),
            "grants_authority": False,
            "data_class": self.data_class,
            "trust": self.trust,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> DirectoryLookup:
        return cls(
            identifier=str(data["identifier"]),
            provider_id=str(data["provider_id"]),
            url=str(data["url"]),
            status=int(data["status"]),
            content_type=str(data.get("content_type", "")),
            body_sha256=str(data["body_sha256"]),
            body_bytes=int(data["body_bytes"]),
            retrieved_at=_parse_dt(data["retrieved_at"]),
            data_class=str(data.get("data_class", "PUBLIC")),
            trust=str(data.get("trust", "UNTRUSTED")),
        )

    @classmethod
    def from_evidence(cls, evidence) -> DirectoryLookup:
        """Build a record from what the fetcher returned, without trusting it blindly."""

        return cls(
            identifier=evidence.identifier,
            provider_id=evidence.provider_id,
            url=evidence.url,
            status=int(evidence.status),
            content_type=evidence.content_type,
            body_sha256=evidence.body_sha256,
            body_bytes=int(evidence.body_bytes),
            retrieved_at=_parse_dt(evidence.retrieved_at),
            data_class=evidence.data_class,
            trust=evidence.trust,
        )


class DirectoryLookupStore:
    """Integrity-checked records of public directory reads, with their bodies."""

    def __init__(
        self,
        root: Path | None = None,
        *,
        allow_in_repository: bool = False,
        audit: AuditLog | None = None,
    ) -> None:
        self.root = resolve_lookup_root(root)
        if not allow_in_repository and _inside_git_worktree(self.root):
            raise DirectoryLookupError(
                "directory lookups are personal runtime data and are refused "
                "inside a git working tree"
            )
        self.audit = audit
        self.path = self.root / "lookups.json"
        self.bodies = self.root / "bodies"

    # -- reads ---------------------------------------------------------------

    def lookups(self) -> tuple[DirectoryLookup, ...]:
        return tuple(
            DirectoryLookup.from_dict(item)
            for item in self._load_payload().get("lookups", ())
        )

    def get(self, identifier: str) -> DirectoryLookup | None:
        for item in self.lookups():
            if item.identifier == identifier:
                return item
        return None

    def body_path(self, lookup: DirectoryLookup) -> Path:
        return self.bodies / f"{lookup.body_sha256}.bin"

    def body(self, identifier: str) -> bytes:
        """The retrieved bytes, re-hashed before they are handed back."""

        lookup = self.get(identifier)
        if lookup is None:
            raise DirectoryLookupError(f"no stored lookup for {identifier!r}")
        path = self.body_path(lookup)
        if not path.exists():
            raise DirectoryLookupError(f"the stored body for {identifier!r} is missing")
        raw = path.read_bytes()
        # The hash is the whole point of storing them together: content that no
        # longer matches what was recorded is not what was retrieved.
        if hashlib.sha256(raw).hexdigest() != lookup.body_sha256:
            raise DirectoryLookupError(
                f"the stored body for {identifier!r} does not match its recorded hash"
            )
        return raw

    def verify(self) -> None:
        self._load_payload()
        self.lookups()

    # -- writes --------------------------------------------------------------

    def record(self, evidence, *, actor: str, body: bytes | None = None) -> DirectoryLookup:
        """Store one read. Re-reading the same programme replaces its record."""

        lookup = DirectoryLookup.from_evidence(evidence)
        payload = evidence.body if body is None else body
        if payload is not None:
            if hashlib.sha256(payload).hexdigest() != lookup.body_sha256:
                raise DirectoryLookupError(
                    "the body does not match the hash the fetcher recorded"
                )
            self.bodies.mkdir(parents=True, exist_ok=True)
            self.body_path(lookup).write_bytes(payload)

        current = {item.identifier: item for item in self.lookups()}
        current[lookup.identifier] = lookup
        self._write(current.values())
        if self.audit is not None:
            self.audit.append(
                actor=actor,
                action="directory.lookup.record",
                detail={
                    "identifier": lookup.identifier,
                    "provider_id": lookup.provider_id,
                    "status": lookup.status,
                    "body_sha256": lookup.body_sha256,
                    "data_class": lookup.data_class,
                    "trust": lookup.trust,
                    "grants_authority": False,
                    "target_interaction": False,
                },
            )
        return lookup

    # -- internals -----------------------------------------------------------

    def _load_payload(self) -> dict[str, Any]:
        if not self.path.exists():
            return {"schema_version": SCHEMA_VERSION, "lookups": []}
        try:
            wrapper = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise DirectoryLookupError(f"cannot load directory lookups: {exc}") from exc
        if not isinstance(wrapper, dict) or set(wrapper) != {"payload", "digest"}:
            raise DirectoryLookupError("directory lookups have an invalid envelope")
        payload = wrapper["payload"]
        if not isinstance(payload, dict) or _digest(payload) != wrapper["digest"]:
            raise DirectoryLookupError("directory lookup integrity check failed")
        if payload.get("schema_version") != SCHEMA_VERSION:
            raise DirectoryLookupError("unsupported directory lookup schema")
        if not isinstance(payload.get("lookups"), list):
            raise DirectoryLookupError("directory lookups must be a list")
        return payload

    def _write(self, lookups: Iterable[DirectoryLookup]) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema_version": SCHEMA_VERSION,
            "lookups": [
                item.to_dict()
                for item in sorted(lookups, key=lambda value: value.identifier)
            ],
        }
        wrapper = {"payload": payload, "digest": _digest(payload)}
        encoded = json.dumps(wrapper, indent=2, sort_keys=True) + "\n"
        handle, temp_name = tempfile.mkstemp(
            prefix="lookups-", suffix=".tmp", dir=self.root
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


__all__ = [
    "DirectoryLookup",
    "DirectoryLookupError",
    "DirectoryLookupStore",
    "resolve_lookup_root",
]
