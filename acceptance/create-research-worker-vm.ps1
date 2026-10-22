# Items 4 and 5 of Docs/host-change-review-packet.md: create the worker VM and
# attach the boot disk. Elevated. Runs only after the Hyper-V role is live.
#
# Everything here is exactly what the packet's section 2 lists, and nothing
# else. The VM has zero network adapters and Secure Boot on the Microsoft UEFI
# CA template, because the donor's shim is signed by that CA and the whole point
# of copying signed components verbatim is that this template then refuses a
# rebuilt one.
#
#   powershell -ExecutionPolicy Bypass -File acceptance/create-research-worker-vm.ps1 -Vhdx <path>
#
# The VM ID is captured and recorded. It is never wildcarded and never guessed
# downstream: the carrier admits exactly this UUID.

[CmdletBinding()]
param(
    [Parameter(Mandatory)] [string]$Vhdx,
    [string]$Name = 'GreyTheory-Research-Worker',
    [string]$RuntimeRoot = 'E:\Projects\GreyTheory\runtime\hyperv\GreyTheory-Research-Worker',
    [string]$LogRoot = 'E:\Projects\GreyTheory\acceptance\host-change'
)

$ErrorActionPreference = 'Stop'

$principal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    throw 'Creating a VM needs the Hyper-V administrators role; run elevated.'
}
if (-not (Get-Service vmms -ErrorAction SilentlyContinue)) {
    throw 'The Hyper-V role is not installed (no vmms service). Apply items 1-3 and reboot first.'
}
if (-not (Test-Path $Vhdx)) { throw "no VHDX at $Vhdx" }
if ((Get-Item $Vhdx).Extension -ne '.vhdx') { throw "$Vhdx is not a .vhdx; a Generation 2 VM needs VHDX" }

if (Get-VM -Name $Name -ErrorAction SilentlyContinue) {
    throw "a VM named $Name already exists; this script creates, it does not reconcile. Remove it deliberately first."
}

New-Item -ItemType Directory -Force $RuntimeRoot | Out-Null
New-Item -ItemType Directory -Force $LogRoot | Out-Null

$vm = New-VM -Name $Name -Generation 2 -MemoryStartupBytes 2GB -Path $RuntimeRoot -NoVHD
Set-VM -VM $vm -ProcessorCount 2 -StaticMemory -AutomaticCheckpointsEnabled $false `
       -AutomaticStartAction Nothing -AutomaticStopAction TurnOff -CheckpointType Disabled
Set-VMFirmware -VM $vm -EnableSecureBoot On -SecureBootTemplate MicrosoftUEFICertificateAuthority

# New-VM attaches one adapter by default. Zero is the contract.
Get-VMNetworkAdapter -VM $vm | Remove-VMNetworkAdapter
Add-VMHardDiskDrive -VM $vm -ControllerType SCSI -Path $Vhdx
$disk = Get-VMHardDiskDrive -VM $vm | Select-Object -First 1
Set-VMFirmware -VM $vm -FirstBootDevice $disk

$vm = Get-VM -Name $Name
$record = [ordered]@{
    schema = 'greytheory.vm-creation/1'
    created_at = (Get-Date).ToString('o')
    packet_items = @(4, 5)
    name = $vm.Name
    vm_id = $vm.Id.Guid
    generation = $vm.Generation
    processors = $vm.ProcessorCount
    memory_bytes = $vm.MemoryStartup
    dynamic_memory = $vm.DynamicMemoryEnabled
    checkpoint_type = $vm.CheckpointType.ToString()
    secure_boot = (Get-VMFirmware -VM $vm).SecureBoot.ToString()
    secure_boot_template = (Get-VMFirmware -VM $vm).SecureBootTemplate
    network_adapters = @(Get-VMNetworkAdapter -VM $vm).Count
    vhdx = $Vhdx
    vhdx_sha256 = (Get-FileHash -Algorithm SHA256 $Vhdx).Hash.ToLower()
    runtime_root = $RuntimeRoot
    # Creating a VM is not booting one. Nothing here is boot evidence.
    vm_booted = $false
    boot_verified = $false
}

$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$recordPath = Join-Path $LogRoot "vm-creation-$stamp.json"
$record | ConvertTo-Json -Depth 4 | Set-Content -Encoding utf8 $recordPath

$record.GetEnumerator() | ForEach-Object { "{0,-24} {1}" -f $_.Key, $_.Value }
Write-Output ""
Write-Output "record: $recordPath"

if ($record.network_adapters -ne 0) { throw 'network adapter count is not zero; refusing to leave the VM in this state' }
