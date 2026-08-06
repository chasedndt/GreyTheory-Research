"""Plane 1 — the Authority Plane.

``scope`` defines what a contract *is*, ``compiler`` turns programme source
text into one, and ``gate`` is the only place execution is ever permitted.
"""

# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 ChaseInTech

from greytheory.authority.approvals import (
    Approval,
    ApprovalStore,
    ChaseOSApprovalStore,
    LocalApprovalStore,
)
from greytheory.authority.compiler import CompilationResult, compile_contract
from greytheory.authority.gate import AccessRequest, AuthorityLevel, Decision, Gate, Reason
from greytheory.authority.scope import (
    AssetPattern,
    ContractStatus,
    PatternType,
    ScopeClassification,
    ScopeContract,
)

__all__ = [
    "AccessRequest",
    "Approval",
    "ApprovalStore",
    "AssetPattern",
    "AuthorityLevel",
    "ChaseOSApprovalStore",
    "LocalApprovalStore",
    "CompilationResult",
    "ContractStatus",
    "Decision",
    "Gate",
    "PatternType",
    "Reason",
    "ScopeClassification",
    "ScopeContract",
    "compile_contract",
]
