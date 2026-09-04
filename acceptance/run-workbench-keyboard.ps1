[CmdletBinding()]
param(
    [string]$BaseUrl = "",
    [string]$EvidenceRoot = "",
    [string]$VisualQaRoot = ""
)

$ErrorActionPreference = "Stop"
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$uiRoot = Join-Path $repoRoot "workbench_ui"
$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
if (-not $EvidenceRoot) {
    $EvidenceRoot = "E:\Projects\GreyTheory\acceptance\workbench-keyboard-$stamp-$PID"
}
if (-not $VisualQaRoot) {
    $VisualQaRoot = "E:\Visual QA\GreyTheory Visual QA\Current Reviews\$(Get-Date -Format 'yyyy-MM-dd')-whole-app-keyboard"
}
New-Item -ItemType Directory -Force -Path $EvidenceRoot, $VisualQaRoot | Out-Null

$bundledNodeRoot = Join-Path $env:USERPROFILE ".cache\codex-runtimes\codex-primary-runtime\dependencies\node"
$nodeCommand = Get-Command node.exe -ErrorAction SilentlyContinue
$nodeExe = if ($nodeCommand) { $nodeCommand.Source } else { Join-Path $bundledNodeRoot "bin\node.exe" }
if (-not (Test-Path -LiteralPath $nodeExe)) { throw "Node.js was not found." }

$npmCli = Join-Path $bundledNodeRoot "node_modules\npm\bin\npm-cli.js"
if (-not (Test-Path -LiteralPath $npmCli)) {
    $npmCommand = Get-Command npm.cmd -ErrorAction SilentlyContinue
    if (-not $npmCommand) { throw "npm was not found." }
    $npmCli = $npmCommand.Source
}

$playwrightCandidates = @(
    (Join-Path $uiRoot "node_modules"),
    $env:NODE_PATH,
    (Join-Path $bundledNodeRoot "node_modules")
) | Where-Object { $_ -and (Test-Path -LiteralPath (Join-Path $_ "playwright")) }
if (-not $playwrightCandidates) {
    throw "Playwright was not found. Install it for the workbench or set NODE_PATH to a node_modules directory containing Playwright."
}
$playwrightRoot = @($playwrightCandidates)[0]

$ownedPreview = $null
$previousNodePath = $env:NODE_PATH
try {
    if (-not $BaseUrl) {
        Push-Location $uiRoot
        try {
            if ($npmCli.EndsWith(".js")) { & $nodeExe $npmCli run build }
            else { & $npmCli run build }
            if ($LASTEXITCODE -ne 0) { throw "The workbench build failed with exit code $LASTEXITCODE." }
        } finally {
            Pop-Location
        }

        $listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Loopback, 0)
        $listener.Start()
        $port = ([System.Net.IPEndPoint]$listener.LocalEndpoint).Port
        $listener.Stop()
        $BaseUrl = "http://127.0.0.1:$port/"

        $viteScript = Join-Path $uiRoot "node_modules\vite\bin\vite.js"
        if (-not (Test-Path -LiteralPath $viteScript)) { throw "The local Vite runtime was not found." }
        $stdoutPath = Join-Path $EvidenceRoot "preview.stdout.log"
        $stderrPath = Join-Path $EvidenceRoot "preview.stderr.log"
        $ownedPreview = Start-Process -FilePath $nodeExe -ArgumentList @($viteScript, "preview", "--host", "127.0.0.1", "--port", "$port", "--strictPort") -WorkingDirectory $uiRoot -WindowStyle Hidden -RedirectStandardOutput $stdoutPath -RedirectStandardError $stderrPath -PassThru

        $ready = $false
        for ($attempt = 0; $attempt -lt 40; $attempt += 1) {
            if ($ownedPreview.HasExited) { throw "The owned Vite preview exited before it became ready." }
            try {
                $response = Invoke-WebRequest -UseBasicParsing -Uri $BaseUrl -TimeoutSec 2
                if ($response.StatusCode -eq 200) { $ready = $true; break }
            } catch {
                Start-Sleep -Milliseconds 250
            }
        }
        if (-not $ready) { throw "The owned Vite preview did not become ready at $BaseUrl." }
    }

    $env:NODE_PATH = $playwrightRoot
    $harness = Join-Path $PSScriptRoot "run-workbench-keyboard.cjs"
    & $nodeExe $harness --base-url $BaseUrl --evidence-dir $EvidenceRoot --screenshot-dir $VisualQaRoot
    if ($LASTEXITCODE -ne 0) { throw "Keyboard acceptance failed. See $(Join-Path $EvidenceRoot 'acceptance.json')." }
    Write-Output (Join-Path $EvidenceRoot "acceptance.json")
} finally {
    $env:NODE_PATH = $previousNodePath
    if ($ownedPreview -and -not $ownedPreview.HasExited) {
        Stop-Process -Id $ownedPreview.Id -Force
        $ownedPreview.WaitForExit()
    }
}
