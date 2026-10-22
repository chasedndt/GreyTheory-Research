"""Reachable exposure: a service answered on a port, said as a claim.

An exposure observation is only meaningful against a scope contract. The
collector asks the contract first and emits **nothing** for a host that is not
``IN_SCOPE`` - not a weaker claim, nothing - because a claim about an
out-of-scope host is a record of having looked where the programme said not to.

Provenance, as with every collector:

* ``observed`` - the host answered on the port; the banner, if any, is quoted.
* ``inferred`` - the service is one that is rarely meant to face the internet
  (a datastore, a remote desktop). "Rarely meant to" is a judgement, so it is
  inferred, never checked.
* ``checked``  - never emitted here. Proving an exposure *matters* means
  interacting with the service, which the posture and an operator decide.

Live probing is refused below ``PASSIVE_HTTP``; the module carries no network
code of its own, and a test asserts it.
"""

# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 ChaseInTech

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from greytheory.authority.scope import ScopeClassification
from greytheory.provenance import Claim, Tag
from greytheory_collectors.probe_posture import require_probe_posture  # noqa: F401

SOURCE = "greytheory_collectors.reachable_exposure"

#: Services whose mere reachability is worth an inferred claim. Deliberately
#: short: this is a prompt for a human, not a vulnerability database.
UNEXPECTED_SERVICES: tuple[tuple[int, str, str], ...] = (
    (6379, "redis", "datastore; unauthenticated by default"),
    (27017, "mongodb", "datastore; historically unauthenticated by default"),
    (9200, "elasticsearch", "datastore; REST API with no auth unless configured"),
    (3389, "rdp", "remote desktop; credential and exploit target"),
    (445, "smb", "file sharing; rarely intended to face the internet"),
)


class ScopeOracle(Protocol):
    """The two questions a contract must answer. ``ScopeContract`` satisfies it."""

    def classify(self, asset: str) -> ScopeClassification: ...
    def prohibits(self, technique: str | None) -> bool: ...


@dataclass(frozen=True)
class ExposureObservation:
    host: str
    port: int
    transport: str = "tcp"
    banner: str = ""
    observed_by: str = ""
    """Tool or fixture that produced this. Required; an unattributed
    observation is not evidence."""


@dataclass(frozen=True)
class ExposureAssessment:
    host: str
    port: int
    classification: ScopeClassification
    claims: tuple[Claim, ...]
    refused_reason: str | None = None

    @property
    def strongest_tag(self) -> Tag | None:
        if any(c.tag is Tag.INFERRED for c in self.claims):
            return Tag.INFERRED
        return Tag.OBSERVED if self.claims else None

    def to_dict(self) -> dict:
        return {
            "host": self.host,
            "port": self.port,
            "classification": self.classification.value,
            "strongest_provenance": self.strongest_tag.value if self.strongest_tag else None,
            "proven": False,
            "refused_reason": self.refused_reason,
            "claims": [c.to_dict() for c in self.claims],
        }


def evaluate(obs: ExposureObservation, contract: ScopeOracle) -> ExposureAssessment:
    """Emit claims for an in-scope host only. Out of scope yields no claim."""

    if not obs.observed_by.strip():
        raise ValueError("an exposure observation must name what observed it")

    classification = contract.classify(obs.host)
    if classification is not ScopeClassification.IN_SCOPE:
        return ExposureAssessment(
            obs.host, obs.port, classification, (),
            refused_reason=f"{obs.host} is {classification.value}; no claim is recorded",
        )
    if contract.prohibits("port-scanning"):
        return ExposureAssessment(
            obs.host, obs.port, classification, (),
            refused_reason="the programme prohibits port scanning; the observation is not usable",
        )

    banner = f", banner {obs.banner.strip()!r}" if obs.banner.strip() else ""
    claims = [
        Claim(
            text=f"{obs.host}:{obs.port}/{obs.transport} answered{banner}",
            tag=Tag.OBSERVED,
            source=f"{SOURCE} via {obs.observed_by}",
        )
    ]
    for port, name, why in UNEXPECTED_SERVICES:
        if port == obs.port:
            claims.append(
                Claim(
                    text=f"port {port} is conventionally {name} ({why}); exposure is probably unintended",
                    tag=Tag.INFERRED,
                    source=SOURCE,
                )
            )
            break

    return ExposureAssessment(obs.host, obs.port, classification, tuple(claims))
