@echo off
REM ======================================================
REM OmniAssist AI - Debug Launcher (For Developers)
REM Shows detailed output and keeps console open
REM ======================================================

cd /d "%~dp0"
title OmniAssist AI - Debug Mode

cls
echo.
echo ===============================================
echo   OmniAssist AI - DEBUG MODE
echo ===============================================
echo.

REM Check Python venv
if not exist "venv\Scripts\python.exe" (
    echo [ERROR] Python venv not found!
    echo.
    echo Setup:
    echo   python -m venv venv
    echo   .\venv\Scripts\pip install -r backend/requirements.txt
    echo   .\venv\Scripts\pip install -r desktop_1/requirements.txt
    echo.
    pause
    exit /b 1
)

REM Check Ollama
echo [1/3] Checking Ollama...
curl -s http://localhost:11434/api/tags >nul 2>&1
if errorlevel 1 (
    echo [WARN] Ollama not running. Start it manually: ollama serve
) else (
    echo [OK] Ollama is running
)

REM Create logs folder
if not exist "logs" mkdir logs

echo [2/4] Preparing secure runtime environment...
echo Backend will auto-generate secrets on first run.

REM Start backend
echo.
echo [3/4] Starting backend API...
echo Log: logs\backend.log
echo.
set "OMNIASSIST_WAKE_WORD_AUTOSTART=0"
start "Backend API" /MIN cmd /c ".\venv\Scripts\python.exe backend\api_service.py > logs\backend.log 2>&1"

REM Wait for backend
echo Waiting for backend to start...
set BACKEND_READY=0
for /L %%I in (1,1,45) do (
    curl -s http://127.0.0.1:5000/api/health >nul 2>&1
    if not errorlevel 1 (
        set BACKEND_READY=1
        goto BACKEND_READY
    )
    timeout /t 1 /nobreak >nul
)

:BACKEND_READY
if "%BACKEND_READY%"=="0" (
    echo [ERROR] Backend did not become healthy in time.
    echo Showing last log lines:
    powershell -NoProfile -Command "if (Test-Path 'logs\backend.log') { Get-Content 'logs\backend.log' -Tail 40 }"
    pause
    exit /b 1
)

REM Check backend health
curl -s http://localhost:5000/api/health >nul 2>&1
if errorlevel 1 (
    echo [WARN] Backend may not be ready. Check logs\backend.log
) else (
    echo [OK] Backend is ready
)

REM Start frontend
echo.
echo [4/4] Starting desktop UI...
.\venv\Scripts\python.exe desktop_1\main.py

echo.
echo ===============================================
echo   App stopped. Check logs/ for details.
echo ===============================================
pause
