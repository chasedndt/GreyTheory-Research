[CmdletBinding()]
param(
    [ValidatePattern("^[A-Za-z0-9._-]+$")]
    [string]$Distribution = "Ubuntu",
    [ValidateRange(30, 180)]
    [int]$TimeoutSeconds = 120,
    [string]$OutputRoot = "E:\Projects\GreyTheory\acceptance"
)

$ErrorActionPreference = "Stop"
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
if ($repoRoot -match '[\s"]') {
    throw "Repository paths containing whitespace or quotes are not supported by this acceptance wrapper."
}
$runName = "ubuntu-worker-service-{0}-{1}" -f (Get-Date -Format "yyyyMMdd-HHmmss"), $PID
New-Item -ItemType Directory -Path $OutputRoot -Force | Out-Null
$runRoot = New-Item -ItemType Directory -Path (Join-Path $OutputRoot $runName)
$recordPath = Join-Path $runRoot.FullName "acceptance.json"
$stderrPath = Join-Path $runRoot.FullName "acceptance-error.log"

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
    -RedirectStandardOutput $recordPath -RedirectStandardError $stderrPath `
    -NoNewWindow -PassThru
$ownedProcessHandle = $process.Handle
if (-not $process.WaitForExit($TimeoutSeconds * 1000)) {
    $ownedWslIds = @(Get-OwnedWslDescendantIds -ParentId $process.Id)
    foreach ($ownedWslId in $ownedWslIds) {
        Stop-Process -Id $ownedWslId -Force -ErrorAction SilentlyContinue
    }
    Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue
    throw "GreyTheory Ubuntu worker service acceptance exceeded the $TimeoutSeconds-second wrapper ceiling."
}
if ($process.ExitCode -ne 0) {
    if (Test-Path -LiteralPath $stderrPath -PathType Leaf) {
        Get-Content -LiteralPath $stderrPath | Out-Host
    }
    throw "GreyTheory Ubuntu worker service acceptance failed with exit code $($process.ExitCode)."
}
if (-not (Test-Path -LiteralPath $recordPath -PathType Leaf)) {
    throw "GreyTheory Ubuntu worker service acceptance produced no JSON record."
}
try {
    $record = Get-Content -LiteralPath $recordPath -Raw | ConvertFrom-Json
} catch {
    throw "GreyTheory Ubuntu worker service acceptance record is not valid JSON."
}
if (
    $record.posture -ne "LOCAL_FIXTURE" -or
    $record.passive_http_enabled -ne $false -or
    $record.external_network_contact -ne $false -or
    $record.programme_contacted -ne $false -or
    $record.vps_used -ne $false -or
    $record.root_kek_present -ne $false -or
    $record.worker_service_assembled -ne $true -or
    $record.namespace.default_route -ne $false -or
    $record.namespace.effective_uid -ne 65534 -or
    $record.namespace.effective_capabilities -ne 0 -or
    $record.namespace.bounding_capabilities -ne 0 -or
    $record.namespace.no_new_privileges -ne $true -or
    $record.worker_service.capture_encrypted -ne $true -or
    $record.worker_service.capture_round_trip_verified -ne $true -or
    $record.worker_service.receipt_signature_verified -ne $true -or
    $record.worker_service.replay_state -ne "completed" -or
    $record.worker_service.worker.child_alive -ne $false -or
    $record.worker_service.worker.exitcode -ne 0
) {
    throw "GreyTheory Ubuntu worker service acceptance record failed its local-only invariants."
}
Get-Content -LiteralPath $recordPath -Raw
