"""One lifecycle, with a hard seam at the boundary of what we may assert.

Invariant I5: the system records programme outcomes. It never awards them.
"""

from __future__ import annotations

import pytest

from greytheory.findings import Finding, Taxonomy, TransitionError
from greytheory.provenance import Claim, Tag


# --- role-binding helpers -------------------------------------------------
#
# report_ready now requires a claim in each of the seven roles rather than a
# count of checked claims. These helpers build a well-formed set so the
# lifecycle tests exercise transitions rather than re-testing claims.py.

from datetime import datetime, timezone

from greytheory.checks import ValidatorRegistry
from greytheory.claims import (
    JUDGEMENT_ROLES,
    MUST_BE_CHECKED,
    ClaimRole,
    RoleBinding,
)
from greytheory.findings import ScopeRecheck

NOW = datetime(2026, 8, 9, 12, 0, tzinfo=timezone.utc)
AUTHORITY = "fingerprint_abc"


def _checked_binding(registry: ValidatorRegistry, role: ClaimRole) -> RoleBinding:
    assertion = f"Deterministic answer for the {role.value} role."

    class _Validator:
        validator_id = f"test.role.{role.value}"
        version = "1.0.0"
        exact_assertion = assertion
        possible_outcomes = ("supported", "refuted")

        def validate(self, inputs):
            return "supported"

    registry.register(_Validator())
    receipt = registry.run(
        _Validator.validator_id, inputs=(role.value.encode(),), authority_ref=AUTHORITY
    )
    claim = registry.promote(Claim(assertion, Tag.INFERRED, "test"), receipt)
    return RoleBinding(role=role, claim=claim, receipt=receipt)


def bind_every_role(item: Finding) -> Finding:
    registry = ValidatorRegistry()
    for role in MUST_BE_CHECKED:
        item.bind_role(_checked_binding(registry, role))
    for role in JUDGEMENT_ROLES:
        item.bind_role(
            RoleBinding(
                role=role,
                claim=Claim(
                    f"Operator position on the {role.value} role.",
                    Tag.INFERRED,
                    "operator:test",
                ),
                uncertainty=f"What remains unknown about {role.value}.",
            )
        )
    return item


def current_scope(item: Finding) -> ScopeRecheck:
    return ScopeRecheck(
        finding_authority_ref=item.authority_ref,
        current_authority_ref=item.authority_ref,
        programme_id="test",
        checked_at=NOW,
        contract_status="verified",
    )


def finding(**overrides) -> Finding:
    base = dict(
        id="finding_1",
        title="BOLA in document sharing",
        lane=3,
        target="app.example.test",
        authority_ref="fingerprint_abc",
    )
    base.update(overrides)
    return Finding(**base)


def walk_to_report_ready(item: Finding) -> None:
    bind_every_role(item)
    for state in (
        Taxonomy.CONTEXTUAL,
        Taxonomy.CANDIDATE,
        Taxonomy.VALIDATED,
        Taxonomy.REPORT_READY,
    ):
        item.advance(state, actor="chase")


def test_a_finding_cannot_exist_without_an_authority_reference():
    with pytest.raises(ValueError, match="authority reference"):
        finding(authority_ref="")


def test_internal_progression():
    item = finding()
    walk_to_report_ready(item)
    assert item.state is Taxonomy.REPORT_READY
    assert not item.is_external
    assert len(item.history) == 4


def test_states_cannot_be_skipped():
    item = finding()
    with pytest.raises(TransitionError, match="not a permitted transition"):
        item.advance(Taxonomy.VALIDATED, actor="chase")


def test_report_ready_requires_every_role_to_be_answered():
    # The old guard was "at least one checked claim", which a finding could
    # satisfy while proving nothing about whether anything was wrong.
    item = finding()
    item.claims.append(Claim("looks exploitable", Tag.INFERRED, "model"))
    item.advance(Taxonomy.CONTEXTUAL, actor="chase")
    item.advance(Taxonomy.CANDIDATE, actor="chase")
    item.advance(Taxonomy.VALIDATED, actor="chase")
    with pytest.raises(TransitionError, match="seven roles"):
        item.advance(Taxonomy.REPORT_READY, actor="chase")


def test_a_partial_set_of_roles_still_blocks():
    item = finding()
    bind_every_role(item)
    item.role_bindings = [
        b for b in item.role_bindings if b.role is not ClaimRole.BOUNDARY
    ]
    for state in (Taxonomy.CONTEXTUAL, Taxonomy.CANDIDATE, Taxonomy.VALIDATED):
        item.advance(state, actor="chase")
    with pytest.raises(TransitionError, match="boundary"):
        item.advance(Taxonomy.REPORT_READY, actor="chase")


def test_submission_requires_a_scope_recheck():
    item = finding()
    walk_to_report_ready(item)
    with pytest.raises(TransitionError, match="scope recheck"):
        item.advance(
            Taxonomy.SUBMITTED, actor="chase", operator_approval="approval_9"
        )


def test_submission_blocks_when_the_contract_has_changed_since_the_evidence():
    # Evidence gathered Monday, scope narrowed Wednesday, report sent Friday.
    # Nothing earlier in the lifecycle would notice.
    item = finding()
    walk_to_report_ready(item)
    moved = ScopeRecheck(
        finding_authority_ref=item.authority_ref,
        current_authority_ref="a_different_fingerprint",
        programme_id="test",
        checked_at=NOW,
        contract_status="verified",
    )
    with pytest.raises(TransitionError, match="contract in force has changed"):
        item.advance(
            Taxonomy.SUBMITTED,
            actor="chase",
            operator_approval="approval_9",
            scope_recheck=moved,
        )


def test_the_recheck_must_belong_to_this_finding():
    item = finding()
    walk_to_report_ready(item)
    someone_elses = ScopeRecheck(
        finding_authority_ref="another_findings_ref",
        current_authority_ref="another_findings_ref",
        programme_id="test",
        checked_at=NOW,
        contract_status="verified",
    )
    with pytest.raises(TransitionError, match="different finding"):
        item.advance(
            Taxonomy.SUBMITTED,
            actor="chase",
            operator_approval="approval_9",
            scope_recheck=someone_elses,
        )


def test_submission_requires_an_operator_approval():
    item = finding()
    walk_to_report_ready(item)
    with pytest.raises(TransitionError, match="approval reference"):
        item.advance(Taxonomy.SUBMITTED, actor="chase")

    item.advance(Taxonomy.SUBMITTED, actor="chase", operator_approval="approval_9", scope_recheck=current_scope(item))
    assert item.is_external


def test_programme_outcomes_cannot_be_asserted_without_evidence():
    item = finding()
    walk_to_report_ready(item)
    item.advance(Taxonomy.SUBMITTED, actor="chase", operator_approval="approval_9", scope_recheck=current_scope(item))
    item.advance(
        Taxonomy.TRIAGED, actor="chase", programme_evidence="h1_msg_1001"
    )

    # This is the whole point of I5 — we cannot call our own finding valid.
    with pytest.raises(TransitionError, match="never awards itself"):
        item.advance(Taxonomy.VALID, actor="chase")

    item.advance(Taxonomy.VALID, actor="chase", programme_evidence="h1_msg_1002")
    assert item.state is Taxonomy.VALID


def test_full_lifecycle_through_to_disclosure():
    item = finding()
    walk_to_report_ready(item)
    item.advance(Taxonomy.SUBMITTED, actor="chase", operator_approval="approval_9", scope_recheck=current_scope(item))
    for state in (
        Taxonomy.TRIAGED,
        Taxonomy.VALID,
        Taxonomy.REWARDED,
        Taxonomy.FIXED,
        Taxonomy.RETESTED,
        Taxonomy.DISCLOSED,
    ):
        item.advance(state, actor="chase", programme_evidence=f"evidence_{state.value}")
    assert item.state is Taxonomy.DISCLOSED


def test_duplicate_path_closes_privately():
    item = finding()
    walk_to_report_ready(item)
    item.advance(Taxonomy.SUBMITTED, actor="chase", operator_approval="a1", scope_recheck=current_scope(item))
    item.advance(Taxonomy.TRIAGED, actor="chase", programme_evidence="e1")
    item.advance(Taxonomy.DUPLICATE, actor="chase", programme_evidence="e2")
    item.advance(Taxonomy.PRIVATE_CLOSED, actor="chase", programme_evidence="e3")
    assert item.state is Taxonomy.PRIVATE_CLOSED


class TestDemotion:
    def test_internal_findings_can_be_walked_back_down(self):
        item = finding()
        walk_to_report_ready(item)
        item.demote(Taxonomy.CANDIDATE, actor="chase", reason="reproduction failed")
        assert item.state is Taxonomy.CANDIDATE
        assert "demoted" in item.history[-1]["note"]

    def test_demotion_must_actually_go_down(self):
        item = finding()
        item.advance(Taxonomy.CONTEXTUAL, actor="chase")
        with pytest.raises(TransitionError, match="not below"):
            item.demote(Taxonomy.VALIDATED, actor="chase", reason="wishful")

    def test_programme_outcomes_cannot_be_demoted(self):
        item = finding()
        walk_to_report_ready(item)
        item.advance(Taxonomy.SUBMITTED, actor="chase", operator_approval="a1", scope_recheck=current_scope(item))
        with pytest.raises(TransitionError, match="internal states"):
            item.demote(Taxonomy.CANDIDATE, actor="chase", reason="regret")


def test_provenance_summary_counts_each_tag():
    item = finding()
    item.claims.extend(
        [
            Claim("observed a", Tag.OBSERVED, "tool"),
            Claim("inferred b", Tag.INFERRED, "model"),
            Claim("checked c", Tag.CHECKED, "validator", "c1"),
        ]
    )
    assert item.provenance_summary() == {"observed": 1, "checked": 1, "inferred": 1}
    assert len(item.proven_claims) == 1


def test_round_trips_through_dict():
    item = finding()
    walk_to_report_ready(item)
    restored = Finding.from_dict(item.to_dict())
    assert restored.state is item.state
    assert restored.authority_ref == item.authority_ref
    assert len(restored.claims) == len(item.claims)
