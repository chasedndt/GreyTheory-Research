"""What a record must declare before it may claim live authority.

Each refusal here corresponds to a way real bug bounty research goes wrong:
traffic nobody can attribute, a declared source address that is not the real
one, a tunnel that silently falls back to the researcher's home connection, or
terms "accepted" by nobody in particular.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from greytheory.authority.live_authority import (
    MAX_DEFENSIBLE_RPS,
    EgressDeclaration,
    LiveAuthorityDeclaration,
    LiveAuthorityError,
    TermsAcceptance,
    TrafficIdentity,
    live_authority_ambiguities,
)

NOW = datetime(2026, 9, 14, 12, 0, tzinfo=timezone.utc)


def _identity(**over):
    base = dict(
        header_name="X-Bug-Bounty",
        header_value="chaseintech",
        user_agent="GreyTheory-research/1 (+chaseintech; authorised programme testing)",
    )
    base.update(over)
    return TrafficIdentity(**base)


def _egress(**over):
    # Deliberately a globally routable address. The RFC 5737 documentation
    # ranges (203.0.113.0/24 and friends) cannot be used here: Python
    # classifies them as private, so the module rejects them - correctly, since
    # a documentation address is by definition not where traffic comes from.
    base = dict(addresses=("51.15.44.201",), gateway_note="WireGuard via research VPS", fail_closed=True)
    base.update(over)
    return EgressDeclaration(**base)


def _terms(**over):
    base = dict(
        accepted_by="chase",
        statement="Read the GitLab programme guidelines and HackerOne core ineligible list, and accept them.",
        accepted_at=NOW,
        source_refs=("sources/gitlab-programme-guidelines.md",),
    )
    base.update(over)
    return TermsAcceptance(**base)


def _declaration(**over):
    base = dict(rate_limit_rps=2.0, identity=_identity(), egress=_egress(), terms=_terms())
    base.update(over)
    return LiveAuthorityDeclaration(**base)


# -- identity ----------------------------------------------------------------

def test_a_complete_declaration_is_accepted_and_grants_nothing():
    record = _declaration().to_dict()

    assert record["grants_authority"] is False
    assert record["egress_fail_closed"] is True
    assert record["identification_header"] == "X-Bug-Bounty"


def test_a_browser_imitating_user_agent_is_refused():
    """Blending in is what an attacker does; identification is the point."""

    with pytest.raises(LiveAuthorityError, match="imitates a browser"):
        _identity(user_agent="Mozilla/5.0 (Windows NT 10.0) Chrome/120.0 Safari/537.36")


def test_identification_must_actually_identify():
    with pytest.raises(LiveAuthorityError, match="must be named"):
        _identity(header_name="  ")
    with pytest.raises(LiveAuthorityError, match="identifies nobody"):
        _identity(header_value="")
    with pytest.raises(LiveAuthorityError, match="user agent is required"):
        _identity(user_agent=" ")


def test_the_identity_renders_the_headers_traffic_will_carry():
    headers = _identity().headers()
    assert headers["X-Bug-Bounty"] == "chaseintech"
    assert "GreyTheory-research" in headers["User-Agent"]


# -- egress ------------------------------------------------------------------

@pytest.mark.parametrize("address", ["192.168.1.10", "127.0.0.1", "10.0.0.5", "169.254.1.1"])
def test_a_non_routable_egress_address_is_refused(address):
    """Declaring an address the target cannot see states something untrue."""

    with pytest.raises(LiveAuthorityError, match="not globally routable"):
        _egress(addresses=(address,))


def test_egress_must_be_declared_at_all():
    with pytest.raises(LiveAuthorityError, match="declare the public address"):
        _egress(addresses=())


def test_a_malformed_address_is_refused():
    with pytest.raises(LiveAuthorityError, match="not an IP address"):
        _egress(addresses=("not-an-ip",))


def test_egress_that_does_not_fail_closed_is_refused():
    """A dropped tunnel must stop traffic, not reveal the researcher's own IP."""

    with pytest.raises(LiveAuthorityError, match="fail closed"):
        _egress(fail_closed=False)


def test_ipv6_is_accepted_when_routable():
    # Not 2001:db8::/32 - that is the IPv6 documentation prefix, and private.
    assert _egress(addresses=("2606:4700:4700::1111",)) is not None


# -- terms -------------------------------------------------------------------

def test_a_model_cannot_accept_terms():
    for actor in ("claude", "an llm assistant", "gpt-5", "greytheory bot"):
        with pytest.raises(LiveAuthorityError, match="cannot be the one who accepts"):
            _terms(accepted_by=actor)


def test_acceptance_must_be_a_statement_not_a_checkbox():
    with pytest.raises(LiveAuthorityError, match="checkbox"):
        _terms(statement="ok agreed")


def test_acceptance_must_name_the_sources_that_were_read():
    with pytest.raises(LiveAuthorityError, match="name the saved sources"):
        _terms(source_refs=())


def test_acceptance_time_must_be_timezone_aware():
    with pytest.raises(LiveAuthorityError, match="timezone-aware"):
        _terms(accepted_at=datetime(2026, 9, 14, 12, 0))


# -- rate limit --------------------------------------------------------------

@pytest.mark.parametrize("rps", [0, -1.0])
def test_a_rate_limit_must_be_positive(rps):
    with pytest.raises(LiveAuthorityError, match="greater than zero"):
        _declaration(rate_limit_rps=rps)


def test_a_rate_limit_nobody_could_review_is_refused():
    with pytest.raises(LiveAuthorityError, match="not a rate limit"):
        _declaration(rate_limit_rps=MAX_DEFENSIBLE_RPS + 1)


# -- the compiler-facing entry point ----------------------------------------

def _record(**over):
    base = {
        "rate_limit_rps": 2.0,
        "live_authority": {
            "identification_header": "X-Bug-Bounty",
            "identification_value": "chaseintech",
            "user_agent": "GreyTheory-research/1 (+chaseintech)",
            "egress": {"addresses": ["51.15.44.201"], "fail_closed": True},
            "terms": {
                "accepted_by": "chase",
                "statement": "Read the programme guidelines and ineligible list, and accept them.",
                "accepted_at": NOW.isoformat(),
                "source_refs": ["sources/gitlab-programme-guidelines.md"],
            },
        },
    }
    base.update(over)
    return base


@pytest.mark.parametrize("level", ["LOCAL_FIXTURE", "NONE", "local_fixture"])
def test_nothing_is_required_of_work_that_never_leaves_the_machine(level):
    assert live_authority_ambiguities({}, level) == []


def test_live_authority_without_a_declaration_is_an_ambiguity():
    issues = live_authority_ambiguities({"rate_limit_rps": 2.0}, "PASSIVE_HTTP")
    assert len(issues) == 1 and "declares no live_authority block" in issues[0]


def test_a_complete_record_produces_no_ambiguity():
    assert live_authority_ambiguities(_record(), "PASSIVE_HTTP") == []


def test_an_unusable_declaration_is_reported_not_raised():
    """The compiler collects reasons; it does not crash on a bad record."""

    bad = _record()
    bad["live_authority"]["egress"]["fail_closed"] = False

    issues = live_authority_ambiguities(bad, "AUTHENTICATED")
    assert len(issues) == 1 and "fail closed" in issues[0]


def test_every_live_level_is_covered():
    for level in ("PASSIVE_HTTP", "AUTHENTICATED", "INTRUSIVE"):
        assert live_authority_ambiguities({}, level), f"{level} must require a declaration"
