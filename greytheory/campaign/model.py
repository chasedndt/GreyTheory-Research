"""The shape of a bug-bounty campaign: stages, and what blocks each one.

GreyTheory's whole point is to carry one person from *choosing a programme* to
*submitting a defensible report*, teaching the material on the way. Every piece
of that already exists - scope compilation, programme-driven curriculum,
lessons, collectors, experiment planning, report drafting, submission
transport - but nothing said, in one place, **where a campaign actually is and
what is stopping it moving.**

That question was being answered in conversation. It belongs in code, because
the honest answer changes with posture, evidence and approval, and a person
should never have to ask an agent whether they are allowed to proceed.

Two rules make this trustworthy rather than decorative:

* **A stage is satisfied only by evidence that predates the asking.** No stage
  infers its own completion from a later one, and none is satisfied by
  intention.
* **A later stage satisfied before an earlier one is a warning, not progress.**
  Writing a report for evidence you have not gathered is the exact failure this
  product exists to prevent, so the campaign names it rather than showing a
  tidy green line.
"""

# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 ChaseInTech

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Stage(str, Enum):
    """Ordered. Position matters: earlier stages are prerequisites."""

    PROGRAMME = "programme"
    """A compiled programme with reviewed scope."""

    CURRICULUM = "curriculum"
    """Study topics derived from that scope."""

    STUDY = "study"
    """The chosen topic actually practised, with receipts."""

    PLAN = "plan"
    """An experiment plan for the chosen topic, reviewed by a human."""

    EVIDENCE = "evidence"
    """Checked, receipt-backed claims about the programme's own assets."""

    DRAFT = "draft"
    """A report with no missing sections and no placeholders."""

    SUBMISSION = "submission"
    """Every claim submittable, kill switch lifted, operator approval in hand."""


STAGE_ORDER: tuple[Stage, ...] = tuple(Stage)


@dataclass(frozen=True)
class StageState:
    """One stage, and the truthful reason it is or is not satisfied."""

    stage: Stage
    satisfied: bool
    because: str
    """What was observed. Always populated, satisfied or not."""

    next_action: str = ""
    """What would move this stage forward. Empty when satisfied."""

    blocked_by_governance: bool = False
    """True when the blocker is a decision only the operator may make - a
    posture change, a credential, an approval - rather than work to be done.
    Kept separate so 'not finished' is never confused with 'not permitted'."""

    def to_dict(self) -> dict[str, object]:
        return {
            "stage": self.stage.value,
            "satisfied": self.satisfied,
            "because": self.because,
            "next_action": self.next_action,
            "blocked_by_governance": self.blocked_by_governance,
        }


@dataclass(frozen=True)
class Campaign:
    """Where one campaign stands, end to end."""

    programme_id: str
    programme_name: str
    stages: tuple[StageState, ...]

    def state(self, stage: Stage) -> StageState:
        for item in self.stages:
            if item.stage is stage:
                return item
        raise KeyError(stage)

    @property
    def current(self) -> StageState:
        """The first unsatisfied stage - the honest 'you are here'."""
        for item in self.stages:
            if not item.satisfied:
                return item
        return self.stages[-1]

    @property
    def complete(self) -> bool:
        return all(item.satisfied for item in self.stages)

    @property
    def premature(self) -> tuple[Stage, ...]:
        """Stages satisfied while something earlier is not.

        Not a rounding error. A finished draft above missing evidence, or a
        submission above an unreviewed plan, is work that ran ahead of its own
        justification, and it is worth seeing.
        """

        out: list[Stage] = []
        seen_gap = False
        for item in self.stages:
            if not item.satisfied:
                seen_gap = True
            elif seen_gap:
                out.append(item.stage)
        return tuple(out)

    def to_dict(self) -> dict[str, object]:
        return {
            "schema": "greytheory.campaign/1",
            "programme_id": self.programme_id,
            "programme_name": self.programme_name,
            "current_stage": self.current.stage.value,
            "complete": self.complete,
            # Restated so a consumer cannot read progress as permission.
            "submitted": False,
            "premature_stages": [s.value for s in self.premature],
            "stages": [s.to_dict() for s in self.stages],
        }
