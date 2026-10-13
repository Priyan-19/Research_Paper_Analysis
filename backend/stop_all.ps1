# PowerShell Script to Stop All Project Services (FastAPI, Streamlit, Docker Databases)

Write-Host "==========================================================" -ForegroundColor Yellow
Write-Host "[+] Stopping LLM + Knowledge Graph Research Assistant System" -ForegroundColor Yellow
Write-Host "==========================================================" -ForegroundColor Yellow

$backendDir = $PSScriptRoot
Set-Location $backendDir

# 1. Stop FastAPI and Streamlit processes running on ports 8001 and 8502
Write-Host "`n[1/2] Stopping FastAPI Server & Streamlit UI processes..." -ForegroundColor Cyan
Get-NetTCPConnection -LocalPort 8502, 8001 -ErrorAction SilentlyContinue | ForEach-Object {
    $proc = Get-Process -Id $_.OwningProcess -ErrorAction SilentlyContinue
    if ($proc -and $proc.ProcessName -notlike "*docker*" -and $proc.ProcessName -notlike "*vpnkit*") {
        Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
    }
}

# 2. Stop Docker Database Containers (PostgreSQL, Neo4j, Redis)
Write-Host "`n[2/2] Stopping Docker Database Services (PostgreSQL, Neo4j, Redis)..." -ForegroundColor Cyan
docker-compose down

Write-Host "`n==========================================================" -ForegroundColor Green
Write-Host "SUCCESS: All Services Stopped Cleanly!" -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Green
