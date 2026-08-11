"""Data classes, trust labels and model roles.

Three separate questions get confused whenever an LLM is wired into a security
tool, so they are three separate types here:

**How sensitive is this?** — :class:`DataClass`. Governs whether a fragment may
leave the machine at all.

**Who wrote it?** — :class:`TrustLabel`. A programme page and a target response
are both text; only one of them was written by someone with an interest in
what this system does next.

**What is the model allowed to do with it?** — :class:`ModelRole`. A role that
may draft a report is not thereby a role that may decide a claim is proven.

Collapsing any two of these produces the failure the whole project is built
against: a target's response is treated as instruction, or a sensitive capture
is sent to a remote provider because it happened to be in the prompt.
"""

# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 ChaseInTech

from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum, Enum


class DataClass(IntEnum):
    """Ordered by sensitivity. A provider is approved up to a maximum."""

    PUBLIC = 0
    """Published programme rules, advisories, documentation."""

    PROGRAMME_SENSITIVE = 1
    """Private programme notes, unpublished scope, triage correspondence."""

    TARGET_SENSITIVE = 2
    """Redacted responses, architecture detail, endpoint maps."""

    RAW_RESTRICTED = 3
    """Tokens, credentials, personal data, raw captures. Never sent remotely."""

    @classmethod
    def parse(cls, name: str) -> DataClass:
        try:
            return cls[str(name).strip().upper()]
        except KeyError:
            return cls.RAW_RESTRICTED  # unknown is most restrictive, per I3


class TrustLabel(str, Enum):
    """Who authored a fragment, from the system's point of view."""

    OPERATOR = "operator"
    """The researcher, or this system's own records."""

    PUBLISHED = "published"
    """A programme or vendor policy the operator chose to trust as a source."""

    UNTRUSTED = "untrusted"
    """Target-controlled: responses, page content, uploaded files, tool output.

    Never instruction. A fragment carrying this label is content the model is
    reasoning *about*, and the gateway records its presence so a surprising
    output can be traced back to it.
    """


@dataclass(frozen=True)
class ProviderPolicy:
    """What one provider is permitted to receive.

    ``local`` is the field that matters. A local provider may be approved for
    ``RAW_RESTRICTED`` because nothing leaves the machine; a remote one may
    not be, whatever else is configured.
    """

    provider_id: str
    local: bool
    max_data_class: DataClass
    approved_by: str = ""
    note: str = ""

    def __post_init__(self) -> None:
        if not self.local and self.max_data_class >= DataClass.RAW_RESTRICTED:
            raise PolicyError(
                f"provider {self.provider_id!r} is remote and cannot be approved "
                "for RAW_RESTRICTED; raw captures and credentials do not leave "
                "the machine"
            )
        if self.max_data_class >= DataClass.TARGET_SENSITIVE and not self.approved_by:
            raise PolicyError(
                f"provider {self.provider_id!r} is approved for "
                f"{self.max_data_class.name} and must name who approved it"
            )

    def admits(self, data_class: DataClass) -> bool:
        return data_class <= self.max_data_class


class PolicyError(Exception):
    """Raised when a policy or a routing decision would be unsound."""


class ModelRole(str, Enum):
    POLICY_ANALYST = "policy_analyst"
    CARTOGRAPHER = "cartographer"
    HYPOTHESIS_ANALYST = "hypothesis_analyst"
    EXPERIMENT_PLANNER = "experiment_planner"
    SCEPTICAL_CRITIC = "sceptical_critic"
    EVIDENCE_CURATOR = "evidence_curator"
    REPORT_DRAFTER = "report_drafter"
    TUTOR = "tutor"
    POSTMORTEM_ANALYST = "postmortem_analyst"


@dataclass(frozen=True)
class RoleContract:
    """What a role may produce, and the ceiling on what it may receive."""

    role: ModelRole
    may: tuple[str, ...]
    must_not: tuple[str, ...]
    max_data_class: DataClass
    requires_citations: bool = True
    """Whether every substantive statement must cite a supplied context id."""


ROLE_CONTRACTS: dict[ModelRole, RoleContract] = {
    ModelRole.POLICY_ANALYST: RoleContract(
        role=ModelRole.POLICY_ANALYST,
        may=("extract proposed rules", "name ambiguities", "cite source precedence"),
        must_not=("verify a contract", "resolve an ambiguity", "grant scope"),
        max_data_class=DataClass.PROGRAMME_SENSITIVE,
    ),
    ModelRole.CARTOGRAPHER: RoleContract(
        role=ModelRole.CARTOGRAPHER,
        may=("organise assets", "propose relationships"),
        must_not=("declare a derived asset in scope",),
        max_data_class=DataClass.TARGET_SENSITIVE,
    ),
    ModelRole.HYPOTHESIS_ANALYST: RoleContract(
        role=ModelRole.HYPOTHESIS_ANALYST,
        may=("propose theories", "state falsifiers", "estimate factors"),
        must_not=("call a theory a finding", "assign authority"),
        max_data_class=DataClass.TARGET_SENSITIVE,
    ),
    ModelRole.EXPERIMENT_PLANNER: RoleContract(
        role=ModelRole.EXPERIMENT_PLANNER,
        may=("design minimal tests", "state controls and stop conditions"),
        must_not=("execute", "request an action directly", "widen a budget"),
        max_data_class=DataClass.TARGET_SENSITIVE,
    ),
    ModelRole.SCEPTICAL_CRITIC: RoleContract(
        role=ModelRole.SCEPTICAL_CRITIC,
        may=("find assumptions", "offer counterexamples", "name missing proof"),
        must_not=("promote a claim", "mark a gate passed"),
        max_data_class=DataClass.TARGET_SENSITIVE,
    ),
    ModelRole.EVIDENCE_CURATOR: RoleContract(
        role=ModelRole.EVIDENCE_CURATOR,
        may=("link claims to artifacts", "summarise redacted evidence"),
        must_not=("modify raw evidence", "issue a check receipt"),
        max_data_class=DataClass.TARGET_SENSITIVE,
    ),
    ModelRole.REPORT_DRAFTER: RoleContract(
        role=ModelRole.REPORT_DRAFTER,
        may=("draft from supported claims", "propose wording"),
        must_not=("add uncited impact", "state severity as fact"),
        max_data_class=DataClass.TARGET_SENSITIVE,
    ),
    ModelRole.TUTOR: RoleContract(
        role=ModelRole.TUTOR,
        may=("explain concepts", "propose the next learning step"),
        must_not=("award mastery", "infer mastery from completion"),
        max_data_class=DataClass.PUBLIC,
        requires_citations=False,
    ),
    ModelRole.POSTMORTEM_ANALYST: RoleContract(
        role=ModelRole.POSTMORTEM_ANALYST,
        may=("extract lessons", "propose score changes"),
        must_not=("rewrite outcome history",),
        max_data_class=DataClass.TARGET_SENSITIVE,
    ),
}


def contract_for(role: ModelRole) -> RoleContract:
    return ROLE_CONTRACTS[role]


__all__ = [
    "DataClass",
    "ModelRole",
    "PolicyError",
    "ProviderPolicy",
    "ROLE_CONTRACTS",
    "RoleContract",
    "TrustLabel",
    "contract_for",
]
