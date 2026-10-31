# PowerShell Script to Launch Full Project (Databases + FastAPI Backend + React Web UI)

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "[+] Launching LLM + Knowledge Graph Research Assistant System" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

$backendDir = $PSScriptRoot

# Step 0: Free Ports 5173, 8000, and 8001 (only killing python/node processes, ignoring Docker)
Get-NetTCPConnection -LocalPort 5173, 8000, 8001 -ErrorAction SilentlyContinue | ForEach-Object {
    $proc = Get-Process -Id $_.OwningProcess -ErrorAction SilentlyContinue
    if ($proc -and $proc.ProcessName -notlike "*docker*" -and $proc.ProcessName -notlike "*vpnkit*") {
        Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
    }
}

# Step 1: Ensure Docker Desktop is Running & Start Database Containers
Write-Host "`n[1/3] Starting Docker Database Services (PostgreSQL, Neo4j, Redis)..." -ForegroundColor Yellow
Set-Location $backendDir

docker info > $null 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "  -> Docker Desktop is not running. Launching Docker Desktop..." -ForegroundColor Cyan
    $dockerExe = "C:\Program Files\Docker\Docker\Docker Desktop.exe"
    if (Test-Path $dockerExe) {
        Start-Process $dockerExe
        Write-Host "  -> Waiting for Docker Engine to initialize..." -ForegroundColor Cyan
        $maxWait = 60
        while ($maxWait -gt 0) {
            Start-Sleep -Seconds 2
            docker info > $null 2>&1
            if ($LASTEXITCODE -eq 0) { break }
            $maxWait -= 2
        }
    }
}

docker-compose up -d postgres neo4j redis

$pythonExe = Join-Path $backendDir ".venv\Scripts\python.exe"

# Step 2: Start FastAPI Backend Server in New Window (Port 8000)
Write-Host "`n[2/3] Starting FastAPI Backend API Server on Port 8000..." -ForegroundColor Yellow
$backendCmd = "`"$pythonExe`" -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000"
Start-Process powershell -WorkingDirectory $backendDir -ArgumentList "-ExecutionPolicy Bypass -NoExit -Command $backendCmd"

# Step 3: Start Modern React Frontend in New Window (Port 5173)
Write-Host "`n[3/3] Starting React Web UI (Vite) on Port 5173..." -ForegroundColor Yellow
$frontendDir = Join-Path $backendDir "..\frontend"
$frontendCmd = "npm run dev"
Start-Process powershell -WorkingDirectory $frontendDir -ArgumentList "-ExecutionPolicy Bypass -NoExit -Command $frontendCmd"

Write-Host "`n==========================================================" -ForegroundColor Green
Write-Host "SUCCESS: All Project Components Launched!" -ForegroundColor Green
Write-Host "  * React Web UI:       http://localhost:5173" -ForegroundColor Cyan
Write-Host "  * FastAPI REST Docs:  http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "  * Neo4j Browser:      http://localhost:7474" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Green
