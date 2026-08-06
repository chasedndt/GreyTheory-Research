"""The gate. The only place execution is ever permitted.

Every check here resolves ambiguity toward denial (invariant I3), and every
decision — allow or deny — is written to the audit log before it is returned.
An allow that was not audited is indistinguishable from an allow that never
happened, so auditing is not optional and is not the caller's responsibility.

The posture ceiling deserves a note. It is a system-wide cap applied *on top of*
whatever a contract grants, so the current local-only operating posture is
enforced in code rather than remembered. A contract that legitimately grants
``AUTHENTICATED`` still cannot exercise it while the ceiling sits at
``LOCAL_FIXTURE``.
"""

# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 ChaseInTech

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Callable

from greytheory.audit import AuditLog
from greytheory.authority.approvals import (
    DEFAULT_APPROVAL_MAX_AGE,
    ApprovalStore,
)
from greytheory.authority.scope import (
    ContractStatus,
    ScopeClassification,
    ScopeContract,
)

DEFAULT_MAX_CONTRACT_AGE = timedelta(days=7)
"""How long a verified contract is trusted before it must be re-checked.
Programmes change their scope without announcing it."""


class AuthorityLevel(int, Enum):
    """Ordered. A request may never exceed what the contract and posture allow."""

    NONE = 0
    LOCAL_FIXTURE = 1
    """Local files and fixtures. No network."""

    PASSIVE_HTTP = 2
    """Unauthenticated reads of in-scope hosts."""

    AUTHENTICATED = 3
    """Requests using accounts the operator controls."""

    INTRUSIVE = 4
    """Anything that could materially affect a target. Always human-approved."""

    @classmethod
    def parse(cls, name: str) -> AuthorityLevel:
        try:
            return cls[name.strip().upper()]
        except KeyError:
            return cls.NONE  # unknown means none, per I3


class Reason(str, Enum):
    ALLOWED = "allowed"
    NO_CONTRACT = "no_contract"
    CONTRACT_NOT_VERIFIED = "contract_not_verified"
    CONTRACT_BLOCKED = "contract_blocked"
    CONTRACT_STALE = "contract_stale"
    ASSET_OUT_OF_SCOPE = "asset_out_of_scope"
    ASSET_UNRESOLVED = "asset_unresolved"
    DERIVED_ASSET_NOT_INHERITED = "derived_asset_not_inherited"
    AUTHORITY_LEVEL_EXCEEDED = "authority_level_exceeded"
    POSTURE_CEILING_EXCEEDED = "posture_ceiling_exceeded"
    TECHNIQUE_PROHIBITED = "technique_prohibited"
    KILL_SWITCH_ENGAGED = "kill_switch_engaged"
    APPROVAL_REQUIRED = "approval_required"
    APPROVAL_NOT_FOUND = "approval_not_found"
    APPROVAL_DENIED = "approval_denied"
    APPROVAL_NOT_BINDING = "approval_not_binding"
    APPROVAL_EXPIRED = "approval_expired"
    APPROVAL_ALREADY_CONSUMED = "approval_already_consumed"


@dataclass(frozen=True)
class AccessRequest:
    """A proposed action, described before it happens."""

    asset: str
    authority_level: AuthorityLevel
    actor: str
    technique: str | None = None
    derived_from: str | None = None
    """The asset this one was discovered through, if any. Recorded so a denial
    can say *why* the asset looked in scope when it was not."""

    purpose: str = ""

    action_type: str = ""
    """What is being done, e.g. ``read_object``. An approval is bound to this
    plus the asset — approval to read is not approval to delete."""

    approval_id: str | None = None
    """Operator approval this request presents. Required above
    ``Gate.approval_required_above``."""

    def to_dict(self) -> dict[str, Any]:
        return {
            "asset": self.asset,
            "authority_level": self.authority_level.name,
            "actor": self.actor,
            "technique": self.technique,
            "derived_from": self.derived_from,
            "purpose": self.purpose,
            "action_type": self.action_type,
            "approval_id": self.approval_id,
        }


@dataclass(frozen=True)
class Decision:
    allowed: bool
    reason: Reason
    detail: str
    authority_ref: str | None
    """Contract fingerprint the decision was made against. Artifacts produced
    under an allow must carry this (invariant I2)."""

    audit_seq: int | None = None

    def __bool__(self) -> bool:
        return self.allowed

    def raise_if_denied(self) -> None:
        if not self.allowed:
            raise PermissionError(f"{self.reason.value}: {self.detail}")


class Gate:
    """Fail-closed authority check.

    Args:
        audit: Where decisions are recorded.
        posture_ceiling: System-wide cap. Defaults to ``LOCAL_FIXTURE``, which
            is the current operating posture in `Docs/scope-policy.md`.
        max_contract_age: Age past which a contract is stale and grants nothing.
        clock: Injected for testability.
    """

    def __init__(
        self,
        audit: AuditLog,
        *,
        posture_ceiling: AuthorityLevel = AuthorityLevel.LOCAL_FIXTURE,
        max_contract_age: timedelta = DEFAULT_MAX_CONTRACT_AGE,
        approvals: ApprovalStore | None = None,
        approval_required_above: AuthorityLevel = AuthorityLevel.PASSIVE_HTTP,
        approval_max_age: timedelta = DEFAULT_APPROVAL_MAX_AGE,
        clock: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
    ):
        self.audit = audit
        self.posture_ceiling = posture_ceiling
        self.max_contract_age = max_contract_age
        self.approvals = approvals
        self.approval_required_above = approval_required_above
        self.approval_max_age = approval_max_age
        self._clock = clock
        self._kill_switch = False

    def engage_kill_switch(self, *, actor: str, reason: str) -> None:
        """Deny everything until explicitly released."""
        self._kill_switch = True
        self.audit.append(
            actor=actor,
            action="kill_switch.engage",
            detail={"reason": reason},
        )

    def release_kill_switch(self, *, actor: str, reason: str) -> None:
        self._kill_switch = False
        self.audit.append(
            actor=actor,
            action="kill_switch.release",
            detail={"reason": reason},
        )

    @property
    def kill_switch_engaged(self) -> bool:
        return self._kill_switch

    def evaluate(
        self, contract: ScopeContract | None, request: AccessRequest
    ) -> Decision:
        """Decide whether ``request`` may proceed. Always audited."""
        decision = self._decide(contract, request)
        record = self.audit.append(
            actor=request.actor,
            action="gate.evaluate",
            authority_ref=decision.authority_ref,
            detail={
                "request": request.to_dict(),
                "allowed": decision.allowed,
                "reason": decision.reason.value,
                "detail": decision.detail,
                "contract_id": contract.id if contract else None,
                "posture_ceiling": self.posture_ceiling.name,
            },
        )
        return Decision(
            allowed=decision.allowed,
            reason=decision.reason,
            detail=decision.detail,
            authority_ref=decision.authority_ref,
            audit_seq=record.seq,
        )

    def _decide(
        self, contract: ScopeContract | None, request: AccessRequest
    ) -> Decision:
        if self._kill_switch:
            return Decision(
                False,
                Reason.KILL_SWITCH_ENGAGED,
                "kill switch is engaged; all execution is denied",
                None,
            )

        if contract is None:
            return Decision(
                False, Reason.NO_CONTRACT, "no scope contract supplied", None
            )

        ref = contract.fingerprint()

        if contract.status is ContractStatus.BLOCKED:
            return Decision(
                False,
                Reason.CONTRACT_BLOCKED,
                f"contract is blocked by {len(contract.ambiguities)} ambiguity/ies: "
                + "; ".join(contract.ambiguities[:3]),
                ref,
            )

        if contract.status is not ContractStatus.VERIFIED or not contract.human_reviewed:
            return Decision(
                False,
                Reason.CONTRACT_NOT_VERIFIED,
                f"contract status is {contract.status.value} and human_reviewed="
                f"{contract.human_reviewed}; only a human-reviewed, verified "
                "contract grants authority",
                ref,
            )

        if contract.is_stale(now=self._clock(), max_age=self.max_contract_age):
            return Decision(
                False,
                Reason.CONTRACT_STALE,
                f"contract was last verified {contract.verified_at.isoformat()}, "
                f"beyond the {self.max_contract_age} trust window; re-verify the "
                "programme before testing",
                ref,
            )

        if contract.prohibits(request.technique):
            return Decision(
                False,
                Reason.TECHNIQUE_PROHIBITED,
                f"technique {request.technique!r} is prohibited by this contract",
                ref,
            )

        classification = contract.classify(request.asset)
        if classification is ScopeClassification.OUT_OF_SCOPE:
            return Decision(
                False,
                Reason.ASSET_OUT_OF_SCOPE,
                f"{request.asset!r} matches an out-of-scope pattern",
                ref,
            )
        if classification is ScopeClassification.UNRESOLVED:
            if request.derived_from:
                return Decision(
                    False,
                    Reason.DERIVED_ASSET_NOT_INHERITED,
                    f"{request.asset!r} was discovered through "
                    f"{request.derived_from!r} but does not independently satisfy "
                    "the contract; scope is not inherited",
                    ref,
                )
            return Decision(
                False,
                Reason.ASSET_UNRESOLVED,
                f"{request.asset!r} matches no in-scope pattern; absence of a "
                "match is denial",
                ref,
            )

        granted = AuthorityLevel.parse(contract.max_authority)
        if request.authority_level > granted:
            return Decision(
                False,
                Reason.AUTHORITY_LEVEL_EXCEEDED,
                f"request needs {request.authority_level.name} but the contract "
                f"grants at most {granted.name}",
                ref,
            )

        if request.authority_level > self.posture_ceiling:
            return Decision(
                False,
                Reason.POSTURE_CEILING_EXCEEDED,
                f"request needs {request.authority_level.name} but the current "
                f"operating posture caps execution at {self.posture_ceiling.name}",
                ref,
            )

        if request.authority_level > self.approval_required_above:
            approval_decision = self._check_approval(request, ref)
            if approval_decision is not None:
                return approval_decision

        return Decision(
            True,
            Reason.ALLOWED,
            f"{request.asset!r} is in scope at {request.authority_level.name}",
            ref,
        )

    def _check_approval(
        self, request: AccessRequest, ref: str
    ) -> Decision | None:
        """Return a denial, or ``None`` if the approval is good.

        Scope says *what may be touched*. An approval says *that this specific
        act was consented to, once, recently*. Both are required above the
        approval threshold; neither substitutes for the other.
        """
        if self.approvals is None:
            return Decision(
                False,
                Reason.APPROVAL_REQUIRED,
                f"{request.authority_level.name} requires an operator approval "
                "but this gate has no approval store configured",
                ref,
            )

        if not request.approval_id:
            return Decision(
                False,
                Reason.APPROVAL_REQUIRED,
                f"{request.authority_level.name} requires an operator approval; "
                "the request presented none",
                ref,
            )

        approval = self.approvals.lookup(request.approval_id)
        if approval is None:
            return Decision(
                False,
                Reason.APPROVAL_NOT_FOUND,
                f"no approval record found for {request.approval_id!r}",
                ref,
            )

        if not approval.granted:
            return Decision(
                False,
                Reason.APPROVAL_DENIED,
                f"approval {approval.approval_id!r} was denied by "
                f"{approval.operator_id!r}",
                ref,
            )

        if not approval.covers(
            action_type=request.action_type, target=request.asset
        ):
            return Decision(
                False,
                Reason.APPROVAL_NOT_BINDING,
                f"approval {approval.approval_id!r} covers "
                f"{approval.action_type!r} on {approval.target!r}, not "
                f"{request.action_type!r} on {request.asset!r}",
                ref,
            )

        if approval.is_expired(now=self._clock(), max_age=self.approval_max_age):
            return Decision(
                False,
                Reason.APPROVAL_EXPIRED,
                f"approval {approval.approval_id!r} was given "
                f"{approval.responded_at.isoformat()}, beyond the "
                f"{self.approval_max_age} window; ask again",
                ref,
            )

        if self._already_consumed(approval.approval_id):
            return Decision(
                False,
                Reason.APPROVAL_ALREADY_CONSUMED,
                f"approval {approval.approval_id!r} has already been spent; "
                "approvals are single-use",
                ref,
            )

        return None

    def _already_consumed(self, approval_id: str) -> bool:
        """Has this approval already authorised an allow?

        Checked against the audit log rather than a separate ledger — the log
        already records every allow, so it already knows what has been spent,
        and a second store would be a second thing to keep honest.
        """
        for record in self.audit:
            if record.action != "gate.evaluate":
                continue
            if not record.detail.get("allowed"):
                continue
            if record.detail.get("request", {}).get("approval_id") == approval_id:
                return True
        return False
