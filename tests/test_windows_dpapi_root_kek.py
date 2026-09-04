from __future__ import annotations

import hashlib
import hmac
import json
import os
from datetime import datetime, timezone
from pathlib import Path

import pytest

from greytheory.audit import AuditLog
from greytheory_broker import (
    RootKekLease,
    RootKekProviderError,
    WindowsDpapiRootKekProvider,
    encrypt_capture,
    open_capture_key_store,
)
from greytheory_broker.os_secrets import (
    WINDOWS_DPAPI_DESCRIPTION,
)


NOW = datetime(2026, 9, 4, 9, 45, tzinfo=timezone.utc)
ACTOR = "fixture-operator"
AUTHORITY = "authority-root-kek-fixture"
ROOT = Path(__file__).resolve().parents[1]


class BoundBackend:
    """Authenticated reversible fake for platform-independent provider tests."""

    def __init__(self, binding: bytes = b"fixture-profile-binding") -> None:
        self.binding = binding

    def protect(self, data: bytes, *, entropy: bytes, description: str) -> bytes:
        stream = hashlib.sha256(self.binding + entropy).digest()
        ciphertext = bytes(value ^ stream[index % len(stream)] for index, value in enumerate(data))
        tag = hmac.new(self.binding, entropy + ciphertext, hashlib.sha256).digest()
        assert description == WINDOWS_DPAPI_DESCRIPTION
        return tag + ciphertext

    def unprotect(self, data: bytes, *, entropy: bytes) -> tuple[bytes, str]:
        tag, ciphertext = data[:32], data[32:]
        expected = hmac.new(self.binding, entropy + ciphertext, hashlib.sha256).digest()
        if not hmac.compare_digest(tag, expected):
            raise RootKekProviderError("fixture profile binding refused")
        stream = hashlib.sha256(self.binding + entropy).digest()
        plaintext = bytes(
            value ^ stream[index % len(stream)] for index, value in enumerate(ciphertext)
        )
        return plaintext, WINDOWS_DPAPI_DESCRIPTION


def provider(tmp_path: Path, *, backend: BoundBackend | None = None):
    audit = AuditLog(tmp_path / "audit.jsonl", clock=lambda: NOW)
    return (
        WindowsDpapiRootKekProvider(
            tmp_path / "root-kek.json",
            audit=audit,
            backend=backend or BoundBackend(),
            clock=lambda: NOW,
        ),
        audit,
    )


def test_dpapi_provider_opens_capture_store_and_zeroes_lease(tmp_path: Path) -> None:
    root_provider, audit = provider(tmp_path)
    root_provider.provision(actor=ACTOR, authorization_ref=AUTHORITY)

    with root_provider.lease(actor=ACTOR, authorization_ref=AUTHORITY) as lease:
        material = bytes(lease.material)
        view = lease.material
        store = open_capture_key_store(
            tmp_path / "capture-keys",
            provider=root_provider,
            audit=audit,
            actor=ACTOR,
            authorization_ref=AUTHORITY,
        )
    assert lease.closed is True
    assert bytes(view) == b"\x00" * 32
    with pytest.raises(RootKekProviderError, match="closed"):
        _ = lease.material

    persisted = root_provider.path.read_text(encoding="utf-8")
    assert material.hex() not in persisted
    assert '"key_hex"' not in persisted
    recipient = store.provision(actor=ACTOR, authorization_ref=AUTHORITY, at=NOW)
    capture = encrypt_capture(
        b"same-profile protected recovery",
        recipient=recipient,
        ticket_digest="a" * 64,
        created_at=NOW,
    )

    reopened = open_capture_key_store(
        tmp_path / "capture-keys",
        provider=root_provider,
        audit=audit,
        actor=ACTOR,
        authorization_ref=AUTHORITY,
    )
    assert (
        reopened.decrypt(capture, actor=ACTOR, authorization_ref=AUTHORITY)
        == b"same-profile protected recovery"
    )
    actions = [record.action for record in audit]
    assert actions[:4] == [
        "broker.root_kek.provision",
        "broker.root_kek.lease",
        "broker.root_kek.lease",
        "broker.capture_key.provision",
    ]


def test_dpapi_provider_refuses_reprovision_tamper_and_wrong_binding(tmp_path: Path) -> None:
    root_provider, _ = provider(tmp_path)
    root_provider.provision(actor=ACTOR, authorization_ref=AUTHORITY)
    with pytest.raises(RootKekProviderError, match="already exists"):
        root_provider.provision(actor=ACTOR, authorization_ref=AUTHORITY)

    original = json.loads(root_provider.path.read_text(encoding="utf-8"))
    record = dict(original)
    protected = str(record["protected_payload_hex"])
    record["protected_payload_hex"] = (
        "00" if protected[:2] != "00" else "01"
    ) + protected[2:]
    root_provider.path.write_text(json.dumps(record), encoding="utf-8")
    with pytest.raises(RootKekProviderError, match="binding refused"):
        root_provider.lease(actor=ACTOR, authorization_ref=AUTHORITY)

    other_provider, _ = provider(tmp_path / "other", backend=BoundBackend(b"other-profile"))
    other_provider.path.parent.mkdir(parents=True, exist_ok=True)
    other_provider.path.write_text(json.dumps(original), encoding="utf-8")
    with pytest.raises(RootKekProviderError, match="binding refused"):
        other_provider.lease(actor=ACTOR, authorization_ref=AUTHORITY)


def test_dpapi_provider_bounds_the_protected_record(tmp_path: Path) -> None:
    root_provider, _ = provider(tmp_path)
    root_provider.path.write_bytes(b"{" + (b"x" * 65_536))
    with pytest.raises(RootKekProviderError, match="size ceiling"):
        root_provider.lease(actor=ACTOR, authorization_ref=AUTHORITY)


def test_dpapi_provider_never_replaces_an_existing_record(tmp_path: Path) -> None:
    root_provider, _ = provider(tmp_path)
    original = b"operator-owned-existing-record"
    root_provider.path.write_bytes(original)

    with pytest.raises(RootKekProviderError, match="already exists"):
        root_provider._write({"candidate": "must-not-replace"})
    assert root_provider.path.read_bytes() == original


def test_dpapi_provider_refuses_git_storage_and_missing_authority(tmp_path: Path) -> None:
    with pytest.raises(RootKekProviderError, match="Git worktree"):
        WindowsDpapiRootKekProvider(
            ROOT / ".unsafe-root-kek.json",
            audit=AuditLog(tmp_path / "audit.jsonl", clock=lambda: NOW),
            backend=BoundBackend(),
        )
    root_provider, _ = provider(tmp_path)
    with pytest.raises(RootKekProviderError, match="actor"):
        root_provider.provision(actor="", authorization_ref=AUTHORITY)
    with pytest.raises(RootKekProviderError, match="authorization"):
        root_provider.provision(actor=ACTOR, authorization_ref="")


def test_uninitialised_lease_cleanup_is_safe() -> None:
    lease = RootKekLease.__new__(RootKekLease)
    lease.close()


def test_windows_acceptance_keeps_candidate_boundaries_explicit() -> None:
    harness = (ROOT / "acceptance" / "windows_dpapi_root_kek.py").read_text(
        encoding="utf-8"
    )
    wrapper = (
        ROOT / "acceptance" / "run-windows-dpapi-root-kek.ps1"
    ).read_text(encoding="utf-8")

    for marker in (
        '"provider_approved_for_posture": False',
        '"acl_hardening_accepted": False',
        '"independent_disaster_recovery_accepted": False',
        '"cross_profile_recovery_accepted": False',
        '"worker_exercised": False',
        '"external_network_contact": False',
    ):
        assert marker in harness
    for marker in (
        "$record.provider_approved_for_posture -ne $false",
        "$record.acl_hardening_accepted -ne $false",
        "$record.independent_disaster_recovery_accepted -ne $false",
        "$record.cross_profile_recovery_accepted -ne $false",
        "$record.root_kek_plaintext_persisted -ne $false",
    ):
        assert marker in wrapper


@pytest.mark.skipif(os.name != "nt", reason="Windows DPAPI host proof")
def test_real_windows_current_user_dpapi_round_trip(tmp_path: Path) -> None:
    audit = AuditLog(tmp_path / "audit.jsonl", clock=lambda: NOW)
    root_provider = WindowsDpapiRootKekProvider(
        tmp_path / "root-kek.json",
        audit=audit,
        clock=lambda: NOW,
    )
    root_provider.provision(actor=ACTOR, authorization_ref=AUTHORITY)
    with root_provider.lease(actor=ACTOR, authorization_ref=AUTHORITY) as lease:
        assert len(lease.material) == 32
    assert lease.closed is True
