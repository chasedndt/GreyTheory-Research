"""GreyTheory — a local-first Security Research Operating System.

This package implements the offline trust kernel. The Authority Plane remains
the root: nothing in the Signal or Judgement planes may execute except through
it.

The invariants enforced here are defined in `Docs/definition.md` section 3:

* **I1** provenance triple — every claim is ``observed``, ``checked`` or ``inferred``
* **I2** authority reference — every artifact names the authority it was produced under
* **I3** fail-closed — absence, staleness and ambiguity all resolve to denial
* **I5** no self-award — the system records programme outcomes, it never asserts them

There is no network code in this package, and none belongs here.
"""

# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 ChaseInTech

from greytheory.advisories import Advisory, AdvisorySet, Version
from greytheory.audit import AuditLog, AuditRecord, AuditVerificationError
from greytheory.authority.approvals import (
    Approval,
    ApprovalStore,
    ChaseOSApprovalStore,
    LocalApprovalStore,
)
from greytheory.authority.gate import AccessRequest, AuthorityLevel, Decision, Gate, Reason
from greytheory.authority.scope import (
    AssetPattern,
    ContractStatus,
    ScopeClassification,
    ScopeContract,
)
from greytheory.authority.sources import (
    BundleCompilationResult,
    BundleError,
    CaptureMode,
    DerivationKind,
    HumanResolution,
    ProgrammeSource,
    ProgrammeSourceBundle,
    ResolutionStatus,
    SourceDerivation,
    SourceKind,
    compile_source_bundle,
)
from greytheory.evidence import (
    EvidenceArtifact,
    EvidenceError,
    EvidenceVault,
    VaultLocationError,
)
from greytheory.findings import Finding, Taxonomy, TransitionError
from greytheory.provenance import Claim, ProvenanceError, Tag
from greytheory.ledger import (
    Expense,
    Forecast,
    InsufficientData,
    Ledger,
    LedgerError,
    Metrics,
    Payout,
    Session,
    SessionKind,
    TriageEvent,
    TriageOutcome,
)
from greytheory.learning import (
    AssessorKind,
    CardUpdateProposal,
    EvidenceRequirement,
    FixtureRunReceipt,
    HypothesisTemplate,
    LearningError,
    LearningStoreError,
    LocalTrainingFixture,
    MasteryAssessment,
    MasteryDimension,
    MasteryLevel,
    MasteryState,
    MasteryStore,
    SkillGraph,
    TrainingFixtureRunner,
    VulnerabilityCard,
    VulnerabilityCatalogue,
    load_builtin_catalogue,
)
from greytheory.hypothesis import (
    AssessmentSource,
    FactorAssessment,
    FactorDirection,
    FactorExplanation,
    FactorWeight,
    HypothesisRanker,
    HypothesisRankingError,
    HypothesisRankingInput,
    QueuePartition,
    RankedHypothesis,
    RankingFactor,
    RankingPolicy,
    ResearchQueue,
    conservative_local_policy,
    parse_ranking_inputs,
)
from greytheory.registry import (
    Attention,
    ContractVersion,
    ProgrammeRegistry,
    RegistryError,
    ScopeDiff,
)
from greytheory.report import ReportDraft
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
    WorkspaceSnapshot,
    WorkspaceStatus,
)
from greytheory.validation import (
    Attestation,
    GateId,
    GateResult,
    GateStatus,
    ValidationReport,
    validate,
)

__version__ = "0.1.0"

__all__ = [
    "Advisory",
    "AdvisorySet",
    "Version",
    "TriageOutcome",
    "TriageEvent",
    "SessionKind",
    "Session",
    "Payout",
    "Metrics",
    "LedgerError",
    "Ledger",
    "InsufficientData",
    "Forecast",
    "Expense",
    "AccessRequest",
    "Approval",
    "ApprovalStore",
    "AssetPattern",
    "Attestation",
    "Attention",
    "AuditLog",
    "AuditRecord",
    "AuditVerificationError",
    "AuthorityLevel",
    "BundleCompilationResult",
    "BundleError",
    "CaptureMode",
    "DerivationKind",
    "ChaseOSApprovalStore",
    "Claim",
    "ContractStatus",
    "ContractVersion",
    "Decision",
    "EvidenceArtifact",
    "EvidenceError",
    "EvidenceVault",
    "Finding",
    "Gate",
    "GateId",
    "GateResult",
    "GateStatus",
    "HumanResolution",
    "LocalApprovalStore",
    "ProgrammeRegistry",
    "ProgrammeSource",
    "ProgrammeSourceBundle",
    "ProvenanceError",
    "Reason",
    "RegistryError",
    "ReportDraft",
    "ResolutionStatus",
    "ScopeClassification",
    "ScopeContract",
    "ScopeDiff",
    "SourceKind",
    "SourceDerivation",
    "Tag",
    "Taxonomy",
    "TransitionError",
    "ValidationReport",
    "VaultLocationError",
    "__version__",
    "compile_source_bundle",
    "validate",
]

__all__.extend(
    [
        "ActionReceipt",
        "ActionRequest",
        "AssetKind",
        "AssetRelationship",
        "EffectBudget",
        "ExperimentPlan",
        "ExperimentStatus",
        "Hypothesis",
        "HypothesisStatus",
        "Lesson",
        "RelationshipKind",
        "ResearchDomainError",
        "ResearchIdentity",
        "ResearchSession",
        "ResearchStore",
        "ResearchStoreError",
        "ResearchWorkspace",
        "SessionStatus",
        "TargetAsset",
        "WorkspaceSnapshot",
        "WorkspaceStatus",
    ]
)

__all__.extend(
    [
        "AssessmentSource",
        "FactorAssessment",
        "FactorDirection",
        "FactorExplanation",
        "FactorWeight",
        "HypothesisRanker",
        "HypothesisRankingError",
        "HypothesisRankingInput",
        "QueuePartition",
        "RankedHypothesis",
        "RankingFactor",
        "RankingPolicy",
        "ResearchQueue",
        "conservative_local_policy",
        "parse_ranking_inputs",
    ]
)

__all__.extend(
    [
        "AssessorKind",
        "CardUpdateProposal",
        "EvidenceRequirement",
        "FixtureRunReceipt",
        "HypothesisTemplate",
        "LearningError",
        "LearningStoreError",
        "LocalTrainingFixture",
        "MasteryAssessment",
        "MasteryDimension",
        "MasteryLevel",
        "MasteryState",
        "MasteryStore",
        "SkillGraph",
        "TrainingFixtureRunner",
        "VulnerabilityCard",
        "VulnerabilityCatalogue",
        "load_builtin_catalogue",
    ]
)
