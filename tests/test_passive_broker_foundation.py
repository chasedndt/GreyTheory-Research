"""Offline conformance proof for the still-dark passive broker boundary."""

from __future__ import annotations

import ast
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
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
from greytheory.capabilities import CapabilityStatus, capability
from greytheory.research import ActionRequest, AssetKind, EffectBudget, TargetAsset
from greytheory_broker import (
    BrokerContractError,
    BrokerDenied,
    BrokerDenialReason,
    BrokerKillSwitch,
    BrokerLimits,
    BrokerStorageError,
    CaptureKeyError,
    CaptureKeyStore,
    CaptureRecipient,
    Ed25519Signer,
    PassiveBrokerSession,
    PassiveTicketIssuer,
    SignedPassiveReceipt,
    SignedPassiveTicket,
    TargetPolicyError,
    TicketReplayLedger,
    canonical_https_url,
    decrypt_capture,
    encrypt_capture,
    public_addresses,
)


NOW = datetime(2026, 8, 25, 8, 0, tzinfo=timezone.utc)
TICKET_SIGNER = Ed25519Signer.from_private_bytes(bytes(range(32)))
RECEIPT_SIGNER = Ed25519Signer.from_private_bytes(bytes(range(32, 64)))
CAPTURE_PRIVATE_KEY = X25519PrivateKey.from_private_bytes(bytes(range(64, 96)))
CAPTURE_RECIPIENT = CaptureRecipient.from_public_key(
    CAPTURE_PRIVATE_KEY.public_key(), created_at=NOW
)
PASSIVE_CONTRACT = ScopeContract(
    id="scope-passive-fixture",
    programme_id="passive-fixture",
    verified_at=NOW,
    status=ContractStatus.VERIFIED,
    assets_in_scope=[AssetPattern(PatternType.EXACT, "https://example.com/")],
    max_authority="PASSIVE_HTTP",
    rate_limit_rps=0.5,
    human_reviewed=True,
)
AUTHORITY = PASSIVE_CONTRACT.fingerprint()


def request(*, action_type: str = "passive_http.head") -> ActionRequest:
    return ActionRequest(
        id="request-head",
        workspace_id="workspace-1",
        session_id="session-1",
        experiment_id="experiment-1",
        authority_ref=AUTHORITY,
        action_type=action_type,
        exact_action="Read the exact HTTPS response metadata once with HEAD",
        target_asset_id="asset-url",
        identity_id=None,
        required_authority=AuthorityLevel.PASSIVE_HTTP,
        purpose="Verify one bounded passive canary response",
        technique="passive-http-head",
        max_requests=1,
        expected_effects=EffectBudget.from_mapping({"reads": 1}),
        stop_conditions=("redirect", "private-address", "budget", "kill-switch"),
        created_at=NOW,
    )


def asset(*, url: str = "https://example.com/") -> TargetAsset:
    return TargetAsset(
        id="asset-url",
        workspace_id="workspace-1",
        authority_ref=AUTHORITY,
        kind=AssetKind.URL,
        canonical_identifier=url,
        scope_classification=ScopeClassification.IN_SCOPE,
        display_name="Passive canary URL",
        classification_evidence_ref="contract:fixture-passive",
    )


def gate_evidence(
    tmp_path, action_request, target_asset, *, suffix="", contract=PASSIVE_CONTRACT
):
    audit = AuditLog(tmp_path / f"gate{suffix}.jsonl", clock=lambda: NOW)
    decision = Gate(
        audit,
        posture_ceiling=AuthorityLevel.PASSIVE_HTTP,
        clock=lambda: NOW,
    ).evaluate(
        contract,
        action_request.to_access_request(target_asset, actor="broker-issuer"),
    )
    assert decision.reason is Reason.ALLOWED
    return audit, decision


def ticket(tmp_path, *, suffix: str = "1", issued_at: datetime = NOW):
    action_request = replace(request(), id=f"request-{suffix}")
    target_asset = asset()
    audit, decision = gate_evidence(tmp_path, action_request, target_asset, suffix=suffix)
    return PassiveTicketIssuer(TICKET_SIGNER).issue(
        ticket_id=f"ticket-{suffix}",
        request=action_request,
        asset=target_asset,
        decision=decision,
        audit=audit,
        contract=PASSIVE_CONTRACT,
        evidence_key_ref=CAPTURE_RECIPIENT.key_id,
        nonce=(suffix[-1] * 32 if suffix[-1] in "abcdef0123456789" else "b" * 32),
        issued_at=issued_at,
    )


def encrypted_capture(signed, *, size: int = 512, recipient=CAPTURE_RECIPIENT):
    return encrypt_capture(
        b"x" * size,
        recipient=recipient,
        ticket_digest=signed.digest,
        created_at=NOW,
    )


def released_runtime(tmp_path, *, at: datetime = NOW):
    kill_switch = BrokerKillSwitch(tmp_path / "kill-switch")
    kill_switch.release(
        actor="fixture-operator",
        reason="offline conformance fixture only",
        at=at,
        authorization_ref="posture-fixture-passive",
    )
    return kill_switch, TicketReplayLedger(tmp_path / "ledger")


def test_url_policy_requires_one_canonical_unauthenticated_https_spelling():
    assert canonical_https_url("https://example.com/") == "https://example.com/"
    assert canonical_https_url("https://xn--bcher-kva.example/path") == (
        "https://xn--bcher-kva.example/path"
    )
    for unsafe in (
        "http://example.com/",
        "https://user@example.com/",
        "https://example.com:8443/",
        "https://example.com/?token=no",
        "https://example.com/#fragment",
        "https://127.0.0.1/",
        "https://example.com/a/../b",
        "https://example.com/caf\u00e9",
        "https://example.com/%2fadmin",
        "https://EXAMPLE.com/",
        " https://example.com/",
    ):
        with pytest.raises(TargetPolicyError):
            canonical_https_url(unsafe)


def test_dns_policy_refuses_empty_mixed_private_metadata_and_reserved_answers():
    assert public_addresses(("8.8.8.8", "2606:4700:4700::1111")) == (
        "2606:4700:4700::1111",
        "8.8.8.8",
    )
    for unsafe in (
        (),
        ("127.0.0.1",),
        ("8.8.8.8", "10.0.0.1"),
        ("169.254.169.254",),
        ("192.0.2.1",),
        ("::1",),
        ("fd00::1",),
        ("fe80::1%eth0",),
    ):
        with pytest.raises(TargetPolicyError):
            public_addresses(unsafe)


def test_ticket_issuance_requires_exact_audited_passive_head_and_programme_rate(tmp_path):
    issuer = PassiveTicketIssuer(TICKET_SIGNER)
    action_request = request()
    target_asset = asset()
    audit, decision = gate_evidence(tmp_path, action_request, target_asset)
    signed = issuer.issue(
        ticket_id="ticket-1",
        request=action_request,
        asset=target_asset,
        decision=decision,
        audit=audit,
        contract=PASSIVE_CONTRACT,
        evidence_key_ref="age-key-1",
        nonce="1" * 32,
        issued_at=NOW,
    )
    signed.verify(verifier=TICKET_SIGNER.verifier, now=NOW)
    assert signed.signature_algorithm == "ed25519"
    assert signed.signing_key_id == TICKET_SIGNER.verifier.key_id
    assert not hasattr(TICKET_SIGNER.verifier, "sign")
    with pytest.raises(BrokerContractError, match="verification key"):
        signed.verify(verifier=RECEIPT_SIGNER.verifier, now=NOW)
    assert signed.payload.limits == BrokerLimits(rate_limit_rps=0.5)
    assert signed.payload.required_authority is AuthorityLevel.PASSIVE_HTTP
    assert signed.payload.data_class.name == "RAW_RESTRICTED"
    assert signed.payload.trust_label.value == "untrusted"

    denied = replace(decision, allowed=False, reason=Reason.POSTURE_CEILING_EXCEEDED)
    with pytest.raises(BrokerContractError, match="Gate allow"):
        issuer.issue(
            ticket_id="ticket-denied",
            request=action_request,
            asset=target_asset,
            decision=denied,
            audit=audit,
            contract=PASSIVE_CONTRACT,
            evidence_key_ref="age-key-1",
            nonce="2" * 32,
            issued_at=NOW,
        )
    no_rate = replace(PASSIVE_CONTRACT, rate_limit_rps=None)
    no_rate_request = replace(action_request, authority_ref=no_rate.fingerprint())
    no_rate_asset = replace(target_asset, authority_ref=no_rate.fingerprint())
    no_rate_audit, no_rate_decision = gate_evidence(
        tmp_path,
        no_rate_request,
        no_rate_asset,
        suffix="-no-rate",
        contract=no_rate,
    )
    with pytest.raises(BrokerContractError, match="explicit positive programme rate"):
        issuer.issue(
            ticket_id="ticket-no-rate",
            request=no_rate_request,
            asset=no_rate_asset,
            decision=no_rate_decision,
            audit=no_rate_audit,
            contract=no_rate,
            evidence_key_ref="age-key-1",
            nonce="3" * 32,
            issued_at=NOW,
        )
    get_request = request(action_type="passive_http.get")
    get_audit, get_decision = gate_evidence(
        tmp_path, get_request, target_asset, suffix="-get"
    )
    with pytest.raises(BrokerContractError, match="only passive_http.head"):
        issuer.issue(
            ticket_id="ticket-get",
            request=get_request,
            asset=target_asset,
            decision=get_decision,
            audit=get_audit,
            contract=PASSIVE_CONTRACT,
            evidence_key_ref="age-key-1",
            nonce="4" * 32,
            issued_at=NOW,
        )


def test_ticket_signature_tampering_and_expiry_fail_closed(tmp_path):
    signed = ticket(tmp_path)
    round_trip = SignedPassiveTicket.from_dict(signed.to_dict())
    round_trip.verify(verifier=TICKET_SIGNER.verifier, now=NOW)
    assert round_trip == signed
    tampered = signed.to_dict()
    tampered["payload"]["canonical_url"] = "https://other.example/"
    tampered["payload"]["canonical_host"] = "other.example"
    modified = SignedPassiveTicket.from_dict(tampered)
    with pytest.raises(BrokerContractError, match="signature"):
        modified.verify(verifier=TICKET_SIGNER.verifier, now=NOW)
    with pytest.raises(BrokerContractError, match="expired"):
        signed.verify(
            verifier=TICKET_SIGNER.verifier, now=NOW + timedelta(minutes=3)
        )


def test_ticket_issuer_rejects_stale_or_modified_gate_evidence(tmp_path):
    action_request = request()
    target_asset = asset()
    audit, decision = gate_evidence(tmp_path, action_request, target_asset)
    issuer = PassiveTicketIssuer(TICKET_SIGNER)
    common = dict(
        ticket_id="ticket-evidence",
        request=action_request,
        asset=target_asset,
        decision=decision,
        audit=audit,
        contract=PASSIVE_CONTRACT,
        evidence_key_ref="age-key-1",
        nonce="f" * 32,
    )
    with pytest.raises(BrokerContractError, match="not fresh"):
        issuer.issue(**common, issued_at=NOW + timedelta(seconds=31))

    with pytest.raises(BrokerContractError, match="no longer verified"):
        issuer.issue(
            **{
                **common,
                "contract": replace(PASSIVE_CONTRACT, status=ContractStatus.BLOCKED),
            },
            issued_at=NOW,
        )

    audit.append(actor="operator", action="kill_switch.engage", detail={"reason": "stop"})
    with pytest.raises(BrokerContractError, match="latest audit event"):
        issuer.issue(**common, issued_at=NOW)

    damaged = audit.path.read_text(encoding="utf-8").replace(
        '"allowed":true', '"allowed":false'
    )
    audit.path.write_text(damaged, encoding="utf-8")
    with pytest.raises(BrokerContractError, match="audit chain"):
        issuer.issue(**common, issued_at=NOW)


def test_kill_switch_is_default_engaged_digest_checked_and_release_bound(tmp_path):
    switch = BrokerKillSwitch(tmp_path / "switch")
    assert switch.state().engaged is True
    assert switch.state().healthy is False
    with pytest.raises(BrokerStorageError, match="authorization"):
        switch.release(
            actor="operator",
            reason="missing authority",
            at=NOW,
            authorization_ref="",
        )
    released = switch.release(
        actor="operator",
        reason="fixture acceptance only",
        at=NOW,
        authorization_ref="posture-fixture",
    )
    assert released.engaged is False and released.healthy is True
    envelope = switch.path.read_text(encoding="utf-8").replace(
        '"engaged": false', '"engaged": true'
    )
    switch.path.write_text(envelope, encoding="utf-8")
    assert switch.state().engaged is True
    assert switch.state().healthy is False


def test_one_ticket_completes_once_with_signed_encrypted_capture_receipt(tmp_path):
    runtime_now = [NOW]
    switch, ledger = released_runtime(tmp_path)
    signed = ticket(tmp_path)
    session = PassiveBrokerSession.begin(
        ticket=signed,
        method="HEAD",
        url="https://example.com/",
        ticket_verifier=TICKET_SIGNER.verifier,
        receipt_signer=RECEIPT_SIGNER,
        ledger=ledger,
        kill_switch=switch,
        worker_id="ubuntu-fixture-worker",
        worker_version="0.1.0-test",
        clock=lambda: runtime_now[0],
    )
    assert session.authorize_resolution(("8.8.8.8",)) == ("8.8.8.8",)
    runtime_now[0] += timedelta(seconds=1)
    capture = encrypted_capture(signed)
    receipt = session.record_response(
        status_code=200,
        content_type="text/html",
        capture=capture,
    )

    receipt.verify(verifier=RECEIPT_SIGNER.verifier, ticket=signed)
    round_trip = SignedPassiveReceipt.from_dict(receipt.to_dict())
    round_trip.verify(verifier=RECEIPT_SIGNER.verifier, ticket=signed)
    assert round_trip == receipt
    assert receipt.payload.outcome.value == "completed"
    assert receipt.payload.request_count == 1
    assert receipt.payload.redirects == ()
    assert receipt.payload.data_class.name == "RAW_RESTRICTED"
    assert receipt.payload.capture_bytes == capture.capture_bytes
    assert receipt.payload.capture_sha256 == capture.capture_sha256
    assert receipt.payload.capture_envelope_sha256 == capture.envelope_sha256
    assert decrypt_capture(capture, private_key=CAPTURE_PRIVATE_KEY) == b"x" * 512
    reservation = ledger.get(signed.digest)
    assert reservation is not None and reservation.status == "completed"
    assert reservation.receipt_digest == receipt.digest
    ledger.verify()

    tampered = receipt.to_dict()
    tampered["payload"]["content_type"] = "application/octet-stream"
    with pytest.raises(BrokerContractError, match="signature"):
        SignedPassiveReceipt.from_dict(tampered).verify(
            verifier=RECEIPT_SIGNER.verifier, ticket=signed
        )

    with pytest.raises(BrokerDenied) as replay:
        PassiveBrokerSession.begin(
            ticket=signed,
            method="HEAD",
            url="https://example.com/",
            ticket_verifier=TICKET_SIGNER.verifier,
            receipt_signer=RECEIPT_SIGNER,
            ledger=TicketReplayLedger(tmp_path / "ledger"),
            kill_switch=switch,
            worker_id="ubuntu-fixture-worker",
            worker_version="0.1.0-test",
            clock=lambda: runtime_now[0],
        )
    assert replay.value.reason is BrokerDenialReason.TICKET_REPLAY


def test_rate_limit_is_atomic_across_distinct_tickets_for_the_same_host(tmp_path):
    runtime_now = [NOW]
    switch, ledger = released_runtime(tmp_path)
    first = ticket(tmp_path, suffix="1")
    second = ticket(tmp_path, suffix="2")

    PassiveBrokerSession.begin(
        ticket=first,
        method="HEAD",
        url="https://example.com/",
        ticket_verifier=TICKET_SIGNER.verifier,
        receipt_signer=RECEIPT_SIGNER,
        ledger=ledger,
        kill_switch=switch,
        worker_id="ubuntu-fixture-worker",
        worker_version="0.1.0-test",
        clock=lambda: runtime_now[0],
    )
    runtime_now[0] += timedelta(seconds=1)
    with pytest.raises(BrokerDenied) as limited:
        PassiveBrokerSession.begin(
            ticket=second,
            method="HEAD",
            url="https://example.com/",
            ticket_verifier=TICKET_SIGNER.verifier,
            receipt_signer=RECEIPT_SIGNER,
            ledger=ledger,
            kill_switch=switch,
            worker_id="ubuntu-fixture-worker",
            worker_version="0.1.0-test",
            clock=lambda: runtime_now[0],
        )
    assert limited.value.reason is BrokerDenialReason.RATE_LIMIT
    assert ledger.get(second.digest) is None

    runtime_now[0] += timedelta(seconds=1)
    admitted = PassiveBrokerSession.begin(
        ticket=second,
        method="HEAD",
        url="https://example.com/",
        ticket_verifier=TICKET_SIGNER.verifier,
        receipt_signer=RECEIPT_SIGNER,
        ledger=ledger,
        kill_switch=switch,
        worker_id="ubuntu-fixture-worker",
        worker_version="0.1.0-test",
        clock=lambda: runtime_now[0],
    )
    assert admitted.ticket == second
    assert ledger.get(second.digest).min_interval_seconds == 2.0


@pytest.mark.parametrize(
    ("case", "expected"),
    (
        ("private_dns", BrokerDenialReason.DNS_DENIED),
        ("redirect", BrokerDenialReason.REDIRECT_DENIED),
        ("oversize", BrokerDenialReason.CAPTURE_TOO_LARGE),
        ("kill_switch", BrokerDenialReason.KILL_SWITCH),
        ("timeout", BrokerDenialReason.DURATION_EXCEEDED),
    ),
)
def test_runtime_denials_stop_and_seal_the_reserved_ticket(tmp_path, case, expected):
    runtime_now = [NOW]
    switch, ledger = released_runtime(tmp_path)
    signed = ticket(tmp_path, suffix={
        "private_dns": "a",
        "redirect": "b",
        "oversize": "c",
        "kill_switch": "d",
        "timeout": "e",
    }[case])
    session = PassiveBrokerSession.begin(
        ticket=signed,
        method="HEAD",
        url="https://example.com/",
        ticket_verifier=TICKET_SIGNER.verifier,
        receipt_signer=RECEIPT_SIGNER,
        ledger=ledger,
        kill_switch=switch,
        worker_id="ubuntu-fixture-worker",
        worker_version="0.1.0-test",
        clock=lambda: runtime_now[0],
    )
    with pytest.raises(BrokerDenied) as denied:
        if case == "private_dns":
            session.authorize_resolution(("8.8.8.8", "127.0.0.1"))
        else:
            session.authorize_resolution(("8.8.8.8",))
            if case == "kill_switch":
                switch.engage(actor="operator", reason="stop now", at=runtime_now[0])
            if case == "timeout":
                runtime_now[0] += timedelta(seconds=31)
            session.record_response(
                status_code=302 if case == "redirect" else 200,
                content_type="text/html",
                capture=encrypted_capture(
                    signed, size=70_000 if case == "oversize" else 100
                ),
                redirect_location=("https://other.example/" if case == "redirect" else None),
            )
    assert denied.value.reason is expected
    assert denied.value.receipt is not None
    denied.value.receipt.verify(
        verifier=RECEIPT_SIGNER.verifier, ticket=signed
    )
    assert denied.value.receipt.payload.outcome.value == "stopped"
    assert denied.value.receipt.payload.stop_reason == expected.value
    assert ledger.get(signed.digest).status == "completed"


def test_runtime_storage_is_refused_inside_repository():
    repository_root = Path(__file__).resolve().parents[1]
    with pytest.raises(BrokerStorageError, match="Git worktree"):
        TicketReplayLedger(repository_root / "broker-runtime")
    with pytest.raises(BrokerStorageError, match="Git worktree"):
        BrokerKillSwitch(repository_root / "broker-runtime")
    with pytest.raises(CaptureKeyError, match="Git worktree"):
        CaptureKeyStore(
            repository_root / "broker-runtime",
            key_encryption_key=b"k" * 32,
            audit=AuditLog(repository_root / "broker-runtime-audit.jsonl"),
        )


@pytest.mark.parametrize("case", ("untyped", "wrong_ticket", "wrong_key"))
def test_response_capture_must_be_typed_and_match_ticket_and_recipient(
    tmp_path, case
):
    switch, ledger = released_runtime(tmp_path)
    signed = ticket(
        tmp_path,
        suffix={
            "untyped": "6",
            "wrong_ticket": "7",
            "wrong_key": "8",
        }[case],
    )
    session = PassiveBrokerSession.begin(
        ticket=signed,
        method="HEAD",
        url="https://example.com/",
        ticket_verifier=TICKET_SIGNER.verifier,
        receipt_signer=RECEIPT_SIGNER,
        ledger=ledger,
        kill_switch=switch,
        worker_id="ubuntu-fixture-worker",
        worker_version="0.1.0-test",
        clock=lambda: NOW,
    )
    session.authorize_resolution(("8.8.8.8",))
    if case == "untyped":
        capture = {"capture_sha256": "b" * 64}
    elif case == "wrong_ticket":
        capture = encrypt_capture(
            b"response",
            recipient=CAPTURE_RECIPIENT,
            ticket_digest="f" * 64,
            created_at=NOW,
        )
    else:
        other_private = X25519PrivateKey.generate()
        other_recipient = CaptureRecipient.from_public_key(
            other_private.public_key(), created_at=NOW
        )
        capture = encrypted_capture(signed, recipient=other_recipient)

    with pytest.raises(BrokerDenied) as denied:
        session.record_response(
            status_code=200,
            content_type="text/html",
            capture=capture,
        )
    assert denied.value.reason is BrokerDenialReason.RESPONSE_INVALID
    assert denied.value.receipt is not None
    denied.value.receipt.verify(
        verifier=RECEIPT_SIGNER.verifier,
        ticket=signed,
    )


def test_broker_package_contains_no_network_process_or_worker_adapter():
    root = Path(__file__).resolve().parents[1] / "greytheory_broker"
    forbidden_modules = {
        "aiohttp",
        "http.client",
        "httpx",
        "requests",
        "socket",
        "subprocess",
        "urllib.request",
    }
    imported: set[str] = set()
    for path in root.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module)
    assert imported.isdisjoint(forbidden_modules)
    assert not any(path.name in {"worker.py", "executor.py", "http.py"} for path in root.glob("*.py"))
    assert capability("passive_http_worker").status is CapabilityStatus.UNAVAILABLE
