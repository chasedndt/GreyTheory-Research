"""Read-model section: everything a human needs to review a compiled contract.

Reviewing is the gate that turns `PENDING_REVIEW` into `VERIFIED`, and it is a
claim about having *read* something. Asking someone to review without putting
the material in front of them produces a rubber stamp, which is the one outcome
this gate exists to prevent. So this section carries both halves side by side:

* **what the compiler concluded** - in scope, out of scope, prohibited;
* **what it read** - the source documents themselves, from the registry's own
  stored copy rather than from any working-tree file, so the reviewer sees the
  bytes that were actually compiled.

Two things are surfaced that are easy to lose and matter to a reviewer:

* ``capture_mode`` - ``verbatim`` is the publisher's own text; an
  ``operator_extract`` is a paraphrase someone made. Reviewing a paraphrase is
  not the same act as reviewing the source, and the difference must be visible.
* **hash agreement** - each source declares a hash and the bundle records the
  hash actually computed. If they disagree the stored content is not what was
  claimed, and no amount of reading fixes that.

Unresolved ``human_resolutions`` are included because they are precisely what a
blocked contract is waiting on, and `mark_reviewed` refuses a blocked contract:
review does not resolve ambiguity, it confirms a clean compile was read.
"""

# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 ChaseInTech

from __future__ import annotations

import json

from greytheory_app.contracts import (
    ReadinessStatus,
    WorkbenchMetric,
    WorkbenchRecord,
    WorkbenchSection,
)

SECTION_ID = "review"
SECTION_TITLE = "Review material"

#: Enough of a document to judge it in place; the full text stays on disk.
MAX_CONTENT_CHARS = 8000


def _stored_bundle(registry, programme_id: str) -> dict:
    """The registry's own copy of what it compiled, or an empty mapping."""

    latest = registry.latest(programme_id)
    if latest is None:
        return {}
    try:
        return json.loads(registry.source(programme_id, latest.version))
    except Exception:
        # A source that cannot be read is worth saying so about, but it must
        # not take the whole section down with it.
        return {}


def _scope_record(programme_id: str, kind: str, title: str, values: list[str]) -> WorkbenchRecord:
    return WorkbenchRecord(
        id=f"review:{programme_id}:{kind}",
        title=title,
        status=ReadinessStatus.READY if values else ReadinessStatus.EMPTY,
        subtitle=f"{programme_id} · {len(values)} entries",
        detail="\n".join(values) if values else "none recorded",
        attributes=(
            ("programme_id", programme_id),
            ("kind", kind),
            ("count", str(len(values))),
            ("grants_authority", "false"),
        ),
    )


def _state_record(programme_id: str, contract) -> WorkbenchRecord:
    """Whether this one programme has been reviewed, as its own fact.

    The section already counts how many programmes await review, but a count
    cannot tell a reader whether *this* one is among them. Without that, an
    interface has no honest basis for offering - or withholding - a review
    control, so it is carried per programme rather than smeared across the
    three scope records.
    """

    reviewed = bool(getattr(contract, "human_reviewed", False))
    # `mark_reviewed` sets `status`, but a contract from an older store may not
    # carry one, and a missing status must not take the whole section down.
    status = getattr(contract, "status", None)
    status_name = getattr(status, "value", "") or "unknown"
    return WorkbenchRecord(
        id=f"review:{programme_id}:state",
        title=programme_id,
        status=ReadinessStatus.READY if reviewed else ReadinessStatus.ATTENTION,
        subtitle=f"{programme_id} · {'reviewed' if reviewed else 'awaiting review'}",
        detail=(
            f"A person recorded reading this contract; it reads {status_name}."
            if reviewed
            else "No person has recorded reading this compiled contract yet."
        ),
        attributes=(
            ("programme_id", programme_id),
            ("kind", "programme_state"),
            ("human_reviewed", "true" if reviewed else "false"),
            ("contract_status", status_name),
            ("grants_authority", "false"),
        ),
    )


def build_review_section(registry) -> WorkbenchSection:
    """Compiled conclusions beside the sources they were drawn from."""

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
            note="Review material is read from compiled programmes; none is available.",
        )

    programme_ids = list(registry.programmes())
    if not programme_ids:
        return WorkbenchSection(
            SECTION_ID,
            SECTION_TITLE,
            ReadinessStatus.EMPTY,
            metrics=(WorkbenchMetric("Programmes", "0", ReadinessStatus.EMPTY),),
            note="Compile a programme to receive its review material.",
        )

    records: list[WorkbenchRecord] = []
    documents = 0
    mismatches = 0
    awaiting = 0

    for programme_id in programme_ids:
        contract = registry.current_contract(programme_id)
        if contract is None:
            continue
        if not contract.human_reviewed:
            awaiting += 1

        records.append(_state_record(programme_id, contract))
        records.append(_scope_record(
            programme_id, "in-scope", "In scope",
            [p.value for p in getattr(contract, "assets_in_scope", ()) or ()],
        ))
        records.append(_scope_record(
            programme_id, "out-of-scope", "Out of scope",
            [p.value for p in getattr(contract, "assets_out_of_scope", ()) or ()],
        ))
        records.append(_scope_record(
            programme_id, "prohibited", "Prohibited techniques",
            list(getattr(contract, "prohibited_techniques", ()) or ()),
        ))

        bundle = _stored_bundle(registry, programme_id)
        for source in bundle.get("sources") or []:
            if not isinstance(source, dict):
                continue
            source_id = str(source.get("id") or "")
            if not source_id:
                continue
            documents += 1
            declared = str(source.get("declared_hash") or "")
            actual = str(source.get("actual_hash") or "")
            agrees = bool(declared) and declared == actual
            if not agrees:
                mismatches += 1
            content = str(source.get("content") or "")
            records.append(WorkbenchRecord(
                id=f"review:{programme_id}:source:{source_id}",
                title=source_id,
                # A hash disagreement is not a presentation detail. The stored
                # content is not what was claimed, and reading it proves nothing.
                status=ReadinessStatus.READY if agrees else ReadinessStatus.BLOCKED,
                subtitle=f"{programme_id} · {source.get('capture_mode') or 'unknown capture'}",
                detail=content[:MAX_CONTENT_CHARS],
                attributes=(
                    ("programme_id", programme_id),
                    ("kind", "source_document"),
                    ("capture_mode", str(source.get("capture_mode") or "unknown")),
                    ("hash_agrees", "true" if agrees else "false"),
                    ("declared_hash", declared),
                    ("bytes", str(len(content))),
                    ("truncated", "true" if len(content) > MAX_CONTENT_CHARS else "false"),
                ),
            ))

        for index, resolution in enumerate(bundle.get("human_resolutions") or [], start=1):
            question = resolution.get("id") if isinstance(resolution, dict) else str(resolution)
            resolved = bool(isinstance(resolution, dict) and resolution.get("resolved_by"))
            records.append(WorkbenchRecord(
                id=f"review:{programme_id}:resolution:{index}",
                title=str(question or f"resolution {index}"),
                status=ReadinessStatus.READY if resolved else ReadinessStatus.BLOCKED,
                subtitle=f"{programme_id} · human resolution",
                detail=(
                    str(resolution.get("question") or "") if isinstance(resolution, dict) else ""
                ) or "A human must settle this before the contract can compile clean.",
                attributes=(
                    ("programme_id", programme_id),
                    ("kind", "human_resolution"),
                    ("resolved", "true" if resolved else "false"),
                ),
            ))

    return WorkbenchSection(
        SECTION_ID,
        SECTION_TITLE,
        ReadinessStatus.BLOCKED if mismatches else ReadinessStatus.READY,
        metrics=(
            WorkbenchMetric("Source documents", str(documents), ReadinessStatus.READY),
            WorkbenchMetric(
                "Hash disagreements", str(mismatches),
                ReadinessStatus.BLOCKED if mismatches else ReadinessStatus.READY,
                "stored content differing from the hash it declared",
            ),
            WorkbenchMetric(
                "Awaiting review", str(awaiting),
                ReadinessStatus.ATTENTION if awaiting else ReadinessStatus.READY,
            ),
        ),
        records=tuple(records),
        note=(
            "The compiled conclusions beside the sources they came from, taken "
            "from the registry's own stored copy. Reviewing confirms a clean "
            "compile was read; it does not resolve ambiguity and grants nothing."
        ),
    )
