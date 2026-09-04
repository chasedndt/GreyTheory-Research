#!/usr/bin/env bash
set -euo pipefail

destination="${1:?destination is required}"
case "$destination" in
  /mnt/e/Projects/GreyTheory/toolcache/nftables-ubuntu-24.04-amd64) ;;
  *)
    printf 'Refusing unexpected nftables destination: %s\n' "$destination" >&2
    exit 1
    ;;
esac

checksum_file="acceptance/fixtures/ubuntu-nftables-amd64.sha256"
if test -x "$destination/root/usr/sbin/nft"; then
  (cd "$destination" && sha256sum --check "$OLDPWD/$checksum_file")
  exit 0
fi
if test -e "$destination"; then
  printf 'Refusing non-empty or incomplete destination: %s\n' "$destination" >&2
  exit 1
fi

parent="$(dirname "$destination")"
mkdir -p "$parent"
staging="$(mktemp -d -p "$parent" nftables-stage.XXXXXX)"
case "$staging" in
  /mnt/e/Projects/GreyTheory/toolcache/nftables-stage.*) ;;
  *)
    printf 'Refusing unexpected staging path: %s\n' "$staging" >&2
    exit 1
    ;;
esac

cd "$staging"
apt-get download \
  libmnl0=1.0.5-2build1 \
  libnftables1=1.0.9-1ubuntu0.1 \
  libnftnl11=1.2.6-2build1 \
  libxtables12=1.8.10-3ubuntu2 \
  nftables=1.0.9-1ubuntu0.1
sha256sum --check "$OLDPWD/$checksum_file"
mkdir root
dpkg-deb -x libmnl0_1.0.5-2build1_amd64.deb root
dpkg-deb -x libnftables1_1.0.9-1ubuntu0.1_amd64.deb root
dpkg-deb -x libnftnl11_1.2.6-2build1_amd64.deb root
dpkg-deb -x libxtables12_1.8.10-3ubuntu2_amd64.deb root
dpkg-deb -x nftables_1.0.9-1ubuntu0.1_amd64.deb root
LD_LIBRARY_PATH="$staging/root/usr/lib/x86_64-linux-gnu" \
  "$staging/root/usr/sbin/nft" --version
mv "$staging" "$destination"
