@echo off
REM ======================================================
REM OmniAssist AI - Simple One-Click Start
REM ======================================================

cd /d "%~dp0"
title OmniAssist AI

cls
echo.
echo ===============================================
echo   OmniAssist AI - Starting...
echo ===============================================
echo.

REM Check venv
if not exist "venv\Scripts\python.exe" (
    echo ERROR: Python venv not found!
    echo.
    echo Run this first:
    echo   python -m venv venv
    echo   .\venv\Scripts\pip install -r backend/requirements.txt
    echo   .\venv\Scripts\pip install -r desktop_1/requirements.txt
    echo.
    pause
    exit /b 1
)

REM Create logs folder if needed
if not exist "logs" mkdir logs

REM Backend now auto-generates runtime secrets if missing.
echo Preparing secure runtime environment...

REM If backend is already healthy, skip duplicate startup.
curl -s http://127.0.0.1:5000/api/health >nul 2>&1
if not errorlevel 1 (
    echo Backend already running.
    goto START_FRONTEND
)

REM Start backend in a detached window (not /B) so closing this launcher does not stop API
echo Starting backend...
set "OMNIASSIST_WAKE_WORD_AUTOSTART=0"
start "Backend" /MIN cmd /c ".\venv\Scripts\python.exe backend\api_service.py > logs\backend.log 2>&1"

REM Wait for backend readiness (up to 45s to allow model load on slower machines)
set BACKEND_READY=0
for /L %%I in (1,1,45) do (
    curl -s http://127.0.0.1:5000/api/health >nul 2>&1
    if not errorlevel 1 (
        set BACKEND_READY=1
        goto BACKEND_OK
    )
    timeout /t 1 /nobreak >nul
)

:BACKEND_OK
if "%BACKEND_READY%"=="0" (
    echo ERROR: Backend did not become healthy in time.
    echo.
    echo Recent backend log output:
    powershell -NoProfile -Command "if (Test-Path 'logs\backend.log') { Get-Content 'logs\backend.log' -Tail 30 }"
    echo.
    pause
    exit /b 1
)

REM Start frontend
:START_FRONTEND
echo Starting desktop app...
start "OmniAssist" .\venv\Scripts\python.exe desktop_1\main.py

echo.
echo ===============================================
echo   App started! Close this window when done.
echo ===============================================
echo.
pause
