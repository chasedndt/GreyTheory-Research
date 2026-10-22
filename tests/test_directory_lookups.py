"""Stored records of what a public programme directory returned.

The failures that matter here are all forms of one mistake: letting a saved copy
of a public page acquire a standing it never had. Saving something does not make
it trusted, does not make it private, and does not make it permission.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone

import pytest

from greytheory.directory_lookups import (
    DirectoryLookup,
    DirectoryLookupError,
    DirectoryLookupStore,
)

BODY = b'{"programme": "gitlab", "scope": []}'
DIGEST = hashlib.sha256(BODY).hexdigest()
NOW = "2026-09-15T12:00:00Z"


@dataclass(frozen=True)
class _Evidence:
    """Mirrors DirectoryEvidence without importing the fetcher into these tests."""

    identifier: str = "hackerone:gitlab"
    provider_id: str = "hackerone-directory"
    url: str = "https://hackerone.com/gitlab"
    status: int = 200
    content_type: str = "application/json"
    body_sha256: str = DIGEST
    body_bytes: int = len(BODY)
    retrieved_at: str = NOW
    data_class: str = "PUBLIC"
    trust: str = "UNTRUSTED"
    body: bytes = BODY


def _store(tmp_path, audit=None) -> DirectoryLookupStore:
    return DirectoryLookupStore(tmp_path / "directory", allow_in_repository=True, audit=audit)


# -- a saved copy keeps its original standing --------------------------------


def test_a_stored_read_never_claims_authority():
    with pytest.raises(DirectoryLookupError, match="never grants authority"):
        DirectoryLookup(
            identifier="hackerone:gitlab",
            provider_id="hackerone-directory",
            url="https://hackerone.com/gitlab",
            status=200,
            content_type="application/json",
            body_sha256=DIGEST,
            body_bytes=len(BODY),
            retrieved_at=datetime(2026, 9, 15, tzinfo=timezone.utc),
            grants_authority=True,
        )


@pytest.mark.parametrize(
    "field, value",
    [("data_class", "RESTRICTED"), ("trust", "VERIFIED"), ("trust", "CHECKED")],
)
def test_saving_public_untrusted_content_upgrades_neither(field, value):
    kwargs = dict(
        identifier="hackerone:gitlab",
        provider_id="hackerone-directory",
        url="https://hackerone.com/gitlab",
        status=200,
        content_type="application/json",
        body_sha256=DIGEST,
        body_bytes=len(BODY),
        retrieved_at=datetime(2026, 9, 15, tzinfo=timezone.utc),
    )
    kwargs[field] = value
    with pytest.raises(DirectoryLookupError, match="public and untrusted"):
        DirectoryLookup(**kwargs)


def test_a_plain_http_url_is_refused_even_after_the_fact():
    with pytest.raises(DirectoryLookupError, match="HTTPS"):
        DirectoryLookup(
            identifier="hackerone:gitlab",
            provider_id="hackerone-directory",
            url="http://hackerone.com/gitlab",
            status=200,
            content_type="application/json",
            body_sha256=DIGEST,
            body_bytes=len(BODY),
            retrieved_at=datetime(2026, 9, 15, tzinfo=timezone.utc),
        )


def test_an_identifier_names_a_platform_and_a_handle():
    with pytest.raises(DirectoryLookupError, match="platform:handle"):
        DirectoryLookup(
            identifier="gitlab",
            provider_id="hackerone-directory",
            url="https://hackerone.com/gitlab",
            status=200,
            content_type="application/json",
            body_sha256=DIGEST,
            body_bytes=len(BODY),
            retrieved_at=datetime(2026, 9, 15, tzinfo=timezone.utc),
        )


# -- the bytes stay tied to their hash ---------------------------------------


def test_a_recorded_read_keeps_its_body_and_hands_it_back(tmp_path):
    store = _store(tmp_path)
    lookup = store.record(_Evidence(), actor="chase")

    assert lookup.platform == "hackerone"
    assert lookup.handle == "gitlab"
    assert store.body("hackerone:gitlab") == BODY


def test_a_body_that_disagrees_with_the_recorded_hash_is_refused(tmp_path):
    store = _store(tmp_path)
    with pytest.raises(DirectoryLookupError, match="does not match the hash"):
        store.record(_Evidence(), actor="chase", body=b"something else entirely")


def test_tampered_bytes_are_refused_on_the_way_out(tmp_path):
    store = _store(tmp_path)
    lookup = store.record(_Evidence(), actor="chase")
    store.body_path(lookup).write_bytes(b"replaced after the fact")

    with pytest.raises(DirectoryLookupError, match="does not match its recorded hash"):
        store.body("hackerone:gitlab")


def test_a_missing_body_is_reported_rather_than_returned_empty(tmp_path):
    store = _store(tmp_path)
    lookup = store.record(_Evidence(), actor="chase")
    store.body_path(lookup).unlink()

    with pytest.raises(DirectoryLookupError, match="missing"):
        store.body("hackerone:gitlab")


# -- ordinary storage behaviour ----------------------------------------------


def test_re_reading_a_programme_replaces_its_record(tmp_path):
    store = _store(tmp_path)
    store.record(_Evidence(), actor="chase")
    later = b'{"programme": "gitlab", "scope": ["*.gitlab.com"]}'
    store.record(
        _Evidence(
            body=later,
            body_sha256=hashlib.sha256(later).hexdigest(),
            body_bytes=len(later),
            retrieved_at="2026-09-16T09:00:00Z",
        ),
        actor="chase",
    )

    assert len(store.lookups()) == 1
    assert store.body("hackerone:gitlab") == later


def test_several_programmes_are_kept_side_by_side(tmp_path):
    store = _store(tmp_path)
    store.record(_Evidence(), actor="chase")
    other = b"<html>ynab</html>"
    store.record(
        _Evidence(
            identifier="bugcrowd:ynab",
            provider_id="bugcrowd-directory",
            url="https://bugcrowd.com/ynab",
            content_type="text/html",
            body=other,
            body_sha256=hashlib.sha256(other).hexdigest(),
            body_bytes=len(other),
        ),
        actor="chase",
    )

    assert [item.identifier for item in store.lookups()] == [
        "bugcrowd:ynab", "hackerone:gitlab",
    ]


def test_state_survives_a_new_store_instance(tmp_path):
    _store(tmp_path).record(_Evidence(), actor="chase")
    reopened = DirectoryLookupStore(tmp_path / "directory", allow_in_repository=True)

    assert reopened.get("hackerone:gitlab").url == "https://hackerone.com/gitlab"


def test_tampered_state_fails_closed(tmp_path):
    store = _store(tmp_path)
    store.record(_Evidence(), actor="chase")
    store.path.write_text(
        store.path.read_text(encoding="utf-8").replace("hackerone.com", "elsewhere.test"),
        encoding="utf-8",
    )

    with pytest.raises(DirectoryLookupError, match="integrity check failed"):
        store.lookups()


def test_lookups_are_refused_inside_a_repository(tmp_path):
    (tmp_path / ".git").mkdir()
    with pytest.raises(DirectoryLookupError, match="refused inside a git working tree"):
        DirectoryLookupStore(tmp_path / "directory")


def test_the_audit_record_states_what_the_read_was_not(tmp_path):
    written: list[dict] = []

    class _Audit:
        def append(self, *, actor, action, authority_ref=None, detail=None):
            written.append({"action": action, **(detail or {})})

    _store(tmp_path, audit=_Audit()).record(_Evidence(), actor="chase")

    assert written[0]["action"] == "directory.lookup.record"
    # A log that did not say so could later be read as evidence of permission.
    assert written[0]["grants_authority"] is False
    assert written[0]["target_interaction"] is False
    assert written[0]["trust"] == "UNTRUSTED"
