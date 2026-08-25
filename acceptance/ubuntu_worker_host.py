"""Offline Ubuntu host acceptance for GreyTheory passive worker primitives.

Run only inside the repository's ephemeral user/network namespace wrapper.
The namespace has no default route and only a loopback interface. A globally
routable-looking address is assigned to loopback so the production public-IP
request contract can be exercised without contacting any external system.
"""

# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 ChaseInTech

from __future__ import annotations

import json
import multiprocessing
import os
import platform
import socket
import ssl
import sys
import threading
import time
from pathlib import Path
from typing import Any

from greytheory_worker import CancellableSystemResolver, DirectTlsHeadTransport
from greytheory_worker_contract import AdapterTimedOut, DirectHeadRequest, TransportFailed


CANARY_ADDRESS = "8.8.8.8"
CANARY_HOST = "greytheory-canary.invalid"
CANARY_PORT = 443
ROOT = Path(__file__).resolve().parents[1]
CERTIFICATE = ROOT / "acceptance" / "fixtures" / "ubuntu-canary-cert.pem"
PRIVATE_KEY = ROOT / "acceptance" / "fixtures" / "ubuntu-canary-key.pem"
HEADER_PARTS = (
    b"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n",
    b"X-GreyTheory-Canary: local-only\r\n\r\n",
)


class AcceptanceError(RuntimeError):
    """Raised when host behavior does not prove the acceptance contract."""


def _os_release() -> dict[str, str]:
    values: dict[str, str] = {}
    for raw_line in Path("/etc/os-release").read_text(encoding="utf-8").splitlines():
        if "=" not in raw_line:
            continue
        key, value = raw_line.split("=", 1)
        values[key] = value.strip().strip('"')
    return values


def _has_default_route() -> bool:
    lines = Path("/proc/net/route").read_text(encoding="ascii").splitlines()[1:]
    for line in lines:
        fields = line.split()
        if len(fields) >= 8 and fields[1] == "00000000" and fields[7] == "00000000":
            return True
    return False


def _assert_isolated_namespace() -> dict[str, Any]:
    if sys.platform != "linux":
        raise AcceptanceError("Ubuntu worker acceptance requires Linux")
    release = _os_release()
    if release.get("ID") != "ubuntu" or release.get("VERSION_ID") != "24.04":
        raise AcceptanceError("acceptance requires Ubuntu 24.04")
    interfaces = tuple(name for _, name in socket.if_nameindex())
    if interfaces != ("lo",):
        raise AcceptanceError(
            f"isolated namespace must expose only loopback, found {interfaces!r}"
        )
    if _has_default_route():
        raise AcceptanceError("isolated namespace must not contain a default route")
    return {
        "distribution": release.get("PRETTY_NAME", "Ubuntu 24.04"),
        "kernel": platform.release(),
        "interfaces": list(interfaces),
        "default_route": False,
        "effective_uid": os.geteuid(),
    }


class _CanaryServer:
    def __init__(self, *, expect_request: bytes | None) -> None:
        self.expect_request = expect_request
        self.request = b""
        self.error: BaseException | None = None
        self.handshake_failed = False
        self._listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP)
        self._listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._listener.settimeout(5.0)
        self._listener.bind((CANARY_ADDRESS, CANARY_PORT))
        self._listener.listen(1)
        self._thread = threading.Thread(
            target=self._serve,
            name="greytheory-owned-canary",
            daemon=False,
        )

    def start(self) -> None:
        self._thread.start()

    def _serve(self) -> None:
        try:
            raw, _ = self._listener.accept()
            raw.settimeout(5.0)
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            context.minimum_version = ssl.TLSVersion.TLSv1_2
            context.load_cert_chain(certfile=CERTIFICATE, keyfile=PRIVATE_KEY)
            context.set_alpn_protocols(["http/1.1"])
            try:
                with context.wrap_socket(raw, server_side=True) as tls:
                    if self.expect_request is None:
                        raise AcceptanceError("a refused TLS client completed the handshake")
                    captured = bytearray()
                    while b"\r\n\r\n" not in captured:
                        chunk = tls.recv(4096)
                        if not chunk:
                            raise AcceptanceError("canary client closed before its request")
                        captured.extend(chunk)
                        if len(captured) > 8192:
                            raise AcceptanceError("canary request exceeded 8192 bytes")
                    self.request = bytes(captured)
                    if self.request != self.expect_request:
                        raise AcceptanceError("canary received an unexpected request")
                    tls.sendall(HEADER_PARTS[0])
                    time.sleep(0.02)
                    tls.sendall(HEADER_PARTS[1])
            except ssl.SSLError:
                if self.expect_request is not None:
                    raise
                self.handshake_failed = True
        except BaseException as exc:
            self.error = exc
        finally:
            self._listener.close()

    def finish(self) -> None:
        self._thread.join(timeout=7.0)
        if self._thread.is_alive():
            raise AcceptanceError("owned TLS canary did not stop")
        if self.error is not None:
            raise AcceptanceError(f"owned TLS canary failed: {self.error}") from self.error


def _request(host: str = CANARY_HOST) -> DirectHeadRequest:
    return DirectHeadRequest(
        ticket_digest="a" * 64,
        canonical_url=f"https://{host}/acceptance",
        canonical_host=host,
        request_target="/acceptance",
        exact_address=CANARY_ADDRESS,
        tls_server_name=host,
        max_capture_bytes=65_536,
        deadline_monotonic=time.monotonic() + 5.0,
    )


def _assert_direct_tls() -> dict[str, Any]:
    request = _request()
    canary = _CanaryServer(expect_request=request.wire_bytes)
    canary.start()
    original_getaddrinfo = socket.getaddrinfo

    def forbidden_resolution(*args: Any, **kwargs: Any) -> Any:
        raise AcceptanceError("direct transport attempted hostname resolution")

    socket.getaddrinfo = forbidden_resolution
    try:
        result = DirectTlsHeadTransport(ca_file=CERTIFICATE).head(request)
    finally:
        socket.getaddrinfo = original_getaddrinfo
        canary.finish()
    expected_headers = b"".join(HEADER_PARTS)
    if result.raw_header_block != expected_headers:
        raise AcceptanceError("direct transport did not retain the exact header block")
    if result.connected_address != CANARY_ADDRESS or result.body_bytes_received != 0:
        raise AcceptanceError("direct transport evidence does not match the canary")
    if not result.connection_closed or result.proxy_used or result.redirects_followed:
        raise AcceptanceError("direct transport widened its one-shot contract")

    mismatched = _request("wrong.greytheory-canary.invalid")
    refused_canary = _CanaryServer(expect_request=None)
    refused_canary.start()
    try:
        try:
            DirectTlsHeadTransport(ca_file=CERTIFICATE).head(mismatched)
        except TransportFailed:
            pass
        else:
            raise AcceptanceError("TLS hostname mismatch was accepted")
    finally:
        refused_canary.finish()
    if not refused_canary.handshake_failed:
        raise AcceptanceError("canary did not observe the refused TLS handshake")

    return {
        "numeric_address": result.connected_address,
        "request_sha256": result.request_digest,
        "bytes_received": result.bytes_received,
        "body_bytes_received": result.body_bytes_received,
        "proxy_used": result.proxy_used,
        "redirects_followed": result.redirects_followed,
        "connection_closed": result.connection_closed,
        "hostname_mismatch_refused": True,
        "resolver_calls_during_transport": 0,
        "server_writes": len(HEADER_PARTS),
    }


def _blocking_resolver_child(channel: Any, canonical_host: str) -> None:
    del canonical_host
    try:
        time.sleep(60.0)
    finally:
        channel.close()


class _BlockingSpawnContext:
    def __init__(self) -> None:
        self._context = multiprocessing.get_context("spawn")
        self.process: Any | None = None

    def Pipe(self, *, duplex: bool) -> Any:
        return self._context.Pipe(duplex=duplex)

    def Process(self, **kwargs: Any) -> Any:
        kwargs["target"] = _blocking_resolver_child
        self.process = self._context.Process(**kwargs)
        return self.process


def _assert_resolver_cancellation() -> dict[str, Any]:
    context = _BlockingSpawnContext()
    resolver = CancellableSystemResolver(
        process_context=context,
        shutdown_grace_seconds=0.1,
    )
    started = time.monotonic()
    try:
        resolver.resolve(
            CANARY_HOST,
            deadline_monotonic=started + 0.2,
        )
    except AdapterTimedOut:
        pass
    else:
        raise AcceptanceError("blocking resolver was not cancelled at its deadline")
    elapsed = time.monotonic() - started
    if elapsed > 2.0:
        raise AcceptanceError(f"resolver cancellation took {elapsed:.3f} seconds")
    if context.process is None or context.process.is_alive():
        raise AcceptanceError("owned resolver child remained alive after cancellation")
    if context.process.exitcode is None:
        raise AcceptanceError("owned resolver child has no terminal exit status")
    return {
        "process_start_method": "spawn",
        "deadline_seconds": 0.2,
        "elapsed_seconds": round(elapsed, 6),
        "child_alive": False,
        "child_exitcode": context.process.exitcode,
    }


def main() -> int:
    evidence = {
        "schema_version": 1,
        "posture": "LOCAL_FIXTURE",
        "external_network_contact": False,
        "namespace": _assert_isolated_namespace(),
        "direct_tls": _assert_direct_tls(),
        "resolver_cancellation": _assert_resolver_cancellation(),
        "passive_http_enabled": False,
        "worker_service_assembled": False,
    }
    print(json.dumps(evidence, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
