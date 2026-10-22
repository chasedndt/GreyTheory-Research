# Apply items 1-3 of Docs/host-change-review-packet.md. Elevated. Reboots only
# when told to.
#
# Operator approval for this packet was given on 2026-09-09 ("Yes, apply all
# five now"), recorded in Docs/handovers/2026-09-09-host-change-and-architecture-handover.md.
# The approval is the reason this file may exist; the file is not itself the
# approval, and running it twice is safe because every step checks before it
# acts.
#
# Items 4 and 5 (create the VM, attach the VHDX) need the Hyper-V role to be
# live, which needs the reboot, so they live in a separate script that runs
# afterwards.
#
#   powershell -ExecutionPolicy Bypass -File acceptance/apply-host-change-packet.ps1
#   powershell -ExecutionPolicy Bypass -File acceptance/apply-host-change-packet.ps1 -Reboot
#
# When launching elevated from an unelevated shell, do not quote the -File path
# inside Start-Process -ArgumentList: the quotes pass through literally and the
# elevated shell exits at once, having looked for a file whose name starts with
# a quote. Use an unquoted path, or wrap the call in -Command.
#
# Writes a record of what it observed and did next to this script's log root,
# so the change is auditable independent of the shell that ran it.

[CmdletBinding()]
param(
    [switch]$Reboot,
    [string]$LogRoot = 'E:\Projects\GreyTheory\acceptance\host-change'
)

$ErrorActionPreference = 'Stop'

$principal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    throw 'This script changes Windows features and HKLM; run it elevated.'
}

$ServiceGuid = '00004754-facb-11e6-bd58-64006a7986d3'
$RegistryPath = "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Virtualization\GuestCommunicationServices\$ServiceGuid"
$ElementName = 'GreyTheory research worker VSOCK'

New-Item -ItemType Directory -Force $LogRoot | Out-Null
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$record = [ordered]@{
    schema = 'greytheory.host-change-application/1'
    applied_at = (Get-Date).ToString('o')
    packet = 'Docs/host-change-review-packet.md'
    approval = '2026-09-09 operator: "Yes, apply all five now"'
    before = [ordered]@{}
    actions = @()
    after = [ordered]@{}
    reboot_requested = [bool]$Reboot
    # Items 4 and 5 are not this script's to claim.
    vm_created = $false
    vhdx_attached = $false
}

function Feature-State([string]$name) {
    (Get-WindowsOptionalFeature -Online -FeatureName $name).State.ToString()
}

# -- observe first --------------------------------------------------------
$features = @('Microsoft-Hyper-V', 'Microsoft-Hyper-V-Management-PowerShell')
foreach ($f in $features) { $record.before[$f] = Feature-State $f }
$record.before['registry_key_present'] = Test-Path $RegistryPath
$record.before['hypervisor_present'] = (Get-CimInstance Win32_ComputerSystem).HypervisorPresent
$record.before['vmms_installed'] = [bool](Get-Service vmms -ErrorAction SilentlyContinue)

Write-Output "before:"
$record.before.GetEnumerator() | ForEach-Object { "  {0,-42} {1}" -f $_.Key, $_.Value }

# The record is written even when a step fails, so an observe-only run is
# never lost. The first real run failed inside DISM and left nothing behind
# but a stdout log; the 'before' observation is the useful part of that.
$recordPath = Join-Path $LogRoot "host-change-$stamp.json"
$record['outcome'] = 'incomplete'
try {

# -- item 1 and 2: features ------------------------------------------------
$needsReboot = $false
foreach ($f in $features) {
    if ((Feature-State $f) -eq 'Enabled') {
        $record.actions += "$f already enabled; no change"
        continue
    }
    $r = Enable-WindowsOptionalFeature -Online -FeatureName $f -All -NoRestart
    $record.actions += "enabled $f (RestartNeeded=$($r.RestartNeeded))"
    if ($r.RestartNeeded) { $needsReboot = $true }
}

# -- item 3: one registry key ---------------------------------------------
if (Test-Path $RegistryPath) {
    $existing = (Get-ItemProperty $RegistryPath).ElementName
    if ($existing -ne $ElementName) {
        throw "registry key exists with a different ElementName ('$existing'); refusing to overwrite something this packet did not create"
    }
    $record.actions += 'registry key already present with the expected ElementName; no change'
} else {
    New-Item -Path $RegistryPath -Force | Out-Null
    New-ItemProperty -Path $RegistryPath -Name ElementName -Value $ElementName -PropertyType String | Out-Null
    $record.actions += "created $RegistryPath ElementName='$ElementName'"
}

# -- observe again ---------------------------------------------------------
foreach ($f in $features) { $record.after[$f] = Feature-State $f }
$record.after['registry_key_present'] = Test-Path $RegistryPath
$record.after['restart_needed'] = $needsReboot

Write-Output ""
Write-Output "actions:"
$record.actions | ForEach-Object { "  $_" }
Write-Output ""
Write-Output "after:"
$record.after.GetEnumerator() | ForEach-Object { "  {0,-42} {1}" -f $_.Key, $_.Value }

$record['outcome'] = 'applied'
}
catch {
    $record['outcome'] = 'failed'
    $record['error'] = $_.Exception.Message
    throw
}
finally {
    $record | ConvertTo-Json -Depth 4 | Set-Content -Encoding utf8 $recordPath
    Write-Output ""
    Write-Output "record: $recordPath ($($record['outcome']))"
}

if ($Reboot) {
    Write-Output ""
    Write-Output "rebooting in 20 seconds (operator-authorised)"
    shutdown.exe /r /t 20 /c "GreyTheory host-change packet: Hyper-V role enabled; Hermes and the role-buttons bot need relaunching after boot."
}
