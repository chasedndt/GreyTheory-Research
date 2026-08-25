"""Typed orchestration boundary for a future direct passive HEAD adapter.

This module performs no DNS, socket, TLS, HTTP, subprocess, or proxy operation.
It constrains injected lower-level implementations and turns their typed
evidence into an encrypted capture plus a broker-signed receipt.
"""

# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 ChaseInTech

from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import dataclass
from typing import Callable, Protocol
from urllib.parse import urlsplit

from greytheory_broker.contracts import SignedPassiveReceipt
from greytheory_broker.encryption import (
    CaptureRecipient,
    EncryptedCapture,
    encrypt_capture,
)
from greytheory_broker.guard import (
    BrokerDenialReason,
    PassiveBrokerSession,
)
from greytheory_broker.url_policy import (
    canonical_hostname,
    canonical_https_url,
    public_addresses,
)


HEADER_NAME = re.compile(rb"^[!#$%&'*+\-.^_`|~0-9A-Za-z]+$")
STATUS_LINE = re.compile(rb"^HTTP/(?:1\.0|1\.1) ([0-9]{3})(?: [\x20-\x7e]*)?$")
METHOD = "HEAD"
PORT = 443
PROXY_MODE = "disabled"
REDIRECT_MODE = "record_only"
MAX_HEADER_COUNT = 100


class AdapterContractError(ValueError):
    """Raised when lower-level adapter evidence is ambiguous or inconsistent."""


class ResolutionFailed(RuntimeError):
    """Raised by a resolver when it cannot return one complete DNS answer."""


class TransportFailed(RuntimeError):
    """Raised by a direct transport when no valid response was returned."""


class AdapterTimedOut(TimeoutError):
    """Raised when a resolver or transport cancels at the supplied deadline."""


def _finite(value: float, label: str) -> float:
    number = float(value)
    if not math.isfinite(number) or number < 0:
        raise AdapterContractError(f"{label} must be a finite monotonic value")
    return number


def _required(value: str, label: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise AdapterContractError(f"{label} is required")
    return text


@dataclass(frozen=True)
class ResolutionResult:
    """Evidence claimed by one future resolver invocation."""

    canonical_host: str
    addresses: tuple[str, ...]
    started_monotonic: float
    ended_monotonic: float
    resolver_call_count: int = 1
    search_suffix_used: bool = False

    def __post_init__(self) -> None:
        if canonical_hostname(f"https://{self.canonical_host}/") != self.canonical_host:
            raise AdapterContractError("resolution host is not canonical")
        start = _finite(self.started_monotonic, "resolution start")
        end = _finite(self.ended_monotonic, "resolution end")
        if end < start:
            raise AdapterContractError("resolution end precedes its start")
        if self.resolver_call_count != 1:
            raise AdapterContractError("passive-head-v1 requires one resolver call")
        if self.search_suffix_used:
            raise AdapterContractError("DNS search-suffix expansion is forbidden")
        if not isinstance(self.addresses, tuple):
            raise AdapterContractError("resolution addresses must be a tuple")


class Resolver(Protocol):
    """A future isolated resolver must implement this deadline-bound call."""

    def resolve(
        self,
        canonical_host: str,
        *,
        deadline_monotonic: float,
    ) -> ResolutionResult: ...


@dataclass(frozen=True)
class DirectHeadRequest:
    """The exact no-proxy request a lower-level transport may perform."""

    ticket_digest: str
    canonical_url: str
    canonical_host: str
    request_target: str
    exact_address: str
    tls_server_name: str
    max_capture_bytes: int
    deadline_monotonic: float
    method: str = METHOD
    port: int = PORT
    proxy_mode: str = PROXY_MODE
    redirect_mode: str = REDIRECT_MODE

    def __post_init__(self) -> None:
        canonical = canonical_https_url(self.canonical_url)
        parsed = urlsplit(canonical)
        expected_target = parsed.path or "/"
        if self.canonical_host != canonical_hostname(canonical):
            raise AdapterContractError("request host does not match canonical URL")
        if self.request_target != expected_target:
            raise AdapterContractError("request target does not match canonical URL")
        try:
            self.request_target.encode("ascii")
        except UnicodeEncodeError as exc:
            raise AdapterContractError("request target must be ASCII") from exc
        if public_addresses((self.exact_address,)) != (self.exact_address,):
            raise AdapterContractError("request address is not canonical and public")
        if self.tls_server_name != self.canonical_host:
            raise AdapterContractError("TLS server name must equal the canonical host")
        if self.method != METHOD or self.port != PORT:
            raise AdapterContractError("passive-head-v1 requires HEAD on port 443")
        if self.proxy_mode != PROXY_MODE:
            raise AdapterContractError("ambient and configured proxies are forbidden")
        if self.redirect_mode != REDIRECT_MODE:
            raise AdapterContractError("redirects may only be recorded, never followed")
        if not 1 <= self.max_capture_bytes <= 65_536:
            raise AdapterContractError("request capture ceiling is invalid")
        _finite(self.deadline_monotonic, "request deadline")
        if not re.fullmatch(r"[a-f0-9]{64}", self.ticket_digest):
            raise AdapterContractError("request ticket digest is invalid")

    @property
    def wire_bytes(self) -> bytes:
        return (
            f"HEAD {self.request_target} HTTP/1.1\r\n"
            f"Host: {self.canonical_host}\r\n"
            "User-Agent: GreyTheory-Passive/0.1\r\n"
            "Accept: */*\r\n"
            "Accept-Encoding: identity\r\n"
            "Connection: close\r\n\r\n"
        ).encode("ascii")

    @property
    def digest(self) -> str:
        payload = {
            "ticket_digest": self.ticket_digest,
            "canonical_url": self.canonical_url,
            "canonical_host": self.canonical_host,
            "request_target": self.request_target,
            "exact_address": self.exact_address,
            "tls_server_name": self.tls_server_name,
            "method": self.method,
            "port": self.port,
            "proxy_mode": self.proxy_mode,
            "redirect_mode": self.redirect_mode,
            "max_capture_bytes": self.max_capture_bytes,
            "deadline_monotonic": self.deadline_monotonic,
            "wire_sha256": hashlib.sha256(self.wire_bytes).hexdigest(),
        }
        encoded = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        ).encode("ascii")
        return hashlib.sha256(encoded).hexdigest()


@dataclass(frozen=True)
class HeadTransportResult:
    """Evidence returned by one future direct TLS transport call."""

    request_digest: str
    connected_address: str
    tls_server_name: str
    raw_header_block: bytes
    bytes_received: int
    body_bytes_received: int
    started_monotonic: float
    ended_monotonic: float
    proxy_used: bool = False
    redirects_followed: int = 0
    connection_closed: bool = True

    def __post_init__(self) -> None:
        if not re.fullmatch(r"[a-f0-9]{64}", self.request_digest):
            raise AdapterContractError("transport request digest is invalid")
        _required(self.connected_address, "transport connected address")
        _required(self.tls_server_name, "transport TLS server name")
        if not isinstance(self.raw_header_block, bytes):
            raise AdapterContractError("transport header capture must be bytes")
        if (
            isinstance(self.bytes_received, bool)
            or not isinstance(self.bytes_received, int)
            or self.bytes_received < 0
        ):
            raise AdapterContractError("transport byte count is invalid")
        if self.body_bytes_received != 0:
            raise AdapterContractError("HEAD transport must not receive body bytes")
        start = _finite(self.started_monotonic, "transport start")
        end = _finite(self.ended_monotonic, "transport end")
        if end < start:
            raise AdapterContractError("transport end precedes its start")
        if self.proxy_used:
            raise AdapterContractError("transport used a proxy")
        if self.redirects_followed != 0:
            raise AdapterContractError("transport followed a redirect")
        if not self.connection_closed:
            raise AdapterContractError("transport did not close its connection")


class HeadTransport(Protocol):
    """A future direct TLS transport must implement this one-shot call."""

    def head(self, request: DirectHeadRequest) -> HeadTransportResult: ...


@dataclass(frozen=True)
class PassiveAdapterResult:
    resolution: ResolutionResult
    request: DirectHeadRequest
    transport: HeadTransportResult
    capture: EncryptedCapture
    receipt: SignedPassiveReceipt


@dataclass(frozen=True)
class _ParsedHeaders:
    status_code: int
    content_type: str
    redirect_location: str | None


def _parse_headers(raw: bytes, *, max_capture_bytes: int) -> _ParsedHeaders:
    if len(raw) > max_capture_bytes:
        raise OverflowError("response headers exceed the signed capture ceiling")
    if not raw.endswith(b"\r\n\r\n") or raw.find(b"\r\n\r\n") != len(raw) - 4:
        raise AdapterContractError(
            "transport must return one complete header block and no body bytes"
        )
    lines = raw[:-4].split(b"\r\n")
    if not lines or len(lines) - 1 > MAX_HEADER_COUNT:
        raise AdapterContractError("response header count is invalid")
    match = STATUS_LINE.fullmatch(lines[0])
    if match is None:
        raise AdapterContractError("response status line is invalid")
    status_code = int(match.group(1))
    if not 100 <= status_code <= 599:
        raise AdapterContractError("response status code is invalid")
    headers: dict[str, list[str]] = {}
    for line in lines[1:]:
        if not line or line[:1] in {b" ", b"\t"} or b":" not in line:
            raise AdapterContractError("response contains an ambiguous header line")
        name_raw, value_raw = line.split(b":", 1)
        if HEADER_NAME.fullmatch(name_raw) is None:
            raise AdapterContractError("response header name is invalid")
        if any(byte < 32 and byte != 9 for byte in value_raw) or 127 in value_raw:
            raise AdapterContractError("response header value contains controls")
        try:
            name = name_raw.decode("ascii").lower()
            value = value_raw.strip().decode("latin-1")
        except UnicodeDecodeError as exc:
            raise AdapterContractError("response header cannot be decoded") from exc
        headers.setdefault(name, []).append(value)
    content_types = headers.get("content-type", [])
    if len(content_types) != 1 or not content_types[0].strip():
        raise AdapterContractError(
            "response requires exactly one explicit Content-Type header"
        )
    try:
        content_types[0].encode("ascii")
    except UnicodeEncodeError as exc:
        raise AdapterContractError("response Content-Type must be ASCII") from exc
    locations = headers.get("location", [])
    if len(locations) > 1:
        raise AdapterContractError("response contains multiple Location headers")
    return _ParsedHeaders(
        status_code=status_code,
        content_type=content_types[0].strip().lower(),
        redirect_location=(
            locations[0] if 300 <= status_code <= 399 and locations else None
        ),
    )


class PassiveHeadAdapter:
    """Orchestrate injected I/O evidence through the passive broker guard."""

    def __init__(
        self,
        *,
        resolver: Resolver,
        transport: HeadTransport,
        monotonic: Callable[[], float],
    ) -> None:
        self.resolver = resolver
        self.transport = transport
        self.monotonic = monotonic

    def _observed_time(
        self,
        session: PassiveBrokerSession,
        label: str,
    ) -> float:
        try:
            return _finite(self.monotonic(), label)
        except Exception as exc:
            session.stop(
                BrokerDenialReason.RESPONSE_INVALID,
                f"monotonic clock failed closed: {exc}",
            )

    def run(
        self,
        *,
        session: PassiveBrokerSession,
        recipient: CaptureRecipient,
    ) -> PassiveAdapterResult:
        if type(session) is not PassiveBrokerSession:
            raise AdapterContractError("adapter requires a passive broker session")
        if type(recipient) is not CaptureRecipient:
            session.stop(
                BrokerDenialReason.RESPONSE_INVALID,
                "adapter requires a typed capture recipient",
            )
        if recipient.key_id != session.ticket.payload.evidence_key_ref:
            session.stop(
                BrokerDenialReason.RESPONSE_INVALID,
                "adapter recipient does not match the signed ticket",
            )
        started = self._observed_time(session, "adapter start")
        deadline = started + session.ticket.payload.limits.max_duration_seconds
        host = session.ticket.payload.canonical_host
        try:
            resolution = self.resolver.resolve(
                host,
                deadline_monotonic=deadline,
            )
        except AdapterTimedOut as exc:
            session.stop(BrokerDenialReason.DURATION_EXCEEDED, str(exc))
        except Exception as exc:
            session.stop(
                BrokerDenialReason.DNS_DENIED,
                f"resolver failed closed: {exc}",
            )
        if type(resolution) is not ResolutionResult:
            session.stop(
                BrokerDenialReason.DNS_DENIED,
                "resolver returned an untyped result",
            )
        if resolution.canonical_host != host:
            session.stop(
                BrokerDenialReason.DNS_DENIED,
                "resolver result belongs to another hostname",
            )
        observed_after_resolution = self._observed_time(
            session, "adapter time after resolution"
        )
        if (
            resolution.started_monotonic < started
            or resolution.ended_monotonic > observed_after_resolution
        ):
            session.stop(
                BrokerDenialReason.DNS_DENIED,
                "resolver timing evidence is inconsistent",
            )
        if resolution.ended_monotonic > deadline or observed_after_resolution > deadline:
            session.stop(
                BrokerDenialReason.DURATION_EXCEEDED,
                "DNS resolution exceeded the signed duration ceiling",
            )
        admitted = session.authorize_resolution(resolution.addresses)
        try:
            request = DirectHeadRequest(
                ticket_digest=session.ticket.digest,
                canonical_url=session.ticket.payload.canonical_url,
                canonical_host=host,
                request_target=urlsplit(session.ticket.payload.canonical_url).path or "/",
                exact_address=admitted[0],
                tls_server_name=host,
                max_capture_bytes=session.ticket.payload.limits.max_capture_bytes,
                deadline_monotonic=deadline,
            )
        except AdapterContractError as exc:
            session.stop(BrokerDenialReason.RESPONSE_INVALID, str(exc))
        try:
            response = self.transport.head(request)
        except AdapterTimedOut as exc:
            session.stop(BrokerDenialReason.DURATION_EXCEEDED, str(exc))
        except Exception as exc:
            session.stop(
                BrokerDenialReason.RESPONSE_INVALID,
                f"direct transport failed closed: {exc}",
            )
        if type(response) is not HeadTransportResult:
            session.stop(
                BrokerDenialReason.RESPONSE_INVALID,
                "transport returned an untyped result",
            )
        if (
            response.request_digest != request.digest
            or response.connected_address != request.exact_address
            or response.tls_server_name != request.tls_server_name
            or response.bytes_received != len(response.raw_header_block)
        ):
            session.stop(
                BrokerDenialReason.RESPONSE_INVALID,
                "transport evidence does not match the exact direct request",
            )
        observed_after_transport = self._observed_time(
            session, "adapter time after transport"
        )
        if (
            response.started_monotonic < observed_after_resolution
            or response.ended_monotonic > observed_after_transport
        ):
            session.stop(
                BrokerDenialReason.RESPONSE_INVALID,
                "transport timing evidence is inconsistent",
            )
        if response.ended_monotonic > deadline or observed_after_transport > deadline:
            session.stop(
                BrokerDenialReason.DURATION_EXCEEDED,
                "direct transport exceeded the signed duration ceiling",
            )
        try:
            parsed = _parse_headers(
                response.raw_header_block,
                max_capture_bytes=request.max_capture_bytes,
            )
        except OverflowError as exc:
            session.stop(BrokerDenialReason.CAPTURE_TOO_LARGE, str(exc))
        except AdapterContractError as exc:
            session.stop(BrokerDenialReason.RESPONSE_INVALID, str(exc))
        try:
            capture = encrypt_capture(
                response.raw_header_block,
                recipient=recipient,
                ticket_digest=session.ticket.digest,
                created_at=session.clock(),
            )
        except Exception as exc:
            session.stop(
                BrokerDenialReason.RESPONSE_INVALID,
                f"capture encryption failed closed: {exc}",
            )
        if self._observed_time(session, "adapter time before receipt") > deadline:
            session.stop(
                BrokerDenialReason.DURATION_EXCEEDED,
                "capture encryption exceeded the signed duration ceiling",
            )
        receipt = session.record_response(
            status_code=parsed.status_code,
            content_type=parsed.content_type,
            capture=capture,
            redirect_location=parsed.redirect_location,
        )
        return PassiveAdapterResult(
            resolution=resolution,
            request=request,
            transport=response,
            capture=capture,
            receipt=receipt,
        )


__all__ = [
    "AdapterContractError",
    "AdapterTimedOut",
    "DirectHeadRequest",
    "HeadTransport",
    "HeadTransportResult",
    "PassiveAdapterResult",
    "PassiveHeadAdapter",
    "ResolutionFailed",
    "ResolutionResult",
    "Resolver",
    "TransportFailed",
]
