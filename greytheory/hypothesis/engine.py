"""Deterministic, explainable hypothesis ranking with no execution path."""

# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 ChaseInTech

from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from datetime import datetime, timezone
from typing import Callable

from greytheory.authority.gate import DEFAULT_MAX_CONTRACT_AGE
from greytheory.authority.scope import (
    ContractStatus,
    ScopeClassification,
    ScopeContract,
)
from greytheory.hypothesis.domain import (
    ASSESSED_FACTORS,
    AssessmentSource,
    FactorDirection,
    FactorExplanation,
    HypothesisRankingError,
    HypothesisRankingInput,
    QueuePartition,
    RankedHypothesis,
    RankingFactor,
    RankingPolicy,
    ResearchQueue,
    conservative_local_policy,
)
from greytheory.learning import LearningError, VulnerabilityCatalogue
from greytheory.research.domain import Hypothesis, HypothesisStatus, ResearchSession
from greytheory.research.store import WorkspaceSnapshot


QUEUEABLE_STATUSES = frozenset(
    {HypothesisStatus.DRAFT, HypothesisStatus.SCOPED, HypothesisStatus.PLANNED}
)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _canonical(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


class HypothesisRanker:
    """Create a ranked queue of unproven research hypotheses.

    Four factors are derived from governed records.  Five factors are explicit
    estimates with provenance and uncertainty.  The ranker cannot transition a
    hypothesis, call the Gate, create an action request, or create a receipt.
    """

    def __init__(
        self,
        *,
        policy: RankingPolicy | None = None,
        clock: Callable[[], datetime] = _utcnow,
    ) -> None:
        self.policy = policy or conservative_local_policy()
        self._clock = clock

    def rank(
        self,
        *,
        snapshot: WorkspaceSnapshot,
        contract: ScopeContract,
        ranking_inputs: tuple[HypothesisRankingInput, ...],
        catalogue: VulnerabilityCatalogue,
    ) -> ResearchQueue:
        now = self._clock()
        if now.tzinfo is None:
            raise HypothesisRankingError("ranking clock must be timezone-aware")
        self._validate_binding(snapshot, contract)
        if not ranking_inputs:
            raise HypothesisRankingError("at least one hypothesis is required")

        before_requests = len(snapshot.action_requests)
        before_receipts = len(snapshot.action_receipts)
        seen: set[str] = set()
        scored: list[RankedHypothesis] = []
        for ranking_input in ranking_inputs:
            if ranking_input.hypothesis_id in seen:
                raise HypothesisRankingError("each hypothesis may appear only once")
            seen.add(ranking_input.hypothesis_id)
            try:
                hypothesis = snapshot.hypotheses[ranking_input.hypothesis_id]
            except KeyError as exc:
                raise HypothesisRankingError(
                    f"unknown hypothesis {ranking_input.hypothesis_id!r}"
                ) from exc
            if hypothesis.status not in QUEUEABLE_STATUSES:
                raise HypothesisRankingError(
                    f"hypothesis {hypothesis.id!r} is {hypothesis.status.value}, not queueable"
                )
            try:
                catalogue.card(ranking_input.card_id)
            except LearningError as exc:
                raise HypothesisRankingError(
                    f"unknown vulnerability card {ranking_input.card_id!r}"
                ) from exc
            session = snapshot.sessions[hypothesis.session_id]
            scored.append(
                self._score(
                    snapshot=snapshot,
                    contract=contract,
                    hypothesis=hypothesis,
                    session=session,
                    ranking_input=ranking_input,
                    now=now,
                )
            )

        if len(snapshot.action_requests) != before_requests or len(snapshot.action_receipts) != before_receipts:
            raise HypothesisRankingError("ranking mutated execution records")

        ordered = sorted(
            scored,
            key=lambda item: (
                0 if item.queue_partition is QueuePartition.PLANNING_CANDIDATE else 1,
                -item.score_bps,
                item.hypothesis_id,
            ),
        )
        ranked = tuple(replace(item, rank=index) for index, item in enumerate(ordered, 1))
        material = {
            "schema_version": 1,
            "generated_at": now.astimezone(timezone.utc).isoformat(),
            "workspace_id": snapshot.workspace.id,
            "programme_id": snapshot.workspace.programme_id,
            "contract_fingerprint": contract.fingerprint(),
            "operating_posture": snapshot.workspace.operating_posture.name,
            "catalogue_digest": catalogue.digest(),
            "policy": {**self.policy.to_dict(), "digest": self.policy.digest()},
            "items": [item.to_dict() for item in ranked],
            "decision_support_only": True,
            "execution_requests_created": 0,
            "action_receipts_created": 0,
            "claim_state": "unproven_hypotheses",
        }
        digest = hashlib.sha256(_canonical(material).encode("utf-8")).hexdigest()
        return ResearchQueue(
            id=f"research-queue-{digest[:12]}",
            schema_version=1,
            generated_at=now,
            workspace_id=snapshot.workspace.id,
            programme_id=snapshot.workspace.programme_id,
            contract_fingerprint=contract.fingerprint(),
            operating_posture=snapshot.workspace.operating_posture.name,
            catalogue_digest=catalogue.digest(),
            policy=self.policy,
            items=ranked,
            queue_digest=digest,
        )

    @staticmethod
    def _validate_binding(snapshot: WorkspaceSnapshot, contract: ScopeContract) -> None:
        workspace = snapshot.workspace
        if workspace.programme_id != contract.programme_id:
            raise HypothesisRankingError("workspace programme does not match the contract")
        if workspace.contract_id != contract.id:
            raise HypothesisRankingError("workspace contract id does not match the contract")
        if workspace.authority_ref != contract.fingerprint():
            raise HypothesisRankingError("workspace authority does not match the contract")

    def _score(
        self,
        *,
        snapshot: WorkspaceSnapshot,
        contract: ScopeContract,
        hypothesis: Hypothesis,
        session: ResearchSession,
        ranking_input: HypothesisRankingInput,
        now: datetime,
    ) -> RankedHypothesis:
        explanations: list[FactorExplanation] = []
        scope = self._scope_factor(snapshot, contract, hypothesis, now)
        explanations.append(scope)
        explanations.append(self._evidence_factor(hypothesis))

        for factor in (
            RankingFactor.LIKELIHOOD,
            RankingFactor.POTENTIAL_IMPACT,
        ):
            explanations.append(self._assessed_factor(ranking_input, factor))

        explanations.append(self._test_cost_factor(hypothesis, session))
        explanations.append(self._side_effect_factor(hypothesis))

        for factor in (
            RankingFactor.DUPLICATE_RISK,
            RankingFactor.SKILL_VALUE,
            RankingFactor.TARGET_SPECIFIC_NOVELTY,
        ):
            explanations.append(self._assessed_factor(ranking_input, factor))

        if tuple(item.factor for item in explanations) != tuple(RankingFactor):
            raise HypothesisRankingError("internal factor order is incomplete")
        score = sum(item.contribution_bps for item in explanations)
        partition = (
            QueuePartition.PLANNING_CANDIDATE
            if scope.raw_level == 4
            else QueuePartition.SCOPE_REVIEW_REQUIRED
        )
        return RankedHypothesis(
            rank=0,
            hypothesis_id=hypothesis.id,
            card_id=ranking_input.card_id,
            source_title=hypothesis.title,
            source_status=hypothesis.status.value,
            proposed_action=hypothesis.action,
            target_asset_id=hypothesis.target_asset_id,
            potential_consequence=hypothesis.consequence,
            reasoning=hypothesis.reasoning,
            expected_safe_behaviour=hypothesis.expected_safe_behaviour,
            expected_counter_behaviour=hypothesis.expected_vulnerable_behaviour,
            falsifier=hypothesis.falsifier,
            minimum_evidence=hypothesis.evidence_needs,
            queue_partition=partition,
            score_bps=score,
            item_type="research_hypothesis",
            claim_state="unproven",
            decision_support_only=True,
            execution_authority="none",
            factors=tuple(explanations),
            assumptions=hypothesis.assumptions,
            stop_conditions=hypothesis.stop_conditions,
        )

    def _explanation(
        self,
        factor: RankingFactor,
        raw_level: int,
        *,
        rationale: str,
        provenance_refs: tuple[str, ...],
        uncertainties: tuple[str, ...],
        derivation: str,
        observed_inputs: tuple[str, ...],
    ) -> FactorExplanation:
        weight = self.policy.weight(factor)
        oriented = (
            raw_level
            if weight.direction is FactorDirection.HIGHER_IS_BETTER
            else 4 - raw_level
        )
        return FactorExplanation(
            factor=factor,
            raw_level=raw_level,
            oriented_level=oriented,
            direction=weight.direction,
            weight_percent=weight.weight_percent,
            contribution_bps=oriented * weight.weight_percent * 25,
            rationale=rationale,
            provenance_refs=provenance_refs,
            uncertainties=uncertainties,
            derivation=derivation,
            observed_inputs=observed_inputs,
        )

    def _scope_factor(
        self,
        snapshot: WorkspaceSnapshot,
        contract: ScopeContract,
        hypothesis: Hypothesis,
        now: datetime,
    ) -> FactorExplanation:
        asset = snapshot.assets[hypothesis.target_asset_id]
        current = contract.classify(asset.canonical_identifier)
        reasons: list[str] = []
        if contract.status is not ContractStatus.VERIFIED:
            reasons.append(f"contract status is {contract.status.value}")
        if not contract.human_reviewed:
            reasons.append("contract is not human-reviewed")
        if contract.is_stale(now=now, max_age=DEFAULT_MAX_CONTRACT_AGE):
            reasons.append("contract is stale")
        if asset.scope_classification is not ScopeClassification.IN_SCOPE:
            reasons.append(f"stored asset classification is {asset.scope_classification.value}")
        if current is not ScopeClassification.IN_SCOPE:
            reasons.append(f"current contract classification is {current.value}")
        if current is not asset.scope_classification:
            reasons.append("stored and current classifications differ")
        level = 4 if not reasons else 0
        rationale = (
            "Current human-reviewed contract and stored asset record agree that the target is in scope."
            if level == 4
            else "Scope confidence is fail-closed: " + "; ".join(reasons) + "."
        )
        return self._explanation(
            RankingFactor.SCOPE_CONFIDENCE,
            level,
            rationale=rationale,
            provenance_refs=(
                f"contract:{contract.id}",
                f"contract-fingerprint:{contract.fingerprint()}",
                asset.classification_evidence_ref,
            ),
            uncertainties=(
                "Scope confidence is authority evidence only; it does not support the hypothesis itself.",
            ),
            derivation="system_derived",
            observed_inputs=(
                f"contract_status={contract.status.value}",
                f"human_reviewed={str(contract.human_reviewed).lower()}",
                f"stored_classification={asset.scope_classification.value}",
                f"current_classification={current.value}",
            ),
        )

    def _evidence_factor(self, hypothesis: Hypothesis) -> FactorExplanation:
        refs = tuple(dict.fromkeys((*hypothesis.supporting_observation_refs, *hypothesis.result_refs)))
        level = min(len(refs), 4)
        return self._explanation(
            RankingFactor.EVIDENCE_ALREADY_PRESENT,
            level,
            rationale=(
                f"The hypothesis declares {len(refs)} unique supporting/result reference(s); "
                "the level is a capped inventory count, not an evidence-quality judgement."
            ),
            provenance_refs=refs,
            uncertainties=(
                "Reference presence does not prove integrity, relevance, or support for the consequence.",
            ),
            derivation="system_derived",
            observed_inputs=(f"declared_reference_count={len(refs)}",),
        )

    def _test_cost_factor(
        self, hypothesis: Hypothesis, session: ResearchSession
    ) -> FactorExplanation:
        request_ratio = self._ratio(hypothesis.estimated_request_cost, session.request_budget)
        time_ratio = self._ratio(hypothesis.estimated_time_minutes, session.time_budget_minutes)
        ratio = max(request_ratio, time_ratio)
        level = self._ratio_level(ratio)
        return self._explanation(
            RankingFactor.TEST_COST,
            level,
            rationale=(
                "Cost magnitude is the larger of declared request-budget and time-budget use; "
                f"the maximum ratio is {ratio:.4f}."
            ),
            provenance_refs=(f"session:{session.id}", f"hypothesis:{hypothesis.id}"),
            uncertainties=(
                "Declared estimates may differ from future observed cost and grant no permission to test.",
            ),
            derivation="system_derived",
            observed_inputs=(
                f"requests={hypothesis.estimated_request_cost}/{session.request_budget}",
                f"minutes={hypothesis.estimated_time_minutes}/{session.time_budget_minutes}",
            ),
        )

    def _side_effect_factor(self, hypothesis: Hypothesis) -> FactorExplanation:
        active = tuple((name, amount) for name, amount in hypothesis.estimated_effects.limits if amount)
        unknown: list[str] = []
        levels: list[int] = []
        for name, _ in active:
            level, known = self.policy.effect_level(name)
            levels.append(level)
            if not known:
                unknown.append(name)
        level = max(levels, default=0)
        uncertainty = [
            "Effect levels describe declared side-effect magnitude, not observed behavior."
        ]
        if unknown:
            uncertainty.append(
                "Unknown effect names use the policy's conservative maximum: " + ", ".join(unknown) + "."
            )
        return self._explanation(
            RankingFactor.SIDE_EFFECT_RISK,
            level,
            rationale=(
                "The policy maps each non-zero declared effect to a risk level and uses the maximum; "
                f"active effects are {dict(active)}."
            ),
            provenance_refs=(f"hypothesis:{hypothesis.id}", f"policy:{self.policy.id}"),
            uncertainties=tuple(uncertainty),
            derivation="system_derived",
            observed_inputs=tuple(f"{name}={amount}" for name, amount in active) or ("no_effects",),
        )

    def _assessed_factor(
        self, ranking_input: HypothesisRankingInput, factor: RankingFactor
    ) -> FactorExplanation:
        if factor not in ASSESSED_FACTORS:
            raise HypothesisRankingError(f"{factor.value} is not an assessed factor")
        assessment = ranking_input.assessment(factor)
        derivation = (
            "operator_estimate"
            if assessment.source is AssessmentSource.OPERATOR
            else "test_fixture_estimate"
        )
        return self._explanation(
            factor,
            assessment.level,
            rationale=assessment.rationale,
            provenance_refs=(ranking_input.source_ref, *assessment.provenance_refs),
            uncertainties=assessment.uncertainties,
            derivation=derivation,
            observed_inputs=(
                f"assessment_id={ranking_input.id}",
                f"actor={ranking_input.actor}",
                f"source={assessment.source.value}",
                f"raw_level={assessment.level}",
            ),
        )

    @staticmethod
    def _ratio(amount: int, budget: int) -> float:
        if budget == 0:
            return 0.0 if amount == 0 else 1.0
        return amount / budget

    @staticmethod
    def _ratio_level(ratio: float) -> int:
        if ratio <= 0:
            return 0
        if ratio <= 0.25:
            return 1
        if ratio <= 0.50:
            return 2
        if ratio <= 0.75:
            return 3
        return 4
