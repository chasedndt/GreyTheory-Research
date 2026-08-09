"""The lane contract — what a collector is, and what it is forbidden to be.

A lane observes. That is the whole of its job.

The temptation with a detection layer is to let it conclude: a version match
becomes "vulnerable", a matched pattern becomes "a leaked secret". Every one of
those promotions is a judgement made by something that cannot see the product,
the impact, or the programme's rules — and once a lane can conclude, the rest
of the system is downstream of its optimism.

So two limits are structural rather than advisory:

**A lane cannot promote past ``contextual``.** :class:`RawSignal` has no field
for a higher taxonomy level. Promotion is the Judgement Plane's job.

**A lane cannot reach anything except through a granted Decision.** Collectors
never receive a path or a hostname directly; they receive a
:class:`LaneContext` built from an allow, and every read goes through it.

A lane *may* produce a ``checked`` claim, because a deterministic test that
could have failed is proof of what it tested — "this version string is inside
this advisory's affected range" is a fact. What it is not is a vulnerability.
"""

# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 ChaseInTech

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Protocol, Sequence, runtime_checkable

from greytheory.authority.gate import AuthorityLevel
from greytheory.findings import Finding, Taxonomy
from greytheory.provenance import Claim, Tag


class SignalLevel(str, Enum):
    """The only two levels a collector may assign.

    There is deliberately no ``candidate`` here. A lane that could emit one
    would be deciding that something is worth a human's time, which is exactly
    the judgement it is not equipped to make.
    """

    INFORMATIONAL = "informational"
    CONTEXTUAL = "contextual"

    def to_taxonomy(self) -> Taxonomy:
        return Taxonomy(self.value)


@dataclass(frozen=True)
class LaneSpec:
    """What a lane is and what it needs before it may run."""

    id: str
    lane: int
    """1 known-vuln, 2 exposure, 3 web, 4 AI-app."""

    title: str
    requires_authority: AuthorityLevel
    network: bool = False
    """Whether the collector performs network I/O.

    Network lanes cannot live in this package and the runner refuses them. The
    core stays offline by construction, not by convention.
    """

    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "lane": self.lane,
            "title": self.title,
            "requires_authority": self.requires_authority.name,
            "network": self.network,
            "description": self.description,
        }


@dataclass(frozen=True)
class RawSignal:
    """One observation. Not a finding, and never more than ``contextual``."""

    id: str
    lane: int
    asset: str
    kind: str
    title: str
    level: SignalLevel
    claims: list[Claim] = field(default_factory=list)
    detail: dict[str, Any] = field(default_factory=dict)
    authority_ref: str = ""
    """Stamped by the runner from the Decision that permitted the collection."""

    observed_at: datetime | None = None

    @property
    def proven_claims(self) -> list[Claim]:
        return [c for c in self.claims if c.is_proven]

    def to_finding(self, finding_id: str) -> Finding:
        """Lift into a Finding at the level the lane assigned. No higher.

        The finding starts where the signal did. Anything above that has to be
        earned through the validation gates.
        """
        if not self.authority_ref:
            raise ValueError(
                "signal has no authority reference; it was not produced through "
                "a granted Decision (I2)"
            )
        finding = Finding(
            id=finding_id,
            title=self.title,
            lane=self.lane,
            target=self.asset,
            authority_ref=self.authority_ref,
        )
        finding.claims.extend(self.claims)
        if self.level is SignalLevel.CONTEXTUAL:
            finding.advance(Taxonomy.CONTEXTUAL, actor=f"lane:{self.lane}")
        return finding

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "lane": self.lane,
            "asset": self.asset,
            "kind": self.kind,
            "title": self.title,
            "level": self.level.value,
            "claims": [c.to_dict() for c in self.claims],
            "detail": dict(self.detail),
            "authority_ref": self.authority_ref,
            "observed_at": self.observed_at.isoformat() if self.observed_at else None,
        }


class LaneContextError(Exception):
    """Raised when a collector reaches outside what it was granted."""


class LaneContext:
    """The only thing a collector is handed. Every read is bounded by it.

    A collector never sees a raw path. It sees this, built from an allow, rooted
    at one directory, and every read is checked against that root — so a lane
    that tries to wander cannot, even by accident, and a lane with a traversal
    bug fails loudly instead of quietly widening its own scope.
    """

    def __init__(
        self,
        *,
        asset: str,
        root: str | Path,
        authority_ref: str,
        clock=lambda: datetime.now(timezone.utc),
    ):
        self.asset = asset
        self.root = Path(root).resolve()
        self.authority_ref = authority_ref
        self._clock = clock
        if not self.root.is_dir():
            raise LaneContextError(f"lane root {self.root} is not a directory")

    def now(self) -> datetime:
        return self._clock()

    def _resolve(self, relative: str | Path) -> Path:
        candidate = (self.root / Path(relative)).resolve()
        if candidate != self.root and self.root not in candidate.parents:
            raise LaneContextError(
                f"{relative!r} resolves outside the granted root {self.root}; "
                "a lane may only read what it was authorised to read"
            )
        return candidate

    def exists(self, relative: str | Path) -> bool:
        return self._resolve(relative).exists()

    def read_text(self, relative: str | Path) -> str:
        path = self._resolve(relative)
        if not path.is_file():
            raise LaneContextError(f"{relative!r} is not a readable file")
        return path.read_text(encoding="utf-8", errors="replace")

    def read_bytes(self, relative: str | Path) -> bytes:
        path = self._resolve(relative)
        if not path.is_file():
            raise LaneContextError(f"{relative!r} is not a readable file")
        return path.read_bytes()

    def iter_files(self, pattern: str = "**/*") -> list[Path]:
        """Paths relative to the root, so a collector cannot leak absolutes."""
        return sorted(
            path.relative_to(self.root)
            for path in self.root.glob(pattern)
            if path.is_file()
        )


@runtime_checkable
class Lane(Protocol):
    """A collector. Observes, emits, concludes nothing."""

    spec: LaneSpec

    def collect(self, context: LaneContext) -> Sequence[RawSignal]: ...


def observed(text: str, source: str) -> Claim:
    return Claim(text=text, tag=Tag.OBSERVED, source=source)


def checked(text: str, source: str, check_ref: str) -> Claim:
    """Legacy origin path for deterministic static-collector results.

    This does not promote an observed or inferred claim. New promotion paths
    must consume a registry-issued CheckReceipt; migrate collectors to persisted
    receipts when their artifact contract is introduced.
    """
    return Claim(text=text, tag=Tag.CHECKED, source=source, check_ref=check_ref)


__all__ = [
    "Lane",
    "LaneContext",
    "LaneContextError",
    "LaneSpec",
    "RawSignal",
    "SignalLevel",
    "checked",
    "observed",
]
