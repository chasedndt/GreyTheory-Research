[CmdletBinding()]
param(
    [string]$OutputRoot = "E:\Projects\GreyTheory\acceptance",
    [string]$PythonCommand = "python",
    [string]$PackageWheel
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function New-SessionToken {
    $bytes = New-Object byte[] 32
    $generator = [Security.Cryptography.RandomNumberGenerator]::Create()
    try { $generator.GetBytes($bytes) } finally { $generator.Dispose() }
    return [Convert]::ToBase64String($bytes).TrimEnd("=").Replace("+", "-").Replace("/", "_")
}

function Get-FreeLoopbackPort {
    $listener = [Net.Sockets.TcpListener]::new([Net.IPAddress]::Loopback, 0)
    $listener.Start()
    try { return ([Net.IPEndPoint]$listener.LocalEndpoint).Port } finally { $listener.Stop() }
}

function Start-AcceptanceWorkbench {
    param(
        [Parameter(Mandatory)][string]$PowerShell,
        [Parameter(Mandatory)][string]$LaunchScript,
        [Parameter(Mandatory)][int]$Port,
        [Parameter(Mandatory)][string]$LogLabel,
        [Parameter(Mandatory)][string]$RunRoot
    )
    $stdout = Join-Path $RunRoot "$LogLabel.log"
    $stderr = Join-Path $RunRoot "$LogLabel-error.log"
    $token = New-SessionToken
    $previousToken = $env:GREYTHEORY_SESSION_TOKEN
    try {
        $env:GREYTHEORY_SESSION_TOKEN = $token
        $process = Start-Process -FilePath $PowerShell -ArgumentList @(
            "-NoLogo", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $LaunchScript,
            "-NoBrowser", "-SessionTokenFromEnvironment"
        ) -RedirectStandardOutput $stdout -RedirectStandardError $stderr -WindowStyle Hidden -PassThru
    } finally {
        $env:GREYTHEORY_SESSION_TOKEN = $previousToken
    }

    $baseUrl = "http://127.0.0.1:$Port"
    $deadline = (Get-Date).AddSeconds(25)
    while ((Get-Date) -lt $deadline) {
        if ($process.HasExited) { throw "Installed workbench exited during $LogLabel startup." }
        try {
            $health = Invoke-RestMethod -Uri "$baseUrl/healthz" -TimeoutSec 1
            if ($health.posture -eq "LOCAL_FIXTURE") {
                $child = Get-CimInstance Win32_Process -Filter "ParentProcessId = $($process.Id)" |
                    Where-Object { $_.Name -eq "greytheory-workbench.exe" } |
                    Select-Object -First 1
                if (-not $child) {
                    throw "The installed launch script did not retain an owned workbench child."
                }
                return [PSCustomObject]@{
                    Process = $process
                    WorkbenchProcess = Get-Process -Id $child.ProcessId
                    Token = $token
                    BaseUrl = $baseUrl
                    Stdout = $stdout
                    Stderr = $stderr
                }
            }
        } catch {
            Start-Sleep -Milliseconds 100
        }
    }
    $children = Get-CimInstance Win32_Process -Filter "ParentProcessId = $($process.Id)" -ErrorAction SilentlyContinue
    foreach ($child in $children) { Stop-Process -Id $child.ProcessId -Force -ErrorAction SilentlyContinue }
    if (-not $process.HasExited) { Stop-Process -Id $process.Id -Force }
    throw "Installed workbench did not become healthy during $LogLabel startup."
}

function Stop-AcceptanceWorkbench {
    param([Parameter(Mandatory)]$Runtime)
    if ($Runtime.WorkbenchProcess -and -not $Runtime.WorkbenchProcess.HasExited) {
        Stop-Process -Id $Runtime.WorkbenchProcess.Id -Force
        [void]$Runtime.WorkbenchProcess.WaitForExit(5000)
    }
    if (-not $Runtime.Process.HasExited) { Stop-Process -Id $Runtime.Process.Id -Force }
    [void]$Runtime.Process.WaitForExit(5000)
    if ($Runtime.WorkbenchProcess) { $Runtime.WorkbenchProcess.Dispose() }
    $Runtime.Process.Dispose()
}

function Get-AuthenticatedSnapshot {
    param([Parameter(Mandatory)]$Runtime)
    return Invoke-RestMethod -Uri "$($Runtime.BaseUrl)/api/v1/snapshot" `
        -Headers @{ Authorization = "Bearer $($Runtime.Token)" } -TimeoutSec 5
}

function Assert-JourneyPersisted {
    param(
        [Parameter(Mandatory)]$Runtime,
        [Parameter(Mandatory)][string]$JourneyId,
        [Parameter(Mandatory)][string]$Stage
    )
    $snapshot = Get-AuthenticatedSnapshot $Runtime
    if ($snapshot.posture -ne "LOCAL_FIXTURE" -or $snapshot.live_target_available -ne $false) {
        throw "$Stage crossed the local-only posture boundary."
    }
    if (($snapshot | ConvertTo-Json -Depth 30) -notmatch [regex]::Escape($JourneyId)) {
        throw "$Stage did not retain the accepted learning journey."
    }
}

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$runName = "windows-user-install-{0}-{1}" -f (Get-Date -Format "yyyyMMdd-HHmmss"), $PID
New-Item -ItemType Directory -Path $OutputRoot -Force | Out-Null
$runRoot = New-Item -ItemType Directory -Path (Join-Path $OutputRoot $runName)
$installRoot = Join-Path $runRoot.FullName "user-install"
$dataRoot = Join-Path $runRoot.FullName "user-data"
$shortcutRoot = Join-Path $runRoot.FullName "start-menu"
$recordPath = Join-Path $runRoot.FullName "acceptance.json"
$runtime = $null

if ($PackageWheel) {
    $wheel = Get-Item -LiteralPath $PackageWheel
    $build = [PSCustomObject]@{
        Wheel = $wheel.FullName
        Sha256 = (Get-FileHash -LiteralPath $wheel.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
    }
} else {
    $build = & (Join-Path $repoRoot "scripts\build-windows-package.ps1") `
        -OutputRoot (Join-Path $runRoot.FullName "package") -PythonCommand $PythonCommand
}
$port = Get-FreeLoopbackPort
$installer = Join-Path $repoRoot "scripts\install-windows-user.ps1"
$journeyId = "acceptance-install-{0}" -f ([guid]::NewGuid().ToString("N"))

try {
    $fresh = & $installer -PackageWheel $build.Wheel -PythonCommand $PythonCommand `
        -InstallRoot $installRoot -DataRoot $dataRoot -ShortcutRoot $shortcutRoot -Port $port
    if ($fresh.install_mode -ne "fresh") { throw "Initial installation was not recorded as fresh." }
    if ($fresh.posture -ne "LOCAL_FIXTURE" -or $fresh.live_target_available -ne $false) {
        throw "Installer manifest crossed the local-only posture boundary."
    }

    $shell = New-Object -ComObject WScript.Shell
    $shortcut = $shell.CreateShortcut($fresh.shortcut)
    if ([IO.Path]::GetFileName($shortcut.TargetPath) -ne "powershell.exe") {
        throw "Shortcut target is not the bounded Windows user launcher."
    }
    if ($shortcut.Arguments -notmatch [regex]::Escape($fresh.launcher)) {
        throw "Shortcut does not bind the installed GreyTheory launch script."
    }

    $runtime = Start-AcceptanceWorkbench -PowerShell $shortcut.TargetPath -LaunchScript $fresh.launcher `
        -Port $port -LogLabel "fresh-launch" -RunRoot $runRoot.FullName
    $index = Invoke-WebRequest -Uri "$($runtime.BaseUrl)/" -TimeoutSec 5 -UseBasicParsing
    if ($index.StatusCode -ne 200 -or $index.Content -notmatch "GreyTheory") {
        throw "The shortcut-target application did not serve its bundled UI."
    }
    $commandId = "start-{0}" -f ([guid]::NewGuid().ToString("N"))
    $command = [ordered]@{
        schema_version = "greytheory.workbench.v1"
        id = $commandId
        kind = "start_learning_journey"
        operator_ref = "operator-local"
        issued_at = (Get-Date).ToUniversalTime().ToString("o")
        idempotency_key = $commandId
        workspace_id = $null
        expected_revision = $null
        requested_authority = "NONE"
        human_acknowledged = $false
        fields = @{ journey_id = $journeyId }
        executable = $false
    }
    $result = Invoke-RestMethod -Uri "$($runtime.BaseUrl)/api/v1/commands" -Method Post `
        -Headers @{ Authorization = "Bearer $($runtime.Token)"; Origin = $runtime.BaseUrl } `
        -ContentType "application/json" -Body ($command | ConvertTo-Json -Depth 6) -TimeoutSec 5
    if ($result.disposition -ne "accepted" -or $result.executed -ne $false) {
        throw "The installed application did not accept the bounded learning command."
    }
    Assert-JourneyPersisted -Runtime $runtime -JourneyId $journeyId -Stage "fresh launch"
    Stop-AcceptanceWorkbench $runtime
    $runtime = $null

    $runtime = Start-AcceptanceWorkbench -PowerShell $shortcut.TargetPath -LaunchScript $fresh.launcher `
        -Port $port -LogLabel "restart" -RunRoot $runRoot.FullName
    Assert-JourneyPersisted -Runtime $runtime -JourneyId $journeyId -Stage "restart"
    Stop-AcceptanceWorkbench $runtime
    $runtime = $null

    $upgrade = & $installer -PackageWheel $build.Wheel -PythonCommand $PythonCommand `
        -InstallRoot $installRoot -DataRoot $dataRoot -ShortcutRoot $shortcutRoot -Port $port
    if ($upgrade.install_mode -ne "upgrade") { throw "Reinstallation was not recorded as an upgrade." }
    $runtime = Start-AcceptanceWorkbench -PowerShell $shortcut.TargetPath -LaunchScript $upgrade.launcher `
        -Port $port -LogLabel "upgrade" -RunRoot $runRoot.FullName
    Assert-JourneyPersisted -Runtime $runtime -JourneyId $journeyId -Stage "upgrade"
    Stop-AcceptanceWorkbench $runtime
    $runtime = $null

    $archiveRoot = Join-Path $runRoot.FullName "replaced-user-install"
    $resolvedInstall = [IO.Path]::GetFullPath($installRoot)
    $resolvedRun = [IO.Path]::GetFullPath($runRoot.FullName).TrimEnd('\') + '\'
    if (-not $resolvedInstall.StartsWith($resolvedRun, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Recovery move target escaped the bounded acceptance directory."
    }
    Move-Item -LiteralPath $resolvedInstall -Destination $archiveRoot
    $recovery = & $installer -PackageWheel $build.Wheel -PythonCommand $PythonCommand `
        -InstallRoot $installRoot -DataRoot $dataRoot -ShortcutRoot $shortcutRoot -Port $port
    if ($recovery.install_mode -ne "recovery") { throw "Runtime replacement was not recorded as recovery." }
    $recoveryShortcut = $shell.CreateShortcut($recovery.shortcut)
    $runtime = Start-AcceptanceWorkbench -PowerShell $recoveryShortcut.TargetPath -LaunchScript $recovery.launcher `
        -Port $port -LogLabel "recovery" -RunRoot $runRoot.FullName
    Assert-JourneyPersisted -Runtime $runtime -JourneyId $journeyId -Stage "recovery"

    $record = [ordered]@{
        accepted = $true
        host = "Windows"
        account_scope = "current_user_isolated_paths"
        separate_user_accepted = $false
        posture = "LOCAL_FIXTURE"
        live_target_available = $false
        bundled_ui = $true
        shortcut_created = $true
        shortcut_target_launch_checked = $true
        automatic_browser_open_configured = $true
        persisted_journey_restart = $true
        persisted_journey_upgrade = $true
        persisted_journey_recovery = $true
        signed_installer = $false
        wheel_sha256 = $build.Sha256
        wheel = $build.Wheel
        install_root = $installRoot
        archived_runtime = $archiveRoot
        private_data_root = $dataRoot
        shortcut = $recovery.shortcut
        journey_id = $journeyId
    }
    $record | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $recordPath -Encoding utf8
} finally {
    if ($runtime) { Stop-AcceptanceWorkbench $runtime }
}

if (-not (Test-Path -LiteralPath $recordPath -PathType Leaf)) {
    throw "Windows user-install acceptance did not produce a record."
}
Get-Content -LiteralPath $recordPath -Raw
