"""Offline full-path acceptance for the bounded Ubuntu passive worker.

The wrapper runs this file as a non-root, capability-empty process inside an
ephemeral network namespace with only loopback and no default route. A synthetic
globally-routable-looking address and hosts entry terminate at the owned local
TLS canary; no packet can leave the namespace.
"""

# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 ChaseInTech

from __future__ import annotations

import json
import os
import platform
import secrets
import socket
import ssl
import sys
import tempfile
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey

from greytheory.audit import AuditLog
from greytheory.authority.gate import AuthorityLevel, Gate, Reason
from greytheory.authority.scope import (
    AssetPattern,
    ContractStatus,
    PatternType,
    ScopeClassification,
    ScopeContract,
)
from greytheory.research import ActionRequest, AssetKind, EffectBudget, TargetAsset
from greytheory_broker import (
    BrokerKillSwitch,
    CaptureRecipient,
    Ed25519Signer,
    PassiveTicketIssuer,
    TicketReplayLedger,
    decrypt_capture,
)
from greytheory_worker import PassiveWorkerAssembly, WORKER_ID, WORKER_VERSION


CANARY_ADDRESS = "8.8.8.8"
CANARY_HOST = "greytheory-canary.invalid"
CANARY_URL = f"https://{CANARY_HOST}/acceptance"
CANARY_PORT = 443
ROOT = Path(__file__).resolve().parents[1]
CERTIFICATE = ROOT / "acceptance" / "fixtures" / "ubuntu-canary-cert.pem"
PRIVATE_KEY = ROOT / "acceptance" / "fixtures" / "ubuntu-canary-key.pem"
HEADERS = (
    b"HTTP/1.1 200 OK\r\n"
    b"Content-Type: text/plain\r\n"
    b"X-GreyTheory-Canary: local-only\r\n\r\n"
)
EXPECTED_REQUEST = (
    b"HEAD /acceptance HTTP/1.1\r\n"
    b"Host: greytheory-canary.invalid\r\n"
    b"User-Agent: GreyTheory-Passive/0.1\r\n"
    b"Accept: */*\r\n"
    b"Accept-Encoding: identity\r\n"
    b"Connection: close\r\n\r\n"
)


class AcceptanceError(RuntimeError):
    """Raised when host behavior does not prove the acceptance contract."""


def _os_release() -> dict[str, str]:
    values: dict[str, str] = {}
    for raw_line in Path("/etc/os-release").read_text(encoding="utf-8").splitlines():
        if "=" in raw_line:
            key, value = raw_line.split("=", 1)
            values[key] = value.strip().strip('"')
    return values


def _has_default_route() -> bool:
    lines = Path("/proc/net/route").read_text(encoding="ascii").splitlines()[1:]
    return any(
        len(fields) >= 8
        and fields[1] == "00000000"
        and fields[7] == "00000000"
        for fields in (line.split() for line in lines)
    )


def _security_status() -> dict[str, Any]:
    values: dict[str, str] = {}
    for line in Path("/proc/self/status").read_text(encoding="ascii").splitlines():
        key, separator, value = line.partition(":")
        if separator:
            values[key] = value.strip()
    return {
        "effective_capabilities": int(values["CapEff"], 16),
        "bounding_capabilities": int(values["CapBnd"], 16),
        "no_new_privileges": values["NoNewPrivs"] == "1",
    }


def _assert_isolated_unprivileged_host() -> dict[str, Any]:
    if sys.platform != "linux":
        raise AcceptanceError("Ubuntu worker acceptance requires Linux")
    release = _os_release()
    if release.get("ID") != "ubuntu" or release.get("VERSION_ID") != "24.04":
        raise AcceptanceError("acceptance requires Ubuntu 24.04")
    interfaces = tuple(name for _, name in socket.if_nameindex())
    if interfaces != ("lo",) or _has_default_route():
        raise AcceptanceError(
            "worker namespace must expose only loopback and no default route"
        )
    security = _security_status()
    if (
        os.geteuid() == 0
        or os.getegid() == 0
        or security["effective_capabilities"] != 0
        or security["bounding_capabilities"] != 0
        or security["no_new_privileges"] is not True
    ):
        raise AcceptanceError(
            "acceptance process must be non-root, capability-empty, and no-new-privileges"
        )
    return {
        "distribution": release.get("PRETTY_NAME", "Ubuntu 24.04"),
        "kernel": platform.release(),
        "interfaces": list(interfaces),
        "default_route": False,
        "effective_uid": os.geteuid(),
        "effective_gid": os.getegid(),
        **security,
    }


class _CanaryServer:
    def __init__(self) -> None:
        self.request = b""
        self.error: BaseException | None = None
        self._listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._listener.settimeout(10.0)
        self._listener.bind((CANARY_ADDRESS, CANARY_PORT))
        self._listener.listen(1)
        self._thread = threading.Thread(
            target=self._serve,
            name="greytheory-owned-worker-canary",
            daemon=False,
        )

    def start(self) -> None:
        self._thread.start()

    def _serve(self) -> None:
        try:
            raw, _ = self._listener.accept()
            raw.settimeout(10.0)
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            context.minimum_version = ssl.TLSVersion.TLSv1_2
            context.load_cert_chain(certfile=CERTIFICATE, keyfile=PRIVATE_KEY)
            context.set_alpn_protocols(["http/1.1"])
            with context.wrap_socket(raw, server_side=True) as tls:
                captured = bytearray()
                while b"\r\n\r\n" not in captured:
                    chunk = tls.recv(4096)
                    if not chunk:
                        raise AcceptanceError(
                            "worker closed before sending a complete request"
                        )
                    captured.extend(chunk)
                    if len(captured) > 8192:
                        raise AcceptanceError("worker request exceeded 8192 bytes")
                self.request = bytes(captured)
                if self.request != EXPECTED_REQUEST:
                    raise AcceptanceError("canary received an unexpected request")
                tls.sendall(HEADERS[:35])
                tls.sendall(HEADERS[35:])
        except BaseException as exc:
            self.error = exc
        finally:
            self._listener.close()

    def finish(self) -> None:
        self._thread.join(timeout=12.0)
        if self._thread.is_alive():
            raise AcceptanceError("owned TLS canary did not stop")
        if self.error is not None:
            raise AcceptanceError(f"owned TLS canary failed: {self.error}") from self.error


def _contract(now: datetime) -> ScopeContract:
    return ScopeContract(
        id="scope-passive-worker-acceptance",
        programme_id="passive-worker-acceptance",
        verified_at=now,
        status=ContractStatus.VERIFIED,
        assets_in_scope=[AssetPattern(PatternType.EXACT, CANARY_URL)],
        max_authority="PASSIVE_HTTP",
        rate_limit_rps=0.5,
        human_reviewed=True,
    )


def _assert_full_worker_path() -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    contract = _contract(now)
    authority = contract.fingerprint()
    request = ActionRequest(
        id="request-passive-worker-acceptance",
        workspace_id="workspace-passive-worker-acceptance",
        session_id="session-passive-worker-acceptance",
        experiment_id="experiment-passive-worker-acceptance",
        authority_ref=authority,
        action_type="passive_http.head",
        exact_action="Read one owned local canary header block with HEAD",
        target_asset_id="asset-passive-worker-canary",
        identity_id=None,
        required_authority=AuthorityLevel.PASSIVE_HTTP,
        purpose="Offline no-route passive worker acceptance",
        technique="passive-http-head",
        max_requests=1,
        expected_effects=EffectBudget.from_mapping({"reads": 1}),
        stop_conditions=("redirect", "private-address", "budget", "kill-switch"),
        created_at=now,
    )
    asset = TargetAsset(
        id="asset-passive-worker-canary",
        workspace_id=request.workspace_id,
        authority_ref=authority,
        kind=AssetKind.URL,
        canonical_identifier=CANARY_URL,
        scope_classification=ScopeClassification.IN_SCOPE,
        display_name="Owned offline passive worker canary",
        classification_evidence_ref="fixture:no-route-worker-canary",
    )
    ticket_signer = Ed25519Signer.generate()
    receipt_signer = Ed25519Signer.generate()
    capture_private = X25519PrivateKey.generate()
    recipient = CaptureRecipient.from_public_key(
        capture_private.public_key(), created_at=now
    )
    with tempfile.TemporaryDirectory(prefix="greytheory-worker-acceptance-") as root:
        private_root = Path(root)
        audit = AuditLog(private_root / "gate.jsonl", clock=lambda: now)
        decision = Gate(
            audit,
            posture_ceiling=AuthorityLevel.PASSIVE_HTTP,
            clock=lambda: now,
        ).evaluate(contract, request.to_access_request(asset, actor="acceptance-broker"))
        if decision.reason is not Reason.ALLOWED:
            raise AcceptanceError("synthetic acceptance Gate did not allow the fixture")
        ticket = PassiveTicketIssuer(ticket_signer).issue(
            ticket_id="ticket-passive-worker-acceptance",
            request=request,
            asset=asset,
            decision=decision,
            audit=audit,
            contract=contract,
            evidence_key_ref=recipient.key_id,
            nonce=secrets.token_hex(16),
            issued_at=now,
        )
        switch = BrokerKillSwitch(private_root / "kill-switch")
        switch.release(
            actor="acceptance-operator",
            reason="owned no-route worker acceptance only",
            at=now,
            authorization_ref="fixture:passive-worker-acceptance",
        )
        ledger = TicketReplayLedger(private_root / "ledger")
        canary = _CanaryServer()
        canary.start()
        try:
            result = PassiveWorkerAssembly(
                ticket_verifier=ticket_signer.verifier,
                receipt_signer=receipt_signer,
                ledger=ledger,
                kill_switch=switch,
                ca_file=CERTIFICATE,
                clock=lambda: datetime.now(timezone.utc),
            ).run(ticket=ticket, recipient=recipient)
        except BaseException as worker_error:
            try:
                canary.finish()
            except AcceptanceError as canary_error:
                raise AcceptanceError(
                    "worker assembly failed before the canary completed: "
                    f"{type(worker_error).__name__}: {worker_error}; "
                    f"canary: {canary_error}"
                ) from worker_error
            raise
        else:
            canary.finish()
        if decrypt_capture(
            result.adapter.capture, private_key=capture_private
        ) != HEADERS:
            raise AcceptanceError("encrypted worker capture did not round-trip")
        result.adapter.receipt.verify(
            verifier=receipt_signer.verifier,
            ticket=ticket,
        )
        reservation = ledger.get(ticket.digest)
        if reservation is None or reservation.status != "completed":
            raise AcceptanceError("worker ticket was not completed exactly once")
        if result.adapter.resolution.addresses != (CANARY_ADDRESS,):
            raise AcceptanceError("system resolver did not return the owned canary")
        if not result.worker.identity.is_unprivileged_linux:
            raise AcceptanceError("spawned worker identity is not unprivileged")
        return {
            "ticket_digest": ticket.digest,
            "request_digest": result.adapter.request.digest,
            "resolved_addresses": list(result.adapter.resolution.addresses),
            "status_code": result.adapter.receipt.payload.status_code,
            "content_type": result.adapter.receipt.payload.content_type,
            "capture_bytes": result.adapter.capture.capture_bytes,
            "capture_encrypted": True,
            "capture_round_trip_verified": True,
            "receipt_signature_verified": True,
            "replay_state": reservation.status,
            "worker": result.worker.to_dict(),
            "canary_request_exact": canary.request == EXPECTED_REQUEST,
        }


def main() -> int:
    evidence = {
        "schema_version": 1,
        "posture": "LOCAL_FIXTURE",
        "external_network_contact": False,
        "namespace": _assert_isolated_unprivileged_host(),
        "worker_service": _assert_full_worker_path(),
        "worker_id": WORKER_ID,
        "worker_version": WORKER_VERSION,
        "passive_http_enabled": False,
        "worker_service_assembled": True,
        "vps_used": False,
        "programme_contacted": False,
        "root_kek_present": False,
    }
    print(json.dumps(evidence, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
