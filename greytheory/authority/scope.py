"""The ScopeContract — authorisation as a runtime object rather than prose.

A programme's rules are only useful to a machine once they are a thing that can
be checked, versioned, hashed and expired. That is what this module builds.

Two rules do most of the work, and both come from `Docs/definition.md` section 2:

* **Out-of-scope beats in-scope** on every match. Overlap resolves to denial.
* **Derived assets are not inherited.** An asset found *through* an in-scope
  asset is out of scope until it independently satisfies the contract.
"""

# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 ChaseInTech

from __future__ import annotations

import hashlib
import ipaddress
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any


class PatternType(str, Enum):
    EXACT = "exact"
    WILDCARD = "wildcard"
    CIDR = "cidr"


class ScopeClassification(str, Enum):
    """The result of asking a contract about one asset."""

    IN_SCOPE = "in_scope"
    OUT_OF_SCOPE = "out_of_scope"
    UNRESOLVED = "unresolved"
    """Matched nothing. Under I3 this is a denial, not a maybe."""


class ContractStatus(str, Enum):
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    """Compiled cleanly but not yet reviewed by a human. Still blocks execution."""

    VERIFIED = "verified"
    BLOCKED = "blocked"
    """Ambiguous, conflicting, incomplete, or explicitly paused."""


class PatternError(ValueError):
    """Raised when a scope pattern cannot be parsed. Never silently skipped."""


@dataclass(frozen=True)
class AssetPattern:
    """One line of a scope table."""

    type: PatternType
    value: str
    note: str = ""

    def __post_init__(self) -> None:
        if not self.value.strip():
            raise PatternError("empty scope pattern")
        if self.type is PatternType.CIDR:
            try:
                ipaddress.ip_network(self.value, strict=False)
            except ValueError as exc:
                raise PatternError(f"invalid CIDR {self.value!r}: {exc}") from exc
        if self.type is PatternType.WILDCARD and not self.value.startswith("*."):
            raise PatternError(
                f"wildcard pattern {self.value!r} must start with '*.'"
            )

    def matches(self, asset: str) -> bool:
        asset = asset.strip().lower()
        if not asset:
            return False
        value = self.value.strip().lower()

        if self.type is PatternType.EXACT:
            return asset == value

        if self.type is PatternType.WILDCARD:
            # '*.example.com' covers subdomains at any depth, but not the apex.
            # The apex must be listed explicitly if it is in scope.
            suffix = value[1:]  # '.example.com'
            return asset.endswith(suffix) and len(asset) > len(suffix)

        if self.type is PatternType.CIDR:
            try:
                address = ipaddress.ip_address(asset)
            except ValueError:
                return False  # a hostname is not an address; resolution is not our job
            return address in ipaddress.ip_network(value, strict=False)

        return False

    def to_dict(self) -> dict[str, Any]:
        return {"type": self.type.value, "value": self.value, "note": self.note}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AssetPattern:
        return cls(
            type=PatternType(data["type"]),
            value=data["value"],
            note=data.get("note", ""),
        )


@dataclass
class ScopeContract:
    """A compiled, checkable authorisation.

    ``ambiguities`` is deliberately part of the object rather than a compiler
    side effect: a contract carries the reasons it cannot be trusted, so nothing
    downstream has to go looking for them.
    """

    id: str
    programme_id: str
    verified_at: datetime
    status: ContractStatus = ContractStatus.DRAFT
    assets_in_scope: list[AssetPattern] = field(default_factory=list)
    assets_out_of_scope: list[AssetPattern] = field(default_factory=list)
    prohibited_techniques: list[str] = field(default_factory=list)
    max_authority: str = "LOCAL_FIXTURE"
    """Highest authority level this contract grants, by name. Compared against
    :class:`~greytheory.authority.gate.AuthorityLevel` at the gate."""

    rate_limit_rps: float | None = None
    ambiguities: list[str] = field(default_factory=list)
    source_hashes: list[str] = field(default_factory=list)
    human_reviewed: bool = False
    notes: str = ""

    def classify(self, asset: str) -> ScopeClassification:
        """Classify one asset. Out-of-scope wins; no match is not a pass."""
        if any(pattern.matches(asset) for pattern in self.assets_out_of_scope):
            return ScopeClassification.OUT_OF_SCOPE
        if any(pattern.matches(asset) for pattern in self.assets_in_scope):
            return ScopeClassification.IN_SCOPE
        return ScopeClassification.UNRESOLVED

    def is_stale(self, *, now: datetime, max_age: timedelta) -> bool:
        """Scope changes. A contract verified long enough ago is not evidence
        of anything, regardless of what it says."""
        return (now - self.verified_at) > max_age

    def prohibits(self, technique: str | None) -> bool:
        if not technique:
            return False
        needle = technique.strip().lower()
        return any(item.strip().lower() == needle for item in self.prohibited_techniques)

    def fingerprint(self) -> str:
        """Stable identifier for this contract's substantive content.

        Changes whenever scope, exclusions, prohibitions or granted authority
        change — so a programme edit produces a visibly different contract even
        if the id is reused.
        """
        material = "|".join(
            [
                self.programme_id,
                ";".join(sorted(p.value for p in self.assets_in_scope)),
                ";".join(sorted(p.value for p in self.assets_out_of_scope)),
                ";".join(sorted(self.prohibited_techniques)),
                self.max_authority,
            ]
        )
        return hashlib.sha256(material.encode("utf-8")).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "programme_id": self.programme_id,
            "verified_at": self.verified_at.isoformat(),
            "status": self.status.value,
            "assets_in_scope": [p.to_dict() for p in self.assets_in_scope],
            "assets_out_of_scope": [p.to_dict() for p in self.assets_out_of_scope],
            "prohibited_techniques": list(self.prohibited_techniques),
            "max_authority": self.max_authority,
            "rate_limit_rps": self.rate_limit_rps,
            "ambiguities": list(self.ambiguities),
            "source_hashes": list(self.source_hashes),
            "human_reviewed": self.human_reviewed,
            "notes": self.notes,
            "fingerprint": self.fingerprint(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ScopeContract:
        verified_at = data["verified_at"]
        if isinstance(verified_at, str):
            verified_at = datetime.fromisoformat(verified_at)
        if verified_at.tzinfo is None:
            verified_at = verified_at.replace(tzinfo=timezone.utc)
        return cls(
            id=data["id"],
            programme_id=data["programme_id"],
            verified_at=verified_at,
            status=ContractStatus(data.get("status", "draft")),
            assets_in_scope=[
                AssetPattern.from_dict(p) for p in data.get("assets_in_scope", [])
            ],
            assets_out_of_scope=[
                AssetPattern.from_dict(p) for p in data.get("assets_out_of_scope", [])
            ],
            prohibited_techniques=list(data.get("prohibited_techniques", [])),
            max_authority=data.get("max_authority", "LOCAL_FIXTURE"),
            rate_limit_rps=data.get("rate_limit_rps"),
            ambiguities=list(data.get("ambiguities", [])),
            source_hashes=list(data.get("source_hashes", [])),
            human_reviewed=bool(data.get("human_reviewed", False)),
            notes=data.get("notes", ""),
        )
