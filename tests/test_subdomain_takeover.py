"""Subdomain-takeover collector: honest provenance, no verdicts, no probing."""

from __future__ import annotations

import pytest

from greytheory.authority.gate import AuthorityLevel
from greytheory.provenance import Tag
from greytheory_collectors.subdomain_takeover import (
    DnsObservation,
    HttpObservation,
    ProbeRefused,
    evaluate,
    require_probe_posture,
)
from greytheory_collectors.takeover_fingerprints import FINGERPRINTS


def test_a_cname_into_a_known_provider_is_an_observed_claim_only():
    a = evaluate(DnsObservation("docs.example.test", ("old-team.github.io.",)))

    assert a.candidate and a.provider == "github-pages"
    assert {c.tag for c in a.claims} == {Tag.OBSERVED}
    assert a.strongest_tag is Tag.OBSERVED
    assert a.to_dict()["proven"] is False


def test_a_dangling_record_adds_a_second_observed_fact():
    a = evaluate(DnsObservation("docs.example.test", ("old-team.github.io",), resolves=False))

    texts = [c.text for c in a.claims]
    assert any("dangling" in t for t in texts)
    assert all(c.tag is Tag.OBSERVED for c in a.claims)


def test_a_body_marker_is_inferred_never_checked():
    a = evaluate(
        DnsObservation("cdn.example.test", ("bucket.s3.amazonaws.com",)),
        HttpObservation(404, "<Code>NoSuchBucket</Code>"),
    )

    assert a.strongest_tag is Tag.INFERRED
    assert not any(c.tag is Tag.CHECKED for c in a.claims)
    assert not any(c.is_proven for c in a.claims)
    assert "token" in a.proof_requires


def test_a_marker_without_a_provider_cname_is_nothing():
    """A 404 page alone is not evidence of anything."""

    a = evaluate(
        DnsObservation("www.example.test", ("lb.example.test",)),
        HttpObservation(404, "NoSuchBucket"),
    )
    assert not a.candidate and a.claims == ()


def test_marker_matching_is_case_insensitive_and_suffix_matching_is_exact():
    a = evaluate(
        DnsObservation("x.example.test", ("app.herokuapp.com",)),
        HttpObservation(404, "no such APP"),
    )
    assert a.strongest_tag is Tag.INFERRED

    # "notherokuapp.com" must not match "herokuapp.com".
    b = evaluate(DnsObservation("y.example.test", ("cname.notherokuapp.com",)))
    assert not b.candidate


@pytest.mark.parametrize("fp", FINGERPRINTS, ids=lambda f: f.provider)
def test_every_fingerprint_names_the_human_proof_step(fp):
    assert fp.cname_suffixes and fp.body_markers
    assert "operator" in fp.proof_requires.lower() or "token" in fp.proof_requires.lower()


def test_live_probing_is_refused_below_passive_http():
    with pytest.raises(ProbeRefused, match="LOCAL_FIXTURE"):
        require_probe_posture(AuthorityLevel.LOCAL_FIXTURE)
    with pytest.raises(ProbeRefused):
        require_probe_posture(AuthorityLevel.NONE)
    require_probe_posture(AuthorityLevel.PASSIVE_HTTP)  # allowed


def test_the_module_has_no_resolver_or_socket_of_its_own():
    import inspect

    import greytheory_collectors.subdomain_takeover as m

    src = inspect.getsource(m)
    for banned in ("socket", "dns.resolver", "urllib", "requests", "http.client"):
        assert banned not in src, f"collector must not carry a probe: {banned}"
