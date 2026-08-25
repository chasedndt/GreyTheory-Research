"""Dark-by-default passive broker contracts; contains no network adapter."""

# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 ChaseInTech

from greytheory_broker.contracts import (
    POLICY_VERSION,
    RECEIPT_SCHEMA_VERSION,
    TICKET_SCHEMA_VERSION,
    BrokerContractError,
    BrokerLimits,
    PassiveMethod,
    PassiveReceiptPayload,
    PassiveTicketIssuer,
    PassiveTicketPayload,
    ReceiptOutcome,
    SignedPassiveReceipt,
    SignedPassiveTicket,
)
from greytheory_broker.guard import (
    BrokerDenied,
    BrokerDenialReason,
    PassiveBrokerSession,
)
from greytheory_broker.storage import (
    BrokerKillSwitch,
    BrokerStorageError,
    KillSwitchState,
    RateLimitDenied,
    TicketReplayDenied,
    TicketReplayLedger,
    TicketReservation,
)
from greytheory_broker.signing import (
    ED25519_ALGORITHM,
    Ed25519Signer,
    Ed25519Verifier,
    MessageSigner,
    MessageVerifier,
    SigningError,
)
from greytheory_broker.url_policy import (
    TargetPolicyError,
    canonical_hostname,
    canonical_https_url,
    public_addresses,
)

__all__ = [
    "POLICY_VERSION",
    "RECEIPT_SCHEMA_VERSION",
    "TICKET_SCHEMA_VERSION",
    "BrokerContractError",
    "BrokerDenied",
    "BrokerDenialReason",
    "BrokerKillSwitch",
    "BrokerLimits",
    "BrokerStorageError",
    "ED25519_ALGORITHM",
    "Ed25519Signer",
    "Ed25519Verifier",
    "KillSwitchState",
    "MessageSigner",
    "MessageVerifier",
    "RateLimitDenied",
    "PassiveBrokerSession",
    "PassiveMethod",
    "PassiveReceiptPayload",
    "PassiveTicketIssuer",
    "PassiveTicketPayload",
    "ReceiptOutcome",
    "SignedPassiveReceipt",
    "SignedPassiveTicket",
    "SigningError",
    "TargetPolicyError",
    "TicketReplayDenied",
    "TicketReplayLedger",
    "TicketReservation",
    "canonical_hostname",
    "canonical_https_url",
    "public_addresses",
]
