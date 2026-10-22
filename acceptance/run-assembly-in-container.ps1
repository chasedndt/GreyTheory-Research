# Run the VHDX assembly inside a throwaway privileged container.
#
# The assembly needs loop devices, `kpartx`, `sgdisk` and `mkfs.vfat`. Neither
# WSL distro on this host has that combination — the Ubuntu distro has no
# `mkfs.vfat` or `kpartx` and no passwordless sudo, and Docker Desktop's own
# distro has no `sgdisk` or `dmsetup`. The container supplies all of it.
#
# This is deliberately NOT a host change and does not appear in
# Docs/host-change-review-packet.md: no Windows feature, service, registry key
# or VM is touched, and the container is removed the moment it exits. What it
# does need is `--privileged`, because attaching a loop device and creating
# device-mapper nodes are kernel operations a normal container cannot perform.
#
# It exists as a file because the first two builds were driven by a one-off
# command that left no record. A build nobody can reproduce is not a build you
# can stand behind, and reconstructing it later cost more than writing it down.
#
#   powershell -File acceptance/run-assembly-in-container.ps1
#
# Exit code is the assembly's own. Output is streamed and also captured.

[CmdletBinding()]
param(
    # Ubuntu 24.04 matches the donor's release line. Pinning by tag rather than
    # digest is a deliberate looseness: the container is a toolbox, and nothing
    # it installs reaches the artifact. Every byte that lands in the image comes
    # from the pinned donor or the pinned payload, both digest-checked.
    [string]$Image = 'ubuntu:24.04',
    [string]$RepoRoot = 'E:\Projects\GreyTheory\2026-09-01-workbench-read-model-binding\worktree',
    [string]$ArtifactRoot = 'E:\Projects\GreyTheory',

    # Container-side paths for the two pinned inputs. Both are digest-checked by
    # the assembly itself; these only say where to look.
    [string]$Donor = '/mnt/e/Projects/GreyTheory/artifacts/hyperv-boot-sources/release-20260826/livecd.ubuntu-cpc.azure.vhd',
    [string]$Payload = '/mnt/e/Projects/GreyTheory/artifacts/ubuntu-worker-image/4ad931ec21fa53cb8ec0d0865064287c1f37f3f1/greytheory-passive-worker-amd64.squashfs',
    [string]$AssemblyRoot = '/mnt/e/Projects/GreyTheory/artifacts/greytheory-vhdx',

    # Check every precondition and stop before touching a loop device.
    [switch]$PlanOnly
)

$ErrorActionPreference = 'Stop'

if (-not (Test-Path (Join-Path $RepoRoot 'acceptance/assemble-greytheory-vhdx.sh'))) {
    throw "no assembly script under $RepoRoot"
}

# Installed inside the container, never on the host.
$tools = 'gdisk dosfstools kpartx util-linux coreutils'

$inner = @'
set -eu
export DEBIAN_FRONTEND=noninteractive
# apt chatter goes to stderr, which PowerShell renders as an error record even
# on success. Silence both streams; a real failure still trips `set -e`.
apt-get update -qq >/dev/null 2>&1
apt-get install -y -qq __TOOLS__ >/dev/null 2>&1
export GREYTHEORY_DONOR_VHD='__DONOR__'
export GREYTHEORY_ROOT_PAYLOAD='__PAYLOAD__'
export GREYTHEORY_ASSEMBLY_ROOT='__ASSEMBLY_ROOT__'
export GREYTHEORY_ASSEMBLY_PLAN_ONLY='__PLAN_ONLY__'
cd /mnt/e/Projects/GreyTheory/__REPO_REL__
exec ./acceptance/assemble-greytheory-vhdx.sh
'@

$repoRel = (Resolve-Path $RepoRoot).Path.Substring((Resolve-Path $ArtifactRoot).Path.Length).TrimStart('\') -replace '\\', '/'
$inner = $inner.
    Replace('__TOOLS__', $tools).
    Replace('__REPO_REL__', $repoRel).
    Replace('__DONOR__', $Donor).
    Replace('__PAYLOAD__', $Payload).
    Replace('__ASSEMBLY_ROOT__', $AssemblyRoot).
    Replace('__PLAN_ONLY__', $(if ($PlanOnly) { '1' } else { '0' }))

# LF only: a CR reaching `sh` inside the container is a syntax error.
$inner = $inner -replace "`r`n", "`n"

Write-Output "image        $Image"
Write-Output "repo         $repoRel"
Write-Output "privileged   yes (loop devices and device-mapper)"
Write-Output ''

# --rm so nothing survives the run. /dev bind-mounted so loop nodes created in
# the container are visible to it; the cleanup trap in the assembly script
# removes device-mapper mappings before detaching loops, or a leaked device
# stays on the host kernel after the container is gone.
$dockerArgs = @(
    'run', '--rm', '--privileged',
    '-v', 'E:\:/mnt/e',
    '-v', '/dev:/dev',
    '-w', '/mnt/e',
    $Image, 'sh', '-c', $inner
)

& docker @dockerArgs
$code = $LASTEXITCODE

Write-Output ''
Write-Output "assembly exit code: $code"
exit $code
