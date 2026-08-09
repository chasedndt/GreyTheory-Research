"""The first complete GreyTheory research demonstration, entirely local.

This module joins the existing authority, research, evidence, validation and
reporting contracts around one deliberately vulnerable two-account fixture.
It raises no operating posture and exposes no submission path.
"""

# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 ChaseInTech

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable

from greytheory.audit import AuditLog
from greytheory.authority.compiler import compile_contract, mark_reviewed
from greytheory.authority.gate import AuthorityLevel, Gate
from greytheory.checks import ValidatorRegistry
from greytheory.evidence import EvidenceVault
from greytheory.execution import LocalActionExecutor
from greytheory.findings import Taxonomy
from greytheory.lab.two_account import OwnershipValidator, TwoAccountFixture
from greytheory.learning import CardUpdateProposal
from greytheory.provenance import Claim, Tag
from greytheory.report import ReportClaim, ReportDraft
from greytheory.research import (
    ActionRequest,
    AssetKind,
    AssetRelationship,
    EffectBudget,
    ExperimentPlan,
    ExperimentStatus,
    Hypothesis,
    HypothesisStatus,
    Lesson,
    RelationshipKind,
    ResearchIdentity,
    ResearchSession,
    ResearchStore,
    ResearchWorkspace,
    TargetAsset,
)
from greytheory.authority.scope import ScopeClassification
from greytheory.validation import Attestation, GateId, validate


DEFAULT_PROGRAMME = (
    Path(__file__).resolve().parents[1]
    / "fixtures"
    / "lab"
    / "two-account-authorization"
    / "programme.json"
)


class VerticalSliceError(RuntimeError):
    """Raised when any exit condition of the demonstration is not satisfied."""


@dataclass(frozen=True)
class OperatorStatements:
    """Review and attestation text supplied by an operator or labelled fixture."""

    operator: str
    kind: str
    contract_reviewed: bool
    reproducibility: str
    impact: str
    duplicate_risk: str

    def __post_init__(self) -> None:
        if not self.operator.strip():
            raise VerticalSliceError("operator statements require a named actor")
        if self.kind not in {"human", "test_fixture"}:
            raise VerticalSliceError("operator statement kind must be human or test_fixture")
        if not self.contract_reviewed:
            raise VerticalSliceError("the saved contract requires an explicit review confirmation")
        for label in ("reproducibility", "impact", "duplicate_risk"):
            if len(getattr(self, label).strip()) < 20:
                raise VerticalSliceError(f"{label} attestation is too short")

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> OperatorStatements:
        return cls(
            operator=str(data.get("operator", "")),
            kind=str(data.get("kind", "")),
            contract_reviewed=data.get("contract_reviewed") is True,
            reproducibility=str(data.get("reproducibility", "")),
            impact=str(data.get("impact", "")),
            duplicate_risk=str(data.get("duplicate_risk", "")),
        )


# Compatibility name for the Milestone 4 public surface.  The contract now
# lives in the learning system, where proposals can be validated against card
# revision provenance but cannot mutate the catalogue.
VulnerabilityCardUpdate = CardUpdateProposal


@dataclass(frozen=True)
class VerticalSliceResult:
    status: str
    operating_posture: str
    workspace_id: str
    session_id: str
    hypothesis_id: str
    experiment_id: str
    action_request_id: str
    gate_decision_ref: str
    action_receipt_id: str
    observation_id: str
    check_receipt_id: str
    finding_id: str
    finding_state: str
    report_path: str
    postmortem_id: str
    vulnerability_card_update_id: str
    executed_actions: int
    persisted_action_receipts: int
    evidence_refs: tuple[str, ...]
    attestation_kind: str
    submission_performed: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            key: list(value) if isinstance(value, tuple) else value
            for key, value in self.__dict__.items()
        }


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = value.to_dict() if hasattr(value, "to_dict") else value
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _redacted_response(raw: bytes) -> bytes:
    value = json.loads(raw)
    if value.get("object"):
        value["object"]["content"] = "[REDACTED SYNTHETIC CONTENT]"
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def _redacted_manifest(raw: bytes) -> bytes:
    value = json.loads(raw)
    value["controlled_identities"] = ["controlled-account-A", "controlled-account-B"]
    value["objects"] = {
        "object-user-a": "controlled-account-A",
        "object-user-b": "controlled-account-B",
    }
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def run_local_two_account_slice(
    root: str | Path,
    *,
    statements: OperatorStatements,
    programme_path: str | Path = DEFAULT_PROGRAMME,
    clock: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
    vulnerable: bool = True,
) -> VerticalSliceResult:
    """Run the complete local fixture once and persist reviewable artifacts."""
    operator = statements.operator
    run_root = Path(root).expanduser().resolve()
    result_path = run_root / "result.json"
    if result_path.exists():
        raise VerticalSliceError("the run root already contains a completed result")
    run_root.mkdir(parents=True, exist_ok=True)
    now = clock()

    source_path = Path(programme_path)
    raw_rules = source_path.read_text(encoding="utf-8")
    compiled = compile_contract(json.loads(raw_rules), raw_source=raw_rules, now=now)
    if compiled.blocked:
        raise VerticalSliceError("saved local training rules did not compile cleanly")
    contract = mark_reviewed(compiled.contract, reviewer=operator)
    _write_json(run_root / "contract.json", contract)

    audit = AuditLog(run_root / "audit.jsonl", clock=clock)
    research = ResearchStore(run_root / "research", audit=audit, clock=clock)
    vault = EvidenceVault(run_root / "evidence", audit=audit, clock=clock)
    authority_ref = contract.fingerprint()
    workspace_id = "workspace-local-two-account"
    session_id = "session-cross-owner-read"
    hypothesis_id = "hypothesis-cross-owner-read"
    experiment_id = "experiment-cross-owner-read"
    finding_id = "finding-local-cross-owner-read"

    workspace = ResearchWorkspace(
        id=workspace_id,
        programme_id=contract.programme_id,
        contract_id=contract.id,
        authority_ref=authority_ref,
        title="Local two-account object-ownership research",
        operating_posture=AuthorityLevel.LOCAL_FIXTURE,
        request_budget=1,
        time_budget_minutes=45,
        effect_budget=EffectBudget.from_mapping({"reads": 1, "mutations": 0}),
        goals=("Test one controlled object-ownership boundary",),
        unresolved_questions=("Would the safe implementation reject the same read?",),
        created_at=now,
    )
    research.create_workspace(workspace, contract=contract, actor=operator)

    asset_specs = (
        ("asset-app", AssetKind.LOCAL_FIXTURE, "fixture://two-account", "Two-account fixture", None),
        ("asset-account-a", AssetKind.ACCOUNT, "fixture://two-account/accounts/identity-user-a", "Controlled account A", "asset-app"),
        ("asset-account-b", AssetKind.ACCOUNT, "fixture://two-account/accounts/identity-user-b", "Controlled account B", "asset-app"),
        ("asset-object-a", AssetKind.RESOURCE_CLASS, "fixture://two-account/objects/object-user-a", "Synthetic object A", "asset-app"),
        ("asset-object-b", AssetKind.RESOURCE_CLASS, "fixture://two-account/objects/object-user-b", "Synthetic object B", "asset-app"),
    )
    assets: dict[str, TargetAsset] = {}
    for asset_id, kind, identifier, name, parent in asset_specs:
        asset = TargetAsset(
            id=asset_id,
            workspace_id=workspace_id,
            authority_ref=authority_ref,
            kind=kind,
            canonical_identifier=identifier,
            scope_classification=ScopeClassification.IN_SCOPE,
            display_name=name,
            discovered_from_id=parent,
            classification_evidence_ref=f"contract:{authority_ref}",
        )
        research.add_asset(asset, contract=contract, actor=operator)
        assets[asset_id] = asset

    for relation_id, owner, owned in (
        ("relationship-account-a-owns-object-a", "asset-account-a", "asset-object-a"),
        ("relationship-account-b-owns-object-b", "asset-account-b", "asset-object-b"),
    ):
        research.add_relationship(
            AssetRelationship(
                id=relation_id,
                workspace_id=workspace_id,
                authority_ref=authority_ref,
                source_asset_id=owner,
                kind=RelationshipKind.OWNS,
                target_asset_id=owned,
                basis="The saved local fixture ownership manifest defines this relationship",
                evidence_refs=("fixture-ownership-manifest",),
            ),
            actor=operator,
        )

    for suffix, object_id in (("a", "asset-object-a"), ("b", "asset-object-b")):
        research.add_identity(
            ResearchIdentity(
                id=f"identity-user-{suffix}",
                workspace_id=workspace_id,
                programme_id=contract.programme_id,
                authority_ref=authority_ref,
                role=f"controlled user {suffix.upper()}",
                ownership_attestation_ref=f"attestation:operator-controls-user-{suffix}",
                credential_ref=f"credential:in-memory-user-{suffix}",
                permitted_uses=("read synthetic objects in the local fixture",),
                created_at=now,
                expires_at=now + timedelta(hours=1),
                required_researcher_marker=f"greytheory-local-user-{suffix}",
                synthetic_object_ids=(object_id,),
            ),
            actor=operator,
        )

    research.add_session(
        ResearchSession(
            id=session_id,
            workspace_id=workspace_id,
            authority_ref=authority_ref,
            goal="Determine whether controlled user A can read controlled user B's object",
            operating_posture=AuthorityLevel.LOCAL_FIXTURE,
            identity_ids=("identity-user-a", "identity-user-b"),
            request_budget=1,
            time_budget_minutes=30,
            effect_budget=EffectBudget.from_mapping({"reads": 1, "mutations": 0}),
            created_at=now,
        ),
        actor=operator,
    )
    hypothesis = Hypothesis(
        id=hypothesis_id,
        workspace_id=workspace_id,
        session_id=session_id,
        authority_ref=authority_ref,
        title="Object ownership may not be checked on the local read path",
        preconditions=("Both identities and objects are controlled and synthetic",),
        actor_identity_id="identity-user-a",
        action="Read controlled object B once as controlled user A",
        target_asset_id="asset-object-b",
        consequence="One controlled identity receives another identity's synthetic content",
        reasoning="The deliberately vulnerable route returns by identifier without comparing ownership",
        supporting_observation_refs=(),
        assumptions=("The ownership manifest is the authoritative local oracle",),
        required_authority=AuthorityLevel.LOCAL_FIXTURE,
        expected_safe_behaviour="The fixture returns a 403 owner-mismatch response",
        expected_vulnerable_behaviour="The fixture returns object B to user A with HTTP 200",
        falsifier="The same controlled cross-owner request returns 403 or no object body",
        evidence_needs=("Gate-bound action receipt", "Response bytes", "Ownership manifest", "Check receipt"),
        stop_conditions=("unexpected-target", "scope-change", "request-budget-reached"),
        estimated_request_cost=1,
        estimated_time_minutes=20,
        estimated_effects=EffectBudget.from_mapping({"reads": 1}),
        duplicate_risk="Not applicable beyond the isolated training demonstration",
        learning_value="Proves the complete object-ownership research chain",
    )
    research.add_hypothesis(hypothesis, actor=operator)
    research.transition_hypothesis(workspace_id, hypothesis_id, HypothesisStatus.SCOPED, actor=operator)
    research.transition_hypothesis(workspace_id, hypothesis_id, HypothesisStatus.PLANNED, actor=operator)
    experiment = ExperimentPlan(
        id=experiment_id,
        workspace_id=workspace_id,
        session_id=session_id,
        hypothesis_id=hypothesis_id,
        authority_ref=authority_ref,
        ordered_actions=("Read controlled object B exactly once as controlled user A",),
        positive_controls=("The ownership manifest maps object B to user B",),
        negative_controls=("A safe fixture returns 403 for the cross-owner read",),
        expected_outcomes=("supported", "refuted", "invalid_input"),
        required_authority=AuthorityLevel.LOCAL_FIXTURE,
        effect_budget=EffectBudget.from_mapping({"reads": 1}),
        rollback_steps=("Delete the disposable run directory",),
        stop_conditions=("unexpected-target", "scope-change", "request-budget-reached"),
        evidence_plan=("Hash response and ownership manifest bytes before validation",),
    )
    research.add_experiment(experiment, actor=operator)
    research.transition_experiment(workspace_id, experiment_id, ExperimentStatus.READY, actor=operator)
    research.start_session(workspace_id, session_id, actor=operator)
    research.transition_experiment(workspace_id, experiment_id, ExperimentStatus.ACTIVE, actor=operator)
    research.transition_hypothesis(workspace_id, hypothesis_id, HypothesisStatus.TESTING, actor=operator)
    request = ActionRequest(
        id="request-cross-owner-read",
        workspace_id=workspace_id,
        session_id=session_id,
        experiment_id=experiment_id,
        authority_ref=authority_ref,
        action_type="read_object",
        exact_action="Read fixture object B exactly once as controlled user A",
        target_asset_id="asset-object-b",
        identity_id="identity-user-a",
        required_authority=AuthorityLevel.LOCAL_FIXTURE,
        purpose="Test the stated local object-ownership hypothesis",
        technique="object-ownership-check",
        max_requests=1,
        expected_effects=EffectBudget.from_mapping({"reads": 1}),
        stop_conditions=("unexpected-target", "scope-change", "request-budget-reached"),
        created_at=now,
    )
    research.add_action_request(request, actor=operator)

    fixture = TwoAccountFixture(vulnerable=vulnerable)
    executor = LocalActionExecutor(
        research=research,
        gate=Gate(audit, posture_ceiling=AuthorityLevel.LOCAL_FIXTURE, clock=clock),
        contract=contract,
        fixture=fixture,
        clock=clock,
    )
    attempt = executor.execute(workspace_id, request.id)
    if not attempt.decision.allowed or not attempt.receipt or not attempt.response or not attempt.observation:
        raise VerticalSliceError(f"local action was denied: {attempt.decision.reason.value}")

    response_bytes = attempt.response.body
    manifest_bytes = fixture.ownership_manifest()
    response_artifact = vault.store_raw(
        finding_id=finding_id,
        artifact_id="response-cross-owner-read",
        kind="local_request_response",
        data=response_bytes,
        authority_ref=authority_ref,
        extension=".json",
        source_account="identity-user-a",
        notes="Synthetic controlled response from the in-memory fixture",
    )
    vault.attach_redacted(
        finding_id=finding_id,
        artifact_id=response_artifact.id,
        data=_redacted_response(response_bytes),
    )
    manifest_artifact = vault.store_raw(
        finding_id=finding_id,
        artifact_id="fixture-ownership-manifest",
        kind="ownership_manifest",
        data=manifest_bytes,
        authority_ref=authority_ref,
        extension=".json",
        notes="Controlled identity-to-object ownership oracle",
    )
    vault.attach_redacted(
        finding_id=finding_id,
        artifact_id=manifest_artifact.id,
        data=_redacted_manifest(manifest_bytes),
    )

    validators = ValidatorRegistry(clock=clock)
    validators.register(OwnershipValidator())
    check_receipt = validators.run(
        OwnershipValidator.validator_id,
        inputs=(response_bytes, manifest_bytes),
        authority_ref=authority_ref,
    )
    inferred = Claim(check_receipt.exact_assertion, Tag.INFERRED, "hypothesis:cross-owner-read")
    checked = validators.promote(inferred, check_receipt)
    if check_receipt.input_artifact_hashes != (
        response_artifact.raw_sha256,
        manifest_artifact.raw_sha256,
    ):
        raise VerticalSliceError("validator inputs do not match stored evidence hashes")

    check_bytes = (json.dumps(check_receipt.to_dict(), sort_keys=True) + "\n").encode()
    check_artifact = vault.store_raw(
        finding_id=finding_id,
        artifact_id="deterministic-check-receipt",
        kind="check_receipt",
        data=check_bytes,
        authority_ref=authority_ref,
        extension=".json",
        notes="Registry-issued receipt for the ownership validator",
    )
    check_redacted = {**check_receipt.to_dict(), "runner_digest": "[REDACTED FROM EXPORT]"}
    vault.attach_redacted(
        finding_id=finding_id,
        artifact_id=check_artifact.id,
        data=(json.dumps(check_redacted, sort_keys=True) + "\n").encode(),
    )

    finding = attempt.observation.to_finding(finding_id)
    finding.claims.extend(
        [
            checked,
            Claim(
                "The demonstrated consequence is limited to confidentiality between two controlled synthetic accounts.",
                Tag.INFERRED,
                f"operator:{operator}",
            ),
        ]
    )
    finding.evidence_refs.extend(
        [response_artifact.id, manifest_artifact.id, check_artifact.id]
    )
    finding.advance(Taxonomy.CANDIDATE, actor=operator, now=now)
    finding.advance(Taxonomy.VALIDATED, actor=operator, now=now)

    report_claims = [
        ReportClaim(
            claim=attempt.observation.claims[0],
            evidence_refs=(response_artifact.id,),
        ),
        ReportClaim(
            claim=checked,
            evidence_refs=(response_artifact.id, manifest_artifact.id, check_artifact.id),
        ),
        ReportClaim(
            claim=finding.claims[-1],
            evidence_refs=(response_artifact.id, manifest_artifact.id),
        ),
    ]
    draft = ReportDraft(
        finding_id=finding_id,
        authority_ref=authority_ref,
        title="Local two-account fixture permits a controlled cross-owner object read",
        programme="GreyTheory local two-account authorization training fixture",
        asset=assets["asset-object-b"].canonical_identifier,
        summary="Controlled user A can read controlled user B's synthetic object through the deliberately vulnerable local route.",
        affected_feature="In-memory object read",
        preconditions=("Two operator-controlled identities and synthetic objects",),
        steps=(
            "Compile and human-review the saved LOCAL_FIXTURE training rules.",
            "Create controlled users A and B and map one synthetic object to each.",
            "Allow one user-A read of object B through the GreyTheory gate.",
            "Re-derive ownership from the stored response and manifest bytes.",
        ),
        expected_result="A safe implementation returns 403 because user A does not own object B.",
        actual_result="The deliberately vulnerable fixture returns object B with HTTP 200.",
        security_impact="The local demonstration shows a bounded confidentiality failure between controlled synthetic accounts.",
        evidence_index=[response_artifact.id, manifest_artifact.id, check_artifact.id],
        claim_matrix=report_claims,
        data_minimisation_statement="All identities, objects, and content are synthetic and held only in the local run directory.",
        severity_proposed="Training finding only",
        severity_framework="GreyTheory local fixture classification",
        severity_rationale="No real target or third-party data exists; the artifact demonstrates the research chain, not live severity.",
        remediation="Compare the authenticated identity to the stored object owner before returning the object.",
        unresolved_uncertainty=["No claim is made about any real application or programme."],
        tested_at=now.isoformat(),
        researcher_accounts=["identity-user-a", "identity-user-b"],
    )
    attestations = [
        Attestation(
            GateId.B_REPRODUCIBILITY,
            operator,
            statements.reproducibility,
            now,
            [response_artifact.id, check_artifact.id],
        ),
        Attestation(
            GateId.C_IMPACT,
            operator,
            statements.impact,
            now,
            [response_artifact.id, manifest_artifact.id],
        ),
        Attestation(
            GateId.E_DUPLICATE_RISK,
            operator,
            statements.duplicate_risk,
            now,
            [manifest_artifact.id],
        ),
    ]
    validation = validate(
        finding,
        vault=vault,
        draft=draft,
        attestations=attestations,
        audit=audit,
        now=now,
    )
    if not validation.submission_ready:
        reasons = [reason for item in validation.blocking for reason in item.reasons]
        raise VerticalSliceError("validation did not pass: " + "; ".join(reasons))
    finding.advance(Taxonomy.REPORT_READY, actor=operator, note="Gates B-F passed", now=now)

    research.transition_experiment(
        workspace_id,
        experiment_id,
        ExperimentStatus.COMPLETED,
        actor=operator,
        outcome_summary="The controlled cross-owner read was supported by a deterministic check",
        result_refs=(attempt.receipt.id, check_receipt.id, finding_id),
    )
    research.transition_hypothesis(
        workspace_id,
        hypothesis_id,
        HypothesisStatus.SUPPORTED,
        actor=operator,
        result_summary=checked.text,
        result_refs=(attempt.observation.id, check_receipt.id),
    )
    research.transition_hypothesis(
        workspace_id,
        hypothesis_id,
        HypothesisStatus.CONVERTED_TO_FINDING,
        actor=operator,
        finding_ref=finding_id,
    )
    card_update = CardUpdateProposal(
        id="card-update-local-bola-v1",
        card_id="idor-bola",
        status="proposed",
        change="Add the two-account ownership oracle, safe 403 control, and receipt-backed evidence pattern.",
        checked_claim_ref=check_receipt.id,
        evidence_refs=(response_artifact.id, manifest_artifact.id, check_artifact.id),
        source_kind="test_fixture",
    )
    lesson = Lesson(
        id="postmortem-local-two-account",
        workspace_id=workspace_id,
        session_id=session_id,
        hypothesis_id=hypothesis_id,
        authority_ref=authority_ref,
        summary="A gate-bound local action can become a report-ready finding without laundering model output into proof.",
        what_was_tested=("One cross-owner read between two controlled synthetic identities",),
        prioritisation_reason="It is the smallest complete authorization research slice",
        observation_refs=(attempt.observation.id, attempt.receipt.id, check_receipt.id),
        disproved=("The research-domain records alone constituted an end-to-end execution proof",),
        incorrect_assumptions=("A caller-supplied could-have-failed Boolean was a sufficient provenance control",),
        result_change_conditions=("The safe fixture returns 403", "The ownership manifest does not support the returned object"),
        target_score_change="Mark the local authorization chain demonstrated; do not change any real-target score.",
        vulnerability_card_updates=(f"proposal:{card_update.id}",),
        next_actions=("Build the Milestone 5 vulnerability-card system before applying this proposal as canonical knowledge",),
        created_at=now,
    )
    research.add_lesson(lesson, actor=operator)
    completed = research.complete_session(
        workspace_id,
        session_id,
        actor=operator,
        time_spent_minutes=20,
        outcome_summary="A report-ready local finding, postmortem, and proposed card update were produced.",
        checked_evidence_refs=(response_artifact.id, manifest_artifact.id, check_artifact.id),
    )

    research.verify(workspace_id)
    evidence_problems = vault.verify(finding_id)
    if evidence_problems:
        raise VerticalSliceError("evidence verification failed: " + "; ".join(evidence_problems))
    snapshot = research.snapshot(workspace_id)
    if fixture.action_count != 1 or len(snapshot.action_receipts) != fixture.action_count:
        raise VerticalSliceError("executed actions do not map one-to-one to action receipts")
    if not completed.checked_evidence_refs and not snapshot.lessons:
        raise VerticalSliceError("session produced neither checked evidence nor a lesson")

    report_path = run_root / "report.md"
    report_path.write_text(draft.render(), encoding="utf-8")
    _write_json(run_root / "report.json", draft)
    _write_json(run_root / "finding.json", finding)
    _write_json(run_root / "validation.json", validation)
    _write_json(run_root / "postmortem.json", lesson)
    _write_json(run_root / "vulnerability-card-update.json", card_update)
    result = VerticalSliceResult(
        status="complete",
        operating_posture=AuthorityLevel.LOCAL_FIXTURE.name,
        workspace_id=workspace_id,
        session_id=session_id,
        hypothesis_id=hypothesis_id,
        experiment_id=experiment_id,
        action_request_id=request.id,
        gate_decision_ref=attempt.receipt.gate_decision_ref,
        action_receipt_id=attempt.receipt.id,
        observation_id=attempt.observation.id,
        check_receipt_id=check_receipt.id,
        finding_id=finding_id,
        finding_state=finding.state.value,
        report_path=str(report_path),
        postmortem_id=lesson.id,
        vulnerability_card_update_id=card_update.id,
        executed_actions=fixture.action_count,
        persisted_action_receipts=len(snapshot.action_receipts),
        evidence_refs=tuple(finding.evidence_refs),
        attestation_kind=statements.kind,
    )
    _write_json(result_path, result)
    return result


__all__ = [
    "DEFAULT_PROGRAMME",
    "OperatorStatements",
    "VerticalSliceError",
    "VerticalSliceResult",
    "VulnerabilityCardUpdate",
    "run_local_two_account_slice",
]
