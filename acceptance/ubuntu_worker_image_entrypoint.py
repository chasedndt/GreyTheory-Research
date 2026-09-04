"""Admission checks and full-service proof for the read-only Ubuntu image."""

# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 ChaseInTech

from __future__ import annotations

import contextlib
import errno
import io
import json
import os
import platform
from pathlib import Path
from typing import Any

from acceptance import ubuntu_egress_probe, ubuntu_worker_service


class ImageAdmissionError(RuntimeError):
    """Raised when the immutable worker runtime does not match its contract."""


ALLOWED_ENVIRONMENT = {
    "HOME",
    "LANG",
    "PATH",
    "PYTHONDONTWRITEBYTECODE",
    "PYTHONPATH",
    "TMPDIR",
}
EXPECTED_HOSTS = (
    "127.0.0.1 localhost\n"
    "::1 localhost\n"
    "8.8.8.8 greytheory-canary.invalid greytheory-canary.invalid.\n"
)


def _decode_mount_field(value: str) -> str:
    return (
        value.replace(r"\040", " ")
        .replace(r"\011", "\t")
        .replace(r"\012", "\n")
        .replace(r"\134", "\\")
    )


def _parse_mountinfo(raw: str) -> dict[str, dict[str, Any]]:
    mounts: dict[str, dict[str, Any]] = {}
    for line in raw.splitlines():
        if not line:
            continue
        try:
            left, right = line.split(" - ", 1)
        except ValueError as exc:
            raise ImageAdmissionError("invalid mountinfo record") from exc
        left_fields = left.split()
        right_fields = right.split()
        if len(left_fields) < 6 or len(right_fields) < 3:
            raise ImageAdmissionError("incomplete mountinfo record")
        mount_point = _decode_mount_field(left_fields[4])
        mounts[mount_point] = {
            "mount_options": sorted(set(left_fields[5].split(","))),
            "optional_fields": left_fields[6:],
            "filesystem": right_fields[0],
            "source": _decode_mount_field(right_fields[1]),
            "super_options": sorted(set(right_fields[2].split(","))),
        }
    return mounts


def _required_mount(
    mounts: dict[str, dict[str, Any]],
    path: str,
    *,
    filesystem: str,
    options: set[str],
) -> dict[str, Any]:
    mount = mounts.get(path)
    if mount is None or mount["filesystem"] != filesystem:
        raise ImageAdmissionError(f"required {filesystem} mount is absent: {path}")
    actual_options = set(mount["mount_options"]) | set(mount["super_options"])
    if not options.issubset(actual_options):
        raise ImageAdmissionError(f"mount options are incomplete: {path}")
    return mount


def _security_status() -> dict[str, Any]:
    values: dict[str, str] = {}
    for line in Path("/proc/self/status").read_text(encoding="ascii").splitlines():
        key, separator, value = line.partition(":")
        if separator:
            values[key] = value.strip()
    return {
        "effective_uid": os.geteuid(),
        "effective_gid": os.getegid(),
        "supplementary_groups": os.getgroups(),
        "effective_capabilities": int(values["CapEff"], 16),
        "bounding_capabilities": int(values["CapBnd"], 16),
        "no_new_privileges": values["NoNewPrivs"] == "1",
    }


def _assert_write_denied(path: Path) -> dict[str, Any]:
    try:
        path.write_bytes(b"must-not-write")
    except OSError as exc:
        if exc.errno not in {errno.EACCES, errno.EROFS, errno.EPERM}:
            raise ImageAdmissionError(
                f"write denial was ambiguous for {path}: {type(exc).__name__}"
            ) from exc
        return {
            "path": str(path),
            "denied": True,
            "errno": exc.errno,
            "error": errno.errorcode.get(exc.errno, type(exc).__name__),
        }
    try:
        path.unlink()
    except OSError:
        pass
    raise ImageAdmissionError(f"immutable image path was writable: {path}")


def _assert_runtime() -> dict[str, Any]:
    if platform.system() != "Linux":
        raise ImageAdmissionError("image admission requires Linux")
    unexpected_environment = sorted(set(os.environ) - ALLOWED_ENVIRONMENT)
    if unexpected_environment:
        raise ImageAdmissionError("worker environment contains unapproved variables")
    security = _security_status()
    if security != {
        "effective_uid": 65534,
        "effective_gid": 65534,
        "supplementary_groups": [],
        "effective_capabilities": 0,
        "bounding_capabilities": 0,
        "no_new_privileges": True,
    }:
        raise ImageAdmissionError("worker identity does not match the image contract")
    mounts = _parse_mountinfo(
        Path("/proc/self/mountinfo").read_text(encoding="ascii")
    )
    root = _required_mount(
        mounts,
        "/",
        filesystem="squashfs",
        options={"ro", "nodev", "nosuid"},
    )
    if any(field.startswith("shared:") for field in root["optional_fields"]):
        raise ImageAdmissionError("image root mount is unexpectedly shared")
    tmp = _required_mount(
        mounts,
        "/tmp",
        filesystem="tmpfs",
        options={"rw", "nodev", "nosuid", "noexec"},
    )
    run = _required_mount(
        mounts,
        "/run",
        filesystem="tmpfs",
        options={"rw", "nodev", "nosuid", "noexec"},
    )
    dev = _required_mount(
        mounts,
        "/dev",
        filesystem="tmpfs",
        options={"rw", "nosuid", "noexec"},
    )
    proc = _required_mount(
        mounts,
        "/proc",
        filesystem="proc",
        options={"ro", "nodev", "nosuid", "noexec"},
    )
    if Path("/etc/hosts").read_text(encoding="ascii") != EXPECTED_HOSTS:
        raise ImageAdmissionError("image hosts file does not match the owned canary")
    actual_devices = sorted(
        entry.name for entry in Path("/dev").iterdir() if not entry.is_symlink()
    )
    if actual_devices != ["full", "null", "random", "tty", "urandom", "zero"]:
        raise ImageAdmissionError("image device allowlist does not match the contract")
    write_denials = [
        _assert_write_denied(Path("/etc/.greytheory-write-probe")),
        _assert_write_denied(Path("/opt/greytheory/.greytheory-write-probe")),
    ]
    return {
        "security": security,
        "mounts": {
            "root": root,
            "tmp": tmp,
            "run": run,
            "dev": dev,
            "proc": proc,
        },
        "devices": actual_devices,
        "write_denials": write_denials,
        "environment": sorted(os.environ),
    }


def _captured_json(callable_: Any) -> dict[str, Any]:
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        result = callable_()
    if result != 0:
        raise ImageAdmissionError("embedded acceptance returned a non-zero result")
    try:
        payload = json.loads(output.getvalue())
    except json.JSONDecodeError as exc:
        raise ImageAdmissionError("embedded acceptance did not emit JSON") from exc
    if not isinstance(payload, dict):
        raise ImageAdmissionError("embedded acceptance emitted a non-object")
    return payload


def main() -> int:
    evidence = {
        "schema_version": 1,
        "posture": "LOCAL_FIXTURE",
        "external_network_contact": False,
        "programme_contacted": False,
        "passive_http_enabled": False,
        "vps_used": False,
        "image_runtime": _assert_runtime(),
        "egress_probes": _captured_json(ubuntu_egress_probe.main),
        "worker_service": _captured_json(ubuntu_worker_service.main),
    }
    print(json.dumps(evidence, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
