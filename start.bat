@echo off
echo ========================================
echo   NEXUS - AI Research Scientist
echo   Starting backend and frontend...
echo ========================================
echo.

echo [1/2] Starting Backend (FastAPI)...
start "NEXUS Backend" cmd /c "cd /d %~dp0 && call .venv\Scripts\activate.bat && python -m uvicorn backend.app.main:app --reload --port 8000"

echo [2/2] Starting Frontend (Vite)...
timeout /t 3 /nobreak >nul
start "NEXUS Frontend" cmd /c "cd /d %~dp0frontend && npm run dev"

echo.
echo ========================================
echo   NEXUS is starting...
echo   Backend:  http://localhost:8000
echo   Frontend: http://localhost:5173
echo   API docs: http://localhost:8000/docs
echo ========================================
echo.
echo Press any key to exit this launcher (servers will keep running)
pause >nul
