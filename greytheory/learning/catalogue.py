"""Load and validate the built-in vulnerability-card catalogue and skill graph."""

# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 ChaseInTech

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable, Iterable

from greytheory.learning.domain import (
    CardRevision,
    CardUpdateProposal,
    LearningError,
    MasteryAssessment,
    MasteryDimension,
    MasteryLevel,
    MasteryState,
    VulnerabilityCard,
)
from greytheory.learning.fixtures import (
    FixtureRunReceipt,
    LocalTrainingFixture,
    TrainingFixtureRunner,
)


MILESTONE5_CARD_IDS = frozenset(
    {
        "reflected-xss",
        "stored-xss",
        "dom-xss",
        "sql-injection",
        "csrf",
        "ssrf",
        "idor-bola",
        "bfla",
        "session-management",
        "business-logic-authorization",
        "indirect-prompt-injection",
        "tool-authorization-failure",
    }
)


@dataclass(frozen=True)
class CatalogueEntry:
    card: VulnerabilityCard
    fixture: LocalTrainingFixture

    def to_dict(self) -> dict:
        return {"card": self.card.to_dict(), "fixture": self.fixture.to_dict()}


class VulnerabilityCatalogue:
    """An immutable, integrity-checkable set of cards and their local labs."""

    def __init__(self, entries: Iterable[CatalogueEntry]) -> None:
        by_id: dict[str, CatalogueEntry] = {}
        fixture_ids: set[str] = set()
        for entry in entries:
            card = entry.card
            fixture = entry.fixture
            if card.id in by_id:
                raise LearningError(f"duplicate vulnerability card {card.id!r}")
            if fixture.id in fixture_ids:
                raise LearningError(f"duplicate local fixture {fixture.id!r}")
            if fixture.card_id != card.id:
                raise LearningError(
                    f"fixture {fixture.id!r} belongs to {fixture.card_id!r}, not {card.id!r}"
                )
            if card.local_fixture.id != fixture.id:
                raise LearningError(
                    f"card {card.id!r} references fixture {card.local_fixture.id!r}, not {fixture.id!r}"
                )
            by_id[card.id] = entry
            fixture_ids.add(fixture.id)
        if not by_id:
            raise LearningError("a vulnerability catalogue cannot be empty")
        self._entries = by_id
        self.graph = SkillGraph(tuple(entry.card for entry in by_id.values()))

    @classmethod
    def load(cls, data_root: Path) -> VulnerabilityCatalogue:
        cards_root = data_root / "cards"
        entries: list[CatalogueEntry] = []
        for card_path in sorted(cards_root.glob("*.json")):
            try:
                card_data = json.loads(card_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                raise LearningError(f"cannot load vulnerability card {card_path}: {exc}") from exc
            if not isinstance(card_data, dict):
                raise LearningError(f"vulnerability card {card_path} must be an object")
            card = VulnerabilityCard.from_dict(card_data)
            fixture_path = data_root / card.local_fixture.relative_path
            try:
                fixture_path.relative_to(data_root)
            except ValueError as exc:
                raise LearningError("fixture path escaped the catalogue data root") from exc
            entries.append(
                CatalogueEntry(card=card, fixture=LocalTrainingFixture.load(fixture_path))
            )
        return cls(entries)

    @property
    def card_ids(self) -> tuple[str, ...]:
        return tuple(sorted(self._entries))

    def card(self, card_id: str) -> VulnerabilityCard:
        try:
            return self._entries[card_id].card
        except KeyError as exc:
            raise LearningError(f"unknown vulnerability card {card_id!r}") from exc

    def fixture(self, card_id: str) -> LocalTrainingFixture:
        try:
            return self._entries[card_id].fixture
        except KeyError as exc:
            raise LearningError(f"unknown vulnerability card {card_id!r}") from exc

    def run_fixture(
        self,
        card_id: str,
        *,
        clock: Callable[[], datetime] | None = None,
    ) -> FixtureRunReceipt:
        return TrainingFixtureRunner(clock=clock).run(self.fixture(card_id))

    def run_all_fixtures(
        self, *, clock: Callable[[], datetime] | None = None
    ) -> tuple[FixtureRunReceipt, ...]:
        return tuple(self.run_fixture(card_id, clock=clock) for card_id in self.card_ids)

    def applied_revision(self, proposal: CardUpdateProposal) -> CardRevision:
        """Prove that a proposal is acknowledged by explicit revision provenance."""

        card = self.card(proposal.card_id)
        proposal_ref = f"milestone4:{proposal.id}"
        matches = [
            revision
            for revision in card.revisions
            if proposal_ref in revision.source_refs
        ]
        if len(matches) != 1:
            raise LearningError(
                f"proposal {proposal.id!r} is not applied by exactly one card revision"
            )
        revision = matches[0]
        if revision.source_kind != proposal.source_kind:
            raise LearningError("proposal and applied revision source kinds do not match")
        return revision

    def to_dict(self) -> dict:
        return {
            "schema_version": 1,
            "cards": [self._entries[item].to_dict() for item in self.card_ids],
            "skill_graph": self.graph.to_dict(),
        }

    def digest(self) -> str:
        encoded = json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


class SkillGraph:
    """Acyclic card prerequisites plus six independent mastery dimensions."""

    def __init__(self, cards: Iterable[VulnerabilityCard]) -> None:
        self._cards = {card.id: card for card in cards}
        for card in self._cards.values():
            missing = set(card.prerequisite_card_ids) - set(self._cards)
            if missing:
                raise LearningError(
                    f"card {card.id!r} has unknown prerequisites {sorted(missing)!r}"
                )
        self._order = self._topological_order()

    @property
    def order(self) -> tuple[str, ...]:
        return self._order

    def prerequisites(self, card_id: str) -> tuple[str, ...]:
        try:
            return self._cards[card_id].prerequisite_card_ids
        except KeyError as exc:
            raise LearningError(f"unknown vulnerability card {card_id!r}") from exc

    def mastery_states(
        self,
        assessments: Iterable[MasteryAssessment],
        *,
        include_non_crediting: bool = False,
    ) -> tuple[MasteryState, ...]:
        latest: dict[tuple[str, MasteryDimension], MasteryAssessment] = {}
        for assessment in assessments:
            if assessment.card_id not in self._cards:
                raise LearningError(
                    f"mastery assessment references unknown card {assessment.card_id!r}"
                )
            if not assessment.credits_mastery and not include_non_crediting:
                continue
            key = (assessment.card_id, assessment.dimension)
            previous = latest.get(key)
            if previous is None or (assessment.assessed_at, assessment.id) > (
                previous.assessed_at,
                previous.id,
            ):
                latest[key] = assessment
        states: list[MasteryState] = []
        for card_id in self._order:
            for dimension in MasteryDimension:
                assessment = latest.get((card_id, dimension))
                states.append(
                    MasteryState(
                        card_id=card_id,
                        dimension=dimension,
                        level=(
                            assessment.level
                            if assessment is not None
                            else MasteryLevel.NOT_ASSESSED
                        ),
                        assessment_id=assessment.id if assessment else None,
                        review_due=assessment.review_due if assessment else None,
                    )
                )
        return tuple(states)

    def prerequisite_gaps(
        self, card_id: str, assessments: Iterable[MasteryAssessment]
    ) -> tuple[str, ...]:
        """Return card prerequisites without human independent test evidence."""

        states = {
            (item.card_id, item.dimension): item
            for item in self.mastery_states(assessments)
        }
        return tuple(
            prerequisite
            for prerequisite in self.prerequisites(card_id)
            if states[(prerequisite, MasteryDimension.TEST)].level
            < MasteryLevel.INDEPENDENT
        )

    def to_dict(self) -> dict:
        return {
            "nodes": list(self._order),
            "edges": [
                {"prerequisite": prerequisite, "card": card.id}
                for card in sorted(self._cards.values(), key=lambda item: item.id)
                for prerequisite in card.prerequisite_card_ids
            ],
            "mastery_dimensions": [item.value for item in MasteryDimension],
            "mastery_credit_rule": "human evidence-bound assessment only",
        }

    def _topological_order(self) -> tuple[str, ...]:
        temporary: set[str] = set()
        permanent: set[str] = set()
        ordered: list[str] = []

        def visit(card_id: str) -> None:
            if card_id in permanent:
                return
            if card_id in temporary:
                raise LearningError("vulnerability-card prerequisites contain a cycle")
            temporary.add(card_id)
            for prerequisite in self._cards[card_id].prerequisite_card_ids:
                visit(prerequisite)
            temporary.remove(card_id)
            permanent.add(card_id)
            ordered.append(card_id)

        for card_id in sorted(self._cards):
            visit(card_id)
        return tuple(ordered)


def load_builtin_catalogue() -> VulnerabilityCatalogue:
    catalogue = VulnerabilityCatalogue.load(Path(__file__).with_name("data"))
    actual = set(catalogue.card_ids)
    if actual != MILESTONE5_CARD_IDS:
        raise LearningError(
            "built-in catalogue must contain exactly the 12 Milestone 5 cards; "
            f"missing={sorted(MILESTONE5_CARD_IDS - actual)!r} "
            f"extra={sorted(actual - MILESTONE5_CARD_IDS)!r}"
        )
    return catalogue


__all__ = [
    "CatalogueEntry",
    "MILESTONE5_CARD_IDS",
    "SkillGraph",
    "VulnerabilityCatalogue",
    "load_builtin_catalogue",
]
