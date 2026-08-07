"""Advisory sets — real vulnerability data, imported offline.

Lane 1 previously required a hand-written `advisories.json`, which made it a
demonstration rather than a tool. This module imports the format the world
actually publishes — OSV, used by GitHub, PyPI, npm, Go and the rest — from
files the operator has already downloaded. Nothing here fetches anything.

Two things are easy to get wrong and are handled deliberately.

**Ecosystem matching.** `requests` on PyPI and `requests` on npm are different
packages, and a name-only match reports the wrong one with total confidence.
Every advisory and every dependency carries an ecosystem, and a match requires
both to agree.

**Version ordering.** `2.0.0-rc1` is *earlier* than `2.0.0`, and a naive
comparison gets that backwards — which means a release candidate is reported as
patched when it is not, or a fixed version is flagged as vulnerable. Release
components compare numerically, and a pre-release sorts before the release it
precedes.

An advisory match remains a *version match*. Reachability, the affected code
path and the programme's exclusions are all still unknown, and Lane 1 says so.
"""

# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 ChaseInTech

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from functools import total_ordering
from pathlib import Path
from typing import Any, Iterable

ECOSYSTEM_ALIASES = {
    "pypi": "PyPI",
    "python": "PyPI",
    "npm": "npm",
    "node": "npm",
    "javascript": "npm",
    "go": "Go",
    "golang": "Go",
    "maven": "Maven",
    "java": "Maven",
    "rubygems": "RubyGems",
    "ruby": "RubyGems",
    "crates.io": "crates.io",
    "rust": "crates.io",
    "nuget": "NuGet",
    "packagist": "Packagist",
    "php": "Packagist",
}


def normalise_ecosystem(value: str) -> str:
    """Canonical ecosystem name. Unknown values pass through unchanged."""
    text = str(value or "").strip()
    return ECOSYSTEM_ALIASES.get(text.lower(), text)


def normalise_package(name: str, ecosystem: str) -> str:
    """Canonical package name for the ecosystem's own rules."""
    text = str(name or "").strip().lower()
    if normalise_ecosystem(ecosystem) == "PyPI":
        # PEP 503: runs of -, _ and . are equivalent.
        text = re.sub(r"[-_.]+", "-", text)
    return text


_VERSION_PART = re.compile(r"(\d+)")


@total_ordering
@dataclass(frozen=True)
class Version:
    """A comparable version.

    Deliberately lenient about what it accepts and strict about how it orders.
    Real manifests contain `1.2`, `2.0.0-rc1`, `4.0.0+build7` and worse; the
    ordering that matters is release-then-prerelease.
    """

    raw: str

    @property
    def release(self) -> tuple[int, ...]:
        head = re.split(r"[-+]", self.raw.strip(), maxsplit=1)[0]
        parts: list[int] = []
        for chunk in head.split("."):
            match = _VERSION_PART.match(chunk.strip())
            if not match:
                break
            parts.append(int(match.group(1)))
        return tuple(parts) or (0,)

    @property
    def prerelease(self) -> tuple[str, ...]:
        """Empty for a final release, which is why a final release sorts last."""
        text = self.raw.strip()
        # semver style: 2.0.0-rc1
        match = re.search(r"[-]([0-9A-Za-z.]+)", re.split(r"\+", text, maxsplit=1)[0])
        if match:
            return tuple(match.group(1).lower().split("."))
        # PEP 440 style: 2.0.0rc1, 1.0b2
        match = re.search(r"\d(a|b|rc|alpha|beta|dev)\.?(\d*)$", text, re.IGNORECASE)
        if match:
            return (match.group(1).lower(), match.group(2) or "0")
        return ()

    def _key(self) -> tuple:
        # A pre-release sorts before the release it precedes, so the flag is 0
        # for pre-releases and 1 for finals.
        return (self.release, 0 if self.prerelease else 1, self.prerelease)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Version):
            return NotImplemented
        a, b = self._key(), other._key()
        length = max(len(a[0]), len(b[0]))
        return (
            self._padded(a[0], length),
            a[1],
            a[2],
        ) == (self._padded(b[0], length), b[1], b[2])

    def __lt__(self, other: Version) -> bool:
        a, b = self._key(), other._key()
        length = max(len(a[0]), len(b[0]))
        return (
            self._padded(a[0], length),
            a[1],
            a[2],
        ) < (self._padded(b[0], length), b[1], b[2])

    @staticmethod
    def _padded(parts: tuple[int, ...], length: int) -> tuple[int, ...]:
        # 1.2 and 1.2.0 are the same version; padding makes them compare so.
        return parts + (0,) * (length - len(parts))

    def __str__(self) -> str:
        return self.raw


@dataclass(frozen=True)
class Advisory:
    id: str
    package: str
    ecosystem: str
    introduced: str | None = None
    fixed: str | None = None
    severity: str = ""
    summary: str = ""
    aliases: tuple[str, ...] = ()
    source: str = ""

    def affects(self, version: str) -> bool:
        """Is this version inside the affected range?

        ``introduced`` is inclusive, ``fixed`` is exclusive — the convention
        OSV uses, and getting it backwards reports the patched release as
        vulnerable.
        """
        current = Version(version)
        if self.introduced and current < Version(self.introduced):
            return False
        if self.fixed and not current < Version(self.fixed):
            return False
        return True

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "package": self.package,
            "ecosystem": self.ecosystem,
            "introduced": self.introduced,
            "fixed": self.fixed,
            "severity": self.severity,
            "summary": self.summary,
            "aliases": list(self.aliases),
            "source": self.source,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Advisory:
        return cls(
            id=data["id"],
            package=normalise_package(data["package"], data.get("ecosystem", "")),
            ecosystem=normalise_ecosystem(data.get("ecosystem", "")),
            introduced=data.get("introduced"),
            fixed=data.get("fixed"),
            severity=data.get("severity", ""),
            summary=data.get("summary", ""),
            aliases=tuple(data.get("aliases", ())),
            source=data.get("source", ""),
        )


def from_osv(record: dict[str, Any], *, source: str = "osv") -> list[Advisory]:
    """Convert one OSV record into advisories — one per affected package range.

    OSV allows several affected packages and several ranges per record, so one
    record legitimately becomes several advisories. Records that declare no
    usable range are skipped rather than guessed at: an advisory with unknown
    bounds would match every version.
    """
    identifier = str(record.get("id", "")).strip()
    if not identifier:
        return []

    summary = str(record.get("summary") or record.get("details") or "")[:300]
    aliases = tuple(str(a) for a in record.get("aliases", []))

    severity = ""
    database = record.get("database_specific") or {}
    if isinstance(database, dict):
        severity = str(database.get("severity", "") or "")
    if not severity:
        entries = record.get("severity") or []
        if isinstance(entries, list) and entries:
            severity = str(entries[0].get("score", "") or "")

    advisories: list[Advisory] = []
    for affected in record.get("affected", []) or []:
        package = affected.get("package") or {}
        name = package.get("name")
        ecosystem = normalise_ecosystem(package.get("ecosystem", ""))
        if not name:
            continue

        for entry in affected.get("ranges", []) or []:
            introduced: str | None = None
            fixed: str | None = None
            for event in entry.get("events", []) or []:
                if "introduced" in event:
                    value = str(event["introduced"])
                    introduced = None if value == "0" else value
                elif "fixed" in event:
                    fixed = str(event["fixed"])
                elif "last_affected" in event:
                    # Inclusive upper bound. Left unconverted rather than
                    # guessed into an exclusive one.
                    fixed = None
            if introduced is None and fixed is None:
                continue
            advisories.append(
                Advisory(
                    id=identifier,
                    package=normalise_package(name, ecosystem),
                    ecosystem=ecosystem,
                    introduced=introduced,
                    fixed=fixed,
                    severity=severity,
                    summary=summary,
                    aliases=aliases,
                    source=source,
                )
            )
    return advisories


@dataclass
class AdvisorySet:
    """A queryable local advisory set. Built offline, versioned like anything else."""

    advisories: list[Advisory] = field(default_factory=list)

    def __len__(self) -> int:
        return len(self.advisories)

    def add(self, advisory: Advisory) -> None:
        self.advisories.append(advisory)

    def matches(self, package: str, ecosystem: str, version: str) -> list[Advisory]:
        """Advisories affecting this exact package, in this ecosystem, at this version."""
        name = normalise_package(package, ecosystem)
        eco = normalise_ecosystem(ecosystem)
        return [
            advisory
            for advisory in self.advisories
            if advisory.package == name
            and advisory.ecosystem == eco
            and advisory.affects(version)
        ]

    def ecosystems(self) -> set[str]:
        return {a.ecosystem for a in self.advisories}

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": "greytheory.advisories/1",
            "count": len(self.advisories),
            "advisories": [a.to_dict() for a in self.advisories],
        }

    def write(self, path: str | Path) -> Path:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")
        return target

    @classmethod
    def from_dict(cls, data: Any) -> AdvisorySet:
        """Accepts our own format, a bare list, or a list of OSV records."""
        if isinstance(data, dict) and "advisories" in data:
            entries = data["advisories"]
        elif isinstance(data, list):
            entries = data
        else:
            entries = [data]

        advisories: list[Advisory] = []
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            if "affected" in entry:  # OSV shape
                advisories.extend(from_osv(entry))
            elif "package" in entry and "id" in entry:
                advisories.append(Advisory.from_dict(entry))
        return cls(advisories=advisories)

    @classmethod
    def load(cls, path: str | Path) -> AdvisorySet:
        source = Path(path)
        if source.is_dir():
            return cls.load_directory(source)
        return cls.from_dict(json.loads(source.read_text(encoding="utf-8")))

    @classmethod
    def load_directory(cls, directory: str | Path) -> AdvisorySet:
        """Load every JSON file in a tree — the shape OSV bulk exports arrive in."""
        combined = cls()
        for path in sorted(Path(directory).rglob("*.json")):
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError, OSError):
                continue  # an unreadable file is not an advisory
            combined.advisories.extend(cls.from_dict(payload).advisories)
        return combined

    @classmethod
    def from_records(cls, records: Iterable[dict[str, Any]]) -> AdvisorySet:
        combined = cls()
        for record in records:
            combined.advisories.extend(cls.from_dict(record).advisories)
        return combined


__all__ = [
    "Advisory",
    "AdvisorySet",
    "ECOSYSTEM_ALIASES",
    "Version",
    "from_osv",
    "normalise_ecosystem",
    "normalise_package",
]
