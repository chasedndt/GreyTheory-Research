# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 ChaseInTech

from greytheory_collectors.takeover_fingerprints.model import Fingerprint

FINGERPRINT = Fingerprint(
    provider="aws-s3",
    cname_suffixes=("amazonaws.com",),
    body_markers=("NoSuchBucket", "The specified bucket does not exist"),
    proof_requires=(
        "Create the named bucket in the same region and serve a unique token; "
        "bucket names are global, so an operator must confirm it is still free."
    ),
)
