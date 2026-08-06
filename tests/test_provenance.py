"""Invariant I1 — inference must not be able to launder itself into proof."""

from __future__ import annotations

import pytest

from greytheory.provenance import Claim, ProvenanceError, Tag, partition


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


def test_promotion_requires_a_falsifiable_check():
    claim = Claim("account B can read A's object", Tag.INFERRED, source="model")
    with pytest.raises(ProvenanceError, match="falsifiable"):
        claim.promote_to_checked("check_always_true", could_have_failed=False)


def test_promotion_returns_a_new_claim_and_leaves_the_original_intact():
    claim = Claim("account B can read A's object", Tag.INFERRED, source="model")
    promoted = claim.promote_to_checked("check_12", could_have_failed=True)

    assert promoted.tag is Tag.CHECKED
    assert promoted.check_ref == "check_12"
    assert promoted.is_proven
    # The original stays as it was — provenance is a record, not a mutable field.
    assert claim.tag is Tag.INFERRED
    assert claim.check_ref is None


def test_a_checked_claim_cannot_be_promoted_again():
    claim = Claim("confirmed", Tag.CHECKED, source="validator", check_ref="c1")
    with pytest.raises(ProvenanceError, match="already checked"):
        claim.promote_to_checked("c2", could_have_failed=True)


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
