"""Asymmetric Ed25519 ticket and receipt signing primitives.

Key persistence, provisioning, rotation, and hardware/OS protection are outside
this module and remain required before a worker can be activated.
"""

# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 ChaseInTech

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from typing import Protocol

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)


ED25519_ALGORITHM = "ed25519"
ED25519_SIGNATURE = re.compile(r"^[a-f0-9]{128}$")


class SigningError(ValueError):
    """Raised when a signing key or signature is invalid or mismatched."""


class MessageVerifier(Protocol):
    algorithm: str
    key_id: str

    def verify(self, message: bytes, signature: str) -> None: ...


class MessageSigner(MessageVerifier, Protocol):
    def sign(self, message: bytes) -> str: ...


def _key_id(public_bytes: bytes) -> str:
    return f"ed25519:{hashlib.sha256(public_bytes).hexdigest()[:32]}"


@dataclass(frozen=True)
class Ed25519Verifier:
    """Public verification material safe to provision to a worker."""

    _key: Ed25519PublicKey
    algorithm: str = ED25519_ALGORITHM

    @classmethod
    def from_public_bytes(cls, value: bytes) -> Ed25519Verifier:
        try:
            return cls(Ed25519PublicKey.from_public_bytes(bytes(value)))
        except ValueError as exc:
            raise SigningError("Ed25519 public keys must contain exactly 32 bytes") from exc

    @property
    def public_bytes(self) -> bytes:
        return self._key.public_bytes_raw()

    @property
    def key_id(self) -> str:
        return _key_id(self.public_bytes)

    def verify(self, message: bytes, signature: str) -> None:
        if not ED25519_SIGNATURE.fullmatch(str(signature or "")):
            raise SigningError("Ed25519 signatures must be 64-byte lowercase hex")
        try:
            self._key.verify(bytes.fromhex(signature), bytes(message))
        except InvalidSignature as exc:
            raise SigningError("Ed25519 signature verification failed") from exc


@dataclass(frozen=True)
class Ed25519Signer:
    """Private signing material; never serialised into ticket/receipt records."""

    _key: Ed25519PrivateKey
    algorithm: str = ED25519_ALGORITHM

    @classmethod
    def generate(cls) -> Ed25519Signer:
        return cls(Ed25519PrivateKey.generate())

    @classmethod
    def from_private_bytes(cls, value: bytes) -> Ed25519Signer:
        try:
            return cls(Ed25519PrivateKey.from_private_bytes(bytes(value)))
        except ValueError as exc:
            raise SigningError("Ed25519 private keys must contain exactly 32 bytes") from exc

    @property
    def private_bytes(self) -> bytes:
        return self._key.private_bytes_raw()

    @property
    def verifier(self) -> Ed25519Verifier:
        return Ed25519Verifier(self._key.public_key())

    @property
    def public_bytes(self) -> bytes:
        return self.verifier.public_bytes

    @property
    def key_id(self) -> str:
        return self.verifier.key_id

    def sign(self, message: bytes) -> str:
        return self._key.sign(bytes(message)).hex()

    def verify(self, message: bytes, signature: str) -> None:
        self.verifier.verify(message, signature)


__all__ = [
    "ED25519_ALGORITHM",
    "Ed25519Signer",
    "Ed25519Verifier",
    "MessageSigner",
    "MessageVerifier",
    "SigningError",
]
