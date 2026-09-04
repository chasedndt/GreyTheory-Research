[CmdletBinding()]
param(
    [ValidatePattern("^[A-Za-z0-9._-]+$")]
    [string]$Distribution = "Ubuntu",
    [ValidateRange(30, 180)]
    [int]$TimeoutSeconds = 120,
    [string]$OutputRoot = "E:\Projects\GreyTheory\acceptance",
    [string]$NftRoot = "E:\Projects\GreyTheory\toolcache\nftables-ubuntu-24.04-amd64"
)

$ErrorActionPreference = "Stop"
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
if ($repoRoot -match '[\s"]') {
    throw "Repository paths containing whitespace or quotes are not supported by this acceptance wrapper."
}
if ($NftRoot -notmatch '^E:\\Projects\\GreyTheory\\toolcache\\nftables-ubuntu-24\.04-amd64$') {
    throw "The nftables tool cache must use the governed E: GreyTheory path."
}
$nftPackage = Join-Path $NftRoot "nftables_1.0.9-1ubuntu0.1_amd64.deb"
if (-not (Test-Path -LiteralPath $nftPackage -PathType Leaf)) {
    throw "Pinned nftables tool is absent. Run acceptance\stage-ubuntu-nftables.ps1 first."
}
$runName = "ubuntu-egress-policy-{0}-{1}" -f (Get-Date -Format "yyyyMMdd-HHmmss"), $PID
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

$linuxNftCache = "/mnt/e/Projects/GreyTheory/toolcache/nftables-ubuntu-24.04-amd64"
$arguments = @(
    "-d", $Distribution,
    "--user", "root",
    "--cd", $repoRoot,
    "--",
    "env",
    "GREYTHEORY_NFT_CACHE=$linuxNftCache",
    "unshare", "-Urnm", "-f", "--kill-child=KILL",
    "--map-user=65534", "--map-group=65534", "--keep-caps",
    "--propagation", "private", "--",
    "bash", "acceptance/run-ubuntu-egress-policy.sh"
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
    throw "GreyTheory Ubuntu egress acceptance exceeded the $TimeoutSeconds-second wrapper ceiling."
}
if ($process.ExitCode -ne 0) {
    if (Test-Path -LiteralPath $stderrPath -PathType Leaf) {
        Get-Content -LiteralPath $stderrPath | Out-Host
    }
    throw "GreyTheory Ubuntu egress acceptance failed with exit code $($process.ExitCode)."
}
try {
    $record = Get-Content -LiteralPath $recordPath -Raw | ConvertFrom-Json
} catch {
    throw "GreyTheory Ubuntu egress acceptance record is not valid JSON."
}
if (
    $record.posture -ne "LOCAL_FIXTURE" -or
    $record.external_network_contact -ne $false -or
    $record.programme_contacted -ne $false -or
    $record.passive_http_enabled -ne $false -or
    $record.vps_used -ne $false -or
    $record.hardened_worker_image_accepted -ne $false -or
    $record.egress_policy.engine -ne "nftables" -or
    $record.egress_policy.default_input -ne "drop" -or
    $record.egress_policy.default_forward -ne "drop" -or
    $record.egress_policy.default_output -ne "drop" -or
    $record.egress_policy.denied_probe_packets -lt 3 -or
    $record.egress_policy.route_mutation_denied -ne $true -or
    $record.egress_policy.firewall_mutation_denied -ne $true -or
    $record.worker_service.receipt_signature_verified -ne $true -or
    $record.worker_service.replay_state -ne "completed" -or
    $record.worker_service.worker.child_alive -ne $false -or
    $record.worker_service.worker.exitcode -ne 0
) {
    throw "GreyTheory Ubuntu egress acceptance record failed its local-only invariants."
}
Get-Content -LiteralPath $recordPath -Raw
