"""One lifecycle, with a hard seam at the boundary of what we may assert.

Invariant I5: the system records programme outcomes. It never awards them.
"""

from __future__ import annotations

import pytest

from greytheory.findings import Finding, Taxonomy, TransitionError
from greytheory.provenance import Claim, Tag


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
    item.claims.append(Claim("B read A's object", Tag.CHECKED, "validator", "check_1"))
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


def test_report_ready_requires_at_least_one_checked_claim():
    # Inference alone is not a report.
    item = finding()
    item.claims.append(Claim("looks exploitable", Tag.INFERRED, "model"))
    item.advance(Taxonomy.CONTEXTUAL, actor="chase")
    item.advance(Taxonomy.CANDIDATE, actor="chase")
    item.advance(Taxonomy.VALIDATED, actor="chase")
    with pytest.raises(TransitionError, match="checked"):
        item.advance(Taxonomy.REPORT_READY, actor="chase")


def test_submission_requires_an_operator_approval():
    item = finding()
    walk_to_report_ready(item)
    with pytest.raises(TransitionError, match="approval reference"):
        item.advance(Taxonomy.SUBMITTED, actor="chase")

    item.advance(Taxonomy.SUBMITTED, actor="chase", operator_approval="approval_9")
    assert item.is_external


def test_programme_outcomes_cannot_be_asserted_without_evidence():
    item = finding()
    walk_to_report_ready(item)
    item.advance(Taxonomy.SUBMITTED, actor="chase", operator_approval="approval_9")
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
    item.advance(Taxonomy.SUBMITTED, actor="chase", operator_approval="approval_9")
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
    item.advance(Taxonomy.SUBMITTED, actor="chase", operator_approval="a1")
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
        item.advance(Taxonomy.SUBMITTED, actor="chase", operator_approval="a1")
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
