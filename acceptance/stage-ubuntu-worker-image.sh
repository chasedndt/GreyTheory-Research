#!/usr/bin/env bash
set -euo pipefail

cache="${GREYTHEORY_IMAGE_CACHE:?GREYTHEORY_IMAGE_CACHE is required}"
repo_root="$(pwd -P)"
base_name="ubuntu-base-24.04.4-base-amd64.tar.gz"
base_url="https://cdimage.ubuntu.com/ubuntu-base/releases/24.04/release"
key_url="https://archive.ubuntu.com/ubuntu/project/ubuntu-archive-keyring.gpg"
package_url_prefix="https://archive.ubuntu.com/ubuntu/pool/main/"
signing_fingerprint="843938DF228D22F7B3742BC0D94AA3F0EFE21092"
archive_signing_fingerprint="F6ECB3762474EDA9D21B7022871920D1991BC93C"
archive_url="https://archive.ubuntu.com/ubuntu"
archive_suites=(noble noble-updates noble-security)
base_checksums="$repo_root/acceptance/fixtures/ubuntu-base-24.04.4-amd64.sha256"
package_lock="$repo_root/acceptance/fixtures/ubuntu-worker-image-package-lock.json"

case "$cache" in
  /mnt/e/Projects/GreyTheory/toolcache/ubuntu-worker-image-24.04.4-amd64) ;;
  *)
    printf 'Refusing unexpected Ubuntu worker-image cache: %s\n' "$cache" >&2
    exit 1
    ;;
esac

mkdir -p "$cache/packages"
curl --fail --location --proto '=https' --tlsv1.2 \
  --output "$cache/SHA256SUMS" "$base_url/SHA256SUMS"
curl --fail --location --proto '=https' --tlsv1.2 \
  --output "$cache/SHA256SUMS.gpg" "$base_url/SHA256SUMS.gpg"
curl --fail --location --proto '=https' --tlsv1.2 \
  --output "$cache/ubuntu-archive-keyring.gpg" "$key_url"

signature_status="$(
  gpgv --status-fd 1 --keyring "$cache/ubuntu-archive-keyring.gpg" \
    "$cache/SHA256SUMS.gpg" "$cache/SHA256SUMS"
)"
if ! grep -Fq "[GNUPG:] VALIDSIG $signing_fingerprint " \
  <<<"$signature_status"; then
  printf 'Ubuntu checksum signature did not use the pinned image key.\n' >&2
  exit 1
fi
pinned_base_digest="$(awk '{print $1}' "$base_checksums")"
if ! grep -Fxq "$pinned_base_digest *$base_name" "$cache/SHA256SUMS" && \
  ! grep -Fxq "$pinned_base_digest  $base_name" "$cache/SHA256SUMS"; then
  printf 'Pinned Ubuntu base digest is absent from the signed checksum set.\n' >&2
  exit 1
fi
if ! test -f "$cache/$base_name"; then
  curl --fail --location --proto '=https' --tlsv1.2 \
    --output "$cache/$base_name" "$base_url/$base_name"
fi
(cd "$cache" && sha256sum --check "$base_checksums")

metadata_root="$cache/archive-metadata"
mkdir -p "$metadata_root"
for suite in "${archive_suites[@]}"; do
  suite_root="$metadata_root/$suite"
  mkdir -p "$suite_root"
  curl --fail --location --proto '=https' --tlsv1.2 \
    --output "$suite_root/InRelease.partial" "$archive_url/dists/$suite/InRelease"
  mv -- "$suite_root/InRelease.partial" "$suite_root/InRelease"
  rm -f -- "$suite_root/Release.partial"
  archive_status="$(
    gpgv --status-fd 1 --keyring "$cache/ubuntu-archive-keyring.gpg" \
      --output "$suite_root/Release.partial" "$suite_root/InRelease"
  )"
  if ! grep -Fq "[GNUPG:] VALIDSIG $archive_signing_fingerprint " \
    <<<"$archive_status"; then
    printf 'Ubuntu archive metadata did not use the pinned archive key: %s\n' \
      "$suite" >&2
    exit 1
  fi
  mv -- "$suite_root/Release.partial" "$suite_root/Release"
  curl --fail --location --proto '=https' --tlsv1.2 \
    --output "$suite_root/Packages.xz.partial" \
    "$archive_url/dists/$suite/main/binary-amd64/Packages.xz"
  mv -- "$suite_root/Packages.xz.partial" "$suite_root/Packages.xz"
done

python3 acceptance/verify_ubuntu_archive_packages.py \
  "$package_lock" "$metadata_root" "$archive_signing_fingerprint" \
  "$cache/ubuntu-archive-keyring.gpg" \
  > "$cache/package-provenance.json.partial"
mv -- "$cache/package-provenance.json.partial" "$cache/package-provenance.json"

mapfile -t package_rows < <(
  python3 - "$package_lock" "$package_url_prefix" <<'PY'
import json
import re
import sys
from pathlib import Path

lock = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
prefix = sys.argv[2]
if (
    lock.get("schema_version") != 1
    or lock.get("release") != "24.04.4"
    or lock.get("architecture") != "amd64"
    or lock.get("archive_signing_fingerprint")
    != "F6ECB3762474EDA9D21B7022871920D1991BC93C"
    or lock.get("archive_suites")
    != ["noble", "noble-updates", "noble-security"]
):
    raise SystemExit("invalid Ubuntu worker-image package lock header")
packages = lock.get("packages")
if not isinstance(packages, list) or not packages:
    raise SystemExit("Ubuntu worker-image package lock is empty")
seen_names: set[str] = set()
seen_files: set[str] = set()
for package in packages:
    name = package.get("name")
    version = package.get("version")
    architecture = package.get("architecture")
    filename = package.get("filename")
    url = package.get("url")
    digest = package.get("sha256")
    if not isinstance(name, str) or not re.fullmatch(r"[a-z0-9][a-z0-9+.-]+", name):
        raise SystemExit("invalid package name")
    if not isinstance(version, str) or not re.fullmatch(r"[A-Za-z0-9.+:~_-]+", version):
        raise SystemExit(f"invalid package version: {name}")
    if architecture not in {"all", "amd64"}:
        raise SystemExit(f"invalid package architecture: {name}")
    if not isinstance(filename, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9.+~_-]+[.]deb", filename):
        raise SystemExit(f"invalid package filename: {name}")
    if not isinstance(url, str) or not url.startswith(prefix) or url.rsplit("/", 1)[-1] != filename:
        raise SystemExit(f"invalid package URL: {name}")
    if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
        raise SystemExit(f"invalid package digest: {name}")
    if name in seen_names or filename in seen_files:
        raise SystemExit(f"duplicate package lock entry: {name}")
    seen_names.add(name)
    seen_files.add(filename)
    print("\t".join((name, version, architecture, filename, url, digest)))
PY
)

expected_files=()
for row in "${package_rows[@]}"; do
  IFS=$'\t' read -r name version architecture filename url digest <<<"$row"
  expected_files+=("$filename")
  target="$cache/packages/$filename"
  if ! test -f "$target"; then
    partial="$target.partial"
    rm -f -- "$partial"
    curl --fail --location --proto '=https' --tlsv1.2 \
      --output "$partial" "$url"
    printf '%s  %s\n' "$digest" "$partial" | sha256sum --check --status -
    mv -- "$partial" "$target"
  fi
  printf '%s  %s\n' "$digest" "$target" | sha256sum --check --status -
  test "$(dpkg-deb -f "$target" Package)" = "$name"
  test "$(dpkg-deb -f "$target" Version)" = "$version"
  test "$(dpkg-deb -f "$target" Architecture)" = "$architecture"
done

actual_files="$(find "$cache/packages" -maxdepth 1 -type f -name '*.deb' -printf '%f\n' | sort)"
expected_files_sorted="$(printf '%s\n' "${expected_files[@]}" | sort)"
if test "$actual_files" != "$expected_files_sorted"; then
  printf 'Refusing Ubuntu worker-image cache with an unexpected package set.\n' >&2
  exit 1
fi
printf 'Ubuntu worker-image inputs verified: one signed base plus %d archive-proven packages.\n' \
  "${#expected_files[@]}"
