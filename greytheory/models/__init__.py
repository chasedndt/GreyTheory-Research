"""Plane 1/3 — the model gateway.

Nothing here calls a network. A real provider is supplied from outside the
core; the gateway enforces classification, citation and provenance around it.

Every model output enters the system as ``inferred``. There is no path from a
model response to a ``checked`` claim — that requires a validator receipt, and
a model cannot issue one.
"""

# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 ChaseInTech

from greytheory.models.evaluation import (
    EvalCase,
    EvalReport,
    EvalResult,
    builtin_cases,
    run_suite,
)
from greytheory.models.gateway import (
    ContextFragment,
    EchoProvider,
    GatewayError,
    ModelGateway,
    ModelOutput,
    ModelProvider,
    ModelRequest,
    ProviderResponse,
)
from greytheory.models.policy import (
    ROLE_CONTRACTS,
    DataClass,
    ModelRole,
    PolicyError,
    ProviderPolicy,
    RoleContract,
    TrustLabel,
    contract_for,
)

__all__ = [
    "ContextFragment",
    "DataClass",
    "EchoProvider",
    "EvalCase",
    "EvalReport",
    "EvalResult",
    "GatewayError",
    "ModelGateway",
    "ModelOutput",
    "ModelProvider",
    "ModelRequest",
    "ModelRole",
    "PolicyError",
    "ProviderPolicy",
    "ROLE_CONTRACTS",
    "RoleContract",
    "TrustLabel",
    "builtin_cases",
    "contract_for",
    "run_suite",
]
