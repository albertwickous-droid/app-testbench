[CmdletBinding()]
param([switch]$Force)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest
$ProgressPreference = "SilentlyContinue"

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$AssetDir = Join-Path $RepoRoot "runs\case-assets\vlc-http-playback"
$ApkPath = Join-Path $AssetDir "org.videolan.vlc_13070208.apk"
$VideoPath = Join-Path $AssetDir "sintel-trailer.mp4"
$ApkUrl = "https://f-droid.org/repo/org.videolan.vlc_13070208.apk"
$VideoUrl = "https://media.w3.org/2010/05/sintel/trailer.mp4"
$ApkHash = "727693d59c4d678c046386812a103209a25423460c9d22e38e12460f12402ab6"
$VideoHash = "b670602fa00934ca27c4351bb0efe7ea7a07fae57284e44226025eeed7c51254"

New-Item -ItemType Directory -Force -Path $AssetDir | Out-Null

function Ensure-Asset {
    param(
        [string]$Path,
        [string]$Uri,
        [string]$ExpectedHash
    )
    if (Test-Path -LiteralPath $Path) {
        $currentHash = (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
        if ($currentHash -eq $ExpectedHash) { return }
        if (-not $Force) {
            throw "Asset hash mismatch at $Path. Re-run with -Force to replace only this pinned test asset."
        }
        Remove-Item -LiteralPath $Path -Force
    }
    $tempPath = "$Path.download"
    if (Test-Path -LiteralPath $tempPath) { Remove-Item -LiteralPath $tempPath -Force }
    try {
        Invoke-WebRequest -Uri $Uri -OutFile $tempPath
        $downloadedHash = (Get-FileHash -LiteralPath $tempPath -Algorithm SHA256).Hash.ToLowerInvariant()
        if ($downloadedHash -ne $ExpectedHash) {
            throw "Downloaded asset SHA256 mismatch. Expected $ExpectedHash, got $downloadedHash."
        }
        Move-Item -LiteralPath $tempPath -Destination $Path
    }
    finally {
        if (Test-Path -LiteralPath $tempPath) { Remove-Item -LiteralPath $tempPath -Force }
    }
}

Ensure-Asset -Path $ApkPath -Uri $ApkUrl -ExpectedHash $ApkHash
Ensure-Asset -Path $VideoPath -Uri $VideoUrl -ExpectedHash $VideoHash
Write-Output ("{0}|{1}" -f $ApkPath, $VideoPath)
