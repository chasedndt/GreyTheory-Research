"""Milestone 5 vulnerability-card, fixture, and skill-graph acceptance."""

from __future__ import annotations

import ast
import json
from datetime import date, datetime, timezone
from pathlib import Path

import pytest

from greytheory.cli import main
from greytheory.learning import (
    AssessorKind,
    LearningError,
    LearningStoreError,
    MILESTONE5_CARD_IDS,
    MasteryAssessment,
    MasteryDimension,
    MasteryLevel,
    MasteryStore,
    load_builtin_catalogue,
)


NOW = datetime(2026, 8, 9, 18, 0, tzinfo=timezone.utc)


def human_assessment(**changes) -> MasteryAssessment:
    values = {
        "id": "assessment-bola-test-1",
        "card_id": "idor-bola",
        "dimension": MasteryDimension.TEST,
        "level": MasteryLevel.INDEPENDENT,
        "assessor": "operator-chase",
        "assessor_kind": AssessorKind.HUMAN,
        "evidence_refs": ("lab-report:controlled-two-account-review",),
        "rationale": "The operator reviewed a falsifiable plan, both controls, and a clean repeat.",
        "assessed_at": NOW,
        "review_due": date(2026, 11, 9),
    }
    values.update(changes)
    return MasteryAssessment(**values)


def test_builtin_catalogue_satisfies_every_milestone_5_exit_condition():
    catalogue = load_builtin_catalogue()

    assert set(catalogue.card_ids) == MILESTONE5_CARD_IDS
    assert len(catalogue.card_ids) == 12
    assert len(catalogue.digest()) == 64
    assert set(catalogue.graph.order) == MILESTONE5_CARD_IDS

    for card_id in catalogue.card_ids:
        card = catalogue.card(card_id)
        assert card.local_fixture.id == catalogue.fixture(card_id).id
        assert card.hypothesis_templates
        assert {item.role for item in card.minimum_evidence} >= {
            "behaviour",
            "boundary",
            "control",
            "reproduction",
            "impact",
        }
        assert tuple(card.mastery_dimensions) == tuple(MasteryDimension)
        assert card.framework_references
        assert card.review_date >= date(2026, 8, 9)


def test_all_twelve_fixtures_execute_distinct_synthetic_boundary_logic():
    catalogue = load_builtin_catalogue()
    receipts = catalogue.run_all_fixtures(clock=lambda: NOW)

    assert len(receipts) == 12
    assert len({item.fixture_id for item in receipts}) == 12
    assert len({catalogue.fixture(item.card_id).mechanism for item in receipts}) == 12
    assert all(item.controls_passed for item in receipts)
    assert all(item.vulnerable_case_demonstrated for item in receipts)
    assert all(item.scope == "synthetic_training_only" for item in receipts)
    assert all(item.proves_real_vulnerability is False for item in receipts)
    assert all(item.credits_mastery is False for item in receipts)
    for receipt in receipts:
        by_role = {item.role.value: item for item in receipt.case_results}
        assert by_role["positive_control"].property_held is True
        assert by_role["vulnerable_probe"].property_held is False
        assert by_role["vulnerable_probe"].controlled_effect_observed is True
        assert by_role["negative_control"].property_held is True


def test_hypothesis_templates_require_exact_variables_and_remain_theories():
    template = load_builtin_catalogue().card("idor-bola").hypothesis_templates[0]
    values = {
        "preconditions": "two owned identities and one synthetic object",
        "actor": "identity-a",
        "action": "read",
        "object": "object-b",
        "owner": "identity-b",
        "controlled_consequence": "one synthetic field is returned",
    }
    statement = template.instantiate(values)
    assert "identity-a" in statement
    assert "may perform" in statement
    with pytest.raises(LearningError, match="exactly match"):
        template.instantiate({**values, "unsupported_claim": "valid vulnerability"})


def test_bola_card_consumes_the_milestone_4_proposal_without_overclaiming():
    card = load_builtin_catalogue().card("idor-bola")
    applied = card.revisions[-1]

    assert applied.version == "1.0.0"
    assert applied.source_kind == "test_fixture"
    assert "milestone4:card-update-local-bola-v1" in applied.source_refs
    assert "test-fixture:milestone4-local-two-account" in card.completed_lab_refs
    assert card.real_session_refs == ()
    assert "safe denial control" in applied.summary
    assert any("receipt-bound evidence" in item for item in card.lessons)


def test_lab_completion_and_test_fixture_assessment_do_not_award_mastery(tmp_path):
    catalogue = load_builtin_catalogue()
    catalogue.run_fixture("idor-bola", clock=lambda: NOW)
    fixture_assessment = human_assessment(
        id="assessment-bola-fixture-1",
        assessor="milestone5-acceptance-fixture",
        assessor_kind=AssessorKind.TEST_FIXTURE,
    )

    store = MasteryStore(tmp_path / "private-learning", catalogue=catalogue)
    store.record(fixture_assessment)
    credited = catalogue.graph.mastery_states(store.assessments())
    all_recorded = catalogue.graph.mastery_states(
        store.assessments(), include_non_crediting=True
    )

    credited_test = next(
        item
        for item in credited
        if item.card_id == "idor-bola" and item.dimension is MasteryDimension.TEST
    )
    recorded_test = next(
        item
        for item in all_recorded
        if item.card_id == "idor-bola" and item.dimension is MasteryDimension.TEST
    )
    assert credited_test.level is MasteryLevel.NOT_ASSESSED
    assert recorded_test.level is MasteryLevel.INDEPENDENT


def test_human_evidence_updates_only_one_dimension_and_prerequisite_gap(tmp_path):
    catalogue = load_builtin_catalogue()
    store = MasteryStore(tmp_path / "private-learning", catalogue=catalogue)
    store.record(human_assessment())
    states = catalogue.graph.mastery_states(store.assessments())

    bola = [item for item in states if item.card_id == "idor-bola"]
    assert len(bola) == 6
    assert next(item for item in bola if item.dimension is MasteryDimension.TEST).level is MasteryLevel.INDEPENDENT
    assert all(
        item.level is MasteryLevel.NOT_ASSESSED
        for item in bola
        if item.dimension is not MasteryDimension.TEST
    )
    assert catalogue.graph.prerequisite_gaps("bfla", store.assessments()) == ()
    assert catalogue.graph.prerequisite_gaps("csrf", store.assessments()) == (
        "session-management",
    )


def test_mastery_assessment_requires_evidence_and_cannot_name_ai_as_human():
    with pytest.raises(LearningError, match="at least one"):
        human_assessment(evidence_refs=())
    with pytest.raises(LearningError, match="model or agent"):
        human_assessment(assessor="GreyTheory AI assistant")
    with pytest.raises(LearningError, match="not-assessed"):
        human_assessment(level=MasteryLevel.NOT_ASSESSED)


def test_mastery_store_is_integrity_checked_and_refuses_repository_state(tmp_path):
    catalogue = load_builtin_catalogue()
    root = tmp_path / "private-learning"
    store = MasteryStore(root, catalogue=catalogue)
    store.record(human_assessment())
    store.verify()

    wrapper = json.loads((root / "mastery.json").read_text(encoding="utf-8"))
    wrapper["payload"]["assessments"][0]["level"] = "transferable"
    (root / "mastery.json").write_text(json.dumps(wrapper), encoding="utf-8")
    with pytest.raises(LearningStoreError, match="integrity check"):
        store.verify()

    repo = tmp_path / "repo"
    (repo / ".git").mkdir(parents=True)
    with pytest.raises(LearningStoreError, match="git working tree"):
        MasteryStore(repo / "learning", catalogue=catalogue)


def test_cli_verifies_catalogue_and_tracks_explicit_human_assessment(tmp_path, capsys):
    proof = tmp_path / "fixture-proof.json"
    assert main(["learning", "verify", "--out", str(proof), "--json"]) == 0
    verified = json.loads(capsys.readouterr().out)
    assert verified["card_count"] == verified["fixture_count"] == 12
    assert verified["real_vulnerabilities_proven"] == 0
    assert verified["mastery_credits_awarded"] == 0
    assert verified["network_actions"] == 0
    assert json.loads(proof.read_text(encoding="utf-8"))["catalogue_digest"] == verified[
        "catalogue_digest"
    ]

    root = tmp_path / "private-learning"
    assert main(
        [
            "learning",
            "assess",
            "--root",
            str(root),
            "--assessment-id",
            "assessment-cli-bola-test",
            "--card",
            "idor-bola",
            "--dimension",
            "test",
            "--level",
            "independent",
            "--assessor",
            "operator-chase",
            "--evidence-ref",
            "lab-report:controlled-two-account-review",
            "--rationale",
            "Reviewed the plan, controls, and clean repeat.",
            "--assessed-at",
            NOW.isoformat(),
            "--review-due",
            "2026-11-09",
            "--json",
        ]
    ) == 0
    recorded = json.loads(capsys.readouterr().out)
    assert recorded["credits_mastery"] is True

    assert main(["learning", "status", "--root", str(root), "--json"]) == 0
    status = json.loads(capsys.readouterr().out)
    assert status["credited_assessment_count"] == 1
    assert status["non_crediting_assessment_count"] == 0
    assert sum(item["level"] != "not_assessed" for item in status["mastery"]) == 1


def test_learning_modules_have_no_network_process_or_model_imports():
    root = Path(__file__).resolve().parents[1] / "greytheory" / "learning"
    forbidden = {"socket", "requests", "httpx", "urllib", "aiohttp", "subprocess", "openai", "anthropic"}
    for path in root.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imported: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module.split(".")[0])
        assert not (imported & forbidden), path
