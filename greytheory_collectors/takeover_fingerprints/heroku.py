# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 ChaseInTech

from greytheory_collectors.takeover_fingerprints.model import Fingerprint

FINGERPRINT = Fingerprint(
    provider="heroku",
    cname_suffixes=("herokuapp.com", "herokudns.com", "herokussl.com"),
    body_markers=("No such app", "herokucdn.com/error-pages/no-such-app"),
    proof_requires=(
        "Add the hostname as a custom domain on an app the operator owns and "
        "serve a unique token; Heroku verifies domain ownership, so this may fail."
    ),
)
