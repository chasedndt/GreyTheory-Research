"""Invariant I1 — inference must not be able to launder itself into proof."""

from __future__ import annotations

import pytest

from greytheory.checks import CheckError, ValidatorRegistry
from greytheory.provenance import Claim, ProvenanceError, Tag, partition


class ExactValidator:
    validator_id = "exact"
    version = "1.0.0"
    exact_assertion = "account B can read A's object"
    possible_outcomes = ("supported", "refuted")

    def __init__(self, outcome="supported"):
        self.outcome = outcome

    def validate(self, inputs):
        return self.outcome


def test_checked_claim_requires_a_check_reference():
    with pytest.raises(ProvenanceError, match="must reference the check"):
        Claim(text="the endpoint is vulnerable", tag=Tag.CHECKED, source="validator")


def test_unproven_claim_may_not_carry_a_check_reference():
    with pytest.raises(ProvenanceError, match="must not carry a check reference"):
        Claim(
            text="probably vulnerable",
            tag=Tag.INFERRED,
            source="model",
            check_ref="check_001",
        )


def test_only_checked_claims_are_proven():
    observed = Claim("returned 200", Tag.OBSERVED, source="http_probe")
    inferred = Claim("likely misconfigured", Tag.INFERRED, source="model")
    checked = Claim("body differs across roles", Tag.CHECKED, "validator", "check_7")

    assert not observed.is_proven
    assert not inferred.is_proven
    assert checked.is_proven


def test_promotion_requires_a_registered_validator():
    claim = Claim("account B can read A's object", Tag.INFERRED, source="model")
    registry = ValidatorRegistry()
    with pytest.raises(CheckError, match="not registered"):
        registry.run("exact", inputs=(b"artifact",), authority_ref="contract")


def test_registry_receipt_promotes_matching_claim_and_leaves_original_intact():
    claim = Claim("account B can read A's object", Tag.INFERRED, source="model")
    registry = ValidatorRegistry()
    registry.register(ExactValidator())
    receipt = registry.run("exact", inputs=(b"artifact",), authority_ref="contract")
    promoted = registry.promote(claim, receipt)

    assert promoted.tag is Tag.CHECKED
    assert promoted.check_ref == receipt.id
    assert promoted.source == "validator:exact@1.0.0"
    assert promoted.is_proven
    # The original stays as it was — provenance is a record, not a mutable field.
    assert claim.tag is Tag.INFERRED
    assert claim.check_ref is None


def test_receipt_is_single_use_and_a_refuted_receipt_cannot_promote():
    claim = Claim("account B can read A's object", Tag.INFERRED, source="model")
    registry = ValidatorRegistry()
    registry.register(ExactValidator())
    receipt = registry.run("exact", inputs=(b"artifact",), authority_ref="contract")
    registry.promote(claim, receipt)
    with pytest.raises(CheckError, match="already been consumed"):
        registry.promote(claim, receipt)

    failing = ValidatorRegistry()
    failing.register(ExactValidator("refuted"))
    failed = failing.run("exact", inputs=(b"artifact",), authority_ref="contract")
    with pytest.raises(CheckError, match="supported"):
        failing.promote(claim, failed)


def test_partition_separates_the_three_tags():
    claims = [
        Claim("a", Tag.OBSERVED, "tool"),
        Claim("b", Tag.OBSERVED, "tool"),
        Claim("c", Tag.INFERRED, "model"),
        Claim("d", Tag.CHECKED, "validator", "c1"),
    ]
    result = partition(claims)
    assert len(result[Tag.OBSERVED]) == 2
    assert len(result[Tag.INFERRED]) == 1
    assert len(result[Tag.CHECKED]) == 1


def test_a_claim_must_say_something_and_name_a_source():
    with pytest.raises(ProvenanceError):
        Claim("   ", Tag.OBSERVED, source="tool")
    with pytest.raises(ProvenanceError):
        Claim("something", Tag.OBSERVED, source="  ")
