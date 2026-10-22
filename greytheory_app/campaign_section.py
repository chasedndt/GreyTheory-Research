"""Read-model section: where each compiled programme's campaign stands.

Kept out of `service.py` for the same reason the curriculum section is - the
mapping from stored state to "you are here" should be reviewable on its own.

The adapter below is the part worth reading. A ``ScopeContract`` always carries
a ``verified_at`` datetime, so treating that field as proof of verification
would report a DRAFT contract as verified. The trust signal is ``status``, and
``PENDING_REVIEW`` says in its own docstring that it still blocks execution. A
contract also carries ``ambiguities`` - the reasons it cannot be trusted - so a
contract holding any is not offered as verified either.

Nothing here grants authority, and a practice receipt is practice: the receipt
record itself sets ``credits_mastery`` and ``proves_real_vulnerability`` to
false, and this section never reads a receipt as evidence about a programme.
"""

# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 ChaseInTech

from __future__ import annotations

from greytheory.authority.gate import AuthorityLevel
from greytheory.authority.scope import ContractStatus
from greytheory.campaign import assess_campaign
from greytheory_app.contracts import (
    ReadinessStatus,
    WorkbenchMetric,
    WorkbenchRecord,
    WorkbenchSection,
)

SECTION_ID = "campaign"
SECTION_TITLE = "Campaign"

#: Compact per-stage markers, so one record shows the whole journey.
_OK, _GOV, _TODO = "ok", "gov", "todo"


def _programme_dict(programme_id: str, contract) -> dict:
    """Adapt a compiled contract to the assessor's input, honestly."""

    status = getattr(contract, "status", None)
    ambiguities = list(getattr(contract, "ambiguities", ()) or ())
    trusted = status is ContractStatus.VERIFIED and not ambiguities

    rows = []
    for pattern in getattr(contract, "assets_in_scope", ()) or ():
        rows.append(
            {
                "type": getattr(pattern, "type", ""),
                "value": getattr(pattern, "value", ""),
                "note": getattr(pattern, "note", "") or "",
            }
        )

    verified_at = getattr(contract, "verified_at", None)
    return {
        "id": programme_id,
        "name": programme_id,
        "in_scope": rows,
        "prohibited_techniques": list(getattr(contract, "prohibited_techniques", ()) or ()),
        # Supplied only when the contract is actually trusted. A datetime that
        # exists regardless is not evidence that anyone reviewed it.
        "verified_at": verified_at.isoformat() if (trusted and verified_at) else "",
        "max_authority": str(getattr(contract, "max_authority", "") or ""),
    }


def _marker(state) -> str:
    if state.satisfied:
        return _OK
    return _GOV if state.blocked_by_governance else _TODO


def _status_for(campaign) -> ReadinessStatus:
    if campaign.complete:
        return ReadinessStatus.READY
    return (
        ReadinessStatus.BLOCKED
        if campaign.current.blocked_by_governance
        else ReadinessStatus.ATTENTION
    )


def _active_card_id(journeys) -> str | None:
    """The topic currently being worked, if any.

    A `LearningJourney` carries no programme link, so this is deliberately not
    attributed here. `_study_stage` already refuses a topic that the
    programme's own scope did not select, so passing the card straight through
    cannot credit one bounty with study done for another.
    """

    if journeys is None:
        return None
    try:
        active = [j for j in journeys.journeys() if getattr(j, "status", None) and
                  str(getattr(j.status, "value", j.status)) == "active"]
    except Exception:
        return None
    if not active:
        return None
    # Ordering must not mix types: a missing `updated_at` cannot fall back to 0
    # and then be compared against a datetime, which raises. Journeys without a
    # timestamp simply do not win the comparison.
    stamped = [j for j in active if getattr(j, "updated_at", None) is not None]
    newest = max(stamped, key=lambda j: j.updated_at) if stamped else active[0]
    return getattr(newest, "card_id", None)


def _draft_for(contract, report_store, report_drafts):
    """The draft produced under *this* contract, or None.

    Matched on `authority_ref` against the contract fingerprint. A draft
    written against an earlier compile will not match, and that is correct: a
    report cites the contract it was produced under, so a substantive scope
    change should not silently inherit an older draft. Do not loosen this to a
    programme-name match - `ReportDraft.programme` is never populated, so such
    a join would match nothing while appearing to work.
    """

    fingerprint = ""
    try:
        fingerprint = contract.fingerprint()
    except Exception:
        return None
    if not fingerprint:
        return None

    drafts = []
    if report_drafts:
        drafts = list(report_drafts)
    elif report_store is not None:
        try:
            drafts = [case.draft for case in report_store.cases()]
        except Exception:
            return None
    for draft in drafts:
        if getattr(draft, "authority_ref", "") == fingerprint:
            return draft
    return None


def build_campaign_section(
    registry,
    *,
    posture: AuthorityLevel,
    fixture_receipts=None,
    journeys=None,
    report_store=None,
    report_drafts=None,
) -> WorkbenchSection:
    """One record per compiled programme, naming its stage and its blocker."""

    if registry is None:
        return WorkbenchSection(
            SECTION_ID,
            SECTION_TITLE,
            ReadinessStatus.UNKNOWN,
            metrics=(
                WorkbenchMetric(
                    "Programmes", "unknown", ReadinessStatus.UNKNOWN,
                    "no programme registry configured",
                ),
            ),
            note="A campaign is measured against a compiled programme; none is available.",
        )

    programme_ids = list(registry.programmes())
    if not programme_ids:
        return WorkbenchSection(
            SECTION_ID,
            SECTION_TITLE,
            ReadinessStatus.EMPTY,
            metrics=(WorkbenchMetric("Programmes", "0", ReadinessStatus.EMPTY),),
            note="Compile a programme to begin a campaign.",
        )

    practised = frozenset(
        receipt.card_id
        for receipt in (fixture_receipts.receipts() if fixture_receipts is not None else ())
    )
    chosen_card_id = _active_card_id(journeys)

    records: list[WorkbenchRecord] = []
    governance_blocked = 0
    for programme_id in programme_ids:
        contract = registry.current_contract(programme_id)
        if contract is None:
            continue
        campaign = assess_campaign(
            _programme_dict(programme_id, contract),
            execution_posture=posture,
            chosen_card_id=chosen_card_id,
            practised_cards=practised,
            # Deliberately not supplied, because no honest source exists yet:
            #
            # * `plan_reviewed_by` - `ExperimentPlan` records a status but never
            #   who reviewed it. Deriving a name from `status is READY` would
            #   assert a person acted when nothing recorded that they did.
            # * `claims` - nothing in this service constructs a SubmissionClaim,
            #   and correctly so: a claim describes evidence gathered against a
            #   real target, which LOCAL_FIXTURE forbids.
            #
            # Both stages therefore report honestly as unmet rather than being
            # fed a value that would make them look satisfied.
            draft=_draft_for(contract, report_store, report_drafts),
        )
        current = campaign.current
        if current.blocked_by_governance:
            governance_blocked += 1

        records.append(
            WorkbenchRecord(
                id=f"campaign:{programme_id}",
                title=programme_id,
                status=_status_for(campaign),
                subtitle=f"stage: {current.stage.value}",
                # The reason, not just the position. A stage name without its
                # cause is a progress bar, and a progress bar cannot say
                # "waiting on you" as distinct from "unfinished".
                detail=current.because,
                attributes=(
                    ("current_stage", current.stage.value),
                    ("next_action", current.next_action),
                    ("blocked_by_governance", "true" if current.blocked_by_governance else "false"),
                    ("stages", ",".join(f"{s.stage.value}={_marker(s)}" for s in campaign.stages)),
                    ("premature_stages", ",".join(s.value for s in campaign.premature)),
                    ("practised_topics", str(len(practised))),
                    ("posture", posture.name),
                    ("grants_authority", "false"),
                    ("submitted", "false"),
                ),
            )
        )

    return WorkbenchSection(
        SECTION_ID,
        SECTION_TITLE,
        ReadinessStatus.READY if records else ReadinessStatus.EMPTY,
        metrics=(
            WorkbenchMetric("Programmes", str(len(programme_ids)), ReadinessStatus.READY),
            WorkbenchMetric(
                "Awaiting a decision",
                str(governance_blocked),
                ReadinessStatus.BLOCKED if governance_blocked else ReadinessStatus.READY,
                "stages waiting on an operator decision rather than on work",
            ),
        ),
        records=tuple(records),
        note=(
            "Stages report what was observed and what would move them forward. "
            "A stage marked gov is waiting on an operator decision, not on work."
        ),
    )
