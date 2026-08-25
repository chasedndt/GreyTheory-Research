"""Offline claim-role assembly for the bounded two-account fixture.

This module does not execute the fixture. It only re-derives claims from raw
artifacts already held in the private evidence vault and from operator
attestations already persisted on the report case.
"""

# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 ChaseInTech

from __future__ import annotations

import json
from datetime import datetime
from typing import Callable

from greytheory.authority.scope import (
    ContractStatus,
    ScopeClassification,
    ScopeContract,
)
from greytheory.checks import ValidatorRegistry
from greytheory.claims import ClaimRole, RoleBinding, readiness_problems
from greytheory.evidence import EvidenceArtifact, EvidenceVault
from greytheory.findings import Finding
from greytheory.lab.two_account import OwnershipValidator
from greytheory.provenance import Claim, Tag
from greytheory.report import ReportClaim, ReportDraft
from greytheory.validation import Attestation, GateId
from greytheory.validators import (
    ContractCurrencyValidator,
    EvidenceIntegrityValidator,
    OwnershipBoundaryValidator,
    SyntheticTargetValidator,
)


class ClaimAssemblyError(ValueError):
    """Raised when stored state cannot support a sound fixture claim matrix."""


def _canonical_json(value: object) -> bytes:
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        + "\n"
    ).encode("utf-8")


def _one_artifact(
    artifacts: list[EvidenceArtifact], *, kind: str
) -> EvidenceArtifact:
    matches = [item for item in artifacts if item.kind == kind]
    if len(matches) != 1:
        raise ClaimAssemblyError(
            f"local fixture claim assembly requires exactly one {kind!r} "
            f"artifact; found {len(matches)}"
        )
    return matches[0]


def _attestation(
    attestations: tuple[Attestation, ...], gate: GateId
) -> Attestation:
    matches = [item for item in attestations if item.gate is gate]
    if len(matches) != 1:
        raise ClaimAssemblyError(
            f"local fixture claim assembly requires one {gate.value} attestation"
        )
    return matches[0]


def assemble_two_account_fixture_claims(
    finding: Finding,
    draft: ReportDraft,
    *,
    vault: EvidenceVault,
    contract: ScopeContract,
    attestations: tuple[Attestation, ...],
    operator: str,
    reproduction_uncertainty: str,
    impact_uncertainty: str,
    clock: Callable[[], datetime],
) -> tuple[Finding, ReportDraft]:
    """Build all seven roles without performing another fixture action."""
    if not finding.target.startswith("fixture://two-account/"):
        raise ClaimAssemblyError(
            "two-account claim assembly is limited to the exact local fixture"
        )
    if draft.finding_id != finding.id or draft.authority_ref != finding.authority_ref:
        raise ClaimAssemblyError("finding and draft authority bindings do not match")
    if contract.status is not ContractStatus.VERIFIED or not contract.human_reviewed:
        raise ClaimAssemblyError("claim assembly requires a reviewed current contract")
    if contract.classify(finding.target) is not ScopeClassification.IN_SCOPE:
        raise ClaimAssemblyError("the local fixture target is not currently in scope")
    if vault.verify(finding.id):
        raise ClaimAssemblyError("claim assembly requires intact private evidence")

    manifest = vault.manifest(finding.id)
    if not manifest.artifacts:
        raise ClaimAssemblyError("claim assembly requires stored private evidence")
    if any(item.authority_ref != finding.authority_ref for item in manifest.artifacts):
        raise ClaimAssemblyError("evidence authority does not match the finding")
    response_artifact = _one_artifact(
        manifest.artifacts, kind="local_request_response"
    )
    ownership_artifact = _one_artifact(
        manifest.artifacts, kind="ownership_manifest"
    )
    response = vault.read_raw(finding.id, response_artifact.id)
    ownership = vault.read_raw(finding.id, ownership_artifact.id)

    registry = ValidatorRegistry(clock=clock)
    for validator_type in (
        OwnershipValidator,
        OwnershipBoundaryValidator,
        SyntheticTargetValidator,
        ContractCurrencyValidator,
        EvidenceIntegrityValidator,
    ):
        registry.register(validator_type())

    def checked(
        role: ClaimRole, validator_id: str, inputs: tuple[bytes, ...]
    ) -> RoleBinding:
        receipt = registry.run(
            validator_id,
            inputs=inputs,
            authority_ref=finding.authority_ref,
        )
        if not receipt.successful:
            raise ClaimAssemblyError(
                f"{role.value} validator returned {receipt.actual_outcome!r}"
            )
        claim = registry.promote(
            Claim(receipt.exact_assertion, Tag.INFERRED, f"fixture:{role.value}"),
            receipt,
        )
        return RoleBinding(role=role, claim=claim, receipt=receipt)

    recorded = {
        artifact.id: artifact.raw_sha256 for artifact in manifest.artifacts
    }
    current_contract = {
        "authority_ref": contract.fingerprint(),
        "status": contract.status.value,
    }
    checked_bindings = (
        checked(
            ClaimRole.BEHAVIOUR,
            OwnershipValidator.validator_id,
            (response, ownership),
        ),
        checked(
            ClaimRole.BOUNDARY,
            OwnershipBoundaryValidator.validator_id,
            (response, ownership),
        ),
        checked(
            ClaimRole.TARGET,
            SyntheticTargetValidator.validator_id,
            (response, ownership),
        ),
        checked(
            ClaimRole.SCOPE,
            ContractCurrencyValidator.validator_id,
            (
                _canonical_json({"authority_ref": finding.authority_ref}),
                _canonical_json(current_contract),
            ),
        ),
        checked(
            ClaimRole.EVIDENCE_INTEGRITY,
            EvidenceIntegrityValidator.validator_id,
            (_canonical_json(recorded), _canonical_json(recorded)),
        ),
    )

    reproduction = _attestation(attestations, GateId.B_REPRODUCIBILITY)
    impact = _attestation(attestations, GateId.C_IMPACT)
    judgement_bindings = (
        RoleBinding(
            role=ClaimRole.REPRODUCTION,
            claim=Claim(
                reproduction.statement,
                Tag.OBSERVED,
                f"operator:{operator}",
            ),
            uncertainty=reproduction_uncertainty,
        ),
        RoleBinding(
            role=ClaimRole.IMPACT,
            claim=Claim(impact.statement, Tag.INFERRED, f"operator:{operator}"),
            uncertainty=impact_uncertainty,
        ),
    )
    assembled = Finding.from_dict(finding.to_dict())
    for binding in (*checked_bindings, *judgement_bindings):
        assembled.bind_role(binding)
    problems = readiness_problems(assembled.role_bindings)
    if problems:
        raise ClaimAssemblyError("claim matrix is incomplete: " + "; ".join(problems))

    evidence_ids = tuple(item.id for item in manifest.artifacts)
    role_refs: dict[ClaimRole, tuple[str, ...]] = {
        ClaimRole.BEHAVIOUR: (response_artifact.id, ownership_artifact.id),
        ClaimRole.BOUNDARY: (response_artifact.id, ownership_artifact.id),
        ClaimRole.TARGET: (response_artifact.id, ownership_artifact.id),
        ClaimRole.SCOPE: evidence_ids,
        ClaimRole.EVIDENCE_INTEGRITY: evidence_ids,
        ClaimRole.REPRODUCTION: tuple(reproduction.evidence_refs),
        ClaimRole.IMPACT: tuple(impact.evidence_refs),
    }
    revised_draft = ReportDraft.from_dict(draft.to_dict())
    by_role = {item.role: item for item in assembled.role_bindings}
    revised_draft.claim_matrix = [
        ReportClaim(by_role[role].claim, role_refs[role]) for role in ClaimRole
    ]
    revised_draft.evidence_index = list(
        dict.fromkeys((*revised_draft.evidence_index, *evidence_ids))
    )
    return assembled, revised_draft


__all__ = [
    "ClaimAssemblyError",
    "assemble_two_account_fixture_claims",
]
