# Root Launcher for LLM + Knowledge Graph Research Assistant
$backendScript = Join-Path $PSScriptRoot "backend\run_all.ps1"
if (Test-Path $backendScript) {
    & $backendScript
} else {
    Write-Error "Could not find $backendScript"
}
