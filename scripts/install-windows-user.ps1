[CmdletBinding()]
param(
    [string]$PackageWheel,
    [string]$PythonCommand = "python",
    [string]$InstallRoot = (Join-Path $env:LOCALAPPDATA "Programs\GreyTheory"),
    [string]$DataRoot = (Join-Path $env:LOCALAPPDATA "GreyTheory"),
    [string]$ShortcutRoot = (Join-Path $env:APPDATA "Microsoft\Windows\Start Menu\Programs\GreyTheory"),
    [ValidateRange(1, 65535)]
    [int]$Port = 8765
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Resolve-AbsolutePath {
    param([Parameter(Mandatory)][string]$Path)
    return [IO.Path]::GetFullPath($Path)
}

function Assert-UserWritableTarget {
    param(
        [Parameter(Mandatory)][string]$Path,
        [Parameter(Mandatory)][string]$Name
    )
    $root = [IO.Path]::GetPathRoot($Path)
    if (-not $root -or $Path.TrimEnd('\') -eq $root.TrimEnd('\')) {
        throw "$Name must be a bounded directory, not a drive root."
    }
    if ($Path -match '^[A-Za-z]:\\(?:Windows|Program Files(?: \(x86\))?)(?:\\|$)') {
        throw "$Name must be a current-user location, not a system-managed directory."
    }
}

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$installPath = Resolve-AbsolutePath $InstallRoot
$dataPath = Resolve-AbsolutePath $DataRoot
$shortcutPath = Resolve-AbsolutePath $ShortcutRoot
Assert-UserWritableTarget $installPath "InstallRoot"
Assert-UserWritableTarget $dataPath "DataRoot"
Assert-UserWritableTarget $shortcutPath "ShortcutRoot"

$manifestPath = Join-Path $installPath "install-manifest.json"
$existingManifest = Test-Path -LiteralPath $manifestPath -PathType Leaf
$existingData = Test-Path -LiteralPath $dataPath -PathType Container
if ((Test-Path -LiteralPath $installPath -PathType Container) -and -not $existingManifest) {
    $existingEntries = @(Get-ChildItem -LiteralPath $installPath -Force -ErrorAction Stop)
    if ($existingEntries.Count -gt 0) {
        throw "InstallRoot is non-empty but is not a GreyTheory user installation."
    }
}

if ($PackageWheel) {
    $wheel = Get-Item -LiteralPath $PackageWheel
    $build = [PSCustomObject]@{
        Wheel = $wheel.FullName
        Sha256 = (Get-FileHash -LiteralPath $wheel.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
    }
} else {
    $build = & (Join-Path $repoRoot "scripts\build-windows-package.ps1") `
        -PythonCommand $PythonCommand
}

New-Item -ItemType Directory -Path $installPath -Force | Out-Null
New-Item -ItemType Directory -Path $dataPath -Force | Out-Null
New-Item -ItemType Directory -Path $shortcutPath -Force | Out-Null

$venvRoot = Join-Path $installPath "runtime"
$venvPython = Join-Path $venvRoot "Scripts\python.exe"
if (-not (Test-Path -LiteralPath $venvPython -PathType Leaf)) {
    & $PythonCommand -m venv $venvRoot
    if ($LASTEXITCODE -ne 0) { throw "GreyTheory user runtime creation failed." }
}

& $venvPython -m pip install --disable-pip-version-check --no-deps --force-reinstall $build.Wheel | Out-Host
if ($LASTEXITCODE -ne 0) { throw "GreyTheory wheel installation failed." }

$launcher = Join-Path $venvRoot "Scripts\greytheory-workbench.exe"
if (-not (Test-Path -LiteralPath $launcher -PathType Leaf)) {
    throw "The installed GreyTheory workbench launcher is missing."
}
$version = (& $venvPython -c "import importlib.metadata as m; print(m.version('greytheory'))").Trim()
if ($LASTEXITCODE -ne 0 -or -not $version) { throw "The installed GreyTheory version could not be read." }

$escapedDataPath = $dataPath.Replace("'", "''")
$launchScript = Join-Path $installPath "Launch-GreyTheory.ps1"
@"
[CmdletBinding()]
param(
    [switch]`$NoBrowser,
    [switch]`$SessionTokenFromEnvironment
)
`$ErrorActionPreference = "Stop"
`$workbench = Join-Path `$PSScriptRoot "runtime\Scripts\greytheory-workbench.exe"
`$arguments = @("--root", '$escapedDataPath', "--port", "$Port")
if (`$SessionTokenFromEnvironment) { `$arguments += "--session-token-env" }
`$browserJob = `$null
if (-not `$NoBrowser) {
    `$browserJob = Start-Job -ScriptBlock {
        param([string]`$HealthUrl, [string]`$WorkbenchUrl)
        `$deadline = (Get-Date).AddSeconds(30)
        while ((Get-Date) -lt `$deadline) {
            try {
                `$health = Invoke-RestMethod -Uri `$HealthUrl -TimeoutSec 1
                if (`$health.posture -eq "LOCAL_FIXTURE" -and `$health.live_target_available -eq `$false) {
                    Start-Process `$WorkbenchUrl
                    return
                }
            } catch {
                Start-Sleep -Milliseconds 150
            }
        }
    } -ArgumentList "http://127.0.0.1:$Port/healthz", "http://127.0.0.1:$Port/"
}
try {
    & `$workbench @arguments
    exit `$LASTEXITCODE
} finally {
    if (`$browserJob) {
        Stop-Job -Job `$browserJob -ErrorAction SilentlyContinue
        Remove-Job -Job `$browserJob -Force -ErrorAction SilentlyContinue
    }
}
"@ | Set-Content -LiteralPath $launchScript -Encoding utf8

$powershell = (Get-Command powershell.exe -ErrorAction Stop).Source

$shortcutFile = Join-Path $shortcutPath "GreyTheory Research Preview.lnk"
$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($shortcutFile)
$shortcut.TargetPath = $powershell
$shortcut.Arguments = '-NoLogo -NoProfile -ExecutionPolicy Bypass -File "{0}"' -f $launchScript
$shortcut.WorkingDirectory = $installPath
$shortcut.Description = "Open the GreyTheory LOCAL_FIXTURE research workbench"
$shortcut.IconLocation = "$powershell,0"
$shortcut.Save()
if (-not (Test-Path -LiteralPath $shortcutFile -PathType Leaf)) {
    throw "The GreyTheory current-user shortcut was not created."
}

$installMode = if ($existingManifest) { "upgrade" } elseif ($existingData) { "recovery" } else { "fresh" }
$manifest = [ordered]@{
    schema_version = "greytheory-user-install-v1"
    product = "GreyTheory"
    version = $version
    installed_at = (Get-Date).ToUniversalTime().ToString("o")
    install_mode = $installMode
    posture = "LOCAL_FIXTURE"
    live_target_available = $false
    wheel_sha256 = $build.Sha256
    install_root = $installPath
    data_root = $dataPath
    shortcut = $shortcutFile
    launcher = $launchScript
    runtime_launcher = $launcher
    port = $Port
}
$temporaryManifest = "$manifestPath.tmp-$PID"
$manifest | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $temporaryManifest -Encoding utf8
Move-Item -LiteralPath $temporaryManifest -Destination $manifestPath -Force

[PSCustomObject]$manifest
