"""Bounded public-directory reads authorised by ADR-0029 tier 1.

Every test here drives the fetcher through an injected fake connection, so the
suite performs no real network I/O. What is being tested is that the declared
boundaries are enforced in code rather than trusted to the caller.
"""

from __future__ import annotations

import pytest

from greytheory_intelligence.directory_fetcher import (
    DirectoryFetchError,
    build_directory_url,
    fetch_directory,
)
from greytheory_intelligence.registry import build_intelligence_plan


class _FakeResponse:
    def __init__(self, status, headers, body):
        self.status = status
        self._headers = headers
        self._body = body

    def getheader(self, name):
        return self._headers.get(name)

    def read(self, limit=None):
        return self._body[:limit] if limit is not None else self._body


class _FakeConnection:
    """Records exactly what the fetcher sent, so headers can be asserted."""

    def __init__(self, response):
        self._response = response
        self.requests = []
        self.closed = False

    def request(self, method, path, headers=None):
        self.requests.append({"method": method, "path": path, "headers": headers or {}})

    def getresponse(self):
        return self._response

    def close(self):
        self.closed = True


def _factory(response):
    holder = {}

    def build(host, port, timeout):
        holder["connection"] = _FakeConnection(response)
        holder["host"] = host
        holder["port"] = port
        holder["timeout"] = timeout
        return holder["connection"]

    return build, holder


def _plan(identifier="hackerone:gitlab", provider="hackerone-directory"):
    return build_intelligence_plan(provider, identifier)


def test_a_directory_plan_resolves_to_its_exact_authorised_url():
    assert build_directory_url(_plan()) == "https://hackerone.com/gitlab"


def test_a_successful_read_produces_public_untrusted_evidence():
    body = b'{"programme": "gitlab"}'
    factory, holder = _factory(_FakeResponse(200, {"Content-Type": "application/json"}, body))

    evidence = fetch_directory(_plan(), connection_factory=factory)

    assert evidence.status == 200
    assert evidence.body_bytes == len(body)
    assert evidence.data_class == "PUBLIC"
    assert evidence.trust == "UNTRUSTED"
    assert evidence.grants_authority is False
    assert evidence.target_interaction is False
    assert evidence.redirects_followed == 0
    assert holder["connection"].closed is True


def test_the_read_sends_no_credential_of_any_kind():
    factory, holder = _factory(_FakeResponse(200, {"Content-Type": "application/json"}, b"{}"))

    evidence = fetch_directory(_plan(), connection_factory=factory)

    sent = holder["connection"].requests[0]
    assert sent["method"] == "GET"
    names = {key.lower() for key in sent["headers"]}
    assert "authorization" not in names
    assert "cookie" not in names
    assert not any("token" in name or "api-key" in name for name in names)
    assert evidence.credentials_sent is False


def test_a_redirect_is_refused_rather_than_followed():
    factory, _ = _factory(_FakeResponse(302, {"Location": "https://elsewhere.example"}, b""))

    with pytest.raises(DirectoryFetchError, match="redirect"):
        fetch_directory(_plan(), connection_factory=factory)


def test_an_oversized_response_is_refused_at_the_ceiling():
    oversized = b"x" * 4_000_001
    factory, _ = _factory(_FakeResponse(200, {"Content-Type": "application/json"}, oversized))

    with pytest.raises(DirectoryFetchError, match="ceiling"):
        fetch_directory(_plan(), connection_factory=factory)


def test_an_unexpected_content_type_is_refused():
    factory, _ = _factory(_FakeResponse(200, {"Content-Type": "application/octet-stream"}, b"\x00"))

    with pytest.raises(DirectoryFetchError, match="content type"):
        fetch_directory(_plan(), connection_factory=factory)


def test_a_non_200_status_is_refused():
    factory, _ = _factory(_FakeResponse(403, {"Content-Type": "application/json"}, b"{}"))

    with pytest.raises(DirectoryFetchError, match="status 403"):
        fetch_directory(_plan(), connection_factory=factory)


def test_an_advisory_provider_cannot_be_used_for_a_directory_read():
    plan = build_intelligence_plan("osv", "CVE-2026-1234")
    with pytest.raises(DirectoryFetchError, match="directory reads only"):
        fetch_directory(plan, connection_factory=_factory(_FakeResponse(200, {}, b""))[0])


def test_the_identifier_platform_must_match_its_provider():
    # A bugcrowd handle may not be read through the HackerOne provider.
    plan = build_intelligence_plan("hackerone-directory", "bugcrowd:ynab")
    with pytest.raises(DirectoryFetchError, match="does not match"):
        build_directory_url(plan)


@pytest.mark.parametrize(
    "provider_id",
    ["hackerone-directory", "bugcrowd-directory", "intigriti-directory", "yeswehack-directory"],
)
def test_every_approved_platform_resolves_over_https_only(provider_id):
    platform = provider_id.removesuffix("-directory")
    url = build_directory_url(build_intelligence_plan(provider_id, f"{platform}:example"))
    assert url.startswith("https://")


def test_the_fetcher_module_opens_no_plain_http_client():
    from pathlib import Path

    source = Path("greytheory_intelligence/directory_fetcher.py").read_text(encoding="utf-8")
    assert "HTTPConnection" not in source.replace("HTTPSConnection", "")
    assert "requests" not in source
    assert "urllib.request" not in source
