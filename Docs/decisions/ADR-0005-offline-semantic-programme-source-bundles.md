# ADR-0005 — Offline semantic programme-source bundles

- Status: ACCEPTED
- Date: 2026-08-09

## Context

A real programme's authority is distributed across platform defaults, programme guidelines, structured scope tables, attachments, and linked policies. Treating one manually assembled JSON record as the source hides which documents were read, how faithfully they were captured, which source won a conflict, and whether a later source edit invalidates review.

Saving arbitrary rendered pages as if every capture were equivalent is also misleading. A platform CSV export is verbatim structured evidence; a bounded operator transcript is an extract. The authority record must preserve that distinction.

## Decision

GreyTheory represents one reviewed authority input as an offline `ProgrammeSourceBundle`:

- every source has a kind, capture mode, public HTTPS provenance URL, retrieval time, optional source-update time, safe local path, and declared/actual content hash;
- capture mode is explicit: `structured_export`, `verbatim`, or `operator_extract`;
- precedence is one high-to-low list containing the complete source set;
- every compiled authority field cites one or more source IDs;
- structured exports may declare a deterministic derivation check, so the normalised contract cannot silently omit or add scope rows;
- an operator-structured target-group extract may also declare a format-specific derivation check, but its capture mode must remain `operator_extract` rather than masquerading as a platform export;
- human conflict resolutions are first-class records; pending, rejected, unattributed, or undated decisions block compilation;
- compilation hashes each source plus one canonical semantic snapshot containing the record, source metadata/content, precedence, citations, and resolutions;
- registry review attaches to that complete semantic snapshot, so any substantive source or governing-metadata change invalidates review;
- the bundle loader/compiler never fetches a URL. Acquisition remains a separate operator action until Scope Watch reaches its gated milestone.

## Consequences

- A clean bundle still stops at `PENDING_REVIEW`; compilation never grants authority.
- Extracts can be useful without masquerading as complete page archives.
- Whitespace-only changes to manifest JSON do not invalidate review, while semantic changes do.
- Public source snapshots can live in the repository; confidential programme sources remain protected by the existing registry guard.
- The Bugcrowd/YNAB proof preserves two rendered target groups as an operator extract, derives all 3/5 rows, and blocks on two real programme-prose conflicts instead of choosing authority for the human.
- The schema remains PARTIAL until one direct-VDP bundle proves it against an independently hosted source shape.
