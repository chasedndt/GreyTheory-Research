[CmdletBinding()]
param(
    [ValidatePattern("^[A-Za-z0-9._-]+$")]
    [string]$Distribution = "Ubuntu",
    [ValidateRange(60, 600)]
    [int]$TimeoutSeconds = 240,
    [string]$OutputRoot = "E:\Projects\GreyTheory\acceptance",
    [string]$NftRoot = "E:\Projects\GreyTheory\toolcache\nftables-ubuntu-24.04-amd64",
    [string]$ArtifactRoot = "E:\Projects\GreyTheory\artifacts\ubuntu-worker-image"
)

$ErrorActionPreference = "Stop"
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
if ($repoRoot -match '[\s"]') {
    throw "Repository paths containing whitespace or quotes are not supported by this acceptance wrapper."
}
if ($OutputRoot -notmatch '^E:\\Projects\\GreyTheory\\acceptance$') {
    throw "Ubuntu worker-image evidence must use the governed E: acceptance path."
}
if ($NftRoot -notmatch '^E:\\Projects\\GreyTheory\\toolcache\\nftables-ubuntu-24\.04-amd64$') {
    throw "The nftables tool cache must use the governed E: GreyTheory path."
}
if ($ArtifactRoot -notmatch '^E:\\Projects\\GreyTheory\\artifacts\\ubuntu-worker-image$') {
    throw "Ubuntu worker images must use the governed E: artifact path."
}
$status = @(& git -C $repoRoot status --porcelain --untracked-files=normal)
if ($LASTEXITCODE -ne 0 -or $status.Count -ne 0) {
    throw "Ubuntu worker-image runtime acceptance requires a clean, committed source tree."
}
$revision = (& git -C $repoRoot rev-parse --verify HEAD).Trim()
if ($LASTEXITCODE -ne 0 -or $revision -notmatch '^[0-9a-f]{40}$') {
    throw "Could not resolve the exact source revision for image acceptance."
}
$imageRoot = Join-Path $ArtifactRoot $revision
$imagePath = Join-Path $imageRoot "greytheory-passive-worker-amd64.squashfs"
$manifestPath = Join-Path $imageRoot "build-manifest.json"
$provenancePath = Join-Path $imageRoot "package-provenance.json"
if (-not (Test-Path -LiteralPath $imagePath -PathType Leaf) -or
    -not (Test-Path -LiteralPath $manifestPath -PathType Leaf) -or
    -not (Test-Path -LiteralPath $provenancePath -PathType Leaf)) {
    throw "The clean-HEAD Ubuntu worker image and manifest are absent. Build them first."
}
$nftPackage = Join-Path $NftRoot "nftables_1.0.9-1ubuntu0.1_amd64.deb"
if (-not (Test-Path -LiteralPath $nftPackage -PathType Leaf)) {
    throw "Pinned nftables tools are absent. Run acceptance\stage-ubuntu-nftables.ps1 first."
}

$runName = "ubuntu-worker-image-{0}-{1}" -f (Get-Date -Format "yyyyMMdd-HHmmss"), $PID
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

$linuxTimeoutSeconds = $TimeoutSeconds - 15
$linuxImageRoot = "/mnt/e/Projects/GreyTheory/artifacts/ubuntu-worker-image/$revision"
$linuxNftRoot = "/mnt/e/Projects/GreyTheory/toolcache/nftables-ubuntu-24.04-amd64"
$arguments = @(
    "-d", $Distribution,
    "--user", "root",
    "--cd", $repoRoot,
    "--",
    "env",
    "GREYTHEORY_IMAGE_DIR=$linuxImageRoot",
    "GREYTHEORY_NFT_CACHE=$linuxNftRoot",
    "unshare", "--mount", "--net", "--fork", "--kill-child=KILL",
    "--propagation", "private", "--",
    "timeout", "--foreground", "--signal=TERM", "--kill-after=5s", "${linuxTimeoutSeconds}s",
    "bash", "acceptance/run-ubuntu-worker-image.sh"
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
    throw "GreyTheory Ubuntu worker-image acceptance exceeded the $TimeoutSeconds-second wrapper ceiling."
}
if ($process.ExitCode -ne 0) {
    if (Test-Path -LiteralPath $stderrPath -PathType Leaf) {
        Get-Content -LiteralPath $stderrPath | Out-Host
    }
    throw "GreyTheory Ubuntu worker-image acceptance failed with exit code $($process.ExitCode)."
}
try {
    $record = Get-Content -LiteralPath $recordPath -Raw | ConvertFrom-Json
} catch {
    throw "GreyTheory Ubuntu worker-image acceptance record is not valid JSON."
}
if (
    $record.posture -ne "LOCAL_FIXTURE" -or
    $record.external_network_contact -ne $false -or
    $record.programme_contacted -ne $false -or
    $record.passive_http_enabled -ne $false -or
    $record.vps_used -ne $false -or
    $record.image_runtime_accepted -ne $true -or
    $record.hardened_worker_image_accepted -ne $false -or
    $record.reboot_vm_conformance_accepted -ne $false -or
    $record.egress_policy.default_input -ne "drop" -or
    $record.egress_policy.default_forward -ne "drop" -or
    $record.egress_policy.default_output -ne "drop" -or
    $record.egress_policy.denied_probe_packets -lt 3 -or
    $record.egress_policy.route_mutation_denied -ne $true -or
    $record.egress_policy.firewall_mutation_denied -ne $true -or
    $record.supply_chain.package_count -ne 18 -or
    $record.supply_chain.archive_signing_fingerprint -ne "F6ECB3762474EDA9D21B7022871920D1991BC93C" -or
    $record.worker_service.receipt_signature_verified -ne $true -or
    $record.worker_service.replay_state -ne "completed" -or
    $record.worker_service.worker.child_alive -ne $false -or
    $record.worker_service.worker.exitcode -ne 0
) {
    throw "GreyTheory Ubuntu worker-image acceptance record failed its local-only invariants."
}
Get-Content -LiteralPath $recordPath -Raw
