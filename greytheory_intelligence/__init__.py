"""Contract-only public vulnerability-intelligence integration boundary.

The package describes and validates read-only provider requests. It deliberately
ships no HTTP client, scheduler, credential store, or execution entrypoint.
"""

# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 ChaseInTech

from .registry import (
    INTELLIGENCE_PROVIDERS,
    IntelligencePlan,
    IntelligenceProvider,
    QueryKind,
    build_intelligence_plan,
)

__all__ = [
    "INTELLIGENCE_PROVIDERS",
    "IntelligencePlan",
    "IntelligenceProvider",
    "QueryKind",
    "build_intelligence_plan",
]
