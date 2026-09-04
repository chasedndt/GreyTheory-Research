[CmdletBinding()]
param(
    [ValidatePattern("^[A-Za-z0-9._-]+$")]
    [string]$Distribution = "Ubuntu",
    [ValidateRange(60, 600)]
    [int]$TimeoutSeconds = 300,
    [string]$ImageCache = "E:\Projects\GreyTheory\toolcache\ubuntu-worker-image-24.04.4-amd64"
)

$ErrorActionPreference = "Stop"
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
if ($repoRoot -match '[\s"]') {
    throw "Repository paths containing whitespace or quotes are not supported by this staging wrapper."
}
if ($ImageCache -notmatch '^E:\\Projects\\GreyTheory\\toolcache\\ubuntu-worker-image-24\.04\.4-amd64$') {
    throw "The Ubuntu worker-image cache must use the governed E: GreyTheory path."
}
New-Item -ItemType Directory -Path $ImageCache -Force | Out-Null

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

$arguments = @(
    "-d", $Distribution,
    "--user", "root",
    "--cd", $repoRoot,
    "--",
    "env",
    "GREYTHEORY_IMAGE_CACHE=/mnt/e/Projects/GreyTheory/toolcache/ubuntu-worker-image-24.04.4-amd64",
    "bash", "acceptance/stage-ubuntu-worker-image.sh"
)
$process = Start-Process -FilePath "wsl.exe" -ArgumentList $arguments `
    -NoNewWindow -PassThru
$ownedProcessHandle = $process.Handle
if (-not $process.WaitForExit($TimeoutSeconds * 1000)) {
    $ownedWslIds = @(Get-OwnedWslDescendantIds -ParentId $process.Id)
    foreach ($ownedWslId in $ownedWslIds) {
        Stop-Process -Id $ownedWslId -Force -ErrorAction SilentlyContinue
    }
    Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue
    throw "Ubuntu worker-image staging exceeded the $TimeoutSeconds-second ceiling."
}
if ($process.ExitCode -ne 0) {
    throw "Ubuntu worker-image staging failed with exit code $($process.ExitCode)."
}
