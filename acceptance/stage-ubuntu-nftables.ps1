[CmdletBinding()]
param(
    [ValidatePattern("^[A-Za-z0-9._-]+$")]
    [string]$Distribution = "Ubuntu",
    [string]$DestinationRoot = "E:\Projects\GreyTheory\toolcache\nftables-ubuntu-24.04-amd64"
)

$ErrorActionPreference = "Stop"
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
if ($DestinationRoot -notmatch '^E:\\Projects\\GreyTheory\\toolcache\\nftables-ubuntu-24\.04-amd64$') {
    throw "The nftables tool cache must use the governed E: GreyTheory path."
}
$linuxDestination = "/mnt/e/Projects/GreyTheory/toolcache/nftables-ubuntu-24.04-amd64"
$arguments = @(
    "-d", $Distribution,
    "--user", "root",
    "--cd", $repoRoot,
    "--",
    "bash", "acceptance/stage-ubuntu-nftables.sh", $linuxDestination
)
& wsl.exe @arguments
if ($LASTEXITCODE -ne 0) {
    throw "Could not stage the pinned Ubuntu nftables acceptance tool under E:."
}
