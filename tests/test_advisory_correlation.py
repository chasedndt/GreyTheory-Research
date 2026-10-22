"""Advisory correlation: supplied advisories, ordered versions, inferred only."""

from __future__ import annotations

import inspect

import pytest

from greytheory.authority.scope import ScopeClassification
from greytheory.provenance import Tag
from greytheory_collectors.advisory_correlation import (
    Advisory,
    TechnologyObservation,
    VersionError,
    correlate,
    parse_version,
)


class _Contract:
    def __init__(self, in_scope=()):
        self.in_scope = set(in_scope)

    def classify(self, asset):
        return ScopeClassification.IN_SCOPE if asset in self.in_scope else ScopeClassification.OUT_OF_SCOPE

    def prohibits(self, technique):
        return False


CONTRACT = _Contract({"www.example.test"})
ADV = Advisory(
    id="EXAMPLE-2026-0001", product="ExampleServer", affected_from="2.4.0",
    fixed_in="2.4.9", summary="request smuggling in the proxy module",
    supplied_by="operator:chase",
)


def _obs(version="2.4.3", host="www.example.test", product="ExampleServer", by="fixture:banner"):
    return TechnologyObservation(host=host, product=product, version=version, observed_by=by)


def test_version_inside_the_range_is_inferred_never_checked():
    a = correlate(_obs("2.4.3"), (ADV,), CONTRACT)

    assert [c.tag for c in a.claims] == [Tag.OBSERVED, Tag.INFERRED]
    assert a.matched_advisories == ("EXAMPLE-2026-0001",)
    assert not any(c.is_proven for c in a.claims)
    assert "supplied by operator:chase" in a.claims[1].source
    assert a.to_dict()["proven"] is False


@pytest.mark.parametrize("version", ["2.3.9", "2.4.9", "2.5.0", "3.0"])
def test_versions_outside_the_range_only_yield_the_observation(version):
    a = correlate(_obs(version), (ADV,), CONTRACT)
    assert [c.tag for c in a.claims] == [Tag.OBSERVED] and a.matched_advisories == ()


def test_range_bounds_are_inclusive_from_and_exclusive_fixed_in():
    assert ADV.covers("2.4.0") and not ADV.covers("2.4.9")


def test_dotted_versions_compare_numerically_not_lexically():
    assert parse_version("2.10") > parse_version("2.9")


def test_a_version_that_cannot_be_ordered_is_said_not_skipped():
    a = correlate(_obs("2.4.1-beta"), (ADV,), CONTRACT)

    assert a.matched_advisories == ()
    assert any("not correlated" in c.text and c.tag is Tag.OBSERVED for c in a.claims)
    with pytest.raises(VersionError):
        parse_version("2.4.1-beta")


def test_a_different_product_is_ignored():
    a = correlate(_obs(product="OtherServer"), (ADV,), CONTRACT)
    assert a.matched_advisories == () and len(a.claims) == 1


def test_out_of_scope_host_records_no_claim():
    a = correlate(_obs(host="other.example.test"), (ADV,), CONTRACT)
    assert a.claims == () and a.classification is ScopeClassification.OUT_OF_SCOPE


def test_unattributed_inputs_are_refused():
    with pytest.raises(ValueError, match="name what observed it"):
        correlate(_obs(by=""), (ADV,), CONTRACT)
    bad = Advisory("X-1", "ExampleServer", "1.0", "2.0", "s", supplied_by=" ")
    with pytest.raises(ValueError, match="who supplied it"):
        correlate(_obs(), (bad,), CONTRACT)


def test_no_advisories_ship_with_the_module():
    import greytheory_collectors.advisory_correlation as m

    src = inspect.getsource(m)
    assert "CVE-" not in src, "a bundled advisory would be an unverified claim about a real product"
    for banned in ("socket", "urllib", "requests"):
        assert banned not in src
