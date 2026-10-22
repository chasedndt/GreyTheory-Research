"""Read-model section: which programmes are being worked, and which are set aside.

Two things this section deliberately does not do.

It does not encode active-versus-archived in `ReadinessStatus`. That vocabulary
answers "is this ready", and an archived entry is neither ready nor blocked -
it is simply on a shelf. Overloading a readiness signal with a lifecycle
meaning would make the field unreadable for both purposes, so lifecycle lives
in the subtitle and attributes where a reader can see it for what it is.

It does not describe programmes that are *not* shortlisted. Browsing what is
available is a different question with a different source, and answering both
here would make the section a second, competing view of the registry.
"""

# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 ChaseInTech

from __future__ import annotations

from greytheory_app.contracts import (
    ReadinessStatus,
    WorkbenchMetric,
    WorkbenchRecord,
    WorkbenchSection,
)

SECTION_ID = "shortlist"
SECTION_TITLE = "Shortlist"

#: Stated on the section itself, because an archive whose rules are unstated
#: is one people avoid using.
BOUNDARY_NOTE = (
    "Programmes you have chosen to work, and those you have set aside. "
    "Archiving is reversible and deletes nothing; restore any entry at any "
    "time. Shortlisting records an intention only - it grants no authority, "
    "proves nothing about scope, and never raises a posture."
)


def _entry_record(entry) -> WorkbenchRecord:
    archived = entry.is_archived
    return WorkbenchRecord(
        id=f"shortlist:{entry.programme_id}",
        title=entry.programme_id,
        # Both are intact records; readiness is not the axis in question here.
        status=ReadinessStatus.READY,
        subtitle="set aside" if archived else "being worked",
        detail=entry.note or (
            "Set aside; no reason recorded." if archived
            else "On your active list."
        ),
        attributes=(
            ("programme_id", entry.programme_id),
            ("kind", "shortlist_entry"),
            ("status", entry.status.value),
            ("outcome", entry.outcome.value),
            ("shortlisted_at", entry.shortlisted_at.isoformat()),
            ("updated_at", entry.updated_at.isoformat()),
            # Carried so a command can pin its write and refuse to act on a
            # view the operator has since changed elsewhere.
            ("revision", str(entry.revision)),
            ("grants_authority", "false"),
        ),
    )


def build_shortlist_section(store) -> WorkbenchSection:
    """One record per shortlisted programme, active and archived alike."""

    if store is None:
        return WorkbenchSection(
            SECTION_ID,
            SECTION_TITLE,
            ReadinessStatus.UNKNOWN,
            metrics=(
                WorkbenchMetric(
                    "Shortlist", "unknown", ReadinessStatus.UNKNOWN,
                    "no shortlist store configured",
                ),
            ),
            note="No shortlist is measured; configure a private root outside Git.",
        )

    try:
        entries = store.entries()
    except Exception as exc:  # noqa: BLE001 - the source failed; say so
        # Fail closed rather than reporting an empty shortlist, which would be
        # indistinguishable from having set nothing aside.
        return WorkbenchSection(
            SECTION_ID,
            SECTION_TITLE,
            ReadinessStatus.BLOCKED,
            metrics=(
                WorkbenchMetric("Source", "failed", ReadinessStatus.BLOCKED, str(exc)),
            ),
            note="The shortlist failed closed; no empty or healthy state was inferred.",
        )

    active = [item for item in entries if not item.is_archived]
    archived = [item for item in entries if item.is_archived]

    if not entries:
        return WorkbenchSection(
            SECTION_ID,
            SECTION_TITLE,
            ReadinessStatus.EMPTY,
            metrics=(
                WorkbenchMetric("Being worked", "0", ReadinessStatus.EMPTY),
                WorkbenchMetric("Set aside", "0", ReadinessStatus.EMPTY),
            ),
            note=BOUNDARY_NOTE,
        )

    return WorkbenchSection(
        SECTION_ID,
        SECTION_TITLE,
        # Everything archived is a real state worth distinguishing from an
        # empty shortlist: the work was done, not never started.
        ReadinessStatus.READY if active else ReadinessStatus.ATTENTION,
        metrics=(
            # Counts on both, symmetric, so either view can be reached knowing
            # whether it holds anything.
            WorkbenchMetric(
                "Being worked", str(len(active)),
                ReadinessStatus.READY if active else ReadinessStatus.ATTENTION,
            ),
            WorkbenchMetric("Set aside", str(len(archived)), ReadinessStatus.READY),
        ),
        records=tuple(
            _entry_record(item)
            for item in sorted(entries, key=lambda value: value.programme_id)
        ),
        note=BOUNDARY_NOTE,
    )
