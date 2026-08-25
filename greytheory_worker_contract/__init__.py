"""Network-free conformance contract for a future isolated passive worker."""

# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 ChaseInTech

from greytheory_worker_contract.adapter import (
    AdapterContractError,
    AdapterTimedOut,
    DirectHeadRequest,
    HeadTransport,
    HeadTransportResult,
    PassiveAdapterResult,
    PassiveHeadAdapter,
    ResolutionFailed,
    ResolutionResult,
    Resolver,
    TransportFailed,
    TransportCaptureLimitExceeded,
)

__all__ = [
    "AdapterContractError",
    "AdapterTimedOut",
    "DirectHeadRequest",
    "HeadTransport",
    "HeadTransportResult",
    "PassiveAdapterResult",
    "PassiveHeadAdapter",
    "ResolutionFailed",
    "ResolutionResult",
    "Resolver",
    "TransportFailed",
    "TransportCaptureLimitExceeded",
]
