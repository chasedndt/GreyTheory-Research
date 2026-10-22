"""Subdomain-takeover verification as claims, not verdicts.

The collector consumes *observations* something else gathered - a CNAME chain
and, optionally, an HTTP response - and produces claims whose provenance says
exactly how far the evidence goes:

* ``observed``  - the name's CNAME resolves into a known provider. A fact.
* ``inferred``  - the provider's unclaimed-resource marker was seen in the
  body. Circumstantial: error pages change and CDNs front many tenants.
* ``checked``   - never produced here. Binary proof of a takeover is *claiming
  the resource and serving a token*, which is an action on the target. That
  needs the execution posture to allow it and an operator to do it, and the
  resulting check reference is recorded through the trust kernel, not by this
  module deciding it happened.

Gathering the observations live is refused below ``PASSIVE_HTTP``. At
``LOCAL_FIXTURE`` the collector only evaluates observations supplied from
fixtures, which is what makes it testable today.
"""

# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 ChaseInTech

from __future__ import annotations

from dataclasses import dataclass, field

from greytheory.authority.gate import AuthorityLevel
from greytheory.provenance import Claim, Tag
from greytheory_collectors.probe_posture import (  # noqa: F401 - re-exported
    LIVE_PROBE_REQUIRES,
    ProbeRefused,
    require_probe_posture,
)
from greytheory_collectors.takeover_fingerprints import FINGERPRINTS, Fingerprint

SOURCE = "greytheory_collectors.subdomain_takeover"


@dataclass(frozen=True)
class DnsObservation:
    name: str
    cname_chain: tuple[str, ...] = ()
    """Each CNAME target in order, as returned by the resolver."""
    resolves: bool = True
    """False when the final target returns NXDOMAIN - the dangling case."""


@dataclass(frozen=True)
class HttpObservation:
    status: int
    body_excerpt: str = ""


@dataclass(frozen=True)
class TakeoverAssessment:
    name: str
    provider: str | None
    claims: tuple[Claim, ...]
    proof_requires: str | None
    strongest_tag: Tag | None

    @property
    def candidate(self) -> bool:
        """True when there is at least an observed link to a provider."""
        return self.provider is not None

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "provider": self.provider,
            "candidate": self.candidate,
            "strongest_provenance": self.strongest_tag.value if self.strongest_tag else None,
            # Restated so a consumer cannot read a candidate as a finding.
            "proven": False,
            "proof_requires": self.proof_requires,
            "claims": [c.to_dict() for c in self.claims],
        }


def _provider_for(chain: tuple[str, ...], fingerprints) -> tuple[Fingerprint | None, str | None]:
    for target in chain:
        for fp in fingerprints:
            if fp.matches_cname(target):
                return fp, target
    return None, None


def evaluate(
    dns: DnsObservation,
    http: HttpObservation | None = None,
    *,
    fingerprints: tuple[Fingerprint, ...] = FINGERPRINTS,
) -> TakeoverAssessment:
    """Turn observations into provenance-tagged claims. Never proves anything."""

    fp, target = _provider_for(dns.cname_chain, fingerprints)
    if fp is None:
        return TakeoverAssessment(dns.name, None, (), None, None)

    claims = [
        Claim(
            text=f"{dns.name} CNAMEs to {target}, a {fp.provider} endpoint",
            tag=Tag.OBSERVED,
            source=SOURCE,
        )
    ]
    if not dns.resolves:
        claims.append(
            Claim(
                text=f"{target} does not resolve; the record is dangling",
                tag=Tag.OBSERVED,
                source=SOURCE,
            )
        )

    if http is not None:
        hits = fp.matches_body(http.body_excerpt)
        if hits:
            claims.append(
                Claim(
                    text=(
                        f"HTTP {http.status} body carries {fp.provider} unclaimed-resource "
                        f"marker {hits[0]!r}; the resource is probably unclaimed"
                    ),
                    tag=Tag.INFERRED,
                    source=SOURCE,
                )
            )

    strongest = Tag.INFERRED if any(c.tag is Tag.INFERRED for c in claims) else Tag.OBSERVED
    return TakeoverAssessment(dns.name, fp.provider, tuple(claims), fp.proof_requires, strongest)


def require_probe_posture(posture: AuthorityLevel) -> None:
    """Refuse a live resolver or HTTP probe unless the posture allows it.

    The caller passes the *recorded* execution posture. This module has no
    resolver of its own on purpose: at ``LOCAL_FIXTURE`` there is nothing it
    could legitimately query, so it should not be able to.
    """

    if posture < LIVE_PROBE_REQUIRES:
        raise ProbeRefused(
            f"live takeover probing needs execution posture {LIVE_PROBE_REQUIRES.name}; "
            f"recorded posture is {posture.name}. Evaluate fixture observations instead."
        )
