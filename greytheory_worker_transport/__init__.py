"""Authenticated, carrier-neutral broker-to-worker transport contract."""

# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 ChaseInTech

from greytheory_worker_transport.protocol import (
    AuthenticatedTransportSession,
    BROKER_TRANSPORT_SCHEMA_VERSION,
    BrokerTransportError,
    BrokerTransportHandshake,
    HandshakeReplayGuard,
    IdentitySigner,
    IdentityVerifier,
    InMemoryHandshakeReplayGuard,
    MAX_HANDSHAKE_SECONDS,
    MAX_TRANSPORT_FRAME_BYTES,
    TransportMessageType,
    TransportRole,
    WorkerTransportHandshake,
)

__all__ = [
    "AuthenticatedTransportSession",
    "BROKER_TRANSPORT_SCHEMA_VERSION",
    "BrokerTransportError",
    "BrokerTransportHandshake",
    "HandshakeReplayGuard",
    "IdentitySigner",
    "IdentityVerifier",
    "InMemoryHandshakeReplayGuard",
    "MAX_HANDSHAKE_SECONDS",
    "MAX_TRANSPORT_FRAME_BYTES",
    "TransportMessageType",
    "TransportRole",
    "WorkerTransportHandshake",
]
