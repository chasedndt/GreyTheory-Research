"""Versioned learner-to-research case-pack contracts.

Case packs compose existing vulnerability cards, fixtures, evidence expectations,
and transfer work into one teachable unit.  They describe future live-programme
inputs, but cannot enable a network posture or create testing authority.
"""

# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 ChaseInTech

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping

from greytheory.learning.catalogue import VulnerabilityCatalogue
from greytheory.learning.domain import LearningError, SAFE_ID


CASE_PACK_SCHEMA_VERSION = 1
ALLOWED_STATES = frozenset({"ready_local", "queued"})
ALLOWED_TRACKS = frozenset({"guided", "assisted", "transfer"})
REQUIRED_LIVE_FIELDS = frozenset(
    {
        "programme_id",
        "source_bundle_digest",
        "scope_contract_fingerprint",
        "max_authority",
        "rate_limit",
        "data_policy",
        "disclosure_policy",
    }
)


def _required(value: Any, label: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise LearningError(f"{label} is required")
    return text


def _safe_id(value: Any, label: str) -> str:
    text = _required(value, label)
    if not SAFE_ID.fullmatch(text):
        raise LearningError(f"{label} {text!r} is not a safe identifier")
    return text


def _texts(value: Any, label: str) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        raise LearningError(f"{label} must be a list")
    items = tuple(_required(item, label) for item in value)
    if not items or len(items) != len(set(items)):
        raise LearningError(f"{label} must contain unique non-empty values")
    return items


@dataclass(frozen=True)
class LiveProgrammeAdapter:
    """A deliberately dark compatibility description, never an activation switch."""

    state: str
    enabled: bool
    required_authority_fields: tuple[str, ...]
    activation_gates: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.state != "dark" or self.enabled:
            raise LearningError("case-pack live-programme adapters must remain dark")
        if set(self.required_authority_fields) != REQUIRED_LIVE_FIELDS:
            raise LearningError(
                "case-pack live compatibility must require the complete authority field set"
            )
        if len(self.activation_gates) < 4:
            raise LearningError("live compatibility requires explicit acceptance gates")

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> LiveProgrammeAdapter:
        return cls(
            state=_required(data.get("state"), "live adapter state"),
            enabled=data.get("enabled") is True,
            required_authority_fields=_texts(
                data.get("required_authority_fields"), "required authority fields"
            ),
            activation_gates=_texts(data.get("activation_gates"), "activation gates"),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "state": self.state,
            "enabled": False,
            "required_authority_fields": list(self.required_authority_fields),
            "activation_gates": list(self.activation_gates),
        }


@dataclass(frozen=True)
class LearningCasePack:
    schema_version: int
    id: str
    version: str
    title: str
    summary: str
    state: str
    estimated_minutes: int
    primary_card_id: str
    card_ids: tuple[str, ...]
    fixture_id: str
    objectives: tuple[str, ...]
    traditional_lens: str
    ai_lens: str
    tracks: tuple[str, ...]
    live_programme_adapter: LiveProgrammeAdapter
    current_posture: str = "LOCAL_FIXTURE"
    awards_mastery: bool = False
    proves_real_vulnerability: bool = False

    def __post_init__(self) -> None:
        if self.schema_version != CASE_PACK_SCHEMA_VERSION:
            raise LearningError("unsupported case-pack schema")
        _safe_id(self.id, "case-pack id")
        _required(self.version, "case-pack version")
        _required(self.title, "case-pack title")
        _required(self.summary, "case-pack summary")
        _safe_id(self.primary_card_id, "primary card id")
        _safe_id(self.fixture_id, "fixture id")
        if self.state not in ALLOWED_STATES:
            raise LearningError(f"unsupported case-pack state {self.state!r}")
        if (
            isinstance(self.estimated_minutes, bool)
            or not isinstance(self.estimated_minutes, int)
            or not 10 <= self.estimated_minutes <= 240
        ):
            raise LearningError("case-pack duration must be between 10 and 240 minutes")
        if self.primary_card_id not in self.card_ids:
            raise LearningError("primary card must be included in the case pack")
        if set(self.tracks) != ALLOWED_TRACKS:
            raise LearningError("case packs must support guided, assisted, and transfer tracks")
        if self.current_posture != "LOCAL_FIXTURE":
            raise LearningError("case packs cannot raise the current operating posture")
        if self.awards_mastery or self.proves_real_vulnerability:
            raise LearningError("case packs award no mastery and prove no real vulnerability")

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> LearningCasePack:
        card_ids = tuple(_safe_id(item, "case-pack card id") for item in _texts(data.get("card_ids"), "case-pack card ids"))
        return cls(
            schema_version=int(data.get("schema_version", 0)),
            id=_safe_id(data.get("id"), "case-pack id"),
            version=_required(data.get("version"), "case-pack version"),
            title=_required(data.get("title"), "case-pack title"),
            summary=_required(data.get("summary"), "case-pack summary"),
            state=_required(data.get("state"), "case-pack state"),
            estimated_minutes=data.get("estimated_minutes"),
            primary_card_id=_safe_id(data.get("primary_card_id"), "primary card id"),
            card_ids=card_ids,
            fixture_id=_safe_id(data.get("fixture_id"), "fixture id"),
            objectives=_texts(data.get("objectives"), "case-pack objectives"),
            traditional_lens=_required(data.get("traditional_lens"), "traditional lens"),
            ai_lens=_required(data.get("ai_lens"), "AI lens"),
            tracks=_texts(data.get("tracks"), "case-pack tracks"),
            live_programme_adapter=LiveProgrammeAdapter.from_dict(
                data.get("live_programme_adapter", {})
            ),
            current_posture=_required(
                data.get("current_posture", "LOCAL_FIXTURE"), "current posture"
            ),
            awards_mastery=data.get("awards_mastery") is True,
            proves_real_vulnerability=data.get("proves_real_vulnerability") is True,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "id": self.id,
            "version": self.version,
            "title": self.title,
            "summary": self.summary,
            "state": self.state,
            "estimated_minutes": self.estimated_minutes,
            "primary_card_id": self.primary_card_id,
            "card_ids": list(self.card_ids),
            "fixture_id": self.fixture_id,
            "objectives": list(self.objectives),
            "traditional_lens": self.traditional_lens,
            "ai_lens": self.ai_lens,
            "tracks": list(self.tracks),
            "live_programme_adapter": self.live_programme_adapter.to_dict(),
            "current_posture": "LOCAL_FIXTURE",
            "awards_mastery": False,
            "proves_real_vulnerability": False,
        }


class CasePackRegistry:
    def __init__(
        self,
        packs: Iterable[LearningCasePack],
        *,
        catalogue: VulnerabilityCatalogue,
    ) -> None:
        by_id: dict[str, LearningCasePack] = {}
        for pack in packs:
            if pack.id in by_id:
                raise LearningError(f"duplicate case pack {pack.id!r}")
            for card_id in pack.card_ids:
                catalogue.card(card_id)
            fixture = catalogue.fixture(pack.primary_card_id)
            if pack.fixture_id != fixture.id:
                raise LearningError(
                    f"case pack {pack.id!r} does not bind its primary card fixture"
                )
            by_id[pack.id] = pack
        if not by_id:
            raise LearningError("a case-pack registry cannot be empty")
        self._packs = by_id

    @classmethod
    def load(
        cls, data_root: Path, *, catalogue: VulnerabilityCatalogue
    ) -> CasePackRegistry:
        packs: list[LearningCasePack] = []
        for path in sorted(data_root.glob("*.json")):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                raise LearningError(f"cannot load case pack {path}: {exc}") from exc
            if not isinstance(data, dict):
                raise LearningError(f"case pack {path} must be an object")
            packs.append(LearningCasePack.from_dict(data))
        return cls(packs, catalogue=catalogue)

    @property
    def pack_ids(self) -> tuple[str, ...]:
        return tuple(sorted(self._packs))

    def pack(self, pack_id: str) -> LearningCasePack:
        try:
            return self._packs[pack_id]
        except KeyError as exc:
            raise LearningError(f"unknown case pack {pack_id!r}") from exc

    def packs(self) -> tuple[LearningCasePack, ...]:
        return tuple(self._packs[item] for item in self.pack_ids)

    def digest(self) -> str:
        payload = [pack.to_dict() for pack in self.packs()]
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def load_builtin_case_packs(
    catalogue: VulnerabilityCatalogue,
) -> CasePackRegistry:
    return CasePackRegistry.load(
        Path(__file__).with_name("data") / "casepacks", catalogue=catalogue
    )


__all__ = [
    "CASE_PACK_SCHEMA_VERSION",
    "CasePackRegistry",
    "LearningCasePack",
    "LiveProgrammeAdapter",
    "load_builtin_case_packs",
]
