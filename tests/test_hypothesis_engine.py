from __future__ import annotations

import ast
import json
from dataclasses import replace
from pathlib import Path

import pytest

from greytheory.cli import main
from greytheory.hypothesis import (
    ASSESSED_FACTORS,
    SYSTEM_DERIVED_FACTORS,
    AssessmentSource,
    FactorAssessment,
    FactorDirection,
    HypothesisRanker,
    HypothesisRankingError,
    HypothesisRankingInput,
    QueuePartition,
    RankingFactor,
    build_local_ranking_fixture,
    conservative_local_policy,
    parse_ranking_inputs,
    populate_local_ranking_store,
    run_local_ranking_fixture,
    write_research_queue,
)
from greytheory.research.domain import HypothesisStatus, TargetAsset


def test_policy_has_exact_nine_factors_and_conservative_directions():
    policy = conservative_local_policy()

    assert {item.factor for item in policy.weights} == set(RankingFactor)
    assert len(policy.weights) == 9
    assert sum(item.weight_percent for item in policy.weights) == 100
    assert SYSTEM_DERIVED_FACTORS == {
        RankingFactor.SCOPE_CONFIDENCE,
        RankingFactor.EVIDENCE_ALREADY_PRESENT,
        RankingFactor.TEST_COST,
        RankingFactor.SIDE_EFFECT_RISK,
    }
    assert ASSESSED_FACTORS == set(RankingFactor) - SYSTEM_DERIVED_FACTORS
    assert policy.weight(RankingFactor.TEST_COST).direction is FactorDirection.LOWER_IS_BETTER
    assert (
        policy.weight(RankingFactor.SIDE_EFFECT_RISK).direction
        is FactorDirection.LOWER_IS_BETTER
    )
    assert policy.effect_level("unknown-effect") == (4, False)


def test_local_fixture_produces_stable_fully_explained_ranked_queue():
    proof = run_local_ranking_fixture()
    queue = proof["queue"]

    assert proof["status"] == "complete"
    assert proof["ranked_hypotheses"] == 3
    assert proof["explained_factors_per_item"] == [9, 9, 9]
    assert proof["claim_states"] == ["unproven"]
    assert [item["hypothesis_id"] for item in queue["items"]] == [
        "hypothesis-ranking-bola",
        "hypothesis-ranking-csrf",
        "hypothesis-ranking-session",
    ]
    assert [item["score_bps"] for item in queue["items"]] == [7500, 6375, 5625]
    assert [item["rank"] for item in queue["items"]] == [1, 2, 3]
    assert all(
        [factor["factor"] for factor in item["factors"]]
        == [factor.value for factor in RankingFactor]
        for item in queue["items"]
    )
    assert all(
        sum(factor["contribution_bps"] for factor in item["factors"])
        == item["score_bps"]
        for item in queue["items"]
    )
    assert queue["queue_digest"] == run_local_ranking_fixture()["queue"]["queue_digest"]


def test_queue_is_explicitly_unproven_and_cannot_create_execution_records():
    proof = run_local_ranking_fixture()
    queue = proof["queue"]

    assert queue["decision_support_only"] is True
    assert queue["claim_state"] == "unproven_hypotheses"
    assert queue["execution_requests_created"] == 0
    assert queue["action_receipts_created"] == 0
    assert proof["execution_requests_before"] == proof["execution_requests_after"] == 0
    assert proof["action_receipts_before"] == proof["action_receipts_after"] == 0
    assert proof["network_actions"] == proof["model_calls"] == proof["external_targets"] == 0
    for item in queue["items"]:
        assert item["item_type"] == "research_hypothesis"
        assert item["claim_state"] == "unproven"
        assert item["decision_support_only"] is True
        assert item["execution_authority"] == "none"
        assert item["theory"]["falsifier"]
        assert item["theory"]["minimum_evidence"]
        assert item["theory"]["proposed_action"]


def test_queue_digest_and_factor_arithmetic_are_self_verifying():
    fixture = build_local_ranking_fixture()
    queue = HypothesisRanker(clock=lambda: fixture.snapshot.workspace.created_at).rank(
        snapshot=fixture.snapshot,
        contract=fixture.contract,
        ranking_inputs=fixture.ranking_inputs,
        catalogue=fixture.catalogue,
    )

    assert queue.queue_digest == queue.calculated_digest()
    with pytest.raises(HypothesisRankingError, match="integrity"):
        replace(queue, queue_digest="0" * 64)
    first = queue.items[0]
    factor = first.factors[0]
    with pytest.raises(HypothesisRankingError, match="contribution"):
        replace(factor, contribution_bps=factor.contribution_bps + 1)


def test_assessed_score_change_has_exact_explained_delta():
    fixture = build_local_ranking_fixture()
    original = fixture.ranking_inputs[1]
    changed_assessments = tuple(
        replace(item, level=3)
        if item.factor is RankingFactor.LIKELIHOOD
        else item
        for item in original.assessments
    )
    changed = replace(original, assessments=changed_assessments)
    ranker = HypothesisRanker(clock=lambda: fixture.snapshot.workspace.created_at)

    baseline = ranker.rank(
        snapshot=fixture.snapshot,
        contract=fixture.contract,
        ranking_inputs=(original,),
        catalogue=fixture.catalogue,
    ).items[0]
    rescored = ranker.rank(
        snapshot=fixture.snapshot,
        contract=fixture.contract,
        ranking_inputs=(changed,),
        catalogue=fixture.catalogue,
    ).items[0]

    assert rescored.score_bps - baseline.score_bps == 250
    likelihood = next(
        item for item in rescored.factors if item.factor is RankingFactor.LIKELIHOOD
    )
    assert likelihood.raw_level == 3
    assert likelihood.weight_percent == 10
    assert likelihood.contribution_bps == 750


def test_inputs_require_exact_assessed_factors_and_reject_derived_self_scores():
    fixture = build_local_ranking_fixture()
    valid = fixture.ranking_inputs[0]

    with pytest.raises(HypothesisRankingError, match="exactly five factors"):
        replace(valid, assessments=valid.assessments[:-1])

    with pytest.raises(HypothesisRankingError, match="system-derived"):
        FactorAssessment(
            factor=RankingFactor.SCOPE_CONFIDENCE,
            level=4,
            rationale="Caller tries to award scope confidence.",
            provenance_refs=("caller:scope",),
            uncertainties=("This must be derived instead.",),
            source=AssessmentSource.OPERATOR,
        )


def test_model_source_is_refused_before_the_model_gateway_exists():
    data = build_local_ranking_fixture().ranking_inputs[0].to_dict()
    data["assessments"][0]["source"] = "model"

    with pytest.raises(HypothesisRankingError, match="model scoring is not built"):
        HypothesisRankingInput.from_dict(data)


def test_scope_uncertainty_partitions_items_ahead_of_numeric_score():
    fixture = build_local_ranking_fixture()
    original = fixture.snapshot.hypotheses["hypothesis-ranking-bola"]
    unresolved_asset = TargetAsset(
        id="asset-ranking-unresolved",
        workspace_id=fixture.snapshot.workspace.id,
        authority_ref=fixture.snapshot.workspace.authority_ref,
        kind=fixture.snapshot.assets["asset-ranking-local"].kind,
        canonical_identifier="unlisted.rank.fixture",
        scope_classification=fixture.snapshot.assets[
            "asset-ranking-local"
        ].scope_classification.UNRESOLVED,
        display_name="Unresolved synthetic asset",
        classification_evidence_ref="fixture-scope:unresolved",
    )
    hypotheses = {
        **fixture.snapshot.hypotheses,
        original.id: replace(original, target_asset_id=unresolved_asset.id),
    }
    snapshot = replace(
        fixture.snapshot,
        assets={**fixture.snapshot.assets, unresolved_asset.id: unresolved_asset},
        hypotheses=hypotheses,
    )

    queue = HypothesisRanker(clock=lambda: fixture.snapshot.workspace.created_at).rank(
        snapshot=snapshot,
        contract=fixture.contract,
        ranking_inputs=fixture.ranking_inputs,
        catalogue=fixture.catalogue,
    )

    assert queue.items[-1].hypothesis_id == original.id
    assert queue.items[-1].queue_partition is QueuePartition.SCOPE_REVIEW_REQUIRED
    scope = queue.items[-1].factors[0]
    assert scope.factor is RankingFactor.SCOPE_CONFIDENCE
    assert scope.raw_level == scope.contribution_bps == 0


def test_wrong_contract_and_terminal_hypotheses_are_refused():
    fixture = build_local_ranking_fixture()
    ranker = HypothesisRanker(clock=lambda: fixture.snapshot.workspace.created_at)

    wrong_contract = replace(fixture.contract, prohibited_techniques=("different",))
    with pytest.raises(HypothesisRankingError, match="authority does not match"):
        ranker.rank(
            snapshot=fixture.snapshot,
            contract=wrong_contract,
            ranking_inputs=fixture.ranking_inputs,
            catalogue=fixture.catalogue,
        )

    first = fixture.snapshot.hypotheses[fixture.ranking_inputs[0].hypothesis_id]
    terminal = replace(first, status=HypothesisStatus.REFUTED)
    snapshot = replace(
        fixture.snapshot,
        hypotheses={**fixture.snapshot.hypotheses, first.id: terminal},
    )
    with pytest.raises(HypothesisRankingError, match="not queueable"):
        ranker.rank(
            snapshot=snapshot,
            contract=fixture.contract,
            ranking_inputs=fixture.ranking_inputs,
            catalogue=fixture.catalogue,
        )


def test_parse_inputs_rejects_duplicates_and_empty_packets():
    data = build_local_ranking_fixture().ranking_inputs[0].to_dict()
    with pytest.raises(HypothesisRankingError, match="at least one"):
        parse_ranking_inputs([])
    with pytest.raises(HypothesisRankingError, match="only once"):
        parse_ranking_inputs([data, {**data, "id": "another-input"}])


def test_queue_writeback_is_atomic_and_refuses_repository_storage(tmp_path):
    fixture = build_local_ranking_fixture()
    queue = HypothesisRanker(clock=lambda: fixture.snapshot.workspace.created_at).rank(
        snapshot=fixture.snapshot,
        contract=fixture.contract,
        ranking_inputs=fixture.ranking_inputs,
        catalogue=fixture.catalogue,
    )
    output = write_research_queue(tmp_path / "queue.json", queue)

    assert json.loads(output.read_text(encoding="utf-8"))["queue_digest"] == queue.queue_digest
    assert not (tmp_path / ".queue.json.tmp").exists()
    with pytest.raises(HypothesisRankingError, match="cannot be written inside"):
        write_research_queue(Path.cwd() / "build" / "forbidden-queue.json", queue)


def test_cli_verify_and_private_store_ranking(tmp_path, capsys):
    proof_path = tmp_path / "ranking-proof.json"
    assert main(["hypothesis", "verify", "--out", str(proof_path), "--json"]) == 0
    proof = json.loads(capsys.readouterr().out)
    assert proof["ranked_hypotheses"] == 3
    assert proof_path.exists()

    root = tmp_path / "research"
    fixture = populate_local_ranking_store(root)
    contract_path = tmp_path / "contract.json"
    contract_path.write_text(
        json.dumps(fixture.contract.to_dict(), indent=2), encoding="utf-8"
    )
    inputs_path = tmp_path / "ranking-inputs.json"
    inputs_path.write_text(
        json.dumps(
            {"ranking_inputs": [item.to_dict() for item in fixture.ranking_inputs]},
            indent=2,
        ),
        encoding="utf-8",
    )
    queue_path = tmp_path / "queue.json"
    assert (
        main(
            [
                "--actor",
                "fixture-operator",
                "hypothesis",
                "rank",
                "--root",
                str(root),
                "--workspace",
                fixture.snapshot.workspace.id,
                "--contract",
                str(contract_path),
                "--assessments",
                str(inputs_path),
                "--as-of",
                fixture.snapshot.workspace.created_at.isoformat(),
                "--out",
                str(queue_path),
                "--json",
            ]
        )
        == 0
    )
    queue = json.loads(capsys.readouterr().out)
    assert queue["item_count"] == 3
    assert queue["queue_digest"] == json.loads(queue_path.read_text())["queue_digest"]
    assert (root / "ranking-audit.jsonl").exists()


def test_engine_has_no_network_model_process_or_execution_imports():
    root = Path(__file__).parents[1]
    files = tuple((root / "greytheory" / "hypothesis").glob("*.py"))
    imported: set[str] = set()
    for path in files:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module)
                imported.add(node.module.split(".")[0])

    assert not imported.intersection(
        {
            "socket",
            "requests",
            "httpx",
            "urllib",
            "subprocess",
            "playwright",
            "selenium",
            "openai",
            "anthropic",
            "greytheory.execution",
        }
    )
