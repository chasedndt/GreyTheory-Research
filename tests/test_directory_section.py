"""The directory-lookup read model.

The risk this section carries is not a wrong number: it is a saved copy of a
public page being read as though it were reviewed scope. Most of these tests are
about that distinction surviving into the wire format.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from greytheory_app.contracts import ReadinessStatus
from greytheory_app.directory_section import build_directory_section

RETRIEVED = datetime(2026, 9, 15, 12, 0, tzinfo=timezone.utc)


@dataclass(frozen=True)
class _Lookup:
    identifier: str = "hackerone:gitlab"
    provider_id: str = "hackerone-directory"
    url: str = "https://hackerone.com/gitlab"
    status: int = 200
    content_type: str = "application/json"
    body_sha256: str = "a" * 64
    body_bytes: int = 2048
    retrieved_at: datetime = RETRIEVED
    data_class: str = "PUBLIC"
    trust: str = "UNTRUSTED"

    @property
    def platform(self) -> str:
        return self.identifier.split(":", 1)[0]

    @property
    def handle(self) -> str:
        return self.identifier.split(":", 1)[1]


class _Store:
    def __init__(self, lookups=(), error=None):
        self._lookups = tuple(lookups)
        self._error = error

    def lookups(self):
        if self._error is not None:
            raise self._error
        return self._lookups


def _attrs(record):
    return dict(record.attributes)


def test_no_store_reads_as_unknown_not_as_nothing_read():
    section = build_directory_section(None)
    assert section.status is ReadinessStatus.UNKNOWN


def test_a_failing_store_fails_closed():
    section = build_directory_section(_Store(error=RuntimeError("integrity check failed")))

    assert section.status is ReadinessStatus.BLOCKED
    assert "failed closed" in section.note


def test_an_empty_store_states_what_a_lookup_is_before_you_rely_on_one():
    section = build_directory_section(_Store())

    assert section.status is ReadinessStatus.EMPTY
    assert "not a scope contract" in section.note
    assert "grants no authority" in section.note


def test_a_stored_lookup_carries_where_it_came_from_and_how_big_it_was():
    section = build_directory_section(_Store([_Lookup()]))
    record = section.records[0]
    attributes = _attrs(record)

    assert record.detail == "https://hackerone.com/gitlab"
    assert attributes["platform"] == "hackerone"
    assert attributes["handle"] == "gitlab"
    assert attributes["body_bytes"] == "2048"
    assert attributes["body_sha256"] == "a" * 64
    assert attributes["retrieved_at"].startswith("2026-09-15")


def test_every_record_restates_that_it_is_public_untrusted_and_grants_nothing():
    section = build_directory_section(_Store([
        _Lookup(),
        _Lookup(identifier="bugcrowd:ynab", url="https://bugcrowd.com/ynab"),
    ]))

    for record in section.records:
        attributes = _attrs(record)
        assert attributes["data_class"] == "PUBLIC"
        assert attributes["trust"] == "UNTRUSTED"
        # The saved copy of a public page must never read as permission.
        assert attributes["grants_authority"] == "false"


def test_counts_cover_both_how_many_and_how_much():
    section = build_directory_section(_Store([
        _Lookup(body_bytes=1000),
        _Lookup(identifier="bugcrowd:ynab", url="https://bugcrowd.com/ynab", body_bytes=2500),
    ]))
    metrics = {metric.label: metric.value for metric in section.metrics}

    assert metrics["Programmes read"] == "2"
    assert metrics["Bytes retrieved"] == "3500"


def test_records_are_ordered_and_uniquely_identified():
    section = build_directory_section(_Store([
        _Lookup(identifier="yeswehack:zeta", url="https://yeswehack.com/zeta"),
        _Lookup(identifier="bugcrowd:alpha", url="https://bugcrowd.com/alpha"),
    ]))
    ids = [record.id for record in section.records]

    assert ids == ["lookup:bugcrowd:alpha", "lookup:yeswehack:zeta"]
    assert len(ids) == len(set(ids))
