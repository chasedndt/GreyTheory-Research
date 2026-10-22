# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 ChaseInTech

from greytheory_collectors.takeover_fingerprints.model import Fingerprint

FINGERPRINT = Fingerprint(
    provider="fastly",
    cname_suffixes=("fastly.net", "fastlylb.net"),
    body_markers=("Fastly error: unknown domain",),
    proof_requires=(
        "Attach the hostname to a Fastly service the operator controls and serve "
        "a unique token from it."
    ),
)
