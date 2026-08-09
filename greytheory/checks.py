"""Deterministic check receipts and the registry that may issue them.

A caller saying that a check *could have failed* is not evidence that a check
ran. Registered validators receive exact input bytes; the registry hashes
those bytes and the validator implementation. Only a successful receipt issued
by that registry can promote its matching assertion to ``checked``.
"""

# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 ChaseInTech

from __future__ import annotations

import hashlib
import inspect
import json
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from typing import Callable, Protocol

from greytheory.provenance import Claim, ProvenanceError, Tag


class CheckError(ProvenanceError):
    """Raised when a deterministic check or receipt is unsound."""


class DeterministicValidator(Protocol):
    validator_id: str
    version: str
    exact_assertion: str
    possible_outcomes: tuple[str, ...]

    def validate(self, inputs: tuple[bytes, ...]) -> str:
        """Return exactly one declared outcome for the supplied artifacts."""


@dataclass(frozen=True)
class CheckReceipt:
    id: str
    validator_id: str
    validator_version: str
    input_artifact_hashes: tuple[str, ...]
    exact_assertion: str
    possible_outcomes: tuple[str, ...]
    actual_outcome: str
    issued_at: datetime
    runner_digest: str
    authority_ref: str

    def __post_init__(self) -> None:
        if not self.id.strip() or not self.validator_id.strip():
            raise CheckError("a check receipt requires an id and validator id")
        if not self.validator_version.strip():
            raise CheckError("a check receipt requires a validator version")
        if not self.exact_assertion.strip():
            raise CheckError("a check receipt requires an exact assertion")
        if len(set(self.possible_outcomes)) < 2:
            raise CheckError("a deterministic check requires at least two outcomes")
        if "supported" not in self.possible_outcomes:
            raise CheckError("a promotable check must declare a supported outcome")
        if self.actual_outcome not in self.possible_outcomes:
            raise CheckError("actual outcome was not declared by the validator")
        if not self.input_artifact_hashes:
            raise CheckError("a check receipt requires input artifact hashes")
        for digest in (*self.input_artifact_hashes, self.runner_digest):
            if len(digest) != 64 or any(ch not in "0123456789abcdef" for ch in digest):
                raise CheckError("check receipt hashes must be lowercase SHA-256 digests")
        if not self.authority_ref.strip():
            raise CheckError("a check receipt requires an authority reference")
        if self.issued_at.tzinfo is None:
            raise CheckError("check receipt time must be timezone-aware")

    @property
    def successful(self) -> bool:
        return self.actual_outcome == "supported"

    def to_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "validator_id": self.validator_id,
            "validator_version": self.validator_version,
            "input_artifact_hashes": list(self.input_artifact_hashes),
            "exact_assertion": self.exact_assertion,
            "possible_outcomes": list(self.possible_outcomes),
            "actual_outcome": self.actual_outcome,
            "issued_at": self.issued_at.isoformat(),
            "runner_digest": self.runner_digest,
            "authority_ref": self.authority_ref,
        }


def _validator_digest(validator: DeterministicValidator) -> str:
    try:
        source = inspect.getsource(type(validator))
    except (OSError, TypeError):
        source = repr(type(validator))
    material = json.dumps(
        {
            "validator_id": validator.validator_id,
            "version": validator.version,
            "source": source,
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(material).hexdigest()


class ValidatorRegistry:
    """Issue and consume receipts without trusting caller-created objects."""

    def __init__(
        self,
        *,
        clock: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
    ) -> None:
        self._clock = clock
        self._validators: dict[str, DeterministicValidator] = {}
        self._issued: dict[str, CheckReceipt] = {}
        self._consumed: set[str] = set()

    def register(self, validator: DeterministicValidator) -> None:
        if not validator.validator_id.strip() or not validator.version.strip():
            raise CheckError("a validator requires an id and version")
        if validator.validator_id in self._validators:
            raise CheckError(f"validator {validator.validator_id!r} is already registered")
        if len(set(validator.possible_outcomes)) < 2:
            raise CheckError("a validator must expose a reachable failure outcome")
        self._validators[validator.validator_id] = validator

    def run(
        self,
        validator_id: str,
        *,
        inputs: tuple[bytes, ...],
        authority_ref: str,
    ) -> CheckReceipt:
        try:
            validator = self._validators[validator_id]
        except KeyError as exc:
            raise CheckError(f"validator {validator_id!r} is not registered") from exc
        if not inputs or any(not isinstance(item, bytes) or not item for item in inputs):
            raise CheckError("validator inputs must be non-empty byte artifacts")
        input_hashes = tuple(hashlib.sha256(item).hexdigest() for item in inputs)
        actual = validator.validate(inputs)
        if actual not in validator.possible_outcomes:
            raise CheckError(
                f"validator returned undeclared outcome {actual!r}; receipt refused"
            )
        issued_at = self._clock()
        receipt_material = json.dumps(
            {
                "validator": validator.validator_id,
                "version": validator.version,
                "inputs": input_hashes,
                "assertion": validator.exact_assertion,
                "actual": actual,
                "issued_at": issued_at.isoformat(),
                "authority_ref": authority_ref,
                "ordinal": len(self._issued),
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        receipt_id = "check_" + hashlib.sha256(receipt_material).hexdigest()[:24]
        receipt = CheckReceipt(
            id=receipt_id,
            validator_id=validator.validator_id,
            validator_version=validator.version,
            input_artifact_hashes=input_hashes,
            exact_assertion=validator.exact_assertion,
            possible_outcomes=validator.possible_outcomes,
            actual_outcome=actual,
            issued_at=issued_at,
            runner_digest=_validator_digest(validator),
            authority_ref=authority_ref,
        )
        self._issued[receipt.id] = receipt
        return receipt

    def promote(self, claim: Claim, receipt: CheckReceipt) -> Claim:
        """Consume one successful receipt to promote its exact assertion."""
        if claim.tag is Tag.CHECKED:
            raise CheckError("claim is already checked")
        issued = self._issued.get(receipt.id)
        if issued is None or issued != receipt:
            raise CheckError("check receipt was not issued by this registry")
        if receipt.id in self._consumed:
            raise CheckError("check receipt has already been consumed")
        if not receipt.successful:
            raise CheckError("only a supported check receipt can promote a claim")
        if claim.text != receipt.exact_assertion:
            raise CheckError("claim text does not match the receipt's exact assertion")
        self._consumed.add(receipt.id)
        return replace(
            claim,
            tag=Tag.CHECKED,
            source=f"validator:{receipt.validator_id}@{receipt.validator_version}",
            check_ref=receipt.id,
        )


__all__ = [
    "CheckError",
    "CheckReceipt",
    "DeterministicValidator",
    "ValidatorRegistry",
]
