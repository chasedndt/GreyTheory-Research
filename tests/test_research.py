from __future__ import annotations

import json
import re
from dataclasses import replace
from datetime import datetime, timedelta, timezone

import pytest

from greytheory.audit import AuditLog
from greytheory.authority.gate import AuthorityLevel, Decision, Gate, Reason
from greytheory.authority.scope import (
    AssetPattern,
    ContractStatus,
    PatternType,
    ScopeClassification,
    ScopeContract,
)
from greytheory.research import (
    ActionReceipt,
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
    ResearchDomainError,
    ResearchIdentity,
    ResearchSession,
    ResearchStore,
    ResearchStoreError,
    ResearchWorkspace,
    SessionStatus,
    TargetAsset,
    WorkspaceStatus,
    metadata_items,
)

NOW = datetime(2026, 8, 9, 12, 0, tzinfo=timezone.utc)


def contract(
    *,
    status: ContractStatus = ContractStatus.VERIFIED,
    reviewed: bool = True,
) -> ScopeContract:
    return ScopeContract(
        id="contract-local-two-account",
        programme_id="programme-local-training",
        verified_at=NOW,
        status=status,
        assets_in_scope=[
            AssetPattern(PatternType.EXACT, "fixture://two-account-app"),
            AssetPattern(PatternType.EXACT, "fixture://objects/user-b"),
        ],
        max_authority="LOCAL_FIXTURE",
        human_reviewed=reviewed,
        source_hashes=["a" * 64],
    )


def workspace(bound: ScopeContract) -> ResearchWorkspace:
    return ResearchWorkspace(
        id="workspace-local-authz",
        programme_id=bound.programme_id,
        contract_id=bound.id,
        authority_ref=bound.fingerprint(),
        title="Local two-account authorisation research",
        operating_posture=AuthorityLevel.LOCAL_FIXTURE,
        request_budget=4,
        time_budget_minutes=90,
        effect_budget=EffectBudget.from_mapping({"reads": 4, "mutations": 0}),
        goals=("Test one controlled object-ownership boundary",),
        unresolved_questions=("Does the fixture enforce ownership server-side?",),
        created_at=NOW,
    )


def store_with_workspace(tmp_path):
    audit = AuditLog(tmp_path / "audit.jsonl", clock=lambda: NOW)
    research = ResearchStore(tmp_path / "research", audit=audit, clock=lambda: NOW)
    bound = contract()
    research.create_workspace(workspace(bound), contract=bound, actor="researcher")
    return research, audit, bound


def assets(research: ResearchStore, bound: ScopeContract):
    authority_ref = bound.fingerprint()
    app = TargetAsset(
        id="asset-app",
        workspace_id="workspace-local-authz",
        authority_ref=authority_ref,
        kind=AssetKind.LOCAL_FIXTURE,
        canonical_identifier="fixture://two-account-app",
        scope_classification=ScopeClassification.IN_SCOPE,
        display_name="Two-account training application",
        classification_evidence_ref=f"contract:{authority_ref}",
    )
    object_b = TargetAsset(
        id="asset-object-b",
        workspace_id="workspace-local-authz",
        authority_ref=authority_ref,
        kind=AssetKind.RESOURCE_CLASS,
        canonical_identifier="fixture://objects/user-b",
        scope_classification=ScopeClassification.IN_SCOPE,
        display_name="Controlled object owned by user B",
        discovered_from_id=app.id,
        classification_evidence_ref=f"contract:{authority_ref}",
    )
    research.add_asset(app, contract=bound, actor="researcher")
    research.add_asset(object_b, contract=bound, actor="researcher")
    return app, object_b


def identity(bound: ScopeContract) -> ResearchIdentity:
    return ResearchIdentity(
        id="identity-user-a",
        workspace_id="workspace-local-authz",
        programme_id=bound.programme_id,
        authority_ref=bound.fingerprint(),
        role="controlled user A",
        ownership_attestation_ref="attestation:user-a-owned",
        credential_ref="credential:user-a-local",
        permitted_uses=("read synthetic objects in the local fixture",),
        created_at=NOW,
        expires_at=NOW + timedelta(hours=2),
        required_researcher_marker="researcher+greytheory@example.invalid",
        synthetic_object_ids=("asset-object-a",),
    )


def session(bound: ScopeContract) -> ResearchSession:
    return ResearchSession(
        id="session-object-ownership",
        workspace_id="workspace-local-authz",
        authority_ref=bound.fingerprint(),
        goal="Determine whether user A can read user B's controlled object",
        operating_posture=AuthorityLevel.LOCAL_FIXTURE,
        identity_ids=("identity-user-a",),
        request_budget=2,
        time_budget_minutes=45,
        effect_budget=EffectBudget.from_mapping({"reads": 2, "mutations": 0}),
        created_at=NOW,
    )


def hypothesis(bound: ScopeContract) -> Hypothesis:
    return Hypothesis(
        id="hypothesis-object-ownership",
        workspace_id="workspace-local-authz",
        session_id="session-object-ownership",
        authority_ref=bound.fingerprint(),
        title="Object ownership may not be checked server-side",
        preconditions=("Both test identities and objects are researcher-controlled",),
        actor_identity_id="identity-user-a",
        action="Request the controlled object belonging to user B as user A",
        target_asset_id="asset-object-b",
        consequence="One controlled identity reads another identity's object",
        reasoning="The object identifier may be trusted without an ownership lookup",
        supporting_observation_refs=(),
        assumptions=("The fixture maps each object to one owner",),
        required_authority=AuthorityLevel.LOCAL_FIXTURE,
        expected_safe_behaviour="The fixture rejects the cross-owner read",
        expected_vulnerable_behaviour="The fixture returns user B's synthetic object",
        falsifier="Every controlled cross-owner request is rejected after ownership lookup",
        evidence_needs=("Gate receipt", "Deterministic response observation"),
        stop_conditions=("redirect-observed", "scope-change"),
        estimated_request_cost=1,
        estimated_time_minutes=20,
        estimated_effects=EffectBudget.from_mapping({"reads": 1}),
        duplicate_risk="Low in the isolated training fixture",
        learning_value="Reusable object-ownership experiment pattern",
    )


def experiment(bound: ScopeContract) -> ExperimentPlan:
    return ExperimentPlan(
        id="experiment-object-ownership",
        workspace_id="workspace-local-authz",
        session_id="session-object-ownership",
        hypothesis_id="hypothesis-object-ownership",
        authority_ref=bound.fingerprint(),
        ordered_actions=("Read user B's synthetic object once as user A",),
        positive_controls=("User B can read user B's synthetic object",),
        negative_controls=("User A cannot read user B's synthetic object",),
        expected_outcomes=("A deterministic allow or deny response is recorded",),
        required_authority=AuthorityLevel.LOCAL_FIXTURE,
        effect_budget=EffectBudget.from_mapping({"reads": 1}),
        rollback_steps=("Delete the disposable local fixture data",),
        stop_conditions=("redirect-observed", "scope-change"),
        evidence_plan=("Hash the structured local response",),
    )


def action_request(bound: ScopeContract) -> ActionRequest:
    return ActionRequest(
        id="request-cross-owner-read",
        workspace_id="workspace-local-authz",
        session_id="session-object-ownership",
        experiment_id="experiment-object-ownership",
        authority_ref=bound.fingerprint(),
        action_type="read_object",
        exact_action="Read fixture object user-b exactly once as controlled user A",
        target_asset_id="asset-object-b",
        identity_id="identity-user-a",
        required_authority=AuthorityLevel.LOCAL_FIXTURE,
        purpose="Test the stated object-ownership hypothesis",
        technique="object-ownership-check",
        max_requests=1,
        expected_effects=EffectBudget.from_mapping({"reads": 1}),
        stop_conditions=("redirect-observed", "scope-change"),
        created_at=NOW,
    )


def prepare_active_experiment(research: ResearchStore, bound: ScopeContract):
    app, object_b = assets(research, bound)
    research.add_relationship(
        AssetRelationship(
            id="relationship-app-contains-object",
            workspace_id="workspace-local-authz",
            authority_ref=bound.fingerprint(),
            source_asset_id=app.id,
            kind=RelationshipKind.CONTAINS,
            target_asset_id=object_b.id,
            basis="The local fixture manifest defines this controlled object",
            evidence_refs=("fixture-manifest:object-b",),
        ),
        actor="researcher",
    )
    research.add_identity(identity(bound), actor="researcher")
    research.add_session(session(bound), actor="researcher")
    research.add_hypothesis(hypothesis(bound), actor="researcher")
    research.transition_hypothesis(
        "workspace-local-authz",
        "hypothesis-object-ownership",
        HypothesisStatus.SCOPED,
        actor="researcher",
    )
    research.transition_hypothesis(
        "workspace-local-authz",
        "hypothesis-object-ownership",
        HypothesisStatus.PLANNED,
        actor="researcher",
    )
    research.add_experiment(experiment(bound), actor="researcher")
    research.transition_experiment(
        "workspace-local-authz",
        "experiment-object-ownership",
        ExperimentStatus.READY,
        actor="researcher",
    )
    research.start_session(
        "workspace-local-authz", "session-object-ownership", actor="researcher"
    )
    research.transition_experiment(
        "workspace-local-authz",
        "experiment-object-ownership",
        ExperimentStatus.ACTIVE,
        actor="researcher",
    )
    research.transition_hypothesis(
        "workspace-local-authz",
        "hypothesis-object-ownership",
        HypothesisStatus.TESTING,
        actor="researcher",
    )
    return app, object_b


def test_complete_local_session_uses_all_ten_domain_objects_and_persists(tmp_path):
    research, audit, bound = store_with_workspace(tmp_path)
    _, object_b = prepare_active_experiment(research, bound)
    request = action_request(bound)
    research.add_action_request(request, actor="researcher")

    gate = Gate(
        audit,
        posture_ceiling=AuthorityLevel.LOCAL_FIXTURE,
        clock=lambda: NOW,
    )
    decision = gate.evaluate(
        bound, request.to_access_request(object_b, actor="local-fixture-worker")
    )
    assert decision.allowed
    receipt = ActionReceipt.from_execution(
        id="receipt-cross-owner-read",
        request=request,
        asset=object_b,
        decision=decision,
        worker="local-fixture-worker",
        tool_version="1.0.0",
        started_at=NOW,
        ended_at=NOW,
        request_count=1,
        response_metadata={"status_code": 403, "content_type": "application/json"},
        output_hashes=("b" * 64,),
        effects=EffectBudget.from_mapping({"reads": 1}),
    )
    research.record_action_receipt(receipt, actor="local-fixture-worker")
    research.transition_experiment(
        "workspace-local-authz",
        "experiment-object-ownership",
        ExperimentStatus.COMPLETED,
        actor="researcher",
        outcome_summary="The controlled cross-owner read was rejected",
        result_refs=(receipt.id,),
    )
    research.transition_hypothesis(
        "workspace-local-authz",
        "hypothesis-object-ownership",
        HypothesisStatus.REFUTED,
        actor="researcher",
        result_summary="The fixture consistently enforced ownership for this test",
        result_refs=(receipt.id,),
    )
    lesson = Lesson(
        id="lesson-server-side-ownership",
        workspace_id="workspace-local-authz",
        session_id="session-object-ownership",
        hypothesis_id="hypothesis-object-ownership",
        authority_ref=bound.fingerprint(),
        summary="Keep the ownership validator as the negative-control oracle",
        what_was_tested=("One cross-owner read between controlled identities",),
        prioritisation_reason="It is the smallest safe falsifier for the hypothesis",
        observation_refs=(receipt.id,),
        disproved=("The fixture trusts the submitted object identifier",),
        incorrect_assumptions=("The ownership lookup might be absent",),
        result_change_conditions=("A different route bypasses the ownership lookup",),
        target_score_change="No score increase from this refuted path",
        vulnerability_card_updates=("Record the 403 response as a negative control",),
        next_actions=("Test a distinct local route in a later structured session",),
        created_at=NOW,
    )
    research.add_lesson(lesson, actor="researcher")
    research.transition_hypothesis(
        "workspace-local-authz",
        "hypothesis-object-ownership",
        HypothesisStatus.CONVERTED_TO_LESSON,
        actor="researcher",
        lesson_ref=lesson.id,
    )
    completed = research.complete_session(
        "workspace-local-authz",
        "session-object-ownership",
        actor="researcher",
        time_spent_minutes=25,
        outcome_summary="The hypothesis was refuted and captured as a reusable lesson",
    )

    assert completed.status is SessionStatus.COMPLETED
    research.verify("workspace-local-authz")
    reopened = ResearchStore(
        tmp_path / "research", audit=audit, clock=lambda: NOW
    ).snapshot("workspace-local-authz")
    assert len(reopened.assets) == 2
    assert len(reopened.relationships) == 1
    assert len(reopened.identities) == 1
    assert len(reopened.sessions) == 1
    assert len(reopened.hypotheses) == 1
    assert len(reopened.experiments) == 1
    assert len(reopened.action_requests) == 1
    assert len(reopened.action_receipts) == 1
    assert len(reopened.lessons) == 1
    assert reopened.sessions[completed.id] == completed
    assert reopened.hypotheses["hypothesis-object-ownership"].status is HypothesisStatus.CONVERTED_TO_LESSON
    assert audit.is_valid()


def test_workspace_requires_current_verified_human_reviewed_contract(tmp_path):
    research = ResearchStore(tmp_path / "research", clock=lambda: NOW)
    pending = contract(status=ContractStatus.PENDING_REVIEW, reviewed=False)
    with pytest.raises(ResearchStoreError, match="human-reviewed, verified"):
        research.create_workspace(workspace(pending), contract=pending, actor="researcher")

    stale = contract()
    stale.verified_at = NOW - timedelta(days=8)
    with pytest.raises(ResearchStoreError, match="stale"):
        research.create_workspace(workspace(stale), contract=stale, actor="researcher")


def test_asset_scope_is_recomputed_and_relationships_never_widen_it(tmp_path):
    research, _, bound = store_with_workspace(tmp_path)
    app, _ = assets(research, bound)
    unresolved = TargetAsset(
        id="asset-discovered-host",
        workspace_id="workspace-local-authz",
        authority_ref=bound.fingerprint(),
        kind=AssetKind.DOMAIN,
        canonical_identifier="discovered.example.invalid",
        scope_classification=ScopeClassification.IN_SCOPE,
        display_name="Discovered host",
        discovered_from_id=app.id,
        classification_evidence_ref=f"contract:{bound.fingerprint()}",
    )
    with pytest.raises(ResearchStoreError, match="does not match"):
        research.add_asset(unresolved, contract=bound, actor="researcher")

    correctly_unresolved = TargetAsset.from_dict(
        {
            **unresolved.to_dict(),
            "scope_classification": ScopeClassification.UNRESOLVED.value,
        }
    )
    research.add_asset(correctly_unresolved, contract=bound, actor="researcher")
    research.add_relationship(
        AssetRelationship(
            id="relationship-discovery",
            workspace_id="workspace-local-authz",
            authority_ref=bound.fingerprint(),
            source_asset_id=app.id,
            kind=RelationshipKind.CALLS,
            target_asset_id=correctly_unresolved.id,
            basis="A saved fixture manifest mentions the host",
        ),
        actor="researcher",
    )
    assert research.snapshot("workspace-local-authz").assets[
        correctly_unresolved.id
    ].scope_classification is ScopeClassification.UNRESOLVED


def test_identity_and_receipt_metadata_do_not_accept_secret_values(tmp_path):
    bound = contract()
    with pytest.raises(ResearchDomainError, match="safe identifier"):
        ResearchIdentity.from_dict(
            {
                **identity(bound).to_dict(),
                "credential_ref": "Bearer actual-secret-value",
            }
        )
    with pytest.raises(ResearchDomainError, match="sensitive response metadata"):
        metadata_items({"authorization": "Bearer secret"})


def test_hypothesis_and_experiment_lifecycles_are_explicit(tmp_path):
    research, _, bound = store_with_workspace(tmp_path)
    assets(research, bound)
    research.add_identity(identity(bound), actor="researcher")
    research.add_session(session(bound), actor="researcher")
    research.add_hypothesis(hypothesis(bound), actor="researcher")
    with pytest.raises(ResearchStoreError, match="not a hypothesis transition"):
        research.transition_hypothesis(
            "workspace-local-authz",
            "hypothesis-object-ownership",
            HypothesisStatus.SUPPORTED,
            actor="researcher",
        )
    assert not hasattr(experiment(bound), "execute")


def test_action_request_needs_active_session_experiment_and_testing_hypothesis(tmp_path):
    research, _, bound = store_with_workspace(tmp_path)
    assets(research, bound)
    research.add_identity(identity(bound), actor="researcher")
    research.add_session(session(bound), actor="researcher")
    research.add_hypothesis(hypothesis(bound), actor="researcher")
    with pytest.raises(ResearchStoreError, match="no experiment"):
        research.add_action_request(action_request(bound), actor="researcher")


def test_denied_or_unbound_gate_decision_cannot_produce_a_receipt(tmp_path):
    _, object_b = (
        TargetAsset(
            id="asset-app",
            workspace_id="workspace-local-authz",
            authority_ref=contract().fingerprint(),
            kind=AssetKind.LOCAL_FIXTURE,
            canonical_identifier="fixture://two-account-app",
            scope_classification=ScopeClassification.IN_SCOPE,
            display_name="app",
            classification_evidence_ref="contract:local",
        ),
        TargetAsset(
            id="asset-object-b",
            workspace_id="workspace-local-authz",
            authority_ref=contract().fingerprint(),
            kind=AssetKind.RESOURCE_CLASS,
            canonical_identifier="fixture://objects/user-b",
            scope_classification=ScopeClassification.IN_SCOPE,
            display_name="object",
            classification_evidence_ref="contract:local",
        ),
    )
    denied = Decision(False, Reason.ASSET_UNRESOLVED, "no", contract().fingerprint(), 0)
    with pytest.raises(ResearchDomainError, match="denied"):
        ActionReceipt.from_execution(
            id="receipt-denied",
            request=action_request(contract()),
            asset=object_b,
            decision=denied,
            worker="fixture-worker",
            tool_version="1.0",
            started_at=NOW,
            ended_at=NOW,
            request_count=0,
        )


def test_receipts_fail_closed_on_request_and_session_budget_overrun(tmp_path):
    research, audit, bound = store_with_workspace(tmp_path)
    _, object_b = prepare_active_experiment(research, bound)
    request = action_request(bound)
    research.add_action_request(request, actor="researcher")
    decision = Gate(
        audit, posture_ceiling=AuthorityLevel.LOCAL_FIXTURE, clock=lambda: NOW
    ).evaluate(bound, request.to_access_request(object_b, actor="worker"))
    receipt = ActionReceipt.from_execution(
        id="receipt-over-budget",
        request=request,
        asset=object_b,
        decision=decision,
        worker="fixture-worker",
        tool_version="1.0",
        started_at=NOW,
        ended_at=NOW,
        request_count=2,
        effects=EffectBudget.from_mapping({"reads": 1}),
    )
    with pytest.raises(ResearchStoreError, match="does not exist"):
        research.record_action_receipt(
            replace(
                receipt,
                id="receipt-forged-gate-reference",
                gate_decision_ref="audit:999",
                request_count=1,
            ),
            actor="worker",
        )
    with pytest.raises(ResearchStoreError, match="action request count"):
        research.record_action_receipt(receipt, actor="worker")


def test_redirect_receipt_requires_a_recorded_stop_condition(tmp_path):
    research, audit, bound = store_with_workspace(tmp_path)
    _, object_b = prepare_active_experiment(research, bound)
    request = action_request(bound)
    research.add_action_request(request, actor="researcher")
    decision = Gate(
        audit, posture_ceiling=AuthorityLevel.LOCAL_FIXTURE, clock=lambda: NOW
    ).evaluate(bound, request.to_access_request(object_b, actor="worker"))
    receipt = ActionReceipt.from_execution(
        id="receipt-redirect",
        request=request,
        asset=object_b,
        decision=decision,
        worker="fixture-worker",
        tool_version="1.0",
        started_at=NOW,
        ended_at=NOW,
        request_count=1,
        redirects=("fixture://redirect",),
        effects=EffectBudget.from_mapping({"reads": 1}),
    )
    with pytest.raises(ResearchStoreError, match="redirects must fire"):
        research.record_action_receipt(receipt, actor="worker")


def test_empty_session_cannot_disappear_as_completed_work(tmp_path):
    research, _, bound = store_with_workspace(tmp_path)
    research.add_session(
        ResearchSession.from_dict(
            {
                **session(bound).to_dict(),
                "identity_ids": [],
            }
        ),
        actor="researcher",
    )
    research.start_session(
        "workspace-local-authz", "session-object-ownership", actor="researcher"
    )
    with pytest.raises(ResearchStoreError, match="checked evidence"):
        research.complete_session(
            "workspace-local-authz",
            "session-object-ownership",
            actor="researcher",
            time_spent_minutes=5,
            outcome_summary="Nothing happened",
        )


def test_workspace_integrity_failure_is_detected(tmp_path):
    research, _, _ = store_with_workspace(tmp_path)
    path = tmp_path / "research" / "workspace-local-authz" / "workspace.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["workspace"]["title"] = "silently changed"
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ResearchStoreError, match="integrity check"):
        research.snapshot("workspace-local-authz")


def test_research_data_is_refused_inside_a_repository_by_default(tmp_path):
    (tmp_path / ".git").mkdir()
    with pytest.raises(ResearchStoreError, match="git working tree"):
        ResearchStore(tmp_path / "private-research")
    assert ResearchStore(tmp_path / "fixture", allow_in_repository=True)


def test_archived_workspace_is_persisted_and_read_only(tmp_path):
    research, _, bound = store_with_workspace(tmp_path)
    archived = research.archive_workspace("workspace-local-authz", actor="researcher")
    assert archived.status is WorkspaceStatus.ARCHIVED
    assert research.snapshot(archived.id).workspace.status is WorkspaceStatus.ARCHIVED
    with pytest.raises(ResearchStoreError, match="read-only"):
        research.add_asset(
            TargetAsset(
                id="asset-late",
                workspace_id=archived.id,
                authority_ref=bound.fingerprint(),
                kind=AssetKind.LOCAL_FIXTURE,
                canonical_identifier="fixture://two-account-app",
                scope_classification=ScopeClassification.IN_SCOPE,
                display_name="Late asset",
                classification_evidence_ref=f"contract:{bound.fingerprint()}",
            ),
            contract=bound,
            actor="researcher",
        )


def test_research_package_has_no_network_or_process_execution_imports():
    source = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (
            __import__("pathlib").Path(__file__).parents[1] / "greytheory" / "research"
        ).glob("*.py")
    )
    assert not re.search(
        r"^\s*(?:from|import)\s+(?:requests|httpx|urllib|socket|subprocess)\b",
        source,
        re.MULTILINE,
    )
