"""Bind locked worker-image packages to verified Ubuntu archive metadata."""

# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 ChaseInTech

from __future__ import annotations

import hashlib
import json
import lzma
import sys
from pathlib import Path
from typing import Any


class ArchiveVerificationError(RuntimeError):
    """Raised when signed archive metadata does not bind every locked package."""


EXPECTED_SUITES = ["noble", "noble-updates", "noble-security"]
EXPECTED_FINGERPRINT = "F6ECB3762474EDA9D21B7022871920D1991BC93C"
INDEX_NAME = "main/binary-amd64/Packages.xz"
ARCHIVE_PREFIX = "https://archive.ubuntu.com/ubuntu/"


def _digest(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _release_indexes(payload: bytes) -> dict[str, tuple[str, int]]:
    try:
        lines = payload.decode("utf-8").splitlines()
    except UnicodeDecodeError as exc:
        raise ArchiveVerificationError("verified Release metadata is not UTF-8") from exc
    indexes: dict[str, tuple[str, int]] = {}
    in_sha256 = False
    for line in lines:
        if line == "SHA256:":
            in_sha256 = True
            continue
        if in_sha256 and line and not line.startswith(" "):
            break
        if in_sha256 and line.startswith(" "):
            try:
                checksum, size, name = line.split()
                parsed_size = int(size)
            except (ValueError, TypeError) as exc:
                raise ArchiveVerificationError(
                    "verified Release SHA256 entry is invalid"
                ) from exc
            indexes[name] = (checksum, parsed_size)
    if INDEX_NAME not in indexes:
        raise ArchiveVerificationError("verified Release omits the required index")
    return indexes


def _package_records(payload: bytes) -> list[dict[str, str]]:
    try:
        lines = lzma.decompress(payload).decode("utf-8").splitlines()
    except (lzma.LZMAError, UnicodeDecodeError) as exc:
        raise ArchiveVerificationError("Packages.xz is invalid") from exc
    records: list[dict[str, str]] = []
    fields: dict[str, str] = {}
    for line in lines + [""]:
        if not line:
            if fields:
                records.append(fields)
                fields = {}
            continue
        if line.startswith(" "):
            continue
        key, separator, value = line.partition(": ")
        if separator:
            fields[key] = value
    return records


def verify(
    lock_path: Path,
    metadata_root: Path,
    fingerprint: str,
    keyring_path: Path,
) -> dict[str, Any]:
    try:
        lock = json.loads(lock_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ArchiveVerificationError("package lock is invalid") from exc
    suites = lock.get("archive_suites")
    if (
        lock.get("schema_version") != 1
        or lock.get("release") != "24.04.4"
        or lock.get("architecture") != "amd64"
        or fingerprint != EXPECTED_FINGERPRINT
        or lock.get("archive_signing_fingerprint") != fingerprint
        or suites != EXPECTED_SUITES
    ):
        raise ArchiveVerificationError("package lock archive identity is invalid")
    packages = lock.get("packages")
    if not isinstance(packages, list) or not packages:
        raise ArchiveVerificationError("package lock is empty")
    try:
        keyring = keyring_path.read_bytes()
    except OSError as exc:
        raise ArchiveVerificationError("Ubuntu archive keyring is absent") from exc
    if not keyring:
        raise ArchiveVerificationError("Ubuntu archive keyring is empty")

    records: list[tuple[str, dict[str, str]]] = []
    suite_evidence: list[dict[str, object]] = []
    for suite in suites:
        suite_root = metadata_root / suite
        try:
            inrelease = (suite_root / "InRelease").read_bytes()
            release = (suite_root / "Release").read_bytes()
            packages_compressed = (suite_root / "Packages.xz").read_bytes()
        except OSError as exc:
            raise ArchiveVerificationError(
                f"archive metadata is incomplete: {suite}"
            ) from exc
        expected = _release_indexes(release)[INDEX_NAME]
        if expected != (_digest(packages_compressed), len(packages_compressed)):
            raise ArchiveVerificationError(f"signed Packages index mismatch: {suite}")
        records.extend((suite, record) for record in _package_records(packages_compressed))
        suite_evidence.append(
            {
                "suite": suite,
                "inrelease_sha256": _digest(inrelease),
                "release_sha256": _digest(release),
                "packages_index": INDEX_NAME,
                "packages_index_sha256": _digest(packages_compressed),
                "packages_index_bytes": len(packages_compressed),
            }
        )

    package_evidence: list[dict[str, object]] = []
    for package in packages:
        if not isinstance(package, dict):
            raise ArchiveVerificationError("package lock entry is invalid")
        url = package.get("url")
        if not isinstance(url, str) or not url.startswith(ARCHIVE_PREFIX):
            raise ArchiveVerificationError("package URL is outside the Ubuntu archive")
        relative = url.removeprefix(ARCHIVE_PREFIX)
        matches = [
            suite
            for suite in suites
            if any(
                record_suite == suite
                and fields.get("Package") == package.get("name")
                and fields.get("Version") == package.get("version")
                and fields.get("Architecture") == package.get("architecture")
                and fields.get("Filename") == relative
                and fields.get("SHA256") == package.get("sha256")
                for record_suite, fields in records
            )
        ]
        if not matches:
            raise ArchiveVerificationError(
                "package is absent from signed archive metadata: "
                f"{package.get('name', '<unknown>')}"
            )
        package_evidence.append(
            {
                "name": package["name"],
                "version": package["version"],
                "architecture": package["architecture"],
                "sha256": package["sha256"],
                "suites": matches,
            }
        )
    return {
        "schema_version": 1,
        "archive_signing_fingerprint": fingerprint,
        "archive_keyring_sha256": _digest(keyring),
        "suites": suite_evidence,
        "packages": package_evidence,
    }


def main(arguments: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if arguments is None else arguments)
    if len(args) != 4:
        raise ArchiveVerificationError(
            "expected package lock, metadata root, archive fingerprint, and keyring"
        )
    record = verify(Path(args[0]), Path(args[1]), args[2], Path(args[3]))
    print(json.dumps(record, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
