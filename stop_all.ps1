# Root Stopper for LLM + Knowledge Graph Research Assistant
$backendScript = Join-Path $PSScriptRoot "backend\stop_all.ps1"
if (Test-Path $backendScript) {
    & $backendScript
} else {
    Write-Error "Could not find $backendScript"
}
