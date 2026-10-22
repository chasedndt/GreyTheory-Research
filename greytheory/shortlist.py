"""Which programmes the operator has chosen to work, and which are set aside.

This is deliberately *not* a `ResearchWorkspace`. A workspace requires a
human-reviewed, verified, unexpired contract, which means it cannot exist until
after review - and shortlisting is the act that leads someone to review a
programme in the first place. Requiring the outcome as a precondition of the
intent would make the front door unreachable.

It is also not built on `archive_workspace`, which is one-way: that store
refuses every write to an archived record, including the write that would
un-archive it. Archiving here is reversible with no expiry, which is what the
word means everywhere it is used well - a shelf, not a bin. Nothing is ever
deleted by this module.

Three separable facts are kept separate on purpose:

* **status** - active or archived, meaning where the entry sits.
* **outcome** - why it was set aside, recorded only when archiving.
* **authority** - not here at all. A shortlist is an intention. It grants
  nothing, proves nothing about scope, and never raises a posture.
"""

# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 ChaseInTech

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Iterable, Mapping

from greytheory.audit import AuditLog

SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,191}$")
SCHEMA_VERSION = 1

#: A note explaining why something was set aside. Long enough to be a reason,
#: short enough that nobody writes a report into it.
MAX_NOTE_CHARS = 280


class ShortlistError(ValueError):
    """Raised when shortlist state would be invalid or unsafe to persist."""


class ShortlistStatus(str, Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"


class ShortlistOutcome(str, Enum):
    """Why an entry was set aside. Recorded on archive, cleared on restore.

    Kept apart from status because "where it sits" and "how it went" are
    different questions, and collapsing them loses the answer to the second.
    """

    UNSET = "unset"
    FINISHED = "finished"
    NOT_STARTED = "not_started"
    OUT_OF_SCOPE_NOW = "out_of_scope_now"
    NO_LONGER_ELIGIBLE = "no_longer_eligible"


def resolve_shortlist_root(explicit: Path | None = None) -> Path:
    if explicit is not None:
        return Path(explicit).expanduser().resolve()
    if configured := os.environ.get("GREYTHEORY_SHORTLIST_ROOT"):
        return Path(configured).expanduser().resolve()
    if local_app_data := os.environ.get("LOCALAPPDATA"):
        return Path(local_app_data) / "GreyTheory" / "shortlist"
    return Path.home() / ".local" / "share" / "greytheory" / "shortlist"


def _inside_git_worktree(path: Path) -> bool:
    candidate = path.resolve()
    return any((parent / ".git").exists() for parent in (candidate, *candidate.parents))


def _digest(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _parse_dt(value: Any, label: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(str(value))
    except (TypeError, ValueError) as exc:
        raise ShortlistError(f"{label} is not a valid timestamp") from exc
    return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=timezone.utc)


@dataclass(frozen=True)
class ShortlistEntry:
    """One programme the operator has chosen to work, or has set aside."""

    programme_id: str
    status: ShortlistStatus
    shortlisted_at: datetime
    updated_at: datetime
    revision: int = 0
    outcome: ShortlistOutcome = ShortlistOutcome.UNSET
    note: str = ""

    def __post_init__(self) -> None:
        if not SAFE_ID.fullmatch(str(self.programme_id or "")):
            raise ShortlistError(
                f"programme id {self.programme_id!r} is not a safe identifier"
            )
        if not isinstance(self.status, ShortlistStatus):
            raise ShortlistError("shortlist status must be a ShortlistStatus value")
        if not isinstance(self.outcome, ShortlistOutcome):
            raise ShortlistError("shortlist outcome must be a ShortlistOutcome value")
        if self.shortlisted_at.tzinfo is None or self.updated_at.tzinfo is None:
            raise ShortlistError("shortlist times must be timezone-aware")
        if self.updated_at < self.shortlisted_at:
            raise ShortlistError("a shortlist update cannot precede the shortlisting")
        if self.revision < 0:
            raise ShortlistError("shortlist revision cannot be negative")
        if len(self.note) > MAX_NOTE_CHARS:
            raise ShortlistError(
                f"a shortlist note is limited to {MAX_NOTE_CHARS} characters"
            )
        # An outcome answers "why was this set aside", so an active entry
        # carrying one would be stating a reason for something that did not
        # happen. Restore clears it for the same reason.
        if self.status is ShortlistStatus.ACTIVE and self.outcome is not ShortlistOutcome.UNSET:
            raise ShortlistError("an active shortlist entry cannot carry an outcome")

    @property
    def is_archived(self) -> bool:
        return self.status is ShortlistStatus.ARCHIVED

    def to_dict(self) -> dict[str, Any]:
        return {
            "programme_id": self.programme_id,
            "status": self.status.value,
            "shortlisted_at": self.shortlisted_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "revision": self.revision,
            "outcome": self.outcome.value,
            "note": self.note,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> ShortlistEntry:
        try:
            status = ShortlistStatus(str(data["status"]))
            outcome = ShortlistOutcome(str(data.get("outcome", "unset")))
        except ValueError as exc:
            raise ShortlistError(f"unknown shortlist state: {exc}") from exc
        return cls(
            programme_id=str(data["programme_id"]),
            status=status,
            shortlisted_at=_parse_dt(data["shortlisted_at"], "shortlisted_at"),
            updated_at=_parse_dt(data["updated_at"], "updated_at"),
            revision=int(data.get("revision", 0)),
            outcome=outcome,
            note=str(data.get("note", "")),
        )


class ShortlistStore:
    """Integrity-checked shortlist state with optimistic revision checks."""

    def __init__(
        self,
        root: Path | None = None,
        *,
        allow_in_repository: bool = False,
        audit: AuditLog | None = None,
        clock=lambda: datetime.now(timezone.utc),
    ) -> None:
        self.root = resolve_shortlist_root(root)
        if not allow_in_repository and _inside_git_worktree(self.root):
            raise ShortlistError(
                "the shortlist is personal runtime data and is refused inside a git working tree"
            )
        self.audit = audit
        self._clock = clock
        self.path = self.root / "shortlist.json"

    # -- reads ---------------------------------------------------------------

    def entries(self) -> tuple[ShortlistEntry, ...]:
        return tuple(
            ShortlistEntry.from_dict(item)
            for item in self._load_payload().get("entries", ())
        )

    def active(self) -> tuple[ShortlistEntry, ...]:
        return tuple(e for e in self.entries() if e.status is ShortlistStatus.ACTIVE)

    def archived(self) -> tuple[ShortlistEntry, ...]:
        return tuple(e for e in self.entries() if e.status is ShortlistStatus.ARCHIVED)

    def get(self, programme_id: str) -> ShortlistEntry | None:
        for entry in self.entries():
            if entry.programme_id == programme_id:
                return entry
        return None

    def verify(self) -> None:
        self._load_payload()
        self.entries()

    # -- transitions ---------------------------------------------------------

    def shortlist(self, programme_id: str, *, actor: str) -> ShortlistEntry:
        """Record an intention to work this programme.

        Shortlisting something already shortlisted is refused rather than
        silently re-dated: the original date is when the operator decided, and
        overwriting it would quietly rewrite their own history.
        """

        existing = self.get(programme_id)
        if existing is not None and existing.status is ShortlistStatus.ACTIVE:
            raise ShortlistError(f"{programme_id!r} is already shortlisted")
        now = self._clock().astimezone(timezone.utc)
        if existing is not None:
            # Previously archived: restoring by shortlisting again keeps the
            # original decision date and advances the revision.
            return self._save(
                replace(
                    existing,
                    status=ShortlistStatus.ACTIVE,
                    outcome=ShortlistOutcome.UNSET,
                    note="",
                    updated_at=now,
                    revision=existing.revision + 1,
                ),
                actor=actor,
                action="shortlist.restore",
            )
        return self._save(
            ShortlistEntry(
                programme_id=programme_id,
                status=ShortlistStatus.ACTIVE,
                shortlisted_at=now,
                updated_at=now,
            ),
            actor=actor,
            action="shortlist.add",
        )

    def archive(
        self,
        programme_id: str,
        *,
        actor: str,
        outcome: ShortlistOutcome = ShortlistOutcome.UNSET,
        note: str = "",
        expected_revision: int | None = None,
    ) -> ShortlistEntry:
        """Set a programme aside. Reversible, with nothing deleted."""

        entry = self._require(programme_id)
        if entry.status is ShortlistStatus.ARCHIVED:
            raise ShortlistError(f"{programme_id!r} is already archived")
        self._check_revision(entry, expected_revision)
        return self._save(
            replace(
                entry,
                status=ShortlistStatus.ARCHIVED,
                outcome=outcome,
                note=note.strip(),
                updated_at=self._clock().astimezone(timezone.utc),
                revision=entry.revision + 1,
            ),
            actor=actor,
            action="shortlist.archive",
        )

    def restore(
        self,
        programme_id: str,
        *,
        actor: str,
        expected_revision: int | None = None,
    ) -> ShortlistEntry:
        """Bring an archived programme back to the active list.

        The guard checks the *transition*, not the stored status, which is the
        whole point: a store that refuses all writes to an archived record can
        never un-archive one, and its archive is a one-way door wearing the
        wrong word.
        """

        entry = self._require(programme_id)
        if entry.status is ShortlistStatus.ACTIVE:
            raise ShortlistError(f"{programme_id!r} is already active")
        self._check_revision(entry, expected_revision)
        return self._save(
            replace(
                entry,
                status=ShortlistStatus.ACTIVE,
                outcome=ShortlistOutcome.UNSET,
                note="",
                updated_at=self._clock().astimezone(timezone.utc),
                revision=entry.revision + 1,
            ),
            actor=actor,
            action="shortlist.restore",
        )

    # -- internals -----------------------------------------------------------

    def _require(self, programme_id: str) -> ShortlistEntry:
        entry = self.get(programme_id)
        if entry is None:
            raise ShortlistError(f"{programme_id!r} is not on the shortlist")
        return entry

    @staticmethod
    def _check_revision(entry: ShortlistEntry, expected_revision: int | None) -> None:
        if expected_revision is None:
            return
        if entry.revision != expected_revision:
            raise ShortlistError(
                f"shortlist revision conflict: expected {expected_revision}, "
                f"current {entry.revision}"
            )

    def _save(self, entry: ShortlistEntry, *, actor: str, action: str) -> ShortlistEntry:
        current = {item.programme_id: item for item in self.entries()}
        current[entry.programme_id] = entry
        self._write(current.values())
        if self.audit is not None:
            self.audit.append(
                actor=actor,
                action=action,
                detail={
                    "programme_id": entry.programme_id,
                    "status": entry.status.value,
                    "outcome": entry.outcome.value,
                    "revision": entry.revision,
                    # Stated on every record so the log cannot later be read as
                    # evidence of permission to act on the programme.
                    "grants_authority": False,
                },
            )
        return entry

    def _load_payload(self) -> dict[str, Any]:
        if not self.path.exists():
            return {"schema_version": SCHEMA_VERSION, "entries": []}
        try:
            wrapper = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ShortlistError(f"cannot load the shortlist: {exc}") from exc
        if not isinstance(wrapper, dict) or set(wrapper) != {"payload", "digest"}:
            raise ShortlistError("the shortlist has an invalid envelope")
        payload = wrapper["payload"]
        if not isinstance(payload, dict) or _digest(payload) != wrapper["digest"]:
            raise ShortlistError("shortlist integrity check failed")
        if payload.get("schema_version") != SCHEMA_VERSION:
            raise ShortlistError("unsupported shortlist schema")
        if not isinstance(payload.get("entries"), list):
            raise ShortlistError("shortlist entries must be a list")
        return payload

    def _write(self, entries: Iterable[ShortlistEntry]) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema_version": SCHEMA_VERSION,
            "entries": [
                item.to_dict()
                for item in sorted(entries, key=lambda value: value.programme_id)
            ],
        }
        wrapper = {"payload": payload, "digest": _digest(payload)}
        encoded = json.dumps(wrapper, indent=2, sort_keys=True) + "\n"
        handle, temp_name = tempfile.mkstemp(
            prefix="shortlist-", suffix=".tmp", dir=self.root
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
    "MAX_NOTE_CHARS",
    "ShortlistEntry",
    "ShortlistError",
    "ShortlistOutcome",
    "ShortlistStatus",
    "ShortlistStore",
    "resolve_shortlist_root",
]
