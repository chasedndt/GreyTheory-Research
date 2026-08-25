"""Private, local broker state for kill-switch and ticket replay controls."""

# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 ChaseInTech

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from greytheory.evidence import find_repository_root


class BrokerStorageError(RuntimeError):
    """Raised when broker runtime state is unsafe, stale, or inconsistent."""


class TicketReplayDenied(BrokerStorageError):
    """Raised after a ticket digest has been reserved once."""


class RateLimitDenied(BrokerStorageError):
    """Raised before reservation when the host interval has not elapsed."""


def _private_root(root: str | os.PathLike[str]) -> Path:
    path = Path(root).expanduser().resolve()
    if find_repository_root(path) is not None:
        raise BrokerStorageError("broker runtime state is refused inside a Git worktree")
    path.mkdir(parents=True, exist_ok=True)
    return path


def _aware(value: datetime, label: str) -> datetime:
    if value.tzinfo is None:
        raise BrokerStorageError(f"{label} must be timezone-aware")
    return value.astimezone(timezone.utc)


def _canonical(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _digest(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(_canonical(payload).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class KillSwitchState:
    engaged: bool
    revision: int
    actor: str
    reason: str
    changed_at: datetime
    authorization_ref: str
    healthy: bool = True

    def __post_init__(self) -> None:
        if self.revision < 0:
            raise BrokerStorageError("kill-switch revision cannot be negative")
        if not self.actor.strip() or not self.reason.strip():
            raise BrokerStorageError("kill-switch actor and reason are required")
        _aware(self.changed_at, "kill-switch change time")
        if not self.engaged and not self.authorization_ref.strip():
            raise BrokerStorageError("releasing the kill switch requires an authorization reference")

    def to_dict(self) -> dict[str, Any]:
        return {
            "engaged": self.engaged,
            "revision": self.revision,
            "actor": self.actor,
            "reason": self.reason,
            "changed_at": self.changed_at.astimezone(timezone.utc).isoformat(),
            "authorization_ref": self.authorization_ref,
        }


class BrokerKillSwitch:
    """Digest-protected switch that fails engaged when absent or corrupt."""

    def __init__(self, root: str | os.PathLike[str]) -> None:
        self.root = _private_root(root)
        self.path = self.root / "kill-switch.json"

    def state(self) -> KillSwitchState:
        if not self.path.exists():
            return KillSwitchState(
                True,
                0,
                "system",
                "kill-switch state is absent; fail closed",
                datetime.fromtimestamp(0, timezone.utc),
                "",
                healthy=False,
            )
        try:
            envelope = json.loads(self.path.read_text(encoding="utf-8"))
            payload = envelope["payload"]
            if set(envelope) != {"payload", "digest"} or envelope["digest"] != _digest(payload):
                raise BrokerStorageError("kill-switch integrity check failed")
            return KillSwitchState(
                engaged=payload["engaged"] is True,
                revision=int(payload["revision"]),
                actor=str(payload["actor"]),
                reason=str(payload["reason"]),
                changed_at=datetime.fromisoformat(str(payload["changed_at"])),
                authorization_ref=str(payload.get("authorization_ref", "")),
            )
        except Exception:
            return KillSwitchState(
                True,
                0,
                "system",
                "kill-switch state is unreadable or corrupt; fail closed",
                datetime.fromtimestamp(0, timezone.utc),
                "",
                healthy=False,
            )

    @property
    def engaged(self) -> bool:
        return self.state().engaged

    def engage(self, *, actor: str, reason: str, at: datetime) -> KillSwitchState:
        return self._write(True, actor=actor, reason=reason, at=at, authorization_ref="")

    def release(
        self,
        *,
        actor: str,
        reason: str,
        at: datetime,
        authorization_ref: str,
    ) -> KillSwitchState:
        return self._write(
            False,
            actor=actor,
            reason=reason,
            at=at,
            authorization_ref=authorization_ref,
        )

    def _write(
        self,
        engaged: bool,
        *,
        actor: str,
        reason: str,
        at: datetime,
        authorization_ref: str,
    ) -> KillSwitchState:
        current = self.state()
        state = KillSwitchState(
            engaged=engaged,
            revision=current.revision + 1,
            actor=str(actor).strip(),
            reason=str(reason).strip(),
            changed_at=_aware(at, "kill-switch change time"),
            authorization_ref=str(authorization_ref).strip(),
        )
        payload = state.to_dict()
        encoded = json.dumps(
            {"payload": payload, "digest": _digest(payload)},
            indent=2,
            sort_keys=True,
        ) + "\n"
        handle, temp_name = tempfile.mkstemp(
            prefix="kill-switch-", suffix=".tmp", dir=self.root
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
        return state


@dataclass(frozen=True)
class TicketReservation:
    ticket_digest: str
    ticket_id: str
    canonical_host: str
    min_interval_seconds: float
    status: str
    reserved_at: datetime
    completed_at: datetime | None
    receipt_digest: str | None


class TicketReplayLedger:
    """SQLite exact-once reservation; a crash consumes rather than replays."""

    def __init__(self, root: str | os.PathLike[str]) -> None:
        self.root = _private_root(root)
        self.path = self.root / "ticket-replay.sqlite3"
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=5, isolation_level=None)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute("PRAGMA journal_mode=WAL")
            connection.execute("PRAGMA synchronous=FULL")
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS ticket_reservations (
                    ticket_digest TEXT PRIMARY KEY,
                    ticket_id TEXT NOT NULL,
                    canonical_host TEXT NOT NULL,
                    min_interval_seconds REAL NOT NULL CHECK (min_interval_seconds > 0),
                    status TEXT NOT NULL CHECK (status IN ('reserved', 'completed')),
                    reserved_at TEXT NOT NULL,
                    completed_at TEXT,
                    receipt_digest TEXT,
                    CHECK (
                        (status = 'reserved' AND completed_at IS NULL AND receipt_digest IS NULL)
                        OR
                        (status = 'completed' AND completed_at IS NOT NULL AND receipt_digest IS NOT NULL)
                    )
                )
                """
            )
            columns = {
                row[1] for row in connection.execute("PRAGMA table_info(ticket_reservations)")
            }
            expected = {
                "ticket_digest",
                "ticket_id",
                "canonical_host",
                "min_interval_seconds",
                "status",
                "reserved_at",
                "completed_at",
                "receipt_digest",
            }
            if columns != expected:
                raise BrokerStorageError(
                    "ticket replay ledger schema is incompatible; migration is required"
                )
            connection.execute("PRAGMA user_version=1")

    def reserve(
        self,
        *,
        ticket_digest: str,
        ticket_id: str,
        canonical_host: str,
        min_interval_seconds: float,
        at: datetime,
    ) -> None:
        when_value = _aware(at, "ticket reservation time")
        when = when_value.isoformat()
        if not canonical_host.strip() or min_interval_seconds <= 0:
            raise BrokerStorageError("rate reservation requires a host and positive interval")
        try:
            with self._connect() as connection:
                connection.execute("BEGIN IMMEDIATE")
                existing = connection.execute(
                    "SELECT 1 FROM ticket_reservations WHERE ticket_digest = ?",
                    (ticket_digest,),
                ).fetchone()
                if existing is not None:
                    connection.rollback()
                    raise TicketReplayDenied(
                        f"ticket {ticket_id!r} has already been reserved or consumed"
                    )
                previous = connection.execute(
                    """
                    SELECT reserved_at, min_interval_seconds
                      FROM ticket_reservations
                     WHERE canonical_host = ?
                     ORDER BY reserved_at DESC
                     LIMIT 1
                    """,
                    (canonical_host,),
                ).fetchone()
                if previous is not None:
                    previous_at = datetime.fromisoformat(previous["reserved_at"])
                    required = max(
                        float(min_interval_seconds),
                        float(previous["min_interval_seconds"]),
                    )
                    if (when_value - previous_at).total_seconds() < required:
                        connection.rollback()
                        raise RateLimitDenied(
                            f"host {canonical_host!r} requires {required:g}s between tickets"
                        )
                connection.execute(
                    """
                    INSERT INTO ticket_reservations
                    VALUES (?, ?, ?, ?, 'reserved', ?, NULL, NULL)
                    """,
                    (
                        ticket_digest,
                        ticket_id,
                        canonical_host,
                        float(min_interval_seconds),
                        when,
                    ),
                )
                connection.commit()
        except sqlite3.IntegrityError as exc:
            raise TicketReplayDenied(
                f"ticket {ticket_id!r} has already been reserved or consumed"
            ) from exc

    def complete(
        self,
        *,
        ticket_digest: str,
        receipt_digest: str,
        at: datetime,
    ) -> None:
        when = _aware(at, "ticket completion time").isoformat()
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            cursor = connection.execute(
                """
                UPDATE ticket_reservations
                   SET status = 'completed', completed_at = ?, receipt_digest = ?
                 WHERE ticket_digest = ? AND status = 'reserved'
                """,
                (when, receipt_digest, ticket_digest),
            )
            if cursor.rowcount != 1:
                connection.rollback()
                raise BrokerStorageError("ticket is missing, replayed, or already completed")
            connection.commit()

    def get(self, ticket_digest: str) -> TicketReservation | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM ticket_reservations WHERE ticket_digest = ?",
                (ticket_digest,),
            ).fetchone()
        if row is None:
            return None
        return TicketReservation(
            ticket_digest=row["ticket_digest"],
            ticket_id=row["ticket_id"],
            canonical_host=row["canonical_host"],
            min_interval_seconds=float(row["min_interval_seconds"]),
            status=row["status"],
            reserved_at=datetime.fromisoformat(row["reserved_at"]),
            completed_at=(
                datetime.fromisoformat(row["completed_at"])
                if row["completed_at"]
                else None
            ),
            receipt_digest=row["receipt_digest"],
        )

    def verify(self) -> None:
        with self._connect() as connection:
            result = connection.execute("PRAGMA integrity_check").fetchone()[0]
            if result != "ok":
                raise BrokerStorageError(f"ticket replay ledger integrity failed: {result}")
            invalid = connection.execute(
                """
                SELECT COUNT(*) FROM ticket_reservations
                 WHERE (status = 'reserved' AND (completed_at IS NOT NULL OR receipt_digest IS NOT NULL))
                    OR (status = 'completed' AND (completed_at IS NULL OR receipt_digest IS NULL))
                """
            ).fetchone()[0]
            if invalid:
                raise BrokerStorageError("ticket replay ledger contains invalid state")


__all__ = [
    "BrokerKillSwitch",
    "RateLimitDenied",
    "BrokerStorageError",
    "KillSwitchState",
    "TicketReplayDenied",
    "TicketReplayLedger",
    "TicketReservation",
]
