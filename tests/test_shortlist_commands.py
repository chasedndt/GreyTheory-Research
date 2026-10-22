"""Curating the shortlist through the application, and reading it back.

These exercise the real store against a temporary root rather than a fake. The
wiring between the service and the store is the thing most likely to be wrong,
and a fake would agree with whatever interface I had imagined.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from greytheory.authority.gate import AuthorityLevel
from greytheory.shortlist import ShortlistOutcome, ShortlistStatus, ShortlistStore
from greytheory_app.contracts import (
    CommandDisposition,
    CommandField,
    CommandKind,
    ReadinessStatus,
    WorkbenchCommand,
    WorkbenchContractError,
)
from greytheory_app.service import WorkbenchApplicationService
from greytheory_app.shortlist_section import build_shortlist_section

NOW = datetime(2026, 9, 15, 12, 0, tzinfo=timezone.utc)


def _store(tmp_path) -> ShortlistStore:
    return ShortlistStore(tmp_path / "shortlist", allow_in_repository=True)


def _service(store) -> WorkbenchApplicationService:
    return WorkbenchApplicationService(shortlist=store, clock=lambda: NOW)


def _command(kind, fields, *, key="k1", **over) -> WorkbenchCommand:
    base = dict(
        id="cmd-1",
        kind=kind,
        operator_ref="operator-local",
        issued_at=NOW,
        idempotency_key=key,
        fields=tuple(CommandField.from_pair(k, v) for k, v in fields.items()),
        requested_authority=AuthorityLevel.NONE,
    )
    base.update(over)
    return WorkbenchCommand(**base)


# -- the contract ------------------------------------------------------------


@pytest.mark.parametrize(
    "kind",
    [
        CommandKind.SHORTLIST_PROGRAMME,
        CommandKind.ARCHIVE_PROGRAMME,
        CommandKind.RESTORE_PROGRAMME,
    ],
)
def test_curating_the_shortlist_carries_no_execution_authority(kind):
    with pytest.raises(WorkbenchContractError, match="no execution authority"):
        _command(kind, {"programme_id": "p"}, requested_authority=AuthorityLevel.LOCAL_FIXTURE)


def test_curation_does_not_demand_acknowledgement_ceremony():
    """Deliberate: these are cheap and reversible. A ceremony on every one
    would train the operator to click through the ones that matter."""

    command = _command(CommandKind.SHORTLIST_PROGRAMME, {"programme_id": "p"})
    assert command.human_acknowledged is False


# -- shortlisting ------------------------------------------------------------


def test_shortlisting_records_an_intention_and_says_it_grants_nothing(tmp_path):
    store = _store(tmp_path)
    result = _service(store).handle(
        _command(CommandKind.SHORTLIST_PROGRAMME, {"programme_id": "hackerone-gitlab-public"})
    )

    assert result.disposition is CommandDisposition.ACCEPTED
    assert "grants no authority" in result.message
    assert result.record_refs == ("shortlist:hackerone-gitlab-public",)
    assert [e.programme_id for e in store.active()] == ["hackerone-gitlab-public"]


def test_an_unregistered_programme_can_still_be_shortlisted(tmp_path):
    """Shortlisting is what leads someone to register and review a programme,
    so requiring registration first would make the front door unreachable."""

    store = _store(tmp_path)
    result = _service(store).handle(
        _command(CommandKind.SHORTLIST_PROGRAMME, {"programme_id": "never-registered"})
    )
    assert result.disposition is CommandDisposition.ACCEPTED


def test_shortlisting_twice_surfaces_the_stores_own_refusal(tmp_path):
    store = _store(tmp_path)
    service = _service(store)
    service.handle(_command(CommandKind.SHORTLIST_PROGRAMME, {"programme_id": "p"}))
    result = service.handle(
        _command(CommandKind.SHORTLIST_PROGRAMME, {"programme_id": "p"}, key="k2")
    )

    assert result.disposition is CommandDisposition.INVALID
    assert "already shortlisted" in result.message


# -- archiving and restoring -------------------------------------------------


def test_archive_then_restore_is_a_round_trip(tmp_path):
    store = _store(tmp_path)
    service = _service(store)
    service.handle(_command(CommandKind.SHORTLIST_PROGRAMME, {"programme_id": "p"}))

    archived = service.handle(
        _command(
            CommandKind.ARCHIVE_PROGRAMME,
            {"programme_id": "p", "outcome": "finished", "note": "paid out"},
            key="k2",
        )
    )
    assert archived.disposition is CommandDisposition.ACCEPTED
    assert "can be restored at any time" in archived.message
    assert store.get("p").outcome is ShortlistOutcome.FINISHED

    restored = service.handle(
        _command(CommandKind.RESTORE_PROGRAMME, {"programme_id": "p"}, key="k3")
    )
    assert restored.disposition is CommandDisposition.ACCEPTED
    assert store.get("p").status is ShortlistStatus.ACTIVE
    # The reason for setting it aside cannot outlive the setting-aside.
    assert store.get("p").outcome is ShortlistOutcome.UNSET


def test_an_unknown_outcome_is_refused_and_names_what_is_permitted(tmp_path):
    store = _store(tmp_path)
    service = _service(store)
    service.handle(_command(CommandKind.SHORTLIST_PROGRAMME, {"programme_id": "p"}))

    result = service.handle(
        _command(
            CommandKind.ARCHIVE_PROGRAMME,
            {"programme_id": "p", "outcome": "gave-up"},
            key="k2",
        )
    )
    assert result.disposition is CommandDisposition.INVALID
    assert "unknown shortlist outcome" in result.message
    assert "out_of_scope_now" in result.message


def test_a_stale_revision_is_refused(tmp_path):
    store = _store(tmp_path)
    service = _service(store)
    service.handle(_command(CommandKind.SHORTLIST_PROGRAMME, {"programme_id": "p"}))
    service.handle(
        _command(CommandKind.ARCHIVE_PROGRAMME, {"programme_id": "p"}, key="k2")
    )

    result = service.handle(
        _command(
            CommandKind.RESTORE_PROGRAMME,
            {"programme_id": "p"},
            key="k3",
            expected_revision=0,
        )
    )
    assert result.disposition is CommandDisposition.INVALID
    assert "revision conflict" in result.message


def test_restoring_something_never_shortlisted_is_refused(tmp_path):
    result = _service(_store(tmp_path)).handle(
        _command(CommandKind.RESTORE_PROGRAMME, {"programme_id": "ghost"})
    )
    assert result.disposition is CommandDisposition.INVALID
    assert "not on the shortlist" in result.message


def test_unexpected_fields_are_refused(tmp_path):
    result = _service(_store(tmp_path)).handle(
        _command(
            CommandKind.SHORTLIST_PROGRAMME,
            {"programme_id": "p", "priority": "high"},
        )
    )
    assert result.disposition is CommandDisposition.INVALID
    assert "do not match its contract" in result.message


def test_without_a_store_the_command_is_refused_rather_than_ignored():
    result = _service(None).handle(
        _command(CommandKind.SHORTLIST_PROGRAMME, {"programme_id": "p"})
    )
    assert result.disposition is CommandDisposition.INVALID
    assert "no shortlist store is configured" in result.message


# -- the read model ----------------------------------------------------------


def test_no_store_reads_as_unknown_not_as_an_empty_shortlist():
    section = build_shortlist_section(None)
    assert section.status is ReadinessStatus.UNKNOWN


def test_an_empty_shortlist_reports_both_counts_as_zero(tmp_path):
    section = build_shortlist_section(_store(tmp_path))
    metrics = {m.label: m.value for m in section.metrics}

    assert section.status is ReadinessStatus.EMPTY
    assert metrics == {"Being worked": "0", "Set aside": "0"}
    # The rule of the place is stated before anyone relies on it.
    assert "reversible" in section.note and "deletes nothing" in section.note


def test_counts_are_symmetric_and_records_carry_their_lifecycle(tmp_path):
    store = _store(tmp_path)
    store.shortlist("active-one", actor="chase")
    store.shortlist("set-aside-one", actor="chase")
    store.archive("set-aside-one", actor="chase", outcome=ShortlistOutcome.FINISHED)

    section = build_shortlist_section(store)
    metrics = {m.label: m.value for m in section.metrics}
    records = {r.title: r for r in section.records}

    assert metrics == {"Being worked": "1", "Set aside": "1"}
    assert dict(records["set-aside-one"].attributes)["status"] == "archived"
    assert dict(records["set-aside-one"].attributes)["outcome"] == "finished"
    assert records["set-aside-one"].subtitle == "set aside"
    assert records["active-one"].subtitle == "being worked"


def test_lifecycle_is_not_smuggled_into_the_readiness_vocabulary(tmp_path):
    """An archived entry is neither ready nor blocked - it is on a shelf.
    Readiness must stay readable as readiness."""

    store = _store(tmp_path)
    store.shortlist("p", actor="chase")
    store.archive("p", actor="chase")

    record = build_shortlist_section(store).records[0]
    assert record.status is ReadinessStatus.READY
    assert dict(record.attributes)["status"] == "archived"


def test_everything_archived_is_distinguished_from_nothing_shortlisted(tmp_path):
    store = _store(tmp_path)
    store.shortlist("p", actor="chase")
    store.archive("p", actor="chase")

    section = build_shortlist_section(store)
    # The work was done, not never started, and the two should not look alike.
    assert section.status is ReadinessStatus.ATTENTION
    assert section.status is not ReadinessStatus.EMPTY


def test_a_failing_store_fails_closed(tmp_path):
    class _Broken:
        def entries(self):
            raise RuntimeError("shortlist integrity check failed")

    section = build_shortlist_section(_Broken())
    assert section.status is ReadinessStatus.BLOCKED
    assert "failed closed" in section.note


def test_no_shortlist_record_claims_authority(tmp_path):
    store = _store(tmp_path)
    store.shortlist("p", actor="chase")

    for record in build_shortlist_section(store).records:
        assert dict(record.attributes)["grants_authority"] == "false"
