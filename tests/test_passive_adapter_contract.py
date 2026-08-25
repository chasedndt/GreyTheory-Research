"""Network-free conformance proof for the future passive worker adapter."""

from __future__ import annotations

import ast
from dataclasses import replace
from datetime import datetime, timezone
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
    BrokerDenied,
    BrokerDenialReason,
    BrokerKillSwitch,
    CaptureRecipient,
    Ed25519Signer,
    PassiveBrokerSession,
    PassiveTicketIssuer,
    TicketReplayLedger,
    decrypt_capture,
)
from greytheory_worker_contract import (
    AdapterTimedOut,
    HeadTransportResult,
    PassiveHeadAdapter,
    ResolutionFailed,
    ResolutionResult,
)


NOW = datetime(2026, 8, 25, 10, 0, tzinfo=timezone.utc)
TICKET_SIGNER = Ed25519Signer.from_private_bytes(bytes(range(32)))
RECEIPT_SIGNER = Ed25519Signer.from_private_bytes(bytes(range(32, 64)))
CAPTURE_PRIVATE = X25519PrivateKey.from_private_bytes(bytes(range(64, 96)))
CAPTURE_RECIPIENT = CaptureRecipient.from_public_key(
    CAPTURE_PRIVATE.public_key(), created_at=NOW
)
CONTRACT = ScopeContract(
    id="scope-passive-adapter-fixture",
    programme_id="passive-adapter-fixture",
    verified_at=NOW,
    status=ContractStatus.VERIFIED,
    assets_in_scope=[AssetPattern(PatternType.EXACT, "https://example.com/path")],
    max_authority="PASSIVE_HTTP",
    rate_limit_rps=0.5,
    human_reviewed=True,
)
AUTHORITY = CONTRACT.fingerprint()
GOOD_HEADERS = (
    b"HTTP/1.1 200 OK\r\n"
    b"Content-Type: text/html; charset=utf-8\r\n"
    b"Server: fixture\r\n\r\n"
)


class MonotonicFixture:
    def __init__(self) -> None:
        self.value = 0.0

    def __call__(self) -> float:
        return self.value


class FixtureResolver:
    def __init__(
        self,
        clock: MonotonicFixture,
        *,
        addresses: tuple[str, ...] = ("8.8.8.8", "1.1.1.1"),
        host: str = "example.com",
        error: Exception | None = None,
        ended: float = 0.2,
    ) -> None:
        self.clock = clock
        self.addresses = addresses
        self.host = host
        self.error = error
        self.ended = ended
        self.calls: list[tuple[str, float]] = []

    def resolve(self, canonical_host: str, *, deadline_monotonic: float):
        self.calls.append((canonical_host, deadline_monotonic))
        if self.error is not None:
            raise self.error
        self.clock.value = self.ended
        return ResolutionResult(
            canonical_host=self.host,
            addresses=self.addresses,
            started_monotonic=0.1,
            ended_monotonic=self.ended,
        )


class FixtureTransport:
    def __init__(self, clock: MonotonicFixture, callback=None) -> None:
        self.clock = clock
        self.callback = callback
        self.calls = []

    def head(self, request):
        self.calls.append(request)
        if self.callback is not None:
            return self.callback(request)
        self.clock.value = 0.4
        return transport_result(request)


def transport_result(request, **overrides):
    values = {
        "request_digest": request.digest,
        "connected_address": request.exact_address,
        "tls_server_name": request.tls_server_name,
        "raw_header_block": GOOD_HEADERS,
        "bytes_received": len(GOOD_HEADERS),
        "body_bytes_received": 0,
        "started_monotonic": 0.3,
        "ended_monotonic": 0.4,
        "proxy_used": False,
        "redirects_followed": 0,
        "connection_closed": True,
    }
    values.update(overrides)
    return HeadTransportResult(**values)


def action_request(suffix: str) -> ActionRequest:
    return ActionRequest(
        id=f"request-adapter-{suffix}",
        workspace_id="workspace-1",
        session_id="session-1",
        experiment_id="experiment-1",
        authority_ref=AUTHORITY,
        action_type="passive_http.head",
        exact_action="Read one exact HTTPS response header block with HEAD",
        target_asset_id="asset-url",
        identity_id=None,
        required_authority=AuthorityLevel.PASSIVE_HTTP,
        purpose="Prove the direct passive adapter boundary",
        technique="passive-http-head",
        max_requests=1,
        expected_effects=EffectBudget.from_mapping({"reads": 1}),
        stop_conditions=("redirect", "private-address", "budget", "kill-switch"),
        created_at=NOW,
    )


def begin_session(tmp_path, *, suffix: str = "1"):
    request = action_request(suffix)
    asset = TargetAsset(
        id="asset-url",
        workspace_id="workspace-1",
        authority_ref=AUTHORITY,
        kind=AssetKind.URL,
        canonical_identifier="https://example.com/path",
        scope_classification=ScopeClassification.IN_SCOPE,
        display_name="Passive adapter fixture",
        classification_evidence_ref="contract:passive-adapter-fixture",
    )
    audit = AuditLog(tmp_path / f"gate-{suffix}.jsonl", clock=lambda: NOW)
    decision = Gate(
        audit,
        posture_ceiling=AuthorityLevel.PASSIVE_HTTP,
        clock=lambda: NOW,
    ).evaluate(CONTRACT, request.to_access_request(asset, actor="broker-issuer"))
    assert decision.reason is Reason.ALLOWED
    signed = PassiveTicketIssuer(TICKET_SIGNER).issue(
        ticket_id=f"ticket-adapter-{suffix}",
        request=request,
        asset=asset,
        decision=decision,
        audit=audit,
        contract=CONTRACT,
        evidence_key_ref=CAPTURE_RECIPIENT.key_id,
        nonce=suffix * 32,
        issued_at=NOW,
    )
    switch = BrokerKillSwitch(tmp_path / f"kill-{suffix}")
    switch.release(
        actor="fixture-operator",
        reason="network-free adapter conformance only",
        at=NOW,
        authorization_ref="posture-passive-fixture",
    )
    ledger = TicketReplayLedger(tmp_path / f"ledger-{suffix}")
    session = PassiveBrokerSession.begin(
        ticket=signed,
        method="HEAD",
        url="https://example.com/path",
        ticket_verifier=TICKET_SIGNER.verifier,
        receipt_signer=RECEIPT_SIGNER,
        ledger=ledger,
        kill_switch=switch,
        worker_id="ubuntu-contract-fixture",
        worker_version="0.1.0-contract",
        clock=lambda: NOW,
    )
    return signed, session, switch, ledger


def assert_signed_stop(denied, signed, ledger, reason, *, request_count):
    assert denied.value.reason is reason
    assert denied.value.receipt is not None
    denied.value.receipt.verify(
        verifier=RECEIPT_SIGNER.verifier,
        ticket=signed,
    )
    assert denied.value.receipt.payload.stop_reason == reason.value
    assert denied.value.receipt.payload.request_count == request_count
    assert ledger.get(signed.digest).status == "completed"


def test_adapter_builds_one_exact_direct_request_and_encrypts_headers(tmp_path):
    signed, session, _, ledger = begin_session(tmp_path)
    monotonic = MonotonicFixture()
    resolver = FixtureResolver(monotonic)
    transport = FixtureTransport(monotonic)
    result = PassiveHeadAdapter(
        resolver=resolver,
        transport=transport,
        monotonic=monotonic,
    ).run(session=session, recipient=CAPTURE_RECIPIENT)

    assert resolver.calls == [("example.com", 30.0)]
    assert len(transport.calls) == 1
    request = result.request
    assert request.exact_address == "1.1.1.1"
    assert request.tls_server_name == "example.com"
    assert request.request_target == "/path"
    assert request.proxy_mode == "disabled"
    assert request.redirect_mode == "record_only"
    assert request.wire_bytes == (
        b"HEAD /path HTTP/1.1\r\n"
        b"Host: example.com\r\n"
        b"User-Agent: GreyTheory-Passive/0.1\r\n"
        b"Accept: */*\r\n"
        b"Accept-Encoding: identity\r\n"
        b"Connection: close\r\n\r\n"
    )
    assert b"Proxy" not in request.wire_bytes
    assert request.digest != replace(request, ticket_digest="f" * 64).digest
    assert request.digest != replace(request, exact_address="8.8.8.8").digest
    assert request.digest != replace(request, deadline_monotonic=29.0).digest
    assert decrypt_capture(
        result.capture,
        private_key=CAPTURE_PRIVATE,
    ) == GOOD_HEADERS
    result.receipt.verify(
        verifier=RECEIPT_SIGNER.verifier,
        ticket=signed,
    )
    assert result.receipt.payload.status_code == 200
    assert result.receipt.payload.content_type == "text/html; charset=utf-8"
    assert result.receipt.payload.resolved_addresses == ("1.1.1.1", "8.8.8.8")
    assert ledger.get(signed.digest).receipt_digest == result.receipt.digest


@pytest.mark.parametrize(
    ("case", "reason", "request_count"),
    (
        ("resolver_error", BrokerDenialReason.DNS_DENIED, 0),
        ("resolver_timeout", BrokerDenialReason.DURATION_EXCEEDED, 0),
        ("wrong_host", BrokerDenialReason.DNS_DENIED, 0),
        ("mixed_private", BrokerDenialReason.DNS_DENIED, 0),
        ("late_resolution", BrokerDenialReason.DURATION_EXCEEDED, 0),
    ),
)
def test_resolution_failures_stop_before_transport(
    tmp_path, case, reason, request_count
):
    signed, session, _, ledger = begin_session(tmp_path, suffix={
        "resolver_error": "2",
        "resolver_timeout": "3",
        "wrong_host": "4",
        "mixed_private": "5",
        "late_resolution": "6",
    }[case])
    monotonic = MonotonicFixture()
    kwargs = {}
    if case == "resolver_error":
        kwargs["error"] = ResolutionFailed("fixture DNS failure")
    elif case == "resolver_timeout":
        kwargs["error"] = AdapterTimedOut("fixture DNS timeout")
    elif case == "wrong_host":
        kwargs["host"] = "other.example"
    elif case == "mixed_private":
        kwargs["addresses"] = ("8.8.8.8", "127.0.0.1")
    else:
        kwargs["ended"] = 31.0
    resolver = FixtureResolver(monotonic, **kwargs)
    transport = FixtureTransport(monotonic)

    with pytest.raises(BrokerDenied) as denied:
        PassiveHeadAdapter(
            resolver=resolver,
            transport=transport,
            monotonic=monotonic,
        ).run(session=session, recipient=CAPTURE_RECIPIENT)
    assert transport.calls == []
    assert_signed_stop(denied, signed, ledger, reason, request_count=request_count)


@pytest.mark.parametrize(
    "case",
    (
        "wrong_request",
        "wrong_address",
        "wrong_sni",
        "wrong_byte_count",
        "proxy",
        "followed_redirect",
        "body",
        "open_connection",
    ),
)
def test_transport_evidence_must_prove_one_closed_direct_connection(tmp_path, case):
    signed, session, _, ledger = begin_session(tmp_path, suffix={
        "wrong_request": "7",
        "wrong_address": "8",
        "wrong_sni": "9",
        "wrong_byte_count": "a",
        "proxy": "b",
        "followed_redirect": "c",
        "body": "d",
        "open_connection": "e",
    }[case])
    monotonic = MonotonicFixture()

    def callback(request):
        monotonic.value = 0.4
        overrides = {
            "wrong_request": {"request_digest": "f" * 64},
            "wrong_address": {"connected_address": "8.8.8.8"},
            "wrong_sni": {"tls_server_name": "other.example"},
            "wrong_byte_count": {"bytes_received": len(GOOD_HEADERS) + 1},
            "proxy": {"proxy_used": True},
            "followed_redirect": {"redirects_followed": 1},
            "body": {"body_bytes_received": 1},
            "open_connection": {"connection_closed": False},
        }[case]
        return transport_result(request, **overrides)

    with pytest.raises(BrokerDenied) as denied:
        PassiveHeadAdapter(
            resolver=FixtureResolver(monotonic),
            transport=FixtureTransport(monotonic, callback),
            monotonic=monotonic,
        ).run(session=session, recipient=CAPTURE_RECIPIENT)
    assert_signed_stop(
        denied,
        signed,
        ledger,
        BrokerDenialReason.RESPONSE_INVALID,
        request_count=1,
    )


@pytest.mark.parametrize(
    ("case", "raw", "reason"),
    (
        (
            "redirect",
            b"HTTP/1.1 302 Found\r\nContent-Type: text/html\r\nLocation: https://other.example/\r\n\r\n",
            BrokerDenialReason.REDIRECT_DENIED,
        ),
        (
            "missing_content_type",
            b"HTTP/1.1 200 OK\r\nServer: fixture\r\n\r\n",
            BrokerDenialReason.RESPONSE_INVALID,
        ),
        (
            "duplicate_content_type",
            b"HTTP/1.1 200 OK\r\nContent-Type: text/html\r\nContent-Type: text/plain\r\n\r\n",
            BrokerDenialReason.RESPONSE_INVALID,
        ),
        (
            "folded_header",
            b"HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n folded\r\n\r\n",
            BrokerDenialReason.RESPONSE_INVALID,
        ),
        (
            "body_after_headers",
            b"HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\nbody",
            BrokerDenialReason.RESPONSE_INVALID,
        ),
        (
            "oversize",
            b"HTTP/1.1 200 OK\r\nX-Fill: " + b"x" * 65_510 + b"\r\nContent-Type: text/html\r\n\r\n",
            BrokerDenialReason.CAPTURE_TOO_LARGE,
        ),
    ),
    ids=(
        "redirect",
        "missing-content-type",
        "duplicate-content-type",
        "folded-header",
        "body-after-headers",
        "oversize",
    ),
)
def test_response_parser_denies_redirects_ambiguity_body_and_oversize(
    tmp_path, case, raw, reason
):
    signed, session, _, ledger = begin_session(tmp_path, suffix={
        "redirect": "f",
        "missing_content_type": "1",
        "duplicate_content_type": "2",
        "folded_header": "3",
        "body_after_headers": "4",
        "oversize": "5",
    }[case])
    monotonic = MonotonicFixture()

    def callback(request):
        monotonic.value = 0.4
        return transport_result(
            request,
            raw_header_block=raw,
            bytes_received=len(raw),
        )

    with pytest.raises(BrokerDenied) as denied:
        PassiveHeadAdapter(
            resolver=FixtureResolver(monotonic),
            transport=FixtureTransport(monotonic, callback),
            monotonic=monotonic,
        ).run(session=session, recipient=CAPTURE_RECIPIENT)
    assert_signed_stop(denied, signed, ledger, reason, request_count=1)


@pytest.mark.parametrize("phase", ("transport_exception", "transport_deadline"))
def test_transport_timeout_paths_stop_the_reserved_ticket(tmp_path, phase):
    signed, session, _, ledger = begin_session(
        tmp_path,
        suffix="6" if phase == "transport_exception" else "7",
    )
    monotonic = MonotonicFixture()

    def callback(request):
        if phase == "transport_exception":
            raise AdapterTimedOut("fixture transport timeout")
        monotonic.value = 31.0
        return transport_result(
            request,
            started_monotonic=0.3,
            ended_monotonic=31.0,
        )

    with pytest.raises(BrokerDenied) as denied:
        PassiveHeadAdapter(
            resolver=FixtureResolver(monotonic),
            transport=FixtureTransport(monotonic, callback),
            monotonic=monotonic,
        ).run(session=session, recipient=CAPTURE_RECIPIENT)
    assert_signed_stop(
        denied,
        signed,
        ledger,
        BrokerDenialReason.DURATION_EXCEEDED,
        request_count=1,
    )


def test_kill_switch_recheck_wins_before_accepting_transport_evidence(tmp_path):
    signed, session, switch, ledger = begin_session(tmp_path, suffix="8")
    monotonic = MonotonicFixture()

    def callback(request):
        switch.engage(actor="fixture-operator", reason="stop now", at=NOW)
        monotonic.value = 0.4
        return transport_result(request)

    with pytest.raises(BrokerDenied) as denied:
        PassiveHeadAdapter(
            resolver=FixtureResolver(monotonic),
            transport=FixtureTransport(monotonic, callback),
            monotonic=monotonic,
        ).run(session=session, recipient=CAPTURE_RECIPIENT)
    assert_signed_stop(
        denied,
        signed,
        ledger,
        BrokerDenialReason.KILL_SWITCH,
        request_count=1,
    )


def test_worker_contract_package_contains_no_network_or_process_implementation():
    root = Path(__file__).resolve().parents[1] / "greytheory_worker_contract"
    forbidden = {
        "aiohttp",
        "http.client",
        "httpx",
        "requests",
        "socket",
        "ssl",
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
    assert imported.isdisjoint(forbidden)
    assert capability("passive_http_worker").status is CapabilityStatus.UNAVAILABLE
