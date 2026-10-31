@echo off
echo ==========================================================
echo [+] Launching LLM + Knowledge Graph Research Assistant System
echo ==========================================================

cd /d %~dp0

powershell -Command "Get-NetTCPConnection -LocalPort 5173, 8000, 8001 -ErrorAction SilentlyContinue | ForEach-Object { $p = Get-Process -Id $_.OwningProcess -ErrorAction SilentlyContinue; if ($p -and $p.ProcessName -notlike '*docker*' -and $p.ProcessName -notlike '*vpnkit*') { Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue } }"

echo.
echo [1/3] Starting Docker Database Services (PostgreSQL, Neo4j, Redis)...
docker-compose up -d postgres neo4j redis

echo.
echo [2/3] Starting FastAPI Backend API Server on Port 8000...
start "FastAPI Backend Server" powershell -NoExit -Command "cd '%~dp0'; .venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000"

echo.
echo [3/3] Starting React Web UI on Port 5173...
start "React Web UI" powershell -NoExit -Command "cd '%~dp0\..\frontend'; npm run dev"

echo.
echo ==========================================================
echo SUCCESS: All Project Components Launched!
echo   * React Web UI:       http://localhost:5173
echo   * FastAPI REST Docs:  http://localhost:8000/docs
echo   * Neo4j Browser:      http://localhost:7474
echo ==========================================================
