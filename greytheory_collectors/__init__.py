"""Binary-proof collectors (Milestone 10).

A collector turns observations into claims with honest provenance. It never
promotes a claim to ``checked`` on its own: ``checked`` requires a deterministic
check the operator can point to, and for most of these collectors that check is
an action against a target, which the execution posture must permit first.
"""

# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 ChaseInTech
