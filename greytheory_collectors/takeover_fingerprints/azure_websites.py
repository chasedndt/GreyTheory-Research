# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 ChaseInTech

from greytheory_collectors.takeover_fingerprints.model import Fingerprint

FINGERPRINT = Fingerprint(
    provider="azure-websites",
    cname_suffixes=("azurewebsites.net", "cloudapp.net", "trafficmanager.net"),
    body_markers=("404 Web Site not found", "Error 404 - Web app not found"),
    proof_requires=(
        "Register the released resource name in the operator's own subscription "
        "and serve a unique token from it."
    ),
)
