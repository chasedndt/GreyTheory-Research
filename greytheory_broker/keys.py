"""Governed, KEK-wrapped recipient keys for passive capture envelopes."""

# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 ChaseInTech

from __future__ import annotations

import hashlib
import hmac
import json
import os
import tempfile
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Mapping

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from greytheory.audit import AuditLog
from greytheory.evidence import find_repository_root
from greytheory_broker.encryption import (
    CAPTURE_ALGORITHM,
    CaptureRecipient,
    EncryptedCapture,
    decrypt_capture,
)


KEY_STORE_SCHEMA = "greytheory.passive-capture-keys.v1"
KEY_WRAP_ALGORITHM = "aes-256-gcm"


class CaptureKeyError(ValueError):
    """Raised when recipient key state is unsafe, corrupt, or unauthorized."""


class CaptureKeyStatus(str, Enum):
    ACTIVE = "active"
    RETIRED = "retired"
    REVOKED = "revoked"


def _aware(value: datetime, label: str) -> datetime:
    if value.tzinfo is None:
        raise CaptureKeyError(f"{label} must be timezone-aware")
    return value.astimezone(timezone.utc)


def _required(value: str, label: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise CaptureKeyError(f"{label} is required")
    return text


def _canonical(value: Mapping[str, Any]) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("utf-8")


@dataclass(frozen=True)
class CaptureKeyRecord:
    recipient: CaptureRecipient
    status: CaptureKeyStatus
    wrapped_private_key_hex: str
    wrap_nonce_hex: str
    created_by: str
    authorization_ref: str
    retired_at: datetime | None = None
    retired_by: str = ""
    retirement_authorization_ref: str = ""
    revoked_at: datetime | None = None
    revoked_by: str = ""
    revocation_authorization_ref: str = ""
    revocation_reason: str = ""
    wrap_algorithm: str = KEY_WRAP_ALGORITHM

    def __post_init__(self) -> None:
        if not isinstance(self.status, CaptureKeyStatus):
            raise CaptureKeyError("capture key status is invalid")
        if self.wrap_algorithm != KEY_WRAP_ALGORITHM:
            raise CaptureKeyError("unsupported capture-key wrapping algorithm")
        if len(self.wrap_nonce_hex) != 24:
            raise CaptureKeyError("capture-key wrap nonce must be 12 bytes")
        if len(self.wrapped_private_key_hex) != 96:
            raise CaptureKeyError("wrapped capture private key is invalid")
        try:
            bytes.fromhex(self.wrap_nonce_hex)
            bytes.fromhex(self.wrapped_private_key_hex)
        except ValueError as exc:
            raise CaptureKeyError("wrapped capture key fields must be hex") from exc
        _required(self.created_by, "capture key creator")
        _required(self.authorization_ref, "capture key authorization reference")
        if self.status is CaptureKeyStatus.ACTIVE:
            if any(
                (
                    self.retired_at is not None,
                    bool(self.retired_by),
                    bool(self.retirement_authorization_ref),
                    self.revoked_at is not None,
                    bool(self.revoked_by),
                    bool(self.revocation_authorization_ref),
                    bool(self.revocation_reason),
                )
            ):
                raise CaptureKeyError("active capture key has terminal state")
        if self.status is CaptureKeyStatus.RETIRED:
            if self.retired_at is None:
                raise CaptureKeyError("retired capture key requires a retirement time")
            _required(self.retired_by, "capture key retirement actor")
            _required(
                self.retirement_authorization_ref,
                "capture key retirement authorization reference",
            )
            if any(
                (
                    self.revoked_at is not None,
                    bool(self.revoked_by),
                    bool(self.revocation_authorization_ref),
                    bool(self.revocation_reason),
                )
            ):
                raise CaptureKeyError("retired capture key has revocation state")
        if self.status is CaptureKeyStatus.REVOKED:
            if self.revoked_at is None or not self.revocation_reason.strip():
                raise CaptureKeyError(
                    "revoked capture key requires a time and reason"
                )
            _required(self.revoked_by, "capture key revocation actor")
            _required(
                self.revocation_authorization_ref,
                "capture key revocation authorization reference",
            )
        if self.retired_at is not None:
            _aware(self.retired_at, "capture key retirement time")
        if self.revoked_at is not None:
            _aware(self.revoked_at, "capture key revocation time")

    @property
    def id(self) -> str:
        return self.recipient.key_id

    def _wrap_aad_dict(self) -> dict[str, str]:
        return {
            "schema_version": KEY_STORE_SCHEMA,
            "wrap_algorithm": self.wrap_algorithm,
            "key_id": self.id,
            "public_key_hex": self.recipient.public_key_hex,
            "created_at": self.recipient.created_at.astimezone(timezone.utc).isoformat(),
        }

    @property
    def wrap_aad(self) -> bytes:
        return _canonical(self._wrap_aad_dict())

    def to_dict(self) -> dict[str, Any]:
        return {
            "recipient": self.recipient.to_dict(),
            "status": self.status.value,
            "wrapped_private_key_hex": self.wrapped_private_key_hex,
            "wrap_nonce_hex": self.wrap_nonce_hex,
            "wrap_algorithm": self.wrap_algorithm,
            "created_by": self.created_by,
            "authorization_ref": self.authorization_ref,
            "retired_at": (
                self.retired_at.astimezone(timezone.utc).isoformat()
                if self.retired_at is not None
                else None
            ),
            "retired_by": self.retired_by,
            "retirement_authorization_ref": self.retirement_authorization_ref,
            "revoked_at": (
                self.revoked_at.astimezone(timezone.utc).isoformat()
                if self.revoked_at is not None
                else None
            ),
            "revoked_by": self.revoked_by,
            "revocation_authorization_ref": self.revocation_authorization_ref,
            "revocation_reason": self.revocation_reason,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> CaptureKeyRecord:
        return cls(
            recipient=CaptureRecipient.from_dict(data["recipient"]),
            status=CaptureKeyStatus(str(data["status"])),
            wrapped_private_key_hex=str(data["wrapped_private_key_hex"]),
            wrap_nonce_hex=str(data["wrap_nonce_hex"]),
            created_by=str(data["created_by"]),
            authorization_ref=str(data["authorization_ref"]),
            retired_at=(
                datetime.fromisoformat(str(data["retired_at"]))
                if data.get("retired_at") is not None
                else None
            ),
            retired_by=str(data.get("retired_by", "")),
            retirement_authorization_ref=str(
                data.get("retirement_authorization_ref", "")
            ),
            revoked_at=(
                datetime.fromisoformat(str(data["revoked_at"]))
                if data.get("revoked_at") is not None
                else None
            ),
            revoked_by=str(data.get("revoked_by", "")),
            revocation_authorization_ref=str(
                data.get("revocation_authorization_ref", "")
            ),
            revocation_reason=str(data.get("revocation_reason", "")),
            wrap_algorithm=str(data["wrap_algorithm"]),
        )


class CaptureKeyStore:
    """Persist wrapped private keys; never persist the external KEK."""

    def __init__(
        self,
        root: str | os.PathLike[str],
        *,
        key_encryption_key: bytes,
        audit: AuditLog,
    ) -> None:
        self.root = Path(root).expanduser().resolve()
        if find_repository_root(self.root) is not None:
            raise CaptureKeyError("capture keys are refused inside a Git worktree")
        if not isinstance(key_encryption_key, (bytes, bytearray, memoryview)):
            raise CaptureKeyError("capture key-encryption key must be bytes")
        root_kek = bytes(key_encryption_key)
        if len(root_kek) != 32:
            raise CaptureKeyError("capture key-encryption key must be exactly 32 bytes")
        self._wrap_key = hmac.new(
            root_kek,
            b"greytheory.passive-capture-keys.v1|wrap",
            hashlib.sha256,
        ).digest()
        self._manifest_mac_key = hmac.new(
            root_kek,
            b"greytheory.passive-capture-keys.v1|manifest",
            hashlib.sha256,
        ).digest()
        if not isinstance(audit, AuditLog):
            raise CaptureKeyError("capture key store requires an audit log")
        self.root.mkdir(parents=True, exist_ok=True)
        try:
            self.root.chmod(0o700)
        except OSError:
            pass
        self.path = self.root / "capture-keys.json"
        self.audit = audit

    def records(self) -> tuple[CaptureKeyRecord, ...]:
        if not self.path.exists():
            return ()
        try:
            envelope = json.loads(self.path.read_text(encoding="utf-8"))
            if set(envelope) != {"payload", "mac"}:
                raise CaptureKeyError("capture key store envelope is invalid")
            payload = envelope["payload"]
            if not isinstance(payload, dict):
                raise CaptureKeyError("capture key store payload is invalid")
            expected = hmac.new(
                self._manifest_mac_key,
                _canonical(payload),
                hashlib.sha256,
            ).hexdigest()
            if not hmac.compare_digest(str(envelope["mac"]), expected):
                raise CaptureKeyError("capture key store authentication failed")
            if payload.get("schema_version") != KEY_STORE_SCHEMA:
                raise CaptureKeyError("capture key store schema is unsupported")
            records = tuple(
                CaptureKeyRecord.from_dict(item) for item in payload.get("keys", [])
            )
        except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
            raise CaptureKeyError(f"cannot load capture key store: {exc}") from exc
        ids = [item.id for item in records]
        if len(ids) != len(set(ids)):
            raise CaptureKeyError("capture key store contains duplicate key ids")
        if sum(item.status is CaptureKeyStatus.ACTIVE for item in records) > 1:
            raise CaptureKeyError("capture key store contains multiple active keys")
        return records

    def provision(
        self,
        *,
        actor: str,
        authorization_ref: str,
        at: datetime,
    ) -> CaptureRecipient:
        actor = _required(actor, "capture key actor")
        authorization_ref = _required(
            authorization_ref, "capture key authorization reference"
        )
        when = _aware(at, "capture key provision time")
        records = list(self.records())
        rotating = any(
            item.status is CaptureKeyStatus.ACTIVE for item in records
        )
        if any(
            item.status is CaptureKeyStatus.ACTIVE
            and item.recipient.created_at.astimezone(timezone.utc) > when
            for item in records
        ):
            raise CaptureKeyError("capture key rotation cannot be backdated")
        records = [
            replace(
                item,
                status=CaptureKeyStatus.RETIRED,
                retired_at=when,
                retired_by=actor,
                retirement_authorization_ref=authorization_ref,
            )
            if item.status is CaptureKeyStatus.ACTIVE
            else item
            for item in records
        ]
        private_key = X25519PrivateKey.generate()
        recipient = CaptureRecipient.from_public_key(
            private_key.public_key(), created_at=when
        )
        nonce = os.urandom(12)
        template = CaptureKeyRecord(
            recipient=recipient,
            status=CaptureKeyStatus.ACTIVE,
            wrapped_private_key_hex="00" * 48,
            wrap_nonce_hex=nonce.hex(),
            created_by=actor,
            authorization_ref=authorization_ref,
        )
        wrapped = AESGCM(self._wrap_key).encrypt(
            nonce,
            private_key.private_bytes_raw(),
            template.wrap_aad,
        )
        records.append(
            replace(template, wrapped_private_key_hex=wrapped.hex())
        )
        self._write(records)
        self._audit(
            (
                "broker.capture_key.rotate"
                if rotating
                else "broker.capture_key.provision"
            ),
            actor,
            authorization_ref,
            recipient.key_id,
        )
        return recipient

    def active_recipient(self) -> CaptureRecipient:
        active = [
            item for item in self.records() if item.status is CaptureKeyStatus.ACTIVE
        ]
        if len(active) != 1:
            raise CaptureKeyError("capture key store has no single active recipient")
        return active[0].recipient

    def revoke(
        self,
        key_id: str,
        *,
        actor: str,
        authorization_ref: str,
        reason: str,
        at: datetime,
    ) -> CaptureKeyRecord:
        actor = _required(actor, "capture key actor")
        authorization_ref = _required(
            authorization_ref, "capture key authorization reference"
        )
        reason = _required(reason, "capture key revocation reason")
        when = _aware(at, "capture key revocation time")
        records = list(self.records())
        for index, item in enumerate(records):
            if item.id != key_id:
                continue
            if item.status is CaptureKeyStatus.REVOKED:
                raise CaptureKeyError("capture key is already revoked")
            if item.recipient.created_at.astimezone(timezone.utc) > when:
                raise CaptureKeyError("capture key revocation cannot be backdated")
            if (
                item.retired_at is not None
                and item.retired_at.astimezone(timezone.utc) > when
            ):
                raise CaptureKeyError(
                    "capture key revocation cannot predate retirement"
                )
            updated = replace(
                item,
                status=CaptureKeyStatus.REVOKED,
                revoked_at=when,
                revoked_by=actor,
                revocation_authorization_ref=authorization_ref,
                revocation_reason=reason,
            )
            records[index] = updated
            self._write(records)
            self._audit(
                "broker.capture_key.revoke",
                actor,
                authorization_ref,
                item.id,
            )
            return updated
        raise CaptureKeyError(f"unknown capture key {key_id!r}")

    def decrypt(
        self,
        envelope: EncryptedCapture,
        *,
        actor: str,
        authorization_ref: str,
    ) -> bytes:
        actor = _required(actor, "capture decrypt actor")
        authorization_ref = _required(
            authorization_ref, "capture decrypt authorization reference"
        )
        if type(envelope) is not EncryptedCapture:
            raise CaptureKeyError("capture decrypt requires a typed envelope")
        record = next(
            (item for item in self.records() if item.id == envelope.key_id), None
        )
        if record is None:
            raise CaptureKeyError("capture envelope references an unknown key")
        try:
            private_bytes = AESGCM(self._wrap_key).decrypt(
                bytes.fromhex(record.wrap_nonce_hex),
                bytes.fromhex(record.wrapped_private_key_hex),
                record.wrap_aad,
            )
        except InvalidTag as exc:
            raise CaptureKeyError("wrapped capture private key authentication failed") from exc
        private_key = X25519PrivateKey.from_private_bytes(private_bytes)
        plaintext = decrypt_capture(envelope, private_key=private_key)
        self._audit(
            "broker.capture.decrypt",
            actor,
            authorization_ref,
            record.id,
            detail={
                "ticket_digest": envelope.ticket_digest,
                "capture_envelope_sha256": envelope.envelope_sha256,
                "capture_sha256": envelope.capture_sha256,
            },
        )
        return plaintext

    def _write(self, records: list[CaptureKeyRecord]) -> None:
        payload = {
            "schema_version": KEY_STORE_SCHEMA,
            "keys": [item.to_dict() for item in records],
        }
        envelope = {
            "payload": payload,
            "mac": hmac.new(
                self._manifest_mac_key,
                _canonical(payload),
                hashlib.sha256,
            ).hexdigest(),
        }
        encoded = json.dumps(envelope, indent=2, sort_keys=True) + "\n"
        handle, name = tempfile.mkstemp(
            prefix="capture-keys-", suffix=".tmp", dir=self.root
        )
        temporary = Path(name)
        try:
            with os.fdopen(handle, "w", encoding="utf-8", newline="\n") as stream:
                stream.write(encoded)
                stream.flush()
                os.fsync(stream.fileno())
            temporary.replace(self.path)
            try:
                self.path.chmod(0o600)
            except OSError:
                pass
        except Exception:
            temporary.unlink(missing_ok=True)
            raise

    def _audit(
        self,
        action: str,
        actor: str,
        authorization_ref: str,
        key_id: str,
        *,
        detail: Mapping[str, Any] | None = None,
    ) -> None:
        self.audit.append(
            actor=actor,
            action=action,
            authority_ref=authorization_ref,
            detail={
                "authorization_ref": authorization_ref,
                "key_id": key_id,
                "capture_algorithm": CAPTURE_ALGORITHM,
                "key_wrap_algorithm": KEY_WRAP_ALGORITHM,
                **dict(detail or {}),
            },
        )


__all__ = [
    "KEY_STORE_SCHEMA",
    "KEY_WRAP_ALGORITHM",
    "CaptureKeyError",
    "CaptureKeyRecord",
    "CaptureKeyStatus",
    "CaptureKeyStore",
]
