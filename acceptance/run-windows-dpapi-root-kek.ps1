[CmdletBinding()]
param(
    [string]$OutputRoot = "E:\Projects\GreyTheory\acceptance",
    [string]$PythonCommand = "python",
    [ValidateRange(15, 120)]
    [int]$TimeoutSeconds = 60
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$runName = "windows-dpapi-root-kek-{0}-{1}" -f (Get-Date -Format "yyyyMMdd-HHmmss"), $PID
New-Item -ItemType Directory -Path $OutputRoot -Force | Out-Null
$runRoot = New-Item -ItemType Directory -Path (Join-Path $OutputRoot $runName)
$privateRoot = Join-Path $runRoot.FullName "private"
$recordPath = Join-Path $runRoot.FullName "acceptance.json"
$stderrPath = Join-Path $runRoot.FullName "acceptance-error.log"
$script = Join-Path $repoRoot "acceptance\windows_dpapi_root_kek.py"

$process = Start-Process -FilePath $PythonCommand -ArgumentList @(
    $script, "--root", $privateRoot
) -WorkingDirectory $repoRoot -RedirectStandardOutput $recordPath `
    -RedirectStandardError $stderrPath -WindowStyle Hidden -PassThru
$processHandle = $process.Handle
if (-not $process.WaitForExit($TimeoutSeconds * 1000)) {
    Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue
    throw "GreyTheory Windows DPAPI acceptance exceeded its process ceiling."
}
if ($process.ExitCode -ne 0) {
    if (Test-Path -LiteralPath $stderrPath -PathType Leaf) {
        Get-Content -LiteralPath $stderrPath | Out-Host
    }
    throw "GreyTheory Windows DPAPI acceptance failed with exit code $($process.ExitCode)."
}
if (-not (Test-Path -LiteralPath $recordPath -PathType Leaf)) {
    throw "GreyTheory Windows DPAPI acceptance produced no JSON record."
}
try {
    $record = Get-Content -LiteralPath $recordPath -Raw | ConvertFrom-Json
} catch {
    throw "GreyTheory Windows DPAPI acceptance record is not valid JSON."
}
if (
    $record.host -ne "Windows" -or
    $record.provider_id -ne "windows-dpapi-current-user-v1" -or
    $record.provider_scope -ne "current_user" -or
    $record.posture -ne "LOCAL_FIXTURE" -or
    $record.passive_http_enabled -ne $false -or
    $record.external_network_contact -ne $false -or
    $record.worker_exercised -ne $false -or
    $record.provider_approved_for_posture -ne $false -or
    $record.acl_hardening_accepted -ne $false -or
    $record.independent_disaster_recovery_accepted -ne $false -or
    $record.root_kek_plaintext_persisted -ne $false -or
    $record.root_kek_lease_zeroed -ne $true -or
    $record.restart_recovery_same_profile -ne $true -or
    $record.protected_backup_recovery_same_profile -ne $true -or
    $record.cross_profile_recovery_accepted -ne $false -or
    $record.tampered_record_refused -ne $true -or
    $record.capture_recipient_private_key_wrapped -ne $true -or
    $record.capture_round_trip_verified -ne $true -or
    $record.audit_chain_verified -ne $true
) {
    throw "GreyTheory Windows DPAPI acceptance record failed its candidate-provider invariants."
}
Get-Content -LiteralPath $recordPath -Raw
