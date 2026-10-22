# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 ChaseInTech

from greytheory_collectors.takeover_fingerprints.model import Fingerprint

FINGERPRINT = Fingerprint(
    provider="github-pages",
    cname_suffixes=("github.io",),
    body_markers=("There isn't a GitHub Pages site here",),
    proof_requires=(
        "Create a repository whose Pages site answers for the exact hostname and "
        "serve a unique token; only the operator does this, and only in scope."
    ),
)
