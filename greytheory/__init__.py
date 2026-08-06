"""GreyTheory AI — a proof-first security research control plane.

This package implements **Plane 1, the Authority Plane**: the root of the system.
Nothing in the Signal or Judgement planes may execute except through it.

The invariants enforced here are defined in `Docs/definition.md` section 3:

* **I1** provenance triple — every claim is ``observed``, ``checked`` or ``inferred``
* **I2** authority reference — every artifact names the authority it was produced under
* **I3** fail-closed — absence, staleness and ambiguity all resolve to denial
* **I5** no self-award — the system records programme outcomes, it never asserts them

There is no network code in this package, and none belongs here.
"""

# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 ChaseInTech

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
from greytheory.evidence import (
    EvidenceArtifact,
    EvidenceError,
    EvidenceVault,
    VaultLocationError,
)
from greytheory.findings import Finding, Taxonomy, TransitionError
from greytheory.provenance import Claim, ProvenanceError, Tag
from greytheory.registry import (
    Attention,
    ContractVersion,
    ProgrammeRegistry,
    RegistryError,
    ScopeDiff,
)
from greytheory.report import ReportDraft
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
    "LocalApprovalStore",
    "ProgrammeRegistry",
    "ProvenanceError",
    "Reason",
    "RegistryError",
    "ReportDraft",
    "ScopeClassification",
    "ScopeContract",
    "ScopeDiff",
    "Tag",
    "Taxonomy",
    "TransitionError",
    "ValidationReport",
    "VaultLocationError",
    "__version__",
    "validate",
]
