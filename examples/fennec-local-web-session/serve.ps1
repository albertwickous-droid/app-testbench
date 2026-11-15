[CmdletBinding()]
param([int]$Port = 18765)

$ErrorActionPreference = "Stop"
$SitePath = Join-Path $PSScriptRoot "site"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$VenvPython = Join-Path $RepoRoot ".venv\Scripts\python.exe"
$Python = if (Test-Path -LiteralPath $VenvPython) { $VenvPython } else { "python" }

& $Python -m http.server $Port --bind 127.0.0.1 --directory $SitePath
