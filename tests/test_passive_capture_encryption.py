"""Offline confidentiality and key-lifecycle proof for passive captures."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone

import pytest

from greytheory.audit import AuditLog
from greytheory_broker import (
    CaptureEncryptionError,
    CaptureKeyError,
    CaptureKeyStatus,
    CaptureKeyStore,
    EncryptedCapture,
    encrypt_capture,
)


NOW = datetime(2026, 8, 25, 9, 0, tzinfo=timezone.utc)
TICKET_DIGEST = "a" * 64
ACTOR = "fixture-operator"
AUTHORITY = "authority-passive-fixture"


def decrypt(store, capture):
    return store.decrypt(
        capture,
        actor=ACTOR,
        authorization_ref=AUTHORITY,
    )


def test_key_store_wraps_rotates_and_recovers_old_and_current_captures(tmp_path):
    key_root = tmp_path / "operator-capture-keys"
    audit = AuditLog(tmp_path / "audit.jsonl", clock=lambda: NOW)
    store = CaptureKeyStore(
        key_root,
        key_encryption_key=b"k" * 32,
        audit=audit,
    )

    first = store.provision(
        actor=ACTOR,
        authorization_ref=AUTHORITY,
        at=NOW,
    )
    first_capture = encrypt_capture(
        b"first immutable response",
        recipient=first,
        ticket_digest=TICKET_DIGEST,
        created_at=NOW,
    )
    assert decrypt(store, first_capture) == b"first immutable response"

    persisted = store.path.read_text(encoding="utf-8")
    assert (b"k" * 32).hex() not in persisted
    assert "wrapped_private_key_hex" in persisted
    assert '"private_key_hex"' not in persisted

    second = store.provision(
        actor=ACTOR,
        authorization_ref=AUTHORITY,
        at=NOW + timedelta(hours=1),
    )
    records = store.records()
    assert [(item.id, item.status) for item in records] == [
        (first.key_id, CaptureKeyStatus.RETIRED),
        (second.key_id, CaptureKeyStatus.ACTIVE),
    ]
    assert store.active_recipient() == second
    assert records[0].retired_by == ACTOR
    assert records[0].retirement_authorization_ref == AUTHORITY
    assert decrypt(store, first_capture) == b"first immutable response"

    second_capture = encrypt_capture(
        b"second immutable response",
        recipient=second,
        ticket_digest=TICKET_DIGEST,
        created_at=NOW + timedelta(hours=1),
    )
    reopened = CaptureKeyStore(
        key_root,
        key_encryption_key=b"k" * 32,
        audit=audit,
    )
    assert decrypt(reopened, second_capture) == b"second immutable response"
    with pytest.raises(CaptureKeyError, match="authentication"):
        CaptureKeyStore(
            key_root,
            key_encryption_key=b"z" * 32,
            audit=audit,
        ).records()

    actions = [record.action for record in audit]
    assert actions == [
        "broker.capture_key.provision",
        "broker.capture.decrypt",
        "broker.capture_key.rotate",
        "broker.capture.decrypt",
        "broker.capture.decrypt",
    ]
    assert all(
        record.authority_ref == "authority-passive-fixture" for record in audit
    )


def test_revocation_requires_authority_and_removes_active_recipient(tmp_path):
    store = CaptureKeyStore(
        tmp_path / "operator-capture-keys",
        key_encryption_key=b"k" * 32,
        audit=AuditLog(tmp_path / "audit.jsonl", clock=lambda: NOW),
    )
    recipient = store.provision(
        actor=ACTOR,
        authorization_ref=AUTHORITY,
        at=NOW,
    )
    capture = encrypt_capture(
        b"retained evidence",
        recipient=recipient,
        ticket_digest=TICKET_DIGEST,
        created_at=NOW,
    )

    with pytest.raises(CaptureKeyError, match="authorization"):
        store.revoke(
            recipient.key_id,
            actor=ACTOR,
            authorization_ref="",
            reason="fixture compromise drill",
            at=NOW + timedelta(minutes=1),
        )
    with pytest.raises(CaptureKeyError, match="decrypt actor"):
        store.decrypt(capture, actor="", authorization_ref=AUTHORITY)
    revoked = store.revoke(
        recipient.key_id,
        actor=ACTOR,
        authorization_ref=AUTHORITY,
        reason="fixture compromise drill",
        at=NOW + timedelta(minutes=1),
    )
    assert revoked.status is CaptureKeyStatus.REVOKED
    assert revoked.revoked_by == ACTOR
    assert revoked.revocation_authorization_ref == AUTHORITY
    with pytest.raises(CaptureKeyError, match="no single active"):
        store.active_recipient()
    assert decrypt(store, capture) == b"retained evidence"


def test_capture_envelope_tampering_fails_authentication(tmp_path):
    store = CaptureKeyStore(
        tmp_path / "operator-capture-keys",
        key_encryption_key=b"k" * 32,
        audit=AuditLog(tmp_path / "audit.jsonl", clock=lambda: NOW),
    )
    recipient = store.provision(
        actor=ACTOR,
        authorization_ref=AUTHORITY,
        at=NOW,
    )
    capture = encrypt_capture(
        b"authenticated evidence",
        recipient=recipient,
        ticket_digest=TICKET_DIGEST,
        created_at=NOW,
    )
    round_trip = EncryptedCapture.from_dict(capture.to_dict())
    assert round_trip == capture
    assert decrypt(store, round_trip) == b"authenticated evidence"

    changed_ciphertext = ("00" if capture.ciphertext_hex[:2] != "00" else "01")
    tampered_ciphertext = replace(
        capture,
        ciphertext_hex=changed_ciphertext + capture.ciphertext_hex[2:],
    )
    with pytest.raises(CaptureEncryptionError, match="authentication"):
        decrypt(store, tampered_ciphertext)

    tampered_metadata = replace(capture, capture_bytes=capture.capture_bytes + 1)
    with pytest.raises(CaptureEncryptionError, match="authentication"):
        decrypt(store, tampered_metadata)


def test_capture_inputs_are_strictly_typed_and_ticket_bound(tmp_path):
    store = CaptureKeyStore(
        tmp_path / "operator-capture-keys",
        key_encryption_key=b"k" * 32,
        audit=AuditLog(tmp_path / "audit.jsonl", clock=lambda: NOW),
    )
    recipient = store.provision(
        actor=ACTOR,
        authorization_ref=AUTHORITY,
        at=NOW,
    )
    with pytest.raises(CaptureEncryptionError, match="ticket digest"):
        encrypt_capture(
            b"response",
            recipient=recipient,
            ticket_digest="not-a-digest",
            created_at=NOW,
        )
    with pytest.raises(CaptureEncryptionError, match="must be bytes"):
        encrypt_capture(
            8,
            recipient=recipient,
            ticket_digest=TICKET_DIGEST,
            created_at=NOW,
        )
    with pytest.raises(CaptureEncryptionError, match="timezone-aware"):
        encrypt_capture(
            b"response",
            recipient=recipient,
            ticket_digest=TICKET_DIGEST,
            created_at=NOW.replace(tzinfo=None),
        )
    with pytest.raises(CaptureEncryptionError, match="predate"):
        encrypt_capture(
            b"response",
            recipient=recipient,
            ticket_digest=TICKET_DIGEST,
            created_at=NOW - timedelta(seconds=1),
        )
