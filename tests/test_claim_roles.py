"""Claim roles, the claim-evidence matrix, and the role validators."""

# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 ChaseInTech

from __future__ import annotations

import json
from datetime import datetime, timezone

import pytest

from greytheory.checks import ValidatorRegistry
from greytheory.claims import (
    JUDGEMENT_ROLES,
    MUST_BE_CHECKED,
    REQUIRED_ROLES,
    ClaimRole,
    ClaimRoleError,
    RoleBinding,
    build_matrix,
    readiness_problems,
)
from greytheory.provenance import Claim, Tag
from greytheory.validators import (
    ContractCurrencyValidator,
    EvidenceIntegrityValidator,
    OwnershipBoundaryValidator,
    SyntheticTargetValidator,
)

NOW = datetime(2026, 8, 9, 12, 0, tzinfo=timezone.utc)
AUTHORITY = "fingerprint_abc"


def blob(value) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def receipted(role: ClaimRole) -> tuple[Claim, object]:
    assertion = f"Deterministic answer for {role.value}."

    class _V:
        validator_id = f"test.{role.value}"
        version = "1.0.0"
        exact_assertion = assertion
        possible_outcomes = ("supported", "refuted")

        def validate(self, inputs):
            return "supported"

    registry = ValidatorRegistry()
    registry.register(_V())
    receipt = registry.run(_V.validator_id, inputs=(b"x",), authority_ref=AUTHORITY)
    return registry.promote(Claim(assertion, Tag.INFERRED, "test"), receipt), receipt


def full_set() -> list[RoleBinding]:
    bindings = []
    for role in MUST_BE_CHECKED:
        claim, receipt = receipted(role)
        bindings.append(RoleBinding(role=role, claim=claim, receipt=receipt))
    for role in JUDGEMENT_ROLES:
        bindings.append(
            RoleBinding(
                role=role,
                claim=Claim(f"Position on {role.value}.", Tag.INFERRED, "operator"),
                uncertainty=f"Unknown about {role.value}.",
            )
        )
    return bindings


class TestRoleSets:
    def test_every_role_is_either_checked_or_judgement(self):
        assert MUST_BE_CHECKED | JUDGEMENT_ROLES == set(REQUIRED_ROLES)
        assert not (MUST_BE_CHECKED & JUDGEMENT_ROLES)

    def test_impact_is_never_machine_settled(self):
        # Whether a proven behaviour matters is a judgement about the product,
        # its users and the programme's view.
        assert ClaimRole.IMPACT in JUDGEMENT_ROLES

    def test_reproduction_is_a_judgement_role(self):
        # Checkable in principle, but only by acting on the target a second
        # time. Requiring a receipt would push every finding into doubling its
        # interaction, against minimum impact.
        assert ClaimRole.REPRODUCTION in JUDGEMENT_ROLES


class TestBindingSoundness:
    def test_a_checked_role_rejects_an_inferred_claim(self):
        with pytest.raises(ClaimRoleError, match="must be answered by a 'checked'"):
            RoleBinding(
                role=ClaimRole.BOUNDARY,
                claim=Claim("I think so", Tag.INFERRED, "model"),
            )

    def test_a_checked_role_requires_its_receipt(self):
        claim, _ = receipted(ClaimRole.BOUNDARY)
        with pytest.raises(ClaimRoleError, match="requires the validator receipt"):
            RoleBinding(role=ClaimRole.BOUNDARY, claim=claim)

    def test_the_receipt_must_match_the_claim(self):
        claim, _ = receipted(ClaimRole.BOUNDARY)
        _, other = receipted(ClaimRole.TARGET)
        with pytest.raises(ClaimRoleError, match="but its claim references"):
            RoleBinding(role=ClaimRole.BOUNDARY, claim=claim, receipt=other)

    def test_a_judgement_role_must_state_its_uncertainty(self):
        with pytest.raises(ClaimRoleError, match="must state what"):
            RoleBinding(
                role=ClaimRole.IMPACT,
                claim=Claim("Very bad indeed", Tag.INFERRED, "operator"),
            )


class TestReadiness:
    def test_a_complete_set_has_no_problems(self):
        assert readiness_problems(full_set()) == []

    def test_each_missing_role_is_named(self):
        bindings = [b for b in full_set() if b.role is not ClaimRole.SCOPE]
        problems = readiness_problems(bindings)
        assert any("'scope'" in p for p in problems)

    def test_one_claim_cannot_answer_two_roles(self):
        # The shortcut the old count-based guard invited.
        claim, receipt = receipted(ClaimRole.BOUNDARY)
        duplicated = Claim(
            claim.text, Tag.CHECKED, claim.source, claim.check_ref
        )
        bindings = full_set() + [
            RoleBinding(role=ClaimRole.TARGET, claim=duplicated, receipt=receipt)
        ]
        assert any("cannot be two different kinds" in p for p in readiness_problems(bindings))


class TestMatrix:
    def test_supported_and_asserted_are_separated(self):
        matrix = build_matrix(full_set())
        assert len(matrix.supported) == len(MUST_BE_CHECKED)
        assert len(matrix.asserted) == len(JUDGEMENT_ROLES)
        assert matrix.complete

    def test_missing_roles_are_rendered_as_missing(self):
        bindings = [b for b in full_set() if b.role is not ClaimRole.IMPACT]
        matrix = build_matrix(bindings)
        assert not matrix.complete
        assert "**missing**" in matrix.render()

    def test_render_is_a_table_a_report_can_embed(self):
        rendered = build_matrix(full_set()).render()
        assert rendered.startswith("| Role | Claim |")
        assert "supported" in rendered and "asserted" in rendered


class TestOwnershipBoundaryValidator:
    def run(self, response, manifest) -> str:
        return OwnershipBoundaryValidator().validate((blob(response), blob(manifest)))

    def test_a_non_owner_read_is_supported(self):
        assert self.run(
            {"fixture_id": "f", "requester_identity_id": "a", "object": {"id": "o1"}},
            {"fixture_id": "f", "objects": {"o1": "b"}},
        ) == "supported"

    def test_the_owner_reading_their_own_object_is_refuted(self):
        assert self.run(
            {"fixture_id": "f", "requester_identity_id": "b", "object": {"id": "o1"}},
            {"fixture_id": "f", "objects": {"o1": "b"}},
        ) == "refuted"

    def test_an_explicit_grant_is_refuted(self):
        # A shared object read by its grantee is a feature, not a finding.
        assert self.run(
            {"fixture_id": "f", "requester_identity_id": "a", "object": {"id": "o1"}},
            {"fixture_id": "f", "objects": {"o1": "b"}, "grants": {"o1": ["a"]}},
        ) == "refuted"

    def test_mismatched_fixtures_are_invalid(self):
        assert self.run(
            {"fixture_id": "f", "requester_identity_id": "a", "object": {"id": "o1"}},
            {"fixture_id": "other", "objects": {"o1": "b"}},
        ) == "invalid_input"


class TestSyntheticTargetValidator:
    def run(self, response, manifest) -> str:
        return SyntheticTargetValidator().validate((blob(response), blob(manifest)))

    def test_a_controlled_synthetic_object_is_supported(self):
        assert self.run(
            {"fixture_id": "f", "object": {"id": "o1"}},
            {"fixture_id": "f", "objects": {"o1": "b"}, "controlled_identities": ["b"]},
        ) == "supported"

    def test_an_object_owned_by_an_uncontrolled_party_is_refuted(self):
        # This is the guard against a proof resting on a real user's data.
        assert self.run(
            {"fixture_id": "f", "object": {"id": "o1"}},
            {"fixture_id": "f", "objects": {"o1": "stranger"}, "controlled_identities": ["b"]},
        ) == "refuted"

    def test_an_object_absent_from_the_synthetic_list_is_refuted(self):
        assert self.run(
            {"fixture_id": "f", "object": {"id": "o1"}},
            {
                "fixture_id": "f",
                "objects": {"o1": "b"},
                "controlled_identities": ["b"],
                "synthetic_objects": ["o2"],
            },
        ) == "refuted"


class TestContractCurrencyValidator:
    def run(self, recorded, current) -> str:
        return ContractCurrencyValidator().validate((blob(recorded), blob(current)))

    def test_matching_fingerprints_are_supported(self):
        assert self.run(
            {"authority_ref": "abc"}, {"authority_ref": "abc", "status": "verified"}
        ) == "supported"

    def test_a_changed_contract_is_refuted(self):
        assert self.run(
            {"authority_ref": "abc"}, {"authority_ref": "def", "status": "verified"}
        ) == "refuted"

    def test_an_unverified_contract_is_refuted_even_when_it_matches(self):
        assert self.run(
            {"authority_ref": "abc"}, {"authority_ref": "abc", "status": "blocked"}
        ) == "refuted"

    def test_a_missing_reference_is_invalid(self):
        assert self.run({"authority_ref": ""}, {"authority_ref": "abc"}) == "invalid_input"


class TestEvidenceIntegrityValidator:
    def run(self, recorded, recomputed) -> str:
        return EvidenceIntegrityValidator().validate((blob(recorded), blob(recomputed)))

    def test_identical_digests_are_supported(self):
        assert self.run({"a": "1", "b": "2"}, {"a": "1", "b": "2"}) == "supported"

    def test_a_changed_digest_is_refuted(self):
        assert self.run({"a": "1"}, {"a": "changed"}) == "refuted"

    def test_a_missing_artifact_is_refuted(self):
        assert self.run({"a": "1", "b": "2"}, {"a": "1"}) == "refuted"

    def test_an_empty_manifest_is_invalid_rather_than_vacuously_true(self):
        # "Nothing to check" must never read as "everything verified".
        assert self.run({}, {}) == "invalid_input"


def test_every_role_validator_declares_a_refuting_outcome():
    for validator in (
        OwnershipBoundaryValidator(),
        SyntheticTargetValidator(),
        ContractCurrencyValidator(),
        EvidenceIntegrityValidator(),
    ):
        # A check that cannot fail proves nothing.
        assert "refuted" in validator.possible_outcomes
        assert len(set(validator.possible_outcomes)) >= 2
