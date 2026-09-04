"""Fail-closed contracts for future public intelligence fetchers.

This module is intentionally network-free. A later governed worker may consume
an :class:`IntelligencePlan`, materialise immutable source evidence, and return
that evidence to the existing offline importers. Merely creating a plan grants
no authority and performs no external action.
"""

# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 ChaseInTech

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum


class QueryKind(StrEnum):
    CVE = "cve"
    PACKAGE = "package"


_CVE = re.compile(r"^CVE-[0-9]{4}-[0-9]{4,}$", re.IGNORECASE)
_PACKAGE = re.compile(r"^(PyPI|npm|Go|Maven|RubyGems|crates\.io|NuGet|Packagist):[A-Za-z0-9@._/+~-]+@[A-Za-z0-9._+~-]+$")


@dataclass(frozen=True)
class IntelligenceProvider:
    id: str
    version: str
    name: str
    authority: str
    origin: str
    allowed_methods: tuple[str, ...]
    query_kinds: tuple[QueryKind, ...]
    authentication: str
    maximum_identifiers: int
    maximum_response_bytes: int
    data_class: str = "PUBLIC"
    side_effects: tuple[str, ...] = ("external_read",)
    stop_conditions: tuple[str, ...] = (
        "redirect",
        "unexpected_content_type",
        "response_limit",
        "rate_limit",
        "schema_mismatch",
    )


INTELLIGENCE_PROVIDERS: dict[str, IntelligenceProvider] = {
    "osv": IntelligenceProvider("osv", "1", "OSV.dev", "public", "https://api.osv.dev", ("GET", "POST"), (QueryKind.CVE, QueryKind.PACKAGE), "none", 32, 2_000_000),
    "cisa-kev": IntelligenceProvider("cisa-kev", "1", "CISA KEV", "public", "https://www.cisa.gov", ("GET",), (QueryKind.CVE,), "none", 1, 4_000_000),
    "epss": IntelligenceProvider("epss", "1", "FIRST EPSS", "public", "https://api.first.org", ("GET",), (QueryKind.CVE,), "none", 100, 1_000_000),
    "nvd": IntelligenceProvider("nvd", "1", "NVD", "public", "https://services.nvd.nist.gov", ("GET",), (QueryKind.CVE,), "optional_server_key", 1, 2_000_000),
    "github-advisories": IntelligenceProvider("github-advisories", "1", "GitHub Advisories", "public", "https://api.github.com", ("GET",), (QueryKind.CVE,), "optional_server_token", 1, 2_000_000),
}


@dataclass(frozen=True)
class IntelligencePlan:
    provider_id: str
    provider_version: str
    query_kind: QueryKind
    identifier: str
    posture: str = "CONTRACT_ONLY"
    executable: bool = False
    target_interaction: bool = False
    preserves_source: bool = True

    def to_dict(self) -> dict[str, object]:
        return {
            "schema": "greytheory.intelligence-plan/1",
            "provider_id": self.provider_id,
            "provider_version": self.provider_version,
            "query_kind": self.query_kind.value,
            "identifier": self.identifier,
            "posture": self.posture,
            "executable": self.executable,
            "target_interaction": self.target_interaction,
            "preserves_source": self.preserves_source,
        }


def build_intelligence_plan(provider_id: str, identifier: str) -> IntelligencePlan:
    """Validate a CVE or package coordinate and return a non-executing plan."""
    provider = INTELLIGENCE_PROVIDERS.get(str(provider_id).strip())
    if provider is None:
        raise ValueError("unknown intelligence provider")
    value = str(identifier).strip()
    if _CVE.fullmatch(value):
        kind = QueryKind.CVE
        value = value.upper()
    elif _PACKAGE.fullmatch(value):
        kind = QueryKind.PACKAGE
    else:
        raise ValueError("identifier must be a CVE or versioned package coordinate")
    if kind not in provider.query_kinds:
        raise ValueError(f"{provider.name} does not accept {kind.value} queries")
    return IntelligencePlan(
        provider_id=provider.id,
        provider_version=provider.version,
        query_kind=kind,
        identifier=value,
    )
