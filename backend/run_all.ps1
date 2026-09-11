# PowerShell Script to Launch Full Project (Databases + Backend + Streamlit UI)

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "[+] Launching LLM + Knowledge Graph Research Assistant System" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

$backendDir = $PSScriptRoot

# Step 0: Free Ports 8000 and 8501 if previously occupied
Get-NetTCPConnection -LocalPort 8501 -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }

# Step 1: Start Docker Database Services
Write-Host "`n[1/3] Starting Docker Database Services (PostgreSQL, Neo4j, Redis)..." -ForegroundColor Yellow
Set-Location $backendDir
docker-compose up -d postgres neo4j redis

# Step 2: Start FastAPI Backend Server in New Window
Write-Host "`n[2/3] Starting FastAPI Backend API Server on Port 8000..." -ForegroundColor Yellow
$backendCmd = "Set-Location '$backendDir'; .venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendCmd

# Step 3: Start Streamlit Frontend UI in New Window
Write-Host "`n[3/3] Starting Streamlit Web Interface on Port 8501..." -ForegroundColor Yellow
$frontendCmd = "Set-Location '$backendDir'; .venv\Scripts\python.exe -m streamlit run streamlit_app.py --server.port 8501 --server.address 127.0.0.1"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $frontendCmd

Write-Host "`n==========================================================" -ForegroundColor Green
Write-Host "SUCCESS: All Project Components Launched!" -ForegroundColor Green
Write-Host "  * Streamlit Web UI:   http://localhost:8501" -ForegroundColor Cyan
Write-Host "  * FastAPI REST Docs:  http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "  * Neo4j Browser:      http://localhost:7474" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Green
