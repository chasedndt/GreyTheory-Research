"""The audit log must make silent edits detectable, not merely discouraged."""

from __future__ import annotations

import json

import pytest

from greytheory.audit import GENESIS, AuditLog, AuditVerificationError


def test_first_record_starts_the_chain(tmp_path):
    log = AuditLog(tmp_path / "audit.jsonl")
    record = log.append(actor="chase", action="test.action")

    assert record.seq == 0
    assert record.prev_hash == GENESIS
    assert record.hash == record.digest()


def test_records_chain_to_their_predecessor(tmp_path):
    log = AuditLog(tmp_path / "audit.jsonl")
    first = log.append(actor="chase", action="one")
    second = log.append(actor="chase", action="two")

    assert second.seq == 1
    assert second.prev_hash == first.hash
    log.verify()


def test_a_clean_log_verifies(tmp_path):
    log = AuditLog(tmp_path / "audit.jsonl")
    for i in range(5):
        log.append(actor="chase", action=f"action_{i}", detail={"i": i})

    log.verify()
    assert log.is_valid()
    assert len(log.records()) == 5


def test_editing_a_record_breaks_the_chain(tmp_path):
    path = tmp_path / "audit.jsonl"
    log = AuditLog(path)
    log.append(actor="chase", action="gate.evaluate", detail={"allowed": False})
    log.append(actor="chase", action="gate.evaluate", detail={"allowed": False})

    # Flip a denial into an allow after the fact — the exact tampering the
    # chain exists to catch.
    lines = path.read_text(encoding="utf-8").splitlines()
    tampered = json.loads(lines[0])
    tampered["detail"]["allowed"] = True
    lines[0] = json.dumps(tampered, sort_keys=True, separators=(",", ":"))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    assert not log.is_valid()
    with pytest.raises(AuditVerificationError, match="has been modified"):
        log.verify()


def test_removing_a_record_breaks_the_chain(tmp_path):
    path = tmp_path / "audit.jsonl"
    log = AuditLog(path)
    for i in range(3):
        log.append(actor="chase", action=f"action_{i}")

    lines = path.read_text(encoding="utf-8").splitlines()
    path.write_text("\n".join([lines[0], lines[2]]) + "\n", encoding="utf-8")

    with pytest.raises(AuditVerificationError, match="sequence break"):
        log.verify()


def test_log_survives_reopening(tmp_path):
    path = tmp_path / "audit.jsonl"
    AuditLog(path).append(actor="chase", action="one")
    AuditLog(path).append(actor="chase", action="two")

    reopened = AuditLog(path)
    assert len(reopened.records()) == 2
    reopened.verify()


def test_authority_reference_is_recorded(tmp_path):
    log = AuditLog(tmp_path / "audit.jsonl")
    record = log.append(actor="chase", action="gate.evaluate", authority_ref="abc123")
    assert record.authority_ref == "abc123"
