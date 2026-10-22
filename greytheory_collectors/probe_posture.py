"""The one rule every collector shares: no live probe below ``PASSIVE_HTTP``.

Collectors evaluate observations. Gathering those observations from a real
host is a separate act, gated by the recorded execution posture, and the gate
lives here so no collector can carry a softer copy of it.
"""

# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 ChaseInTech

from __future__ import annotations

from greytheory.authority.gate import AuthorityLevel

LIVE_PROBE_REQUIRES = AuthorityLevel.PASSIVE_HTTP


class ProbeRefused(PermissionError):
    """Raised when a live probe is requested below the posture that allows it."""


def require_probe_posture(posture: AuthorityLevel, *, what: str = "live probing") -> None:
    """Refuse unless the *recorded* execution posture allows a live probe.

    The caller passes the recorded posture; collectors hold no resolver or
    socket of their own, so at ``LOCAL_FIXTURE`` they could not probe even if
    this check were bypassed.
    """

    if posture < LIVE_PROBE_REQUIRES:
        raise ProbeRefused(
            f"{what} needs execution posture {LIVE_PROBE_REQUIRES.name}; "
            f"recorded posture is {posture.name}. Evaluate fixture observations instead."
        )
