"""Invariant I1 — the provenance triple.

Every claim the system holds is exactly one of:

``observed``
    A tool saw this. Verbatim or summarised, but not interpreted.
``checked``
    A deterministic test ran and returned a binary result.
``inferred``
    A model or a human believes this follows from something else.

The rule that makes an LLM safe to use at every step of the system is that an
``inferred`` claim can never be silently upgraded. Promotion to ``checked``
requires a test that *could have failed* — a check that always passes proves
nothing and is rejected here rather than downstream.
"""

# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 ChaseInTech

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Tag(str, Enum):
    """The three permitted provenance tags. There is no fourth."""

    OBSERVED = "observed"
    CHECKED = "checked"
    INFERRED = "inferred"


class ProvenanceError(Exception):
    """Raised when a claim's provenance would become unsound."""


@dataclass(frozen=True)
class Claim:
    """A single statement, permanently bound to how it came to be believed.

    Frozen on purpose: provenance is not editable in place. Promotion returns a
    new claim so the original remains in the record.
    """

    text: str
    tag: Tag
    source: str
    """Tool name, model identifier, or operator — whoever is answerable for it."""

    check_ref: str | None = None
    """Identifier of the deterministic check. Required by, and only by, ``checked``."""

    def __post_init__(self) -> None:
        if not self.text.strip():
            raise ProvenanceError("a claim must say something")
        if not self.source.strip():
            raise ProvenanceError("a claim must name its source")
        if self.tag is Tag.CHECKED and not self.check_ref:
            raise ProvenanceError(
                "a 'checked' claim must reference the check that produced it"
            )
        if self.tag is not Tag.CHECKED and self.check_ref:
            raise ProvenanceError(
                f"a '{self.tag.value}' claim must not carry a check reference; "
                "that would misrepresent it as proven"
            )

    @property
    def is_proven(self) -> bool:
        """Only ``checked`` claims are proven. Observation is not proof."""
        return self.tag is Tag.CHECKED

    def to_dict(self) -> dict:
        return {
            "text": self.text,
            "tag": self.tag.value,
            "source": self.source,
            "check_ref": self.check_ref,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Claim:
        return cls(
            text=data["text"],
            tag=Tag(data["tag"]),
            source=data["source"],
            check_ref=data.get("check_ref"),
        )


def partition(claims: list[Claim]) -> dict[Tag, list[Claim]]:
    """Split claims by tag.

    Reports and evidence packages must present these separately — merging
    observation, proof and inference into one narrative is how severity
    inflation happens.
    """
    result: dict[Tag, list[Claim]] = {tag: [] for tag in Tag}
    for claim in claims:
        result[claim.tag].append(claim)
    return result
