"""Safe HTTP misconfiguration checks over a response somebody already has.

"Safe" means two things. The checks read one ordinary response - no crafted
input, no state change - and the module performs no request of its own; the
response is supplied, from a fixture today and from a posture-gated fetch
later. Each check is a small pure function so the list stays reviewable.

Provenance:

* ``observed`` - what the headers literally say, or that a header is absent.
* ``inferred`` - the risk that absence or value usually implies. Inferred
  because a missing header on one response is not a property of the site, and
  a permissive value may be intentional for that endpoint.
* ``checked``  - never. Demonstrating that a misconfiguration is exploitable
  is an experiment, and experiments are planned, budgeted, and approved.

Scope first: no claim for a host not ``IN_SCOPE``.
"""

# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 ChaseInTech

from __future__ import annotations

from dataclasses import dataclass, field

from greytheory.authority.scope import ScopeClassification
from greytheory.provenance import Claim, Tag
from greytheory_collectors.reachable_exposure import ScopeOracle

SOURCE = "greytheory_collectors.http_misconfiguration"


@dataclass(frozen=True)
class HttpResponseObservation:
    host: str
    url_path: str
    status: int
    headers: dict[str, str] = field(default_factory=dict)
    """Header names are matched case-insensitively."""
    body_excerpt: str = ""
    over_tls: bool = True
    observed_by: str = ""


@dataclass(frozen=True)
class MisconfigurationAssessment:
    host: str
    url_path: str
    classification: ScopeClassification
    claims: tuple[Claim, ...]
    checks_run: tuple[str, ...] = ()
    refused_reason: str | None = None

    def to_dict(self) -> dict:
        return {
            "host": self.host,
            "path": self.url_path,
            "classification": self.classification.value,
            "checks_run": list(self.checks_run),
            "proven": False,
            "refused_reason": self.refused_reason,
            "claims": [c.to_dict() for c in self.claims],
        }


def _header(obs: HttpResponseObservation, name: str) -> str | None:
    for k, v in obs.headers.items():
        if k.lower() == name.lower():
            return v
    return None


def _observed(text: str) -> Claim:
    return Claim(text=text, tag=Tag.OBSERVED, source=SOURCE)


def _inferred(text: str) -> Claim:
    return Claim(text=text, tag=Tag.INFERRED, source=SOURCE)


# -- checks: each returns claims for one concern ------------------------------

def check_hsts(obs: HttpResponseObservation) -> list[Claim]:
    if not obs.over_tls:
        return []
    v = _header(obs, "Strict-Transport-Security")
    if v is None:
        return [_observed("Strict-Transport-Security is absent"),
                _inferred("without HSTS a first visit over plain HTTP can be downgraded")]
    return [_observed(f"Strict-Transport-Security: {v}")]


def check_csp(obs: HttpResponseObservation) -> list[Claim]:
    v = _header(obs, "Content-Security-Policy")
    if v is None:
        return [_observed("Content-Security-Policy is absent"),
                _inferred("without CSP an injected script has no second line of defence")]
    out = [_observed(f"Content-Security-Policy: {v}")]
    if "'unsafe-inline'" in v and "script-src" in v:
        out.append(_inferred("script-src permits 'unsafe-inline', which weakens CSP against XSS"))
    return out


def check_cors(obs: HttpResponseObservation) -> list[Claim]:
    origin = _header(obs, "Access-Control-Allow-Origin")
    creds = _header(obs, "Access-Control-Allow-Credentials")
    if origin is None:
        return []
    out = [_observed(f"Access-Control-Allow-Origin: {origin}")]
    if origin.strip() == "*" and (creds or "").strip().lower() == "true":
        out.append(_inferred("wildcard origin with credentials is refused by browsers, "
                             "but reflects a misconfigured CORS policy"))
    return out


def check_server_disclosure(obs: HttpResponseObservation) -> list[Claim]:
    out = []
    for name in ("Server", "X-Powered-By"):
        v = _header(obs, name)
        if v and any(ch.isdigit() for ch in v):
            out.append(_observed(f"{name}: {v}"))
            out.append(_inferred(f"{name} discloses a version, which narrows advisory correlation for an attacker too"))
    return out


def check_directory_listing(obs: HttpResponseObservation) -> list[Claim]:
    if obs.status == 200 and "Index of /" in obs.body_excerpt:
        return [_observed(f"{obs.url_path} returned a directory index"),
                _inferred("a directory listing exposes file names that were not meant to be discovered")]
    return []


CHECKS = (
    ("hsts", check_hsts),
    ("csp", check_csp),
    ("cors", check_cors),
    ("server-disclosure", check_server_disclosure),
    ("directory-listing", check_directory_listing),
)


def evaluate(obs: HttpResponseObservation, contract: ScopeOracle) -> MisconfigurationAssessment:
    if not obs.observed_by.strip():
        raise ValueError("an HTTP response observation must name what observed it")

    classification = contract.classify(obs.host)
    if classification is not ScopeClassification.IN_SCOPE:
        return MisconfigurationAssessment(
            obs.host, obs.url_path, classification, (),
            refused_reason=f"{obs.host} is {classification.value}; no claim is recorded",
        )

    claims: list[Claim] = []
    for _, check in CHECKS:
        claims.extend(check(obs))
    return MisconfigurationAssessment(
        obs.host, obs.url_path, classification, tuple(claims), tuple(n for n, _ in CHECKS)
    )
