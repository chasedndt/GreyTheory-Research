"""Carrier-neutral authenticated channel for the future isolated worker.

This module deliberately contains no socket, listener, process, launcher, or
network implementation.  It authenticates a pinned broker and worker, derives
fresh directional keys, encrypts every frame, and enforces the existing
resolve -> resolution -> head -> transport exchange.  A later VM carrier must
preserve this contract rather than inventing authority at the transport edge.
"""

# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 ChaseInTech

from __future__ import annotations

import base64
import binascii
import hashlib
import json
import re
import secrets
import threading
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Mapping, Protocol

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric.x25519 import (
    X25519PrivateKey,
    X25519PublicKey,
)
from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

BROKER_TRANSPORT_SCHEMA_VERSION = "greytheory.broker-transport.v1"
MAX_TRANSPORT_FRAME_BYTES = 196_608
MAX_HANDSHAKE_SECONDS = 30
SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,191}$")
SAFE_NONCE = re.compile(r"^[a-f0-9]{32,128}$")
SAFE_DIGEST = re.compile(r"^[a-f0-9]{64}$")
SAFE_KEY_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,191}$")
ED25519_ALGORITHM = "ed25519"


class BrokerTransportError(ValueError):
    """Raised when the authenticated channel fails closed."""


class IdentityVerifier(Protocol):
    """Public identity operation required by the transport contract."""

    algorithm: str
    key_id: str

    def verify(self, message: bytes, signature: str) -> None: ...


class IdentitySigner(IdentityVerifier, Protocol):
    """Private identity operation supplied by the owning endpoint."""

    def sign(self, message: bytes) -> str: ...


class TransportRole(str, Enum):
    BROKER = "broker"
    WORKER = "worker"

    @property
    def peer(self) -> TransportRole:
        return (
            TransportRole.WORKER
            if self is TransportRole.BROKER
            else TransportRole.BROKER
        )


class TransportMessageType(str, Enum):
    RESOLVE = "resolve"
    RESOLUTION = "resolution"
    HEAD = "head"
    TRANSPORT = "transport"
    ERROR = "error"


class HandshakeReplayGuard(Protocol):
    """Consume one authenticated broker hello digest at most once."""

    def consume(
        self, digest: str, *, now: datetime, expires_at: datetime
    ) -> None: ...


class InMemoryHandshakeReplayGuard:
    """Bounded process-lifetime guard for tests and one-shot local workers.

    A reboot-conformant carrier must inject a durable implementation.  The
    contract makes that choice explicit instead of silently accepting replay.
    """

    def __init__(self, *, max_entries: int = 1_024) -> None:
        if isinstance(max_entries, bool) or not 1 <= max_entries <= 65_536:
            raise BrokerTransportError("transport replay guard capacity is invalid")
        self.max_entries = max_entries
        self._seen: dict[str, datetime] = {}
        self._lock = threading.Lock()

    def consume(
        self, digest: str, *, now: datetime, expires_at: datetime
    ) -> None:
        value = _digest(digest, "broker hello digest")
        when = _aware(now, "transport replay time")
        expiry = _aware(expires_at, "transport replay expiry")
        if expiry <= when:
            raise BrokerTransportError("expired broker hello cannot enter replay state")
        with self._lock:
            self._seen = {
                item: deadline
                for item, deadline in self._seen.items()
                if deadline > when
            }
            if value in self._seen:
                raise BrokerTransportError("broker hello has already been consumed")
            if len(self._seen) >= self.max_entries:
                raise BrokerTransportError("transport replay guard is at capacity")
            self._seen[value] = expiry


def _aware(value: datetime, label: str) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None:
        raise BrokerTransportError(f"{label} must be timezone-aware")
    return value.astimezone(timezone.utc)


def _safe_id(value: str, label: str) -> str:
    text = str(value or "")
    if not SAFE_ID.fullmatch(text):
        raise BrokerTransportError(f"{label} is not a safe identifier")
    return text


def _key_id(value: str, label: str) -> str:
    text = str(value or "")
    if not SAFE_KEY_ID.fullmatch(text):
        raise BrokerTransportError(f"{label} is not a safe key identifier")
    return text


def _nonce(value: str, label: str) -> str:
    text = str(value or "")
    if not SAFE_NONCE.fullmatch(text):
        raise BrokerTransportError(f"{label} must be 16-64 bytes of lowercase hex")
    return text


def _digest(value: str, label: str) -> str:
    text = str(value or "")
    if not SAFE_DIGEST.fullmatch(text):
        raise BrokerTransportError(f"{label} must be a lowercase SHA-256 digest")
    return text


def _exact_keys(
    value: Mapping[str, Any], expected: set[str], label: str
) -> None:
    if set(value) != expected:
        raise BrokerTransportError(f"{label} fields are not exact")


def _canonical(value: Mapping[str, Any]) -> bytes:
    try:
        encoded = json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("ascii")
    except (TypeError, ValueError) as exc:
        raise BrokerTransportError("transport value is not canonical JSON") from exc
    return encoded


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise BrokerTransportError("transport JSON contains a duplicate key")
        value[key] = item
    return value


def _decode(raw: bytes, *, label: str) -> Mapping[str, Any]:
    if not isinstance(raw, bytes) or not raw or len(raw) > MAX_TRANSPORT_FRAME_BYTES:
        raise BrokerTransportError(f"{label} size is invalid")
    try:
        value = json.loads(raw.decode("ascii"), object_pairs_hook=_unique_object)
    except BrokerTransportError:
        raise
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise BrokerTransportError(f"{label} is not canonical JSON") from exc
    if not isinstance(value, dict) or _canonical(value) != raw:
        raise BrokerTransportError(f"{label} is not canonical JSON")
    return value


def _signed_message(
    *, kind: str, payload: Mapping[str, Any], algorithm: str, key_id: str
) -> bytes:
    return _canonical(
        {
            "kind": kind,
            "payload": dict(payload),
            "signature_algorithm": algorithm,
            "signing_key_id": key_id,
        }
    )


def _seal_hello(
    *, kind: str, payload: Mapping[str, Any], signer: IdentitySigner
) -> bytes:
    if signer.algorithm != ED25519_ALGORITHM:
        raise BrokerTransportError("broker transport v1 requires Ed25519 identities")
    key_id = _key_id(signer.key_id, "signing key id")
    message = _signed_message(
        kind=kind,
        payload=payload,
        algorithm=signer.algorithm,
        key_id=key_id,
    )
    envelope = {
        "kind": kind,
        "payload": dict(payload),
        "signature": signer.sign(message),
        "signature_algorithm": signer.algorithm,
        "signing_key_id": key_id,
    }
    raw = _canonical(envelope)
    if len(raw) > MAX_TRANSPORT_FRAME_BYTES:
        raise BrokerTransportError("transport handshake exceeds the fixed ceiling")
    return raw


def _open_hello(
    raw: bytes,
    *,
    expected_kind: str,
    verifier: IdentityVerifier,
) -> Mapping[str, Any]:
    envelope = _decode(raw, label="transport handshake")
    _exact_keys(
        envelope,
        {
            "kind",
            "payload",
            "signature",
            "signature_algorithm",
            "signing_key_id",
        },
        "transport handshake",
    )
    if envelope["kind"] != expected_kind:
        raise BrokerTransportError("transport handshake kind is invalid")
    if envelope["signature_algorithm"] != ED25519_ALGORITHM:
        raise BrokerTransportError("transport handshake algorithm is unsupported")
    if (
        envelope["signature_algorithm"] != verifier.algorithm
        or envelope["signing_key_id"] != verifier.key_id
    ):
        raise BrokerTransportError("transport handshake identity is not pinned")
    payload = envelope["payload"]
    if not isinstance(payload, dict):
        raise BrokerTransportError("transport handshake payload is not an object")
    message = _signed_message(
        kind=expected_kind,
        payload=payload,
        algorithm=str(envelope["signature_algorithm"]),
        key_id=str(envelope["signing_key_id"]),
    )
    try:
        verifier.verify(message, str(envelope["signature"]))
    except Exception as exc:
        raise BrokerTransportError("transport handshake signature is invalid") from exc
    return payload


@dataclass(frozen=True)
class _BrokerHello:
    session_id: str
    broker_key_id: str
    worker_key_id: str
    broker_nonce: str
    broker_ephemeral_key_hex: str
    issued_at: datetime
    expires_at: datetime
    max_frame_bytes: int = MAX_TRANSPORT_FRAME_BYTES
    schema_version: str = BROKER_TRANSPORT_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _safe_id(self.session_id, "transport session id")
        _key_id(self.broker_key_id, "broker key id")
        _key_id(self.worker_key_id, "worker key id")
        _nonce(self.broker_nonce, "broker nonce")
        _x25519_public(self.broker_ephemeral_key_hex, "broker ephemeral key")
        issued = _aware(self.issued_at, "transport issue time")
        expires = _aware(self.expires_at, "transport expiry time")
        if expires <= issued or expires - issued > timedelta(seconds=MAX_HANDSHAKE_SECONDS):
            raise BrokerTransportError(
                "transport lifetime must be positive and at most 30 seconds"
            )
        if self.max_frame_bytes != MAX_TRANSPORT_FRAME_BYTES:
            raise BrokerTransportError("transport frame ceiling is not v1 compatible")
        if self.schema_version != BROKER_TRANSPORT_SCHEMA_VERSION:
            raise BrokerTransportError("transport schema is unsupported")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "session_id": self.session_id,
            "broker_key_id": self.broker_key_id,
            "worker_key_id": self.worker_key_id,
            "broker_nonce": self.broker_nonce,
            "broker_ephemeral_key_hex": self.broker_ephemeral_key_hex,
            "issued_at": self.issued_at.astimezone(timezone.utc).isoformat(),
            "expires_at": self.expires_at.astimezone(timezone.utc).isoformat(),
            "max_frame_bytes": self.max_frame_bytes,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> _BrokerHello:
        _exact_keys(
            data,
            {
                "schema_version",
                "session_id",
                "broker_key_id",
                "worker_key_id",
                "broker_nonce",
                "broker_ephemeral_key_hex",
                "issued_at",
                "expires_at",
                "max_frame_bytes",
            },
            "broker hello payload",
        )
        if isinstance(data["max_frame_bytes"], bool) or not isinstance(
            data["max_frame_bytes"], int
        ):
            raise BrokerTransportError("transport frame ceiling must be an integer")
        try:
            issued_at = datetime.fromisoformat(str(data["issued_at"]))
            expires_at = datetime.fromisoformat(str(data["expires_at"]))
        except ValueError as exc:
            raise BrokerTransportError("transport hello time is invalid") from exc
        return cls(
            session_id=str(data["session_id"]),
            broker_key_id=str(data["broker_key_id"]),
            worker_key_id=str(data["worker_key_id"]),
            broker_nonce=str(data["broker_nonce"]),
            broker_ephemeral_key_hex=str(data["broker_ephemeral_key_hex"]),
            issued_at=issued_at,
            expires_at=expires_at,
            max_frame_bytes=data["max_frame_bytes"],
            schema_version=str(data["schema_version"]),
        )


@dataclass(frozen=True)
class _WorkerHello:
    session_id: str
    broker_key_id: str
    worker_key_id: str
    broker_nonce: str
    worker_nonce: str
    worker_ephemeral_key_hex: str
    broker_hello_digest: str
    expires_at: datetime
    schema_version: str = BROKER_TRANSPORT_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _safe_id(self.session_id, "transport session id")
        _key_id(self.broker_key_id, "broker key id")
        _key_id(self.worker_key_id, "worker key id")
        _nonce(self.broker_nonce, "broker nonce")
        _nonce(self.worker_nonce, "worker nonce")
        _x25519_public(self.worker_ephemeral_key_hex, "worker ephemeral key")
        _digest(self.broker_hello_digest, "broker hello digest")
        _aware(self.expires_at, "transport expiry time")
        if self.schema_version != BROKER_TRANSPORT_SCHEMA_VERSION:
            raise BrokerTransportError("transport schema is unsupported")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "session_id": self.session_id,
            "broker_key_id": self.broker_key_id,
            "worker_key_id": self.worker_key_id,
            "broker_nonce": self.broker_nonce,
            "worker_nonce": self.worker_nonce,
            "worker_ephemeral_key_hex": self.worker_ephemeral_key_hex,
            "broker_hello_digest": self.broker_hello_digest,
            "expires_at": self.expires_at.astimezone(timezone.utc).isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> _WorkerHello:
        _exact_keys(
            data,
            {
                "schema_version",
                "session_id",
                "broker_key_id",
                "worker_key_id",
                "broker_nonce",
                "worker_nonce",
                "worker_ephemeral_key_hex",
                "broker_hello_digest",
                "expires_at",
            },
            "worker hello payload",
        )
        try:
            expires_at = datetime.fromisoformat(str(data["expires_at"]))
        except ValueError as exc:
            raise BrokerTransportError("transport hello time is invalid") from exc
        return cls(
            session_id=str(data["session_id"]),
            broker_key_id=str(data["broker_key_id"]),
            worker_key_id=str(data["worker_key_id"]),
            broker_nonce=str(data["broker_nonce"]),
            worker_nonce=str(data["worker_nonce"]),
            worker_ephemeral_key_hex=str(data["worker_ephemeral_key_hex"]),
            broker_hello_digest=str(data["broker_hello_digest"]),
            expires_at=expires_at,
            schema_version=str(data["schema_version"]),
        )


def _x25519_public(value: str, label: str) -> X25519PublicKey:
    if not re.fullmatch(r"[a-f0-9]{64}", str(value or "")):
        raise BrokerTransportError(f"{label} must be a 32-byte lowercase hex key")
    try:
        return X25519PublicKey.from_public_bytes(bytes.fromhex(value))
    except ValueError as exc:
        raise BrokerTransportError(f"{label} is invalid") from exc


def _public_hex(private_key: X25519PrivateKey) -> str:
    if not isinstance(private_key, X25519PrivateKey):
        raise BrokerTransportError("transport ephemeral key must be X25519")
    return private_key.public_key().public_bytes_raw().hex()


def _derive_keys(
    *,
    private_key: X25519PrivateKey,
    peer_public_hex: str,
    transcript_digest: str,
) -> tuple[bytes, bytes]:
    try:
        shared = private_key.exchange(
            _x25519_public(peer_public_hex, "transport peer ephemeral key")
        )
    except ValueError as exc:
        raise BrokerTransportError("transport key agreement failed") from exc
    material = HKDF(
        algorithm=hashes.SHA256(),
        length=64,
        salt=bytes.fromhex(_digest(transcript_digest, "transport transcript")),
        info=BROKER_TRANSPORT_SCHEMA_VERSION.encode("ascii"),
    ).derive(shared)
    return material[:32], material[32:]


class BrokerTransportHandshake:
    """Pending broker half of one mutually authenticated session."""

    def __init__(
        self,
        *,
        hello: _BrokerHello,
        raw_hello: bytes,
        ephemeral_private_key: X25519PrivateKey,
    ) -> None:
        self._hello = hello
        self._raw_hello = raw_hello
        self._ephemeral_private_key: X25519PrivateKey | None = ephemeral_private_key
        self._finished = False

    @classmethod
    def start(
        cls,
        *,
        session_id: str,
        broker_signer: IdentitySigner,
        worker_key_id: str,
        issued_at: datetime,
        expires_at: datetime,
    ) -> tuple[BrokerTransportHandshake, bytes]:
        ephemeral = X25519PrivateKey.generate()
        hello = _BrokerHello(
            session_id=session_id,
            broker_key_id=broker_signer.key_id,
            worker_key_id=worker_key_id,
            broker_nonce=secrets.token_hex(16),
            broker_ephemeral_key_hex=_public_hex(ephemeral),
            issued_at=_aware(issued_at, "transport issue time"),
            expires_at=_aware(expires_at, "transport expiry time"),
        )
        raw = _seal_hello(
            kind="broker_hello", payload=hello.to_dict(), signer=broker_signer
        )
        return cls(
            hello=hello,
            raw_hello=raw,
            ephemeral_private_key=ephemeral,
        ), raw

    def finish(
        self,
        raw_worker_hello: bytes,
        *,
        worker_verifier: IdentityVerifier,
        now: datetime,
    ) -> AuthenticatedTransportSession:
        if self._finished:
            raise BrokerTransportError("transport handshake is already finished")
        self._finished = True
        ephemeral = self._ephemeral_private_key
        self._ephemeral_private_key = None
        if ephemeral is None:
            raise BrokerTransportError("transport ephemeral key is unavailable")
        when = _aware(now, "transport verification time")
        if when < self._hello.issued_at or when >= self._hello.expires_at:
            raise BrokerTransportError("transport handshake is outside its lifetime")
        payload = _open_hello(
            raw_worker_hello,
            expected_kind="worker_hello",
            verifier=worker_verifier,
        )
        response = _WorkerHello.from_dict(payload)
        expected_digest = hashlib.sha256(self._raw_hello).hexdigest()
        if (
            worker_verifier.key_id != self._hello.worker_key_id
            or response.session_id != self._hello.session_id
            or response.broker_key_id != self._hello.broker_key_id
            or response.worker_key_id != self._hello.worker_key_id
            or response.broker_nonce != self._hello.broker_nonce
            or response.broker_hello_digest != expected_digest
            or response.expires_at != self._hello.expires_at
        ):
            raise BrokerTransportError("worker hello is not bound to the broker hello")
        transcript = hashlib.sha256(
            self._raw_hello + raw_worker_hello
        ).hexdigest()
        broker_to_worker, worker_to_broker = _derive_keys(
            private_key=ephemeral,
            peer_public_hex=response.worker_ephemeral_key_hex,
            transcript_digest=transcript,
        )
        return AuthenticatedTransportSession(
            role=TransportRole.BROKER,
            session_id=self._hello.session_id,
            transcript_digest=transcript,
            expires_at=self._hello.expires_at,
            send_key=broker_to_worker,
            receive_key=worker_to_broker,
        )


class WorkerTransportHandshake:
    """Authenticate one broker hello and return the pinned worker response."""

    @classmethod
    def accept(
        cls,
        raw_broker_hello: bytes,
        *,
        broker_verifier: IdentityVerifier,
        worker_signer: IdentitySigner,
        replay_guard: HandshakeReplayGuard,
        now: datetime,
    ) -> tuple[AuthenticatedTransportSession, bytes]:
        when = _aware(now, "transport verification time")
        payload = _open_hello(
            raw_broker_hello,
            expected_kind="broker_hello",
            verifier=broker_verifier,
        )
        hello = _BrokerHello.from_dict(payload)
        if (
            hello.broker_key_id != broker_verifier.key_id
            or hello.worker_key_id != worker_signer.key_id
        ):
            raise BrokerTransportError("broker hello identities are not pinned")
        if when < hello.issued_at or when >= hello.expires_at:
            raise BrokerTransportError("transport handshake is outside its lifetime")
        hello_digest = hashlib.sha256(raw_broker_hello).hexdigest()
        replay_guard.consume(
            hello_digest,
            now=when,
            expires_at=hello.expires_at,
        )
        if worker_signer.algorithm != ED25519_ALGORITHM:
            raise BrokerTransportError("broker transport v1 requires Ed25519 identities")
        ephemeral = X25519PrivateKey.generate()
        response = _WorkerHello(
            session_id=hello.session_id,
            broker_key_id=hello.broker_key_id,
            worker_key_id=hello.worker_key_id,
            broker_nonce=hello.broker_nonce,
            worker_nonce=secrets.token_hex(16),
            worker_ephemeral_key_hex=_public_hex(ephemeral),
            broker_hello_digest=hello_digest,
            expires_at=hello.expires_at,
        )
        raw_response = _seal_hello(
            kind="worker_hello", payload=response.to_dict(), signer=worker_signer
        )
        transcript = hashlib.sha256(
            raw_broker_hello + raw_response
        ).hexdigest()
        broker_to_worker, worker_to_broker = _derive_keys(
            private_key=ephemeral,
            peer_public_hex=hello.broker_ephemeral_key_hex,
            transcript_digest=transcript,
        )
        session = AuthenticatedTransportSession(
            role=TransportRole.WORKER,
            session_id=hello.session_id,
            transcript_digest=transcript,
            expires_at=hello.expires_at,
            send_key=worker_to_broker,
            receive_key=broker_to_worker,
        )
        return session, raw_response


class AuthenticatedTransportSession:
    """One ephemeral, mutually authenticated, fixed-sequence channel."""

    def __init__(
        self,
        *,
        role: TransportRole,
        session_id: str,
        transcript_digest: str,
        expires_at: datetime,
        send_key: bytes,
        receive_key: bytes,
    ) -> None:
        self.role = TransportRole(role)
        self.session_id = _safe_id(session_id, "transport session id")
        self.transcript_digest = _digest(
            transcript_digest, "transport transcript"
        )
        self.expires_at = _aware(expires_at, "transport expiry time")
        if len(send_key) != 32 or len(receive_key) != 32:
            raise BrokerTransportError("transport session keys must be 32 bytes")
        self._send_key = bytearray(send_key)
        self._receive_key = bytearray(receive_key)
        self._phase = (
            "send_resolve" if self.role is TransportRole.BROKER else "receive_resolve"
        )
        self._closed = False

    @property
    def closed(self) -> bool:
        return self._closed

    @property
    def phase(self) -> str:
        return self._phase

    def close(self) -> None:
        for key in (self._send_key, self._receive_key):
            for index in range(len(key)):
                key[index] = 0
        self._closed = True
        self._phase = "closed"

    def _require_open(self, now: datetime) -> None:
        if self._closed:
            raise BrokerTransportError("transport session is closed")
        if _aware(now, "transport frame time") >= self.expires_at:
            self.close()
            raise BrokerTransportError("transport session has expired")

    def _outgoing(self, message_type: TransportMessageType) -> tuple[int, str, bool]:
        if self.role is TransportRole.BROKER:
            table = {
                ("send_resolve", TransportMessageType.RESOLVE): (
                    1,
                    "receive_resolution",
                    False,
                ),
                ("send_head", TransportMessageType.HEAD): (
                    2,
                    "receive_transport",
                    False,
                ),
            }
        else:
            table = {
                ("send_resolution", TransportMessageType.RESOLUTION): (
                    1,
                    "receive_head",
                    False,
                ),
                ("send_transport", TransportMessageType.TRANSPORT): (
                    2,
                    "closed",
                    True,
                ),
                ("send_resolution", TransportMessageType.ERROR): (1, "closed", True),
                ("send_transport", TransportMessageType.ERROR): (2, "closed", True),
            }
        try:
            return table[(self._phase, message_type)]
        except KeyError as exc:
            raise BrokerTransportError(
                "transport message is out of order or invalid for its sender"
            ) from exc

    def _incoming(self, message_type: TransportMessageType) -> tuple[int, str, bool]:
        if self.role is TransportRole.BROKER:
            table = {
                ("receive_resolution", TransportMessageType.RESOLUTION): (
                    1,
                    "send_head",
                    False,
                ),
                ("receive_transport", TransportMessageType.TRANSPORT): (
                    2,
                    "closed",
                    True,
                ),
                ("receive_resolution", TransportMessageType.ERROR): (1, "closed", True),
                ("receive_transport", TransportMessageType.ERROR): (2, "closed", True),
            }
        else:
            table = {
                ("receive_resolve", TransportMessageType.RESOLVE): (
                    1,
                    "send_resolution",
                    False,
                ),
                ("receive_head", TransportMessageType.HEAD): (
                    2,
                    "send_transport",
                    False,
                ),
            }
        try:
            return table[(self._phase, message_type)]
        except KeyError as exc:
            raise BrokerTransportError(
                "transport message is replayed, out of order, or invalid"
            ) from exc

    @staticmethod
    def _direction(sender: TransportRole) -> str:
        return f"{sender.value}_to_{sender.peer.value}"

    @staticmethod
    def _aead_nonce(sender: TransportRole, sequence: int) -> bytes:
        prefix = b"GTRB" if sender is TransportRole.BROKER else b"GTRW"
        return prefix + sequence.to_bytes(8, "big")

    def seal(
        self,
        message_type: TransportMessageType | str,
        payload: Mapping[str, Any],
        *,
        now: datetime,
    ) -> bytes:
        self._require_open(now)
        try:
            kind = TransportMessageType(message_type)
        except ValueError as exc:
            raise BrokerTransportError("transport message type is unsupported") from exc
        if not isinstance(payload, Mapping):
            raise BrokerTransportError("transport payload must be an object")
        sequence, next_phase, closes = self._outgoing(kind)
        plaintext = _canonical(dict(payload))
        metadata = {
            "schema_version": BROKER_TRANSPORT_SCHEMA_VERSION,
            "session_id": self.session_id,
            "transcript_digest": self.transcript_digest,
            "direction": self._direction(self.role),
            "sequence": sequence,
            "message_type": kind.value,
        }
        aad = _canonical(metadata)
        ciphertext = ChaCha20Poly1305(bytes(self._send_key)).encrypt(
            self._aead_nonce(self.role, sequence), plaintext, aad
        )
        envelope = dict(metadata)
        envelope["ciphertext_b64"] = base64.b64encode(ciphertext).decode("ascii")
        raw = _canonical(envelope)
        if len(raw) > MAX_TRANSPORT_FRAME_BYTES:
            raise BrokerTransportError("transport frame exceeds the fixed ceiling")
        self._phase = next_phase
        if closes:
            self.close()
        return raw

    def open(
        self,
        raw: bytes,
        *,
        now: datetime,
    ) -> tuple[TransportMessageType, Mapping[str, Any]]:
        self._require_open(now)
        envelope = _decode(raw, label="transport frame")
        _exact_keys(
            envelope,
            {
                "schema_version",
                "session_id",
                "transcript_digest",
                "direction",
                "sequence",
                "message_type",
                "ciphertext_b64",
            },
            "transport frame",
        )
        if (
            envelope["schema_version"] != BROKER_TRANSPORT_SCHEMA_VERSION
            or envelope["session_id"] != self.session_id
            or envelope["transcript_digest"] != self.transcript_digest
            or envelope["direction"] != self._direction(self.role.peer)
        ):
            raise BrokerTransportError("transport frame is not bound to this session")
        if isinstance(envelope["sequence"], bool) or not isinstance(
            envelope["sequence"], int
        ):
            raise BrokerTransportError("transport sequence must be an integer")
        try:
            kind = TransportMessageType(envelope["message_type"])
        except (TypeError, ValueError) as exc:
            raise BrokerTransportError("transport message type is unsupported") from exc
        sequence, next_phase, closes = self._incoming(kind)
        if envelope["sequence"] != sequence:
            raise BrokerTransportError("transport sequence is replayed or invalid")
        encoded = envelope["ciphertext_b64"]
        if not isinstance(encoded, str):
            raise BrokerTransportError("transport ciphertext must be base64 text")
        try:
            ciphertext = base64.b64decode(encoded, validate=True)
        except (ValueError, binascii.Error) as exc:
            raise BrokerTransportError("transport ciphertext is not canonical base64") from exc
        if base64.b64encode(ciphertext).decode("ascii") != encoded:
            raise BrokerTransportError("transport ciphertext is not canonical base64")
        metadata = {key: envelope[key] for key in envelope if key != "ciphertext_b64"}
        try:
            plaintext = ChaCha20Poly1305(bytes(self._receive_key)).decrypt(
                self._aead_nonce(self.role.peer, sequence),
                ciphertext,
                _canonical(metadata),
            )
        except InvalidTag as exc:
            raise BrokerTransportError("transport frame authentication failed") from exc
        payload = _decode(plaintext, label="transport payload")
        self._phase = next_phase
        if closes:
            self.close()
        return kind, payload


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
