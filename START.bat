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

REM Check required security env vars
if "%OMNIASSIST_FLASK_SECRET_KEY%"=="" (
    echo ERROR: OMNIASSIST_FLASK_SECRET_KEY is not set.
    echo Set it once in PowerShell:
    echo   setx OMNIASSIST_FLASK_SECRET_KEY "your-long-random-secret"
    echo.
    pause
    exit /b 1
)

if "%OMNIASSIST_JWT_SECRET%"=="" (
    echo ERROR: OMNIASSIST_JWT_SECRET is not set.
    echo Set it once in PowerShell:
    echo   setx OMNIASSIST_JWT_SECRET "your-long-random-secret"
    echo.
    pause
    exit /b 1
)

REM Start backend in background (cmd /c so stdout/stderr are captured in the log)
echo Starting backend...
start "Backend" /B cmd /c ".\venv\Scripts\python.exe backend\api_service.py > logs\backend.log 2>&1"

REM Wait for backend to initialise (Whisper model load ~4 s, plus small margin)
timeout /t 10 /nobreak >nul

REM Start frontend
echo Starting desktop app...
start "OmniAssist" .\venv\Scripts\python.exe desktop_1\main.py

echo.
echo ===============================================
echo   App started! Close this window when done.
echo ===============================================
echo.
pause
