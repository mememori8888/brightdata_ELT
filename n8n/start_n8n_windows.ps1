param(
  [Parameter(Mandatory = $true)]
  [string]$DataRoot,

  [string]$StorageState = ""
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$resolvedDataRoot = (Resolve-Path -LiteralPath $DataRoot).Path

if (-not (Test-Path -LiteralPath (Join-Path $resolvedDataRoot "results"))) {
  throw "DataRoot must contain results/: $resolvedDataRoot"
}

if ([string]::IsNullOrWhiteSpace($StorageState)) {
  $StorageState = Join-Path $repoRoot "n8n\.secrets\google-maps-storage-state.json"
}
if (Test-Path -LiteralPath $StorageState) {
  $resolvedStorageState = (Resolve-Path -LiteralPath $StorageState).Path
} else {
  $resolvedStorageState = [IO.Path]::GetFullPath($StorageState)
  Write-Warning "Google login state does not exist yet. Import and run the semi-manual profile workflow with Codex: $resolvedStorageState"
}

if (-not (Get-Command npx -ErrorAction SilentlyContinue)) {
  throw "npx is not available. Install Node.js first: https://nodejs.org/"
}

$env:N8N_USER_FOLDER = Join-Path $repoRoot "n8n\.n8n-user"
$env:N8N_SECURE_COOKIE = "false"
$env:N8N_DIAGNOSTICS_ENABLED = "false"
$env:N8N_PERSONALIZATION_ENABLED = "false"
$env:N8N_BLOCK_ENV_ACCESS_IN_NODE = "false"
$env:BRIGHTDATA_ELT_ROOT = $repoRoot
$env:BRIGHTDATA_ELT_DATA_ROOT = $resolvedDataRoot
$env:GOOGLE_MAPS_STORAGE_STATE = $resolvedStorageState

New-Item -ItemType Directory -Force -Path $env:N8N_USER_FOLDER | Out-Null

Write-Host "Starting n8n..."
Write-Host "Open: http://localhost:5678"
Write-Host "Data root: $resolvedDataRoot"
Write-Host "Import workflow: $(Join-Path $repoRoot 'n8n\google_reviews_local_relevance_workflow.json')"

Set-Location -LiteralPath $repoRoot
npx n8n start
