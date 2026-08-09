"""Report drafts — structure enforced, content still the operator's.

A report is the artifact a programme actually reads, and most reports fail for
structural reasons rather than technical ones: a missing precondition, steps
that skip the state the reader needs, an impact paragraph that describes a
behaviour instead of a consequence, a severity with no reasoning attached.

This module makes the structure checkable. It does not write reports. It
cannot judge whether an impact claim is *true* — only whether one was made,
whether it cites evidence, and whether anything was left as a placeholder.

The draft deliberately separates ``severity_proposed`` from
``severity_rationale``. A severity without reasoning is a number someone hoped
for, and Gate F rejects it.
"""

# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 ChaseInTech

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from greytheory.provenance import Claim, Tag

PLACEHOLDER_PATTERN = re.compile(
    r"\b(tbd|tbc|todo|fixme|xxx|lorem ipsum|fill in|placeholder)\b", re.IGNORECASE
)
"""Markers that a section was started and never finished."""

ABSOLUTE_CLAIMS = (
    "all users",
    "every user",
    "any attacker",
    "complete takeover",
    "full compromise",
    "trivially",
    "instantly",
    "catastrophic",
    "unlimited",
)
"""Phrases that are usually true only in a narrower sense than written.

These produce warnings, never failures. Sometimes an attacker really can reach
every user — but the claim should be one the writer made deliberately, and
seeing it flagged is what makes that deliberate.
"""

REQUIRED_TEXT_SECTIONS = (
    "title",
    "summary",
    "affected_feature",
    "expected_result",
    "actual_result",
    "security_impact",
    "data_minimisation_statement",
    "remediation",
)

REQUIRED_LIST_SECTIONS = ("steps", "evidence_index", "claim_matrix")


@dataclass(frozen=True)
class ReportClaim:
    """One report assertion bound to provenance and exact evidence artifacts."""

    claim: Claim
    evidence_refs: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.evidence_refs or any(not item.strip() for item in self.evidence_refs):
            raise ValueError("every report claim requires an evidence reference")
        if self.claim.tag is Tag.CHECKED and not self.claim.check_ref:
            raise ValueError("a checked report claim requires its check receipt")

    def to_dict(self) -> dict[str, Any]:
        return {
            "claim": self.claim.to_dict(),
            "evidence_refs": list(self.evidence_refs),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ReportClaim:
        return cls(
            claim=Claim.from_dict(data["claim"]),
            evidence_refs=tuple(data.get("evidence_refs", ())),
        )


@dataclass
class ReportDraft:
    """A report in progress. Structure is enforced; prose is not."""

    finding_id: str
    authority_ref: str
    """Invariant I2 — the contract this was produced under, cited in the report
    so the programme can see the researcher read their rules."""

    title: str = ""
    programme: str = ""
    asset: str = ""
    summary: str = ""
    affected_feature: str = ""
    preconditions: list[str] = field(default_factory=list)
    steps: list[str] = field(default_factory=list)
    expected_result: str = ""
    actual_result: str = ""
    security_impact: str = ""
    evidence_index: list[str] = field(default_factory=list)
    claim_matrix: list[ReportClaim] = field(default_factory=list)
    data_minimisation_statement: str = ""
    severity_proposed: str = ""
    severity_framework: str = ""
    severity_rationale: str = ""
    remediation: str = ""
    unresolved_uncertainty: list[str] = field(default_factory=list)
    """What is still unknown. An empty list is a claim in itself, and usually
    a false one — most findings have a remaining question."""

    tested_at: str = ""
    researcher_accounts: list[str] = field(default_factory=list)

    def missing_sections(self) -> list[str]:
        missing = [
            name
            for name in REQUIRED_TEXT_SECTIONS
            if not str(getattr(self, name, "")).strip()
        ]
        missing.extend(
            name for name in REQUIRED_LIST_SECTIONS if not getattr(self, name, [])
        )
        return missing

    def placeholders(self) -> list[str]:
        """Sections still containing an unfinished marker."""
        found: list[str] = []
        for name in REQUIRED_TEXT_SECTIONS + ("severity_rationale",):
            value = str(getattr(self, name, ""))
            if PLACEHOLDER_PATTERN.search(value):
                found.append(name)
        for name in REQUIRED_LIST_SECTIONS + ("preconditions",):
            for index, item in enumerate(getattr(self, name, [])):
                if PLACEHOLDER_PATTERN.search(str(item)):
                    found.append(f"{name}[{index}]")
        return found

    def absolute_claims(self) -> list[str]:
        """Unqualified absolutes in the impact narrative. Warnings only."""
        haystack = f"{self.summary} {self.security_impact}".lower()
        return [phrase for phrase in ABSOLUTE_CLAIMS if phrase in haystack]

    def render(self) -> str:
        """Render to the markdown a programme actually receives."""
        def bullets(items: list[str], empty: str) -> str:
            return "\n".join(f"- {item}" for item in items) if items else empty

        def numbered(items: list[str]) -> str:
            return "\n".join(f"{i}. {step}" for i, step in enumerate(items, 1))

        return f"""# {self.title or "[untitled]"}

## Programme and asset
- Programme: {self.programme}
- In-scope asset: {self.asset}
- Scope contract: {self.authority_ref}
- Tested at: {self.tested_at}
- Researcher account(s): {", ".join(self.researcher_accounts) or "-"}

## Summary
{self.summary}

## Affected feature
{self.affected_feature}

## Preconditions
{bullets(self.preconditions, "- None beyond a standard account.")}

## Steps to reproduce
{numbered(self.steps)}

## Expected result
{self.expected_result}

## Actual result
{self.actual_result}

## Security impact
{self.security_impact}

## Evidence
{bullets(self.evidence_index, "- None attached.")}

## Claim provenance
{bullets([
    f"{item.claim.text} | provenance: {item.claim.tag.value} | "
    f"source: {item.claim.source} | check: {item.claim.check_ref or '-'} | "
    f"evidence: {', '.join(item.evidence_refs)}"
    for item in self.claim_matrix
], "- No claims linked.")}

## Data-minimisation statement
{self.data_minimisation_statement}

## Severity assessment
- Proposed severity: {self.severity_proposed}
- Framework: {self.severity_framework}
- Rationale: {self.severity_rationale}

## Suggested remediation
{self.remediation}

## Remaining uncertainty
{bullets(self.unresolved_uncertainty, "- None recorded.")}
"""

    def to_dict(self) -> dict[str, Any]:
        return {
            "finding_id": self.finding_id,
            "authority_ref": self.authority_ref,
            "title": self.title,
            "programme": self.programme,
            "asset": self.asset,
            "summary": self.summary,
            "affected_feature": self.affected_feature,
            "preconditions": list(self.preconditions),
            "steps": list(self.steps),
            "expected_result": self.expected_result,
            "actual_result": self.actual_result,
            "security_impact": self.security_impact,
            "evidence_index": list(self.evidence_index),
            "claim_matrix": [item.to_dict() for item in self.claim_matrix],
            "data_minimisation_statement": self.data_minimisation_statement,
            "severity_proposed": self.severity_proposed,
            "severity_framework": self.severity_framework,
            "severity_rationale": self.severity_rationale,
            "remediation": self.remediation,
            "unresolved_uncertainty": list(self.unresolved_uncertainty),
            "tested_at": self.tested_at,
            "researcher_accounts": list(self.researcher_accounts),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ReportDraft:
        values = dict(data)
        values["claim_matrix"] = [
            ReportClaim.from_dict(item) for item in data.get("claim_matrix", [])
        ]
        return cls(**values)


__all__ = [
    "ABSOLUTE_CLAIMS",
    "PLACEHOLDER_PATTERN",
    "REQUIRED_LIST_SECTIONS",
    "REQUIRED_TEXT_SECTIONS",
    "ReportClaim",
    "ReportDraft",
]
