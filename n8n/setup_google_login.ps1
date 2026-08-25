param(
  [string]$StorageState = "",
  [int]$WaitSeconds = 0,
  [switch]$CodexAssisted
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)

if (-not $CodexAssisted) {
  throw "This operation requires an active Codex-assisted session. Re-run with -CodexAssisted after Codex confirms the procedure."
}
if ($WaitSeconds -lt 0 -or $WaitSeconds -gt 1800) {
  throw "WaitSeconds must be between 0 and 1800."
}

if ([string]::IsNullOrWhiteSpace($StorageState)) {
  $StorageState = Join-Path $repoRoot "n8n\.secrets\google-maps-storage-state.json"
}

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
  throw "python is not available. Install Python 3.11 or later first."
}

$stateDirectory = Split-Path -Parent $StorageState
New-Item -ItemType Directory -Force -Path $stateDirectory | Out-Null

Set-Location -LiteralPath $repoRoot
python -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) { throw "Failed to install Python requirements." }
python -m pip install playwright
if ($LASTEXITCODE -ne 0) { throw "Failed to install Playwright." }
python -m playwright install chromium
if ($LASTEXITCODE -ne 0) { throw "Failed to install Playwright Chromium." }

$arguments = @(
  "scripts\enrich_review_relevance_ranks_state.py",
  "--storage-state", $StorageState,
  "--login-only"
)
if ($WaitSeconds -gt 0) {
  Write-Host "A Chromium window will open. Sign in to Google within $WaitSeconds seconds."
  $arguments += @("--login-wait-seconds", $WaitSeconds)
} else {
  Write-Host "A Chromium window will open. Sign in to Google, return here, and press Enter."
}
python @arguments
if ($LASTEXITCODE -ne 0) { throw "Google login state was not created." }

Write-Host "Google login state saved: $StorageState"
Write-Host "This file contains authentication data. Do not commit or share it."
