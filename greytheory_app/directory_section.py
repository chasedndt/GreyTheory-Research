"""Read-model section: what public programme directories returned.

A lookup is the front door to registering a programme, and it is easy to
mistake for more than it is. Everything here is written to prevent that:

* it is **what a platform publishes to anyone**, retrieved anonymously;
* it is `PUBLIC` and `UNTRUSTED`, and saving it changed neither;
* it is **not a scope contract**. A contract is compiled from saved sources and
  reviewed by a person. This is one of those sources, before any of that.

The section therefore reports what was read, when, and how large it was - and
says plainly that none of it grants authority to touch the programme it
describes.
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

SECTION_ID = "directory"
SECTION_TITLE = "Directory lookups"

BOUNDARY_NOTE = (
    "What a platform publishes openly about a programme, retrieved anonymously "
    "over HTTPS with redirects refused. This is public, untrusted source "
    "material - the thing a programme bundle is later compiled from. It is not "
    "a scope contract, it has not been reviewed by anyone, and it grants no "
    "authority to test the programme it describes."
)


def _lookup_record(lookup) -> WorkbenchRecord:
    return WorkbenchRecord(
        id=f"lookup:{lookup.identifier}",
        title=lookup.identifier,
        # A stored lookup is a successful read; failures are never recorded.
        status=ReadinessStatus.READY,
        subtitle=f"{lookup.platform} · {lookup.content_type}",
        detail=lookup.url,
        attributes=(
            ("identifier", lookup.identifier),
            ("kind", "directory_lookup"),
            ("platform", lookup.platform),
            ("handle", lookup.handle),
            ("url", lookup.url),
            ("status", str(lookup.status)),
            ("content_type", lookup.content_type),
            ("body_sha256", lookup.body_sha256),
            ("body_bytes", str(lookup.body_bytes)),
            ("retrieved_at", lookup.retrieved_at.isoformat()),
            # Restated on every record. A saved copy of a public page must
            # never read as permission, however official its source looks.
            ("data_class", lookup.data_class),
            ("trust", lookup.trust),
            ("grants_authority", "false"),
        ),
    )


def build_directory_section(store) -> WorkbenchSection:
    """One record per programme whose public page has been read."""

    if store is None:
        return WorkbenchSection(
            SECTION_ID,
            SECTION_TITLE,
            ReadinessStatus.UNKNOWN,
            metrics=(
                WorkbenchMetric(
                    "Programmes read", "unknown", ReadinessStatus.UNKNOWN,
                    "no directory lookup store configured",
                ),
            ),
            note="No directory reads are recorded; configure a private root outside Git.",
        )

    try:
        lookups = store.lookups()
    except Exception as exc:  # noqa: BLE001 - the source failed; say so
        # Fail closed. Reporting "nothing read" for a store that could not be
        # opened would be indistinguishable from having read nothing.
        return WorkbenchSection(
            SECTION_ID,
            SECTION_TITLE,
            ReadinessStatus.BLOCKED,
            metrics=(
                WorkbenchMetric("Source", "failed", ReadinessStatus.BLOCKED, str(exc)),
            ),
            note="The lookup store failed closed; no empty or healthy state was inferred.",
        )

    if not lookups:
        return WorkbenchSection(
            SECTION_ID,
            SECTION_TITLE,
            ReadinessStatus.EMPTY,
            metrics=(WorkbenchMetric("Programmes read", "0", ReadinessStatus.EMPTY),),
            note=BOUNDARY_NOTE,
        )

    return WorkbenchSection(
        SECTION_ID,
        SECTION_TITLE,
        ReadinessStatus.READY,
        metrics=(
            WorkbenchMetric("Programmes read", str(len(lookups)), ReadinessStatus.READY),
            WorkbenchMetric(
                "Bytes retrieved",
                str(sum(item.body_bytes for item in lookups)),
                ReadinessStatus.READY,
                "public content held locally",
            ),
        ),
        records=tuple(
            _lookup_record(item)
            for item in sorted(lookups, key=lambda value: value.identifier)
        ),
        note=BOUNDARY_NOTE,
    )
