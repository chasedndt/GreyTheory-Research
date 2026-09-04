"""Signed, serialisable contracts for the dark passive-worker boundary."""

# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 ChaseInTech

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Mapping

from greytheory.audit import AuditLog
from greytheory.authority.gate import AuthorityLevel, Decision
from greytheory.authority.scope import ContractStatus, ScopeContract
from greytheory.models import DataClass, TrustLabel
from greytheory.research import ActionRequest, AssetKind, TargetAsset
from greytheory_broker.url_policy import (
    canonical_hostname,
    canonical_https_url,
    public_addresses,
)
from greytheory_broker.signing import MessageSigner, MessageVerifier, SigningError


TICKET_SCHEMA_VERSION = "greytheory.passive-ticket.v1"
RECEIPT_SCHEMA_VERSION = "greytheory.passive-receipt.v1"
POLICY_VERSION = "passive-head-v1"
SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,191}$")
SHA256 = re.compile(r"^[a-f0-9]{64}$")


class BrokerContractError(ValueError):
    """Raised when a broker record would weaken or obscure a boundary."""


class PassiveMethod(str, Enum):
    HEAD = "HEAD"


class ReceiptOutcome(str, Enum):
    COMPLETED = "completed"
    STOPPED = "stopped"


def _aware(value: datetime, label: str) -> datetime:
    if value.tzinfo is None:
        raise BrokerContractError(f"{label} must be timezone-aware")
    return value.astimezone(timezone.utc)


def _id(value: str, label: str) -> str:
    text = str(value or "").strip()
    if not SAFE_ID.fullmatch(text):
        raise BrokerContractError(f"{label} {value!r} is not a safe identifier")
    return text


def _required(value: str, label: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise BrokerContractError(f"{label} is required")
    return text


def _digest(value: str, label: str) -> str:
    text = str(value or "")
    if not SHA256.fullmatch(text):
        raise BrokerContractError(f"{label} must be a lowercase SHA-256 digest")
    return text


def _canonical(data: Mapping[str, Any]) -> bytes:
    return json.dumps(
        data, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("utf-8")


def _signed_message(
    payload: Mapping[str, Any], *, algorithm: str, key_id: str
) -> bytes:
    return _canonical(
        {
            "signature_algorithm": _required(algorithm, "signature algorithm"),
            "signing_key_id": _id(key_id, "signing key id"),
            "payload": dict(payload),
        }
    )


@dataclass(frozen=True)
class BrokerLimits:
    """Hard ceiling for the first, metadata-only passive action."""

    max_requests: int = 1
    max_redirects: int = 0
    max_capture_bytes: int = 65_536
    max_duration_seconds: int = 30
    rate_limit_rps: float = 0.5

    def __post_init__(self) -> None:
        if self.max_requests != 1:
            raise BrokerContractError("passive-head-v1 permits exactly one request")
        if self.max_redirects != 0:
            raise BrokerContractError("passive-head-v1 denies every redirect")
        if not 1 <= self.max_capture_bytes <= 65_536:
            raise BrokerContractError("capture limit must be between 1 and 65536 bytes")
        if not 1 <= self.max_duration_seconds <= 30:
            raise BrokerContractError("duration limit must be between 1 and 30 seconds")
        if not 0 < self.rate_limit_rps <= 1:
            raise BrokerContractError("passive rate must be positive and at most 1 rps")

    def to_dict(self) -> dict[str, int | float]:
        return {
            "max_requests": self.max_requests,
            "max_redirects": self.max_redirects,
            "max_capture_bytes": self.max_capture_bytes,
            "max_duration_seconds": self.max_duration_seconds,
            "rate_limit_rps": self.rate_limit_rps,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> BrokerLimits:
        return cls(
            max_requests=int(data["max_requests"]),
            max_redirects=int(data["max_redirects"]),
            max_capture_bytes=int(data["max_capture_bytes"]),
            max_duration_seconds=int(data["max_duration_seconds"]),
            rate_limit_rps=float(data["rate_limit_rps"]),
        )


@dataclass(frozen=True)
class PassiveTicketPayload:
    id: str
    workspace_id: str
    session_id: str
    request_id: str
    target_asset_id: str
    authority_ref: str
    gate_decision_ref: str
    action_type: str
    method: PassiveMethod
    canonical_url: str
    canonical_host: str
    issued_at: datetime
    expires_at: datetime
    limits: BrokerLimits
    evidence_key_ref: str
    nonce: str
    policy_version: str = POLICY_VERSION
    required_authority: AuthorityLevel = AuthorityLevel.PASSIVE_HTTP
    data_class: DataClass = DataClass.RAW_RESTRICTED
    trust_label: TrustLabel = TrustLabel.UNTRUSTED
    schema_version: str = TICKET_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for label, value in (
            ("ticket id", self.id),
            ("workspace id", self.workspace_id),
            ("session id", self.session_id),
            ("request id", self.request_id),
            ("target asset id", self.target_asset_id),
            ("evidence key reference", self.evidence_key_ref),
        ):
            _id(value, label)
        _digest(self.authority_ref, "ticket authority reference")
        if not re.fullmatch(r"audit:(?:0|[1-9][0-9]*)", self.gate_decision_ref):
            raise BrokerContractError("ticket requires a valid audited gate decision")
        if self.action_type != "passive_http.head" or self.method is not PassiveMethod.HEAD:
            raise BrokerContractError("passive-head-v1 supports only passive_http.head")
        canonical = canonical_https_url(self.canonical_url)
        if canonical != self.canonical_url or canonical_hostname(canonical) != self.canonical_host:
            raise BrokerContractError("ticket URL and hostname are not canonically bound")
        issued = _aware(self.issued_at, "ticket issue time")
        expires = _aware(self.expires_at, "ticket expiry time")
        if expires <= issued or expires - issued > timedelta(minutes=5):
            raise BrokerContractError("ticket lifetime must be positive and at most five minutes")
        if self.required_authority is not AuthorityLevel.PASSIVE_HTTP:
            raise BrokerContractError("passive tickets require exactly PASSIVE_HTTP")
        if self.data_class is not DataClass.RAW_RESTRICTED:
            raise BrokerContractError("passive captures default to RAW_RESTRICTED")
        if self.trust_label is not TrustLabel.UNTRUSTED:
            raise BrokerContractError("target responses must remain UNTRUSTED")
        if self.policy_version != POLICY_VERSION or self.schema_version != TICKET_SCHEMA_VERSION:
            raise BrokerContractError("unsupported passive ticket policy or schema")
        if not re.fullmatch(r"[a-f0-9]{32,128}", self.nonce):
            raise BrokerContractError("ticket nonce must be 32-128 lowercase hex characters")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "policy_version": self.policy_version,
            "id": self.id,
            "workspace_id": self.workspace_id,
            "session_id": self.session_id,
            "request_id": self.request_id,
            "target_asset_id": self.target_asset_id,
            "authority_ref": self.authority_ref,
            "gate_decision_ref": self.gate_decision_ref,
            "action_type": self.action_type,
            "method": self.method.value,
            "canonical_url": self.canonical_url,
            "canonical_host": self.canonical_host,
            "issued_at": self.issued_at.astimezone(timezone.utc).isoformat(),
            "expires_at": self.expires_at.astimezone(timezone.utc).isoformat(),
            "limits": self.limits.to_dict(),
            "evidence_key_ref": self.evidence_key_ref,
            "nonce": self.nonce,
            "required_authority": self.required_authority.name,
            "data_class": self.data_class.name,
            "trust_label": self.trust_label.value,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> PassiveTicketPayload:
        return cls(
            id=str(data["id"]),
            workspace_id=str(data["workspace_id"]),
            session_id=str(data["session_id"]),
            request_id=str(data["request_id"]),
            target_asset_id=str(data["target_asset_id"]),
            authority_ref=str(data["authority_ref"]),
            gate_decision_ref=str(data["gate_decision_ref"]),
            action_type=str(data["action_type"]),
            method=PassiveMethod(str(data["method"])),
            canonical_url=str(data["canonical_url"]),
            canonical_host=str(data["canonical_host"]),
            issued_at=datetime.fromisoformat(str(data["issued_at"])),
            expires_at=datetime.fromisoformat(str(data["expires_at"])),
            limits=BrokerLimits.from_dict(data["limits"]),
            evidence_key_ref=str(data["evidence_key_ref"]),
            nonce=str(data["nonce"]),
            policy_version=str(data["policy_version"]),
            required_authority=AuthorityLevel.parse(str(data["required_authority"])),
            data_class=DataClass.parse(str(data["data_class"])),
            trust_label=TrustLabel(str(data["trust_label"])),
            schema_version=str(data["schema_version"]),
        )


@dataclass(frozen=True)
class SignedPassiveTicket:
    payload: PassiveTicketPayload
    signature_algorithm: str
    signing_key_id: str
    signature: str

    @classmethod
    def sign(
        cls, payload: PassiveTicketPayload, *, signer: MessageSigner
    ) -> SignedPassiveTicket:
        message = _signed_message(
            payload.to_dict(), algorithm=signer.algorithm, key_id=signer.key_id
        )
        return cls(payload, signer.algorithm, signer.key_id, signer.sign(message))

    def verify(self, *, verifier: MessageVerifier, now: datetime) -> None:
        if (
            verifier.algorithm != self.signature_algorithm
            or verifier.key_id != self.signing_key_id
        ):
            raise BrokerContractError("passive ticket verification key does not match")
        message = _signed_message(
            self.payload.to_dict(),
            algorithm=self.signature_algorithm,
            key_id=self.signing_key_id,
        )
        try:
            verifier.verify(message, self.signature)
        except SigningError as exc:
            raise BrokerContractError("passive ticket signature is invalid") from exc
        when = _aware(now, "ticket verification time")
        if when < self.payload.issued_at.astimezone(timezone.utc):
            raise BrokerContractError("passive ticket is not valid yet")
        if when >= self.payload.expires_at.astimezone(timezone.utc):
            raise BrokerContractError("passive ticket has expired")

    @property
    def digest(self) -> str:
        return hashlib.sha256(_canonical(self.payload.to_dict())).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        return {
            "payload": self.payload.to_dict(),
            "signature_algorithm": self.signature_algorithm,
            "signing_key_id": self.signing_key_id,
            "signature": self.signature,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> SignedPassiveTicket:
        return cls(
            PassiveTicketPayload.from_dict(data["payload"]),
            _required(str(data["signature_algorithm"]), "ticket signature algorithm"),
            _id(str(data["signing_key_id"]), "ticket signing key id"),
            _required(str(data["signature"]), "ticket signature"),
        )


class PassiveTicketIssuer:
    """Translate one fresh audited Gate allow into one signed passive intent."""

    def __init__(
        self, signer: MessageSigner, *, max_capture_bytes: int = 65_536
    ) -> None:
        self._signer = signer
        self.max_capture_bytes = max_capture_bytes

    def issue(
        self,
        *,
        ticket_id: str,
        request: ActionRequest,
        asset: TargetAsset,
        decision: Decision,
        audit: AuditLog,
        contract: ScopeContract,
        evidence_key_ref: str,
        nonce: str,
        issued_at: datetime,
        lifetime: timedelta = timedelta(minutes=2),
    ) -> SignedPassiveTicket:
        if not decision.allowed or decision.audit_seq is None:
            raise BrokerContractError("a passive ticket requires a fresh audited Gate allow")
        if decision.authority_ref != request.authority_ref:
            raise BrokerContractError("gate authority does not match the action request")
        if request.required_authority is not AuthorityLevel.PASSIVE_HTTP:
            raise BrokerContractError("action request does not require PASSIVE_HTTP")
        if request.action_type != "passive_http.head":
            raise BrokerContractError("the first passive policy supports only passive_http.head")
        if request.identity_id is not None:
            raise BrokerContractError("the passive pilot refuses authenticated identities")
        if request.max_requests != 1 or request.expected_effects.to_dict() != {"reads": 1}:
            raise BrokerContractError("the passive action must bind exactly one read")
        if asset.id != request.target_asset_id or asset.workspace_id != request.workspace_id:
            raise BrokerContractError("ticket asset does not match the action request")
        if asset.authority_ref != request.authority_ref:
            raise BrokerContractError("ticket asset authority does not match the request")
        if asset.kind not in {AssetKind.URL, AssetKind.API, AssetKind.ENDPOINT}:
            raise BrokerContractError("the passive pilot requires a URL-like target asset")
        if asset.scope_classification.value != "in_scope":
            raise BrokerContractError("the target asset is not recorded as in scope")
        canonical = canonical_https_url(asset.canonical_identifier)
        issued = _aware(issued_at, "ticket issue time")
        try:
            audit.verify()
        except Exception as exc:
            raise BrokerContractError(f"gate audit chain is not valid: {exc}") from exc
        gate_record = next(
            (record for record in audit if record.seq == decision.audit_seq), None
        )
        if gate_record is None or gate_record.action != "gate.evaluate":
            raise BrokerContractError("the allowed decision has no matching gate audit record")
        if audit.tail() is None or audit.tail().seq != gate_record.seq:
            raise BrokerContractError("the Gate allow is no longer the latest audit event")
        try:
            evaluated_at = datetime.fromisoformat(gate_record.timestamp).astimezone(timezone.utc)
        except (TypeError, ValueError) as exc:
            raise BrokerContractError("gate audit record has an invalid timestamp") from exc
        if evaluated_at > issued or issued - evaluated_at > timedelta(seconds=30):
            raise BrokerContractError("gate allow is not fresh enough for ticket issuance")
        expected_access = request.to_access_request(asset, actor=gate_record.actor).to_dict()
        if (
            gate_record.authority_ref != request.authority_ref
            or gate_record.detail.get("allowed") is not True
            or gate_record.detail.get("request") != expected_access
            or gate_record.detail.get("posture_ceiling") != "PASSIVE_HTTP"
            or gate_record.detail.get("contract_id") != contract.id
        ):
            raise BrokerContractError(
                "gate audit record is not bound to this exact passive request and posture"
            )
        if contract.fingerprint() != request.authority_ref:
            raise BrokerContractError("scope contract fingerprint does not match the request")
        if contract.status is not ContractStatus.VERIFIED or not contract.human_reviewed:
            raise BrokerContractError("scope contract is no longer verified and human-reviewed")
        if contract.rate_limit_rps is None or contract.rate_limit_rps <= 0:
            raise BrokerContractError("ticket issuance requires an explicit positive programme rate")
        payload = PassiveTicketPayload(
            id=ticket_id,
            workspace_id=request.workspace_id,
            session_id=request.session_id,
            request_id=request.id,
            target_asset_id=asset.id,
            authority_ref=request.authority_ref,
            gate_decision_ref=f"audit:{decision.audit_seq}",
            action_type=request.action_type,
            method=PassiveMethod.HEAD,
            canonical_url=canonical,
            canonical_host=canonical_hostname(canonical),
            issued_at=issued,
            expires_at=issued + lifetime,
            limits=BrokerLimits(
                max_capture_bytes=self.max_capture_bytes,
                rate_limit_rps=min(float(contract.rate_limit_rps), 1.0),
            ),
            evidence_key_ref=evidence_key_ref,
            nonce=nonce,
        )
        return SignedPassiveTicket.sign(payload, signer=self._signer)


@dataclass(frozen=True)
class PassiveReceiptPayload:
    id: str
    ticket_id: str
    ticket_digest: str
    worker_id: str
    worker_version: str
    outcome: ReceiptOutcome
    started_at: datetime
    ended_at: datetime
    request_count: int
    resolved_addresses: tuple[str, ...]
    status_code: int | None
    content_type: str
    capture_bytes: int
    capture_sha256: str | None
    capture_envelope_sha256: str | None
    stop_reason: str | None = None
    redirects: tuple[str, ...] = ()
    data_class: DataClass = DataClass.RAW_RESTRICTED
    trust_label: TrustLabel = TrustLabel.UNTRUSTED
    schema_version: str = RECEIPT_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for label, value in (
            ("receipt id", self.id),
            ("ticket id", self.ticket_id),
            ("worker id", self.worker_id),
        ):
            _id(value, label)
        _digest(self.ticket_digest, "receipt ticket digest")
        _required(self.worker_version, "worker version")
        start = _aware(self.started_at, "receipt start time")
        end = _aware(self.ended_at, "receipt end time")
        if end < start:
            raise BrokerContractError("receipt end time precedes start time")
        if self.request_count not in {0, 1}:
            raise BrokerContractError("passive-head-v1 receipts contain zero or one request")
        if self.redirects:
            raise BrokerContractError("passive-head-v1 cannot report a followed redirect")
        if self.resolved_addresses:
            try:
                canonical_addresses = public_addresses(self.resolved_addresses)
            except ValueError as exc:
                raise BrokerContractError(f"receipt contains unsafe DNS evidence: {exc}") from exc
            object.__setattr__(self, "resolved_addresses", canonical_addresses)
        if self.capture_bytes < 0:
            raise BrokerContractError("capture byte count cannot be negative")
        for digest, label in (
            (self.capture_sha256, "capture digest"),
            (self.capture_envelope_sha256, "encrypted envelope digest"),
        ):
            if digest is not None:
                _digest(digest, label)
        if self.outcome is ReceiptOutcome.COMPLETED:
            if self.request_count != 1 or self.status_code is None:
                raise BrokerContractError("completed receipt requires one response")
            if self.capture_sha256 is None or self.capture_envelope_sha256 is None:
                raise BrokerContractError(
                    "completed receipt requires capture and encrypted-envelope digests"
                )
            if self.stop_reason is not None:
                raise BrokerContractError("completed receipt cannot carry a stop reason")
        elif not self.stop_reason:
            raise BrokerContractError("stopped receipt requires a stop reason")
        if self.data_class is not DataClass.RAW_RESTRICTED:
            raise BrokerContractError("passive receipt data must remain RAW_RESTRICTED")
        if self.trust_label is not TrustLabel.UNTRUSTED:
            raise BrokerContractError("passive receipt data must remain UNTRUSTED")
        if self.schema_version != RECEIPT_SCHEMA_VERSION:
            raise BrokerContractError("unsupported passive receipt schema")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "id": self.id,
            "ticket_id": self.ticket_id,
            "ticket_digest": self.ticket_digest,
            "worker_id": self.worker_id,
            "worker_version": self.worker_version,
            "outcome": self.outcome.value,
            "started_at": self.started_at.astimezone(timezone.utc).isoformat(),
            "ended_at": self.ended_at.astimezone(timezone.utc).isoformat(),
            "request_count": self.request_count,
            "resolved_addresses": list(self.resolved_addresses),
            "status_code": self.status_code,
            "content_type": self.content_type,
            "capture_bytes": self.capture_bytes,
            "capture_sha256": self.capture_sha256,
            "capture_envelope_sha256": self.capture_envelope_sha256,
            "stop_reason": self.stop_reason,
            "redirects": list(self.redirects),
            "data_class": self.data_class.name,
            "trust_label": self.trust_label.value,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> PassiveReceiptPayload:
        return cls(
            id=str(data["id"]),
            ticket_id=str(data["ticket_id"]),
            ticket_digest=str(data["ticket_digest"]),
            worker_id=str(data["worker_id"]),
            worker_version=str(data["worker_version"]),
            outcome=ReceiptOutcome(str(data["outcome"])),
            started_at=datetime.fromisoformat(str(data["started_at"])),
            ended_at=datetime.fromisoformat(str(data["ended_at"])),
            request_count=int(data["request_count"]),
            resolved_addresses=tuple(str(item) for item in data["resolved_addresses"]),
            status_code=(
                int(data["status_code"]) if data.get("status_code") is not None else None
            ),
            content_type=str(data.get("content_type", "")),
            capture_bytes=int(data["capture_bytes"]),
            capture_sha256=(
                str(data["capture_sha256"])
                if data.get("capture_sha256") is not None
                else None
            ),
            capture_envelope_sha256=(
                str(data["capture_envelope_sha256"])
                if data.get("capture_envelope_sha256") is not None
                else None
            ),
            stop_reason=(
                str(data["stop_reason"]) if data.get("stop_reason") is not None else None
            ),
            redirects=tuple(str(item) for item in data.get("redirects", ())),
            data_class=DataClass.parse(str(data["data_class"])),
            trust_label=TrustLabel(str(data["trust_label"])),
            schema_version=str(data["schema_version"]),
        )


@dataclass(frozen=True)
class SignedPassiveReceipt:
    payload: PassiveReceiptPayload
    signature_algorithm: str
    signing_key_id: str
    signature: str

    @classmethod
    def sign(
        cls, payload: PassiveReceiptPayload, *, signer: MessageSigner
    ) -> SignedPassiveReceipt:
        message = _signed_message(
            payload.to_dict(), algorithm=signer.algorithm, key_id=signer.key_id
        )
        return cls(payload, signer.algorithm, signer.key_id, signer.sign(message))

    def verify(
        self, *, verifier: MessageVerifier, ticket: SignedPassiveTicket
    ) -> None:
        if self.payload.ticket_id != ticket.payload.id or self.payload.ticket_digest != ticket.digest:
            raise BrokerContractError("receipt is not bound to the supplied ticket")
        if (
            verifier.algorithm != self.signature_algorithm
            or verifier.key_id != self.signing_key_id
        ):
            raise BrokerContractError("passive receipt verification key does not match")
        message = _signed_message(
            self.payload.to_dict(),
            algorithm=self.signature_algorithm,
            key_id=self.signing_key_id,
        )
        try:
            verifier.verify(message, self.signature)
        except SigningError as exc:
            raise BrokerContractError("passive receipt signature is invalid") from exc
        if self.payload.started_at < ticket.payload.issued_at or (
            self.payload.request_count > ticket.payload.limits.max_requests
        ):
            raise BrokerContractError("passive receipt exceeds its signed ticket limits")
        if self.payload.outcome is ReceiptOutcome.COMPLETED and (
            self.payload.ended_at > ticket.payload.expires_at
            or self.payload.ended_at - self.payload.started_at
            > timedelta(seconds=ticket.payload.limits.max_duration_seconds)
            or self.payload.capture_bytes > ticket.payload.limits.max_capture_bytes
        ):
            raise BrokerContractError("completed receipt exceeds its signed ticket limits")

    @property
    def digest(self) -> str:
        return hashlib.sha256(_canonical(self.payload.to_dict())).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        return {
            "payload": self.payload.to_dict(),
            "signature_algorithm": self.signature_algorithm,
            "signing_key_id": self.signing_key_id,
            "signature": self.signature,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> SignedPassiveReceipt:
        return cls(
            PassiveReceiptPayload.from_dict(data["payload"]),
            _required(str(data["signature_algorithm"]), "receipt signature algorithm"),
            _id(str(data["signing_key_id"]), "receipt signing key id"),
            _required(str(data["signature"]), "receipt signature"),
        )


__all__ = [
    "POLICY_VERSION",
    "RECEIPT_SCHEMA_VERSION",
    "TICKET_SCHEMA_VERSION",
    "BrokerContractError",
    "BrokerLimits",
    "PassiveMethod",
    "PassiveReceiptPayload",
    "PassiveTicketIssuer",
    "PassiveTicketPayload",
    "ReceiptOutcome",
    "SignedPassiveReceipt",
    "SignedPassiveTicket",
]
