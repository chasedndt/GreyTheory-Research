"""Compile programme source material into a ScopeContract.

The compiler's job is not to be clever. It is to be *suspicious*: it reads a
programme record, records a hash of the source it read, and refuses to produce
a usable contract when anything is missing, contradictory or unparseable.

A clean compile does not produce a verified contract. It produces
``PENDING_REVIEW`` — a human must look at it before it grants anything. That is
the human gate expressed as code rather than as a paragraph in a policy file.
"""

# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 ChaseInTech

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from greytheory.authority.scope import (
    AssetPattern,
    ContractStatus,
    PatternError,
    PatternType,
    ScopeContract,
)

AUTHORITY_NAMES = {
    "NONE",
    "LOCAL_FIXTURE",
    "PASSIVE_HTTP",
    "AUTHENTICATED",
    "INTRUSIVE",
}

AMBIGUITY_MARKERS = ("tbd", "tbc", "unclear", "ask", "unknown", "?", "see email")
"""Substrings that indicate a human never finished reading the programme."""


@dataclass
class CompilationResult:
    contract: ScopeContract
    ambiguities: list[str] = field(default_factory=list)

    @property
    def blocked(self) -> bool:
        return self.contract.status is ContractStatus.BLOCKED


def source_hash(raw: str) -> str:
    """Hash of the exact source text a contract was compiled from.

    Lets a later re-read of the programme page prove whether the rules changed,
    without needing to store the page itself.
    """
    return "sha256:" + hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _parse_patterns(
    entries: list[dict[str, Any]], *, label: str, ambiguities: list[str]
) -> list[AssetPattern]:
    patterns: list[AssetPattern] = []
    for index, entry in enumerate(entries):
        try:
            patterns.append(AssetPattern.from_dict(entry))
        except (PatternError, KeyError, ValueError) as exc:
            # An unparseable rule is an ambiguity, never a skipped line.
            ambiguities.append(f"{label}[{index}] could not be parsed: {exc}")
    return patterns


def _text_ambiguities(value: str, *, where: str) -> list[str]:
    lowered = value.lower()
    return [
        f"{where} contains unresolved marker {marker!r}"
        for marker in AMBIGUITY_MARKERS
        if marker in lowered
    ]


def compile_contract(
    programme: dict[str, Any],
    *,
    raw_source: str | None = None,
    now: datetime | None = None,
) -> CompilationResult:
    """Compile a programme record into a ScopeContract.

    Args:
        programme: The parsed programme record.
        raw_source: The exact source text the record was derived from, hashed
            into the contract so later drift is detectable.
        now: Injected clock, for testability.

    Returns:
        A :class:`CompilationResult`. The contract is ``BLOCKED`` if anything is
        ambiguous, and ``PENDING_REVIEW`` at best — never ``VERIFIED`` straight
        out of the compiler.
    """
    now = now or datetime.now(timezone.utc)
    ambiguities: list[str] = []

    programme_id = str(programme.get("id") or "").strip()
    if not programme_id:
        ambiguities.append("programme record has no id")

    in_scope = _parse_patterns(
        programme.get("in_scope", []), label="in_scope", ambiguities=ambiguities
    )
    out_of_scope = _parse_patterns(
        programme.get("out_of_scope", []), label="out_of_scope", ambiguities=ambiguities
    )

    if not in_scope:
        ambiguities.append("no in-scope assets: contract grants nothing")

    # An asset in both lists is not a resolvable overlap. Out-of-scope wins at
    # the gate, but the contradiction means the source was misread or the
    # programme itself is unclear — either way a human must look.
    in_values = {(p.type, p.value.lower()) for p in in_scope}
    for pattern in out_of_scope:
        if (pattern.type, pattern.value.lower()) in in_values:
            ambiguities.append(
                f"{pattern.value!r} appears in both in-scope and out-of-scope"
            )

    max_authority = str(programme.get("max_authority", "LOCAL_FIXTURE")).upper()
    if max_authority not in AUTHORITY_NAMES:
        ambiguities.append(
            f"unknown max_authority {max_authority!r}; "
            f"expected one of {sorted(AUTHORITY_NAMES)}"
        )
        max_authority = "NONE"

    rate_limit = programme.get("rate_limit_rps")
    if max_authority in {"PASSIVE_HTTP", "AUTHENTICATED", "INTRUSIVE"} and not rate_limit:
        ambiguities.append(
            f"max_authority {max_authority} permits target interaction but no "
            "rate limit is defined"
        )

    if programme.get("paused"):
        ambiguities.append("programme is marked paused")

    for field_name in ("notes", "scope_notes", "policy_summary"):
        value = programme.get(field_name)
        if isinstance(value, str):
            ambiguities.extend(_text_ambiguities(value, where=field_name))

    for entry in programme.get("in_scope", []) + programme.get("out_of_scope", []):
        note = entry.get("note") if isinstance(entry, dict) else None
        if isinstance(note, str):
            ambiguities.extend(
                _text_ambiguities(note, where=f"scope note on {entry.get('value')!r}")
            )

    declared = programme.get("verified_at")
    if declared:
        verified_at = (
            datetime.fromisoformat(declared) if isinstance(declared, str) else declared
        )
        if verified_at.tzinfo is None:
            verified_at = verified_at.replace(tzinfo=timezone.utc)
    else:
        ambiguities.append("programme record has no verified_at timestamp")
        verified_at = now

    hashes: list[str] = []
    if raw_source is not None:
        hashes.append(source_hash(raw_source))
    else:
        hashes.append(source_hash(json.dumps(programme, sort_keys=True, default=str)))
        ambiguities.append(
            "no raw programme source supplied; hash covers the parsed record only"
        )

    status = (
        ContractStatus.BLOCKED if ambiguities else ContractStatus.PENDING_REVIEW
    )

    contract = ScopeContract(
        id=str(programme.get("contract_id") or f"scope_{programme_id or 'unknown'}"),
        programme_id=programme_id or "unknown",
        verified_at=verified_at,
        status=status,
        assets_in_scope=in_scope,
        assets_out_of_scope=out_of_scope,
        prohibited_techniques=list(programme.get("prohibited_techniques", [])),
        max_authority=max_authority,
        rate_limit_rps=rate_limit,
        ambiguities=ambiguities,
        source_hashes=hashes,
        human_reviewed=False,
        notes=str(programme.get("notes", "")),
    )
    return CompilationResult(contract=contract, ambiguities=ambiguities)


def mark_reviewed(contract: ScopeContract, *, reviewer: str) -> ScopeContract:
    """Record that a human reviewed this contract, promoting it to VERIFIED.

    Refuses on a blocked contract: review does not resolve ambiguity, it only
    confirms that a clean compile was read by someone. Resolving ambiguity means
    fixing the source and recompiling.
    """
    if contract.status is ContractStatus.BLOCKED:
        raise ValueError(
            "a blocked contract cannot be reviewed into verification; "
            f"resolve its {len(contract.ambiguities)} ambiguity/ies and recompile"
        )
    contract.human_reviewed = True
    contract.status = ContractStatus.VERIFIED
    contract.notes = (contract.notes + f"\nreviewed by: {reviewer}").strip()
    return contract
