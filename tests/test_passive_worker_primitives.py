"""Syscall-injected proof for the unlaunched passive worker primitives."""

from __future__ import annotations

import json
import socket
import ssl
from pathlib import Path

import pytest

import greytheory_worker.primitives as primitives
from greytheory_worker import (
    CancellableSystemResolver,
    DirectTlsHeadTransport,
    WorkerPrimitiveError,
)
from greytheory_worker_contract import (
    AdapterTimedOut,
    DirectHeadRequest,
    ResolutionFailed,
    TransportCaptureLimitExceeded,
    TransportFailed,
)


GOOD_HEADERS = b"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\n"


class MonotonicFixture:
    def __init__(self, value: float = 0.0) -> None:
        self.value = value

    def __call__(self) -> float:
        return self.value


class ChildChannel:
    def __init__(self) -> None:
        self.messages = []
        self.closed = False

    def send_bytes(self, message) -> None:
        self.messages.append(message)

    def close(self) -> None:
        self.closed = True


class ParentChannel:
    def __init__(self, clock, *, message=None, available=True, poll_value=0.2) -> None:
        self.clock = clock
        self.message = message
        self.available = available
        self.poll_value = poll_value
        self.poll_timeouts = []
        self.closed = False

    def poll(self, timeout) -> bool:
        self.poll_timeouts.append(timeout)
        self.clock.value = self.poll_value
        return self.available

    def recv_bytes(self, maximum):
        assert maximum == primitives.MAX_RESOLVER_MESSAGE_BYTES
        if isinstance(self.message, Exception):
            raise self.message
        return self.message

    def close(self) -> None:
        self.closed = True


class FakeProcess:
    def __init__(self, *, stubborn=False, start_error=None) -> None:
        self.stubborn = stubborn
        self.start_error = start_error
        self.started = False
        self.alive = False
        self.terminated = False
        self.killed = False
        self.join_timeouts = []

    def start(self) -> None:
        if self.start_error is not None:
            raise self.start_error
        self.started = True
        self.alive = True

    def is_alive(self) -> bool:
        return self.alive

    def terminate(self) -> None:
        self.terminated = True
        if not self.stubborn:
            self.alive = False

    def kill(self) -> None:
        self.killed = True
        self.alive = False

    def join(self, timeout=None) -> None:
        self.join_timeouts.append(timeout)
        if self.started and not self.stubborn:
            self.alive = False


class FakeProcessContext:
    def __init__(
        self,
        clock,
        *,
        message=None,
        available=True,
        poll_value=0.2,
        stubborn=False,
        start_error=None,
    ) -> None:
        if message is None:
            message = resolver_message(
                status="ok",
                addresses=["8.8.8.8", "1.1.1.1"],
            )
        self.parent = ParentChannel(
            clock,
            message=message,
            available=available,
            poll_value=poll_value,
        )
        self.child = ChildChannel()
        self.process = FakeProcess(stubborn=stubborn, start_error=start_error)
        self.process_kwargs = None

    def Pipe(self, *, duplex):
        assert duplex is False
        return self.parent, self.child

    def Process(self, **kwargs):
        self.process_kwargs = kwargs
        return self.process


class FakeRawSocket:
    def __init__(self) -> None:
        self.timeouts = []
        self.connect_target = None
        self.closed = False

    def settimeout(self, value) -> None:
        self.timeouts.append(value)

    def connect(self, target) -> None:
        self.connect_target = target

    def close(self) -> None:
        self.closed = True


class FakeTlsSocket:
    def __init__(
        self,
        raw_socket,
        *,
        chunks=None,
        peer="8.8.8.8",
        alpn="http/1.1",
        recv_error=None,
    ) -> None:
        self.raw_socket = raw_socket
        self.chunks = list(chunks or [GOOD_HEADERS])
        self.peer = peer
        self.alpn = alpn
        self.recv_error = recv_error
        self.timeouts = []
        self.sent = []
        self.recv_sizes = []
        self.closed = False

    def selected_alpn_protocol(self):
        return self.alpn

    def getpeername(self):
        return (self.peer, 443)

    def settimeout(self, value) -> None:
        self.timeouts.append(value)

    def sendall(self, data) -> None:
        self.sent.append(data)

    def recv(self, size):
        self.recv_sizes.append(size)
        if self.recv_error is not None:
            raise self.recv_error
        return self.chunks.pop(0) if self.chunks else b""

    def close(self) -> None:
        self.closed = True
        self.raw_socket.close()


class FakeTlsContext:
    def __init__(self, tls_socket) -> None:
        self.tls_socket = tls_socket
        self.wrap_calls = []

    def wrap_socket(self, raw_socket, **kwargs):
        assert raw_socket is self.tls_socket.raw_socket
        self.wrap_calls.append(kwargs)
        return self.tls_socket


def direct_request(*, address="8.8.8.8", maximum=65_536, deadline=30.0):
    return DirectHeadRequest(
        ticket_digest="a" * 64,
        canonical_url="https://example.com/path",
        canonical_host="example.com",
        request_target="/path",
        exact_address=address,
        tls_server_name="example.com",
        max_capture_bytes=maximum,
        deadline_monotonic=deadline,
    )


def resolver_message(*, status, addresses=None, message=None):
    payload = {"status": status}
    if addresses is not None:
        payload["addresses"] = addresses
    if message is not None:
        payload["message"] = message
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("ascii")


def make_transport(tmp_path, *, tls_socket, clock=None):
    ca_file = tmp_path / "ca-bundle.pem"
    ca_file.write_text("fixture only", encoding="ascii")
    calls = {"socket": [], "context": []}

    def socket_factory(family, kind, protocol):
        calls["socket"].append((family, kind, protocol))
        return tls_socket.raw_socket

    context = FakeTlsContext(tls_socket)

    def context_factory(path):
        calls["context"].append(path)
        return context

    transport = DirectTlsHeadTransport(
        ca_file=ca_file,
        socket_factory=socket_factory,
        tls_context_factory=context_factory,
        monotonic=clock or MonotonicFixture(),
    )
    return transport, context, calls


def test_resolver_child_uses_one_absolute_system_lookup(monkeypatch):
    channel = ChildChannel()
    calls = []

    def getaddrinfo(host, port, **kwargs):
        calls.append((host, port, kwargs))
        return [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("8.8.8.8", 443)),
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("1.1.1.1", 443)),
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("8.8.8.8", 443)),
        ]

    monkeypatch.setattr(primitives.socket, "getaddrinfo", getaddrinfo)
    primitives._resolver_child(channel, "example.com")

    assert len(calls) == 1
    assert calls[0][0] == "example.com."
    assert calls[0][1] == 443
    assert calls[0][2]["type"] == socket.SOCK_STREAM
    assert [json.loads(item.decode("ascii")) for item in channel.messages] == [
        {"addresses": ["1.1.1.1", "8.8.8.8"], "status": "ok"}
    ]
    assert channel.closed is True


def test_resolver_child_serializes_failure_without_pickle(monkeypatch):
    channel = ChildChannel()

    def fail(*args, **kwargs):
        raise socket.gaierror("fixture failure")

    monkeypatch.setattr(primitives.socket, "getaddrinfo", fail)
    primitives._resolver_child(channel, "example.com")
    message = json.loads(channel.messages[0].decode("ascii"))
    assert message["status"] == "error"
    assert "fixture failure" in message["message"]
    assert channel.closed is True


def test_cancellable_resolver_returns_typed_result_and_owns_one_child():
    clock = MonotonicFixture()
    context = FakeProcessContext(clock)
    resolver = CancellableSystemResolver(
        process_context=context,
        monotonic=clock,
    )
    result = resolver.resolve("example.com", deadline_monotonic=30.0)

    assert result.addresses == ("8.8.8.8", "1.1.1.1")
    assert result.started_monotonic == 0.0
    assert result.ended_monotonic == 0.2
    assert context.process.started is True
    assert context.process.alive is False
    assert context.process_kwargs["target"] is primitives._resolver_child
    assert context.process_kwargs["args"][1] == "example.com"
    assert context.process_kwargs["daemon"] is True
    assert context.parent.closed is True
    assert context.child.closed is True


@pytest.mark.parametrize("stubborn", (False, True))
def test_resolver_timeout_stops_only_its_owned_child(stubborn):
    clock = MonotonicFixture()
    context = FakeProcessContext(
        clock,
        available=False,
        poll_value=30.0,
        stubborn=stubborn,
    )
    resolver = CancellableSystemResolver(
        process_context=context,
        monotonic=clock,
    )
    with pytest.raises(AdapterTimedOut, match="resolver"):
        resolver.resolve("example.com", deadline_monotonic=30.0)
    assert context.process.terminated is True
    assert context.process.killed is stubborn
    assert context.process.alive is False
    assert context.parent.closed is True
    assert context.child.closed is True


def test_resolver_child_error_and_start_failure_fail_closed():
    clock = MonotonicFixture()
    error_context = FakeProcessContext(
        clock,
        message=resolver_message(
            status="error",
            message="gaierror: fixture failure",
        ),
    )
    with pytest.raises(ResolutionFailed, match="fixture failure"):
        CancellableSystemResolver(
            process_context=error_context,
            monotonic=clock,
        ).resolve("example.com", deadline_monotonic=30.0)

    start_context = FakeProcessContext(
        MonotonicFixture(),
        start_error=OSError("spawn refused"),
    )
    with pytest.raises(ResolutionFailed, match="spawn refused"):
        CancellableSystemResolver(
            process_context=start_context,
            monotonic=MonotonicFixture(),
        ).resolve("example.com", deadline_monotonic=30.0)
    assert start_context.parent.closed is True
    assert start_context.child.closed is True


@pytest.mark.parametrize(
    "message",
    (
        b"not-json",
        resolver_message(status="ok", addresses=[]),
        resolver_message(status="ok", addresses=[1]),
        resolver_message(status="ok", addresses=["8.8.8.8"] * 65),
    ),
)
def test_resolver_rejects_malformed_or_unbounded_child_messages(message):
    clock = MonotonicFixture()
    context = FakeProcessContext(clock, message=message)
    with pytest.raises(ResolutionFailed):
        CancellableSystemResolver(
            process_context=context,
            monotonic=clock,
        ).resolve("example.com", deadline_monotonic=30.0)


def test_resolver_rejects_non_finite_deadline_before_spawning():
    clock = MonotonicFixture()
    context = FakeProcessContext(clock)
    with pytest.raises(WorkerPrimitiveError, match="deadline"):
        CancellableSystemResolver(
            process_context=context,
            monotonic=clock,
        ).resolve("example.com", deadline_monotonic=float("inf"))
    assert context.process.started is False


def test_direct_tls_transport_connects_numeric_address_and_closes(tmp_path):
    raw = FakeRawSocket()
    tls = FakeTlsSocket(raw)
    transport, context, calls = make_transport(tmp_path, tls_socket=tls)
    request = direct_request()
    result = transport.head(request)

    assert calls["socket"] == [(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP)]
    assert raw.connect_target == ("8.8.8.8", 443)
    assert context.wrap_calls == [
        {
            "server_hostname": "example.com",
            "do_handshake_on_connect": True,
        }
    ]
    assert tls.sent == [request.wire_bytes]
    assert result.connected_address == "8.8.8.8"
    assert result.raw_header_block == GOOD_HEADERS
    assert result.request_digest == request.digest
    assert result.proxy_used is False
    assert result.redirects_followed == 0
    assert result.connection_closed is True
    assert tls.closed is True and raw.closed is True


def test_direct_tls_transport_uses_numeric_ipv6_tuple(tmp_path):
    raw = FakeRawSocket()
    address = "2606:4700:4700::1111"
    tls = FakeTlsSocket(raw, peer=address)
    transport, _, calls = make_transport(tmp_path, tls_socket=tls)
    result = transport.head(direct_request(address=address))
    assert calls["socket"][0][0] == socket.AF_INET6
    assert raw.connect_target == (address, 443, 0, 0)
    assert result.connected_address == address


@pytest.mark.parametrize(
    ("case", "expected"),
    (
        ("timeout", AdapterTimedOut),
        ("oversize", TransportCaptureLimitExceeded),
        ("body", TransportFailed),
        ("peer", TransportFailed),
        ("alpn", TransportFailed),
        ("incomplete", TransportFailed),
    ),
)
def test_direct_tls_transport_failures_close_owned_socket(tmp_path, case, expected):
    raw = FakeRawSocket()
    maximum = 64 if case == "oversize" else 65_536
    kwargs = {}
    if case == "timeout":
        kwargs["recv_error"] = socket.timeout("fixture timeout")
    elif case == "oversize":
        kwargs["chunks"] = [b"x" * 65]
    elif case == "body":
        kwargs["chunks"] = [GOOD_HEADERS + b"body"]
    elif case == "peer":
        kwargs["peer"] = "1.1.1.1"
    elif case == "alpn":
        kwargs["alpn"] = "h2"
    else:
        kwargs["chunks"] = [b"HTTP/1.1 200 OK\r\n", b""]
    tls = FakeTlsSocket(raw, **kwargs)
    transport, _, _ = make_transport(tmp_path, tls_socket=tls)
    with pytest.raises(expected):
        transport.head(direct_request(maximum=maximum))
    assert tls.closed is True and raw.closed is True


def test_transport_requires_explicit_existing_ca_bundle(tmp_path):
    with pytest.raises(WorkerPrimitiveError, match="CA bundle"):
        DirectTlsHeadTransport(ca_file=tmp_path / "missing.pem")


def test_default_tls_context_is_pinned_and_disables_key_logging(monkeypatch):
    class Context:
        def __init__(self, protocol):
            self.protocol = protocol
            self.check_hostname = None
            self.verify_mode = None
            self.minimum_version = None
            self.options = 0
            self.keylog_filename = "ambient.log"
            self.loaded = []
            self.alpn = []

        def load_verify_locations(self, *, cafile):
            self.loaded.append(cafile)

        def set_alpn_protocols(self, protocols):
            self.alpn = protocols

    created = []

    def context_factory(protocol):
        context = Context(protocol)
        created.append(context)
        return context

    monkeypatch.setattr(primitives.ssl, "SSLContext", context_factory)
    ca_file = Path("/etc/ssl/certs/ca-certificates.crt")
    context = primitives._default_tls_context(ca_file)
    assert context.protocol == ssl.PROTOCOL_TLS_CLIENT
    assert context.check_hostname is True
    assert context.verify_mode == ssl.CERT_REQUIRED
    assert context.minimum_version == ssl.TLSVersion.TLSv1_2
    assert context.keylog_filename is None
    assert context.loaded == [str(ca_file)]
    assert context.alpn == ["http/1.1"]
