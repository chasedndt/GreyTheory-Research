"""Reviewing a programme from the application, as a bounded human act.

Review is the gate that turns PENDING_REVIEW into VERIFIED, so the refusals
matter more than the happy path. Each test here corresponds to a way the act
could be made meaningless: performed without a person, claimed by a model,
replayed from a queue, or applied to a contract whose ambiguities reading
cannot fix.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from greytheory.authority.gate import AuthorityLevel
from greytheory.authority.scope import ContractStatus
from greytheory_app.contracts import (
    CommandDisposition,
    CommandField,
    CommandKind,
    WorkbenchCommand,
    WorkbenchContractError,
)
from greytheory_app.service import WorkbenchApplicationService

NOW = datetime(2026, 9, 15, 12, 0, tzinfo=timezone.utc)
DEFAULT_FIELDS = {"programme_id": "hackerone-gitlab-public", "reviewer": "chase"}


def _command(**over) -> WorkbenchCommand:
    fields = over.pop("fields", DEFAULT_FIELDS)
    base = dict(
        id="cmd-review-1",
        kind=CommandKind.REVIEW_PROGRAMME,
        operator_ref="operator-local",
        issued_at=NOW,
        idempotency_key="review-key-1",
        fields=tuple(CommandField.from_pair(k, v) for k, v in fields.items()),
        requested_authority=AuthorityLevel.NONE,
        human_acknowledged=True,
    )
    base.update(over)
    return WorkbenchCommand(**base)


# -- the contract refuses what would make the act meaningless ----------------


def test_reviewing_carries_no_execution_authority():
    with pytest.raises(WorkbenchContractError, match="no execution authority"):
        _command(requested_authority=AuthorityLevel.LOCAL_FIXTURE)


def test_reviewing_requires_explicit_human_acknowledgement():
    with pytest.raises(WorkbenchContractError, match="human acknowledgement"):
        _command(human_acknowledged=False)


def test_a_well_formed_review_command_is_accepted_by_the_contract():
    command = _command()
    assert command.kind is CommandKind.REVIEW_PROGRAMME
    assert command.requested_authority is AuthorityLevel.NONE


# -- the service refuses the rest --------------------------------------------


class _Contract:
    status = ContractStatus.VERIFIED
    max_authority = "LOCAL_FIXTURE"

    def fingerprint(self):
        return "sha256:" + "a" * 64


class _Registry:
    """Stands in for ProgrammeRegistry.review, which is the real decider."""

    def __init__(self, error: Exception | None = None):
        self.error = error
        self.reviewed: list[tuple[str, str]] = []

    def review(self, programme_id, *, reviewer):
        if self.error is not None:
            raise self.error
        self.reviewed.append((programme_id, reviewer))
        return _Contract()


def _service(registry, clock=lambda: NOW) -> WorkbenchApplicationService:
    return WorkbenchApplicationService(registry=registry, clock=clock)


def test_a_review_reaches_the_registry_and_names_both_parties():
    registry = _Registry()
    result = _service(registry).handle(_command())

    assert result.disposition is CommandDisposition.ACCEPTED
    assert registry.reviewed == [("hackerone-gitlab-public", "chase")]
    assert "chase" in result.message
    # The ceiling is restated, because reviewing does not raise it.
    assert "LOCAL_FIXTURE" in result.message


@pytest.mark.parametrize(
    "reviewer", ["claude", "an llm assistant", "gpt-5", "greytheory bot"]
)
def test_a_model_cannot_be_the_reviewer(reviewer):
    registry = _Registry()
    result = _service(registry).handle(
        _command(fields={"programme_id": "p", "reviewer": reviewer})
    )

    assert result.disposition is CommandDisposition.INVALID
    assert "cannot be its reviewer" in result.message
    # The refusal must happen before the registry is touched, not after.
    assert registry.reviewed == []


def test_an_unnamed_reviewer_is_refused():
    registry = _Registry()
    result = _service(registry).handle(
        _command(fields={"programme_id": "p", "reviewer": "   "})
    )

    assert result.disposition is CommandDisposition.INVALID
    assert "requires reviewer" in result.message
    assert registry.reviewed == []


def test_a_blocked_contract_refusal_reaches_the_operator_verbatim():
    """The registry's own reason is the useful one. A blocked contract cannot be
    read into verification, and the operator needs to be told to resolve and
    recompile - not handed something vaguer."""

    registry = _Registry(
        ValueError(
            "a blocked contract cannot be reviewed into verification; "
            "resolve its 2 ambiguity/ies and recompile"
        )
    )
    result = _service(registry).handle(_command())

    assert result.disposition is CommandDisposition.INVALID
    assert "resolve its 2 ambiguity/ies and recompile" in result.message


def test_an_already_reviewed_programme_is_refused():
    registry = _Registry(RuntimeError("'p' v1 is already reviewed"))
    result = _service(registry).handle(_command())

    assert result.disposition is CommandDisposition.INVALID
    assert "already reviewed" in result.message


@pytest.mark.parametrize(
    "issued, marker",
    [
        (NOW + timedelta(minutes=5), "future-dated"),
        (NOW - timedelta(minutes=30), "stale"),
    ],
)
def test_a_replayed_or_queued_review_is_refused(issued, marker):
    """An approval that lands long after the person meant it is not consent."""

    registry = _Registry()
    result = _service(registry).handle(_command(issued_at=issued))

    assert result.disposition is CommandDisposition.INVALID
    assert marker in result.message
    assert registry.reviewed == []


def test_without_a_registry_the_command_is_refused_rather_than_ignored():
    result = _service(None).handle(_command())

    assert result.disposition is CommandDisposition.INVALID
    assert "registry" in result.message
