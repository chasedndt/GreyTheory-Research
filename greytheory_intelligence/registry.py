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
    #: A public bug bounty programme directory listing. Reads what a programme
    #: publishes to anyone — scope shape, reward band, activity — so the
    #: learning surface can follow real demand. It is not authenticated, it
    #: reads no account state, and it never touches a programme's assets.
    PROGRAMME_DIRECTORY = "programme_directory"
    #: The operator's own account state on a platform: invitations,
    #: submissions, reputation, private programme scope. Authenticated, read
    #: only, and RESTRICTED — it must never reach an export or a share card.
    OPERATOR_ACCOUNT = "operator_account"


_CVE = re.compile(r"^CVE-[0-9]{4}-[0-9]{4,}$", re.IGNORECASE)
_PACKAGE = re.compile(r"^(PyPI|npm|Go|Maven|RubyGems|crates\.io|NuGet|Packagist):[A-Za-z0-9@._/+~-]+@[A-Za-z0-9._+~-]+$")
#: A directory query names a platform and an optional public programme handle.
_DIRECTORY = re.compile(r"^(hackerone|bugcrowd|intigriti|yeswehack):[a-z0-9][a-z0-9._-]{0,63}$")
#: An account query names a platform and one bounded account view.
_ACCOUNT = re.compile(r"^(hackerone|bugcrowd|intigriti|yeswehack)/(programmes|invitations|submissions|profile)$")


class TrustTier(StrEnum):
    """How much standing a source has to be read at all.

    Per ADR-0029 a directory read is acceptable because the source is an
    established programme authority, not because GET is inherently safe. A
    source without that standing is refused rather than fetched cautiously.
    """

    #: Established bug bounty platform or public vulnerability authority.
    PROGRAMME_AUTHORITY = "programme_authority"
    #: Recognised public advisory body.
    ADVISORY_AUTHORITY = "advisory_authority"


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
    trust_tier: TrustTier = TrustTier.ADVISORY_AUTHORITY
    #: HTTPS only. A plain-HTTP origin is a configuration error, never upgraded.
    require_tls: bool = True
    follow_redirects: bool = False
    sends_credentials: bool = False
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
    # Public programme directories. These describe what a bounty platform
    # publishes openly. Authentication is "none" deliberately: an authenticated
    # connector reads account state (invitations, submissions, reputation) and
    # is a separate, larger decision that this registry must not smuggle in.
    "hackerone-directory": IntelligenceProvider("hackerone-directory", "1", "HackerOne public directory", "public", "https://hackerone.com", ("GET",), (QueryKind.PROGRAMME_DIRECTORY,), "none", 1, 4_000_000, trust_tier=TrustTier.PROGRAMME_AUTHORITY),
    "bugcrowd-directory": IntelligenceProvider("bugcrowd-directory", "1", "Bugcrowd public programme index", "public", "https://bugcrowd.com", ("GET",), (QueryKind.PROGRAMME_DIRECTORY,), "none", 1, 4_000_000, trust_tier=TrustTier.PROGRAMME_AUTHORITY),
    "intigriti-directory": IntelligenceProvider("intigriti-directory", "1", "Intigriti public programme index", "public", "https://www.intigriti.com", ("GET",), (QueryKind.PROGRAMME_DIRECTORY,), "none", 1, 4_000_000, trust_tier=TrustTier.PROGRAMME_AUTHORITY),
    "yeswehack-directory": IntelligenceProvider("yeswehack-directory", "1", "YesWeHack public programme index", "public", "https://yeswehack.com", ("GET",), (QueryKind.PROGRAMME_DIRECTORY,), "none", 1, 4_000_000, trust_tier=TrustTier.PROGRAMME_AUTHORITY),
    # Tier 2: the operator's own account state, read with a token the operator
    # provisions themselves. RESTRICTED because private programme scope and
    # submission history must never reach an export, share card, or coach.
    "hackerone-account": IntelligenceProvider("hackerone-account", "1", "HackerOne account", "operator", "https://api.hackerone.com", ("GET",), (QueryKind.OPERATOR_ACCOUNT,), "operator_token", 1, 4_000_000, data_class="RESTRICTED", trust_tier=TrustTier.PROGRAMME_AUTHORITY, sends_credentials=True),
    "bugcrowd-account": IntelligenceProvider("bugcrowd-account", "1", "Bugcrowd account", "operator", "https://api.bugcrowd.com", ("GET",), (QueryKind.OPERATOR_ACCOUNT,), "operator_token", 1, 4_000_000, data_class="RESTRICTED", trust_tier=TrustTier.PROGRAMME_AUTHORITY, sends_credentials=True),
    "intigriti-account": IntelligenceProvider("intigriti-account", "1", "Intigriti account", "operator", "https://api.intigriti.com", ("GET",), (QueryKind.OPERATOR_ACCOUNT,), "operator_token", 1, 4_000_000, data_class="RESTRICTED", trust_tier=TrustTier.PROGRAMME_AUTHORITY, sends_credentials=True),
    "yeswehack-account": IntelligenceProvider("yeswehack-account", "1", "YesWeHack account", "operator", "https://apps.yeswehack.com", ("GET",), (QueryKind.OPERATOR_ACCOUNT,), "operator_token", 1, 4_000_000, data_class="RESTRICTED", trust_tier=TrustTier.PROGRAMME_AUTHORITY, sends_credentials=True),
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
    elif _DIRECTORY.fullmatch(value.lower()):
        kind = QueryKind.PROGRAMME_DIRECTORY
        value = value.lower()
    elif _ACCOUNT.fullmatch(value.lower()):
        kind = QueryKind.OPERATOR_ACCOUNT
        value = value.lower()
    else:
        raise ValueError(
            "identifier must be a CVE, versioned package coordinate, "
            "platform:handle directory reference, or platform/view account view"
        )
    if kind not in provider.query_kinds:
        raise ValueError(f"{provider.name} does not accept {kind.value} queries")
    return IntelligencePlan(
        provider_id=provider.id,
        provider_version=provider.version,
        query_kind=kind,
        identifier=value,
    )
