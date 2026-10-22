"""What a programme record must declare before it may claim live authority.

The compiler already refuses `PASSIVE_HTTP` and above without a rate limit.
A rate limit alone is not enough to put traffic on someone else's production
systems. Three more things must be declared, and each exists because of a way
real research goes wrong:

* **Identity** - the target's security team must be able to tell a researcher
  from an attacker while the traffic is happening, not afterwards. Unidentified
  traffic gets blocked, or escalated to an incident.
* **Egress** - one declared, publicly routable source address. A declared
  egress that is private or loopback is a statement about where traffic comes
  from that is not true, and `fail_closed` must be set because a tunnel that
  drops back to the researcher's home address defeats the whole arrangement.
* **Accepted terms** - a named human who read the programme's own sources and
  says so in their own words. This mirrors `validation.Attestation`: a model may
  draft it but cannot be its attester, and a few words is a checkbox rather than
  a statement.

Nothing here grants authority. It describes what must be *present and true*
before the compiler will carry a higher ceiling, so that a record cannot claim
live authority by simply asserting it.
"""

# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 ChaseInTech

from __future__ import annotations

import ipaddress
from dataclasses import dataclass, field
from datetime import datetime

#: Authority names that put traffic on a target's systems.
LIVE_AUTHORITY_NAMES = frozenset({"PASSIVE_HTTP", "AUTHENTICATED", "INTRUSIVE"})

#: Above this, a "rate limit" is not limiting anything a human could review.
MAX_DEFENSIBLE_RPS = 20.0

#: Substrings that mean a user agent is pretending to be an ordinary browser.
_BROWSER_MARKERS = ("mozilla/", "chrome/", "safari/", "gecko", "edg/", "opr/")

#: An attester must be a person. Same rule as validation.Attestation.
_NOT_A_PERSON = ("model", "llm", "assistant", "claude", "openai", "gpt", "bot")


class LiveAuthorityError(ValueError):
    """Raised when a live-authority declaration would be untrue or unsafe."""


@dataclass(frozen=True)
class TrafficIdentity:
    """How the target can recognise this traffic while it is arriving."""

    header_name: str
    header_value: str
    user_agent: str

    def __post_init__(self) -> None:
        if not self.header_name.strip():
            raise LiveAuthorityError("an identification header must be named")
        if not self.header_value.strip():
            raise LiveAuthorityError(
                "an identification header with no value identifies nobody"
            )
        agent = self.user_agent.strip()
        if not agent:
            raise LiveAuthorityError("a user agent is required to identify traffic")
        lowered = agent.lower()
        # Impersonating a browser is the opposite of identifying yourself, and
        # it is what an attacker does to blend in.
        for marker in _BROWSER_MARKERS:
            if marker in lowered:
                raise LiveAuthorityError(
                    f"user agent {agent!r} imitates a browser; research traffic "
                    "must announce itself, not blend in"
                )

    def headers(self) -> dict[str, str]:
        return {self.header_name: self.header_value, "User-Agent": self.user_agent}


@dataclass(frozen=True)
class EgressDeclaration:
    """The address the target will actually see, and what happens if it fails."""

    addresses: tuple[str, ...]
    gateway_note: str = ""
    fail_closed: bool = True

    def __post_init__(self) -> None:
        if not self.addresses:
            raise LiveAuthorityError(
                "declare the public address research traffic will come from; "
                "a programme cannot allow-list or attribute what it is not told"
            )
        for raw in self.addresses:
            try:
                address = ipaddress.ip_address(str(raw).strip())
            except ValueError as exc:
                raise LiveAuthorityError(f"{raw!r} is not an IP address") from exc
            # `is_global` is the one correct predicate here: it excludes
            # private, loopback, link-local, multicast and reserved ranges in a
            # single check. It also excludes the RFC 5737 and RFC 3849
            # documentation ranges (203.0.113.0/24, 2001:db8::/32), which is
            # right rather than inconvenient - a documentation address is by
            # definition not where traffic comes from, so it can never be a
            # truthful declared egress.
            if not address.is_global:
                raise LiveAuthorityError(
                    f"{address} is not globally routable; a declared egress "
                    "address must be the address the target will actually see"
                )
        if not self.fail_closed:
            raise LiveAuthorityError(
                "egress must fail closed: if the declared gateway drops, traffic "
                "must stop rather than fall back to the researcher's own address"
            )


@dataclass(frozen=True)
class TermsAcceptance:
    """A person saying they read this programme's rules and accept them."""

    accepted_by: str
    statement: str
    accepted_at: datetime
    source_refs: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        actor = self.accepted_by.strip()
        if not actor:
            raise LiveAuthorityError("terms acceptance must name who accepted them")
        lowered = actor.lower()
        if any(marker in lowered for marker in _NOT_A_PERSON):
            raise LiveAuthorityError(
                "a model may draft an acceptance but cannot be the one who accepts"
            )
        if len(self.statement.strip()) < 20:
            raise LiveAuthorityError(
                "an acceptance must say what was read and agreed; a few words is "
                "a checkbox, not a statement"
            )
        if not self.source_refs:
            raise LiveAuthorityError(
                "name the saved sources that were read; accepting terms without "
                "naming them cannot be checked later"
            )
        if self.accepted_at.tzinfo is None:
            raise LiveAuthorityError("acceptance time must be timezone-aware")


@dataclass(frozen=True)
class LiveAuthorityDeclaration:
    """Everything that must be true before a record may claim live authority."""

    rate_limit_rps: float
    identity: TrafficIdentity
    egress: EgressDeclaration
    terms: TermsAcceptance

    def __post_init__(self) -> None:
        if self.rate_limit_rps <= 0:
            raise LiveAuthorityError("a rate limit must be greater than zero")
        if self.rate_limit_rps > MAX_DEFENSIBLE_RPS:
            raise LiveAuthorityError(
                f"{self.rate_limit_rps} requests/second is not a rate limit a "
                f"human could review; {MAX_DEFENSIBLE_RPS} is the ceiling here"
            )

    def to_dict(self) -> dict[str, object]:
        return {
            "rate_limit_rps": self.rate_limit_rps,
            "identification_header": self.identity.header_name,
            "user_agent": self.identity.user_agent,
            "egress_addresses": list(self.egress.addresses),
            "egress_fail_closed": self.egress.fail_closed,
            "terms_accepted_by": self.terms.accepted_by,
            "terms_source_refs": list(self.terms.source_refs),
            # Restated so a record of the declaration cannot read as permission.
            "grants_authority": False,
        }


def live_authority_ambiguities(programme: dict, max_authority: str) -> list[str]:
    """Reasons this record may not carry `max_authority`, in compiler style.

    Returns an empty list for ceilings at or below ``LOCAL_FIXTURE``: nothing
    here applies to work that never leaves the machine.
    """

    if str(max_authority).upper() not in LIVE_AUTHORITY_NAMES:
        return []

    raw = programme.get("live_authority")
    if not isinstance(raw, dict) or not raw:
        return [
            f"max_authority {max_authority} puts traffic on a target but the "
            "record declares no live_authority block (identity, egress, terms)"
        ]

    try:
        identity = TrafficIdentity(
            header_name=str(raw.get("identification_header") or ""),
            header_value=str(raw.get("identification_value") or ""),
            user_agent=str(raw.get("user_agent") or ""),
        )
        egress_raw = raw.get("egress") or {}
        egress = EgressDeclaration(
            addresses=tuple(str(a) for a in (egress_raw.get("addresses") or ())),
            gateway_note=str(egress_raw.get("gateway_note") or ""),
            fail_closed=bool(egress_raw.get("fail_closed", False)),
        )
        terms_raw = raw.get("terms") or {}
        accepted_at = terms_raw.get("accepted_at")
        if isinstance(accepted_at, str):
            accepted_at = datetime.fromisoformat(accepted_at)
        # A missing acceptance time must not quietly become "now" and pass the
        # timezone check. Absent is absent, and the refusal should say so.
        if accepted_at is None:
            return [
                "live_authority declaration is not usable: terms acceptance "
                "does not say when it was accepted"
            ]
        terms = TermsAcceptance(
            accepted_by=str(terms_raw.get("accepted_by") or ""),
            statement=str(terms_raw.get("statement") or ""),
            accepted_at=accepted_at or datetime.now(),
            source_refs=tuple(str(s) for s in (terms_raw.get("source_refs") or ())),
        )
        LiveAuthorityDeclaration(
            rate_limit_rps=float(programme.get("rate_limit_rps") or 0),
            identity=identity,
            egress=egress,
            terms=terms,
        )
    except LiveAuthorityError as exc:
        return [f"live_authority declaration is not usable: {exc}"]
    except (TypeError, ValueError) as exc:
        return [f"live_authority declaration could not be read: {exc}"]

    return []
