[CmdletBinding()]
param(
    [string]$Distribution = "Ubuntu"
)

$ErrorActionPreference = "Stop"
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$linuxRoot = (& wsl.exe -d $Distribution --cd $repoRoot -- pwd)
if ($null -ne $linuxRoot) {
    $linuxRoot = $linuxRoot.Trim()
}
if ($LASTEXITCODE -ne 0 -or -not $linuxRoot) {
    throw "Could not map the GreyTheory repository into WSL distribution '$Distribution'."
}
if ($linuxRoot.Contains("'")) {
    throw "Repository paths containing a single quote are not supported by this wrapper."
}

$command = @"
set -euo pipefail
runtime_dir=`$(mktemp -d)
cleanup() {
  umount /etc 2>/dev/null || true
  rm -rf -- "`$runtime_dir"
}
trap cleanup EXIT
ip link set lo up
ip addr add 8.8.8.8/32 dev lo
sysctl -q -w net.ipv4.ip_unprivileged_port_start=0
mkdir -p "`$runtime_dir/etc-upper" "`$runtime_dir/etc-work"
mount -t overlay overlay \
  -o "lowerdir=/etc,upperdir=`$runtime_dir/etc-upper,workdir=`$runtime_dir/etc-work" \
  /etc
printf '\n8.8.8.8 greytheory-canary.invalid\n' >> /etc/hosts
cd -- '$linuxRoot'
setpriv --no-new-privs --bounding-set=-all --inh-caps=-all --ambient-caps=-all -- \
  env PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. \
  python3 acceptance/ubuntu_worker_service.py
"@

& wsl.exe -d $Distribution -- unshare -Urnm -f --kill-child=KILL `
    --map-user=65534 --map-group=65534 --keep-caps --propagation private -- `
    bash -lc $command
if ($LASTEXITCODE -ne 0) {
    throw "GreyTheory Ubuntu worker service acceptance failed with exit code $LASTEXITCODE."
}
