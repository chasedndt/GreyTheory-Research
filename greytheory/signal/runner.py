"""The lane runner — the only way a collector ever executes.

Collectors are not called directly anywhere in this system. They are called
here, and only after the gate has allowed the specific asset at the specific
authority level the lane declared. A lane that is denied does not run at all;
it does not get a chance to decide whether the denial applied to it.

Three things are enforced here rather than trusted:

**Network lanes are refused.** A lane declaring ``network=True`` cannot run in
this package at all. The core is offline by construction, and a collector that
wanted to change that would have to be moved out rather than argued with.

**Every signal is stamped with the authority that permitted it.** A collector
cannot forge one — the runner overwrites whatever the lane put there.

**Denials are recorded, not swallowed.** A skipped target is part of the run
record. A run that quietly collected from three of five targets and reported
success would be worse than one that failed.
"""

# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 ChaseInTech

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from greytheory.audit import AuditLog
from greytheory.authority.gate import AccessRequest, Decision, Gate
from greytheory.authority.scope import ScopeContract
from greytheory.signal.contract import Lane, LaneContext, LaneContextError, RawSignal


class LaneRefused(Exception):
    """Raised when a lane may not run at all, regardless of target."""


@dataclass
class TargetOutcome:
    asset: str
    allowed: bool
    reason: str
    signals: list[RawSignal] = field(default_factory=list)
    error: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "asset": self.asset,
            "allowed": self.allowed,
            "reason": self.reason,
            "signals": [s.to_dict() for s in self.signals],
            "error": self.error,
        }


@dataclass
class LaneRun:
    lane_id: str
    started_at: datetime
    outcomes: list[TargetOutcome]

    @property
    def signals(self) -> list[RawSignal]:
        return [s for outcome in self.outcomes for s in outcome.signals]

    @property
    def skipped(self) -> list[TargetOutcome]:
        return [o for o in self.outcomes if not o.allowed]

    @property
    def failed(self) -> list[TargetOutcome]:
        return [o for o in self.outcomes if o.allowed and o.error]

    def to_dict(self) -> dict[str, Any]:
        return {
            "lane_id": self.lane_id,
            "started_at": self.started_at.isoformat(),
            "signal_count": len(self.signals),
            "skipped": len(self.skipped),
            "failed": len(self.failed),
            "outcomes": [o.to_dict() for o in self.outcomes],
        }


def run_lane(
    lane: Lane,
    *,
    targets: Mapping[str, str | Path],
    gate: Gate,
    contract: ScopeContract | None,
    actor: str,
    approval_id: str | None = None,
    audit: AuditLog | None = None,
    clock: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
) -> LaneRun:
    """Run a collector across targets it is authorised for.

    Args:
        lane: The collector.
        targets: Asset name -> local root. The asset name is what the gate
            checks; the root is what the collector may read. They are separate
            because scope is expressed in the programme's terms, not the
            filesystem's.
        gate: The authority gate. Non-negotiable.
        contract: The scope contract in force.
        approval_id: Passed through when the lane's authority level is above
            the gate's approval threshold.

    Raises:
        LaneRefused: If the lane declares network I/O.
    """
    if lane.spec.network:
        raise LaneRefused(
            f"lane {lane.spec.id!r} declares network I/O and cannot run in the "
            "core package. Network collectors live outside greytheory/ and act "
            "only through a granted Decision."
        )

    started = clock()
    outcomes: list[TargetOutcome] = []

    for asset, root in targets.items():
        decision: Decision = gate.evaluate(
            contract,
            AccessRequest(
                asset=asset,
                authority_level=lane.spec.requires_authority,
                actor=actor,
                action_type=f"collect:{lane.spec.id}",
                approval_id=approval_id,
                purpose=lane.spec.title,
            ),
        )

        if not decision.allowed:
            outcomes.append(
                TargetOutcome(asset=asset, allowed=False, reason=decision.reason.value)
            )
            continue

        try:
            context = LaneContext(
                asset=asset,
                root=root,
                authority_ref=decision.authority_ref or "",
                clock=clock,
            )
            collected = list(lane.collect(context))
        except (LaneContextError, OSError, ValueError) as exc:
            outcomes.append(
                TargetOutcome(
                    asset=asset,
                    allowed=True,
                    reason=decision.reason.value,
                    error=f"{type(exc).__name__}: {exc}",
                )
            )
            continue

        # The lane does not get to claim its own authority. Whatever it set is
        # replaced with what the gate actually granted.
        stamped = [
            replace(
                signal,
                authority_ref=decision.authority_ref or "",
                observed_at=signal.observed_at or started,
            )
            for signal in collected
        ]
        outcomes.append(
            TargetOutcome(
                asset=asset,
                allowed=True,
                reason=decision.reason.value,
                signals=stamped,
            )
        )

    run = LaneRun(lane_id=lane.spec.id, started_at=started, outcomes=outcomes)

    if audit is not None:
        audit.append(
            actor=actor,
            action="lane.run",
            authority_ref=contract.fingerprint() if contract else None,
            detail={
                "lane": lane.spec.to_dict(),
                "targets": list(targets),
                "signal_count": len(run.signals),
                "skipped": [
                    {"asset": o.asset, "reason": o.reason} for o in run.skipped
                ],
                "failed": [
                    {"asset": o.asset, "error": o.error} for o in run.failed
                ],
            },
        )
    return run


def run_lanes(
    lanes: Sequence[Lane],
    **kwargs: Any,
) -> list[LaneRun]:
    """Run several collectors over the same targets."""
    return [run_lane(lane, **kwargs) for lane in lanes]


__all__ = ["LaneRefused", "LaneRun", "TargetOutcome", "run_lane", "run_lanes"]
