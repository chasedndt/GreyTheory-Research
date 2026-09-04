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
    object_pack = registry.pack("api-object-ownership")
    assert object_pack.state == "ready_local"
    assert object_pack.version == "1.1.0"
    assert object_pack.fixture_id == "fixture-idor-bola"
    assert registry.pack("session-role-transition").state == "queued"


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


def test_object_ownership_case_pack_runs_the_full_local_learning_loop(tmp_path):
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
        "start-object-ownership-pack",
        CommandKind.START_LEARNING_JOURNEY,
        fields={
            "journey_id": "journey-object-ownership",
            "card_id": "idor-bola",
            "dimension": "explain",
            "today": "2026-09-04",
            "objective": "Explain and test the actor-object-action boundary.",
            "track": "standard",
        },
    ))
    assert started.disposition is CommandDisposition.ACCEPTED

    practise = service.handle(_command(
        "advance-object-to-practise",
        CommandKind.ADVANCE_LEARNING_JOURNEY,
        fields={"journey_id": "journey-object-ownership"},
        revision=0,
    ))
    assert practise.disposition is CommandDisposition.ACCEPTED

    recorded = service.handle(_command(
        "run-object-ownership-fixture",
        CommandKind.RUN_LEARNING_FIXTURE,
        fields={
            "journey_id": "journey-object-ownership",
            "case_pack_id": "api-object-ownership",
            "card_id": "idor-bola",
        },
        revision=1,
        authority=AuthorityLevel.LOCAL_FIXTURE,
        acknowledged=True,
    ))
    assert recorded.disposition is CommandDisposition.ACCEPTED
    receipt = receipts.receipts()[0]
    receipt_ref = f"fixture-receipt:{receipt.id}"
    assert receipt.card_id == "idor-bola"
    assert receipt.controls_passed is True
    assert receipt.vulnerable_case_demonstrated is True
    assert receipt.proves_real_vulnerability is False
    assert receipt.credits_mastery is False

    prove = service.handle(_command(
        "advance-object-to-prove",
        CommandKind.ADVANCE_LEARNING_JOURNEY,
        fields={
            "journey_id": "journey-object-ownership",
            "fixture_receipt_ref": receipt_ref,
        },
        revision=1,
    ))
    assert prove.disposition is CommandDisposition.ACCEPTED
    reflect = service.handle(_command(
        "advance-object-to-reflect",
        CommandKind.ADVANCE_LEARNING_JOURNEY,
        fields={
            "journey_id": "journey-object-ownership",
            "evidence_refs": (receipt_ref,),
        },
        revision=2,
    ))
    assert reflect.disposition is CommandDisposition.ACCEPTED
    assess = service.handle(_command(
        "advance-object-to-assess",
        CommandKind.ADVANCE_LEARNING_JOURNEY,
        fields={
            "journey_id": "journey-object-ownership",
            "reflection": (
                "The synthetic controls demonstrate the ownership invariant, "
                "but they do not prove a live endpoint, scope, or real impact."
            ),
        },
        revision=3,
    ))
    assert assess.disposition is CommandDisposition.ACCEPTED
    at_assess = journeys.get("journey-object-ownership")
    assert at_assess.current_stage.value == "assess"
    assert at_assess.checkpoints[-1].stage.value == "reflect"
    assert "do not prove a live endpoint" in at_assess.checkpoints[-1].note

    assessment = service.handle(_command(
        "record-object-ownership-assessment",
        CommandKind.RECORD_MASTERY_ASSESSMENT,
        fields={
            "assessment_id": "assessment-object-ownership-explain",
            "card_id": "idor-bola",
            "dimension": "explain",
            "level": "independent",
            "evidence_refs": (receipt_ref,),
            "rationale": (
                "I explained the actor-object-action invariant, all three "
                "controls, and the limit between a fixture and a live claim."
            ),
            "review_due": "2026-12-04",
        },
        revision=0,
        acknowledged=True,
    ))
    assert assessment.disposition is CommandDisposition.ACCEPTED

    completed = service.handle(_command(
        "complete-object-ownership-journey",
        CommandKind.ADVANCE_LEARNING_JOURNEY,
        fields={
            "journey_id": "journey-object-ownership",
            "assessment_id": "assessment-object-ownership-explain",
        },
        revision=4,
    ))
    assert completed.disposition is CommandDisposition.ACCEPTED
    journey = journeys.get("journey-object-ownership")
    assert journey.status.value == "completed"
    assert journey.current_stage.value == "complete"
    assert journey.checkpoints[-1].stage.value == "assess"
    assert mastery.assessments()[0].assessor_kind.value == "human"


def test_queued_case_pack_cannot_run_a_fixture(tmp_path):
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
    service.handle(_command(
        "start-queued-pack",
        CommandKind.START_LEARNING_JOURNEY,
        fields={
            "journey_id": "journey-queued-pack",
            "card_id": "session-management",
            "dimension": "explain",
            "today": "2026-09-04",
            "objective": "Verify a queued pack remains launch dark.",
            "track": "standard",
        },
    ))
    service.handle(_command(
        "advance-queued-pack",
        CommandKind.ADVANCE_LEARNING_JOURNEY,
        fields={"journey_id": "journey-queued-pack"},
        revision=0,
    ))
    current = journeys.get("journey-queued-pack")

    rejected = service.handle(_command(
        "run-queued-pack",
        CommandKind.RUN_LEARNING_FIXTURE,
        fields={
            "journey_id": current.id,
            "case_pack_id": "session-role-transition",
            "card_id": current.card_id,
        },
        revision=current.revision,
        authority=AuthorityLevel.LOCAL_FIXTURE,
        acknowledged=True,
    ))

    assert rejected.disposition is CommandDisposition.INVALID
    assert "ready local case pack" in rejected.message
    assert receipts.receipts() == ()
