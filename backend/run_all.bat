@echo off
echo ==========================================================
echo [+] Launching LLM + Knowledge Graph Research Assistant System
echo ==========================================================

cd /d %~dp0

powershell -Command "Get-NetTCPConnection -LocalPort 8501 -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }; Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }"

echo.
echo [1/3] Starting Docker Database Services (PostgreSQL, Neo4j, Redis)...
docker-compose up -d postgres neo4j redis

echo.
echo [2/3] Starting FastAPI Backend API Server on Port 8000...
start "FastAPI Backend Server" powershell -NoExit -Command "cd '%~dp0'; .venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000"

echo.
echo [3/3] Starting Streamlit Web Interface on Port 8501...
start "Streamlit Web UI" powershell -NoExit -Command "cd '%~dp0'; .venv\Scripts\python.exe -m streamlit run streamlit_app.py --server.port 8501"

echo.
echo ==========================================================
echo SUCCESS: All Project Components Launched!
echo   * Streamlit Web UI:   http://localhost:8501
echo   * FastAPI REST Docs:  http://localhost:8000/docs
echo   * Neo4j Browser:      http://localhost:7474
echo ==========================================================
