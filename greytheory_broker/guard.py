"""Offline state machine a future passive adapter must call around every I/O."""

# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 ChaseInTech

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Callable, NoReturn

from greytheory_broker.contracts import (
    BrokerContractError,
    PassiveReceiptPayload,
    ReceiptOutcome,
    SignedPassiveReceipt,
    SignedPassiveTicket,
)
from greytheory_broker.encryption import EncryptedCapture
from greytheory_broker.storage import (
    BrokerKillSwitch,
    BrokerStorageError,
    RateLimitDenied,
    TicketReplayDenied,
    TicketReplayLedger,
)
from greytheory_broker.signing import MessageSigner, MessageVerifier
from greytheory_broker.url_policy import (
    TargetPolicyError,
    canonical_https_url,
    public_addresses,
)


class BrokerDenialReason(str, Enum):
    INVALID_TICKET = "invalid_ticket"
    TICKET_REPLAY = "ticket_replay"
    RATE_LIMIT = "rate_limit"
    KILL_SWITCH = "kill_switch"
    METHOD_MISMATCH = "method_mismatch"
    TARGET_MISMATCH = "target_mismatch"
    DNS_DENIED = "dns_denied"
    REDIRECT_DENIED = "redirect_denied"
    DURATION_EXCEEDED = "duration_exceeded"
    CAPTURE_TOO_LARGE = "capture_too_large"
    RESPONSE_INVALID = "response_invalid"
    SESSION_STATE = "session_state"


class BrokerDenied(RuntimeError):
    """A stable denial with an optional signed stop receipt."""

    def __init__(
        self,
        reason: BrokerDenialReason,
        detail: str,
        *,
        receipt: SignedPassiveReceipt | None = None,
    ) -> None:
        super().__init__(f"{reason.value}: {detail}")
        self.reason = reason
        self.detail = detail
        self.receipt = receipt


class PassiveBrokerSession:
    """Enforce one signed HEAD ticket without performing network activity.

    A future adapter must call ``begin`` before DNS, ``authorize_resolution``
    before connecting, and ``record_response`` before accepting evidence. This
    class imports no DNS, HTTP, socket, browser, or process implementation.
    """

    def __init__(
        self,
        *,
        ticket: SignedPassiveTicket,
        ledger: TicketReplayLedger,
        kill_switch: BrokerKillSwitch,
        receipt_signer: MessageSigner,
        worker_id: str,
        worker_version: str,
        started_at: datetime,
        clock: Callable[[], datetime],
    ) -> None:
        self.ticket = ticket
        self.ledger = ledger
        self.kill_switch = kill_switch
        self.receipt_signer = receipt_signer
        self.worker_id = worker_id
        self.worker_version = worker_version
        self.started_at = started_at
        self.clock = clock
        self.resolved_addresses: tuple[str, ...] = ()
        self.request_count = 0
        self.closed = False

    @classmethod
    def begin(
        cls,
        *,
        ticket: SignedPassiveTicket,
        method: str,
        url: str,
        ticket_verifier: MessageVerifier,
        receipt_signer: MessageSigner,
        ledger: TicketReplayLedger,
        kill_switch: BrokerKillSwitch,
        worker_id: str,
        worker_version: str,
        clock: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
    ) -> PassiveBrokerSession:
        now = clock()
        try:
            ticket.verify(verifier=ticket_verifier, now=now)
        except BrokerContractError as exc:
            raise BrokerDenied(BrokerDenialReason.INVALID_TICKET, str(exc)) from exc
        state = kill_switch.state()
        if state.engaged:
            raise BrokerDenied(BrokerDenialReason.KILL_SWITCH, state.reason)
        if method != ticket.payload.method.value:
            raise BrokerDenied(
                BrokerDenialReason.METHOD_MISMATCH,
                f"ticket permits {ticket.payload.method.value}, not {method!r}",
            )
        try:
            canonical = canonical_https_url(url)
        except TargetPolicyError as exc:
            raise BrokerDenied(BrokerDenialReason.TARGET_MISMATCH, str(exc)) from exc
        if canonical != ticket.payload.canonical_url:
            raise BrokerDenied(
                BrokerDenialReason.TARGET_MISMATCH,
                "request URL does not exactly match the signed ticket",
            )
        try:
            ledger.reserve(
                ticket_digest=ticket.digest,
                ticket_id=ticket.payload.id,
                canonical_host=ticket.payload.canonical_host,
                min_interval_seconds=1.0 / ticket.payload.limits.rate_limit_rps,
                at=now,
            )
        except RateLimitDenied as exc:
            raise BrokerDenied(BrokerDenialReason.RATE_LIMIT, str(exc)) from exc
        except TicketReplayDenied as exc:
            raise BrokerDenied(BrokerDenialReason.TICKET_REPLAY, str(exc)) from exc
        return cls(
            ticket=ticket,
            ledger=ledger,
            kill_switch=kill_switch,
            receipt_signer=receipt_signer,
            worker_id=worker_id,
            worker_version=worker_version,
            started_at=now,
            clock=clock,
        )

    def authorize_resolution(
        self, addresses: tuple[str, ...]
    ) -> tuple[str, ...]:
        """Admit one complete DNS answer before the adapter connects."""

        self._require_open()
        now = self.clock()
        self._check_runtime(now)
        if self.request_count:
            self._deny(BrokerDenialReason.SESSION_STATE, "a request was already admitted", now)
        try:
            resolved = public_addresses(addresses)
        except TargetPolicyError as exc:
            self._deny(BrokerDenialReason.DNS_DENIED, str(exc), now)
        self.resolved_addresses = resolved
        self.request_count = 1
        return resolved

    def record_response(
        self,
        *,
        status_code: int,
        content_type: str,
        capture: EncryptedCapture,
        redirect_location: str | None = None,
    ) -> SignedPassiveReceipt:
        """Validate and seal metadata after the single admitted HEAD request."""

        self._require_open()
        now = self.clock()
        self._check_runtime(now)
        if self.request_count != 1 or not self.resolved_addresses:
            self._deny(
                BrokerDenialReason.SESSION_STATE,
                "response arrived without an admitted DNS resolution",
                now,
            )
        if redirect_location is not None or 300 <= status_code <= 399:
            self._deny(
                BrokerDenialReason.REDIRECT_DENIED,
                "passive-head-v1 records but never follows redirects",
                now,
            )
        if not 100 <= status_code <= 599 or not str(content_type).strip():
            self._deny(
                BrokerDenialReason.RESPONSE_INVALID,
                "response status and content type must be explicit",
                now,
            )
        if type(capture) is not EncryptedCapture:
            self._deny(
                BrokerDenialReason.RESPONSE_INVALID,
                "response requires a typed encrypted capture envelope",
                now,
            )
        if capture.ticket_digest != self.ticket.digest:
            self._deny(
                BrokerDenialReason.RESPONSE_INVALID,
                "capture envelope belongs to another passive ticket",
                now,
            )
        if capture.key_id != self.ticket.payload.evidence_key_ref:
            self._deny(
                BrokerDenialReason.RESPONSE_INVALID,
                "capture envelope recipient does not match the signed ticket",
                now,
            )
        capture_bytes = capture.capture_bytes
        if capture_bytes < 0 or capture_bytes > self.ticket.payload.limits.max_capture_bytes:
            self._deny(
                BrokerDenialReason.CAPTURE_TOO_LARGE,
                f"capture size {capture_bytes} exceeds the signed ceiling",
                now,
            )
        payload = PassiveReceiptPayload(
            id=f"receipt-{self.ticket.payload.id}",
            ticket_id=self.ticket.payload.id,
            ticket_digest=self.ticket.digest,
            worker_id=self.worker_id,
            worker_version=self.worker_version,
            outcome=ReceiptOutcome.COMPLETED,
            started_at=self.started_at,
            ended_at=now,
            request_count=self.request_count,
            resolved_addresses=self.resolved_addresses,
            status_code=status_code,
            content_type=str(content_type).strip().lower(),
            capture_bytes=capture_bytes,
            capture_sha256=capture.capture_sha256,
            capture_envelope_sha256=capture.envelope_sha256,
        )
        return self._seal(payload)

    def stop(
        self,
        reason: BrokerDenialReason,
        detail: str,
    ) -> NoReturn:
        """Seal a fail-closed adapter stop without exposing receipt authorship."""

        self._require_open()
        if not isinstance(reason, BrokerDenialReason):
            raise BrokerDenied(
                BrokerDenialReason.SESSION_STATE,
                "adapter stop reason is invalid",
            )
        message = str(detail or "").strip()
        if not message:
            raise BrokerDenied(
                BrokerDenialReason.SESSION_STATE,
                "adapter stop detail is required",
            )
        now = self.clock()
        state = self.kill_switch.state()
        if state.engaged:
            self._deny(BrokerDenialReason.KILL_SWITCH, state.reason, now)
        if now >= self.ticket.payload.expires_at:
            self._deny(
                BrokerDenialReason.INVALID_TICKET,
                "ticket expired during the attempt",
                now,
            )
        self._deny(reason, message, now)

    def _check_runtime(self, now: datetime) -> None:
        state = self.kill_switch.state()
        if state.engaged:
            self._deny(BrokerDenialReason.KILL_SWITCH, state.reason, now)
        if now >= self.ticket.payload.expires_at:
            self._deny(BrokerDenialReason.INVALID_TICKET, "ticket expired during the attempt", now)
        duration = now - self.started_at
        if duration > timedelta(seconds=self.ticket.payload.limits.max_duration_seconds):
            self._deny(
                BrokerDenialReason.DURATION_EXCEEDED,
                "attempt exceeded the signed duration ceiling",
                now,
            )

    def _require_open(self) -> None:
        if self.closed:
            raise BrokerDenied(
                BrokerDenialReason.SESSION_STATE,
                "passive broker session is already closed",
            )

    def _deny(
        self, reason: BrokerDenialReason, detail: str, now: datetime
    ) -> None:
        payload = PassiveReceiptPayload(
            id=f"receipt-{self.ticket.payload.id}",
            ticket_id=self.ticket.payload.id,
            ticket_digest=self.ticket.digest,
            worker_id=self.worker_id,
            worker_version=self.worker_version,
            outcome=ReceiptOutcome.STOPPED,
            started_at=self.started_at,
            ended_at=now,
            request_count=self.request_count,
            resolved_addresses=self.resolved_addresses,
            status_code=None,
            content_type="",
            capture_bytes=0,
            capture_sha256=None,
            capture_envelope_sha256=None,
            stop_reason=reason.value,
        )
        receipt = self._seal(payload)
        raise BrokerDenied(reason, detail, receipt=receipt)

    def _seal(self, payload: PassiveReceiptPayload) -> SignedPassiveReceipt:
        receipt = SignedPassiveReceipt.sign(payload, signer=self.receipt_signer)
        try:
            self.ledger.complete(
                ticket_digest=self.ticket.digest,
                receipt_digest=receipt.digest,
                at=payload.ended_at,
            )
        except BrokerStorageError:
            self.closed = True
            raise
        self.closed = True
        return receipt


__all__ = [
    "BrokerDenied",
    "BrokerDenialReason",
    "PassiveBrokerSession",
]
