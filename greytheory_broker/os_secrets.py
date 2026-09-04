"""Operator-side root-KEK providers; never imported by the passive worker."""

# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 ChaseInTech

from __future__ import annotations

import ctypes
import hashlib
import json
import os
import secrets
import tempfile
from collections.abc import Callable, Mapping
from ctypes import wintypes
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol

from greytheory.audit import AuditLog
from greytheory.evidence import find_repository_root


ROOT_KEK_BYTES = 32
ROOT_KEK_RECORD_MAX_BYTES = 65_536
ROOT_KEK_RECORD_SCHEMA = "greytheory.root-kek-provider.v1"
WINDOWS_DPAPI_PROVIDER_ID = "windows-dpapi-current-user-v1"
WINDOWS_DPAPI_SCOPE = "current_user"
WINDOWS_DPAPI_DESCRIPTION = "GreyTheory passive capture root KEK"
WINDOWS_DPAPI_ENTROPY = (
    b"greytheory.root-kek-provider.v1|windows-dpapi-current-user"
)
_CRYPTPROTECT_UI_FORBIDDEN = 0x01


class RootKekProviderError(ValueError):
    """Raised when an OS root-key provider cannot fail closed."""


class DpapiBackend(Protocol):
    """Narrow injectable boundary around Windows DPAPI."""

    def protect(self, data: bytes, *, entropy: bytes, description: str) -> bytes: ...

    def unprotect(
        self, data: bytes, *, entropy: bytes
    ) -> tuple[bytes, str]: ...


class RootKekLease:
    """Short-lived mutable root-key material that zeroes itself on close."""

    def __init__(self, material: bytes, *, provider_id: str) -> None:
        if not isinstance(material, bytes) or len(material) != ROOT_KEK_BYTES:
            raise RootKekProviderError("root KEK lease requires exactly 32 bytes")
        self.provider_id = str(provider_id)
        self._material = bytearray(material)
        self._closed = False

    @property
    def material(self) -> memoryview:
        if self._closed:
            raise RootKekProviderError("root KEK lease is closed")
        return memoryview(self._material)

    @property
    def closed(self) -> bool:
        return self._closed

    def close(self) -> None:
        if not getattr(self, "_closed", True):
            for index in range(len(self._material)):
                self._material[index] = 0
            self._closed = True

    def __enter__(self) -> RootKekLease:
        if self._closed:
            raise RootKekProviderError("root KEK lease is closed")
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def __repr__(self) -> str:
        state = "closed" if self._closed else "active"
        return f"RootKekLease(provider_id={self.provider_id!r}, state={state!r})"

    def __del__(self) -> None:  # pragma: no cover - best-effort finalizer
        try:
            self.close()
        except Exception:
            pass


class _DataBlob(ctypes.Structure):
    _fields_ = [
        ("cbData", wintypes.DWORD),
        ("pbData", ctypes.POINTER(ctypes.c_ubyte)),
    ]


def _input_blob(data: bytes) -> tuple[_DataBlob, ctypes.Array[ctypes.c_char]]:
    buffer = ctypes.create_string_buffer(data, len(data))
    blob = _DataBlob(
        len(data), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_ubyte))
    )
    return blob, buffer


class WindowsDpapiBackend:
    """Direct `CRYPTPROTECT_UI_FORBIDDEN` CurrentUser DPAPI adapter."""

    def __init__(self) -> None:
        if os.name != "nt":
            raise RootKekProviderError("Windows DPAPI is available only on Windows")
        self._crypt32 = ctypes.WinDLL("Crypt32.dll", use_last_error=True)
        self._kernel32 = ctypes.WinDLL("Kernel32.dll", use_last_error=True)
        self._crypt32.CryptProtectData.argtypes = [
            ctypes.POINTER(_DataBlob),
            wintypes.LPCWSTR,
            ctypes.POINTER(_DataBlob),
            ctypes.c_void_p,
            ctypes.c_void_p,
            wintypes.DWORD,
            ctypes.POINTER(_DataBlob),
        ]
        self._crypt32.CryptProtectData.restype = wintypes.BOOL
        self._crypt32.CryptUnprotectData.argtypes = [
            ctypes.POINTER(_DataBlob),
            ctypes.POINTER(wintypes.LPWSTR),
            ctypes.POINTER(_DataBlob),
            ctypes.c_void_p,
            ctypes.c_void_p,
            wintypes.DWORD,
            ctypes.POINTER(_DataBlob),
        ]
        self._crypt32.CryptUnprotectData.restype = wintypes.BOOL
        self._kernel32.LocalFree.argtypes = [ctypes.c_void_p]
        self._kernel32.LocalFree.restype = ctypes.c_void_p

    def protect(self, data: bytes, *, entropy: bytes, description: str) -> bytes:
        source, source_buffer = _input_blob(data)
        entropy_blob, entropy_buffer = _input_blob(entropy)
        output = _DataBlob()
        _ = (source_buffer, entropy_buffer)
        if not self._crypt32.CryptProtectData(
            ctypes.byref(source),
            description,
            ctypes.byref(entropy_blob),
            None,
            None,
            _CRYPTPROTECT_UI_FORBIDDEN,
            ctypes.byref(output),
        ):
            raise RootKekProviderError(
                f"Windows DPAPI protection failed: {ctypes.WinError(ctypes.get_last_error())}"
            )
        try:
            return ctypes.string_at(output.pbData, output.cbData)
        finally:
            self._kernel32.LocalFree(output.pbData)

    def unprotect(self, data: bytes, *, entropy: bytes) -> tuple[bytes, str]:
        source, source_buffer = _input_blob(data)
        entropy_blob, entropy_buffer = _input_blob(entropy)
        output = _DataBlob()
        description = wintypes.LPWSTR()
        _ = (source_buffer, entropy_buffer)
        if not self._crypt32.CryptUnprotectData(
            ctypes.byref(source),
            ctypes.byref(description),
            ctypes.byref(entropy_blob),
            None,
            None,
            _CRYPTPROTECT_UI_FORBIDDEN,
            ctypes.byref(output),
        ):
            raise RootKekProviderError(
                f"Windows DPAPI unprotection failed: {ctypes.WinError(ctypes.get_last_error())}"
            )
        try:
            return ctypes.string_at(output.pbData, output.cbData), str(
                description.value or ""
            )
        finally:
            if description:
                self._kernel32.LocalFree(description)
            self._kernel32.LocalFree(output.pbData)


def _aware(value: datetime, label: str) -> datetime:
    if value.tzinfo is None:
        raise RootKekProviderError(f"{label} must be timezone-aware")
    return value.astimezone(timezone.utc)


def _required(value: str, label: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise RootKekProviderError(f"{label} is required")
    return text


def _canonical(value: Mapping[str, Any]) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("utf-8")


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise RootKekProviderError(f"duplicate root KEK record key {key!r}")
        result[key] = value
    return result


class WindowsDpapiRootKekProvider:
    """Persist a 32-byte root KEK under the current Windows user profile."""

    provider_id = WINDOWS_DPAPI_PROVIDER_ID
    scope = WINDOWS_DPAPI_SCOPE

    def __init__(
        self,
        path: str | os.PathLike[str],
        *,
        audit: AuditLog,
        backend: DpapiBackend | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self.path = Path(path).expanduser().resolve()
        if find_repository_root(self.path.parent) is not None:
            raise RootKekProviderError("root KEK records are refused inside a Git worktree")
        if not isinstance(audit, AuditLog):
            raise RootKekProviderError("root KEK provider requires an audit log")
        self.audit = audit
        self._backend = backend if backend is not None else WindowsDpapiBackend()
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    def provision(self, *, actor: str, authorization_ref: str) -> None:
        actor = _required(actor, "root KEK actor")
        authorization_ref = _required(
            authorization_ref, "root KEK authorization reference"
        )
        if self.path.exists():
            raise RootKekProviderError("root KEK record already exists")
        created_at = _aware(self._clock(), "root KEK provision time")
        material = bytearray(secrets.token_bytes(ROOT_KEK_BYTES))
        try:
            payload = {
                "schema_version": ROOT_KEK_RECORD_SCHEMA,
                "provider_id": self.provider_id,
                "scope": self.scope,
                "created_at": created_at.isoformat(),
                "key_hex": bytes(material).hex(),
            }
            protected = self._backend.protect(
                _canonical(payload),
                entropy=WINDOWS_DPAPI_ENTROPY,
                description=WINDOWS_DPAPI_DESCRIPTION,
            )
        finally:
            for index in range(len(material)):
                material[index] = 0
        record = {
            "schema_version": ROOT_KEK_RECORD_SCHEMA,
            "provider_id": self.provider_id,
            "scope": self.scope,
            "protected_payload_hex": protected.hex(),
        }
        self._write(record)
        self._audit(
            "broker.root_kek.provision",
            actor,
            authorization_ref,
            detail={"record_sha256": hashlib.sha256(_canonical(record)).hexdigest()},
        )

    def lease(self, *, actor: str, authorization_ref: str) -> RootKekLease:
        actor = _required(actor, "root KEK actor")
        authorization_ref = _required(
            authorization_ref, "root KEK authorization reference"
        )
        record = self._read()
        try:
            protected = bytes.fromhex(str(record["protected_payload_hex"]))
        except ValueError as exc:
            raise RootKekProviderError("root KEK protected payload is not hex") from exc
        if not protected:
            raise RootKekProviderError("root KEK protected payload is empty")
        plaintext, description = self._backend.unprotect(
            protected, entropy=WINDOWS_DPAPI_ENTROPY
        )
        if description != WINDOWS_DPAPI_DESCRIPTION:
            raise RootKekProviderError("root KEK DPAPI description does not match")
        try:
            payload = json.loads(
                plaintext.decode("utf-8"), object_pairs_hook=_unique_object
            )
            if not isinstance(payload, dict):
                raise RootKekProviderError("root KEK protected payload must be an object")
            expected = {
                "schema_version",
                "provider_id",
                "scope",
                "created_at",
                "key_hex",
            }
            if set(payload) != expected:
                raise RootKekProviderError("root KEK protected payload keys are invalid")
            if payload["schema_version"] != ROOT_KEK_RECORD_SCHEMA:
                raise RootKekProviderError("root KEK protected schema is unsupported")
            if payload["provider_id"] != self.provider_id or payload["scope"] != self.scope:
                raise RootKekProviderError("root KEK protected provider binding is invalid")
            _aware(datetime.fromisoformat(str(payload["created_at"])), "root KEK creation time")
            material = bytes.fromhex(str(payload["key_hex"]))
        except (UnicodeDecodeError, json.JSONDecodeError, ValueError, TypeError) as exc:
            if isinstance(exc, RootKekProviderError):
                raise
            raise RootKekProviderError(f"root KEK protected payload is invalid: {exc}") from exc
        if len(material) != ROOT_KEK_BYTES:
            raise RootKekProviderError("root KEK protected material is not 32 bytes")
        self._audit(
            "broker.root_kek.lease",
            actor,
            authorization_ref,
            detail={"record_sha256": hashlib.sha256(_canonical(record)).hexdigest()},
        )
        return RootKekLease(material, provider_id=self.provider_id)

    def _read(self) -> dict[str, Any]:
        if not self.path.is_file():
            raise RootKekProviderError("root KEK record does not exist")
        try:
            with self.path.open("rb") as stream:
                encoded = stream.read(ROOT_KEK_RECORD_MAX_BYTES + 1)
            if not encoded:
                raise RootKekProviderError("root KEK record is empty")
            if len(encoded) > ROOT_KEK_RECORD_MAX_BYTES:
                raise RootKekProviderError("root KEK record exceeds its size ceiling")
            record = json.loads(
                encoded.decode("utf-8"), object_pairs_hook=_unique_object
            )
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise RootKekProviderError(f"cannot read root KEK record: {exc}") from exc
        if not isinstance(record, dict):
            raise RootKekProviderError("root KEK record must be an object")
        expected = {
            "schema_version",
            "provider_id",
            "scope",
            "protected_payload_hex",
        }
        if set(record) != expected:
            raise RootKekProviderError("root KEK record keys are invalid")
        if record["schema_version"] != ROOT_KEK_RECORD_SCHEMA:
            raise RootKekProviderError("root KEK record schema is unsupported")
        if record["provider_id"] != self.provider_id or record["scope"] != self.scope:
            raise RootKekProviderError("root KEK record provider binding is invalid")
        return record

    def _write(self, record: Mapping[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        try:
            self.path.parent.chmod(0o700)
        except OSError:
            pass
        handle, name = tempfile.mkstemp(
            prefix="root-kek-", suffix=".tmp", dir=self.path.parent
        )
        temporary = Path(name)
        try:
            with os.fdopen(handle, "w", encoding="utf-8", newline="\n") as stream:
                json.dump(record, stream, indent=2, sort_keys=True)
                stream.write("\n")
                stream.flush()
                os.fsync(stream.fileno())
            try:
                os.link(temporary, self.path)
            except FileExistsError as exc:
                raise RootKekProviderError("root KEK record already exists") from exc
            temporary.unlink()
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
        *,
        detail: Mapping[str, Any],
    ) -> None:
        self.audit.append(
            actor=actor,
            action=action,
            authority_ref=authorization_ref,
            detail={
                "authorization_ref": authorization_ref,
                "provider_id": self.provider_id,
                "scope": self.scope,
                **dict(detail),
            },
        )


def open_capture_key_store(
    root: str | os.PathLike[str],
    *,
    provider: WindowsDpapiRootKekProvider,
    audit: AuditLog,
    actor: str,
    authorization_ref: str,
):
    """Derive a capture-key store from one short-lived OS-protected lease."""

    from greytheory_broker.keys import CaptureKeyStore

    if not isinstance(provider, WindowsDpapiRootKekProvider):
        raise RootKekProviderError("capture key store requires the Windows DPAPI provider")
    with provider.lease(actor=actor, authorization_ref=authorization_ref) as lease:
        return CaptureKeyStore(
            root,
            key_encryption_key=lease.material,
            audit=audit,
        )


__all__ = [
    "ROOT_KEK_BYTES",
    "ROOT_KEK_RECORD_MAX_BYTES",
    "ROOT_KEK_RECORD_SCHEMA",
    "WINDOWS_DPAPI_DESCRIPTION",
    "WINDOWS_DPAPI_ENTROPY",
    "WINDOWS_DPAPI_PROVIDER_ID",
    "WINDOWS_DPAPI_SCOPE",
    "DpapiBackend",
    "RootKekLease",
    "RootKekProviderError",
    "WindowsDpapiBackend",
    "WindowsDpapiRootKekProvider",
    "open_capture_key_store",
]
