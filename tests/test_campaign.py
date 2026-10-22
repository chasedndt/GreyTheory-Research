"""Campaign assessment: honest stages, governance blockers named as such.

The central assertion in this file is that checked evidence about a programme's
own assets cannot be reported at LOCAL_FIXTURE, and that the reason is recorded
as a governance block rather than as unfinished work. Confusing "not permitted"
with "not done" is how a person ends up believing they are behind when they are
actually waiting on a decision.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from greytheory.authority.gate import AuthorityLevel
from greytheory.campaign import Stage, assess_campaign
from greytheory.provenance import Claim, Tag
from greytheory.report import ReportClaim, ReportDraft
from greytheory_intelligence.submission import SubmissionClaim

REPO = Path(__file__).resolve().parents[1]
GITLAB = REPO / "fixtures/programmes/public/hackerone-gitlab-2026-08-09/programme.json"


@pytest.fixture(scope="module")
def programme() -> dict:
    return json.loads(GITLAB.read_text(encoding="utf-8"))


def _checked(n: int = 2) -> tuple[SubmissionClaim, ...]:
    return tuple(
        SubmissionClaim(text=f"claim {i}", state="checked", receipt_id=f"receipt-{i}")
        for i in range(n)
    )


def _probeable(programme: dict) -> dict:
    """A programme whose own contract permits live work.

    Every real record compiled so far caps at LOCAL_FIXTURE, and the ceiling is
    checked before the posture. Tests about the *host posture* therefore need a
    programme that is not already capped, or they would silently assert the
    contract ceiling instead and pass for the wrong reason.
    """

    return dict(programme, max_authority="PASSIVE_HTTP")


def test_every_real_programme_is_capped_at_local_fixture(programme):
    """Recorded because it is easy to miss: raising the host posture alone
    would still not permit probing any programme compiled so far."""

    assert programme["max_authority"] == "LOCAL_FIXTURE"

    state = assess_campaign(
        programme, execution_posture=AuthorityLevel.PASSIVE_HTTP, claims=_checked()
    ).state(Stage.EVIDENCE)

    assert not state.satisfied and state.blocked_by_governance
    assert "caps authority" in state.because


def _complete_draft() -> ReportDraft:
    draft = ReportDraft(finding_id="f-1", authority_ref="a" * 64)
    for name in ("title", "programme", "asset", "summary", "affected_feature",
                 "expected_result", "actual_result", "security_impact",
                 "data_minimisation_statement", "severity_proposed",
                 "severity_framework", "severity_rationale", "remediation"):
        if hasattr(draft, name):
            setattr(draft, name, f"written {name}")
    draft.steps = ["send the request as user A", "observe the response"]
    draft.evidence_index = ["receipt-0"]
    # A required section: a report without a claim matrix has asserted nothing
    # traceable. The claim inside it is checked and carries its receipt, which
    # is what makes the premature-draft case interesting - the *report* asserts
    # proof while the *campaign* has been given no checked evidence at all.
    draft.claim_matrix = [
        ReportClaim(
            claim=Claim(
                text="user A was served user B's object",
                tag=Tag.CHECKED,
                source="local.two_account.cross_owner_read",
                check_ref="check-0001",
            ),
            evidence_refs=("receipt-0",),
        )
    ]
    return draft


# -- the programme and its curriculum ----------------------------------------

def test_a_real_verified_programme_satisfies_the_first_two_stages(programme):
    c = assess_campaign(programme, execution_posture=AuthorityLevel.LOCAL_FIXTURE)

    assert c.state(Stage.PROGRAMME).satisfied
    assert c.state(Stage.CURRICULUM).satisfied
    assert "in-scope assets" in c.state(Stage.PROGRAMME).because


def test_an_unverified_programme_is_blocked_by_governance_not_effort(programme):
    unverified = dict(programme)
    unverified.pop("verified_at", None)

    state = assess_campaign(unverified, execution_posture=AuthorityLevel.LOCAL_FIXTURE).state(Stage.PROGRAMME)

    assert not state.satisfied and state.blocked_by_governance
    assert "verif" in state.because


def test_a_programme_with_no_scope_is_refused(programme):
    empty = dict(programme, in_scope=[])
    state = assess_campaign(empty, execution_posture=AuthorityLevel.LOCAL_FIXTURE).state(Stage.PROGRAMME)
    assert not state.satisfied and not state.blocked_by_governance


# -- study -------------------------------------------------------------------

def test_a_topic_outside_what_the_scope_selected_is_refused(programme):
    c = assess_campaign(
        programme, execution_posture=AuthorityLevel.LOCAL_FIXTURE,
        chosen_card_id="not-a-selected-topic", practised_cards=frozenset({"not-a-selected-topic"}),
    )
    state = c.state(Stage.STUDY)
    assert not state.satisfied and "not among the topics" in state.because


def test_a_chosen_topic_needs_a_practice_receipt(programme):
    offered = assess_campaign(programme, execution_posture=AuthorityLevel.LOCAL_FIXTURE)
    assert offered.state(Stage.CURRICULUM).satisfied
    from greytheory.learning.programme_curriculum import curriculum_for_programme

    card = curriculum_for_programme(programme).card_ids[0]

    unpractised = assess_campaign(
        programme, execution_posture=AuthorityLevel.LOCAL_FIXTURE, chosen_card_id=card
    ).state(Stage.STUDY)
    assert not unpractised.satisfied and "no practice receipt" in unpractised.because

    practised = assess_campaign(
        programme, execution_posture=AuthorityLevel.LOCAL_FIXTURE,
        chosen_card_id=card, practised_cards=frozenset({card}),
    ).state(Stage.STUDY)
    assert practised.satisfied


# -- the posture gate, which is the point ------------------------------------

@pytest.mark.parametrize("posture", [AuthorityLevel.NONE, AuthorityLevel.LOCAL_FIXTURE])
def test_checked_evidence_cannot_be_claimed_below_passive_http(programme, posture):
    """Even with checked claims in hand, the posture forbids the assertion."""

    state = assess_campaign(
        _probeable(programme), execution_posture=posture, claims=_checked()
    ).state(Stage.EVIDENCE)

    assert not state.satisfied
    assert state.blocked_by_governance
    assert "PASSIVE_HTTP" in state.because
    assert "operator decisions" in state.next_action


def test_at_passive_http_missing_evidence_is_work_not_governance(programme):
    state = assess_campaign(
        _probeable(programme), execution_posture=AuthorityLevel.PASSIVE_HTTP,
        claims=(SubmissionClaim(text="c", state="inferred"),),
    ).state(Stage.EVIDENCE)

    assert not state.satisfied
    assert not state.blocked_by_governance, "unproven claims are work to do, not permission to seek"
    assert "none checked" in state.because


def test_evidence_is_satisfied_only_by_checked_receipt_backed_claims(programme):
    state = assess_campaign(
        _probeable(programme), execution_posture=AuthorityLevel.PASSIVE_HTTP, claims=_checked()
    ).state(Stage.EVIDENCE)
    assert state.satisfied

    no_receipt = assess_campaign(
        _probeable(programme), execution_posture=AuthorityLevel.PASSIVE_HTTP,
        claims=(SubmissionClaim(text="c", state="checked", receipt_id=""),),
    ).state(Stage.EVIDENCE)
    assert not no_receipt.satisfied


# -- draft and submission ----------------------------------------------------

def test_an_incomplete_draft_names_what_is_missing(programme):
    state = assess_campaign(
        programme, execution_posture=AuthorityLevel.LOCAL_FIXTURE,
        draft=ReportDraft(finding_id="f-1", authority_ref="a" * 64),
    ).state(Stage.DRAFT)

    assert not state.satisfied and "missing" in state.because


def test_submission_needs_every_claim_checked_then_the_switch_then_approval(programme):
    mixed = _checked(1) + (SubmissionClaim(text="guess", state="inferred"),)
    s = assess_campaign(
        programme, execution_posture=AuthorityLevel.PASSIVE_HTTP, claims=mixed,
        submission_enabled=True, submission_approved_by="operator:chase",
    ).state(Stage.SUBMISSION)
    assert not s.satisfied and "not checked" in s.because

    switched_off = assess_campaign(
        programme, execution_posture=AuthorityLevel.PASSIVE_HTTP, claims=_checked(),
        submission_enabled=False, submission_approved_by="operator:chase",
    ).state(Stage.SUBMISSION)
    assert not switched_off.satisfied and switched_off.blocked_by_governance
    assert "kill switch" in switched_off.because

    unapproved = assess_campaign(
        programme, execution_posture=AuthorityLevel.PASSIVE_HTTP, claims=_checked(),
        submission_enabled=True,
    ).state(Stage.SUBMISSION)
    assert not unapproved.satisfied and unapproved.blocked_by_governance

    ready = assess_campaign(
        programme, execution_posture=AuthorityLevel.PASSIVE_HTTP, claims=_checked(),
        submission_enabled=True, submission_approved_by="operator:chase",
    ).state(Stage.SUBMISSION)
    assert ready.satisfied


# -- the campaign as a whole -------------------------------------------------

def test_current_is_the_first_unsatisfied_stage(programme):
    c = assess_campaign(programme, execution_posture=AuthorityLevel.LOCAL_FIXTURE)
    assert c.current.stage is Stage.STUDY, "programme and curriculum are already satisfied"
    assert not c.complete


def test_a_draft_written_above_missing_evidence_is_flagged_as_premature(programme):
    """The failure this product exists to prevent, named rather than hidden."""

    c = assess_campaign(
        programme, execution_posture=AuthorityLevel.LOCAL_FIXTURE, draft=_complete_draft()
    )

    assert c.state(Stage.DRAFT).satisfied
    assert not c.state(Stage.EVIDENCE).satisfied
    assert Stage.DRAFT in c.premature


def test_the_record_never_implies_a_submission_happened(programme):
    d = assess_campaign(
        programme, execution_posture=AuthorityLevel.PASSIVE_HTTP, claims=_checked(),
        submission_enabled=True, submission_approved_by="operator:chase",
    ).to_dict()

    assert d["submitted"] is False
    assert d["schema"] == "greytheory.campaign/1"
    assert len(d["stages"]) == len(Stage)
