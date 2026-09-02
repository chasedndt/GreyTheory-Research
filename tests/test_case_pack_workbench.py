"""Case-pack contracts and the persisted synthetic learner loop."""

# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 ChaseInTech

from __future__ import annotations

import json
from datetime import datetime, timezone

import pytest

from greytheory.authority.gate import AuthorityLevel
from greytheory.learning import (
    FixtureReceiptStore,
    LearningJourneyStore,
    LearningStoreError,
    MasteryStore,
    load_builtin_case_packs,
    load_builtin_catalogue,
)
from greytheory_app import (
    CommandDisposition,
    CommandField,
    CommandKind,
    WorkbenchApplicationService,
    WorkbenchCommand,
)


NOW = datetime(2026, 9, 2, 9, 0, tzinfo=timezone.utc)


def _command(command_id, kind, *, fields, revision=None, authority=AuthorityLevel.NONE, acknowledged=False):
    return WorkbenchCommand(
        id=command_id,
        kind=kind,
        operator_ref="operator-local",
        issued_at=NOW,
        idempotency_key=command_id,
        fields=tuple(CommandField(name, value) for name, value in fields.items()),
        expected_revision=revision,
        requested_authority=authority,
        human_acknowledged=acknowledged,
    )


def test_builtin_case_packs_are_versioned_local_and_live_dark():
    catalogue = load_builtin_catalogue()
    registry = load_builtin_case_packs(catalogue)

    assert registry.pack_ids == (
        "agent-authorization-boundary",
        "api-object-ownership",
        "session-role-transition",
    )
    assert len(registry.digest()) == 64
    ready = registry.pack("agent-authorization-boundary")
    assert ready.state == "ready_local"
    assert ready.live_programme_adapter.state == "dark"
    assert ready.live_programme_adapter.enabled is False
    assert ready.current_posture == "LOCAL_FIXTURE"
    assert ready.awards_mastery is False
    assert ready.proves_real_vulnerability is False


def test_server_runs_fixture_only_in_practise_and_persists_immutable_receipt(tmp_path):
    catalogue = load_builtin_catalogue()
    mastery = MasteryStore(tmp_path / "mastery", catalogue=catalogue)
    journeys = LearningJourneyStore(tmp_path / "journeys", catalogue=catalogue)
    receipts = FixtureReceiptStore(tmp_path / "receipts", catalogue=catalogue)
    service = WorkbenchApplicationService(
        mastery=mastery,
        journeys=journeys,
        fixture_receipts=receipts,
        clock=lambda: NOW,
    )

    started = service.handle(_command(
        "start-case-pack",
        CommandKind.START_LEARNING_JOURNEY,
        fields={
            "journey_id": "journey-case-pack",
            "card_id": "tool-authorization-failure",
            "dimension": "explain",
            "today": "2026-09-02",
            "objective": "Explain and test the local authorization boundary.",
            "track": "standard",
        },
    ))
    assert started.disposition is CommandDisposition.ACCEPTED
    advanced = service.handle(_command(
        "advance-to-practise",
        CommandKind.ADVANCE_LEARNING_JOURNEY,
        fields={"journey_id": "journey-case-pack"},
        revision=0,
    ))
    assert advanced.disposition is CommandDisposition.ACCEPTED
    current_card_id = journeys.get("journey-case-pack").card_id

    recorded = service.handle(_command(
        "run-case-pack-fixture",
        CommandKind.RUN_LEARNING_FIXTURE,
        fields={
            "journey_id": "journey-case-pack",
            "case_pack_id": "agent-authorization-boundary",
            "card_id": current_card_id,
        },
        revision=1,
        authority=AuthorityLevel.LOCAL_FIXTURE,
        acknowledged=True,
    ))
    assert recorded.disposition is CommandDisposition.ACCEPTED
    assert recorded.executed is False
    assert recorded.code == "learning_fixture_recorded"
    receipt = receipts.receipts()[0]
    assert receipt.controls_passed is True
    assert receipt.proves_real_vulnerability is False
    assert receipt.credits_mastery is False
    assert any(
        item.id == f"fixture-receipt:{receipt.id}"
        for item in service.snapshot().section("learning").records
    )

    envelope = json.loads(receipts.path.read_text(encoding="utf-8"))
    envelope["payload"]["receipts"][0]["proves_real_vulnerability"] = True
    receipts.path.write_text(json.dumps(envelope), encoding="utf-8")
    with pytest.raises(LearningStoreError, match="integrity"):
        receipts.verify()
