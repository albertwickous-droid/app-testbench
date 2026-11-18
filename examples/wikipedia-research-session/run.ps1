[CmdletBinding()]
param(
    [string]$Output = "",
    [string]$ApkPath = "",
    [switch]$SkipPrepare
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest
$ProgressPreference = "SilentlyContinue"

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$VenvPython = Join-Path $RepoRoot ".venv\Scripts\python.exe"
$Python = if (Test-Path -LiteralPath $VenvPython) { $VenvPython } else { "python" }
if (-not $ApkPath) { $ApkPath = Join-Path $RepoRoot "runs\case-assets\wikipedia\org.wikipedia_50616.apk" }
$FlowPath = Join-Path $PSScriptRoot "flow.yaml"

if (-not $Output) {
    $Output = Join-Path $RepoRoot "runs\examples\wikipedia-research-session"
}
New-Item -ItemType Directory -Force -Path $Output | Out-Null

if (-not $SkipPrepare) {
    $ApkPath = (& (Join-Path $PSScriptRoot "fetch-apk.ps1") | Select-Object -Last 1).Trim()
}
elseif (-not (Test-Path -LiteralPath $ApkPath)) {
    throw "Pinned Wikipedia APK is missing. Run fetch-apk.ps1 or omit -SkipPrepare."
}

$env:PYTHONPATH = (Join-Path $RepoRoot "src")
$env:PYTHONUTF8 = "1"
$env:WIKIPEDIA_APK = $ApkPath
try {
    & $Python -m app_testbench doctor --json
    if ($LASTEXITCODE -ne 0) { throw "app-testbench doctor failed with exit code $LASTEXITCODE." }

    & $Python -m app_testbench run $FlowPath `
        --output $Output `
        --junit-xml (Join-Path $Output "junit.xml") `
        --wait-for-boot --boot-timeout 60
    if ($LASTEXITCODE -ne 0) {
        throw "Wikipedia flow failed with exit code $LASTEXITCODE. Inspect $Output."
    }
}
finally {
    Remove-Item Env:WIKIPEDIA_APK -ErrorAction SilentlyContinue
    Remove-Item Env:PYTHONPATH -ErrorAction SilentlyContinue
    Remove-Item Env:PYTHONUTF8 -ErrorAction SilentlyContinue
}

Write-Host "Evidence written to $Output"
