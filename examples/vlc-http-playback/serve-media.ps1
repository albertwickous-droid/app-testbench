[CmdletBinding()]
param([int]$Port = 18766)

$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$VenvPython = Join-Path $RepoRoot ".venv\Scripts\python.exe"
$Python = if (Test-Path -LiteralPath $VenvPython) { $VenvPython } else { "python" }
$AssetDir = Join-Path $RepoRoot "runs\case-assets\vlc-http-playback"

& $Python (Join-Path $PSScriptRoot "range_server.py") `
    --directory $AssetDir --bind 127.0.0.1 --port $Port
