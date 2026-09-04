[CmdletBinding()]
param(
    [string]$OutputRoot = "E:\Projects\GreyTheory\packaging",
    [string]$PythonCommand = "python"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$uiRoot = Join-Path $repoRoot "workbench_ui"
$clientRoot = Join-Path $uiRoot "dist\client"
$runName = "build-{0}-{1}" -f (Get-Date -Format "yyyyMMdd-HHmmss"), $PID
New-Item -ItemType Directory -Path $OutputRoot -Force | Out-Null
$runRoot = New-Item -ItemType Directory -Path (Join-Path $OutputRoot $runName)
$stageRoot = New-Item -ItemType Directory -Path (Join-Path $runRoot.FullName "source")
$wheelRoot = New-Item -ItemType Directory -Path (Join-Path $runRoot.FullName "wheelhouse")

& npm.cmd --prefix $uiRoot run build | Out-Host
if ($LASTEXITCODE -ne 0) {
    throw "Workbench UI build failed with exit code $LASTEXITCODE."
}

foreach ($package in Get-ChildItem -LiteralPath $repoRoot -Directory -Filter "greytheory*") {
    Copy-Item -LiteralPath $package.FullName -Destination (Join-Path $stageRoot.FullName $package.Name) -Recurse
}
foreach ($name in @("pyproject.toml", "README.md", "LICENSE", "NOTICE")) {
    Copy-Item -LiteralPath (Join-Path $repoRoot $name) -Destination $stageRoot.FullName
}

$stagedUiRoot = Join-Path $stageRoot.FullName "greytheory_local\ui"
New-Item -ItemType Directory -Path $stagedUiRoot | Out-Null
Copy-Item -Path (Join-Path $clientRoot "*") -Destination $stagedUiRoot -Recurse

& $PythonCommand -m pip wheel --no-build-isolation --no-deps --wheel-dir $wheelRoot.FullName $stageRoot.FullName | Out-Host
if ($LASTEXITCODE -ne 0) {
    throw "Wheel build failed with exit code $LASTEXITCODE."
}

$wheel = Get-ChildItem -LiteralPath $wheelRoot.FullName -Filter "greytheory-*.whl" | Select-Object -First 1
if (-not $wheel) {
    throw "The GreyTheory wheel was not produced."
}

[PSCustomObject]@{
    RunRoot = $runRoot.FullName
    Wheel = $wheel.FullName
    Sha256 = (Get-FileHash -LiteralPath $wheel.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
}
