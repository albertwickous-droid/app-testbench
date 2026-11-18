[CmdletBinding()]
param([switch]$Force)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest
$ProgressPreference = "SilentlyContinue"

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$AssetDir = Join-Path $RepoRoot "runs\case-assets\wikipedia"
$ApkPath = Join-Path $AssetDir "org.wikipedia_50616.apk"
$DownloadUrl = "https://f-droid.org/repo/org.wikipedia_50616.apk"
$ExpectedHash = "d225e5d08fe461f12fa0af7b617e6e715f3112986165c34e0572a1a056129dd1"
$ExpectedSize = 104747428

New-Item -ItemType Directory -Force -Path $AssetDir | Out-Null

if (Test-Path -LiteralPath $ApkPath) {
    $item = Get-Item -LiteralPath $ApkPath
    $currentHash = (Get-FileHash -LiteralPath $ApkPath -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($item.Length -eq $ExpectedSize -and $currentHash -eq $ExpectedHash) {
        Write-Output $ApkPath
        return
    }
    if (-not $Force) {
        throw "APK mismatch at $ApkPath. Re-run with -Force to replace only this pinned asset."
    }
    Remove-Item -LiteralPath $ApkPath -Force
}

$TempPath = "$ApkPath.download"
if (Test-Path -LiteralPath $TempPath) { Remove-Item -LiteralPath $TempPath -Force }

try {
    Invoke-WebRequest -Uri $DownloadUrl -OutFile $TempPath
    $downloaded = Get-Item -LiteralPath $TempPath
    $downloadedHash = (Get-FileHash -LiteralPath $TempPath -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($downloaded.Length -ne $ExpectedSize) {
        throw "Downloaded APK size mismatch. Expected $ExpectedSize bytes, got $($downloaded.Length)."
    }
    if ($downloadedHash -ne $ExpectedHash) {
        throw "Downloaded APK SHA256 mismatch. Expected $ExpectedHash, got $downloadedHash."
    }
    Move-Item -LiteralPath $TempPath -Destination $ApkPath
}
finally {
    if (Test-Path -LiteralPath $TempPath) { Remove-Item -LiteralPath $TempPath -Force }
}

Write-Output $ApkPath
