#!/usr/bin/env bash
set -euo pipefail

image_dir="${GREYTHEORY_IMAGE_DIR:?GREYTHEORY_IMAGE_DIR is required}"
nft_cache="${GREYTHEORY_NFT_CACHE:?GREYTHEORY_NFT_CACHE is required}"
repo_root="$(pwd -P)"
policy="$repo_root/acceptance/fixtures/ubuntu-egress-policy.nft"
contract="$repo_root/acceptance/fixtures/ubuntu-worker-image-contract.json"
tool_manifest="$repo_root/acceptance/fixtures/ubuntu-nftables-tool-manifest.json"
checksum_file="$repo_root/acceptance/fixtures/ubuntu-nftables-amd64.sha256"
image="$image_dir/greytheory-passive-worker-amd64.squashfs"
manifest="$image_dir/build-manifest.json"
provenance="$image_dir/package-provenance.json"
package_lock="$repo_root/acceptance/fixtures/ubuntu-worker-image-package-lock.json"
supply_chain="$image_dir/supply-chain"
archive_fingerprint="F6ECB3762474EDA9D21B7022871920D1991BC93C"

if [[ ! "$image_dir" =~ ^/mnt/e/Projects/GreyTheory/artifacts/ubuntu-worker-image/[0-9a-f]{40}$ ]]; then
  printf 'Refusing unexpected Ubuntu worker-image directory: %s\n' "$image_dir" >&2
  exit 1
fi
case "$nft_cache" in
  /mnt/e/Projects/GreyTheory/toolcache/nftables-ubuntu-24.04-amd64) ;;
  *) printf 'Refusing unexpected nftables tool cache: %s\n' "$nft_cache" >&2; exit 1 ;;
esac
test "$(id -u)" -eq 0
test -f "$image"
test -f "$manifest"
test -f "$provenance"
test -f "$package_lock"
test -f "$supply_chain/ubuntu-archive-keyring.gpg"
test -f "$policy"
test -f "$contract"
test -f "$tool_manifest"
test -f "$checksum_file"
test -z "$(git status --porcelain --untracked-files=normal)"
test "$(git rev-parse --verify HEAD)" = "${image_dir##*/}"

packages=(
  libmnl0_1.0.5-2build1_amd64.deb
  libnftables1_1.0.9-1ubuntu0.1_amd64.deb
  libnftnl11_1.2.6-2build1_amd64.deb
  libxtables12_1.8.10-3ubuntu2_amd64.deb
  nftables_1.0.9-1ubuntu0.1_amd64.deb
)
(cd "$nft_cache" && sha256sum --check "$checksum_file" >/dev/null)
actual_packages="$(find "$nft_cache" -maxdepth 1 -type f -name '*.deb' -printf '%f\n' | sort)"
expected_packages="$(printf '%s\n' "${packages[@]}" | sort)"
if test "$actual_packages" != "$expected_packages"; then
  printf 'Refusing nftables cache with an unexpected package set.\n' >&2
  exit 1
fi

runtime_dir="$(mktemp -d -p /tmp greytheory-image-runtime.XXXXXX)"
case "$runtime_dir" in
  /tmp/greytheory-image-runtime.*) ;;
  *) printf 'Refusing unexpected image runtime path: %s\n' "$runtime_dir" >&2; exit 1 ;;
esac
rootfs="$runtime_dir/rootfs"
mkdir -p "$rootfs"

cleanup() {
  local status="$?"
  trap - EXIT
  if findmnt -Rno TARGET "$rootfs" 2>/dev/null | grep -q .; then
    umount --recursive "$rootfs" 2>/dev/null || true
  fi
  if findmnt -Rno TARGET "$rootfs" 2>/dev/null | grep -q .; then
    printf 'Refusing cleanup while image mounts remain active under %s.\n' "$rootfs" >&2
    exit 1
  fi
  rm -rf -- "$runtime_dir"
  exit "$status"
}
trap cleanup EXIT

for suite in noble noble-updates noble-security; do
  suite_root="$supply_chain/archive-metadata/$suite"
  test -f "$suite_root/InRelease"
  test -f "$suite_root/Release"
  test -f "$suite_root/Packages.xz"
  signature_status="$(
    gpgv --status-fd 1 --keyring "$supply_chain/ubuntu-archive-keyring.gpg" \
      --output "$runtime_dir/$suite.Release" "$suite_root/InRelease"
  )"
  if ! grep -Fq "[GNUPG:] VALIDSIG $archive_fingerprint " \
    <<<"$signature_status"; then
    printf 'Image artifact archive metadata has an invalid signer: %s\n' "$suite" >&2
    exit 1
  fi
  cmp --silent "$runtime_dir/$suite.Release" "$suite_root/Release"
done
python3 acceptance/verify_ubuntu_archive_packages.py \
  "$package_lock" "$supply_chain/archive-metadata" "$archive_fingerprint" \
  "$supply_chain/ubuntu-archive-keyring.gpg" \
  > "$runtime_dir/package-provenance.json"
cmp --silent "$provenance" "$runtime_dir/package-provenance.json"

mount --make-rprivate /
mount -t squashfs -o loop,ro,nodev,nosuid "$image" "$rootfs"
mount -t tmpfs -o mode=1777,size=64M,nodev,nosuid,noexec tmpfs "$rootfs/tmp"
mount -t tmpfs -o mode=0755,size=8M,nodev,nosuid,noexec tmpfs "$rootfs/run"
mount -t tmpfs -o mode=0755,size=1M,nosuid,noexec tmpfs "$rootfs/dev"
mknod -m 666 "$rootfs/dev/null" c 1 3
mknod -m 666 "$rootfs/dev/zero" c 1 5
mknod -m 666 "$rootfs/dev/full" c 1 7
mknod -m 666 "$rootfs/dev/random" c 1 8
mknod -m 666 "$rootfs/dev/urandom" c 1 9
mknod -m 666 "$rootfs/dev/tty" c 5 0
mount -t proc -o ro,nodev,nosuid,noexec proc "$rootfs/proc"

nft_root="$runtime_dir/nft-root"
nft_bin="$nft_root/usr/sbin/nft"
nft_lib="$nft_root/usr/lib/x86_64-linux-gnu"
mkdir -p "$nft_root"
for package in "${packages[@]}"; do
  dpkg-deb -x "$nft_cache/$package" "$nft_root"
done
test -x "$nft_bin"

ip link set lo up
ip addr add 8.8.8.8/32 dev lo
ip addr add 1.1.1.1/32 dev lo
sysctl -q -w net.ipv4.ip_unprivileged_port_start=0
LD_LIBRARY_PATH="$nft_lib" "$nft_bin" --check --file "$policy"
LD_LIBRARY_PATH="$nft_lib" "$nft_bin" --file "$policy"

ip -j link show > "$runtime_dir/links.json"
ip -j address show > "$runtime_dir/addresses.json"
ip -j route show table all > "$runtime_dir/routes.json"
python3 - "$runtime_dir/links.json" "$runtime_dir/addresses.json" \
  "$runtime_dir/routes.json" > "$runtime_dir/network.json" <<'PY'
import json
import sys
from pathlib import Path

links, addresses, routes = (
    json.loads(Path(value).read_text(encoding="utf-8")) for value in sys.argv[1:]
)
print(json.dumps({"links": links, "addresses": addresses, "routes": routes}))
PY

if setpriv --reuid=65534 --regid=65534 --clear-groups --no-new-privs \
  --bounding-set=-all --inh-caps=-all --ambient-caps=-all -- \
  /usr/sbin/ip route add default dev lo >/dev/null 2>&1; then
  printf 'allowed\n' > "$runtime_dir/route-mutation.txt"
else
  printf 'denied\n' > "$runtime_dir/route-mutation.txt"
fi

if setpriv --reuid=65534 --regid=65534 --clear-groups --no-new-privs \
  --bounding-set=-all --inh-caps=-all --ambient-caps=-all -- \
  env LD_LIBRARY_PATH="$nft_lib" "$nft_bin" flush ruleset >/dev/null 2>&1; then
  printf 'allowed\n' > "$runtime_dir/firewall-mutation.txt"
else
  printf 'denied\n' > "$runtime_dir/firewall-mutation.txt"
fi

chroot "$rootfs" /usr/bin/setpriv \
  --reuid=65534 --regid=65534 --clear-groups --no-new-privs \
  --bounding-set=-all --inh-caps=-all --ambient-caps=-all -- \
  /usr/bin/env -i \
  HOME=/tmp LANG=C.UTF-8 PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 \
  PYTHONPATH=/opt/greytheory TMPDIR=/tmp \
  /usr/bin/python3 /opt/greytheory/acceptance/ubuntu_worker_image_entrypoint.py \
  > "$runtime_dir/runtime.json"

LD_LIBRARY_PATH="$nft_lib" "$nft_bin" list ruleset > "$runtime_dir/ruleset.txt"
python3 acceptance/compose_ubuntu_worker_image_acceptance.py \
  "$manifest" \
  "$image" \
  "$runtime_dir/runtime.json" \
  "$runtime_dir/ruleset.txt" \
  "$policy" \
  "$runtime_dir/network.json" \
  "$runtime_dir/route-mutation.txt" \
  "$runtime_dir/firewall-mutation.txt" \
  "$contract" \
  "$package_lock" \
  "$provenance" \
  "$supply_chain/ubuntu-archive-keyring.gpg"
