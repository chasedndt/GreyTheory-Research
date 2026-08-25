"""Transport-neutral local workbench assembly and command routing.

The service reads existing GreyTheory stores and exposes bounded learning,
research-planning, human-assessment, and private report-export use cases. Action
commands remain typed refusals until their dedicated handler exists. Nothing
here calls a tool, collector, model provider, shell, browser, worker, or network.
"""

# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 ChaseInTech

from __future__ import annotations

import hashlib
import json
from datetime import date, datetime, timedelta, timezone
from typing import Callable, Sequence

from greytheory.audit import AuditLog
from greytheory.authority.approvals import (
    DEFAULT_APPROVAL_MAX_AGE,
    ApprovalStore,
)
from greytheory.authority.gate import AuthorityLevel
from greytheory.authority.scope import ScopeClassification
from greytheory.capabilities import CAPABILITIES, CapabilityStatus
from greytheory.evidence import EvidenceVault
from greytheory.findings import Finding, Taxonomy
from greytheory.learning import (
    AssessorKind,
    GuidedLearningPlanner,
    JourneyStatus,
    LearningJourneyStore,
    MasteryAssessment,
    MasteryDimension,
    MasteryLevel,
    MasteryStore,
    abandon_learning_journey,
    advance_learning_journey,
    load_builtin_catalogue,
    start_learning_journey,
)
from greytheory.registry import ProgrammeRegistry
from greytheory.report import ReportDraft
from greytheory.research import (
    ActionRequest,
    EffectBudget,
    ExperimentPlan,
    Hypothesis,
    ResearchRevisionConflict,
    ResearchStore,
)
from greytheory.research.store import WorkspaceSnapshot
from greytheory.validation import gate_f_report_quality
from greytheory_app.contracts import (
    CommandDisposition,
    CommandKind,
    CommandResult,
    NextAction,
    ReadinessStatus,
    WorkbenchCommand,
    WorkbenchContext,
    WorkbenchContractError,
    WorkbenchMetric,
    WorkbenchRecord,
    WorkbenchSection,
    WorkbenchSnapshot,
)
from greytheory_app.export import ReportExportConflict, ReportExportWriter


def _status_from_capability(status: CapabilityStatus) -> ReadinessStatus:
    return {
        CapabilityStatus.LIVE: ReadinessStatus.READY,
        CapabilityStatus.PARTIAL: ReadinessStatus.ATTENTION,
        CapabilityStatus.PLANNED: ReadinessStatus.UNKNOWN,
        CapabilityStatus.UNAVAILABLE: ReadinessStatus.BLOCKED,
    }[status]


def _section_error(section_id: str, title: str, exc: Exception) -> WorkbenchSection:
    return WorkbenchSection(
        section_id,
        title,
        ReadinessStatus.BLOCKED,
        metrics=(
            WorkbenchMetric(
                "Source",
                "failed",
                ReadinessStatus.BLOCKED,
                str(exc),
                section_id,
            ),
        ),
        note="The source failed closed; no empty or healthy state was inferred.",
    )


def _command_text(
    command: WorkbenchCommand, name: str, *, optional: bool = False
) -> str | None:
    value = command.field(name)
    if value is None and optional:
        return None
    if not isinstance(value, str) or not value.strip():
        raise WorkbenchContractError(f"{command.kind.value} requires {name}")
    return value.strip()


def _command_texts(
    command: WorkbenchCommand, name: str, *, optional: bool = False
) -> tuple[str, ...]:
    value = command.field(name, () if optional else None)
    if not isinstance(value, tuple) or any(not item.strip() for item in value):
        raise WorkbenchContractError(
            f"{command.kind.value} requires {name} as a tuple of text values"
        )
    if not optional and not value:
        raise WorkbenchContractError(f"{command.kind.value} requires {name}")
    return tuple(item.strip() for item in value)


def _command_int(command: WorkbenchCommand, name: str) -> int:
    value = command.field(name)
    if isinstance(value, bool) or not isinstance(value, int):
        raise WorkbenchContractError(
            f"{command.kind.value} requires {name} as an integer"
        )
    return value


def _command_effects(command: WorkbenchCommand, name: str) -> EffectBudget:
    encoded = _command_texts(command, name, optional=True)
    values: dict[str, int] = {}
    for item in encoded:
        effect, separator, amount = item.partition("=")
        effect = effect.strip()
        if not separator or not effect or effect in values:
            raise WorkbenchContractError(
                f"{name} entries must be unique effect=limit pairs"
            )
        try:
            values[effect] = int(amount)
        except ValueError as exc:
            raise WorkbenchContractError(
                f"{name} entries must use integer limits"
            ) from exc
    return EffectBudget.from_mapping(values)


def _require_command_fields(
    command: WorkbenchCommand,
    *,
    required: set[str],
    optional: set[str] | None = None,
) -> None:
    names = {field.name for field in command.fields}
    allowed = required | (optional or set())
    if names != required and not (required <= names <= allowed):
        raise WorkbenchContractError(
            f"{command.kind.value} fields do not match its contract: "
            f"missing={sorted(required - names)!r}, "
            f"unexpected={sorted(names - allowed)!r}"
        )


class WorkbenchApplicationService:
    """Assemble one honest workbench snapshot and route bounded commands."""

    def __init__(
        self,
        *,
        posture: AuthorityLevel = AuthorityLevel.LOCAL_FIXTURE,
        registry: ProgrammeRegistry | None = None,
        audit: AuditLog | None = None,
        research: ResearchStore | None = None,
        mastery: MasteryStore | None = None,
        journeys: LearningJourneyStore | None = None,
        evidence: EvidenceVault | None = None,
        findings: Sequence[Finding] | None = None,
        report_drafts: Sequence[ReportDraft] | None = None,
        report_export_writer: ReportExportWriter | None = None,
        approvals: ApprovalStore | None = None,
        operator_ref: str = "operator-local",
        clock: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
    ) -> None:
        if posture > AuthorityLevel.LOCAL_FIXTURE:
            raise WorkbenchContractError(
                "the current application service is structurally limited to LOCAL_FIXTURE"
            )
        self.posture = posture
        self.registry = registry
        self.audit = audit
        self.research = research
        self.mastery = mastery
        self.journeys = journeys
        self.evidence = evidence
        self.findings = None if findings is None else tuple(findings)
        self.report_drafts = None if report_drafts is None else tuple(report_drafts)
        if self.report_drafts is not None:
            ids = [draft.finding_id for draft in self.report_drafts]
            if len(ids) != len(set(ids)):
                raise WorkbenchContractError(
                    "report draft finding identifiers must be unique"
                )
        self.report_export_writer = report_export_writer
        self.approvals = approvals
        if not str(operator_ref or "").strip():
            raise WorkbenchContractError("application operator reference is required")
        self.operator_ref = str(operator_ref).strip()
        self.clock = clock
        self.catalogue = load_builtin_catalogue()
        self._idempotency: dict[str, tuple[str, CommandResult]] = {}

    def snapshot(self, *, active_workspace_id: str | None = None) -> WorkbenchSnapshot:
        now = self.clock()
        if now.tzinfo is None:
            raise WorkbenchContractError("application clock must be timezone-aware")
        errors: list[str] = []

        programmes = self._safe_section(
            "programmes", "Programmes", self._programmes_section, errors
        )
        research, active = self._research_section(active_workspace_id, errors)
        hypotheses = self._hypotheses_section(active, errors)
        learning, active_journey_id = self._learning_section(now, errors)
        evidence = self._safe_section(
            "evidence", "Evidence", self._evidence_section, errors
        )
        reports = self._safe_section(
            "reports", "Reports", self._reports_section, errors
        )
        approvals = self._approvals_section(active, now, errors)
        capabilities = self._capabilities_section()

        context = self._context(active, active_journey_id)
        provisional = (
            programmes,
            learning,
            research,
            hypotheses,
            evidence,
            reports,
            approvals,
            capabilities,
        )
        overview = self._overview_section(provisional)
        sections = (overview, *provisional)
        next_action = self._next_action(sections, context)
        return WorkbenchSnapshot(
            generated_at=now,
            posture=self.posture,
            context=context,
            next_action=next_action,
            sections=sections,
            source_errors=tuple(errors),
        )

    def _safe_section(
        self,
        section_id: str,
        title: str,
        builder: Callable[[], WorkbenchSection],
        errors: list[str],
    ) -> WorkbenchSection:
        try:
            return builder()
        except Exception as exc:  # A workbench must expose source failure, not crash or guess.
            errors.append(f"{section_id}: {exc}")
            return _section_error(section_id, title, exc)

    def _programmes_section(self) -> WorkbenchSection:
        if self.registry is None:
            return WorkbenchSection(
                "programmes",
                "Programmes",
                ReadinessStatus.UNKNOWN,
                metrics=(
                    WorkbenchMetric(
                        "Registered",
                        "unknown",
                        ReadinessStatus.UNKNOWN,
                        "no programme registry configured",
                    ),
                ),
                note="Configure a private registry before treating programme state as measured.",
            )
        programme_ids = self.registry.programmes()
        if not programme_ids:
            return WorkbenchSection(
                "programmes",
                "Programmes",
                ReadinessStatus.EMPTY,
                metrics=(WorkbenchMetric("Registered", "0", ReadinessStatus.EMPTY),),
                note="The registry is configured and contains no programmes.",
            )
        attention = {item.programme_id: item for item in self.registry.needs_attention()}
        records: list[WorkbenchRecord] = []
        for programme_id in programme_ids:
            version = self.registry.latest(programme_id)
            contract = self.registry.current_contract(programme_id)
            item = attention.get(programme_id)
            records.append(
                WorkbenchRecord(
                    id=programme_id,
                    title=programme_id,
                    status=(
                        ReadinessStatus.ATTENTION if item else ReadinessStatus.READY
                    ),
                    subtitle=(contract.status.value if contract else "unknown"),
                    detail=item.reason if item else "current reviewed state is usable offline",
                    references=(
                        f"contract:{contract.fingerprint()}" if contract else "contract:unknown",
                    ),
                    attributes=(
                        ("version", str(version.version) if version else "unknown"),
                        ("max_authority", contract.max_authority if contract else "unknown"),
                        ("human_reviewed", str(bool(contract and contract.human_reviewed)).lower()),
                    ),
                )
            )
        return WorkbenchSection(
            "programmes",
            "Programmes",
            ReadinessStatus.ATTENTION if attention else ReadinessStatus.READY,
            metrics=(
                WorkbenchMetric("Registered", str(len(records)), ReadinessStatus.READY),
                WorkbenchMetric(
                    "Need attention",
                    str(len(attention)),
                    ReadinessStatus.ATTENTION if attention else ReadinessStatus.READY,
                ),
            ),
            records=tuple(records),
        )

    def _research_section(
        self, active_workspace_id: str | None, errors: list[str]
    ) -> tuple[WorkbenchSection, WorkspaceSnapshot | None]:
        if self.research is None:
            return (
                WorkbenchSection(
                    "research",
                    "Research",
                    ReadinessStatus.UNKNOWN,
                    metrics=(
                        WorkbenchMetric(
                            "Workspaces",
                            "unknown",
                            ReadinessStatus.UNKNOWN,
                            "no private research store configured",
                        ),
                    ),
                    note="No workspace state is measured; configure a private root outside Git.",
                ),
                None,
            )
        try:
            workspace_ids = self.research.workspace_ids()
        except Exception as exc:
            errors.append(f"research: {exc}")
            return _section_error("research", "Research", exc), None
        if not workspace_ids:
            return (
                WorkbenchSection(
                    "research",
                    "Research",
                    ReadinessStatus.EMPTY,
                    metrics=(WorkbenchMetric("Workspaces", "0", ReadinessStatus.EMPTY),),
                    note="The private research store is configured and contains no workspaces.",
                ),
                None,
            )
        selected = active_workspace_id or workspace_ids[0]
        if selected not in workspace_ids:
            exc = ValueError(f"active workspace {selected!r} does not exist")
            errors.append(f"research: {exc}")
            return _section_error("research", "Research", exc), None

        records: list[WorkbenchRecord] = []
        active: WorkspaceSnapshot | None = None
        blocked = False
        for workspace_id in workspace_ids:
            try:
                snapshot = self.research.snapshot(workspace_id)
                if workspace_id == selected:
                    active = snapshot
                running = sum(
                    item.status.value == "active" for item in snapshot.sessions.values()
                )
                records.append(
                    WorkbenchRecord(
                        id=workspace_id,
                        title=snapshot.workspace.title,
                        status=ReadinessStatus.READY,
                        subtitle=snapshot.workspace.status.value,
                        detail=snapshot.workspace.goals[0],
                        references=(f"authority:{snapshot.workspace.authority_ref}",),
                        attributes=(
                            ("programme_id", snapshot.workspace.programme_id),
                            ("posture", snapshot.workspace.operating_posture.name),
                            ("sessions", str(len(snapshot.sessions))),
                            ("active_sessions", str(running)),
                            ("hypotheses", str(len(snapshot.hypotheses))),
                            ("action_requests", str(len(snapshot.action_requests))),
                            ("action_receipts", str(len(snapshot.action_receipts))),
                            ("lessons", str(len(snapshot.lessons))),
                        ),
                    )
                )
            except Exception as exc:
                blocked = True
                errors.append(f"research/{workspace_id}: {exc}")
                records.append(
                    WorkbenchRecord(
                        id=workspace_id,
                        title=workspace_id,
                        status=ReadinessStatus.BLOCKED,
                        detail=str(exc),
                    )
                )
        return (
            WorkbenchSection(
                "research",
                "Research",
                ReadinessStatus.BLOCKED if blocked else ReadinessStatus.READY,
                metrics=(
                    WorkbenchMetric(
                        "Workspaces", str(len(workspace_ids)), ReadinessStatus.READY
                    ),
                    WorkbenchMetric(
                        "Active",
                        selected if active is not None else "unknown",
                        ReadinessStatus.READY if active is not None else ReadinessStatus.BLOCKED,
                    ),
                ),
                records=tuple(records),
            ),
            active,
        )

    def _hypotheses_section(
        self, active: WorkspaceSnapshot | None, errors: list[str]
    ) -> WorkbenchSection:
        if active is None:
            return WorkbenchSection(
                "hypotheses",
                "Hypotheses",
                ReadinessStatus.UNKNOWN,
                metrics=(
                    WorkbenchMetric(
                        "Tracked",
                        "unknown",
                        ReadinessStatus.UNKNOWN,
                        "no readable active workspace",
                    ),
                ),
            )
        if not active.hypotheses:
            return WorkbenchSection(
                "hypotheses",
                "Hypotheses",
                ReadinessStatus.EMPTY,
                metrics=(WorkbenchMetric("Tracked", "0", ReadinessStatus.EMPTY),),
            )
        records: list[WorkbenchRecord] = []
        for hypothesis in sorted(active.hypotheses.values(), key=lambda item: item.id):
            asset = active.assets.get(hypothesis.target_asset_id)
            if asset is None:
                status = ReadinessStatus.BLOCKED
                detail = "target asset record is missing"
            elif hypothesis.required_authority > self.posture:
                status = ReadinessStatus.BLOCKED
                detail = "required authority exceeds current posture"
            elif asset.scope_classification.value != "in_scope":
                status = ReadinessStatus.BLOCKED
                detail = f"target scope is {asset.scope_classification.value}"
            else:
                status = ReadinessStatus.ATTENTION
                detail = "unproven theory; inspect assumptions and evidence needs"
            records.append(
                WorkbenchRecord(
                    id=hypothesis.id,
                    title=hypothesis.title,
                    status=status,
                    subtitle=hypothesis.status.value,
                    detail=detail,
                    references=tuple(hypothesis.supporting_observation_refs),
                    attributes=(
                        ("required_authority", hypothesis.required_authority.name),
                        ("target_asset_id", hypothesis.target_asset_id),
                        ("estimated_requests", str(hypothesis.estimated_request_cost)),
                        ("estimated_minutes", str(hypothesis.estimated_time_minutes)),
                        ("revision", str(hypothesis.revision)),
                        ("finding_ref", hypothesis.finding_ref or "none"),
                        ("lesson_ref", hypothesis.lesson_ref or "none"),
                    ),
                )
            )
        blocked = sum(item.status is ReadinessStatus.BLOCKED for item in records)
        return WorkbenchSection(
            "hypotheses",
            "Hypotheses",
            ReadinessStatus.BLOCKED if blocked else ReadinessStatus.ATTENTION,
            metrics=(
                WorkbenchMetric("Tracked", str(len(records)), ReadinessStatus.READY),
                WorkbenchMetric(
                    "Blocked",
                    str(blocked),
                    ReadinessStatus.BLOCKED if blocked else ReadinessStatus.READY,
                ),
            ),
            records=tuple(records),
            note="Every item remains unproven and carries no execution authority.",
        )

    def _learning_section(
        self, now: datetime, errors: list[str]
    ) -> tuple[WorkbenchSection, str | None]:
        if self.mastery is None:
            return (
                WorkbenchSection(
                    "learning",
                    "Learning",
                    ReadinessStatus.UNKNOWN,
                    metrics=(
                        WorkbenchMetric(
                            "Mastery state",
                            "unknown",
                            ReadinessStatus.UNKNOWN,
                            "no private mastery store configured",
                        ),
                    ),
                    note="The catalogue is available, but personal mastery is not measured.",
                ),
                None,
            )
        try:
            assessments = self.mastery.assessments()
            recommendation = GuidedLearningPlanner(self.catalogue).recommend(
                assessments, today=now.date()
            )
            persisted = self.journeys.journeys() if self.journeys is not None else ()
            active = sorted(
                (item for item in persisted if item.status is JourneyStatus.ACTIVE),
                key=lambda item: (item.updated_at, item.id),
                reverse=True,
            )
            active_journey = active[0] if active else None
            records: list[WorkbenchRecord] = [
                WorkbenchRecord(
                    id=f"recommendation:{recommendation.card_id}:{recommendation.dimension.value}",
                    title=recommendation.card_name,
                    status=ReadinessStatus.ATTENTION,
                    subtitle=f"{recommendation.dimension.value} · {recommendation.mode.value}",
                    detail=recommendation.reason,
                    attributes=(
                        ("current_level", recommendation.current_level.name.lower()),
                        ("review_due", recommendation.review_due.isoformat() if recommendation.review_due else "none"),
                        ("mastery_credit_rule", "explicit human assessment only"),
                    ),
                )
            ]
            records.extend(
                WorkbenchRecord(
                    id=item.id,
                    title=self.catalogue.card(item.card_id).name,
                    status=(
                        ReadinessStatus.ATTENTION
                        if item.status is JourneyStatus.ACTIVE
                        else ReadinessStatus.READY
                    ),
                    subtitle=f"{item.dimension.value} · {item.status.value}",
                    detail=item.objective,
                    attributes=(
                        ("stage", item.current_stage.value),
                        ("revision", str(item.revision)),
                        ("awards_mastery", "false"),
                    ),
                )
                for item in persisted
            )
            return (
                WorkbenchSection(
                    "learning",
                    "Learning",
                    (
                        ReadinessStatus.ATTENTION
                        if self.journeys is None or active_journey is not None
                        else ReadinessStatus.READY
                    ),
                    metrics=(
                        WorkbenchMetric(
                            "Human assessments",
                            str(sum(item.credits_mastery for item in assessments)),
                            ReadinessStatus.READY,
                        ),
                        WorkbenchMetric(
                            "Active journeys",
                            str(len(active)),
                            ReadinessStatus.ATTENTION if active else ReadinessStatus.READY,
                        ),
                    ),
                    records=tuple(records),
                    note=(
                        "Journey persistence is not configured."
                        if self.journeys is None
                        else "Journey completion never awards mastery automatically."
                    ),
                ),
                active_journey.id if active_journey else None,
            )
        except Exception as exc:
            errors.append(f"learning: {exc}")
            return _section_error("learning", "Learning", exc), None

    def _evidence_section(self) -> WorkbenchSection:
        if self.findings is None:
            return WorkbenchSection(
                "evidence",
                "Evidence",
                ReadinessStatus.UNKNOWN,
                metrics=(
                    WorkbenchMetric(
                        "Findings",
                        "unknown",
                        ReadinessStatus.UNKNOWN,
                        "no finding source configured",
                    ),
                ),
            )
        if self.evidence is None:
            return WorkbenchSection(
                "evidence",
                "Evidence",
                ReadinessStatus.UNKNOWN,
                metrics=(
                    WorkbenchMetric(
                        "Artifacts",
                        "unknown",
                        ReadinessStatus.UNKNOWN,
                        "no evidence vault configured",
                    ),
                ),
            )
        if not self.findings:
            return WorkbenchSection(
                "evidence",
                "Evidence",
                ReadinessStatus.EMPTY,
                metrics=(WorkbenchMetric("Findings", "0", ReadinessStatus.EMPTY),),
            )
        records: list[WorkbenchRecord] = []
        artifact_count = exportable = 0
        any_problem = False
        for finding in self.findings:
            manifest = self.evidence.manifest(finding.id)
            problems = self.evidence.verify(finding.id)
            artifact_count += len(manifest.artifacts)
            exported = sum(item.is_exportable for item in manifest.artifacts)
            exportable += exported
            any_problem = any_problem or bool(problems)
            records.append(
                WorkbenchRecord(
                    id=finding.id,
                    title=finding.title,
                    status=(
                        ReadinessStatus.BLOCKED
                        if problems
                        else (
                            ReadinessStatus.READY
                            if manifest.artifacts and exported == len(manifest.artifacts)
                            else ReadinessStatus.ATTENTION
                        )
                    ),
                    subtitle=finding.state.value,
                    detail=(
                        "; ".join(problems)
                        if problems
                        else f"{exported}/{len(manifest.artifacts)} artifacts redacted and exportable"
                    ),
                    references=tuple(item.id for item in manifest.artifacts),
                    attributes=(
                        ("artifacts", str(len(manifest.artifacts))),
                        ("exportable", str(exported)),
                        ("integrity", "failed" if problems else "verified"),
                    ),
                )
            )
        return WorkbenchSection(
            "evidence",
            "Evidence",
            ReadinessStatus.BLOCKED if any_problem else ReadinessStatus.ATTENTION,
            metrics=(
                WorkbenchMetric("Artifacts", str(artifact_count), ReadinessStatus.READY),
                WorkbenchMetric(
                    "Exportable",
                    str(exportable),
                    ReadinessStatus.READY if exportable == artifact_count else ReadinessStatus.ATTENTION,
                ),
            ),
            records=tuple(records),
        )

    def _reports_section(self) -> WorkbenchSection:
        if self.findings is None:
            return WorkbenchSection(
                "reports",
                "Reports",
                ReadinessStatus.UNKNOWN,
                metrics=(
                    WorkbenchMetric(
                        "Findings",
                        "unknown",
                        ReadinessStatus.UNKNOWN,
                        "no finding source configured",
                    ),
                ),
            )
        if not self.findings:
            return WorkbenchSection(
                "reports",
                "Reports",
                ReadinessStatus.EMPTY,
                metrics=(WorkbenchMetric("Findings", "0", ReadinessStatus.EMPTY),),
            )
        records: list[WorkbenchRecord] = []
        ready = 0
        for finding in self.findings:
            unanswered = finding.unanswered_roles
            if finding.state is Taxonomy.REPORT_READY:
                ready += 1
                status = ReadinessStatus.ATTENTION
                detail = "report-ready; export and any submission remain human-owned"
            elif unanswered:
                status = ReadinessStatus.ATTENTION
                detail = f"missing claim roles: {', '.join(item.value for item in unanswered)}"
            else:
                status = ReadinessStatus.READY
                detail = "claim-evidence matrix is complete for the current lifecycle state"
            records.append(
                WorkbenchRecord(
                    id=finding.id,
                    title=finding.title,
                    status=status,
                    subtitle=finding.state.value,
                    detail=detail,
                    references=tuple(finding.evidence_refs),
                    attributes=(
                        ("proven_claims", str(len(finding.proven_claims))),
                        ("unanswered_roles", str(len(unanswered))),
                        ("submission_automated", "false"),
                    ),
                )
            )
        return WorkbenchSection(
            "reports",
            "Reports",
            ReadinessStatus.ATTENTION if ready else ReadinessStatus.READY,
            metrics=(
                WorkbenchMetric("Tracked", str(len(records)), ReadinessStatus.READY),
                WorkbenchMetric(
                    "Report-ready",
                    str(ready),
                    ReadinessStatus.ATTENTION if ready else ReadinessStatus.READY,
                ),
            ),
            records=tuple(records),
            note="The workbench exports drafts; it does not submit, contact, or disclose.",
        )

    def _approvals_section(
        self,
        active: WorkspaceSnapshot | None,
        now: datetime,
        errors: list[str],
    ) -> WorkbenchSection:
        if active is None:
            return WorkbenchSection(
                "approvals",
                "Approvals",
                ReadinessStatus.UNKNOWN,
                metrics=(
                    WorkbenchMetric(
                        "Requests",
                        "unknown",
                        ReadinessStatus.UNKNOWN,
                        "no readable active workspace",
                    ),
                ),
            )
        requests = sorted(active.action_requests.values(), key=lambda item: item.id)
        if not requests:
            return WorkbenchSection(
                "approvals",
                "Approvals",
                ReadinessStatus.EMPTY,
                metrics=(WorkbenchMetric("Requests", "0", ReadinessStatus.EMPTY),),
            )
        records: list[WorkbenchRecord] = []
        blocked = attention = 0
        for request in requests:
            asset = active.assets.get(request.target_asset_id)
            target = asset.canonical_identifier if asset else ""
            if request.approval_ref is None:
                status = ReadinessStatus.ATTENTION
                detail = "no approval reference is attached"
                attention += 1
                approval_source = "none"
            elif self.approvals is None:
                status = ReadinessStatus.UNKNOWN
                detail = "an approval reference exists but no approval provider is configured"
                approval_source = "unknown"
            else:
                try:
                    approval = self.approvals.lookup(request.approval_ref)
                except Exception as exc:
                    errors.append(f"approvals/{request.id}: {exc}")
                    approval = None
                    detail = str(exc)
                if approval is None:
                    status = ReadinessStatus.BLOCKED
                    detail = "approval reference could not be resolved"
                    approval_source = "missing"
                    blocked += 1
                elif not approval.granted:
                    status = ReadinessStatus.BLOCKED
                    detail = "operator denied the request"
                    approval_source = approval.source
                    blocked += 1
                elif approval.is_expired(now=now, max_age=DEFAULT_APPROVAL_MAX_AGE):
                    status = ReadinessStatus.BLOCKED
                    detail = "approval has expired"
                    approval_source = approval.source
                    blocked += 1
                elif not asset or not approval.covers(
                    action_type=request.action_type, target=target
                ):
                    status = ReadinessStatus.BLOCKED
                    detail = "approval binding does not match the exact action and target"
                    approval_source = approval.source
                    blocked += 1
                else:
                    status = ReadinessStatus.READY
                    detail = "bound approval is present; the gate must still evaluate at execution time"
                    approval_source = approval.source
            records.append(
                WorkbenchRecord(
                    id=request.id,
                    title=request.exact_action,
                    status=status,
                    subtitle=request.action_type,
                    detail=detail,
                    references=(
                        f"approval:{request.approval_ref}"
                        if request.approval_ref
                        else "approval:none",
                    ),
                    attributes=(
                        ("target_asset_id", request.target_asset_id),
                        ("required_authority", request.required_authority.name),
                        ("approval_source", approval_source),
                        ("executed", str(request.id in {r.request_id for r in active.action_receipts.values()}).lower()),
                    ),
                )
            )
        return WorkbenchSection(
            "approvals",
            "Approvals",
            (
                ReadinessStatus.BLOCKED
                if blocked
                else ReadinessStatus.ATTENTION
                if attention or self.approvals is None
                else ReadinessStatus.READY
            ),
            metrics=(
                WorkbenchMetric("Requests", str(len(requests)), ReadinessStatus.READY),
                WorkbenchMetric(
                    "Blocked",
                    str(blocked),
                    ReadinessStatus.BLOCKED if blocked else ReadinessStatus.READY,
                ),
            ),
            records=tuple(records),
        )

    def _capabilities_section(self) -> WorkbenchSection:
        records = tuple(
            WorkbenchRecord(
                id=item.id,
                title=item.label,
                status=_status_from_capability(item.status),
                subtitle=item.status.value,
                detail=item.detail,
                references=item.evidence_refs,
                attributes=(("boundary", item.boundary),),
            )
            for item in CAPABILITIES
        )
        return WorkbenchSection(
            "capabilities",
            "Capabilities",
            ReadinessStatus.ATTENTION,
            metrics=(
                WorkbenchMetric(
                    "Implemented",
                    str(sum(item.status is CapabilityStatus.LIVE for item in CAPABILITIES)),
                    ReadinessStatus.READY,
                ),
                WorkbenchMetric(
                    "Unavailable",
                    str(sum(item.status is CapabilityStatus.UNAVAILABLE for item in CAPABILITIES)),
                    ReadinessStatus.BLOCKED,
                    "explicitly unavailable means there is no shipped path",
                ),
            ),
            records=records,
            note="Capability status describes shipped code, not configured runtime health.",
        )

    def _overview_section(
        self, sources: tuple[WorkbenchSection, ...]
    ) -> WorkbenchSection:
        blocked = sum(item.status is ReadinessStatus.BLOCKED for item in sources)
        unknown = sum(item.status is ReadinessStatus.UNKNOWN for item in sources)
        if self.audit is None:
            audit_metric = WorkbenchMetric(
                "Audit chain",
                "unknown",
                ReadinessStatus.UNKNOWN,
                "no audit log configured",
            )
        else:
            intact = self.audit.is_valid()
            audit_metric = WorkbenchMetric(
                "Audit chain",
                "intact" if intact else "broken",
                ReadinessStatus.READY if intact else ReadinessStatus.BLOCKED,
            )
            if not intact:
                blocked += 1
        status = (
            ReadinessStatus.BLOCKED
            if blocked
            else ReadinessStatus.ATTENTION
            if unknown
            else ReadinessStatus.READY
        )
        return WorkbenchSection(
            "overview",
            "Overview",
            status,
            metrics=(
                WorkbenchMetric(
                    "Posture", self.posture.name, ReadinessStatus.READY
                ),
                WorkbenchMetric(
                    "Live targets",
                    "disabled",
                    ReadinessStatus.READY,
                    "the application service refuses posture above LOCAL_FIXTURE",
                ),
                audit_metric,
                WorkbenchMetric(
                    "Blocked sources",
                    str(blocked),
                    ReadinessStatus.BLOCKED if blocked else ReadinessStatus.READY,
                ),
                WorkbenchMetric(
                    "Unknown sources",
                    str(unknown),
                    ReadinessStatus.ATTENTION if unknown else ReadinessStatus.READY,
                ),
            ),
            note="UNKNOWN is unmeasured, not zero or healthy.",
        )

    def _context(
        self, active: WorkspaceSnapshot | None, journey_id: str | None
    ) -> WorkbenchContext:
        if active is None:
            return WorkbenchContext(learning_journey_id=journey_id)
        sessions = sorted(
            active.sessions.values(), key=lambda item: (item.created_at, item.id), reverse=True
        )
        session = next((item for item in sessions if item.status.value == "active"), None)
        if session is None and sessions:
            session = sessions[0]
        hypotheses = sorted(active.hypotheses.values(), key=lambda item: item.id)
        hypothesis = next(
            (item for item in hypotheses if item.status.value not in {"supported", "refuted"}),
            hypotheses[0] if hypotheses else None,
        )
        report_ready = next(
            (
                item
                for item in (self.findings or ())
                if item.state is Taxonomy.REPORT_READY
            ),
            None,
        )
        return WorkbenchContext(
            workspace_id=active.workspace.id,
            session_id=session.id if session else None,
            hypothesis_id=hypothesis.id if hypothesis else None,
            finding_id=report_ready.id if report_ready else None,
            learning_journey_id=journey_id,
        )

    def _next_action(
        self,
        sections: tuple[WorkbenchSection, ...],
        context: WorkbenchContext,
    ) -> NextAction:
        by_id = {section.id: section for section in sections}
        overview = by_id["overview"]
        audit = next(metric for metric in overview.metrics if metric.label == "Audit chain")
        if audit.status is ReadinessStatus.BLOCKED:
            return NextAction(
                "repair-audit",
                "Stop and investigate the audit chain",
                "The configured audit chain failed integrity verification.",
                "/settings/readiness",
                requires_human=True,
            )
        if by_id["research"].status is ReadinessStatus.BLOCKED:
            return NextAction(
                "repair-research",
                "Repair the research source",
                "At least one workspace failed closed and cannot be represented safely.",
                "/research",
                requires_human=True,
            )
        if self.research is None:
            return NextAction(
                "configure-research-root",
                "Configure a private research root",
                "Workspace state is currently unmeasured.",
                "/settings/storage",
                requires_human=True,
            )
        if context.learning_journey_id:
            return NextAction(
                "continue-learning-journey",
                "Continue the active learning journey",
                "A staged journey is already in progress and remains non-crediting until human assessment.",
                f"/learn/journeys/{context.learning_journey_id}",
            )
        if by_id["research"].status is ReadinessStatus.EMPTY:
            return NextAction(
                "create-workspace",
                "Create the first bounded workspace",
                "The private research store is configured but empty.",
                "/research/new",
                requires_human=True,
            )
        if context.hypothesis_id:
            return NextAction(
                "inspect-hypothesis",
                "Inspect the current unproven hypothesis",
                "Review scope, assumptions, evidence needs, and the experiment budget before any action intent.",
                f"/research/hypotheses/{context.hypothesis_id}",
            )
        if context.finding_id:
            return NextAction(
                "review-report-ready-finding",
                "Review the report-ready finding",
                "Export and any later submission remain explicit human decisions.",
                f"/reports/{context.finding_id}",
                requires_human=True,
            )
        recommendation = next(
            (
                record
                for record in by_id["learning"].records
                if record.id.startswith("recommendation:")
            ),
            None,
        )
        if recommendation:
            return NextAction(
                "start-learning-journey",
                "Start the recommended learning path",
                recommendation.detail,
                "/learn/today",
            )
        return NextAction(
            "inspect-readiness",
            "Inspect readiness",
            "No higher-priority safe action is available.",
            "/settings/readiness",
        )

    def handle(self, command: WorkbenchCommand) -> CommandResult:
        if command.operator_ref != self.operator_ref:
            return CommandResult(
                command.id,
                CommandDisposition.INVALID,
                "operator_mismatch",
                "the command operator does not match this local application session",
            )
        canonical = json.dumps(command.to_dict(), sort_keys=True, separators=(",", ":"))
        digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        prior = self._idempotency.get(command.idempotency_key)
        if prior is not None:
            prior_digest, prior_result = prior
            if prior_digest != digest:
                return CommandResult(
                    command.id,
                    CommandDisposition.CONFLICT,
                    "idempotency_conflict",
                    "the idempotency key was already used by a different command",
                )
            return prior_result

        try:
            if command.kind is CommandKind.SELECT_WORKSPACE:
                result = self._select_workspace(command)
            elif command.kind is CommandKind.START_LEARNING_JOURNEY:
                result = self._start_learning(command)
            elif command.kind is CommandKind.ADVANCE_LEARNING_JOURNEY:
                result = self._advance_learning(command)
            elif command.kind is CommandKind.ABANDON_LEARNING_JOURNEY:
                result = self._abandon_learning(command)
            elif command.kind is CommandKind.CREATE_HYPOTHESIS:
                result = self._create_hypothesis(command)
            elif command.kind is CommandKind.REVIEW_HYPOTHESIS_SCOPE:
                result = self._review_hypothesis_scope(command)
            elif command.kind is CommandKind.PLAN_EXPERIMENT:
                result = self._plan_experiment(command)
            elif command.kind is CommandKind.RECORD_MASTERY_ASSESSMENT:
                result = self._record_mastery_assessment(command)
            elif command.kind is CommandKind.EXPORT_REPORT:
                result = self._export_report(command)
            elif command.kind is CommandKind.REQUEST_ACTION:
                result = self._request_action_intent(command)
            else:
                result = CommandResult(
                    command.id,
                    CommandDisposition.REFUSED,
                    "handler_not_implemented",
                    f"{command.kind.value} is typed but has no application handler; no domain state changed",
                )
        except ResearchRevisionConflict as exc:
            result = CommandResult(
                command.id,
                CommandDisposition.CONFLICT,
                "revision_conflict",
                str(exc),
            )
        except ReportExportConflict as exc:
            result = CommandResult(
                command.id,
                CommandDisposition.CONFLICT,
                "record_exists",
                str(exc),
            )
        except Exception as exc:
            result = CommandResult(
                command.id,
                CommandDisposition.INVALID,
                "command_refused",
                str(exc),
            )
        self._idempotency[command.idempotency_key] = (digest, result)
        return result

    def _request_action_intent(self, command: WorkbenchCommand) -> CommandResult:
        if self.research is None:
            raise WorkbenchContractError("no private research store is configured")
        assert command.workspace_id is not None
        _require_command_fields(
            command,
            required={
                "action_type",
                "exact_action",
                "experiment_id",
                "expected_effects",
                "max_requests",
                "purpose",
                "target_asset_id",
            },
            optional={"technique"},
        )
        now = self.clock()
        issued = command.issued_at.astimezone(timezone.utc)
        current = now.astimezone(timezone.utc)
        if issued > current + timedelta(seconds=30):
            raise WorkbenchContractError("action intent command is future-dated")
        if current - issued > timedelta(minutes=10):
            raise WorkbenchContractError("action intent command is stale")
        action_type = _command_text(command, "action_type")
        experiment_id = _command_text(command, "experiment_id")
        target_asset_id = _command_text(command, "target_asset_id")
        exact_action = _command_text(command, "exact_action")
        assert action_type and experiment_id and target_asset_id and exact_action
        if not action_type.startswith("fixture."):
            raise WorkbenchContractError(
                "the current action intent accepts only fixture.* action types"
            )
        max_requests = _command_int(command, "max_requests")
        if max_requests <= 0:
            raise WorkbenchContractError("action intent max_requests must be positive")
        snapshot = self.research.snapshot(command.workspace_id)
        if command.id in snapshot.action_requests:
            return CommandResult(
                command.id,
                CommandDisposition.CONFLICT,
                "record_exists",
                f"action request {command.id!r} already exists",
                (f"action-request:{command.id}",),
            )
        try:
            experiment = snapshot.experiments[experiment_id]
            hypothesis = snapshot.hypotheses[experiment.hypothesis_id]
            asset = snapshot.assets[target_asset_id]
        except KeyError as exc:
            raise WorkbenchContractError(
                f"action intent references unknown server-held state {exc.args[0]!r}"
            ) from exc
        if target_asset_id != hypothesis.target_asset_id:
            raise WorkbenchContractError(
                "action intent target does not match the experiment hypothesis"
            )
        if asset.scope_classification is not ScopeClassification.IN_SCOPE:
            raise WorkbenchContractError(
                "action intent target is not recorded as in scope"
            )
        if exact_action not in experiment.ordered_actions:
            raise WorkbenchContractError(
                "action intent is not one of the server-held experiment actions"
            )
        if experiment.required_authority is not AuthorityLevel.LOCAL_FIXTURE:
            raise WorkbenchContractError(
                "the selected experiment is not limited to LOCAL_FIXTURE"
            )
        request = ActionRequest(
            id=command.id,
            workspace_id=snapshot.workspace.id,
            session_id=experiment.session_id,
            experiment_id=experiment.id,
            authority_ref=snapshot.workspace.authority_ref,
            action_type=action_type,
            exact_action=exact_action,
            target_asset_id=asset.id,
            identity_id=hypothesis.actor_identity_id,
            required_authority=experiment.required_authority,
            purpose=_command_text(command, "purpose") or "",
            technique=_command_text(command, "technique", optional=True),
            max_requests=max_requests,
            expected_effects=_command_effects(command, "expected_effects"),
            stop_conditions=experiment.stop_conditions,
            created_at=command.issued_at,
        )
        self.research.add_action_request(request, actor=self.operator_ref)
        return CommandResult(
            command.id,
            CommandDisposition.ACCEPTED,
            "action_intent_recorded",
            "the bounded LOCAL_FIXTURE action intent was recorded; no Gate decision, approval, receipt, or execution was created",
            (f"action-request:{request.id}", f"experiment:{experiment.id}"),
        )

    def _export_report(self, command: WorkbenchCommand) -> CommandResult:
        if self.findings is None or self.report_drafts is None:
            raise WorkbenchContractError("no server-held report source is configured")
        if self.evidence is None:
            raise WorkbenchContractError("no private evidence vault is configured")
        if self.report_export_writer is None:
            raise WorkbenchContractError("no private report export writer is configured")
        _require_command_fields(command, required={"export_id", "finding_id"})
        now = self.clock()
        issued = command.issued_at.astimezone(timezone.utc)
        current = now.astimezone(timezone.utc)
        if issued > current + timedelta(seconds=30):
            raise WorkbenchContractError("report export command is future-dated")
        if current - issued > timedelta(minutes=10):
            raise WorkbenchContractError("report export command is stale")
        finding_id = _command_text(command, "finding_id")
        export_id = _command_text(command, "export_id")
        assert finding_id is not None and export_id is not None
        finding = next(
            (item for item in self.findings if item.id == finding_id), None
        )
        if finding is None:
            raise WorkbenchContractError(f"unknown report finding {finding_id!r}")
        if finding.state is not Taxonomy.REPORT_READY:
            return CommandResult(
                command.id,
                CommandDisposition.REFUSED,
                "finding_not_report_ready",
                "only a report-ready finding can be exported",
                (f"finding:{finding_id}",),
            )
        draft = next(
            (item for item in self.report_drafts if item.finding_id == finding_id),
            None,
        )
        if draft is None:
            raise WorkbenchContractError(
                f"no server-held report draft exists for {finding_id!r}"
            )
        if draft.authority_ref != finding.authority_ref:
            raise WorkbenchContractError(
                "report draft authority does not match the finding"
            )
        quality = gate_f_report_quality(draft)
        if not quality.passed:
            return CommandResult(
                command.id,
                CommandDisposition.REFUSED,
                "report_quality_blocked",
                "; ".join(quality.reasons),
                (f"finding:{finding_id}",),
            )
        package = self.evidence.export_package(finding_id)
        available = {str(item["id"]) for item in package["artifacts"]}
        missing = sorted(set(draft.evidence_index) - available)
        if missing:
            raise WorkbenchContractError(
                f"report evidence is absent from the verified export package: {missing!r}"
            )
        receipt = self.report_export_writer.export(
            export_id=export_id,
            draft=draft,
            evidence_package=package,
            operator_ref=self.operator_ref,
            exported_at=now,
        )
        return CommandResult(
            command.id,
            CommandDisposition.ACCEPTED,
            "report_exported",
            f"private redacted report export {receipt.export_id!r} was written; no submission or contact occurred",
            (
                f"report-export:{receipt.export_id}",
                f"finding:{finding_id}",
                f"manifest-sha256:{receipt.manifest_sha256}",
            ),
        )

    def _record_mastery_assessment(
        self, command: WorkbenchCommand
    ) -> CommandResult:
        if self.mastery is None:
            raise WorkbenchContractError("no private mastery store is configured")
        _require_command_fields(
            command,
            required={
                "assessment_id",
                "card_id",
                "dimension",
                "level",
                "evidence_refs",
                "rationale",
                "review_due",
            },
        )
        now = self.clock()
        issued = command.issued_at.astimezone(timezone.utc)
        current = now.astimezone(timezone.utc)
        if issued > current + timedelta(seconds=30):
            raise WorkbenchContractError("mastery assessment command is future-dated")
        if current - issued > timedelta(minutes=10):
            raise WorkbenchContractError("mastery assessment command is stale")
        assessment_id = _command_text(command, "assessment_id")
        assert assessment_id is not None
        if any(item.id == assessment_id for item in self.mastery.assessments()):
            return CommandResult(
                command.id,
                CommandDisposition.CONFLICT,
                "record_exists",
                f"mastery assessment {assessment_id!r} already exists",
                (f"mastery-assessment:{assessment_id}",),
            )
        assessment = MasteryAssessment(
            id=assessment_id,
            card_id=_command_text(command, "card_id") or "",
            dimension=MasteryDimension(_command_text(command, "dimension") or ""),
            level=MasteryLevel.parse(_command_text(command, "level") or ""),
            assessor=self.operator_ref,
            assessor_kind=AssessorKind.HUMAN,
            evidence_refs=_command_texts(command, "evidence_refs"),
            rationale=_command_text(command, "rationale") or "",
            assessed_at=command.issued_at,
            review_due=date.fromisoformat(_command_text(command, "review_due") or ""),
        )
        self.mastery.record(assessment)
        return CommandResult(
            command.id,
            CommandDisposition.ACCEPTED,
            "mastery_assessment_recorded",
            "the operator-authored evidence-bound assessment was recorded; no lab, model, or journey awarded mastery",
            (f"mastery-assessment:{assessment.id}",),
        )

    def _select_workspace(self, command: WorkbenchCommand) -> CommandResult:
        if self.research is None:
            raise WorkbenchContractError("no private research store is configured")
        if command.workspace_id is None:
            raise WorkbenchContractError("select_workspace requires a workspace id")
        self.research.snapshot(command.workspace_id)
        return CommandResult(
            command.id,
            CommandDisposition.ACCEPTED,
            "workspace_selected",
            "the workspace is readable; selection is local UI context, not authority",
            (f"workspace:{command.workspace_id}",),
        )

    def _create_hypothesis(self, command: WorkbenchCommand) -> CommandResult:
        if self.research is None:
            raise WorkbenchContractError("no private research store is configured")
        if command.workspace_id is None:
            raise WorkbenchContractError("create_hypothesis requires a workspace id")
        snapshot = self.research.snapshot(command.workspace_id)
        hypothesis_id = _command_text(command, "hypothesis_id")
        assert hypothesis_id is not None
        if hypothesis_id in snapshot.hypotheses:
            return CommandResult(
                command.id,
                CommandDisposition.CONFLICT,
                "record_exists",
                f"hypothesis {hypothesis_id!r} already exists",
                (f"hypothesis:{hypothesis_id}",),
            )
        hypothesis = Hypothesis(
            id=hypothesis_id,
            workspace_id=snapshot.workspace.id,
            session_id=_command_text(command, "session_id") or "",
            authority_ref=snapshot.workspace.authority_ref,
            title=_command_text(command, "title") or "",
            preconditions=_command_texts(command, "preconditions"),
            actor_identity_id=_command_text(
                command, "actor_identity_id", optional=True
            ),
            action=_command_text(command, "action") or "",
            target_asset_id=_command_text(command, "target_asset_id") or "",
            consequence=_command_text(command, "consequence") or "",
            reasoning=_command_text(command, "reasoning") or "",
            supporting_observation_refs=_command_texts(
                command, "supporting_observation_refs", optional=True
            ),
            assumptions=_command_texts(command, "assumptions"),
            required_authority=command.requested_authority,
            expected_safe_behaviour=_command_text(
                command, "expected_safe_behaviour"
            )
            or "",
            expected_vulnerable_behaviour=_command_text(
                command, "expected_vulnerable_behaviour"
            )
            or "",
            falsifier=_command_text(command, "falsifier") or "",
            evidence_needs=_command_texts(command, "evidence_needs"),
            stop_conditions=_command_texts(command, "stop_conditions"),
            estimated_request_cost=_command_int(command, "estimated_request_cost"),
            estimated_time_minutes=_command_int(command, "estimated_time_minutes"),
            estimated_effects=_command_effects(command, "estimated_effects"),
            duplicate_risk=_command_text(command, "duplicate_risk") or "",
            learning_value=_command_text(command, "learning_value") or "",
        )
        self.research.add_hypothesis(hypothesis, actor=command.operator_ref)
        return CommandResult(
            command.id,
            CommandDisposition.ACCEPTED,
            "hypothesis_created",
            "the unproven hypothesis was recorded; no experiment ran and no claim was promoted",
            (f"hypothesis:{hypothesis.id}",),
        )

    def _review_hypothesis_scope(
        self, command: WorkbenchCommand
    ) -> CommandResult:
        if self.research is None:
            raise WorkbenchContractError("no private research store is configured")
        if command.workspace_id is None or command.expected_revision is None:
            raise WorkbenchContractError(
                "review_hypothesis_scope requires workspace and revision"
            )
        hypothesis_id = _command_text(command, "hypothesis_id")
        assert hypothesis_id is not None
        snapshot = self.research.snapshot(command.workspace_id)
        current = snapshot.hypotheses.get(hypothesis_id)
        if current is not None and current.revision != command.expected_revision:
            return CommandResult(
                command.id,
                CommandDisposition.CONFLICT,
                "revision_conflict",
                f"expected revision {command.expected_revision}, current {current.revision}",
                (f"hypothesis:{hypothesis_id}",),
            )
        reviewed = self.research.scope_hypothesis(
            command.workspace_id,
            hypothesis_id,
            actor=command.operator_ref,
            review_basis=_command_text(command, "review_basis") or "",
            expected_revision=command.expected_revision,
        )
        return CommandResult(
            command.id,
            CommandDisposition.ACCEPTED,
            "hypothesis_scope_reviewed",
            "human scope review was recorded against the existing authority; no authority was granted",
            (f"hypothesis:{reviewed.id}",),
        )

    def _plan_experiment(self, command: WorkbenchCommand) -> CommandResult:
        if self.research is None:
            raise WorkbenchContractError("no private research store is configured")
        if command.workspace_id is None or command.expected_revision is None:
            raise WorkbenchContractError("plan_experiment requires workspace and revision")
        snapshot = self.research.snapshot(command.workspace_id)
        hypothesis_id = _command_text(command, "hypothesis_id")
        assert hypothesis_id is not None
        hypothesis = snapshot.hypotheses.get(hypothesis_id)
        if hypothesis is None:
            raise WorkbenchContractError(f"no hypothesis {hypothesis_id!r}")
        if hypothesis.revision != command.expected_revision:
            return CommandResult(
                command.id,
                CommandDisposition.CONFLICT,
                "revision_conflict",
                f"expected revision {command.expected_revision}, current {hypothesis.revision}",
                (f"hypothesis:{hypothesis_id}",),
            )
        experiment_id = _command_text(command, "experiment_id")
        assert experiment_id is not None
        if experiment_id in snapshot.experiments:
            return CommandResult(
                command.id,
                CommandDisposition.CONFLICT,
                "record_exists",
                f"experiment {experiment_id!r} already exists",
                (f"experiment:{experiment_id}",),
            )
        experiment = ExperimentPlan(
            id=experiment_id,
            workspace_id=snapshot.workspace.id,
            session_id=hypothesis.session_id,
            hypothesis_id=hypothesis.id,
            authority_ref=snapshot.workspace.authority_ref,
            ordered_actions=_command_texts(command, "ordered_actions"),
            positive_controls=_command_texts(command, "positive_controls"),
            negative_controls=_command_texts(command, "negative_controls"),
            expected_outcomes=_command_texts(command, "expected_outcomes"),
            required_authority=hypothesis.required_authority,
            effect_budget=_command_effects(command, "effect_budget"),
            rollback_steps=_command_texts(command, "rollback_steps"),
            stop_conditions=_command_texts(command, "stop_conditions"),
            evidence_plan=_command_texts(command, "evidence_plan"),
        )
        planned, persisted = self.research.plan_experiment(
            experiment,
            actor=command.operator_ref,
            expected_hypothesis_revision=command.expected_revision,
        )
        return CommandResult(
            command.id,
            CommandDisposition.ACCEPTED,
            "experiment_planned",
            "the bounded experiment plan was recorded atomically; no action ran",
            (f"hypothesis:{planned.id}", f"experiment:{persisted.id}"),
        )

    def _start_learning(self, command: WorkbenchCommand) -> CommandResult:
        if self.mastery is None or self.journeys is None:
            raise WorkbenchContractError(
                "mastery and journey stores must both be configured"
            )
        journey_id = command.field("journey_id")
        if not isinstance(journey_id, str):
            raise WorkbenchContractError("start_learning_journey requires journey_id")
        card_id = command.field("card_id")
        dimension_value = command.field("dimension")
        today_value = command.field("today")
        objective = command.field("objective")
        recommendation = GuidedLearningPlanner(self.catalogue).recommend(
            self.mastery.assessments(),
            today=(
                date.fromisoformat(today_value)
                if isinstance(today_value, str)
                else command.issued_at.date()
            ),
            preferred_card_id=card_id if isinstance(card_id, str) else None,
            preferred_dimension=(
                MasteryDimension(dimension_value)
                if isinstance(dimension_value, str)
                else None
            ),
        )
        journey = start_learning_journey(
            recommendation,
            journey_id=journey_id,
            now=command.issued_at,
            objective=objective if isinstance(objective, str) else None,
        )
        self.journeys.save(journey)
        return CommandResult(
            command.id,
            CommandDisposition.ACCEPTED,
            "learning_journey_started",
            "the private journey was created; no fixture ran and no mastery was awarded",
            (f"learning-journey:{journey.id}",),
        )

    def _advance_learning(self, command: WorkbenchCommand) -> CommandResult:
        if self.mastery is None or self.journeys is None:
            raise WorkbenchContractError(
                "mastery and journey stores must both be configured"
            )
        journey_id = command.field("journey_id")
        if not isinstance(journey_id, str):
            raise WorkbenchContractError("advance_learning_journey requires journey_id")
        current = self.journeys.get(journey_id)
        if command.expected_revision is None:
            raise WorkbenchContractError("advancing a journey requires expected_revision")
        if current.revision != command.expected_revision:
            return CommandResult(
                command.id,
                CommandDisposition.CONFLICT,
                "revision_conflict",
                f"expected revision {command.expected_revision}, current {current.revision}",
                (f"learning-journey:{current.id}",),
            )
        assessments = self.mastery.assessments()
        assessment_id = command.field("assessment_id")
        assessment = next(
            (
                item
                for item in assessments
                if isinstance(assessment_id, str) and item.id == assessment_id
            ),
            None,
        )
        evidence_refs = command.field("evidence_refs", ())
        if not isinstance(evidence_refs, tuple):
            raise WorkbenchContractError("evidence_refs must be a tuple of strings")
        updated = advance_learning_journey(
            current,
            at=command.issued_at,
            fixture_receipt_ref=(
                command.field("fixture_receipt_ref")
                if isinstance(command.field("fixture_receipt_ref"), str)
                else None
            ),
            evidence_refs=evidence_refs,
            reflection=(
                command.field("reflection")
                if isinstance(command.field("reflection"), str)
                else None
            ),
            assessment=assessment,
            recorded_assessment_ids=tuple(item.id for item in assessments),
        )
        self.journeys.save(updated, expected_revision=current.revision)
        return CommandResult(
            command.id,
            CommandDisposition.ACCEPTED,
            "learning_journey_advanced",
            f"journey advanced to {updated.current_stage.value}; no mastery was awarded by the journey",
            (f"learning-journey:{updated.id}",),
        )

    def _abandon_learning(self, command: WorkbenchCommand) -> CommandResult:
        if self.journeys is None:
            raise WorkbenchContractError("no private journey store is configured")
        journey_id = command.field("journey_id")
        reason = command.field("reason")
        if not isinstance(journey_id, str) or not isinstance(reason, str):
            raise WorkbenchContractError(
                "abandon_learning_journey requires journey_id and reason"
            )
        current = self.journeys.get(journey_id)
        if command.expected_revision != current.revision:
            return CommandResult(
                command.id,
                CommandDisposition.CONFLICT,
                "revision_conflict",
                f"expected revision {command.expected_revision}, current {current.revision}",
                (f"learning-journey:{current.id}",),
            )
        updated = abandon_learning_journey(
            current, at=command.issued_at, reason=reason
        )
        self.journeys.save(updated, expected_revision=current.revision)
        return CommandResult(
            command.id,
            CommandDisposition.ACCEPTED,
            "learning_journey_abandoned",
            "journey stopped with an operator reason; no mastery was awarded",
            (f"learning-journey:{updated.id}",),
        )


__all__ = ["WorkbenchApplicationService"]
