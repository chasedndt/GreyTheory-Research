"""What a subdomain-takeover fingerprint is.

A fingerprint says two things about a hosting provider: which CNAME targets
belong to it, and what its *unclaimed-resource* response looks like. The first
supports an ``observed`` claim (the DNS record points at the provider). The
second supports only an ``inferred`` one: a body marker is circumstantial, and
providers change their error pages without notice.
"""

# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 ChaseInTech

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Fingerprint:
    provider: str
    """Short stable identifier, e.g. ``github-pages``."""

    cname_suffixes: tuple[str, ...]
    """Lower-case DNS suffixes (no leading dot) that identify the provider."""

    body_markers: tuple[str, ...]
    """Substrings of the provider's unclaimed-resource page, case-insensitive."""

    proof_requires: str
    """What a human must do to turn ``inferred`` into ``checked``. Always an
    action on the target, so always gated by execution posture."""

    def matches_cname(self, target: str) -> bool:
        host = target.rstrip(".").lower()
        return any(host == s or host.endswith("." + s) for s in self.cname_suffixes)

    def matches_body(self, body: str) -> tuple[str, ...]:
        lowered = body.lower()
        return tuple(m for m in self.body_markers if m.lower() in lowered)
