"""Application-layer contracts for a future local GreyTheory workbench."""

from __future__ import annotations

import ast
import json
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from greytheory.audit import AuditLog
from greytheory.authority.approvals import LocalApprovalStore
from greytheory.authority.gate import AuthorityLevel
from greytheory.authority.scope import (
    AssetPattern,
    ContractStatus,
    PatternType,
    ScopeClassification,
    ScopeContract,
)
from greytheory.evidence import EvidenceVault
from greytheory.findings import Finding
from greytheory.learning import LearningJourneyStore, MasteryStore, load_builtin_catalogue
from greytheory.research import (
    AssetKind,
    EffectBudget,
    ExperimentStatus,
    HypothesisStatus,
    ResearchSession,
    ResearchRevisionConflict,
    ResearchStore,
    ResearchWorkspace,
    TargetAsset,
)
from greytheory.report import ReportDraft
from greytheory.report_store import ReportStore
from greytheory.vertical_slice import OperatorStatements, run_local_two_account_slice
from greytheory_app import (
    CommandDisposition,
    CommandField,
    CommandKind,
    NextAction,
    ReadinessStatus,
    ReportExportWriter,
    WorkbenchApplicationService,
    WorkbenchCommand,
    WorkbenchContractError,
)


NOW = datetime(2026, 8, 9, 15, 0, tzinfo=timezone.utc)


def command(
    command_id: str,
    kind: CommandKind,
    *,
    key: str | None = None,
    fields: tuple[CommandField, ...] = (),
    revision: int | None = None,
    authority: AuthorityLevel = AuthorityLevel.NONE,
    acknowledged: bool = False,
    workspace_id: str | None = None,
    operator_ref: str = "operator-local",
) -> WorkbenchCommand:
    return WorkbenchCommand(
        id=command_id,
        kind=kind,
        operator_ref=operator_ref,
        issued_at=NOW,
        idempotency_key=key or command_id,
        fields=fields,
        expected_revision=revision,
        requested_authority=authority,
        human_acknowledged=acknowledged,
        workspace_id=workspace_id,
    )


def stores(root: Path) -> tuple[MasteryStore, LearningJourneyStore]:
    catalogue = load_builtin_catalogue()
    return (
        MasteryStore(root, catalogue=catalogue),
        LearningJourneyStore(root, catalogue=catalogue),
    )


def fixture_statements() -> OperatorStatements:
    return OperatorStatements(
        operator="fixture-human-reviewer",
        kind="test_fixture",
        contract_reviewed=True,
        reproducibility="I ran this acceptance fixture from a clean private local run directory.",
        impact="I confirmed only the bounded confidentiality consequence between controlled synthetic accounts.",
        duplicate_risk="I reviewed the saved training rules; residual duplicate risk remains fixture-only.",
    )


def research_planning_service(
    root: Path,
) -> tuple[WorkbenchApplicationService, ResearchStore]:
    bound = ScopeContract(
        id="contract-workbench-local",
        programme_id="programme-workbench-local",
        verified_at=NOW,
        status=ContractStatus.VERIFIED,
        assets_in_scope=(
            AssetPattern(PatternType.EXACT, "fixture://cache-normalization"),
        ),
        max_authority="LOCAL_FIXTURE",
        human_reviewed=True,
        source_hashes=("a" * 64,),
    )
    research = ResearchStore(root / "research", clock=lambda: NOW)
    workspace = ResearchWorkspace(
        id="workspace-workbench-local",
        programme_id=bound.programme_id,
        contract_id=bound.id,
        authority_ref=bound.fingerprint(),
        title="Workbench local research",
        operating_posture=AuthorityLevel.LOCAL_FIXTURE,
        request_budget=3,
        time_budget_minutes=45,
        effect_budget=EffectBudget.from_mapping({"reads": 3}),
        goals=("Practise one falsifiable local experiment",),
        created_at=NOW,
    )
    research.create_workspace(workspace, contract=bound, actor="operator-local")
    research.add_asset(
        TargetAsset(
            id="asset-cache-fixture",
            workspace_id=workspace.id,
            authority_ref=bound.fingerprint(),
            kind=AssetKind.LOCAL_FIXTURE,
            canonical_identifier="fixture://cache-normalization",
            scope_classification=ScopeClassification.IN_SCOPE,
            display_name="Cache normalization fixture",
            classification_evidence_ref=f"contract:{bound.fingerprint()}",
        ),
        contract=bound,
        actor="operator-local",
    )
    research.add_session(
        ResearchSession(
            id="session-cache-local",
            workspace_id=workspace.id,
            authority_ref=bound.fingerprint(),
            goal="Test one cache normalization theory locally",
            operating_posture=AuthorityLevel.LOCAL_FIXTURE,
            identity_ids=(),
            request_budget=2,
            time_budget_minutes=30,
            effect_budget=EffectBudget.from_mapping({"reads": 2}),
            created_at=NOW,
        ),
        actor="operator-local",
    )
    return (
        WorkbenchApplicationService(research=research, clock=lambda: NOW),
        research,
    )


def create_hypothesis_fields() -> tuple[CommandField, ...]:
    return (
        CommandField("hypothesis_id", "hypothesis-cache-key"),
        CommandField("session_id", "session-cache-local"),
        CommandField("title", "Equivalent paths may use distinct cache keys"),
        CommandField("preconditions", ("Synthetic cache fixture is reset",)),
        CommandField("action", "Compare two equivalent local paths"),
        CommandField("target_asset_id", "asset-cache-fixture"),
        CommandField("consequence", "Equivalent content may occupy distinct entries"),
        CommandField("reasoning", "The raw path may be included before normalization"),
        CommandField("supporting_observation_refs", ()),
        CommandField("assumptions", ("The fixture exposes deterministic cache metadata",)),
        CommandField("expected_safe_behaviour", "Equivalent paths share one cache key"),
        CommandField(
            "expected_vulnerable_behaviour", "Equivalent paths create distinct entries"
        ),
        CommandField("falsifier", "Every equivalent path resolves to one cache key"),
        CommandField("evidence_needs", ("Fixture receipt", "Cache-key observation")),
        CommandField("stop_conditions", ("fixture-reset-fails",)),
        CommandField("estimated_request_cost", 2),
        CommandField("estimated_time_minutes", 20),
        CommandField("estimated_effects", ("reads=2",)),
        CommandField("duplicate_risk", "Low in the reset synthetic fixture"),
        CommandField("learning_value", "Reusable cache-key experiment method"),
    )


def experiment_fields() -> tuple[CommandField, ...]:
    return (
        CommandField("experiment_id", "experiment-cache-key"),
        CommandField("hypothesis_id", "hypothesis-cache-key"),
        CommandField("ordered_actions", ("Read two equivalent fixture paths",)),
        CommandField("positive_controls", ("Canonical path returns fixture content",)),
        CommandField("negative_controls", ("Unrelated path has a different key",)),
        CommandField("expected_outcomes", ("Two cache-key observations are recorded",)),
        CommandField("effect_budget", ("reads=2",)),
        CommandField("rollback_steps", ("Reset disposable fixture state",)),
        CommandField("stop_conditions", ("fixture-reset-fails",)),
        CommandField("evidence_plan", ("Hash the structured fixture observations",)),
    )


def mastery_fields() -> tuple[CommandField, ...]:
    return (
        CommandField("assessment_id", "assessment-workbench-idor-test"),
        CommandField("card_id", "idor-bola"),
        CommandField("dimension", "test"),
        CommandField("level", "independent"),
        CommandField(
            "evidence_refs", ("lab-report:controlled-two-account-review",)
        ),
        CommandField(
            "rationale",
            "I reviewed the falsifier, both controls, and the saved receipt.",
        ),
        CommandField("review_due", "2026-11-25"),
    )


def report_draft_fields() -> tuple[CommandField, ...]:
    return (
        CommandField("finding_id", "finding-cache-key"),
        CommandField("title", "Cache normalization may split equivalent keys"),
        CommandField("summary", "A draft operator summary."),
        CommandField("affected_feature", "Synthetic cache normalization"),
        CommandField("preconditions", ("The local cache fixture is reset",)),
        CommandField("steps", ("Compare the two planned fixture paths",)),
        CommandField("expected_result", "Equivalent paths share one key."),
        CommandField("actual_result", "Not yet recorded."),
        CommandField("security_impact", "No real-target impact is claimed."),
        CommandField("evidence_index", ()),
        CommandField(
            "data_minimisation_statement", "Only synthetic local data is used."
        ),
        CommandField("severity_proposed", "Training finding only"),
        CommandField("severity_framework", "GreyTheory local fixture"),
        CommandField("severity_rationale", "No live target exists."),
        CommandField("remediation", "Normalize paths before key generation."),
        CommandField(
            "unresolved_uncertainty", ("The experiment has not produced evidence",)
        ),
        CommandField("tested_at", ""),
        CommandField("researcher_accounts", ()),
    )


def test_contract_refuses_live_posture_and_executable_display_actions():
    with pytest.raises(WorkbenchContractError, match="LOCAL_FIXTURE"):
        WorkbenchApplicationService(posture=AuthorityLevel.PASSIVE_HTTP)
    with pytest.raises(WorkbenchContractError, match="never execution authority"):
        NextAction("run", "Run", "Because", "/run", executable=True)
    with pytest.raises(WorkbenchContractError, match="human acknowledgement"):
        command(
            "scope-without-human",
            CommandKind.REVIEW_HYPOTHESIS_SCOPE,
            fields=(CommandField("hypothesis_id", "hypothesis-1"),),
            revision=0,
        )
    with pytest.raises(WorkbenchContractError, match="no execution authority"):
        command(
            "plan-with-authority",
            CommandKind.PLAN_EXPERIMENT,
            fields=(CommandField("hypothesis_id", "hypothesis-1"),),
            revision=0,
            authority=AuthorityLevel.LOCAL_FIXTURE,
        )
    with pytest.raises(WorkbenchContractError, match="non-negative integer"):
        command(
            "boolean-revision",
            CommandKind.PLAN_EXPERIMENT,
            fields=(CommandField("hypothesis_id", "hypothesis-1"),),
            revision=True,
        )
    with pytest.raises(WorkbenchContractError, match="human acknowledgement"):
        command(
            "mastery-without-human",
            CommandKind.RECORD_MASTERY_ASSESSMENT,
            fields=mastery_fields(),
            revision=0,
        )
    with pytest.raises(WorkbenchContractError, match="no execution authority"):
        command(
            "mastery-with-authority",
            CommandKind.RECORD_MASTERY_ASSESSMENT,
            fields=mastery_fields(),
            revision=0,
            authority=AuthorityLevel.LOCAL_FIXTURE,
            acknowledged=True,
        )
    with pytest.raises(WorkbenchContractError, match="no execution authority"):
        command(
            "report-case-with-authority",
            CommandKind.CREATE_REPORT_CASE,
            fields=(),
            revision=0,
            authority=AuthorityLevel.LOCAL_FIXTURE,
            workspace_id="workspace-1",
        )
    with pytest.raises(WorkbenchContractError, match="current revision"):
        command(
            "report-draft-without-revision",
            CommandKind.SAVE_REPORT_DRAFT,
            fields=(),
        )
    with pytest.raises(WorkbenchContractError, match="human acknowledgement"):
        command(
            "validation-without-human",
            CommandKind.RUN_REPORT_VALIDATION,
            fields=(),
            revision=0,
        )
    with pytest.raises(WorkbenchContractError, match="human acknowledgement"):
        command(
            "export-without-human",
            CommandKind.EXPORT_REPORT,
            fields=(
                CommandField("export_id", "export-1"),
                CommandField("finding_id", "finding-1"),
            ),
            revision=0,
        )
    with pytest.raises(WorkbenchContractError, match="no execution authority"):
        command(
            "export-with-authority",
            CommandKind.EXPORT_REPORT,
            fields=(
                CommandField("export_id", "export-1"),
                CommandField("finding_id", "finding-1"),
            ),
            revision=0,
            authority=AuthorityLevel.LOCAL_FIXTURE,
            acknowledged=True,
        )


def test_empty_snapshot_distinguishes_unknown_from_zero():
    snapshot = WorkbenchApplicationService(clock=lambda: NOW).snapshot()

    assert snapshot.schema_version == "greytheory.workbench.v1"
    assert snapshot.posture is AuthorityLevel.LOCAL_FIXTURE
    assert snapshot.live_target_available is False
    assert snapshot.section("research").status is ReadinessStatus.UNKNOWN
    assert snapshot.section("learning").status is ReadinessStatus.UNKNOWN
    assert snapshot.section("overview").status is ReadinessStatus.ATTENTION
    assert snapshot.next_action.id == "configure-research-root"
    assert snapshot.next_action.executable is False
    assert snapshot.to_dict()["live_target_available"] is False


def test_configured_empty_private_stores_have_empty_and_recommended_states(tmp_path):
    mastery, journeys = stores(tmp_path / "learning")
    service = WorkbenchApplicationService(
        research=ResearchStore(tmp_path / "research"),
        mastery=mastery,
        journeys=journeys,
        clock=lambda: NOW,
    )

    snapshot = service.snapshot()

    assert snapshot.section("research").status is ReadinessStatus.EMPTY
    assert snapshot.section("learning").records[0].id.startswith("recommendation:")
    assert snapshot.next_action.id == "create-workspace"


def test_learning_commands_are_idempotent_revision_bound_and_non_crediting(tmp_path):
    mastery, journeys = stores(tmp_path / "learning")
    service = WorkbenchApplicationService(
        research=ResearchStore(tmp_path / "research"),
        mastery=mastery,
        journeys=journeys,
        clock=lambda: NOW,
    )
    start = command(
        "command-start",
        CommandKind.START_LEARNING_JOURNEY,
        fields=(CommandField("journey_id", "journey-1"),),
    )

    first = service.handle(start)
    repeated = service.handle(start)

    assert first.disposition is CommandDisposition.ACCEPTED
    assert first.executed is False
    assert repeated == first
    assert len(journeys.journeys()) == 1
    assert service.snapshot().context.learning_journey_id == "journey-1"

    changed = command(
        "command-changed",
        CommandKind.START_LEARNING_JOURNEY,
        key="command-start",
        fields=(CommandField("journey_id", "journey-2"),),
    )
    assert service.handle(changed).disposition is CommandDisposition.CONFLICT

    stale = command(
        "command-stale",
        CommandKind.ADVANCE_LEARNING_JOURNEY,
        fields=(CommandField("journey_id", "journey-1"),),
        revision=1,
    )
    assert service.handle(stale).code == "revision_conflict"

    advance = command(
        "command-advance",
        CommandKind.ADVANCE_LEARNING_JOURNEY,
        fields=(CommandField("journey_id", "journey-1"),),
        revision=0,
    )
    result = service.handle(advance)
    persisted = journeys.get("journey-1")
    assert result.disposition is CommandDisposition.ACCEPTED
    assert result.executed is False
    assert persisted.revision == 1
    assert persisted.current_stage.value == "practise"
    assert mastery.assessments() == ()


def test_action_intent_contract_cannot_raise_posture():
    fields = (
        CommandField("action_type", "fixture.read"),
        CommandField("exact_action", "read one synthetic object"),
        CommandField("target_asset_id", "asset-1"),
        CommandField("purpose", "prove a bounded local hypothesis"),
        CommandField("max_requests", 1),
    )
    with pytest.raises(WorkbenchContractError, match="LOCAL_FIXTURE"):
        command(
            "action-passive",
            CommandKind.REQUEST_ACTION,
            fields=fields,
            revision=0,
            authority=AuthorityLevel.PASSIVE_HTTP,
            acknowledged=True,
            workspace_id="workspace-1",
        )


def test_action_intent_records_server_bound_fixture_request_without_execution(tmp_path):
    service, research = research_planning_service(tmp_path)
    assert service.handle(
        command(
            "command-create-hypothesis",
            CommandKind.CREATE_HYPOTHESIS,
            fields=create_hypothesis_fields(),
            revision=0,
            authority=AuthorityLevel.LOCAL_FIXTURE,
            workspace_id="workspace-workbench-local",
        )
    ).disposition is CommandDisposition.ACCEPTED
    assert service.handle(
        command(
            "command-review-scope",
            CommandKind.REVIEW_HYPOTHESIS_SCOPE,
            fields=(
                CommandField("hypothesis_id", "hypothesis-cache-key"),
                CommandField("review_basis", "I matched the exact local fixture contract."),
            ),
            revision=0,
            acknowledged=True,
            workspace_id="workspace-workbench-local",
        )
    ).disposition is CommandDisposition.ACCEPTED
    assert service.handle(
        command(
            "command-plan-experiment",
            CommandKind.PLAN_EXPERIMENT,
            fields=experiment_fields(),
            revision=1,
            workspace_id="workspace-workbench-local",
        )
    ).disposition is CommandDisposition.ACCEPTED
    research.start_session(
        "workspace-workbench-local", "session-cache-local", actor="operator-local"
    )
    research.transition_experiment(
        "workspace-workbench-local",
        "experiment-cache-key",
        ExperimentStatus.READY,
        actor="operator-local",
        expected_revision=0,
    )
    research.transition_experiment(
        "workspace-workbench-local",
        "experiment-cache-key",
        ExperimentStatus.ACTIVE,
        actor="operator-local",
        expected_revision=1,
    )
    research.transition_hypothesis(
        "workspace-workbench-local",
        "hypothesis-cache-key",
        HypothesisStatus.TESTING,
        actor="operator-local",
        expected_revision=2,
    )
    fields = (
        CommandField("action_type", "fixture.cache.read"),
        CommandField("exact_action", "Read two equivalent fixture paths"),
        CommandField("experiment_id", "experiment-cache-key"),
        CommandField("expected_effects", ("reads=2",)),
        CommandField("max_requests", 2),
        CommandField("purpose", "Test the planned cache normalization theory"),
        CommandField("target_asset_id", "asset-cache-fixture"),
        CommandField("technique", "cache-key-comparison"),
    )
    intent = command(
        "action-fixture",
        CommandKind.REQUEST_ACTION,
        fields=fields,
        revision=0,
        authority=AuthorityLevel.LOCAL_FIXTURE,
        acknowledged=True,
        workspace_id="workspace-workbench-local",
    )

    accepted = service.handle(intent)
    repeated = service.handle(intent)
    assert accepted.disposition is CommandDisposition.ACCEPTED, accepted
    assert accepted.executed is False
    assert repeated == accepted
    snapshot = research.snapshot("workspace-workbench-local")
    request = snapshot.action_requests["action-fixture"]

    assert request.authority_ref == snapshot.workspace.authority_ref
    assert request.session_id == "session-cache-local"
    assert request.identity_id is None
    assert request.stop_conditions == snapshot.experiments[
        "experiment-cache-key"
    ].stop_conditions
    assert snapshot.action_receipts == {}

    unplanned = service.handle(
        command(
            "action-unplanned",
            CommandKind.REQUEST_ACTION,
            fields=(
                *fields[:1],
                CommandField("exact_action", "Invent a new fixture action"),
                *fields[2:],
            ),
            revision=0,
            authority=AuthorityLevel.LOCAL_FIXTURE,
            acknowledged=True,
            workspace_id="workspace-workbench-local",
        )
    )
    non_fixture = service.handle(
        command(
            "action-network-shaped",
            CommandKind.REQUEST_ACTION,
            fields=(CommandField("action_type", "http.get"), *fields[1:]),
            revision=0,
            authority=AuthorityLevel.LOCAL_FIXTURE,
            acknowledged=True,
            workspace_id="workspace-workbench-local",
        )
    )
    assert unplanned.disposition is CommandDisposition.INVALID
    assert "server-held experiment actions" in unplanned.message
    assert non_fixture.disposition is CommandDisposition.INVALID
    assert "fixture.*" in non_fixture.message
    assert len(research.snapshot("workspace-workbench-local").action_requests) == 1


def test_research_commands_create_review_and_plan_without_execution(tmp_path):
    service, research = research_planning_service(tmp_path)
    created = service.handle(
        command(
            "command-create-hypothesis",
            CommandKind.CREATE_HYPOTHESIS,
            fields=create_hypothesis_fields(),
            revision=0,
            authority=AuthorityLevel.LOCAL_FIXTURE,
            workspace_id="workspace-workbench-local",
        )
    )
    assert created.disposition is CommandDisposition.ACCEPTED
    assert created.executed is False
    initial = research.snapshot("workspace-workbench-local").hypotheses[
        "hypothesis-cache-key"
    ]
    assert initial.status is HypothesisStatus.DRAFT
    assert initial.revision == 0
    assert initial.authority_ref == research.snapshot(
        "workspace-workbench-local"
    ).workspace.authority_ref

    reviewed = service.handle(
        command(
            "command-review-scope",
            CommandKind.REVIEW_HYPOTHESIS_SCOPE,
            fields=(
                CommandField("hypothesis_id", "hypothesis-cache-key"),
                CommandField(
                    "review_basis",
                    "The stored contract and target classification were reviewed locally",
                ),
            ),
            revision=0,
            acknowledged=True,
            workspace_id="workspace-workbench-local",
        )
    )
    assert reviewed.disposition is CommandDisposition.ACCEPTED
    assert reviewed.executed is False
    scoped = research.snapshot("workspace-workbench-local").hypotheses[
        "hypothesis-cache-key"
    ]
    assert scoped.status is HypothesisStatus.SCOPED
    assert scoped.revision == 1

    stale = service.handle(
        command(
            "command-review-stale",
            CommandKind.REVIEW_HYPOTHESIS_SCOPE,
            fields=(
                CommandField("hypothesis_id", "hypothesis-cache-key"),
                CommandField("review_basis", "Stale browser state"),
            ),
            revision=0,
            acknowledged=True,
            workspace_id="workspace-workbench-local",
        )
    )
    assert stale.disposition is CommandDisposition.CONFLICT
    assert stale.code == "revision_conflict"

    planned = service.handle(
        command(
            "command-plan-experiment",
            CommandKind.PLAN_EXPERIMENT,
            fields=experiment_fields(),
            revision=1,
            workspace_id="workspace-workbench-local",
        )
    )
    repeated = service.handle(
        command(
            "command-plan-experiment",
            CommandKind.PLAN_EXPERIMENT,
            fields=experiment_fields(),
            revision=1,
            workspace_id="workspace-workbench-local",
        )
    )
    final = research.snapshot("workspace-workbench-local")
    assert planned.disposition is CommandDisposition.ACCEPTED
    assert planned.executed is False
    assert repeated == planned
    assert final.hypotheses["hypothesis-cache-key"].status is HypothesisStatus.PLANNED
    assert final.hypotheses["hypothesis-cache-key"].revision == 2
    assert final.experiments["experiment-cache-key"].revision == 0
    assert len(final.experiments) == 1
    snapshot_record = service.snapshot(
        active_workspace_id="workspace-workbench-local"
    ).section("hypotheses").records[0]
    assert ("revision", "2") in snapshot_record.attributes


def test_store_side_revision_race_is_returned_as_a_typed_conflict(tmp_path):
    service, research = research_planning_service(tmp_path)
    service.handle(
        command(
            "command-create-race-hypothesis",
            CommandKind.CREATE_HYPOTHESIS,
            fields=create_hypothesis_fields(),
            revision=0,
            authority=AuthorityLevel.LOCAL_FIXTURE,
            workspace_id="workspace-workbench-local",
        )
    )

    class RacingResearch:
        def snapshot(self, workspace_id):
            return research.snapshot(workspace_id)

        def scope_hypothesis(self, *args, **kwargs):
            raise ResearchRevisionConflict(
                "hypothesis revision conflict: expected 0, current 1"
            )

    result = WorkbenchApplicationService(
        research=RacingResearch(), clock=lambda: NOW
    ).handle(
        command(
            "command-racing-scope",
            CommandKind.REVIEW_HYPOTHESIS_SCOPE,
            fields=(
                CommandField("hypothesis_id", "hypothesis-cache-key"),
                CommandField("review_basis", "Current local review"),
            ),
            revision=0,
            acknowledged=True,
            workspace_id="workspace-workbench-local",
        )
    )

    assert result.disposition is CommandDisposition.CONFLICT
    assert result.code == "revision_conflict"
    assert result.executed is False


def test_mastery_assessment_is_fresh_human_bound_and_evidence_only(tmp_path):
    mastery, journeys = stores(tmp_path / "learning")
    service = WorkbenchApplicationService(
        mastery=mastery,
        journeys=journeys,
        operator_ref="operator-local",
        clock=lambda: NOW,
    )
    assessment_command = command(
        "command-record-mastery",
        CommandKind.RECORD_MASTERY_ASSESSMENT,
        fields=mastery_fields(),
        revision=0,
        acknowledged=True,
    )

    accepted = service.handle(assessment_command)
    repeated = service.handle(assessment_command)
    persisted = mastery.assessments()

    assert accepted.disposition is CommandDisposition.ACCEPTED
    assert accepted.executed is False
    assert repeated == accepted
    assert len(persisted) == 1
    assert persisted[0].assessor == "operator-local"
    assert persisted[0].assessor_kind.value == "human"
    assert persisted[0].credits_mastery is True
    assert persisted[0].evidence_refs == (
        "lab-report:controlled-two-account-review",
    )

    duplicate = service.handle(
        command(
            "command-record-mastery-duplicate",
            CommandKind.RECORD_MASTERY_ASSESSMENT,
            fields=mastery_fields(),
            revision=0,
            acknowledged=True,
        )
    )
    assert duplicate.disposition is CommandDisposition.CONFLICT
    assert duplicate.code == "record_exists"

    unexpected = service.handle(
        command(
            "command-record-mastery-extra",
            CommandKind.RECORD_MASTERY_ASSESSMENT,
            fields=(
                *mastery_fields(),
                CommandField("assessor", "GreyTheory AI"),
            ),
            revision=0,
            acknowledged=True,
        )
    )
    assert unexpected.disposition is CommandDisposition.INVALID
    assert "unexpected=['assessor']" in unexpected.message

    stale = replace(
        command(
            "command-record-mastery-stale",
            CommandKind.RECORD_MASTERY_ASSESSMENT,
            fields=(
                CommandField("assessment_id", "assessment-stale"),
                *mastery_fields()[1:],
            ),
            revision=0,
            acknowledged=True,
        ),
        issued_at=NOW - timedelta(minutes=11),
    )
    stale_result = service.handle(stale)
    assert stale_result.disposition is CommandDisposition.INVALID
    assert "stale" in stale_result.message

    wrong_operator = service.handle(
        command(
            "command-record-mastery-wrong-operator",
            CommandKind.RECORD_MASTERY_ASSESSMENT,
            fields=(
                CommandField("assessment_id", "assessment-wrong-operator"),
                *mastery_fields()[1:],
            ),
            revision=0,
            acknowledged=True,
            operator_ref="another-operator",
        )
    )
    assert wrong_operator.disposition is CommandDisposition.INVALID
    assert wrong_operator.code == "operator_mismatch"
    assert len(mastery.assessments()) == 1


def test_snapshot_reads_the_complete_local_vertical_slice(tmp_path):
    run_root = tmp_path / "run"
    result = run_local_two_account_slice(
        run_root, statements=fixture_statements(), clock=lambda: NOW
    )
    finding = Finding.from_dict(
        json.loads((run_root / "finding.json").read_text(encoding="utf-8"))
    )
    assert len(finding.role_bindings) == 7
    assert finding.unanswered_roles == []
    service = WorkbenchApplicationService(
        audit=AuditLog(run_root / "audit" / "audit.jsonl", clock=lambda: NOW),
        research=ResearchStore(run_root / "research", clock=lambda: NOW),
        evidence=EvidenceVault(run_root / "evidence", clock=lambda: NOW),
        findings=(finding,),
        clock=lambda: NOW,
    )

    snapshot = service.snapshot(active_workspace_id=result.workspace_id)

    assert snapshot.source_errors == ()
    assert snapshot.section("research").status is ReadinessStatus.READY
    assert snapshot.section("hypotheses").records
    assert snapshot.section("evidence").records[0].status is ReadinessStatus.READY
    assert snapshot.section("reports").records[0].status is ReadinessStatus.ATTENTION
    assert snapshot.context.workspace_id == result.workspace_id
    assert snapshot.context.session_id == result.session_id
    assert snapshot.context.finding_id == finding.id
    assert snapshot.live_target_available is False


def test_report_export_is_private_redacted_atomic_and_never_submits(tmp_path):
    run_root = tmp_path / "run"
    result = run_local_two_account_slice(
        run_root, statements=fixture_statements(), clock=lambda: NOW
    )
    finding = Finding.from_dict(
        json.loads((run_root / "finding.json").read_text(encoding="utf-8"))
    )
    draft = ReportDraft.from_dict(
        json.loads((run_root / "report.json").read_text(encoding="utf-8"))
    )
    audit = AuditLog(run_root / "audit" / "audit.jsonl", clock=lambda: NOW)
    report_store = ReportStore(run_root / "reports", audit=audit, clock=lambda: NOW)
    report_store.create(finding, draft, actor="operator-local")
    service = WorkbenchApplicationService(
        audit=audit,
        evidence=EvidenceVault(run_root / "evidence", clock=lambda: NOW),
        report_store=report_store,
        report_export_writer=ReportExportWriter(run_root / "exports", audit=audit),
        clock=lambda: NOW,
    )
    statements = fixture_statements()
    evidence_refs = tuple(finding.evidence_refs)
    validation_fields = (
        CommandField("finding_id", finding.id),
        CommandField("reproducibility_statement", statements.reproducibility),
        CommandField("reproducibility_evidence_refs", evidence_refs),
        CommandField("impact_statement", statements.impact),
        CommandField("impact_evidence_refs", evidence_refs),
        CommandField("duplicate_risk_statement", statements.duplicate_risk),
        CommandField("duplicate_risk_evidence_refs", evidence_refs),
    )
    validation_result = service.handle(
        command(
            "command-validate-report",
            CommandKind.RUN_REPORT_VALIDATION,
            fields=validation_fields,
            revision=0,
            acknowledged=True,
        )
    )
    validated_case = report_store.get(finding.id)
    assert validation_result.disposition is CommandDisposition.ACCEPTED
    assert validation_result.code == "report_validation_passed"
    assert validation_result.executed is False
    assert validated_case.revision == 1
    assert validated_case.finding.state.value == "report_ready"
    assert validated_case.current_validation is not None
    assert validated_case.current_validation.report.submission_ready is True
    assert {item.actor for item in validated_case.current_validation.attestations} == {
        "operator-local"
    }
    report_record = service.snapshot().section("reports").records[0]
    assert dict(report_record.attributes)["latest_validation"] == "passed"
    stale_validation = service.handle(
        command(
            "command-validate-report-stale",
            CommandKind.RUN_REPORT_VALIDATION,
            fields=validation_fields,
            revision=0,
            acknowledged=True,
        )
    )
    assert stale_validation.disposition is CommandDisposition.CONFLICT
    assert stale_validation.code == "revision_conflict"
    assert len(report_store.get(finding.id).validations) == 1
    report_store.save_draft(
        validated_case.draft,
        expected_revision=1,
        actor="operator-local",
    )
    invalidated_record = service.snapshot().section("reports").records[0]
    assert dict(invalidated_record.attributes)["latest_validation"] == "not_run"
    invalidated_case = report_store.get(finding.id)
    assert invalidated_case.current_validation is None
    assert len(invalidated_case.validations) == 1

    export_command = command(
        "command-export-report",
        CommandKind.EXPORT_REPORT,
        fields=(
            CommandField("export_id", "export-local-bola-1"),
            CommandField("finding_id", finding.id),
        ),
        revision=0,
        acknowledged=True,
    )

    accepted = service.handle(export_command)
    repeated = service.handle(export_command)
    destination = run_root / "exports" / "export-local-bola-1"
    manifest = json.loads((destination / "manifest.json").read_text("utf-8"))

    assert accepted.disposition is CommandDisposition.ACCEPTED
    assert accepted.executed is False
    assert repeated == accepted
    assert manifest["submission_performed"] is False
    assert manifest["operator_ref"] == "operator-local"
    assert manifest["finding_id"] == finding.id
    assert (destination / "report.md").is_file()
    assert (destination / "report.json").is_file()
    assert len(manifest["artifacts"]) == 3
    for artifact in manifest["artifacts"]:
        exported = destination / artifact["path"]
        assert exported.is_file()
        assert b"SECRET" not in exported.read_bytes()
    assert not any(destination.rglob("raw"))
    assert audit.records()[-1].action == "report.export"
    assert audit.records()[-1].detail["submission_performed"] is False

    duplicate = service.handle(
        command(
            "command-export-report-duplicate",
            CommandKind.EXPORT_REPORT,
            fields=(
                CommandField("export_id", "export-local-bola-1"),
                CommandField("finding_id", finding.id),
            ),
            revision=0,
            acknowledged=True,
        )
    )
    assert duplicate.disposition is CommandDisposition.CONFLICT
    assert duplicate.code == "record_exists"


def test_report_case_and_draft_are_persisted_revisioned_and_server_bound(tmp_path):
    planning, research = research_planning_service(tmp_path)
    assert planning.handle(
        command(
            "create-hypothesis-for-report",
            CommandKind.CREATE_HYPOTHESIS,
            fields=create_hypothesis_fields(),
            revision=0,
            authority=AuthorityLevel.LOCAL_FIXTURE,
            workspace_id="workspace-workbench-local",
        )
    ).disposition is CommandDisposition.ACCEPTED
    assert planning.handle(
        command(
            "review-hypothesis-for-report",
            CommandKind.REVIEW_HYPOTHESIS_SCOPE,
            fields=(
                CommandField("hypothesis_id", "hypothesis-cache-key"),
                CommandField("review_basis", "Exact local fixture scope reviewed."),
            ),
            revision=0,
            acknowledged=True,
            workspace_id="workspace-workbench-local",
        )
    ).disposition is CommandDisposition.ACCEPTED
    assert planning.handle(
        command(
            "plan-hypothesis-for-report",
            CommandKind.PLAN_EXPERIMENT,
            fields=experiment_fields(),
            revision=1,
            workspace_id="workspace-workbench-local",
        )
    ).disposition is CommandDisposition.ACCEPTED
    research.transition_hypothesis(
        "workspace-workbench-local",
        "hypothesis-cache-key",
        HypothesisStatus.TESTING,
        actor="operator-local",
        expected_revision=2,
    )
    reports = ReportStore(tmp_path / "reports", clock=lambda: NOW)
    evidence = EvidenceVault(tmp_path / "evidence", clock=lambda: NOW)
    service = WorkbenchApplicationService(
        research=research,
        evidence=evidence,
        report_store=reports,
        clock=lambda: NOW,
    )

    created = service.handle(
        command(
            "create-report-case",
            CommandKind.CREATE_REPORT_CASE,
            fields=(
                CommandField("finding_id", "finding-cache-key"),
                CommandField("hypothesis_id", "hypothesis-cache-key"),
                CommandField("lane", 4),
                CommandField(
                    "title", "Cache normalization may split equivalent keys"
                ),
            ),
            revision=0,
            workspace_id="workspace-workbench-local",
        )
    )
    saved = service.handle(
        command(
            "save-report-draft",
            CommandKind.SAVE_REPORT_DRAFT,
            fields=report_draft_fields(),
            revision=0,
        )
    )
    case = ReportStore(tmp_path / "reports", clock=lambda: NOW).get(
        "finding-cache-key"
    )

    assert created.disposition is CommandDisposition.ACCEPTED
    assert created.executed is False
    assert saved.disposition is CommandDisposition.ACCEPTED
    assert saved.code == "report_draft_incomplete"
    assert case.revision == 1
    assert case.finding.state.value == "informational"
    assert case.finding.authority_ref == research.snapshot(
        "workspace-workbench-local"
    ).workspace.authority_ref
    assert case.draft.programme == "programme-workbench-local"
    assert case.draft.asset == "fixture://cache-normalization"
    assert case.draft.summary == "A draft operator summary."
    report_record = service.snapshot().section("reports").records[0]
    assert report_record.id == case.id
    assert dict(report_record.attributes)["draft_revision"] == "1"
    assert dict(report_record.attributes)["export_candidate"] == "false"

    stale = service.handle(
        command(
            "save-report-draft-stale",
            CommandKind.SAVE_REPORT_DRAFT,
            fields=report_draft_fields(),
            revision=0,
        )
    )
    injected_authority = service.handle(
        command(
            "save-report-draft-injected-authority",
            CommandKind.SAVE_REPORT_DRAFT,
            fields=(
                *report_draft_fields(),
                CommandField("authority_ref", "b" * 64),
            ),
            revision=1,
        )
    )
    assert stale.disposition is CommandDisposition.CONFLICT
    assert stale.code == "revision_conflict"
    assert injected_authority.disposition is CommandDisposition.INVALID
    assert "unexpected=['authority_ref']" in injected_authority.message
    assert reports.get(case.id).revision == 1


def test_snapshot_resolves_one_exact_bound_approval_without_treating_it_as_execution(tmp_path):
    run_root = tmp_path / "run"
    result = run_local_two_account_slice(
        run_root, statements=fixture_statements(), clock=lambda: NOW
    )
    persisted = ResearchStore(run_root / "research", clock=lambda: NOW).snapshot(
        result.workspace_id
    )
    original = next(iter(persisted.action_requests.values()))
    request = replace(original, approval_ref="approval-1")
    bound = replace(persisted, action_requests={request.id: request})
    asset = bound.assets[request.target_asset_id]

    class StaticResearch:
        def workspace_ids(self):
            return [bound.workspace.id]

        def snapshot(self, workspace_id):
            assert workspace_id == bound.workspace.id
            return bound

    approvals = LocalApprovalStore()
    approvals.grant(
        approval_id="approval-1",
        operator_id="operator-local",
        action_type=request.action_type,
        target=asset.canonical_identifier,
        responded_at=NOW,
    )
    snapshot = WorkbenchApplicationService(
        research=StaticResearch(), approvals=approvals, clock=lambda: NOW
    ).snapshot(active_workspace_id=result.workspace_id)

    section = snapshot.section("approvals")
    assert section.status is ReadinessStatus.READY
    assert section.records[0].status is ReadinessStatus.READY
    assert "gate must still evaluate" in section.records[0].detail
    assert section.records[0].attributes[-1] == ("executed", "true")


def test_corrupt_workspace_fails_closed_in_snapshot(tmp_path):
    run_root = tmp_path / "run"
    result = run_local_two_account_slice(
        run_root, statements=fixture_statements(), clock=lambda: NOW
    )
    workspace_path = run_root / "research" / result.workspace_id / "workspace.json"
    envelope = json.loads(workspace_path.read_text(encoding="utf-8"))
    envelope["workspace"]["title"] = "tampered"
    workspace_path.write_text(json.dumps(envelope), encoding="utf-8")

    snapshot = WorkbenchApplicationService(
        research=ResearchStore(run_root / "research", clock=lambda: NOW),
        clock=lambda: NOW,
    ).snapshot(active_workspace_id=result.workspace_id)

    assert snapshot.section("research").status is ReadinessStatus.BLOCKED
    assert snapshot.section("research").status is not ReadinessStatus.EMPTY
    assert any("integrity" in error for error in snapshot.source_errors)
    assert snapshot.next_action.id == "repair-research"


def test_application_layer_has_no_network_or_process_imports():
    forbidden = {"aiohttp", "httpx", "requests", "socket", "subprocess", "urllib"}
    root = Path(__file__).resolve().parents[1] / "greytheory_app"
    imported: set[str] = set()
    for path in root.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module.split(".")[0])
    assert imported.isdisjoint(forbidden)
