"""Normalise a built image's clock-derived identity, and record what changed.

The assembly writes an image whose EFI system partition carries FAT timestamps
from the build clock, so two runs of identical inputs differ. This removes that
variation and emits a second, reproducible artifact beside the original.

It is a separate step for the same reason `vhdx_identity.normalise()` is:
normalising is not building, and an artifact and its normalised form are two
different things that should both exist and both be inspectable. The original
is never modified.

    python acceptance/normalise-assembly.py <assembly-directory>

Reads nothing but the image, writes nothing but its normalised twin and a
record. No network, no host change, no claim about a running guest.
"""

# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 ChaseInTech

from __future__ import annotations

import hashlib
import json
import struct
import sys
from pathlib import Path

# Runnable as a file, not only as a module: an operator normalising an artifact
# should not have to know how the package is laid out.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from acceptance.fat_identity import normalise_fat_directories  # noqa: E402

IMAGE_NAME = "greytheory-worker.img"
NORMALISED_NAME = "greytheory-worker-normalised.img"
RECORD_NAME = "normalisation.json"


def esp_offset(data: bytes) -> int:
    """Byte offset of the first GPT partition, read from the table itself."""

    if bytes(data[512:520]) != b"EFI PART":
        raise SystemExit("no GPT header at LBA 1; this is not a GreyTheory image")
    entries_lba = struct.unpack_from("<Q", data, 512 + 72)[0]
    first_entry = entries_lba * 512
    return struct.unpack_from("<Q", data, first_entry + 32)[0] * 512


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        raise SystemExit("usage: normalise-assembly.py <assembly-directory>")

    work = Path(argv[1])
    source = work / IMAGE_NAME
    if not source.is_file():
        raise SystemExit(f"no image at {source}")

    original = source.read_bytes()
    data = bytearray(original)
    offset = esp_offset(data)
    entries = normalise_fat_directories(data, offset)

    # Idempotence is the property that makes a normalised digest quotable: a
    # second pass over the result must change nothing, or the digest would
    # depend on how many times the tool had been run.
    settled = bytearray(data)
    if normalise_fat_directories(settled, offset) != 0 or settled != data:
        raise SystemExit("normalisation is not idempotent; refusing to record a digest")

    (work / NORMALISED_NAME).write_bytes(data)
    record = {
        "schema": "greytheory.assembly-normalisation/1",
        "image": str(source),
        "image_sha256": digest(original),
        "normalised_image": str(work / NORMALISED_NAME),
        "normalised_sha256": digest(bytes(data)),
        "esp_offset": offset,
        "directory_entries_normalised": entries,
        "fields_zeroed": "creation tenths/time/date, last access date, write time/date",
        "idempotent": True,
        # Normalising a container says nothing about the guest inside it.
        "runtime_observed": False,
        "boot_verified": False,
        "vm_created": False,
    }
    (work / RECORD_NAME).write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")

    print(f"image           {record['image_sha256']}")
    print(f"normalised      {record['normalised_sha256']}")
    print(f"entries changed {entries}")
    print(f"record          {work / RECORD_NAME}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
