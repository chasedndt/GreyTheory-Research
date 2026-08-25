"""OS-facing primitives for an unlaunched passive worker.

These classes implement DNS and direct numeric-address TLS/HTTP mechanics, but
they do not provide a service, CLI, scheduler, broker transport, posture route,
or ticket source. Tests inject process, socket, TLS, and clock doubles and make
no network calls.
"""

# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 ChaseInTech

from __future__ import annotations

import ipaddress
import json
import math
import multiprocessing
import socket
import ssl
import time
from pathlib import Path
from typing import Any, Callable

from greytheory_broker.url_policy import canonical_hostname
from greytheory_worker_contract import (
    AdapterContractError,
    AdapterTimedOut,
    DirectHeadRequest,
    HeadTransportResult,
    ResolutionFailed,
    ResolutionResult,
    TransportCaptureLimitExceeded,
    TransportFailed,
)


MAX_RESOLVED_ADDRESSES = 64
MAX_RESOLVER_ERROR_CHARS = 512
MAX_RESOLVER_MESSAGE_BYTES = 16_384
DEFAULT_RESOLVER_SHUTDOWN_GRACE_SECONDS = 0.25
READ_CHUNK_BYTES = 4096


class WorkerPrimitiveError(RuntimeError):
    """Raised when an OS primitive cannot be configured safely."""


def _monotonic_value(clock: Callable[[], float], label: str) -> float:
    value = float(clock())
    if not math.isfinite(value) or value < 0:
        raise WorkerPrimitiveError(f"{label} must be a finite monotonic value")
    return value


def _remaining(clock: Callable[[], float], deadline: float, label: str) -> float:
    deadline_value = float(deadline)
    if not math.isfinite(deadline_value) or deadline_value < 0:
        raise WorkerPrimitiveError("adapter deadline must be a finite monotonic value")
    remaining = deadline_value - _monotonic_value(clock, label)
    if remaining <= 0:
        raise AdapterTimedOut(f"{label} exceeded the adapter deadline")
    return remaining


def _resolver_child(channel: Any, canonical_host: str) -> None:
    """Resolve one absolute hostname inside one owned child process."""

    try:
        absolute_host = f"{canonical_host}."
        records = socket.getaddrinfo(
            absolute_host,
            443,
            family=socket.AF_UNSPEC,
            type=socket.SOCK_STREAM,
            proto=socket.IPPROTO_TCP,
            flags=getattr(socket, "AI_ADDRCONFIG", 0),
        )
        addresses = sorted({str(record[4][0]) for record in records})
        if not addresses:
            raise ResolutionFailed("system resolver returned no addresses")
        if len(addresses) > MAX_RESOLVED_ADDRESSES:
            raise ResolutionFailed(
                f"system resolver returned more than {MAX_RESOLVED_ADDRESSES} addresses"
            )
        channel.send_bytes(
            json.dumps(
                {"status": "ok", "addresses": addresses},
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=True,
            ).encode("ascii")
        )
    except Exception as exc:
        message = f"{type(exc).__name__}: {exc}"[:MAX_RESOLVER_ERROR_CHARS]
        try:
            channel.send_bytes(
                json.dumps(
                    {"status": "error", "message": message},
                    sort_keys=True,
                    separators=(",", ":"),
                    ensure_ascii=True,
                ).encode("ascii")
            )
        except Exception:
            pass
    finally:
        try:
            channel.close()
        except Exception:
            pass


class CancellableSystemResolver:
    """Run blocking system resolution in one owned, terminable child."""

    def __init__(
        self,
        *,
        process_context: Any | None = None,
        monotonic: Callable[[], float] = time.monotonic,
        shutdown_grace_seconds: float = DEFAULT_RESOLVER_SHUTDOWN_GRACE_SECONDS,
    ) -> None:
        self.process_context = process_context or multiprocessing.get_context("spawn")
        self.monotonic = monotonic
        self.shutdown_grace_seconds = float(shutdown_grace_seconds)
        if (
            not math.isfinite(self.shutdown_grace_seconds)
            or self.shutdown_grace_seconds <= 0
            or self.shutdown_grace_seconds > 2
        ):
            raise WorkerPrimitiveError(
                "resolver shutdown grace must be positive and at most two seconds"
            )

    def _stop_owned(self, process: Any) -> None:
        if process.is_alive():
            process.terminate()
            process.join(self.shutdown_grace_seconds)
        if process.is_alive():
            process.kill()
            process.join(self.shutdown_grace_seconds)

    def resolve(
        self,
        canonical_host: str,
        *,
        deadline_monotonic: float,
    ) -> ResolutionResult:
        try:
            expected = canonical_hostname(f"https://{canonical_host}/")
        except Exception as exc:
            raise ResolutionFailed(f"resolver host is invalid: {exc}") from exc
        if expected != canonical_host:
            raise ResolutionFailed("resolver host is not canonical")
        started = _monotonic_value(self.monotonic, "resolver start")
        _remaining(self.monotonic, deadline_monotonic, "resolver start")
        receive_channel: Any | None = None
        send_channel: Any | None = None
        process: Any | None = None
        started_process = False
        try:
            receive_channel, send_channel = self.process_context.Pipe(duplex=False)
            process = self.process_context.Process(
                target=_resolver_child,
                args=(send_channel, canonical_host),
                name="greytheory-passive-resolver",
                daemon=True,
            )
            process.start()
            started_process = True
            send_channel.close()
            timeout = _remaining(
                self.monotonic,
                deadline_monotonic,
                "resolver wait",
            )
            if not receive_channel.poll(timeout):
                self._stop_owned(process)
                raise AdapterTimedOut("system resolver exceeded the adapter deadline")
            try:
                raw_message = receive_channel.recv_bytes(MAX_RESOLVER_MESSAGE_BYTES)
                message = json.loads(raw_message.decode("utf-8"))
            except (
                EOFError,
                OSError,
                UnicodeDecodeError,
                json.JSONDecodeError,
                TypeError,
                ValueError,
            ) as exc:
                raise ResolutionFailed(
                    f"resolver child returned no valid result: {exc}"
                ) from exc
            if not isinstance(message, dict) or message.get("status") not in {
                "ok",
                "error",
            }:
                raise ResolutionFailed("resolver child message shape is invalid")
            ended = _monotonic_value(self.monotonic, "resolver end")
            if ended > float(deadline_monotonic):
                raise AdapterTimedOut("system resolver exceeded the adapter deadline")
            process.join(
                min(
                    self.shutdown_grace_seconds,
                    max(float(deadline_monotonic) - ended, 0),
                )
            )
            if process.is_alive():
                self._stop_owned(process)
            if message["status"] != "ok":
                raise ResolutionFailed(
                    "system resolver failed closed: "
                    f"{str(message.get('message', 'unknown error'))[:MAX_RESOLVER_ERROR_CHARS]}"
                )
            payload = message.get("addresses")
            if (
                not isinstance(payload, list)
                or not 1 <= len(payload) <= MAX_RESOLVED_ADDRESSES
                or any(not isinstance(item, str) for item in payload)
            ):
                raise ResolutionFailed("resolver child addresses are not typed")
            return ResolutionResult(
                canonical_host=canonical_host,
                addresses=tuple(payload),
                started_monotonic=started,
                ended_monotonic=ended,
                resolver_call_count=1,
                search_suffix_used=False,
            )
        except (AdapterTimedOut, ResolutionFailed):
            raise
        except Exception as exc:
            raise ResolutionFailed(f"system resolver failed closed: {exc}") from exc
        finally:
            if receive_channel is not None:
                try:
                    receive_channel.close()
                except Exception:
                    pass
            if send_channel is not None:
                try:
                    send_channel.close()
                except Exception:
                    pass
            if started_process and process is not None and process.is_alive():
                self._stop_owned(process)


def _default_tls_context(ca_file: Path) -> ssl.SSLContext:
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    context.check_hostname = True
    context.verify_mode = ssl.CERT_REQUIRED
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    context.options |= getattr(ssl, "OP_NO_COMPRESSION", 0)
    context.options |= getattr(ssl, "OP_NO_RENEGOTIATION", 0)
    context.keylog_filename = None
    context.load_verify_locations(cafile=str(ca_file))
    context.set_alpn_protocols(["http/1.1"])
    return context


class DirectTlsHeadTransport:
    """Perform one no-proxy HEAD over TLS to one validated numeric address."""

    def __init__(
        self,
        *,
        ca_file: str | Path,
        socket_factory: Callable[[int, int, int], Any] = socket.socket,
        tls_context_factory: Callable[[Path], Any] = _default_tls_context,
        monotonic: Callable[[], float] = time.monotonic,
    ) -> None:
        self.ca_file = Path(ca_file).expanduser().resolve()
        if not self.ca_file.is_file():
            raise WorkerPrimitiveError("worker CA bundle must be an existing file")
        self.socket_factory = socket_factory
        self.tls_context_factory = tls_context_factory
        self.monotonic = monotonic

    def _timeout(self, deadline: float, label: str) -> float:
        return _remaining(self.monotonic, deadline, label)

    def head(self, request: DirectHeadRequest) -> HeadTransportResult:
        if type(request) is not DirectHeadRequest:
            raise TransportFailed("direct transport requires a typed request")
        started = _monotonic_value(self.monotonic, "transport start")
        address = ipaddress.ip_address(request.exact_address)
        family = socket.AF_INET6 if address.version == 6 else socket.AF_INET
        connect_target: tuple[Any, ...] = (
            (request.exact_address, request.port, 0, 0)
            if family == socket.AF_INET6
            else (request.exact_address, request.port)
        )
        raw_socket: Any | None = None
        tls_socket: Any | None = None
        raw_header_block: bytes | None = None
        ended: float | None = None
        peer_address: str | None = None
        try:
            raw_socket = self.socket_factory(
                family,
                socket.SOCK_STREAM,
                socket.IPPROTO_TCP,
            )
            raw_socket.settimeout(
                self._timeout(request.deadline_monotonic, "TCP connect")
            )
            raw_socket.connect(connect_target)
            context = self.tls_context_factory(self.ca_file)
            raw_socket.settimeout(
                self._timeout(request.deadline_monotonic, "TLS handshake")
            )
            tls_socket = context.wrap_socket(
                raw_socket,
                server_hostname=request.tls_server_name,
                do_handshake_on_connect=True,
            )
            raw_socket = None
            selected_alpn = tls_socket.selected_alpn_protocol()
            if selected_alpn not in (None, "http/1.1"):
                raise TransportFailed(
                    f"TLS selected unsupported application protocol {selected_alpn!r}"
                )
            peer = tls_socket.getpeername()
            peer_address = ipaddress.ip_address(str(peer[0])).compressed
            if peer_address != request.exact_address:
                raise TransportFailed(
                    "TLS peer address does not match the validated numeric address"
                )
            tls_socket.settimeout(
                self._timeout(request.deadline_monotonic, "HEAD write")
            )
            tls_socket.sendall(request.wire_bytes)
            captured = bytearray()
            while True:
                tls_socket.settimeout(
                    self._timeout(request.deadline_monotonic, "header read")
                )
                remaining_capacity = request.max_capture_bytes - len(captured)
                read_size = min(READ_CHUNK_BYTES, max(remaining_capacity + 1, 1))
                chunk = tls_socket.recv(read_size)
                if not chunk:
                    raise TransportFailed(
                        "TLS peer closed before one complete response header block"
                    )
                captured.extend(chunk)
                if len(captured) > request.max_capture_bytes:
                    raise TransportCaptureLimitExceeded(
                        "response headers exceed the signed capture ceiling"
                    )
                marker = captured.find(b"\r\n\r\n")
                if marker >= 0:
                    header_end = marker + 4
                    if len(captured) != header_end:
                        raise TransportFailed(
                            "HEAD transport observed bytes after the header block"
                        )
                    raw_header_block = bytes(captured)
                    break
            ended = _monotonic_value(self.monotonic, "transport end")
            if ended > request.deadline_monotonic:
                raise AdapterTimedOut("direct TLS transport exceeded the adapter deadline")
        except (AdapterTimedOut, TransportCaptureLimitExceeded, TransportFailed):
            raise
        except (socket.timeout, TimeoutError) as exc:
            raise AdapterTimedOut(
                "direct TLS transport exceeded the adapter deadline"
            ) from exc
        except (ssl.SSLError, OSError, ValueError) as exc:
            raise TransportFailed(f"direct TLS transport failed closed: {exc}") from exc
        finally:
            if tls_socket is not None:
                try:
                    tls_socket.close()
                except Exception:
                    pass
            elif raw_socket is not None:
                try:
                    raw_socket.close()
                except Exception:
                    pass
        if raw_header_block is None or ended is None or peer_address is None:
            raise TransportFailed("direct TLS transport produced no complete evidence")
        return HeadTransportResult(
            request_digest=request.digest,
            connected_address=peer_address,
            tls_server_name=request.tls_server_name,
            raw_header_block=raw_header_block,
            bytes_received=len(raw_header_block),
            body_bytes_received=0,
            started_monotonic=started,
            ended_monotonic=ended,
            proxy_used=False,
            redirects_followed=0,
            connection_closed=True,
        )


__all__ = [
    "CancellableSystemResolver",
    "DirectTlsHeadTransport",
    "WorkerPrimitiveError",
]
