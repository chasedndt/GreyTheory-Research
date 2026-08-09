"""Validation gates B-F — what has to be true before a finding may be sent.

Gate A (authority) is already enforced at the gate. Gate G (submission) is the
operator's and is not automatable. What sits between is this module.

The gates split into two kinds, and the split matters more than the gates:

**Deterministic** gates re-derive their answer from artifacts every time. Gate D
rehashes evidence off disk; Gate F re-reads the draft. Nobody can assert their
way past them.

**Attested** gates cannot be machine-decided — whether an impact is real, or
whether prior research was checked, is a judgement. So they demand a recorded
human statement naming what was actually done. An attested gate with no
attestation does not pass; it is simply *not assessed*, which is a different
and more honest state than failure.

An LLM can help draft an attestation. It cannot be the attester, because the
attestation is a claim about what a person did.

One rule reads oddly until you have been burned by it: Gate E **rejects** an
attestation claiming duplicate risk is eliminated. It cannot be. A researcher
who believes otherwise has stopped modelling the other researchers, and that
belief costs more than the duplicate would have.
"""

# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 ChaseInTech

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from greytheory.audit import AuditLog
from greytheory.evidence import EvidenceError, EvidenceVault
from greytheory.findings import Finding
from greytheory.report import ReportDraft

CERTAINTY_CLAIMS = (
    "not a duplicate",
    "no duplicate",
    "duplicate risk eliminated",
    "no chance of duplicate",
    "definitely unique",
    "certainly novel",
    "guaranteed original",
    "nobody else",
)
"""Phrases asserting a certainty that is not available to anyone."""


class GateId(str, Enum):
    B_REPRODUCIBILITY = "B_reproducibility"
    C_IMPACT = "C_impact"
    D_EVIDENCE = "D_evidence"
    E_DUPLICATE_RISK = "E_duplicate_risk"
    F_REPORT_QUALITY = "F_report_quality"


class GateStatus(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    NOT_ASSESSED = "not_assessed"
    """No attestation was supplied. Distinct from failure: nobody looked."""


class GateKind(str, Enum):
    DETERMINISTIC = "deterministic"
    ATTESTED = "attested"


@dataclass(frozen=True)
class Attestation:
    """A recorded statement by a person about what they did."""

    gate: GateId
    actor: str
    statement: str
    attested_at: datetime
    evidence_refs: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.actor.strip():
            raise ValueError("an attestation must name who made it")
        actor = self.actor.strip().lower()
        if any(marker in actor for marker in ("model", "llm", "assistant", "claude", "openai")):
            raise ValueError("a model may draft an attestation but cannot be its attester")
        if len(self.statement.strip()) < 20:
            raise ValueError(
                "an attestation must describe what was actually done; a few "
                "words is a checkbox, not a statement"
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "gate": self.gate.value,
            "actor": self.actor,
            "statement": self.statement,
            "attested_at": self.attested_at.isoformat(),
            "evidence_refs": list(self.evidence_refs),
        }


@dataclass(frozen=True)
class GateResult:
    gate: GateId
    status: GateStatus
    kind: GateKind
    reasons: list[str] = field(default_factory=list)
    """Why it did not pass. Empty on a pass."""

    warnings: list[str] = field(default_factory=list)
    """Worth a second look, but not blocking."""

    @property
    def passed(self) -> bool:
        return self.status is GateStatus.PASS

    def to_dict(self) -> dict[str, Any]:
        return {
            "gate": self.gate.value,
            "status": self.status.value,
            "kind": self.kind.value,
            "reasons": list(self.reasons),
            "warnings": list(self.warnings),
        }


@dataclass
class ValidationReport:
    finding_id: str
    results: list[GateResult]
    checked_at: datetime

    @property
    def submission_ready(self) -> bool:
        """Every gate passed. Gate G — whether to actually send — is separate."""
        return all(result.passed for result in self.results)

    @property
    def blocking(self) -> list[GateResult]:
        return [r for r in self.results if not r.passed]

    @property
    def warnings(self) -> list[str]:
        return [w for r in self.results for w in r.warnings]

    def to_dict(self) -> dict[str, Any]:
        return {
            "finding_id": self.finding_id,
            "checked_at": self.checked_at.isoformat(),
            "submission_ready": self.submission_ready,
            "results": [r.to_dict() for r in self.results],
        }


def _attestation_for(
    attestations: list[Attestation], gate: GateId
) -> Attestation | None:
    for attestation in attestations:
        if attestation.gate is gate:
            return attestation
    return None


def gate_b_reproducibility(
    finding: Finding, attestations: list[Attestation]
) -> GateResult:
    """Does it reproduce from a clean state, confirmed server-side?

    Attested, because only the operator knows whether the session was genuinely
    clean. But it also requires a ``checked`` claim: a reproduction nobody
    verified deterministically is a memory of a reproduction.
    """
    reasons: list[str] = []
    attestation = _attestation_for(attestations, GateId.B_REPRODUCIBILITY)

    if attestation is None:
        return GateResult(
            GateId.B_REPRODUCIBILITY,
            GateStatus.NOT_ASSESSED,
            GateKind.ATTESTED,
            ["no reproducibility attestation; nobody has stated it reproduces"],
        )

    if not finding.proven_claims:
        reasons.append(
            "no 'checked' claim on the finding; a reproduction that was never "
            "deterministically verified is not evidence of one"
        )

    warnings: list[str] = []
    if "clean" not in attestation.statement.lower():
        warnings.append(
            "the attestation does not mention a clean session; confirm the "
            "reproduction did not depend on leftover state"
        )

    status = GateStatus.FAIL if reasons else GateStatus.PASS
    return GateResult(
        GateId.B_REPRODUCIBILITY, status, GateKind.ATTESTED, reasons, warnings
    )


def gate_c_impact(finding: Finding, attestations: list[Attestation]) -> GateResult:
    """Is there a real security consequence, not just unusual behaviour?"""
    reasons: list[str] = []
    attestation = _attestation_for(attestations, GateId.C_IMPACT)

    if attestation is None:
        return GateResult(
            GateId.C_IMPACT,
            GateStatus.NOT_ASSESSED,
            GateKind.ATTESTED,
            ["no impact attestation; nobody has stated what the consequence is"],
        )

    if not finding.proven_claims:
        reasons.append(
            "impact rests entirely on observation or inference; at least one "
            "'checked' claim must support it"
        )

    warnings: list[str] = []
    properties = ("confidential", "integrity", "availability", "authoris", "authoriz")
    if not any(word in attestation.statement.lower() for word in properties):
        warnings.append(
            "the attestation does not name a security property "
            "(confidentiality, integrity, availability, authorisation)"
        )

    status = GateStatus.FAIL if reasons else GateStatus.PASS
    return GateResult(GateId.C_IMPACT, status, GateKind.ATTESTED, reasons, warnings)


def gate_d_evidence(finding: Finding, vault: EvidenceVault) -> GateResult:
    """Is the evidence complete, intact, and safe to send?

    Fully deterministic. It rehashes artifacts off disk rather than trusting
    the manifest, so a modified file fails here even though the manifest still
    says otherwise.
    """
    reasons: list[str] = []
    warnings: list[str] = []

    manifest = vault.manifest(finding.id)
    if not manifest.artifacts:
        return GateResult(
            GateId.D_EVIDENCE,
            GateStatus.FAIL,
            GateKind.DETERMINISTIC,
            ["no evidence held for this finding"],
        )

    problems = vault.verify(finding.id)
    reasons.extend(problems)

    unredacted = [a.id for a in manifest.artifacts if not a.is_exportable]
    if unredacted:
        reasons.append(
            f"{len(unredacted)} artifact(s) have no redacted counterpart and "
            f"cannot be sent: {', '.join(unredacted)}"
        )

    for artifact in manifest.artifacts:
        if not artifact.authority_ref:
            reasons.append(f"{artifact.id}: no authority reference (I2)")
        elif artifact.authority_ref != finding.authority_ref:
            warnings.append(
                f"{artifact.id}: produced under a different contract "
                f"({artifact.authority_ref[:12]}...) than the finding "
                f"({finding.authority_ref[:12]}...)"
            )
        if artifact.contains_sensitive_data:
            warnings.append(
                f"{artifact.id}: redacted copy is still marked as containing "
                "sensitive data"
            )

    if not reasons:
        # The export path is the real test of sendability.
        try:
            vault.export_package(finding.id)
        except EvidenceError as exc:
            reasons.append(str(exc))

    status = GateStatus.FAIL if reasons else GateStatus.PASS
    return GateResult(GateId.D_EVIDENCE, status, GateKind.DETERMINISTIC, reasons, warnings)


def gate_e_duplicate_risk(attestations: list[Attestation]) -> GateResult:
    """Was prior work checked — and is the residual risk stated honestly?"""
    attestation = _attestation_for(attestations, GateId.E_DUPLICATE_RISK)
    if attestation is None:
        return GateResult(
            GateId.E_DUPLICATE_RISK,
            GateStatus.NOT_ASSESSED,
            GateKind.ATTESTED,
            ["no duplicate-risk attestation; prior research has not been reviewed"],
        )

    statement = attestation.statement.lower()
    reasons = [
        f"the attestation claims a certainty that does not exist: {phrase!r}. "
        "Duplicate risk can be reduced and estimated, never eliminated."
        for phrase in CERTAINTY_CLAIMS
        if phrase in statement
    ]

    warnings: list[str] = []
    sources = ("disclos", "write-up", "writeup", "changelog", "advisor", "search", "cve")
    if not any(word in statement for word in sources):
        warnings.append(
            "the attestation does not say what was reviewed (public disclosures, "
            "changelogs, write-ups)"
        )

    status = GateStatus.FAIL if reasons else GateStatus.PASS
    return GateResult(
        GateId.E_DUPLICATE_RISK, status, GateKind.ATTESTED, reasons, warnings
    )


def gate_f_report_quality(draft: ReportDraft) -> GateResult:
    """Is the report complete enough for a triager to act on?

    Deterministic. It checks that sections exist and were finished, not that
    the prose is any good.
    """
    reasons: list[str] = []

    missing = draft.missing_sections()
    if missing:
        reasons.append(f"missing section(s): {', '.join(missing)}")

    placeholders = draft.placeholders()
    if placeholders:
        reasons.append(f"unfinished placeholder(s) in: {', '.join(placeholders)}")

    if len(draft.steps) < 2:
        reasons.append(
            "fewer than two reproduction steps; a triager cannot follow a "
            "single-line repro"
        )

    if draft.severity_proposed and not draft.severity_rationale.strip():
        reasons.append(
            "a severity is proposed with no rationale; severity without "
            "reasoning is a number someone hoped for"
        )

    if not draft.authority_ref:
        reasons.append("no authority reference on the draft (I2)")

    evidence_ids = set(draft.evidence_index)
    for index, item in enumerate(draft.claim_matrix):
        unknown = set(item.evidence_refs) - evidence_ids
        if unknown:
            reasons.append(
                f"claim_matrix[{index}] cites evidence absent from the evidence index: "
                + ", ".join(sorted(unknown))
            )

    warnings: list[str] = []
    absolutes = draft.absolute_claims()
    if absolutes:
        warnings.append(
            "unqualified absolute claim(s): "
            + ", ".join(repr(a) for a in absolutes)
            + " - confirm each is literally true"
        )
    if not draft.unresolved_uncertainty:
        warnings.append(
            "no remaining uncertainty recorded; most findings have an open "
            "question, and stating it builds credibility with triage"
        )

    status = GateStatus.FAIL if reasons else GateStatus.PASS
    return GateResult(
        GateId.F_REPORT_QUALITY, status, GateKind.DETERMINISTIC, reasons, warnings
    )


def validate(
    finding: Finding,
    *,
    vault: EvidenceVault,
    draft: ReportDraft,
    attestations: list[Attestation] | None = None,
    audit: AuditLog | None = None,
    now: datetime | None = None,
) -> ValidationReport:
    """Run gates B-F and report the result.

    Passing every gate does not submit anything. It means the finding is
    *eligible* for the operator's Gate G decision, which stays manual.
    """
    attestations = attestations or []
    report = ValidationReport(
        finding_id=finding.id,
        results=[
            gate_b_reproducibility(finding, attestations),
            gate_c_impact(finding, attestations),
            gate_d_evidence(finding, vault),
            gate_e_duplicate_risk(attestations),
            gate_f_report_quality(draft),
        ],
        checked_at=now or datetime.now(timezone.utc),
    )

    if audit is not None:
        audit.append(
            actor="validation",
            action="validation.run",
            authority_ref=finding.authority_ref,
            detail={
                "finding_id": finding.id,
                "submission_ready": report.submission_ready,
                "results": [r.to_dict() for r in report.results],
            },
        )
    return report


__all__ = [
    "Attestation",
    "CERTAINTY_CLAIMS",
    "GateId",
    "GateKind",
    "GateResult",
    "GateStatus",
    "ValidationReport",
    "gate_b_reproducibility",
    "gate_c_impact",
    "gate_d_evidence",
    "gate_e_duplicate_risk",
    "gate_f_report_quality",
    "validate",
]
