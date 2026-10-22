"""Reachable-exposure collector: scope first, provenance honest, no socket."""

from __future__ import annotations

import inspect

import pytest

from greytheory.authority.gate import AuthorityLevel
from greytheory.authority.scope import ScopeClassification
from greytheory.provenance import Tag
from greytheory_collectors.probe_posture import ProbeRefused, require_probe_posture
from greytheory_collectors.reachable_exposure import (
    ExposureObservation,
    evaluate,
)


class _Contract:
    """Duck-typed stand-in for ScopeContract: classify() and prohibits()."""

    def __init__(self, in_scope=(), prohibited=()):
        self.in_scope, self.prohibited = set(in_scope), set(prohibited)

    def classify(self, asset):
        return ScopeClassification.IN_SCOPE if asset in self.in_scope else ScopeClassification.UNRESOLVED

    def prohibits(self, technique):
        return technique in self.prohibited


CONTRACT = _Contract(in_scope={"api.example.test"})


def _obs(host="api.example.test", port=443, banner="", by="fixture:nmap-2026-09-11"):
    return ExposureObservation(host=host, port=port, banner=banner, observed_by=by)


def test_an_in_scope_answer_is_an_observed_claim():
    a = evaluate(_obs(banner="HTTP/1.1 200 OK"), CONTRACT)

    assert a.classification is ScopeClassification.IN_SCOPE
    assert [c.tag for c in a.claims] == [Tag.OBSERVED]
    assert "banner" in a.claims[0].text and "fixture:nmap" in a.claims[0].source
    assert a.to_dict()["proven"] is False


def test_an_unexpected_service_adds_an_inferred_claim_never_checked():
    a = evaluate(_obs(port=6379), CONTRACT)

    assert a.strongest_tag is Tag.INFERRED
    assert not any(c.is_proven for c in a.claims)
    assert "redis" in a.claims[1].text


def test_out_of_scope_yields_no_claim_at_all():
    """Not a weaker claim - none. A claim about it would record having looked."""

    a = evaluate(_obs(host="other.example.test", port=6379), CONTRACT)

    assert a.claims == ()
    assert a.classification is ScopeClassification.UNRESOLVED
    assert "no claim is recorded" in a.refused_reason


def test_a_programme_that_prohibits_port_scanning_makes_the_observation_unusable():
    a = evaluate(_obs(), _Contract(in_scope={"api.example.test"}, prohibited={"port-scanning"}))

    assert a.claims == () and "prohibits" in a.refused_reason


def test_an_unattributed_observation_is_refused():
    with pytest.raises(ValueError, match="name what observed it"):
        evaluate(_obs(by="  "), CONTRACT)


def test_live_probing_is_refused_below_passive_http():
    with pytest.raises(ProbeRefused, match="LOCAL_FIXTURE"):
        require_probe_posture(AuthorityLevel.LOCAL_FIXTURE, what="port probing")
    require_probe_posture(AuthorityLevel.PASSIVE_HTTP)


def test_the_collector_carries_no_socket():
    import greytheory_collectors.reachable_exposure as m

    src = inspect.getsource(m)
    for banned in ("socket", "asyncio.open_connection", "urllib", "requests", "nmap"):
        assert banned not in src, banned
