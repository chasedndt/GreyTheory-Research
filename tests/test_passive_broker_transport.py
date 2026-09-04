"""Network-free proof for the authenticated broker/worker channel contract."""

from __future__ import annotations

import ast
import base64
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from greytheory_broker import Ed25519Signer
from greytheory_worker_transport import (
    BrokerTransportError,
    BrokerTransportHandshake,
    InMemoryHandshakeReplayGuard,
    MAX_TRANSPORT_FRAME_BYTES,
    TransportMessageType,
    WorkerTransportHandshake,
)
from greytheory_worker_contract import (
    DirectHeadRequest,
    HeadTransportResult,
    ResolutionResult,
)


NOW = datetime(2026, 9, 4, 13, 30, tzinfo=timezone.utc)
BROKER_SIGNER = Ed25519Signer.from_private_bytes(bytes(range(32)))
WORKER_SIGNER = Ed25519Signer.from_private_bytes(bytes(range(32, 64)))
OTHER_SIGNER = Ed25519Signer.from_private_bytes(bytes(range(64, 96)))


def sessions(*, now: datetime = NOW):
    replay_guard = InMemoryHandshakeReplayGuard()
    pending, broker_hello = BrokerTransportHandshake.start(
        session_id="transport-fixture-1",
        broker_signer=BROKER_SIGNER,
        worker_key_id=WORKER_SIGNER.key_id,
        issued_at=NOW,
        expires_at=NOW + timedelta(seconds=30),
    )
    worker, worker_hello = WorkerTransportHandshake.accept(
        broker_hello,
        broker_verifier=BROKER_SIGNER.verifier,
        worker_signer=WORKER_SIGNER,
        replay_guard=replay_guard,
        now=now,
    )
    broker = pending.finish(
        worker_hello,
        worker_verifier=WORKER_SIGNER.verifier,
        now=now,
    )
    assert pending._ephemeral_private_key is None
    return broker, worker, broker_hello, worker_hello


def test_mutually_authenticated_channel_encrypts_exact_two_phase_exchange():
    broker, worker, broker_hello, worker_hello = sessions()
    assert b"broker-transport.v1" in broker_hello
    assert BROKER_SIGNER.private_bytes.hex().encode() not in broker_hello
    assert WORKER_SIGNER.private_bytes.hex().encode() not in worker_hello
    assert broker.transcript_digest == worker.transcript_digest

    resolve = broker.seal(
        TransportMessageType.RESOLVE,
        {"canonical_host": "greytheory-canary.invalid", "deadline_monotonic": 30.0},
        now=NOW,
    )
    assert b"greytheory-canary.invalid" not in resolve
    kind, payload = worker.open(resolve, now=NOW)
    assert kind is TransportMessageType.RESOLVE
    assert payload["canonical_host"] == "greytheory-canary.invalid"

    resolution_result = ResolutionResult(
        canonical_host="greytheory-canary.invalid",
        addresses=("8.8.8.8",),
        started_monotonic=0.1,
        ended_monotonic=0.2,
    )
    resolution = worker.seal(
        TransportMessageType.RESOLUTION,
        resolution_result.to_dict(),
        now=NOW,
    )
    resolution_kind, resolution_payload = broker.open(resolution, now=NOW)
    assert resolution_kind is TransportMessageType.RESOLUTION
    assert ResolutionResult.from_dict(resolution_payload) == resolution_result

    direct_request = DirectHeadRequest(
        ticket_digest="c" * 64,
        canonical_url="https://greytheory-canary.invalid/",
        canonical_host="greytheory-canary.invalid",
        request_target="/",
        exact_address="8.8.8.8",
        tls_server_name="greytheory-canary.invalid",
        max_capture_bytes=65_536,
        deadline_monotonic=30.0,
    )
    head = broker.seal(
        TransportMessageType.HEAD,
        direct_request.to_dict(),
        now=NOW,
    )
    head_kind, head_payload = worker.open(head, now=NOW)
    assert head_kind is TransportMessageType.HEAD
    assert DirectHeadRequest.from_dict(head_payload) == direct_request

    raw_headers = b"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\n"
    transport_result = HeadTransportResult(
        request_digest=direct_request.digest,
        connected_address="8.8.8.8",
        tls_server_name="greytheory-canary.invalid",
        raw_header_block=raw_headers,
        bytes_received=len(raw_headers),
        body_bytes_received=0,
        started_monotonic=0.3,
        ended_monotonic=0.4,
    )
    transport = worker.seal(
        TransportMessageType.TRANSPORT,
        transport_result.to_dict(),
        now=NOW,
    )
    assert worker.closed
    transport_kind, transport_payload = broker.open(transport, now=NOW)
    assert transport_kind is TransportMessageType.TRANSPORT
    assert HeadTransportResult.from_dict(transport_payload) == transport_result
    assert broker.closed


def test_tampered_handshake_and_wrong_pinned_identity_fail_closed():
    pending, broker_hello = BrokerTransportHandshake.start(
        session_id="transport-fixture-2",
        broker_signer=BROKER_SIGNER,
        worker_key_id=WORKER_SIGNER.key_id,
        issued_at=NOW,
        expires_at=NOW + timedelta(seconds=30),
    )
    tampered = json.loads(broker_hello)
    tampered["payload"]["session_id"] = "transport-fixture-tampered"
    with pytest.raises(BrokerTransportError, match="signature"):
        WorkerTransportHandshake.accept(
            json.dumps(tampered, sort_keys=True, separators=(",", ":")).encode(),
            broker_verifier=BROKER_SIGNER.verifier,
            worker_signer=WORKER_SIGNER,
            replay_guard=InMemoryHandshakeReplayGuard(),
            now=NOW,
        )

    worker, worker_hello = WorkerTransportHandshake.accept(
        broker_hello,
        broker_verifier=BROKER_SIGNER.verifier,
        worker_signer=WORKER_SIGNER,
        replay_guard=InMemoryHandshakeReplayGuard(),
        now=NOW,
    )
    assert not worker.closed
    with pytest.raises(BrokerTransportError, match="identity|pinned"):
        pending.finish(
            worker_hello,
            worker_verifier=OTHER_SIGNER.verifier,
            now=NOW,
        )
    worker.close()


def test_frame_tamper_replay_reflection_and_order_are_refused():
    broker, worker, _, _ = sessions()
    with pytest.raises(BrokerTransportError, match="out of order"):
        broker.seal(TransportMessageType.HEAD, {}, now=NOW)

    frame = broker.seal(
        TransportMessageType.RESOLVE,
        {"canonical_host": "greytheory-canary.invalid"},
        now=NOW,
    )
    envelope = json.loads(frame)
    ciphertext = bytearray(base64.b64decode(envelope["ciphertext_b64"]))
    ciphertext[-1] ^= 1
    envelope["ciphertext_b64"] = base64.b64encode(ciphertext).decode()
    tampered = json.dumps(envelope, sort_keys=True, separators=(",", ":")).encode()
    with pytest.raises(BrokerTransportError, match="authentication"):
        worker.open(tampered, now=NOW)

    assert worker.open(frame, now=NOW)[0] is TransportMessageType.RESOLVE
    with pytest.raises(BrokerTransportError, match="replayed|out of order"):
        worker.open(frame, now=NOW)
    with pytest.raises(BrokerTransportError, match="session"):
        broker.open(frame, now=NOW)


def test_expiry_duplicate_json_and_oversize_fail_closed():
    pending, hello = BrokerTransportHandshake.start(
        session_id="transport-fixture-3",
        broker_signer=BROKER_SIGNER,
        worker_key_id=WORKER_SIGNER.key_id,
        issued_at=NOW,
        expires_at=NOW + timedelta(seconds=30),
    )
    with pytest.raises(BrokerTransportError, match="lifetime"):
        WorkerTransportHandshake.accept(
            hello,
            broker_verifier=BROKER_SIGNER.verifier,
            worker_signer=WORKER_SIGNER,
            replay_guard=InMemoryHandshakeReplayGuard(),
            now=NOW + timedelta(seconds=30),
        )

    duplicate = hello[:-1] + b',"kind":"broker_hello"}'
    with pytest.raises(BrokerTransportError, match="duplicate"):
        WorkerTransportHandshake.accept(
            duplicate,
            broker_verifier=BROKER_SIGNER.verifier,
            worker_signer=WORKER_SIGNER,
            replay_guard=InMemoryHandshakeReplayGuard(),
            now=NOW,
        )

    broker, _, _, _ = sessions()
    with pytest.raises(BrokerTransportError, match="ceiling"):
        broker.seal(
            TransportMessageType.RESOLVE,
            {"padding": "x" * MAX_TRANSPORT_FRAME_BYTES},
            now=NOW,
        )
    assert broker.phase == "send_resolve"
    assert not broker.closed
    with pytest.raises(BrokerTransportError, match="expired"):
        broker.seal(
            TransportMessageType.RESOLVE,
            {},
            now=NOW + timedelta(seconds=30),
        )
    assert broker.closed


def test_worker_replay_guard_consumes_one_valid_broker_hello_once():
    _, hello = BrokerTransportHandshake.start(
        session_id="transport-fixture-replay",
        broker_signer=BROKER_SIGNER,
        worker_key_id=WORKER_SIGNER.key_id,
        issued_at=NOW,
        expires_at=NOW + timedelta(seconds=30),
    )
    guard = InMemoryHandshakeReplayGuard()
    WorkerTransportHandshake.accept(
        hello,
        broker_verifier=BROKER_SIGNER.verifier,
        worker_signer=WORKER_SIGNER,
        replay_guard=guard,
        now=NOW,
    )
    with pytest.raises(BrokerTransportError, match="already been consumed"):
        WorkerTransportHandshake.accept(
            hello,
            broker_verifier=BROKER_SIGNER.verifier,
            worker_signer=WORKER_SIGNER,
            replay_guard=guard,
            now=NOW,
        )


def test_transport_contract_has_no_carrier_listener_or_process_implementation():
    root = Path(__file__).resolve().parents[1] / "greytheory_worker_transport"
    forbidden = {
        "asyncio",
        "http.client",
        "multiprocessing",
        "socket",
        "ssl",
        "subprocess",
        "urllib.request",
        "greytheory_broker",
    }
    imported: set[str] = set()
    for path in root.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module)
    assert imported.isdisjoint(forbidden)
