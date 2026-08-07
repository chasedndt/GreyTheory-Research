"""Lane 1 — known vulnerabilities, from manifests and a local advisory set.

Entirely static. It reads dependency manifests and compares them against an
advisory file the operator supplies; it fetches nothing, and it never touches
the target.

The important restraint is in what it refuses to say. A version inside an
advisory's affected range is a **version match**, not a vulnerability. The
dependency may not be reachable, the vulnerable code path may not be used, the
programme may exclude the class entirely, and version strings lie. So every
signal here is ``contextual`` and its title says "matches", never "is
vulnerable" — the second phrasing is how a scanner's output becomes a report
nobody can defend.
"""

# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 ChaseInTech

from __future__ import annotations

import json
import re
from typing import Any

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
    """Numeric components only. Enough to order releases, honest about the rest."""
    parts: list[int] = []
    for chunk in re.split(r"[.\-+]", value.strip()):
        if chunk.isdigit():
            parts.append(int(chunk))
        else:
            digits = re.match(r"^(\d+)", chunk)
            if digits:
                parts.append(int(digits.group(1)))
            break
    return tuple(parts) or (0,)


def in_range(version: str, introduced: str | None, fixed: str | None) -> bool:
    current = parse_version(version)
    if introduced and current < parse_version(introduced):
        return False
    if fixed and current >= parse_version(fixed):
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
            "operator-supplied advisory file. Emits version matches, never "
            "vulnerability claims."
        ),
    )

    ADVISORIES = "advisories.json"

    def collect(self, context: LaneContext) -> list[RawSignal]:
        if not context.exists(self.ADVISORIES):
            return []
        try:
            advisories = json.loads(context.read_text(self.ADVISORIES))
        except json.JSONDecodeError:
            return []
        if not isinstance(advisories, list):
            return []

        dependencies = self._dependencies(context)
        signals: list[RawSignal] = []
        source = f"{self.spec.id}"

        for advisory in advisories:
            package = str(advisory.get("package", "")).lower()
            if package not in dependencies:
                continue
            version, origin = dependencies[package]
            introduced = advisory.get("introduced")
            fixed = advisory.get("fixed")
            if not in_range(version, introduced, fixed):
                continue

            identifier = advisory.get("id", "unknown")
            signals.append(
                RawSignal(
                    id=f"{self.spec.id}_{package}_{identifier}",
                    lane=1,
                    asset=context.asset,
                    kind="dependency_version_match",
                    title=(
                        f"{package} {version} matches advisory {identifier} "
                        f"(affected: {introduced or '*'} to {fixed or '*'})"
                    ),
                    level=SignalLevel.CONTEXTUAL,
                    claims=[
                        checked(
                            f"{origin} declares {package}=={version}, which falls "
                            f"inside advisory {identifier}'s affected range",
                            source,
                            f"check:version_range:{package}:{identifier}",
                        ),
                        observed(
                            "a version match is not a vulnerability: reachability, "
                            "the affected code path and the programme's exclusions "
                            "are all unknown here",
                            source,
                        ),
                    ],
                    detail={
                        "package": package,
                        "version": version,
                        "advisory": identifier,
                        "manifest": origin,
                        "severity_hint": advisory.get("severity", ""),
                    },
                    observed_at=context.now(),
                )
            )
        return signals

    def _dependencies(self, context: LaneContext) -> dict[str, tuple[str, str]]:
        found: dict[str, tuple[str, str]] = {}

        if context.exists("requirements.txt"):
            for line in context.read_text("requirements.txt").splitlines():
                if line.strip().startswith("#"):
                    continue
                match = REQUIREMENT.match(line)
                if match:
                    found[match.group(1).lower()] = (match.group(3), "requirements.txt")

        if context.exists("package.json"):
            try:
                package = json.loads(context.read_text("package.json"))
            except json.JSONDecodeError:
                package = {}
            for section in ("dependencies", "devDependencies"):
                for name, spec in (package.get(section) or {}).items():
                    version = str(spec).lstrip("^~>=< ")
                    if version:
                        found[name.lower()] = (version, f"package.json:{section}")

        return found


__all__ = ["DependencyManifestLane", "in_range", "parse_version"]
