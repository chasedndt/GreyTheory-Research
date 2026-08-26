[CmdletBinding()]
param(
    [ValidatePattern("^[A-Za-z0-9._-]+$")]
    [string]$Distribution = "Ubuntu",
    [ValidateRange(30, 180)]
    [int]$TimeoutSeconds = 120
)

$ErrorActionPreference = "Stop"
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
if ($repoRoot -match '[\s"]') {
    throw "Repository paths containing whitespace or quotes are not supported by this acceptance wrapper."
}

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
    "unshare", "-Urnm", "-f", "--kill-child=KILL",
    "--map-user=65534", "--map-group=65534", "--keep-caps",
    "--propagation", "private", "--",
    "bash", "acceptance/run-ubuntu-worker-service.sh"
)
$process = Start-Process -FilePath "wsl.exe" -ArgumentList $arguments `
    -NoNewWindow -PassThru
if (-not $process.WaitForExit($TimeoutSeconds * 1000)) {
    $ownedWslIds = @(Get-OwnedWslDescendantIds -ParentId $process.Id)
    foreach ($ownedWslId in $ownedWslIds) {
        Stop-Process -Id $ownedWslId -Force -ErrorAction SilentlyContinue
    }
    Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue
    throw "GreyTheory Ubuntu worker service acceptance exceeded the $TimeoutSeconds-second wrapper ceiling."
}
if ($process.ExitCode -ne 0) {
    throw "GreyTheory Ubuntu worker service acceptance failed with exit code $($process.ExitCode)."
}
