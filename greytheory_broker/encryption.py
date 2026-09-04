"""Typed capture envelopes for the dark passive-worker boundary."""

# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 ChaseInTech

from __future__ import annotations

import hashlib
import json
import os
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric.x25519 import (
    X25519PrivateKey,
    X25519PublicKey,
)
from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305
from cryptography.hazmat.primitives.kdf.hkdf import HKDF


CAPTURE_SCHEMA_VERSION = "greytheory.passive-capture.v1"
CAPTURE_ALGORITHM = "x25519-hkdf-sha256-chacha20poly1305"
SAFE_KEY_ID = re.compile(r"^x25519:[a-f0-9]{32}$")
SHA256 = re.compile(r"^[a-f0-9]{64}$")
HEX_32 = re.compile(r"^[a-f0-9]{64}$")
HEX_12 = re.compile(r"^[a-f0-9]{24}$")


class CaptureEncryptionError(ValueError):
    """Raised when capture confidentiality or binding cannot be proven."""


def _aware(value: datetime, label: str) -> datetime:
    if value.tzinfo is None:
        raise CaptureEncryptionError(f"{label} must be timezone-aware")
    return value.astimezone(timezone.utc)


def _canonical(value: Mapping[str, Any]) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("utf-8")


def _key_id(public_bytes: bytes) -> str:
    return f"x25519:{hashlib.sha256(public_bytes).hexdigest()[:32]}"


@dataclass(frozen=True)
class CaptureRecipient:
    """Public encryption material safe to provision to a lower-trust worker."""

    key_id: str
    public_key_hex: str
    created_at: datetime
    algorithm: str = CAPTURE_ALGORITHM

    def __post_init__(self) -> None:
        if self.algorithm != CAPTURE_ALGORITHM:
            raise CaptureEncryptionError("unsupported capture encryption algorithm")
        if not SAFE_KEY_ID.fullmatch(self.key_id):
            raise CaptureEncryptionError("capture recipient key id is invalid")
        if not HEX_32.fullmatch(self.public_key_hex):
            raise CaptureEncryptionError("X25519 public key must be 32-byte hex")
        if _key_id(bytes.fromhex(self.public_key_hex)) != self.key_id:
            raise CaptureEncryptionError("capture recipient key id does not match")
        _aware(self.created_at, "capture recipient creation time")

    @classmethod
    def from_public_key(
        cls, public_key: X25519PublicKey, *, created_at: datetime
    ) -> CaptureRecipient:
        raw = public_key.public_bytes_raw()
        return cls(_key_id(raw), raw.hex(), created_at)

    @property
    def public_key(self) -> X25519PublicKey:
        return X25519PublicKey.from_public_bytes(bytes.fromhex(self.public_key_hex))

    def to_dict(self) -> dict[str, str]:
        return {
            "algorithm": self.algorithm,
            "key_id": self.key_id,
            "public_key_hex": self.public_key_hex,
            "created_at": self.created_at.astimezone(timezone.utc).isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> CaptureRecipient:
        return cls(
            key_id=str(data["key_id"]),
            public_key_hex=str(data["public_key_hex"]),
            created_at=datetime.fromisoformat(str(data["created_at"])),
            algorithm=str(data["algorithm"]),
        )


@dataclass(frozen=True)
class EncryptedCapture:
    """One AEAD envelope bound to one ticket digest and recipient key."""

    ticket_digest: str
    key_id: str
    capture_sha256: str
    capture_bytes: int
    ephemeral_public_key_hex: str
    nonce_hex: str
    ciphertext_hex: str
    created_at: datetime
    algorithm: str = CAPTURE_ALGORITHM
    schema_version: str = CAPTURE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema_version != CAPTURE_SCHEMA_VERSION:
            raise CaptureEncryptionError("unsupported capture envelope schema")
        if self.algorithm != CAPTURE_ALGORITHM:
            raise CaptureEncryptionError("unsupported capture encryption algorithm")
        if not SHA256.fullmatch(self.ticket_digest):
            raise CaptureEncryptionError("capture ticket digest is invalid")
        if not SAFE_KEY_ID.fullmatch(self.key_id):
            raise CaptureEncryptionError("capture key id is invalid")
        if not SHA256.fullmatch(self.capture_sha256):
            raise CaptureEncryptionError("capture digest is invalid")
        if (
            isinstance(self.capture_bytes, bool)
            or not isinstance(self.capture_bytes, int)
            or self.capture_bytes < 0
        ):
            raise CaptureEncryptionError(
                "capture byte count must be a non-negative integer"
            )
        if not HEX_32.fullmatch(self.ephemeral_public_key_hex):
            raise CaptureEncryptionError("ephemeral X25519 key must be 32-byte hex")
        if not HEX_12.fullmatch(self.nonce_hex):
            raise CaptureEncryptionError("capture nonce must be 12-byte hex")
        if (
            len(self.ciphertext_hex) < 32
            or len(self.ciphertext_hex) % 2
            or any(ch not in "0123456789abcdef" for ch in self.ciphertext_hex)
        ):
            raise CaptureEncryptionError("capture ciphertext is invalid")
        _aware(self.created_at, "capture encryption time")

    def _aad_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "algorithm": self.algorithm,
            "ticket_digest": self.ticket_digest,
            "key_id": self.key_id,
            "capture_sha256": self.capture_sha256,
            "capture_bytes": self.capture_bytes,
            "created_at": self.created_at.astimezone(timezone.utc).isoformat(),
        }

    @property
    def associated_data(self) -> bytes:
        return _canonical(self._aad_dict())

    def to_dict(self) -> dict[str, Any]:
        return {
            **self._aad_dict(),
            "ephemeral_public_key_hex": self.ephemeral_public_key_hex,
            "nonce_hex": self.nonce_hex,
            "ciphertext_hex": self.ciphertext_hex,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> EncryptedCapture:
        return cls(
            ticket_digest=str(data["ticket_digest"]),
            key_id=str(data["key_id"]),
            capture_sha256=str(data["capture_sha256"]),
            capture_bytes=int(data["capture_bytes"]),
            ephemeral_public_key_hex=str(data["ephemeral_public_key_hex"]),
            nonce_hex=str(data["nonce_hex"]),
            ciphertext_hex=str(data["ciphertext_hex"]),
            created_at=datetime.fromisoformat(str(data["created_at"])),
            algorithm=str(data["algorithm"]),
            schema_version=str(data["schema_version"]),
        )

    @property
    def encoded(self) -> bytes:
        return _canonical(self.to_dict())

    @property
    def envelope_sha256(self) -> str:
        return hashlib.sha256(self.encoded).hexdigest()


def _derive_key(shared_secret: bytes, *, ticket_digest: str, key_id: str) -> bytes:
    return HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=bytes.fromhex(ticket_digest),
        info=f"greytheory-passive-capture-v1|{key_id}".encode("ascii"),
    ).derive(shared_secret)


def encrypt_capture(
    plaintext: bytes,
    *,
    recipient: CaptureRecipient,
    ticket_digest: str,
    created_at: datetime,
) -> EncryptedCapture:
    """Encrypt bytes using only the worker-safe public recipient."""
    if not SHA256.fullmatch(ticket_digest):
        raise CaptureEncryptionError("capture ticket digest is invalid")
    if type(recipient) is not CaptureRecipient:
        raise CaptureEncryptionError("capture recipient must be typed")
    if not isinstance(plaintext, (bytes, bytearray, memoryview)):
        raise CaptureEncryptionError("capture plaintext must be bytes")
    encrypted_at = _aware(created_at, "capture encryption time")
    if recipient.created_at.astimezone(timezone.utc) > encrypted_at:
        raise CaptureEncryptionError("capture encryption cannot predate its recipient")
    raw = bytes(plaintext)
    ephemeral = X25519PrivateKey.generate()
    shared = ephemeral.exchange(recipient.public_key)
    key = _derive_key(shared, ticket_digest=ticket_digest, key_id=recipient.key_id)
    nonce = os.urandom(12)
    template = EncryptedCapture(
        ticket_digest=ticket_digest,
        key_id=recipient.key_id,
        capture_sha256=hashlib.sha256(raw).hexdigest(),
        capture_bytes=len(raw),
        ephemeral_public_key_hex=ephemeral.public_key().public_bytes_raw().hex(),
        nonce_hex=nonce.hex(),
        ciphertext_hex="00" * 16,
        created_at=encrypted_at,
    )
    ciphertext = ChaCha20Poly1305(key).encrypt(
        nonce, raw, template.associated_data
    )
    return EncryptedCapture.from_dict(
        {**template.to_dict(), "ciphertext_hex": ciphertext.hex()}
    )


def decrypt_capture(
    envelope: EncryptedCapture,
    *,
    private_key: X25519PrivateKey,
) -> bytes:
    """Decrypt and verify digest/length using operator-held private material."""
    if type(envelope) is not EncryptedCapture:
        raise CaptureEncryptionError("capture envelope must be typed")
    if not isinstance(private_key, X25519PrivateKey):
        raise CaptureEncryptionError("capture private key must be X25519")
    public_id = _key_id(private_key.public_key().public_bytes_raw())
    if public_id != envelope.key_id:
        raise CaptureEncryptionError("capture private key does not match envelope")
    ephemeral = X25519PublicKey.from_public_bytes(
        bytes.fromhex(envelope.ephemeral_public_key_hex)
    )
    shared = private_key.exchange(ephemeral)
    key = _derive_key(
        shared,
        ticket_digest=envelope.ticket_digest,
        key_id=envelope.key_id,
    )
    try:
        plaintext = ChaCha20Poly1305(key).decrypt(
            bytes.fromhex(envelope.nonce_hex),
            bytes.fromhex(envelope.ciphertext_hex),
            envelope.associated_data,
        )
    except InvalidTag as exc:
        raise CaptureEncryptionError("capture envelope authentication failed") from exc
    if len(plaintext) != envelope.capture_bytes:
        raise CaptureEncryptionError("decrypted capture length does not match")
    if hashlib.sha256(plaintext).hexdigest() != envelope.capture_sha256:
        raise CaptureEncryptionError("decrypted capture digest does not match")
    return plaintext


__all__ = [
    "CAPTURE_ALGORITHM",
    "CAPTURE_SCHEMA_VERSION",
    "CaptureEncryptionError",
    "CaptureRecipient",
    "EncryptedCapture",
    "decrypt_capture",
    "encrypt_capture",
]
