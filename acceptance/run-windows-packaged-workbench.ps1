[CmdletBinding()]
param(
    [string]$OutputRoot = "E:\Projects\GreyTheory\acceptance",
    [string]$PythonCommand = "python",
    [string]$PackageWheel
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$runName = "windows-package-{0}-{1}" -f (Get-Date -Format "yyyyMMdd-HHmmss"), $PID
New-Item -ItemType Directory -Path $OutputRoot -Force | Out-Null
$runRoot = New-Item -ItemType Directory -Path (Join-Path $OutputRoot $runName)
$privateRoot = New-Item -ItemType Directory -Path (Join-Path $runRoot.FullName "private-data")
$installRoot = New-Item -ItemType Directory -Path (Join-Path $runRoot.FullName "install")
$sitePackages = Join-Path $installRoot.FullName "Lib\site-packages"
$stdoutPath = Join-Path $runRoot.FullName "launcher.log"
$stderrPath = Join-Path $runRoot.FullName "launcher-error.log"
$recordPath = Join-Path $runRoot.FullName "acceptance.json"
$process = $null
$previousPythonPath = $env:PYTHONPATH
$previousSessionToken = $env:GREYTHEORY_SESSION_TOKEN

try {
    if ($PackageWheel) {
        $wheel = Get-Item -LiteralPath $PackageWheel
        $build = [PSCustomObject]@{
            Wheel = $wheel.FullName
            Sha256 = (Get-FileHash -LiteralPath $wheel.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
        }
    } else {
        $build = & (Join-Path $repoRoot "scripts\build-windows-package.ps1") -OutputRoot (Join-Path $runRoot.FullName "package") -PythonCommand $PythonCommand
    }
    & $PythonCommand -m pip install --ignore-installed --no-deps --prefix $installRoot.FullName $build.Wheel | Out-Host
    if ($LASTEXITCODE -ne 0) { throw "Wheel installation failed." }
    $launcher = Join-Path $installRoot.FullName "Scripts\greytheory-workbench.exe"
    if (-not (Test-Path -LiteralPath $launcher -PathType Leaf)) { throw "Installed console launcher is missing." }

    $env:PYTHONPATH = $sitePackages
    & $launcher --help | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "Installed console launcher help failed." }

    $tokenBytes = New-Object byte[] 32
    $tokenGenerator = [Security.Cryptography.RandomNumberGenerator]::Create()
    try { $tokenGenerator.GetBytes($tokenBytes) } finally { $tokenGenerator.Dispose() }
    $sessionToken = [Convert]::ToBase64String($tokenBytes).TrimEnd("=").Replace("+", "-").Replace("/", "_")
    $env:GREYTHEORY_SESSION_TOKEN = $sessionToken
    $process = Start-Process -FilePath $launcher -ArgumentList @(
        "--root", $privateRoot.FullName, "--port", "0", "--session-token-env"
    ) -RedirectStandardOutput $stdoutPath -RedirectStandardError $stderrPath -WindowStyle Hidden -PassThru

    $deadline = (Get-Date).AddSeconds(20)
    $launchText = ""
    while ((Get-Date) -lt $deadline) {
        if ($process.HasExited) { throw "Installed workbench exited before acceptance checks." }
        if (Test-Path -LiteralPath $stdoutPath) {
            $launchText = Get-Content -LiteralPath $stdoutPath -Raw
            if ($launchText -match "GreyTheory local API: (http://127\.0\.0\.1:\d+)" -and $launchText -match "Session token: supplied through process environment \(not echoed\)") { break }
        }
        Start-Sleep -Milliseconds 100
    }
    if ($launchText -notmatch "GreyTheory local API: (http://127\.0\.0\.1:\d+)") { throw "Local API URL was not emitted before the deadline." }
    $baseUrl = $Matches[1]
    $index = Invoke-WebRequest -Uri "$baseUrl/" -TimeoutSec 5 -UseBasicParsing
    $health = Invoke-RestMethod -Uri "$baseUrl/healthz" -TimeoutSec 5
    $headers = @{ Authorization = "Bearer $sessionToken" }
    $snapshot = Invoke-RestMethod -Uri "$baseUrl/api/v1/snapshot" -Headers $headers -TimeoutSec 5

    if ($index.StatusCode -ne 200 -or $index.Content -notmatch "GreyTheory") { throw "Bundled UI did not load from the installed application." }
    if ($health.posture -ne "LOCAL_FIXTURE" -or $health.live_target_available -ne $false) { throw "Health response crossed the local-only posture boundary." }
    if ($snapshot.live_target_available -ne $false) { throw "Snapshot exposed live-target capability." }
    if ($launchText -notmatch "Same-origin graphical commands: available") { throw "Installed launcher did not activate its bundled same-origin UI." }

    $record = [ordered]@{
        accepted = $true
        host = "Windows"
        posture = $health.posture
        live_target_available = $health.live_target_available
        loopback_host = ([uri]$baseUrl).Host
        ui_status = $index.StatusCode
        ui_bundled = $true
        snapshot_authenticated = $true
        launcher_present = $true
        wheel_sha256 = $build.Sha256
        wheel = $build.Wheel
        install_root = $installRoot.FullName
        private_data_root = $privateRoot.FullName
    }
    $record | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $recordPath -Encoding utf8
}
finally {
    if ($process) {
        if (-not $process.HasExited) {
            Stop-Process -Id $process.Id -Force
        }
        [void]$process.WaitForExit(5000)
        $process.Dispose()
    }
    $env:PYTHONPATH = $previousPythonPath
    $env:GREYTHEORY_SESSION_TOKEN = $previousSessionToken
}

if (-not (Test-Path -LiteralPath $recordPath -PathType Leaf)) {
    throw "Windows packaged-workbench acceptance did not produce a record."
}
Get-Content -LiteralPath $recordPath -Raw
