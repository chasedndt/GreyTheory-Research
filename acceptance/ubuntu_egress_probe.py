"""Exercise denied destinations behind the Ubuntu LOCAL_FIXTURE egress policy."""

# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 ChaseInTech

from __future__ import annotations

import errno
import json
import os
import platform
import socket
import time
from typing import Any


class ProbeError(RuntimeError):
    """Raised when a forbidden connection is not refused promptly."""


def _status() -> dict[str, str]:
    values: dict[str, str] = {}
    with open("/proc/self/status", encoding="ascii") as handle:
        for line in handle:
            key, separator, value = line.partition(":")
            if separator:
                values[key] = value.strip()
    return values


def _denied_tcp_probe(
    *, name: str, family: socket.AddressFamily, address: str, port: int
) -> dict[str, Any]:
    started = time.monotonic()
    error_number: int | None = None
    error_name: str | None = None
    with socket.socket(family, socket.SOCK_STREAM) as client:
        client.settimeout(1.0)
        try:
            client.connect((address, port))
        except OSError as exc:
            error_number = exc.errno
            error_name = errno.errorcode.get(exc.errno or -1, type(exc).__name__)
        else:
            raise ProbeError(f"forbidden probe {name!r} connected")
    elapsed_ms = round((time.monotonic() - started) * 1000, 3)
    accepted_errors = {
        errno.EACCES,
        errno.ECONNREFUSED,
        errno.EHOSTUNREACH,
        errno.ENETUNREACH,
        errno.EPERM,
        None,
    }
    if error_number not in accepted_errors:
        raise ProbeError(
            f"forbidden probe {name!r} failed ambiguously: {error_name}"
        )
    # A final reject is immediate for IPv4 on this host. WSL2 currently exposes
    # IPv6 loopback rejection to Python as a bounded socket timeout instead;
    # the privileged post-run nftables counter is the authoritative proof that
    # the packet hit the deny rule rather than escaping the namespace.
    if elapsed_ms > 1_250:
        raise ProbeError(f"forbidden probe {name!r} was not refused promptly")
    return {
        "name": name,
        "family": "ipv6" if family is socket.AF_INET6 else "ipv4",
        "address": address,
        "port": port,
        "connected": False,
        "errno": error_number,
        "error": error_name,
        "elapsed_ms": elapsed_ms,
    }


def main() -> int:
    status = _status()
    security = {
        "effective_uid": os.geteuid(),
        "effective_gid": os.getegid(),
        "effective_capabilities": int(status["CapEff"], 16),
        "bounding_capabilities": int(status["CapBnd"], 16),
        "no_new_privileges": status["NoNewPrivs"] == "1",
    }
    if (
        platform.system() != "Linux"
        or security["effective_uid"] == 0
        or security["effective_gid"] == 0
        or security["effective_capabilities"] != 0
        or security["bounding_capabilities"] != 0
        or security["no_new_privileges"] is not True
    ):
        raise ProbeError("egress probes require an unprivileged Linux process")
    probes = [
        _denied_tcp_probe(
            name="allowed-address-wrong-port",
            family=socket.AF_INET,
            address="8.8.8.8",
            port=444,
        ),
        _denied_tcp_probe(
            name="decoy-address-allowed-port",
            family=socket.AF_INET,
            address="1.1.1.1",
            port=443,
        ),
        _denied_tcp_probe(
            name="ipv6-loopback-allowed-port",
            family=socket.AF_INET6,
            address="::1",
            port=443,
        ),
    ]
    print(
        json.dumps(
            {"schema_version": 1, "security": security, "probes": probes},
            sort_keys=True,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
