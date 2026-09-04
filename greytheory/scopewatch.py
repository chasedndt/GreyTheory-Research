"""Scope Watch — noticing that a programme changed, without being told.

The registry already does the hard half: re-register a bundle and it detects
that the source text differs, invalidates the human review, and diffs the
resulting scope. What it cannot do is notice on its own. Somebody has to go and
look.

This module is the watching. It takes the sources a bundle was compiled from,
re-reads them through a fetcher, and reports what changed — with the same
narrowing-versus-widening distinction the registry applies, because only one of
those directions means work already done may no longer be authorised.

**The fetcher is a protocol, and the core ships only a local one.** Reading a
programme page over the network is a network action; it belongs outside
``greytheory/`` and above ``LOCAL_FIXTURE``. What lives here is everything that
happens *after* the bytes arrive, which is all of the logic and none of the
risk. When the posture is raised, an HTTP fetcher is written against this
protocol and nothing in this file changes.

**Nothing here interprets text as permission.** A change is a reason to
re-compile and re-review. It is never itself a grant, and Scope Watch has no
path to `VERIFIED`.
"""

# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 ChaseInTech

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Protocol, runtime_checkable

from greytheory.audit import AuditLog


class WatchError(Exception):
    """Raised when a watch operation would be unsound."""


class SourceState(str, Enum):
    UNCHANGED = "unchanged"
    CHANGED = "changed"
    UNREACHABLE = "unreachable"
    """The source could not be re-read.

    Deliberately not ``unchanged``. A source that cannot be checked is not a
    source that has stayed the same, and treating the two alike is how a
    silently-removed programme page reads as business as usual.
    """

    NEW = "new"
    """Present now, absent from the recorded bundle."""

    GONE = "gone"
    """Recorded in the bundle, absent now. Often a retired programme."""


@runtime_checkable
class SourceFetcher(Protocol):
    """Re-reads one recorded source. The only part that ever needs a network."""

    fetcher_id: str
    network: bool

    def fetch(self, locator: str) -> bytes: ...


class LocalSourceFetcher:
    """Reads saved source files. Offline, and the only fetcher in the core.

    Rooted, like :class:`~greytheory.signal.contract.LaneContext`, so a locator
    from a recorded bundle cannot walk out of the directory it was captured in.
    """

    fetcher_id = "local.files"
    network = False

    def __init__(self, root: str | Path):
        self.root = Path(root).resolve()
        if not self.root.is_dir():
            raise WatchError(f"source root {self.root} is not a directory")

    def fetch(self, locator: str) -> bytes:
        candidate = (self.root / locator).resolve()
        if candidate != self.root and self.root not in candidate.parents:
            raise WatchError(
                f"{locator!r} resolves outside the source root {self.root}"
            )
        if not candidate.is_file():
            raise FileNotFoundError(locator)
        return candidate.read_bytes()


def digest(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


@dataclass(frozen=True)
class WatchedSource:
    """One source as the bundle recorded it."""

    source_id: str
    locator: str
    recorded_hash: str
    kind: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "locator": self.locator,
            "recorded_hash": self.recorded_hash,
            "kind": self.kind,
        }


@dataclass(frozen=True)
class SourceObservation:
    source_id: str
    state: SourceState
    recorded_hash: str = ""
    observed_hash: str = ""
    error: str = ""

    @property
    def needs_attention(self) -> bool:
        return self.state is not SourceState.UNCHANGED

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "state": self.state.value,
            "recorded_hash": self.recorded_hash,
            "observed_hash": self.observed_hash,
            "error": self.error,
        }


@dataclass
class WatchResult:
    programme_id: str
    checked_at: datetime
    fetcher_id: str
    observations: list[SourceObservation] = field(default_factory=list)

    @property
    def changed(self) -> list[SourceObservation]:
        return [o for o in self.observations if o.state is SourceState.CHANGED]

    @property
    def unreachable(self) -> list[SourceObservation]:
        return [o for o in self.observations if o.state is SourceState.UNREACHABLE]

    @property
    def gone(self) -> list[SourceObservation]:
        return [o for o in self.observations if o.state is SourceState.GONE]

    @property
    def review_invalidated(self) -> bool:
        """Whether the human review no longer applies.

        Any change or disappearance invalidates it. Review attaches to the text
        a person actually read, and that text is no longer what is there.
        """
        return bool(self.changed or self.gone)

    @property
    def needs_attention(self) -> list[SourceObservation]:
        return [o for o in self.observations if o.needs_attention]

    def summary(self) -> list[str]:
        lines: list[str] = []
        for label, items in (
            ("changed since capture", self.changed),
            ("no longer present", self.gone),
            ("could not be re-read", self.unreachable),
            (
                "new since capture",
                [o for o in self.observations if o.state is SourceState.NEW],
            ),
        ):
            if items:
                lines.append(
                    f"{label}: {', '.join(sorted(o.source_id for o in items))}"
                )
        return lines

    def to_dict(self) -> dict[str, Any]:
        return {
            "programme_id": self.programme_id,
            "checked_at": self.checked_at.isoformat(),
            "fetcher_id": self.fetcher_id,
            "review_invalidated": self.review_invalidated,
            "summary": self.summary(),
            "observations": [o.to_dict() for o in self.observations],
        }


class ScopeWatch:
    """Re-reads recorded sources and reports what moved.

    Args:
        fetcher: The exact rooted :class:`LocalSourceFetcher` shipped by the
            core. External adapters must capture source bytes outside the core
            and hand the resulting local evidence inward.
        audit: Every watch run is recorded, including unreachable sources.
    """

    def __init__(
        self,
        fetcher: LocalSourceFetcher,
        *,
        audit: AuditLog | None = None,
        clock: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
    ):
        # A Boolean such as ``allow_network_fetcher=True`` is not authority.
        # Restrict the trust kernel to the exact implementation whose rooted
        # file behaviour is reviewed and tested. A subclass could override
        # ``fetch`` and therefore is deliberately not accepted either.
        if type(fetcher) is not LocalSourceFetcher:
            raise WatchError(
                "Scope Watch core accepts only the exact LocalSourceFetcher; "
                "capture external sources in a separately governed adapter "
                "and pass the local evidence inward"
            )
        self.fetcher = fetcher
        self.audit = audit
        self._clock = clock

    def check(
        self,
        programme_id: str,
        sources: Iterable[WatchedSource],
        *,
        observed_ids: Iterable[str] | None = None,
    ) -> WatchResult:
        """Re-read every recorded source and compare.

        Args:
            observed_ids: Source ids visible at the origin now, when the
                fetcher can enumerate them. Supplying it lets the watch detect
                sources that appeared or disappeared rather than only ones that
                changed.
        """
        recorded = list(sources)
        if not recorded:
            raise WatchError(
                f"programme {programme_id!r} has no recorded sources to watch"
            )

        result = WatchResult(
            programme_id=programme_id,
            checked_at=self._clock(),
            fetcher_id=self.fetcher.fetcher_id,
        )

        for source in recorded:
            try:
                payload = self.fetcher.fetch(source.locator)
            except FileNotFoundError:
                result.observations.append(
                    SourceObservation(
                        source_id=source.source_id,
                        state=SourceState.GONE,
                        recorded_hash=source.recorded_hash,
                        error="source is no longer present at its locator",
                    )
                )
                continue
            except Exception as exc:  # noqa: BLE001 - report, never assume unchanged
                result.observations.append(
                    SourceObservation(
                        source_id=source.source_id,
                        state=SourceState.UNREACHABLE,
                        recorded_hash=source.recorded_hash,
                        error=f"{type(exc).__name__}: {exc}",
                    )
                )
                continue

            observed = digest(payload)
            result.observations.append(
                SourceObservation(
                    source_id=source.source_id,
                    state=(
                        SourceState.UNCHANGED
                        if observed == source.recorded_hash
                        else SourceState.CHANGED
                    ),
                    recorded_hash=source.recorded_hash,
                    observed_hash=observed,
                )
            )

        if observed_ids is not None:
            known = {s.source_id for s in recorded}
            for source_id in sorted(set(observed_ids) - known):
                result.observations.append(
                    SourceObservation(source_id=source_id, state=SourceState.NEW)
                )

        if self.audit is not None:
            self.audit.append(
                actor=f"scope_watch:{self.fetcher.fetcher_id}",
                action="scopewatch.check",
                detail={
                    "programme_id": programme_id,
                    "sources_checked": len(recorded),
                    "review_invalidated": result.review_invalidated,
                    "summary": result.summary(),
                    "network_fetcher": bool(getattr(self.fetcher, "network", False)),
                },
            )
        return result


def sources_from_bundle(bundle: Mapping[str, Any]) -> list[WatchedSource]:
    """Extract watchable sources from a recorded bundle snapshot.

    Tolerant of shape because bundle snapshots are written by the registry and
    this should not break when a field is added. A source without both a
    locator and a recorded hash is skipped rather than guessed at — watching a
    source we cannot compare against would report every run as changed.
    """
    entries = bundle.get("sources") or []
    watched: list[WatchedSource] = []
    for entry in entries:
        if not isinstance(entry, Mapping):
            continue
        source_id = str(entry.get("source_id") or entry.get("id") or "").strip()
        locator = str(entry.get("local_path") or entry.get("locator") or "").strip()
        recorded = str(entry.get("hash") or entry.get("sha256") or "").strip()
        if recorded.startswith("sha256:"):
            recorded = recorded.split(":", 1)[1]
        if not (source_id and locator and recorded):
            continue
        watched.append(
            WatchedSource(
                source_id=source_id,
                locator=locator,
                recorded_hash=recorded,
                kind=str(entry.get("kind", "")),
            )
        )
    return watched


__all__ = [
    "LocalSourceFetcher",
    "ScopeWatch",
    "SourceFetcher",
    "SourceObservation",
    "SourceState",
    "WatchError",
    "WatchResult",
    "WatchedSource",
    "digest",
    "sources_from_bundle",
]
