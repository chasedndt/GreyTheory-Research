"""Application-layer contracts for a future local GreyTheory workbench."""

from __future__ import annotations

import ast
import json
from dataclasses import replace
from datetime import datetime, timezone
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
    HypothesisStatus,
    ResearchSession,
    ResearchRevisionConflict,
    ResearchStore,
    ResearchWorkspace,
    TargetAsset,
)
from greytheory.vertical_slice import OperatorStatements, run_local_two_account_slice
from greytheory_app import (
    CommandDisposition,
    CommandField,
    CommandKind,
    NextAction,
    ReadinessStatus,
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
) -> WorkbenchCommand:
    return WorkbenchCommand(
        id=command_id,
        kind=kind,
        operator_ref="operator-local",
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


def test_action_intent_is_typed_but_cannot_execute_or_raise_posture():
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
            authority=AuthorityLevel.PASSIVE_HTTP,
            acknowledged=True,
        )

    result = WorkbenchApplicationService().handle(
        command(
            "action-fixture",
            CommandKind.REQUEST_ACTION,
            fields=fields,
            authority=AuthorityLevel.LOCAL_FIXTURE,
            acknowledged=True,
        )
    )
    assert result.disposition is CommandDisposition.REFUSED
    assert result.code == "handler_not_implemented"
    assert result.executed is False


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


def test_snapshot_reads_the_complete_local_vertical_slice(tmp_path):
    run_root = tmp_path / "run"
    result = run_local_two_account_slice(
        run_root, statements=fixture_statements(), clock=lambda: NOW
    )
    finding = Finding.from_dict(
        json.loads((run_root / "finding.json").read_text(encoding="utf-8"))
    )
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
