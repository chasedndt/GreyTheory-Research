"""The shortlist: which programmes are being worked, and which are set aside.

The property that matters most here is that archiving is *reversible*. The
research store's archive is one-way because its commit path refuses every write
to an archived record - including the write that would un-archive it - so the
first test below exists to make sure this store never acquires that bug.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from greytheory.shortlist import (
    MAX_NOTE_CHARS,
    ShortlistEntry,
    ShortlistError,
    ShortlistOutcome,
    ShortlistStatus,
    ShortlistStore,
)

NOW = datetime(2026, 9, 15, 12, 0, tzinfo=timezone.utc)


class _Clock:
    """Advances on each read, so updated_at is provably later than the start."""

    def __init__(self) -> None:
        self.ticks = 0

    def __call__(self) -> datetime:
        self.ticks += 1
        return NOW + timedelta(minutes=self.ticks)


def _store(tmp_path, audit=None) -> ShortlistStore:
    return ShortlistStore(
        tmp_path / "shortlist", allow_in_repository=True, audit=audit, clock=_Clock()
    )


# -- the property the research store gets wrong ------------------------------


def test_archiving_is_reversible(tmp_path):
    store = _store(tmp_path)
    store.shortlist("hackerone-gitlab-public", actor="chase")
    store.archive("hackerone-gitlab-public", actor="chase")
    restored = store.restore("hackerone-gitlab-public", actor="chase")

    assert restored.status is ShortlistStatus.ACTIVE
    assert store.active() and not store.archived()


def test_restore_is_not_blocked_by_the_archived_state_it_exists_to_undo(tmp_path):
    """The guard must check the transition, not the stored status."""

    store = _store(tmp_path)
    store.shortlist("p", actor="chase")
    store.archive("p", actor="chase")

    # Reachable repeatedly: archive and restore are a cycle, not a one-way door.
    for _ in range(3):
        assert store.restore("p", actor="chase").status is ShortlistStatus.ACTIVE
        assert store.archive("p", actor="chase").status is ShortlistStatus.ARCHIVED


def test_nothing_is_ever_deleted(tmp_path):
    store = _store(tmp_path)
    store.shortlist("p", actor="chase")
    store.archive("p", actor="chase", note="dead end for now")

    # Archived entries remain readable in full, with their note intact.
    assert [e.programme_id for e in store.entries()] == ["p"]
    assert store.get("p").note == "dead end for now"


# -- transitions refuse what would be meaningless ----------------------------


def test_shortlisting_twice_is_refused_rather_than_silently_redated(tmp_path):
    store = _store(tmp_path)
    store.shortlist("p", actor="chase")

    with pytest.raises(ShortlistError, match="already shortlisted"):
        store.shortlist("p", actor="chase")


def test_re_shortlisting_an_archived_programme_keeps_the_original_decision_date(tmp_path):
    store = _store(tmp_path)
    first = store.shortlist("p", actor="chase")
    store.archive("p", actor="chase")
    again = store.shortlist("p", actor="chase")

    assert again.status is ShortlistStatus.ACTIVE
    # When the operator decided is theirs, not something a later action rewrites.
    assert again.shortlisted_at == first.shortlisted_at
    assert again.updated_at > first.updated_at


def test_archiving_or_restoring_an_unknown_programme_is_refused(tmp_path):
    store = _store(tmp_path)
    with pytest.raises(ShortlistError, match="not on the shortlist"):
        store.archive("nope", actor="chase")
    with pytest.raises(ShortlistError, match="not on the shortlist"):
        store.restore("nope", actor="chase")


def test_repeating_a_transition_is_refused(tmp_path):
    store = _store(tmp_path)
    store.shortlist("p", actor="chase")
    with pytest.raises(ShortlistError, match="already active"):
        store.restore("p", actor="chase")

    store.archive("p", actor="chase")
    with pytest.raises(ShortlistError, match="already archived"):
        store.archive("p", actor="chase")


# -- outcome is a separate fact from status ----------------------------------


def test_an_outcome_is_recorded_on_archive_and_cleared_on_restore(tmp_path):
    store = _store(tmp_path)
    store.shortlist("p", actor="chase")
    archived = store.archive(
        "p", actor="chase", outcome=ShortlistOutcome.OUT_OF_SCOPE_NOW, note="scope shrank"
    )
    assert archived.outcome is ShortlistOutcome.OUT_OF_SCOPE_NOW

    restored = store.restore("p", actor="chase")
    # A reason for setting something aside cannot survive un-setting it aside.
    assert restored.outcome is ShortlistOutcome.UNSET
    assert restored.note == ""


def test_an_active_entry_cannot_carry_an_outcome(tmp_path):
    with pytest.raises(ShortlistError, match="cannot carry an outcome"):
        ShortlistEntry(
            programme_id="p",
            status=ShortlistStatus.ACTIVE,
            shortlisted_at=NOW,
            updated_at=NOW,
            outcome=ShortlistOutcome.FINISHED,
        )


def test_a_note_is_bounded(tmp_path):
    store = _store(tmp_path)
    store.shortlist("p", actor="chase")
    with pytest.raises(ShortlistError, match="limited to"):
        store.archive("p", actor="chase", note="x" * (MAX_NOTE_CHARS + 1))


# -- concurrency, persistence and integrity ----------------------------------


def test_a_stale_revision_is_refused(tmp_path):
    store = _store(tmp_path)
    entry = store.shortlist("p", actor="chase")
    store.archive("p", actor="chase", expected_revision=entry.revision)

    with pytest.raises(ShortlistError, match="revision conflict"):
        store.restore("p", actor="chase", expected_revision=entry.revision)


def test_state_survives_a_new_store_instance(tmp_path):
    _store(tmp_path).shortlist("p", actor="chase")
    reopened = ShortlistStore(tmp_path / "shortlist", allow_in_repository=True)

    assert [e.programme_id for e in reopened.active()] == ["p"]


def test_tampered_state_fails_closed(tmp_path):
    store = _store(tmp_path)
    store.shortlist("p", actor="chase")
    store.path.write_text(
        store.path.read_text(encoding="utf-8").replace('"active"', '"archived"'),
        encoding="utf-8",
    )

    with pytest.raises(ShortlistError, match="integrity check failed"):
        store.entries()


def test_the_shortlist_refuses_to_live_inside_a_repository(tmp_path):
    (tmp_path / ".git").mkdir()
    with pytest.raises(ShortlistError, match="refused inside a git working tree"):
        ShortlistStore(tmp_path / "shortlist")


def test_every_audited_transition_states_that_it_grants_nothing(tmp_path):
    written: list[dict] = []

    class _Audit:
        def append(self, *, actor, action, authority_ref=None, detail=None):
            written.append({"actor": actor, "action": action, **(detail or {})})

    store = _store(tmp_path, audit=_Audit())
    store.shortlist("p", actor="chase")
    store.archive("p", actor="chase")
    store.restore("p", actor="chase")

    assert [item["action"] for item in written] == [
        "shortlist.add",
        "shortlist.archive",
        "shortlist.restore",
    ]
    # A shortlist is an intention. The log must never read as permission.
    assert all(item["grants_authority"] is False for item in written)
