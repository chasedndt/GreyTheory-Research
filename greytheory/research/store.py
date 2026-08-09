"""Local persistence and lifecycle enforcement for research workspaces.

The store is intentionally a small, inspectable JSON implementation while the
domain contracts stabilise.  Each workspace is written atomically, carries an
integrity digest, and may also emit the existing hash-chained audit records.
It contains no networking or execution code.
"""

# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 ChaseInTech

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping, TypeVar

from greytheory.audit import AuditLog
from greytheory.authority.gate import AuthorityLevel, DEFAULT_MAX_CONTRACT_AGE
from greytheory.authority.scope import ContractStatus, ScopeContract
from greytheory.evidence import find_repository_root
from greytheory.research.domain import (
    EXPERIMENT_TRANSITIONS,
    HYPOTHESIS_TRANSITIONS,
    ActionReceipt,
    ActionRequest,
    AssetRelationship,
    EffectBudget,
    ExperimentPlan,
    ExperimentStatus,
    Hypothesis,
    HypothesisStatus,
    Lesson,
    ResearchDomainError,
    ResearchIdentity,
    ResearchSession,
    ResearchWorkspace,
    SessionStatus,
    TargetAsset,
    WorkspaceStatus,
)

SCHEMA_VERSION = 1


class ResearchStoreError(ResearchDomainError):
    """Raised when a workspace mutation or persisted state is unsound."""


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def resolve_research_root(explicit: str | os.PathLike[str] | None = None) -> Path:
    if explicit is not None:
        return Path(explicit).expanduser()
    override = os.environ.get("GREYTHEORY_RESEARCH_ROOT")
    if override:
        return Path(override).expanduser()
    vault = os.environ.get("CHASEOS_VAULT_ROOT")
    if vault:
        return Path(vault).expanduser() / "07_LOGS" / "greytheory-research"
    if os.name == "nt":
        base = os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA")
        if base:
            return Path(base) / "GreyTheory" / "research"
        return Path.home() / "AppData" / "Local" / "GreyTheory" / "research"
    xdg = os.environ.get("XDG_DATA_HOME")
    base = Path(xdg) if xdg else Path.home() / ".local" / "share"
    return base / "greytheory" / "research"


def _canonical(data: Mapping[str, Any]) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


@dataclass(frozen=True)
class WorkspaceSnapshot:
    """One complete structured workspace at a point in time."""

    workspace: ResearchWorkspace
    assets: dict[str, TargetAsset]
    relationships: dict[str, AssetRelationship]
    identities: dict[str, ResearchIdentity]
    sessions: dict[str, ResearchSession]
    hypotheses: dict[str, Hypothesis]
    experiments: dict[str, ExperimentPlan]
    action_requests: dict[str, ActionRequest]
    action_receipts: dict[str, ActionReceipt]
    lessons: dict[str, Lesson]

    @classmethod
    def empty(cls, workspace: ResearchWorkspace) -> WorkspaceSnapshot:
        return cls(workspace, {}, {}, {}, {}, {}, {}, {}, {}, {})

    def to_dict(self) -> dict[str, Any]:
        def records(items: Mapping[str, Any]) -> list[dict[str, Any]]:
            return [items[key].to_dict() for key in sorted(items)]

        return {
            "schema_version": SCHEMA_VERSION,
            "workspace": self.workspace.to_dict(),
            "assets": records(self.assets),
            "relationships": records(self.relationships),
            "identities": records(self.identities),
            "sessions": records(self.sessions),
            "hypotheses": records(self.hypotheses),
            "experiments": records(self.experiments),
            "action_requests": records(self.action_requests),
            "action_receipts": records(self.action_receipts),
            "lessons": records(self.lessons),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> WorkspaceSnapshot:
        if data.get("schema_version") != SCHEMA_VERSION:
            raise ResearchStoreError(
                f"unsupported research schema version {data.get('schema_version')!r}"
            )

        def keyed(values: Any, factory: Callable[[Mapping[str, Any]], Any]) -> dict[str, Any]:
            result: dict[str, Any] = {}
            for value in values or ():
                record = factory(value)
                if record.id in result:
                    raise ResearchStoreError(f"duplicate persisted id {record.id!r}")
                result[record.id] = record
            return result

        return cls(
            workspace=ResearchWorkspace.from_dict(data["workspace"]),
            assets=keyed(data.get("assets"), TargetAsset.from_dict),
            relationships=keyed(
                data.get("relationships"), AssetRelationship.from_dict
            ),
            identities=keyed(data.get("identities"), ResearchIdentity.from_dict),
            sessions=keyed(data.get("sessions"), ResearchSession.from_dict),
            hypotheses=keyed(data.get("hypotheses"), Hypothesis.from_dict),
            experiments=keyed(data.get("experiments"), ExperimentPlan.from_dict),
            action_requests=keyed(
                data.get("action_requests"), ActionRequest.from_dict
            ),
            action_receipts=keyed(
                data.get("action_receipts"), ActionReceipt.from_dict
            ),
            lessons=keyed(data.get("lessons"), Lesson.from_dict),
        )


RecordT = TypeVar("RecordT")


class ResearchStore:
    """Manage complete local sessions through typed, referentially safe records."""

    def __init__(
        self,
        root: str | os.PathLike[str] | None = None,
        *,
        audit: AuditLog | None = None,
        clock: Callable[[], datetime] = _utcnow,
        allow_in_repository: bool = False,
    ) -> None:
        self.root = resolve_research_root(root).resolve()
        if find_repository_root(self.root) is not None and not allow_in_repository:
            raise ResearchStoreError(
                "research workspace data cannot live inside a git working tree; "
                "use a private local data root or explicitly allow only a "
                "throwaway fixture"
            )
        self.root.mkdir(parents=True, exist_ok=True)
        self.audit = audit
        self._clock = clock

    def _directory(self, workspace_id: str) -> Path:
        if not workspace_id or any(part in workspace_id for part in ("/", "\\", "..")):
            raise ResearchStoreError("workspace id is not safe for local storage")
        return self.root / workspace_id

    def _path(self, workspace_id: str) -> Path:
        return self._directory(workspace_id) / "workspace.json"

    def workspace_ids(self) -> list[str]:
        return sorted(
            path.parent.name for path in self.root.glob("*/workspace.json") if path.is_file()
        )

    def create_workspace(
        self, workspace: ResearchWorkspace, *, contract: ScopeContract, actor: str
    ) -> ResearchWorkspace:
        if self._path(workspace.id).exists():
            raise ResearchStoreError(f"workspace {workspace.id!r} already exists")
        if contract.status is not ContractStatus.VERIFIED or not contract.human_reviewed:
            raise ResearchStoreError(
                "a research workspace requires a human-reviewed, verified contract"
            )
        if contract.is_stale(now=self._clock(), max_age=DEFAULT_MAX_CONTRACT_AGE):
            raise ResearchStoreError("the workspace contract is stale and must be reviewed")
        if workspace.programme_id != contract.programme_id:
            raise ResearchStoreError("workspace programme does not match the contract")
        if workspace.contract_id != contract.id:
            raise ResearchStoreError("workspace contract id does not match the contract")
        if workspace.authority_ref != contract.fingerprint():
            raise ResearchStoreError("workspace authority does not match the contract")
        granted = AuthorityLevel.parse(contract.max_authority)
        if workspace.operating_posture > granted:
            raise ResearchStoreError("workspace posture exceeds the contract authority")
        snapshot = WorkspaceSnapshot.empty(workspace)
        self._write(snapshot)
        self._audit(
            actor=actor,
            action="research.workspace.create",
            authority_ref=workspace.authority_ref,
            detail={"workspace_id": workspace.id, "programme_id": workspace.programme_id},
        )
        return workspace

    def snapshot(self, workspace_id: str) -> WorkspaceSnapshot:
        path = self._path(workspace_id)
        if not path.exists():
            raise ResearchStoreError(f"no research workspace {workspace_id!r}")
        try:
            envelope = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ResearchStoreError(f"cannot read workspace {workspace_id!r}: {exc}") from exc
        digest = envelope.pop("integrity", None)
        expected = hashlib.sha256(_canonical(envelope).encode("utf-8")).hexdigest()
        if digest != expected:
            raise ResearchStoreError(
                f"workspace {workspace_id!r} failed its integrity check"
            )
        snapshot = WorkspaceSnapshot.from_dict(envelope)
        self._validate_snapshot(snapshot)
        return snapshot

    def add_asset(
        self,
        asset: TargetAsset,
        *,
        contract: ScopeContract,
        actor: str,
    ) -> TargetAsset:
        snapshot = self.snapshot(asset.workspace_id)
        self._check_record(snapshot, asset)
        self._unique(snapshot.assets, asset.id, "asset")
        if contract.fingerprint() != snapshot.workspace.authority_ref:
            raise ResearchStoreError("asset classification contract does not match workspace")
        classification = contract.classify(asset.canonical_identifier)
        if classification is not asset.scope_classification:
            raise ResearchStoreError(
                "asset scope classification does not match the bound contract"
            )
        if asset.discovered_from_id is not None and asset.discovered_from_id not in snapshot.assets:
            raise ResearchStoreError("discovery source asset does not exist")
        assets = {**snapshot.assets, asset.id: asset}
        self._commit(snapshot, actor, "research.asset.add", asset.id, assets=assets)
        return asset

    def add_relationship(
        self, relationship: AssetRelationship, *, actor: str
    ) -> AssetRelationship:
        snapshot = self.snapshot(relationship.workspace_id)
        self._check_record(snapshot, relationship)
        self._unique(snapshot.relationships, relationship.id, "relationship")
        for asset_id in (relationship.source_asset_id, relationship.target_asset_id):
            if asset_id not in snapshot.assets:
                raise ResearchStoreError(f"relationship asset {asset_id!r} does not exist")
        relationships = {**snapshot.relationships, relationship.id: relationship}
        # An edge is only recorded.  No TargetAsset classification is mutated here.
        self._commit(
            snapshot,
            actor,
            "research.relationship.add",
            relationship.id,
            relationships=relationships,
        )
        return relationship

    def add_identity(self, identity: ResearchIdentity, *, actor: str) -> ResearchIdentity:
        snapshot = self.snapshot(identity.workspace_id)
        self._check_record(snapshot, identity)
        self._unique(snapshot.identities, identity.id, "identity")
        if identity.programme_id != snapshot.workspace.programme_id:
            raise ResearchStoreError("identity programme does not match the workspace")
        identities = {**snapshot.identities, identity.id: identity}
        self._commit(
            snapshot, actor, "research.identity.add", identity.id, identities=identities
        )
        return identity

    def add_session(self, session: ResearchSession, *, actor: str) -> ResearchSession:
        snapshot = self.snapshot(session.workspace_id)
        self._check_record(snapshot, session)
        self._unique(snapshot.sessions, session.id, "session")
        if session.status is not SessionStatus.DRAFT:
            raise ResearchStoreError("a new session must begin in draft")
        if session.operating_posture > snapshot.workspace.operating_posture:
            raise ResearchStoreError("session posture exceeds the workspace posture")
        if session.request_budget > snapshot.workspace.request_budget:
            raise ResearchStoreError("session request budget exceeds the workspace budget")
        if session.time_budget_minutes > snapshot.workspace.time_budget_minutes:
            raise ResearchStoreError("session time budget exceeds the workspace budget")
        if not snapshot.workspace.effect_budget.allows(session.effect_budget):
            raise ResearchStoreError("session effect budget exceeds the workspace budget")
        missing = set(session.identity_ids) - set(snapshot.identities)
        if missing:
            raise ResearchStoreError(
                "session references unknown identities: " + ", ".join(sorted(missing))
            )
        sessions = {**snapshot.sessions, session.id: session}
        self._commit(snapshot, actor, "research.session.add", session.id, sessions=sessions)
        return session

    def start_session(
        self, workspace_id: str, session_id: str, *, actor: str
    ) -> ResearchSession:
        snapshot = self.snapshot(workspace_id)
        session = self._get(snapshot.sessions, session_id, "session")
        if session.status is not SessionStatus.DRAFT:
            raise ResearchStoreError("only a draft session can be started")
        now = self._clock()
        for identity_id in session.identity_ids:
            identity = snapshot.identities[identity_id]
            if identity.expires_at is not None and identity.expires_at <= now:
                raise ResearchStoreError(f"identity {identity_id!r} has expired")
        started = replace(session, status=SessionStatus.ACTIVE, started_at=now)
        sessions = {**snapshot.sessions, session_id: started}
        self._commit(snapshot, actor, "research.session.start", session_id, sessions=sessions)
        return started

    def add_hypothesis(self, hypothesis: Hypothesis, *, actor: str) -> Hypothesis:
        snapshot = self.snapshot(hypothesis.workspace_id)
        self._check_record(snapshot, hypothesis)
        self._unique(snapshot.hypotheses, hypothesis.id, "hypothesis")
        session = self._get(snapshot.sessions, hypothesis.session_id, "session")
        if session.status not in {SessionStatus.DRAFT, SessionStatus.ACTIVE}:
            raise ResearchStoreError("a closed session cannot accept a hypothesis")
        if hypothesis.target_asset_id not in snapshot.assets:
            raise ResearchStoreError("hypothesis target asset does not exist")
        if hypothesis.actor_identity_id is not None:
            if hypothesis.actor_identity_id not in session.identity_ids:
                raise ResearchStoreError("hypothesis actor is not assigned to the session")
        if hypothesis.required_authority > session.operating_posture:
            raise ResearchStoreError("hypothesis authority exceeds the session posture")
        if hypothesis.estimated_request_cost > session.request_budget:
            raise ResearchStoreError("hypothesis request estimate exceeds the session budget")
        if hypothesis.estimated_time_minutes > session.time_budget_minutes:
            raise ResearchStoreError("hypothesis time estimate exceeds the session budget")
        if not session.effect_budget.allows(hypothesis.estimated_effects):
            raise ResearchStoreError("hypothesis effect estimate exceeds the session budget")
        hypotheses = {**snapshot.hypotheses, hypothesis.id: hypothesis}
        self._commit(
            snapshot, actor, "research.hypothesis.add", hypothesis.id, hypotheses=hypotheses
        )
        return hypothesis

    def transition_hypothesis(
        self,
        workspace_id: str,
        hypothesis_id: str,
        to: HypothesisStatus,
        *,
        actor: str,
        result_summary: str = "",
        result_refs: tuple[str, ...] = (),
        finding_ref: str | None = None,
        lesson_ref: str | None = None,
    ) -> Hypothesis:
        snapshot = self.snapshot(workspace_id)
        hypothesis = self._get(snapshot.hypotheses, hypothesis_id, "hypothesis")
        if to not in HYPOTHESIS_TRANSITIONS[hypothesis.status]:
            raise ResearchStoreError(
                f"{hypothesis.status.value} -> {to.value} is not a hypothesis transition"
            )
        if to in {
            HypothesisStatus.SUPPORTED,
            HypothesisStatus.REFUTED,
            HypothesisStatus.INCONCLUSIVE,
        }:
            if not result_summary.strip() or not result_refs:
                raise ResearchStoreError(
                    f"{to.value} requires a result summary and evidence/observation references"
                )
        if to is HypothesisStatus.CONVERTED_TO_FINDING and not finding_ref:
            raise ResearchStoreError("finding conversion requires a finding reference")
        if to is HypothesisStatus.CONVERTED_TO_LESSON:
            if not lesson_ref or lesson_ref not in snapshot.lessons:
                raise ResearchStoreError("lesson conversion requires an existing lesson")
        updated = replace(
            hypothesis,
            status=to,
            result_summary=result_summary or hypothesis.result_summary,
            result_refs=result_refs or hypothesis.result_refs,
            finding_ref=finding_ref or hypothesis.finding_ref,
            lesson_ref=lesson_ref or hypothesis.lesson_ref,
        )
        hypotheses = {**snapshot.hypotheses, hypothesis_id: updated}
        self._commit(
            snapshot,
            actor,
            "research.hypothesis.transition",
            hypothesis_id,
            hypotheses=hypotheses,
            detail={"from": hypothesis.status.value, "to": to.value},
        )
        return updated

    def add_experiment(self, experiment: ExperimentPlan, *, actor: str) -> ExperimentPlan:
        snapshot = self.snapshot(experiment.workspace_id)
        self._check_record(snapshot, experiment)
        self._unique(snapshot.experiments, experiment.id, "experiment")
        hypothesis = self._get(snapshot.hypotheses, experiment.hypothesis_id, "hypothesis")
        if experiment.session_id != hypothesis.session_id:
            raise ResearchStoreError("experiment session does not match its hypothesis")
        session = snapshot.sessions[experiment.session_id]
        if experiment.required_authority > session.operating_posture:
            raise ResearchStoreError("experiment authority exceeds the session posture")
        if not session.effect_budget.allows(experiment.effect_budget):
            raise ResearchStoreError("experiment effect budget exceeds the session budget")
        experiments = {**snapshot.experiments, experiment.id: experiment}
        self._commit(
            snapshot, actor, "research.experiment.add", experiment.id, experiments=experiments
        )
        return experiment

    def transition_experiment(
        self,
        workspace_id: str,
        experiment_id: str,
        to: ExperimentStatus,
        *,
        actor: str,
        outcome_summary: str = "",
        result_refs: tuple[str, ...] = (),
    ) -> ExperimentPlan:
        snapshot = self.snapshot(workspace_id)
        experiment = self._get(snapshot.experiments, experiment_id, "experiment")
        if to not in EXPERIMENT_TRANSITIONS[experiment.status]:
            raise ResearchStoreError(
                f"{experiment.status.value} -> {to.value} is not an experiment transition"
            )
        session = snapshot.sessions[experiment.session_id]
        hypothesis = snapshot.hypotheses[experiment.hypothesis_id]
        if to is ExperimentStatus.READY and hypothesis.status is not HypothesisStatus.PLANNED:
            raise ResearchStoreError("an experiment is ready only after its hypothesis is planned")
        if to is ExperimentStatus.ACTIVE:
            if session.status is not SessionStatus.ACTIVE:
                raise ResearchStoreError("an experiment requires an active session")
            if hypothesis.status is not HypothesisStatus.PLANNED:
                raise ResearchStoreError("an experiment requires a planned hypothesis")
        if to in {ExperimentStatus.COMPLETED, ExperimentStatus.STOPPED}:
            if not outcome_summary.strip() or not result_refs:
                raise ResearchStoreError(
                    "a closed experiment requires an outcome summary and result references"
                )
        updated = replace(
            experiment,
            status=to,
            outcome_summary=outcome_summary or experiment.outcome_summary,
            result_refs=result_refs or experiment.result_refs,
        )
        experiments = {**snapshot.experiments, experiment_id: updated}
        self._commit(
            snapshot,
            actor,
            "research.experiment.transition",
            experiment_id,
            experiments=experiments,
            detail={"from": experiment.status.value, "to": to.value},
        )
        return updated

    def add_action_request(self, request: ActionRequest, *, actor: str) -> ActionRequest:
        snapshot = self.snapshot(request.workspace_id)
        self._check_record(snapshot, request)
        self._unique(snapshot.action_requests, request.id, "action request")
        experiment = self._get(snapshot.experiments, request.experiment_id, "experiment")
        session = snapshot.sessions[request.session_id]
        hypothesis = snapshot.hypotheses[experiment.hypothesis_id]
        if experiment.session_id != request.session_id:
            raise ResearchStoreError("action request session does not match the experiment")
        if session.status is not SessionStatus.ACTIVE:
            raise ResearchStoreError("action requests require an active session")
        if experiment.status is not ExperimentStatus.ACTIVE:
            raise ResearchStoreError("action requests require an active experiment")
        if hypothesis.status is not HypothesisStatus.TESTING:
            raise ResearchStoreError("action requests require a testing hypothesis")
        if request.target_asset_id not in snapshot.assets:
            raise ResearchStoreError("action request target asset does not exist")
        if request.identity_id is not None and request.identity_id not in session.identity_ids:
            raise ResearchStoreError("action identity is not assigned to the session")
        if request.required_authority > session.operating_posture:
            raise ResearchStoreError("action authority exceeds the session posture")
        if request.max_requests > session.request_budget:
            raise ResearchStoreError("action request count exceeds the session budget")
        if not experiment.effect_budget.allows(request.expected_effects):
            raise ResearchStoreError("action effects exceed the experiment budget")
        action_requests = {**snapshot.action_requests, request.id: request}
        self._commit(
            snapshot,
            actor,
            "research.action_request.add",
            request.id,
            action_requests=action_requests,
        )
        return request

    def record_action_receipt(
        self, receipt: ActionReceipt, *, actor: str
    ) -> ActionReceipt:
        snapshot = self.snapshot(receipt.workspace_id)
        self._check_record(snapshot, receipt)
        self._unique(snapshot.action_receipts, receipt.id, "action receipt")
        if any(item.request_id == receipt.request_id for item in snapshot.action_receipts.values()):
            raise ResearchStoreError("an action request already has an execution receipt")
        request = self._get(snapshot.action_requests, receipt.request_id, "action request")
        experiment = snapshot.experiments[request.experiment_id]
        session = snapshot.sessions[request.session_id]
        asset = snapshot.assets[request.target_asset_id]
        if session.status is not SessionStatus.ACTIVE:
            raise ResearchStoreError("a receipt cannot be recorded for a closed session")
        for field in (
            "workspace_id",
            "session_id",
            "authority_ref",
            "exact_action",
            "target_asset_id",
            "identity_id",
            "approval_ref",
        ):
            if getattr(receipt, field) != getattr(request, field):
                raise ResearchStoreError(f"receipt {field} does not match its request")
        if receipt.target_canonical_identifier != asset.canonical_identifier:
            raise ResearchStoreError("receipt canonical target does not match the asset")
        self._validate_gate_binding(receipt, request, asset)
        if receipt.request_count > request.max_requests:
            raise ResearchStoreError("receipt exceeds the action request count")
        if not request.expected_effects.allows(receipt.effects):
            raise ResearchStoreError("receipt effects exceed the action request budget")
        if session.started_at is None or receipt.started_at < session.started_at:
            raise ResearchStoreError("receipt predates the active research session")
        if receipt.stop_condition_fired is not None:
            known = set(request.stop_conditions) | set(experiment.stop_conditions)
            if receipt.stop_condition_fired not in known:
                raise ResearchStoreError("receipt names an unknown stop condition")
        if receipt.redirects and receipt.stop_condition_fired is None:
            raise ResearchStoreError("redirects must fire and record a stop condition")

        prior_receipts = [
            item
            for item in snapshot.action_receipts.values()
            if item.session_id == session.id
        ]
        request_total = sum(item.request_count for item in prior_receipts) + receipt.request_count
        if request_total > session.request_budget:
            raise ResearchStoreError("receipt would exceed the session request budget")
        session_effects = self._sum_effects(item.effects for item in prior_receipts).plus(
            receipt.effects
        )
        if not session.effect_budget.allows(session_effects):
            raise ResearchStoreError("receipt would exceed the session effect budget")
        all_receipts = list(snapshot.action_receipts.values())
        workspace_request_total = sum(item.request_count for item in all_receipts) + receipt.request_count
        if workspace_request_total > snapshot.workspace.request_budget:
            raise ResearchStoreError("receipt would exceed the workspace request budget")
        workspace_effects = self._sum_effects(item.effects for item in all_receipts).plus(
            receipt.effects
        )
        if not snapshot.workspace.effect_budget.allows(workspace_effects):
            raise ResearchStoreError("receipt would exceed the workspace effect budget")

        action_receipts = {**snapshot.action_receipts, receipt.id: receipt}
        self._commit(
            snapshot,
            actor,
            "research.action_receipt.record",
            receipt.id,
            action_receipts=action_receipts,
            detail={
                "request_id": receipt.request_id,
                "gate_decision_ref": receipt.gate_decision_ref,
                "request_count": receipt.request_count,
            },
        )
        return receipt

    def add_lesson(self, lesson: Lesson, *, actor: str) -> Lesson:
        snapshot = self.snapshot(lesson.workspace_id)
        self._check_record(snapshot, lesson)
        self._unique(snapshot.lessons, lesson.id, "lesson")
        self._get(snapshot.sessions, lesson.session_id, "session")
        if lesson.hypothesis_id is not None:
            hypothesis = self._get(snapshot.hypotheses, lesson.hypothesis_id, "hypothesis")
            if hypothesis.session_id != lesson.session_id:
                raise ResearchStoreError("lesson hypothesis belongs to another session")
        lessons = {**snapshot.lessons, lesson.id: lesson}
        self._commit(snapshot, actor, "research.lesson.add", lesson.id, lessons=lessons)
        return lesson

    def complete_session(
        self,
        workspace_id: str,
        session_id: str,
        *,
        actor: str,
        time_spent_minutes: int,
        outcome_summary: str,
        checked_evidence_refs: tuple[str, ...] = (),
    ) -> ResearchSession:
        snapshot = self.snapshot(workspace_id)
        session = self._get(snapshot.sessions, session_id, "session")
        if session.status is not SessionStatus.ACTIVE:
            raise ResearchStoreError("only an active session can be completed")
        if any(
            item.session_id == session_id and item.status is ExperimentStatus.ACTIVE
            for item in snapshot.experiments.values()
        ):
            raise ResearchStoreError("active experiments must be closed before the session")
        _summary = outcome_summary.strip()
        if not _summary:
            raise ResearchStoreError("session completion requires an outcome summary")
        if time_spent_minutes < 0 or time_spent_minutes > session.time_budget_minutes:
            raise ResearchStoreError("session time exceeds its declared budget")
        previous_time = sum(
            item.time_spent_minutes
            for item in snapshot.sessions.values()
            if item.id != session.id and item.status is SessionStatus.COMPLETED
        )
        if previous_time + time_spent_minutes > snapshot.workspace.time_budget_minutes:
            raise ResearchStoreError("session would exceed the workspace time budget")

        has_terminal_hypothesis = any(
            item.session_id == session_id
            and item.status in {HypothesisStatus.REFUTED, HypothesisStatus.INCONCLUSIVE}
            for item in snapshot.hypotheses.values()
        )
        has_lesson = any(item.session_id == session_id for item in snapshot.lessons.values())
        if not checked_evidence_refs and not has_terminal_hypothesis and not has_lesson:
            raise ResearchStoreError(
                "a completed session requires checked evidence, a refuted/inconclusive "
                "hypothesis, or a reusable lesson"
            )
        completed = replace(
            session,
            status=SessionStatus.COMPLETED,
            ended_at=self._clock(),
            time_spent_minutes=time_spent_minutes,
            checked_evidence_refs=tuple(checked_evidence_refs),
            outcome_summary=_summary,
        )
        sessions = {**snapshot.sessions, session_id: completed}
        self._commit(
            snapshot,
            actor,
            "research.session.complete",
            session_id,
            sessions=sessions,
            detail={
                "time_spent_minutes": time_spent_minutes,
                "checked_evidence_refs": list(checked_evidence_refs),
                "has_terminal_hypothesis": has_terminal_hypothesis,
                "has_lesson": has_lesson,
            },
        )
        return completed

    def archive_workspace(self, workspace_id: str, *, actor: str) -> ResearchWorkspace:
        snapshot = self.snapshot(workspace_id)
        if any(item.status is SessionStatus.ACTIVE for item in snapshot.sessions.values()):
            raise ResearchStoreError("a workspace with an active session cannot be archived")
        workspace = replace(snapshot.workspace, status=WorkspaceStatus.ARCHIVED)
        self._commit(
            snapshot,
            actor,
            "research.workspace.archive",
            workspace_id,
            workspace=workspace,
        )
        return workspace

    def verify(self, workspace_id: str) -> None:
        self.snapshot(workspace_id)
        if self.audit is not None:
            self.audit.verify()

    def _validate_snapshot(self, snapshot: WorkspaceSnapshot) -> None:
        workspace = snapshot.workspace
        collections = (
            snapshot.assets,
            snapshot.relationships,
            snapshot.identities,
            snapshot.sessions,
            snapshot.hypotheses,
            snapshot.experiments,
            snapshot.action_requests,
            snapshot.action_receipts,
            snapshot.lessons,
        )
        for collection in collections:
            for record in collection.values():
                self._check_record(snapshot, record)
        for asset in snapshot.assets.values():
            if asset.discovered_from_id and asset.discovered_from_id not in snapshot.assets:
                raise ResearchStoreError("persisted asset has an unknown discovery source")
        for relationship in snapshot.relationships.values():
            if relationship.source_asset_id not in snapshot.assets or relationship.target_asset_id not in snapshot.assets:
                raise ResearchStoreError("persisted relationship has an unknown asset")
        for identity in snapshot.identities.values():
            if identity.programme_id != workspace.programme_id:
                raise ResearchStoreError("persisted identity has the wrong programme")
        for session in snapshot.sessions.values():
            if not set(session.identity_ids).issubset(snapshot.identities):
                raise ResearchStoreError("persisted session has an unknown identity")
        for hypothesis in snapshot.hypotheses.values():
            if hypothesis.session_id not in snapshot.sessions:
                raise ResearchStoreError("persisted hypothesis has an unknown session")
            if hypothesis.target_asset_id not in snapshot.assets:
                raise ResearchStoreError("persisted hypothesis has an unknown target")
        for experiment in snapshot.experiments.values():
            if experiment.hypothesis_id not in snapshot.hypotheses:
                raise ResearchStoreError("persisted experiment has an unknown hypothesis")
            if experiment.session_id not in snapshot.sessions:
                raise ResearchStoreError("persisted experiment has an unknown session")
        for request in snapshot.action_requests.values():
            if request.experiment_id not in snapshot.experiments:
                raise ResearchStoreError("persisted action request has an unknown experiment")
            if request.target_asset_id not in snapshot.assets:
                raise ResearchStoreError("persisted action request has an unknown target")
        for receipt in snapshot.action_receipts.values():
            if receipt.request_id not in snapshot.action_requests:
                raise ResearchStoreError("persisted receipt has an unknown request")
        for lesson in snapshot.lessons.values():
            if lesson.session_id not in snapshot.sessions:
                raise ResearchStoreError("persisted lesson has an unknown session")

    def _check_record(self, snapshot: WorkspaceSnapshot, record: Any) -> None:
        if record.workspace_id != snapshot.workspace.id:
            raise ResearchStoreError("record belongs to a different workspace")
        if record.authority_ref != snapshot.workspace.authority_ref:
            raise ResearchStoreError("record authority does not match the workspace")

    @staticmethod
    def _unique(records: Mapping[str, Any], record_id: str, label: str) -> None:
        if record_id in records:
            raise ResearchStoreError(f"{label} {record_id!r} already exists")

    @staticmethod
    def _get(records: Mapping[str, RecordT], record_id: str, label: str) -> RecordT:
        try:
            return records[record_id]
        except KeyError as exc:
            raise ResearchStoreError(f"no {label} {record_id!r}") from exc

    @staticmethod
    def _sum_effects(effects: Any) -> EffectBudget:
        total = EffectBudget()
        for effect in effects:
            total = total.plus(effect)
        return total

    def _validate_gate_binding(
        self,
        receipt: ActionReceipt,
        request: ActionRequest,
        asset: TargetAsset,
    ) -> None:
        if self.audit is None:
            raise ResearchStoreError(
                "an action receipt requires the audit log that issued its gate decision"
            )
        self.audit.verify()
        prefix, separator, sequence = receipt.gate_decision_ref.partition(":")
        if prefix != "audit" or separator != ":" or not sequence.isdigit():
            raise ResearchStoreError("receipt gate decision reference is not an audit sequence")
        records = {record.seq: record for record in self.audit.records()}
        decision = records.get(int(sequence))
        if decision is None or decision.action != "gate.evaluate":
            raise ResearchStoreError("receipt gate decision does not exist in the audit log")
        if decision.authority_ref != receipt.authority_ref:
            raise ResearchStoreError("audited gate authority does not match the receipt")
        detail = decision.detail
        gate_request = detail.get("request", {})
        expected = {
            "asset": asset.canonical_identifier,
            "authority_level": request.required_authority.name,
            "technique": request.technique,
            "purpose": request.purpose,
            "action_type": request.action_type,
            "approval_id": request.approval_ref,
        }
        if detail.get("allowed") is not True:
            raise ResearchStoreError("receipt gate decision was not an allow")
        if any(gate_request.get(key) != value for key, value in expected.items()):
            raise ResearchStoreError("audited gate request does not match the action request")

    def _write(self, snapshot: WorkspaceSnapshot) -> None:
        payload = snapshot.to_dict()
        envelope = {**payload, "integrity": hashlib.sha256(_canonical(payload).encode("utf-8")).hexdigest()}
        directory = self._directory(snapshot.workspace.id)
        directory.mkdir(parents=True, exist_ok=True)
        path = self._path(snapshot.workspace.id)
        temporary = path.with_suffix(".json.tmp")
        temporary.write_text(
            json.dumps(envelope, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        os.replace(temporary, path)

    def _commit(
        self,
        snapshot: WorkspaceSnapshot,
        actor: str,
        action: str,
        record_id: str,
        *,
        detail: Mapping[str, Any] | None = None,
        **changes: Any,
    ) -> WorkspaceSnapshot:
        if snapshot.workspace.status is WorkspaceStatus.ARCHIVED:
            raise ResearchStoreError("an archived workspace is read-only")
        updated = replace(snapshot, **changes)
        self._validate_snapshot(updated)
        self._write(updated)
        self._audit(
            actor=actor,
            action=action,
            authority_ref=updated.workspace.authority_ref,
            detail={"workspace_id": updated.workspace.id, "record_id": record_id, **(detail or {})},
        )
        return updated

    def _audit(
        self,
        *,
        actor: str,
        action: str,
        authority_ref: str,
        detail: Mapping[str, Any],
    ) -> None:
        if self.audit is not None:
            self.audit.append(
                actor=actor,
                action=action,
                authority_ref=authority_ref,
                detail=dict(detail),
            )


__all__ = [
    "ResearchStore",
    "ResearchStoreError",
    "SCHEMA_VERSION",
    "WorkspaceSnapshot",
    "resolve_research_root",
]
