"""Registry of takeover fingerprints, one provider per file."""

# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 ChaseInTech

from greytheory_collectors.takeover_fingerprints import (
    aws_s3,
    azure_websites,
    fastly,
    github_pages,
    heroku,
)
from greytheory_collectors.takeover_fingerprints.model import Fingerprint

FINGERPRINTS: tuple[Fingerprint, ...] = (
    github_pages.FINGERPRINT,
    aws_s3.FINGERPRINT,
    azure_websites.FINGERPRINT,
    heroku.FINGERPRINT,
    fastly.FINGERPRINT,
)

__all__ = ["FINGERPRINTS", "Fingerprint"]
