"""Technology/advisory correlation: "this version is within an affected range".

Two inputs, both supplied rather than fetched:

* a technology observation - product and version as seen on an in-scope host,
  with the observer named;
* advisories - brought by the operator or by Scope Watch. **None ship with
  this module.** A bundled advisory would be a claim about a real product
  that nobody here verified, and a stale one would mislead with authority.

Provenance:

* ``observed`` - the product and version were seen. What the banner said.
* ``inferred`` - the version falls inside an advisory's affected range.
  Inferred because banners lie, backports exist, and "affected" is not
  "exploitable in this deployment".
* ``checked``  - never. Confirming an advisory applies means exercising it,
  which the execution posture and an operator decide.

Scope first, as with every collector: no claim for a host not ``IN_SCOPE``.
"""

# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 ChaseInTech

from __future__ import annotations

import re
from dataclasses import dataclass

from greytheory.authority.scope import ScopeClassification
from greytheory.provenance import Claim, Tag
from greytheory_collectors.reachable_exposure import ScopeOracle

SOURCE = "greytheory_collectors.advisory_correlation"

_VERSION_RE = re.compile(r"^\d+(\.\d+)*$")


class VersionError(ValueError):
    """Raised for a version string that cannot be compared honestly."""


def parse_version(text: str) -> tuple[int, ...]:
    """Dotted integers only. Anything richer is refused rather than guessed:
    ``2.4.1-beta`` and ``2.4.1`` ordering is a policy, not a fact."""

    v = text.strip()
    if not _VERSION_RE.match(v):
        raise VersionError(f"cannot compare version {text!r}; dotted integers only")
    return tuple(int(p) for p in v.split("."))


@dataclass(frozen=True)
class Advisory:
    id: str
    """Stable identifier, e.g. a CVE or vendor bulletin id, as the operator supplied it."""
    product: str
    affected_from: str
    """Inclusive lower bound."""
    fixed_in: str
    """Exclusive upper bound - the first version that is not affected."""
    summary: str
    supplied_by: str
    """Who brought this advisory in. Required; unattributed advisories are refused."""

    def covers(self, version: str) -> bool:
        v = parse_version(version)
        return parse_version(self.affected_from) <= v < parse_version(self.fixed_in)


@dataclass(frozen=True)
class TechnologyObservation:
    host: str
    product: str
    version: str
    observed_by: str


@dataclass(frozen=True)
class CorrelationAssessment:
    host: str
    product: str
    version: str
    classification: ScopeClassification
    claims: tuple[Claim, ...]
    matched_advisories: tuple[str, ...] = ()
    refused_reason: str | None = None

    def to_dict(self) -> dict:
        return {
            "host": self.host,
            "product": self.product,
            "version": self.version,
            "classification": self.classification.value,
            "matched_advisories": list(self.matched_advisories),
            "proven": False,
            "refused_reason": self.refused_reason,
            "claims": [c.to_dict() for c in self.claims],
        }


def correlate(
    obs: TechnologyObservation,
    advisories: tuple[Advisory, ...],
    contract: ScopeOracle,
) -> CorrelationAssessment:
    """Observed version, inferred exposure to supplied advisories. No verdict."""

    if not obs.observed_by.strip():
        raise ValueError("a technology observation must name what observed it")
    for adv in advisories:
        if not adv.supplied_by.strip():
            raise ValueError(f"advisory {adv.id} does not say who supplied it; refused")

    classification = contract.classify(obs.host)
    if classification is not ScopeClassification.IN_SCOPE:
        return CorrelationAssessment(
            obs.host, obs.product, obs.version, classification, (),
            refused_reason=f"{obs.host} is {classification.value}; no claim is recorded",
        )

    claims = [
        Claim(
            text=f"{obs.host} presents {obs.product} {obs.version}",
            tag=Tag.OBSERVED,
            source=f"{SOURCE} via {obs.observed_by}",
        )
    ]
    matched: list[str] = []
    for adv in advisories:
        if adv.product.lower() != obs.product.lower():
            continue
        try:
            hit = adv.covers(obs.version)
        except VersionError as exc:
            # A version we cannot order is not evidence either way. Say so
            # rather than silently skipping the advisory.
            claims.append(Claim(text=f"{adv.id} not correlated: {exc}", tag=Tag.OBSERVED, source=SOURCE))
            continue
        if hit:
            matched.append(adv.id)
            claims.append(
                Claim(
                    text=(
                        f"{obs.product} {obs.version} is within {adv.id}'s affected range "
                        f"[{adv.affected_from}, {adv.fixed_in}); possibly affected - {adv.summary}"
                    ),
                    tag=Tag.INFERRED,
                    source=f"{SOURCE} (advisory supplied by {adv.supplied_by})",
                )
            )

    return CorrelationAssessment(
        obs.host, obs.product, obs.version, classification, tuple(claims), tuple(matched)
    )
