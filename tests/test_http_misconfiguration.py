"""HTTP misconfiguration checks: supplied response, scope first, inferred only."""

from __future__ import annotations

import inspect

import pytest

from greytheory.authority.scope import ScopeClassification
from greytheory.provenance import Tag
from greytheory_collectors.http_misconfiguration import (
    CHECKS,
    HttpResponseObservation,
    evaluate,
)


class _Contract:
    def classify(self, asset):
        return ScopeClassification.IN_SCOPE if asset == "www.example.test" else ScopeClassification.UNRESOLVED

    def prohibits(self, technique):
        return False


C = _Contract()
GOOD = {
    "Strict-Transport-Security": "max-age=63072000; includeSubDomains",
    "Content-Security-Policy": "default-src 'self'; script-src 'self'",
    "Server": "nginx",
}


def _obs(headers=None, status=200, body="", tls=True, host="www.example.test", by="fixture:curl"):
    return HttpResponseObservation(host=host, url_path="/", status=status,
                                   headers=headers if headers is not None else dict(GOOD),
                                   body_excerpt=body, over_tls=tls, observed_by=by)


def test_a_well_configured_response_yields_observed_claims_only():
    a = evaluate(_obs(), C)

    assert a.claims and all(c.tag is Tag.OBSERVED for c in a.claims)
    assert a.checks_run == tuple(n for n, _ in CHECKS)
    assert a.to_dict()["proven"] is False


def test_missing_hsts_and_csp_are_observed_absences_with_inferred_risk():
    a = evaluate(_obs(headers={}), C)

    texts = [c.text for c in a.claims]
    assert "Strict-Transport-Security is absent" in texts
    assert "Content-Security-Policy is absent" in texts
    assert sum(c.tag is Tag.INFERRED for c in a.claims) == 2
    assert not any(c.is_proven for c in a.claims)


def test_hsts_is_not_expected_over_plain_http():
    a = evaluate(_obs(headers={}, tls=False), C)
    assert not any("Strict-Transport" in c.text for c in a.claims)


def test_header_names_match_case_insensitively():
    a = evaluate(_obs(headers={"strict-transport-security": "max-age=1", "content-security-policy": "default-src 'self'"}), C)
    assert not any(c.tag is Tag.INFERRED for c in a.claims)


def test_unsafe_inline_script_src_is_inferred_weakness():
    h = dict(GOOD, **{"Content-Security-Policy": "script-src 'self' 'unsafe-inline'"})
    a = evaluate(_obs(headers=h), C)
    assert any("unsafe-inline" in c.text and c.tag is Tag.INFERRED for c in a.claims)


def test_wildcard_cors_with_credentials_is_inferred_misconfiguration():
    h = dict(GOOD, **{"Access-Control-Allow-Origin": "*", "Access-Control-Allow-Credentials": "true"})
    a = evaluate(_obs(headers=h), C)
    assert any("CORS" in c.text and c.tag is Tag.INFERRED for c in a.claims)

    plain = dict(GOOD, **{"Access-Control-Allow-Origin": "*"})
    b = evaluate(_obs(headers=plain), C)
    assert not any("CORS" in c.text for c in b.claims)


def test_version_bearing_server_header_is_disclosure_but_bare_name_is_not():
    a = evaluate(_obs(headers=dict(GOOD, Server="nginx/1.24.0")), C)
    assert any("discloses a version" in c.text for c in a.claims)
    b = evaluate(_obs(), C)  # Server: nginx
    assert not any("discloses a version" in c.text for c in b.claims)


def test_directory_listing_is_detected_only_on_200():
    a = evaluate(_obs(body="<title>Index of /backup</title>"), C)
    assert any("directory index" in c.text for c in a.claims)
    b = evaluate(_obs(status=403, body="Index of /backup"), C)
    assert not any("directory index" in c.text for c in b.claims)


def test_out_of_scope_host_records_nothing():
    a = evaluate(_obs(headers={}, host="other.example.test"), C)
    assert a.claims == () and a.checks_run == ()


def test_unattributed_observation_is_refused():
    with pytest.raises(ValueError, match="name what observed it"):
        evaluate(_obs(by=""), C)


def test_the_module_makes_no_request():
    import greytheory_collectors.http_misconfiguration as m

    src = inspect.getsource(m)
    for banned in ("socket", "urllib", "requests", "http.client", "httpx"):
        assert banned not in src, banned
