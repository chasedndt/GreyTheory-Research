"""Synthetic, network-free acceptance fixture for the hypothesis engine."""

# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 ChaseInTech

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from greytheory.authority.gate import AuthorityLevel
from greytheory.authority.scope import (
    AssetPattern,
    ContractStatus,
    PatternType,
    ScopeClassification,
    ScopeContract,
)
from greytheory.hypothesis.domain import (
    AssessmentSource,
    FactorAssessment,
    HypothesisRankingInput,
    RankingFactor,
)
from greytheory.hypothesis.engine import HypothesisRanker
from greytheory.learning import VulnerabilityCatalogue, load_builtin_catalogue
from greytheory.research.domain import (
    AssetKind,
    EffectBudget,
    Hypothesis,
    ResearchSession,
    ResearchWorkspace,
    TargetAsset,
)
from greytheory.research.store import ResearchStore, WorkspaceSnapshot


FIXTURE_TIME = datetime(2026, 8, 9, 12, 0, tzinfo=timezone.utc)


@dataclass(frozen=True)
class LocalRankingFixture:
    contract: ScopeContract
    snapshot: WorkspaceSnapshot
    ranking_inputs: tuple[HypothesisRankingInput, ...]
    catalogue: VulnerabilityCatalogue


def _assessment(
    factor: RankingFactor, level: int, *, hypothesis_id: str
) -> FactorAssessment:
    return FactorAssessment(
        factor=factor,
        level=level,
        rationale=(
            f"Synthetic operator estimate for {hypothesis_id}; this value exists only "
            "to exercise deterministic queue ordering."
        ),
        provenance_refs=(f"fixture-assessment:{hypothesis_id}:{factor.value}",),
        uncertainties=(
            "This is a test-fixture estimate and says nothing about an external system.",
        ),
        source=AssessmentSource.TEST_FIXTURE,
    )


def _ranking_input(
    hypothesis_id: str,
    card_id: str,
    *,
    likelihood: int,
    impact: int,
    duplicate: int,
    skill: int,
    novelty: int,
) -> HypothesisRankingInput:
    values = {
        RankingFactor.LIKELIHOOD: likelihood,
        RankingFactor.POTENTIAL_IMPACT: impact,
        RankingFactor.DUPLICATE_RISK: duplicate,
        RankingFactor.SKILL_VALUE: skill,
        RankingFactor.TARGET_SPECIFIC_NOVELTY: novelty,
    }
    return HypothesisRankingInput(
        id=f"ranking-input-{hypothesis_id}",
        hypothesis_id=hypothesis_id,
        card_id=card_id,
        actor="fixture-operator",
        source_ref=f"fixture-ranking:{hypothesis_id}",
        assessments=tuple(
            _assessment(factor, level, hypothesis_id=hypothesis_id)
            for factor, level in values.items()
        ),
    )


def _hypothesis(
    *,
    hypothesis_id: str,
    authority_ref: str,
    title: str,
    action: str,
    consequence: str,
    supporting_refs: tuple[str, ...],
    request_cost: int,
    time_cost: int,
    effects: EffectBudget,
) -> Hypothesis:
    return Hypothesis(
        id=hypothesis_id,
        workspace_id="workspace-ranking-local",
        session_id="session-ranking-local",
        authority_ref=authority_ref,
        title=title,
        preconditions=("Use only the synthetic local fixture and controlled records.",),
        actor_identity_id=None,
        action=action,
        target_asset_id="asset-ranking-local",
        consequence=consequence,
        reasoning="A deliberately bounded theory used to test queue prioritisation.",
        supporting_observation_refs=supporting_refs,
        assumptions=("All represented state is synthetic and locally controlled.",),
        required_authority=AuthorityLevel.LOCAL_FIXTURE,
        expected_safe_behaviour="The local control rejects the disallowed transition.",
        expected_vulnerable_behaviour="The local control accepts the deliberately weak transition.",
        falsifier="All positive and negative fixture controls behave as specified.",
        evidence_needs=("Synthetic control receipt", "Exact fixture-state reference"),
        stop_conditions=("Stop before any network, browser, model, or process action.",),
        estimated_request_cost=request_cost,
        estimated_time_minutes=time_cost,
        estimated_effects=effects,
        duplicate_risk="Estimated only by the labelled fixture input.",
        learning_value="Estimated only by the labelled fixture input.",
    )


def build_local_ranking_fixture() -> LocalRankingFixture:
    contract = ScopeContract(
        id="contract-ranking-local",
        programme_id="programme-ranking-local",
        verified_at=datetime(2026, 8, 9, 9, 0, tzinfo=timezone.utc),
        status=ContractStatus.VERIFIED,
        assets_in_scope=(
            AssetPattern(PatternType.EXACT, "local.rank.fixture", "synthetic only"),
        ),
        assets_out_of_scope=(),
        prohibited_techniques=("network", "browser", "model", "process"),
        max_authority="LOCAL_FIXTURE",
        rate_limit_rps=None,
        ambiguities=(),
        source_hashes=("fixture-source-ranking-local",),
        human_reviewed=True,
        notes="Synthetic Milestone 6 ranking fixture; grants no external authority.",
    )
    authority_ref = contract.fingerprint()
    workspace = ResearchWorkspace(
        id="workspace-ranking-local",
        programme_id=contract.programme_id,
        contract_id=contract.id,
        authority_ref=authority_ref,
        title="Synthetic ranking workspace",
        operating_posture=AuthorityLevel.LOCAL_FIXTURE,
        request_budget=10,
        time_budget_minutes=60,
        effect_budget=EffectBudget.from_mapping({"reads": 4, "mutations": 0}),
        goals=("Produce an explainable queue without executing any hypothesis.",),
        created_at=FIXTURE_TIME,
    )
    asset = TargetAsset(
        id="asset-ranking-local",
        workspace_id=workspace.id,
        authority_ref=authority_ref,
        kind=AssetKind.LOCAL_FIXTURE,
        canonical_identifier="local.rank.fixture",
        scope_classification=ScopeClassification.IN_SCOPE,
        display_name="Synthetic ranking fixture",
        classification_evidence_ref="fixture-scope:ranking-local",
    )
    session = ResearchSession(
        id="session-ranking-local",
        workspace_id=workspace.id,
        authority_ref=authority_ref,
        goal="Prioritise three synthetic research theories without action.",
        operating_posture=AuthorityLevel.LOCAL_FIXTURE,
        identity_ids=(),
        request_budget=10,
        time_budget_minutes=60,
        effect_budget=EffectBudget.from_mapping({"reads": 4, "mutations": 0}),
        created_at=FIXTURE_TIME,
    )
    hypotheses = (
        _hypothesis(
            hypothesis_id="hypothesis-ranking-bola",
            authority_ref=authority_ref,
            title="Controlled object-ownership theory",
            action="Compare one synthetic cross-owner object read.",
            consequence="A controlled ownership boundary may not be enforced.",
            supporting_refs=("fixture-observation:ownership-map", "fixture-observation:control"),
            request_cost=1,
            time_cost=10,
            effects=EffectBudget.from_mapping({"reads": 1}),
        ),
        _hypothesis(
            hypothesis_id="hypothesis-ranking-csrf",
            authority_ref=authority_ref,
            title="Controlled intent-binding theory",
            action="Compare one synthetic state-transition token.",
            consequence="A controlled action may not be bound to synthetic intent.",
            supporting_refs=("fixture-observation:intent-map",),
            request_cost=2,
            time_cost=25,
            effects=EffectBudget.from_mapping({"reads": 1}),
        ),
        _hypothesis(
            hypothesis_id="hypothesis-ranking-session",
            authority_ref=authority_ref,
            title="Controlled session-invalidation theory",
            action="Compare one synthetic post-invalidation session state.",
            consequence="A synthetic session may remain active after invalidation.",
            supporting_refs=(),
            request_cost=1,
            time_cost=5,
            effects=EffectBudget(),
        ),
    )
    snapshot = WorkspaceSnapshot(
        workspace=workspace,
        assets={asset.id: asset},
        relationships={},
        identities={},
        sessions={session.id: session},
        hypotheses={item.id: item for item in hypotheses},
        experiments={},
        action_requests={},
        action_receipts={},
        lessons={},
    )
    ranking_inputs = (
        _ranking_input(
            "hypothesis-ranking-bola",
            "idor-bola",
            likelihood=3,
            impact=3,
            duplicate=2,
            skill=4,
            novelty=3,
        ),
        _ranking_input(
            "hypothesis-ranking-csrf",
            "csrf",
            likelihood=2,
            impact=2,
            duplicate=1,
            skill=3,
            novelty=2,
        ),
        _ranking_input(
            "hypothesis-ranking-session",
            "session-management",
            likelihood=1,
            impact=2,
            duplicate=3,
            skill=2,
            novelty=1,
        ),
    )
    return LocalRankingFixture(
        contract=contract,
        snapshot=snapshot,
        ranking_inputs=ranking_inputs,
        catalogue=load_builtin_catalogue(),
    )


def populate_local_ranking_store(root: str | Path) -> LocalRankingFixture:
    fixture = build_local_ranking_fixture()
    store = ResearchStore(root)
    store.create_workspace(
        fixture.snapshot.workspace, contract=fixture.contract, actor="fixture-operator"
    )
    for asset in fixture.snapshot.assets.values():
        store.add_asset(asset, contract=fixture.contract, actor="fixture-operator")
    for session in fixture.snapshot.sessions.values():
        store.add_session(session, actor="fixture-operator")
    for hypothesis in fixture.snapshot.hypotheses.values():
        store.add_hypothesis(hypothesis, actor="fixture-operator")
    return fixture


def run_local_ranking_fixture() -> dict[str, object]:
    fixture = build_local_ranking_fixture()
    before_requests = len(fixture.snapshot.action_requests)
    before_receipts = len(fixture.snapshot.action_receipts)
    queue = HypothesisRanker(clock=lambda: FIXTURE_TIME).rank(
        snapshot=fixture.snapshot,
        contract=fixture.contract,
        ranking_inputs=fixture.ranking_inputs,
        catalogue=fixture.catalogue,
    )
    return {
        "status": "complete",
        "operating_posture": "LOCAL_FIXTURE",
        "queue": queue.to_dict(),
        "ranked_hypotheses": len(queue.items),
        "explained_factors_per_item": [len(item.factors) for item in queue.items],
        "claim_states": sorted({item.claim_state for item in queue.items}),
        "execution_requests_before": before_requests,
        "execution_requests_after": len(fixture.snapshot.action_requests),
        "action_receipts_before": before_receipts,
        "action_receipts_after": len(fixture.snapshot.action_receipts),
        "network_actions": 0,
        "model_calls": 0,
        "external_targets": 0,
    }
