"""Guided learning remains deterministic, local, and human-assessed."""

import json
from datetime import date, datetime, timedelta, timezone

import pytest

from greytheory.cli import main
from greytheory.learning import (
    AssessorKind,
    GuidedLearningPlanner,
    JourneyStatus,
    LearningError,
    LearningJourneyStore,
    LearningMode,
    LearningStage,
    LearningStoreError,
    LearningTrack,
    MasteryAssessment,
    MasteryDimension,
    MasteryLevel,
    ReviewPolicy,
    abandon_learning_journey,
    advance_learning_journey,
    load_builtin_catalogue,
    start_learning_journey,
)


NOW = datetime(2026, 8, 24, 12, 0, tzinfo=timezone.utc)


def assessment(
    *,
    assessment_id: str = "assessment-idor-explain",
    card_id: str = "idor-bola",
    dimension: MasteryDimension = MasteryDimension.EXPLAIN,
    level: MasteryLevel = MasteryLevel.INTRODUCTORY,
    assessed_at: datetime = NOW - timedelta(days=10),
    review_due: date = date(2026, 8, 21),
    assessor_kind: AssessorKind = AssessorKind.HUMAN,
    evidence_refs: tuple[str, ...] = ("evidence:learning-review",),
) -> MasteryAssessment:
    return MasteryAssessment(
        id=assessment_id,
        card_id=card_id,
        dimension=dimension,
        level=level,
        assessor="operator-chase" if assessor_kind is AssessorKind.HUMAN else "fixture",
        assessor_kind=assessor_kind,
        evidence_refs=evidence_refs,
        rationale="Reviewed the explanation against the evidence.",
        assessed_at=assessed_at,
        review_due=review_due,
    )


def test_empty_profile_starts_at_first_ready_card_and_explain_dimension():
    catalogue = load_builtin_catalogue()
    recommendation = GuidedLearningPlanner(catalogue).recommend(
        (), today=NOW.date()
    )

    assert recommendation.card_id == "idor-bola"
    assert recommendation.dimension is MasteryDimension.EXPLAIN
    assert recommendation.current_level is MasteryLevel.NOT_ASSESSED
    assert recommendation.mode is LearningMode.GUIDED
    assert [item.stage for item in recommendation.stages] == [
        LearningStage.LEARN,
        LearningStage.PRACTISE,
        LearningStage.PROVE,
        LearningStage.REFLECT,
        LearningStage.ASSESS,
    ]
    assert recommendation.to_dict()["operating_posture"] == "LOCAL_FIXTURE"


def test_preferred_card_routes_to_unmet_prerequisite_without_pretending_progress():
    catalogue = load_builtin_catalogue()
    recommendation = GuidedLearningPlanner(catalogue).recommend(
        (), today=NOW.date(), preferred_card_id="csrf"
    )

    assert recommendation.card_id == "session-management"
    assert recommendation.dimension is MasteryDimension.TEST
    assert recommendation.mode is LearningMode.PREREQUISITE
    assert "csrf requires" in recommendation.reason


def test_due_review_wins_before_new_material():
    catalogue = load_builtin_catalogue()
    recommendation = GuidedLearningPlanner(catalogue).recommend(
        (assessment(),), today=NOW.date()
    )

    assert recommendation.card_id == "idor-bola"
    assert recommendation.dimension is MasteryDimension.EXPLAIN
    assert recommendation.mode is LearningMode.REVIEW
    assert recommendation.review_due == date(2026, 8, 21)


def test_test_fixture_assessment_never_enters_credited_review_schedule():
    catalogue = load_builtin_catalogue()
    fixture = assessment(assessor_kind=AssessorKind.TEST_FIXTURE)
    recommendation = GuidedLearningPlanner(catalogue).recommend(
        (fixture,), today=NOW.date()
    )

    assert recommendation.mode is LearningMode.GUIDED
    assert recommendation.current_level is MasteryLevel.NOT_ASSESSED


def test_review_policy_is_small_deterministic_and_refuses_not_assessed():
    policy = ReviewPolicy()
    assert policy.review_due(NOW.date(), MasteryLevel.INTRODUCTORY) == date(2026, 8, 31)
    assert policy.review_due(NOW.date(), MasteryLevel.INDEPENDENT) == date(2026, 9, 23)
    assert policy.review_due(NOW.date(), MasteryLevel.TRANSFERABLE) == date(2026, 11, 22)
    with pytest.raises(LearningError, match="no review interval"):
        policy.review_due(NOW.date(), MasteryLevel.NOT_ASSESSED)


def test_adaptive_review_schedule_is_transparent_reinforcing_and_regression_aware():
    policy = ReviewPolicy()
    first = policy.schedule(
        (),
        card_id="idor-bola",
        dimension=MasteryDimension.EXPLAIN,
        level=MasteryLevel.INDEPENDENT,
        assessed_at=NOW,
    )
    assert first.interval_days == 30
    assert first.review_due == date(2026, 9, 23)
    assert first.adjustment == "baseline"
    assert first.policy_ref == "adaptive-evidence-review-v1"

    introductory = assessment(
        assessment_id="assessment-adaptive-intro",
        level=MasteryLevel.INTRODUCTORY,
        assessed_at=NOW - timedelta(days=30),
        review_due=date(2026, 8, 1),
    )
    once = policy.schedule(
        (introductory,),
        card_id="idor-bola",
        dimension=MasteryDimension.EXPLAIN,
        level=MasteryLevel.ASSISTED,
        assessed_at=NOW,
    )
    assert once.interval_days == 21
    assert once.adjustment == "reinforced_once"

    assisted = assessment(
        assessment_id="assessment-adaptive-assisted",
        level=MasteryLevel.ASSISTED,
        assessed_at=NOW - timedelta(days=10),
        review_due=date(2026, 8, 28),
    )
    twice = policy.schedule(
        (introductory, assisted),
        card_id="idor-bola",
        dimension=MasteryDimension.EXPLAIN,
        level=MasteryLevel.INDEPENDENT,
        assessed_at=NOW,
    )
    assert twice.interval_days == 60
    assert twice.adjustment == "reinforced_twice"
    assert twice.credited_history_count == 2

    regression = policy.schedule(
        (
            assessment(
                assessment_id="assessment-adaptive-independent",
                level=MasteryLevel.INDEPENDENT,
                assessed_at=NOW - timedelta(days=5),
                review_due=date(2026, 9, 18),
            ),
        ),
        card_id="idor-bola",
        dimension=MasteryDimension.EXPLAIN,
        level=MasteryLevel.ASSISTED,
        assessed_at=NOW,
    )
    assert regression.interval_days == 7
    assert regression.adjustment == "regression"

    fixture_only = policy.schedule(
        (assessment(assessor_kind=AssessorKind.TEST_FIXTURE),),
        card_id="idor-bola",
        dimension=MasteryDimension.EXPLAIN,
        level=MasteryLevel.ASSISTED,
        assessed_at=NOW,
    )
    assert fixture_only.credited_history_count == 0
    assert fixture_only.interval_days == 14


def test_assisted_track_exposes_guidance_and_caps_journey_mastery_credit():
    catalogue = load_builtin_catalogue()
    recommendation = GuidedLearningPlanner(catalogue).recommend(
        (),
        today=NOW.date(),
        preferred_card_id="idor-bola",
        preferred_dimension=MasteryDimension.EXPLAIN,
        track=LearningTrack.ASSISTED,
    )
    assert recommendation.track is LearningTrack.ASSISTED
    assert recommendation.stages[0].guidance
    journey = start_learning_journey(
        recommendation, journey_id="journey-assisted-idor", now=NOW
    )
    for offset, kwargs in (
        (1, {}),
        (2, {"fixture_receipt_ref": "fixture-receipt:assisted"}),
        (3, {"evidence_refs": ("evidence:assisted-notes",)}),
        (4, {"reflection": "The hint sequence exposed where I skipped the ownership check."}),
    ):
        journey = advance_learning_journey(
            journey, at=NOW + timedelta(minutes=offset), **kwargs
        )
    independent = assessment(
        assessment_id="assessment-assisted-overclaim",
        level=MasteryLevel.INDEPENDENT,
        assessed_at=NOW + timedelta(minutes=5),
        review_due=date(2026, 9, 23),
    )
    with pytest.raises(LearningError, match="assisted journey cannot evidence"):
        advance_learning_journey(
            journey,
            at=NOW + timedelta(minutes=6),
            assessment=independent,
            recorded_assessment_ids=(independent.id,),
        )
    assisted = assessment(
        assessment_id="assessment-assisted-credited",
        level=MasteryLevel.ASSISTED,
        assessed_at=NOW + timedelta(minutes=5),
        review_due=date(2026, 9, 7),
    )
    completed = advance_learning_journey(
        journey,
        at=NOW + timedelta(minutes=6),
        assessment=assisted,
        recorded_assessment_ids=(assisted.id,),
    )
    assert completed.status is JourneyStatus.COMPLETED
    assert completed.track is LearningTrack.ASSISTED


def test_transfer_track_requires_independent_foundations_and_distinct_context_proof():
    catalogue = load_builtin_catalogue()
    test_assessment = assessment(
        assessment_id="assessment-transfer-test",
        dimension=MasteryDimension.TEST,
        level=MasteryLevel.INDEPENDENT,
        assessed_at=NOW - timedelta(days=5),
        review_due=date(2026, 9, 18),
    )
    with pytest.raises(LearningError, match="unmet: prove"):
        GuidedLearningPlanner(catalogue).recommend(
            (test_assessment,),
            today=NOW.date(),
            preferred_card_id="idor-bola",
            track=LearningTrack.TRANSFER,
        )
    prove_assessment = assessment(
        assessment_id="assessment-transfer-prove",
        dimension=MasteryDimension.PROVE,
        level=MasteryLevel.INDEPENDENT,
        assessed_at=NOW - timedelta(days=4),
        review_due=date(2026, 9, 19),
    )
    recommendation = GuidedLearningPlanner(catalogue).recommend(
        (test_assessment, prove_assessment),
        today=NOW.date(),
        preferred_card_id="idor-bola",
        track=LearningTrack.TRANSFER,
    )
    assert recommendation.dimension is MasteryDimension.TRANSFER
    assert recommendation.track is LearningTrack.TRANSFER
    with pytest.raises(LearningError, match="distinct context"):
        start_learning_journey(
            recommendation, journey_id="journey-transfer-missing", now=NOW
        )
    context_ref = "local-context:alternate-order-shape"
    journey = start_learning_journey(
        recommendation,
        journey_id="journey-transfer-idor",
        now=NOW,
        transfer_context_ref=context_ref,
    )
    journey = advance_learning_journey(journey, at=NOW + timedelta(minutes=1))
    journey = advance_learning_journey(
        journey,
        at=NOW + timedelta(minutes=2),
        fixture_receipt_ref="fixture-receipt:transfer-baseline",
    )
    with pytest.raises(LearningError, match="distinct context"):
        advance_learning_journey(
            journey,
            at=NOW + timedelta(minutes=3),
            evidence_refs=("evidence:transfer-comparison",),
        )
    journey = advance_learning_journey(
        journey,
        at=NOW + timedelta(minutes=3),
        evidence_refs=(context_ref, "evidence:transfer-comparison"),
    )
    journey = advance_learning_journey(
        journey,
        at=NOW + timedelta(minutes=4),
        reflection="The ownership invariant transferred, but the identifier location changed.",
    )
    transfer_assessment = assessment(
        assessment_id="assessment-transfer-context",
        dimension=MasteryDimension.TRANSFER,
        level=MasteryLevel.INTRODUCTORY,
        assessed_at=NOW + timedelta(minutes=5),
        review_due=date(2026, 8, 31),
        evidence_refs=(context_ref, "evidence:transfer-comparison"),
    )
    completed = advance_learning_journey(
        journey,
        at=NOW + timedelta(minutes=6),
        assessment=transfer_assessment,
        recorded_assessment_ids=(transfer_assessment.id,),
    )
    assert completed.status is JourneyStatus.COMPLETED
    assert completed.transfer_context_ref == context_ref
    assert completed.to_dict()["track"] == "transfer"


def test_journey_requires_practice_proof_reflection_and_persisted_human_assessment():
    catalogue = load_builtin_catalogue()
    recommendation = GuidedLearningPlanner(catalogue).recommend(
        (), today=NOW.date()
    )
    journey = start_learning_journey(
        recommendation, journey_id="journey-idor-explain", now=NOW
    )
    assert journey.current_stage is LearningStage.LEARN
    assert journey.to_dict()["awards_mastery"] is False

    journey = advance_learning_journey(journey, at=NOW + timedelta(minutes=5))
    with pytest.raises(LearningError, match="fixture receipt"):
        advance_learning_journey(journey, at=NOW + timedelta(minutes=10))
    journey = advance_learning_journey(
        journey,
        at=NOW + timedelta(minutes=10),
        fixture_receipt_ref="fixture-receipt:idor-bola-1",
    )
    with pytest.raises(LearningError, match="evidence reference"):
        advance_learning_journey(journey, at=NOW + timedelta(minutes=15))
    journey = advance_learning_journey(
        journey,
        at=NOW + timedelta(minutes=15),
        evidence_refs=("evidence:explanation-notes",),
    )
    with pytest.raises(LearningError, match="written reflection"):
        advance_learning_journey(journey, at=NOW + timedelta(minutes=20))
    journey = advance_learning_journey(
        journey,
        at=NOW + timedelta(minutes=20),
        reflection="I now separate an object lookup from the ownership decision.",
    )
    human = assessment(
        assessment_id="assessment-journey-idor-explain",
        assessed_at=NOW + timedelta(minutes=21),
        review_due=date(2026, 8, 31),
    )
    with pytest.raises(LearningError, match="already be persisted"):
        advance_learning_journey(
            journey,
            at=NOW + timedelta(minutes=22),
            assessment=human,
        )
    journey = advance_learning_journey(
        journey,
        at=NOW + timedelta(minutes=22),
        assessment=human,
        recorded_assessment_ids=(human.id,),
    )

    assert journey.status is JourneyStatus.COMPLETED
    assert journey.current_stage is LearningStage.COMPLETE
    assert journey.revision == 5
    assert [item.stage for item in journey.checkpoints] == [
        LearningStage.LEARN,
        LearningStage.PRACTISE,
        LearningStage.PROVE,
        LearningStage.REFLECT,
        LearningStage.ASSESS,
    ]
    assert LearningStage("complete") is LearningStage.COMPLETE


def test_fixture_assessment_cannot_complete_a_journey():
    catalogue = load_builtin_catalogue()
    recommendation = GuidedLearningPlanner(catalogue).recommend(
        (), today=NOW.date()
    )
    journey = start_learning_journey(
        recommendation, journey_id="journey-fixture-credit", now=NOW
    )
    for offset, kwargs in (
        (1, {}),
        (2, {"fixture_receipt_ref": "fixture-receipt:one"}),
        (3, {"evidence_refs": ("evidence:one",)}),
        (4, {"reflection": "A real operator reflection."}),
    ):
        journey = advance_learning_journey(
            journey, at=NOW + timedelta(minutes=offset), **kwargs
        )
    fixture = assessment(
        assessment_id="assessment-fixture-only",
        assessed_at=NOW + timedelta(minutes=5),
        review_due=date(2026, 8, 31),
        assessor_kind=AssessorKind.TEST_FIXTURE,
    )
    with pytest.raises(LearningError, match="human mastery assessment"):
        advance_learning_journey(
            journey,
            at=NOW + timedelta(minutes=6),
            assessment=fixture,
            recorded_assessment_ids=(fixture.id,),
        )


def test_abandon_records_reason_without_completion_or_mastery():
    catalogue = load_builtin_catalogue()
    recommendation = GuidedLearningPlanner(catalogue).recommend(
        (), today=NOW.date()
    )
    journey = start_learning_journey(
        recommendation, journey_id="journey-abandon", now=NOW
    )
    abandoned = abandon_learning_journey(
        journey,
        at=NOW + timedelta(minutes=2),
        reason="Need to revisit the prerequisite terminology.",
    )
    assert abandoned.status is JourneyStatus.ABANDONED
    assert abandoned.current_stage is LearningStage.LEARN
    assert abandoned.to_dict()["awards_mastery"] is False
    with pytest.raises(LearningError, match="only an active"):
        advance_learning_journey(abandoned, at=NOW + timedelta(minutes=3))


def test_learning_journey_round_trip_and_time_guards():
    catalogue = load_builtin_catalogue()
    recommendation = GuidedLearningPlanner(catalogue).recommend(
        (), today=NOW.date()
    )
    journey = start_learning_journey(
        recommendation, journey_id="journey-round-trip", now=NOW
    )
    from greytheory.learning import LearningJourney

    assert LearningJourney.from_dict(journey.to_dict()) == journey
    with pytest.raises(LearningError, match="timezone-aware"):
        start_learning_journey(
            recommendation,
            journey_id="journey-naive",
            now=datetime(2026, 8, 24, 12, 0),
        )
    with pytest.raises(LearningError, match="backwards"):
        advance_learning_journey(journey, at=NOW - timedelta(seconds=1))


def test_journey_store_persists_with_integrity_and_optimistic_revision(tmp_path):
    catalogue = load_builtin_catalogue()
    recommendation = GuidedLearningPlanner(catalogue).recommend(
        (), today=NOW.date()
    )
    journey = start_learning_journey(
        recommendation, journey_id="journey-store", now=NOW
    )
    store = LearningJourneyStore(tmp_path / "private-learning", catalogue=catalogue)
    store.save(journey)
    assert store.get(journey.id) == journey

    advanced = advance_learning_journey(
        journey, at=NOW + timedelta(minutes=1)
    )
    with pytest.raises(LearningStoreError, match="expected revision"):
        store.save(advanced)
    store.save(advanced, expected_revision=journey.revision)
    store.verify()
    assert store.get(journey.id).revision == 1

    twice = advance_learning_journey(
        advanced,
        at=NOW + timedelta(minutes=2),
        fixture_receipt_ref="fixture-receipt:store",
    )
    with pytest.raises(LearningStoreError, match="revision conflict"):
        store.save(twice, expected_revision=0)


def test_journey_store_detects_tampering_and_refuses_git_state(tmp_path):
    catalogue = load_builtin_catalogue()
    recommendation = GuidedLearningPlanner(catalogue).recommend(
        (), today=NOW.date()
    )
    journey = start_learning_journey(
        recommendation, journey_id="journey-integrity", now=NOW
    )
    root = tmp_path / "private-learning"
    store = LearningJourneyStore(root, catalogue=catalogue)
    store.save(journey)

    import json

    wrapper = json.loads((root / "journeys.json").read_text(encoding="utf-8"))
    wrapper["payload"]["journeys"][0]["objective"] = "tampered"
    (root / "journeys.json").write_text(json.dumps(wrapper), encoding="utf-8")
    with pytest.raises(LearningStoreError, match="integrity check"):
        store.verify()

    repo = tmp_path / "repo"
    (repo / ".git").mkdir(parents=True)
    with pytest.raises(LearningStoreError, match="git working tree"):
        LearningJourneyStore(repo / "learning", catalogue=catalogue)


def test_cli_plans_starts_and_advances_a_private_learning_journey(
    tmp_path, capsys
):
    root = tmp_path / "private-learning"
    assert main(
        [
            "learning",
            "plan",
            "--root",
            str(root),
            "--today",
            NOW.date().isoformat(),
            "--json",
        ]
    ) == 0
    plan = json.loads(capsys.readouterr().out)
    assert plan["recommendation"]["card_id"] == "idor-bola"
    assert plan["recommendation"]["mastery_credit_rule"].startswith("explicit")

    assert main(
        [
            "learning",
            "journey-start",
            "--root",
            str(root),
            "--journey-id",
            "journey-cli-idor",
            "--today",
            NOW.date().isoformat(),
            "--at",
            NOW.isoformat(),
            "--json",
        ]
    ) == 0
    started = json.loads(capsys.readouterr().out)
    assert started["journey"]["current_stage"] == "learn"
    assert started["journey"]["awards_mastery"] is False

    assert main(
        [
            "learning",
            "journey-advance",
            "--root",
            str(root),
            "--journey-id",
            "journey-cli-idor",
            "--at",
            (NOW + timedelta(minutes=1)).isoformat(),
            "--json",
        ]
    ) == 0
    advanced = json.loads(capsys.readouterr().out)
    assert advanced["current_stage"] == "practise"
    assert advanced["revision"] == 1

    assert main(
        [
            "learning",
            "journey-advance",
            "--root",
            str(root),
            "--journey-id",
            "journey-cli-idor",
            "--at",
            (NOW + timedelta(minutes=2)).isoformat(),
        ]
    ) == 1
    assert "fixture receipt" in capsys.readouterr().err

    assert main(
        [
            "learning",
            "journey-advance",
            "--root",
            str(root),
            "--journey-id",
            "journey-cli-idor",
            "--fixture-receipt-ref",
            "fixture-receipt:cli-idor",
            "--at",
            (NOW + timedelta(minutes=2)).isoformat(),
            "--json",
        ]
    ) == 0
    practised = json.loads(capsys.readouterr().out)
    assert practised["current_stage"] == "prove"
    assert practised["awards_mastery"] is False

    assert main(
        [
            "learning",
            "journey-status",
            "--root",
            str(root),
            "--journey-id",
            "journey-cli-idor",
            "--json",
        ]
    ) == 0
    status = json.loads(capsys.readouterr().out)
    assert status["journey_count"] == 1
    assert status["journeys"][0]["current_stage"] == "prove"


def test_cli_defaults_human_assessment_to_adaptive_review_and_starts_assisted_track(
    tmp_path, capsys
):
    root = tmp_path / "private-adaptive-learning"
    assert main(
        [
            "learning",
            "assess",
            "--root",
            str(root),
            "--assessment-id",
            "assessment-cli-adaptive",
            "--card",
            "idor-bola",
            "--dimension",
            "explain",
            "--level",
            "independent",
            "--assessor",
            "operator-chase",
            "--evidence-ref",
            "evidence:cli-adaptive",
            "--rationale",
            "The operator independently explained the ownership invariant.",
            "--assessed-at",
            NOW.isoformat(),
            "--json",
        ]
    ) == 0
    recorded = json.loads(capsys.readouterr().out)
    assert recorded["review_policy_ref"] == "adaptive-evidence-review-v1"
    assert recorded["review_due"] == "2026-09-23"
    assert recorded["adaptive_review_schedule"]["adjustment"] == "baseline"

    assert main(
        [
            "learning",
            "journey-start",
            "--root",
            str(root),
            "--journey-id",
            "journey-cli-assisted",
            "--card",
            "idor-bola",
            "--dimension",
            "recognise",
            "--track",
            "assisted",
            "--today",
            NOW.date().isoformat(),
            "--at",
            NOW.isoformat(),
            "--json",
        ]
    ) == 0
    started = json.loads(capsys.readouterr().out)
    assert started["journey"]["track"] == "assisted"
    assert started["recommendation"]["stages"][0]["guidance"]
