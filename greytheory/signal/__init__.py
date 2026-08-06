"""Plane 2 — the Signal Plane.

Collectors that observe and conclude nothing. `contract` defines what a lane
is and is forbidden to be; `runner` is the only way one ever executes.

No lane in this package performs network I/O, and the runner refuses any that
declares it. Network collectors live outside `greytheory/` and act only
through a granted Decision.
"""

# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 ChaseInTech

from greytheory.signal.contract import (
    Lane,
    LaneContext,
    LaneContextError,
    LaneSpec,
    RawSignal,
    SignalLevel,
    checked,
    observed,
)
from greytheory.signal.runner import (
    LaneRefused,
    LaneRun,
    TargetOutcome,
    run_lane,
    run_lanes,
)

__all__ = [
    "Lane",
    "LaneContext",
    "LaneContextError",
    "LaneRefused",
    "LaneRun",
    "LaneSpec",
    "RawSignal",
    "SignalLevel",
    "TargetOutcome",
    "checked",
    "observed",
    "run_lane",
    "run_lanes",
]
