"""Reading a public programme directory from the application.

This is the only command in the service that opens an outbound connection, so
the first test here is not about behaviour at all - it is about making sure the
suite itself never reaches a third party. Everything else tests what the command
refuses, because a read that leaves the machine should be hard to trigger by
accident and impossible to trigger without saying so.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone

import pytest

from greytheory.authority.gate import AuthorityLevel
from greytheory.directory_lookups import DirectoryLookupStore
from greytheory_app.contracts import (
    CommandDisposition,
    CommandField,
    CommandKind,
    WorkbenchCommand,
    WorkbenchContractError,
)
from greytheory_app.service import WorkbenchApplicationService

NOW = datetime(2026, 9, 15, 12, 0, tzinfo=timezone.utc)
BODY = b'{"programme": "gitlab"}'


class _FakeResponse:
    def __init__(self, status=200, headers=None, body=BODY):
        self.status = status
        self._headers = headers or {"Content-Type": "application/json"}
        self._body = body

    def getheader(self, name):
        return self._headers.get(name)

    def read(self, limit=None):
        return self._body[:limit] if limit is not None else self._body


class _FakeConnection:
    def __init__(self, response):
        self._response = response
        self.requests = []

    def request(self, method, path, headers=None):
        self.requests.append({"method": method, "path": path, "headers": headers or {}})

    def getresponse(self):
        return self._response

    def close(self):
        pass


def _factory(response=None):
    seen = {}

    def build(host, port, timeout):
        seen["host"] = host
        seen["connection"] = _FakeConnection(response or _FakeResponse())
        return seen["connection"]

    return build, seen


def _service(tmp_path, connection=None):
    return WorkbenchApplicationService(
        directory_lookups=DirectoryLookupStore(
            tmp_path / "directory", allow_in_repository=True
        ),
        directory_connection=connection,
        clock=lambda: NOW,
    )


def _command(fields=None, **over):
    base = dict(
        id="cmd-lookup-1",
        kind=CommandKind.LOOK_UP_PROGRAMME,
        operator_ref="operator-local",
        issued_at=NOW,
        idempotency_key="lookup-1",
        fields=tuple(
            CommandField.from_pair(k, v)
            for k, v in (fields or {"platform": "hackerone", "handle": "gitlab"}).items()
        ),
        requested_authority=AuthorityLevel.NONE,
        human_acknowledged=True,
    )
    base.update(over)
    return WorkbenchCommand(**base)


# -- the suite must not reach a third party ----------------------------------


def test_the_service_never_opens_a_real_connection_in_tests(tmp_path):
    """Guards the whole suite, not this command.

    Without an injected factory the fetcher builds a real HTTPSConnection, which
    would mean a fresh clone running pytest quietly sends requests to a bug
    bounty platform. This must fail loudly rather than rely on everyone
    remembering to inject one.
    """

    import greytheory_intelligence.directory_fetcher as fetcher

    opened: list[str] = []

    class _Tripwire:
        def __init__(self, *args, **kwargs):
            opened.append("a real connection was opened")
            raise AssertionError("the test suite attempted real network I/O")

    original = fetcher.http.client.HTTPSConnection
    fetcher.http.client.HTTPSConnection = _Tripwire
    try:
        factory, _ = _factory()
        result = _service(tmp_path, factory).handle(_command())
        assert result.disposition is CommandDisposition.ACCEPTED
    finally:
        fetcher.http.client.HTTPSConnection = original

    assert opened == []


# -- the contract ------------------------------------------------------------


def test_a_directory_read_carries_no_execution_authority():
    with pytest.raises(WorkbenchContractError, match="no execution authority"):
        _command(requested_authority=AuthorityLevel.LOCAL_FIXTURE)


def test_a_request_leaving_the_machine_requires_acknowledgement():
    # The shortlist commands deliberately do not ask for this. This one does,
    # because something leaves the machine.
    with pytest.raises(WorkbenchContractError, match="requires explicit human acknowledgement"):
        _command(human_acknowledged=False)


# -- what it does and refuses ------------------------------------------------


def test_a_successful_read_is_stored_and_says_what_it_is_not(tmp_path):
    factory, seen = _factory()
    service = _service(tmp_path, factory)
    result = service.handle(_command())

    assert result.disposition is CommandDisposition.ACCEPTED
    assert seen["host"] == "hackerone.com"
    assert "grants no authority" in result.message
    assert result.record_refs == ("lookup:hackerone:gitlab",)

    stored = service.directory_lookups.get("hackerone:gitlab")
    assert stored.url == "https://hackerone.com/gitlab"
    assert stored.body_sha256 == hashlib.sha256(BODY).hexdigest()
    assert service.directory_lookups.body("hackerone:gitlab") == BODY


def test_the_read_sends_no_credential(tmp_path):
    factory, seen = _factory()
    _service(tmp_path, factory).handle(_command())

    sent = seen["connection"].requests[0]
    assert sent["method"] == "GET"
    names = {key.lower() for key in sent["headers"]}
    assert "authorization" not in names and "cookie" not in names


def test_a_redirect_refusal_reaches_the_operator_in_the_fetchers_words(tmp_path):
    factory, _ = _factory(_FakeResponse(302, {"Location": "https://elsewhere.test"}, b""))
    result = _service(tmp_path, factory).handle(_command())

    assert result.disposition is CommandDisposition.INVALID
    assert "redirect" in result.message


def test_an_unknown_platform_is_refused(tmp_path):
    factory, _ = _factory()
    result = _service(tmp_path, factory).handle(
        _command({"platform": "notaplatform", "handle": "x"})
    )
    assert result.disposition is CommandDisposition.INVALID
    assert "unknown intelligence provider" in result.message


def test_nothing_is_stored_when_the_read_is_refused(tmp_path):
    factory, _ = _factory(_FakeResponse(403, body=b"{}"))
    service = _service(tmp_path, factory)
    result = service.handle(_command())

    assert result.disposition is CommandDisposition.INVALID
    assert service.directory_lookups.lookups() == ()


def test_without_a_store_the_command_is_refused_rather_than_ignored():
    service = WorkbenchApplicationService(clock=lambda: NOW)
    result = service.handle(_command())

    assert result.disposition is CommandDisposition.INVALID
    assert "no directory lookup store" in result.message
