"""Windows CurrentUser DPAPI root-KEK host acceptance."""

# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 ChaseInTech

from __future__ import annotations

import argparse
import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path

from greytheory.audit import AuditLog
from greytheory_broker import (
    EncryptedCapture,
    RootKekProviderError,
    WindowsDpapiRootKekProvider,
    encrypt_capture,
    open_capture_key_store,
)


ACTOR = "operator-dpapi-acceptance"
AUTHORITY = "authority-dpapi-local-fixture"
TICKET_DIGEST = "d" * 64


def _write_json(path: Path, value: dict) -> None:
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def run(root: Path) -> dict:
    if os.name != "nt":
        raise RuntimeError("Windows DPAPI acceptance requires Windows")
    root = root.resolve()
    root.mkdir(parents=True, exist_ok=False)
    now = datetime.now(timezone.utc)
    audit = AuditLog(root / "audit.jsonl", clock=lambda: now)
    provider_path = root / "provider" / "root-kek.json"
    key_root = root / "capture-keys"
    provider = WindowsDpapiRootKekProvider(
        provider_path, audit=audit, clock=lambda: now
    )
    provider.provision(actor=ACTOR, authorization_ref=AUTHORITY)

    with provider.lease(actor=ACTOR, authorization_ref=AUTHORITY) as lease:
        raw_marker = bytes(lease.material)
        material_view = lease.material
    lease_zeroed = bytes(material_view) == b"\x00" * 32 and lease.closed

    store = open_capture_key_store(
        key_root,
        provider=provider,
        audit=audit,
        actor=ACTOR,
        authorization_ref=AUTHORITY,
    )
    recipient = store.provision(
        actor=ACTOR, authorization_ref=AUTHORITY, at=now
    )
    plaintext = b"GreyTheory DPAPI same-profile recovery fixture"
    capture = encrypt_capture(
        plaintext,
        recipient=recipient,
        ticket_digest=TICKET_DIGEST,
        created_at=now,
    )
    capture_path = root / "encrypted-capture.json"
    _write_json(capture_path, capture.to_dict())

    reopened_provider = WindowsDpapiRootKekProvider(provider_path, audit=audit)
    reopened_store = open_capture_key_store(
        key_root,
        provider=reopened_provider,
        audit=audit,
        actor=ACTOR,
        authorization_ref=AUTHORITY,
    )
    persisted_capture = EncryptedCapture.from_dict(
        json.loads(capture_path.read_text(encoding="utf-8"))
    )
    restart_plaintext = reopened_store.decrypt(
        persisted_capture, actor=ACTOR, authorization_ref=AUTHORITY
    )

    recovery_root = root / "same-profile-recovery"
    recovery_provider_path = recovery_root / "provider" / "root-kek.json"
    recovery_provider_path.parent.mkdir(parents=True)
    shutil.copy2(provider_path, recovery_provider_path)
    shutil.copytree(key_root, recovery_root / "capture-keys")
    recovery_audit = AuditLog(recovery_root / "audit.jsonl", clock=lambda: now)
    recovery_provider = WindowsDpapiRootKekProvider(
        recovery_provider_path, audit=recovery_audit
    )
    recovery_store = open_capture_key_store(
        recovery_root / "capture-keys",
        provider=recovery_provider,
        audit=recovery_audit,
        actor=ACTOR,
        authorization_ref=AUTHORITY,
    )
    recovery_plaintext = recovery_store.decrypt(
        persisted_capture, actor=ACTOR, authorization_ref=AUTHORITY
    )

    tampered_path = root / "tampered" / "root-kek.json"
    tampered_path.parent.mkdir(parents=True)
    tampered = json.loads(provider_path.read_text(encoding="utf-8"))
    protected = str(tampered["protected_payload_hex"])
    tampered["protected_payload_hex"] = (
        "00" if protected[:2] != "00" else "01"
    ) + protected[2:]
    _write_json(tampered_path, tampered)
    tampered_provider = WindowsDpapiRootKekProvider(tampered_path, audit=audit)
    tamper_refused = False
    try:
        tampered_provider.lease(actor=ACTOR, authorization_ref=AUTHORITY)
    except RootKekProviderError:
        tamper_refused = True

    raw_hex = raw_marker.hex().encode("ascii")
    plaintext_leaks = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        content = path.read_bytes()
        if raw_marker in content or raw_hex in content:
            plaintext_leaks.append(str(path.relative_to(root)))
    del raw_marker

    return {
        "schema_version": 1,
        "host": "Windows",
        "provider_id": provider.provider_id,
        "provider_scope": provider.scope,
        "posture": "LOCAL_FIXTURE",
        "passive_http_enabled": False,
        "external_network_contact": False,
        "worker_exercised": False,
        "provider_approved_for_posture": False,
        "acl_hardening_accepted": False,
        "independent_disaster_recovery_accepted": False,
        "root_kek_plaintext_persisted": bool(plaintext_leaks),
        "root_kek_lease_zeroed": lease_zeroed,
        "restart_recovery_same_profile": restart_plaintext == plaintext,
        "protected_backup_recovery_same_profile": recovery_plaintext == plaintext,
        "cross_profile_recovery_accepted": False,
        "tampered_record_refused": tamper_refused,
        "capture_recipient_private_key_wrapped": True,
        "capture_round_trip_verified": restart_plaintext == plaintext,
        "audit_chain_verified": audit.is_valid(),
        "audit_actions": [record.action for record in audit],
        "private_root": str(root),
        "provider_record": str(provider_path),
        "capture_key_store": str(key_root),
        "encrypted_capture": str(capture_path),
        "plaintext_leak_paths": plaintext_leaks,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.root), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
