# Convert a normalised raw assembly image to a dynamic VHDX, in the same kind
# of throwaway container the assembly runs in. Not a host change.
#
# `qemu-img` is the converter ADR-0028 and acceptance/vhdx_identity.py assume,
# and it exists in none of the WSL distros on this host. `Convert-VHD` would do
# the same job but needs the Hyper-V role, which is exactly what has not landed
# yet. Doing it here keeps the artifact pipeline independent of the host change.
#
# Input is the *normalised* image (acceptance/normalise-assembly.py), so the
# raw-level identity is already fixed before the container format adds its own
# regenerated identifiers - which acceptance/vhdx_identity.py then normalises
# in turn. Two layers, two normalisers, one digest at each.
#
#   powershell -ExecutionPolicy Bypass -File acceptance/convert-image-to-vhdx.ps1 -AssemblyDir <dir>

[CmdletBinding()]
param(
    [Parameter(Mandatory)] [string]$AssemblyDir,
    [string]$Image = 'ubuntu:24.04'
)

$ErrorActionPreference = 'Stop'

$source = Join-Path $AssemblyDir 'greytheory-worker-normalised.img'
if (-not (Test-Path $source)) { throw "no normalised image at $source; run normalise-assembly.py first" }

# Windows path -> container path under the E: bind mount.
$rel = (Resolve-Path $AssemblyDir).Path -replace '^E:\\', '' -replace '\\', '/'
$dirIn = "/mnt/e/$rel"

$inner = @'
set -eu
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq >/dev/null 2>&1
apt-get install -y -qq qemu-utils >/dev/null 2>&1
cd '__DIR__'
qemu-img convert -f raw -O vhdx -o subformat=dynamic greytheory-worker-normalised.img greytheory-worker.vhdx
qemu-img info --output=json greytheory-worker.vhdx > vhdx-info.json
sha256sum greytheory-worker-normalised.img greytheory-worker.vhdx > conversion-digests.txt
'@
$inner = $inner.Replace('__DIR__', $dirIn) -replace "`r`n", "`n"

Write-Output "source  $source"
Write-Output "output  $(Join-Path $AssemblyDir 'greytheory-worker.vhdx')"
& docker run --rm -v 'E:\:/mnt/e' -w /mnt/e $Image sh -c $inner
$code = $LASTEXITCODE
if ($code -ne 0) { throw "conversion failed with exit code $code" }

Get-Content (Join-Path $AssemblyDir 'conversion-digests.txt')
