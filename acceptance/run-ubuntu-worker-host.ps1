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
ip link set lo up
ip addr add 8.8.8.8/32 dev lo
cd -- '$linuxRoot'
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 acceptance/ubuntu_worker_host.py
"@

& wsl.exe -d $Distribution -- unshare -Urn -- bash -lc $command
if ($LASTEXITCODE -ne 0) {
    throw "GreyTheory Ubuntu worker host acceptance failed with exit code $LASTEXITCODE."
}
