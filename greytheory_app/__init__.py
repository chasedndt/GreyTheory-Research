"""GreyTheory's local operator application layer.

This package may depend on the offline :mod:`greytheory` kernel. The kernel
must never depend on this package. Server and desktop framework choices belong
here later; the first implementation is a transport-neutral contract/service.
"""

# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 ChaseInTech

from greytheory_app.contracts import (
    WORKBENCH_SCHEMA_VERSION,
    CommandDisposition,
    CommandField,
    CommandKind,
    CommandResult,
    NextAction,
    ReadinessStatus,
    WorkbenchCommand,
    WorkbenchContext,
    WorkbenchContractError,
    WorkbenchMetric,
    WorkbenchRecord,
    WorkbenchSection,
    WorkbenchSnapshot,
)
from greytheory_app.service import WorkbenchApplicationService

__all__ = [
    "WORKBENCH_SCHEMA_VERSION",
    "CommandDisposition",
    "CommandField",
    "CommandKind",
    "CommandResult",
    "NextAction",
    "ReadinessStatus",
    "WorkbenchApplicationService",
    "WorkbenchCommand",
    "WorkbenchContext",
    "WorkbenchContractError",
    "WorkbenchMetric",
    "WorkbenchRecord",
    "WorkbenchSection",
    "WorkbenchSnapshot",
]
