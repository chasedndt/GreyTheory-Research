#!/usr/bin/env bash
set -euo pipefail

runtime_dir="$(mktemp -d -p /tmp greytheory-worker.XXXXXX)"
case "$runtime_dir" in
  /tmp/greytheory-worker.*) ;;
  *)
    printf 'Refusing unexpected worker runtime path: %s\n' "$runtime_dir" >&2
    exit 1
    ;;
esac

cleanup() {
  umount /etc/hosts 2>/dev/null || true
  umount /etc 2>/dev/null || true
  rm -rf -- "$runtime_dir"
}
trap cleanup EXIT

ip link set lo up
ip addr add 8.8.8.8/32 dev lo
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

setpriv --no-new-privs --bounding-set=-all --inh-caps=-all --ambient-caps=-all -- \
  env PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. \
  python3 acceptance/ubuntu_worker_service.py
