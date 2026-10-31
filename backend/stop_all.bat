@echo off
echo ==========================================================
echo [+] Stopping LLM + Knowledge Graph Research Assistant System
echo ==========================================================

cd /d %~dp0

powershell -Command "Get-NetTCPConnection -LocalPort 5173, 8000, 8001 -ErrorAction SilentlyContinue | ForEach-Object { $p = Get-Process -Id $_.OwningProcess -ErrorAction SilentlyContinue; if ($p -and $p.ProcessName -notlike '*docker*' -and $p.ProcessName -notlike '*vpnkit*') { Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue } }"

echo.
echo Stopping Docker Database Services (PostgreSQL, Neo4j, Redis)...
docker-compose down

echo.
echo ==========================================================
echo SUCCESS: All Services Stopped Cleanly!
echo ==========================================================

