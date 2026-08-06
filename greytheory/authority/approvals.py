"""Operator approvals — bound, expiring, single-use.

GreyTheory is a standalone tool. It ships a complete, self-sufficient approval
store (:class:`LocalApprovalStore`) and requires nothing else to run.

It also integrates. Where an approval system already exists, GreyTheory reads
from it rather than competing with it — an approval recorded in one place and
invisible to another is worse than either alone. :class:`ChaseOSApprovalStore`
is the first such adapter; :class:`ApprovalStore` is the protocol any other
implementation satisfies.

Whichever store is in use, this module enforces the three properties a decision
record alone does not provide:

**Binding.** An approval authorises one action against one target. An approval
for reading a document does not authorise deleting one, and an approval against
``a.example.test`` does not carry to ``b.example.test``.

**Expiry.** Consent given a month ago is not consent now. Eight hours by
default — a working session, not a week.

**Exact-once consumption.** An approval that has already been spent cannot be
replayed. Enforced against the audit log rather than a second store, since the
log already records every allow and so already knows what has been spent.

---

Open question O2 asked whether ChaseOS already owns an approval layer. It does:

* ``runtime/operator_surface/approvals.py`` — ``ApprovalRequest`` / ``ApprovalResponse``
* ``runtime/operator_surface/contracts.py`` — ``ApprovalRecord``
* ``runtime/osril/approvals.py`` — durable responses at
  ``<vault>/runtime/osril/approvals/<approval_id>.response.json``

When running inside a ChaseOS vault, GreyTheory defers to those records rather
than keeping its own parallel set.

The adapter reads ChaseOS's *filesystem* contract rather than importing it.
That keeps this package dependency-free, lets it run with no ChaseOS present at
all, and means a ChaseOS refactor breaks a test here rather than the runtime.
"""

# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 ChaseInTech

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

DEFAULT_APPROVAL_MAX_AGE = timedelta(hours=8)
"""How long an operator decision stays good for. A working session, not a week."""


@dataclass(frozen=True)
class Approval:
    """One recorded operator decision."""

    approval_id: str
    decision: str
    """``APPROVE`` or ``DENY`` — ChaseOS's vocabulary, kept verbatim."""

    operator_id: str
    responded_at: datetime
    action_type: str = ""
    target: str = ""
    note: str = ""
    source: str = "unknown"
    """Where this was read from, for the audit record."""

    @property
    def granted(self) -> bool:
        return self.decision.strip().upper() == "APPROVE"

    def is_expired(self, *, now: datetime, max_age: timedelta) -> bool:
        return (now - self.responded_at) > max_age

    def covers(self, *, action_type: str, target: str) -> bool:
        """Whether this approval authorises this specific action on this target.

        An empty ``action_type`` or ``target`` on the approval means it was not
        bound to one, and an unbound approval is treated as covering nothing.
        Fail-closed applies here as everywhere: a vague approval is not a
        general one.
        """
        if not self.action_type or not self.target:
            return False
        return (
            self.action_type.strip().lower() == action_type.strip().lower()
            and self.target.strip().lower() == target.strip().lower()
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "approval_id": self.approval_id,
            "decision": self.decision,
            "operator_id": self.operator_id,
            "responded_at": self.responded_at.isoformat(),
            "action_type": self.action_type,
            "target": self.target,
            "note": self.note,
            "source": self.source,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Approval:
        return cls(
            approval_id=data["approval_id"],
            decision=data["decision"],
            operator_id=data.get("operator_id", ""),
            responded_at=_parse_timestamp(data["responded_at"]),
            action_type=data.get("action_type", ""),
            target=data.get("target", ""),
            note=data.get("note", ""),
            source=data.get("source", "unknown"),
        )


@runtime_checkable
class ApprovalStore(Protocol):
    """Anything that can resolve an approval id to a decision."""

    def lookup(self, approval_id: str) -> Approval | None: ...


def _parse_timestamp(value: Any) -> datetime:
    if isinstance(value, datetime):
        parsed = value
    else:
        text = str(value or "").strip().replace("Z", "+00:00")
        parsed = datetime.fromisoformat(text)
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


class ChaseOSApprovalStore:
    """Reads ChaseOS OSRIL approval responses.

    Args:
        vault_root: The ChaseOS vault root. Responses are expected at
            ``<vault_root>/runtime/osril/approvals/<id>.response.json``, which is
            the path ``runtime/osril/approvals.py`` writes to.
    """

    RELATIVE_PATH = Path("runtime") / "osril" / "approvals"

    def __init__(self, vault_root: str | Path):
        self.vault_root = Path(vault_root)

    @property
    def approvals_dir(self) -> Path:
        return self.vault_root / self.RELATIVE_PATH

    def lookup(self, approval_id: str) -> Approval | None:
        # Reject anything that could climb out of the approvals directory. The
        # id reaches us from a request, so it is untrusted input.
        if not approval_id or not approval_id.replace("_", "").replace("-", "").replace(
            ".", ""
        ).isalnum():
            return None

        path = self.approvals_dir / f"{approval_id}.response.json"
        if not path.is_file():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return None
        if not isinstance(data, dict):
            return None

        try:
            responded_at = _parse_timestamp(data.get("responded_at"))
        except ValueError:
            return None

        return Approval(
            approval_id=str(data.get("approval_id", approval_id)),
            decision=str(data.get("decision", "")),
            operator_id=str(data.get("operator_id", "")),
            responded_at=responded_at,
            action_type=str(data.get("action_type", "")),
            target=str(data.get("target", "")),
            note=str(data.get("operator_note", "")),
            source="chaseos_osril",
        )


class LocalApprovalStore:
    """The standalone store. Complete on its own; no external system required.

    This is the default for anyone running GreyTheory outside a wider agent
    platform, and it is a first-class implementation rather than a stub — the
    gate enforces binding, expiry and single-use identically whichever store
    is in play.

    Approvals live in memory for the process lifetime. Callers that need them
    to survive a restart can persist and rehydrate via
    :meth:`to_dict` / :meth:`from_dict`.
    """

    def __init__(self, approvals: dict[str, Approval] | None = None):
        self._approvals: dict[str, Approval] = dict(approvals or {})

    def grant(
        self,
        *,
        approval_id: str,
        operator_id: str,
        action_type: str,
        target: str,
        responded_at: datetime | None = None,
        note: str = "",
    ) -> Approval:
        approval = Approval(
            approval_id=approval_id,
            decision="APPROVE",
            operator_id=operator_id,
            responded_at=responded_at or datetime.now(timezone.utc),
            action_type=action_type,
            target=target,
            note=note,
            source="local",
        )
        self._approvals[approval_id] = approval
        return approval

    def deny(
        self,
        *,
        approval_id: str,
        operator_id: str,
        action_type: str = "",
        target: str = "",
        responded_at: datetime | None = None,
        note: str = "",
    ) -> Approval:
        approval = Approval(
            approval_id=approval_id,
            decision="DENY",
            operator_id=operator_id,
            responded_at=responded_at or datetime.now(timezone.utc),
            action_type=action_type,
            target=target,
            note=note,
            source="local",
        )
        self._approvals[approval_id] = approval
        return approval

    def lookup(self, approval_id: str) -> Approval | None:
        return self._approvals.get(approval_id)

    def to_dict(self) -> dict[str, Any]:
        """Serialisable snapshot, for callers that need approvals to persist."""
        return {
            approval_id: approval.to_dict()
            for approval_id, approval in self._approvals.items()
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> LocalApprovalStore:
        return cls(
            {
                approval_id: Approval.from_dict(payload)
                for approval_id, payload in data.items()
            }
        )


__all__ = [
    "DEFAULT_APPROVAL_MAX_AGE",
    "Approval",
    "ApprovalStore",
    "ChaseOSApprovalStore",
    "LocalApprovalStore",
]
