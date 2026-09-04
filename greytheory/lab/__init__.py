"""Deliberately local, synthetic research fixtures.

Nothing in this package performs network I/O. Fixtures are bounded teaching
surfaces used to prove the trust kernel before any higher operating posture is
considered.
"""

# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 ChaseInTech

from greytheory.lab.two_account import (
    ExecutionDenied,
    FixtureAction,
    FixtureResponse,
    OwnershipValidator,
    TwoAccountFixture,
)

__all__ = [
    "ExecutionDenied",
    "FixtureAction",
    "FixtureResponse",
    "OwnershipValidator",
    "TwoAccountFixture",
]
