#!/usr/bin/env bash
set -euo pipefail

cache="${GREYTHEORY_IMAGE_CACHE:?GREYTHEORY_IMAGE_CACHE is required}"
artifact_root="${GREYTHEORY_IMAGE_ARTIFACT_ROOT:?GREYTHEORY_IMAGE_ARTIFACT_ROOT is required}"
build_mode="${GREYTHEORY_IMAGE_BUILD_MODE:-release}"
repo_root="$(pwd -P)"
base_name="ubuntu-base-24.04.4-base-amd64.tar.gz"
package_lock="$repo_root/acceptance/fixtures/ubuntu-worker-image-package-lock.json"
image_contract="$repo_root/acceptance/fixtures/ubuntu-worker-image-contract.json"

case "$cache" in
  /mnt/e/Projects/GreyTheory/toolcache/ubuntu-worker-image-24.04.4-amd64) ;;
  *) printf 'Refusing unexpected image cache: %s\n' "$cache" >&2; exit 1 ;;
esac
case "$artifact_root" in
  /mnt/e/Projects/GreyTheory/artifacts/ubuntu-worker-image) ;;
  *) printf 'Refusing unexpected artifact root: %s\n' "$artifact_root" >&2; exit 1 ;;
esac
case "$build_mode" in
  release|development) ;;
  *) printf 'Refusing unexpected image build mode: %s\n' "$build_mode" >&2; exit 1 ;;
esac

bash acceptance/stage-ubuntu-worker-image.sh

source_revision="$(git rev-parse --verify HEAD)"
dirty=false
if ! git diff --quiet --ignore-submodules -- || \
  ! git diff --cached --quiet --ignore-submodules -- || \
  test -n "$(git ls-files --others --exclude-standard)"; then
  dirty=true
fi
if test "$build_mode" = "release" && test "$dirty" = true; then
  printf 'Release image builds require a clean, committed source tree.\n' >&2
  exit 1
fi

source_digest="$(
  python3 - "$repo_root" "$build_mode" <<'PY'
import hashlib
import subprocess
import sys
from pathlib import Path

root = Path(sys.argv[1])
mode = sys.argv[2]
direct = [
    "acceptance/build-ubuntu-worker-image.sh",
    "acceptance/fixtures/ubuntu-canary-cert.pem",
    "acceptance/fixtures/ubuntu-canary-key.pem",
    "acceptance/fixtures/ubuntu-egress-policy.nft",
    "acceptance/fixtures/ubuntu-worker-image-contract.json",
    "acceptance/fixtures/ubuntu-worker-image-package-lock.json",
    "acceptance/fixtures/ubuntu-base-24.04.4-amd64.sha256",
    "acceptance/stage-ubuntu-worker-image.sh",
    "acceptance/ubuntu_egress_probe.py",
    "acceptance/ubuntu_worker_image_entrypoint.py",
    "acceptance/ubuntu_worker_service.py",
    "acceptance/verify_ubuntu_archive_packages.py",
]
packages = ("greytheory", "greytheory_broker", "greytheory_worker", "greytheory_worker_contract")
if mode == "release":
    tracked = subprocess.run(
        ["git", "-C", str(root), "ls-files", "-z", "--", *packages, *direct],
        check=True,
        capture_output=True,
    ).stdout
    inputs = [root / item.decode("utf-8") for item in tracked.split(b"\0") if item]
else:
    inputs = [root / item for item in direct]
    for package in packages:
        inputs.extend(
            path
            for path in (root / package).rglob("*")
            if path.is_file()
            and path.suffix != ".pyc"
            and "__pycache__" not in path.parts
        )
if not inputs or any(not path.is_file() for path in inputs):
    raise SystemExit("worker image source input is absent")
digest = hashlib.sha256()
for path in sorted(set(inputs), key=lambda item: item.relative_to(root).as_posix()):
    relative = path.relative_to(root).as_posix().encode("utf-8")
    digest.update(len(relative).to_bytes(4, "big"))
    digest.update(relative)
    payload = path.read_bytes()
    digest.update(len(payload).to_bytes(8, "big"))
    digest.update(payload)
print(digest.hexdigest())
PY
)"
package_lock_digest="$(sha256sum "$package_lock" | awk '{print $1}')"
base_digest="$(awk '{print $1}' acceptance/fixtures/ubuntu-base-24.04.4-amd64.sha256)"
contract_digest="$(sha256sum "$image_contract" | awk '{print $1}')"
archive_provenance_digest="$(sha256sum "$cache/package-provenance.json" | awk '{print $1}')"

mkdir -p "$artifact_root" /mnt/e/Projects/GreyTheory/image-builds
build_root="$(mktemp -d -p /mnt/e/Projects/GreyTheory/image-builds image.XXXXXX)"
case "$build_root" in
  /mnt/e/Projects/GreyTheory/image-builds/image.*) ;;
  *) printf 'Refusing unexpected image build root: %s\n' "$build_root" >&2; exit 1 ;;
esac
active_roots=()

cleanup() {
  local status="$?"
  local root
  trap - EXIT
  for root in "${active_roots[@]}"; do
    if findmnt -Rno TARGET "$root" 2>/dev/null | grep -q .; then
      umount --recursive "$root" 2>/dev/null || true
    fi
  done
  for root in "${active_roots[@]}"; do
    if findmnt -Rno TARGET "$root" 2>/dev/null | grep -q .; then
      printf 'Refusing cleanup while build mounts remain active under %s.\n' "$root" >&2
      exit 1
    fi
  done
  rm -rf -- "$build_root"
  exit "$status"
}
trap cleanup EXIT

install_packages() {
  local rootfs="$1"
  mkdir -p "$rootfs/packages"
  cp -- "$cache/packages/"*.deb "$rootfs/packages/"
  mknod -m 666 "$rootfs/dev/null" c 1 3
  mknod -m 666 "$rootfs/dev/zero" c 1 5
  mknod -m 666 "$rootfs/dev/full" c 1 7
  mknod -m 666 "$rootfs/dev/random" c 1 8
  mknod -m 666 "$rootfs/dev/urandom" c 1 9
  mknod -m 666 "$rootfs/dev/tty" c 5 0
  mount -t proc -o nosuid,nodev,noexec proc "$rootfs/proc"
  chroot "$rootfs" /usr/bin/env \
    DEBIAN_FRONTEND=noninteractive TZ=UTC \
    /bin/sh -c '/usr/bin/dpkg --unpack /packages/*.deb'
  chroot "$rootfs" /usr/bin/env \
    DEBIAN_FRONTEND=noninteractive TZ=UTC \
    /usr/bin/dpkg --configure -a
  chroot "$rootfs" /usr/bin/python3 - <<'PY'
import cryptography
import sqlite3
import ssl

assert cryptography.__version__
assert sqlite3.sqlite_version
assert ssl.OPENSSL_VERSION
PY
  umount "$rootfs/proc"
  rm -f -- "$rootfs/dev/null" "$rootfs/dev/zero" "$rootfs/dev/full" \
    "$rootfs/dev/random" "$rootfs/dev/urandom" "$rootfs/dev/tty"
  rm -rf -- "$rootfs/packages"
}

verify_locked_packages() {
  local rootfs="$1"
  python3 - "$package_lock" "$rootfs" <<'PY'
import json
import subprocess
import sys
from pathlib import Path

lock = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
rootfs = Path(sys.argv[2])
for package in lock["packages"]:
    output = subprocess.run(
        [
            "chroot",
            str(rootfs),
            "/usr/bin/dpkg-query",
            "-W",
            "-f=${Package}\\t${Version}\\t${Architecture}",
            package["name"],
        ],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    expected = "\t".join(
        (package["name"], package["version"], package["architecture"])
    )
    if output != expected:
        raise SystemExit(f"installed package mismatch: {package['name']}")
PY
}

harden_rootfs() {
  local rootfs="$1"
  install -d -m 0755 "$rootfs/opt/greytheory/acceptance/fixtures"
  if test "$build_mode" = "release"; then
    (
      cd "$repo_root"
      git archive --format=tar HEAD -- \
        greytheory greytheory_broker greytheory_worker greytheory_worker_contract \
        acceptance/ubuntu_worker_service.py \
        acceptance/ubuntu_egress_probe.py \
        acceptance/ubuntu_worker_image_entrypoint.py \
        acceptance/fixtures/ubuntu-canary-cert.pem \
        acceptance/fixtures/ubuntu-canary-key.pem
    ) | tar -xf - -C "$rootfs/opt/greytheory"
  else
    cp -a -- "$repo_root/greytheory" "$rootfs/opt/greytheory/"
    cp -a -- "$repo_root/greytheory_broker" "$rootfs/opt/greytheory/"
    cp -a -- "$repo_root/greytheory_worker" "$rootfs/opt/greytheory/"
    cp -a -- "$repo_root/greytheory_worker_contract" "$rootfs/opt/greytheory/"
    cp -- "$repo_root/acceptance/ubuntu_worker_service.py" \
      "$repo_root/acceptance/ubuntu_egress_probe.py" \
      "$repo_root/acceptance/ubuntu_worker_image_entrypoint.py" \
      "$rootfs/opt/greytheory/acceptance/"
    cp -- "$repo_root/acceptance/fixtures/ubuntu-canary-cert.pem" \
      "$repo_root/acceptance/fixtures/ubuntu-canary-key.pem" \
      "$rootfs/opt/greytheory/acceptance/fixtures/"
  fi
  install -d -m 0755 "$rootfs/usr/share/greytheory"
  cp -- "$image_contract" "$package_lock" \
    "$repo_root/acceptance/fixtures/ubuntu-egress-policy.nft" \
    "$rootfs/usr/share/greytheory/"
  printf '127.0.0.1 localhost\n::1 localhost\n8.8.8.8 greytheory-canary.invalid greytheory-canary.invalid.\n' \
    > "$rootfs/etc/hosts"
  printf 'nameserver 127.0.0.1\noptions attempts:1 timeout:1\n' \
    > "$rootfs/etc/resolv.conf"
  printf 'greytheory-worker\n' > "$rootfs/etc/hostname"
  : > "$rootfs/etc/machine-id"
  rm -rf -- "$rootfs/etc/apt" "$rootfs/usr/lib/apt" \
    "$rootfs/var/cache/apt" "$rootfs/var/lib/apt" "$rootfs/var/log"/*
  rm -f -- "$rootfs/usr/bin/apt" "$rootfs/usr/bin/apt-cache" \
    "$rootfs/usr/bin/apt-cdrom" "$rootfs/usr/bin/apt-config" \
    "$rootfs/usr/bin/apt-get" "$rootfs/usr/bin/apt-mark" \
    "$rootfs/usr/bin/dpkg" "$rootfs/usr/bin/dpkg-deb" \
    "$rootfs/usr/bin/dpkg-divert" "$rootfs/usr/bin/dpkg-maintscript-helper" \
    "$rootfs/usr/bin/dpkg-query" "$rootfs/usr/bin/dpkg-realpath" \
    "$rootfs/usr/bin/dpkg-split" "$rootfs/usr/bin/dpkg-statoverride" \
    "$rootfs/usr/bin/dpkg-trigger"
  find "$rootfs" -xdev -type f -name '*.pyc' -delete
  find "$rootfs" -xdev -type d -name __pycache__ -empty -delete
  find "$rootfs" -xdev -perm /6000 -exec chmod a-s {} +
  chmod -R go-w "$rootfs/opt/greytheory" "$rootfs/usr/share/greytheory"
  chmod 1777 "$rootfs/tmp"
  install -d -m 0755 "$rootfs/run" "$rootfs/proc" "$rootfs/dev"
  find "$rootfs" -xdev -exec touch -h -d '@0' {} +
}

build_one() {
  local slot="$1"
  local disk="$build_root/$slot.ext4"
  local rootfs="$build_root/$slot-root"
  local output="$build_root/$slot.squashfs"
  local sort_file="$build_root/$slot.sort"
  mkdir -p "$rootfs"
  active_roots+=("$rootfs")
  truncate -s 1G "$disk"
  mkfs.ext4 -q -F -L greytheory-build "$disk"
  mount -o loop,nodev,nosuid "$disk" "$rootfs"
  tar -xzf "$cache/$base_name" -C "$rootfs"
  install_packages "$rootfs"
  verify_locked_packages "$rootfs"
  harden_rootfs "$rootfs"
  (cd "$rootfs" && find . -xdev -mindepth 1 -printf '%P 0\n' | LC_ALL=C sort) > "$sort_file"
  mksquashfs "$rootfs" "$output" -noappend -comp xz -b 1M \
    -all-time 0 -mkfs-time 0 -no-xattrs -no-progress -sort "$sort_file"
  umount "$rootfs"
}

build_one a
build_one b
image_a="$build_root/a.squashfs"
image_b="$build_root/b.squashfs"
digest_a="$(sha256sum "$image_a" | awk '{print $1}')"
digest_b="$(sha256sum "$image_b" | awk '{print $1}')"
if test "$digest_a" != "$digest_b"; then
  printf 'Independent image builds were not byte-for-byte reproducible.\n' >&2
  exit 1
fi

identity="$source_revision"
if test "$dirty" = true; then
  identity="dirty-$source_digest"
fi
final_root="$artifact_root/$identity"
mkdir -p "$final_root"
final_image="$final_root/greytheory-passive-worker-amd64.squashfs"
final_provenance="$final_root/package-provenance.json"
final_supply_chain="$final_root/supply-chain"
if test -f "$final_image"; then
  existing_digest="$(sha256sum "$final_image" | awk '{print $1}')"
  if test "$existing_digest" != "$digest_a"; then
    printf 'Refusing to replace an image with the same source identity.\n' >&2
    exit 1
  fi
else
  cp -- "$image_a" "$final_image"
fi
if test -f "$final_provenance"; then
  existing_provenance_digest="$(sha256sum "$final_provenance" | awk '{print $1}')"
  if test "$existing_provenance_digest" != "$archive_provenance_digest"; then
    printf 'Refusing to replace provenance for the same source identity.\n' >&2
    exit 1
  fi
else
  cp -- "$cache/package-provenance.json" "$final_provenance"
fi
supply_chain_stage="$build_root/supply-chain"
mkdir -p "$supply_chain_stage/archive-metadata"
cp -- "$cache/ubuntu-archive-keyring.gpg" "$supply_chain_stage/"
for suite in noble noble-updates noble-security; do
  mkdir -p "$supply_chain_stage/archive-metadata/$suite"
  cp -- "$cache/archive-metadata/$suite/InRelease" \
    "$cache/archive-metadata/$suite/Release" \
    "$cache/archive-metadata/$suite/Packages.xz" \
    "$supply_chain_stage/archive-metadata/$suite/"
done
if test -e "$final_supply_chain"; then
  python3 acceptance/verify_ubuntu_archive_packages.py \
    "$package_lock" "$final_supply_chain/archive-metadata" \
    F6ECB3762474EDA9D21B7022871920D1991BC93C \
    "$final_supply_chain/ubuntu-archive-keyring.gpg" \
    > "$build_root/existing-package-provenance.json"
  if ! cmp --silent "$final_provenance" "$build_root/existing-package-provenance.json"; then
    printf 'Refusing an invalid supply-chain bundle for the same source identity.\n' >&2
    exit 1
  fi
else
  mv -- "$supply_chain_stage" "$final_supply_chain"
fi

python3 - "$final_root/build-manifest.json" "$final_image" \
  "$source_revision" "$source_digest" "$base_digest" "$package_lock_digest" \
  "$contract_digest" "$archive_provenance_digest" "$dirty" "$digest_a" <<'PY'
import json
import sys
from pathlib import Path

(
    manifest_path,
    image_path,
    source_revision,
    source_digest,
    base_digest,
    package_lock_digest,
    contract_digest,
    archive_provenance_digest,
    dirty,
    image_digest,
) = sys.argv[1:]
image = Path(image_path)
payload = {
    "schema_version": 1,
    "image": {
        "name": image.name,
        "format": "squashfs",
        "sha256": image_digest,
        "bytes": image.stat().st_size,
        "read_only_format": True,
    },
    "source": {
        "git_revision": source_revision,
        "tree_digest": source_digest,
        "dirty": dirty == "true",
    },
    "inputs": {
        "ubuntu_base_sha256": base_digest,
        "package_lock_sha256": package_lock_digest,
        "image_contract_sha256": contract_digest,
        "archive_provenance_sha256": archive_provenance_digest,
    },
    "reproducibility": {
        "independent_builds": 2,
        "byte_identical": True,
    },
    "runtime_accepted": False,
    "hardened_worker_image_accepted": False,
    "posture": "LOCAL_FIXTURE",
    "external_network_contact": False,
    "programme_contacted": False,
    "passive_http_enabled": False,
    "vps_used": False,
}
encoded = json.dumps(payload, sort_keys=True, indent=2) + "\n"
manifest = Path(manifest_path)
if manifest.exists():
    if manifest.read_text(encoding="utf-8") != encoded:
        raise SystemExit("refusing to replace a build manifest for the same source identity")
else:
    with manifest.open("x", encoding="utf-8", newline="\n") as handle:
        handle.write(encoded)
print(json.dumps(payload, sort_keys=True))
PY
