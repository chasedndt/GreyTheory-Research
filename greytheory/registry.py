"""The programme registry — scope over time, not scope once.

The compiler answers "what do these rules mean today". This module answers the
harder question: *what changed since you last looked, and does your permission
still hold?*

Programmes edit their scope without announcing it. An asset moves out of scope,
a technique gets excluded, a rate limit tightens, the programme pauses. A
researcher who read the rules in March and is still testing in August is
operating on a permission that may no longer exist — the "scope amnesia"
failure, and one of the few that can turn authorised research into an incident.

So the registry enforces one rule above all others:

**Re-registering a programme whose source has changed invalidates the human
review.** The new version starts at ``PENDING_REVIEW`` however thoroughly the
previous one was verified. Review attaches to the *text a person actually
read*, not to the programme in the abstract.

Contracts are never edited. Each registration is a new version, and every
version keeps a snapshot of the exact source it came from, so a later dispute
about what the rules said has an answer.
"""

# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 ChaseInTech

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable

from greytheory.audit import AuditLog
from greytheory.authority.compiler import compile_contract, mark_reviewed, source_hash
from greytheory.authority.gate import DEFAULT_MAX_CONTRACT_AGE
from greytheory.authority.scope import AssetPattern, ContractStatus, ScopeContract
from greytheory.evidence import find_repository_root

SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")


class RegistryError(Exception):
    """Raised when a registry operation would be unsafe or unsound."""


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _validate_id(value: str) -> str:
    text = str(value or "").strip()
    if not SAFE_ID.fullmatch(text):
        raise RegistryError(f"programme id {value!r} is not a safe identifier")
    return text


@dataclass(frozen=True)
class ScopeDiff:
    """What changed between two versions of a programme's scope."""

    added_in_scope: list[str] = field(default_factory=list)
    removed_in_scope: list[str] = field(default_factory=list)
    added_out_of_scope: list[str] = field(default_factory=list)
    removed_out_of_scope: list[str] = field(default_factory=list)
    added_prohibitions: list[str] = field(default_factory=list)
    removed_prohibitions: list[str] = field(default_factory=list)
    authority_change: tuple[str, str] | None = None
    rate_limit_change: tuple[float | None, float | None] | None = None

    @property
    def changed(self) -> bool:
        return any(
            [
                self.added_in_scope,
                self.removed_in_scope,
                self.added_out_of_scope,
                self.removed_out_of_scope,
                self.added_prohibitions,
                self.removed_prohibitions,
                self.authority_change,
                self.rate_limit_change,
            ]
        )

    @property
    def is_narrowing(self) -> bool:
        """Did permission shrink?

        This is the direction that matters. A widened scope is an opportunity;
        a narrowed one means work already done may have been against an asset
        that is no longer authorised, and that needs looking at rather than
        noting.
        """
        return bool(
            self.removed_in_scope
            or self.added_out_of_scope
            or self.added_prohibitions
            or (self.authority_change and _authority_rank(self.authority_change[1])
                < _authority_rank(self.authority_change[0]))
        )

    def summary(self) -> list[str]:
        lines: list[str] = []
        for label, items in (
            ("no longer in scope", self.removed_in_scope),
            ("newly excluded", self.added_out_of_scope),
            ("newly prohibited", self.added_prohibitions),
            ("newly in scope", self.added_in_scope),
            ("no longer excluded", self.removed_out_of_scope),
            ("no longer prohibited", self.removed_prohibitions),
        ):
            if items:
                lines.append(f"{label}: {', '.join(sorted(items))}")
        if self.authority_change:
            lines.append(
                f"granted authority {self.authority_change[0]} -> "
                f"{self.authority_change[1]}"
            )
        if self.rate_limit_change:
            lines.append(
                f"rate limit {self.rate_limit_change[0]} -> "
                f"{self.rate_limit_change[1]}"
            )
        return lines

    def to_dict(self) -> dict[str, Any]:
        return {
            "changed": self.changed,
            "is_narrowing": self.is_narrowing,
            "summary": self.summary(),
        }


_AUTHORITY_ORDER = ["NONE", "LOCAL_FIXTURE", "PASSIVE_HTTP", "AUTHENTICATED", "INTRUSIVE"]


def _authority_rank(name: str) -> int:
    try:
        return _AUTHORITY_ORDER.index(str(name).upper())
    except ValueError:
        return 0


def diff_contracts(before: ScopeContract, after: ScopeContract) -> ScopeDiff:
    """Compare two contracts. Patterns are compared by value, not identity."""

    def values(patterns: list[AssetPattern]) -> set[str]:
        return {f"{p.type.value}:{p.value.lower()}" for p in patterns}

    before_in, after_in = values(before.assets_in_scope), values(after.assets_in_scope)
    before_out = values(before.assets_out_of_scope)
    after_out = values(after.assets_out_of_scope)
    before_pro = {t.lower() for t in before.prohibited_techniques}
    after_pro = {t.lower() for t in after.prohibited_techniques}

    return ScopeDiff(
        added_in_scope=sorted(after_in - before_in),
        removed_in_scope=sorted(before_in - after_in),
        added_out_of_scope=sorted(after_out - before_out),
        removed_out_of_scope=sorted(before_out - after_out),
        added_prohibitions=sorted(after_pro - before_pro),
        removed_prohibitions=sorted(before_pro - after_pro),
        authority_change=(
            (before.max_authority, after.max_authority)
            if before.max_authority != after.max_authority
            else None
        ),
        rate_limit_change=(
            (before.rate_limit_rps, after.rate_limit_rps)
            if before.rate_limit_rps != after.rate_limit_rps
            else None
        ),
    )


@dataclass(frozen=True)
class ContractVersion:
    version: int
    contract: ScopeContract
    source_hash: str
    registered_at: datetime

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "source_hash": self.source_hash,
            "registered_at": self.registered_at.isoformat(),
            "contract": self.contract.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ContractVersion:
        registered_at = datetime.fromisoformat(data["registered_at"])
        if registered_at.tzinfo is None:
            registered_at = registered_at.replace(tzinfo=timezone.utc)
        return cls(
            version=data["version"],
            contract=ScopeContract.from_dict(data["contract"]),
            source_hash=data["source_hash"],
            registered_at=registered_at,
        )


@dataclass
class RegistrationResult:
    version: ContractVersion
    is_new_programme: bool
    source_changed: bool
    diff: ScopeDiff | None
    """``None`` on a first registration; otherwise the change from the previous
    version, even when the source text was identical."""

    @property
    def requires_review(self) -> bool:
        return not self.version.contract.human_reviewed

    @property
    def blocked(self) -> bool:
        return self.version.contract.status is ContractStatus.BLOCKED


@dataclass(frozen=True)
class Attention:
    """One reason a programme needs the operator before it is used again."""

    programme_id: str
    reason: str
    detail: str

    def to_dict(self) -> dict[str, str]:
        return {
            "programme_id": self.programme_id,
            "reason": self.reason,
            "detail": self.detail,
        }


class ProgrammeRegistry:
    """Versioned programme records, compiled contracts and source snapshots.

    Args:
        root: Where records live. Contracts are meant to be versioned, so a
            repository path is normally correct — but see
            ``allow_confidential_in_repository``.
        audit: Every registration and review is recorded.
        allow_confidential_in_repository: Permit storing a programme marked
            ``confidential`` inside a git working tree. Off by default. Private
            programme scope is usually covered by an NDA, and committing it is
            the kind of disclosure that ends programme access.
        clock: Injected for testability.
    """

    def __init__(
        self,
        root: str | Path,
        *,
        audit: AuditLog | None = None,
        allow_confidential_in_repository: bool = False,
        clock: Callable[[], datetime] = _utcnow,
    ):
        self.root = Path(root)
        self._audit = audit
        self._allow_confidential_in_repo = allow_confidential_in_repository
        self._clock = clock
        self.root.mkdir(parents=True, exist_ok=True)

    def _dir(self, programme_id: str) -> Path:
        return self.root / _validate_id(programme_id)

    def _version_path(self, programme_id: str, version: int) -> Path:
        return self._dir(programme_id) / f"v{version}.json"

    def _source_path(self, programme_id: str, version: int) -> Path:
        return self._dir(programme_id) / "source" / f"v{version}.txt"

    def programmes(self) -> list[str]:
        return sorted(
            path.name for path in self.root.iterdir() if path.is_dir()
        ) if self.root.is_dir() else []

    def versions(self, programme_id: str) -> list[ContractVersion]:
        directory = self._dir(programme_id)
        if not directory.is_dir():
            return []
        found: list[ContractVersion] = []
        for path in directory.glob("v*.json"):
            found.append(
                ContractVersion.from_dict(json.loads(path.read_text(encoding="utf-8")))
            )
        return sorted(found, key=lambda v: v.version)

    def latest(self, programme_id: str) -> ContractVersion | None:
        versions = self.versions(programme_id)
        return versions[-1] if versions else None

    def current_contract(self, programme_id: str) -> ScopeContract | None:
        """The latest contract, whatever state it is in.

        Deliberately not filtered to verified contracts — the gate decides
        whether a contract grants anything, and hiding an unusable contract
        here would just move that judgement somewhere less careful.
        """
        version = self.latest(programme_id)
        return version.contract if version else None

    def source(self, programme_id: str, version: int) -> str:
        path = self._source_path(programme_id, version)
        if not path.is_file():
            raise RegistryError(
                f"no source snapshot for {programme_id!r} v{version}"
            )
        return path.read_text(encoding="utf-8")

    def register(
        self, programme: dict[str, Any], *, raw_source: str
    ) -> RegistrationResult:
        """Compile and store a new version of a programme.

        A raw source snapshot is required. Registering without the text the
        rules came from would leave nothing to compare against later, which is
        the whole point of the registry.
        """
        if not raw_source or not raw_source.strip():
            raise RegistryError(
                "a source snapshot is required; without the text the rules came "
                "from there is nothing to detect drift against"
            )

        programme_id = _validate_id(str(programme.get("id") or ""))

        if programme.get("confidential") and not self._allow_confidential_in_repo:
            repository = find_repository_root(self.root)
            if repository is not None:
                raise RegistryError(
                    f"refusing to store confidential programme {programme_id!r} at "
                    f"{self.root} — it is inside the git working tree at "
                    f"{repository}. Private programme scope is usually covered by "
                    "an NDA. Use a path outside the repository, or a gitignored "
                    "one, or pass allow_confidential_in_repository=True."
                )

        previous = self.latest(programme_id)
        incoming_hash = source_hash(raw_source)
        result = compile_contract(programme, raw_source=raw_source, now=self._clock())
        contract = result.contract

        # The rule that carries this module: review attaches to the text a
        # person actually read. Different text, no review.
        source_changed = previous is not None and previous.source_hash != incoming_hash
        if previous is not None and not source_changed:
            # Identical source. Carry the earlier review forward rather than
            # making the operator re-read text they have already read.
            if previous.contract.human_reviewed and not result.blocked:
                mark_reviewed(contract, reviewer=f"carried from v{previous.version}")

        version_number = 1 if previous is None else previous.version + 1
        version = ContractVersion(
            version=version_number,
            contract=contract,
            source_hash=incoming_hash,
            registered_at=self._clock(),
        )

        directory = self._dir(programme_id)
        (directory / "source").mkdir(parents=True, exist_ok=True)
        self._version_path(programme_id, version_number).write_text(
            json.dumps(version.to_dict(), indent=2), encoding="utf-8"
        )
        self._source_path(programme_id, version_number).write_text(
            raw_source, encoding="utf-8"
        )

        diff = (
            diff_contracts(previous.contract, contract) if previous is not None else None
        )

        if self._audit is not None:
            self._audit.append(
                actor="programme_registry",
                action="programme.register",
                authority_ref=contract.fingerprint(),
                detail={
                    "programme_id": programme_id,
                    "version": version_number,
                    "status": contract.status.value,
                    "source_changed": source_changed,
                    "ambiguities": contract.ambiguities,
                    "diff": diff.to_dict() if diff else None,
                },
            )

        return RegistrationResult(
            version=version,
            is_new_programme=previous is None,
            source_changed=source_changed,
            diff=diff,
        )

    def review(self, programme_id: str, *, reviewer: str) -> ScopeContract:
        """Human-review the latest version into VERIFIED."""
        version = self.latest(programme_id)
        if version is None:
            raise RegistryError(f"no programme {programme_id!r} registered")

        contract = version.contract
        if contract.human_reviewed:
            raise RegistryError(
                f"{programme_id!r} v{version.version} is already reviewed"
            )
        mark_reviewed(contract, reviewer=reviewer)

        self._version_path(programme_id, version.version).write_text(
            json.dumps(version.to_dict(), indent=2), encoding="utf-8"
        )
        if self._audit is not None:
            self._audit.append(
                actor=reviewer,
                action="programme.review",
                authority_ref=contract.fingerprint(),
                detail={"programme_id": programme_id, "version": version.version},
            )
        return contract

    def diff_versions(self, programme_id: str, a: int, b: int) -> ScopeDiff:
        by_number = {v.version: v for v in self.versions(programme_id)}
        for number in (a, b):
            if number not in by_number:
                raise RegistryError(f"{programme_id!r} has no version {number}")
        return diff_contracts(by_number[a].contract, by_number[b].contract)

    def needs_attention(
        self, *, max_age: timedelta = DEFAULT_MAX_CONTRACT_AGE
    ) -> list[Attention]:
        """Everything the operator should deal with before testing anything.

        This is the registry's real output. A list of programmes is inert; a
        list of *reasons the permissions might not hold any more* is the thing
        that prevents scope amnesia.
        """
        now = self._clock()
        items: list[Attention] = []

        for programme_id in self.programmes():
            version = self.latest(programme_id)
            if version is None:
                continue
            contract = version.contract

            if contract.status is ContractStatus.BLOCKED:
                items.append(
                    Attention(
                        programme_id,
                        "blocked",
                        f"v{version.version} blocked by {len(contract.ambiguities)} "
                        f"ambiguity/ies: {'; '.join(contract.ambiguities[:2])}",
                    )
                )
                continue

            if not contract.human_reviewed:
                items.append(
                    Attention(
                        programme_id,
                        "awaiting_review",
                        f"v{version.version} compiled clean but nobody has reviewed it; "
                        "it grants nothing until they do",
                    )
                )
                continue

            if contract.is_stale(now=now, max_age=max_age):
                age = now - contract.verified_at
                items.append(
                    Attention(
                        programme_id,
                        "stale",
                        f"last verified {age.days}d ago, beyond the {max_age.days}d "
                        "window; re-read the programme before testing",
                    )
                )

        return items


__all__ = [
    "Attention",
    "ContractVersion",
    "ProgrammeRegistry",
    "RegistrationResult",
    "RegistryError",
    "ScopeDiff",
    "diff_contracts",
]
