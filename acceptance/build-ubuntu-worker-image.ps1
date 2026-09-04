[CmdletBinding()]
param(
    [ValidatePattern("^[A-Za-z0-9._-]+$")]
    [string]$Distribution = "Ubuntu",
    [ValidateSet("release", "development")]
    [string]$BuildMode = "release",
    [ValidateRange(300, 1800)]
    [int]$TimeoutSeconds = 1200,
    [string]$ImageCache = "E:\Projects\GreyTheory\toolcache\ubuntu-worker-image-24.04.4-amd64",
    [string]$ArtifactRoot = "E:\Projects\GreyTheory\artifacts\ubuntu-worker-image"
)

$ErrorActionPreference = "Stop"
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
if ($repoRoot -match '[\s"]') {
    throw "Repository paths containing whitespace or quotes are not supported by this build wrapper."
}
if ($ImageCache -notmatch '^E:\\Projects\\GreyTheory\\toolcache\\ubuntu-worker-image-24\.04\.4-amd64$') {
    throw "The Ubuntu worker-image cache must use the governed E: GreyTheory path."
}
if ($ArtifactRoot -notmatch '^E:\\Projects\\GreyTheory\\artifacts\\ubuntu-worker-image$') {
    throw "Ubuntu worker images must use the governed E: artifact path."
}
New-Item -ItemType Directory -Path $ArtifactRoot -Force | Out-Null
$recordRoot = Join-Path $ArtifactRoot "build-records"
New-Item -ItemType Directory -Path $recordRoot -Force | Out-Null
$recordName = "build-{0}-{1}" -f (Get-Date -Format "yyyyMMdd-HHmmss"), $PID
$stdoutPath = Join-Path $recordRoot "$recordName.json"
$stderrPath = Join-Path $recordRoot "$recordName.stderr.log"

function Get-OwnedWslDescendantIds {
    param([int]$ParentId)

    $result = @()
    $children = @(Get-CimInstance Win32_Process -Filter "ParentProcessId=$ParentId")
    foreach ($child in $children) {
        $result += Get-OwnedWslDescendantIds -ParentId $child.ProcessId
        if ($child.Name -eq "wsl.exe") {
            $result += [int]$child.ProcessId
        }
    }
    return $result
}

$linuxTimeoutSeconds = $TimeoutSeconds - 30
$arguments = @(
    "-d", $Distribution,
    "--user", "root",
    "--cd", $repoRoot,
    "--",
    "env",
    "GREYTHEORY_IMAGE_CACHE=/mnt/e/Projects/GreyTheory/toolcache/ubuntu-worker-image-24.04.4-amd64",
    "GREYTHEORY_IMAGE_ARTIFACT_ROOT=/mnt/e/Projects/GreyTheory/artifacts/ubuntu-worker-image",
    "GREYTHEORY_IMAGE_BUILD_MODE=$BuildMode",
    "unshare", "-m", "--propagation", "private", "--",
    "timeout", "--foreground", "--signal=TERM", "--kill-after=5s", "${linuxTimeoutSeconds}s",
    "bash", "acceptance/build-ubuntu-worker-image.sh"
)
$process = Start-Process -FilePath "wsl.exe" -ArgumentList $arguments `
    -RedirectStandardOutput $stdoutPath -RedirectStandardError $stderrPath `
    -NoNewWindow -PassThru
$ownedProcessHandle = $process.Handle
if (-not $process.WaitForExit($TimeoutSeconds * 1000)) {
    $ownedWslIds = @(Get-OwnedWslDescendantIds -ParentId $process.Id)
    foreach ($ownedWslId in $ownedWslIds) {
        Stop-Process -Id $ownedWslId -Force -ErrorAction SilentlyContinue
    }
    Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue
    throw "Ubuntu worker-image build exceeded the $TimeoutSeconds-second ceiling."
}
if ($process.ExitCode -ne 0) {
    if (Test-Path -LiteralPath $stderrPath -PathType Leaf) {
        Get-Content -LiteralPath $stderrPath | Out-Host
    }
    throw "Ubuntu worker-image build failed with exit code $($process.ExitCode)."
}
$line = Get-Content -LiteralPath $stdoutPath | Select-Object -Last 1
try {
    $record = $line | ConvertFrom-Json
} catch {
    throw "Ubuntu worker-image build did not emit a valid final JSON record."
}
if (
    $record.posture -ne "LOCAL_FIXTURE" -or
    $record.external_network_contact -ne $false -or
    $record.programme_contacted -ne $false -or
    $record.passive_http_enabled -ne $false -or
    $record.vps_used -ne $false -or
    $record.runtime_accepted -ne $false -or
    $record.hardened_worker_image_accepted -ne $false -or
    $record.reproducibility.independent_builds -ne 2 -or
    $record.reproducibility.byte_identical -ne $true
) {
    throw "Ubuntu worker-image build record failed its non-activation invariants."
}
$line
