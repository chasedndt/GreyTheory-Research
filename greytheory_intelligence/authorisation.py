"""Shared transport and tier authorisation for intelligence reads.

Extracted so tier 1 (public directory) and tier 2 (authenticated account) apply
the *same* transport safety rules and differ only where they genuinely should:
whether a credential is sent, and what data class comes back.

ADR-0029 governs. The rule that matters most is the trust anchor — a read is
permitted because the source is an established authority, not because the verb
is a GET. An unlisted or lesser-trusted host is refused, never fetched
carefully.
"""

# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 ChaseInTech

from __future__ import annotations

from enum import StrEnum

from greytheory_intelligence.posture import (
    CollectorPosture,
    CollectorPostureError,
    require_collector_posture,
)
from greytheory_intelligence.registry import (
    INTELLIGENCE_PROVIDERS,
    IntelligencePlan,
    IntelligenceProvider,
    QueryKind,
    TrustTier,
)


class ReadTier(StrEnum):
    #: Unauthenticated read of what a platform publishes to anyone.
    PUBLIC_DIRECTORY = "public_directory"
    #: Authenticated read of the operator's own account state.
    OPERATOR_ACCOUNT = "operator_account"


class IntelligenceAuthorisationError(RuntimeError):
    """Raised when a read is not authorised inside its declared bounds."""


def require_transport_safety(provider: IntelligenceProvider) -> None:
    """Rules every outbound read obeys, whatever tier it belongs to."""

    if not provider.require_tls or not provider.origin.startswith("https://"):
        raise IntelligenceAuthorisationError("intelligence reads require HTTPS")
    if provider.follow_redirects:
        raise IntelligenceAuthorisationError(
            "redirects must be refused so a read cannot leave its approved origin"
        )
    if provider.side_effects != ("external_read",):
        raise IntelligenceAuthorisationError("intelligence providers are read-only")
    if provider.maximum_response_bytes <= 0:
        raise IntelligenceAuthorisationError("a response ceiling is required")


def require_trusted_authority(provider: IntelligenceProvider) -> None:
    """A read needs a source with standing, not merely a safe verb."""

    if provider.trust_tier not in (
        TrustTier.PROGRAMME_AUTHORITY,
        TrustTier.ADVISORY_AUTHORITY,
    ):
        raise IntelligenceAuthorisationError(
            "ADR-0029 permits reads only from an established authority"
        )


def authorise(plan: IntelligencePlan, *, tier: ReadTier) -> IntelligenceProvider:
    """Resolve and authorise the provider a plan names for one tier."""

    provider = INTELLIGENCE_PROVIDERS.get(plan.provider_id)
    if provider is None:
        raise IntelligenceAuthorisationError("unknown provider")

    # The recorded collector posture gates the read, so the code cannot run
    # ahead of what the system says about itself.
    needed = (
        CollectorPosture.OPERATOR_ACCOUNT
        if tier is ReadTier.OPERATOR_ACCOUNT
        else CollectorPosture.PUBLIC_INTELLIGENCE
    )
    try:
        require_collector_posture(needed)
    except CollectorPostureError as error:
        raise IntelligenceAuthorisationError(str(error)) from error

    require_transport_safety(provider)
    require_trusted_authority(provider)

    if tier is ReadTier.PUBLIC_DIRECTORY:
        if plan.query_kind is not QueryKind.PROGRAMME_DIRECTORY:
            raise IntelligenceAuthorisationError("this tier serves directory reads only")
        if provider.trust_tier is not TrustTier.PROGRAMME_AUTHORITY:
            raise IntelligenceAuthorisationError(
                "directory reads require a programme authority"
            )
        if provider.allowed_methods != ("GET",):
            raise IntelligenceAuthorisationError("directory providers are GET only")
        if provider.sends_credentials or provider.authentication != "none":
            raise IntelligenceAuthorisationError("tier 1 reads must be unauthenticated")
        return provider

    if tier is ReadTier.OPERATOR_ACCOUNT:
        if plan.query_kind is not QueryKind.OPERATOR_ACCOUNT:
            raise IntelligenceAuthorisationError("this tier serves account reads only")
        if not provider.sends_credentials:
            raise IntelligenceAuthorisationError(
                "an account provider must declare that it sends a credential"
            )
        if provider.authentication != "operator_token":
            raise IntelligenceAuthorisationError(
                "account reads use an operator-provisioned token"
            )
        if provider.allowed_methods != ("GET",):
            raise IntelligenceAuthorisationError(
                "account reads are GET only; writing is tier 3 and separately approved"
            )
        if provider.data_class != "RESTRICTED":
            raise IntelligenceAuthorisationError(
                "account state is RESTRICTED and must never be classed PUBLIC"
            )
        return provider

    raise IntelligenceAuthorisationError("unknown read tier")
