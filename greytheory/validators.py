"""Reusable deterministic validators for the checked claim roles.

Every validator here settles its question from artifacts the research session
already holds. None of them touches a target, and that is the design
constraint rather than a happy accident: a claim-role guard that required new
interaction to satisfy would push every finding into doing more to the target
than the proof needed, against invariant I4.

Each answers exactly one role. One validator, one assertion — so a receipt
cannot be quietly reused to answer a different question.
"""

# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 ChaseInTech

from __future__ import annotations

import json
from typing import Any

SUPPORTED = "supported"
REFUTED = "refuted"
INVALID = "invalid_input"
OUTCOMES = (SUPPORTED, REFUTED, INVALID)


def _load(raw: bytes) -> Any:
    return json.loads(raw)


class OwnershipBoundaryValidator:
    """BOUNDARY — the requester held no grant over the object it read.

    Behaviour and boundary are different questions and are deliberately
    separate validators. "The read returned a body" and "the reader was not
    entitled to that body" are both required, and proving only the first is how
    a working feature gets reported as a vulnerability.
    """

    validator_id = "boundary.object_ownership"
    version = "1.0.0"
    exact_assertion = (
        "The requesting identity is recorded as neither the owner of the "
        "returned object nor a grantee over it."
    )
    possible_outcomes = OUTCOMES

    def validate(self, inputs: tuple[bytes, ...]) -> str:
        if len(inputs) != 2:
            return INVALID
        try:
            response = _load(inputs[0])
            manifest = _load(inputs[1])
            requester = response["requester_identity_id"]
            returned = response.get("object")
            object_id = returned["id"] if returned else None
            owner = manifest["objects"][object_id]
        except (KeyError, TypeError, ValueError, json.JSONDecodeError):
            return INVALID
        if response.get("fixture_id") != manifest.get("fixture_id"):
            return INVALID

        grants = manifest.get("grants", {}).get(object_id, [])
        if owner == requester or requester in grants:
            return REFUTED
        return SUPPORTED


class SyntheticTargetValidator:
    """TARGET — the affected object is operator-created and synthetic.

    This is the role that keeps a proof from resting on someone else's data.
    A finding whose target claim cannot be established is one where the
    evidence may be a third party's, and that is a privacy incident rather
    than a report.
    """

    validator_id = "target.synthetic_controlled_object"
    version = "1.0.0"
    exact_assertion = (
        "The affected object is recorded as synthetic and owned by a "
        "researcher-controlled identity."
    )
    possible_outcomes = OUTCOMES

    def validate(self, inputs: tuple[bytes, ...]) -> str:
        if len(inputs) != 2:
            return INVALID
        try:
            response = _load(inputs[0])
            manifest = _load(inputs[1])
            returned = response.get("object")
            object_id = returned["id"] if returned else None
            owner = manifest["objects"][object_id]
            controlled = manifest["controlled_identities"]
        except (KeyError, TypeError, ValueError, json.JSONDecodeError):
            return INVALID
        if response.get("fixture_id") != manifest.get("fixture_id"):
            return INVALID

        synthetic = manifest.get("synthetic_objects")
        if synthetic is not None and object_id not in synthetic:
            return REFUTED
        return SUPPORTED if owner in controlled else REFUTED


class ContractCurrencyValidator:
    """SCOPE — the evidence and the contract in force share a fingerprint.

    Inputs are two JSON blobs: what the evidence recorded, and what the
    registry says now. Comparing them inside a validator rather than in
    calling code means the answer arrives as a receipt that can be cited,
    instead of a boolean somebody asserted.
    """

    validator_id = "scope.contract_currency"
    version = "1.0.0"
    exact_assertion = (
        "The authority reference recorded on the evidence matches the contract "
        "fingerprint currently in force for the programme."
    )
    possible_outcomes = OUTCOMES

    def validate(self, inputs: tuple[bytes, ...]) -> str:
        if len(inputs) != 2:
            return INVALID
        try:
            recorded = _load(inputs[0])
            current = _load(inputs[1])
            recorded_ref = str(recorded["authority_ref"])
            current_ref = str(current["authority_ref"])
            status = str(current.get("status", "")).lower()
        except (KeyError, TypeError, ValueError, json.JSONDecodeError):
            return INVALID
        if not recorded_ref or not current_ref:
            return INVALID
        if status and status != "verified":
            return REFUTED
        return SUPPORTED if recorded_ref == current_ref else REFUTED


class EvidenceIntegrityValidator:
    """EVIDENCE_INTEGRITY — every artifact still hashes to what was recorded.

    Takes the recorded manifest and a freshly recomputed one. A mismatch means
    an artifact changed after it was stored, and a report built on it would
    cite evidence that no longer exists in the form it was verified in.
    """

    validator_id = "evidence.integrity"
    version = "1.0.0"
    exact_assertion = (
        "Every recorded evidence artifact still hashes to the digest stored "
        "in its manifest, and none is missing."
    )
    possible_outcomes = OUTCOMES

    def validate(self, inputs: tuple[bytes, ...]) -> str:
        if len(inputs) != 2:
            return INVALID
        try:
            recorded = _load(inputs[0])
            recomputed = _load(inputs[1])
        except (ValueError, json.JSONDecodeError):
            return INVALID
        if not isinstance(recorded, dict) or not isinstance(recomputed, dict):
            return INVALID
        if not recorded:
            return INVALID
        if set(recorded) != set(recomputed):
            return REFUTED
        return SUPPORTED if all(
            recorded[key] == recomputed[key] for key in recorded
        ) else REFUTED


ROLE_VALIDATORS = (
    OwnershipBoundaryValidator,
    SyntheticTargetValidator,
    ContractCurrencyValidator,
    EvidenceIntegrityValidator,
)


__all__ = [
    "ContractCurrencyValidator",
    "EvidenceIntegrityValidator",
    "OwnershipBoundaryValidator",
    "ROLE_VALIDATORS",
    "SyntheticTargetValidator",
]
