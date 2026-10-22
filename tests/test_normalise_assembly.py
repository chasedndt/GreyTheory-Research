"""The normalisation entry point, and the record it is allowed to make.

`fat_identity` is tested on its own; this covers the step an operator actually
runs. Its job is narrow and its refusals matter more than its output: it must
never modify the original, never quote a digest it cannot reproduce, and never
say anything about a guest.
"""

from __future__ import annotations

import hashlib
import json
import struct
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
RUNNER = REPO / "acceptance" / "normalise-assembly.py"

SECTOR = 512
ESP_LBA = 2048


def _image(tmp_path: Path, creation_time: int) -> Path:
    """A tiny GPT image whose single partition holds a FAT32 directory."""

    size = ESP_LBA * SECTOR + 4 * SECTOR
    data = bytearray(size)

    data[SECTOR:SECTOR + 8] = b"EFI PART"
    struct.pack_into("<Q", data, SECTOR + 72, 2)          # entries at LBA 2
    struct.pack_into("<Q", data, 2 * SECTOR + 32, ESP_LBA)  # partition first LBA

    esp = ESP_LBA * SECTOR
    struct.pack_into("<H", data, esp + 11, SECTOR)   # bytes per sector
    data[esp + 13] = 1                               # sectors per cluster
    struct.pack_into("<H", data, esp + 14, 1)        # reserved sectors
    data[esp + 16] = 1                               # one FAT
    struct.pack_into("<I", data, esp + 36, 1)        # FAT sectors
    struct.pack_into("<I", data, esp + 44, 2)        # root cluster
    data[esp + 510:esp + 512] = b"\x55\xaa"

    fat = esp + SECTOR
    struct.pack_into("<I", data, fat + 2 * 4, 0x0FFFFFFF)

    entry = fat + SECTOR
    data[entry:entry + 11] = b"BOOTX64 EFI"
    data[entry + 11] = 0x20
    struct.pack_into("<H", data, entry + 14, creation_time)
    struct.pack_into("<H", data, entry + 22, creation_time)
    struct.pack_into("<H", data, entry + 26, 3)
    struct.pack_into("<I", data, entry + 28, 64)

    work = tmp_path / "assembly-test"
    work.mkdir(parents=True)
    path = work / "greytheory-worker.img"
    path.write_bytes(data)
    return path


def _run(directory: Path):
    return subprocess.run(
        [sys.executable, str(RUNNER), str(directory)],
        capture_output=True, text=True, timeout=180,
    )


def test_two_images_differing_only_by_clock_normalise_to_one_digest(tmp_path):
    first = _image(tmp_path / "a", creation_time=0x5022)
    second = _image(tmp_path / "b", creation_time=0x514D)
    assert first.read_bytes() != second.read_bytes()

    for image in (first, second):
        assert _run(image.parent).returncode == 0, "normalisation failed"

    records = [
        json.loads((image.parent / "normalisation.json").read_text(encoding="utf-8"))
        for image in (first, second)
    ]
    assert records[0]["normalised_sha256"] == records[1]["normalised_sha256"]
    assert records[0]["image_sha256"] != records[1]["image_sha256"]


def test_the_original_image_is_never_modified(tmp_path):
    image = _image(tmp_path, creation_time=0x5022)
    before = hashlib.sha256(image.read_bytes()).hexdigest()

    _run(image.parent)

    assert hashlib.sha256(image.read_bytes()).hexdigest() == before
    assert (image.parent / "greytheory-worker-normalised.img").is_file()


def test_the_record_claims_nothing_about_a_guest(tmp_path):
    image = _image(tmp_path, creation_time=0x5022)
    _run(image.parent)

    record = json.loads((image.parent / "normalisation.json").read_text(encoding="utf-8"))

    # Normalising a container says nothing about what runs inside it.
    assert record["runtime_observed"] is False
    assert record["boot_verified"] is False
    assert record["vm_created"] is False
    assert record["idempotent"] is True
    assert record["directory_entries_normalised"] >= 1


def test_running_twice_reaches_the_same_digest(tmp_path):
    image = _image(tmp_path, creation_time=0x5022)
    _run(image.parent)
    first = (image.parent / "greytheory-worker-normalised.img").read_bytes()

    _run(image.parent)
    assert (image.parent / "greytheory-worker-normalised.img").read_bytes() == first


def test_a_missing_image_is_refused(tmp_path):
    empty = tmp_path / "nothing"
    empty.mkdir()

    result = _run(empty)

    assert result.returncode != 0
    assert "no image at" in result.stderr


def test_something_that_is_not_a_greytheory_image_is_refused(tmp_path):
    work = tmp_path / "assembly-bogus"
    work.mkdir()
    (work / "greytheory-worker.img").write_bytes(bytes(8192))

    result = _run(work)

    assert result.returncode != 0
    assert "not a GreyTheory image" in result.stderr


@pytest.mark.parametrize("field", ["image_sha256", "normalised_sha256", "esp_offset"])
def test_the_record_carries_what_an_auditor_needs(tmp_path, field):
    image = _image(tmp_path, creation_time=0x5022)
    _run(image.parent)

    record = json.loads((image.parent / "normalisation.json").read_text(encoding="utf-8"))
    assert record[field], f"{field} must be recorded"
