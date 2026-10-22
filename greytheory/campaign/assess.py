"""Assess a campaign from evidence that already exists.

Everything here is supplied by the caller and read, never gathered. The
assessor opens no connection, consults no clock for authority, and invents no
state: if a stage's evidence was not passed in, the stage is not satisfied and
says so.

The posture rule is the one worth understanding. Checked evidence *about a
programme's own assets* cannot exist at ``LOCAL_FIXTURE``, because at that
posture nothing may touch them. So the evidence stage is blocked by governance,
not by effort, and the campaign says exactly that rather than implying the
learner is behind.
"""

# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 ChaseInTech

from __future__ import annotations

from greytheory.authority.gate import AuthorityLevel
from greytheory.campaign.model import STAGE_ORDER, Campaign, Stage, StageState
from greytheory.learning.programme_curriculum import curriculum_for_programme
from greytheory.report import ReportDraft
from greytheory_intelligence.submission import SubmissionClaim

#: Touching a programme's own assets starts here. Below it, checked evidence
#: about those assets cannot honestly exist.
LIVE_EVIDENCE_REQUIRES = AuthorityLevel.PASSIVE_HTTP


def _programme_stage(programme: dict) -> StageState:
    name = str(programme.get("name") or "").strip()
    in_scope = list(programme.get("in_scope") or ())
    verified_at = str(programme.get("verified_at") or "").strip()

    if not name or not in_scope:
        return StageState(
            Stage.PROGRAMME, False,
            because="no compiled programme with in-scope assets was supplied",
            next_action="compile a programme from its published policy and review the scope",
        )
    if not verified_at:
        return StageState(
            Stage.PROGRAMME, False,
            because=f"{name} has {len(in_scope)} in-scope assets but no human verification",
            next_action="review the compiled scope and record who verified it",
            blocked_by_governance=True,
        )
    return StageState(
        Stage.PROGRAMME, True,
        because=f"{name}: {len(in_scope)} in-scope assets, verified {verified_at}",
    )


def _curriculum_stage(programme: dict) -> tuple[StageState, tuple[str, ...]]:
    try:
        curriculum = curriculum_for_programme(programme)
    except Exception as exc:  # a malformed record is a fact, not a crash
        return StageState(
            Stage.CURRICULUM, False,
            because=f"scope could not be read into study topics: {exc}",
            next_action="fix the compiled programme record",
        ), ()

    if not curriculum.topics:
        return StageState(
            Stage.CURRICULUM, False,
            because="no study topic matched this programme's scope",
            next_action="add a surface rule covering this programme's assets",
        ), ()

    ranked = ", ".join(t.card_id for t in curriculum.topics[:3])
    return StageState(
        Stage.CURRICULUM, True,
        because=f"{len(curriculum.topics)} topics selected from scope; top: {ranked}",
    ), curriculum.card_ids


def _study_stage(chosen: str | None, offered: tuple[str, ...], practised: frozenset[str]) -> StageState:
    if not chosen:
        return StageState(
            Stage.STUDY, False,
            because=f"no topic chosen from the {len(offered)} this programme selected",
            next_action="choose a topic to work, then practise it",
        )
    if chosen not in offered:
        return StageState(
            Stage.STUDY, False,
            because=f"{chosen} is not among the topics this programme's scope selected",
            next_action=f"choose one of: {', '.join(offered[:5])}",
        )
    if chosen not in practised:
        return StageState(
            Stage.STUDY, False,
            because=f"{chosen} has no practice receipt",
            next_action=f"run the {chosen} synthetic lab end to end",
        )
    return StageState(Stage.STUDY, True, because=f"{chosen} practised, with a receipt")


def _plan_stage(chosen: str | None, reviewed_by: str) -> StageState:
    if not chosen:
        return StageState(
            Stage.PLAN, False,
            because="no topic chosen, so there is nothing to plan",
            next_action="choose a topic first",
        )
    if not reviewed_by.strip():
        return StageState(
            Stage.PLAN, False,
            because=f"no reviewed experiment plan for {chosen}",
            next_action="build the role-object-action matrix and have a human review every family",
            blocked_by_governance=True,
        )
    return StageState(Stage.PLAN, True, because=f"experiment plan for {chosen} reviewed by {reviewed_by}")


def _programme_ceiling(programme: dict) -> AuthorityLevel:
    """The programme's own cap, read from its contract. Unknown means lowest.

    A ceiling that cannot be parsed must never read as permissive: an
    unrecognised value is a reason to stop, not licence to continue.
    """

    raw = str(programme.get("max_authority") or "").strip()
    if not raw:
        return AuthorityLevel.LOCAL_FIXTURE
    try:
        return AuthorityLevel.parse(raw)
    except Exception:
        return AuthorityLevel.LOCAL_FIXTURE


def _evidence_stage(
    posture: AuthorityLevel,
    claims: tuple[SubmissionClaim, ...],
    ceiling: AuthorityLevel = AuthorityLevel.INTRUSIVE,
) -> StageState:
    checked = [c for c in claims if c.is_submittable()]
    # The programme's own ceiling is checked first, because raising the host
    # posture would not help: these are different permissions with different
    # remedies, and telling someone to raise posture here would send them to
    # the wrong decision entirely.
    if ceiling < LIVE_EVIDENCE_REQUIRES:
        return StageState(
            Stage.EVIDENCE, False,
            because=(
                f"this programme's compiled contract caps authority at {ceiling.name}; "
                f"it does not permit the {LIVE_EVIDENCE_REQUIRES.name} activity evidence needs"
            ),
            next_action=(
                "re-compile the contract from the programme's published policy if it "
                "genuinely allows more; otherwise this programme cannot be probed"
            ),
            blocked_by_governance=True,
        )
    if posture < LIVE_EVIDENCE_REQUIRES:
        return StageState(
            Stage.EVIDENCE, False,
            because=(
                f"execution posture is {posture.name}; checked evidence about this "
                f"programme's assets cannot exist below {LIVE_EVIDENCE_REQUIRES.name}"
            ),
            next_action=(
                "accept the isolated worker VM, then raise execution posture to "
                f"{LIVE_EVIDENCE_REQUIRES.name} - both are operator decisions"
            ),
            blocked_by_governance=True,
        )
    if not checked:
        return StageState(
            Stage.EVIDENCE, False,
            because=f"{len(claims)} claims held, none checked and receipt-backed",
            next_action="run the reviewed experiment and capture receipts",
        )
    return StageState(
        Stage.EVIDENCE, True,
        because=f"{len(checked)} of {len(claims)} claims are checked and receipt-backed",
    )


def _draft_stage(draft: ReportDraft | None) -> StageState:
    if draft is None:
        return StageState(
            Stage.DRAFT, False,
            because="no report draft exists",
            next_action="open a report case and draft from the captured evidence",
        )
    missing = draft.missing_sections()
    placeholders = draft.placeholders()
    if missing or placeholders:
        parts = []
        if missing:
            parts.append(f"missing {', '.join(missing)}")
        if placeholders:
            parts.append(f"placeholders in {', '.join(placeholders)}")
        return StageState(
            Stage.DRAFT, False,
            because="; ".join(parts),
            next_action="complete every required section and remove unfinished markers",
        )
    absolutes = draft.absolute_claims()
    note = f" (unqualified absolutes to review: {', '.join(absolutes)})" if absolutes else ""
    return StageState(Stage.DRAFT, True, because=f"all required sections present{note}")


def _submission_stage(
    claims: tuple[SubmissionClaim, ...], enabled: bool, approved_by: str
) -> StageState:
    unsubmittable = [c for c in claims if not c.is_submittable()]
    if not claims:
        return StageState(
            Stage.SUBMISSION, False,
            because="no claims to submit",
            next_action="gather checked evidence first",
        )
    if unsubmittable:
        return StageState(
            Stage.SUBMISSION, False,
            because=f"{len(unsubmittable)} of {len(claims)} claims are not checked and receipt-backed",
            next_action="every claim in an outbound report must be checked; drop or prove the rest",
        )
    if not enabled:
        return StageState(
            Stage.SUBMISSION, False,
            because="the submission kill switch is engaged",
            next_action="lift the kill switch - an operator decision, per submission",
            blocked_by_governance=True,
        )
    if not approved_by.strip():
        return StageState(
            Stage.SUBMISSION, False,
            because="no operator approval bound to this payload",
            next_action="review the exact payload and approve it; editing it invalidates the approval",
            blocked_by_governance=True,
        )
    return StageState(
        Stage.SUBMISSION, True,
        because=f"{len(claims)} checked claims, approved by {approved_by}",
    )


def assess_campaign(
    programme: dict,
    *,
    execution_posture: AuthorityLevel,
    chosen_card_id: str | None = None,
    practised_cards: frozenset[str] = frozenset(),
    plan_reviewed_by: str = "",
    claims: tuple[SubmissionClaim, ...] = (),
    draft: ReportDraft | None = None,
    submission_enabled: bool = False,
    submission_approved_by: str = "",
) -> Campaign:
    """Read the supplied evidence and say where this campaign stands."""

    curriculum_state, offered = _curriculum_stage(programme)
    states = {
        Stage.PROGRAMME: _programme_stage(programme),
        Stage.CURRICULUM: curriculum_state,
        Stage.STUDY: _study_stage(chosen_card_id, offered, practised_cards),
        Stage.PLAN: _plan_stage(chosen_card_id, plan_reviewed_by),
        Stage.EVIDENCE: _evidence_stage(
            execution_posture, claims, _programme_ceiling(programme)
        ),
        Stage.DRAFT: _draft_stage(draft),
        Stage.SUBMISSION: _submission_stage(claims, submission_enabled, submission_approved_by),
    }
    return Campaign(
        programme_id=str(programme.get("id") or ""),
        programme_name=str(programme.get("name") or ""),
        stages=tuple(states[stage] for stage in STAGE_ORDER),
    )
