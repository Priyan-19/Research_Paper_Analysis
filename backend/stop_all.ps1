# PowerShell Script to Stop All Project Services (FastAPI, Streamlit, Docker Databases)

Write-Host "==========================================================" -ForegroundColor Yellow
Write-Host "[+] Stopping LLM + Knowledge Graph Research Assistant System" -ForegroundColor Yellow
Write-Host "==========================================================" -ForegroundColor Yellow

$backendDir = $PSScriptRoot
Set-Location $backendDir

# 1. Stop FastAPI and Streamlit processes running on ports 8000 and 8501
Write-Host "`n[1/2] Stopping FastAPI Server & Streamlit UI processes..." -ForegroundColor Cyan
Get-NetTCPConnection -LocalPort 8501 -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }

# 2. Stop Docker Database Containers (PostgreSQL, Neo4j, Redis)
Write-Host "`n[2/2] Stopping Docker Database Services (PostgreSQL, Neo4j, Redis)..." -ForegroundColor Cyan
docker-compose down

Write-Host "`n==========================================================" -ForegroundColor Green
Write-Host "SUCCESS: All Services Stopped Cleanly!" -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Green
