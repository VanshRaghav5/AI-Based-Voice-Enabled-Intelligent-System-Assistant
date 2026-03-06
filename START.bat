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

REM Start backend in background
echo Starting backend...
start /B "Backend" .\venv\Scripts\python.exe backend\api_service.py > logs\backend.log 2>&1

REM Wait a bit for backend to start
timeout /t 5 /nobreak >nul

REM Start frontend
echo Starting desktop app...
start "OmniAssist" .\venv\Scripts\python.exe desktop_1\main.py

echo.
echo ===============================================
echo   App started! Close this window when done.
echo ===============================================
echo.
pause
