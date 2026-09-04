"""Owned-process passive worker assembly stays narrow, typed, and fail closed."""

from __future__ import annotations

import inspect
import json
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey

from greytheory.authority.gate import AuthorityLevel
from greytheory.models import DataClass, TrustLabel
from greytheory_broker import (
    BrokerDenied,
    BrokerDenialReason,
    BrokerKillSwitch,
    BrokerLimits,
    CaptureRecipient,
    Ed25519Signer,
    PassiveMethod,
    PassiveTicketPayload,
    SignedPassiveTicket,
    TicketReplayLedger,
    decrypt_capture,
)
from greytheory_worker import (
    PassiveWorkerAssembly,
    SpawnedWorkerClient,
    WORKER_ID,
    WORKER_IPC_SCHEMA_VERSION,
    WORKER_VERSION,
    WorkerIdentity,
    WorkerProcessEvidence,
    WorkerProtocolError,
    WorkerProtocolService,
)
from greytheory_worker.service import (
    _default_worker_process_context,
    _worker_child,
)
from greytheory_worker_contract import (
    AdapterContractError,
    DirectHeadRequest,
    HeadTransportResult,
    ResolutionResult,
)


NOW = datetime(2026, 8, 26, 12, 0, tzinfo=timezone.utc)
HEADERS = (
    b"HTTP/1.1 200 OK\r\n"
    b"Content-Type: text/plain\r\n"
    b"X-GreyTheory-Canary: local-only\r\n\r\n"
)
TICKET_SIGNER = Ed25519Signer.from_private_bytes(bytes(range(32)))
RECEIPT_SIGNER = Ed25519Signer.from_private_bytes(bytes(range(32, 64)))
CAPTURE_PRIVATE = X25519PrivateKey.from_private_bytes(bytes(range(64, 96)))
RECIPIENT = CaptureRecipient.from_public_key(
    CAPTURE_PRIVATE.public_key(), created_at=NOW
)
UNPRIVILEGED = WorkerIdentity(
    worker_id=WORKER_ID,
    worker_version=WORKER_VERSION,
    platform="linux",
    process_id=4242,
    effective_uid=65534,
    effective_gid=65534,
    effective_capabilities=0,
    bounding_capabilities=0,
    no_new_privileges=True,
    supplementary_gids=(65534,),
    environment_keys=("LANG", "LC_ALL", "PYTHONDONTWRITEBYTECODE"),
)


def request(address: str = "8.8.8.8") -> DirectHeadRequest:
    return DirectHeadRequest(
        ticket_digest="a" * 64,
        canonical_url="https://greytheory-canary.invalid/acceptance",
        canonical_host="greytheory-canary.invalid",
        request_target="/acceptance",
        exact_address=address,
        tls_server_name="greytheory-canary.invalid",
        max_capture_bytes=65_536,
        deadline_monotonic=30.0,
    )


def transport_result(value: DirectHeadRequest) -> HeadTransportResult:
    return HeadTransportResult(
        request_digest=value.digest,
        connected_address=value.exact_address,
        tls_server_name=value.tls_server_name,
        raw_header_block=HEADERS,
        bytes_received=len(HEADERS),
        body_bytes_received=0,
        started_monotonic=0.3,
        ended_monotonic=0.4,
        proxy_used=False,
        redirects_followed=0,
        connection_closed=True,
    )


class FixtureResolver:
    def resolve(self, canonical_host, *, deadline_monotonic):
        assert deadline_monotonic == 30.0
        return ResolutionResult(
            canonical_host=canonical_host,
            addresses=("8.8.8.8",),
            started_monotonic=0.1,
            ended_monotonic=0.2,
        )


class FixtureTransport:
    def head(self, value):
        return transport_result(value)


def command(sequence: int, name: str, payload: dict) -> dict:
    return {
        "schema_version": WORKER_IPC_SCHEMA_VERSION,
        "sequence": sequence,
        "command": name,
        "payload": payload,
    }


def ticket() -> SignedPassiveTicket:
    payload = PassiveTicketPayload(
        id="ticket-worker-service-fixture",
        workspace_id="workspace-worker-fixture",
        session_id="session-worker-fixture",
        request_id="request-worker-fixture",
        target_asset_id="asset-worker-fixture",
        authority_ref="b" * 64,
        gate_decision_ref="audit:1",
        action_type="passive_http.head",
        method=PassiveMethod.HEAD,
        canonical_url="https://greytheory-canary.invalid/acceptance",
        canonical_host="greytheory-canary.invalid",
        issued_at=NOW,
        expires_at=NOW + timedelta(minutes=2),
        limits=BrokerLimits(rate_limit_rps=0.5),
        evidence_key_ref=RECIPIENT.key_id,
        nonce="c" * 32,
        required_authority=AuthorityLevel.PASSIVE_HTTP,
        data_class=DataClass.RAW_RESTRICTED,
        trust_label=TrustLabel.UNTRUSTED,
    )
    return SignedPassiveTicket.sign(payload, signer=TICKET_SIGNER)


def test_worker_protocol_serializes_and_enforces_resolve_then_exact_head():
    service = WorkerProtocolService(
        resolver=FixtureResolver(),
        transport=FixtureTransport(),
        identity=UNPRIVILEGED,
    )
    resolved = service.handle(
        command(
            1,
            "resolve",
            {
                "canonical_host": "greytheory-canary.invalid",
                "deadline_monotonic": 30.0,
            },
        )
    )
    assert resolved["status"] == "ok"
    assert resolved["result_type"] == "resolution"
    assert ResolutionResult.from_dict(resolved["payload"]).addresses == (
        "8.8.8.8",
    )
    assert WorkerIdentity.from_dict(resolved["worker"]).is_unprivileged_linux

    completed = service.handle(
        command(2, "head", {"request": request().to_dict()})
    )
    assert completed["status"] == "ok"
    assert completed["result_type"] == "transport"
    restored = HeadTransportResult.from_dict(completed["payload"])
    assert restored.raw_header_block == HEADERS
    assert service.closed
    with pytest.raises(WorkerProtocolError, match="already closed"):
        service.handle(command(3, "head", {"request": request().to_dict()}))


def test_worker_protocol_refuses_out_of_order_or_unresolved_address():
    out_of_order = WorkerProtocolService(
        resolver=FixtureResolver(),
        transport=FixtureTransport(),
        identity=UNPRIVILEGED,
    ).handle(command(1, "head", {"request": request().to_dict()}))
    assert out_of_order["status"] == "error"
    assert out_of_order["error_code"] == "protocol_error"

    service = WorkerProtocolService(
        resolver=FixtureResolver(),
        transport=FixtureTransport(),
        identity=UNPRIVILEGED,
    )
    service.handle(
        command(
            1,
            "resolve",
            {
                "canonical_host": "greytheory-canary.invalid",
                "deadline_monotonic": 30.0,
            },
        )
    )
    denied = service.handle(
        command(2, "head", {"request": request("1.1.1.1").to_dict()})
    )
    assert denied["status"] == "error"
    assert denied["error_code"] == "protocol_error"
    assert "not returned" in denied["detail"]


@pytest.mark.parametrize(
    "frame",
    [
        {
            "schema_version": WORKER_IPC_SCHEMA_VERSION,
            "sequence": True,
            "command": "resolve",
            "payload": {
                "canonical_host": "greytheory-canary.invalid",
                "deadline_monotonic": 5.0,
            },
        },
        {
            "schema_version": WORKER_IPC_SCHEMA_VERSION,
            "sequence": 1,
            "command": 7,
            "payload": {
                "canonical_host": "greytheory-canary.invalid",
                "deadline_monotonic": 5.0,
            },
        },
        {
            "schema_version": WORKER_IPC_SCHEMA_VERSION,
            "sequence": 1,
            "command": "resolve",
            "payload": {"canonical_host": 7, "deadline_monotonic": 5.0},
        },
    ],
)
def test_worker_protocol_refuses_json_type_coercion(frame):
    service = WorkerProtocolService(
        resolver=FixtureResolver(),
        transport=FixtureTransport(),
        identity=UNPRIVILEGED,
    )

    try:
        response = service.handle(frame)
    except WorkerProtocolError:
        return
    assert response["status"] == "error"
    assert response["error_code"] == "protocol_error"
    assert service.closed is True


def test_worker_contract_records_are_lossless_across_capped_json_boundary():
    resolution = FixtureResolver().resolve(
        "greytheory-canary.invalid", deadline_monotonic=30.0
    )
    assert ResolutionResult.from_dict(resolution.to_dict()) == resolution
    direct = request()
    assert DirectHeadRequest.from_dict(direct.to_dict()) == direct
    result = transport_result(direct)
    assert HeadTransportResult.from_dict(result.to_dict()) == result
    corrupted = {**result.to_dict(), "raw_header_block_b64": "not base64!"}
    with pytest.raises(ValueError, match="canonical base64"):
        HeadTransportResult.from_dict(corrupted)
    with pytest.raises(AdapterContractError, match="fields are invalid"):
        ResolutionResult.from_dict({**resolution.to_dict(), "unexpected": True})
    with pytest.raises(AdapterContractError, match="JSON integer"):
        HeadTransportResult.from_dict({**result.to_dict(), "bytes_received": True})


class MonotonicFixture:
    def __init__(self) -> None:
        self.value = 0.0

    def __call__(self) -> float:
        return self.value


class FakeWorker:
    def __init__(self, *, monotonic, **kwargs):
        self.monotonic = monotonic
        self.kwargs = kwargs
        self.commands = []

    def resolve(self, canonical_host, *, deadline_monotonic):
        self.commands.append("resolve")
        self.monotonic.value = 0.2
        return ResolutionResult(
            canonical_host=canonical_host,
            addresses=("8.8.8.8",),
            started_monotonic=0.1,
            ended_monotonic=0.2,
        )

    def head(self, value):
        self.commands.append("head")
        self.monotonic.value = 0.4
        return transport_result(value)

    @property
    def evidence(self):
        return WorkerProcessEvidence(
            identity=UNPRIVILEGED,
            process_start_method="spawn",
            commands_completed=tuple(self.commands),
            exitcode=0,
        )

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        del exc_type, exc, traceback


class FakeWorkerFactory:
    def __init__(self):
        self.instances = []

    def __call__(self, **kwargs):
        worker = FakeWorker(**kwargs)
        self.instances.append(worker)
        return worker


def test_parent_assembly_keeps_keys_and_broker_state_out_of_worker(tmp_path):
    signed = ticket()
    switch = BrokerKillSwitch(tmp_path / "switch")
    switch.release(
        actor="fixture-operator",
        reason="offline worker assembly fixture",
        at=NOW,
        authorization_ref="fixture-posture-only",
    )
    ledger = TicketReplayLedger(tmp_path / "ledger")
    monotonic = MonotonicFixture()
    factory = FakeWorkerFactory()
    result = PassiveWorkerAssembly(
        ticket_verifier=TICKET_SIGNER.verifier,
        receipt_signer=RECEIPT_SIGNER,
        ledger=ledger,
        kill_switch=switch,
        ca_file=Path(__file__),
        clock=lambda: NOW,
        monotonic=monotonic,
        worker_factory=factory,
    ).run(ticket=signed, recipient=RECIPIENT)

    assert len(factory.instances) == 1
    assert set(factory.instances[0].kwargs) == {"ca_file"}
    assert decrypt_capture(result.adapter.capture, private_key=CAPTURE_PRIVATE) == HEADERS
    result.adapter.receipt.verify(
        verifier=RECEIPT_SIGNER.verifier,
        ticket=signed,
    )
    assert result.adapter.receipt.payload.worker_id == WORKER_ID
    assert result.worker.identity.is_unprivileged_linux
    assert ledger.get(signed.digest).status == "completed"


def test_engaged_kill_switch_refuses_before_worker_process_creation(tmp_path):
    factory = FakeWorkerFactory()
    with pytest.raises(BrokerDenied) as denied:
        PassiveWorkerAssembly(
            ticket_verifier=TICKET_SIGNER.verifier,
            receipt_signer=RECEIPT_SIGNER,
            ledger=TicketReplayLedger(tmp_path / "ledger"),
            kill_switch=BrokerKillSwitch(tmp_path / "absent-switch"),
            ca_file=Path(__file__),
            clock=lambda: NOW,
            worker_factory=factory,
        ).run(ticket=ticket(), recipient=RECIPIENT)
    assert denied.value.reason is BrokerDenialReason.KILL_SWITCH
    assert factory.instances == []


def test_worker_child_receives_no_broker_authority_or_private_key_material():
    assert tuple(inspect.signature(_worker_child).parameters) == (
        "channel",
        "ca_file",
    )
    source = Path(inspect.getsourcefile(_worker_child)).read_text(encoding="utf-8")
    assert 'multiprocessing.get_context("forkserver")' in source
    assert 'set_forkserver_preload(["greytheory_worker.service"])' in source
    assert 'multiprocessing.get_context("fork")' in source
    forbidden = {
        "CaptureKeyStore",
        "MessageSigner",
        "PassiveBrokerSession",
        "SignedPassiveTicket",
        "TicketReplayLedger",
        "private_bytes",
    }
    assert forbidden.isdisjoint(source.split())
    assert UNPRIVILEGED.is_unprivileged_linux
    assert not WorkerIdentity(
        worker_id=WORKER_ID,
        worker_version=WORKER_VERSION,
        platform="linux",
        process_id=99,
        effective_uid=0,
        effective_gid=0,
        effective_capabilities=0,
        bounding_capabilities=0,
        no_new_privileges=True,
        supplementary_gids=(0,),
        environment_keys=("LANG", "LC_ALL", "PYTHONDONTWRITEBYTECODE"),
    ).is_unprivileged_linux


def test_linux_worker_context_uses_clean_forkserver(monkeypatch):
    marker = object()
    preloads = []

    monkeypatch.setattr("greytheory_worker.service.platform.system", lambda: "Linux")
    monkeypatch.setattr(
        "greytheory_worker.service.multiprocessing.set_forkserver_preload",
        lambda modules: preloads.append(modules),
    )
    monkeypatch.setattr(
        "greytheory_worker.service.multiprocessing.get_context",
        lambda method: marker if method == "forkserver" else None,
    )

    assert _default_worker_process_context() is marker
    assert preloads == [["greytheory_worker.service"]]


class FakeChildChannel:
    def close(self):
        pass


class FakeProcess:
    def __init__(self):
        self.pid = 4242
        self.exitcode = None
        self.alive = False
        self.terminated = False

    def start(self):
        self.alive = True

    def is_alive(self):
        return self.alive

    def join(self, timeout):
        del timeout

    def terminate(self):
        self.terminated = True
        self.alive = False
        self.exitcode = -15

    def kill(self):
        self.alive = False
        self.exitcode = -9


class FakeParentChannel:
    def __init__(self, context, identity):
        self.context = context
        self.identity = identity
        self.response = None
        self.closed = False

    def send_bytes(self, raw):
        frame = json.loads(raw.decode("ascii"))
        self.context.frames.append(frame)
        if frame["command"] == "resolve":
            payload = ResolutionResult(
                canonical_host=frame["payload"]["canonical_host"],
                addresses=("8.8.8.8",),
                started_monotonic=0.1,
                ended_monotonic=0.2,
            ).to_dict()
            result_type = "resolution"
        else:
            direct = DirectHeadRequest.from_dict(frame["payload"]["request"])
            payload = transport_result(direct).to_dict()
            result_type = "transport"
            self.context.process.alive = False
            self.context.process.exitcode = 0
        response = {
            "schema_version": WORKER_IPC_SCHEMA_VERSION,
            "sequence": frame["sequence"],
            "status": "ok",
            "result_type": result_type,
            "payload": payload,
            "worker": self.identity.to_dict(),
        }
        self.response = json.dumps(
            response, sort_keys=True, separators=(",", ":")
        ).encode("ascii")

    def poll(self, timeout):
        assert timeout > 0
        return self.response is not None

    def recv_bytes(self, maximum):
        assert self.response is not None and len(self.response) <= maximum
        return self.response

    def close(self):
        self.closed = True


class FakeProcessContext:
    def __init__(self, identity=UNPRIVILEGED):
        self.identity = identity
        self.process = FakeProcess()
        self.parent = FakeParentChannel(self, identity)
        self.frames = []

    def Pipe(self, *, duplex):
        assert duplex is True
        return self.parent, FakeChildChannel()

    def Process(self, **kwargs):
        assert kwargs["daemon"] is False
        assert kwargs["name"] == "greytheory-ubuntu-passive-worker"
        assert tuple(inspect.signature(kwargs["target"]).parameters) == (
            "channel",
            "ca_file",
        )
        return self.process

    def get_start_method(self):
        return "spawn"


def test_spawned_client_uses_two_capped_frames_and_reaps_owned_process():
    context = FakeProcessContext()
    client = SpawnedWorkerClient(
        ca_file=Path(__file__),
        process_context=context,
        monotonic=lambda: 0.0,
    )
    resolved = client.resolve(
        "greytheory-canary.invalid", deadline_monotonic=30.0
    )
    response = client.head(request())

    assert resolved.addresses == ("8.8.8.8",)
    assert response.raw_header_block == HEADERS
    assert [frame["command"] for frame in context.frames] == ["resolve", "head"]
    assert context.frames[1]["payload"]["request"]["exact_address"] == "8.8.8.8"
    assert client.evidence.commands_completed == ("resolve", "head")
    assert client.evidence.exitcode == 0
    client.close()
    assert context.parent.closed


def test_spawned_client_reaps_worker_that_reports_privileged_identity():
    privileged = replace(
        UNPRIVILEGED,
        effective_uid=0,
        effective_gid=0,
        supplementary_gids=(0,),
    )
    context = FakeProcessContext(privileged)
    client = SpawnedWorkerClient(
        ca_file=Path(__file__),
        process_context=context,
        monotonic=lambda: 0.0,
    )
    with pytest.raises(WorkerProtocolError, match="not an unprivileged Linux"):
        client.resolve("greytheory-canary.invalid", deadline_monotonic=30.0)
    assert context.process.terminated
    assert not context.process.is_alive()
