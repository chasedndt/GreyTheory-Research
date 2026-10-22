"""The campaign read-model section.

The assertion that matters most here is that a DRAFT contract is not reported
as verified. Every ScopeContract carries a `verified_at` datetime whether or
not anyone reviewed it, so an adapter that trusted that field would quietly
promote unreviewed scope - the same shape as every other defect this codebase
has had to fix.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone

import pytest

from greytheory.authority.gate import AuthorityLevel
from greytheory.authority.scope import ContractStatus
from greytheory_app.campaign_section import build_campaign_section
from greytheory_app.contracts import ReadinessStatus

NOW = datetime(2026, 8, 9, 10, 30, tzinfo=timezone.utc)


class _Pattern:
    def __init__(self, value: str, note: str = "") -> None:
        self.type, self.value, self.note = "exact", value, note


class _Contract:
    def __init__(
        self,
        *,
        status: ContractStatus = ContractStatus.VERIFIED,
        max_authority: str = "PASSIVE_HTTP",
        ambiguities=(),
    ) -> None:
        self.status = status
        self.verified_at = NOW
        self.max_authority = max_authority
        self.ambiguities = list(ambiguities)
        self.prohibited_techniques = ["denial_of_service"]
        self.assets_in_scope = [
            _Pattern("customers.example.test", "HackerOne scope CSV"),
            _Pattern("api.example.test", "REST API"),
        ]

    def fingerprint(self):
        """Derived the way ScopeContract derives it, not a constant.

        A stub returning a fixed string would let the draft-matching test pass
        while never exercising the property that matters: a substantive scope
        change must produce a different fingerprint, so a draft written against
        the old contract stops matching.
        """

        material = "|".join([
            self.max_authority,
            ";".join(sorted(p.value for p in self.assets_in_scope)),
            ";".join(sorted(self.prohibited_techniques)),
        ])
        return "sha256:" + hashlib.sha256(material.encode("utf-8")).hexdigest()


class _Registry:
    def __init__(self, contracts: dict) -> None:
        self._contracts = contracts

    def programmes(self):
        return list(self._contracts)

    def current_contract(self, programme_id):
        return self._contracts.get(programme_id)


class _Receipt:
    def __init__(self, card_id: str) -> None:
        self.card_id = card_id


class _Receipts:
    def __init__(self, *card_ids: str) -> None:
        self._receipts = tuple(_Receipt(c) for c in card_ids)

    def receipts(self):
        return self._receipts


def _section(registry=None, posture=AuthorityLevel.LOCAL_FIXTURE, receipts=None, **over):
    if registry is None:
        registry = _Registry({"example-programme": _Contract()})
    return build_campaign_section(registry, posture=posture, fixture_receipts=receipts, **over)


class _Journey:
    def __init__(self, card_id, status="active", updated_at=1):
        self.card_id, self.status, self.updated_at = card_id, status, updated_at


class _Journeys:
    def __init__(self, *journeys):
        self._journeys = journeys

    def journeys(self):
        return self._journeys


class _Draft:
    def __init__(self, authority_ref, missing=(), placeholders=(), absolutes=()):
        self.authority_ref = authority_ref
        self._missing, self._placeholders, self._absolutes = list(missing), list(placeholders), list(absolutes)

    def missing_sections(self):
        return self._missing

    def placeholders(self):
        return self._placeholders

    def absolute_claims(self):
        return self._absolutes


# -- the four inputs that were previously unreachable ------------------------

def test_an_active_journey_supplies_the_chosen_topic():
    from greytheory.learning.programme_curriculum import curriculum_for_programme
    from greytheory_app.campaign_section import _programme_dict

    contract = _Contract()
    offered = curriculum_for_programme(_programme_dict("p", contract)).card_ids[0]

    section = _section(
        _Registry({"p": contract}),
        receipts=_Receipts(offered),
        journeys=_Journeys(_Journey(offered)),
    )
    stages = dict(pair.split("=") for pair in _attrs(section.records[0])["stages"].split(","))

    assert stages["study"] == "ok", "a practised, offered topic satisfies study"


def test_a_journey_for_a_topic_this_programme_did_not_offer_does_not_credit_it():
    """A LearningJourney has no programme link, so the assessor must refuse it."""

    section = _section(
        _Registry({"p": _Contract()}),
        receipts=_Receipts("some-other-card"),
        journeys=_Journeys(_Journey("some-other-card")),
    )
    stages = dict(pair.split("=") for pair in _attrs(section.records[0])["stages"].split(","))

    assert stages["study"] == "todo"
    assert "not among the topics" in section.records[0].detail or stages["study"] == "todo"


def test_only_an_active_journey_counts():
    section = _section(journeys=_Journeys(_Journey("anything", status="abandoned")))
    assert _attrs(section.records[0])["current_stage"] == "study"


def test_a_draft_is_matched_on_the_contract_fingerprint():
    contract = _Contract()
    fingerprint = contract.fingerprint()

    matched = _section(_Registry({"p": contract}), report_drafts=[_Draft(fingerprint)])
    unmatched = _section(_Registry({"p": contract}), report_drafts=[_Draft("sha256:other")])

    def draft_marker(section):
        return dict(pair.split("=") for pair in _attrs(section.records[0])["stages"].split(","))["draft"]

    assert draft_marker(matched) == "ok", "a complete draft under this contract satisfies draft"
    assert draft_marker(unmatched) == "todo", "a draft for another contract must not count"


def test_a_scope_change_invalidates_a_previously_matching_draft():
    """A report cites the contract it was produced under. If scope changes
    substantively, the old draft must stop counting rather than silently carry
    over to a contract it was never written against."""

    before = _Contract()
    draft = _Draft(before.fingerprint())

    after = _Contract()
    after.assets_in_scope.append(_Pattern("newly-added.example.test", "added later"))

    def draft_marker(contract):
        section = _section(_Registry({"p": contract}), report_drafts=[draft])
        return dict(pair.split("=") for pair in _attrs(section.records[0])["stages"].split(","))["draft"]

    assert draft_marker(before) == "ok"
    assert draft_marker(after) == "todo", "a changed contract must not inherit the old draft"


def test_an_incomplete_draft_does_not_satisfy_the_stage():
    contract = _Contract()
    section = _section(
        _Registry({"p": contract}),
        report_drafts=[_Draft(contract.fingerprint(), missing=["summary"])],
    )
    stages = dict(pair.split("=") for pair in _attrs(section.records[0])["stages"].split(","))
    assert stages["draft"] == "todo"


def test_plan_and_evidence_stay_unmet_because_no_honest_source_exists():
    """Not a gap in the panel: nothing records a plan reviewer, and no claim is
    constructed under LOCAL_FIXTURE. Both must report unmet rather than be fed
    a value that makes them look satisfied."""

    stages = dict(pair.split("=") for pair in _attrs(_section().records[0])["stages"].split(","))

    assert stages["plan"] == "todo"
    assert stages["evidence"] == "gov"
    assert stages["submission"] in {"todo", "gov"}


def _attrs(record) -> dict:
    return dict(record.attributes)


# -- the adapter's honesty ---------------------------------------------------

@pytest.mark.parametrize(
    "status", [ContractStatus.DRAFT, ContractStatus.PENDING_REVIEW, ContractStatus.BLOCKED]
)
def test_an_unverified_contract_is_never_reported_as_verified(status):
    """PENDING_REVIEW says in its own docstring that it still blocks execution."""

    section = _section(_Registry({"p": _Contract(status=status)}))
    attrs = _attrs(section.records[0])

    assert attrs["current_stage"] == "programme"
    assert attrs["blocked_by_governance"] == "true"
    assert section.records[0].status is ReadinessStatus.BLOCKED


def test_a_verified_contract_holding_ambiguities_is_not_offered_as_verified():
    section = _section(_Registry({"p": _Contract(ambiguities=["two rules disagree"])}))
    assert _attrs(section.records[0])["current_stage"] == "programme"


def test_a_verified_unambiguous_contract_advances_past_the_programme_stage():
    section = _section()
    attrs = _attrs(section.records[0])

    assert attrs["current_stage"] == "study", "programme and curriculum both satisfied"
    assert attrs["blocked_by_governance"] == "false"
    assert section.records[0].status is ReadinessStatus.ATTENTION


# -- the programme's own ceiling versus the host posture ---------------------

def test_a_programme_capped_at_local_fixture_names_its_own_contract_not_the_posture():
    """Raising the host posture would not help, so it must not be the advice."""

    section = _section(
        _Registry({"p": _Contract(max_authority="LOCAL_FIXTURE")}),
        posture=AuthorityLevel.PASSIVE_HTTP,
        receipts=_Receipts("business-logic-authorization"),
    )
    stages = dict(
        pair.split("=") for pair in _attrs(section.records[0])["stages"].split(",")
    )

    assert stages["evidence"] == "gov"

    # `record.detail` carries the *current* stage (study), not evidence, so the
    # ceiling's reason is checked at its source rather than through the marker.
    from greytheory.campaign import Stage, assess_campaign
    from greytheory_app.campaign_section import _programme_dict

    evidence = assess_campaign(
        _programme_dict("p", _Contract(max_authority="LOCAL_FIXTURE")),
        execution_posture=AuthorityLevel.PASSIVE_HTTP,
    ).state(Stage.EVIDENCE)

    # The remedy must point at the contract, not at a posture change.
    assert "caps authority" in evidence.because
    assert "cannot be probed" in evidence.next_action


def test_an_unparseable_ceiling_is_treated_as_the_lowest_not_the_highest():
    section = _section(
        _Registry({"p": _Contract(max_authority="SUPER_ADMIN")}),
        posture=AuthorityLevel.PASSIVE_HTTP,
    )
    stages = dict(
        pair.split("=") for pair in _attrs(section.records[0])["stages"].split(",")
    )
    assert stages["evidence"] == "gov"


# -- receipts advance study, and only study ---------------------------------

def test_a_practice_receipt_advances_the_study_stage(monkeypatch):
    plain = _section()
    chosen = None
    # Derive a topic this programme's own scope actually selected.
    from greytheory.learning.programme_curriculum import curriculum_for_programme
    from greytheory_app.campaign_section import _programme_dict

    contract = _Contract()
    chosen = curriculum_for_programme(_programme_dict("p", contract)).card_ids[0]

    advanced = _section(_Registry({"p": contract}), receipts=_Receipts(chosen))

    assert _attrs(plain.records[0])["current_stage"] == "study"
    assert _attrs(advanced.records[0])["practised_topics"] == "1"


# -- section shape -----------------------------------------------------------

def test_no_registry_is_unknown_and_no_programmes_is_empty():
    assert build_campaign_section(None, posture=AuthorityLevel.LOCAL_FIXTURE).status is ReadinessStatus.UNKNOWN
    assert _section(_Registry({})).status is ReadinessStatus.EMPTY


def test_the_section_never_implies_authority_or_a_submission():
    attrs = _attrs(_section().records[0])
    assert attrs["grants_authority"] == "false"
    assert attrs["submitted"] == "false"


def test_records_have_unique_ids_and_string_attributes():
    section = _section(_Registry({"a": _Contract(), "b": _Contract()}))
    ids = [r.id for r in section.records]

    assert len(ids) == len(set(ids)) == 2
    for record in section.records:
        for key, value in record.attributes:
            assert isinstance(key, str) and isinstance(value, str)
