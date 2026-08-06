"""Append-only, hash-chained audit log.

Every gate decision and every consequential action lands here. The log is the
system's answer to "what did it actually do", and it is written so that a
silent edit is detectable rather than merely discouraged: each record commits
to the hash of the record before it, so altering or removing any entry breaks
the chain from that point on.

Format is JSONL — one record per line, readable with ``jq``, appendable without
rewriting the file.
"""

# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 ChaseInTech

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterator

GENESIS = "0" * 64
"""``prev_hash`` of the first record. A chain must start somewhere."""


class AuditVerificationError(Exception):
    """Raised when the chain does not verify."""


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _canonical(payload: dict[str, Any]) -> str:
    """Deterministic JSON, so the same record always hashes the same way."""
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)


@dataclass(frozen=True)
class AuditRecord:
    seq: int
    timestamp: str
    actor: str
    action: str
    authority_ref: str | None
    """Invariant I2. ``None`` is permitted only for actions that precede any
    authority existing — chiefly the compilation of a contract itself."""

    detail: dict[str, Any] = field(default_factory=dict)
    prev_hash: str = GENESIS
    hash: str = ""

    def digest(self) -> str:
        """Hash of everything in this record except the hash field itself."""
        body = asdict(self)
        body.pop("hash")
        return hashlib.sha256(_canonical(body).encode("utf-8")).hexdigest()

    def to_json(self) -> str:
        return _canonical(asdict(self))

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AuditRecord:
        return cls(
            seq=data["seq"],
            timestamp=data["timestamp"],
            actor=data["actor"],
            action=data["action"],
            authority_ref=data.get("authority_ref"),
            detail=data.get("detail", {}),
            prev_hash=data["prev_hash"],
            hash=data["hash"],
        )


class AuditLog:
    """A hash-chained JSONL log.

    The log is opened in append mode for every write and flushed immediately.
    It is not a database and does not try to be one; durability matters more
    than throughput, because this file is the only thing that can answer a
    question about the system's past behaviour.
    """

    def __init__(self, path: str | os.PathLike[str], *, clock: Callable[[], datetime] = _utcnow):
        self.path = Path(path)
        self._clock = clock
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(
        self,
        *,
        actor: str,
        action: str,
        authority_ref: str | None = None,
        detail: dict[str, Any] | None = None,
    ) -> AuditRecord:
        """Write one record, chained to the current tail."""
        tail = self.tail()
        record = AuditRecord(
            seq=0 if tail is None else tail.seq + 1,
            timestamp=self._clock().isoformat(),
            actor=actor,
            action=action,
            authority_ref=authority_ref,
            detail=detail or {},
            prev_hash=GENESIS if tail is None else tail.hash,
        )
        record = AuditRecord(**{**asdict(record), "hash": record.digest()})
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(record.to_json() + "\n")
            handle.flush()
        return record

    def __iter__(self) -> Iterator[AuditRecord]:
        if not self.path.exists():
            return
        with self.path.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if line:
                    yield AuditRecord.from_dict(json.loads(line))

    def records(self) -> list[AuditRecord]:
        return list(self)

    def tail(self) -> AuditRecord | None:
        last: AuditRecord | None = None
        for record in self:
            last = record
        return last

    def verify(self) -> None:
        """Walk the chain and confirm nothing has been altered or dropped.

        Raises:
            AuditVerificationError: On the first inconsistency found, naming the
                sequence number so the damage can be located.
        """
        expected_prev = GENESIS
        expected_seq = 0
        for record in self:
            if record.seq != expected_seq:
                raise AuditVerificationError(
                    f"sequence break at {record.seq}: expected {expected_seq}"
                )
            if record.prev_hash != expected_prev:
                raise AuditVerificationError(
                    f"chain break at seq {record.seq}: prev_hash does not match "
                    "the preceding record"
                )
            if record.hash != record.digest():
                raise AuditVerificationError(
                    f"record {record.seq} has been modified since it was written"
                )
            expected_prev = record.hash
            expected_seq += 1

    def is_valid(self) -> bool:
        try:
            self.verify()
        except AuditVerificationError:
            return False
        return True
