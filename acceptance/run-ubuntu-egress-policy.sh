#!/usr/bin/env bash
set -euo pipefail

nft_cache="${GREYTHEORY_NFT_CACHE:?GREYTHEORY_NFT_CACHE is required}"
policy="acceptance/fixtures/ubuntu-egress-policy.nft"
tool_manifest="acceptance/fixtures/ubuntu-nftables-tool-manifest.json"
checksum_file="acceptance/fixtures/ubuntu-nftables-amd64.sha256"

case "$nft_cache" in
  /mnt/e/Projects/GreyTheory/toolcache/nftables-ubuntu-24.04-amd64) ;;
  *)
    printf 'Refusing unexpected nftables tool cache: %s\n' "$nft_cache" >&2
    exit 1
    ;;
esac
test -f "$tool_manifest"
test -f "$checksum_file"
(cd "$nft_cache" && sha256sum --check "$OLDPWD/$checksum_file" >/dev/null)
packages=(
  libmnl0_1.0.5-2build1_amd64.deb
  libnftables1_1.0.9-1ubuntu0.1_amd64.deb
  libnftnl11_1.2.6-2build1_amd64.deb
  libxtables12_1.8.10-3ubuntu2_amd64.deb
  nftables_1.0.9-1ubuntu0.1_amd64.deb
)
actual_packages="$(find "$nft_cache" -maxdepth 1 -type f -name '*.deb' -printf '%f\n' | sort)"
expected_packages="$(printf '%s\n' "${packages[@]}" | sort)"
if test "$actual_packages" != "$expected_packages"; then
  printf 'Refusing nftables cache with an unexpected package set.\n' >&2
  exit 1
fi

runtime_dir="$(mktemp -d -p /tmp greytheory-egress.XXXXXX)"
case "$runtime_dir" in
  /tmp/greytheory-egress.*) ;;
  *)
    printf 'Refusing unexpected egress runtime path: %s\n' "$runtime_dir" >&2
    exit 1
    ;;
esac

cleanup() {
  umount /etc/hosts 2>/dev/null || true
  umount /etc 2>/dev/null || true
  rm -rf -- "$runtime_dir"
}
trap cleanup EXIT

# Reconstruct the userspace tool from the hash-locked packages for every run.
# The host distribution is not modified and a stale extracted binary is never
# trusted as acceptance evidence.
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

mkdir -p "$runtime_dir/etc-upper" "$runtime_dir/etc-work"
printf '127.0.0.1 localhost\n::1 localhost\n8.8.8.8 greytheory-canary.invalid greytheory-canary.invalid.\n' \
  > "$runtime_dir/hosts"
mount -t overlay overlay \
  -o "lowerdir=/etc,upperdir=$runtime_dir/etc-upper,workdir=$runtime_dir/etc-work" \
  /etc
if mountpoint -q /etc/hosts; then
  umount /etc/hosts
fi
mount --bind "$runtime_dir/hosts" /etc/hosts

source_dir="$runtime_dir/source"
mkdir -p "$source_dir"
cp -a -- \
  acceptance \
  greytheory \
  greytheory_broker \
  greytheory_worker \
  greytheory_worker_contract \
  "$source_dir/"
cd "$source_dir"

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

setpriv --no-new-privs --bounding-set=-all --inh-caps=-all --ambient-caps=-all -- \
  env PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. \
  python3 acceptance/ubuntu_egress_probe.py > "$runtime_dir/probes.json"

if setpriv --no-new-privs --bounding-set=-all --inh-caps=-all --ambient-caps=-all -- \
  /usr/sbin/ip route add default dev lo >/dev/null 2>&1; then
  printf 'allowed\n' > "$runtime_dir/route-mutation.txt"
else
  printf 'denied\n' > "$runtime_dir/route-mutation.txt"
fi

if setpriv --no-new-privs --bounding-set=-all --inh-caps=-all --ambient-caps=-all -- \
  env LD_LIBRARY_PATH="$nft_lib" "$nft_bin" flush ruleset >/dev/null 2>&1; then
  printf 'allowed\n' > "$runtime_dir/firewall-mutation.txt"
else
  printf 'denied\n' > "$runtime_dir/firewall-mutation.txt"
fi

setpriv --no-new-privs --bounding-set=-all --inh-caps=-all --ambient-caps=-all -- \
  env PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. \
  python3 acceptance/ubuntu_worker_service.py > "$runtime_dir/service.json"

LD_LIBRARY_PATH="$nft_lib" "$nft_bin" list ruleset > "$runtime_dir/ruleset.txt"
python3 acceptance/compose_ubuntu_egress_acceptance.py \
  "$runtime_dir/service.json" \
  "$runtime_dir/probes.json" \
  "$runtime_dir/ruleset.txt" \
  "$policy" \
  "$runtime_dir/network.json" \
  "$runtime_dir/route-mutation.txt" \
  "$runtime_dir/firewall-mutation.txt" \
  "$tool_manifest"
