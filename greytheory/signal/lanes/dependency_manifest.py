"""Lane 1 — known vulnerabilities, from manifests and a local advisory set.

Entirely static. It reads dependency manifests and compares them against an
advisory set the operator supplied; it fetches nothing, and it never touches
the target. Advisory data is imported offline — see `greytheory.advisories`,
which reads the OSV format that GitHub, PyPI, npm and Go all publish.

Two restraints.

**Ecosystem matching.** `requests` on PyPI and `requests` on npm are different
packages. A match requires the ecosystem to agree, because a name-only match
reports the wrong package with total confidence.

**What it refuses to say.** A version inside an advisory's affected range is a
**version match**, not a vulnerability. The dependency may not be reachable,
the vulnerable code path may not be used, the programme may exclude the class
entirely, and version strings lie. So every signal is ``contextual`` and its
title says "matches", never "is vulnerable" — the second phrasing is how a
scanner's output becomes a report nobody can defend.
"""

# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 ChaseInTech

from __future__ import annotations

import json
import re

from greytheory.advisories import AdvisorySet, Version, normalise_package
from greytheory.authority.gate import AuthorityLevel
from greytheory.signal.contract import (
    LaneContext,
    LaneSpec,
    RawSignal,
    SignalLevel,
    checked,
    observed,
)

REQUIREMENT = re.compile(
    r"^\s*([A-Za-z0-9._-]+)\s*(==|>=|<=|~=)\s*([0-9][0-9A-Za-z.\-+]*)"
)


def parse_version(value: str) -> tuple[int, ...]:
    """Kept for callers that only need the release tuple."""
    return Version(value).release


def in_range(version: str, introduced: str | None, fixed: str | None) -> bool:
    """``introduced`` inclusive, ``fixed`` exclusive — the OSV convention."""
    current = Version(version)
    if introduced and current < Version(introduced):
        return False
    if fixed and not current < Version(fixed):
        return False
    return True


class DependencyManifestLane:
    """Match declared dependency versions against a local advisory set."""

    spec = LaneSpec(
        id="lane1_dependency_manifest",
        lane=1,
        title="Dependency manifest vs local advisories",
        requires_authority=AuthorityLevel.LOCAL_FIXTURE,
        network=False,
        description=(
            "Static comparison of declared dependency versions against an "
            "operator-supplied advisory set, matched by package and ecosystem. "
            "Emits version matches, never vulnerability claims."
        ),
    )

    ADVISORIES = "advisories.json"

    def __init__(self, advisories: AdvisorySet | None = None):
        """Args:
        advisories: An advisory set to use. When omitted, the lane looks for
            ``advisories.json`` inside the granted root — which keeps a
            self-contained lab fixture working without external wiring.
        """
        self._advisories = advisories

    def collect(self, context: LaneContext) -> list[RawSignal]:
        advisories = self._advisories
        if advisories is None:
            if not context.exists(self.ADVISORIES):
                return []
            try:
                advisories = AdvisorySet.from_dict(
                    json.loads(context.read_text(self.ADVISORIES))
                )
            except json.JSONDecodeError:
                return []

        if not len(advisories):
            return []

        source = self.spec.id
        signals: list[RawSignal] = []

        for (package, ecosystem), (version, origin) in self._dependencies(context).items():
            for advisory in advisories.matches(package, ecosystem, version):
                signals.append(
                    RawSignal(
                        id=f"{self.spec.id}_{ecosystem}_{package}_{advisory.id}",
                        lane=1,
                        asset=context.asset,
                        kind="dependency_version_match",
                        title=(
                            f"{package} {version} ({ecosystem}) matches advisory "
                            f"{advisory.id} (affected: "
                            f"{advisory.introduced or '*'} to {advisory.fixed or '*'})"
                        ),
                        level=SignalLevel.CONTEXTUAL,
                        claims=[
                            checked(
                                f"{origin} declares {package}=={version} in the "
                                f"{ecosystem} ecosystem, which falls inside "
                                f"advisory {advisory.id}'s affected range",
                                source,
                                f"check:version_range:{ecosystem}:{package}:{advisory.id}",
                            ),
                            observed(
                                "a version match is not a vulnerability: "
                                "reachability, the affected code path and the "
                                "programme's exclusions are all unknown here",
                                source,
                            ),
                        ],
                        detail={
                            "package": package,
                            "ecosystem": ecosystem,
                            "version": version,
                            "advisory": advisory.id,
                            "aliases": list(advisory.aliases),
                            "manifest": origin,
                            "severity_hint": advisory.severity,
                            "summary": advisory.summary,
                        },
                        observed_at=context.now(),
                    )
                )
        return signals

    def _dependencies(
        self, context: LaneContext
    ) -> dict[tuple[str, str], tuple[str, str]]:
        """Declared dependencies, keyed by (package, ecosystem)."""
        found: dict[tuple[str, str], tuple[str, str]] = {}

        if context.exists("requirements.txt"):
            for line in context.read_text("requirements.txt").splitlines():
                if line.strip().startswith("#"):
                    continue
                match = REQUIREMENT.match(line)
                if match:
                    name = normalise_package(match.group(1), "PyPI")
                    found[(name, "PyPI")] = (match.group(3), "requirements.txt")

        if context.exists("package.json"):
            try:
                package = json.loads(context.read_text("package.json"))
            except json.JSONDecodeError:
                package = {}
            for section in ("dependencies", "devDependencies"):
                for name, spec in (package.get(section) or {}).items():
                    version = str(spec).lstrip("^~>=< ")
                    if version:
                        found[(normalise_package(name, "npm"), "npm")] = (
                            version,
                            f"package.json:{section}",
                        )

        return found


__all__ = ["DependencyManifestLane", "in_range", "parse_version"]
