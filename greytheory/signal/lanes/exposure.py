"""Lane 2 — exposure, over a local tree.

Reads a directory: a checked-out repository, a built web bundle, a deployment
artifact. It fetches nothing and touches no target.

Two restraints shape everything here.

**The value is never recorded.** A signal carries the *shape* of what was found
— its format class, its length, and a short salted-free digest for
de-duplication — and never the bytes. A collector that copies credentials into
the evidence trail has created the problem it was looking for, and it will do
it at scale, quietly, into a store that outlives the engagement.

**Presence is not exposure.** A key in a repository is present. Whether it is
*reachable* depends on whether that path is served, whether the branch is
deployed, whether the file is in the built output — none of which a directory
knows. So every signal here says "present in tree", stays at ``contextual``,
and carries an explicit observed claim naming what remains unknown. The lane
that says "exposed" is the lane that writes reports nobody can defend.
"""

# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 ChaseInTech

from __future__ import annotations

import hashlib
import math
import re
from pathlib import Path
from typing import Iterator

from greytheory.authority.gate import AuthorityLevel
from greytheory.signal.contract import (
    LaneContext,
    LaneSpec,
    RawSignal,
    SignalLevel,
    checked,
    observed,
)

MAX_FILE_BYTES = 2 * 1024 * 1024
"""Files above this are skipped. A collector that reads a 4 GB dump to look for
a token has become a denial of service against its own operator."""

TEXT_SUFFIXES = {
    ".env", ".json", ".yaml", ".yml", ".ini", ".cfg", ".conf", ".toml",
    ".js", ".mjs", ".cjs", ".ts", ".py", ".rb", ".php", ".java", ".go",
    ".txt", ".md", ".sh", ".ps1", ".xml", ".properties", "",
}

CREDENTIAL_FORMATS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("aws_access_key_id", re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b")),
    ("github_token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36,}\b")),
    ("slack_token", re.compile(r"\bxox[baprs]-[0-9A-Za-z-]{10,}\b")),
    ("stripe_secret_key", re.compile(r"\bsk_(?:live|test)_[0-9A-Za-z]{16,}\b")),
    ("google_api_key", re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b")),
    ("private_key_block", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |PGP )?PRIVATE KEY-----")),
    ("jwt", re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.eyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b")),
    ("bearer_header", re.compile(r"\bAuthorization:\s*Bearer\s+[A-Za-z0-9._-]{20,}")),
)

ASSIGNMENT = re.compile(
    r"(?P<key>[A-Za-z0-9_.-]*(?:key|secret|token|password|passwd|credential)"
    r"[A-Za-z0-9_.-]*)\s*[:=]\s*[\"']?(?P<value>[^\s\"',;]{16,})",
    re.IGNORECASE,
)

PLACEHOLDER = re.compile(
    r"^(\$\{?[A-Z_]|env:|secret:|ref:|<|changeme|placeholder|example|xxx+|\.\.\.|"
    r"your[-_]?|todo|dummy|test[-_]?value)",
    re.IGNORECASE,
)

VCS_DIRECTORIES = (".git", ".svn", ".hg", ".bzr")

BACKUP_SUFFIXES = (
    ".bak", ".backup", ".old", ".orig", ".save", ".swp",
    ".sql", ".dump", ".sqlite", ".db",
)
ARCHIVE_SUFFIXES = (".zip", ".tar", ".tgz", ".tar.gz", ".rar", ".7z")

ENTROPY_THRESHOLD = 4.0
"""Shannon bits per character above which a long assigned value is unusual.

Deliberately a *supporting* signal only: entropy alone produces noise, and a
lane that reports every base64 blob teaches its operator to ignore it.
"""


def shannon_entropy(value: str) -> float:
    if not value:
        return 0.0
    counts: dict[str, int] = {}
    for char in value:
        counts[char] = counts.get(char, 0) + 1
    length = len(value)
    return -sum(
        (count / length) * math.log2(count / length) for count in counts.values()
    )


def fingerprint(value: str) -> str:
    """A short digest, for de-duplicating without ever holding the value."""
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:12]


def _is_placeholder(value: str) -> bool:
    return bool(PLACEHOLDER.match(value.strip()))


class ExposureLane:
    """Static review of a local tree for credential and artifact exposure."""

    spec = LaneSpec(
        id="lane2_exposure",
        lane=2,
        title="Local tree exposure review",
        requires_authority=AuthorityLevel.LOCAL_FIXTURE,
        network=False,
        description=(
            "Reads a local directory for credential-shaped strings, VCS "
            "metadata, backups and source maps. Records shape and length, "
            "never values. Reports presence, never reachability."
        ),
    )

    def collect(self, context: LaneContext) -> list[RawSignal]:
        signals: list[RawSignal] = []
        source = self.spec.id
        seen: set[str] = set()

        def emit(
            kind: str, title: str, claims: list, relative: Path, **detail
        ) -> None:
            key = f"{kind}:{relative}:{detail.get('fingerprint', '')}"
            if key in seen:
                return
            seen.add(key)
            signals.append(
                RawSignal(
                    id=f"{self.spec.id}_{kind}_{fingerprint(key)}",
                    lane=2,
                    asset=context.asset,
                    kind=kind,
                    title=title,
                    level=SignalLevel.CONTEXTUAL,
                    claims=claims,
                    detail={"file": str(relative), **detail},
                    observed_at=context.now(),
                )
            )

        self._vcs_metadata(context, emit, source)
        self._artifacts(context, emit, source)
        self._credentials(context, emit, source)
        return signals

    def _vcs_metadata(self, context: LaneContext, emit, source: str) -> None:
        for directory in VCS_DIRECTORIES:
            if not context.exists(directory):
                continue
            emit(
                "vcs_metadata_present",
                f"{directory} metadata is present in the tree",
                [
                    checked(
                        f"{directory} exists at the root of the granted tree",
                        source,
                        f"check:vcs:{directory}",
                    ),
                    observed(
                        "whether this is reachable depends on what the web root "
                        "serves; presence in a tree is not exposure",
                        source,
                    ),
                ],
                Path(directory),
            )

    def _artifacts(self, context: LaneContext, emit, source: str) -> None:
        javascript: set[str] = set()
        maps: set[str] = set()

        for relative in context.iter_files("**/*"):
            name = relative.name.lower()
            suffix = relative.suffix.lower()

            if name.endswith(".js"):
                javascript.add(str(relative))
            if name.endswith(".js.map"):
                maps.add(str(relative)[: -len(".map")])

            if suffix in BACKUP_SUFFIXES or any(
                name.endswith(s) for s in ARCHIVE_SUFFIXES
            ):
                emit(
                    "backup_or_dump_present",
                    f"Backup or archive artifact present: {relative}",
                    [
                        checked(
                            f"{relative} matches a backup or archive suffix",
                            source,
                            f"check:artifact:{relative}",
                        ),
                        observed(
                            "the file was not opened; its contents are unknown",
                            source,
                        ),
                    ],
                    relative,
                )

        for stem in sorted(maps & javascript):
            emit(
                "source_map_present",
                f"Source map ships alongside {stem}",
                [
                    checked(
                        f"{stem}.map exists next to {stem}",
                        source,
                        f"check:sourcemap:{stem}",
                    ),
                    observed(
                        "source maps reveal original source and are often "
                        "intentional in development builds",
                        source,
                    ),
                ],
                Path(stem + ".map"),
            )

    def _readable_files(self, context: LaneContext) -> Iterator[Path]:
        for relative in context.iter_files("**/*"):
            if relative.suffix.lower() not in TEXT_SUFFIXES and not relative.name.startswith(
                ".env"
            ):
                continue
            try:
                if len(context.read_bytes(relative)) > MAX_FILE_BYTES:
                    continue
            except Exception:  # noqa: BLE001 - unreadable is not a finding
                continue
            yield relative

    def _credentials(self, context: LaneContext, emit, source: str) -> None:
        for relative in self._readable_files(context):
            try:
                text = context.read_text(relative)
            except Exception:  # noqa: BLE001
                continue

            for label, pattern in CREDENTIAL_FORMATS:
                for match in pattern.finditer(text):
                    value = match.group(0)
                    emit(
                        "credential_format_match",
                        f"String matching {label} format present in {relative}",
                        [
                            checked(
                                f"{relative} contains a {len(value)}-character "
                                f"string matching the {label} format",
                                source,
                                f"check:format:{label}:{fingerprint(value)}",
                            ),
                            observed(
                                "the value was not read into this signal, not "
                                "validated, and not tested against any service",
                                source,
                            ),
                        ],
                        relative,
                        format=label,
                        length=len(value),
                        fingerprint=fingerprint(value),
                    )

            for match in ASSIGNMENT.finditer(text):
                value = match.group("value")
                if _is_placeholder(value):
                    continue
                entropy = shannon_entropy(value)
                if entropy < ENTROPY_THRESHOLD:
                    continue
                emit(
                    "high_entropy_assignment",
                    f"High-entropy value assigned to {match.group('key')!r} "
                    f"in {relative}",
                    [
                        checked(
                            f"the value assigned to {match.group('key')!r} is "
                            f"{len(value)} characters with {entropy:.2f} bits of "
                            f"entropy per character, above the {ENTROPY_THRESHOLD} "
                            "threshold",
                            source,
                            f"check:entropy:{fingerprint(value)}",
                        ),
                        observed(
                            "entropy alone is weak evidence; this may be a hash, "
                            "an identifier or a build artifact rather than a secret",
                            source,
                        ),
                    ],
                    relative,
                    key=match.group("key"),
                    length=len(value),
                    entropy=round(entropy, 2),
                    fingerprint=fingerprint(value),
                )


__all__ = [
    "CREDENTIAL_FORMATS",
    "ENTROPY_THRESHOLD",
    "ExposureLane",
    "MAX_FILE_BYTES",
    "fingerprint",
    "shannon_entropy",
]
